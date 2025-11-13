"""
Constants for liquidity tools.

Contains chain configurations, RPC URLs, and fee tier definitions.
"""

import os

# RPC URLs from environment
ETHEREUM_MAINNET_RPC = os.getenv("ETHEREUM_MAINNET_RPC", "https://eth.llamarpc.com")
POLYGON_MAINNET_RPC = os.getenv("POLYGON_MAINNET_RPC", "https://polygon.llamarpc.com")
HEDERA_TESTNET_RPC = os.getenv("HEDERA_TESTNET_RPC", "https://testnet.hashio.io/api")

# Fee tiers (basis points)
FEE_TIER_500 = 500   # 0.05%
FEE_TIER_3000 = 3000  # 0.3%
FEE_TIER_10000 = 10000  # 1%

# Default fee tier
DEFAULT_FEE_TIER = FEE_TIER_3000

# Supported fee tiers
SUPPORTED_FEE_TIERS = [FEE_TIER_500, FEE_TIER_3000, FEE_TIER_10000]

# Chain names
CHAIN_ETHEREUM = "ethereum"
CHAIN_POLYGON = "polygon"
CHAIN_HEDERA = "hedera"

# Network names
NETWORK_MAINNET = "mainnet"
NETWORK_TESTNET = "testnet"

