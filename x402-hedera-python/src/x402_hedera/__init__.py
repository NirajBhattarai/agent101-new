"""
x402-hedera-python: x402 Payment Protocol implementation for Hedera Hashgraph.

This package provides Python bindings for the x402 payment protocol specifically
designed for Hedera Hashgraph network, supporting both native HBAR and HTS token payments.
"""

__version__ = "0.1.0"

from x402_hedera.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
)
from x402_hedera.facilitator import FacilitatorClient
from x402_hedera.client import create_payment_header, create_and_sign_payment

__all__ = [
    "PaymentPayload",
    "PaymentRequirements",
    "VerifyResponse",
    "SettleResponse",
    "FacilitatorClient",
    "create_payment_header",
    "create_and_sign_payment",
]

