"""
Orchestrator - Handles agent execution with real LLM integration.
Now supports DeepSeek API, web search, web scraping, and slash commands.
"""
from typing import List, Optional, Dict
import re
from models import Post, AgentRun, CreatePostResponse
from agents import get_agent, extract_mentions
from store import store, DataStore
from services import LLMService, search_web, scrape_content, generate_agent_response
from services.media_service import media_service
from services.scraping_service import scraping_service
from services.email_service import email_service
from config import (
    DEEPSEEK_ENABLED, USE_REAL_LLM, KLINGAI_ENABLED,
    SERPER_ENABLED, SCRAPERAPI_ENABLED, RESEND_ENABLED
)
import asyncio
import logging

logger = logging.getLogger(__name__)


# Command patterns for parsing slash commands
COMMAND_PATTERNS = {
    'video': re.compile(r'/video\s+(.+?)(?:\s+(?:/|$)|$)', re.IGNORECASE),
    'image': re.compile(r'/image\s+(.+?)(?:\s+(?:/|$)|$)', re.IGNORECASE),
    'search': re.compile(r'/search\s+(.+?)(?:\s+(?:/|$)|$)', re.IGNORECASE),
    'scrape': re.compile(r'/scrape\s+(\S+)(?:\s+|$)', re.IGNORECASE),
    'email': re.compile(r'/email\s+(\S+)(?:\s+(.+))?', re.IGNORECASE),
}


class Command:
    """Represents a parsed slash command"""

    def __init__(self, command_type: str, args: Dict[str, str], full_match: str):
        self.type = command_type
        self.args = args
        self.full_match = full_match

    def __repr__(self):
        return f"Command({self.type}, {self.args})"


