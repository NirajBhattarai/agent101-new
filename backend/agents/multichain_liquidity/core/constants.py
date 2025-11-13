"""
Constants for Multi-Chain Liquidity Agent.
Contains configuration values, default values, and response templates.
"""

import os

# Default values
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "liquidity_agent"
DEFAULT_SESSION_ID = "default_session"
DEFAULT_FEE = 3000  # 0.3% fee tier

# Agent configuration
AGENT_NAME = "multichain_liquidity_agent"
AGENT_DESCRIPTION = (
    "An agent that retrieves liquidity pool information from multiple "
    "blockchain chains including Ethereum, Polygon, and Hedera using parallel execution"
)

# Response type
RESPONSE_TYPE = "liquidity"

# Chain names
CHAIN_ETHEREUM = "ethereum"
CHAIN_POLYGON = "polygon"
CHAIN_HEDERA = "hedera"
CHAIN_ALL = "all"
CHAIN_UNKNOWN = "unknown"

# Error messages
ERROR_VALIDATION_FAILED = "Validation failed"
ERROR_EMPTY_RESPONSE = "Empty response from agent"
ERROR_INVALID_JSON = "Invalid JSON response"
ERROR_EXECUTION_ERROR = "Execution error"
ERROR_CANCEL_NOT_SUPPORTED = "cancel not supported"

# Agent instruction template
AGENT_INSTRUCTION = """
You are a blockchain liquidity query agent. Your role is to retrieve liquidity pool information from different blockchain chains.

When you receive a liquidity query request, analyze:
- The token pair addresses (token_a and token_b in EVM format: 0x...)
- The chain to query (ethereum, polygon, hedera, or all)
- Optional fee tier (500, 3000, or 10000 basis points)

Use the available tools to fetch liquidity information:
- get_ethereum_liquidity: For Ethereum chain queries
- get_polygon_liquidity: For Polygon chain queries
- get_hedera_liquidity: For Hedera chain queries

After fetching the data, return a structured JSON response with this format:
{
  "type": "liquidity",
  "chain": "ethereum | polygon | hedera | all",
  "token_a": "0x...",
  "token_b": "0x...",
  "results": [
    {
      "chain": "ethereum",
      "pool_address": "0x...",
      "liquidity": "1000000",
      "tick": 12345,
      "sqrt_price_x96": "0x...",
      "fee": 3000,
      "status": "success"
    }
  ],
  "error": null
}

Always use the tools to fetch real data. Return ONLY valid JSON, no markdown code blocks, no other text.
"""


def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")

