# =============================================================================
# Agent Twitter - API Endpoint Tests
# =============================================================================
#
# Tests for all REST API endpoints
#
# =============================================================================

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Health & Status Endpoints
# =============================================================================

class TestHealthEndpoints:
    """Tests for health check and status endpoints"""

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "endpoints" in data

    def test_status_endpoint(self, client: TestClient):
        """Test the status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "services" in data


# =============================================================================
# Post Endpoints
# =============================================================================

class TestPostEndpoints:
    """Tests for post creation and retrieval endpoints"""

    def test_create_post(self, authenticated_client: TestClient):
        """Test creating a new post"""
        response = authenticated_client.post(
            "/posts",
            json={"text": "Hello world!", "parent_id": None}
        )
        assert response.status_code == 200
        data = response.json()
        assert "post" in data
        assert "agent_runs" in data

    def test_create_post_with_mention(self, authenticated_client: TestClient):
        """Test creating a post with an agent mention"""
        response = authenticated_client.post(
            "/posts",
            json={"text": "Hello @grok!", "parent_id": None}
        )
        assert response.status_code == 200

    def test_create_post_empty_text(self, authenticated_client: TestClient):
        """Test creating a post with empty text (should fail)"""
        response = authenticated_client.post(
            "/posts",
            json={"text": "", "parent_id": None}
        )
        # Should fail validation
        assert response.status_code == 422

    def test_get_thread(self, client: TestClient, sample_thread):
        """Test retrieving a thread"""
        # First create a thread
        from store import store
        store.threads[sample_thread["id"]] = sample_thread

        response = client.get(f"/threads/{sample_thread['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_get_thread_not_found(self, client: TestClient):
        """Test retrieving a non-existent thread"""
        response = client.get("/threads/non-existent")
        assert response.status_code == 404

    def test_get_timeline(self, client: TestClient):
        """Test retrieving the timeline"""
        response = client.get("/timeline?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# =============================================================================
# Agent Endpoints
# =============================================================================

class TestAgentEndpoints:
    """Tests for agent listing and retrieval endpoints"""

    def test_list_agents(self, client: TestClient):
        """Test listing all agents"""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check that agents have required fields
        if data:
            agent = data[0]
            assert "id" in agent
            assert "handle" in agent
            assert "name" in agent

    def test_get_agent_by_handle(self, client: TestClient):
        """Test getting a specific agent by handle"""
        response = client.get("/agents/grok")
        # Might not exist if agents.json doesn't have it
        # But should not error on 404
        assert response.status_code in [200, 404]

    def test_get_agent_not_found(self, client: TestClient):
        """Test getting a non-existent agent"""
        response = client.get("/agents/nonexistentagent")
        assert response.status_code == 404

    def test_prompt_agent(self, client: TestClient, mock_llm_service):
        """Test sending a direct prompt to an agent"""
        response = client.post(
            "/agents/prompt",
            json={"agent_handle": "grok", "prompt": "Tell me a joke"}
        )
        # Response depends on whether grok agent exists
        assert response.status_code in [200, 404]


# =============================================================================
# User Endpoints
# =============================================================================

class TestUserEndpoints:
    """Tests for user-related endpoints"""

    def test_get_current_user(self, client: TestClient):
        """Test getting the current user"""
        response = client.get("/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data


# =============================================================================
# Search Endpoints
# =============================================================================

class TestSearchEndpoints:
    """Tests for search endpoints"""

    def test_web_search_disabled(self, client: TestClient):
        """Test web search when disabled"""
        response = client.post(
            "/search/web",
            json={"query": "test query", "num_results": 5}
        )
        # Should return 501 when service not enabled
        assert response.status_code == 501

    def test_image_search(self, client: TestClient):
        """Test image search"""
        response = client.get("/search/images/test")
        # Mock response from media service
        assert response.status_code == 200


# =============================================================================
# Email Endpoints
# =============================================================================

class TestEmailEndpoints:
    """Tests for email endpoints"""

    def test_send_email_disabled(self, client: TestClient):
        """Test sending email when service is disabled"""
        response = client.post(
            "/email/send",
            json={
                "to": "test@example.com",
                "subject": "Test",
                "html": "<p>Test email</p>"
            }
        )
        # Should return 501 when service not enabled
        assert response.status_code == 501


# =============================================================================
# Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for error handling"""

    def test_404_endpoint(self, client: TestClient):
        """Test accessing non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_method(self, client: TestClient):
        """Test using wrong HTTP method"""
        response = client.post("/health")
        # Method not allowed or 422
        assert response.status_code in [405, 422]
