from typing import List, Dict, Optional, Set
from models import (
    Post,
    AgentRun,
    Thread,
    TimelinePost,
    User,
    AuthorType,
    AgentStatus,
    UserStats,
)
from agents import extract_mentions
import uuid
from datetime import datetime


# Import audit service lazily to avoid circular imports
def _get_audit_service():
    from services.audit_service import audit_service
    return audit_service


class DataStore:
    """In-memory data store for posts, threads, and agent runs"""

    def __init__(self):
        self.posts: Dict[str, Post] = {}
        self.agent_runs: Dict[str, AgentRun] = {}
        self.likes: Dict[str, Set[str]] = {}  # post_id -> set of user_ids who liked
        self.current_user = User(id="user_1", display_name="You", handle="@me")

    def create_post(self, text: str, parent_id: Optional[str] = None) -> Post:
        """Create a new post"""
        post_id = str(uuid.uuid4())

        # Extract mentions
        mentions = extract_mentions(text)

        # Determine thread_id
        if parent_id:
            parent_post = self.posts.get(parent_id)
            thread_id = parent_post.thread_id if parent_post else post_id
        else:
            thread_id = post_id

        post = Post(
            id=post_id,
            author_type=AuthorType.HUMAN,
            author_handle="@me",
            text=text,
            created_at=datetime.now(),
            parent_id=parent_id,
            thread_id=thread_id,
            mentions=mentions,
        )

        self.posts[post_id] = post

        # Log to audit service
        try:
            audit = _get_audit_service()
            audit.log_post_create(
                post_id=post_id,
                user_id=self.current_user.id,
                text=text,
                thread_id=thread_id,
                parent_id=parent_id,
            )
            # Update conversation audit
            audit.update_conversation_audit(
                thread_id=thread_id, participant_id=self.current_user.id
            )
        except Exception:
            # Don't fail post creation if audit logging fails
            pass

        return post

    def create_agent_reply(
        self, agent_handle: str, text: str, parent_id: str, thread_id: str
    ) -> Post:
        """Create a reply post from an agent"""
        post_id = str(uuid.uuid4())

        post = Post(
            id=post_id,
            author_type=AuthorType.AGENT,
            author_handle=agent_handle,
            text=text,
            created_at=datetime.now(),
            parent_id=parent_id,
            thread_id=thread_id,
            mentions=[],
        )

        self.posts[post_id] = post
        return post

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread with all replies"""
        root_post = self.posts.get(thread_id)
        if not root_post:
            return None

        # Get all replies in this thread
        replies = [
            post
            for post in self.posts.values()
            if post.thread_id == thread_id and post.id != thread_id
        ]

        # Sort by creation time
        replies.sort(key=lambda p: p.created_at)

        return Thread(root_post=root_post, replies=replies)

    def get_timeline_posts(
        self, limit: int = 50, user_id: Optional[str] = None
    ) -> List[TimelinePost]:
        """Get timeline posts (root posts only) with reply counts"""
        # Get all root posts (no parent_id)
        root_posts = [post for post in self.posts.values() if post.parent_id is None]

        # Sort by creation time (newest first)
        root_posts.sort(key=lambda p: p.created_at, reverse=True)

        # Add reply counts and like info
        timeline_posts = []
        for post in root_posts[:limit]:
            reply_count = len(
                [
                    p
                    for p in self.posts.values()
                    if p.thread_id == post.id and p.id != post.id
                ]
            )
            like_count = len(self.likes.get(post.id, set()))
            is_liked = bool(user_id and user_id in self.likes.get(post.id, set()))
            timeline_post = TimelinePost(
                **post.dict(exclude={"like_count", "is_liked"}),
                reply_count=reply_count,
                like_count=like_count,
                is_liked=is_liked,
            )
            timeline_posts.append(timeline_post)

        return timeline_posts

    def create_agent_run(
        self, agent_handle: str, trigger_post_id: str, thread_id: str
    ) -> AgentRun:
        """Create a new agent run record"""
        run_id = str(uuid.uuid4())

        trigger_post = self.posts.get(trigger_post_id)
        agent_run = AgentRun(
            id=run_id,
            agent_handle=agent_handle,
            thread_id=thread_id,
            trigger_post_id=trigger_post_id,
            status=AgentStatus.QUEUED,
            started_at=datetime.now(),
            input_context={"trigger_text": trigger_post.text if trigger_post else ""},
        )

        self.agent_runs[run_id] = agent_run
        return agent_run

    def update_agent_run_status(
        self, run_id: str, status: AgentStatus, output_post_id: Optional[str] = None
    ):
        """Update agent run status"""
        if run_id in self.agent_runs:
            self.agent_runs[run_id].status = status
            self.agent_runs[run_id].ended_at = datetime.now()
            if output_post_id:
                self.agent_runs[run_id].output_post_id = output_post_id

    def get_agent_run(self, run_id: str) -> Optional[AgentRun]:
        """Get agent run by ID"""
        return self.agent_runs.get(run_id)

    def get_active_agent_runs(self, thread_id: str) -> List[AgentRun]:
        """Get active agent runs for a thread"""
        return [
            run
            for run in self.agent_runs.values()
            if run.thread_id == thread_id
            and run.status in [AgentStatus.QUEUED, AgentStatus.RUNNING]
        ]

    def get_thread_context(self, thread_id: str, max_posts: int = 10) -> List[Dict]:
        """Get context (recent posts) from a thread"""
        thread = self.get_thread(thread_id)
        if not thread:
            return []

        # Get all posts in thread
        all_posts = [thread.root_post] + thread.replies
        all_posts.sort(key=lambda p: p.created_at)

        # Return recent posts as dicts for context
        return [
            {
                "author": post.author_handle,
                "text": post.text,
                "timestamp": post.created_at.isoformat(),
                "type": post.author_type.value,
            }
            for post in all_posts[-max_posts:]
        ]

    # ==================== LIKE METHODS ====================

    def like_post(self, post_id: str, user_id: str) -> bool:
        """Like a post. Returns True if post was liked, False if already liked."""
        if post_id not in self.likes:
            self.likes[post_id] = set()
        if user_id in self.likes[post_id]:
            return False  # Already liked
        self.likes[post_id].add(user_id)
        return True

    def unlike_post(self, post_id: str, user_id: str) -> bool:
        """Unlike a post. Returns True if post was unliked, False if not liked."""
        if post_id not in self.likes:
            return False  # No likes on this post
        if user_id not in self.likes[post_id]:
            return False  # User hasn't liked this post
        self.likes[post_id].remove(user_id)
        return True

    def get_post_likes(self, post_id: str, user_id: Optional[str] = None) -> Dict:
        """Get like count and user's like status for a post."""
        likes = self.likes.get(post_id, set())
        return {
            "like_count": len(likes),
            "is_liked": user_id in likes if user_id else False,
        }

    # ==================== DELETE METHOD ====================

    def delete_post(self, post_id: str, user_id: str) -> bool:
        """Delete a post. Only the author can delete their own posts."""
        post = self.posts.get(post_id)
        if not post:
            return False
        # In a real app, check if user_id matches post.author
        # For now, allow deletion of any post
        if post_id in self.posts:
            del self.posts[post_id]
        # Also remove from likes
        if post_id in self.likes:
            del self.likes[post_id]
        return True

    # ==================== USER STATS METHODS ====================

    def get_user_stats(self, user_id: str) -> UserStats:
        """Get statistics for a user."""
        user_posts = [
            p for p in self.posts.values() if p.author_type == AuthorType.HUMAN
        ]
        post_count = len(user_posts)
        reply_count = len([p for p in user_posts if p.parent_id is not None])

        # Count total likes on user's posts
        like_count = sum(len(self.likes.get(post.id, set())) for post in user_posts)

        return UserStats(
            user_id=user_id,
            post_count=post_count,
            like_count=like_count,
            reply_count=reply_count,
        )

    def get_user_posts(self, user_id: str, limit: int = 50) -> List[Post]:
        """Get posts by a specific user."""
        all_posts = [
            p for p in self.posts.values() if p.author_type == AuthorType.HUMAN
        ]
        all_posts.sort(key=lambda p: p.created_at, reverse=True)
        return all_posts[:limit]


# Global store instance
store = DataStore()
