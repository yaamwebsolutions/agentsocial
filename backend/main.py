"""
Agent Twitter API - FastAPI Backend
Main application with environment-based configuration.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import uvicorn

from models import (
    Thread, TimelinePost, Agent, CreatePostRequest,
    CreatePostResponse, User
)
from middleware.auth_middleware import get_current_user
from agents import list_agents, get_agent
from store import store
from orchestrator import orchestrator
from config import (
    APP_NAME, APP_ENV, APP_VERSION, BACKEND_HOST, BACKEND_PORT,
    CORS_ORIGINS, BACKEND_LOG_LEVEL, DEEPSEEK_ENABLED,
    DATABASE_ENABLED, SERPER_ENABLED, SCRAPERAPI_ENABLED,
    KLINGAI_ENABLED, RESEND_ENABLED, print_config
)
from services import search_web
from services.media_service import media_service
from services.scraping_service import scraping_service
from services.email_service import email_service
from services.llm_service import generate_agent_response
from monitoring import monitoring

# Configure logging
logging.basicConfig(
    level=getattr(logging, BACKEND_LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class AgentPromptRequest(BaseModel):
    agent_handle: str
    prompt: str


# =============================================================================
# POSTS ENDPOINTS
# =============================================================================

@app.post("/posts", response_model=CreatePostResponse, tags=["Posts"])
async def create_post(request: CreatePostRequest):
    """
    Create a new post and trigger any mentioned agents.

    Agents are mentioned using the @handle syntax (e.g., @grok).
    When agents are mentioned, they will automatically generate responses.

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
async def get_timeline(limit: int = 50):
    """
    Get timeline posts (root posts only).

    Returns the most recent posts in reverse chronological order.
    Use the limit parameter to control the number of results.
    """
    return store.get_timeline_posts(limit)


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
    agent = get_agent(request.agent_handle.lstrip('@'))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    response = await generate_agent_response(
        agent_name=agent.name,
        agent_role=agent.role,
        agent_style=agent.style,
        agent_policy=agent.policy,
        user_message=request.prompt,
        thread_history=[]
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
    for result in results.get("organic", [])[:request.num_results]:
        formatted.append({
            "title": result.get("title", ""),
            "link": result.get("link", ""),
            "snippet": result.get("snippet", ""),
        })

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

    content = await scraping_service.scrape_text(
        request.url, request.extract_links
    )
    if not content:
        raise HTTPException(status_code=500, detail="Failed to scrape URL")

    return {
        "url": request.url,
        "title": content.get("title", ""),
        "content": content.get("text", "")[:5000],
        "links": content.get("links", []) if request.extract_links else []
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
        raise HTTPException(status_code=501, detail="Image generation service not enabled")

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
        to=request.to,
        subject=request.subject,
        html=request.html
    )

    if not message_id:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"message_id": message_id, "status": "sent"}


# =============================================================================
# USER ENDPOINTS
# =============================================================================

@app.get("/me", response_model=User, tags=["Users"])
async def get_current_user():
    """
    Get current user info.

    Returns the profile information for the authenticated user.
    """
    return store.current_user


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
        "environment": APP_ENV
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
        }
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
            "status": "/status"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
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
async def github_login():
    """
    Redirect to GitHub OAuth page.

    Initiates the GitHub OAuth flow by redirecting the user to GitHub's
    authorization page. The user will be redirected back to the callback URL
    after authorization.

    Returns a redirect response to GitHub OAuth.
    """
    from services.auth_service import get_auth_service
    auth_service = get_auth_service()

    # Generate state for CSRF protection
    import secrets
    state = secrets.token_urlsafe(16)

    auth_url = auth_service.get_github_auth_url(state)

    return {
        "auth_url": auth_url,
        "state": state
    }


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
        # Exchange code for access token
        token_response = await auth_service.exchange_code_for_token(code, state)

        # Get user profile from GitHub
        github_user = await auth_service.get_github_user(token_response.access_token)

        # Create user session and JWT
        access_token, auth_user = auth_service.create_user_session(github_user)

        return {
            "access_token": access_token,
            "user": auth_user.dict()
        }

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
async def get_authenticated_user(
    payload: dict = Depends(get_current_user)
):
    """
    Get currently authenticated user.

    Requires valid JWT token in Authorization header.
    Returns the user profile information.

    Raises:
        HTTPException 401: If not authenticated
    """
    return payload


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} in {APP_ENV} mode")
    print_config()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Note: Run 'python seed.py' separately to create seed data
    logger.info("Starting server without seed data...")
    logger.info("Tip: Run 'python seed.py' to create example posts")

    uvicorn.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level=BACKEND_LOG_LEVEL.lower()
    )
