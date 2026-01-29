#!/usr/bin/env python
"""
Agent Twitter - Comprehensive Test Bot
Tests all API endpoints and services automatically.
"""

import asyncio
import httpx
import json
import time
from typing import Dict
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"  # Change this for email tests


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


class TestBot:
    """Comprehensive test bot for Agent Twitter API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.results = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}
        self.test_data = {}

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    def _record_test(
        self, name: str, passed: bool, error: str = None, duration: float = 0
    ):
        self.results["tests"].append(
            {"name": name, "passed": passed, "error": error, "duration": duration}
        )
        if passed:
            self.results["passed"] += 1
            print_success(f"{name} ({duration:.2f}s)")
        else:
            self.results["failed"] += 1
            print_error(f"{name} - {error}")

    async def _get(self, endpoint: str, **kwargs) -> Dict:
        """Make a GET request"""
        try:
            response = await self.client.get(f"{self.base_url}{endpoint}", **kwargs)
            return {
                "status": response.status_code,
                "data": response.json() if response.text else None,
            }
        except Exception as e:
            return {"status": 0, "error": str(e)}

    async def _post(self, endpoint: str, **kwargs) -> Dict:
        """Make a POST request"""
        try:
            response = await self.client.post(f"{self.base_url}{endpoint}", **kwargs)
            return {
                "status": response.status_code,
                "data": response.json() if response.text else None,
            }
        except Exception as e:
            return {"status": 0, "error": str(e)}

    # ========================================================================
    # HEALTH & STATUS TESTS
    # ========================================================================

    async def test_health_check(self):
        """Test the health check endpoint"""
        start = time.time()
        result = await self._get("/health")
        duration = time.time() - start

        if result["status"] == 200 and result["data"].get("status") == "ok":
            self._record_test("Health Check", True, duration=duration)
        else:
            self._record_test(
                "Health Check",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    async def test_status_endpoint(self):
        """Test the status endpoint"""
        start = time.time()
        result = await self._get("/status")
        duration = time.time() - start

        if result["status"] == 200 and "services" in result.get("data", {}):
            self._record_test("Status Endpoint", True, duration=duration)
            print_info(
                f"  Services: {json.dumps(result['data']['services'], indent=2)}"
            )
        else:
            self._record_test(
                "Status Endpoint",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    async def test_root_endpoint(self):
        """Test the root endpoint"""
        start = time.time()
        result = await self._get("/")
        duration = time.time() - start

        if result["status"] == 200 and "endpoints" in result.get("data", {}):
            self._record_test("Root Endpoint", True, duration=duration)
        else:
            self._record_test(
                "Root Endpoint",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    # ========================================================================
    # AGENT TESTS
    # ========================================================================

    async def test_list_agents(self):
        """Test listing all agents"""
        start = time.time()
        result = await self._get("/agents")
        duration = time.time() - start

        if result["status"] == 200 and isinstance(result.get("data"), list):
            agents = result["data"]
            self._record_test(
                f"List Agents ({len(agents)} available)", True, duration=duration
            )
            self.test_data["agents"] = agents
            for agent in agents[:3]:  # Show first 3
                print_info(f"  - {agent.get('handle')}: {agent.get('name')}")
            if len(agents) > 3:
                print_info(f"  ... and {len(agents) - 3} more")
        else:
            self._record_test(
                "List Agents",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    async def test_get_agent(self):
        """Test getting a specific agent"""
        start = time.time()
        result = await self._get("/agents/grok")
        duration = time.time() - start

        if result["status"] == 200 and result["data"].get("id") == "grok":
            self._record_test("Get Agent (@grok)", True, duration=duration)
        else:
            self._record_test(
                "Get Agent (@grok)",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    # ========================================================================
    # POST TESTS
    # ========================================================================

    async def test_create_post(self):
        """Test creating a new post"""
        start = time.time()
        test_text = f"Test post from automated test bot at {datetime.now().strftime('%H:%M:%S')}"
        result = await self._post("/posts", json={"text": test_text})
        duration = time.time() - start

        if result["status"] == 200:
            post = result["data"].get("post", {})
            self.test_data["post_id"] = post.get("id")
            self._record_test("Create Post", True, duration=duration)
            print_info(f"  Post ID: {post.get('id')}")
        else:
            self._record_test(
                "Create Post",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    async def test_post_with_agent_mention(self):
        """Test creating a post with agent mention"""
        start = time.time()
        test_text = "@grok Tell me a joke about testing"
        result = await self._post("/posts", json={"text": test_text})
        duration = time.time() - start

        if result["status"] == 200:
            post = result["data"].get("post", {})
            agent_runs = result["data"].get("triggered_agent_runs", [])
            self.test_data["thread_id"] = post.get("id")
            self._record_test("Post with Agent Mention", True, duration=duration)
            print_info(f"  Triggered {len(agent_runs)} agent(s)")
            # Wait for agent to process
            await asyncio.sleep(2)
        else:
            self._record_test(
                "Post with Agent Mention",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    async def test_get_timeline(self):
        """Test getting the timeline"""
        start = time.time()
        result = await self._get("/timeline?limit=10")
        duration = time.time() - start

        if result["status"] == 200 and isinstance(result.get("data"), list):
            self._record_test(
                f"Get Timeline ({len(result['data'])} posts)", True, duration=duration
            )
        else:
            self._record_test(
                "Get Timeline",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    async def test_get_thread(self):
        """Test getting a thread"""
        if "thread_id" not in self.test_data:
            self.results["skipped"] += 1
            print_warning("Get Thread - Skipped (no thread_id)")
            return

        start = time.time()
        result = await self._get(f"/threads/{self.test_data['thread_id']}")
        duration = time.time() - start

        if result["status"] == 200:
            thread = result["data"]
            self._record_test(
                f"Get Thread ({len(thread.get('replies', []))} replies)",
                True,
                duration=duration,
            )
        else:
            self._record_test(
                "Get Thread",
                False,
                str(result.get("error", "Unexpected response")),
                duration,
            )

    # ========================================================================
    # AGENT PROMPT TESTS
    # ========================================================================

    async def test_agent_prompt(self):
        """Test direct agent prompting"""
        start = time.time()
        result = await self._post(
            "/agents/prompt",
            json={
                "agent_handle": "@grok",
                "prompt": "What is 2+2? Answer in one word.",
            },
        )
        duration = time.time() - start

        if result["status"] == 200 and result["data"].get("response"):
            self._record_test("Agent Direct Prompt", True, duration=duration)
            response = result["data"]["response"][:100]
            print_info(f"  Response: {response}...")
        else:
            self._record_test(
                "Agent Direct Prompt",
                False,
                str(result.get("error", "No response")),
                duration,
            )

    # ========================================================================
    # SEARCH TESTS
    # ========================================================================

    async def test_web_search(self):
        """Test web search"""
        start = time.time()
        result = await self._post(
            "/search/web", json={"query": "Python programming", "num_results": 5}
        )
        duration = time.time() - start

        if result["status"] == 200:
            data = result["data"]
            if "results" in data:
                self._record_test(
                    f"Web Search ({len(data['results'])} results)",
                    True,
                    duration=duration,
                )
                return
            elif "detail" in data and "not enabled" in data["detail"].lower():
                self.results["skipped"] += 1
                print_warning("Web Search - Skipped (service not enabled)")
                return
        self._record_test(
            "Web Search",
            False,
            str(result.get("error", "Unexpected response")),
            duration,
        )

    async def test_image_search(self):
        """Test image search"""
        start = time.time()
        result = await self._get("/search/images/nature?per_page=5")
        duration = time.time() - start

        if result["status"] == 200:
            data = result["data"]
            if "results" in data:
                self._record_test(
                    f"Image Search ({len(data['results'])} results)",
                    True,
                    duration=duration,
                )
                return
        self._record_test(
            "Image Search",
            False,
            str(result.get("error", "Unexpected response")),
            duration,
        )

    # ========================================================================
    # SCRAPING TESTS
    # ========================================================================

    async def test_scrape_webpage(self):
        """Test webpage scraping"""
        start = time.time()
        result = await self._post(
            "/scrape", json={"url": "https://example.com", "extract_links": False}
        )
        duration = time.time() - start

        if result["status"] == 200:
            data = result["data"]
            if data.get("title") or data.get("content"):
                self._record_test("Scrape Webpage", True, duration=duration)
                print_info(f"  Title: {data.get('title', 'N/A')}")
                return
            elif "detail" in data and "not enabled" in data["detail"].lower():
                self.results["skipped"] += 1
                print_warning("Scrape Webpage - Skipped (service not enabled)")
                return
        self._record_test(
            "Scrape Webpage", False, str(result.get("error", "No content")), duration
        )

    # ========================================================================
    # MEDIA TESTS
    # ========================================================================

    async def test_image_generation(self):
        """Test image generation"""
        start = time.time()
        result = await self._post(
            "/media/images/generate",
            json={
                "prompt": "A beautiful sunset over mountains",
                "image_size": "16:9",
                "num_images": 1,
            },
        )
        duration = time.time() - start

        if result["status"] == 200:
            self._record_test("Image Generation", True, duration=duration)
            return
        elif (
            result.get("data", {}).get("detail")
            and "not enabled" in str(result["data"]["detail"]).lower()
        ):
            self.results["skipped"] += 1
            print_warning("Image Generation - Skipped (service not enabled)")
            return
        self._record_test(
            "Image Generation", False, str(result.get("error", "Failed")), duration
        )

    async def test_media_image_search(self):
        """Test media image search API"""
        start = time.time()
        result = await self._post(
            "/media/images/search",
            json={"query": "sunset", "per_page": 5, "source": "auto"},
        )
        duration = time.time() - start

        if result["status"] == 200:
            data = result["data"]
            if "results" in data:
                self._record_test(
                    f"Media Image Search ({len(data['results'])} results)",
                    True,
                    duration=duration,
                )
                return
        self._record_test(
            "Media Image Search", False, str(result.get("error", "Failed")), duration
        )

    # ========================================================================
    # EMAIL TESTS
    # ========================================================================

    async def test_send_email(self):
        """Test sending email"""
        start = time.time()
        result = await self._post(
            "/email/send",
            json={
                "to": TEST_EMAIL,
                "subject": "Test email from Agent Twitter",
                "html": "<h1>Test</h1><p>This is a test email from the automated test bot.</p>",
            },
        )
        duration = time.time() - start

        if result["status"] == 200:
            self._record_test("Send Email", True, duration=duration)
            print_info(f"  Email sent to: {TEST_EMAIL}")
            return
        elif (
            result.get("data", {}).get("detail")
            and "not enabled" in str(result["data"]["detail"]).lower()
        ):
            self.results["skipped"] += 1
            print_warning("Send Email - Skipped (service not enabled)")
            return
        self._record_test(
            "Send Email", False, str(result.get("error", "Failed")), duration
        )

    # ========================================================================
    # MULTI-AGENT TESTS
    # ========================================================================

    async def test_multi_agent_post(self):
        """Test post with multiple agents"""
        start = time.time()
        test_text = "@grok @factcheck @dev What is the meaning of life, the universe, and everything?"
        result = await self._post("/posts", json={"text": test_text})
        duration = time.time() - start

        if result["status"] == 200:
            agent_runs = result["data"].get("triggered_agent_runs", [])
            if len(agent_runs) == 3:
                self._record_test(
                    "Multi-Agent Post (3 agents)", True, duration=duration
                )
                # Wait for agents to process
                await asyncio.sleep(3)
                return
        self._record_test(
            "Multi-Agent Post",
            False,
            f"Expected 3 agents, got {len(agent_runs)}",
            duration,
        )

    # ========================================================================
    # LOAD TESTS
    # ========================================================================

    async def test_concurrent_posts(self):
        """Test creating multiple posts concurrently"""
        print_info("Starting concurrent post test (5 posts)...")

        start = time.time()
        tasks = [
            self._post("/posts", json={"text": f"Concurrent test post {i + 1}"})
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start

        successful = sum(
            1 for r in results if isinstance(r, dict) and r.get("status") == 200
        )
        if successful == 5:
            self._record_test(
                f"Concurrent Posts (5 posts in {duration:.2f}s)",
                True,
                duration=duration,
            )
        else:
            self._record_test(
                "Concurrent Posts", False, f"Only {successful}/5 succeeded", duration
            )

    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================

    async def run_all_tests(self):
        """Run all test suites"""
        print_header("Agent Twitter - Comprehensive Test Suite")
        print_info(f"Target: {BASE_URL}")
        print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Health & Status
        print_header("Phase 1: Health & Status")
        await self.test_health_check()
        await self.test_status_endpoint()
        await self.test_root_endpoint()

        # Agents
        print_header("Phase 2: Agents")
        await self.test_list_agents()
        await self.test_get_agent()
        await self.test_agent_prompt()

        # Posts
        print_header("Phase 3: Posts & Timeline")
        await self.test_create_post()
        await self.test_post_with_agent_mention()
        await self.test_get_timeline()
        await self.test_get_thread()

        # Search
        print_header("Phase 4: Search Services")
        await self.test_web_search()
        await self.test_image_search()

        # Scraping
        print_header("Phase 5: Scraping Services")
        await self.test_scrape_webpage()

        # Media
        print_header("Phase 6: Media Services")
        await self.test_image_generation()
        await self.test_media_image_search()

        # Email
        print_header("Phase 7: Email Services")
        await self.test_send_email()

        # Multi-Agent
        print_header("Phase 8: Multi-Agent Scenarios")
        await self.test_multi_agent_post()

        # Load Testing
        print_header("Phase 9: Load Testing")
        await self.test_concurrent_posts()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")
        total = self.results["passed"] + self.results["failed"]
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        print(f"Total Tests:  {total}")
        print_success(f"Passed:       {self.results['passed']}")
        print_error(f"Failed:       {self.results['failed']}")
        print_warning(f"Skipped:      {self.results['skipped']}")
        print(f"\nPass Rate:    {pass_rate:.1f}%")

        # Show failed tests
        if self.results["failed"] > 0:
            print("\n" + Colors.FAIL + "Failed Tests:" + Colors.ENDC)
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test.get('error', 'Unknown error')}")

        print("\n" + "=" * 60)
        if pass_rate >= 80:
            print_success("Overall: EXCELLENT!")
        elif pass_rate >= 60:
            print_warning("Overall: GOOD")
        else:
            print_error("Overall: NEEDS ATTENTION")
        print("=" * 60)


async def main():
    """Main entry point"""
    async with TestBot(BASE_URL) as bot:
        await bot.run_all_tests()


if __name__ == "__main__":
    print()
    asyncio.run(main())
    print()
