"""Shared error classes for WriteIt application."""

from ...errors import WriteItError


class DomainError(WriteItError):
    """Base exception for domain-specific errors."""
    pass


class ApplicationError(WriteItError):
    """Base exception for application-level errors."""
    pass


class InfrastructureError(WriteItError):
    """Base exception for infrastructure-level errors."""
    pass


class RepositoryError(DomainError):
    """Errors related to repository operations."""
    pass


class QueryError(ApplicationError):
    """Errors related to query operations."""
    pass


class CommandError(ApplicationError):
    """Errors related to command operations."""
    pass


class NotFoundError(DomainError):
    """Raised when a requested resource is not found."""
    pass


class ConflictError(DomainError):
    """Raised when there's a conflict with existing data."""
    pass


class ValidationError(DomainError):
    """Errors related to validation operations."""
    pass


class SecurityError(InfrastructureError):
    """Errors related to security operations."""
    pass


class ConfigurationError(ApplicationError):
    """Errors related to configuration."""
    pass


class BaseApplicationError(ApplicationError):
    """Base application error for backward compatibility."""
    pass


__all__ = [
    "DomainError",
    "ApplicationError", 
    "InfrastructureError",
    "RepositoryError",
    "QueryError",
    "CommandError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "SecurityError",
    "ConfigurationError",
    "BaseApplicationError",
]