"""
Scraping Service - Integrates with ScraperAPI for web scraping.
Allows agents to fetch and extract content from web pages.
"""

import httpx
import logging
from typing import Optional, Dict
from config import SCRAPERAPI_KEY, SCRAPERAPI_URL, SCRAPERAPI_ENABLED, AGENT_TIMEOUT

logger = logging.getLogger(__name__)


class ScrapingService:
    """Service for interacting with ScraperAPI"""

    def __init__(self):
        self.api_url = SCRAPERAPI_URL
        self.api_key = SCRAPERAPI_KEY
        self.enabled = SCRAPERAPI_ENABLED
        self.timeout = AGENT_TIMEOUT + 10  # Add buffer for scraping

    async def scrape(
        self,
        url: str,
        render_js: bool = False,
        country_code: str = "us",
        premium: bool = False,
    ) -> Optional[str]:
        """
        Scrape a web page using ScraperAPI.

        Args:
            url: The URL to scrape
            render_js: Whether to render JavaScript (requires premium)
            country_code: Country code for geo-targeting
            premium: Use premium proxies

        Returns:
            HTML content of the page or None if error
        """
        if not self.enabled:
            logger.warning("ScraperAPI not configured")
            return None

        try:
            # ScraperAPI format: https://api.scraperapi.com/?api_key={key}&url={url}&...
            params = {
                "api_key": self.api_key,
                "url": url,
                "country_code": country_code,
                "render_js": "true" if render_js else "false",
                "premium": "true" if premium else "false",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.api_url,
                    params=params,
                )
                response.raise_for_status()
                return response.text

        except httpx.TimeoutException:
            logger.error(f"ScraperAPI request timed out for URL: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"ScraperAPI error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"ScraperAPI unexpected error: {e}")
            return None

    async def scrape_text(
        self,
        url: str,
        extract_links: bool = False,
    ) -> Optional[Dict]:
        """
        Scrape a web page and extract readable text content.

        Args:
            url: The URL to scrape
            extract_links: Whether to extract links as well

        Returns:
            Dictionary with title, text, and optionally links
        """
        html = await self.scrape(url)
        if not html:
            return None

        try:
            from html.parser import HTMLParser
            import re

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self.title = ""
                    self.in_title = False
                    self.links = []
                    self.current_link = None

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "title":
                        self.in_title = True
                    elif tag == "a" and "href" in attrs_dict:
                        self.current_link = attrs_dict["href"]

                def handle_endtag(self, tag):
                    if tag == "title":
                        self.in_title = False
                    elif tag == "a" and self.current_link:
                        self.links.append(self.current_link)
                        self.current_link = None

                def handle_data(self, data):
                    if self.in_title:
                        self.title = data.strip()
                    elif data.strip():
                        self.text.append(data.strip())

            parser = TextExtractor()
            parser.feed(html)

            # Clean up text
            text_blocks = [t for t in parser.text if len(t) > 20]
            text = " ".join(text_blocks[:50])  # Limit to 50 blocks

            result = {
                "title": parser.title,
                "text": text[:5000],  # Limit to 5000 chars
                "url": url,
            }

            if extract_links:
                result["links"] = parser.links[:20]  # Limit to 20 links

            return result

        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return {"title": "", "text": html[:2000], "url": url}


# Global scraping service instance
scraping_service = ScrapingService()


async def scrape_url(url: str, render_js: bool = False) -> Optional[str]:
    """Convenience function to scrape a URL"""
    return await scraping_service.scrape(url, render_js)


async def scrape_content(url: str) -> Optional[Dict]:
    """Convenience function to scrape and extract content"""
    return await scraping_service.scrape_text(url)
