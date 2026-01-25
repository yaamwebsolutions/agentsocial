"""
AgentSocial SDK - AI-native social platform SDK

Build social applications with @mentionable AI agents.
"""

__version__ = "1.0.0"
__author__ = "Yaam Web Solutions"
__license__ = "MIT"

from agentsocial.client import Client
from agentsocial.models import Post, Thread, Agent, AgentRun
from agentsocial.config import Config

__all__ = [
    "Client",
    "Post",
    "Thread",
    "Agent",
    "AgentRun",
    "Config",
    "__version__",
]
