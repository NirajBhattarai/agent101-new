"""Tool for fetching and discovering popular tokens across chains."""

from packages.blockchain.token_discovery import (
    discover_and_cache_popular_tokens,
    get_all_tokens_for_chain,
    get_token_for_chain,
)


def fetch_popular_tokens(limit: int = 5) -> dict:
    """
    Fetch popular tokens from Ethereum and map them across Ethereum, Polygon, and Hedera.
    Results are cached in memory for use in swaps and balance queries.

    Args:
        limit: Maximum number of tokens to fetch (default: 5 to avoid rate limits)

    Returns:
        Dictionary with discovered tokens and their addresses per chain
    """
    try:
        # Limit to 5 to avoid CoinGecko rate limits (429 errors)
        actual_limit = min(limit, 5)
        discovered = discover_and_cache_popular_tokens(limit=actual_limit)

        # Format response
        tokens_by_chain = {
            "ethereum": [],
            "polygon": [],
            "hedera": [],
        }

        for symbol, token_data in discovered.items():
            if token_data.get("ethereum"):
                tokens_by_chain["ethereum"].append(
                    {
                        "symbol": symbol,
                        "name": token_data.get("name", ""),
                        "address": token_data["ethereum"],
                        "decimals": token_data.get("decimals", {}).get("ethereum", 18),
                    }
                )
            if token_data.get("polygon"):
                tokens_by_chain["polygon"].append(
                    {
                        "symbol": symbol,
                        "name": token_data.get("name", ""),
                        "address": token_data["polygon"],
                        "decimals": token_data.get("decimals", {}).get("polygon", 18),
                    }
                )
            if token_data.get("hedera"):
                tokens_by_chain["hedera"].append(
                    {
                        "symbol": symbol,
                        "name": token_data.get("name", ""),
                        "address": token_data["hedera"],
                        "decimals": token_data.get("decimals", {}).get("hedera", 8),
                    }
                )

        return {
            "type": "token_discovery",
            "status": "success",
            "total_tokens": len(discovered),
            "tokens_by_chain": tokens_by_chain,
            "message": f"Successfully discovered {len(discovered)} popular tokens across chains",
        }
    except Exception as e:
        return {
            "type": "token_discovery",
            "status": "error",
            "error": str(e),
            "message": "Failed to discover tokens",
        }


def get_tokens_for_chain(chain: str) -> dict:
    """
    Get all cached tokens available on a specific chain.

    Args:
        chain: Chain name ("ethereum", "polygon", "hedera")

    Returns:
        Dictionary with list of tokens available on the chain
    """
    try:
        tokens = get_all_tokens_for_chain(chain)

        return {
            "type": "token_list",
            "chain": chain,
            "count": len(tokens),
            "tokens": tokens,
        }
    except Exception as e:
        return {
            "type": "token_list",
            "chain": chain,
            "status": "error",
            "error": str(e),
            "tokens": [],
        }


def get_token_address(symbol: str, chain: str) -> dict:
    """
    Get token address for a specific symbol and chain from cache.

    Args:
        symbol: Token symbol (e.g., "USDC")
        chain: Chain name ("ethereum", "polygon", "hedera")

    Returns:
        Dictionary with token address and info
    """
    try:
        token = get_token_for_chain(symbol, chain)

        if token:
            return {
                "type": "token_address",
                "status": "success",
                "symbol": symbol.upper(),
                "chain": chain,
                "address": token["address"],
                "name": token.get("name", ""),
                "decimals": token.get("decimals", 18),
            }
        else:
            return {
                "type": "token_address",
                "status": "not_found",
                "symbol": symbol.upper(),
                "chain": chain,
                "message": f"Token {symbol} not found on {chain} in cache. Try fetching popular tokens first.",
            }
    except Exception as e:
        return {
            "type": "token_address",
            "status": "error",
            "symbol": symbol.upper(),
            "chain": chain,
            "error": str(e),
        }
