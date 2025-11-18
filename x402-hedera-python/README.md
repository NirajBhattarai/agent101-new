# x402-hedera-python

Python implementation of the x402 Payment Protocol for Hedera Hashgraph.

## Overview

This package provides Python bindings for implementing x402 payment flows on the Hedera network, supporting both native HBAR and HTS (Hedera Token Service) token payments.

## Installation

```bash
# From the package directory
pip install -e .

# Or add to your backend's pyproject.toml dependencies
```

## Features

- **Hedera Native Support**: Full support for HBAR and HTS token payments
- **Facilitator Integration**: Built-in facilitator client for payment verification and settlement
- **Transaction Signing**: Create and sign Hedera transactions for x402 payments
- **Type Safety**: Full Pydantic models for type-safe payment handling

## Quick Start

### Creating a Payment Header

```python
from x402_hedera import create_payment_header
from hiero import AccountId, PrivateKey, Client

# Initialize Hedera client
account_id = AccountId.from_string("0.0.123456")
private_key = PrivateKey.from_string("...")
client = Client.for_testnet()
client.set_operator(account_id, private_key)

# Create payment requirements
payment_requirements = PaymentRequirements(
    scheme="exact",
    network="hedera-testnet",
    max_amount_required="100000000",  # 1 HBAR in tinybars
    pay_to="0.0.789012",
    asset="0.0.0",  # HBAR native token
    extra={"feePayer": "0.0.999999"}  # Facilitator account
)

# Create payment header
payment_header = await create_payment_header(
    client=client,
    account_id=account_id,
    private_key=private_key,
    x402_version=1,
    payment_requirements=payment_requirements
)
```

### Using the Facilitator Client

```python
from x402_hedera import FacilitatorClient

# Initialize facilitator
facilitator = FacilitatorClient(
    config={
        "url": "http://localhost:3002",  # Your facilitator URL
    }
)

# Verify payment
verify_response = await facilitator.verify(
    payment=payment_payload,
    payment_requirements=payment_requirements
)

if verify_response.is_valid:
    # Settle payment
    settle_response = await facilitator.settle(
        payment=payment_payload,
        payment_requirements=payment_requirements
    )
```

## Project Structure

```
x402-hedera-python/
├── src/
│   └── x402_hedera/
│       ├── __init__.py
│       ├── types.py          # Pydantic models
│       ├── facilitator.py    # Facilitator client
│       ├── client.py          # Payment creation
│       ├── encoding.py        # Encoding utilities
│       └── schemes/
│           └── exact/
│               ├── __init__.py
│               ├── client.py   # Exact scheme client
│               └── facilitator.py  # Exact scheme facilitator
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .

# Lint code
ruff check .
```

## License

Apache-2.0

