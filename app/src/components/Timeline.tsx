import { useTimeline } from "@/hooks/useApi";
import { ComposerBox } from "./ComposerBox";
import { PostCard } from "./PostCard";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function Timeline() {
  const { posts, loading, error, refetch } = useTimeline(50);
  const [refreshing, setRefreshing] = useState(false);

  const handlePostCreated = () => {
    refetch();
  };

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

      {/* Posts */}
      <div className="divide-y divide-border/30">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>

      {posts.length === 0 && !loading && (
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
