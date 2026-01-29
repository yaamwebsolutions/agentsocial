import { useState, useEffect, useCallback } from "react";
import type {
  AuditTrailResponse,
  AuditStats,
  MediaAsset,
  ConversationAudit,
  AuditEventType,
  AdminComprehensiveAuditResponse,
  SystemEvent,
  UserActivitySummary,
  ErrorAnalysis,
  SystemConfig,
  ExportOptions,
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
    auditCall<{
      audit: ConversationAudit;
      related_logs: unknown[];
    }>(`/audit/conversations/${threadId}`)
      .then((data) => setAudit(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [threadId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { audit, loading, error, refetch };
}

// ============================================================================
// ADMIN AUDIT HOOKS
// ============================================================================

interface UseAdminAuditOptions {
  start_date?: string;
  end_date?: string;
  event_type?: AuditEventType;
  user_id?: string;
  resource_type?: string;
  status?: string;
}

export function useAdminComprehensiveAudit(options: UseAdminAuditOptions = {}) {
  const [data, setData] = useState<AdminComprehensiveAuditResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (options.start_date) params.append("start_date", options.start_date);
    if (options.end_date) params.append("end_date", options.end_date);
    if (options.event_type) params.append("event_type", options.event_type);
    if (options.user_id) params.append("user_id", options.user_id);
    if (options.resource_type) params.append("resource_type", options.resource_type);
    if (options.status) params.append("status", options.status);

    auditCall<AdminComprehensiveAuditResponse>(
      `/admin/audit/comprehensive?${params.toString()}`
    )
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [options]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useSystemEvents(limit: number = 100) {
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    auditCall<{ events: SystemEvent[] }>(`/admin/audit/system-events?limit=${limit}`)
      .then((data) => setEvents(data.events))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [limit]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { events, loading, error, refetch };
}

export function useUserActivity(userId: string) {
  const [activity, setActivity] = useState<UserActivitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    if (!userId) return;
    setLoading(true);
    auditCall<UserActivitySummary>(`/admin/audit/user-activity/${userId}`)
      .then(setActivity)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { activity, loading, error, refetch };
}

export function useErrorAnalysis(days: number = 7) {
  const [errors, setErrors] = useState<ErrorAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    auditCall<{ errors: ErrorAnalysis[] }>(`/admin/audit/errors?days=${days}`)
      .then((data) => setErrors(data.errors))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [days]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { errors, loading, error, refetch };
}

export function useSystemConfig() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    auditCall<SystemConfig>("/admin/audit/config")
      .then(setConfig)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { config, loading, error, refetch };
}

export function useExportAuditLogs() {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportLogs = useCallback(async (options: ExportOptions) => {
    setExporting(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append("format", options.format);
      if (options.start_date) params.append("start_date", options.start_date);
      if (options.end_date) params.append("end_date", options.end_date);
      if (options.event_type) params.append("event_type", options.event_type);
      if (options.user_id) params.append("user_id", options.user_id);
      if (options.resource_type) params.append("resource_type", options.resource_type);
      if (options.include_details) params.append("include_details", "true");

      const response = await fetch(`${API_BASE}/admin/audit/logs/export?${params.toString()}`, {
        headers: {
          ...(getStoredAccessToken()
            ? { Authorization: `Bearer ${getStoredAccessToken()}` }
            : {}),
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Export failed: ${response.status}`);
      }

      // Handle different response types based on format
      if (options.format === "json") {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `audit-export-${new Date().toISOString()}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // CSV format
        const text = await response.text();
        const blob = new Blob([text], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `audit-export-${new Date().toISOString()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
      return false;
    } finally {
      setExporting(false);
    }
  }, []);

  return { exportLogs, exporting, error };
}
