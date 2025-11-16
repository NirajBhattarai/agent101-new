"""
Token Extractor Agent.

Extracts token information (symbols, addresses, networks) from user queries
and organizes them into structured JSON format by blockchain network.

REQUEST FORMAT:
The agent receives a user query string that may contain:
- Token symbols (e.g., "USDT", "USDC", "ETH", "HBAR", "MATIC")
- Blockchain network names (e.g., "Ethereum", "Polygon", "Hedera")
- Contract addresses (hexadecimal starting with 0x)
- Requests for "all networks" or "all chains"

Example Requests:
- "Get USDT on Ethereum and Polygon"
- "What's the address of USDC on Ethereum, Polygon, and Hedera?"
- "Show me ETH, MATIC, and HBAR on all networks"
- "Get HBAR on Hedera"
- "Find USDC addresses on Ethereum, Polygon, and Hedera"
- "USDT, USDC, and DAI on Ethereum"
- "All stablecoins on Polygon and Hedera"

RESPONSE FORMAT:
Returns a structured JSON object with the following structure:

{
  "networks": {
    "ethereum": {
      "name": "Ethereum",
      "chain_id": 1,
      "rpc": "https://eth.llamarpc.com",
      "tokens": [
        {
          "symbol": "USDT",
          "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
          "decimals": 6,
          "is_native": false,
          "coingecko_id": "tether",
          "wrapped_address": "0x..." // Optional, for native tokens
        },
        {
          "symbol": "ETH",
          "address": "0x0000000000000000000000000000000000000000",
          "decimals": 18,
          "is_native": true,
          "coingecko_id": "ethereum",
          "wrapped_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" // WETH
        }
      ]
    },
    "polygon": {
      "name": "Polygon",
      "chain_id": 137,
      "rpc": "https://polygon.llamarpc.com",
      "tokens": [
        {
          "symbol": "USDT",
          "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
          "decimals": 6,
          "is_native": false,
          "coingecko_id": "tether"
        }
      ]
    },
    "hedera": {
      "name": "Hedera",
      "chain_id": 295,
      "rpc": "https://mainnet.hashio.io/api",
      "tokens": [
        {
          "symbol": "HBAR",
          "address": "0x0000000000000000000000000000000000000000",
          "decimals": 8,
          "is_native": true,
          "coingecko_id": "hedera",
          "tokenid": "0.0.0",
          "wrapped_address": "0x..." // WHBAR
        }
      ]
    }
  },
  "tokens": [
    {
      "symbol": "USDT",
      "chains": ["ethereum", "polygon", "hedera"],
      "references": [
        {"chain": "ethereum", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"},
        {"chain": "polygon", "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"},
        {"chain": "hedera", "address": "0x0000000000000000000000000000000000101b07"}
      ]
    }
  ],
  "networks_list": ["ethereum", "polygon", "hedera"],
  "query_valid": true,
  "error": null,
  "summary": {
    "tokens_found": 1,
    "networks_found": 3,
    "total_tokens_extracted": 3
  }
}

RESPONSE FIELDS:
- networks: Object keyed by network name (ethereum, polygon, hedera)
  - Each network contains: name, chain_id, rpc, tokens array
- tokens: Flat array of unique tokens with cross-chain references
- networks_list: Array of network names found
- query_valid: Boolean indicating if query was understood
- error: Error message string or null
- summary: Statistics about extracted tokens

The response is stored in session.state['token_data'] for use by the balance extractor agent.
"""

import json
import re

from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions.session import Session

# Local imports
from .tools import extract_tokens

# Token Extraction Agent - Uses extract_tokens tool for token extraction
token_extraction_agent = LlmAgent(
    name="TokenExtractorAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a Professional Token Information Extractor.\n\n"
        "YOUR TASK:\n"
        "Extract token information from user queries using the extract_tokens tool.\n"
        "The tool will handle all the complex logic of finding tokens, networks, and addresses.\n\n"
        "HOW TO USE:\n"
        "1. When you receive a user query, call extract_tokens(user_query) with the user's query string\n"
        "2. The tool will return structured token data organized by blockchain network\n"
        "3. Return the complete response object from the tool directly\n\n"
        "The extract_tokens tool will:\n"
        "- Extract token symbols from the query (USDT, USDC, ETH, HBAR, etc.)\n"
        "- Identify blockchain networks mentioned (Ethereum, Polygon, Hedera)\n"
        "- Default to all networks if none specified\n"
        "- Look up token addresses, decimals, and metadata from known token constants\n"
        "- Organize data by network with proper structure\n"
        "- Include wrapped token addresses for native tokens (WHBAR, WETH, WMATIC)\n"
        "- Build cross-chain token references\n\n"
        "OUTPUT:\n"
        "Return the complete response object from extract_tokens tool.\n"
        "The tool response includes:\n"
        "- networks: Token data organized by network (ethereum, polygon, hedera)\n"
        "- tokens: Flat array of unique tokens with cross-chain references\n"
        "- networks_list: Array of network names found\n"
        "- query_valid: Boolean indicating if query was understood\n"
        "- error: Error message or null\n"
        "- summary: Statistics about extracted tokens\n\n"
        "CRITICAL RULES:\n"
        "- ALWAYS use the extract_tokens tool - do not try to extract tokens manually\n"
        "- Return the tool's response object directly (it's already in the correct format)\n"
        "- The tool handles all token lookup, address resolution, and data organization\n"
        "- If the tool returns an error, return the error response as-is"
    ),
    output_key="token_data",
    tools=[extract_tokens],
)


def parse_token_response(session: Session) -> dict:
    """
    Parse token response from single agent.

    Handles two types of responses:
    1. Tool response: Direct token data from extract_tokens tool (has "networks" and "tokens")
    2. Extraction response: Extracted parameters (legacy format)

    Args:
        session: ADK Session with agent output

    Returns:
        Structured token data by network
    """
    try:
        # Get output from agent
        token_data = session.state.get("token_data")

        if not token_data:
            return {
                "networks": {},
                "tokens": [],
                "networks_list": [],
                "query_valid": False,
                "error": "No data extracted",
            }

        # Parse JSON if string
        if isinstance(token_data, str):
            try:
                token_data = json.loads(token_data)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response
                token_data = _extract_json(token_data)

        # Check if this is a tool response (has "networks" and "tokens" fields)
        if isinstance(token_data, dict):
            if "networks" in token_data and "tokens" in token_data:
                # This is a tool response - return as-is
                return token_data
            # Otherwise, it's a legacy extraction response - return as-is

        return token_data

    except Exception as e:
        return {
            "networks": {},
            "tokens": [],
            "networks_list": [],
            "query_valid": False,
            "error": str(e),
        }


def _extract_json(response: str) -> dict:
    """
    Extract JSON from LLM response with advanced fallback.

    Args:
        response: Raw response string from LLM

    Returns:
        Parsed JSON dictionary or empty structure if parsing fails
    """
    try:
        # Try direct parse first
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try generic code block
    json_match = re.search(r"```\s*(\{.*?\})\s*```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find brace-enclosed JSON
    brace_start = response.find("{")
    if brace_start != -1:
        brace_count = 0
        brace_end = -1
        for i in range(brace_start, len(response)):
            if response[i] == "{":
                brace_count += 1
            elif response[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    brace_end = i + 1
                    break

        if brace_end != -1:
            try:
                return json.loads(response[brace_start:brace_end])
            except json.JSONDecodeError:
                pass

    # Return empty structure
    return {
        "networks": {},
        "tokens": [],
        "networks_list": [],
        "query_valid": False,
        "error": "Could not parse JSON from response",
    }
