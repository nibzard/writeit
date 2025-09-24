"""Execution domain errors."""

from ...shared.errors import DomainError


class ExecutionError(DomainError):
    """Base exception for execution domain errors."""
    pass


class LLMProviderError(ExecutionError):
    """Raised when LLM provider operation fails."""
    
    def __init__(self, provider_name: str, reason: str = None):
        self.provider_name = provider_name
        self.reason = reason
        message = f"LLM provider '{provider_name}' operation failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class LLMConnectionError(LLMProviderError):
    """Raised when LLM provider connection fails."""
    
    def __init__(self, provider_name: str, status_code: int = None):
        self.status_code = status_code
        message = f"Failed to connect to LLM provider '{provider_name}'"
        if status_code:
            message += f" (status code: {status_code})"
        super().__init__(provider_name, message)


class LLMRateLimitError(LLMProviderError):
    """Raised when LLM provider rate limit is exceeded."""
    
    def __init__(self, provider_name: str, retry_after: int = None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded for LLM provider '{provider_name}'"
        if retry_after:
            message += f" (retry after {retry_after} seconds)"
        super().__init__(provider_name, message)


class LLMQuotaExceededError(LLMProviderError):
    """Raised when LLM provider quota is exceeded."""
    
    def __init__(self, provider_name: str, quota_type: str = None):
        self.quota_type = quota_type
        message = f"Quota exceeded for LLM provider '{provider_name}'"
        if quota_type:
            message += f" ({quota_type})"
        super().__init__(provider_name, message)


class LLMAuthenticationError(LLMProviderError):
    """Raised when LLM provider authentication fails."""
    
    def __init__(self, provider_name: str):
        super().__init__(provider_name, "Authentication failed")


class CacheError(ExecutionError):
    """Raised when cache operation fails."""
    pass


class CacheMissError(CacheError):
    """Raised when requested item is not found in cache."""
    
    def __init__(self, cache_key: str):
        self.cache_key = cache_key
        super().__init__(f"Cache miss for key '{cache_key}'")


class CacheCorruptionError(CacheError):
    """Raised when cache data is corrupted."""
    
    def __init__(self, cache_key: str, reason: str = None):
        self.cache_key = cache_key
        self.reason = reason
        message = f"Cache corruption detected for key '{cache_key}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class TokenUsageError(ExecutionError):
    """Raised when token usage tracking fails."""
    
    def __init__(self, operation: str, reason: str = None):
        self.operation = operation
        self.reason = reason
        message = f"Token usage error in operation '{operation}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ExecutionContextError(ExecutionError):
    """Raised when execution context is invalid."""
    
    def __init__(self, context_id: str, reason: str = None):
        self.context_id = context_id
        self.reason = reason
        message = f"Execution context '{context_id}' error"
        if reason:
            message += f": {reason}"
        super().__init__(message)


__all__ = [
    "ExecutionError",
    "LLMProviderError",
    "LLMConnectionError",
    "LLMRateLimitError", 
    "LLMQuotaExceededError",
    "LLMAuthenticationError",
    "CacheError",
    "CacheMissError",
    "CacheCorruptionError",
    "TokenUsageError",
    "ExecutionContextError",
]