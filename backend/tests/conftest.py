# =============================================================================
# Agent Twitter - Test Configuration & Fixtures
# =============================================================================
#
# This file contains shared pytest fixtures for testing the backend
#
# =============================================================================

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient

from main import app
from store import store
from models import Agent, Post


# =============================================================================
# Test Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Client Fixtures
# =============================================================================

@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """Create a client with authentication stub"""
    # Mock user payload for authentication
    mock_user_payload = {
        "sub": "test-user-123",
        "name": "Test User",
        "email": "test@example.com",
        "picture": "https://example.com/avatar.jpg"
    }

    # Import the auth functions to override them
    from middleware import auth_middleware

    async def mock_get_optional():
        return mock_user_payload

    async def mock_get_current():
        return mock_user_payload

    app.dependency_overrides[auth_middleware.get_optional_user] = mock_get_optional
    app.dependency_overrides[auth_middleware.get_current_user] = mock_get_current

    yield client

    # Clean up overrides
    app.dependency_overrides.clear()


# =============================================================================
# Store Fixtures
# =============================================================================

@pytest.fixture
def clean_store() -> None:
    """Reset the store before each test"""
    # Store initial state
    initial_posts = list(store.posts.values())
    initial_threads = list(store.threads.values())

    yield

    # Restore initial state
    store.posts.clear()
    store.threads.clear()
    for post in initial_posts:
        store.posts[post.id] = post
    for thread in initial_threads:
        store.threads[thread.id] = thread


@pytest.fixture
def sample_post() -> Post:
    """Create a sample post for testing"""
    return Post(
        id="test-post-1",
        text="Hello world! @grok what do you think?",
        author=store.current_user,
        timestamp="2024-01-01T12:00:00Z"
    )


@pytest.fixture
def sample_thread(sample_post: Post) -> dict:
    """Create a sample thread for testing"""
    return {
        "id": "thread-1",
        "root_post": sample_post,
        "replies": []
    }


# =============================================================================
# Agent Fixtures
# =============================================================================

@pytest.fixture
def mock_agents():
    """Create mock agents for testing"""
    return [
        Agent(
            id="test-agent",
            handle="@test",
            name="Test Agent",
            role="Testing specialist",
            policy="Helps with testing",
            style="Helpful and concise",
            tools=["test_tool"],
            color="#FF0000",
            icon="🧪",
            mock_responses=["Test response: {context}"]
        ),
        Agent(
            id="grok",
            handle="@grok",
            name="Grok",
            role="Generalist",
            policy="General assistance",
            style="Direct and witty",
            tools=["web_search"],
            color="#F59E0B",
            icon="🚀"
        )
    ]


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response"""
    return "This is a mock response from the LLM service."


# =============================================================================
# Service Mocks
# =============================================================================

@pytest.fixture
def mock_llm_service():
    """Mock the LLM service"""
    from services import llm_service
    original_generate = llm_service.generate_agent_response

    async def mock_generate(*args, **kwargs):
        return "Mock LLM response for testing"

    llm_service.generate_agent_response = mock_generate
    yield llm_service

    # Restore original
    llm_service.generate_agent_response = original_generate


@pytest.fixture
def mock_search_service():
    """Mock the search service"""
    from services import search_web
    original_search = search_web

    async def mock_search(query, num_results=10):
        return {
            "organic": [
                {
                    "title": f"Test result for {query}",
                    "link": "https://example.com",
                    "snippet": "This is a test search result"
                }
            ]
        }

    # Patch the search function
    import services
    services.search_web = mock_search
    yield services

    # Restore
    services.search_web = original_search


@pytest.fixture
def mock_email_service():
    """Mock the email service"""
    from services.email_service import email_service
    original_send = email_service.send_email

    async def mock_send(to, subject, html):
        return "test-message-id"

    email_service.send_email = mock_send
    yield email_service

    email_service.send_email = original_send


@pytest.fixture
def mock_media_service():
    """Mock the media service"""
    from services.media_service import media_service

    async def mock_search_images(query, per_page=10):
        return [
            {
                "url": "https://example.com/image.jpg",
                "thumbnail": "https://example.com/thumb.jpg",
                "source": "test"
            }
        ]

    media_service.search_images = mock_search_images
    yield media_service


# =============================================================================
# Environment Fixtures
# =============================================================================

@pytest.fixture
def test_env(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("USE_REAL_LLM", "false")
    monkeypatch.setenv("DEEPSEEK_ENABLED", "false")
    monkeypatch.setenv("DATABASE_ENABLED", "false")
    monkeypatch.setenv("SERPER_ENABLED", "false")
    monkeypatch.setenv("SCRAPERAPI_ENABLED", "false")
    monkeypatch.setenv("KLINGAI_ENABLED", "false")
    monkeypatch.setenv("RESEND_ENABLED", "false")
