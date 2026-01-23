import { useState, useEffect, useCallback } from "react";
import type {
  TimelinePost,
  Thread,
  Agent,
  CreatePostRequest,
  CreatePostResponse,
  User,
  AgentRun,
} from "@/types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Posts
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

  return { posts, loading, error, refetch };
}

export function useThread(threadId: string) {
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
    apiCall<User>("/me")
      .then(setUser)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading, error };
}

// Agent Runs
export function useThreadAgentRuns(threadId: string) {
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

  return { runs, loading, refetch };
}
