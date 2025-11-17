"""Token search tools for Token Research Agent."""

import os
from typing import Optional

import requests
from langchain_community.tools import DuckDuckGoSearchRun


def search_token_on_web(token_symbol: str) -> dict | None:
    """
    Search for token information on the web using DuckDuckGo search via LangChain.

    Args:
        token_symbol: Token symbol to search for (e.g., "USDT", "WBTC")

    Returns:
        Dictionary with token information including search results, or None if not found
    """
    try:
        query = f"{token_symbol} token contract address ethereum polygon"
        search_tool = DuckDuckGoSearchRun()
        search_result = search_tool.run(query)

        if not search_result:
            return None

        # Format the search result
        # DuckDuckGo returns a string, so we'll parse it into structured results
        results = []
        if isinstance(search_result, str):
            # Split by lines or paragraphs and create result entries
            lines = search_result.split("\n")[:5]  # Limit to 5 results
            for i, line in enumerate(lines):
                if line.strip():
                    results.append(
                        {
                            "title": f"Result {i + 1}",
                            "snippet": line.strip(),
                        }
                    )

        return {
            "token_symbol": token_symbol.upper(),
            "search_results": results
            if results
            else [{"title": "Search Result", "snippet": search_result[:500]}],
            "source": "duckduckgo_search",
        }
    except Exception as e:
        print(f"❌ Error searching for token {token_symbol}: {e}")
        return None


def search_token_contract_address(token_symbol: str, chain: str) -> dict | None:
    """
    Search for token contract address on a specific chain using CoinGecko API.

    Args:
        token_symbol: Token symbol (e.g., "USDT")
        chain: Chain name (e.g., "ethereum", "polygon", "hedera")

    Returns:
        Dictionary with contract address and token info, or None if not found
    """
    api_key = os.getenv("COINGECKO_API_KEY")

    try:
        # First, search for the token ID
        # CoinGecko free tier works without API key but has rate limits
        search_url = "https://api.coingecko.com/api/v3/search"
        search_params = {"query": token_symbol}
        search_headers = {}
        if api_key:
            if api_key.startswith("CG-"):
                search_headers["x-cg-demo-api-key"] = api_key
            else:
                search_headers["x-cg-pro-api-key"] = api_key

        search_response = requests.get(
            search_url, params=search_params, headers=search_headers, timeout=10
        )

        # Handle rate limiting for free tier
        if search_response.status_code == 429:
            print(
                "⚠️  CoinGecko rate limit reached. Consider using COINGECKO_API_KEY for higher limits."
            )
            return None

        search_response.raise_for_status()
        search_data = search_response.json()

        if not search_data.get("coins"):
            return None

        # Get the first matching coin
        coin_id = search_data["coins"][0]["id"]

        # Map chain names to CoinGecko platform IDs
        chain_map = {
            "ethereum": "ethereum",
            "polygon": "polygon-pos",
            "bsc": "binance-smart-chain",
            "hedera": "hedera-hashgraph",
        }

        platform_id = chain_map.get(chain.lower())
        if not platform_id:
            return None

        # Get token details
        coin_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        coin_params = {"localization": "false", "tickers": "false"}
        coin_headers = {}
        if api_key:
            if api_key.startswith("CG-"):
                coin_headers["x-cg-demo-api-key"] = api_key
            else:
                coin_headers["x-cg-pro-api-key"] = api_key

        coin_response = requests.get(coin_url, params=coin_params, headers=coin_headers, timeout=10)

        # Handle rate limiting for free tier
        if coin_response.status_code == 429:
            print(
                "⚠️  CoinGecko rate limit reached. Consider using COINGECKO_API_KEY for higher limits."
            )
            return None

        coin_response.raise_for_status()
        coin_data = coin_response.json()

        platforms = coin_data.get("platforms", {})
        contract_address = platforms.get(platform_id)

        # Get decimals from detail_platforms if available
        decimals = 18  # Default
        detail_platforms = coin_data.get("detail_platforms", {})
        if platform_id in detail_platforms:
            decimals = detail_platforms[platform_id].get("decimal_place", 18)

        if contract_address:
            return {
                "token_symbol": token_symbol.upper(),
                "chain": chain,
                "contract_address": contract_address,
                "token_id": coin_id,
                "name": coin_data.get("name", ""),
                "symbol": coin_data.get("symbol", "").upper(),
                "decimals": decimals,
            }

        return None
    except Exception as e:
        print(f"❌ Error searching for {token_symbol} on {chain}: {e}")
        return None
