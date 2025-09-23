# WriteIt Testing Framework

Comprehensive async-first testing framework for WriteIt's domain-driven architecture.

## Overview

This testing framework provides:
- ✅ **Comprehensive pytest configuration** with async support
- ✅ **Domain-specific test utilities** for workspace, storage, events
- ✅ **Mock factories** for deterministic testing
- ✅ **Test isolation** with workspace and storage isolation
- ✅ **Performance tracking** and benchmarking utilities
- ✅ **Event testing** infrastructure for domain events
- ✅ **Async helper utilities** for complex async patterns

## Quick Start

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m "not slow"    # Skip slow tests

# Run with coverage
uv run pytest --cov=src/writeit --cov-report=html

# Run specific test files
uv run pytest tests/unit/domains/workspace/
uv run pytest tests/integration/
```

### Writing Tests

#### Async Tests
All async tests must use explicit `@pytest.mark.asyncio` marker:

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_operation():
    """Test async functionality."""
    await asyncio.sleep(0.001)
    assert True

class TestAsyncClass:
    @pytest.mark.asyncio
    async def test_async_method(self):
        """Async test in class."""
        await some_async_operation()
        assert result == expected
```

#### Using Test Utilities

```python
from tests.utils import (
    async_test_timeout,
    wait_for_condition,
    with_isolated_workspace,
    create_test_workspace
)

@pytest.mark.asyncio
@async_test_timeout(10.0)  # 10 second timeout
async def test_with_timeout():
    """Test with timeout protection."""
    await long_running_operation()

@pytest.mark.asyncio
async def test_workspace_isolation():
    """Test with isolated workspace."""
    async with with_isolated_workspace("test-ws") as workspace:
        # Use workspace for testing
        assert workspace.name.value == "test-ws"
```

## Test Categories and Markers

### Available Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, cross-component)
- `@pytest.mark.contract` - API contract tests
- `@pytest.mark.slow` - Slow-running tests (>1 second)
- `@pytest.mark.llm` - Tests requiring LLM API access
- `@pytest.mark.workspace` - Tests requiring workspace setup
- `@pytest.mark.storage` - Tests requiring LMDB storage
- `@pytest.mark.event_bus` - Tests for event bus functionality
- `@pytest.mark.pipeline` - Tests for pipeline execution

### Test Organization

```
tests/
├── conftest.py              # Global fixtures and configuration
├── utils/                   # Testing utilities and helpers
│   ├── async_helpers.py     # Async testing utilities
│   ├── event_testing.py     # Event system testing
│   ├── workspace_helpers.py # Workspace testing utilities
│   ├── storage_helpers.py   # Storage testing utilities
│   └── mock_factories.py    # Mock object factories
├── unit/                    # Unit tests
│   ├── domains/             # Domain-specific unit tests
│   ├── shared/              # Shared infrastructure tests
│   └── infrastructure/      # Infrastructure layer tests
├── integration/             # Integration tests
└── contract/                # API contract tests
```

## Available Fixtures

### Core Fixtures

- `temp_dir` - Temporary directory for test isolation
- `test_workspace_root` - Test workspace root directory
- `test_config` - Test configuration dictionary
- `mock_llm_provider` - Mock LLM provider for testing
- `test_data_factory` - Factory for creating test data
- `performance_tracker` - Performance measurement utilities

### Async Fixtures

- `async_test_context` - Isolated async context per test
- `simple_mock_event_bus` - Basic mock event bus

### Helper Functions

- `wait_for_condition(condition_func, timeout=5.0)` - Wait for condition
- `wait_for()` - Fixture providing wait_for_condition

## Testing Patterns

### Domain Entity Testing

```python
from writeit.domains.workspace.entities.workspace import Workspace
from tests.utils import create_test_workspace

def test_workspace_entity():
    """Test workspace domain entity."""
    workspace = create_test_workspace("test-ws")
    assert workspace.name.value == "test-ws"
    assert workspace.is_initialized()
```

### Async Service Testing

```python
import pytest
from tests.utils import MockWorkspaceRepository

@pytest.mark.asyncio
async def test_workspace_service():
    """Test workspace service with mock repository."""
    mock_repo = MockWorkspaceRepository()
    service = WorkspaceService(mock_repo)
    
    result = await service.create_workspace("test-ws")
    assert result.name.value == "test-ws"
    assert mock_repo.get_operation_count("save") == 1
```

### Event Testing

