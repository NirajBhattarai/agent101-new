"""
requests client integration for x402 Hedera payments.
"""

from typing import Optional
import requests
import json
import copy
from requests.adapters import HTTPAdapter
from hiero_sdk_python import AccountId, PrivateKey, Client

from x402_hedera.clients.base import (
    x402HederaClient,
    PaymentError,
    PaymentSelectorCallable,
)
from x402_hedera.types import x402PaymentRequiredResponse


class x402HTTPAdapter(HTTPAdapter):
    """HTTP adapter for handling x402 payment required responses."""

    def __init__(
        self,
        client: Client,
        account_id: AccountId,
        private_key: PrivateKey,
        max_value: Optional[int] = None,
        payment_requirements_selector: Optional[PaymentSelectorCallable] = None,
        **kwargs,
    ):
        """Initialize the adapter with an x402HederaClient.

        Args:
            client: Hiero Client instance for Hedera operations
            account_id: AccountId for the paying account
            private_key: PrivateKey for signing payments
            max_value: Optional maximum allowed payment amount in tinybars
            payment_requirements_selector: Optional custom selector for payment requirements
            **kwargs: Additional arguments to pass to HTTPAdapter
        """
        super().__init__(**kwargs)
        self.x402_client = x402HederaClient(
            client=client,
            account_id=account_id,
            private_key=private_key,
            max_value=max_value,
            payment_requirements_selector=payment_requirements_selector,
        )
        self._is_retry = False

    def send(self, request, **kwargs):
        """Send a request with payment handling for 402 responses.

        Args:
            request: The PreparedRequest being sent
            **kwargs: Additional arguments to pass to the adapter

        Returns:
            Response object
        """
        if self._is_retry:
            self._is_retry = False
            return super().send(request, **kwargs)

        response = super().send(request, **kwargs)

        if response.status_code != 402:
            return response

        try:
            # Save the content before we parse it to avoid consuming it
            content = copy.deepcopy(response.content)

            # Parse the JSON content without using response.json() which consumes it
            data = json.loads(content.decode("utf-8"))
            payment_response = x402PaymentRequiredResponse(**data)

            # Select payment requirements
            selected_requirements = self.x402_client.select_payment_requirements(
                payment_response.accepts
            )

            # Create payment header (async call in sync context)
            import asyncio

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                payment_header = loop.run_until_complete(
                    self.x402_client.create_payment_header(
                        selected_requirements, payment_response.x402_version
                    )
                )
            finally:
                loop.close()

            # Mark as retry and add payment header
            self._is_retry = True
            request.headers["X-Payment"] = payment_header
            request.headers["Access-Control-Expose-Headers"] = "X-Payment-Response"

            retry_response = super().send(request, **kwargs)

            # Copy the retry response data to the original response
            response.status_code = retry_response.status_code
            response.headers = retry_response.headers
            response._content = retry_response.content
            return response

        except PaymentError as e:
            self._is_retry = False
            raise e
        except Exception as e:
            self._is_retry = False
            raise PaymentError(f"Failed to handle payment: {str(e)}") from e


def x402_http_adapter(
    client: Client,
    account_id: AccountId,
    private_key: PrivateKey,
    max_value: Optional[int] = None,
    payment_requirements_selector: Optional[PaymentSelectorCallable] = None,
    **kwargs,
) -> x402HTTPAdapter:
    """Create an HTTP adapter that handles 402 Payment Required responses.

    Args:
        client: Hiero Client instance for Hedera operations
        account_id: AccountId for the paying account
        private_key: PrivateKey for signing payments
        max_value: Optional maximum allowed payment amount in tinybars
        payment_requirements_selector: Optional custom selector for payment requirements.
            Should be a callable that takes (accepts, network_filter, scheme_filter, max_value)
            and returns a PaymentRequirements object.
        **kwargs: Additional arguments to pass to HTTPAdapter

    Returns:
        x402HTTPAdapter instance that can be mounted to a requests session
    """
    return x402HTTPAdapter(
        client,
        account_id,
        private_key,
        max_value=max_value,
        payment_requirements_selector=payment_requirements_selector,
        **kwargs,
    )


def x402_requests(
    client: Client,
    account_id: AccountId,
    private_key: PrivateKey,
    max_value: Optional[int] = None,
    payment_requirements_selector: Optional[PaymentSelectorCallable] = None,
    **kwargs,
) -> requests.Session:
    """Create a requests session with x402 Hedera payment handling.

    Args:
        client: Hiero Client instance for Hedera operations
        account_id: AccountId for the paying account
        private_key: PrivateKey for signing payments
        max_value: Optional maximum allowed payment amount in tinybars
        payment_requirements_selector: Optional custom selector for payment requirements.
            Should be a callable that takes (accepts, network_filter, scheme_filter, max_value)
            and returns a PaymentRequirements object.
        **kwargs: Additional arguments to pass to HTTPAdapter

    Returns:
        Session with x402 payment handling configured
    """
    session = requests.Session()
    adapter = x402_http_adapter(
        client,
        account_id,
        private_key,
        max_value=max_value,
        payment_requirements_selector=payment_requirements_selector,
        **kwargs,
    )

    # Mount the adapter for both HTTP and HTTPS
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

