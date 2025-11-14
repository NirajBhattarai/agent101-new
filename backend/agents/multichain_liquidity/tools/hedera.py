"""Hedera liquidity tool."""

import os

from packages.blockchain.hedera.saucerswap.pool.web3_client import (
    SaucerSwapWeb3Client,
)

# Default to mainnet for now (as requested)
HEDERA_MAINNET_RPC = os.getenv("HEDERA_MAINNET_RPC", "https://mainnet.hashio.io/api")
HEDERA_TESTNET_RPC = os.getenv("HEDERA_TESTNET_RPC", HEDERA_MAINNET_RPC)


def get_hedera_liquidity(token_a: str, token_b: str, fee: int = 3000) -> dict:
    """
    Get liquidity for a token pair on Hedera (SaucerSwap).

    Args:
        token_a: Token A address (EVM format: 0x...)
        token_b: Token B address (EVM format: 0x...)
        fee: Pool fee tier (500, 1500, 3000, or 10000)

    Returns:
        Dictionary with pool address, liquidity, and slot0 data
    """
    try:
        from packages.blockchain.hedera.constants import HEDERA_TOKENS

        print(f"🔍 get_hedera_liquidity called: token_a={token_a}, token_b={token_b}, fee={fee}")

        # Convert native HBAR (0x0000...) to wHBAR for pool lookups
        HBAR_NATIVE_ADDRESS = "0x0000000000000000000000000000000000000000"
        if token_a == HBAR_NATIVE_ADDRESS:
            whbar_info = HEDERA_TOKENS.get("WHBAR", {})
            token_a = whbar_info.get("address", token_a)
            print(f"🔄 Converted HBAR to wHBAR for pool lookup: {token_a}")

        if token_b == HBAR_NATIVE_ADDRESS:
            whbar_info = HEDERA_TOKENS.get("WHBAR", {})
            token_b = whbar_info.get("address", token_b)
            print(f"🔄 Converted HBAR to wHBAR for pool lookup: {token_b}")

        print(f"🔍 Using addresses: token_a={token_a}, token_b={token_b}")

        # Use mainnet by default (as requested)
        client = SaucerSwapWeb3Client(rpc_url=HEDERA_MAINNET_RPC, network="mainnet")
        print(f"🔍 Factory address: {client.factory_address}")
        print(f"🔍 RPC URL: {HEDERA_MAINNET_RPC}")
        print(f"🔍 Client type: {type(client).__name__}")
        print(f"🔍 Has get_pool_info override: {hasattr(client, 'get_pool_info')}")
        print(f"🔍 get_pool_info method: {client.get_pool_info}")
        print(
            f"🔍 HEDERA_FEE_TIERS: {client._fee_tiers if hasattr(client, '_fee_tiers') else 'N/A'}"
        )

        # Try all fee tiers (get_pool_info will try all Hedera fee tiers: 500, 1500, 3000, 10000)
        pool_info = client.get_pool_info(token_a, token_b, fee=fee)
        print(f"🔍 Pool info result: {pool_info}")

        if pool_info:
            # pool_info is a TypedDict (PoolInfo), access like a dictionary
            pool_address = pool_info.get("pool_address", "")
            liquidity = pool_info.get("liquidity", 0)
            slot0 = pool_info.get("slot0", {})
            found_fee = pool_info.get("fee", fee)

            # Extract slot0 data
            tick = slot0.get("tick", 0) if isinstance(slot0, dict) else 0
            sqrt_price_x96 = slot0.get("sqrtPriceX96", 0) if isinstance(slot0, dict) else 0

            print(f"✅ Found pool: address={pool_address}, fee={found_fee}, liquidity={liquidity}")

            return {
                "chain": "hedera",
                "network": "mainnet",
                "pool_address": pool_address,
                "token_a": token_a,
                "token_b": token_b,
                "fee": found_fee,  # Use the actual fee tier found
                "liquidity": str(liquidity) if liquidity else "0",
                "tick": tick,
                "sqrt_price_x96": str(sqrt_price_x96) if sqrt_price_x96 else "0",
                "status": "success",
            }
        else:
            return {
                "chain": "hedera",
                "network": "mainnet",
                "pool_address": None,
                "token_a": token_a,
                "token_b": token_b,
                "fee": fee,
                "liquidity": None,
                "status": "pool_not_found",
            }
    except Exception as e:
        return {
            "chain": "hedera",
            "network": "mainnet",
            "token_a": token_a,
            "token_b": token_b,
            "fee": fee,
            "status": "error",
            "error": str(e),
        }
