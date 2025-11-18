"""
Flask middleware for x402 Hedera payment requirements.
"""

import base64
import json
from typing import Any, Dict, Optional, Union, cast
from flask import Flask, request, g
from x402_hedera.path import path_is_match
from x402_hedera.types import (
    PaymentPayload,
    PaymentRequirements,
    SupportedHederaNetworks,
    x402PaymentRequiredResponse,
)
from x402_hedera.common import (
    process_price_to_atomic_amount,
    x402_VERSION,
    find_matching_payment_requirements,
)
from x402_hedera.encoding import safe_base64_decode
from x402_hedera.facilitator import FacilitatorClient, FacilitatorConfig
from x402_hedera.paywall import is_browser_request, get_paywall_html


class ResponseWrapper:
    """Wrapper to capture response status and headers for settlement logic."""

    def __init__(self, start_response):
        self.start_response = start_response
        self.status_code = None
        self.headers = []
        self.body = []

    def __call__(self, status, headers, exc_info=None):
        self.status_code = int(status.split()[0])
        self.headers = headers
        return self.start_response(status, headers, exc_info)

    def add_header(self, name, value):
        """Add a header to the response."""
        self.headers.append((name, value))


class PaymentMiddleware:
    """
    Flask middleware for x402 Hedera payment requirements.
    Allows multiple registrations with different path patterns and configurations.

    Usage:
        middleware = PaymentMiddleware(app)
        middleware.add(path="/weather", price="$0.001", pay_to_address="0.0.123456")
        middleware.add(path="/premium/*", price="0.5", pay_to_address="0.0.123456", asset="0.0.0")
    """

    def __init__(self, app: Flask):
        self.app = app
        self.middleware_configs = []

    def add(
        self,
        price: str | int,
        pay_to_address: str,
        path: Union[str, list[str]] = "*",
        description: str = "",
        mime_type: str = "",
        max_deadline_seconds: int = 60,
        facilitator_config: Optional[FacilitatorConfig] = None,
        network: SupportedHederaNetworks = "hedera-testnet",
        resource: Optional[str] = None,
        asset: Optional[str] = None,
    ):
        """
        Add a payment middleware configuration.

        Args:
            price: Payment price (USD string/int)
            pay_to_address: Hedera account ID to receive payment (e.g., "0.0.123456")
            path: Path(s) to protect. Defaults to "*".
            description: Description of the resource
            mime_type: MIME type of the resource
            max_deadline_seconds: Max time for payment
            facilitator_config: Facilitator config
            network: Network ID (hedera-testnet or hedera-mainnet)
            resource: Resource URL
            asset: Asset identifier (0.0.0 for HBAR, token ID for HTS)
        """
        config = {
            "price": price,
            "pay_to_address": pay_to_address,
            "path": path,
            "description": description,
            "mime_type": mime_type,
            "max_deadline_seconds": max_deadline_seconds,
            "facilitator_config": facilitator_config,
            "network": network,
            "resource": resource,
            "asset": asset,
        }
        self.middleware_configs.append(config)

        # Apply the middleware to the app
        self._apply_middleware()

    def _apply_middleware(self):
        """Apply all middleware configurations to the Flask app."""
        # Create the middleware chain
        current_wsgi_app = self.app.wsgi_app

        for config in self.middleware_configs:
            middleware = self._create_middleware(config, current_wsgi_app)
            current_wsgi_app = middleware

        self.app.wsgi_app = current_wsgi_app

    def _create_middleware(self, config: Dict[str, Any], next_app):
        """Create a WSGI middleware function for the given configuration."""

        # Process price configuration
        try:
            max_amount_required, asset_address, extra_dict = (
                process_price_to_atomic_amount(
                    config["price"], config["network"], config.get("asset")
                )
            )
        except Exception as e:
            raise ValueError(f"Invalid price: {config['price']}. Error: {e}")

        facilitator = FacilitatorClient(config["facilitator_config"])

        def middleware(environ, start_response):
            # Create Flask request context
            with self.app.request_context(environ):
                # Skip if the path is not the same as the path in the middleware
                if not path_is_match(config["path"], request.path):
                    return next_app(environ, start_response)

                # Get resource URL if not explicitly provided
                original_uri = request.headers.get("X-Original-URI")
                if original_uri:
                    # Reconstruct the full URL using the original URI from the proxy
                    resource_url = f"{request.scheme}://{request.host}{original_uri}"
                else:
                    # Fallback to request.url if the header is not present
                    resource_url = config["resource"] or request.url

                # Construct payment details
                payment_requirements = [
                    PaymentRequirements(
                        scheme="exact",
                        network=cast(SupportedHederaNetworks, config["network"]),
                        asset=asset_address,
                        max_amount_required=max_amount_required,
                        resource=resource_url,
                        description=config["description"],
                        mime_type=config["mime_type"],
                        pay_to=config["pay_to_address"],
                        max_timeout_seconds=config["max_deadline_seconds"],
                        extra=extra_dict,
                    )
                ]

                def x402_response(error: str):
                    """Create a 402 response with payment requirements."""
                    request_headers = dict(request.headers)
                    status = "402 Payment Required"

                    if is_browser_request(request_headers):
                        html_content = get_paywall_html(error, payment_requirements)
                        headers = [("Content-Type", "text/html; charset=utf-8")]

                        start_response(status, headers)
                        return [html_content.encode("utf-8")]
                    else:
                        response_data = x402PaymentRequiredResponse(
                            x402_version=x402_VERSION,
                            accepts=payment_requirements,
                            error=error,
                        ).model_dump(by_alias=True)

                        headers = [
                            ("Content-Type", "application/json"),
                            ("Content-Length", str(len(json.dumps(response_data)))),
                        ]

                        start_response(status, headers)
                        return [json.dumps(response_data).encode("utf-8")]

                # Check for payment header
                payment_header = request.headers.get("X-PAYMENT", "")

                if payment_header == "":
                    return x402_response("No X-PAYMENT header provided")

                # Decode payment header
                try:
                    payment_dict = json.loads(safe_base64_decode(payment_header))
                    payment = PaymentPayload(**payment_dict)
                except Exception as e:
                    return x402_response(f"Invalid payment header format: {str(e)}")

                # Find matching payment requirements
                selected_payment_requirements = find_matching_payment_requirements(
                    payment_requirements, payment
                )

                if not selected_payment_requirements:
                    return x402_response("No matching payment requirements found")

                # Verify payment (async call in sync context)
                import asyncio

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    verify_response = loop.run_until_complete(
                        facilitator.verify(payment, selected_payment_requirements)
                    )
                finally:
                    loop.close()

                if not verify_response.is_valid:
                    error_reason = verify_response.invalid_reason or "Unknown error"
                    return x402_response(f"Invalid payment: {error_reason}")

                # Store payment details in Flask g object
                g.payment_details = selected_payment_requirements
                g.verify_response = verify_response

                # Create response wrapper to capture status and headers
                response_wrapper = ResponseWrapper(start_response)

                # Process the request
                response = next_app(environ, response_wrapper)

                # Check if response is successful (2xx status code)
                if (
                    response_wrapper.status_code is not None
                    and response_wrapper.status_code >= 200
                    and response_wrapper.status_code < 300
                ):
                    # Settle the payment for successful responses
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        settle_response = loop.run_until_complete(
                            facilitator.settle(payment, selected_payment_requirements)
                        )

                        if settle_response.success:
                            # Add settlement response header
                            settlement_header = base64.b64encode(
                                settle_response.model_dump_json(by_alias=True).encode(
                                    "utf-8"
                                )
                            ).decode("utf-8")
                            response_wrapper.add_header(
                                "X-PAYMENT-RESPONSE", settlement_header
                            )
                        else:
                            # If settlement fails, we can't return a new response since headers are already sent
                            # Just log the error and continue with the original response
                            print(f"Settle failed: {settle_response.error_reason or settle_response.error}")
                    except Exception as e:
                        # Log the error but don't try to return a new response
                        print(f"Settle failed: {str(e)}")
                    finally:
                        loop.close()

                return response

        return middleware

