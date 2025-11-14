"""Executor validation utilities for balance agent."""

import json

from ..core.constants import (
    CHAIN_UNKNOWN,
    DEFAULT_TOTAL_USD_VALUE,
    ERROR_INVALID_JSON,
    RESPONSE_TYPE,
)


def validate_response_content(content: str) -> str:
    """
    Validate response content and ensure it's valid JSON.

    Args:
        content: Response content string

    Returns:
        Validated content string (guaranteed to be valid JSON)

    Raises:
        ValueError: If content cannot be validated or converted to valid JSON
    """
    if not content or not content.strip():
        # Return a valid error response JSON
        return json.dumps(
            {
                "type": RESPONSE_TYPE,
                "chain": CHAIN_UNKNOWN,
                "account_address": "unknown",
                "balances": [],
                "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
                "error": "Empty response from agent",
            },
            indent=2,
        )

    # Try to parse and validate JSON
    try:
        parsed = json.loads(content)

        # Ensure it's a dict
        if not isinstance(parsed, dict):
            raise ValueError("Response must be a JSON object")

        # Ensure required fields exist
        if "type" not in parsed:
            parsed["type"] = RESPONSE_TYPE
        if "chain" not in parsed:
            parsed["chain"] = CHAIN_UNKNOWN
        if "account_address" not in parsed:
            parsed["account_address"] = "unknown"
        if "balances" not in parsed:
            parsed["balances"] = []
        if "total_usd_value" not in parsed:
            parsed["total_usd_value"] = DEFAULT_TOTAL_USD_VALUE

        # Re-serialize to ensure clean JSON
        return json.dumps(parsed, indent=2)

    except json.JSONDecodeError as e:
        # If content is not valid JSON, wrap it in a valid error response
        print(f"⚠️ Warning: Response is not valid JSON: {e}")
        print(f"   Content preview: {content[:200]}")
        return json.dumps(
            {
                "type": RESPONSE_TYPE,
                "chain": CHAIN_UNKNOWN,
                "account_address": "unknown",
                "balances": [],
                "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
                "error": f"{ERROR_INVALID_JSON}: {str(e)}",
                "raw_response": content[:500] if len(content) > 500 else content,
            },
            indent=2,
        )


def log_sending_response(content: str) -> None:
    """Log sending response."""
    print(f"📤 Sending balance response (length: {len(content)} chars)")
