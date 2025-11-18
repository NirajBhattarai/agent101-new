"""
Facilitator client for x402 Hedera payments.
"""

from typing import Callable, Optional
from typing_extensions import TypedDict
import httpx

from x402_hedera.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
)


class FacilitatorConfig(TypedDict, total=False):
    """Configuration for the x402 facilitator service.

    Attributes:
        url: The base URL for the facilitator service
        create_headers: Optional function to create authentication headers
    """

    url: str
    create_headers: Callable[[], dict[str, dict[str, str]]]


class FacilitatorClient:
    """Client for interacting with x402 facilitator service."""

    def __init__(self, config: Optional[FacilitatorConfig] = None):
        if config is None:
            config = {"url": "https://x402-hedera-production.up.railway.app"}

        # Validate URL format
        url = config.get("url", "")
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL {url}, must start with http:// or https://")
        if url.endswith("/"):
            url = url[:-1]

        self.config = {"url": url, "create_headers": config.get("create_headers")}

    async def verify(
        self, payment: PaymentPayload, payment_requirements: PaymentRequirements
    ) -> VerifyResponse:
        """Verify a payment header is valid and a request should be processed."""
        headers = {"Content-Type": "application/json"}

        if self.config.get("create_headers"):
            custom_headers = await self.config["create_headers"]()
            headers.update(custom_headers.get("verify", {}))

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config['url']}/verify",
                json={
                    "x402Version": payment.x402_version,
                    "paymentPayload": payment.model_dump(by_alias=True),
                    "paymentRequirements": payment_requirements.model_dump(
                        by_alias=True, exclude_none=True
                    ),
                },
                headers=headers,
                follow_redirects=True,
            )

            data = response.json()
            return VerifyResponse(**data)

    async def settle(
        self, payment: PaymentPayload, payment_requirements: PaymentRequirements
    ) -> SettleResponse:
        """Settle a verified payment."""
        headers = {"Content-Type": "application/json"}

        if self.config.get("create_headers"):
            custom_headers = await self.config["create_headers"]()
            headers.update(custom_headers.get("settle", {}))

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config['url']}/settle",
                json={
                    "x402Version": payment.x402_version,
                    "paymentPayload": payment.model_dump(by_alias=True),
                    "paymentRequirements": payment_requirements.model_dump(
                        by_alias=True, exclude_none=True
                    ),
                },
                headers=headers,
                follow_redirects=True,
            )
            data = response.json()
            return SettleResponse(**data)

