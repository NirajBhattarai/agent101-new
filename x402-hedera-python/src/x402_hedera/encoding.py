"""
Encoding utilities for x402 Hedera payments.
"""

import base64
from typing import Any, Dict


def safe_base64_encode(data: bytes) -> str:
    """Safely encode bytes to base64 string."""
    return base64.b64encode(data).decode("utf-8")


def safe_base64_decode(data: str) -> bytes:
    """Safely decode base64 string to bytes."""
    try:
        return base64.b64decode(data)
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {e}")


def encode_payment(payment: Dict[str, Any]) -> str:
    """Encode payment payload to base64 string for X-PAYMENT header."""
    import json

    payment_json = json.dumps(payment, separators=(",", ":"))
    return safe_base64_encode(payment_json.encode("utf-8"))


def decode_payment(encoded: str) -> Dict[str, Any]:
    """Decode base64 payment header to payment payload."""
    import json

    decoded_bytes = safe_base64_decode(encoded)
    return json.loads(decoded_bytes.decode("utf-8"))

