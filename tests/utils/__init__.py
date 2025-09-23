"""Testing utilities for WriteIt.

This package provides common testing utilities, helpers, and patterns
for testing the WriteIt application's async-heavy domain-driven architecture.
"""

from .async_helpers import (
    async_test_timeout,
    wait_for_condition,
    collect_async_generator,
    AsyncContextManager,
)

from .event_testing import (
    EventTestHelper,
    capture_events,
    assert_event_published,
    wait_for_event,
)

from .workspace_helpers import (
    WorkspaceTestHelper,
    create_test_workspace,
    with_isolated_workspace,
)

from .storage_helpers import (
    StorageTestHelper,
    with_test_database,
    assert_stored_correctly,
)

from .mock_factories import (
    MockLLMProvider,
    MockEventBus,
    MockWorkspaceRepository,
    create_mock_pipeline_executor,
)

__all__ = [
    # Async utilities
    "async_test_timeout",
    "wait_for_condition", 
    "collect_async_generator",
    "AsyncContextManager",
    
    # Event testing
    "EventTestHelper",
    "capture_events",
    "assert_event_published",
    "wait_for_event",
    
    # Workspace testing
    "WorkspaceTestHelper", 
    "create_test_workspace",
    "with_isolated_workspace",
    
    # Storage testing
    "StorageTestHelper",
    "with_test_database", 
    "assert_stored_correctly",
    
    # Mock factories
    "MockLLMProvider",
    "MockEventBus", 
    "MockWorkspaceRepository",
    "create_mock_pipeline_executor",
]