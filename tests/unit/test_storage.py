# ABOUTME: Unit tests for WriteIt storage manager functionality
# ABOUTME: Tests LMDB storage operations with workspace awareness
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from writeit.storage.manager import StorageManager, create_storage_manager
from writeit.workspace.workspace import Workspace


class TestStorageManager:
    """Test suite for StorageManager class."""

    @pytest.fixture
    def temp_home(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def workspace_manager(self, temp_home):
        """Create workspace manager with temporary directory."""
        workspace = Workspace(temp_home / ".writeit")
        workspace.initialize()
        workspace.create_workspace("test_workspace")
        return workspace

    @pytest.fixture
    def storage_manager(self, workspace_manager):
        """Create StorageManager instance."""
        return StorageManager(workspace_manager, "test_workspace")

    def test_storage_manager_initialization(self, storage_manager, workspace_manager):
        """Test StorageManager initialization."""
        assert storage_manager.workspace_manager == workspace_manager
        assert storage_manager.workspace_name == "test_workspace"
        assert storage_manager._connections == {}

    def test_storage_path_with_workspace_manager(
        self, storage_manager, workspace_manager
    ):
        """Test storage path resolution with workspace manager."""
        expected_path = workspace_manager.get_workspace_path("test_workspace")
        assert storage_manager.storage_path == expected_path

    def test_storage_path_fallback_without_workspace_manager(self):
        """Test storage path fallback when no workspace manager."""
        storage = StorageManager()
        assert storage.storage_path == Path.cwd() / ".writeit"

    def test_get_db_path(self, storage_manager):
        """Test database path generation."""
        db_path = storage_manager.get_db_path("artifacts")
        expected_path = storage_manager.storage_path / "artifacts.lmdb"
        assert db_path == expected_path

    def test_store_and_load_json(self, storage_manager):
        """Test storing and loading JSON data."""
        test_data = {
            "key": "value",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
        }

        # Store data
        storage_manager.store_json("test_key", test_data)

        # Load data
        loaded_data = storage_manager.load_json("test_key")
        assert loaded_data == test_data

    def test_load_json_default_value(self, storage_manager):
        """Test loading JSON with default value for nonexistent key."""
        default_value = {"default": True}
        result = storage_manager.load_json("nonexistent", default=default_value)
        assert result == default_value

    def test_load_json_corrupted_data(self, storage_manager):
        """Test loading corrupted JSON data returns default."""
        # Store corrupted data directly
        storage_manager.store_binary("corrupted", b"not valid json")

        # Should return default value
        result = storage_manager.load_json("corrupted", default="fallback")
        assert result == "fallback"

    def test_store_and_load_binary(self, storage_manager):
        """Test storing and loading binary data."""
        test_data = b"binary test data \x00\x01\x02\xff"

        # Store binary data
        storage_manager.store_binary("binary_key", test_data)

        # Load binary data
        loaded_data = storage_manager.load_binary("binary_key")
        assert loaded_data == test_data

    def test_load_binary_default_value(self, storage_manager):
        """Test loading binary with default value for nonexistent key."""
        default_value = b"default binary"
        result = storage_manager.load_binary("nonexistent", default=default_value)
        assert result == default_value

    def test_store_and_load_object(self, storage_manager):
        """Test storing and loading Python objects."""
        test_object = {
            "string": "test",
            "number": 42,
            "list": [1, 2, {"nested": True}],
            "set": {1, 2, 3},  # Set will be preserved through pickle
        }

        # Store object
        storage_manager.store_object("object_key", test_object)

        # Load object
        loaded_object = storage_manager.load_object("object_key")
        assert loaded_object == test_object

    def test_load_object_default_value(self, storage_manager):
        """Test loading object with default value for nonexistent key."""
        default_object = {"default": "object"}
        result = storage_manager.load_object("nonexistent", default=default_object)
        assert result == default_object

    def test_load_object_corrupted_data(self, storage_manager):
        """Test loading corrupted pickle data returns default."""
        # Store corrupted data
        storage_manager.store_binary("corrupted_pickle", b"not valid pickle data")

        # Should return default
        result = storage_manager.load_object("corrupted_pickle", default="fallback")
        assert result == "fallback"

    def test_delete_existing_key(self, storage_manager):
        """Test deleting existing key."""
        # Store data first
        storage_manager.store_json("to_delete", {"data": "value"})
        assert storage_manager.exists("to_delete")

        # Delete key
        result = storage_manager.delete("to_delete")
        assert result is True
        assert not storage_manager.exists("to_delete")

    def test_delete_nonexistent_key(self, storage_manager):
        """Test deleting nonexistent key."""
        result = storage_manager.delete("nonexistent")
        assert result is False

    def test_exists_key(self, storage_manager):
        """Test checking key existence."""
        assert not storage_manager.exists("test_key")

        storage_manager.store_json("test_key", {"data": "value"})
        assert storage_manager.exists("test_key")

    def test_list_keys_empty(self, storage_manager):
        """Test listing keys when database is empty."""
        keys = storage_manager.list_keys()
        assert keys == []

    def test_list_keys_with_data(self, storage_manager):
        """Test listing keys with stored data."""
        # Store multiple keys
        storage_manager.store_json("key1", "value1")
        storage_manager.store_json("key2", "value2")
        storage_manager.store_json("prefix_key1", "value3")
        storage_manager.store_json("prefix_key2", "value4")

        # List all keys
        all_keys = storage_manager.list_keys()
        assert set(all_keys) == {"key1", "key2", "prefix_key1", "prefix_key2"}

    def test_list_keys_with_prefix(self, storage_manager):
        """Test listing keys with prefix filter."""
        # Store keys with different prefixes
        storage_manager.store_json("user_1", "value1")
        storage_manager.store_json("user_2", "value2")
        storage_manager.store_json("article_1", "value3")
        storage_manager.store_json("article_2", "value4")

        # List keys with prefix
        user_keys = storage_manager.list_keys("user_")
        article_keys = storage_manager.list_keys("article_")

        assert set(user_keys) == {"user_1", "user_2"}
        assert set(article_keys) == {"article_1", "article_2"}

    def test_multiple_databases(self, storage_manager):
        """Test using multiple named databases."""
        # Store data in different databases
        storage_manager.store_json("key1", "main_value", db_name="main")
        storage_manager.store_json("key1", "artifacts_value", db_name="artifacts")
        storage_manager.store_json("key1", "pipelines_value", db_name="pipelines")

        # Load from different databases
        main_value = storage_manager.load_json("key1", db_name="main")
        artifacts_value = storage_manager.load_json("key1", db_name="artifacts")
        pipelines_value = storage_manager.load_json("key1", db_name="pipelines")

        assert main_value == "main_value"
        assert artifacts_value == "artifacts_value"
        assert pipelines_value == "pipelines_value"

    def test_sub_databases(self, storage_manager):
        """Test using sub-databases within a database."""
        # Store data in different sub-databases
        storage_manager.store_json("key1", "value1", db_name="main", db_key="sub1")
        storage_manager.store_json("key1", "value2", db_name="main", db_key="sub2")

        # Load from different sub-databases
        value1 = storage_manager.load_json("key1", db_name="main", db_key="sub1")
        value2 = storage_manager.load_json("key1", db_name="main", db_key="sub2")

        assert value1 == "value1"
        assert value2 == "value2"

    def test_get_stats(self, storage_manager):
        """Test getting database statistics."""
        # Store some data
        for i in range(10):
            storage_manager.store_json(f"key_{i}", {"index": i})

        stats = storage_manager.get_stats()

        # Check that stats contain expected keys
        assert "entries" in stats
        assert "page_size" in stats
        assert "depth" in stats
        assert isinstance(stats["entries"], int)
        assert stats["entries"] >= 10  # At least our 10 entries

    def test_close_connections(self, storage_manager):
        """Test closing all connections."""
        # Create connections by storing data
        storage_manager.store_json("key1", "value1", db_name="db1")
        storage_manager.store_json("key2", "value2", db_name="db2")

        # Should have connections
        assert len(storage_manager._connections) > 0

        # Close connections
        storage_manager.close()

        # Connections should be cleared
        assert len(storage_manager._connections) == 0

    def test_connection_reuse(self, storage_manager):
        """Test that connections are reused properly."""
        # Store data twice in same database
        storage_manager.store_json("key1", "value1")
        storage_manager.store_json("key2", "value2")

        # Should only have one connection for default workspace/db
        assert len(storage_manager._connections) == 1

    def test_workspace_isolation(self, workspace_manager):
        """Test that different workspaces have isolated storage."""
        # Create another workspace
        workspace_manager.create_workspace("workspace2")

        # Create storage managers for different workspaces
        storage1 = StorageManager(workspace_manager, "test_workspace")
        storage2 = StorageManager(workspace_manager, "workspace2")

        # Store data in each workspace
        storage1.store_json("shared_key", "workspace1_value")
        storage2.store_json("shared_key", "workspace2_value")

        # Data should be isolated
        value1 = storage1.load_json("shared_key")
        value2 = storage2.load_json("shared_key")

        assert value1 == "workspace1_value"
        assert value2 == "workspace2_value"


class TestStorageManagerFactory:
    """Test suite for storage manager factory function."""

    def test_create_storage_manager_no_args(self):
        """Test creating storage manager with no arguments."""
        storage = create_storage_manager()

        assert isinstance(storage, StorageManager)
        assert storage.workspace_manager is None
        assert storage.workspace_name is None

    def test_create_storage_manager_with_workspace_manager(self):
        """Test creating storage manager with workspace manager."""
        mock_workspace = Mock()
        storage = create_storage_manager(workspace_manager=mock_workspace)

        assert storage.workspace_manager == mock_workspace
        assert storage.workspace_name is None

    def test_create_storage_manager_with_workspace_name(self):
        """Test creating storage manager with workspace name."""
        mock_workspace = Mock()
        storage = create_storage_manager(
            workspace_manager=mock_workspace, workspace_name="test_workspace"
        )

        assert storage.workspace_manager == mock_workspace
        assert storage.workspace_name == "test_workspace"
