"""
FastAPI middleware for x402 Hedera payment requirements.
"""

import base64
import json
import logging
from typing import Any, Callable, Optional, cast

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import validate_call

from x402_hedera.common import (
    process_price_to_atomic_amount,
    x402_VERSION,
    find_matching_payment_requirements,
)
from x402_hedera.encoding import safe_base64_decode
from x402_hedera.facilitator import FacilitatorClient, FacilitatorConfig
from x402_hedera.path import path_is_match
from x402_hedera.paywall import is_browser_request, get_paywall_html
from x402_hedera.types import (
    PaymentPayload,
    PaymentRequirements,
    SupportedHederaNetworks,
)

logger = logging.getLogger(__name__)


@validate_call
def require_payment(
    price: str | int,
    pay_to_address: str,
    path: str | list[str] = "*",
    description: str = "",
    mime_type: str = "",
    max_deadline_seconds: int = 60,
    facilitator_config: Optional[FacilitatorConfig] = None,
    network: SupportedHederaNetworks = "hedera-testnet",
    resource: Optional[str] = None,
    asset: Optional[str] = None,
    allowed_paths: Optional[list[str]] = None,
):
    """Generate a FastAPI middleware that gates payments for an endpoint.

    Args:
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

    Returns:
        Callable: FastAPI middleware function that checks for valid payment before processing requests
    """

    try:
        max_amount_required, asset_address, extra_dict = process_price_to_atomic_amount(
            price, network, asset
        )
    except Exception as e:
        raise ValueError(f"Invalid price: {price}. Error: {e}")

    facilitator = FacilitatorClient(facilitator_config)

    async def middleware(request: Request, call_next: Callable):
        # Skip if the path is not the same as the path in the middleware
        if not path_is_match(path, request.url.path):
            return await call_next(request)
        
        # Check if path is in allowed_paths (bypass payment)
        if allowed_paths is not None and path_is_match(allowed_paths, request.url.path):
            return await call_next(request)
        
        # Special case: Allow GET requests to / for agent card discovery
        # POST requests to / (task execution) still require payment
        if request.url.path == "/" and request.method == "GET":
            return await call_next(request)

        # Get resource URL if not explicitly provided
        resource_url = resource or str(request.url)

        # Construct payment details
        payment_requirements = [
            PaymentRequirements(
                scheme="exact",
                network=cast(SupportedHederaNetworks, network),
                asset=asset_address,
                max_amount_required=max_amount_required,
                resource=resource_url,
                description=description,
                mime_type=mime_type,
                pay_to=pay_to_address,
                max_timeout_seconds=max_deadline_seconds,
                extra=extra_dict,
            )
        ]

        def x402_response(error: str):
            """Create a 402 response with payment requirements.
            
            Always returns HTTP 402 status code as per x402 specification.
            Matches TypeScript implementation behavior.
            """
            request_headers = dict(request.headers)
            status_code = 402

            if is_browser_request(request_headers):
                html_content = get_paywall_html(error, payment_requirements)
                headers = {"Content-Type": "text/html; charset=utf-8"}

                return HTMLResponse(
                    content=html_content,
                    status_code=status_code,
                    headers=headers,
                )
            else:
                from x402_hedera.types import x402PaymentRequiredResponse

                # Always return 402 status code with standard x402 Payment Required Response format
                # This matches the TypeScript implementation and x402 specification
                logger.info("💰 402 Payment Required - returning standard x402 format")
                
                payment_response = x402PaymentRequiredResponse(
                    x402_version=x402_VERSION,
                    accepts=payment_requirements,
                    error=error,
                )
                
                # Return standard x402 Payment Required Response format (camelCase per spec)
                # Format: { "x402Version": 1, "error": "...", "accepts": [...] }
                x402_response_data = payment_response.model_dump(by_alias=True)
                
                logger.info(f"   x402Version: {payment_response.x402_version}")
                logger.info(f"   Error: {error[:100]}...")
                logger.info(f"   Payment requirements: {len(payment_requirements)} option(s)")
                if payment_requirements:
                    logger.info(f"   Pay to: {payment_requirements[0].pay_to}")
                    logger.info(f"   Max amount: {payment_requirements[0].max_amount_required}")
                    logger.info(f"   Network: {payment_requirements[0].network}")
                    logger.info(f"   Asset: {payment_requirements[0].asset}")
                
                headers = {"Content-Type": "application/json; charset=utf-8"}

                return JSONResponse(
                    content=x402_response_data,
                    status_code=status_code,  # Always return 402 as per x402 spec
                    headers=headers,
                )

        # Check for payment header
        payment_header = request.headers.get("X-PAYMENT", "")

        if payment_header == "":
            return x402_response("No X-PAYMENT header provided")

        # Decode payment header
        try:
            payment_dict = json.loads(safe_base64_decode(payment_header))
            payment = PaymentPayload(**payment_dict)
        except Exception as e:
            logger.warning(
                f"Invalid payment header format from {request.client.host if request.client else 'unknown'}: {str(e)}"
            )
            return x402_response("Invalid payment header format")

        # Find matching payment requirements
        selected_payment_requirements = find_matching_payment_requirements(
            payment_requirements, payment
        )

        if not selected_payment_requirements:
            return x402_response("No matching payment requirements found")

        # Verify payment
        verify_response = await facilitator.verify(
            payment, selected_payment_requirements
        )

        if not verify_response.is_valid:
            error_reason = verify_response.invalid_reason or "Unknown error"
            return x402_response(f"Invalid payment: {error_reason}")

        request.state.payment_details = selected_payment_requirements
        request.state.verify_response = verify_response

        # Process the request
        response = await call_next(request)

        # Early return without settling if the response is not a 2xx
        if response.status_code < 200 or response.status_code >= 300:
            return response

        # Settle the payment
        try:
            settle_response = await facilitator.settle(
                payment, selected_payment_requirements
            )
            if settle_response.success:
                response.headers["X-PAYMENT-RESPONSE"] = base64.b64encode(
                    settle_response.model_dump_json(by_alias=True).encode("utf-8")
                ).decode("utf-8")
            else:
                return x402_response(
                    "Settle failed: "
                    + (settle_response.error_reason or settle_response.error or "Unknown error")
                )
        except Exception:
            return x402_response("Settle failed")

        return response

    return middleware

