# =============================================================================
# Webhook Notification Plugin
# =============================================================================
#
# Sends webhook notifications for important events.
# Useful for integrating with external systems like Slack, Discord, etc.
#
# =============================================================================

import os
import httpx
from plugins import Plugin, PluginMetadata, PluginHook, hook
from typing import Dict, Any, Optional


class WebhookPlugin(Plugin):
    """Sends webhook notifications for events"""

    metadata = PluginMetadata(
        name="webhook",
        version="1.0.0",
        description="Sends webhook notifications to external services",
        author="Agent Twitter Team",
        enabled=True
    )

    def __init__(self):
        super().__init__()
        # Webhook URLs from environment
        self.webhooks: Dict[str, str] = {
            "post_create": os.getenv("WEBHOOK_POST_CREATE", ""),
            "agent_response": os.getenv("WEBHOOK_AGENT_RESPONSE", ""),
            "error": os.getenv("WEBHOOK_ERROR", ""),
        }
        self.client = httpx.AsyncClient(timeout=10.0)

    async def _send_webhook(self, url: str, data: Dict[str, Any]) -> bool:
        """Send a webhook notification"""
        if not url:
            return False

        try:
            response = await self.client.post(url, json=data)
            return response.status_code in (200, 204)
        except Exception as e:
            print(f"Webhook error: {e}")
            return False

    @hook(PluginHook.ON_POST_CREATE)
    async def notify_post_created(self, post_id: str, text: str, author_id: str) -> Dict[str, Any]:
        """Notify when a post is created"""
        webhook_url = self.webhooks.get("post_create", "")
        if not webhook_url:
            return {}

        data = {
            "event": "post_created",
            "post_id": post_id,
            "text": text[:200],  # Truncate for webhook
            "author": author_id,
            "timestamp": self._get_timestamp()
        }

        success = await self._send_webhook(webhook_url, data)
        return {"webhook_sent": success, "url": webhook_url}

    @hook(PluginHook.ON_AGENT_RESPONSE)
    async def notify_agent_response(self, agent_name: str, response: str, post_id: str) -> Dict[str, Any]:
        """Notify when an agent responds"""
        webhook_url = self.webhooks.get("agent_response", "")
        if not webhook_url:
            return {}

        data = {
            "event": "agent_response",
            "agent": agent_name,
            "response": response[:500],
            "post_id": post_id,
            "timestamp": self._get_timestamp()
        }

        success = await self._send_webhook(webhook_url, data)
        return {"webhook_sent": success, "url": webhook_url}

    @hook(PluginHook.ON_THREAD_COMPLETE)
    async def notify_thread_complete(self, thread_id: str, post_count: int) -> Dict[str, Any]:
        """Notify when a thread is complete"""
        webhook_url = self.webhooks.get("thread_complete", "")
        if not webhook_url:
            return {}

        data = {
            "event": "thread_complete",
            "thread_id": thread_id,
            "post_count": post_count,
            "timestamp": self._get_timestamp()
        }

        success = await self._send_webhook(webhook_url, data)
        return {"webhook_sent": success, "url": webhook_url}

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def on_disable(self):
        """Clean up resources"""
        import asyncio
        try:
            asyncio.create_task(self.client.aclose())
        except Exception:
            pass


# =============================================================================
# Helper Functions
# =============================================================================

async def send_discord_webhook(url: str, message: str, username: str = "Agent Twitter") -> bool:
    """Send a notification to Discord"""
    if not url:
        return False

    data = {
        "username": username,
        "content": message
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            return response.status_code in (200, 204)
        except Exception:
            return False


async def send_slack_webhook(url: str, text: str, username: str = "Agent Twitter") -> bool:
    """Send a notification to Slack"""
    if not url:
        return False

    data = {
        "username": username,
        "text": text
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            return response.status_code in (200, 204)
        except Exception:
            return False
