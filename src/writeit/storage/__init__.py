# ABOUTME: WriteIt LMDB storage library
# ABOUTME: Handles persistent state management and data storage

# Export the new infrastructure storage manager for backward compatibility
from ..infrastructure.base.storage_manager import LMDBStorageManager

# Alias LMDBStorageManager as StorageManager for backward compatibility
StorageManager = LMDBStorageManager

__all__ = ["StorageManager", "LMDBStorageManager"]
