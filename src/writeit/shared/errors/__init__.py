"""Shared error classes for WriteIt application."""

from ...errors import WriteItError


class RepositoryError(WriteItError):
    """Errors related to repository operations."""
    pass


class QueryError(WriteItError):
    """Errors related to query operations."""
    pass


class CommandError(WriteItError):
    """Errors related to command operations."""
    pass


__all__ = [
    "RepositoryError",
    "QueryError", 
    "CommandError",
]