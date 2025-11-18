"""
x402-hedera-python: x402 Payment Protocol implementation for Hedera Hashgraph.

This package provides Python bindings for the x402 payment protocol specifically
designed for Hedera Hashgraph network, supporting both native HBAR and HTS token payments.
"""

__version__ = "0.1.0"

# Core types
from x402_hedera.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
    x402PaymentRequiredResponse,
    SupportedHederaNetworks,
)

# Facilitator
from x402_hedera.facilitator import FacilitatorClient, FacilitatorConfig

# Client functions
from x402_hedera.client import create_payment_header, create_and_sign_payment

# HTTP clients (lazy import to avoid requiring hiero at package level)
def _import_clients():
    """Lazy import of clients to avoid requiring hiero at package level."""
    from x402_hedera.clients import (
        x402HederaClient,
        x402HttpxClient,
        x402_requests,
        x402_http_adapter,
        x402_payment_hooks,
        PaymentError,
        PaymentAmountExceededError,
    )
    return {
        "x402HederaClient": x402HederaClient,
        "x402HttpxClient": x402HttpxClient,
        "x402_requests": x402_requests,
        "x402_http_adapter": x402_http_adapter,
        "x402_payment_hooks": x402_payment_hooks,
        "PaymentError": PaymentError,
        "PaymentAmountExceededError": PaymentAmountExceededError,
    }

# Server middleware (lazy imports to avoid circular dependencies)
def _get_require_payment():
    """Lazy import of FastAPI middleware."""
    from x402_hedera.fastapi import require_payment
    return require_payment

def _get_payment_middleware():
    """Lazy import of Flask middleware."""
    from x402_hedera.flask import PaymentMiddleware
    return PaymentMiddleware

def _get_x402_payment_middleware():
    """Lazy import of Starlette middleware."""
    from x402_hedera.starlette import x402PaymentMiddleware
    return x402PaymentMiddleware

# For backward compatibility, try to import but don't fail if clients aren't available
try:
    from x402_hedera.fastapi import require_payment
    from x402_hedera.flask import PaymentMiddleware
    from x402_hedera.starlette import x402PaymentMiddleware
except ImportError:
    # If import fails (e.g., missing hiero), set to None
    require_payment = None
    PaymentMiddleware = None
    x402PaymentMiddleware = None

# Utilities
from x402_hedera.common import x402_VERSION, process_price_to_atomic_amount, find_matching_payment_requirements
from x402_hedera.encoding import encode_payment, decode_payment, safe_base64_encode, safe_base64_decode
from x402_hedera.path import path_is_match
from x402_hedera.paywall import get_paywall_html, is_browser_request

__all__ = [
    # Types
    "PaymentPayload",
    "PaymentRequirements",
    "VerifyResponse",
    "SettleResponse",
    "x402PaymentRequiredResponse",
    "SupportedHederaNetworks",
    # Facilitator
    "FacilitatorClient",
    "FacilitatorConfig",
    # Client functions
    "create_payment_header",
    "create_and_sign_payment",
    # HTTP clients (use _import_clients() to get these)
    "_import_clients",
    # Server middleware
    "require_payment",
    "PaymentMiddleware",
    "x402PaymentMiddleware",
    # Utilities
    "x402_VERSION",
    "process_price_to_atomic_amount",
    "find_matching_payment_requirements",
    "encode_payment",
    "decode_payment",
    "safe_base64_encode",
    "safe_base64_decode",
    "path_is_match",
    "get_paywall_html",
    "is_browser_request",
]

