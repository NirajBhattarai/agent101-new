"""
Constants for Orchestrator Agent.

Configuration values and defaults.
"""

import os

# Default values
DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_USER_ID = "demo_user"
DEFAULT_APP_NAME = "agents"
DEFAULT_SESSION_TIMEOUT = 3600
DEFAULT_PORT = 9000

# Agent configuration
AGENT_NAME = "OrchestratorAgent"


# Model configuration
def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")
