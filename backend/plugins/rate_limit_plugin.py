# =============================================================================
# Rate Limiting Plugin
# =============================================================================
#
# Implements rate limiting for API endpoints and agent calls.
# Helps prevent abuse and manage resource usage.
#
# =============================================================================

import time
from collections import defaultdict
from plugins import Plugin, PluginMetadata, PluginHook, hook
from typing import Dict, Tuple


class RateLimitPlugin(Plugin):
    """Rate limits API calls and agent usage"""

    metadata = PluginMetadata(
        name="rate_limit",
        version="1.0.0",
        description="Rate limits API calls and agent usage",
        author="Agent Twitter Team",
        enabled=True
    )

    def __init__(self):
        super().__init__()
        # Store request counts: {user_id: {endpoint: [(timestamp, count)]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        # Rate limit configuration (requests per minute)
        self.limits: Dict[str, int] = {
            "default": 60,
            "/posts": 30,
            "/agents/prompt": 20,
            "/search/web": 10,
        }

        # Agent rate limits (calls per minute)
        self.agent_limits: Dict[str, int] = {
            "default": 10,
        }

        # Agent call tracking
        self.agent_calls: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(self, requests: list, window: int = 60) -> list:
        """Remove requests older than the time window"""
        cutoff = time.time() - window
        return [req for req in requests if req > cutoff]

    def _check_rate_limit(self, user_id: str, endpoint: str, limit: Optional[int] = None) -> Tuple[bool, int]:
        """Check if a request is within rate limits"""
        limit = limit or self.limits.get(endpoint, self.limits["default"])

        # Clean old requests
        self.requests[user_id][endpoint] = self._clean_old_requests(
            self.requests[user_id][endpoint]
        )

        # Check limit
        current_count = len(self.requests[user_id][endpoint])
        if current_count >= limit:
            return False, 0  # Rate limited

        # Add this request
        self.requests[user_id][endpoint].append(time.time())
        return True, limit - current_count - 1  # OK, remaining count

    @hook(PluginHook.ON_API_REQUEST)
    def check_api_rate_limit(self, user_id: str, endpoint: str, method: str = "GET") -> Dict[str, any]:
        """Check rate limit before processing API request"""
        # Only rate limit POST/PUT/DELETE for now
        if method == "GET":
            return {"allowed": True}

        allowed, remaining = self._check_rate_limit(user_id, endpoint)

        if not allowed:
            return {
                "allowed": False,
                "error": "Rate limit exceeded",
                "limit": self.limits.get(endpoint, self.limits["default"])
            }

        return {
            "allowed": True,
            "remaining": remaining
        }

    @hook(PluginHook.ON_AGENT_RESPONSE)
    def check_agent_rate_limit(self, agent_name: str, response: str, post_id: str) -> Dict[str, any]:
        """Track agent calls for rate limiting"""
        limit = self.agent_limits.get(agent_name, self.agent_limits["default"])

        # Clean old calls
        self.agent_calls[agent_name] = self._clean_old_requests(self.agent_calls[agent_name])

        # Check limit (this is post-response, so just tracking)
        self.agent_calls[agent_name].append(time.time())

        current = len(self.agent_calls[agent_name])

        return {
            "agent": agent_name,
            "calls_this_minute": current,
            "limit": limit,
            "near_limit": current >= limit * 0.8
        }

    def get_usage_stats(self, user_id: str) -> Dict[str, any]:
        """Get rate limit usage stats for a user"""
        stats = {}
        for endpoint, requests in self.requests[user_id].items():
            limit = self.limits.get(endpoint, self.limits["default"])
            # Clean old first
            requests = self._clean_old_requests(requests)
            stats[endpoint] = {
                "used": len(requests),
                "limit": limit,
                "remaining": max(0, limit - len(requests))
            }
        return stats

    def get_agent_stats(self, agent_name: str) -> Dict[str, any]:
        """Get rate limit stats for an agent"""
        calls = self._clean_old_requests(self.agent_calls[agent_name])
        limit = self.agent_limits.get(agent_name, self.agent_limits["default"])
        return {
            "agent": agent_name,
            "calls_this_minute": len(calls),
            "limit": limit,
            "remaining": max(0, limit - len(calls))
        }
