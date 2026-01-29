"""
Agent Twitter API - FastAPI Backend
Main application with environment-based configuration.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import uvicorn
import jwt

from models import (
    Thread,
    TimelinePost,
    Agent,
    CreatePostRequest,
    CreatePostResponse,
    User,
    UserStats,
    AuditEventType,
)
from middleware.audit_middleware import AuditMiddleware
from middleware.auth_middleware import (
    get_current_user,
    get_optional_user,
    get_token_payload,
)
from middleware.admin_middleware import require_admin
from agents import list_agents, get_agent
from store import store
from orchestrator import orchestrator
from config import (
    APP_NAME,
    APP_ENV,
    APP_VERSION,
    BACKEND_HOST,
    BACKEND_PORT,
    CORS_ORIGINS,
    BACKEND_LOG_LEVEL,
    DEEPSEEK_ENABLED,
    DATABASE_ENABLED,
    SERPER_ENABLED,
    SCRAPERAPI_ENABLED,
    KLINGAI_ENABLED,
    RESEND_ENABLED,
    AUTH0_ENABLED,
    GITHUB_ENABLED,
    AUTH_REQUIRED,
    AUTH_REQUIRED_FOR_WRITES,
    print_config,
)
from services import search_web
from services.oauth_state import generate_oauth_state, verify_oauth_state
from services.media_service import media_service
from services.scraping_service import scraping_service
from services.email_service import email_service
from services.llm_service import generate_agent_response
from monitoring import monitoring

# Configure logging
logging.basicConfig(
    level=getattr(logging, BACKEND_LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# API METADATA & DOCUMENTATION
# =============================================================================

tags_metadata = [
    {
        "name": "Posts",
        "description": "Create and retrieve posts and threaded conversations",
    },
    {
        "name": "Agents",
        "description": "Manage AI agents and send direct prompts",
    },
    {
        "name": "Search",
        "description": "Web search and content discovery endpoints",
    },
    {
        "name": "Media",
        "description": "Image and video generation and search",
    },
    {
        "name": "Scraping",
        "description": "Web scraping and content extraction",
    },
    {
        "name": "Email",
        "description": "Email notifications via Resend",
    },
    {
        "name": "Users",
        "description": "User profile and information",
    },
    {
        "name": "Health",
        "description": "Health check and system status",
    },
    {
        "name": "Authentication",
        "description": "GitHub OAuth login and user session management",
    },
    {
        "name": "Audit",
        "description": "Enterprise-grade audit trail and event logging",
    },
]

app = FastAPI(
    title=f"{APP_NAME} API",
    version=APP_VERSION,
    description="""## AI-Powered Twitter-like Platform with Agent Mentions

Agent Twitter allows you to create posts and @mention AI agents to get intelligent responses.

### Features
- **Config-driven Agents**: Add/remove agents without code changes via `agents.json`
- **Multiple Integrations**: LLM, web search, media generation, email notifications
- **Threaded Conversations**: Full discussion thread support
- **Modular Architecture**: Easy to extend with new services

### Quick Start
1. Create a post with an agent mention: `Hello @grok!`
2. The agent will automatically respond
3. Continue the conversation by replying

### Agent Mentions
Supported agents include:
- **@grok** - Generalist AI assistant
- **@factcheck** - Fact-checking and verification
- **@summarizer** - Content summarization
- **@writer** - Content creation and refinement
- **@dev** - Technical problem solving
- **@analyst** - Strategic analysis
- **@researcher** - Information gathering
- **@coach** - Personal development

