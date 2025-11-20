# Agent101 - Multi-Agent DeFi Platform

A comprehensive DeFi platform powered by a multi-agent system that enables users to interact with multiple blockchain networks (Ethereum, Polygon, Hedera) through natural language conversations.

## 🏗️ Architecture Overview

Agent101 follows a **multi-agent orchestration architecture** with a clear separation between frontend, backend agents, and shared blockchain packages.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CopilotKit UI + Wallet Integration (Reown AppKit)       │  │
│  │  - Chat Interface                                        │  │
│  │  - Swap, Balance, Liquidity, Bridge Features            │  │
│  │  - Payment Facilitator (x402 Hedera)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ AG-UI Protocol
                             │ (HTTP/JSON-RPC)
┌────────────────────────────▼────────────────────────────────────┐
│              Orchestrator Agent (Port 9000)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Google ADK + AG-UI Protocol Adapter                      │  │
│  │  - Receives user queries                                  │  │
│  │  - Coordinates specialized agents                        │  │
│  │  - Aggregates responses                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬───────────┬───────────┬───────────┬───────────────┘
            │           │           │           │
            │ A2A       │ A2A       │ A2A       │ A2A
            │ Protocol  │ Protocol  │ Protocol  │ Protocol
    ┌───────▼───┐ ┌─────▼────┐ ┌───▼────┐ ┌───▼──────┐
    │  Balance  │ │Liquidity │ │  Swap  │ │Sentiment│
    │  Agent    │ │  Agent   │ │ Agent  │ │ Agent   │
    │  (9997)   │ │  (9998)  │ │ (9999) │ │(10000)  │
    └───────┬───┘ └─────┬────┘ └───┬────┘ └───┬──────┘
            │           │           │           │
            └───────────┴───────────┴───────────┘
                           │
                           │ Direct Tool Calls
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              Blockchain Packages (Shared)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Ethereum    │  │   Polygon    │  │    Hedera    │         │
│  │  - Uniswap   │  │   - Uniswap  │  │  - SaucerSwap│         │
│  │  - Balance   │  │   - Balance  │  │  - Balance   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **Frontend** (`frontend/`)
- **Framework**: Next.js 16 with React 19
- **UI**: CopilotKit for conversational interface
- **Wallet**: Reown AppKit (formerly WalletConnect) for multi-chain wallet connectivity
- **State Management**: Redux Toolkit + TanStack Query
- **Features**: Chat, Swap, Balance, Liquidity, Bridge, Payment Facilitator

#### 2. **Backend Agents** (`backend/agents/`)
- **Orchestrator Agent** (Port 9000): Central coordinator using Google ADK + AG-UI Protocol
  - Routes queries to specialized agents via A2A Protocol
  - Aggregates responses from multiple agents
  - Handles agent coordination and workflow management

- **Specialized Agents**: Each agent handles a specific domain
  - **Balance Agent** (Port 9997): Multi-chain balance queries
    - Uses SequentialAgent with token extraction and balance extraction sub-agents
    - Supports Hedera, Ethereum, and Polygon
    - Returns structured balance data with USD valuations
  
  - **LiquidityFinder** (Port 9998): Multi-chain liquidity analysis
    - Single orchestrator agent that handles token resolution internally
    - Queries Uniswap V3 pools (Ethereum/Polygon) and SaucerSwap pools (Hedera)
    - Supports multiple fee tiers (500, 3000, 10000 basis points)
    - Returns comprehensive liquidity data including pool addresses, TVL, and tick information
  
  - **Swap Agent** (Port 9999): Token swap execution
    - Intelligent swap routing across multiple DEXes
    - Automatic rate comparison and slippage protection
    - Supports native tokens and ERC-20 tokens
  
  - **Sentiment Agent** (Port 10000): Cryptocurrency sentiment analysis
    - Powered by Santiment API
    - Tracks social volume, trending topics, and community sentiment
  
  - **Trading Agent** (Port 10001): ML-powered trading recommendations
    - AI-powered trading signals for BTC and ETH
    - Machine learning predictions and technical indicators
    - Risk-adjusted recommendations
  
  - **Token Research Agent**: Comprehensive token discovery
    - Finds contract addresses across multiple chains
    - Verifies token metadata
    - Explores cross-chain availability

