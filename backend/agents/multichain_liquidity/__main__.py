"""
Multi-Chain Liquidity Agent Server (ADK + A2A Protocol)

Starts the Multi-Chain Liquidity Agent as an A2A Protocol server.
"""

import json
import logging
import os
import warnings

import uvicorn

# Suppress deprecation warning for agent.json endpoint (will be fixed in future a2a-server update)
warnings.filterwarnings(
    "ignore", message=".*Deprecated agent card endpoint.*", category=DeprecationWarning
)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .executor import LiquidityExecutor  # noqa: E402

# Import x402 middleware directly from module to avoid __init__.py clients import
from x402_hedera.starlette.middleware import x402PaymentMiddleware  # noqa: E402

# Configure logger
logger = logging.getLogger("multichain_liquidity")
logger.setLevel(logging.INFO)

# Create console handler if not exists
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Define custom logging middleware
class CustomLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"📥 Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"📤 Response: {response.status_code}")
        
        # Log 402 responses for debugging
        if response.status_code == 402:
            logger.warning("💰 402 Payment Required response detected")
            logger.warning(f"   Path: {request.url.path}")
            logger.warning(f"   Method: {request.method}")
            logger.warning(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        return response


# Railway uses PORT env var, fallback to LIQUIDITY_PORT or default
port = int(os.getenv("PORT", os.getenv("LIQUIDITY_PORT", 9998)))

skill = AgentSkill(
    id="multichain_liquidity_agent",
    name="LiquidityFinder",
    description=(
        "Retrieves liquidity pool information from multiple blockchain chains "
        "(Ethereum, Polygon, Hedera) using parallel execution with ADK. "
        "Queries Uniswap V3 pools on Ethereum and Polygon, and SaucerSwap pools on Hedera. "
        "Supports multiple fee tiers (500, 3000, 10000 basis points) and returns "
        "pool addresses, liquidity amounts, current prices, and tick information."
    ),
    tags=[
        "defi",
        "liquidity",
        "blockchain",
        "multi-chain",
        "adk",
        "parallel",
        "uniswap",
        "saucerswap",
    ],
    examples=[
        "Get liquidity for token pair 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 and 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 on all chains",
        "Check liquidity for 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 and 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270 on Polygon with fee tier 3000",
        "Get liquidity pools for tokens 0x0000000000000000000000000000000000000000 and 0x0000000000000000000000000000000000000001 on Ethereum and Hedera",
        "Show liquidity for token addresses 0x1234567890123456789012345678901234567890 and 0x0987654321098765432109876543210987654321",
        "Get liquidity for USDC/ETH pair on all chains with 0.3% fee tier",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name="LiquidityFinder",
    description=(
        "ADK-powered agent that retrieves liquidity pool information from multiple blockchain chains "
        "using parallel execution. Queries Uniswap V3 pools on Ethereum and Polygon mainnets, "
        "and SaucerSwap pools on Hedera testnet. Supports multiple fee tiers and returns comprehensive "
        "liquidity data including pool addresses, liquidity amounts, current prices, and tick information. "
        "All chain queries execute in parallel for optimal performance."
    ),
    url=cardUrl,
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
    supportsAuthenticatedExtendedCard=False,
)


def main():
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found!")
        print("   Set either GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        print("   Example: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://aistudio.google.com/app/apikey")
        print()

    request_handler = DefaultRequestHandler(
        agent_executor=LiquidityExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    app = server.build()
    logger.info("Building A2A Starlette application")
    logger.info(f"Agent card URL: {cardUrl}")
    
    app.add_middleware(CustomLoggingMiddleware)
    logger.info("Added CustomLoggingMiddleware")
    
    # Add x402 payment middleware if configured
    pay_to_address = "0.0.123456" #os.getenv("X402_PAY_TO_ADDRESS") 
    payment_price = "$0.01" #os.getenv("X402_PAYMENT_PRICE", "$0.01")
    payment_enabled = True #os.getenv("X402_PAYMENT_ENABLED", "false").lower() == "true"
    network = os.getenv("X402_NETWORK", "hedera-testnet")
    
    logger.info("Checking x402 payment configuration")
    logger.debug(f"X402_PAYMENT_ENABLED: {payment_enabled}")
    logger.debug(f"X402_PAY_TO_ADDRESS: {pay_to_address}")
    logger.debug(f"X402_PAYMENT_PRICE: {payment_price}")
    logger.debug(f"X402_NETWORK: {network}")
    
    if payment_enabled and pay_to_address:
        # Define allowed paths that bypass payment (e.g., health checks, agent card)
        # NOTE: POST to / (task execution) is protected - requires payment via X-PAYMENT header
        # GET to / and /.well-known/agent.json are free for agent card discovery
        allowed_paths = [
            "/health",
            "/healthz",
            "/.well-known/agent.json",  # Agent card JSON (GET)
            "/.well-known/agent-card.json",  # Agent card JSON (new format)
            # POST to / (task execution) is protected - requires payment
            # GET to / (agent card) is also protected but browser requests show paywall
        ]
        
        app.add_middleware(
            x402PaymentMiddleware,
            price=payment_price,
            pay_to_address=pay_to_address,
            path="*",  # Protect all paths, except those in allowed_paths
            description="Multi-Chain Liquidity Agent API access",
            network=network,
            allowed_paths=allowed_paths,  # These paths bypass payment
        )
        logger.info("💰 x402 Payment middleware enabled")
        logger.info(f"   Pay to: {pay_to_address}")
        logger.info(f"   Price: {payment_price}")
        logger.info(f"   Network: {network}")
        logger.info(f"   Protected path: * (all paths)")
        logger.info(f"   Allowed paths (bypass payment): {allowed_paths}")
        logger.info(f"   NOTE: POST to / (task execution) requires payment")
        logger.info(f"   NOTE: GET to /.well-known/agent.json is free for discovery")
    else:
        if not payment_enabled:
            logger.info("💡 x402 Payment middleware disabled (X402_PAYMENT_ENABLED not set to 'true')")
        elif not pay_to_address:
            logger.warning("⚠️  x402 Payment middleware disabled (X402_PAY_TO_ADDRESS not configured)")

    logger.info("=" * 60)
    logger.info(f"💧 Starting Multi-Chain Liquidity Agent (ADK + A2A)")
    logger.info(f"   URL: http://0.0.0.0:{port}")
    logger.info(f"   Agent: {public_agent_card.name}")
    logger.info(f"   Description: {public_agent_card.description}")
    logger.info(f"   Version: {public_agent_card.version}")
    logger.info(f"   Skills: {len(public_agent_card.skills)}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
