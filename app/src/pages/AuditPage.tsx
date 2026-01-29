import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  useAuditLogs,
  useAuditStats,
  useMediaAssets,
  useConversationAudits,
} from "@/hooks/useAudit";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
} from "lucide-react";

const eventLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> =
  {
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

function formatTimestamp(timestamp: string): string {
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

export function AuditPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [page, setPage] = useState(1);

  // Always call hooks (React Rules of Hooks)
  const { logs, loading: logsLoading, refetch: refetchLogs } = useAuditLogs({
    page,
    page_size: 50,
    autoRefresh: isAuthenticated, // Only auto-refresh if authenticated
  });

  const { stats, loading: statsLoading, refetch: refetchStats } = useAuditStats();

  const { assets, loading: assetsLoading, refetch: refetchAssets } = useMediaAssets({
    limit: 50,
  });

  const { conversations, loading: convLoading, refetch: refetchConv } =
    useConversationAudits();

  const handleRefresh = () => {
    refetchLogs();
    refetchStats();
    refetchAssets();
    refetchConv();
  };

  // Require authentication - render auth prompt after hooks
  if (!isAuthenticated) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <Card className="border-0 rounded-2xl bg-muted/30 p-8 text-center">
          <Shield className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-bold mb-2">Authentication Required</h2>
          <p className="text-muted-foreground mb-4">Please log in to access audit trail features.</p>
          <Button onClick={() => navigate("/")}>Back to Home</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">Audit Trail</h1>
          <p className="text-muted-foreground">
            Enterprise-grade activity logs, media assets, and conversation history
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="logs">Activity Logs</TabsTrigger>
          <TabsTrigger value="media">Media Assets</TabsTrigger>
          <TabsTrigger value="conversations">Conversations</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {statsLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid gap-4 md:grid-cols-4">
                <Card className="p-4">
                  <div className="text-2xl font-bold">{stats?.total_logs || 0}</div>
                  <div className="text-sm text-muted-foreground">Total Events</div>
                </Card>
                <Card className="p-4">
                  <div className="text-2xl font-bold">{stats?.video_count || 0}</div>
                  <div className="text-sm text-muted-foreground">Videos Generated</div>
                </Card>
                <Card className="p-4">
                  <div className="text-2xl font-bold">{stats?.image_count || 0}</div>
                  <div className="text-sm text-muted-foreground">Images Generated</div>
                </Card>
                <Card className="p-4">
                  <div className="text-2xl font-bold">
                    {stats?.total_conversations || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Conversations</div>
                </Card>
              </div>

              {/* Event Type Breakdown */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Event Breakdown</h3>
                <div className="space-y-2">
                  {Object.entries(stats?.event_type_counts || {}).map(([type, count]) => {
                    const info = eventLabels[type] || {
                      label: type,
                      icon: <FileText size={16} />,
                      color: "bg-gray-500",
                    };
                    return (
                      <div key={type} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`p-1 rounded ${info.color} text-white`}>
                            {info.icon}
                          </div>
                          <span className="text-sm">{info.label}</span>
                        </div>
                        <Badge variant="secondary">{count as number}</Badge>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Activity Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          {logsLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <Card className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-muted-foreground">
                    Showing {logs?.logs.length || 0} of {logs?.total_count || 0} events
                  </span>
                  {logs && page > 1 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => p - 1)}
                    >
                      Previous
                    </Button>
                  )}
                  {logs?.has_more && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  {logs?.logs.map((log) => {
                    const info = eventLabels[log.event_type] || {
                      label: log.event_type,
                      icon: <FileText size={16} />,
                      color: "bg-gray-500",
                    };
                    return (
                      <div
                        key={log.id}
                        className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                      >
                        <div className={`p-2 rounded-lg ${info.color} text-white flex-shrink-0`}>
                          {info.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium">{info.label}</span>
                            {getStatusIcon(log.status)}
                            <span className="text-xs text-muted-foreground">
                              {formatTimestamp(log.timestamp)}
                            </span>
                          </div>
                          {log.resource_id && (
                            <div className="text-xs text-muted-foreground mt-1">
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
                          {log.error_message && (
                            <div className="text-sm text-red-500 mt-1">
                              Error: {log.error_message}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Media Assets Tab */}
        <TabsContent value="media" className="space-y-4">
          {assetsLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">
                Generated Media ({assets.length})
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                {assets.map((asset) => (
                  <div
                    key={asset.id}
                    className="border rounded-lg p-4 space-y-2 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {asset.asset_type === "video" ? (
                          <Video size={18} className="text-purple-500" />
                        ) : (
                          <Image size={18} className="text-indigo-500" />
                        )}
                        <span className="font-medium capitalize">{asset.asset_type}</span>
                      </div>
                      <Badge variant={asset.status === "ready" ? "default" : "secondary"}>
                        {asset.status}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground line-clamp-2">
                      Prompt: {asset.prompt}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Service: {asset.service} • {formatTimestamp(asset.created_at)}
                    </div>
                    {asset.url && (
                      <a
                        href={asset.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-500 hover:underline flex items-center gap-1"
                      >
                        {asset.asset_type === "video" ? "Watch Video" : "View Image"} →
                      </a>
                    )}
                    {asset.thread_id && (
                      <div className="text-xs text-muted-foreground">
                        From conversation:{" "}
                        <a
                          href={`/thread/${asset.thread_id}`}
                          className="text-blue-500 hover:underline"
                        >
                          {asset.thread_id.slice(0, 8)}...
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {assets.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  No media assets generated yet. Use /image or /video commands to generate
                  media.
                </div>
              )}
            </Card>
          )}
        </TabsContent>

        {/* Conversations Tab */}
        <TabsContent value="conversations" className="space-y-4">
          {convLoading ? (
            <div className="flex justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">
                Conversations ({conversations.length})
              </h3>
              <div className="space-y-3">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <a
                        href={`/thread/${conv.thread_id}`}
                        className="font-medium hover:underline"
                      >
                        {conv.thread_id.slice(0, 12)}...
                      </a>
                      <Badge variant="outline">{conv.status}</Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Messages</div>
                        <div className="font-medium">{conv.message_count}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Agents</div>
                        <div className="font-medium">
                          {conv.agent_handles.length > 0
                            ? conv.agent_handles.join(", ")
                            : "-"}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Media</div>
                        <div className="font-medium">{conv.media_assets.length}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Commands</div>
                        <div className="font-medium">
                          {conv.commands_executed.length > 0
                            ? conv.commands_executed.join(", ")
                            : "-"}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground mt-2">
                      Last active: {formatTimestamp(conv.updated_at)}
                    </div>
                  </div>
                ))}
              </div>
              {conversations.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  No conversations yet. Start a conversation to see it here.
                </div>
              )}
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