#### 3. **Blockchain Packages** (`backend/packages/blockchain/`)
- **Shared Libraries**: Reusable blockchain integration code
- **Supported Chains**: Ethereum, Polygon, Hedera
- **DEX Integrations**: Uniswap V3 (Ethereum/Polygon), SaucerSwap (Hedera)

### Communication Protocols

1. **AG-UI Protocol**: Frontend ↔ Orchestrator
   - JSON-RPC over HTTP
   - Enables natural language conversations

2. **A2A Protocol**: Orchestrator ↔ Specialized Agents
   - Agent-to-Agent communication
   - Enables agent coordination and delegation

3. **Direct Tool Calls**: Agents ↔ Blockchain Packages
   - Direct function calls to blockchain clients
   - No protocol overhead for internal operations

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **uv** (Python package manager, recommended)
- **Google API Key** (for Gemini models)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd agent101-new
```

2. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

3. **Install Backend Dependencies**
```bash
cd backend
# Using uv (recommended):
uv venv
uv sync --extra dev
# Or using Makefile:
make backend-install
```

### Environment Setup

**Frontend** (`.env.local`):
```bash
# Required: Get your project ID from https://cloud.reown.com
NEXT_PUBLIC_REOWN_PROJECT_ID=your_project_id

# Optional: For payment facilitator functionality
HEDERA_FACILITATOR_ACCOUNT_ID=0.0.xxxxx
HEDERA_FACILITATOR_PRIVATE_KEY=your_private_key

# Optional: Agent URLs (defaults shown)
ORCHESTRATOR_URL=http://localhost:9000
BALANCE_AGENT_URL=http://localhost:9997
SWAP_AGENT_URL=http://localhost:9999
MULTICHAIN_LIQUIDITY_AGENT_URL=http://localhost:9998
SENTIMENT_AGENT_URL=http://localhost:10000
TRADING_AGENT_URL=http://localhost:10001
TOKEN_RESEARCH_AGENT_URL=http://localhost:10002
```

**Backend** (`.env`):
```bash
# Required: Get your API key from https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key
# OR use GEMINI_API_KEY (alternative)
# GEMINI_API_KEY=your_gemini_api_key

# Optional: Model configuration
GEMINI_MODEL=gemini-2.5-pro

# Optional: Agent ports (defaults shown)
ORCHESTRATOR_PORT=9000
BALANCE_AGENT_PORT=9997
LIQUIDITY_AGENT_PORT=9998
SWAP_AGENT_PORT=9999
SENTIMENT_AGENT_PORT=10000
TRADING_AGENT_PORT=10001
TOKEN_RESEARCH_AGENT_PORT=10002
```

> **Note**: Copy `.env.example` files (if available) or create `.env.local` (frontend) and `.env` (backend) files with the above variables.

### Running the Application

**Option 1: Using Makefile (Recommended)**
```bash
# Start all agents
make agents-start

# In another terminal, start frontend
make frontend-dev
```

**Option 2: Manual Start**

1. **Start Backend Agents**:
```bash
# Terminal 1: Orchestrator
cd backend && uv run -m agents.orchestrator

