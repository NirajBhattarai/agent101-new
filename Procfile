# Railway Procfile for backend services
# Each service should be deployed as a separate Railway service

# Orchestrator Agent (Main service)
orchestrator: cd backend && uv run -m agents.orchestrator.orchestrator

# Balance Agent
balance: cd backend && uv run -m agents.balance

# Liquidity Agent
liquidity: cd backend && uv run -m agents.multichain_liquidity

# Swap Agent
swap: cd backend && uv run -m agents.swap