class Orchestrator:
    """Orchestrates agent runs when posts contain mentions and executes slash commands"""

    def __init__(self, data_store: DataStore):
        self.store = data_store
        self.llm_service = LLMService()

    def extract_commands(self, text: str) -> List[Command]:
        """
        Extract slash commands from post text.

        Returns a list of Command objects with their type and arguments.
        Supports: /video, /image, /search, /scrape, /email
        """
        commands = []

        # Check for /video command
        video_match = COMMAND_PATTERNS['video'].search(text)
        if video_match:
            prompt = video_match.group(1).strip()
            commands.append(Command('video', {'prompt': prompt}, video_match.group(0)))

        # Check for /image command
        image_match = COMMAND_PATTERNS['image'].search(text)
        if image_match:
            prompt = image_match.group(1).strip()
            commands.append(Command('image', {'prompt': prompt}, image_match.group(0)))

        # Check for /search command
        search_match = COMMAND_PATTERNS['search'].search(text)
        if search_match:
            query = search_match.group(1).strip()
            commands.append(Command('search', {'query': query}, search_match.group(0)))

        # Check for /scrape command
        scrape_match = COMMAND_PATTERNS['scrape'].search(text)
        if scrape_match:
            url = scrape_match.group(1).strip()
            commands.append(Command('scrape', {'url': url}, scrape_match.group(0)))

        # Check for /email command
        email_match = COMMAND_PATTERNS['email'].search(text)
        if email_match:
            email = email_match.group(1).strip()
            content = email_match.group(2).strip() if email_match.group(2) else ""
            commands.append(Command('email', {'to': email, 'content': content}, email_match.group(0)))

        return commands

    async def process_post(self, text: str, parent_id: Optional[str] = None) -> CreatePostResponse:
        """Process a new post and trigger any mentioned agents or execute commands"""

        # Extract commands before creating the post
        commands = self.extract_commands(text)

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

        # Execute commands asynchronously
        for command in commands:
            asyncio.create_task(self._execute_command(command, post))

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

    async def _execute_command(self, command: Command, trigger_post: Post):
        """Execute a slash command and create a reply post with the result"""
        try:
            logger.info(f"Executing command: {command.type} with args: {command.args}")

            if command.type == 'video':
                await self._execute_video_command(command, trigger_post)
            elif command.type == 'image':
                await self._execute_image_command(command, trigger_post)
            elif command.type == 'search':
                await self._execute_search_command(command, trigger_post)
            elif command.type == 'scrape':
                await self._execute_scrape_command(command, trigger_post)
            elif command.type == 'email':
                await self._execute_email_command(command, trigger_post)
            else:
                logger.warning(f"Unknown command type: {command.type}")

        except Exception as e:
            logger.error(f"Error executing command {command.type}: {e}")
            # Create error reply
            error_text = f"❌ Error executing `/{command.type}` command: {str(e)}"
            self.store.create_agent_reply(
                agent_handle="@system",
                text=error_text,
                parent_id=trigger_post.id,
                thread_id=trigger_post.thread_id
            )

    async def _execute_video_command(self, command: Command, trigger_post: Post):
        """Execute /video command - generate video using KlingAI"""
        prompt = command.args['prompt']

        if not KLINGAI_ENABLED:
            reply_text = f"🎬 **Video Generation**\n\n⚠️ Video generation service is not enabled. Please configure KLINGAI credentials.\n\nPrompt: *{prompt}*"
        else:
            result = await media_service.klingai.text_to_video(prompt)
            if result and 'data' in result:
                video_url = result['data'].get('url', '')
                reply_text = f"🎬 **Video Generated**\n\n**Prompt:** {prompt}\n\n[Watch Video]({video_url})\n\n✅ Video generation complete!"
            else:
                reply_text = f"🎬 **Video Generation**\n\n⚠️ Failed to generate video. Please try again or check the prompt.\n\nPrompt: *{prompt}*"

        self.store.create_agent_reply(
            agent_handle="@video",
            text=reply_text,
            parent_id=trigger_post.id,
            thread_id=trigger_post.thread_id
        )

    async def _execute_image_command(self, command: Command, trigger_post: Post):
        """Execute /image command - generate image using KlingAI"""
        prompt = command.args['prompt']

        if not KLINGAI_ENABLED:
            reply_text = f"🎨 **Image Generation**\n\n⚠️ Image generation service is not enabled. Please configure KLINGAI credentials.\n\nPrompt: *{prompt}*"
        else:
            result = await media_service.klingai.generate_image(prompt)
            if result and 'data' in result:
                # Handle image result
                images = result['data']
                if images and len(images) > 0:
                    image_url = images[0].get('url', '')
                    reply_text = f"🎨 **Image Generated**\n\n**Prompt:** {prompt}\n\n![Generated Image]({image_url})\n\n✅ Image generation complete!"
                else:
                    reply_text = f"🎨 **Image Generation**\n\n⚠️ No image returned. Please try again.\n\nPrompt: *{prompt}*"
            else:
                reply_text = f"🎨 **Image Generation**\n\n⚠️ Failed to generate image. Please try again or check the prompt.\n\nPrompt: *{prompt}*"

        self.store.create_agent_reply(
            agent_handle="@image",
            text=reply_text,
            parent_id=trigger_post.id,
            thread_id=trigger_post.thread_id
        )

    async def _execute_search_command(self, command: Command, trigger_post: Post):
        """Execute /search command - search the web"""
        query = command.args['query']

        if not SERPER_ENABLED:
            reply_text = f"🔍 **Web Search**\n\n⚠️ Search service is not enabled. Please configure SERPER_API_KEY.\n\nQuery: *{query}*"
        else:
            results = await search_web(query, num_results=5)
            if results and 'organic' in results:
                formatted_results = []
                for result in results['organic'][:5]:
                    title = result.get('title', 'No title')
                    link = result.get('link', '')
                    snippet = result.get('snippet', 'No description')
                    formatted_results.append(f"**[{title}]({link})**\n{snippet}")

                reply_text = f"🔍 **Search Results for:** {query}\n\n" + "\n\n".join(formatted_results)
            else:
                reply_text = f"🔍 **Web Search**\n\n⚠️ No results found. Please try a different query.\n\nQuery: *{query}*"

        self.store.create_agent_reply(
            agent_handle="@search",
            text=reply_text,
            parent_id=trigger_post.id,
            thread_id=trigger_post.thread_id
        )

    async def _execute_scrape_command(self, command: Command, trigger_post: Post):
        """Execute /scrape command - scrape a webpage"""
        url = command.args['url']

        if not SCRAPERAPI_ENABLED:
            reply_text = f"📄 **Web Scraping**\n\n⚠️ Scraping service is not enabled. Please configure SCRAPERAPI_KEY.\n\nURL: {url}"
        else:
            content = await scraping_service.scrape_text(url, extract_links=True)
            if content:
                title = content.get('title', 'No title')
                text = content.get('text', '')[:1500]
                links = content.get('links', [])[:5]

                links_text = "\n".join([f"- {link}" for link in links]) if links else "No links found"

                reply_text = f"📄 **Scraped:** {url}\n\n**Title:** {title}\n\n**Content:**\n{text}...\n\n**Links:**\n{links_text}"
            else:
                reply_text = f"📄 **Web Scraping**\n\n⚠️ Failed to scrape URL. Please check the URL and try again.\n\nURL: {url}"

        self.store.create_agent_reply(
            agent_handle="@scrape",
            text=reply_text,
            parent_id=trigger_post.id,
            thread_id=trigger_post.thread_id
        )

    async def _execute_email_command(self, command: Command, trigger_post: Post):
        """Execute /email command - send content as email"""
        to_email = command.args['to']
        content = command.args.get('content', '')

        # If no content provided, use the original post text (without the command)
        if not content:
            # Remove the email command from the post text
            import re
            content = re.sub(r'/email\s+\S+\s*', '', trigger_post.text).strip() or "No additional content"

        if not RESEND_ENABLED:
            reply_text = f"📧 **Email**\n\n⚠️ Email service is not enabled. Please configure RESEND_API_KEY.\n\nTo: {to_email}"
        else:
            # Create HTML email
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>📧 Message from AgentSocial</h2>
                    </div>
                    <div class="content">
                        <p>{content.replace(chr(10), '<br>')}</p>
                    </div>
                </div>
            </body>
            </html>
            """

            message_id = await email_service.send_email(
                to=to_email,
                subject=f"Message from AgentSocial",
                html=html
            )

            if message_id:
                reply_text = f"📧 **Email Sent**\n\n✅ Successfully sent email to: {to_email}\n\n**Message ID:** {message_id}\n\n**Content:** {content}"
            else:
                reply_text = f"📧 **Email**\n\n⚠️ Failed to send email. Please check the recipient address and try again.\n\nTo: {to_email}"

        self.store.create_agent_reply(
            agent_handle="@email",
            text=reply_text,
            parent_id=trigger_post.id,
            thread_id=trigger_post.thread_id
        )

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
