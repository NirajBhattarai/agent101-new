"""
Starlette middleware for x402 Hedera payment requirements.
"""

import os
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from x402_hedera.fastapi.middleware import require_payment as create_fastapi_middleware
from x402_hedera.types import SupportedHederaNetworks


class x402PaymentMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware for x402 Hedera payment requirements.
    
    This wraps the FastAPI middleware function to work with Starlette applications.
    Since FastAPI is built on Starlette, the middleware function is compatible.
    
    Usage:
        from x402_hedera.starlette import x402PaymentMiddleware
        
        app.add_middleware(
            x402PaymentMiddleware,
            price="$0.01",
            pay_to_address="0.0.123456",
            path="/api/*",
            allowed_paths=["/api/health", "/api/liquidity"],  # These paths bypass payment
        )
    """

    def __init__(
        self,
        app,
        price: str | int,
        pay_to_address: str,
        path: str | list[str] = "*",
        description: str = "",
        mime_type: str = "",
        max_deadline_seconds: int = 60,
        facilitator_config: Optional[dict] = None,
        network: SupportedHederaNetworks = "hedera-testnet",
        resource: Optional[str] = None,
        asset: Optional[str] = None,
        allowed_paths: Optional[list[str]] = None,
    ):
        """Initialize the x402 payment middleware.

        Args:
            app: The Starlette application
            price: Payment price as USD string/int (e.g., "$0.01", 0.01, "0.001")
            pay_to_address: Hedera account ID to receive the payment (e.g., "0.0.123456")
            path: Path to gate with payments. Defaults to "*" for all paths.
            description: Description of what is being purchased. Defaults to "".
            mime_type: MIME type of the resource. Defaults to "".
            max_deadline_seconds: Maximum time allowed for payment. Defaults to 60.
            facilitator_config: Configuration for the payment facilitator.
                If not provided, defaults to the public Hedera facilitator.
            network: Hedera network ID. Defaults to "hedera-testnet".
            resource: Resource URL. Defaults to None (uses request URL).
            asset: Asset identifier. Defaults to None (uses USDC for testnet, HBAR if "0.0.0").
            allowed_paths: List of paths that bypass payment requirements.
                Supports exact matches, glob patterns, and regex patterns (prefix with 'regex:').
                Defaults to None (no allowed paths).
        """
        super().__init__(app)
        
        # Get facilitator URL from config or environment or use default
        if facilitator_config is None:
            facilitator_url = os.getenv(
                "X402_FACILITATOR_URL",
                "https://x402-hedera-production.up.railway.app"
            )
            facilitator_config = {"url": facilitator_url}
        
        # Create the FastAPI middleware function
        # This returns a callable that takes (request, call_next) which is compatible with Starlette
        self.payment_middleware = create_fastapi_middleware(
            price=price,
            pay_to_address=pay_to_address,
            path=path,
            description=description,
            mime_type=mime_type,
            max_deadline_seconds=max_deadline_seconds,
            facilitator_config=facilitator_config,
            network=network,
            resource=resource,
            asset=asset,
            allowed_paths=allowed_paths,
        )

    async def dispatch(self, request: Request, call_next):
        """Dispatch the request through the x402 payment middleware."""
        # The FastAPI middleware function is already compatible with Starlette
        # It expects (request, call_next) which matches Starlette's middleware pattern
        return await self.payment_middleware(request, call_next)

