"""
Base client for handling x402 Hedera payments.
"""

import time
import secrets
from typing import Optional, Callable, List
from hiero_sdk_python import AccountId, PrivateKey, Client

from x402_hedera.types import (
    PaymentRequirements,
    PaymentPayload,
    SupportedHederaNetworks,
)
from x402_hedera.client import create_payment_header
from x402_hedera.encoding import safe_base64_decode
import json

# Define type for the payment requirements selector
PaymentSelectorCallable = Callable[
    [List[PaymentRequirements], Optional[str], Optional[str], Optional[int]],
    PaymentRequirements,
]


def decode_x_payment_response(header: str) -> dict:
    """Decode the X-PAYMENT-RESPONSE header.

    Args:
        header: The X-PAYMENT-RESPONSE header to decode

    Returns:
        The decoded payment response containing:
        - success: bool
        - transaction: str (transaction ID)
        - network: str
        - payer: str (account ID)
    """
    decoded = safe_base64_decode(header)
    result = json.loads(decoded)
    return result


class PaymentError(Exception):
    """Base class for payment-related errors."""

    pass


class PaymentAmountExceededError(PaymentError):
    """Raised when payment amount exceeds maximum allowed value."""

    pass


class MissingRequestConfigError(PaymentError):
    """Raised when request configuration is missing."""

    pass


class PaymentAlreadyAttemptedError(PaymentError):
    """Raised when payment has already been attempted."""

    pass


class UnsupportedSchemeException(PaymentError):
    """Raised when no supported payment scheme is found."""

    pass


class x402HederaClient:
    """Base client for handling x402 Hedera payments."""

    def __init__(
        self,
        client: Client,
        account_id: AccountId,
        private_key: PrivateKey,
        max_value: Optional[int] = None,
        payment_requirements_selector: Optional[PaymentSelectorCallable] = None,
    ):
        """Initialize the x402 Hedera client.

        Args:
            client: Hiero Client instance for Hedera operations
            account_id: AccountId for the paying account
            private_key: PrivateKey for signing payments
            max_value: Optional maximum allowed payment amount in tinybars
            payment_requirements_selector: Optional custom selector for payment requirements
        """
        self.client = client
        self.account_id = account_id
        self.private_key = private_key
        self.max_value = max_value
        self._payment_requirements_selector = (
            payment_requirements_selector or self.default_payment_requirements_selector
        )

    @staticmethod
    def default_payment_requirements_selector(
        accepts: List[PaymentRequirements],
        network_filter: Optional[str] = None,
        scheme_filter: Optional[str] = None,
        max_value: Optional[int] = None,
    ) -> PaymentRequirements:
        """Select payment requirements from the list of accepted requirements.

        Args:
            accepts: List of accepted payment requirements
            network_filter: Optional network to filter by (e.g., "hedera-testnet")
            scheme_filter: Optional scheme to filter by (e.g., "exact")
            max_value: Optional maximum allowed payment amount in tinybars

        Returns:
            Selected payment requirements

        Raises:
            UnsupportedSchemeException: If no supported scheme is found
            PaymentAmountExceededError: If payment amount exceeds max_value
        """
        for payment_requirements in accepts:
            scheme = payment_requirements.scheme
            network = payment_requirements.network

            # Check scheme filter
            if scheme_filter and scheme != scheme_filter:
                continue

            # Check network filter
            if network_filter and network != network_filter:
                continue

            if scheme == "exact":
                # Check max value if set
                if max_value is not None:
                    max_amount = int(payment_requirements.max_amount_required)
                    if max_amount > max_value:
                        raise PaymentAmountExceededError(
                            f"Payment amount {max_amount} exceeds maximum allowed value {max_value}"
                        )

                return payment_requirements

        raise UnsupportedSchemeException("No supported payment scheme found")

    def select_payment_requirements(
        self,
        accepts: List[PaymentRequirements],
        network_filter: Optional[str] = None,
        scheme_filter: Optional[str] = None,
    ) -> PaymentRequirements:
        """Select payment requirements using the configured selector.

        Args:
            accepts: List of accepted payment requirements
            network_filter: Optional network to filter by
            scheme_filter: Optional scheme to filter by

        Returns:
            Selected payment requirements

        Raises:
            UnsupportedSchemeException: If no supported scheme is found
            PaymentAmountExceededError: If payment amount exceeds max_value
        """
        return self._payment_requirements_selector(
            accepts, network_filter, scheme_filter, self.max_value
        )

    async def create_payment_header(
        self,
        payment_requirements: PaymentRequirements,
        x402_version: int = 1,
    ) -> str:
        """Create a payment header for the given requirements.

        Args:
            payment_requirements: Selected payment requirements
            x402_version: x402 protocol version

        Returns:
            Signed payment header (base64 encoded)
        """
        return await create_payment_header(
            client=self.client,
            account_id=self.account_id,
            private_key=self.private_key,
            x402_version=x402_version,
            payment_requirements=payment_requirements,
        )

    def generate_nonce(self) -> str:
        """Generate a random nonce (32 bytes = 64 hex chars)."""
        return secrets.token_hex(32)

