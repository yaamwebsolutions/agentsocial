"""
Search Service - Integrates with Serper.dev for Google Search results.
Allows agents to fetch real-time web search results.
"""
import httpx
import logging
from typing import List, Dict, Optional
from config import SERPER_API_KEY, SERPER_API_URL, SERPER_ENABLED, AGENT_TIMEOUT

logger = logging.getLogger(__name__)


class SearchService:
    """Service for interacting with Serper.dev Google Search API"""

    def __init__(self):
        self.api_url = SERPER_API_URL
        self.api_key = SERPER_API_KEY
        self.enabled = SERPER_ENABLED
        self.timeout = AGENT_TIMEOUT

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search"
    ) -> Optional[Dict]:
        """
        Perform a web search using Serper.dev API.

        Args:
            query: The search query string
            num_results: Number of results to return (max 100)
            search_type: Type of search (search, images, news, places)

        Returns:
            Dictionary with search results or None if error
        """
        if not self.enabled:
            logger.warning("Serper API not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use different endpoint for images/news
                url = self.api_url
                if search_type == "images":
                    url = self.api_url.replace("/search", "/images")
                elif search_type == "news":
                    url = self.api_url.replace("/search", "/news")
                elif search_type == "places":
                    url = self.api_url.replace("/search", "/places")

                response = await client.post(
                    url,
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "q": query,
                        "num": min(num_results, 100),
                    },
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Serper API request timed out for query: {query}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Serper API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Serper API unexpected error: {e}")
            return None

    async def search_images(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """Search for images"""
        return await self.search(query, num_results, "images")

    async def search_news(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """Search for news articles"""
        return await self.search(query, num_results, "news")

    def format_results(self, results: Dict) -> str:
        """Format search results into a readable string"""
        if not results or "organic" not in results:
            return "No results found."

        formatted = []
        for result in results["organic"][:5]:
            title = result.get("title", "No title")
            link = result.get("link", "")
            snippet = result.get("snippet", "No description")
            formatted.append(f"- {title}\n  {snippet}\n  {link}")

        return "\n\n".join(formatted)


# Global search service instance
search_service = SearchService()


async def search_web(query: str, num_results: int = 10) -> Optional[Dict]:
    """Convenience function to perform web search"""
    return await search_service.search(query, num_results)


async def get_search_context(query: str, max_results: int = 3) -> str:
    """Get formatted search context for LLM prompts"""
    results = await search_web(query, max_results)
    if not results:
        return f"No search results available for: {query}"

    service = SearchService()
    formatted = service.format_results(results)
    return f"Search results for '{query}':\n\n{formatted}"
