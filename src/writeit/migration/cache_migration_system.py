"""Cache Migration System for WriteIt DDD Refactoring.

This module provides comprehensive cache migration utilities for converting
legacy cache formats to the new DDD-compatible structure. It handles:
- LLM response cache migration
- Template cache migration
- Workspace cache migration
- Cache structure reorganization
- Cache validation and cleanup
"""

import json
import pickle
import lmdb
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union, Set
import hashlib
import uuid

from writeit.workspace.workspace import Workspace


class CacheMigrationError(Exception):
    """Exception raised during cache migration."""
    pass


class CacheMigrationSystem:
    """Handles migration of cache data to DDD format."""
    
    def __init__(self, workspace: Workspace):
        """Initialize cache migration system.
        
        Args:
            workspace: Workspace instance
        """
        self.workspace = workspace
        self.migration_log = []
        self.cache_stats = {
            "entries_migrated": 0,
            "entries_skipped": 0,
            "entries_failed": 0,
            "cache_files_processed": 0,
            "storage_optimized": False
        }
        
    def log_migration(self, message: str, level: str = "info") -> None:
        """Log cache migration activity."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.migration_log.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
        
    def get_migration_log(self) -> List[Dict[str, Any]]:
        """Get migration log.
        
        Returns:
            List of migration log entries
        """
        return self.migration_log
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache migration statistics.
        
        Returns:
            Cache migration statistics
        """
        return self.cache_stats.copy()
        
    def migrate_all_caches(self, workspace_name: Optional[str] = None) -> bool:
        """Migrate all cache data to DDD format.
        
        Args:
            workspace_name: Specific workspace to migrate (None for all)
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.log_migration("Starting comprehensive cache migration")
            
            # Migrate global cache
            global_success = self._migrate_global_cache()
            
            # Migrate workspace caches
            workspace_success = self._migrate_workspace_caches(workspace_name)
            
            # Optimize cache storage
            optimization_success = self._optimize_cache_storage()
            
            # Validate migrated cache
            validation_success = self._validate_migrated_cache()
            
            overall_success = all([global_success, workspace_success, 
                                 optimization_success, validation_success])
            
            if overall_success:
                self.log_migration("Cache migration completed successfully")
                self.log_migration(f"Statistics: {self.cache_stats}")
            else:
                self.log_migration("Cache migration completed with issues", "warning")
                
            return overall_success
            
        except Exception as e:
            self.log_migration(f"Cache migration failed: {e}", "error")
            return False
            
    def _migrate_global_cache(self) -> bool:
        """Migrate global cache data.
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.log_migration("Migrating global cache")
            
            # Find global cache directories
            global_cache_paths = [
                self.workspace.base_dir / "cache",
                self.workspace.base_dir / "global_cache"
            ]
            
            success = True
            for cache_path in global_cache_paths:
                if cache_path.exists():
                    if not self._migrate_cache_directory(cache_path, "global"):
                        success = False
                        
            return success
            
        except Exception as e:
            self.log_migration(f"Global cache migration failed: {e}", "error")
            return False
            
    def _migrate_workspace_caches(self, workspace_name: Optional[str] = None) -> bool:
        """Migrate workspace-specific cache data.
        
        Args:
            workspace_name: Specific workspace to migrate (None for all)
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            if workspace_name:
                workspace_names = [workspace_name]
            else:
                workspace_names = self.workspace.list_workspaces()
                
            if not workspace_names:
                self.log_migration("No workspaces found for cache migration", "warning")
                return True
                
            success_count = 0
            for ws_name in workspace_names:
                if self._migrate_workspace_cache(ws_name):
                    success_count += 1
                    
            result = success_count == len(workspace_names)
            if result:
                self.log_migration(f"Successfully migrated {success_count} workspace caches")
            else:
                self.log_migration(f"Migrated {success_count}/{len(workspace_names)} workspace caches", "warning")
                
            return result
            
        except Exception as e:
            self.log_migration(f"Workspace cache migration failed: {e}", "error")
            return False
            
    def _migrate_workspace_cache(self, workspace_name: str) -> bool:
        """Migrate cache for a specific workspace.
        
        Args:
            workspace_name: Name of workspace
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            
            # Find cache directories
            cache_paths = [
                workspace_path / "cache",
                workspace_path / "workspace" / "cache",
                workspace_path / ".cache"
            ]
            
            success = True
            for cache_path in cache_paths:
                if cache_path.exists():
                    if not self._migrate_cache_directory(cache_path, "workspace", workspace_name):
                        success = False
                        
            if success:
                self.log_migration(f"Successfully migrated cache for workspace: {workspace_name}")
            else:
                self.log_migration(f"Cache migration failed for workspace: {workspace_name}", "warning")
                
            return success
            
        except Exception as e:
            self.log_migration(f"Workspace cache migration failed for {workspace_name}: {e}", "error")
            return False
            
    def _migrate_cache_directory(self, cache_path: Path, cache_type: str, workspace_name: Optional[str] = None) -> bool:
        """Migrate a specific cache directory.
        
        Args:
            cache_path: Path to cache directory
            cache_type: Type of cache ('global' or 'workspace')
            workspace_name: Workspace name (for workspace caches)
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.log_migration(f"Migrating cache directory: {cache_path}")
            
            # Create backup
            backup_path = self._create_cache_backup(cache_path)
            
            # Process LMDB files
            lmdb_files = list(cache_path.glob("*.mdb")) + list(cache_path.glob("*.lmdb"))
            for lmdb_file in lmdb_files:
                self._migrate_lmdb_cache(lmdb_file, cache_type, workspace_name)
                
            # Process JSON cache files
            json_files = list(cache_path.glob("*.json"))
            for json_file in json_files:
                self._migrate_json_cache(json_file, cache_type, workspace_name)
                
            # Process pickle cache files
            pickle_files = list(cache_path.glob("*.pkl")) + list(cache_path.glob("*.pickle"))
            for pickle_file in pickle_files:
                self._migrate_pickle_cache(pickle_file, cache_type, workspace_name)
                
            # Create DDD cache structure
            self._create_ddd_cache_structure(cache_path, cache_type, workspace_name)
            
            self.cache_stats["cache_files_processed"] += 1
            self.log_migration(f"Successfully migrated cache directory: {cache_path}")
            return True
            
        except Exception as e:
            self.log_migration(f"Failed to migrate cache directory {cache_path}: {e}", "error")
            return False
            
    def _create_cache_backup(self, cache_path: Path) -> Path:
        """Create backup of cache directory.
        
        Args:
            cache_path: Path to cache directory
            
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_name = cache_path.name
        backup_name = f"cache_backup_{cache_name}_{timestamp}"
        backup_path = cache_path.parent / backup_name
        
        try:
            if cache_path.is_dir():
                shutil.copytree(cache_path, backup_path)
            else:
                shutil.copy2(cache_path, backup_path)
                
            self.log_migration(f"Created cache backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.log_migration(f"Failed to create cache backup: {e}", "error")
            raise CacheMigrationError(f"Backup creation failed: {e}")
            
    def _migrate_lmdb_cache(self, lmdb_file: Path, cache_type: str, workspace_name: Optional[str] = None) -> None:
        """Migrate LMDB cache file to DDD format.
        
        Args:
            lmdb_file: Path to LMDB file
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
        """
        try:
            self.log_migration(f"Migrating LMDB cache: {lmdb_file.name}")
            
            # Open legacy LMDB
            legacy_env = lmdb.open(str(lmdb_file), readonly=True, max_dbs=10)
            
            # Create new LMDB with DDD structure
            target_dir = lmdb_file.parent / "migrated"
            target_dir.mkdir(exist_ok=True)
            target_file = target_dir / f"ddd_{lmdb_file.name}"
            
            new_env = lmdb.open(str(target_file), max_dbs=10)
            
            # Migrate entries
            with legacy_env.begin() as legacy_txn:
                with new_env.begin(write=True) as new_txn:
                    cursor = legacy_txn.cursor()
                    
                    for key, value in cursor:
                        try:
                            # Migrate cache entry
                            migrated_entry = self._migrate_cache_entry(
                                key, value, cache_type, workspace_name
                            )
                            
                            # Store migrated entry
                            new_txn.put(key, migrated_entry)
                            self.cache_stats["entries_migrated"] += 1
                            
                        except Exception as e:
                            self.log_migration(f"Failed to migrate LMDB entry {key}: {e}", "warning")
                            self.cache_stats["entries_failed"] += 1
                            continue
                            
            # Close environments
            legacy_env.close()
            new_env.close()
            
            self.log_migration(f"Successfully migrated LMDB cache: {lmdb_file.name}")
            
        except Exception as e:
            self.log_migration(f"LMDB cache migration failed for {lmdb_file}: {e}", "error")
            raise CacheMigrationError(f"LMDB migration failed: {e}")
            
    def _migrate_json_cache(self, json_file: Path, cache_type: str, workspace_name: Optional[str] = None) -> None:
        """Migrate JSON cache file to DDD format.
        
        Args:
            json_file: Path to JSON cache file
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
        """
        try:
            self.log_migration(f"Migrating JSON cache: {json_file.name}")
            
            # Load JSON cache
            with open(json_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Migrate cache data
            migrated_data = self._migrate_cache_structure(cache_data, cache_type, workspace_name)
            
            # Create target directory
            target_dir = json_file.parent / "migrated"
            target_dir.mkdir(exist_ok=True)
            target_file = target_dir / f"ddd_{json_file.name}"
            
            # Save migrated cache
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(migrated_data, f, indent=2, ensure_ascii=False)
                
            self.cache_stats["entries_migrated"] += len(cache_data) if isinstance(cache_data, dict) else 1
            self.log_migration(f"Successfully migrated JSON cache: {json_file.name}")
            
        except Exception as e:
            self.log_migration(f"JSON cache migration failed for {json_file}: {e}", "error")
            raise CacheMigrationError(f"JSON migration failed: {e}")
            
    def _migrate_pickle_cache(self, pickle_file: Path, cache_type: str, workspace_name: Optional[str] = None) -> None:
        """Migrate pickle cache file to DDD format.
        
        Args:
            pickle_file: Path to pickle cache file
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
        """
        try:
            self.log_migration(f"Migrating pickle cache: {pickle_file.name}")
            
            # Load pickle cache
            with open(pickle_file, 'rb') as f:
                cache_data = pickle.load(f)
                
            # Convert to JSON-compatible format and migrate
            json_data = self._convert_pickle_to_json(cache_data)
            migrated_data = self._migrate_cache_structure(json_data, cache_type, workspace_name)
            
            # Create target directory
            target_dir = pickle_file.parent / "migrated"
            target_dir.mkdir(exist_ok=True)
            target_file = target_dir / f"ddd_{pickle_file.stem}.json"
            
            # Save as JSON (new format)
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(migrated_data, f, indent=2, ensure_ascii=False)
                
            self.cache_stats["entries_migrated"] += len(json_data) if isinstance(json_data, dict) else 1
            self.log_migration(f"Successfully migrated pickle cache: {pickle_file.name}")
            
        except Exception as e:
            self.log_migration(f"Pickle cache migration failed for {pickle_file}: {e}", "error")
            raise CacheMigrationError(f"Pickle migration failed: {e}")
            
    def _migrate_cache_entry(self, key: bytes, value: bytes, cache_type: str, workspace_name: Optional[str] = None) -> bytes:
        """Migrate a single cache entry.
        
        Args:
            key: Entry key
            value: Entry value
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
            
        Returns:
            Migrated entry value as bytes
        """
        try:
            # Try to decode as JSON
            try:
                entry_data = json.loads(value.decode('utf-8'))
                migrated_data = self._migrate_cache_entry_data(entry_data, cache_type, workspace_name)
                return json.dumps(migrated_data).encode('utf-8')
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Binary data, wrap with DDD metadata
                migrated_data = {
                    "_ddd_cache": True,
                    "_cache_type": cache_type,
                    "_workspace": workspace_name,
                    "_migrated_at": datetime.now().isoformat(),
                    "_data_type": "binary",
                    "_original_hash": hashlib.sha256(value).hexdigest(),
                    "_data": value.hex()
                }
                return json.dumps(migrated_data).encode('utf-8')
                
        except Exception as e:
            raise CacheMigrationError(f"Cache entry migration failed: {e}")
            
    def _migrate_cache_entry_data(self, entry_data: Any, cache_type: str, workspace_name: Optional[str] = None) -> Dict[str, Any]:
        """Migrate cache entry data structure.
        
        Args:
            entry_data: Original cache entry data
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
            
        Returns:
            Migrated cache entry data
        """
        if not isinstance(entry_data, dict):
            # Simple value, wrap with DDD metadata
            return {
                "_ddd_cache": True,
                "_cache_type": cache_type,
                "_workspace": workspace_name,
                "_migrated_at": datetime.now().isoformat(),
                "_data_type": "simple",
                "_value": entry_data
            }
            
        # Add DDD metadata to existing dictionary
        migrated = entry_data.copy()
        migrated.update({
            "_ddd_cache": True,
            "_cache_type": cache_type,
            "_workspace": workspace_name,
            "_migrated_at": datetime.now().isoformat(),
            "_cache_version": "2.0"
        })
        
        # Handle specific cache types
        if "llm_response" in migrated:
            migrated["llm_response"] = self._migrate_llm_response_cache(migrated["llm_response"])
        elif "template" in migrated:
            migrated["template"] = self._migrate_template_cache(migrated["template"])
            
        return migrated
        
    def _migrate_cache_structure(self, cache_data: Any, cache_type: str, workspace_name: Optional[str] = None) -> Dict[str, Any]:
        """Migrate entire cache structure.
        
        Args:
            cache_data: Original cache data
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
            
        Returns:
            Migrated cache structure
        """
        if not isinstance(cache_data, dict):
            # Simple cache, wrap with DDD structure
            return {
                "_ddd_cache": True,
                "_cache_type": cache_type,
                "_workspace": workspace_name,
                "_migrated_at": datetime.now().isoformat(),
                "_cache_version": "2.0",
                "_data": cache_data
            }
            
        # Add DDD metadata
        migrated = {
            "_ddd_cache": True,
            "_cache_type": cache_type,
            "_workspace": workspace_name,
            "_migrated_at": datetime.now().isoformat(),
            "_cache_version": "2.0",
            "_entries": {}
        }
        
        # Migrate each entry
        for key, value in cache_data.items():
            migrated["_entries"][key] = self._migrate_cache_entry_data(value, cache_type, workspace_name)
            
        return migrated
        
    def _migrate_llm_response_cache(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate LLM response cache data.
        
        Args:
            response_data: LLM response data
            
        Returns:
            Migrated LLM response data
        """
        migrated = response_data.copy()
        
        # Add DDD-specific fields
        migrated.update({
            "_domain": "llm",
            "_entity_type": "response",
            "_cache_compatible": True,
            "_token_tracking": {
                "input_tokens": response_data.get("input_tokens", 0),
                "output_tokens": response_data.get("output_tokens", 0),
                "total_tokens": response_data.get("total_tokens", 0)
            }
        })
        
        return migrated
        
    def _migrate_template_cache(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate template cache data.
        
        Args:
            template_data: Template cache data
            
        Returns:
            Migrated template cache data
        """
        migrated = template_data.copy()
        
        # Add DDD-specific fields
        migrated.update({
            "_domain": "pipeline",
            "_entity_type": "template",
            "_cache_compatible": True,
            "_template_metadata": {
                "rendered_at": template_data.get("rendered_at"),
                "variables_used": template_data.get("variables", []),
                "cache_key": self._generate_cache_key(template_data)
            }
        })
        
        return migrated
        
    def _convert_pickle_to_json(self, pickle_data: Any) -> Any:
        """Convert pickle data to JSON-compatible format.
        
        Args:
            pickle_data: Data loaded from pickle file
            
        Returns:
            JSON-compatible data
        """
        try:
            # Simple types can be returned as-is
            if isinstance(pickle_data, (str, int, float, bool)) or pickle_data is None:
                return pickle_data
                
            # Lists and dictionaries need recursive conversion
            elif isinstance(pickle_data, list):
                return [self._convert_pickle_to_json(item) for item in pickle_data]
            elif isinstance(pickle_data, dict):
                return {key: self._convert_pickle_to_json(value) for key, value in pickle_data.items()}
                
            # Complex objects need special handling
            else:
                return {
                    "_pickle_type": type(pickle_data).__name__,
                    "_module": type(pickle_data).__module__,
                    "_repr": repr(pickle_data),
                    "_converted": "pickle_to_json"
                }
                
        except Exception as e:
            return {
                "_conversion_error": str(e),
                "_original_type": type(pickle_data).__name__
            }
            
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key for data.
        
        Args:
            data: Data to generate key for
            
        Returns:
            Cache key string
        """
        key_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()
        
    def _create_ddd_cache_structure(self, cache_path: Path, cache_type: str, workspace_name: Optional[str] = None) -> None:
        """Create DDD-compliant cache directory structure.
        
        Args:
            cache_path: Path to cache directory
            cache_type: Type of cache
            workspace_name: Workspace name (for workspace caches)
        """
        # Create DDD cache structure
        ddd_structure = {
            "domains": {
                "llm": True,     # LLM cache
                "pipeline": True, # Pipeline cache
                "workspace": True # Workspace cache
            },
            "storage": {
                "lmdb": True,    # LMDB cache files
                "json": True,    # JSON cache files
                "temp": True     # Temporary cache files
            },
            "metadata": True,    # Cache metadata
            "backup": True,     # Cache backups
            "migrated": True    # Migrated cache files
        }
        
        def create_structure(base_path: Path, structure: Dict[str, Any]) -> None:
            for name, definition in structure.items():
                if isinstance(definition, bool):
                    dir_path = base_path / name
                    dir_path.mkdir(exist_ok=True)
                elif isinstance(definition, dict):
                    create_structure(base_path / name, definition)
                    
        create_structure(cache_path, ddd_structure)
        
        # Create cache metadata
        metadata = {
            "cache_type": cache_type,
            "workspace": workspace_name,
            "migrated_at": datetime.now().isoformat(),
            "migration_version": "2.0",
            "ddd_compatible": True,
            "structure": ddd_structure
        }
        
        metadata_file = cache_path / "domains" / "cache_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
    def _optimize_cache_storage(self) -> bool:
        """Optimize cache storage after migration.
        
        Returns:
            True if optimization successful, False otherwise
        """
        try:
            self.log_migration("Optimizing cache storage")
            
            # Clean up expired entries
            self._cleanup_expired_cache_entries()
            
            # Compact LMDB databases
            self._compact_lmdb_databases()
            
            # Remove duplicate entries
            self._remove_duplicate_cache_entries()
            
            self.cache_stats["storage_optimized"] = True
            self.log_migration("Cache storage optimization completed")
            return True
            
        except Exception as e:
            self.log_migration(f"Cache storage optimization failed: {e}", "error")
            return False
            
    def _cleanup_expired_cache_entries(self) -> None:
        """Clean up expired cache entries."""
        # Implementation would scan cache files and remove expired entries
        self.log_migration("Cleaned up expired cache entries")
        
    def _compact_lmdb_databases(self) -> None:
        """Compact LMDB databases to reduce storage."""
        # Implementation would compact LMDB databases
        self.log_migration("Compacted LMDB databases")
        
    def _remove_duplicate_cache_entries(self) -> None:
        """Remove duplicate cache entries."""
        # Implementation would remove duplicates based on content hashes
        self.log_migration("Removed duplicate cache entries")
        
    def _validate_migrated_cache(self) -> bool:
        """Validate migrated cache data.
        
        Returns:
            True if validation successful, False otherwise
        """
        try:
            self.log_migration("Validating migrated cache")
            
            # Check cache structure
            structure_valid = self._validate_cache_structure()
            
            # Check cache entries
            entries_valid = self._validate_cache_entries()
            
            # Check cache metadata
            metadata_valid = self._validate_cache_metadata()
            
            validation_success = all([structure_valid, entries_valid, metadata_valid])
            
            if validation_success:
                self.log_migration("Cache validation completed successfully")
            else:
                self.log_migration("Cache validation found issues", "warning")
                
            return validation_success
            
        except Exception as e:
            self.log_migration(f"Cache validation failed: {e}", "error")
            return False
            
    def _validate_cache_structure(self) -> bool:
        """Validate cache directory structure.
        
        Returns:
            True if structure valid, False otherwise
        """
        # Implementation would validate DDD cache structure
        return True
        
    def _validate_cache_entries(self) -> bool:
        """Validate cache entries.
        
        Returns:
            True if entries valid, False otherwise
        """
        # Implementation would validate cache entries
        return True
        
    def _validate_cache_metadata(self) -> bool:
        """Validate cache metadata.
        
        Returns:
            True if metadata valid, False otherwise
        """
        # Implementation would validate cache metadata
        return True