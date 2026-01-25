import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageCircle, Clock, Bot, Loader2, Sparkles, Heart, Trash2 } from "lucide-react";
import type { Post, TimelinePost, AgentRun } from "@/types/api";
import { likePost, unlikePost, deletePost } from "@/hooks/useApi";
import { useAgents } from "@/hooks/useApi";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface PostCardProps {
  post: Post | TimelinePost;
  isReply?: boolean;
  agentRuns?: AgentRun[];
  showThread?: boolean;
  onLike?: (postId: string, newLikeState: boolean) => void;
  onDelete?: (postId: string) => void;
}

export function PostCard({
  post,
  isReply = false,
  agentRuns = [],
  showThread = true,
  onLike,
  onDelete
}: PostCardProps) {
  const navigate = useNavigate();
  const { agents } = useAgents();
  const { theme } = useTheme();
  const { isAuthenticated } = useAuth();

  const [isLiked, setIsLiked] = useState(post.is_liked || false);
  const [likeCount, setLikeCount] = useState(post.like_count || 0);
  const [isLiking, setIsLiking] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isAgent = post.author_type === "agent";
  const timelinePost = post as TimelinePost;
  const hasReplies = timelinePost.reply_count > 0;
  const isDark = theme === "dark";

  // Find agent info
  const agentInfo = agents?.find((a) => a.handle === post.author_handle);

  // Format timestamp
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    if (days < 7) return `${days}d`;
    return date.toLocaleDateString();
  };

  const handleLike = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAuthenticated || isLiking) return;

    setIsLiking(true);
    try {
      if (isLiked) {
        const result = await unlikePost(post.id);
        setIsLiked(result.is_liked);
        setLikeCount(result.like_count);
      } else {
        const result = await likePost(post.id);
        setIsLiked(result.is_liked);
        setLikeCount(result.like_count);
      }
      onLike?.(post.id, !isLiked);
    } catch (error) {
      console.error("Failed to toggle like:", error);
    } finally {
      setIsLiking(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAuthenticated || isDeleting) return;

    if (!confirm("Are you sure you want to delete this post?")) return;

    setIsDeleting(true);
    try {
      await deletePost(post.id);
      onDelete?.(post.id);
    } catch (error) {
      console.error("Failed to delete post:", error);
      setIsDeleting(false);
    }
  };

  // Get agent gradient
  const getAgentGradient = (color: string) => {
    return `linear-gradient(135deg, ${color}, ${color}cc)`;
  };

  // Check if text contains markdown
  const hasMarkdown = (text: string) => {
    return /(```|`|\*\*|\*|##|#|^-\s|^(\d+)\.\s)/.test(text);
  };

  // Highlight mentions in text (for non-markdown content)
  const renderTextWithMentions = (text: string) => {
    const parts = text.split(/(@[a-zA-Z0-9_]+)/g);
    return parts.map((part, index) => {
      if (part.startsWith("@")) {
        const agent = agents?.find((a) => a.handle === part);
        if (agent) {
          return (
            <span
              key={index}
              className="font-semibold cursor-pointer hover:underline transition-all"
              style={{ color: agent.color }}
            >
              {part}
            </span>
          );
        }
        return (
          <span key={index} className="font-semibold text-primary">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const handleClick = () => {
    if (!isReply && showThread) {
      navigate(`/thread/${post.id}`);
    }
  };

  return (
    <Card
      className={`border-0 rounded-2xl overflow-hidden transition-all duration-300 ${
        isReply
          ? "border-l-2 border-l-primary/30 bg-transparent"
          : "bg-card/50 hover:bg-card/80 hover:shadow-xl hover:shadow-primary/5 border border-transparent hover:border-border/50"
      } ${showThread && !isReply ? "cursor-pointer" : ""}`}
      onClick={handleClick}
    >
      <div className="p-5">
        <div className="flex gap-4">
          {/* Enhanced Avatar */}
          <div className="flex-shrink-0">
            {isAgent ? (
              <div className="relative group">
                <div
                  className="w-12 h-12 rounded-2xl flex items-center justify-center text-white text-xl shadow-lg transition-all duration-300 group-hover:scale-105"
                  style={{
                    background: getAgentGradient(agentInfo?.color || "#3B82F6"),
                  }}
                >
                  {agentInfo?.icon || <Bot className="w-6 h-6" />}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full border-2 border-card" />
                <div className="absolute inset-0 rounded-2xl bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            ) : (
              <div className="relative group">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white font-bold text-lg shadow-lg transition-all duration-300 group-hover:scale-105 ${
                  isDark
                    ? "bg-gradient-to-br from-amber-400 to-yellow-600"
                    : "bg-gradient-to-br from-blue-400 to-blue-600"
                }`}>
                  Y
                </div>
                <div className="absolute inset-0 rounded-2xl bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Enhanced Header */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-base">
                {isAgent ? agentInfo?.name || post.author_handle : "You"}
              </span>
              <span className="text-muted-foreground text-sm">
                {post.author_handle}
              </span>
              <span className="text-muted-foreground/50 text-sm">·</span>
              <span className="text-muted-foreground text-sm flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTime(post.created_at)}
              </span>

              {/* Enhanced Agent Badge */}
              {isAgent && (
                <Badge
                  variant="secondary"
                  className="text-xs font-medium ml-1 gap-1 px-2.5 py-0.5"
                  style={{
                    backgroundColor: `${agentInfo?.color}20`,
                    color: agentInfo?.color,
                    border: `1px solid ${agentInfo?.color}30`,
                  }}
                >
                  <Sparkles className="w-3 h-3" />
                  AI Agent
                </Badge>
              )}
            </div>

            {/* Enhanced Text - with Markdown support for agents */}
            <div className="mt-3 text-base leading-relaxed break-words">
              {isAgent && hasMarkdown(post.text) ? (
                <MarkdownRenderer content={post.text} />
              ) : (
                <p className="whitespace-pre-wrap">{renderTextWithMentions(post.text)}</p>
              )}
            </div>

            {/* Enhanced Mention Badges */}
            {post.mentions.length > 0 && (
              <div className="flex gap-2 mt-3 flex-wrap">
                {post.mentions.map((mention) => {
                  const agent = agents?.find((a) => a.handle === `@${mention}`);
                  if (!agent) return null;
                  return (
                    <Badge
                      key={mention}
                      variant="outline"
                      className="text-xs font-medium gap-1.5 px-3 py-1 rounded-full transition-all hover:scale-105 cursor-pointer"
                      style={{
                        borderColor: `${agent.color}40`,
                        backgroundColor: `${agent.color}15`,
                        color: agent.color,
                      }}
                    >
                      <span className="text-sm">{agent.icon}</span>
                      {agent.handle}
                    </Badge>
                  );
                })}
              </div>
            )}

            {/* Agent runs status */}
            {agentRuns.length > 0 && (
              <div className="mt-4 space-y-2">
                {agentRuns.map((run) => {
                  const runAgent = agents?.find((a) => a.handle === run.agent_handle);
                  return (
                    <div
                      key={run.id}
                      className="flex items-center gap-2 text-sm p-2.5 rounded-xl bg-muted/30 backdrop-blur-sm"
                      style={{
                        borderLeft: `3px solid ${runAgent?.color || "#3B82F6"}`,
                      }}
                    >
                      {run.status === "queued" && (
                        <>
                          <div className="relative">
                            <div className="w-3 h-3 rounded-full bg-yellow-500 animate-pulse" />
                            <div className="absolute inset-0 w-3 h-3 rounded-full bg-yellow-500 animate-ping opacity-50" />
                          </div>
                          <span className="text-muted-foreground">
                            <span className="font-medium" style={{ color: runAgent?.color }}>
                              {runAgent?.name}
                            </span>{" "}
                            is thinking...
                          </span>
                        </>
                      )}
                      {run.status === "running" && (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" style={{ color: runAgent?.color }} />
                          <span className="text-muted-foreground">
                            <span className="font-medium" style={{ color: runAgent?.color }}>
                              {runAgent?.name}
                            </span>{" "}
                            is responding...
                          </span>
                        </>
                      )}
                      {run.status === "done" && (
                        <>
                          <div className="w-3 h-3 rounded-full bg-green-500 shadow-lg shadow-green-500/50" />
                          <span className="text-muted-foreground">
                            <span className="font-medium" style={{ color: runAgent?.color }}>
                              {runAgent?.name}
                            </span>{" "}
                            responded
                          </span>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4">
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-primary gap-2 rounded-full px-4 h-9 transition-all hover:bg-primary/10"
                onClick={(e) => {
                  e.stopPropagation();
                  if (!isReply && showThread) {
                    navigate(`/thread/${post.id}`);
                  }
                }}
              >
                <MessageCircle className="w-4 h-4" />
                {hasReplies ? <span className="font-medium">{timelinePost.reply_count}</span> : <span>Reply</span>}
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className={`gap-2 rounded-full px-4 h-9 transition-all ${
                  isLiked
                    ? "text-red-500 hover:text-red-600 hover:bg-red-50"
                    : "text-muted-foreground hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20"
                }`}
                onClick={handleLike}
                disabled={isLiking || !isAuthenticated}
              >
                <Heart className={`w-4 h-4 transition-transform ${isLiked ? "fill-current scale-110" : ""} ${isLiking ? "animate-pulse" : ""}`} />
                <span className="font-medium">{likeCount}</span>
              </Button>

              {!isAgent && isAuthenticated && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive gap-2 rounded-full px-3 h-9 transition-all hover:bg-destructive/10"
                  onClick={handleDelete}
                  disabled={isDeleting}
                >
                  <Trash2 className={`w-4 h-4 ${isDeleting ? "animate-pulse" : ""}`} />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
