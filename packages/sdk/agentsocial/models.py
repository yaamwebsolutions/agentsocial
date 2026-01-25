"""
Data models for AgentSocial
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AuthorType:
    """Author type constants"""
    HUMAN = "human"
    AGENT = "agent"


class Post(BaseModel):
    """A post in the social network"""
    id: str
    text: str
    author_handle: str
    author_type: str
    created_at: datetime
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    mentions: Optional[List[str]] = None
    like_count: int = 0
    is_liked: bool = False


class TimelinePost(Post):
    """A post in the timeline with additional metadata"""
    reply_count: int = 0
    agent_runs: List["AgentRun"] = []


class Thread(BaseModel):
    """A thread containing a root post and replies"""
    id: str
    root_post: Post
    replies: List[Post]


class Agent(BaseModel):
    """An AI agent configuration"""
    id: str
    handle: str
    name: str
    role: str
    policy: str = ""
    style: str = ""
    color: str = "#FF6B00"
    enabled: bool = True


class AgentRun(BaseModel):
    """An agent execution run"""
    id: str
    agent_handle: str
    status: str
    thread_id: str
    trigger_post_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    input_context: Optional[Dict[str, Any]] = None
    output_post_id: Optional[str] = None
    trace: Dict[str, Any] = {}


class User(BaseModel):
    """A user in the system"""
    id: str
    handle: str
    display_name: str
    email: Optional[str] = None
    github_login: Optional[str] = None


class CreatePostRequest(BaseModel):
    """Request to create a post"""
    text: str
    mentions: List[str] = []
    parent_id: Optional[str] = None


class CreatePostResponse(BaseModel):
    """Response from creating a post"""
    id: str
    text: str
    author_handle: str
    created_at: datetime
    thread_id: Optional[str] = None
