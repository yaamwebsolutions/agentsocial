import { useParams, useNavigate } from "react-router-dom";
import { useThread, useThreadAgentRuns } from "@/hooks/useApi";
import { useSSE } from "@/hooks/useSSE";
import { ComposerBox } from "./ComposerBox";
import { PostCard } from "./PostCard";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, Wifi, WifiOff } from "lucide-react";
import { useState, useCallback } from "react";
import type { AgentRun, Post } from "@/types/api";

export function ThreadView() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const { thread, loading, error, refetch } = useThread(threadId || "");
  const { runs, refetch: refetchRuns } = useThreadAgentRuns(threadId || "");

  // Local state for SSE-managed data
  const [sseAgentRuns, setSseAgentRuns] = useState<AgentRun[]>([]);
  const [ssePosts, setSsePosts] = useState<Post[]>([]);

  // SSE connection
  const { isConnected: sseConnected } = useSSE(threadId || "", {
    onAgentRun: useCallback((run: AgentRun) => {
      setSseAgentRuns((prev) => {
        // Avoid duplicates
        if (prev.some((r) => r.id === run.id)) return prev;
        return [...prev, run];
      });
    }, []),

    onAgentStatusChange: useCallback((run: AgentRun) => {
      setSseAgentRuns((prev) =>
        prev.map((r) => (r.id === run.id ? run : r))
      );
      // Refetch when agent completes
      if (run.status === "done" || run.status === "error") {
        refetch();
      }
    }, [refetch]),

    onNewPost: useCallback((post: Post) => {
      setSsePosts((prev) => {
        // Avoid duplicates
        if (prev.some((p) => p.id === post.id)) return prev;
        return [...prev, post];
      });
      refetch();
    }, [refetch]),
  });

  // Merge SSE and polling data
  const allAgentRuns = useCallback(() => {
    const runMap = new Map<string, AgentRun>();

    // Add polling runs
    runs.forEach((run) => runMap.set(run.id, run));

    // Override with SSE runs (more up-to-date)
    sseAgentRuns.forEach((run) => runMap.set(run.id, run));

    return Array.from(runMap.values());
  }, [runs, sseAgentRuns]);

  const displayAgentRuns = allAgentRuns();

  const handleReplyCreated = () => {
    refetch();
    refetchRuns();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !thread) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">Thread not found</p>
        <Button onClick={() => navigate("/")}>Go back home</Button>
      </div>
    );
  }

  // Merge SSE posts with thread posts
  const allPosts = [
    thread.root_post,
    ...thread.replies,
    ...ssePosts.filter((p) =>
      !thread.replies.some((r) => r.id === p.id) && p.id !== thread.root_post.id
    ),
  ];

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header with SSE connection indicator */}
      <div className="sticky top-0 z-10 bg-background/80 backdrop-blur border-b border-border/50 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/")}
              className="rounded-full"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-xl font-semibold">Thread</h1>
          </div>
          <div
            className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full ${
              sseConnected
                ? "bg-green-500/10 text-green-600 dark:text-green-400"
                : "bg-muted text-muted-foreground"
            }`}
            title={sseConnected ? "Live updates connected" : "Using polling fallback"}
          >
            {sseConnected ? (
              <>
                <Wifi className="w-3 h-3" />
                Live
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                Polling
              </>
            )}
          </div>
        </div>
      </div>

      {/* Root Post */}
      <div className="border-b border-border/50">
        <PostCard post={thread.root_post} agentRuns={displayAgentRuns} />
      </div>

      {/* Reply Composer */}
      <div className="p-4 border-b border-border/50">
        <ComposerBox
          parentId={thread.root_post.id}
          onPostCreated={handleReplyCreated}
          placeholder="Post your reply"
        />
      </div>

      {/* Replies */}
      <div className="divide-y divide-border/30">
        {allPosts.map((post) => {
          const isReply = post.id !== thread.root_post.id;
          return (
            <PostCard
              key={post.id}
              post={post}
              isReply={isReply}
              agentRuns={isReply ? [] : displayAgentRuns}
            />
          );
        })}
      </div>

      {thread.replies.length === 0 && ssePosts.length === 0 && (
        <div className="p-8 text-center text-muted-foreground">
          No replies yet. Be the first to reply!
        </div>
      )}
    </div>
  );
}
