"""
Agent Twitter API - FastAPI Backend
Main application with environment-based configuration.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
import uvicorn

from models import (
    Thread, TimelinePost, Agent, CreatePostRequest,
    CreatePostResponse, User
)
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

# Configure logging
logging.basicConfig(
    level=getattr(logging, BACKEND_LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=f"{APP_NAME} API",
    version=APP_VERSION,
    description="AI-powered Twitter-like platform with agent mentions"
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

@app.post("/posts", response_model=CreatePostResponse)
async def create_post(request: CreatePostRequest):
    """Create a new post and trigger any mentioned agents"""
    result = await orchestrator.process_post(request.text, request.parent_id)
    return result


@app.get("/threads/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """Get a thread with all replies"""
    thread = store.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@app.get("/timeline", response_model=List[TimelinePost])
async def get_timeline(limit: int = 50):
    """Get timeline posts (root posts only)"""
    return store.get_timeline_posts(limit)


# =============================================================================
# AGENTS ENDPOINTS
# =============================================================================

@app.get("/agents", response_model=List[Agent])
async def get_agents():
    """List all available agents"""
    return list_agents()


@app.get("/agents/{handle}", response_model=Agent)
async def get_agent_by_handle(handle: str):
    """Get a specific agent by handle"""
    agent = get_agent(handle)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/agents/prompt")
async def prompt_agent(request: AgentPromptRequest):
    """Send a direct prompt to an agent without creating a post"""
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

@app.post("/search/web")
async def web_search(request: SearchRequest):
    """Search the web using Serper.dev"""
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


@app.get("/search/images/{query}")
async def image_search(query: str, per_page: int = 10):
    """Search for images using available media services"""
    results = await media_service.search_images(query, per_page)
    return {"query": query, "results": results}


# =============================================================================
# SCRAPING ENDPOINTS
# =============================================================================

@app.post("/scrape")
async def scrape_webpage(request: ScrapeRequest):
    """Scrape a webpage and extract content"""
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

@app.post("/media/images/generate")
async def generate_image(request: ImageGenerateRequest):
    """Generate an image using KlingAI"""
    if not KLINGAI_ENABLED:
        raise HTTPException(status_code=501, detail="Image generation service not enabled")

    result = await media_service.klingai.generate_image(
        request.prompt, request.image_size, request.num_images
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate image")

    return {"prompt": request.prompt, "result": result}


@app.post("/media/images/search")
async def search_images(request: ImageSearchRequest):
    """Search for stock images"""
    results = await media_service.search_images(
        request.query, request.per_page, request.source
    )
    return {"query": request.query, "source": request.source, "results": results}


@app.post("/media/videos/search")
async def search_videos(query: str, per_page: int = 10):
    """Search for stock videos"""
    results = await media_service.search_videos(query, per_page)
    return {"query": query, "results": results}


# =============================================================================
# EMAIL ENDPOINTS
# =============================================================================

@app.post("/email/send")
async def send_email(request: EmailSendRequest):
    """Send an email using Resend"""
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

@app.get("/me", response_model=User)
async def get_current_user():
    """Get current user info"""
    return store.current_user


# =============================================================================
# AGENT RUNS ENDPOINTS
# =============================================================================

@app.get("/threads/{thread_id}/agent-runs")
async def get_thread_agent_runs(thread_id: str):
    """Get active agent runs for a thread"""
    runs = store.get_active_agent_runs(thread_id)
    return {"runs": runs}


@app.post("/agent-runs/{run_id}/retry")
async def retry_agent_run(run_id: str):
    """Retry a failed agent run (not implemented yet)"""
    raise HTTPException(status_code=501, detail="Not implemented")


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV
    }


@app.get("/status")
async def get_status():
    """Get service status"""
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


@app.get("/")
async def root():
    """Root endpoint with API information"""
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
        }
    }


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
