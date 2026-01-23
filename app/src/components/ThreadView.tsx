import { useParams, useNavigate } from "react-router-dom";
import { useThread, useThreadAgentRuns } from "@/hooks/useApi";
import { ComposerBox } from "./ComposerBox";
import { PostCard } from "./PostCard";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2 } from "lucide-react";

export function ThreadView() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const { thread, loading, error, refetch } = useThread(threadId || "");
  const { runs } = useThreadAgentRuns(threadId || "");

  const handleReplyCreated = () => {
    refetch();
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

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/80 backdrop-blur border-b border-border/50 p-4">
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
      </div>

      {/* Root Post */}
      <div className="border-b border-border/50">
        <PostCard post={thread.root_post} agentRuns={runs} />
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
        {thread.replies.map((reply) => (
          <PostCard
            key={reply.id}
            post={reply}
            isReply={true}
          />
        ))}
      </div>

      {thread.replies.length === 0 && (
        <div className="p-8 text-center text-muted-foreground">
          No replies yet. Be the first to reply!
        </div>
      )}
    </div>
  );
}
