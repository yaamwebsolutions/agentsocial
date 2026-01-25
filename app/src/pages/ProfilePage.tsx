import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, BarChart3, Heart, MessageCircle, ArrowLeft } from "lucide-react";
import { PostCard } from "@/components/PostCard";
import { useUserStats, useUserPosts, useCurrentUser } from "@/hooks/useApi";
import { useNavigate } from "react-router-dom";
import { useTheme } from "@/contexts/ThemeContext";
import type { Post } from "@/types/api";

export function ProfilePage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const { data: currentUser } = useCurrentUser();
  const { stats, loading: statsLoading, error: statsError } = useUserStats(userId || "user_1");
  const { posts, loading: postsLoading, error: postsError, refetch } = useUserPosts(userId || "user_1");

  const isOwnProfile = currentUser?.id === userId;

  if (statsLoading || postsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-6 px-4">
      {/* Header with back button */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="rounded-full"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <h1 className="text-2xl font-bold">
          {isOwnProfile ? "Your Profile" : "User Profile"}
        </h1>
      </div>

      {/* Profile Card */}
      <Card className={`border-0 rounded-2xl overflow-hidden mb-6 ${
        isDark
          ? "bg-gradient-to-br from-amber-500/10 to-yellow-600/10"
          : "bg-gradient-to-br from-blue-500/10 to-blue-600/10"
      }`}>
        <div className="p-6">
          <div className="flex items-center gap-4">
            <div className={`w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg ${
              isDark
                ? "bg-gradient-to-br from-amber-400 to-yellow-600"
                : "bg-gradient-to-br from-blue-400 to-blue-600"
            }`}>
              <User className="w-10 h-10" />
            </div>
            <div>
              <h2 className="text-xl font-bold">{currentUser?.display_name || "User"}</h2>
              <p className="text-muted-foreground">@{currentUser?.handle || "user"}</p>
            </div>
          </div>

          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="text-center p-4 rounded-xl bg-background/50 backdrop-blur-sm">
                <BarChart3 className="w-6 h-6 mx-auto mb-2 text-primary" />
                <div className="text-2xl font-bold">{stats.post_count}</div>
                <div className="text-sm text-muted-foreground">Posts</div>
              </div>
              <div className="text-center p-4 rounded-xl bg-background/50 backdrop-blur-sm">
                <Heart className="w-6 h-6 mx-auto mb-2 text-red-500" />
                <div className="text-2xl font-bold">{stats.like_count}</div>
                <div className="text-sm text-muted-foreground">Likes</div>
              </div>
              <div className="text-center p-4 rounded-xl bg-background/50 backdrop-blur-sm">
                <MessageCircle className="w-6 h-6 mx-auto mb-2 text-primary" />
                <div className="text-2xl font-bold">{stats.reply_count}</div>
                <div className="text-sm text-muted-foreground">Replies</div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Posts */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold px-2">Posts</h3>
        {posts.length === 0 ? (
          <Card className="border-0 rounded-2xl bg-muted/30 p-8 text-center text-muted-foreground">
            No posts yet
          </Card>
        ) : (
          posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              isReply={!!post.parent_id}
              showThread={false}
              onDelete={(deletedId) => {
                // Remove the deleted post from the list
                const updatedPosts = posts.filter((p) => p.id !== deletedId);
                // In a real app, you'd update the parent state
                refetch();
              }}
            />
          ))
        )}
      </div>
    </div>
  );
}
