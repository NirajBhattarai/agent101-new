"""
Orchestrator Agent Definition

Defines the OrchestratorAgent class.
"""

try:
    from ag_ui_adk import ADKAgent  # noqa: E402
except ImportError:
    ADKAgent = None  # type: ignore

from google.adk.agents.llm_agent import LlmAgent

from .core.constants import (
    AGENT_NAME,
    DEFAULT_APP_NAME,
    DEFAULT_SESSION_TIMEOUT,  # noqa: E402
    DEFAULT_USER_ID,  # noqa: E402
    check_api_keys,  # noqa: E402
    get_model_name,  # noqa: E402
)
from .core.instruction import ORCHESTRATOR_INSTRUCTION  # noqa: E402


def build_orchestrator_agent() -> LlmAgent:
    """Build and configure the orchestrator LLM agent."""
    model_name = get_model_name()
    check_api_keys()
    return LlmAgent(
        name=AGENT_NAME,
        model=model_name,
        instruction=ORCHESTRATOR_INSTRUCTION,
    )


def build_adk_orchestrator_agent() -> ADKAgent:
    """Build ADK agent wrapper for AG-UI Protocol."""
    if ADKAgent is None:
        raise ImportError(
            "ag_ui_adk is not installed. Install it with: uv pip install ag-ui-adk or make backend-install"
        )

    orchestrator_agent = build_orchestrator_agent()
    return ADKAgent(
        adk_agent=orchestrator_agent,
        app_name=DEFAULT_APP_NAME,
        user_id=DEFAULT_USER_ID,
        session_timeout_seconds=DEFAULT_SESSION_TIMEOUT,
        use_in_memory_services=True,
    )
