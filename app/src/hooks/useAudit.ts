import { useState, useEffect, useCallback } from "react";
import type {
  AuditTrailResponse,
  AuditStats,
  MediaAsset,
  ConversationAudit,
  AuditEventType,
} from "@/types/api";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

function getStoredAccessToken(): string | null {
  const keys = ["auth0_id_token", "auth0_access_token", "access_token"];
  for (const key of keys) {
    const token = localStorage.getItem(key);
    if (token) return token;
  }
  return null;
}

async function auditCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = getStoredAccessToken();
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// AUDIT LOGS HOOK
// ============================================================================

interface UseAuditLogsOptions {
  event_type?: AuditEventType;
  user_id?: string;
  resource_type?: string;
  resource_id?: string;
  thread_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
  autoRefresh?: boolean;
}

export function useAuditLogs(options: UseAuditLogsOptions = {}) {
  const [logs, setLogs] = useState<AuditTrailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (options.event_type) params.append("event_type", options.event_type);
    if (options.user_id) params.append("user_id", options.user_id);
    if (options.resource_type) params.append("resource_type", options.resource_type);
    if (options.resource_id) params.append("resource_id", options.resource_id);
    if (options.thread_id) params.append("thread_id", options.thread_id);
    if (options.status) params.append("status", options.status);
    params.append("page", String(options.page ?? 1));
    params.append("page_size", String(options.page_size ?? 50));

    auditCall<AuditTrailResponse>(`/audit/logs?${params.toString()}`)
      .then(setLogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [options]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (options.autoRefresh) {
      const interval = setInterval(fetchLogs, 30000);
      return () => clearInterval(interval);
    }
  }, [fetchLogs, options.autoRefresh]);

  return { logs, loading, error, refetch: fetchLogs };
}

// ============================================================================
// AUDIT STATS HOOK
// ============================================================================

export function useAuditStats() {
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    auditCall<AuditStats>("/audit/stats")
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { stats, loading, error, refetch };
}

// ============================================================================
// MEDIA ASSETS HOOK
// ============================================================================

interface UseMediaAssetsOptions {
  asset_type?: "video" | "image";
  thread_id?: string;
  user_id?: string;
  limit?: number;
}

export function useMediaAssets(options: UseMediaAssetsOptions = {}) {
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (options.asset_type) params.append("asset_type", options.asset_type);
    if (options.thread_id) params.append("thread_id", options.thread_id);
    if (options.user_id) params.append("user_id", options.user_id);
    params.append("limit", String(options.limit ?? 50));

    auditCall<{ assets: MediaAsset[]; count: number }>(
      `/audit/media?${params.toString()}`
    )
      .then((data) => setAssets(data.assets))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [options]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { assets, loading, error, refetch };
}

// ============================================================================
// CONVERSATION AUDITS HOOK
// ============================================================================

export function useConversationAudits() {
  const [conversations, setConversations] = useState<ConversationAudit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    auditCall<{ conversations: ConversationAudit[]; count: number }>(
      "/audit/conversations"
    )
      .then((data) => setConversations(data.conversations))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { conversations, loading, error, refetch };
}

// ============================================================================
// SINGLE CONVERSATION AUDIT HOOK
// ============================================================================

export function useConversationAudit(threadId: string) {
  const [audit, setAudit] = useState<{
    audit: ConversationAudit;
    related_logs: any[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    if (!threadId) return;
    setLoading(true);
    auditCall(`/audit/conversations/${threadId}`)
      .then((data) => setAudit(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [threadId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { audit, loading, error, refetch };
}
