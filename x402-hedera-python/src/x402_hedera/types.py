"""
Type definitions for x402 Hedera payment protocol.
"""

from __future__ import annotations

from typing import Any, Optional, Dict, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


# Supported Hedera networks
SupportedHederaNetworks = Literal["hedera-testnet", "hedera-mainnet"]


class PaymentPayload(BaseModel):
    """Payment payload containing transaction data."""

    scheme: str = Field(..., description="Payment scheme (e.g., 'exact')")
    network: SupportedHederaNetworks = Field(..., description="Hedera network")
    x402_version: int = Field(..., alias="x402Version", description="x402 protocol version")
    payload: Dict[str, Any] = Field(..., description="Payment payload data")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ExactHederaPayload(TypedDict):
    """Exact Hedera payment payload structure."""

    transaction: str  # Base64 encoded Hedera transaction


class PaymentRequirements(BaseModel):
    """Payment requirements for x402 payment."""

    scheme: str = Field(..., description="Payment scheme")
    network: SupportedHederaNetworks = Field(..., description="Hedera network")
    max_amount_required: str = Field(..., alias="maxAmountRequired", description="Maximum amount in atomic units")
    resource: Optional[str] = Field(None, description="Resource identifier")
    pay_to: Optional[str] = Field(None, alias="payTo", description="Recipient account ID")
    asset: Optional[str] = Field(None, description="Asset identifier (0.0.0 for HBAR, token ID for HTS)")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra payment requirements")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class VerifyResponse(BaseModel):
    """Response from payment verification."""

    is_valid: bool = Field(..., alias="isValid", description="Whether payment is valid")
    invalid_reason: Optional[str] = Field(None, alias="invalidReason", description="Reason if invalid")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SettleResponse(BaseModel):
    """Response from payment settlement."""

    success: bool = Field(..., description="Whether settlement was successful")
    error: Optional[str] = Field(None, description="Error message if settlement failed")
    transaction_id: Optional[str] = Field(None, alias="transactionId", description="Settled transaction ID")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

