"""Storage testing utilities.

Provides helpers for testing LMDB storage operations, database isolation,
and storage-related functionality in WriteIt's domain architecture.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional, List
from unittest.mock import AsyncMock, Mock
import json

from writeit.storage import StorageManager
from writeit.workspace import WorkspaceManager


class StorageTestHelper:
    """Helper for storage-related testing."""
    
    def __init__(self):
        self.temp_dirs: List[Path] = []
        self.storage_managers: List[StorageManager] = []
    
    def create_temp_storage_dir(self) -> Path:
        """Create temporary storage directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix="writeit_storage_test_"))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    async def create_test_storage_manager(
        self,
        workspace_name: str = "test-workspace",
        storage_dir: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> StorageManager:
        """Create a test storage manager."""
        if storage_dir is None:
            storage_dir = self.create_temp_storage_dir()
        
        if config is None:
            config = {
                "backend": "lmdb",
                "timeout_seconds": 10,
                "max_db_size": "10MB",
            }
        
        # Create workspace manager
        workspace_manager = WorkspaceManager(str(storage_dir))
        await workspace_manager.initialize()
        
        # Create storage manager
        storage_manager = StorageManager(
            workspace_manager=workspace_manager,
            workspace_name=workspace_name,
            config=config
        )
        
        await storage_manager.initialize()
        self.storage_managers.append(storage_manager)
        
        return storage_manager
    
    async def cleanup(self):
        """Clean up all test storage resources."""
        # Clean up storage managers
        for storage_manager in self.storage_managers:
            try:
                await storage_manager.cleanup()
            except Exception:
                pass  # Ignore cleanup errors
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        self.temp_dirs.clear()
        self.storage_managers.clear()


@asynccontextmanager
async def with_test_database(
    db_name: str = "test_db",
    workspace_name: str = "test-workspace",
    **config_overrides
) -> AsyncGenerator[Any, None]:
    """Context manager for isolated database testing.
    
    Args:
        db_name: Name of the test database
        workspace_name: Name of the test workspace
        **config_overrides: Storage configuration overrides
    
    Usage:
        async with with_test_database("user_db") as db:
            # Use database for testing
            await db.store("user:123", user_data)
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="writeit_db_test_"))
    
    try:
        # Default config
        config = {
            "backend": "lmdb",
            "timeout_seconds": 10,
            "max_db_size": "10MB",
        }
        config.update(config_overrides)
        
        # Create workspace manager
        workspace_manager = WorkspaceManager(str(temp_dir))
        await workspace_manager.initialize()
        
        # Create storage manager
        storage_manager = StorageManager(
            workspace_manager=workspace_manager,
            workspace_name=workspace_name,
            config=config
        )
        
        await storage_manager.initialize()
        
        # Get database
        async with storage_manager.get_database(db_name) as db:
            yield db
    
    finally:
        # Cleanup
        try:
            await storage_manager.cleanup()
        except Exception:
            pass
        
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


async def assert_stored_correctly(
    storage_manager: StorageManager,
    db_name: str,
    key: str,
    expected_data: Any,
    data_type: str = "json"
) -> None:
    """Assert that data is stored correctly in the database.
    
    Args:
        storage_manager: Storage manager to use
        db_name: Database name
        key: Storage key
        expected_data: Expected data
        data_type: Type of data ("json", "bytes", "string")
    
    Raises:
        AssertionError: If data is not stored correctly
    """
    async with storage_manager.get_database(db_name) as db:
        if data_type == "json":
            stored_data = await storage_manager.load_json(key, db_name)
            assert stored_data == expected_data, f"JSON data mismatch for key {key}"
        
        elif data_type == "bytes":
            stored_data = await storage_manager.load_bytes(key, db_name)
            assert stored_data == expected_data, f"Bytes data mismatch for key {key}"
        
        elif data_type == "string":
            stored_data = await storage_manager.load_string(key, db_name)
            assert stored_data == expected_data, f"String data mismatch for key {key}"
        
        else:
            raise ValueError(f"Unsupported data type: {data_type}")


class MockStorageManager:
    """Mock storage manager for testing."""
    
    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}  # db_name -> key -> data
        self.operation_log: List[tuple[str, str, str]] = []  # (operation, db_name, key)
        self.should_fail = False
        self.failure_message = "Mock storage failure"
    
    async def initialize(self):
        """Initialize mock storage."""
        self.operation_log.append(("initialize", "", ""))
    
    async def cleanup(self):
        """Cleanup mock storage."""
        self.operation_log.append(("cleanup", "", ""))
    
    async def store_json(self, key: str, data: Any, db_name: str = "default") -> None:
        """Store JSON data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if db_name not in self.data:
            self.data[db_name] = {}
        
        self.data[db_name][key] = data
        self.operation_log.append(("store_json", db_name, key))
    
    async def load_json(self, key: str, db_name: str = "default") -> Any:
        """Load JSON data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("load_json", db_name, key))
        
        if db_name not in self.data or key not in self.data[db_name]:
            raise KeyError(f"Key {key} not found in database {db_name}")
        
        return self.data[db_name][key]
    
    async def store_bytes(self, key: str, data: bytes, db_name: str = "default") -> None:
        """Store bytes data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if db_name not in self.data:
            self.data[db_name] = {}
        
        self.data[db_name][key] = data
        self.operation_log.append(("store_bytes", db_name, key))
    
    async def load_bytes(self, key: str, db_name: str = "default") -> bytes:
        """Load bytes data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("load_bytes", db_name, key))
        
        if db_name not in self.data or key not in self.data[db_name]:
            raise KeyError(f"Key {key} not found in database {db_name}")
        
        return self.data[db_name][key]
    
    async def store_string(self, key: str, data: str, db_name: str = "default") -> None:
        """Store string data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if db_name not in self.data:
            self.data[db_name] = {}
        
        self.data[db_name][key] = data
        self.operation_log.append(("store_string", db_name, key))
    
    async def load_string(self, key: str, db_name: str = "default") -> str:
        """Load string data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("load_string", db_name, key))
        
        if db_name not in self.data or key not in self.data[db_name]:
            raise KeyError(f"Key {key} not found in database {db_name}")
        
        return self.data[db_name][key]
    
    async def delete(self, key: str, db_name: str = "default") -> None:
        """Delete data."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("delete", db_name, key))
        
        if db_name in self.data and key in self.data[db_name]:
            del self.data[db_name][key]
    
    async def exists(self, key: str, db_name: str = "default") -> bool:
        """Check if key exists."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("exists", db_name, key))
        return db_name in self.data and key in self.data[db_name]
    
    async def list_keys(self, db_name: str = "default", prefix: str = "") -> List[str]:
        """List keys with optional prefix."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_keys", db_name, prefix))
        
        if db_name not in self.data:
            return []
        
        keys = list(self.data[db_name].keys())
        if prefix:
            keys = [key for key in keys if key.startswith(prefix)]
        
        return sorted(keys)
    
    def get_database(self, db_name: str):
        """Get database context manager."""
        return MockDatabaseContext(self, db_name)
    
    # Test helper methods
    def get_operation_count(self, operation: str, db_name: str = "", key: str = "") -> int:
        """Get count of specific operations."""
        return len([
            log for log in self.operation_log
            if (not operation or log[0] == operation) and
               (not db_name or log[1] == db_name) and
               (not key or log[2] == key)
        ])
    
    def clear_operation_log(self) -> None:
        """Clear operation log."""
        self.operation_log.clear()
    
    def get_stored_data(self, db_name: str = "default") -> Dict[str, Any]:
        """Get all stored data for a database."""
        return self.data.get(db_name, {}).copy()
    
    def clear_all_data(self) -> None:
        """Clear all stored data."""
        self.data.clear()


