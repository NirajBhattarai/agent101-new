"""
Multi-Chain Liquidity Agent Definition

Defines the LiquidityAgent class that handles liquidity queries using parallel execution with ParallelAgent.
"""

import os
# Follow https://google.github.io/adk-docs/get-started/quickstart/ to learn the setup
try:
    # Try google.genai.agents first (newer API)
    from google.genai.agents import LlmAgent, ParallelAgent, SequentialAgent  # noqa: E402
except ImportError:
    try:
        # Fallback to google.adk.agents
        from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
        from google.adk.agents.parallel_agent import ParallelAgent  # noqa: E402
        from google.adk.agents.sequential_agent import SequentialAgent  # noqa: E402
    except ImportError:
        # Final fallback
        from google.adk.agents import LlmAgent, ParallelAgent  # noqa: E402
        try:
            from google.adk.agents.sequential_agent import SequentialAgent  # noqa: E402
        except ImportError:
            SequentialAgent = None  # SequentialAgent may not be available

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.memory.in_memory_memory_service import (  # noqa: E402
    InMemoryMemoryService,
)
from google.adk.artifacts import InMemoryArtifactService  # noqa: E402

from .tools import (  # noqa: E402
    get_ethereum_liquidity,
    get_polygon_liquidity,
    get_hedera_liquidity,
    log_message,
)
from .core.constants import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_USER_ID,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    AGENT_INSTRUCTION,
    ERROR_VALIDATION_FAILED,
)
from .services.query_parser import (  # noqa: E402
    extract_token_addresses,
    parse_chain,
    extract_fee_tier,
)
from .services.response_builder import build_liquidity_response  # noqa: E402
from .core.response_validator import (  # noqa: E402
    validate_and_serialize_response,
    log_response_info,
    validate_json,
    build_error_response,
)


# Gemini model configuration (following ADK quickstart pattern)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

def _get_model_name() -> str:
    """Get Gemini model name from environment."""
    return GEMINI_MODEL


def _check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")


# --- 1. Define Chain-Specific Sub-Agents (to run in parallel) ---
def _build_chain_sub_agents() -> tuple[LlmAgent, LlmAgent, LlmAgent]:
    """Build chain-specific sub-agents for parallel execution."""
    # Agent 1: Ethereum Liquidity Researcher
    ethereum_agent = LlmAgent(
        name="EthereumLiquidityAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI agent specializing in Ethereum blockchain liquidity analysis.

Your task:
1. Extract token addresses (token_a and token_b) from the user's request
2. Use the get_ethereum_liquidity tool to fetch liquidity data
3. If fee tier is not specified, default to 3000 (0.3%)
4. Return the result as a JSON object with chain, pool_address, liquidity, tick, and status.

Output *only* the JSON result, no additional commentary.
""",
        description="Gets liquidity data for token pairs on Ethereum mainnet.",
        tools=[get_ethereum_liquidity],
        # Store result in state for the merger agent
        output_key="ethereum_liquidity_result",
    )

    # Agent 2: Polygon Liquidity Researcher
    polygon_agent = LlmAgent(
        name="PolygonLiquidityAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI agent specializing in Polygon blockchain liquidity analysis.

Your task:
1. Extract token addresses (token_a and token_b) from the user's request
2. Use the get_polygon_liquidity tool to fetch liquidity data
3. If fee tier is not specified, default to 3000 (0.3%)
4. Return the result as a JSON object with chain, pool_address, liquidity, tick, and status.

Output *only* the JSON result, no additional commentary.
""",
        description="Gets liquidity data for token pairs on Polygon mainnet.",
        tools=[get_polygon_liquidity],
        # Store result in state for the merger agent
        output_key="polygon_liquidity_result",
    )

    # Agent 3: Hedera Liquidity Researcher
    hedera_agent = LlmAgent(
        name="HederaLiquidityAgent",
        model=GEMINI_MODEL,
        instruction="""You are an AI agent specializing in Hedera blockchain liquidity analysis.

Your task:
1. Extract token addresses (token_a and token_b) from the user's request
2. Use the get_hedera_liquidity tool to fetch liquidity data
3. If fee tier is not specified, default to 3000 (0.3%)
4. Return the result as a JSON object with chain, pool_address, liquidity, tick, and status.

Output *only* the JSON result, no additional commentary.
""",
        description="Gets liquidity data for token pairs on Hedera testnet (SaucerSwap).",
        tools=[get_hedera_liquidity],
        # Store result in state for the merger agent
        output_key="hedera_liquidity_result",
    )

    return ethereum_agent, polygon_agent, hedera_agent


