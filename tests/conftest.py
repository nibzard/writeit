"""Global pytest configuration and fixtures for WriteIt tests.

This module provides:
- Async test environment setup
- Test isolation utilities
- Common test fixtures
- Environment configuration for testing
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional
from unittest.mock import AsyncMock, Mock
import pytest
import pytest_asyncio
from uuid import uuid4


# ============================================================================
# Async Test Environment Configuration
# ============================================================================

@pytest_asyncio.fixture(scope="session")
def event_loop_policy():
    """Configure asyncio event loop policy for testing."""
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def async_test_context():
    """Provide isolated async context for each test."""
    # Create new event loop for isolation
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        yield loop
    finally:
        # Clean up pending tasks
        pending = asyncio.all_tasks(loop)
        if pending:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        
        loop.close()


# ============================================================================
# Test Environment Setup
# ============================================================================

@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test isolation."""
    temp_path = tempfile.mkdtemp(prefix="writeit_test_")
    try:
        yield Path(temp_path)
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def test_workspace_root(temp_dir):
    """Create test workspace root directory."""
    workspace_root = temp_dir / "test_workspaces"
    workspace_root.mkdir(parents=True, exist_ok=True)
    return workspace_root


@pytest.fixture(scope="function")
def test_config():
    """Provide test configuration settings."""
    return {
        "workspace": {
            "default_name": "test-workspace",
            "auto_create": True,
            "isolation_enabled": True,
        },
        "storage": {
            "backend": "lmdb",
            "timeout_seconds": 30,
            "max_db_size": "10MB",
        },
        "llm": {
            "default_model": "mock",
            "timeout_seconds": 60,
            "cache_enabled": True,
            "cache_ttl_hours": 24,
        },
        "pipeline": {
            "max_concurrent_steps": 3,
            "step_timeout_seconds": 300,
            "enable_streaming": True,
        },
        "testing": {
            "mock_llm_responses": True,
            "deterministic_uuids": True,
            "fast_mode": True,
        }
    }


# ============================================================================
# Mock LLM and External Services
# ============================================================================

@pytest.fixture
def mock_llm_provider():
    """Provide mock LLM provider for deterministic testing."""
    mock = AsyncMock()
    
    # Configure common responses
    mock.generate_text = AsyncMock(return_value="Mock generated text")
    mock.stream_text = AsyncMock()
    mock.get_model_info = Mock(return_value={
        "name": "mock-model",
        "version": "1.0.0",
        "provider": "mock",
        "context_length": 4096
    })
    
    return mock


@pytest.fixture
def mock_pipeline_context():
    """Provide mock pipeline execution context."""
    return {
        "pipeline_id": str(uuid4()),
        "run_id": str(uuid4()),
        "workspace_name": "test-workspace",
        "user_inputs": {
            "topic": "Test Topic",
            "style": "formal"
        },
        "step_results": {},
        "metadata": {
            "created_at": "2025-01-15T10:00:00Z",
            "version": "1.0.0"
        }
    }


# ============================================================================
# Test Markers and Utilities
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Add custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "requires_llm: marks tests that require actual LLM API access")
    config.addinivalue_line("markers", "requires_network: marks tests that require network access")
    
    # Set test environment variables
    os.environ["WRITEIT_TEST_MODE"] = "true"
    os.environ["WRITEIT_LOG_LEVEL"] = "WARNING"  # Reduce log noise in tests


# Removed custom pytest_collection_modifyitems - using asyncio_mode = "auto" instead


# ============================================================================
# Test Data Factories
# ============================================================================

class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_pipeline_yaml(name: str = "test-pipeline") -> Dict[str, Any]:
        """Create a test pipeline YAML structure."""
        return {
            "metadata": {
                "name": f"{name}",
                "description": f"Test pipeline: {name}",
                "version": "1.0.0"
            },
            "defaults": {
                "model": "mock-model"
            },
            "inputs": {
                "topic": {
                    "type": "text",
                    "label": "Topic",
                    "required": True,
                    "default": "Test Topic"
                }
            },
            "steps": {
                "generate": {
                    "name": "Generate Content",
                    "type": "llm_generate",
                    "prompt_template": "Write about {{ inputs.topic }}",
                    "model_preference": ["{{ defaults.model }}"]
                }
            }
        }
    
    @staticmethod
    def create_workspace_config(**overrides) -> Dict[str, Any]:
        """Create a test workspace configuration."""
        config = {
            "name": "test-workspace",
            "description": "Test workspace",
            "settings": {
                "auto_save": True,
                "cache_enabled": True,
                "default_model": "mock-model"
            },
            "security": {
                "isolation_enabled": True,
                "allowed_operations": ["read", "write", "execute"]
            }
        }
        config.update(overrides)
        return config


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory()


# ============================================================================
# Environment Variable Management
# ============================================================================

@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    # Set test-specific environment variables
    test_env = {
        "WRITEIT_TEST_MODE": "true",
        "WRITEIT_LOG_LEVEL": "WARNING",
        "WRITEIT_CACHE_DISABLED": "false",  # Enable caching for performance
        "WRITEIT_WORKSPACE_ROOT": "",  # Will be set by individual tests
        "WRITEIT_LLM_PROVIDER": "mock",
        "WRITEIT_DATABASE_TIMEOUT": "10",  # Shorter timeout for tests
    }
    
    os.environ.update(test_env)
    
    try:
        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


# ============================================================================
# Performance and Timing Utilities
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    import time
    from collections import defaultdict
    
    metrics = defaultdict(list)
    
    class PerformanceTracker:
        def time_operation(self, operation_name: str):
            """Context manager to time operations."""
            return self._TimedOperation(operation_name, metrics)
        
        def get_metrics(self) -> Dict[str, Any]:
            """Get collected performance metrics."""
            return {
                name: {
                    "count": len(times),
                    "total": sum(times),
                    "average": sum(times) / len(times) if times else 0,
                    "min": min(times) if times else 0,
                    "max": max(times) if times else 0,
                }
                for name, times in metrics.items()
            }
        
        class _TimedOperation:
            def __init__(self, name: str, metrics: Dict):
                self.name = name
                self.metrics = metrics
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.metrics[self.name].append(duration)
    
    return PerformanceTracker()


# ============================================================================
# Simplified Mock Classes for Testing
# ============================================================================

class SimpleMockEventBus:
    """Simple mock event bus for basic testing."""
    
    def __init__(self):
        self.published_events = []
        self.running = False
    
    async def publish(self, event):
        """Mock publish event."""
        self.published_events.append(event)
        return Mock(
            event=event,
            handlers_executed=0,
            handlers_failed=0,
            errors=[],
            stored_event=event
        )
    
    async def start(self):
        """Mock start."""
        self.running = True
    
    async def stop(self):
        """Mock stop."""
        self.running = False


@pytest.fixture
def simple_mock_event_bus():
    """Provide simple mock event bus."""
    return SimpleMockEventBus()


# ============================================================================
# Test Helper Functions
# ============================================================================

async def wait_for_condition(condition_func, timeout=5.0, poll_interval=0.1):
    """Wait for a condition to become true."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(poll_interval)
    
    return False


@pytest.fixture
def wait_for():
    """Provide wait_for_condition helper."""
    return wait_for_condition