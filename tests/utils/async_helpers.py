"""Async testing helper utilities.

Provides utilities for testing async operations, timeouts, waiting for conditions,
and managing async context in tests.
"""

import asyncio
import functools
import time
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, TypeVar, AsyncGenerator, List, Optional
import pytest

T = TypeVar('T')


def async_test_timeout(seconds: float = 30.0):
    """Decorator to add timeout to async test functions.
    
    Args:
        seconds: Timeout in seconds (default: 30.0)
    
    Usage:
        @async_test_timeout(10.0)
        async def test_something():
            await some_long_operation()
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator


async def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    poll_interval: float = 0.1,
    error_message: str = "Condition not met within timeout"
) -> None:
    """Wait for a condition to become true.
    
    Args:
        condition: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        poll_interval: How often to check condition in seconds
        error_message: Error message if timeout is reached
    
    Raises:
        asyncio.TimeoutError: If condition is not met within timeout
    
    Usage:
        await wait_for_condition(
            lambda: len(event_handler.received_events) > 0,
            timeout=2.0
        )
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return
        await asyncio.sleep(poll_interval)
    
    raise asyncio.TimeoutError(error_message)


async def wait_for_condition_async(
    condition: Callable[[], Awaitable[bool]],
    timeout: float = 5.0, 
    poll_interval: float = 0.1,
    error_message: str = "Async condition not met within timeout"
) -> None:
    """Wait for an async condition to become true.
    
    Args:
        condition: Async function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        poll_interval: How often to check condition in seconds
        error_message: Error message if timeout is reached
    
    Raises:
        asyncio.TimeoutError: If condition is not met within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if await condition():
            return
        await asyncio.sleep(poll_interval)
    
    raise asyncio.TimeoutError(error_message)


async def collect_async_generator(
    async_gen: AsyncGenerator[T, None],
    max_items: int = 100,
    timeout: float = 5.0
) -> List[T]:
    """Collect items from an async generator with timeout protection.
    
    Args:
        async_gen: The async generator to collect from
        max_items: Maximum number of items to collect
        timeout: Total timeout for collection
    
    Returns:
        List of collected items
    
    Usage:
        async def data_stream():
            for i in range(5):
                yield f"item-{i}"
                await asyncio.sleep(0.1)
        
        items = await collect_async_generator(data_stream())
        assert len(items) == 5
    """
    items = []
    
    try:
        async with asyncio.timeout(timeout):
            async for item in async_gen:
                items.append(item)
                if len(items) >= max_items:
                    break
    except asyncio.TimeoutError:
        # Return what we collected before timeout
        pass
    
    return items


class AsyncContextManager:
    """Helper for testing async context managers.
    
    Provides utilities for testing that async context managers
    properly enter, exit, and handle exceptions.
    """
    
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.entered = False
        self.exited = False
        self.exception_handled = False
        self.enter_result = None
        self.exit_result = None
    
    async def __aenter__(self):
        self.entered = True
        self.enter_result = await self.context_manager.__aenter__()
        return self.enter_result
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        if exc_type is not None:
            self.exception_handled = True
        self.exit_result = await self.context_manager.__aexit__(exc_type, exc_val, exc_tb)
        return self.exit_result


@asynccontextmanager
async def async_timeout_context(timeout: float = 5.0):
    """Async context manager that enforces a timeout.
    
    Args:
        timeout: Timeout in seconds
    
    Usage:
        async with async_timeout_context(2.0):
            await some_operation()  # Will timeout after 2 seconds
    """
    try:
        async with asyncio.timeout(timeout):
            yield
    except asyncio.TimeoutError:
        pytest.fail(f"Operation exceeded timeout of {timeout} seconds")


async def run_with_timeout(coro: Awaitable[T], timeout: float = 30.0) -> T:
    """Run a coroutine with timeout protection.
    
    Args:
        coro: The coroutine to run
        timeout: Timeout in seconds
    
    Returns:
        Result of the coroutine
    
    Raises:
        asyncio.TimeoutError: If operation times out
    """
    return await asyncio.wait_for(coro, timeout=timeout)


class AsyncTaskTracker:
    """Track and manage async tasks during testing.
    
    Helps ensure all tasks are properly cleaned up and provides
    utilities for waiting for task completion.
    """
    
    def __init__(self):
        self.tasks: List[asyncio.Task] = []
    
    def create_task(self, coro: Awaitable[T], name: Optional[str] = None) -> asyncio.Task[T]:
        """Create and track a new task."""
        task = asyncio.create_task(coro, name=name)
        self.tasks.append(task)
        return task
    
    async def wait_for_all_tasks(self, timeout: float = 5.0) -> None:
        """Wait for all tracked tasks to complete."""
        if not self.tasks:
            return
        
        done, pending = await asyncio.wait(
            self.tasks,
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED
        )
        
        # Cancel any pending tasks
        for task in pending:
            task.cancel()
            
        # Wait for cancellation to complete
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
    
    async def cleanup(self):
        """Cancel and clean up all tracked tasks."""
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
    
    def get_running_tasks(self) -> List[asyncio.Task]:
        """Get list of currently running tasks."""
        return [task for task in self.tasks if not task.done()]
    
    def get_completed_tasks(self) -> List[asyncio.Task]:
        """Get list of completed tasks."""
        return [task for task in self.tasks if task.done()]


async def wait_for_tasks_completion(
    tasks: List[asyncio.Task], 
    timeout: float = 5.0,
    return_when: str = "ALL_COMPLETED"
) -> None:
    """Wait for a list of tasks to complete.
    
    Args:
        tasks: List of tasks to wait for
        timeout: Maximum time to wait
        return_when: When to return ('ALL_COMPLETED', 'FIRST_COMPLETED', etc.)
    """
    if not tasks:
        return
    
    done, pending = await asyncio.wait(
        tasks,
        timeout=timeout,
        return_when=getattr(asyncio, return_when)
    )
    
    # Cancel any remaining pending tasks
    for task in pending:
        task.cancel()
        
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def assert_async_raises(
    exception_type: type,
    coro: Awaitable[Any],
    match: Optional[str] = None
) -> None:
    """Assert that an async operation raises a specific exception.
    
    Args:
        exception_type: Expected exception type
        coro: Coroutine that should raise the exception
        match: Optional regex pattern to match in exception message
    
    Usage:
        await assert_async_raises(
            ValueError,
            some_async_operation(),
            match="invalid parameter"
        )
    """
    with pytest.raises(exception_type, match=match):
        await coro


@asynccontextmanager
async def suppress_async_warnings():
    """Context manager to suppress common async testing warnings."""
    import warnings
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine.*never awaited.*")
        warnings.filterwarnings("ignore", message=".*unclosed event loop.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending.*")
        yield


class AsyncTestHelper:
    """Collection of async testing utilities in a single class."""
    
    def __init__(self):
        self.task_tracker = AsyncTaskTracker()
    
    async def cleanup(self):
        """Clean up all helper resources."""
        await self.task_tracker.cleanup()
    
    def create_task(self, coro: Awaitable[T], name: Optional[str] = None) -> asyncio.Task[T]:
        """Create and track a task."""
        return self.task_tracker.create_task(coro, name)
    
    async def wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float = 5.0,
        poll_interval: float = 0.1
    ) -> None:
        """Wait for a condition to become true."""
        return await wait_for_condition(condition, timeout, poll_interval)
    
    async def collect_from_generator(
        self,
        async_gen: AsyncGenerator[T, None],
        max_items: int = 100,
        timeout: float = 5.0
    ) -> List[T]:
        """Collect items from async generator."""
        return await collect_async_generator(async_gen, max_items, timeout)
    
    async def run_with_timeout(self, coro: Awaitable[T], timeout: float = 30.0) -> T:
        """Run coroutine with timeout."""
        return await run_with_timeout(coro, timeout)