import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  useAdminComprehensiveAudit,
  useSystemEvents,
  useErrorAnalysis,
  useSystemConfig,
  useExportAuditLogs,
} from "@/hooks/useAudit";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Loader2,
  FileText,
  Video,
  Image,
  MessageSquare,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  Download,
  Search,
  Filter,
  Activity,
  Bug,
  Users,
  Database,
} from "lucide-react";

const eventLabels: Record<
  string,
  { label: string; icon: React.ReactNode; color: string }
> = {
  post_create: { label: "Post Created", icon: <FileText size={16} />, color: "bg-blue-500" },
  post_delete: { label: "Post Deleted", icon: <FileText size={16} />, color: "bg-red-500" },
  post_like: { label: "Post Liked", icon: <FileText size={16} />, color: "bg-pink-500" },
  post_unlike: { label: "Post Unliked", icon: <FileText size={16} />, color: "bg-gray-500" },
  agent_run_start: {
    label: "Agent Started",
    icon: <MessageSquare size={16} />,
    color: "bg-yellow-500",
  },
  agent_run_complete: {
    label: "Agent Completed",
    icon: <CheckCircle size={16} />,
    color: "bg-green-500",
  },
  agent_run_error: {
    label: "Agent Error",
    icon: <XCircle size={16} />,
    color: "bg-red-500",
  },
  media_video_generate: {
    label: "Video Generated",
    icon: <Video size={16} />,
    color: "bg-purple-500",
  },
  media_image_generate: {
    label: "Image Generated",
    icon: <Image size={16} />,
    color: "bg-indigo-500",
  },
  media_search: {
    label: "Media Searched",
    icon: <Image size={16} />,
    color: "bg-cyan-500",
  },
  auth_login: { label: "User Login", icon: <CheckCircle size={16} />, color: "bg-green-500" },
  auth_logout: { label: "User Logout", icon: <FileText size={16} />, color: "bg-gray-500" },
  auth_failed: { label: "Auth Failed", icon: <XCircle size={16} />, color: "bg-red-500" },
  command_executed: {
    label: "Command Executed",
    icon: <CheckCircle size={16} />,
    color: "bg-green-500",
  },
  command_failed: {
    label: "Command Failed",
    icon: <XCircle size={16} />,
    color: "bg-red-500",
  },
  system_error: {
    label: "System Error",
    icon: <AlertTriangle size={16} />,
    color: "bg-red-500",
  },
  system_startup: {
    label: "System Startup",
    icon: <CheckCircle size={16} />,
    color: "bg-blue-500",
  },
};

function getStatusIcon(status: string) {
  switch (status) {
    case "success":
      return <CheckCircle size={16} className="text-green-500" />;
    case "failed":
      return <XCircle size={16} className="text-red-500" />;
    case "pending":
      return <Clock size={16} className="text-yellow-500" />;
    default:
      return <Clock size={16} className="text-gray-500" />;
  }
}

