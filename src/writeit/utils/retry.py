# ABOUTME: Retry utilities for WriteIt API calls and operations
# ABOUTME: Provides exponential backoff and configurable retry strategies

import asyncio
import time
import random
from typing import Callable, Any, Optional, Type, Union, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    
    def __init__(self, last_exception: Exception, attempts: int):
        self.last_exception = last_exception
        self.attempts = attempts
        super().__init__(f"Failed after {attempts} attempts. Last error: {last_exception}")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay (exponential backoff)
        jitter: Add random jitter to delay to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry on
        on_retry: Optional callback function called on each retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts")
                        raise RetryError(e, max_attempts)
                    
                    # Calculate delay with jitter
                    actual_delay = current_delay
                    if jitter:
                        actual_delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1} of {max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {actual_delay:.2f}s"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(actual_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """Async retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay (exponential backoff)
        jitter: Add random jitter to delay to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry on
        on_retry: Optional callback function called on each retry
        
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(f"Async function {func.__name__} failed after {max_attempts} attempts")
                        raise RetryError(e, max_attempts)
                    
                    # Calculate delay with jitter
                    actual_delay = current_delay
                    if jitter:
                        actual_delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1} of {max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {actual_delay:.2f}s"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(actual_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator


class RetryConfig:
    """Configuration for retry operations."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return delay


# Common retry configurations
LLM_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True
)

FILE_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=0.1,
    max_delay=2.0,
    backoff_factor=1.5,
    jitter=True
)

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=0.5,
    max_delay=10.0,
    backoff_factor=2.0,
    jitter=True
)