class MockDatabaseContext:
    """Mock database context manager."""
    
    def __init__(self, storage_manager: MockStorageManager, db_name: str):
        self.storage_manager = storage_manager
        self.db_name = db_name
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def store(self, key: str, data: Any) -> None:
        """Store data in this database."""
        if isinstance(data, dict) or isinstance(data, list):
            await self.storage_manager.store_json(key, data, self.db_name)
        elif isinstance(data, bytes):
            await self.storage_manager.store_bytes(key, data, self.db_name)
        elif isinstance(data, str):
            await self.storage_manager.store_string(key, data, self.db_name)
        else:
            # Convert to JSON for other types
            await self.storage_manager.store_json(key, data, self.db_name)
    
    async def load(self, key: str) -> Any:
        """Load data from this database."""
        # Try to load as JSON first, then fall back to other types
        try:
            return await self.storage_manager.load_json(key, self.db_name)
        except:
            try:
                return await self.storage_manager.load_string(key, self.db_name)
            except:
                return await self.storage_manager.load_bytes(key, self.db_name)
    
    async def delete(self, key: str) -> None:
        """Delete data from this database."""
        await self.storage_manager.delete(key, self.db_name)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in this database."""
        return await self.storage_manager.exists(key, self.db_name)
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List keys in this database."""
        return await self.storage_manager.list_keys(self.db_name, prefix)


