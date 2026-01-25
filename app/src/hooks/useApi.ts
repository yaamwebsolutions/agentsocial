import { useState, useEffect, useCallback } from "react";
import type {
  TimelinePost,
  Thread,
  Agent,
  CreatePostRequest,
  CreatePostResponse,
  User,
  UserStats,
  AgentRun,
  Post,
} from "@/types/api";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

const AUTH_TOKEN_KEYS = ["auth0_access_token", "access_token"];

function getStoredAccessToken(): string | null {
  for (const key of AUTH_TOKEN_KEYS) {
    const token = localStorage.getItem(key);
    if (token) {
      return token;
    }
  }
  return null;
}

async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const accessToken = getStoredAccessToken();
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    // Try to get the error message from the response body
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // If parsing JSON fails, use the default error message
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

// Posts with auto-refresh
export function useTimeline(limit: number = 50) {
  const [posts, setPosts] = useState<TimelinePost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    apiCall<TimelinePost[]>(`/timeline?limit=${limit}`)
      .then(setPosts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [limit]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  // Auto-refresh timeline every 10 seconds for new posts
  useEffect(() => {
    const interval = setInterval(() => {
      // Silent refresh - don't show loading indicator
      apiCall<TimelinePost[]>(`/timeline?limit=${limit}`)
        .then(setPosts)
        .catch(() => {
          // Silently fail on auto-refresh
        });
    }, 10000);

    return () => clearInterval(interval);
  }, [limit]);

  return { posts, loading, error, refetch };
}

export function useThread(threadId: string, options: { disableAutoPoll?: boolean } = {}) {
  const [thread, setThread] = useState<Thread | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    apiCall<Thread>(`/threads/${threadId}`)
      .then(setThread)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [threadId]);

  useEffect(() => {
    if (threadId) {
      refetch();
    }
  }, [threadId, refetch]);

  // Auto-poll thread when there are active agent runs (only if auto-poll enabled)
  useEffect(() => {
    if (options.disableAutoPoll) return;
    if (!thread) return;

    // Check if any post has active agent mentions
    const allPosts = [thread.root_post, ...thread.replies];
    const hasAgentMentions = allPosts.some((post) =>
      post.mentions && post.mentions.length > 0
    );

    if (!hasAgentMentions) return;

    // Poll every 3 seconds for thread updates when agents are involved
    const interval = setInterval(() => {
      refetch();
    }, 3000);

    return () => clearInterval(interval);
  }, [thread, refetch, options.disableAutoPoll]);

  return { thread, loading, error, refetch };
}

export async function createPost(
  request: CreatePostRequest
): Promise<CreatePostResponse> {
  return apiCall<CreatePostResponse>("/posts", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// Agents
export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiCall<Agent[]>("/agents")
      .then(setAgents)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { agents, loading, error };
}

// User
export function useCurrentUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiCall<User>("/auth/me")
      .then(setUser)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading, error };
}

// Agent Runs with auto-polling for active runs
export function useThreadAgentRuns(threadId: string, options: { disableAutoPoll?: boolean } = {}) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(() => {
    apiCall<{ runs: AgentRun[] }>(`/threads/${threadId}/agent-runs`)
      .then((data) => setRuns(data.runs))
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  }, [threadId]);

  useEffect(() => {
    if (threadId) {
      refetch();
    }
  }, [threadId, refetch]);

  // Auto-poll when there are active agent runs (only if auto-poll enabled)
  useEffect(() => {
    if (options.disableAutoPoll) return;

    // Check if there are any active (queued or running) agent runs
    const hasActiveRuns = runs.some(
      (run) => run.status === "queued" || run.status === "running"
    );

    if (!hasActiveRuns) return;

    // Poll every 2 seconds when there are active runs
    const interval = setInterval(() => {
      refetch();
    }, 2000);

    return () => clearInterval(interval);
  }, [runs, refetch, options.disableAutoPoll]);

  return { runs, loading, refetch };
}

// Like/Unlike
export async function likePost(postId: string): Promise<{
  liked: boolean;
  like_count: number;
  is_liked: boolean;
}> {
  return apiCall(`/posts/${postId}/like`, {
    method: "POST",
  });
}

export async function unlikePost(postId: string): Promise<{
  unliked: boolean;
  like_count: number;
  is_liked: boolean;
}> {
  return apiCall(`/posts/${postId}/unlike`, {
    method: "POST",
  });
}

// Delete Post
export async function deletePost(postId: string): Promise<{ message: string }> {
  return apiCall(`/posts/${postId}`, {
    method: "DELETE",
  });
}

// User Stats
export function useUserStats(userId: string) {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    apiCall<UserStats>(`/users/${userId}/stats`)
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  useEffect(() => {
    if (userId) {
      refetch();
    }
  }, [userId, refetch]);

  return { stats, loading, error, refetch };
}

// User Posts
export function useUserPosts(userId: string, limit: number = 50) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    apiCall<Post[]>(`/users/${userId}/posts?limit=${limit}`)
      .then(setPosts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId, limit]);

  useEffect(() => {
    if (userId) {
      refetch();
    }
  }, [userId, limit, refetch]);

  return { posts, loading, error, refetch };
}