### Configuration
Agents are configured via `backend/agents.json`. See the [GitHub repo](https://github.com/yourusername/agent-twitter) for details.
""",
    terms_of_service="https://github.com/yourusername/agent-twitter/blob/main/CODE_OF_CONDUCT.md",
    contact={
        "name": "Agent Twitter Contributors",
        "url": "https://github.com/yourusername/agent-twitter",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/yourusername/agent-twitter/blob/main/LICENSE",
    },
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
allow_credentials = "*" not in CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit middleware for automatic request logging
app.add_middleware(AuditMiddleware)


async def require_user(
    payload: Optional[dict] = Depends(get_optional_user),
):
    """
    Require authenticated user if AUTH_REQUIRED is enabled.
    Used for endpoints that should be protected in strict auth mode.
    """
    if AUTH_REQUIRED and not payload:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def require_user_for_write(
    payload: Optional[dict] = Depends(get_optional_user),
):
    """
    Require authenticated user for write operations.
    This is enabled by default (AUTH_REQUIRED_FOR_WRITES=true) to protect
    POST/PUT/DELETE operations while keeping reads public.

    Provides a 401 response with a clear message indicating authentication
    is required to perform write operations.
    """
    if AUTH_REQUIRED_FOR_WRITES and not payload:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to create posts. Please log in first.",
            headers={"WWW-Authenticate": "Bearer", "X-Auth-Required": "write"},
        )
    return payload


# =============================================================================
# REQUEST MODELS
# =============================================================================


class SearchRequest(BaseModel):
    query: str
    num_results: int = 10


class ScrapeRequest(BaseModel):
    url: str
    extract_links: bool = False


class ImageGenerateRequest(BaseModel):
    prompt: str
    image_size: str = "16:9"
    num_images: int = 1


class ImageSearchRequest(BaseModel):
    query: str
    per_page: int = 10
    source: str = "auto"


class EmailSendRequest(BaseModel):
    to: str
    subject: str
    html: str


class VideoGenerateRequest(BaseModel):
    prompt: str
    duration: int = 5


class AgentPromptRequest(BaseModel):
    agent_handle: str
    prompt: str


# =============================================================================
# POSTS ENDPOINTS
# =============================================================================


@app.post("/posts", response_model=CreatePostResponse, tags=["Posts"])
async def create_post(
    request: CreatePostRequest,
    _user: Optional[dict] = Depends(require_user_for_write),
):
    """
    Create a new post and trigger any mentioned agents.

    Agents are mentioned using the @handle syntax (e.g., @grok).
    When agents are mentioned, they will automatically generate responses.

    **Authentication:** Required by default (AUTH_REQUIRED_FOR_WRITES=true)

    - **text**: The post content (supports agent mentions with @)
    - **parent_id**: Optional ID of parent post for replies
    """
    result = await orchestrator.process_post(request.text, request.parent_id)
    return result


@app.get("/threads/{thread_id}", response_model=Thread, tags=["Posts"])
async def get_thread(thread_id: str):
    """
    Get a thread with all replies.

    Returns the root post and all associated replies in chronological order.
    """
    thread = store.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@app.get("/timeline", response_model=List[TimelinePost], tags=["Posts"])
async def get_timeline(
    limit: int = 50, _user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get timeline posts (root posts only).

    Returns the most recent posts in reverse chronological order.
    Use the limit parameter to control the number of results.
    """
    user_id = _user.get("sub") if _user else None
    return store.get_timeline_posts(limit, user_id)


@app.post("/posts/{post_id}/like", tags=["Posts"])
async def like_post(
    post_id: str, _user: Optional[dict] = Depends(require_user_for_write)
):
    """
    Like a post.

    Toggles a like on the specified post. Returns the updated like count and status.
    Requires authentication.
    """
    if not _user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = _user.get("sub", "user_1")
    liked = store.like_post(post_id, user_id)
    like_info = store.get_post_likes(post_id, user_id)

    return {
        "liked": liked,
        "like_count": like_info["like_count"],
        "is_liked": like_info["is_liked"],
    }


@app.post("/posts/{post_id}/unlike", tags=["Posts"])
async def unlike_post(
    post_id: str, _user: Optional[dict] = Depends(require_user_for_write)
):
    """
    Unlike a post.

    Removes a like from the specified post. Returns the updated like count and status.
    Requires authentication.
    """
    if not _user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = _user.get("sub", "user_1")
    unliked = store.unlike_post(post_id, user_id)
    like_info = store.get_post_likes(post_id, user_id)

    return {
        "unliked": unliked,
        "like_count": like_info["like_count"],
        "is_liked": like_info["is_liked"],
    }


@app.delete("/posts/{post_id}", tags=["Posts"])
async def delete_post(
    post_id: str, _user: Optional[dict] = Depends(require_user_for_write)
):
    """
    Delete a post.

    Permanently deletes the specified post. Only the post author can delete their posts.
    Requires authentication.
    """
    if not _user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = _user.get("sub", "user_1")
    success = store.delete_post(post_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Post not found")

    return {"message": "Post deleted successfully"}


# =============================================================================
# AGENTS ENDPOINTS
# =============================================================================


@app.get("/agents", response_model=List[Agent], tags=["Agents"])
async def get_agents():
    """
    List all available agents.

    Returns a list of all configured agents with their metadata including
    name, handle, role, and capabilities.
    """
    return list_agents()


@app.get("/agents/{handle}", response_model=Agent, tags=["Agents"])
async def get_agent_by_handle(handle: str):
    """
    Get a specific agent by handle.

    Returns detailed information about a specific agent including
    its role, policy, style, and available tools.
    """
    agent = get_agent(handle)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/agents/prompt", tags=["Agents"])
async def prompt_agent(request: AgentPromptRequest):
    """
    Send a direct prompt to an agent without creating a post.

    Use this endpoint for one-off interactions with agents that
    don't need to be stored as posts.

    - **agent_handle**: The agent's @handle (with or without @)
    - **prompt**: The message to send to the agent
    """
    agent = get_agent(request.agent_handle.lstrip("@"))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    response = await generate_agent_response(
        agent_name=agent.name,
        agent_role=agent.role,
        agent_style=agent.style,
        agent_policy=agent.policy,
        user_message=request.prompt,
        thread_history=[],
    )

    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response")

    return {"agent": agent.handle, "response": response}


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================


@app.post("/search/web", tags=["Search"])
async def web_search(request: SearchRequest):
    """
    Search the web using Serper.dev.

    Requires SERPER_API_KEY to be configured.
    Returns organic search results with title, link, and snippet.
    """
    if not SERPER_ENABLED:
        raise HTTPException(status_code=501, detail="Search service not enabled")

    results = await search_web(request.query, request.num_results)
    if not results:
        return {"query": request.query, "results": []}

    formatted = []
    for result in results.get("organic", [])[: request.num_results]:
        formatted.append(
            {
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
            }
        )

    return {"query": request.query, "results": formatted}


@app.get("/search/images/{query}", tags=["Search"])
async def image_search(query: str, per_page: int = 10):
    """
    Search for images using available media services.

    Searches across multiple stock image services (Pexels, Pixabay, Unsplash).
    Requires at least one media service API key to be configured.
    """
    results = await media_service.search_images(query, per_page)
    return {"query": query, "results": results}


# =============================================================================
# SCRAPING ENDPOINTS
# =============================================================================


@app.post("/scrape", tags=["Scraping"])
async def scrape_webpage(request: ScrapeRequest):
    """
    Scrape a webpage and extract content.

    Requires SCRAPERAPI_KEY to be configured.
    Returns the page title, text content, and optionally extracted links.

    - **url**: The URL to scrape
    - **extract_links**: Whether to extract links from the page
    """
    if not SCRAPERAPI_ENABLED:
        raise HTTPException(status_code=501, detail="Scraping service not enabled")

    content = await scraping_service.scrape_text(request.url, request.extract_links)
    if not content:
        raise HTTPException(status_code=500, detail="Failed to scrape URL")

    return {
        "url": request.url,
        "title": content.get("title", ""),
        "content": content.get("text", "")[:5000],
        "links": content.get("links", []) if request.extract_links else [],
    }


# =============================================================================
# MEDIA ENDPOINTS
# =============================================================================


@app.post("/media/images/generate", tags=["Media"])
async def generate_image(request: ImageGenerateRequest):
    """
    Generate an image using KlingAI.

    Requires KLINGAI_ACCESS_KEY and KLINGAI_SECRET_KEY to be configured.

    - **prompt**: The image generation prompt
    - **image_size**: Aspect ratio (e.g., "16:9")
    - **num_images**: Number of images to generate
    """
    if not KLINGAI_ENABLED:
        raise HTTPException(
            status_code=501, detail="Image generation service not enabled"
        )

    result = await media_service.klingai.generate_image(
        request.prompt, request.image_size, request.num_images
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate image")

    return {"prompt": request.prompt, "result": result}


@app.post("/media/images/search", tags=["Media"])
async def search_images(request: ImageSearchRequest):
    """
    Search for stock images.

    Searches across Pexels, Pixabay, and Unsplash based on configuration.
    Set source to "auto" to search all available services.

    - **query**: Search query string
    - **per_page**: Number of results to return
    - **source**: Specific service or "auto" for all
    """
    results = await media_service.search_images(
        request.query, request.per_page, request.source
    )
    return {"query": request.query, "source": request.source, "results": results}


@app.post("/media/videos/search", tags=["Media"])
async def search_videos(query: str, per_page: int = 10):
    """
    Search for stock videos.

    Searches across Pexels and Pixabay for video content.

    - **query**: Search query string
    - **per_page**: Number of results to return
    """
    results = await media_service.search_videos(query, per_page)
    return {"query": query, "results": results}


@app.post("/media/videos/generate", tags=["Media"])
async def generate_video(request: VideoGenerateRequest):
    """
    Generate a video using KlingAI text-to-video.

    Requires KLINGAI_ACCESS_KEY and KLINGAI_SECRET_KEY to be configured.

    - **prompt**: The video generation prompt
    - **duration**: Video duration in seconds (default: 5)
    """
    if not KLINGAI_ENABLED:
        raise HTTPException(
            status_code=501, detail="Video generation service not enabled"
        )

    result = await media_service.klingai.text_to_video(request.prompt, request.duration)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate video")

    return {"prompt": request.prompt, "result": result}


# =============================================================================
# EMAIL ENDPOINTS
# =============================================================================


@app.post("/email/send", tags=["Email"])
async def send_email(request: EmailSendRequest):
    """
    Send an email using Resend.

    Requires RESEND_API_KEY to be configured.

    - **to**: Recipient email address
    - **subject**: Email subject line
    - **html**: HTML email body
    """
    if not RESEND_ENABLED:
        raise HTTPException(status_code=501, detail="Email service not enabled")

    message_id = await email_service.send_email(
        to=request.to, subject=request.subject, html=request.html
    )

    if not message_id:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"message_id": message_id, "status": "sent"}


# =============================================================================
# USER ENDPOINTS
# =============================================================================


@app.get("/me", response_model=User, tags=["Users"])
async def get_current_app_user():
    """
    Get current user info.

    Returns the profile information for the authenticated user.
    """
    return store.current_user


@app.get("/users/{user_id}/stats", response_model=UserStats, tags=["Users"])
async def get_user_stats(user_id: str):
    """
    Get user statistics.

    Returns post count, like count, and reply count for the specified user.
    """
    return store.get_user_stats(user_id)


@app.get("/users/{user_id}/posts", tags=["Users"])
async def get_user_posts(user_id: str, limit: int = 50):
    """
    Get posts by a specific user.

    Returns the most recent posts created by the specified user.
    """
    return store.get_user_posts(user_id, limit)


# =============================================================================
# AGENT RUNS ENDPOINTS
# =============================================================================


@app.get("/threads/{thread_id}/agent-runs", tags=["Posts"])
async def get_thread_agent_runs(thread_id: str):
    """
    Get active agent runs for a thread.

    Returns information about agent processing runs for the specified thread.
    """
    runs = store.get_active_agent_runs(thread_id)
    return {"runs": runs}


@app.get("/threads/{thread_id}/stream", tags=["Posts"])
async def stream_thread_updates(thread_id: str):
    """
    Stream real-time updates for a thread using Server-Sent Events (SSE).

    This endpoint provides a continuous stream of updates including:
    - New agent runs (queued/running)
    - Agent status changes
    - New posts/replies in the thread

    The connection stays open and sends events as they happen.
    Clients should use EventSource to consume this stream.
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def event_stream():
        """Generator that yields SSE events"""
        # Track previously seen runs to detect changes
        seen_runs = set()
        # Track previously seen posts
        seen_posts = set()
        last_new_post_id = None

        try:
            while True:
                # Check for new/updated agent runs
                active_runs = store.get_active_agent_runs(thread_id)
                current_runs = {run.id for run in active_runs}

                # Check for new runs
                new_runs = current_runs - seen_runs
                if new_runs:
                    for run_id in new_runs:
                        run = next((r for r in active_runs if r.id == run_id), None)
                        if run:
                            data = json.dumps(
                                {
                                    "type": "agent_run",
                                    "data": {
                                        "id": run.id,
                                        "agent_handle": run.agent_handle,
                                        "status": run.status,
                                        "thread_id": run.thread_id,
                                        "trigger_post_id": run.trigger_post_id,
                                        "started_at": run.started_at.isoformat()
                                        if hasattr(run.started_at, "isoformat")
                                        else run.started_at,
                                    },
                                }
                            )
                            yield f"event: agent_run\ndata: {data}\n\n"
                    seen_runs.update(new_runs)

                # Check for status changes in existing runs
                for run in active_runs:
                    if run.id in seen_runs:
                        # Get latest run data from store
                        latest_run = store.get_agent_run(run.id)
                        if latest_run and latest_run.status != run.status:
                            data = json.dumps(
                                {
                                    "type": "agent_status_change",
                                    "data": {
                                        "id": latest_run.id,
                                        "agent_handle": latest_run.agent_handle,
                                        "status": latest_run.status,
                                        "thread_id": latest_run.thread_id,
                                        "ended_at": latest_run.ended_at.isoformat()
                                        if latest_run.ended_at
                                        else None,
                                    },
                                }
                            )
                            yield f"event: agent_status_change\ndata: {data}\n\n"

                # Check for new posts in the thread
                thread = store.get_thread(thread_id)
                if thread:
                    current_post_ids = {
                        p.id for p in [thread.root_post] + thread.replies
                    }
                    new_posts = current_post_ids - seen_posts

                    if new_posts:
                        for post in [thread.root_post] + thread.replies:
                            if post.id in new_posts and post.id != last_new_post_id:
                                data = json.dumps(
                                    {
                                        "type": "new_post",
                                        "data": {
                                            "id": post.id,
                                            "author_handle": post.author_handle,
                                            "author_type": post.author_type.value
                                            if hasattr(post.author_type, "value")
                                            else post.author_type,
                                            "text": post.text,
                                            "created_at": post.created_at.isoformat()
                                            if hasattr(post.created_at, "isoformat")
                                            else post.created_at,
                                            "parent_id": post.parent_id,
                                            "thread_id": post.thread_id,
                                            "mentions": post.mentions or [],
                                        },
                                    }
                                )
                                yield f"event: new_post\ndata: {data}\n\n"
                                last_new_post_id = post.id

                        seen_posts.update(new_posts)

                # Send heartbeat every 5 seconds to keep connection alive
                yield ": heartbeat\n\n"

                # Wait before next check (2 seconds to reduce load)
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            # Client disconnected
            logger.info(f"SSE client disconnected from thread {thread_id}")
            raise
        except Exception as e:
            logger.error(f"SSE error for thread {thread_id}: {e}")
            data = json.dumps({"type": "error", "data": {"message": str(e)}})
            yield f"event: error\ndata: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/agent-runs/{run_id}/retry", tags=["Posts"])
async def retry_agent_run(run_id: str):
    """
    Retry a failed agent run.

    This endpoint is not yet implemented.
    """
    raise HTTPException(status_code=501, detail="Not implemented")


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns a simple status check for load balancers and monitoring systems.
    """
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
    }


@app.get("/status", tags=["Health"])
async def get_status():
    """
    Get detailed service status.

    Returns the status of all configured services and integrations.
    Useful for debugging and monitoring.
    """
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "services": {
            "deepseek_llm": "enabled" if DEEPSEEK_ENABLED else "disabled",
            "database": "enabled" if DATABASE_ENABLED else "in-memory",
            "serper_search": "enabled" if SERPER_ENABLED else "disabled",
            "scraperapi": "enabled" if SCRAPERAPI_ENABLED else "disabled",
            "klingai": "enabled" if KLINGAI_ENABLED else "disabled",
            "resend_email": "enabled" if RESEND_ENABLED else "disabled",
            "auth0": "enabled" if AUTH0_ENABLED else "disabled",
            "github": "enabled" if GITHUB_ENABLED else "disabled",
        },
    }


