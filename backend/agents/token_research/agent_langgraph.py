"""
LangGraph-based Token Research Agent

Uses LangGraph with ReAct pattern for token discovery and search.
"""

import os
from collections.abc import AsyncIterable
from typing import Any, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from .tools.token_discovery import discover_popular_tokens
from .tools.token_fetcher import (
    fetch_popular_tokens,
    get_token_address,
    get_tokens_for_chain,
)
from .tools.token_search import search_token_contract_address

memory = MemorySaver()


@tool
def search_token(token_symbol: str, chain: str | None = None) -> dict:
    """Search for a token by symbol and optionally on a specific chain.

    Args:
        token_symbol: Token symbol to search for (e.g., "USDT", "WBTC")
        chain: Optional chain name (e.g., "ethereum", "polygon", "hedera")

    Returns:
        Dictionary with token information including contract address and details
    """
    try:
        # First try to get from cache
        if chain:
            result = get_token_address(token_symbol, chain)
            if result.get("status") == "success":
                return result

        # If not in cache or no chain specified, search via web/API
        if chain:
            result = search_token_contract_address(token_symbol, chain)
            if result:
                return {
                    "type": "token_search",
                    "status": "success",
                    "token_symbol": result.get("token_symbol", token_symbol.upper()),
                    "chain": chain,
                    "contract_address": result.get("contract_address"),
                    "name": result.get("name", ""),
                    "decimals": result.get("decimals", 18),
                }

        # Try searching across all chains if no specific chain was provided
        if not chain:
            for chain_name in ["ethereum", "polygon", "hedera"]:
                result = search_token_contract_address(token_symbol, chain_name)
                if result:
                    return {
                        "type": "token_search",
                        "status": "success",
                        "token_symbol": result.get("token_symbol", token_symbol.upper()),
                        "chain": chain_name,
                        "contract_address": result.get("contract_address"),
                        "name": result.get("name", ""),
                        "decimals": result.get("decimals", 18),
                    }

        return {
            "type": "token_search",
            "status": "not_found",
            "token_symbol": token_symbol.upper(),
            "message": f"Token {token_symbol} not found. Try discovering popular tokens first.",
        }
    except Exception as e:
        return {
            "type": "token_search",
            "status": "error",
            "token_symbol": token_symbol.upper(),
            "error": str(e),
        }


@tool
def discover_tokens(limit: int = 5) -> dict:
    """Discover popular tokens across multiple chains (Ethereum, Polygon, Hedera).

    Args:
        limit: Maximum number of tokens to discover (default: 5)

    Returns:
        Dictionary with discovered tokens organized by chain
    """
    try:
        result = fetch_popular_tokens(limit=limit)
        return result
    except Exception as e:
        return {
            "type": "token_discovery",
            "status": "error",
            "error": str(e),
            "message": "Failed to discover tokens",
        }


@tool
def get_chain_tokens(chain: str) -> dict:
    """Get all available tokens for a specific chain from cache.

    Args:
        chain: Chain name ("ethereum", "polygon", "hedera")

    Returns:
        Dictionary with list of tokens available on the chain
    """
    try:
        result = get_tokens_for_chain(chain)
        return result
    except Exception as e:
        return {
            "type": "token_list",
            "chain": chain,
            "status": "error",
            "error": str(e),
            "tokens": [],
        }


class ResponseFormat(BaseModel):
    """Response format for the agent."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class TokenResearchLangGraphAgent:
    """Token Research Agent using LangGraph with ReAct pattern."""

    SYSTEM_INSTRUCTION = (
        "You are a specialized assistant for token research and discovery across blockchain networks. "
        "Your purpose is to help users find token information, contract addresses, and discover popular tokens. "
        "You can search for specific tokens by symbol, discover popular tokens across chains, and get token lists for specific chains. "
        "Always provide clear, accurate information about tokens including their contract addresses, symbols, and which chains they're available on. "
        "If a user asks about something other than token research, politely redirect them to token-related queries."
    )

    FORMAT_INSTRUCTION = (
        "Set response status to input_required if the user needs to provide more information to complete the request. "
        "Set response status to error if there is an error while processing the request. "
        "Set response status to completed if the request is complete and you have provided the token information."
    )

    def __init__(self):
        model_source = os.getenv("model_source", "google")
        if model_source == "google":
            self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        else:
            from langchain_openai import ChatOpenAI

            self.model = ChatOpenAI(
                model=os.getenv("TOOL_LLM_NAME", "gpt-4"),
                openai_api_key=os.getenv("API_KEY", ""),
                openai_api_base=os.getenv("TOOL_LLM_URL", ""),
                temperature=0,
            )

        self.tools = [search_token, discover_tokens, get_chain_tokens]

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=(self.FORMAT_INSTRUCTION, ResponseFormat),
        )

    async def stream(self, query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
        """Stream agent responses with status updates."""
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": context_id}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "🔍 Searching for token information...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "📊 Processing token data...",
                }

        yield self.get_agent_response(config)

    def get_agent_response(self, config: dict) -> dict[str, Any]:
        """Get the final agent response from the graph state."""
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get("structured_response")

        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message,
                }
            if structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message,
                }
            if structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message,
                }

        # Fallback: extract message from last AI message
        messages = current_state.values.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": str(last_message.content),
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