# --- 2. Create the ParallelAgent (Runs chain agents concurrently) ---
def _build_parallel_agent() -> ParallelAgent:
    """Build parallel agent with chain-specific sub-agents."""
    ethereum_agent, polygon_agent, hedera_agent = _build_chain_sub_agents()
    
    # This agent orchestrates the concurrent execution of the chain agents.
    # It finishes once all chain agents have completed and stored their results in state.
    return ParallelAgent(
        name="ParallelLiquidityAgent",
        sub_agents=[ethereum_agent, polygon_agent, hedera_agent],
        description="Runs multiple chain-specific liquidity agents in parallel to gather liquidity data across Ethereum, Polygon, and Hedera.",
    )


class LiquidityAgent:
    """Agent that retrieves liquidity pool information from blockchain chains using parallel execution with ParallelAgent."""

    def __init__(self):
        _check_api_keys()
        
        # Build parallel agent with sub-agents
        self._parallel_agent = _build_parallel_agent()
        self._user_id = DEFAULT_USER_ID
        
        self._runner = Runner(
            app_name=AGENT_NAME,
            agent=self._parallel_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """Invoke the agent with a query."""
        print(f"💧 Liquidity Agent received query: {query}")
        
        # Parse query
        token_a, token_b = extract_token_addresses(query)
        chain = parse_chain(query)
        fee = extract_fee_tier(query) or 3000
        
        if not token_a or not token_b:
            error_msg = "Could not extract token addresses from query. Please provide two token addresses (0x...)"
            return build_error_response(chain, token_a or "unknown", token_b or "unknown", error_msg)
        
        try:
            # Build query for parallel agent
            parallel_query = f"Get liquidity for token pair {token_a} and {token_b} with fee {fee}"
            
            # Run parallel agent - sub-agents execute concurrently
            result = await self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                message=parallel_query,
            )
            
            # Extract results from parallel agent state
            # Results are stored in state with output_key names
            ethereum_result = None
            polygon_result = None
            hedera_result = None
            
            if hasattr(result, 'state') and result.state:
                state = result.state
                ethereum_result = state.get("ethereum_liquidity_result")
                polygon_result = state.get("polygon_liquidity_result")
                hedera_result = state.get("hedera_liquidity_result")
                
                # If results are strings, try to parse them
                import json
                if isinstance(ethereum_result, str):
                    try:
                        ethereum_result = json.loads(ethereum_result)
                    except:
                        pass
                if isinstance(polygon_result, str):
                    try:
                        polygon_result = json.loads(polygon_result)
                    except:
                        pass
                if isinstance(hedera_result, str):
                    try:
                        hedera_result = json.loads(hedera_result)
                    except:
                        pass
            
            # Fallback: If ParallelAgent doesn't populate state correctly, call tools directly
            # This ensures we always get results even if ParallelAgent state extraction fails
            if not (ethereum_result or polygon_result or hedera_result):
                print("⚠️  ParallelAgent state not populated, falling back to direct tool calls")
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [
                        loop.run_in_executor(executor, get_ethereum_liquidity, token_a, token_b, fee),
                        loop.run_in_executor(executor, get_polygon_liquidity, token_a, token_b, fee),
                        loop.run_in_executor(executor, get_hedera_liquidity, token_a, token_b, fee),
                    ]
                    ethereum_result, polygon_result, hedera_result = await asyncio.gather(*futures)
            
            # Build response
            liquidity_data = build_liquidity_response(
                chain=chain,
                token_a=token_a,
                token_b=token_b,
                ethereum_result=ethereum_result,
                polygon_result=polygon_result,
                hedera_result=hedera_result,
            )
            
            response = validate_and_serialize_response(liquidity_data)
            log_response_info(token_a, token_b, chain, response)
            validate_json(response)
            return response
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"{ERROR_VALIDATION_FAILED}: {str(e)}"
            return build_error_response(chain, token_a, token_b, error_msg)