function getSeverityIcon(severity: string) {
  switch (severity) {
    case "critical":
      return <AlertTriangle size={16} className="text-red-600" />;
    case "error":
      return <XCircle size={16} className="text-red-500" />;
    case "warning":
      return <AlertTriangle size={16} className="text-yellow-500" />;
    default:
      return <CheckCircle size={16} className="text-blue-500" />;
  }
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case "critical":
      return "bg-red-600 text-white";
    case "error":
      return "bg-red-100 text-red-700 border-red-300";
    case "warning":
      return "bg-yellow-100 text-yellow-700 border-yellow-300";
    default:
      return "bg-blue-100 text-blue-700 border-blue-300";
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

function timeAgo(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
}

export function AdminAuditDashboard() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [userId, setUserId] = useState("");
  const [errorDays, setErrorDays] = useState(7);

  // Always call hooks (React Rules of Hooks)
  // Fetch comprehensive audit data
  const {
    data,
    loading: dataLoading,
    error: dataError,
    refetch: refetchData,
  } = useAdminComprehensiveAudit();

  // Fetch system events
  const {
    events,
    loading: eventsLoading,
    refetch: refetchEvents,
  } = useSystemEvents(100);

  // Fetch error analysis
  const {
    errors,
    loading: errorsLoading,
    refetch: refetchErrors,
  } = useErrorAnalysis(errorDays);

  // Fetch system config
  const {
    config,
    loading: configLoading,
    refetch: refetchConfig,
  } = useSystemConfig();

  // Export functionality
  const { exportLogs, exporting } = useExportAuditLogs();

  const handleRefresh = () => {
    refetchData();
    refetchEvents();
    refetchErrors();
    refetchConfig();
  };

  const handleExport = async (format: "json" | "csv") => {
    await exportLogs({ format });
  };

  const handleSearchUser = () => {
    if (userId.trim()) {
      navigate(`/admin/audit/user/${userId}`);
    }
  };

  // Require authentication - check after all hooks are called
  if (!isAuthenticated) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <Card className="border-0 rounded-2xl bg-muted/30 p-8 text-center">
          <Shield className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-bold mb-2">Authentication Required</h2>
          <p className="text-muted-foreground mb-4">Please log in to access admin audit features.</p>
          <Button onClick={() => navigate("/")}>Back to Home</Button>
        </Card>
      </div>
    );
  }

  if (dataError && !data) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="flex items-center gap-3 text-red-700">
            <XCircle size={24} />
            <div>
              <h3 className="font-semibold">Access Denied</h3>
              <p className="text-sm">{dataError}</p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Shield className="text-purple-600" size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Admin Audit Dashboard</h1>
            <p className="text-muted-foreground">
              Enterprise-grade audit trail with full system visibility
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("json")}
            disabled={exporting}
          >
            <Download size={16} className="mr-2" />
            Export JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("csv")}
            disabled={exporting}
          >
            <Download size={16} className="mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* User Search */}
      <Card className="p-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <Label htmlFor="user-search" className="sr-only">
              Search User Activity
            </Label>
            <div className="relative">
              <Search
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                id="user-search"
                placeholder="Search user activity by ID..."
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearchUser()}
                className="pl-10"
              />
            </div>
          </div>
          <Button onClick={handleSearchUser} disabled={!userId.trim()}>
            <Users size={16} className="mr-2" />
            View User
          </Button>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="events">System Events</TabsTrigger>
          <TabsTrigger value="errors">Error Analysis</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="logs">Detailed Logs</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {dataLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : data ? (
            <>
              {/* Stats Cards */}
              <div className="grid gap-4 md:grid-cols-5">
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity size={18} className="text-blue-500" />
                    <span className="text-sm text-muted-foreground">Total Events</span>
                  </div>
                  <div className="text-2xl font-bold">{data.stats.total_logs || 0}</div>
                </Card>
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Video size={18} className="text-purple-500" />
                    <span className="text-sm text-muted-foreground">Videos</span>
                  </div>
                  <div className="text-2xl font-bold">{data.stats.video_count || 0}</div>
                </Card>
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Image size={18} className="text-indigo-500" />
                    <span className="text-sm text-muted-foreground">Images</span>
                  </div>
                  <div className="text-2xl font-bold">{data.stats.image_count || 0}</div>
                </Card>
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare size={18} className="text-green-500" />
                    <span className="text-sm text-muted-foreground">Conversations</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data.stats.total_conversations || 0}
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Database size={18} className="text-orange-500" />
                    <span className="text-sm text-muted-foreground">Media Assets</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data.stats.total_media_assets || 0}
                  </div>
                </Card>
              </div>

              {/* Event Breakdown */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Event Type Breakdown</h3>
                <div className="grid gap-3 md:grid-cols-2">
                  {Object.entries(data.stats.event_type_counts || {}).map(
                    ([type, count]) => {
                      const info = eventLabels[type] || {
                        label: type,
                        icon: <FileText size={16} />,
                        color: "bg-gray-500",
                      };
                      return (
                        <div
                          key={type}
                          className="flex items-center justify-between p-3 rounded-lg border"
                        >
                          <div className="flex items-center gap-2">
                            <div className={`p-1.5 rounded ${info.color} text-white`}>
                              {info.icon}
                            </div>
                            <span className="text-sm font-medium">{info.label}</span>
                          </div>
                          <Badge variant="secondary">{count as number}</Badge>
                        </div>
                      );
                    }
                  )}
                </div>
              </Card>

              {/* Recent System Events */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Recent System Events</h3>
                <div className="space-y-2">
                  {data.system_events.slice(0, 10).map((event) => (
                    <div
                      key={event.id}
                      className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50"
                    >
                      <div className="flex-shrink-0">{getSeverityIcon(event.severity)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium">{event.description}</span>
                          <Badge
                            variant="outline"
                            className={getSeverityColor(event.severity)}
                          >
                            {event.severity}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {formatTimestamp(event.timestamp)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          ) : null}
        </TabsContent>

        {/* System Events Tab */}
        <TabsContent value="events" className="space-y-4">
          {eventsLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">
                  System Events ({events.length})
                </h3>
              </div>
              <div className="space-y-2">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="p-4 rounded-lg border hover:bg-muted/50"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">{getSeverityIcon(event.severity)}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="font-medium">{event.description}</span>
                          <Badge
                            variant="outline"
                            className={getSeverityColor(event.severity)}
                          >
                            {event.severity}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {event.event_type}
                          </span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {formatTimestamp(event.timestamp)}
                        </div>
                        {Object.keys(event.details).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                              View Details
                            </summary>
                            <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-x-auto">
                              {JSON.stringify(event.details, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {events.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  No system events recorded yet.
                </div>
              )}
            </Card>
          )}
        </TabsContent>

        {/* Error Analysis Tab */}
        <TabsContent value="errors" className="space-y-4">
          <Card className="p-4 mb-4">
            <div className="flex items-center gap-4">
              <div>
                <Label htmlFor="error-days">Time Period</Label>
                <div className="flex items-center gap-2 mt-1">
                  <Input
                    id="error-days"
                    type="number"
                    min={1}
                    max={90}
                    value={errorDays}
                    onChange={(e) => setErrorDays(Number(e.target.value))}
                    className="w-20"
                  />
                  <span className="text-sm text-muted-foreground">days</span>
                  <Button size="sm" onClick={() => refetchErrors()}>
                    <Filter size={14} className="mr-2" />
                    Apply
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {errorsLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-4">
              {errors.map((error) => (
                <Card key={error.error_type} className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Bug size={20} className="text-red-500" />
                      <div>
                        <h4 className="font-semibold">{error.error_type}</h4>
                        <p className="text-sm text-muted-foreground">
                          {error.count} occurrences • {error.affected_users}{" "}
                          users affected
                        </p>
                      </div>
                    </div>
                    <Badge variant="destructive">{error.count}</Badge>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                    <div>
                      <div className="text-muted-foreground">First Occurrence</div>
                      <div>{formatTimestamp(error.first_occurrence)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Last Occurrence</div>
                      <div>{formatTimestamp(error.last_occurrence)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Total Count</div>
                      <div>{error.count}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Affected Users</div>
                      <div>{error.affected_users}</div>
                    </div>
                  </div>

                  {error.sample_errors.length > 0 && (
                    <details>
                      <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground mb-2">
                        Sample Errors ({error.sample_errors.length})
                      </summary>
                      <div className="space-y-2">
                        {error.sample_errors.map((sample, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-red-50 border border-red-200 rounded-lg"
                          >
                            <div className="flex items-center gap-2 text-sm mb-1">
                              <span className="font-medium">
                                {formatTimestamp(sample.timestamp)}
                              </span>
                              {sample.user_id && (
                                <span className="text-muted-foreground">
                                  • User: {sample.user_id.slice(0, 8)}...
                                </span>
                              )}
                            </div>
                            <div className="text-sm">{sample.message}</div>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </Card>
              ))}
              {errors.length === 0 && (
                <Card className="p-12">
                  <div className="text-center text-muted-foreground">
                    <CheckCircle size={48} className="mx-auto mb-4 text-green-500" />
                    <p>No errors recorded in the last {errorDays} days.</p>
                  </div>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4">
          {configLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : config ? (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">System Configuration</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="font-medium text-sm text-muted-foreground uppercase">
                    Audit Settings
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="text-sm">Audit Enabled</span>
                      <Badge variant={config.audit_enabled ? "default" : "secondary"}>
                        {config.audit_enabled ? "Yes" : "No"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="text-sm">Database Enabled</span>
                      <Badge variant={config.database_enabled ? "default" : "secondary"}>
                        {config.database_enabled ? "Yes" : "No"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="text-sm">Detailed Logging</span>
                      <Badge variant={config.detailed_logging ? "default" : "secondary"}>
                        {config.detailed_logging ? "Yes" : "No"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="text-sm">Retention Period</span>
                      <Badge variant="outline">{config.retention_days} days</Badge>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium text-sm text-muted-foreground uppercase">
                    Authentication
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="text-sm">Auth0 Enabled</span>
                      <Badge variant={config.auth0_enabled ? "default" : "secondary"}>
                        {config.auth0_enabled ? "Yes" : "No"}
                      </Badge>
                    </div>
                  </div>

                  <h4 className="font-medium text-sm text-muted-foreground uppercase">
                    Admin Access
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="text-sm">Admin User IDs</span>
                      <Badge variant="outline">{config.admin_user_ids_count}</Badge>
                    </div>
                    <div className="p-3 rounded-lg border">
                      <span className="text-sm block mb-2">Admin Email Domains</span>
                      <div className="flex flex-wrap gap-1">
                        {config.admin_email_domains.length > 0 ? (
                          config.admin_email_domains.map((domain) => (
                            <Badge key={domain} variant="secondary">
                              @{domain}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-xs text-muted-foreground">None configured</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ) : null}
        </TabsContent>

        {/* Detailed Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          {dataLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : data ? (
            <Card className="p-4">
              <div className="mb-4">
                <span className="text-sm text-muted-foreground">
                  Showing {data.logs.length} recent audit logs
                </span>
              </div>
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {data.logs.map((log) => {
                  const info = eventLabels[log.event_type] || {
                    label: log.event_type,
                    icon: <FileText size={16} />,
                    color: "bg-gray-500",
                  };
                  return (
                    <div
                      key={log.id}
                      className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50"
                    >
                      <div className={`p-2 rounded-lg ${info.color} text-white flex-shrink-0`}>
                        {info.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium">{info.label}</span>
                          {getStatusIcon(log.status)}
                          <span className="text-xs text-muted-foreground">
                            {timeAgo(log.timestamp)}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {formatTimestamp(log.timestamp)}
                        </div>
                        {log.user_id && (
                          <div className="text-xs text-muted-foreground">
                            User: {log.user_id.slice(0, 12)}...
                          </div>
                        )}
                        {log.resource_id && (
                          <div className="text-xs text-muted-foreground">
                            Resource: {log.resource_type}:{log.resource_id}
                          </div>
                        )}
                        {log.thread_id && (
                          <div className="text-xs text-muted-foreground">
                            Thread:{" "}
                            <a
                              href={`/thread/${log.thread_id}`}
                              className="text-blue-500 hover:underline"
                            >
                              {log.thread_id.slice(0, 8)}...
                            </a>
                          </div>
                        )}
                        {log.ip_address && (
                          <div className="text-xs text-muted-foreground">
                            IP: {log.ip_address}
                          </div>
                        )}
                        {log.error_message && (
                          <div className="text-sm text-red-500 mt-1">
                            Error: {log.error_message}
                          </div>
                        )}
                        {Object.keys(log.details || {}).length > 0 && (
                          <details className="mt-1">
                            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                              View Details
                            </summary>
                            <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-x-auto max-h-32">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}
