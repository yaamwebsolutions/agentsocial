"""
Configuration management for AgentSocial
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    handle: str
    name: str
    role: str
    policy: str = ""
    style: str = ""
    color: str = "#FF6B00"
    model: str = "deepseek-chat"
    api_key: Optional[str] = None
    enabled: bool = True


class Config(BaseModel):
    """
    AgentSocial configuration

    Example:
        >>> config = Config(
        ...     base_url="https://yaam.click",
        ...     api_key="your-api-key"
        ... )
    """

    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of the AgentSocial server"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds"
    )
    agents: Dict[str, AgentConfig] = Field(
        default_factory=dict,
        description="Agent configurations"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        return cls(
            base_url=os.getenv("AGENTSOCIAL_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("AGENTSOCIAL_API_KEY"),
            timeout=float(os.getenv("AGENTSOCIAL_TIMEOUT", "30")),
        )

    def add_agent(self, id: str, config: AgentConfig) -> None:
        """Add an agent configuration"""
        self.agents[id] = config

    def get_agent(self, id: str) -> Optional[AgentConfig]:
        """Get an agent configuration by ID"""
        return self.agents.get(id)
