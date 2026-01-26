"""
LLM Service - Integrates with DeepSeek API for real AI responses.
Falls back to MockLLM if API key is not configured.
"""

import httpx
import asyncio
import logging
from typing import List, Dict, Optional
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_ENABLED,
    AGENT_TIMEOUT,
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with DeepSeek API"""

    def __init__(self):
        self.base_url = DEEPSEEK_BASE_URL
        self.api_key = DEEPSEEK_API_KEY
        self.model = DEEPSEEK_MODEL
        self.enabled = DEEPSEEK_ENABLED
        self.timeout = AGENT_TIMEOUT

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[str]:
        """Generate a response from DeepSeek API"""
        if not self.enabled:
            logger.warning("DeepSeek API not configured, using mock responses")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            logger.error("DeepSeek API request timed out")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(
                f"DeepSeek API error: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"DeepSeek API unexpected error: {e}")
            return None

    async def generate_agent_response(
        self,
        agent_name: str,
        agent_role: str,
        agent_style: str,
        agent_policy: str,
        user_message: str,
        thread_history: Optional[List[Dict]] = None,
    ) -> Optional[str]:
        """Generate a response tailored to a specific agent"""
        # Build system prompt based on agent configuration
        system_prompt = self._build_system_prompt(
            agent_name, agent_role, agent_style, agent_policy
        )

        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]

        # Add thread context if available
        if thread_history:
            for msg in thread_history[-5:]:  # Last 5 messages for context
                role = "assistant" if msg.get("type") == "agent" else "user"
                messages.append({"role": role, "content": msg.get("text", "")})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Generate response
        return await self.generate(messages, temperature=0.7)

    def _build_system_prompt(
        self, name: str, role: str, style: str, policy: str
    ) -> str:
        """Build a system prompt for an agent"""
        return f"""You are {name}, an AI agent with the following configuration:

ROLE: {role}

POLICY: {policy}

STYLE: {style}

IMPORTANT GUIDELINES:
- Respond in a way that matches your defined style and role
- Keep responses concise and Twitter-friendly (under 500 words when possible)
- Use markdown formatting for better readability
- If you need to provide code, use proper code blocks
- Stay in character as {name} at all times
- Do not give medical, legal, or financial advice
- Be helpful, accurate, and safe"""


# Global LLM service instance
llm_service = LLMService()


async def generate_agent_response(
    agent_name: str,
    agent_role: str,
    agent_style: str,
    agent_policy: str,
    user_message: str,
    thread_history: Optional[List[Dict]] = None,
) -> Optional[str]:
    """Convenience function to generate agent response"""
    return await llm_service.generate_agent_response(
        agent_name, agent_role, agent_style, agent_policy, user_message, thread_history
    )


class MockLLM:
    """Fallback Mock LLM for when API is not configured"""

    @staticmethod
    def generate_response(
        agent, context: str, thread_history: List[Dict] = None
    ) -> str:
        """Generate a mock response based on agent type"""
        agent_id = agent.id if hasattr(agent, "id") else agent
        context_short = context[:200]

        if hasattr(agent, "mock_responses") and agent.mock_responses:
            import random

            responses = [
                resp.replace("{context}", context_short)
                for resp in agent.mock_responses
            ]
            return random.choice(responses)

        responses = {
            "grok": MockLLM._grok_response(context),
            "factcheck": MockLLM._factcheck_response(context),
            "summarizer": MockLLM._summarizer_response(context),
            "writer": MockLLM._writer_response(context),
            "dev": MockLLM._dev_response(context),
            "analyst": MockLLM._analyst_response(context),
            "researcher": MockLLM._researcher_response(context),
            "coach": MockLLM._coach_response(context),
        }

        return responses.get(
            agent_id,
            f"Hi! I'm {agent_id if isinstance(agent_id, str) else 'AI'}. I received: {context[:100]}...",
        )

    @staticmethod
    def _grok_response(context: str) -> str:
        import random

        responses = [
            f"Alright, here's the deal: {context[:50]}... is basically about understanding the fundamentals. Keep it simple.",
            f"Look, {context[:40]}... isn't rocket science. Break it down: 1) Identify the issue, 2) Apply common sense, 3) Execute.",
            f"Real talk: {context[:45]}... comes down to priorities. What matters most? Cut the fluff and focus there.",
            f"Hot take: {context[:35]}... is overrated. Experiment fast, fail faster, learn fastest.",
        ]
        return random.choice(responses)

    @staticmethod
    def _factcheck_response(context: str) -> str:
        return f"🔍 **Claim Analysis**\n\n**Points to verify:**\n• Specific data points mentioned\n• Timeline accuracy\n• Source attribution\n\n**Status:** Requires fact-checking from reliable sources."

    @staticmethod
    def _summarizer_response(context: str) -> str:
        return f"📋 **TL;DR**\n\n**Key Points:**\n• Main topic: {context[:30]}...\n• Core issue identified\n\n**Action Items:**\n• [ ] Review findings\n• [ ] Identify next steps"

    @staticmethod
    def _writer_response(context: str) -> str:
        return f"✍️ **Here are 3 versions:**\n\n**Punchy:**\n{context[:40]}... but make it unforgettable.\n\n**Professional:**\nRegarding {context[:35]}... , a structured approach yields optimal results.\n\n**Casual:**\nSo {context[:30]}... ? Keep it real."

    @staticmethod
    def _dev_response(context: str) -> str:
        return f"⚡ **Technical Solution**\n\n```python\n# Approach for: {context[:30]}...\ndef solution():\n    problem = extract_core_issue()\n    return build_and_test(problem)\n```\n\n**Notes:** Keep it modular and testable."

    @staticmethod
    def _analyst_response(context: str) -> str:
        return f"📊 **Decision Matrix**\n\n| Criteria | Option A | Option B |\n|----------|----------|----------|\n| Cost     | Low      | Medium   |\n| Time     | Fast     | Medium   |\n\n**Recommendation:** Evaluate based on your priorities for {context[:25]}..."

    @staticmethod
    def _researcher_response(context: str) -> str:
        return f"🔬 **Research Summary**\n\n**Background on {context[:40]}...**\n\n1. Key findings from recent studies\n2. Expert consensus on the topic\n3. Areas requiring further investigation\n\n**Bottom Line:** Well-documented with clear guidelines available."

    @staticmethod
    def _coach_response(context: str) -> str:
        return f"🎯 **Coaching Framework**\n\n**Your Goal:** {context[:40]}...\n\n**Steps:**\n1. Clarify exactly what you want\n2. Break into weekly milestones\n3. Start with smallest action today\n\n**You've got this! Progress > Perfection.**"
