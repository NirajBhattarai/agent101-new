"""Web3 client for interacting with SaucerSwap pools."""

from packages.blockchain.dex.base import BaseUniswapV3Client
from packages.blockchain.hedera.saucerswap.constants import NETWORKS

# Hedera-specific fee tiers (includes 1500 bps which SaucerSwap uses)
# Standard Uniswap V3 tiers: 500, 3000, 10000
# SaucerSwap also uses: 1500
HEDERA_FEE_TIERS = [500, 1500, 3000, 10000]  # 0.05%, 0.15%, 0.3%, 1%

# Re-export for backward compatibility
FEE_TIERS = HEDERA_FEE_TIERS

__all__ = ["SaucerSwapWeb3Client", "FEE_TIERS", "HEDERA_FEE_TIERS"]


class SaucerSwapWeb3Client(BaseUniswapV3Client):
    """Web3 client for SaucerSwap DEX interactions."""

    def __init__(self, rpc_url: str, network: str = "mainnet"):
        """
        Initialize Web3 client.

        Args:
            rpc_url: RPC endpoint URL
            network: Network type - "mainnet" or "testnet"
        """
        network = network.lower()
        if network not in NETWORKS:
            raise ValueError(
                f"Unsupported network: {network}. Supported networks: {list(NETWORKS.keys())}"
            )

        factory_address = NETWORKS[network]["factory"]
        network_name = NETWORKS[network]["name"]

        super().__init__(
            rpc_url=rpc_url,
            factory_address=factory_address,
            network_name=network_name,
        )
        self.network = network
        # Override fee tiers for Hedera (includes 1500)
        self._fee_tiers = HEDERA_FEE_TIERS

    def get_pool_address(
        self,
        token_a: str,
        token_b: str,
        fee: int = 3000,
    ):
        """
        Get pool address from factory (Hedera-specific with 1500 fee tier support).

        Overrides base method to support Hedera fee tiers including 1500.

        Args:
            token_a: Token A address (EVM format: 0x...)
            token_b: Token B address (EVM format: 0x...)
            fee: Pool fee tier in basis points (500, 1500, 3000, or 10000)

        Returns:
            Pool address if exists, None otherwise

        Raises:
            InvalidFeeTierError: If invalid fee tier
            InvalidAddressError: If invalid address format
            ValueError: If contract call fails
        """
        from packages.blockchain.dex.utils.errors import InvalidFeeTierError, InvalidAddressError
        from packages.blockchain.dex.utils.address import normalize_address

        if fee not in HEDERA_FEE_TIERS:
            raise InvalidFeeTierError(
                f"Invalid fee tier: {fee}. Supported fees for Hedera: {HEDERA_FEE_TIERS}"
            )

        if not token_a or not token_b:
            raise InvalidAddressError("Both token_a and token_b addresses are required")

        if token_a == token_b:
            raise InvalidAddressError("token_a and token_b must be different")

        # Normalize and sort addresses
        try:
            token_a = normalize_address(token_a)
            token_b = normalize_address(token_b)
        except ValueError as e:
            raise InvalidAddressError(f"Invalid address format: {str(e)}") from e

        token0, token1 = (token_a, token_b) if token_a < token_b else (token_b, token_a)

        try:
            self.logger.info(f"🔍 Calling factory.getPool(token0={token0}, token1={token1}, fee={fee}) on factory {self.factory_address}")
            pool_address = self.factory_contract.functions.getPool(token0, token1, fee).call()
            self.logger.info(f"🔍 Factory returned pool_address: {pool_address}")
            
            # Check if pool exists (0x0000... means no pool)
            if not pool_address or pool_address == "0x0000000000000000000000000000000000000000":
                self.logger.debug(f"❌ No pool exists for fee {fee} bps (returned 0x0000...)")
                return None
            
            self.logger.info(f"✅ Pool found: {pool_address} for fee {fee} bps")
            return pool_address
        except Exception as e:
            # Handle contract call errors - pool might not exist, which is okay
            error_msg = str(e)
            error_str_lower = error_msg.lower()
            
            # Check for various forms of "pool doesn't exist" errors
            if any(phrase in error_str_lower for phrase in [
                "execution reverted",
                "contract_execution_exception",
                "revert",
                "pool does not exist"
            ]):
                # Pool doesn't exist for this fee tier - this is expected, not an error
                self.logger.debug(f"❌ Pool does not exist for fee {fee} bps (contract reverted): {error_msg}")
                return None
            
            # Other errors should be raised
            self.logger.warning(f"⚠️ Error calling factory.getPool: {error_msg}")
            raise ValueError(f"Failed to get pool address: {error_msg}") from e

    def get_pool_info(
        self,
        token_a: str,
        token_b: str,
        fee: int = 3000,
    ):
        """
        Get complete pool information including address, liquidity, and slot0.
        Tries all Hedera fee tiers (500, 1500, 3000, 10000) until a pool is found.

        Overrides base method to use Hedera-specific fee tiers.

        Args:
            token_a: Token A address
            token_b: Token B address
            fee: Pool fee tier (used as starting point, then tries all fees)

        Returns:
            PoolInfo dictionary or None if pool doesn't exist for any fee tier
        """
        self.logger.info(
            f"Searching for pool: token_a={token_a}, token_b={token_b}, "
            f"network={self.network_name}, starting_fee={fee}"
        )

        # Create ordered list of fees to try: start with provided fee, then try others
        fees_to_try = [fee] + [f for f in HEDERA_FEE_TIERS if f != fee]
        
        self.logger.info(f"🔍 Hedera fee tiers to try: {fees_to_try} (HEDERA_FEE_TIERS={HEDERA_FEE_TIERS})")

        from packages.blockchain.dex.base.types import PoolInfo
        from packages.blockchain.dex.utils.address import normalize_address

        for current_fee in fees_to_try:
            self.logger.info(f"🔍 Trying fee tier: {current_fee} bps for {token_a}/{token_b}")

            try:
                pool_address = self.get_pool_address(token_a, token_b, current_fee)
                if not pool_address:
                    self.logger.debug(f"❌ No pool found for fee tier {current_fee} bps")
                    continue

                self.logger.info(f"✅ Pool address found for fee {current_fee} bps: {pool_address}")

                try:
                    liquidity = self.get_pool_liquidity(pool_address)
                    slot0 = self.get_pool_slot0(pool_address)

                    # Normalize addresses for token0/token1
                    token_a_norm = normalize_address(token_a).lower()
                    token_b_norm = normalize_address(token_b).lower()

                    self.logger.info(
                        f"Successfully retrieved pool info: fee={current_fee} bps, "
                        f"liquidity={liquidity}, tick={slot0['tick']}, "
                        f"pool_address={pool_address}"
                    )

                    pool_info_dict = PoolInfo(
                        pool_address=pool_address,
                        token0=min(token_a_norm, token_b_norm),
                        token1=max(token_a_norm, token_b_norm),
                        fee=current_fee,
                        liquidity=liquidity,
                        slot0=slot0,
                    )
                    self.logger.info(f"✅ Returning pool info: {pool_info_dict}")
                    return pool_info_dict
                except Exception as e:
                    self.logger.error(
                        f"Error retrieving pool info for fee {current_fee} bps, "
                        f"pool_address={pool_address}: {str(e)}",
                        exc_info=True,
                    )
                    # If this fee tier fails, try the next one
                    continue
            except ValueError as e:
                # ValueError from get_pool_address means contract call failed
                # But we already handle "execution reverted" in get_pool_address, so this shouldn't happen
                # Unless it's a different error - log it but continue
                error_msg = str(e)
                if "Failed to get pool address" in error_msg:
                    # This means get_pool_address raised ValueError, but we should have caught reverted errors
                    # Check if it's a reverted error that slipped through
                    if "execution reverted" in error_msg.lower() or "CONTRACT_EXECUTION_EXCEPTION" in error_msg:
                        self.logger.debug(f"❌ Pool does not exist for fee {current_fee} bps (caught in get_pool_info): {error_msg}")
                    else:
                        self.logger.warning(f"⚠️ Unexpected error getting pool address for fee {current_fee} bps: {error_msg}")
                else:
                    self.logger.warning(f"⚠️ Error getting pool address for fee {current_fee} bps: {error_msg}")
                continue
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Unexpected exception getting pool address for fee {current_fee} bps: {str(e)}"
                )
                continue

        # No pool found for any fee tier
        self.logger.warning(
            f"❌ No pool found for any fee tier. Tried Hedera fees: {fees_to_try}. "
            f"token_a={token_a}, token_b={token_b}, network={self.network_name}, factory={self.factory_address}"
        )
        return None
