# =============================================================================
# Agent Twitter - Service Tests
# =============================================================================
#
# Tests for external service integrations (LLM, search, media, email)
#
# =============================================================================

import pytest
from unittest.mock import AsyncMock, patch


# =============================================================================
# LLM Service Tests
# =============================================================================

class TestLLMService:
    """Tests for the LLM service"""

    @pytest.mark.asyncio
    async def test_generate_agent_response_disabled(self):
        """Test LLM response generation when disabled"""
        from services.llm_service import generate_agent_response
        from config import DEEPSEEK_ENABLED

        if not DEEPSEEK_ENABLED:
            response = await generate_agent_response(
                agent_name="Test",
                agent_role="Test role",
                agent_style="Test style",
                agent_policy="Test policy",
                user_message="Hello",
                thread_history=[]
            )
            # Should return a mock response when disabled
            assert response is not None
            assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_generate_agent_response_with_mock(self):
        """Test LLM response with mock agent"""
        from services.llm_service import generate_agent_response

        # Create a mock agent with mock_responses
        class MockAgent:
            mock_responses = ["Mock response: {context}"]

        response = await generate_agent_response(
            agent_name="Test",
            agent_role="Test role",
            agent_style="Test style",
            agent_policy="Test policy",
            user_message="Hello",
            thread_history=[],
            agent=MockAgent()
        )

        assert response is not None
        assert isinstance(response, str)


# =============================================================================
# Search Service Tests
# =============================================================================

class TestSearchService:
    """Tests for the web search service"""

    @pytest.mark.asyncio
    async def test_search_web_disabled(self):
        """Test web search when disabled"""
        from services import search_web
        from config import SERPER_ENABLED

        if not SERPER_ENABLED:
            result = await search_web("test query", 5)
            assert result is None or result == {}


# =============================================================================
# Media Service Tests
# =============================================================================

class TestMediaService:
    """Tests for the media service"""

    @pytest.mark.asyncio
    async def test_search_images(self):
        """Test image search"""
        from services.media_service import media_service
        results = await media_service.search_images("test query", 5)
        # Should return a list (even if empty)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_videos(self):
        """Test video search"""
        from services.media_service import media_service
        results = await media_service.search_videos("test query", 5)
        # Should return a list (even if empty)
        assert isinstance(results, list)


# =============================================================================
# Email Service Tests
# =============================================================================

class TestEmailService:
    """Tests for the email service"""

    @pytest.mark.asyncio
    async def test_send_email_disabled(self):
        """Test sending email when disabled"""
        from services.email_service import email_service
        from config import RESEND_ENABLED

        if not RESEND_ENABLED:
            result = await email_service.send_email(
                to="test@example.com",
                subject="Test",
                html="<p>Test</p>"
            )
            # Should return None when disabled
            assert result is None


# =============================================================================
# Scraping Service Tests
# =============================================================================

class TestScrapingService:
    """Tests for the web scraping service"""

    @pytest.mark.asyncio
    async def test_scrape_text_disabled(self):
        """Test web scraping when disabled"""
        from services.scraping_service import scraping_service
        from config import SCRAPERAPI_ENABLED

        if not SCRAPERAPI_ENABLED:
            result = await scraping_service.scrape_text("https://example.com")
            # Should return None when disabled
            assert result is None
