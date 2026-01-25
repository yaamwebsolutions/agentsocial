from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum

class AuthorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"

class AgentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

class Agent(BaseModel):
    id: str
    handle: str
    name: str
    role: str
    policy: str
    style: str
    tools: List[str] = Field(default_factory=list)
    color: str = "#3B82F6"
    icon: str = "🤖"
    mock_responses: List[str] = Field(default_factory=list)

class User(BaseModel):
    id: str
    display_name: str
    handle: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserStats(BaseModel):
    user_id: str
    post_count: int
    like_count: int
    reply_count: int

class Post(BaseModel):
    id: str
    author_type: AuthorType
    author_handle: str
    text: str
    created_at: datetime
    parent_id: Optional[str] = None
    thread_id: str
    mentions: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    like_count: int = 0
    is_liked: bool = False

class AgentRun(BaseModel):
    id: str
    agent_handle: str
    thread_id: str
    trigger_post_id: str
    status: AgentStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    input_context: Dict[str, Any] = Field(default_factory=dict)
    output_post_id: Optional[str] = None
    trace: Dict[str, Any] = Field(default_factory=dict)

class Thread(BaseModel):
    root_post: Post
    replies: List[Post]

class TimelinePost(Post):
    reply_count: int = 0

class CreatePostRequest(BaseModel):
    text: str
    parent_id: Optional[str] = None

class CreatePostResponse(BaseModel):
    post: Post
    triggered_agent_runs: List[AgentRun]
