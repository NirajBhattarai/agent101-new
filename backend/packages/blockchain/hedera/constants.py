"""
Hedera token addresses and IDs.

Comprehensive list of Hedera token addresses (Hedera format) and EVM addresses.

Each token has: address (EVM), decimals, and tokenid (Hedera format).
"""

# Hedera tokens - Dictionary format with address, decimals, and tokenid
# tokenid is hedera token id (0.0.123456) and tokenaddress is evm address (0x...)

HEDERA_TOKENS = {
    "HBAR": {
        "address": "0x0000000000000000000000000000000000000000",  # EVM address
        "decimals": 8,
        "tokenid": "0.0.0",  # Native token
    },
    "USDC": {
        "address": "0x000000000000000000000000000000000006f89a",
        "decimals": 6,
        "tokenid": "0.0.456858",
    },
    "SAUCE": {
        "address": "0x00000000000000000000000000000000000b2ad5",
        "decimals": 8,
        "tokenid": "0.0.731861",
    },
    "JAM": {
        "address": "0x000000000000000000000000000000000001f3f5",
        "decimals": 8,
        "tokenid": "0.0.127877",
    },
    "WHBAR": {
        "address": "0x0000000000000000000000000000000000163B5a",
        "decimals": 8,
        "tokenid": "0.0.1456986",
    },
}

# Legacy format mappings for backward compatibility
# Hedera tokens - Hedera format addresses (0.0.123456) - for balance checking
HEDERA_TOKEN_IDS = {symbol: token["tokenid"] for symbol, token in HEDERA_TOKENS.items()}

# Hedera token EVM address mapping - for contract calls
HEDERA_TOKEN_EVM_ADDRESSES = {symbol: token["address"] for symbol, token in HEDERA_TOKENS.items()}
