# Multi-Chain Liquidity Agent - Comprehensive Analysis

## Overview

The **Multi-Chain Liquidity Agent** (LiquidityFinder) is an A2A Protocol agent that retrieves liquidity pool information from multiple blockchain networks (Ethereum, Polygon, Hedera) using Google ADK with parallel execution capabilities.

**Port**: 9998  
**Protocol**: A2A Protocol  
**Model**: gemini-2.5-flash  
**Architecture**: Single orchestrator agent with direct tool calls

---

## Architecture

### Component Structure

```
multichain_liquidity/
├── __main__.py              # A2A server entry point with x402 middleware
├── executor.py              # A2A executor implementation
├── agents/
│   └── orchestrator.py     # Single LLM agent with tools
├── tools/                   # Blockchain liquidity tools
│   ├── ethereum.py         # Uniswap V3 liquidity queries
│   ├── polygon.py          # Uniswap V3 liquidity queries
│   ├── hedera.py           # SaucerSwap liquidity queries
│   └── token_resolver.py   # Token symbol → address resolution
├── core/
│   └── constants.py        # Configuration constants
└── services/
    └── executor_validator.py  # Response validation
```

### Architecture Pattern

**Single Orchestrator Agent Pattern** (unlike Balance Agent's SequentialAgent):
- One LLM agent (`LiquidityOrchestratorAgent`) handles the entire workflow
- Agent decides which chains to query based on user input
- Agent resolves token addresses if needed
- Agent calls liquidity tools directly (parallel execution)
- Agent returns structured JSON response

---

## Key Components

### 1. Server Entry Point (`__main__.py`)

**Responsibilities**:
- Creates A2A Starlette application
- Configures agent card with skills and capabilities
- Sets up x402 payment middleware (optional)
- Adds custom logging middleware
- Starts uvicorn server

**Key Features**:
- **x402 Payment Middleware**: Optional payment protection for `/api/*` endpoints
  - Configurable via environment variables
  - Currently hardcoded to enabled (lines 134-136) - should use env vars
  - Supports HBAR and HTS token payments
- **Custom Logging**: Request/response logging middleware
- **Agent Card**: Defines agent capabilities, skills, and examples

**Configuration**:
```python
# Port configuration
port = int(os.getenv("PORT", os.getenv("LIQUIDITY_PORT", 9998)))

# x402 Payment (currently hardcoded - needs env var fix)
pay_to_address = "0.0.123456"  # Should be: os.getenv("X402_PAY_TO_ADDRESS")
payment_price = "$0.01"         # Should be: os.getenv("X402_PAYMENT_PRICE", "$0.01")
payment_enabled = True          # Should be: os.getenv("X402_PAYMENT_ENABLED", "false").lower() == "true"
network = os.getenv("X402_NETWORK", "hedera-testnet")
```

**Issues Found**:
- Lines 134-136: x402 payment configuration is hardcoded instead of using environment variables
- Should read from `.env` file as documented in `X402_SETUP.md`

---

### 2. Executor (`executor.py`)

**Responsibilities**:
- Implements `AgentExecutor` interface for A2A Protocol
- Manages session lifecycle
- Executes orchestrator agent
- Captures and parses agent responses
- Validates and formats JSON responses
- Handles errors gracefully

**Execution Flow**:
1. Extract user query and session ID from context
2. Create/retrieve session using `InMemoryRunner`
3. Execute orchestrator agent with user query
4. Capture response from events and session state
5. Parse JSON response (handles markdown code blocks)
6. Validate response content
7. Enqueue response to event queue

**Response Parsing Strategy**:
- Checks session state for `liquidity_response` key
- Falls back to parsing last assistant message
- Removes markdown code blocks (` ```json `)
- Validates JSON structure
- Returns error response if parsing fails

**Key Methods**:
- `execute()`: Main execution method
- `cancel()`: Not supported (raises exception)
- `_get_session_id()`: Extracts session ID from context
- `_build_execution_error_response()`: Creates error JSON response

---

### 3. Orchestrator Agent (`agents/orchestrator.py`)

**Agent Definition**:
- **Name**: `LiquidityOrchestratorAgent`
- **Model**: `gemini-2.5-flash`
- **Type**: `LlmAgent` (Google ADK)
- **Output Key**: `liquidity_response` (stored in session state)

**Tools Available**:
1. `resolve_token_for_liquidity(token_symbol, chain)` - Token resolution
2. `get_ethereum_liquidity(token_a, token_b, fee)` - Ethereum Uniswap V3
3. `get_polygon_liquidity(token_a, token_b, fee)` - Polygon Uniswap V3
4. `get_hedera_liquidity(token_a, token_b, fee)` - Hedera SaucerSwap

**Workflow** (as instructed to the LLM):
1. **Parse Query**: Extract token pair, chain specification, token addresses
2. **Token Resolution**: Resolve symbols to addresses if needed
3. **Chain Selection**: Determine which chains to query (ethereum, polygon, hedera, or all)
4. **Call Liquidity Tools**: For each chain, try all fee tiers and select highest liquidity
5. **Return JSON**: Structured response with all results

**Fee Tiers**:
- **Ethereum/Polygon**: 500, 3000, 10000 basis points
- **Hedera**: 500, 1500, 3000, 10000 basis points

**Response Format**:
```json
{
  "type": "liquidity",
  "chain": "all" | "ethereum" | "polygon" | "hedera",
  "token_a": "0x...",
  "token_b": "0x...",
  "results": [
    {
      "chain": "ethereum",
      "network": "mainnet",
      "pool_address": "0x...",
      "token_a": "0x...",
      "token_b": "0x...",
      "fee": 3000,
      "liquidity": "1234567890",
      "tick": 12345,
      "sqrt_price_x96": "123456789012345678901234567890",
      "status": "success" | "pool_not_found" | "error",
      "error": "error message (if status is error)"
    }
  ]
}
```

---

### 4. Tools

#### Token Resolver (`tools/token_resolver.py`)

**Purpose**: Resolve token symbols to addresses across chains

**Function**: `resolve_token_for_liquidity(token_symbol: str, chain: str) -> dict`

**Returns**:
```python
{
    "symbol": "LINK",
    "address": "0x...",        # For ethereum/polygon
    "address_evm": "0x...",   # For hedera
    "address_hedera": "0.0.123456",  # For hedera (if available)
    "decimals": 18,
    "source": "constants" | "cache" | "token_research",
    "explorer_url": "https://...",
    "status": "success" | "not_found" | "error"
}
```

**Implementation**: Delegates to `swap.services.token_resolver.resolve_token_address()`

---

#### Ethereum Liquidity Tool (`tools/ethereum.py`)

**Purpose**: Query Uniswap V3 pools on Ethereum mainnet

**Function**: `get_ethereum_liquidity(token_a: str, token_b: str, fee: int = 3000) -> dict`

**RPC**: `ETHEREUM_MAINNET_RPC` (default: `https://eth.llamarpc.com`)

**Returns**:
```python
{
    "chain": "ethereum",
    "network": "mainnet",
    "pool_address": "0x...",
    "token_a": "0x...",
    "token_b": "0x...",
    "fee": 3000,
    "liquidity": "1234567890",
    "tick": 12345,
    "sqrt_price_x96": "123456789012345678901234567890",
    "status": "success" | "pool_not_found" | "error"
}
```

**Implementation**: Uses `packages.blockchain.ethereum.uniswap.pool.web3_client.UniswapWeb3Client`

---

#### Polygon Liquidity Tool (`tools/polygon.py`)

**Purpose**: Query Uniswap V3 pools on Polygon mainnet

**Function**: `get_polygon_liquidity(token_a: str, token_b: str, fee: int = 3000) -> dict`

**Similar to Ethereum tool**, uses Polygon-specific client

---

#### Hedera Liquidity Tool (`tools/hedera.py`)

**Purpose**: Query SaucerSwap pools on Hedera

**Function**: `get_hedera_liquidity(token_a: str, token_b: str, fee: int = 3000) -> dict`

**RPC**: `HEDERA_MAINNET_RPC` (default: `https://mainnet.hashio.io/api`)

**Special Handling**:
- Converts native HBAR (`0x0000...`) to wHBAR address for pool lookups
- Uses `HEDERA_TOKENS` constants to get wHBAR address
- Supports fee tiers: 500, 1500, 3000, 10000

**Implementation**: Uses `packages.blockchain.hedera.saucerswap.pool.web3_client.SaucerSwapWeb3Client`

---

## Communication Flow

### Request Flow

```
User Query (Frontend)
    ↓
Orchestrator Agent (Port 9000)
    ↓
A2A Protocol
    ↓
Multi-Chain Liquidity Agent (Port 9998)
    ↓
LiquidityExecutor.execute()
    ↓
LiquidityOrchestratorAgent (Google ADK)
    ↓
Tools (resolve_token, get_*_liquidity)
    ↓
Blockchain Packages (Uniswap/SaucerSwap clients)
    ↓
Blockchain Networks (Ethereum/Polygon/Hedera)
```

### Response Flow

```
Blockchain Networks
    ↓
Blockchain Packages
    ↓
Tools (return dict)
    ↓
LiquidityOrchestratorAgent (returns JSON)
    ↓
LiquidityExecutor (parses, validates)
    ↓
A2A Protocol
    ↓
Orchestrator Agent
    ↓
Frontend (displays in LiquidityCard)
```

---

## Features

### 1. Multi-Chain Support
- **Ethereum**: Uniswap V3 pools
- **Polygon**: Uniswap V3 pools
- **Hedera**: SaucerSwap pools

### 2. Token Resolution
- Automatic symbol → address resolution
- Supports popular tokens via constants
- Falls back to token research agent if needed

### 3. Fee Tier Support
- Tries multiple fee tiers per chain
- Selects pool with highest liquidity
- Returns actual fee tier found

### 4. Parallel Execution
- Agent can query multiple chains simultaneously
- Uses ADK's parallel execution capabilities

### 5. x402 Payment Integration
- Optional payment middleware
- Protects `/api/*` endpoints
- Supports HBAR and HTS tokens
- Uses Hedera facilitator for verification/settlement

### 6. Error Handling
- Graceful error responses
- Pool not found handling
- Token resolution failures
- JSON parsing errors

---

## Configuration

### Environment Variables

```bash
# Server
PORT=9998                    # Server port (Railway uses PORT)
LIQUIDITY_PORT=9998          # Fallback port

# Google API
GOOGLE_API_KEY=...           # Required for ADK
GEMINI_API_KEY=...           # Alternative to GOOGLE_API_KEY

# RPC Endpoints
ETHEREUM_MAINNET_RPC=https://eth.llamarpc.com
POLYGON_MAINNET_RPC=...
HEDERA_MAINNET_RPC=https://mainnet.hashio.io/api
HEDERA_TESTNET_RPC=...

# x402 Payment (optional)
X402_PAYMENT_ENABLED=true
X402_PAY_TO_ADDRESS=0.0.123456
X402_PAYMENT_PRICE=$0.01
X402_NETWORK=hedera-testnet
X402_FACILITATOR_URL=https://x402-hedera-production.up.railway.app

# External URL (for agent card)
RENDER_EXTERNAL_URL=https://your-agent-url.com
```

---

## Issues & Recommendations

### Critical Issues

1. **Hardcoded x402 Configuration** (Lines 134-136 in `__main__.py`)
   - **Problem**: Payment settings are hardcoded instead of using environment variables
   - **Impact**: Cannot configure payments without code changes
   - **Fix**: Use `os.getenv()` for all x402 settings

2. **Missing Error Handling in Tools**
   - Some tools may not handle all edge cases
   - Consider adding retry logic for RPC calls

### Recommendations

1. **Environment Variable Configuration**
   - Fix x402 payment configuration to use env vars
   - Add validation for required env vars on startup

2. **Response Caching**
   - Consider caching liquidity results for popular pairs
   - Reduce RPC calls and improve response time

3. **Rate Limiting**
   - Add rate limiting for x402-protected endpoints
   - Prevent abuse of free endpoints

4. **Monitoring & Logging**
   - Add structured logging (JSON format)
   - Track metrics: request count, response times, error rates

5. **Testing**
   - Add unit tests for tools
   - Add integration tests for executor
   - Test x402 payment flow

6. **Documentation**
   - Add API documentation
   - Document response formats
   - Add examples for each chain

---

## Comparison with Balance Agent

| Feature | Balance Agent | Liquidity Agent |
|---------|--------------|-----------------|
| **Architecture** | SequentialAgent (2 sub-agents) | Single orchestrator agent |
| **Token Resolution** | Separate token extraction agent | Built into orchestrator |
| **Chain Queries** | Sequential | Parallel (via ADK) |
| **Response Format** | Structured balance data | Structured liquidity data |
| **Complexity** | Higher (multi-agent) | Lower (single agent) |

---

## Usage Examples

### Example 1: Single Chain Query
```
Query: "Get liquidity for LINK/USDT on ethereum"
→ Resolves LINK and USDT on ethereum
→ Calls get_ethereum_liquidity with all fee tiers
→ Returns best pool (highest liquidity)
```

### Example 2: Multi-Chain Query
```
Query: "Get liquidity for HBAR/USDC"
→ Resolves HBAR and USDC on all chains
→ Calls liquidity tools for ethereum, polygon, hedera
→ Returns results for all chains
```

### Example 3: Token Address Query
```
Query: "Get liquidity for 0x5149... 0xdAC1... on polygon"
→ No resolution needed (already addresses)
→ Calls get_polygon_liquidity with all fee tiers
→ Returns best pool
```

---

## Dependencies

### Core Dependencies
- `a2a-sdk>=0.3.10` - A2A Protocol
- `a2a-server>=0.6.1` - A2A server
- `google-adk>=1.17.0` - Google ADK
- `hiero-sdk-python>=0.1.7` - Hedera SDK
- `web3>=6.15.0` - Ethereum/Polygon Web3

### Blockchain Packages
- `packages.blockchain.ethereum.uniswap` - Ethereum Uniswap V3
- `packages.blockchain.polygon.uniswap` - Polygon Uniswap V3
- `packages.blockchain.hedera.saucerswap` - Hedera SaucerSwap

### x402 Payment
- `x402-hedera-python` - x402 payment protocol (local package)

---

## Testing

### Manual Testing

1. **Start the agent**:
   ```bash
   cd backend
   uv run -m agents.multichain_liquidity
   ```

2. **Test via A2A Protocol**:
   ```bash
   curl -X POST http://localhost:9998/api/task \
     -H "Content-Type: application/json" \
     -d '{
       "input": "Get liquidity for LINK/USDT on ethereum"
     }'
   ```

3. **Test via Orchestrator**:
   - Use frontend chat interface
   - Query: "Get liquidity for HBAR/USDC"

### Test Cases

- ✅ Single chain query (ethereum)
- ✅ Single chain query (polygon)
- ✅ Single chain query (hedera)
- ✅ Multi-chain query (all)
- ✅ Token symbol resolution
- ✅ Token address (no resolution)
- ✅ Pool not found handling
- ✅ Error handling
- ✅ x402 payment flow (if enabled)

---

## Performance Considerations

1. **RPC Calls**: Each liquidity query makes multiple RPC calls (one per fee tier per chain)
2. **Parallel Execution**: ADK enables parallel chain queries
3. **Response Time**: Depends on RPC latency (typically 1-3 seconds)
4. **Caching**: No caching currently - consider adding for popular pairs

---

## Security Considerations

1. **x402 Payment**: Protects API endpoints from abuse
2. **Input Validation**: Token addresses validated by tools
3. **Error Messages**: Should not leak sensitive information
4. **Rate Limiting**: Consider adding for production

---

## Future Enhancements

1. **Response Caching**: Cache popular token pairs
2. **Historical Data**: Track liquidity over time
3. **Price Impact Calculation**: Calculate price impact for swaps
4. **More DEXes**: Support additional DEXes (SushiSwap, etc.)
5. **Testnet Support**: Add testnet network support
6. **WebSocket Updates**: Real-time liquidity updates

---

## Conclusion

The Multi-Chain Liquidity Agent is a well-structured A2A Protocol agent that provides comprehensive liquidity information across Ethereum, Polygon, and Hedera networks. It uses a single orchestrator agent pattern with direct tool calls, enabling efficient parallel execution.

**Key Strengths**:
- Clean architecture with clear separation of concerns
- Multi-chain support with automatic token resolution
- Flexible fee tier handling
- Optional x402 payment integration

**Areas for Improvement**:
- Fix hardcoded x402 configuration
- Add response caching
- Improve error handling and retry logic
- Add comprehensive testing

