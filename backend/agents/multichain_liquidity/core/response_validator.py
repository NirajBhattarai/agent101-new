"""
Response validation utilities for liquidity agent.

Handles validation and serialization of liquidity responses.
"""

import json
from .constants import RESPONSE_TYPE
from .models.liquidity import StructuredLiquidity
from .exceptions import ValidationError


def validate_and_serialize_response(liquidity_data: dict) -> str:
    """Validate and serialize liquidity response to JSON."""
    try:
        validated_liquidity = StructuredLiquidity(**liquidity_data)
        return json.dumps(validated_liquidity.model_dump(), indent=2)
    except Exception as e:
        raise ValidationError(
            f"Failed to validate liquidity response: {str(e)}",
            details={"liquidity_data": liquidity_data},
        ) from e


def build_error_response(chain: str, token_a: str, token_b: str, error: str) -> str:
    """Build error response."""
    error_data = {
        "type": RESPONSE_TYPE,
        "chain": chain,
        "token_a": token_a,
        "token_b": token_b,
        "results": [],
        "error": error,
    }
    return json.dumps(error_data, indent=2)


def log_response_info(token_a: str, token_b: str, chain: str, response: str) -> None:
    """Log response information."""
    print(f"✅ Returning liquidity response for {token_a}/{token_b} on {chain}")
    print(f"📦 Response length: {len(response)} chars")
    print(f"📄 Response preview: {response[:200]}...")


def validate_json(response: str) -> None:
    """Validate that response is valid JSON."""
    json.loads(response)

