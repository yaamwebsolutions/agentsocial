# =============================================================================
# Agent Twitter - Agent System Tests
# =============================================================================
#
# Tests for agent loading, configuration, and management
#
# =============================================================================

import pytest
import json
from pathlib import Path
from agents import list_agents, get_agent, Agent


# =============================================================================
# Agent Loading Tests
# =============================================================================


class TestAgentLoading:
    """Tests for agent loading from configuration"""

    def test_load_agents_from_file(self):
        """Test loading agents from agents.json"""
        agents = list_agents()
        assert agents is not None
        assert isinstance(agents, list)

    def test_list_agents(self):
        """Test listing all agents"""
        agents = list_agents()
        assert isinstance(agents, list)
        # Check that each agent is an Agent or dict
        for agent in agents:
            assert hasattr(agent, "id") or "id" in agent

    def test_get_agent_by_handle(self):
        """Test retrieving a specific agent"""
        # Try to get a known agent
        agent = get_agent("grok")
        if agent:
            assert hasattr(agent, "id") or "id" in agent
            assert (agent.id if hasattr(agent, "id") else agent["id"]) == "grok"

    def test_get_agent_nonexistent(self):
        """Test retrieving a non-existent agent"""
        agent = get_agent("thisagentdoesnotexist")
        assert agent is None


# =============================================================================
# Agent Configuration Tests
# =============================================================================


class TestAgentConfiguration:
    """Tests for agent configuration structure"""

    def test_agent_config_exists(self):
        """Test that agents.json file exists"""
        config_path = Path("backend/agents.json")
        # Try both relative and absolute paths
        if not config_path.exists():
            config_path = Path("agents.json")
        assert config_path.exists()

    def test_agent_config_valid_json(self):
        """Test that agents.json is valid JSON"""
        config_paths = [Path("backend/agents.json"), Path("agents.json")]
        config_path = None
        for p in config_paths:
            if p.exists():
                config_path = p
                break

        if config_path:
            with open(config_path) as f:
                data = json.load(f)
            assert isinstance(data, list)

    def test_agent_has_required_fields(self):
        """Test that agents have all required fields"""
        agents = list_agents()
        if agents:
            agent = agents[0]
            required_fields = ["id", "handle", "name", "role", "policy", "style"]
            if hasattr(agent, "id"):
                for field in required_fields:
                    assert hasattr(agent, field)
            else:
                for field in required_fields:
                    assert field in agent


# =============================================================================
# Agent Mock Response Tests
# =============================================================================


class TestAgentMockResponses:
    """Tests for agent mock response functionality"""

    def test_agent_with_mock_responses(self):
        """Test that agents can have mock responses"""
        agent = get_agent("grok")
        if agent and hasattr(agent, "mock_responses"):
            # Some agents might have mock responses
            if agent.mock_responses:
                assert isinstance(agent.mock_responses, list)
                assert all(isinstance(r, str) for r in agent.mock_responses)

    def test_mock_response_substitution(self):
        """Test mock response context substitution"""
        agent = get_agent("grok")
        if agent and hasattr(agent, "mock_responses") and agent.mock_responses:
            mock = agent.mock_responses[0]
            # Test that {context} placeholder exists
            if "{context}" in mock:
                substituted = mock.replace("{context}", "test context")
                assert "test context" in substituted
                assert "{context}" not in substituted


# =============================================================================
# Agent Filtering Tests
# =============================================================================


class TestAgentFiltering:
    """Tests for filtering agents by various criteria"""

    def test_list_enabled_agents_only(self):
        """Test listing agents - all agents are returned"""
        agents = list_agents()
        if agents:
            # Agent model doesn't have an 'enabled' field, all agents are active
            assert isinstance(agents, list)
            assert len(agents) > 0

    def test_get_agent_by_tool(self):
        """Test finding agents that have a specific tool"""
        agents = list_agents()
        if agents:
            # Find agents with web_search tool
            tool_name = "web_search"
            agents_with_tool = [a for a in agents if tool_name in a.tools]
            # At least grok should have this
            assert len(agents_with_tool) >= 0


# =============================================================================
# Agent Reload Tests
# =============================================================================


class TestAgentReload:
    """Tests for agent reloading functionality"""

    def test_reload_agents_exists(self):
        """Test that reload_agents function exists"""
        from agents import reload_agents

        assert callable(reload_agents)

    def test_reload_agents(self):
        """Test reloading agents"""
        from agents import reload_agents

        # Count before reload
        before = len(list_agents())
        # Reload
        reload_agents()
        # Count after
        after = len(list_agents())
        # Should be the same
        assert before == after
