"""
FastAPI middleware for x402 Hedera payments.
"""

from x402_hedera.fastapi.middleware import require_payment

__all__ = ["require_payment"]

