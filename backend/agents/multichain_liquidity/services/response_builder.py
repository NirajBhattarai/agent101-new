"""
Response building utilities for liquidity agent.

Handles construction of liquidity responses from parallel agent results.
"""

from typing import Optional
from ..core.constants import CHAIN_ALL, CHAIN_ETHEREUM, CHAIN_POLYGON, CHAIN_HEDERA
from ..core.models.liquidity import LiquidityResult, StructuredLiquidity


def build_liquidity_response(
    chain: str,
    token_a: str,
    token_b: str,
    ethereum_result: Optional[dict] = None,
    polygon_result: Optional[dict] = None,
    hedera_result: Optional[dict] = None,
) -> dict:
    """Build liquidity response from parallel agent results."""
    results = []
    
    # Process Ethereum result
    if chain in [CHAIN_ALL, CHAIN_ETHEREUM] and ethereum_result:
        if isinstance(ethereum_result, dict):
            results.append(LiquidityResult(**ethereum_result))
        elif isinstance(ethereum_result, str):
            # Try to parse if it's a JSON string
            import json
            try:
                parsed = json.loads(ethereum_result)
                if isinstance(parsed, dict):
                    results.append(LiquidityResult(**parsed))
            except:
                pass
    
    # Process Polygon result
    if chain in [CHAIN_ALL, CHAIN_POLYGON] and polygon_result:
        if isinstance(polygon_result, dict):
            results.append(LiquidityResult(**polygon_result))
        elif isinstance(polygon_result, str):
            import json
            try:
                parsed = json.loads(polygon_result)
                if isinstance(parsed, dict):
                    results.append(LiquidityResult(**parsed))
            except:
                pass
    
    # Process Hedera result
    if chain in [CHAIN_ALL, CHAIN_HEDERA] and hedera_result:
        if isinstance(hedera_result, dict):
            results.append(LiquidityResult(**hedera_result))
        elif isinstance(hedera_result, str):
            import json
            try:
                parsed = json.loads(hedera_result)
                if isinstance(parsed, dict):
                    results.append(LiquidityResult(**parsed))
            except:
                pass
    
    return StructuredLiquidity(
        chain=chain,
        token_a=token_a,
        token_b=token_b,
        results=results,
    ).model_dump()

