"""
Client for creating x402 Hedera payment headers.
"""

from typing import TYPE_CHECKING

from x402_hedera.types import PaymentPayload, PaymentRequirements
from x402_hedera.encoding import encode_payment

if TYPE_CHECKING:
    from hiero import AccountId, PrivateKey, Client


async def create_payment_header(
    client: "Client",
    account_id: "AccountId",
    private_key: "PrivateKey",
    x402_version: int,
    payment_requirements: PaymentRequirements,
) -> str:
    """Create and encode a payment header for the given client and payment requirements.

    Args:
        client: The Hedera client instance
        account_id: The account ID making the payment
        private_key: The private key for signing
        x402_version: The version of the x402 protocol to use
        payment_requirements: The payment requirements containing scheme and network information

    Returns:
        A base64 encoded payment header string

    Raises:
        Error if payment creation or encoding fails
    """
    payment_payload = await create_and_sign_payment(
        client=client,
        account_id=account_id,
        private_key=private_key,
        x402_version=x402_version,
        payment_requirements=payment_requirements,
    )
    return encode_payment(payment_payload.model_dump(by_alias=True))


async def create_and_sign_payment(
    client: "Client",
    account_id: "AccountId",
    private_key: "PrivateKey",
    x402_version: int,
    payment_requirements: PaymentRequirements,
) -> PaymentPayload:
    """Create and sign a payment for the given client and payment requirements.

    Args:
        client: The Hedera client instance
        account_id: The account ID making the payment
        private_key: The private key for signing
        x402_version: The version of the x402 protocol to use
        payment_requirements: The payment requirements containing transfer details

    Returns:
        A payment payload containing a base64 encoded Hedera transaction

    Raises:
        Error if transaction creation, signing, or serialization fails
    """
    from hiero import (
        TransferTransaction,
        AccountId as HederaAccountId,
        TokenId,
        Hbar,
        TransactionId,
    )
    from x402_hedera.encoding import safe_base64_encode

    # Extract facilitator's account ID from payment requirements
    facilitator_account_id_str = payment_requirements.extra.get("feePayer") if payment_requirements.extra else None
    if not facilitator_account_id_str:
        raise ValueError("feePayer is required in paymentRequirements.extra")

    facilitator_account_id = HederaAccountId.from_string(facilitator_account_id_str)
    recipient_account_id = HederaAccountId.from_string(payment_requirements.pay_to)
    amount = int(payment_requirements.max_amount_required)

    # Generate transaction ID with facilitator as the fee payer
    transaction_id = TransactionId.generate(facilitator_account_id)

    # Determine if this is HBAR or token transfer
    asset = payment_requirements.asset or "0.0.0"
    is_hbar = asset == "0.0.0" or asset.lower() == "hbar"

    # Create transfer transaction
    if is_hbar:
        # HBAR transfer
        transaction = (
            TransferTransaction()
            .set_transaction_id(transaction_id)
            .add_hbar_transfer(account_id, Hbar.from_tinybars(-amount))
            .add_hbar_transfer(recipient_account_id, Hbar.from_tinybars(amount))
        )
    else:
        # Token transfer
        token_id = TokenId.from_string(asset)
        transaction = (
            TransferTransaction()
            .set_transaction_id(transaction_id)
            .add_token_transfer(token_id, account_id, -amount)
            .add_token_transfer(token_id, recipient_account_id, amount)
        )

    # Freeze and sign the transaction
    transaction = transaction.freeze_with(client)
    signed_transaction = transaction.sign(private_key)

    # Serialize to bytes and encode to base64
    transaction_bytes = signed_transaction.to_bytes()
    base64_encoded_transaction = safe_base64_encode(transaction_bytes)

    # Return payment payload
    return PaymentPayload(
        scheme=payment_requirements.scheme,
        network=payment_requirements.network,
        x402_version=x402_version,
        payload={"transaction": base64_encoded_transaction},
    )

