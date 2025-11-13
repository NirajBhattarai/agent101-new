# Orchestrator Agent

A DeFi liquidity orchestrator agent that coordinates specialized agents to fetch and aggregate on-chain liquidity and balance information across multiple blockchain networks.

## Overview

The Orchestrator Agent acts as a central coordinator that:
- **Receives user requests** via AG-UI Protocol
- **Delegates tasks** to specialized agents (Balance, Liquidity, Bridge, Swap)
- **Aggregates results** from multiple agents
- **Provides unified responses** to users

## Architecture

The Orchestrator Agent follows a clean, modular architecture:

```
orchestrator/
├── __init__.py              # Package initialization
├── __main__.py              # Server entry point (FastAPI app)
├── agent.py                 # Agent definition
├── README.md                # This file
│
└── core/                    # Core domain logic
    ├── __init__.py
    ├── constants.py         # Configuration constants
    └── instruction.py       # LLM instruction prompt
```

## Architecture Layers

### 1. **Core Layer** (`core/`)
Contains fundamental building blocks:
- **`constants.py`**: Configuration values, defaults, model settings
- **`instruction.py`**: Comprehensive LLM instruction prompt describing all available agents and workflows

### 2. **Agent Layer** (`agent.py`)
Defines the orchestrator agent:
- **`build_orchestrator_agent()`**: Builds the LLM agent with instruction
- **`build_adk_orchestrator_agent()`**: Wraps agent for AG-UI Protocol

### 3. **Server Layer** (`__main__.py`)
FastAPI application:
- **`create_app()`**: Creates FastAPI app with agent endpoint
- **`main()`**: Server entry point

## Available Specialized Agents

The orchestrator coordinates these agents:

1. **Balance Agent** (A2A Protocol)
   - Fetches account balances from Polygon and Hedera
   - Supports single chain or all chains queries

2. **Multi-Chain Liquidity Agent** (A2A Protocol)
   - Fetches liquidity information from multiple chains (Ethereum, Polygon, Hedera)
   - Supports multiple chains and token pairs

3. **Bridge Agent** (A2A Protocol)
   - Handles token bridging between Hedera and Polygon
   - Provides bridge quotes and executes bridges

4. **Swap Agent** (A2A Protocol)
   - Handles token swaps on Hedera and Polygon
   - Aggregates swap options from multiple DEXes

5. **Swap Router Agent** (A2A Protocol)
   - Intelligent multi-chain swap routing optimizer for large swaps
   - Analyzes liquidity and optimizes routing across chains

6. **Pool Calculator Agent** (A2A Protocol)
   - Processes liquidity data and calculates optimal swap allocations

7. **Market Insights Agent** (A2A Protocol)
   - Fetches trending tokens across multiple networks

## Usage

### Running the Orchestrator

```bash
# From backend directory
cd backend/agents/orchestrator
uv run -m agents.orchestrator

# Or directly
python -m agents.orchestrator
```

Server starts at `http://0.0.0.0:9000/`

### Example Queries

- "Get my balance on Polygon"
- "Show me liquidity for HBAR/USDC"
- "Bridge 100 USDC from Hedera to Polygon"
- "Swap 0.1 HBAR to USDC on Hedera"

## Configuration

Set environment variables:

```bash
# API Keys
GOOGLE_API_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here

# Model Configuration
GEMINI_MODEL=gemini-2.5-pro  # Default

# Server Configuration
ORCHESTRATOR_PORT=9000  # Default
```

## Design Principles

### Clean Code Architecture
- **Separation of Concerns**: Agent definition separated from server setup
- **Constants Extraction**: Configuration moved to constants file
- **Modular Design**: Easy to extend with new agents
- **Consistent Structure**: Follows same pattern as other agents (uses `__main__.py`)

## Integration

The Orchestrator integrates with:
- **Frontend**: Receives requests via AG-UI Protocol
- **Specialized Agents**: Calls agents via A2A Protocol using `send_message_to_a2a_agent` tool
- **A2A Middleware**: Provides communication layer between orchestrator and agents

## License

Part of AgentFlow 101 - Hedera Hello Future: Ascension Hackathon 2025