# Terminal 2-7: Specialized Agents
cd backend && uv run -m agents.balance
cd backend && uv run -m agents.multichain_liquidity
cd backend && uv run -m agents.swap
cd backend && uv run -m agents.sentiment
cd backend && uv run -m agents.trading
cd backend && uv run -m agents.token_research
```

2. **Start Frontend**:
```bash
cd frontend
npm run dev
```

## 📁 Project Structure

```
agent101-new/
├── frontend/                          # Next.js frontend application
│   ├── app/                           # Next.js app router
│   │   ├── api/                       # API routes
│   │   │   ├── copilotkit/            # CopilotKit integration
│   │   │   ├── facilitator/          # Payment facilitator (x402 Hedera)
│   │   │   └── orchestrator/          # Orchestrator proxy
│   │   ├── chat/                      # Chat interface page
│   │   ├── swap/                      # Swap feature page
│   │   ├── payment/                   # Payment facilitator page
│   │   ├── layout.tsx                 # Root layout
│   │   └── page.tsx                   # Landing page
│   ├── components/                    # React components
│   │   ├── chat/                      # Chat UI components
│   │   │   ├── a2a/                   # A2A protocol visualizers
│   │   │   └── DeFiChat.tsx           # Main chat component
│   │   ├── features/                  # Feature-specific components
│   │   │   ├── balance/                # Balance display card
│   │   │   ├── bridge/                 # Bridge transaction card
│   │   │   ├── liquidity/              # Liquidity pool card
│   │   │   ├── market_insights/        # Market insights card
│   │   │   ├── pool_calculator/         # Pool calculator card
│   │   │   ├── swap/                   # Swap transaction card
│   │   │   │   └── components/         # Swap sub-components
│   │   │   ├── swap_router/            # Swap router card
│   │   │   └── token-research/         # Token research card
│   │   ├── forms/                      # Form components
│   │   │   ├── balance/                # Balance query form
│   │   │   ├── bridge/                 # Bridge transaction form
│   │   │   ├── liquidity/              # Liquidity query form
│   │   │   ├── payment/                # Payment facilitator form
│   │   │   ├── shared/                 # Shared form utilities
│   │   │   └── swap/                   # Swap requirements form
│   │   └── shared/                     # Shared components
│   │       ├── Logo.tsx                # Logo component
│   │       └── WalletConnect.tsx       # Wallet connection
│   ├── lib/                            # Library code
│   │   ├── config/                     # App configuration
│   │   ├── constants/                  # App constants (chains, tokens, DEXes)
│   │   ├── features/                   # Feature implementations
│   │   │   ├── bridge/                 # Bridge logic
│   │   │   └── swap/                   # Swap logic
│   │   ├── shared/                     # Shared utilities
│   │   │   ├── blockchain/             # Blockchain utilities
│   │   │   ├── contracts/              # Contract ABIs
│   │   │   └── crypto/                 # Crypto utilities
│   │   └── store/                      # Redux store
│   │       └── slices/                 # Redux slices
│   ├── types/                          # TypeScript type definitions
│   ├── utils/                          # Utility functions
│   │   └── liquidityTransformer.ts     # Liquidity data transformer
│   └── scripts/                        # Utility scripts
│
├── backend/                            # Python backend
│   ├── agents/                         # Agent implementations
│   │   ├── orchestrator/              # Orchestrator agent (Port 9000)
│   │   │   ├── agent.py                # Main orchestrator agent
│   │   │   └── core/                   # Core orchestrator logic
│   │   │       ├── instruction.py      # Agent instructions
│   │   │       └── logger.py           # Logging utilities
│   │   ├── balance/                    # Balance agent (Port 9997)
│   │   │   ├── agent.py                # Sequential agent definition
│   │   │   ├── balance_extractor_agent.py  # Balance extraction agent
│   │   │   ├── token_extractor_agent.py    # Token extraction agent
│   │   │   ├── executor.py             # A2A executor
│   │   │   ├── core/                   # Core balance logic
│   │   │   │   ├── constants.py       # Balance constants
│   │   │   │   ├── models/            # Pydantic models
│   │   │   │   └── response_validator.py
│   │   │   ├── services/               # Service layer
│   │   │   │   ├── response_builder.py
│   │   │   │   └── token_filter.py
│   │   │   └── tools/                  # Balance tools
│   │   │       ├── hedera.py           # Hedera balance tool
│   │   │       ├── ethereum.py         # Ethereum balance tool
│   │   │       ├── polygon.py          # Polygon balance tool
│   │   │       └── all_chains.py       # Multi-chain balance tool
│   │   ├── multichain_liquidity/       # LiquidityFinder agent (Port 9998)
│   │   │   ├── agents/                 # Agent definitions
│   │   │   │   └── orchestrator.py     # Single orchestrator agent
│   │   │   ├── executor.py             # A2A executor
│   │   │   ├── core/                   # Core liquidity logic
│   │   │   │   └── constants.py
│   │   │   ├── services/               # Service layer
│   │   │   └── tools/                  # Liquidity tools
│   │   │       ├── hedera.py           # Hedera liquidity tool
│   │   │       ├── ethereum.py         # Ethereum liquidity tool
│   │   │       ├── polygon.py          # Polygon liquidity tool
│   │   │       └── token_resolver.py   # Token resolution tool
│   │   ├── swap/                       # Swap agent (Port 9999)
│   │   │   ├── agent.py                # Swap agent definition
│   │   │   ├── executor.py             # A2A executor
│   │   │   ├── core/                   # Core swap logic
│   │   │   │   ├── constants.py
│   │   │   │   ├── models/             # Swap models
│   │   │   │   └── response_validator.py
│   │   │   ├── services/               # Service layer
│   │   │   │   ├── query_parser.py
│   │   │   │   ├── response_builder.py
│   │   │   │   ├── token_resolver.py
│   │   │   │   └── explorer_utils.py
│   │   │   └── tools/                  # Swap tools
│   │   │       ├── hedera.py           # Hedera swap tool
│   │   │       ├── ethereum.py         # Ethereum swap tool
│   │   │       └── polygon.py          # Polygon swap tool
│   │   ├── sentiment/                  # Sentiment agent (Port 10000)
│   │   │   ├── agent.py                # Sentiment agent definition
│   │   │   ├── executor.py             # A2A executor
│   │   │   ├── core/                   # Core sentiment logic
│   │   │   ├── services/               # Service layer
│   │   │   └── tools/                  # Sentiment tools
│   │   │       └── santiment.py        # Santiment API integration
│   │   ├── trading/                    # Trading agent (Port 10001)
│   │   │   ├── agent.py                # Trading agent definition
│   │   │   ├── executor.py             # A2A executor
│   │   │   ├── core/                   # Core trading logic
│   │   │   ├── services/               # Service layer
│   │   │   └── tools/                  # Trading tools
│   │   │       ├── price_data.py       # Price data fetching
│   │   │       ├── technical_analysis.py
│   │   │       ├── ml_predictor.py     # ML predictions
│   │   │       └── trading_strategy.py
│   │   └── token_research/             # Token Research agent
│   │       ├── agent.py                # ADK agent definition
│   │       ├── agent_langgraph.py      # LangGraph agent (alternative)
│   │       ├── executor.py             # A2A executor
│   │       ├── core/                   # Core token research logic
│   │       │   ├── models/             # Token research models
│   │       │   └── response_validator.py
│   │       ├── services/               # Service layer
│   │       └── tools/                  # Token research tools
│   │           ├── token_search.py     # Token search
│   │           ├── token_fetcher.py    # Token data fetching
│   │           └── token_discovery.py  # Token discovery
│   └── packages/                       # Shared packages
│       └── blockchain/                 # Blockchain integrations
│           ├── dex/                    # DEX abstractions
│           │   ├── abis/                # Contract ABIs
│           │   ├── base/                # Base DEX classes
│           │   └── utils/              # DEX utilities
│           ├── ethereum/                # Ethereum integration
│           │   ├── balance/            # Balance client
│           │   ├── uniswap/            # Uniswap V3 integration
│           │   │   ├── pool/           # Pool operations
│           │   │   └── factory.py      # Pool factory
│           │   └── constants.py
│           ├── polygon/                # Polygon integration
│           │   ├── balance/            # Balance client
│           │   ├── uniswap/            # Uniswap V3 integration
│           │   └── constants.py
│           ├── hedera/                 # Hedera integration
│           │   ├── balance/            # Balance client
│           │   ├── saucerswap/         # SaucerSwap integration
│           │   │   ├── pool/           # Pool operations
│           │   │   └── factory.py      # Pool factory
│           │   ├── client.py           # Hedera client
│           │   ├── transactions.py    # Transaction utilities
│           │   └── constants.py
│           ├── token_discovery.py      # Token discovery utilities
│           └── token_updater.py       # Token metadata updater
│
└── Makefile                            # Development commands
```

## 🔄 Agent Workflow

### Example: Token Swap Workflow

1. **User Query**: "Swap 0.1 HBAR to USDC on Hedera"
2. **Orchestrator** receives query via AG-UI Protocol
3. **Orchestrator** calls **Balance Agent** (A2A) to check user balance
4. **Orchestrator** calls **Liquidity Agent** (A2A) to find pools
5. **Orchestrator** calls **Swap Agent** (A2A) to execute swap
6. **Orchestrator** aggregates results and responds to frontend

### Agent Communication Flow

```
User → Frontend → Orchestrator → Balance Agent → Blockchain Package
                              → Liquidity Agent → Blockchain Package
                              → Swap Agent → Blockchain Package
                              → Response → Frontend → User
