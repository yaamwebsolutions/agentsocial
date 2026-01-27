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


# =============================================================================
# AUDIT TRAIL MODELS
# =============================================================================


class AuditEventType(str, Enum):
    """Types of audit events"""

    # Post events
    POST_CREATE = "post_create"
    POST_DELETE = "post_delete"
    POST_LIKE = "post_like"
    POST_UNLIKE = "post_unlike"

    # Agent events
    AGENT_RUN_START = "agent_run_start"
    AGENT_RUN_COMPLETE = "agent_run_complete"
    AGENT_RUN_ERROR = "agent_run_error"

    # Media generation events
    MEDIA_VIDEO_GENERATE = "media_video_generate"
    MEDIA_IMAGE_GENERATE = "media_image_generate"
    MEDIA_SEARCH = "media_search"

    # Authentication events
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"

    # Command execution events
    COMMAND_EXECUTED = "command_executed"
    COMMAND_FAILED = "command_failed"

    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_STARTUP = "system_startup"


class AuditLog(BaseModel):
    """Enterprise-grade audit log entry"""

    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Resource information
    resource_type: Optional[str] = None  # e.g., "post", "agent_run", "media"
    resource_id: Optional[str] = None

    # Event details
    details: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"  # success, failed, pending
    error_message: Optional[str] = None

    # Related resources for traceability
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    agent_run_id: Optional[str] = None


class MediaAsset(BaseModel):
    """Track generated media assets (videos, images)"""

    id: str
    created_at: datetime
    asset_type: Literal["video", "image"]  # type of media
    url: str  # URL to the generated media
    prompt: str  # The prompt used to generate

    # Generation metadata
    generated_by: str  # user_id or "system"
    service: str  # e.g., "klingai", "pexels"
    thread_id: Optional[str] = None  # Related conversation
    post_id: Optional[str] = None  # Post containing the media

    # Additional metadata
    duration_seconds: Optional[int] = None  # For videos
    thumbnail_url: Optional[str] = None
    status: str = "ready"  # ready, processing, failed


class ConversationAudit(BaseModel):
    """Audit trail for conversations/threads"""

    id: str
    thread_id: str
    created_at: datetime
    updated_at: datetime

    # Participants
    participant_ids: List[str] = Field(default_factory=list)
    agent_handles: List[str] = Field(default_factory=list)

    # Statistics
    message_count: int = 0
    human_message_count: int = 0
    agent_message_count: int = 0

    # Media generated in this conversation
    media_assets: List[str] = Field(default_factory=list)  # MediaAsset IDs

    # Commands executed
    commands_executed: List[str] = Field(default_factory=list)

    # Status
    status: str = "active"  # active, archived


class AuditTrailResponse(BaseModel):
    """Response model for audit trail queries"""

    logs: List[AuditLog]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class AuditFilters(BaseModel):
    """Filters for audit trail queries"""

    event_type: Optional[AuditEventType] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    thread_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


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