class StorageTestDataFactory:
    """Factory for creating test data for storage operations."""
    
    @staticmethod
    def create_pipeline_run_data(run_id: str = "test-run-123") -> Dict[str, Any]:
        """Create test pipeline run data."""
        return {
            "run_id": run_id,
            "pipeline_id": "test-pipeline",
            "workspace_name": "test-workspace",
            "status": "running",
            "created_at": "2025-01-15T10:00:00Z",
            "inputs": {
                "topic": "Test Topic",
                "style": "formal"
            },
            "steps": {
                "outline": {
                    "status": "completed",
                    "result": "Test outline content"
                },
                "content": {
                    "status": "running", 
                    "result": None
                }
            },
            "metadata": {
                "version": "1.0.0",
                "user": "test-user"
            }
        }
    
    @staticmethod
    def create_workspace_data(workspace_name: str = "test-workspace") -> Dict[str, Any]:
        """Create test workspace data."""
        return {
            "name": workspace_name,
            "description": f"Test workspace: {workspace_name}",
            "root_path": f"/tmp/workspaces/{workspace_name}",
            "configuration": {
                "auto_save": True,
                "cache_enabled": True,
                "default_model": "gpt-4"
            },
            "created_at": "2025-01-15T10:00:00Z",
            "last_accessed": "2025-01-15T10:00:00Z",
            "is_active": True
        }
    
    @staticmethod
    def create_event_data(event_id: str = "test-event-123") -> Dict[str, Any]:
        """Create test event data."""
        return {
            "event_id": event_id,
            "event_type": "TestEvent",
            "aggregate_id": "test-aggregate-456",
            "timestamp": "2025-01-15T10:00:00Z",
            "data": {
                "test_field": "test_value",
                "number_field": 42
            },
            "metadata": {
                "version": 1,
                "source": "test"
            }
        }


async def test_storage_isolation(
    storage_manager1: StorageManager,
    storage_manager2: StorageManager,
    test_key: str = "isolation_test",
    test_data: Any = {"test": "data"}
) -> None:
    """Test that two storage managers are properly isolated.
    
    Args:
        storage_manager1: First storage manager
        storage_manager2: Second storage manager
        test_key: Key to use for testing
        test_data: Data to store
    
    Raises:
        AssertionError: If isolation is violated
    """
    db_name = "isolation_test_db"
    
    # Store data in first storage manager
    await storage_manager1.store_json(test_key, test_data, db_name)
    
    # Verify data exists in first manager
    stored_data = await storage_manager1.load_json(test_key, db_name)
    assert stored_data == test_data, "Data not stored correctly in first manager"
    
    # Verify data does NOT exist in second manager
    try:
        await storage_manager2.load_json(test_key, db_name)
        assert False, "Isolation violated: data accessible from second manager"
    except KeyError:
        pass  # Expected - data should not be accessible


class StorageBenchmarkHelper:
    """Helper for benchmarking storage operations."""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
    
    async def benchmark_operation(
        self,
        operation_name: str,
        operation: callable,
        iterations: int = 100
    ) -> Dict[str, float]:
        """Benchmark a storage operation.
        
        Args:
            operation_name: Name of the operation being benchmarked
            operation: Async callable to benchmark
            iterations: Number of iterations to run
        
        Returns:
            Performance statistics
        """
        import time
        
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            await operation()
            end_time = time.time()
            times.append(end_time - start_time)
        
        self.operation_times[operation_name] = times
        
        return {
            "operation": operation_name,
            "iterations": iterations,
            "total_time": sum(times),
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "median_time": sorted(times)[len(times) // 2]
        }
    
    def get_benchmark_summary(self) -> Dict[str, Any]:
        """Get summary of all benchmarks."""
        return {
            operation: {
                "iterations": len(times),
                "average_ms": (sum(times) / len(times)) * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
            }
            for operation, times in self.operation_times.items()
        }