import { useParams, useNavigate } from "react-router-dom";
import { useUserActivity } from "@/hooks/useAudit";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  ArrowLeft,
  Activity,
  Calendar,
  Clock,
  MessageSquare,
  Image,
  AlertCircle,
  Globe,
  Monitor,
} from "lucide-react";

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

export function AdminUserActivity() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();

  const { activity, loading, error, refetch } = useUserActivity(userId || "");

  if (!userId) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        <Card className="p-6">
          <p className="text-muted-foreground">No user ID provided.</p>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || !activity) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle size={24} />
            <div>
              <h3 className="font-semibold">Error Loading User Activity</h3>
              <p className="text-sm">{error || "Unknown error"}</p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Header */}
      <div className="mb-6 flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} className="mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">User Activity Report</h1>
          <p className="text-muted-foreground font-mono text-sm">
            ID: {userId}
          </p>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={18} className="text-blue-500" />
            <span className="text-sm text-muted-foreground">Total Actions</span>
          </div>
          <div className="text-2xl font-bold">{activity.total_actions}</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare size={18} className="text-green-500" />
            <span className="text-sm text-muted-foreground">Conversations</span>
          </div>
          <div className="text-2xl font-bold">
            {activity.conversations_created}
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Image size={18} className="text-purple-500" />
            <span className="text-sm text-muted-foreground">Media Generated</span>
          </div>
          <div className="text-2xl font-bold">{activity.media_generated}</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={18} className="text-red-500" />
            <span className="text-sm text-muted-foreground">Errors</span>
          </div>
          <div className="text-2xl font-bold">{activity.errors_encountered}</div>
        </Card>
      </div>

      {/* Timeline */}
      <Card className="p-6 mb-4">
        <h3 className="text-lg font-semibold mb-4">Activity Timeline</h3>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <Calendar size={18} className="text-muted-foreground" />
            <div>
              <div className="text-sm text-muted-foreground">First Seen</div>
              <div className="font-medium">{formatTimestamp(activity.first_seen)}</div>
              <div className="text-xs text-muted-foreground">
                {timeAgo(activity.first_seen)}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Clock size={18} className="text-muted-foreground" />
            <div>
              <div className="text-sm text-muted-foreground">Last Seen</div>
              <div className="font-medium">{formatTimestamp(activity.last_seen)}</div>
              <div className="text-xs text-muted-foreground">
                {timeAgo(activity.last_seen)}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Action Breakdown */}
      <Card className="p-6 mb-4">
        <h3 className="text-lg font-semibold mb-4">Action Breakdown</h3>
        <div className="space-y-2">
          {Object.entries(activity.action_breakdown).map(([action, count]) => (
            <div
              key={action}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <span className="font-medium capitalize">{action.replace(/_/g, " ")}</span>
              <Badge variant="secondary">{count}</Badge>
            </div>
          ))}
          {Object.keys(activity.action_breakdown).length === 0 && (
            <p className="text-sm text-muted-foreground">No actions recorded.</p>
          )}
        </div>
      </Card>

      {/* IP Addresses */}
      {activity.ip_addresses.length > 0 && (
        <Card className="p-6 mb-4">
          <h3 className="text-lg font-semibold mb-4">IP Addresses</h3>
          <div className="flex flex-wrap gap-2">
            {activity.ip_addresses.map((ip) => (
              <Badge key={ip} variant="outline">
                <Globe size={12} className="mr-1" />
                {ip}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* User Agents */}
      {activity.user_agents.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">User Agents</h3>
          <div className="space-y-2">
            {activity.user_agents.map((ua, idx) => (
              <div key={idx} className="p-3 rounded-lg border">
                <div className="flex items-start gap-2">
                  <Monitor size={16} className="text-muted-foreground flex-shrink-0 mt-0.5" />
                  <span className="text-sm font-mono break-all">{ua}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Refresh Button */}
      <div className="mt-4 flex justify-center">
        <Button variant="outline" onClick={refetch}>
          <Activity size={16} className="mr-2" />
          Refresh Data
        </Button>
      </div>
    </div>
  );
}
