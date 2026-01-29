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

// =============================================================================
// AUDIT TRAIL TYPES
// =============================================================================

export type AuditEventType =
  | "post_create"
  | "post_delete"
  | "post_like"
  | "post_unlike"
  | "agent_run_start"
  | "agent_run_complete"
  | "agent_run_error"
  | "media_video_generate"
  | "media_image_generate"
  | "media_search"
  | "auth_login"
  | "auth_logout"
  | "auth_failed"
  | "command_executed"
  | "command_failed"
  | "system_error"
  | "system_startup";

export interface AuditLog {
  id: string;
  timestamp: string;
  event_type: AuditEventType;
  user_id?: string;
  session_id?: string;
  ip_address?: string;
  user_agent?: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  status: string;
  error_message?: string;
  thread_id?: string;
  post_id?: string;
  agent_run_id?: string;
}

export interface MediaAsset {
  id: string;
  created_at: string;
  asset_type: "video" | "image";
  url: string;
  prompt: string;
  generated_by: string;
  service: string;
  thread_id?: string;
  post_id?: string;
  duration_seconds?: number;
  thumbnail_url?: string;
  status: string;
}

export interface ConversationAudit {
  id: string;
  thread_id: string;
  created_at: string;
  updated_at: string;
  participant_ids: string[];
  agent_handles: string[];
  message_count: number;
  human_message_count: number;
  agent_message_count: number;
  media_assets: string[];
  commands_executed: string[];
  status: string;
}

export interface AuditTrailResponse {
  logs: AuditLog[];
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface AuditStats {
  total_logs: number;
  total_media_assets: number;
  total_conversations: number;
  event_type_counts: Record<string, number>;
  video_count: number;
  image_count: number;
}

// =============================================================================
// ADMIN AUDIT TYPES
// =============================================================================

export interface AdminComprehensiveAuditResponse {
  logs: AuditLog[];
  media_assets: MediaAsset[];
  conversations: ConversationAudit[];
  stats: AuditStats;
  system_events: SystemEvent[];
}

export interface SystemEvent {
  id: string;
  timestamp: string;
  event_type: string;
  description: string;
  severity: "info" | "warning" | "error" | "critical";
  details: Record<string, any>;
}

export interface UserActivitySummary {
  user_id: string;
  total_actions: number;
  first_seen: string;
  last_seen: string;
  action_breakdown: Record<string, number>;
  ip_addresses: string[];
  user_agents: string[];
  conversations_created: number;
  media_generated: number;
  errors_encountered: number;
}

export interface ErrorAnalysis {
  error_type: string;
  count: number;
  first_occurrence: string;
  last_occurrence: string;
  affected_users: number;
  sample_errors: Array<{
    timestamp: string;
    user_id?: string;
    message: string;
    details: Record<string, any>;
  }>;
}

export interface SystemConfig {
  audit_enabled: boolean;
  database_enabled: boolean;
  retention_days: number;
  detailed_logging: boolean;
  admin_user_ids_count: number;
  admin_email_domains: string[];
  auth0_enabled: boolean;
}

export interface ExportOptions {
  format: "json" | "csv";
  start_date?: string;
  end_date?: string;
  event_type?: AuditEventType;
  user_id?: string;
  resource_type?: string;
  include_details?: boolean;
}
