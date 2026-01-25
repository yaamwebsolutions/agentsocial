export type AuthorType = "human" | "agent";

export type AgentStatus = "queued" | "running" | "done" | "error";

export interface User {
  id: string;
  display_name: string;
  handle: string;
  avatar_url?: string;
  bio?: string;
}

export interface UserStats {
  user_id: string;
  post_count: number;
  like_count: number;
  reply_count: number;
}

export interface Agent {
  id: string;
  handle: string;
  name: string;
  role: string;
  policy: string;
  style: string;
  tools: string[];
  color: string;
  icon: string;
  mock_responses?: string[];
}

export interface Post {
  id: string;
  author_type: AuthorType;
  author_handle: string;
  text: string;
  created_at: string;
  parent_id?: string;
  thread_id: string;
  mentions: string[];
  meta: Record<string, any>;
  like_count: number;
  is_liked: boolean;
}

export interface TimelinePost extends Post {
  reply_count: number;
}

export interface AgentRun {
  id: string;
  agent_handle: string;
  thread_id: string;
  trigger_post_id: string;
  status: AgentStatus;
  started_at: string;
  ended_at?: string;
  input_context: Record<string, any>;
  output_post_id?: string;
  trace: Record<string, any>;
}

export interface Thread {
  root_post: Post;
  replies: Post[];
}

export interface CreatePostRequest {
  text: string;
  parent_id?: string;
}

export interface CreatePostResponse {
  post: Post;
  triggered_agent_runs: AgentRun[];
}
