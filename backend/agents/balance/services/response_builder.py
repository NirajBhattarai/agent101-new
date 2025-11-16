"""
Response building utilities for balance agent.

Handles formatting and aggregation of balance responses.
NOTE: This module does NOT call tools directly - all tool calls are handled by the agent.
This module only formats and aggregates responses that come from the agent.
"""

from ..core.constants import (
    CHAIN_ALL,
    DEFAULT_TOTAL_USD_VALUE,
    RESPONSE_TYPE,
)

# Token search and discovery moved to Token Research Agent
from .token_filter import filter_balances_by_token


def add_chain_to_balances(balances: list, chain: str) -> list:
    """Add chain information to balance entries."""
    return [{**balance, "chain": chain} for balance in balances]


def build_unknown_chain_response(chain: str, account_address: str) -> dict:
    """Build response for unknown chain."""
    return {
        "type": RESPONSE_TYPE,
        "chain": chain,
        "account_address": account_address,
        "balances": [],
        "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
    }


def build_all_chains_token_response(agent_response: dict, token_symbol: str) -> dict:
    """
    Format balance response for a token across all supported chains.

    NOTE: This function does NOT call tools - it aggregates responses from the agent.
    The agent should have already called get_balance_all_chains and provided the response.

    Args:
        agent_response: Response from agent (should be from get_balance_all_chains tool)
        token_symbol: Token symbol to filter by

    Returns:
        Combined balance response from all chains
    """
    if not isinstance(agent_response, dict) or agent_response.get("type") != "balance_summary":
        return (
            agent_response
            if isinstance(agent_response, dict)
            else build_unknown_chain_response("all", "unknown")
        )

    # Extract and filter balances from all chains
    all_balances = []
    for chain_name, chain_result in agent_response.get("chains", {}).items():
        chain_balances = chain_result.get("balances", [])
        filtered_balances = filter_balances_by_token(chain_balances, token_symbol)
        all_balances.extend(add_chain_to_balances(filtered_balances, chain_name))

    return {
        "type": RESPONSE_TYPE,
        "chain": CHAIN_ALL,
        "account_address": agent_response.get("account_address", "unknown"),
        "token_symbol": token_symbol,
        "balances": all_balances,
        "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
    }


def build_popular_tokens_response(agent_response: dict) -> dict:
    """
    Format balance response for popular tokens across all chains.

    NOTE: This function does NOT call tools - it formats responses from the agent.
    The agent should have already called get_popular_tokens and get_balance_all_chains.

    Args:
        agent_response: Response from agent (should contain popular tokens balance data)

    Returns:
        Combined balance response for popular tokens
    """
    # Agent should have already called tools and provided the response
    # This function just formats/validates the response
    if not isinstance(agent_response, dict):
        return {
            "type": RESPONSE_TYPE,
            "chain": CHAIN_ALL,
            "account_address": "N/A",
            "query_type": "popular_tokens",
            "balances": [],
            "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
        }

    # Ensure response has correct format
    if "type" not in agent_response:
        agent_response["type"] = RESPONSE_TYPE
    if "query_type" not in agent_response:
        agent_response["query_type"] = "popular_tokens"
    if "chain" not in agent_response:
        agent_response["chain"] = CHAIN_ALL

    return agent_response


def build_all_chains_response(agent_response: dict, token_symbol: str | None = None) -> dict:
    """
    Format response for all chains.

    NOTE: This function does NOT call tools - it formats responses from the agent.
    The agent should have already called get_balance_all_chains and provided the response.

    Args:
        agent_response: Response from agent (should be from get_balance_all_chains tool)
        token_symbol: Optional token symbol to filter by

    Returns:
        Formatted balance response for all chains
    """
    if not isinstance(agent_response, dict):
        return build_unknown_chain_response("all", "unknown")

    # If not balance_summary format, return as-is
    if agent_response.get("type") != "balance_summary":
        return agent_response

    # Extract balances from each chain
    all_balances = []
    for chain_name, chain_result in agent_response.get("chains", {}).items():
        chain_balances = chain_result.get("balances", [])
        if token_symbol:
            chain_balances = filter_balances_by_token(chain_balances, token_symbol)
        all_balances.extend(add_chain_to_balances(chain_balances, chain_name))

    response = {
        "type": RESPONSE_TYPE,
        "chain": CHAIN_ALL,
        "account_address": agent_response.get("account_address", "unknown"),
        "balances": all_balances,
        "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
    }
    if token_symbol:
        response["token_symbol"] = token_symbol
    return response
