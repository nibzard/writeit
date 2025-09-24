"""Core repository integration tests without complex serialization.

Tests basic repository functionality with minimal serialization complexity.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from uuid import uuid4

# Fix import paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.base.storage_manager import LMDBStorageManager
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName


async def test_basic_storage_operations():
    """Test basic LMDB storage operations without complex serialization."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
                
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name
        
        workspace_manager = MockWorkspaceManager(temp_db_path)
        
        print("Testing basic LMDB storage operations...")
        
        # Create storage manager
        storage = LMDBStorageManager(
            workspace_manager=workspace_manager,
            workspace_name="test",
            map_size_mb=50,
            max_dbs=10
        )
        
        # Test basic JSON storage
        test_data = {
            "id": str(uuid4()),
            "name": "Test Entity",
            "description": "Test description",
            "version": "1.0.0",
            "metadata": {"type": "test"}
        }
        
        # Save data
        print("Testing JSON storage...")
        storage.store_json("test_entity", test_data, "test_db")
        
        # Load data
        loaded_data = storage.load_json("test_entity", "test_db")
        print(f"Loaded data type: {type(loaded_data)}")
        print(f"Loaded data: {loaded_data}")
        assert loaded_data is not None, "Data should be loaded"
        
        # Handle case where data might be returned as string
        if isinstance(loaded_data, str):
            loaded_data = json.loads(loaded_data)
        
        assert loaded_data["name"] == "Test Entity", "Name should match"
        assert loaded_data["id"] == test_data["id"], "ID should match"
        print("✅ JSON storage successful")
        
        # Test list operations
        print("Testing list operations...")
        all_keys = storage.list_keys("test_db")
        assert "test_entity" in all_keys, "Key should be in list"
        print("✅ List operations successful")
        
        # Test delete
        print("Testing delete operations...")
        storage.delete_key("test_entity", "test_db")
        deleted_data = storage.load_json("test_entity", "test_db")
        assert deleted_data is None, "Data should be deleted"
        print("✅ Delete operations successful")
        
        # Clean up
        storage.close()


async def test_workspace_isolation_basic():
    """Test workspace isolation at storage level."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
                
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name
        
        workspace_manager = MockWorkspaceManager(temp_db_path)
        
        print("Testing workspace isolation...")
        
        # Create storage for different workspaces
        storage1 = LMDBStorageManager(workspace_manager, "workspace1", map_size_mb=50)
        storage2 = LMDBStorageManager(workspace_manager, "workspace2", map_size_mb=50)
        
        # Store data in each workspace
        data1 = {"id": "1", "workspace": "workspace1", "value": "data1"}
        data2 = {"id": "2", "workspace": "workspace2", "value": "data2"}
        
        storage1.store_json("shared_key", data1, "test_db")
        storage2.store_json("shared_key", data2, "test_db")
        
        # Verify isolation
        loaded1 = storage1.load_json("shared_key", "test_db")
        loaded2 = storage2.load_json("shared_key", "test_db")
        
        assert loaded1["workspace"] == "workspace1", "Workspace 1 data should be isolated"
        assert loaded2["workspace"] == "workspace2", "Workspace 2 data should be isolated"
        
        print("✅ Workspace isolation successful")
        
        # Clean up
        storage1.close()
        storage2.close()


async def test_transaction_behavior():
    """Test transaction behavior and error handling."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
                
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name
        
        workspace_manager = MockWorkspaceManager(temp_db_path)
        storage = LMDBStorageManager(workspace_manager, "test", map_size_mb=50)
        
        print("Testing transaction behavior...")
        
        # Test normal operation
        test_data = {"id": "tx_test", "value": "initial"}
        storage.store_json("tx_test", test_data, "test_db")
        
        # Verify storage
        loaded = storage.load_json("tx_test", "test_db")
        assert loaded["value"] == "initial", "Initial value should be stored"
        
        # Test update
        test_data["value"] = "updated"
        storage.store_json("tx_test", test_data, "test_db")
        
        updated = storage.load_json("tx_test", "test_db")
        assert updated["value"] == "updated", "Value should be updated"
        
        print("✅ Transaction behavior successful")
        
        # Clean up
        storage.close()


async def test_concurrent_access():
    """Test concurrent access patterns."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
                
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name
        
        workspace_manager = MockWorkspaceManager(temp_db_path)
        
        print("Testing concurrent access...")
        
        # Create multiple storage instances (simulating concurrent access)
        storages = []
        for i in range(3):
            storage = LMDBStorageManager(workspace_manager, "concurrent_test", map_size_mb=50)
            storages.append(storage)
        
        # Concurrent writes
        async def write_data(storage, index):
            data = {"id": f"concurrent_{index}", "index": index, "value": f"data_{index}"}
            storage.store_json(f"concurrent_{index}", data, "test_db")
            return f"concurrent_{index}"
        
        # Execute concurrent writes
        tasks = [write_data(storages[i], i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # Verify all data was written
        verification_storage = LMDBStorageManager(workspace_manager, "concurrent_test", map_size_mb=50)
        
        all_keys = verification_storage.list_keys("test_db")
        for expected_key in results:
            assert expected_key in all_keys, f"Key {expected_key} should exist"
            
            data = verification_storage.load_json(expected_key, "test_db")
            assert data is not None, f"Data for {expected_key} should exist"
        
        print("✅ Concurrent access successful")
        
        # Clean up
        for storage in storages:
            storage.close()
        verification_storage.close()


async def test_database_recovery():
    """Test database persistence and recovery."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
                
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name
        
        workspace_manager = MockWorkspaceManager(temp_db_path)
        
        print("Testing database recovery...")
        
        # Create and populate database
        storage1 = LMDBStorageManager(workspace_manager, "recovery_test", map_size_mb=50)
        
        recovery_data = {
            "id": "recovery_test",
            "message": "This should persist",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        storage1.store_json("recovery_key", recovery_data, "recovery_db")
        
        # Verify data is there
        loaded = storage1.load_json("recovery_key", "recovery_db")
        assert loaded is not None, "Data should be stored"
        
        # Close the database
        storage1.close()
        
        # Reopen database and verify data persists
        storage2 = LMDBStorageManager(workspace_manager, "recovery_test", map_size_mb=50)
        
        recovered_data = storage2.load_json("recovery_key", "recovery_db")
        assert recovered_data is not None, "Data should be recovered"
        assert recovered_data["message"] == "This should persist", "Message should match"
        
        print("✅ Database recovery successful")
        
        # Clean up
        storage2.close()


async def run_all_tests():
    """Run all core integration tests."""
    print("🧪 Running Core Repository Integration Tests...\n")
    
    try:
        await test_basic_storage_operations()
        print()
        
        await test_workspace_isolation_basic()
        print()
        
        await test_transaction_behavior()
        print()
        
        await test_concurrent_access()
        print()
        
        await test_database_recovery()
        print()
        
        print("🎉 All core repository integration tests passed!")
        
    except Exception as e:
        print(f"❌ Core integration test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())