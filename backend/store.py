from typing import List, Dict, Optional
from models import Post, AgentRun, Thread, TimelinePost, User, AuthorType, AgentStatus
from agents import extract_mentions
import uuid
from datetime import datetime

class DataStore:
    """In-memory data store for posts, threads, and agent runs"""
    
    def __init__(self):
        self.posts: Dict[str, Post] = {}
        self.agent_runs: Dict[str, AgentRun] = {}
        self.current_user = User(
            id="user_1",
            display_name="You",
            handle="@me"
        )
    
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
            mentions=mentions
        )
        
        self.posts[post_id] = post
        return post
    
    def create_agent_reply(self, agent_handle: str, text: str, parent_id: str, thread_id: str) -> Post:
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
            mentions=[]
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
            post for post in self.posts.values()
            if post.thread_id == thread_id and post.id != thread_id
        ]
        
        # Sort by creation time
        replies.sort(key=lambda p: p.created_at)
        
        return Thread(root_post=root_post, replies=replies)
    
    def get_timeline_posts(self, limit: int = 50) -> List[TimelinePost]:
        """Get timeline posts (root posts only) with reply counts"""
        # Get all root posts (no parent_id)
        root_posts = [
            post for post in self.posts.values()
            if post.parent_id is None
        ]
        
        # Sort by creation time (newest first)
        root_posts.sort(key=lambda p: p.created_at, reverse=True)
        
        # Add reply counts
        timeline_posts = []
        for post in root_posts[:limit]:
            reply_count = len([
                p for p in self.posts.values()
                if p.thread_id == post.id and p.id != post.id
            ])
            timeline_post = TimelinePost(**post.dict(), reply_count=reply_count)
            timeline_posts.append(timeline_post)
        
        return timeline_posts
    
    def create_agent_run(self, agent_handle: str, trigger_post_id: str, thread_id: str) -> AgentRun:
        """Create a new agent run record"""
        run_id = str(uuid.uuid4())
        
        agent_run = AgentRun(
            id=run_id,
            agent_handle=agent_handle,
            thread_id=thread_id,
            trigger_post_id=trigger_post_id,
            status=AgentStatus.QUEUED,
            started_at=datetime.now(),
            input_context={"trigger_text": self.posts.get(trigger_post_id, {}).text}
        )
        
        self.agent_runs[run_id] = agent_run
        return agent_run
    
    def update_agent_run_status(self, run_id: str, status: AgentStatus, output_post_id: Optional[str] = None):
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
            run for run in self.agent_runs.values()
            if run.thread_id == thread_id and run.status in [AgentStatus.QUEUED, AgentStatus.RUNNING]
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
                "type": post.author_type.value
            }
            for post in all_posts[-max_posts:]
        ]

# Global store instance
store = DataStore()