```python
import pytest
from tests.utils import EventTestHelper, capture_events

@pytest.mark.asyncio
async def test_event_publishing():
    """Test domain event publishing."""
    async with capture_events([WorkspaceCreated]) as capture:
        await workspace_service.create_workspace("test")
        
        assert capture.event_count == 1
        events = capture.get_events_of_type(WorkspaceCreated)
        assert len(events) == 1
```

### Storage Testing

```python
import pytest
from tests.utils import with_test_database, assert_stored_correctly

@pytest.mark.asyncio
async def test_storage_operations():
    """Test storage operations with isolated database."""
    async with with_test_database("test_db") as db:
        test_data = {"key": "value", "number": 42}
        
        await db.store("test_key", test_data)
        loaded_data = await db.load("test_key")
        
        assert loaded_data == test_data
```

### Performance Testing

```python
@pytest.mark.asyncio
async def test_performance_tracking(performance_tracker):
    """Test with performance tracking."""
    with performance_tracker.time_operation("database_write"):
        await database.store_large_object(large_data)
    
    metrics = performance_tracker.get_metrics()
    assert metrics["database_write"]["average"] < 1.0  # Should be fast
```

## Configuration

### pytest.ini (Legacy)
Contains basic configuration with references to pyproject.toml.

### pyproject.toml
Main configuration file with:
- Test discovery patterns
- Async testing setup
- Comprehensive markers
- Coverage configuration
- Output formatting
- Timeout protection

### Key Configuration Options

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]

# Async tests require explicit @pytest.mark.asyncio marker
# Auto-detection has compatibility issues with current setup

addopts = [
    "-v",                    # Verbose output
    "--tb=short",           # Short traceback format
    "--strict-markers",     # Strict marker validation
    "--timeout=300",        # 5 minute timeout for LLM operations
    "--durations=10",       # Show 10 slowest tests
]
```

## Mock Objects and Testing Doubles

### MockLLMProvider
```python
mock_llm = MockLLMProvider()
mock_llm.set_response("write about", "Mock content about the topic")
mock_llm.set_default_response("Default mock response")

response = await mock_llm.generate_text("write about testing")
assert response == "Mock content about the topic"
```

### MockEventBus
```python
mock_bus = MockEventBus()
await mock_bus.start()

result = await mock_bus.publish(test_event)
assert result.handlers_executed == 0
assert len(mock_bus.published_events) == 1
```

### MockWorkspaceRepository
```python
mock_repo = MockWorkspaceRepository()
mock_repo.add_workspace(test_workspace)

found = await mock_repo.find_by_name(workspace_name)
assert found == test_workspace
assert mock_repo.get_operation_count("find_by_name") == 1
```

## Environment Variables

Test environment automatically sets:
- `WRITEIT_TEST_MODE=true`
- `WRITEIT_LOG_LEVEL=WARNING`
- `WRITEIT_LLM_PROVIDER=mock`
- `WRITEIT_DATABASE_TIMEOUT=10`

## Best Practices

### 1. Test Isolation
- Each test gets fresh temporary directories
- Use isolated workspaces for workspace tests
- Mock external dependencies (LLM APIs, networks)

### 2. Async Testing
- Always use `@pytest.mark.asyncio` for async tests
- Use timeout decorators for long operations
- Clean up async resources properly

### 3. Deterministic Testing
- Use mock responses instead of real LLM calls
- Use fixed UUIDs and timestamps where possible
- Control randomness and external factors

### 4. Performance Awareness
- Mark slow tests with `@pytest.mark.slow`
- Use performance tracking for critical paths
- Set appropriate timeouts

### 5. Domain Testing
- Test domain entities in isolation
- Test services with mock repositories
- Test integration points with real components

## Troubleshooting

### Common Issues

**Async tests failing with "not natively supported"**
- Ensure `@pytest.mark.asyncio` marker is present
- Check that pytest-asyncio is installed correctly

**Import errors in tests**
- Verify module imports in test files
- Check that conftest.py imports are working

**Timeout errors**
- Increase timeout for slow operations
- Use `@async_test_timeout(seconds)` decorator

**Database/Storage errors**
- Ensure proper cleanup of test databases
- Use isolated storage contexts for tests

### Debug Commands

```bash
# Check pytest configuration
uv run pytest --collect-only --quiet

# Check installed plugins
uv run pytest --version

# Run with verbose debugging
uv run pytest -v -s tests/test_specific.py

# Check markers
uv run pytest --markers
```

## Future Enhancements

- [ ] Add property-based testing with Hypothesis
- [ ] Enhanced performance benchmarking
- [ ] Test data generation utilities
- [ ] Snapshot testing for complex outputs
- [ ] Parallel test execution optimization
- [ ] Advanced event sequence validation