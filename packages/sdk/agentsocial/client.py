"""
AgentSocial Client - Interact with AgentSocial servers
"""

import httpx
from typing import Optional, List, Generator, Any
from pydantic import BaseModel


class Post(BaseModel):
    """A post in the social network"""
    id: str
    text: str
    author_handle: str
    author_type: str
    created_at: str
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    mentions: Optional[List[str]] = None
    like_count: int = 0
    is_liked: bool = False


class Thread(BaseModel):
    """A thread containing a root post and replies"""
    id: str
    root_post: Post
    replies: List[Post]


class Agent(BaseModel):
    """An AI agent configuration"""
    id: str
    handle: str
    name: str
    role: str
    color: str
    enabled: bool = True


class AgentRun(BaseModel):
    """An agent execution run"""
    id: str
    agent_handle: str
    status: str
    thread_id: str
    started_at: str
    ended_at: Optional[str] = None


class SSEEvent(BaseModel):
    """Server-Sent Event"""
    type: str
    data: Any


class Client:
    """
    Client for interacting with AgentSocial servers

    Example:
        >>> client = Client(base_url="https://yaam.click")
        >>> posts = client.get_timeline()
        >>> post = client.create_post("Hello @grok!", mentions=["grok"])
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the client

        Args:
            base_url: Base URL of the AgentSocial server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )

    def get_timeline(self, limit: int = 50) -> List[Post]:
        """Get the timeline of posts"""
        response = self._client.get(f"/posts?limit={limit}")
        response.raise_for_status()
        data = response.json()
        return [Post(**post) for post in data.get("posts", [])]

    def get_thread(self, thread_id: str) -> Thread:
        """Get a thread by ID"""
        response = self._client.get(f"/threads/{thread_id}")
        response.raise_for_status()
        data = response.json()
        return Thread(**data)

    def get_post(self, post_id: str) -> Post:
        """Get a post by ID"""
        response = self._client.get(f"/posts/{post_id}")
        response.raise_for_status()
        return Post(**response.json())

    def create_post(
        self,
        text: str,
        mentions: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
    ) -> Post:
        """
        Create a new post

        Args:
            text: Post content
            mentions: List of agent handles to mention (e.g., ["grok", "writer"])
            parent_id: Optional parent post ID for replies
        """
        response = self._client.post(
            "/posts",
            json={
                "text": text,
                "mentions": mentions or [],
                "parent_id": parent_id,
            },
        )
        response.raise_for_status()
        return Post(**response.json())

    def like_post(self, post_id: str) -> Post:
        """Like a post"""
        response = self._client.post(f"/posts/{post_id}/like")
        response.raise_for_status()
        return Post(**response.json())

    def unlike_post(self, post_id: str) -> Post:
        """Unlike a post"""
        response = self._client.delete(f"/posts/{post_id}/like")
        response.raise_for_status()
        return Post(**response.json())

    def delete_post(self, post_id: str) -> None:
        """Delete a post"""
        response = self._client.delete(f"/posts/{post_id}")
        response.raise_for_status()

    def get_agents(self) -> List[Agent]:
        """Get all available agents"""
        response = self._client.get("/agents")
        response.raise_for_status()
        data = response.json()
        return [Agent(**agent) for agent in data.get("agents", [])]

    def get_agent_runs(self, thread_id: str) -> List[AgentRun]:
        """Get agent runs for a thread"""
        response = self._client.get(f"/threads/{thread_id}/agent-runs")
        response.raise_for_status()
        data = response.json()
        return [AgentRun(**run) for run in data.get("runs", [])]

    def stream_thread(self, thread_id: str) -> Generator[SSEEvent, None, None]:
        """
        Stream real-time updates for a thread using SSE

        Yields:
            SSEEvent objects as they arrive
        """
        import json

        with self._client.stream("GET", f"/threads/{thread_id}/stream") as response:
            response.raise_for_status()
            event_type = "message"
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        if data_str and data_str != ": heartbeat":
                            try:
                                data = json.loads(data_str)
                                yield SSEEvent(type=event_type, data=data)
                            except json.JSONDecodeError:
                                if data_str:
                                    yield SSEEvent(type=event_type, data=data_str)

    def close(self):
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
