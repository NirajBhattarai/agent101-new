"""Token resolution tool for liquidity agents."""

from typing import Any

from ...swap.services.token_resolver import resolve_token_address


def resolve_token_for_liquidity(token_symbol: str, chain: str) -> dict[str, Any]:
    """
    Resolve token symbol to address for liquidity queries.

    Args:
        token_symbol: Token symbol (e.g., "LINK", "USDC", "USDT")
        chain: Chain name ("ethereum", "polygon", "hedera")

    Returns:
        Dictionary with token info including address:
        {
            "symbol": "LINK",
            "address": "0x...",  # For ethereum/polygon
            "address_evm": "0x...",  # For hedera
            "address_hedera": "0.0.123456",  # For hedera (if available)
            "decimals": 18,
            "source": "constants" | "cache" | "token_research",
            "explorer_url": "https://..."
        }
    """
    try:
        result = resolve_token_address(token_symbol, chain)
        if result:
            return {
                "symbol": result.get("symbol", token_symbol.upper()),
                "address": result.get("address") or result.get("address_evm"),
                "address_evm": result.get("address_evm"),
                "address_hedera": result.get("address_hedera"),
                "decimals": result.get("decimals", 18),
                "source": result.get("source", "unknown"),
                "explorer_url": result.get("explorer_url"),
                "status": "success",
            }
        else:
            return {
                "symbol": token_symbol.upper(),
                "address": None,
                "status": "not_found",
                "error": f"Token {token_symbol} not found on {chain}",
            }
    except Exception as e:
        return {
            "symbol": token_symbol.upper(),
            "address": None,
            "status": "error",
            "error": str(e),
        }
