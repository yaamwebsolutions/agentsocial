import { useTimeline } from "@/hooks/useApi";
import { ComposerBox } from "./ComposerBox";
import { PostCard } from "./PostCard";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useCallback } from "react";
import type { Post, AgentRun } from "@/types/api";
import { useAgents } from "@/hooks/useApi";

export function Timeline() {
  const { posts, loading, error, refetch } = useTimeline(50);
  const { agents } = useAgents();
  const [refreshing, setRefreshing] = useState(false);
  // Optimistic state for instant feedback
  const [optimisticPosts, setOptimisticPosts] = useState<Post[]>([]);
  const [optimisticAgentRuns, setOptimisticAgentRuns] = useState<Record<string, AgentRun[]>>({});

  // Combine actual posts with optimistic posts
  const displayPosts = [...optimisticPosts, ...posts];

  const handlePostCreated = useCallback((post: Post) => {
    // Extract mentions from the post
    const mentions = post.mentions || [];
    const agentHandles = mentions.map(m => `@${m}`);

    // Find agent info for mentions
    const mentionedAgents = agents?.filter(a => agentHandles.includes(a.handle)) || [];

    // Create optimistic agent runs for mentioned agents
    if (mentionedAgents.length > 0) {
      const newAgentRuns: AgentRun[] = mentionedAgents.map(agent => ({
        id: `optimistic-${Date.now()}-${agent.id}`,
        agent_handle: agent.handle,
        thread_id: post.thread_id || post.id,
        trigger_post_id: post.id,
        status: "queued",
        started_at: new Date().toISOString(),
        ended_at: undefined,
        input_context: { trigger_text: post.text },
        output_post_id: undefined,
        trace: {},
      }));

      setOptimisticAgentRuns(prev => ({
        ...prev,
        [post.id]: newAgentRuns,
      }));
    }

    // Add to optimistic posts (will be replaced when real data comes back)
    setOptimisticPosts(prev => [post, ...prev]);

    // Refresh to get real data
    refetch();

    // Clear optimistic state after a short delay (real data should be back)
    setTimeout(() => {
      setOptimisticPosts([]);
      setOptimisticAgentRuns({});
    }, 3000);
  }, [agents, refetch]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  if (loading && posts.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Composer */}
      <div className="p-4 border-b border-border/50">
        <ComposerBox onPostCreated={handlePostCreated} />
      </div>

      {/* Refresh button */}
      <div className="p-2 border-b border-border/50 flex justify-center">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
          className="text-muted-foreground hover:text-primary"
        >
          {refreshing ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>

      {/* Posts - using displayPosts for optimistic updates */}
      <div className="divide-y divide-border/30">
        {displayPosts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            agentRuns={optimisticAgentRuns[post.id] || []}
          />
        ))}
      </div>

      {displayPosts.length === 0 && !loading && (
        <div className="p-8 text-center text-muted-foreground">
          No posts yet. Be the first to post!
          <br />
          <span className="text-sm mt-2 block">
            Try mentioning @grok, @dev, or @writer
          </span>
        </div>
      )}

      {error && (
        <div className="p-8 text-center text-destructive">
          Failed to load posts. Try refreshing.
        </div>
      )}
    </div>
  );
}
