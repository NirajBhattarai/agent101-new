# Contributing to Agent101

Thank you for your interest in contributing to Agent101! This document provides guidelines and instructions for contributing to the project.

## 🏗️ Project Structure

Agent101 is a multi-agent DeFi platform with the following structure:

- **Frontend** (`frontend/`): Next.js application with CopilotKit UI
- **Backend** (`backend/`): Python-based multi-agent system
  - **Agents** (`backend/agents/`): Specialized agents for different DeFi operations
  - **Packages** (`backend/packages/`): Shared blockchain integration code

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **uv** (Python package manager, recommended)
- **Google API Key** (for Gemini models)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent101-new
   ```

2. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local  # Create .env.local from example
   # Edit .env.local with your configuration
   ```

3. **Set up Backend**
   ```bash
   cd backend
   uv venv
   uv sync --extra dev
   cp .env.example .env  # Create .env from example
   # Edit .env with your configuration
   ```

## 📝 Development Workflow

### Code Style

**Backend (Python)**:
- Use **Ruff** for formatting and linting
- Follow **PEP 8** style guidelines
- Run `make backend-format` before committing
- Run `make backend-lint` to check for issues

**Frontend (TypeScript/React)**:
- Use **Prettier** for formatting
- Follow **ESLint** rules
- Run `npm run format` before committing
- Run `npm run lint` to check for issues

### Running Tests

**Backend**:
```bash
make backend-test              # Run all tests
make backend-test-coverage     # Run with coverage
make backend-test-saucerswap   # Run Hedera tests
make backend-test-uniswap     # Run Uniswap tests
```

**Frontend**:
- Tests should be added as needed (currently minimal test coverage)

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code structure
   - Maintain separation of concerns (agents, packages, frontend)
   - Write clear, documented code

3. **Test your changes**
   - Run relevant tests
   - Test manually if needed
   - Ensure all agents can start successfully

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: description of your change"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `test:` for tests
   - `chore:` for maintenance

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🏗️ Architecture Guidelines

### Adding a New Agent

1. **Create agent directory structure**:
   ```
   backend/agents/your_agent/
   ├── __init__.py
   ├── __main__.py        # A2A server entry point
   ├── agent.py           # Agent logic
   ├── executor.py        # A2A executor
   ├── core/
   │   ├── constants.py
   │   └── ...
   ├── services/          # Business logic
   └── tools/             # Blockchain tools
   ```

2. **Implement the agent**:
   - Follow the pattern of existing agents (see `balance/` or `swap/` as examples)
   - Use A2A Protocol for agent-to-agent communication
   - Implement proper error handling

3. **Register in orchestrator**:
   - Add agent URL to `frontend/app/api/copilotkit/route.ts`
   - Update orchestrator instructions in `backend/agents/orchestrator/core/instruction.py`

4. **Update documentation**:
   - Add agent to main `README.md`
   - Update `backend/README.md`
   - Add to `Makefile` if needed

### Adding a New Blockchain Integration

1. **Create blockchain package**:
   ```
   backend/packages/blockchain/your_chain/
   ├── balance/
   ├── dex/
   └── constants.py
   ```

2. **Follow existing patterns**:
   - Look at `ethereum/`, `polygon/`, or `hedera/` as examples
   - Implement balance queries
   - Implement DEX integration if applicable

3. **Add to agents**:
   - Update relevant agents to support the new chain
   - Add chain constants
   - Update frontend constants

## 🐛 Reporting Issues

When reporting issues, please include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: 
  - OS and version
  - Node.js version
  - Python version
  - Relevant environment variables (without sensitive values)

## 💡 Feature Requests

For feature requests:

- Describe the feature clearly
- Explain the use case
- Consider if it fits the project's scope
- Be open to discussion and alternative approaches

## 📚 Documentation

When adding features:

- Update relevant README files
- Add code comments for complex logic
- Update API documentation if applicable
- Keep examples up to date

## ✅ Code Review Process

1. All PRs require review
2. Address review comments promptly
3. Ensure tests pass
4. Ensure code is formatted and linted
5. Update documentation as needed

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what's best for the project

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Thank you for contributing to Agent101! Your contributions help make DeFi more accessible through AI-powered agents.

