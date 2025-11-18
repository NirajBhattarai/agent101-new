"""
Common utilities for x402 Hedera payments.
"""

from decimal import Decimal
from typing import List, Optional, Tuple

from x402_hedera.types import PaymentRequirements, PaymentPayload, SupportedHederaNetworks


# Hedera constants
HBAR_DECIMALS = 8
USDC_TOKEN_ID_TESTNET = "0.0.429274"
USDC_TOKEN_ID_MAINNET = "0.0.456858"  # Update with actual mainnet USDC token ID
USDC_DECIMALS = 6

# x402 protocol version
x402_VERSION = 1


def parse_money(amount: str | int, asset: str, network: str) -> int:
    """Parse money string or int into tinybars or token atomic units.

    Args:
        amount: str | int - if int, should be the full amount including token specific decimals
        asset: Asset identifier (0.0.0 for HBAR, token ID for HTS)
        network: Network identifier (hedera-testnet or hedera-mainnet)

    Returns:
        Amount in atomic units (tinybars for HBAR, token units for HTS)
    """
    if isinstance(amount, str):
        if amount.startswith("$"):
            amount = amount[1:]
        decimal_amount = Decimal(amount)

        # Determine decimals based on asset
        if asset == "0.0.0" or asset.lower() == "hbar":
            decimals = HBAR_DECIMALS
        else:
            # For tokens, use USDC decimals (6) as default
            # In production, you might want to fetch this from the token
            decimals = USDC_DECIMALS

        decimal_amount = decimal_amount * Decimal(10**decimals)
        return int(decimal_amount)
    return amount


def process_price_to_atomic_amount(
    price: str | int, network: SupportedHederaNetworks, asset: Optional[str] = None
) -> Tuple[str, str, dict]:
    """Process a Price into atomic amount, asset address, and extra info.

    Args:
        price: Money amount (USD string/int) - will be converted to USDC or HBAR
        network: Network identifier
        asset: Optional asset identifier. If None, defaults to USDC for testnet

    Returns:
        Tuple of (max_amount_required, asset_address, extra_dict)

    Raises:
        ValueError: If price format is invalid
    """
    try:
        if isinstance(price, str) and price.startswith("$"):
            price = price[1:]
        amount = Decimal(str(price))

        # Determine asset
        if asset is None:
            # Default to USDC for testnet
            if network == "hedera-testnet":
                asset_address = USDC_TOKEN_ID_TESTNET
                decimals = USDC_DECIMALS
            else:
                asset_address = USDC_TOKEN_ID_MAINNET
                decimals = USDC_DECIMALS
        elif asset == "0.0.0" or asset.lower() == "hbar":
            asset_address = "0.0.0"
            decimals = HBAR_DECIMALS
        else:
            asset_address = asset
            decimals = USDC_DECIMALS  # Default to USDC decimals for tokens

        # Convert to atomic units
        atomic_amount = int(amount * Decimal(10**decimals))

        # Extra dict for Hedera (can include facilitator info)
        extra_dict = {}

        return str(atomic_amount), asset_address, extra_dict

    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid price format: {price}. Error: {e}")


def find_matching_payment_requirements(
    payment_requirements: List[PaymentRequirements],
    payment: PaymentPayload,
) -> Optional[PaymentRequirements]:
    """
    Finds the matching payment requirements for the given payment.

    Args:
        payment_requirements: The payment requirements to search through
        payment: The payment to match against

    Returns:
        The matching payment requirements or None if no match is found
    """
    for req in payment_requirements:
        if req.scheme == payment.scheme and req.network == payment.network:
            return req
    return None

