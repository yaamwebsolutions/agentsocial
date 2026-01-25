/**
 * Authentication-related type definitions for the AgentTwitter platform
 */

// =============================================================================
// AUTH0 TYPES
// =============================================================================

export interface Auth0User {
  sub: string;              // Auth0 user ID
  user_id?: string;
  email: string;
  email_verified: boolean;
  name: string;
  nickname: string;
  picture: string;
  updated_at?: string;
  auth0_id: string;
  github_login?: string;
  avatar_url?: string;
}

export interface Auth0Tokens {
  access_token: string;
  id_token: string;
  token_type: string;
  expires_in?: number;
}

export interface Auth0LoginResponse {
  login_url: string;
  state: string;
}

export interface Auth0CallbackResponse {
  access_token: string;
  id_token: string;
  token_type: string;
  expires_in?: number;
  user: Auth0User;
}

// =============================================================================
// GITHUB TYPES
// =============================================================================

// =============================================================================
// ENUMS
// =============================================================================

export type RepoCategory =
  | "web_framework"
  | "database"
  | "devops"
  | "ai_ml"
  | "tool"
  | "library"
  | "other";

export type NotificationType = "star_milestone" | "new_release" | "trending";

export type TimeRange = "day" | "week" | "month" | "all";

export type SortField = "stars" | "forks" | "updated";

export type SortOrder = "desc" | "asc";

// =============================================================================
// GITHUB USER MODELS
// =============================================================================

export interface GitHubUser {
  id: number;
  login: string;
  name: string | null;
  email: string | null;
  avatar_url: string | null;
  bio: string | null;
  location: string | null;
  blog: string | null;
  public_repos: number;
  followers: number;
  following: number;
  html_url: string | null;
}

export interface AuthUser {
  id: string;
  github_id: number;
  github_login: string;
  avatar_url: string | null;
  name: string | null;
  email: string | null;
  bio: string | null;
  created_at: string;
  last_login: string;
}

// =============================================================================
// REPOSITORY MODELS
// =============================================================================

export interface Repository {
  id: string;
  github_id: number;
  owner: string;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  watchers: number;
  homepage: string | null;
  url: string;
  html_url: string;
  topics: string[];
  category: RepoCategory;
  is_tracking: boolean;
  created_at: string;
  updated_at: string;
  last_star_fetch: string | null;
  pushed_at: string | null;
  default_branch: string;
}

export interface StarHistoryPoint {
  timestamp: string;
  star_count: number;
}

export interface RepositoryRelease {
  id: string;
  repo_id: string;
  tag_name: string;
  name: string | null;
  html_url: string;
  published_at: string;
  is_prerelease: boolean;
  author: {
    login: string;
    avatar_url: string;
  } | null;
  body: string | null;
}

export interface Commit {
  sha: string;
  message: string;
  author: {
    name: string;
    email: string;
    login: string;
    avatar_url: string;
  };
  html_url: string;
  url: string;
  timestamp: string;
}

export interface Issue {
  id: number;
  title: string;
  body: string | null;
  state: "open" | "closed" | "all";
  user: {
    login: string;
    avatar_url: string;
  };
  labels: {
    name: string;
    color: string;
  }[];
  html_url: string;
  created_at: string;
  updated_at: string;
  comments: number;
}

// =============================================================================
// TRACKED REPOSITORY (with enriched data)
// =============================================================================

export interface TrackedRepo {
  repository: Repository;
  latest_release: RepositoryRelease | null;
  star_change_24h: number;
  star_change_7d: number;
  star_change_30d: number;
  star_velocity_7d: number;  // stars per day
  star_velocity_30d: number; // stars per day
  rank_all: number | null;     // rank across all tracked repos
  rank_language: number | null; // rank within same language
  milestone_next: number | null; // next star milestone (1000, 10000, etc.)
}

// =============================================================================
// NOTIFICATIONS
// =============================================================================

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  link_url: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  data?: Record<string, any>; // Additional data (repo_id, star_count, etc.)
}

// =============================================================================
// SEARCH & FILTERS
// =============================================================================

export interface SearchFilters {
  language?: string;
  min_stars?: number;
  sort_by?: SortField;
  order?: SortOrder;
  topics?: string[];
}

export interface LeaderboardFilters {
  category?: RepoCategory;
  language?: string;
  time_range?: TimeRange;
  limit?: number;
}

export interface RepoSearchRequest {
  query: string;
  filters?: SearchFilters;
}

export interface RepoSearchResponse {
  total_count: number;
  incomplete_results: boolean;
  items: Repository[];
}

// =============================================================================
// ANALYTICS
// =============================================================================

export interface AnalyticsDashboard {
  total_repos: number;
  total_stars: number;
  total_forks: number;
  active_repos_24h: number;
  active_repos_7d: number;
  top_languages: {
    language: string;
    count: number;
    percentage: number;
  }[];
  fastest_growing: TrackedRepo[];
  recent_milestones: Notification[];
}

export interface RepoStats {
  repo_id: string;
  star_history: StarHistoryPoint[];
  growth_24h: number;
  growth_7d: number;
  growth_30d: number;
  growth_90d: number;
  star_velocity: {
    "1d": number;
    "7d": number;
    "30d": number;
  };
  percentiles: {
    stars: number;    // percentile among all tracked repos
    growth_7d: number;
    growth_30d: number;
  };
  milestones: {
    milestone: number;
    achieved_at: string;
  }[];
}

// =============================================================================
// AI ANALYSIS
// =============================================================================

export interface RepoAnalysis {
  summary: string;
  key_features: string[];
  use_cases: string[];
  strengths: string[];
  improvements: string[];
  similar_repos: string[];
  tech_stack: string[];
  sentiment: "positive" | "neutral" | "caution";
  ai_generated: boolean;
  generated_at: string;
}

export interface RepoComparison {
  repos: Repository[];
  comparison_matrix: Record<string, boolean | number>;
  recommendation: string;
  use_case: string;
}

// =============================================================================
// TRACKING REQUESTS
// =============================================================================

export interface TrackRepoRequest {
  full_name: string;  // e.g., "facebook/react"
  notify_on_release?: boolean;
  notify_on_star_milestone?: boolean;
  star_milestone_interval?: number;  // Notify every N stars (100, 1000, etc.)
}

export interface UpdateTrackingRequest {
  repo_id: string;
  notify_on_release?: boolean;
  notify_on_star_milestone?: boolean;
  star_milestone_interval?: number;
}

// =============================================================================
// API REQUEST/RESPONSE TYPES
// =============================================================================

export interface GitHubAuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface GitHubOAuthCallbackRequest {
  code: string;
  state: string;
}

export interface GitHubOAuthResponse {
  access_token: string;
  token_type: string;
  scope?: string;
  user?: AuthUser;
}

export interface AuthMeResponse {
  user: AuthUser;
  permissions: string[];
}

// =============================================================================
// CHART DATA
// =============================================================================

export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface LanguageStats {
  language: string;
  count: number;
  percentage: number;
  color: string;
}

export interface TrendingRepo {
  repo: TrackedRepo;
  growth_rate: number;  // stars per day
  period: string;      // "24h", "7d", "30d"
  rank: number;
}
