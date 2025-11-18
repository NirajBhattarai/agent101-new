# x402 Payment Middleware Setup

The multichain liquidity agent now supports x402 payment protocol for Hedera Hashgraph. This allows you to charge for API access using HBAR or HTS tokens.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your configuration (see Configuration section below)

3. The middleware is imported directly from `x402_hedera.starlette` package

## Configuration

Set the following environment variables to enable x402 payments (see `.env.example` for template):

```bash
# Enable x402 payment middleware
export X402_PAYMENT_ENABLED=true

# Hedera account ID to receive payments (required if enabled)
export X402_PAY_TO_ADDRESS="0.0.123456"

# Payment price (default: $0.01)
export X402_PAYMENT_PRICE="$0.01"

# Hedera network (default: hedera-testnet)
export X402_NETWORK="hedera-testnet"

# Facilitator URL (optional, defaults to public facilitator)
export X402_FACILITATOR_URL="https://x402-hedera-production.up.railway.app"
```

## How It Works

1. When `X402_PAYMENT_ENABLED=true` and `X402_PAY_TO_ADDRESS` is set, the middleware protects API endpoints matching `/api/*`
2. Requests without a valid `X-PAYMENT` header receive a `402 Payment Required` response
3. Clients can use the x402-hedera-python clients (httpx or requests) to automatically handle payments
4. Payments are verified and settled through the facilitator service

## Example Client Usage

### Using httpx client:

```python
from hiero import AccountId, PrivateKey, Client
from x402_hedera.clients import x402HttpxClient

client = Client.for_testnet()
account_id = AccountId.from_string("0.0.123456")
private_key = PrivateKey.from_string("...")

async with x402HttpxClient(
    client, 
    account_id, 
    private_key, 
    base_url="http://localhost:9998"
) as http_client:
    response = await http_client.get("/api/liquidity")
    print(await response.aread())
```

### Using requests client:

```python
from hiero import AccountId, PrivateKey, Client
from x402_hedera.clients import x402_requests

client = Client.for_testnet()
account_id = AccountId.from_string("0.0.123456")
private_key = PrivateKey.from_string("...")

session = x402_requests(client, account_id, private_key)
response = session.get("http://localhost:9998/api/liquidity")
print(response.content)
```

## Disabling Payments

To disable payments, either:
- Set `X402_PAYMENT_ENABLED=false` (or leave unset)
- Remove `X402_PAY_TO_ADDRESS` environment variable

The agent will still function normally, just without payment protection.

## Notes

- The middleware only protects paths matching `/api/*` by default
- Health checks, agent card endpoints, and other non-API endpoints remain free
- Payments are processed on Hedera testnet by default (set `X402_NETWORK=hedera-mainnet` for production)
- The facilitator handles payment verification and settlement automatically

