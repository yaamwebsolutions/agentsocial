"""
Media Service - Integrates with KlingAI, Pexels, Pixabay, and Unsplash.
Provides image and video generation/retrieval capabilities.
"""
import httpx
import logging
from typing import Optional, Dict, List
from config import (
    KLINGAI_ACCESS_KEY, KLINGAI_SECRET_KEY, KLINGAI_API_URL, KLINGAI_ENABLED,
    PEXELS_API_KEY, PEXELS_ENABLED,
    PIXABAY_API_KEY, PIXABAY_ENABLED,
    UNSPLASH_ACCESS_KEY, UNSPLASH_ENABLED,
    AGENT_TIMEOUT
)

logger = logging.getLogger(__name__)


class KlingAIService:
    """Service for KlingAI video and image generation"""

    def __init__(self):
        self.access_key = KLINGAI_ACCESS_KEY
        self.secret_key = KLINGAI_SECRET_KEY
        self.api_url = KLINGAI_API_URL
        self.enabled = KLINGAI_ENABLED
        self.timeout = 60  # Longer timeout for generation

    async def generate_image(
        self,
        prompt: str,
        image_size: str = "16:9",
        num_images: int = 1,
    ) -> Optional[Dict]:
        """Generate an image using KlingAI"""
        if not self.enabled:
            logger.warning("KlingAI not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/videos/image2video",
                    headers={"Authorization": f"Bearer {self.access_key}"},
                    json={
                        "prompt": prompt,
                        "image_size": image_size,
                        "num_images": num_images,
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"KlingAI image generation error: {e}")
            return None

    async def text_to_video(
        self,
        prompt: str,
        duration: int = 5,
    ) -> Optional[Dict]:
        """Generate a video from text prompt using KlingAI"""
        if not self.enabled:
            logger.warning("KlingAI not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/videos/text2video",
                    headers={"Authorization": f"Bearer {self.access_key}"},
                    json={
                        "prompt": prompt,
                        "duration": duration,
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"KlingAI video generation error: {e}")
            return None


class PexelsService:
    """Service for Pexels stock photos and videos"""

    def __init__(self):
        self.api_key = PEXELS_API_KEY
        self.enabled = PEXELS_ENABLED and PEXELS_API_KEY != "your-pexels-key"
        self.timeout = AGENT_TIMEOUT

    async def search_photos(
        self,
        query: str,
        per_page: int = 10,
    ) -> Optional[Dict]:
        """Search for photos on Pexels"""
        if not self.enabled:
            logger.warning("Pexels not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": self.api_key},
                    params={
                        "query": query,
                        "per_page": per_page,
                        "orientation": "landscape",
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Pexels search error: {e}")
            return None

    async def search_videos(
        self,
        query: str,
        per_page: int = 10,
    ) -> Optional[Dict]:
        """Search for videos on Pexels"""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.pexels.com/videos/search",
                    headers={"Authorization": self.api_key},
                    params={
                        "query": query,
                        "per_page": per_page,
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Pexels video search error: {e}")
            return None


class PixabayService:
    """Service for Pixabay stock media"""

    def __init__(self):
        self.api_key = PIXABAY_API_KEY
        self.enabled = PIXABAY_ENABLED and PIXABAY_API_KEY != "your-pixabay-key"
        self.timeout = AGENT_TIMEOUT

    async def search_images(
        self,
        query: str,
        per_page: int = 10,
    ) -> Optional[List[Dict]]:
        """Search for images on Pixabay"""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://pixabay.com/api/",
                    params={
                        "key": self.api_key,
                        "q": query,
                        "per_page": per_page,
                        "image_type": "photo",
                        "safesearch": "true",
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("hits", [])
        except Exception as e:
            logger.error(f"Pixabay search error: {e}")
            return None

    async def search_videos(
        self,
        query: str,
        per_page: int = 10,
    ) -> Optional[List[Dict]]:
        """Search for videos on Pixabay"""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://pixabay.com/api/videos/",
                    params={
                        "key": self.api_key,
                        "q": query,
                        "per_page": per_page,
                        "video_type": "film",
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("hits", [])
        except Exception as e:
            logger.error(f"Pixabay video search error: {e}")
            return None


class UnsplashService:
    """Service for Unsplash stock photos"""

    def __init__(self):
        self.access_key = UNSPLASH_ACCESS_KEY
        self.enabled = UNSPLASH_ENABLED and UNSPLASH_ACCESS_KEY != "your-unsplash-key"
        self.timeout = AGENT_TIMEOUT

    async def search_photos(
        self,
        query: str,
        per_page: int = 10,
    ) -> Optional[Dict]:
        """Search for photos on Unsplash"""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.unsplash.com/search/photos",
                    headers={
                        "Authorization": f"Client-ID {self.access_key}",
                    },
                    params={
                        "query": query,
                        "per_page": per_page,
                        "orientation": "landscape",
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Unsplash search error: {e}")
            return None

    async def get_random_photo(self, query: str = "") -> Optional[Dict]:
        """Get a random photo from Unsplash"""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if query:
                    params["query"] = query

                response = await client.get(
                    "https://api.unsplash.com/photos/random",
                    headers={
                        "Authorization": f"Client-ID {self.access_key}",
                    },
                    params=params,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Unsplash random photo error: {e}")
            return None


class MediaService:
    """Unified media service combining all media providers"""

    def __init__(self):
        self.klingai = KlingAIService()
        self.pexels = PexelsService()
        self.pixabay = PixabayService()
        self.unsplash = UnsplashService()

    async def search_images(
        self,
        query: str,
        per_page: int = 10,
        source: str = "auto",
    ) -> List[Dict]:
        """
        Search for images across available providers.

        Args:
            query: Search query
            per_page: Number of results
            source: Provider to use (auto, pexels, pixabay, unsplash)

        Returns:
            List of image results with unified format
        """
        results = []

        # Try providers in order
        if source == "auto" or source == "pexels":
            pexels_data = await self.pexels.search_photos(query, per_page)
            if pexels_data and "photos" in pexels_data:
                for photo in pexels_data["photos"]:
                    results.append({
                        "url": photo["src"]["large"],
                        "thumbnail": photo["src"]["small"],
                        "photographer": photo["photographer"],
                        "source": "pexels",
                        "alt": photo.get("alt", query),
                    })

        if not results and (source == "auto" or source == "unsplash"):
            unsplash_data = await self.unsplash.search_photos(query, per_page)
            if unsplash_data and "results" in unsplash_data:
                for photo in unsplash_data["results"]:
                    results.append({
                        "url": photo["urls"]["regular"],
                        "thumbnail": photo["urls"]["small"],
                        "photographer": photo["user"]["name"],
                        "source": "unsplash",
                        "alt": photo.get("description") or photo.get("alt_description") or query,
                    })

        if not results and (source == "auto" or source == "pixabay"):
            pixabay_data = await self.pixabay.search_images(query, per_page)
            if pixabay_data:
                for photo in pixabay_data:
                    results.append({
                        "url": photo["webformatURL"],
                        "thumbnail": photo["previewURL"],
                        "photographer": photo["user"],
                        "source": "pixabay",
                        "alt": photo.get("tags", query),
                    })

        return results[:per_page]

    async def search_videos(
        self,
        query: str,
        per_page: int = 10,
        source: str = "auto",
    ) -> List[Dict]:
        """Search for videos across available providers"""
        results = []

        if source == "auto" or source == "pexels":
            pexels_data = await self.pexels.search_videos(query, per_page)
            if pexels_data and "videos" in pexels_data:
                for video in pexels_data["videos"]:
                    results.append({
                        "url": video["video_files"][0]["link"],
                        "thumbnail": video["image"],
                        "duration": video["duration"],
                        "source": "pexels",
                    })

        if not results and (source == "auto" or source == "pixabay"):
            pixabay_data = await self.pixabay.search_videos(query, per_page)
            if pixabay_data:
                for video in pixabay_data:
                    results.append({
                        "url": video["videos"]["medium"]["url"],
                        "thumbnail": video["picture_id"],
                        "duration": video.get("duration", 0),
                        "source": "pixabay",
                    })

        return results[:per_page]

    async def generate_image(self, prompt: str) -> Optional[Dict]:
        """Generate an image using KlingAI"""
        return await self.klingai.generate_image(prompt)


# Global media service instance
media_service = MediaService()
