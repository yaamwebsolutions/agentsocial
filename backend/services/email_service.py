"""
Email Service - Integrates with Resend for email notifications.
Allows agents to send email notifications and reports.
"""
import httpx
import logging
from typing import Optional, List, Dict
from config import RESEND_API_KEY, RESEND_ENABLED

logger = logging.getLogger(__name__)


class EmailService:
    """Service for interacting with Resend Email API"""

    def __init__(self):
        self.api_key = RESEND_API_KEY
        self.api_url = "https://api.resend.com/emails"
        self.enabled = RESEND_ENABLED

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        from_email: str = "AgentTwitter <noreply@agenttwitter.app>",
        text: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send an email using Resend API.

        Args:
            to: Recipient email address or list of addresses
            subject: Email subject
            html: HTML content of the email
            from_email: Sender email address
            text: Plain text content (optional)

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("Resend API not configured")
            return None

        # Normalize to list
        if isinstance(to, str):
            to = [to]

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "from": from_email,
                    "to": to,
                    "subject": subject,
                    "html": html,
                }

                if text:
                    payload["text"] = text

                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("id")

        except httpx.HTTPStatusError as e:
            logger.error(f"Resend API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Resend API unexpected error: {e}")
            return None

    async def send_agent_response(
        self,
        to: str,
        agent_name: str,
        agent_handle: str,
        original_message: str,
        agent_response: str,
        thread_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send an email notification about an agent response.

        Args:
            to: Recipient email
            agent_name: Name of the agent that responded
            agent_handle: Handle of the agent (e.g., @grok)
            original_message: The original user message
            agent_response: The agent's response
            thread_url: Link to the thread (optional)

        Returns:
            Message ID if successful
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .agent-badge {{ display: inline-block; background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; }}
                .original-message {{ background: white; padding: 15px; border-left: 4px solid #ddd; margin: 15px 0; }}
                .agent-response {{ background: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50; margin: 15px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🤖 New Response from {agent_name}</h2>
                </div>
                <div class="content">
                    <p>You received a response from <span class="agent-badge">{agent_handle}</span></p>

                    <h3>Your message:</h3>
                    <div class="original-message">
                        {original_message}
                    </div>

                    <h3>Response:</h3>
                    <div class="agent-response">
                        {agent_response.replace(chr(10), '<br>')}
                    </div>

                    {f'<a href="{thread_url}" class="button">View Thread</a>' if thread_url else ''}
                </div>
                <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
                    Sent by AgentTwitter - Your AI Agent Platform
                </p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to,
            subject=f"New response from {agent_handle}",
            html=html,
            text=f"You received a response from {agent_handle}\n\nYour message:\n{original_message}\n\nResponse:\n{agent_response}",
        )

    async def send_digest(
        self,
        to: str,
        agent_interactions: List[Dict],
        period: str = "daily",
    ) -> Optional[str]:
        """
        Send a digest email of agent interactions.

        Args:
            to: Recipient email
            agent_interactions: List of interaction dictionaries
            period: Time period (daily, weekly)

        Returns:
            Message ID if successful
        """
        interactions_html = ""
        for interaction in agent_interactions[:10]:
            interactions_html += f"""
            <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                <strong>{interaction.get('agent_handle', 'Agent')}</strong>
                <p style="margin: 5px 0; color: #666;">{interaction.get('original_message', '')[:100]}...</p>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 Your {period.capitalize()} Agent Digest</h2>
                    <p>You had {len(agent_interactions)} agent interactions</p>
                </div>
                <div style="padding: 20px 0;">
                    <h3>Recent Interactions:</h3>
                    {interactions_html}
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to,
            subject=f"Your {period} agent digest",
            html=html,
        )


# Global email service instance
email_service = EmailService()