@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint with API information.

    Returns an overview of available endpoints and links to documentation.
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": "AI-powered Twitter-like platform with agent mentions",
        "endpoints": {
            "posts": "/posts",
            "timeline": "/timeline",
            "threads": "/threads/{id}",
            "agents": "/agents",
            "search": "/search/web",
            "scrape": "/scrape",
            "media": "/media/images/generate, /media/images/search",
            "email": "/email/send",
            "health": "/health",
            "status": "/status",
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
    }


# =============================================================================
# MONITORING & METRICS ENDPOINTS
# =============================================================================


@app.get("/metrics", tags=["Health"])
async def get_metrics(since_minutes: Optional[int] = None):
    """
    Get application metrics.

    Returns counters, gauges, and metric summaries.
    Use `since_minutes` to get metrics from a specific time window.
    """
    from datetime import timedelta

    since = timedelta(minutes=since_minutes) if since_minutes else None
    return monitoring.get_metrics(since=since)


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with system resources.

    Returns health status for system resources (CPU, memory, disk)
    and can be extended with custom health checks.
    """
    return monitoring.get_health()


@app.get("/monitoring/status", tags=["Health"])
async def monitoring_status():
    """
    Get monitoring system status.

    Returns information about the monitoring system itself,
    including registered health checks and metric count.
    """
    return {
        "status": "running",
        "health_checks": len(monitoring.health.checks),
        "metrics_count": len(monitoring.registry._metrics),
        "counters_count": len(monitoring.registry._counters),
        "gauges_count": len(monitoring.registry._gauges),
    }


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================


@app.get("/auth/github/login", tags=["Authentication"])
async def github_login(redirect_uri: Optional[str] = None):
    """
    Get GitHub OAuth login URL.

    Returns the GitHub OAuth authorization URL that the user should be redirected to.
    The frontend can handle the redirect, or use the URL directly.

    Query Parameters:
        redirect_uri: Where to redirect after login (defaults to backend callback URL)

    Returns:
        Dictionary with the authorization URL and state
    """
    from services.auth_service import get_auth_service

    auth_service = get_auth_service()

    # Generate state for CSRF protection
    state = generate_oauth_state()

    # Use provided redirect_uri or default to backend callback
    final_redirect_uri = redirect_uri or "https://yaam.click/callback"

    auth_url = auth_service.get_github_auth_url(state, redirect_uri=final_redirect_uri)

    return {"auth_url": auth_url, "state": state}


@app.get("/auth/github/callback", tags=["Authentication"])
async def github_callback(code: str, state: str):
    """
    Handle GitHub OAuth callback.

    Exchanges the authorization code for an access token and retrieves
    the user's GitHub profile. Creates a session and returns a JWT token.

    Args:
        code: Authorization code from GitHub
        state: State parameter for CSRF validation

    Returns:
        Dictionary with access_token and user information
    """
    from services.auth_service import get_auth_service

    auth_service = get_auth_service()

    try:
        if not verify_oauth_state(state):
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        # Exchange code for access token
        token_response = await auth_service.exchange_code_for_token(code, state)

        # Get user profile from GitHub
        github_user = await auth_service.get_github_user(token_response.access_token)

        # Create user session and JWT
        access_token, auth_user = auth_service.create_user_session(github_user)

        return {"access_token": access_token, "user": auth_user.dict()}

    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@app.post("/auth/github/callback", tags=["Authentication"])
async def github_callback_post(request: dict):
    """
    Handle GitHub OAuth callback via POST (for frontend callbacks).

    Exchanges the authorization code for an access token and retrieves
    the user's GitHub profile. Creates a session and returns a JWT token.

    Request Body:
        code: Authorization code from GitHub
        redirect_uri: The redirect URI used in the login request
        state: State parameter for CSRF validation

    Returns:
        Dictionary with access_token and user information
    """
    from services.auth_service import get_auth_service

    auth_service = get_auth_service()

    code = request.get("code")
    redirect_uri = request.get("redirect_uri", "https://yaam.click/callback")
    state = request.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    if not verify_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    try:
        # Exchange code for access token (with matching redirect_uri)
        token_response = await auth_service.exchange_code_for_token(
            code, state, redirect_uri=redirect_uri
        )

        # Get user profile from GitHub
        github_user = await auth_service.get_github_user(token_response.access_token)

        # Create user session and JWT
        access_token, auth_user = auth_service.create_user_session(github_user)

        return {"access_token": access_token, "user": auth_user.dict()}

    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@app.post("/auth/logout", tags=["Authentication"])
async def logout():
    """
    Logout user and clear session.

    In a stateless JWT setup, the client should simply discard the token.
    This endpoint can be expanded to invalidate tokens in a refresh token setup.
    """
    return {"message": "Logged out successfully"}


@app.get("/auth/me", tags=["Authentication"])
async def get_authenticated_user(payload: dict = Depends(get_current_user)):
    """
    Get currently authenticated user.

    Requires valid JWT token in Authorization header.
    Returns the user profile information.

    Raises:
        HTTPException 401: If not authenticated
    """
    return payload


@app.get("/me", tags=["Authentication"])
async def get_authenticated_user_alias(payload: dict = Depends(get_current_user)):
    """Alias for /auth/me to keep frontend compatible."""
    return payload


# =============================================================================
# AUTH0 ENDPOINTS
# =============================================================================


@app.get("/auth0/login", tags=["Authentication"])
async def auth0_login(
    redirect_uri: Optional[str] = None,
    connection: Optional[str] = None,
    state: Optional[str] = None,
):
    """
    Get Auth0 login URL.

    Returns the Auth0 Universal Login URL that the user should be redirected to.
    The frontend can handle the redirect, or use the URL directly.

    Query Parameters:
        redirect_uri: Where to redirect after login (defaults to frontend URL)
        connection: Specific Auth0 connection (e.g., "github", "google")
        state: CSRF protection parameter

    Returns:
        Dictionary with the login URL
    """
    from services.auth0_service import get_auth0_service

    auth0_service = get_auth0_service()

    if not auth0_service.enabled:
        raise HTTPException(status_code=501, detail="Auth0 not configured")

    # Always generate a fresh state for CSRF protection
    # Client should receive and return this state, not provide their own
    final_state = generate_oauth_state()

    # Default redirect to frontend
    if not redirect_uri:
        redirect_uri = "https://yaam.click/callback"

    login_url = auth0_service.get_login_url(
        redirect_uri=redirect_uri, state=final_state, connection=connection
    )

    return {"login_url": login_url, "state": final_state}


@app.post("/auth0/callback", tags=["Authentication"])
async def auth0_callback(request: dict):
    """
    Handle Auth0 OAuth callback.

    Exchanges the authorization code for tokens and retrieves user info.

    Request Body:
        code: Authorization code from Auth0
        redirect_uri: The redirect URI used in the login request

    Returns:
        Dictionary with access_token, id_token, and user information
    """
    from services.auth0_service import get_auth0_service

    auth0_service = get_auth0_service()

    if not auth0_service.enabled:
        raise HTTPException(status_code=501, detail="Auth0 not configured")

    code = request.get("code")
    redirect_uri = request.get("redirect_uri", "https://yaam.click/callback")
    state = request.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    if not verify_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Exchange code for tokens
    token_response = await auth0_service.exchange_code_for_token(code, redirect_uri)

    if not token_response:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    access_token = token_response.get("access_token")
    id_token = token_response.get("id_token")

    # Get user info
    user_info = await auth0_service.get_user_info(access_token)

    if not user_info:
        # Decode id_token as fallback
        user_info = jwt.decode(id_token, options={"verify_signature": False})

    return {
        "access_token": access_token,
        "id_token": id_token,
        "token_type": token_response.get("token_type", "Bearer"),
        "expires_in": token_response.get("expires_in"),
        "user": auth0_service.normalize_user(user_info),
    }


@app.get("/auth0/user", tags=["Authentication"])
async def auth0_get_user(payload: dict = Depends(get_current_user)):
    """
    Get Auth0 user info.

    Requires valid Auth0 JWT. Returns the user profile information.
    Can be used to refresh user data from Auth0.

    Raises:
        HTTPException 401: If not authenticated
    """
    return payload


@app.get("/auth0/logout", tags=["Authentication"])
async def auth0_logout(return_to: str = "https://yaam.click"):
    """
    Get Auth0 logout URL.

    Returns the Auth0 logout URL that will log the user out of Auth0
    and redirect back to your application.

    Query Parameters:
        return_to: Where to redirect after logout

    Returns:
        Dictionary with the logout URL
    """
    from services.auth0_service import get_auth0_service

    auth0_service = get_auth0_service()

    if not auth0_service.enabled:
        raise HTTPException(status_code=501, detail="Auth0 not configured")

    logout_url = auth0_service.get_logout_url(return_to=return_to)

    return {"logout_url": logout_url}


# =============================================================================
# AUDIT TRAIL ENDPOINTS
# =============================================================================


@app.get("/audit/logs", tags=["Audit"])
async def get_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
    _user: Optional[dict] = Depends(get_optional_user),
):
    """
    Get audit logs with filtering and pagination.

    Returns enterprise-grade audit trail of all system events.
    Useful for compliance, debugging, and tracking user activity.

    Query Parameters:
        event_type: Filter by event type (post_create, agent_run_start, etc.)
        user_id: Filter by user who performed the action
        resource_type: Filter by resource type (post, agent_run, media, etc.)
        resource_id: Filter by specific resource ID
        thread_id: Filter by thread/conversation
        status: Filter by status (success, failed, pending)
        page: Page number for pagination
        page_size: Number of results per page

    Returns paginated list of audit log entries.
    """
    from services.audit_service import audit_service
    from models import AuditEventType

    # Convert string to enum if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            pass

    result = audit_service.get_logs(
        event_type=event_type_enum,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        thread_id=thread_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return result


@app.get("/audit/stats", tags=["Audit"])
async def get_audit_stats(_user: Optional[dict] = Depends(get_optional_user)):
    """
    Get audit trail statistics.

    Returns summary statistics about the audit trail including
    event counts, media generation counts, and conversation stats.
    """
    from services.audit_service import audit_service

    return audit_service.get_stats()


@app.get("/audit/media", tags=["Audit"])
async def get_media_assets(
    asset_type: Optional[str] = None,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    _user: Optional[dict] = Depends(get_optional_user),
):
    """
    Get generated media assets (videos, images).

    Returns all generated media with their URLs, prompts, and metadata.
    Useful for finding past generated content.

    Query Parameters:
        asset_type: Filter by asset type (video, image)
        thread_id: Filter by related thread/conversation
        user_id: Filter by user who generated the media
        limit: Maximum number of results

    Returns list of media assets with download URLs.
    """
    from services.audit_service import audit_service

    assets = audit_service.get_media_assets(
        asset_type=asset_type, thread_id=thread_id, user_id=user_id, limit=limit
    )

    return {"assets": assets, "count": len(assets)}


@app.get("/audit/conversations", tags=["Audit"])
async def get_conversation_audits(_user: Optional[dict] = Depends(get_optional_user)):
    """
    Get all conversation audits.

    Returns audit information for all threads including participants,
    message counts, media generated, and commands executed.
    """
    from services.audit_service import audit_service

    conversations = audit_service.get_all_conversation_audits()

    return {
        "conversations": conversations,
        "count": len(conversations),
    }


@app.get("/audit/conversations/{thread_id}", tags=["Audit"])
async def get_conversation_audit(
    thread_id: str, _user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get audit information for a specific conversation.

    Returns detailed audit data for a thread including all participants,
    media assets generated, commands executed, and activity timeline.
    """
    from services.audit_service import audit_service

    audit = audit_service.get_conversation_audit(thread_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Conversation audit not found")

    # Get related logs for this thread
    logs_result = audit_service.get_logs_sync(thread_id=thread_id, page_size=100)
    logs_result = audit_service.get_logs(thread_id=thread_id, page_size=100)

    return {
        "audit": audit,
        "related_logs": logs_result["logs"],
    }


# =============================================================================
# ADMIN AUDIT ENDPOINTS (Admin Only)
# =============================================================================


@app.get("/admin/whoami", tags=["Admin"])
async def admin_whoami(
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Get current user information for admin configuration.

    Returns the user's ID and email so you can configure ADMIN_USER_IDS.
    Use this to find your user ID to set as the sole admin.
    """
    # Get the full token payload which contains the user_id
    payload = await get_token_payload()

    if not payload:
        return {
            "authenticated": False,
            "message": "Not authenticated. Please log in first.",
            "instructions": "After logging in, visit this page again to see your user ID.",
        }

    result = {
        "authenticated": True,
        "user_id": getattr(payload, "user_id", None),
        "email": getattr(payload, "email", None),
        "name": getattr(payload, "name", None),
        "sub": getattr(payload, "sub", None),
        "iss": getattr(payload, "iss", None),
    }

    # Add raw payload for debugging
    if hasattr(payload, "dict"):
        result["raw_payload"] = payload.dict()

    # Add configuration instructions
    result["instructions"] = {
        "how_to_configure_admin": [
            "1. Copy your 'user_id' or 'sub' field above",
            "2. Set ADMIN_USER_IDS environment variable: ADMIN_USER_IDS=your_user_id_here",
            "3. Set ADMIN_EMAIL_DOMAINS to empty: ADMIN_EMAIL_DOMAINS=",
            "4. Restart the backend",
        ],
        "example": f"ADMIN_USER_IDS={result.get('user_id') or result.get('sub', 'your_user_id_here')}",
    }

    return result


@app.get("/admin/audit/logs/export", tags=["Audit"])
async def export_audit_logs(
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    _admin: dict = Depends(require_admin),
):
    """
    Export audit logs in JSON or CSV format (ADMIN ONLY).

    Query Parameters:
        format: Export format - "json" or "csv" (default: json)
        start_date: Start date filter (ISO 8601 format)
        end_date: End date filter (ISO 8601 format)

    Returns downloadable file with audit logs.
    """
    from datetime import datetime
    from fastapi.responses import Response
    import json

    from services.audit_service import audit_service

    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get all logs (no pagination for export)
    result = audit_service.get_logs_sync(
        start_date=start_dt, end_date=end_dt, page_size=100000
    )

    if format == "csv":
        import io

        import csv

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "timestamp",
                "event_type",
                "user_id",
                "resource_type",
                "resource_id",
                "status",
                "thread_id",
                "post_id",
                "ip_address",
                "user_agent",
                "details",
                "error_message",
            ]
        )
        for log in result["logs"]:
            writer.writerow(
                [
                    log.id,
                    log.timestamp,
                    log.event_type.value,
                    log.user_id,
                    log.resource_type,
                    log.resource_id,
                    log.status,
                    log.thread_id,
                    log.post_id,
                    log.ip_address,
                    log.user_agent,
                    json.dumps(log.details),
                    log.error_message,
                ]
            )

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
        )

    # Default to JSON
    return Response(
        content=json.dumps(
            [log.dict() for log in result["logs"]],
            default=str,
            indent=2,
        ),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=audit_logs.json"},
    )


@app.get("/admin/audit/comprehensive", tags=["Audit"])
async def get_comprehensive_audit(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_types: Optional[str] = None,
    user_ids: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
    _admin: dict = Depends(require_admin),
):
    """
    Get comprehensive audit logs with advanced filtering (ADMIN ONLY).

    Query Parameters:
        start_date: Start date filter (ISO 8601 format)
        end_date: End date filter (ISO 8601 format)
        event_types: Comma-separated list of event types to filter
        user_ids: Comma-separated list of user IDs to filter
        search: Search query for details/error messages
        page: Page number (default: 1)
        page_size: Results per page (default: 100, max: 1000)
    """
    from datetime import datetime

    from services.audit_service import audit_service

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Parse event types
    event_type_list = None
    if event_types:
        event_type_list = event_types.split(",")

    # Parse user IDs
    user_id_list = None
    if user_ids:
        user_id_list = user_ids.split(",")

    # Limit page size
    page_size = min(page_size, 1000)

    # For now, use the sync version with first user ID filter
    # TODO: Update to use async version with multiple filters
    result = audit_service.get_logs_sync(
        user_id=user_id_list[0] if user_id_list else None,
        start_date=start_dt,
        end_date=end_dt,
        page=page,
        page_size=page_size,
    )

    # Apply additional filters post-query
    filtered_logs = result["logs"]
    if event_type_list:
        filtered_logs = [
            log for log in filtered_logs if log.event_type.value in event_type_list
        ]
    if search:
        search_lower = search.lower()
        filtered_logs = [
            log
            for log in filtered_logs
            if search_lower in str(log.details).lower()
            or (log.error_message and search_lower in log.error_message.lower())
        ]

    result["logs"] = filtered_logs
    result["total_count"] = len(filtered_logs)

    return result


@app.get("/admin/audit/system-events", tags=["Audit"])
async def get_system_events(hours: int = 24, _admin: dict = Depends(require_admin)):
    """
    Get recent system events for monitoring (ADMIN ONLY).

    Returns system-related events like errors, startup, etc.

    Query Parameters:
        hours: Number of hours to look back (default: 24)
    """
    from services.audit_service import audit_service
    from models import AuditEventType

    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)

    # Get system-related events
    result = audit_service.get_logs_sync(
        start_date=start_date,
        end_date=end_date,
        page_size=1000,
    )

    # Filter to system events
    system_events = [
        log
        for log in result["logs"]
        if log.event_type
        in [
            AuditEventType.SYSTEM_ERROR,
            AuditEventType.SYSTEM_STARTUP,
            AuditEventType.COMMAND_FAILED,
            AuditEventType.AGENT_RUN_ERROR,
            AuditEventType.AUTH_FAILED,
        ]
    ]

    # Group by event type
    events_by_type: dict = {}
    for log in system_events:
        event_type = log.event_type.value
        if event_type not in events_by_type:
            events_by_type[event_type] = []
        events_by_type[event_type].append(log)

    return {
        "time_range": f"Last {hours} hours",
        "events": events_by_type,
        "total_count": len(system_events),
    }


@app.get("/admin/audit/user-activity/{user_id}", tags=["Audit"])
async def get_user_activity(
    user_id: str,
    days: int = 7,
    _admin: dict = Depends(require_admin),
):
    """
    Get detailed activity for a specific user (ADMIN ONLY).

    Returns all user actions, posts, agent interactions, and media generation.

    Query Parameters:
        days: Number of days to look back (default: 7)
    """
    from services.audit_service import audit_service

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get all user activities
    result = audit_service.get_logs_sync(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page_size=1000,
    )

    # Group by resource type
    activities_by_type = {}
    for log in result["logs"]:
        resource_type = log.resource_type or "unknown"
        if resource_type not in activities_by_type:
            activities_by_type[resource_type] = []
        activities_by_type[resource_type].append(log)

    # Get user statistics
    stats = audit_service.get_stats()

    # Get user's media assets
    media_assets = audit_service.get_media_assets(user_id=user_id, limit=100)

    return {
        "user_id": user_id,
        "time_range": f"Last {days} days",
        "activities": activities_by_type,
        "total_events": len(result["logs"]),
        "media_generated": len(media_assets),
        "system_stats": stats,
    }


@app.get("/admin/audit/media-expired", tags=["Audit"])
async def get_expired_media(
    days: int = 30,
    _admin: dict = Depends(require_admin),
):
    """
    Get media assets older than specified days (ADMIN ONLY).

    Useful for cleanup and retention policy management.

    Query Parameters:
        days: Age threshold in days (default: 30)
    """
    from services.audit_service import audit_service

    cutoff_date = datetime.now() - timedelta(days=days)

    # Get all media assets
    all_media = audit_service.get_media_assets(limit=10000)

    # Filter for old assets
    expired_media = [asset for asset in all_media if asset.created_at < cutoff_date]

    return {
        "cutoff_date": cutoff_date.isoformat(),
        "expired_count": len(expired_media),
        "expired_media": [
            {
                "id": asset.id,
                "type": asset.asset_type,
                "url": asset.url,
                "created_at": asset.created_at.isoformat(),
                "thread_id": asset.thread_id,
            }
            for asset in expired_media
        ],
    }


@app.get("/admin/audit/errors", tags=["Audit"])
async def get_error_logs(
    hours: int = 24,
    event_type: Optional[str] = None,
    _admin: dict = Depends(require_admin),
):
    """
    Get all error logs for analysis (ADMIN ONLY).

    Query Parameters:
        hours: Number of hours to look back (default: 24)
        event_type: Filter by specific event type
    """
    from services.audit_service import audit_service

    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)

    # Get failed events
    result = audit_service.get_logs_sync(
        start_date=start_date,
        end_date=end_date,
        status="failed",
        page_size=1000,
    )

    # Filter by event type if specified
    errors = result["logs"]
    if event_type:
        errors = [log for log in errors if log.event_type.value == event_type]

    # Group by error type
    errors_by_type: dict = {}
    for log in errors:
        key = log.event_type.value
        if key not in errors_by_type:
            errors_by_type[key] = []
        errors_by_type[key].append(log)

    return {
        "time_range": f"Last {hours} hours",
        "total_errors": len(errors),
        "errors_by_type": errors_by_type,
    }


@app.get("/admin/audit/config", tags=["Audit"])
async def get_admin_audit_config(_admin: dict = Depends(require_admin)):
    """
    Get audit system configuration (ADMIN ONLY).
    """
    from middleware.admin_middleware import get_admin_config
    from services.database_service import database_service

    return {
        "admin_config": get_admin_config(),
        "database_enabled": database_service.is_enabled(),
    }


# =============================================================================
# STARTUP
# =============================================================================


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} in {APP_ENV} mode")
    print_config()

    # Initialize database service for audit trail
    if DATABASE_ENABLED:
        try:
            from services.database_service import database_service
            from services.audit_service import audit_service

            await database_service.initialize()
            audit_service.set_database_service(database_service)
            logger.info("Database service initialized for audit trail")
        except Exception as e:
            logger.warning(f"Failed to initialize database service: {e}")

    # Log system startup
    from services.audit_service import audit_service as audit

    audit.log_event_sync(
        event_type=AuditEventType.SYSTEM_STARTUP,
        details={"app_version": APP_VERSION, "environment": APP_ENV},
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Note: Run 'python seed.py' separately to create seed data
    logger.info("Starting server without seed data...")
    logger.info("Tip: Run 'python seed.py' to create example posts")

    uvicorn.run(
        app, host=BACKEND_HOST, port=BACKEND_PORT, log_level=BACKEND_LOG_LEVEL.lower()
    )
