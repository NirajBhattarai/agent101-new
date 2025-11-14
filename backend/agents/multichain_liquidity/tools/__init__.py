"""
Tools for multi-chain liquidity agents.

Exports liquidity query functions and their ADK FunctionDeclarations.
"""

# Try google.genai.types first (newer API)
try:
    from google.genai.types import FunctionDeclaration, Schema  # noqa: E402
except ImportError:
    # Fallback to google.adk.types
    try:
        from google.adk.types import FunctionDeclaration, Schema  # noqa: E402
    except ImportError:
        # If neither is available, create a dummy class
        class FunctionDeclaration:
            def __init__(self, **kwargs):
                pass

        class Schema:
            def __init__(self, **kwargs):
                pass


from .ethereum import get_ethereum_liquidity
from .hedera import get_hedera_liquidity
from .log_message import log_message
from .polygon import get_polygon_liquidity

# Function declarations for ADK
get_ethereum_liquidity_func = FunctionDeclaration(
    name="get_ethereum_liquidity",
    description="Get liquidity for a token pair on Ethereum mainnet. Returns pool address, liquidity amount, and current price data.",
    parameters=Schema(
        type="object",
        properties={
            "token_a": Schema(type="string", description="Token A address (EVM format: 0x...)"),
            "token_b": Schema(type="string", description="Token B address (EVM format: 0x...)"),
            "fee": Schema(
                type="integer",
                description="Pool fee tier in basis points. Options: 500 (0.05%), 3000 (0.3%), 10000 (1%)",
            ),
        },
        required=["token_a", "token_b"],
    ),
)

get_polygon_liquidity_func = FunctionDeclaration(
    name="get_polygon_liquidity",
    description="Get liquidity for a token pair on Polygon mainnet. Returns pool address, liquidity amount, and current price data.",
    parameters=Schema(
        type="object",
        properties={
            "token_a": Schema(type="string", description="Token A address (EVM format: 0x...)"),
            "token_b": Schema(type="string", description="Token B address (EVM format: 0x...)"),
            "fee": Schema(
                type="integer",
                description="Pool fee tier in basis points. Options: 500 (0.05%), 3000 (0.3%), 10000 (1%)",
            ),
        },
        required=["token_a", "token_b"],
    ),
)

get_hedera_liquidity_func = FunctionDeclaration(
    name="get_hedera_liquidity",
    description="Get liquidity for a token pair on Hedera testnet (SaucerSwap). Returns pool address, liquidity amount, and current price data.",
    parameters=Schema(
        type="object",
        properties={
            "token_a": Schema(type="string", description="Token A address (EVM format: 0x...)"),
            "token_b": Schema(type="string", description="Token B address (EVM format: 0x...)"),
            "fee": Schema(
                type="integer",
                description="Pool fee tier in basis points. Options: 500 (0.05%), 3000 (0.3%), 10000 (1%)",
            ),
        },
        required=["token_a", "token_b"],
    ),
)

__all__ = [
    "get_ethereum_liquidity",
    "get_polygon_liquidity",
    "get_hedera_liquidity",
    "log_message",
    "get_ethereum_liquidity_func",
    "get_polygon_liquidity_func",
    "get_hedera_liquidity_func",
]
