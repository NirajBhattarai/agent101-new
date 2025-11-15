"""
Balance Agent Definition

Defines the BalanceAgent class that handles balance queries using direct tool calls.
"""

from .core.constants import (
    ERROR_VALIDATION_FAILED,
    RESPONSE_TYPE,
)
from .core.response_validator import (
    build_error_response,
    log_response_info,
    validate_and_serialize_response,
    validate_json,
)
from .services.query_parser import parse_query_intent
from .services.response_builder import (
    build_all_chains_token_response,
    build_balance_response,
    build_popular_tokens_response,
    build_token_balance_response,
)





class BalanceAgent:
    """Agent that retrieves account balance information from blockchain chains using direct tool calls."""

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Invoke the agent with a query.

        Supports:
        - Specific token on specific chain: "get USDT on Ethereum"
        - Token across all chains: "get USDT balance"
        - Popular tokens: "get popular tokens"
        - Standard balance queries: "get balance on Polygon"

        Note: Token discovery queries should be handled by Token Research Agent.
        """
        print(f"🔍 Balance Agent received query: {query}")

        try:
            # Parse query intent
            intent = parse_query_intent(query)
            account_address = intent["account_address"]
            chain = intent["chain"]
            token_symbol = intent.get("token_symbol")
            is_popular_tokens = intent.get("is_popular_tokens", False)
            is_all_chains_token = intent.get("is_all_chains_token", False)
            address_error = intent.get("address_error")

            # Handle address validation errors
            if address_error:
                from .core.constants import (
                    ERROR_ACCOUNT_ADDRESS_REQUIRED,
                    ERROR_INVALID_ACCOUNT_ADDRESS,
                )

                error_msg = (
                    ERROR_ACCOUNT_ADDRESS_REQUIRED
                    if "required" in address_error.lower()
                    else ERROR_INVALID_ACCOUNT_ADDRESS
                )
                balance_data = build_error_response(
                    chain, account_address or "unknown", f"{error_msg}: {address_error}"
                )
                response = validate_and_serialize_response(balance_data)
                log_response_info(account_address or "unknown", chain, response)
                return response

            # Handle popular tokens query (get balances of popular tokens)
            if is_popular_tokens:
                print("📊 Fetching popular tokens balances...")
                balance_data = build_popular_tokens_response(account_address)
            # Handle token across all chains
            elif is_all_chains_token and token_symbol:
                print(f"🌐 Fetching {token_symbol} balance across all chains...")
                balance_data = build_all_chains_token_response(account_address, token_symbol)
            # Handle specific token on specific chain
            elif token_symbol and chain != "all":
                print(f"🔍 Fetching {token_symbol} balance on {chain}...")
                balance_data = build_token_balance_response(chain, account_address, token_symbol)
            # Handle standard balance query
            else:
                balance_data = build_balance_response(chain, account_address, token_symbol)

            response = validate_and_serialize_response(balance_data)
            log_response_info(account_address or "N/A", chain, response)

            # Validate JSON format (but don't fail - response is already validated)
            try:
                validate_json(response)
            except Exception as e:
                print(f"⚠️ JSON validation warning: {e}")
                # Response is already valid JSON from validate_and_serialize_response
                # This is just a double-check

            return response
        except Exception as e:
            print(f"❌ Validation error: {e}")
            import traceback

            traceback.print_exc()
            error_msg = f"{ERROR_VALIDATION_FAILED}: {str(e)}"
            try:
                intent = parse_query_intent(query)
                error_response = build_error_response(
                    intent["chain"], intent.get("account_address") or "unknown", error_msg
                )
            except Exception as parse_error:
                # Fallback if even parsing fails
                print(f"❌ Error parsing query for error response: {parse_error}")
                error_response = build_error_response("unknown", "unknown", error_msg)

            # Ensure it's valid JSON
            try:
                import json

                json.loads(error_response)
            except Exception:
                # If error response is not valid JSON, create a simple one
                error_response = json.dumps(
                    {
                        "type": RESPONSE_TYPE,
                        "chain": "unknown",
                        "account_address": "unknown",
                        "balances": [],
                        "total_usd_value": "$0.00",
                        "error": error_msg,
                    },
                    indent=2,
                )

            return error_response
