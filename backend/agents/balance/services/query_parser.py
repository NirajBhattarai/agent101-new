"""
Query parsing utilities for balance agent.

Handles extraction of account addresses and chain detection from queries.
"""

import re
from typing import Optional

from ..core.constants import (
    CHAIN_ALL,
    CHAIN_ETHEREUM,
    CHAIN_HEDERA,
    CHAIN_POLYGON,
    DEFAULT_CHAIN,
)
from .token_parser import (
    extract_token_symbol,
    is_all_chains_token_query,
    is_popular_tokens_query,
    is_token_discovery_query,
    is_token_specific_query,
)


def extract_hedera_address(query: str) -> Optional[str]:
    """Extract Hedera account address from query."""
    match = re.search(r"0\.0\.\d+", query)
    return match.group() if match else None


def extract_evm_address(query: str) -> Optional[str]:
    """Extract EVM address from query."""
    match = re.search(r"0x[a-fA-F0-9]{40}", query)
    return match.group() if match else None


def extract_account_address(query: str) -> Optional[str]:
    """Extract account address from query. Returns None if not found."""
    hedera_addr = extract_hedera_address(query)
    if hedera_addr:
        return hedera_addr
    evm_addr = extract_evm_address(query)
    if evm_addr:
        return evm_addr
    return None


def detect_chain_from_address(address: str, query: str = "") -> str:
    """
    Detect chain from address format.
    For EVM addresses, tries to infer from query context first.
    """
    if address.startswith("0.0."):
        return CHAIN_HEDERA
    if address.startswith("0x"):
        # Try to infer from query context first
        query_lower = query.lower()
        if "ethereum" in query_lower or ("eth" in query_lower and "hedera" not in query_lower):
            return CHAIN_ETHEREUM
        if "polygon" in query_lower or "matic" in query_lower:
            return CHAIN_POLYGON
        # If no context, check if it's a known Ethereum address pattern
        # (Ethereum addresses are more common, so default to Ethereum)
        # But this is a fallback - ideally query should specify chain
        return CHAIN_ETHEREUM  # Default to Ethereum as it's more common
    return DEFAULT_CHAIN


def detect_chain_from_query(query: str) -> Optional[str]:
    """Detect chain from query text."""
    query_lower = query.lower()
    if "ethereum" in query_lower or ("eth" in query_lower and "hedera" not in query_lower):
        return CHAIN_ETHEREUM
    if "polygon" in query_lower:
        return CHAIN_POLYGON
    if "hedera" in query_lower:
        return CHAIN_HEDERA
    if "all" in query_lower or "all chains" in query_lower:
        return CHAIN_ALL
    return None


def parse_chain(query: str, account_address: Optional[str]) -> str:
    """Parse chain from query and address."""
    chain = detect_chain_from_query(query)
    if chain:
        return chain
    if account_address:
        return detect_chain_from_address(account_address, query)
    return DEFAULT_CHAIN


def validate_account_address(
    address: Optional[str], require_address: bool = True
) -> tuple[Optional[str], Optional[str]]:
    """
    Validate account address format.

    Returns:
        Tuple of (validated_address, error_message)
    """
    if address is None:
        if require_address:
            return None, "Account address is required"
        return None, None

    # Validate Hedera format
    if address.startswith("0.0."):
        parts = address.split(".")
        if len(parts) == 3:
            try:
                int(parts[0])
                int(parts[1])
                int(parts[2])
                return address, None
            except ValueError:
                return None, "Invalid Hedera address format"

    # Validate EVM format
    if address.startswith("0x"):
        if len(address) == 42 and all(c in "0123456789abcdefABCDEF" for c in address[2:]):
            return address, None
        return None, "Invalid EVM address format"

    return None, "Unknown address format"


def parse_query_intent(query: str) -> dict:
    """
    Parse query to determine intent and extract parameters.

    Returns:
        Dictionary with:
        - account_address: Extracted account address (None if not found)
        - chain: Chain name or "all"
        - token_symbol: Token symbol if specified
        - is_token_specific: Whether query is for a specific token
        - is_popular_tokens: Whether query is for popular tokens
        - is_token_discovery: Whether query is for token discovery
        - is_all_chains_token: Whether query is for token across all chains
        - address_error: Error message if address validation failed
    """
    account_address = extract_account_address(query)
    chain = parse_chain(query, account_address)
    token_symbol = extract_token_symbol(query)

    # Validate address (don't require for token discovery or popular tokens queries)
    is_discovery = is_token_discovery_query(query)
    is_popular = is_popular_tokens_query(query)
    require_address = not (is_discovery or is_popular)

    validated_address, address_error = validate_account_address(account_address, require_address)

    # Adjust chain if token query without chain specification
    if is_all_chains_token_query(query) and token_symbol:
        chain = CHAIN_ALL

    return {
        "account_address": validated_address,
        "chain": chain,
        "token_symbol": token_symbol,
        "is_token_specific": is_token_specific_query(query),
        "is_popular_tokens": is_popular_tokens_query(query),
        "is_token_discovery": is_token_discovery_query(query),
        "is_all_chains_token": is_all_chains_token_query(query),
        "address_error": address_error,
    }
