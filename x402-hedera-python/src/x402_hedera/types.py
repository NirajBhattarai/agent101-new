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
    max_timeout_seconds: int = Field(60, alias="maxTimeoutSeconds", description="Maximum timeout in seconds")
    description: str = Field("", description="Description of the resource")
    mime_type: str = Field("", alias="mimeType", description="MIME type of the resource")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra payment requirements")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_validator("max_amount_required")
    def validate_max_amount_required(cls, v):
        try:
            int(v)
        except ValueError:
            raise ValueError(
                "max_amount_required must be an integer encoded as a string"
            )
        return v


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
    error_reason: Optional[str] = Field(None, alias="errorReason", description="Detailed error reason")
    transaction_id: Optional[str] = Field(None, alias="transactionId", description="Settled transaction ID")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class x402PaymentRequiredResponse(BaseModel):
    """Response returned by a server as JSON alongside a 402 response code."""

    x402_version: int = Field(..., alias="x402Version", description="x402 protocol version")
    accepts: list[PaymentRequirements] = Field(..., description="List of accepted payment requirements")
    error: str = Field("", description="Error message if payment is invalid")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

