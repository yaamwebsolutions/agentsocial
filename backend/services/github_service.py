"""
GitHub API Service
Handles all interactions with GitHub's API including repository data,
stargazers, commits, issues, releases, and search.
"""

import os
import httpx
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GitHubAPIException(Exception):
    """Custom exception for GitHub API errors"""

    pass


class RateLimitError(GitHubAPIException):
    """Raised when GitHub API rate limit is exceeded"""

    def __init__(self, reset_time: datetime):
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded. Resets at {reset_time}")


class GitHubService:
    """
    Service for interacting with GitHub API.
    Implements rate limiting, caching, and retry logic.
    """

    API_BASE = "https://api.github.com"

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.client = httpx.AsyncClient(headers=self._get_headers(), timeout=30.0)
        self._rate_limit_remaining = 5000
        self._rate_limit_reset = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization if token is available"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentTwitter/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Make a request to GitHub API with rate limit handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /repos/facebook/react)
            **kwargs: Additional arguments for httpx

        Returns:
            JSON response data

        Raises:
            RateLimitError: When rate limit is exceeded
            GitHubAPIException: For other API errors
        """
        if self._rate_limit_remaining <= 1:
            if self._rate_limit_reset:
                wait_time = (self._rate_limit_reset - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time:.0f}s")
                    await asyncio.sleep(wait_time)

        url = f"{self.API_BASE}{endpoint}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()

            # Update rate limit info from headers
            self._rate_limit_remaining = int(
                response.headers.get("x-ratelimit-remaining", 5000)
            )
            reset_ts = response.headers.get("x-ratelimit-reset")
            if reset_ts:
                self._rate_limit_reset = datetime.fromtimestamp(int(reset_ts))

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                reset_ts = e.response.headers.get("x-ratelimit-reset")
                if reset_ts:
                    raise RateLimitError(datetime.fromtimestamp(int(reset_ts)))
            raise GitHubAPIException(f"GitHub API error: {e.response.status_code}")

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a repository.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name

        Returns:
            Repository data dictionary
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}")

    async def get_star_count(self, owner: str, repo: str) -> int:
        """
        Get current star count for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Number of stars
        """
        data = await self.get_repository(owner, repo)
        return data.get("stargazers_count", 0)

    async def get_stargazers(
        self, owner: str, repo: str, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get stargazers for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Results per page (max 100)

        Returns:
            List of stargazer dictionaries
        """
        stargazers = []
        page = 1

        while True:
            data = await self._make_request(
                "GET",
                f"/repos/{owner}/{repo}/stargazers",
                params={"page": page, "per_page": per_page},
            )
            if not data:
                break
            stargazers.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return stargazers

    async def get_commits(
        self, owner: str, repo: str, since: Optional[str] = None, per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent commits for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            since: ISO 8601 timestamp (optional)
            per_page: Results per page

        Returns:
            List of commit dictionaries
        """
        params = {"per_page": per_page, "sha": "main"}
        if since:
            params["since"] = since

        return await self._make_request(
            "GET", f"/repos/{owner}/{repo}/commits", params=params
        )

    async def get_issues(
        self, owner: str, repo: str, state: str = "open", per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get issues for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            per_page: Results per page

        Returns:
            List of issue dictionaries
        """
        return await self._make_request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page},
        )

    async def get_releases(
        self, owner: str, repo: str, per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get releases for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Results per page

        Returns:
            List of release dictionaries
        """
        return await self._make_request(
            "GET", f"/repos/{owner}/{repo}/releases", params={"per_page": per_page}
        )

    async def get_readme(
        self, owner: str, repo: str, default_branch: str = "main"
    ) -> str:
        """
        Get README content for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            default_branch: Default branch name

        Returns:
            README content as string
        """
        try:
            # Try default branch first
            data = await self._make_request(
                "GET",
                f"/repos/{owner}/{repo}/readme",
                headers={"Accept": "application/vnd.github.raw"},
            )
            return data
        except GitHubAPIException:
            # Fallback to trying common README filenames
            for filename in ["README.md", "README.rst", "README.txt"]:
                try:
                    return await self._make_request(
                        "GET",
                        f"/repos/{owner}/{repo}/contents/{filename}",
                        headers={"Accept": "application/vnd.github.raw"},
                    )
                except GitHubAPIException:
                    continue
            return ""

    async def search_repositories(
        self, query: str, sort: str = "stars", order: str = "desc", per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for repositories on GitHub.

        Args:
            query: Search query
            sort: Sort field (stars, forks, updated)
            order: Sort order (desc, asc)
            per_page: Results per page

        Returns:
            List of repository dictionaries
        """
        return await self._make_request(
            "GET",
            "/search/repositories",
            params={"q": query, "sort": sort, "order": order, "per_page": per_page},
        )

    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Get a user's GitHub profile.

        Args:
            username: GitHub username

        Returns:
            User profile dictionary
        """
        return await self._make_request("GET", f"/users/{username}")

    async def get_user_repos(
        self, username: str, type: str = "owner", per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get repositories for a user.

        Args:
            username: GitHub username
            type: Repository type (owner, member, all)
            per_page: Results per page

        Returns:
            List of repository dictionaries
        """
        return await self._make_request(
            "GET",
            f"/users/{username}/repos",
            params={"type": type, "per_page": per_page, "sort": "updated"},
        )

    async def get_user_repos_authed(
        self, visibility: str = "public", per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get repositories for authenticated user.

        Args:
            visibility: Repository visibility (all, public, private)
            per_page: Results per page

        Returns:
            List of repository dictionaries
        """
        return await self._make_request(
            "GET",
            "/user/repos",
            params={"visibility": visibility, "per_page": per_page, "sort": "updated"},
        )

    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Get programming languages used in a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary mapping language to byte count
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/languages")

    async def get_topics(self, owner: str, repo: str) -> List[str]:
        """
        Get topics for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of topic strings
        """
        data = await self.get_repository(owner, repo)
        return data.get("topics", [])


# Global instance
github_service = GitHubService()


def get_github_service() -> GitHubService:
    """Get the global GitHub service instance"""
    return github_service
