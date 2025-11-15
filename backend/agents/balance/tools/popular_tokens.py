"""Popular tokens utility for balance agent."""

import os
from typing import Optional

import requests


def get_popular_tokens() -> list[dict]:
    """
    Get list of popular/trending tokens using CoinGecko API.

    Returns:
        List of dictionaries with token information (symbol, name, id)
    """
    api_key = os.getenv("COINGECKO_API_KEY")

    if not api_key:
        print("⚠️  CoinGecko API key not configured. Using default popular tokens.")
        return _get_default_popular_tokens()

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": False,
        }
        # CoinGecko API key format: x-cg-demo-api-key for demo, x-cg-pro-api-key for pro
        headers = {}
        if api_key:
            # Try both header formats
            if api_key.startswith("CG-"):
                headers["x-cg-demo-api-key"] = api_key
            else:
                headers["x-cg-pro-api-key"] = api_key

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        tokens = []
        for token in data:
            tokens.append(
                {
                    "id": token.get("id", ""),
                    "symbol": token.get("symbol", "").upper(),
                    "name": token.get("name", ""),
                    "market_cap": token.get("market_cap", 0),
                }
            )

        return tokens
    except Exception as e:
        print(f"❌ Error fetching popular tokens from CoinGecko: {e}")
        return _get_default_popular_tokens()


def _get_default_popular_tokens() -> list[dict]:
    """Get default list of popular tokens if API is unavailable."""
    return [
        {"symbol": "BTC", "name": "Bitcoin", "id": "bitcoin"},
        {"symbol": "ETH", "name": "Ethereum", "id": "ethereum"},
        {"symbol": "USDT", "name": "Tether", "id": "tether"},
        {"symbol": "BNB", "name": "BNB", "id": "binancecoin"},
        {"symbol": "SOL", "name": "Solana", "id": "solana"},
        {"symbol": "USDC", "name": "USD Coin", "id": "usd-coin"},
        {"symbol": "XRP", "name": "XRP", "id": "ripple"},
        {"symbol": "DOGE", "name": "Dogecoin", "id": "dogecoin"},
        {"symbol": "ADA", "name": "Cardano", "id": "cardano"},
        {"symbol": "TRX", "name": "TRON", "id": "tron"},
        {"symbol": "MATIC", "name": "Polygon", "id": "matic-network"},
        {"symbol": "DOT", "name": "Polkadot", "id": "polkadot"},
        {"symbol": "LINK", "name": "Chainlink", "id": "chainlink"},
        {"symbol": "WBTC", "name": "Wrapped Bitcoin", "id": "wrapped-bitcoin"},
        {"symbol": "UNI", "name": "Uniswap", "id": "uniswap"},
    ]

