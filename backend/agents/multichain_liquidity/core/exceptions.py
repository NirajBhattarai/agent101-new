"""
Custom exceptions for Multi-Chain Liquidity Agent.
"""


class LiquidityAgentError(Exception):
    """Base exception for liquidity agent errors."""

    pass


class InvalidTokenAddressError(LiquidityAgentError):
    """Raised when token address is invalid."""

    pass


class ChainNotSupportedError(LiquidityAgentError):
    """Raised when chain is not supported."""

    pass


class LiquidityFetchError(LiquidityAgentError):
    """Raised when liquidity fetch fails."""

    pass


class ValidationError(LiquidityAgentError):
    """Raised when validation fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}