```

## 🛠️ Development

### Code Quality

**Backend**:
```bash
make backend-format      # Format code
make backend-lint        # Lint code
make backend-type-check  # Type checking
make backend-test        # Run tests
```

**Frontend**:
```bash
make frontend-format     # Format code
npm run lint            # Lint code
```

### Testing

**Backend Tests**:
```bash
make backend-test                    # All tests
make backend-test-saucerswap         # Hedera tests
make backend-test-uniswap            # Uniswap tests
make backend-test-coverage           # With coverage
```

## 📚 Documentation

- [Backend README](./backend/README.md) - Backend architecture and agent details
- [Frontend README](./frontend/README.md) - Frontend architecture and features
- [Orchestrator README](./backend/agents/orchestrator/README.md) - Orchestrator agent details
- [Contributing Guide](./CONTRIBUTING.md) - Guidelines for contributing to the project

## 🔌 API Endpoints

### Orchestrator Agent
- **URL**: `http://localhost:9000/`
- **Protocol**: AG-UI Protocol (JSON-RPC)

### Specialized Agents (A2A Protocol)
- **Balance Agent**: `http://localhost:9997/`
- **LiquidityFinder**: `http://localhost:9998/`
- **Swap Agent**: `http://localhost:9999/`
- **Sentiment Agent**: `http://localhost:10000/`
- **Trading Agent**: `http://localhost:10001/`
- **Token Research Agent**: `http://localhost:10002/`

