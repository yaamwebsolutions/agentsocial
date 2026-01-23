"""
Orchestrator - Handles agent execution with real LLM integration.
Now supports DeepSeek API, web search, and web scraping.
"""
from typing import List, Optional
from models import Post, AgentRun, CreatePostResponse
from agents import get_agent, extract_mentions
from store import store, DataStore
from services import LLMService, search_web, scrape_content, generate_agent_response
from config import DEEPSEEK_ENABLED, USE_REAL_LLM
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates agent runs when posts contain mentions"""

    def __init__(self, data_store: DataStore):
        self.store = data_store
        self.llm_service = LLMService()

    async def process_post(self, text: str, parent_id: Optional[str] = None) -> CreatePostResponse:
        """Process a new post and trigger any mentioned agents"""

        # Create the post
        post = self.store.create_post(text, parent_id)

        # Extract mentions
        mentions = extract_mentions(text)

        # Create agent runs for each mention
        triggered_runs: List[AgentRun] = []

        for mention in mentions:
            agent = get_agent(mention)
            if agent:
                agent_run = self.store.create_agent_run(
                    agent_handle=agent.handle,
                    trigger_post_id=post.id,
                    thread_id=post.thread_id
                )
                triggered_runs.append(agent_run)

                # Trigger async agent execution
                asyncio.create_task(self._execute_agent(agent_run, post))

        return CreatePostResponse(post=post, triggered_agent_runs=triggered_runs)

    async def _execute_agent(self, agent_run: AgentRun, trigger_post: Post):
        """Execute an agent run asynchronously with real LLM"""
        try:
            # Update status to running
            self.store.update_agent_run_status(agent_run.id, "running")
            logger.info(f"Executing agent {agent_run.agent_handle} for post {trigger_post.id}")

            # Get agent configuration
            agent = get_agent(agent_run.agent_handle)
            if not agent:
                raise ValueError(f"Agent {agent_run.agent_handle} not found")

            # Get thread context
            context = self.store.get_thread_context(agent_run.thread_id, max_posts=5)

            # Generate response using real LLM or fallback to mock
            if USE_REAL_LLM and DEEPSEEK_ENABLED:
                logger.info(f"Using DeepSeek API for {agent.name}")
                response_text = await self._generate_with_llm(agent, trigger_post.text, context)
            else:
                logger.info(f"Using MockLLM for {agent.name}")
                response_text = await self._generate_mock(agent, trigger_post.text, context)

            if not response_text:
                raise ValueError("No response generated")

            # Create agent reply post
            reply_post = self.store.create_agent_reply(
                agent_handle=agent.handle,
                text=response_text,
                parent_id=trigger_post.id,
                thread_id=agent_run.thread_id
            )

            # Update agent run as completed
            self.store.update_agent_run_status(
                agent_run.id,
                "done",
                output_post_id=reply_post.id
            )

            logger.info(f"Agent {agent.name} completed successfully")

        except Exception as e:
            logger.error(f"Error executing agent {agent_run.agent_handle}: {e}")
            # Mark as error
            self.store.update_agent_run_status(agent_run.id, "error")
            # Create error reply
            agent = get_agent(agent_run.agent_handle) if agent_run.agent_handle else None
            error_text = f"❌ Error processing request: {str(e)}"
            self.store.create_agent_reply(
                agent_handle=agent.handle if agent else "@unknown",
                text=error_text,
                parent_id=trigger_post.id,
                thread_id=agent_run.thread_id
            )

    async def _generate_with_llm(
        self,
        agent,
        user_message: str,
        thread_history: List[dict]
    ) -> Optional[str]:
        """Generate response using DeepSeek API"""
        response = await generate_agent_response(
            agent_name=agent.name,
            agent_role=agent.role,
            agent_style=agent.style,
            agent_policy=agent.policy,
            user_message=user_message,
            thread_history=thread_history,
        )

        if response:
            return response

        # Fallback to mock if LLM fails
        logger.warning(f"LLM call failed for {agent.name}, falling back to mock")
        return await self._generate_mock(agent, user_message, thread_history)

    async def _generate_mock(
        self,
        agent,
        user_message: str,
        thread_history: List[dict]
    ) -> str:
        """Generate mock response (fallback)"""
        # Import MockLLM locally for fallback
        from services.llm_service import MockLLM
        return MockLLM.generate_response(agent, user_message, thread_history)

    async def search_and_respond(
        self,
        query: str,
        agent_handle: str,
        thread_id: str,
    ) -> Optional[str]:
        """
        Perform web search and return formatted results.
        Useful for @researcher and @factcheck agents.
        """
        results = await search_web(query, num_results=5)
        if not results:
            return None

        # Format results
        formatted = []
        for result in results.get("organic", [])[:5]:
            title = result.get("title", "No title")
            snippet = result.get("snippet", "No description")
            link = result.get("link", "")
            formatted.append(f"• [{title}]({link})\n  {snippet}")

        return "\n\n".join(formatted)

    async def scrape_and_respond(
        self,
        url: str,
        agent_handle: str,
        thread_id: str,
    ) -> Optional[str]:
        """
        Scrape a URL and return extracted content.
        Useful for @researcher agent.
        """
        content = await scrape_content(url)
        if not content:
            return None

        return f"""**Scraped from:** {url}

**Title:** {content.get('title', 'No title')}

**Content:**
{content.get('text', '')[:2000]}...
"""


# Global orchestrator instance
orchestrator = Orchestrator(store)
