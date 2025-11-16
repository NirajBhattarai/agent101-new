"""Token extraction tool for extracting token information from user queries."""

from packages.blockchain.ethereum.constants import ETHEREUM_TOKENS
from packages.blockchain.hedera.constants import HEDERA_TOKENS
from packages.blockchain.polygon.constants import POLYGON_TOKENS


def _get_coingecko_id(symbol: str) -> str:
    """Get CoinGecko ID for a token symbol."""
    coingecko_map = {
        "USDT": "tether",
        "USDC": "usd-coin",
        "DAI": "dai",
        "ETH": "ethereum",
        "WETH": "weth",
        "MATIC": "matic-network",
        "WMATIC": "wmatic",
        "HBAR": "hedera",
        "WHBAR": "wrapped-hedera",
        "WBTC": "wrapped-bitcoin",
        "LINK": "chainlink",
        "UNI": "uniswap",
    }
    return coingecko_map.get(symbol.upper(), symbol.lower().replace(" ", "-"))


def _extract_token_symbols(query: str) -> list[str]:
    """Extract token symbols from query."""
    query_upper = query.upper()
    all_tokens = set()

    # Check all known tokens
    for chain_tokens in [ETHEREUM_TOKENS, POLYGON_TOKENS, HEDERA_TOKENS]:
        for symbol in chain_tokens.keys():
            if symbol in query_upper:
                all_tokens.add(symbol)

    return sorted(all_tokens)


def _extract_networks(query: str) -> list[str]:
    """Extract network names from query."""
    query_lower = query.lower()
    networks = []

    if "ethereum" in query_lower or "eth" in query_lower:
        networks.append("ethereum")
    if "polygon" in query_lower or "matic" in query_lower:
        networks.append("polygon")
    if "hedera" in query_lower or "hbar" in query_lower:
        networks.append("hedera")
    if "all" in query_lower and ("network" in query_lower or "chain" in query_lower):
        networks = ["ethereum", "polygon", "hedera"]

    return networks if networks else ["ethereum", "polygon", "hedera"]


def _build_token_object(symbol: str, chain: str, token_data: dict) -> dict:
    """Build token object for response."""
    address = token_data.get("address", "0x0000000000000000000000000000000000000000")
    decimals = token_data.get("decimals", 18)
    tokenid = token_data.get("tokenid", "")

    # Determine if native
    is_native = False
    if chain == "hedera":
        is_native = tokenid == "0.0.0" or symbol == "HBAR"
    elif chain == "ethereum":
        is_native = symbol == "ETH" or address == "0x0000000000000000000000000000000000000000"
    elif chain == "polygon":
        is_native = symbol == "MATIC" or address == "0x0000000000000000000000000000000000000000"

    token_obj = {
        "symbol": symbol,
        "address": address,
        "decimals": decimals,
        "is_native": is_native,
        "coingecko_id": _get_coingecko_id(symbol),
    }

    # Add tokenid for Hedera
    if chain == "hedera" and tokenid:
        token_obj["tokenid"] = tokenid

    # Add wrapped address for native tokens
    if is_native:
        wrapped_map = {
            "HBAR": HEDERA_TOKENS.get("WHBAR", {}).get("address", ""),
            "ETH": ETHEREUM_TOKENS.get("WETH", {}).get("address", ""),
            "MATIC": POLYGON_TOKENS.get("WMATIC", {}).get("address", ""),
        }
        wrapped_addr = wrapped_map.get(symbol, "")
        if wrapped_addr:
            token_obj["wrapped_address"] = wrapped_addr

    return token_obj


def extract_tokens(user_query: str) -> dict:
    """
    Extract token information from user query and return structured token data.

    Args:
        user_query: User query string containing token symbols and/or network names

    Returns:
        Dictionary with token information organized by network:
        {
            "networks": {
                "ethereum": {...},
                "polygon": {...},
                "hedera": {...}
            },
            "tokens": [...],
            "networks_list": [...],
            "query_valid": true,
            "error": null,
            "summary": {...}
        }
    """
    try:
        # Extract token symbols and networks from query
        token_symbols = _extract_token_symbols(user_query)
        networks = _extract_networks(user_query)

        if not token_symbols:
            return {
                "networks": {},
                "tokens": [],
                "networks_list": [],
                "query_valid": False,
                "error": "No token symbols found in query",
                "summary": {
                    "tokens_found": 0,
                    "networks_found": 0,
                    "total_tokens_extracted": 0,
                },
            }

        # Chain token constants mapping
        chain_tokens_map = {
            "ethereum": ETHEREUM_TOKENS,
            "polygon": POLYGON_TOKENS,
            "hedera": HEDERA_TOKENS,
        }

        # Chain RPC URLs
        chain_rpc_map = {
            "ethereum": "https://eth.llamarpc.com",
            "polygon": "https://polygon.llamarpc.com",
            "hedera": "https://mainnet.hashio.io/api",
        }

        # Chain IDs
        chain_id_map = {
            "ethereum": 1,
            "polygon": 137,
            "hedera": 295,
        }

        # Chain names
        chain_name_map = {
            "ethereum": "Ethereum",
            "polygon": "Polygon",
            "hedera": "Hedera",
        }

        # Build networks structure
        networks_data = {}
        tokens_flat = []
        token_references = {}

        for chain in networks:
            chain_tokens = chain_tokens_map[chain]
            tokens_list = []

            for symbol in token_symbols:
                if symbol in chain_tokens:
                    token_data = chain_tokens[symbol]
                    token_obj = _build_token_object(symbol, chain, token_data)
                    tokens_list.append(token_obj)

                    # Build flat tokens array with references
                    if symbol not in token_references:
                        token_references[symbol] = {
                            "symbol": symbol,
                            "chains": [],
                            "references": [],
                        }

                    if chain not in token_references[symbol]["chains"]:
                        token_references[symbol]["chains"].append(chain)

                    token_references[symbol]["references"].append(
                        {"chain": chain, "address": token_obj["address"]}
                    )

            if tokens_list:
                networks_data[chain] = {
                    "name": chain_name_map[chain],
                    "chain_id": chain_id_map[chain],
                    "rpc": chain_rpc_map[chain],
                    "tokens": tokens_list,
                }

        # Build flat tokens array
        tokens_flat = list(token_references.values())

        # Calculate summary
        total_tokens_extracted = sum(
            len(network.get("tokens", [])) for network in networks_data.values()
        )

        return {
            "networks": networks_data,
            "tokens": tokens_flat,
            "networks_list": list(networks_data.keys()),
            "query_valid": True,
            "error": None,
            "summary": {
                "tokens_found": len(token_symbols),
                "networks_found": len(networks_data),
                "total_tokens_extracted": total_tokens_extracted,
            },
        }

    except Exception as e:
        return {
            "networks": {},
            "tokens": [],
            "networks_list": [],
            "query_valid": False,
            "error": str(e),
            "summary": {
                "tokens_found": 0,
                "networks_found": 0,
                "total_tokens_extracted": 0,
            },
        }