### Frontend API Routes
- **CopilotKit Route**: `/api/copilotkit` - Main chat interface (connects to orchestrator)
- **Payment Facilitator**: `/api/facilitator/*` - Payment verification and settlement

> **Note**: The orchestrator API route (`/api/orchestrator`) is mentioned in some documentation but is not currently implemented. The frontend uses `/api/copilotkit` which directly connects to the orchestrator via AG-UI Protocol.

## 🌐 Supported Blockchains

- **Ethereum**: Uniswap V3, ERC-20 tokens
- **Polygon**: Uniswap V3, ERC-20 tokens
- **Hedera**: SaucerSwap, HTS tokens, HBAR

## ⚠️ Implementation Notes

### Agent Architecture
The platform uses a multi-agent architecture with the following implementations:

**Implemented as Separate Agents** (A2A Protocol):
- Balance Agent (Port 9997)
- Multi-Chain Liquidity Agent (Port 9998)
- Swap Agent (Port 9999)
- Sentiment Agent (Port 10000)
- Trading Agent (Port 10001)
- Token Research Agent (Port 10002)

**Handled by Orchestrator** (not separate agents):
- Bridge functionality - Frontend components exist, but bridge logic is handled by the orchestrator
- Swap Router - Frontend components exist, but routing logic is handled by the orchestrator
- Pool Calculator - Frontend components exist, but calculations are handled client-side or by orchestrator
- Market Insights - Frontend components exist, but insights are provided by orchestrator/sentiment agent

> **Note**: Some features (Bridge, Swap Router, Pool Calculator, Market Insights) have frontend UI components but are implemented as orchestrator capabilities rather than separate A2A agents. This is by design for simpler architecture.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for detailed guidelines.

Quick checklist:
1. Follow the existing code structure
2. Maintain separation of concerns (agents, packages, frontend)
3. Write tests for new features
4. Update documentation


## 📝 License

MIT License

## 🙏 Acknowledgments

Built for **Hedera Hello Future: Ascension Hackathon 2025**

