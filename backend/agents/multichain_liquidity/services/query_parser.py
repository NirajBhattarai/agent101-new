"""
Query parsing utilities for liquidity agent.

Handles extraction of token addresses and chain detection from queries.
"""

import re
from typing import Optional
from ..core.constants import (
    CHAIN_ETHEREUM,
    CHAIN_POLYGON,
    CHAIN_HEDERA,
    CHAIN_ALL,
    CHAIN_UNKNOWN,
)


def extract_token_addresses(query: str) -> tuple[Optional[str], Optional[str]]:
    """Extract token addresses from query."""
    # Pattern for EVM addresses (0x followed by 40 hex chars)
    evm_pattern = r"0x[a-fA-F0-9]{40}"
    addresses = re.findall(evm_pattern, query)
    
    if len(addresses) >= 2:
        return addresses[0], addresses[1]
    elif len(addresses) == 1:
        return addresses[0], None
    return None, None


def detect_chain_from_query(query: str) -> Optional[str]:
    """Detect chain from query text."""
    query_lower = query.lower()
    if "ethereum" in query_lower or "eth" in query_lower and "hedera" not in query_lower:
        return CHAIN_ETHEREUM
    if "polygon" in query_lower:
        return CHAIN_POLYGON
    if "hedera" in query_lower:
        return CHAIN_HEDERA
    if "all" in query_lower:
        return CHAIN_ALL
    return None


def parse_chain(query: str) -> str:
    """Parse chain from query."""
    chain = detect_chain_from_query(query)
    if chain:
        return chain
    return CHAIN_ALL  # Default to all chains


def extract_fee_tier(query: str) -> Optional[int]:
    """Extract fee tier from query."""
    # Look for fee mentions: 500, 3000, 10000 or 0.05%, 0.3%, 1%
    fee_patterns = [
        (r"\b(500|3000|10000)\b", lambda x: int(x)),
        (r"0\.05%", lambda x: 500),
        (r"0\.3%", lambda x: 3000),
        (r"1%", lambda x: 10000),
    ]
    
    for pattern, converter in fee_patterns:
        match = re.search(pattern, query)
        if match:
            return converter(match.group(1) if match.groups() else match.group(0))
    return None

