# ABOUTME: Cache format migration utilities for WriteIt DDD refactoring
# ABOUTME: Handles migration from legacy cache formats to new secure cache format with workspace isolation
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import shutil
from dataclasses import dataclass, field
import lmdb

from writeit.migration.cache_migrator import CacheMigrationManager, CacheMigrationResult


@dataclass
class CacheFormatUpdateResult:
    """Result of cache format update."""
    
    success: bool
    message: str
    updated_entries: int = 0
    skipped_entries: int = 0
    failed_entries: int = 0
    cleaned_entries: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    backup_path: Optional[Path] = None


class CacheFormatUpdater:
    """Updates cache formats to new secure DDD-compatible format."""
    
    def __init__(self, cache_migration_manager: CacheMigrationManager):
        """Initialize cache format updater.
        
        Args:
            cache_migration_manager: Cache migration manager instance
        """
        self.cache_manager = cache_migration_manager
        self.update_log = []
    
    def log_update(self, message: str, level: str = "info") -> None:
        """Log cache format update activity."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.update_log.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
    
    def get_update_log(self) -> List[Dict[str, Any]]:
        """Get update log.
        
        Returns:
            List of update log entries
        """
        return self.update_log
    
    def update_cache_format(
        self,
        workspace_path: Path,
        backup: bool = True,
        skip_pickle: bool = True,
        cleanup_expired: bool = True,
        dry_run: bool = False
    ) -> CacheFormatUpdateResult:
        """Update cache format to new DDD-compatible format.
        
        Args:
            workspace_path: Path to workspace directory
            backup: Whether to create backup
            skip_pickle: Whether to skip pickle data for security
            cleanup_expired: Whether to clean up expired entries
            dry_run: Whether to only show what would be done
            
        Returns:
            Update result
        """
        result = CacheFormatUpdateResult(
            success=False,
            message="Cache format update"
        )
        
        try:
            self.log_update(f"Starting cache format update for: {workspace_path}")
            
            # Use cache migration manager to migrate cache
            migration_results = self.cache_manager.migrate_workspace_cache(
                workspace_path=workspace_path,
                backup=backup,
                skip_pickle=skip_pickle,
                cleanup_expired=cleanup_expired,
                dry_run=dry_run
            )
            
            if not migration_results:
                result.success = True
                result.message = "No cache found to migrate"
                return result
            
            # Aggregate results
            for migration_result in migration_results:
                result.updated_entries += migration_result.migrated_entries
                result.skipped_entries += migration_result.skipped_entries
                result.failed_entries += migration_result.failed_entries
                result.warnings.extend(migration_result.warnings)
                result.errors.extend(migration_result.errors)
                
                if migration_result.backup_path:
                    result.backup_path = migration_result.backup_path
                
                result.cleaned_entries += migration_result.migrated_entries
            
            # Apply DDD-specific cache format updates
            if not dry_run and result.updated_entries > 0:
                ddd_update_result = self._apply_ddd_cache_format_updates(workspace_path)
                result.updated_entries += ddd_update_result.updated_entries
                result.warnings.extend(ddd_update_result.warnings)
                result.errors.extend(ddd_update_result.errors)
            
            # Clean up legacy cache if successful
            if not dry_run and result.success:
                cleanup_result = self._cleanup_legacy_cache(workspace_path)
                result.cleaned_entries += cleanup_result
            
            result.success = len(result.errors) == 0
            result.message = (
                f"Successfully updated cache format: {result.updated_entries} entries updated" 
                if result.success else
                f"Cache format update completed with {len(result.errors)} errors"
            )
            
            if result.skipped_entries > 0:
                result.warnings.append(f"Skipped {result.skipped_entries} entries (pickle data)")
            
            if result.cleaned_entries > 0:
                result.warnings.append(f"Cleaned up {result.cleaned_entries} legacy cache entries")
            
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"Cache format update failed: {str(e)}"
            result.errors.append(str(e))
            return result
    
    def _apply_ddd_cache_format_updates(self, workspace_path: Path) -> CacheFormatUpdateResult:
        """Apply DDD-specific cache format updates.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            DDD update result
        """
        result = CacheFormatUpdateResult(success=True, message="DDD cache format updates")
        
        try:
            # Update cache metadata for workspace isolation
            cache_dir = workspace_path / "cache"
            if not cache_dir.exists():
                return result
            
            # Update cache entries with DDD metadata
            cache_files = list(cache_dir.glob("*.json"))
            updated_count = 0
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # Add DDD-specific metadata
                    if isinstance(cache_data, dict):
                        cache_data.update({
                            "workspace_isolated": True,
                            "workspace_name": workspace_path.name,
                            "cache_version": "2.0",
                            "ddd_compatible": True,
                            "updated_at": datetime.now().isoformat(),
                            "domain_separated": True
                        })
                        
                        # Add workspace-specific cache keys
                        if "cache_key" in cache_data:
                            cache_data["workspace_cache_key"] = f"{workspace_path.name}:{cache_data['cache_key']}"
                        
                        # Update LLM cache entries with domain context
                        if cache_data.get("type") == "llm_response":
                            cache_data.update({
                                "domain": "llm",
                                "workspace_context": True,
                                "isolated": True
                            })
                        
                        # Update pipeline cache entries
                        elif cache_data.get("type") == "pipeline":
                            cache_data.update({
                                "domain": "pipeline",
                                "workspace_context": True,
                                "domain_separated": True
                            })
                        
                        # Write updated cache entry
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, indent=2, ensure_ascii=False)
                        
                        updated_count += 1
                
                except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
                    result.warnings.append(f"Failed to update cache file {cache_file.name}: {str(e)}")
                    continue
            
            result.updated_entries = updated_count
            self.log_update(f"Applied DDD format updates to {updated_count} cache entries")
            
            # Create cache metadata file
            cache_metadata = {
                "workspace": workspace_path.name,
                "cache_version": "2.0",
                "ddd_compatible": True,
                "workspace_isolated": True,
                "domain_separated": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_entries": updated_count,
                "cache_structure": {
                    "llm": "cache/llm/",
                    "pipeline": "cache/pipeline/",
                    "workspace": "cache/workspace/",
                    "temp": "cache/temp/"
                }
            }
            
            metadata_file = cache_dir / "cache_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(cache_metadata, f, indent=2, ensure_ascii=False)
            
            self.log_update(f"Created cache metadata: {metadata_file}")
            
            # Create domain-specific cache directories
            domain_dirs = [
                cache_dir / "llm",
                cache_dir / "pipeline", 
                cache_dir / "workspace",
                cache_dir / "temp"
            ]
            
            for domain_dir in domain_dirs:
                domain_dir.mkdir(exist_ok=True)
                
                # Create domain-specific metadata
                domain_metadata = {
                    "domain": domain_dir.name,
                    "workspace": workspace_path.name,
                    "isolation_level": "workspace",
                    "created_at": datetime.now().isoformat()
                }
                
                domain_meta_file = domain_dir / "domain_metadata.json"
                with open(domain_meta_file, 'w', encoding='utf-8') as f:
                    json.dump(domain_metadata, f, indent=2, ensure_ascii=False)
            
            self.log_update("Created domain-specific cache directories")
            
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"DDD cache format update failed: {str(e)}")
            return result
    
    def _cleanup_legacy_cache(self, workspace_path: Path) -> int:
        """Clean up legacy cache files and directories.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Number of cleaned up items
        """
        cleaned_count = 0
        
        try:
            legacy_cache_paths = [
                workspace_path / ".writeit" / "cache",
                workspace_path / ".cache",
                workspace_path / ".writeit" / "cache.mdb",
                workspace_path / ".writeit" / "cache.lmdb",
                workspace_path / "cache.mdb",
                workspace_path / "cache.lmdb"
            ]
            
            for legacy_path in legacy_cache_paths:
                if legacy_path.exists():
                    try:
                        if legacy_path.is_file():
                            legacy_path.unlink()
                            cleaned_count += 1
                            self.log_update(f"Removed legacy cache file: {legacy_path.name}")
                        elif legacy_path.is_dir():
                            shutil.rmtree(legacy_path)
                            cleaned_count += 1
                            self.log_update(f"Removed legacy cache directory: {legacy_path.name}")
                    except OSError as e:
                        self.log_update(f"Could not remove legacy cache {legacy_path}: {str(e)}", "warning")
            
            return cleaned_count
            
        except Exception as e:
            self.log_update(f"Legacy cache cleanup failed: {str(e)}", "warning")
            return 0
    
    def validate_cache_format(self, workspace_path: Path) -> List[str]:
        """Validate that cache format has been properly updated.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            cache_dir = workspace_path / "cache"
            
            if not cache_dir.exists():
                issues.append("Cache directory does not exist")
                return issues
            
            # Check for cache metadata
            metadata_file = cache_dir / "cache_metadata.json"
            if not metadata_file.exists():
                issues.append("Cache metadata file missing")
            else:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    if not metadata.get("ddd_compatible"):
                        issues.append("Cache not marked as DDD compatible")
                    
                    if metadata.get("cache_version") != "2.0":
                        issues.append("Cache version not updated")
                    
                    if not metadata.get("workspace_isolated"):
                        issues.append("Cache not marked as workspace isolated")
                    
                except Exception as e:
                    issues.append(f"Cannot read cache metadata: {e}")
            
            # Check domain directories
            domain_dirs = ["llm", "pipeline", "workspace", "temp"]
            for domain_dir in domain_dirs:
                dir_path = cache_dir / domain_dir
                if not dir_path.exists():
                    issues.append(f"Missing domain cache directory: {domain_dir}")
                else:
                    # Check domain metadata
                    domain_meta_file = dir_path / "domain_metadata.json"
                    if not domain_meta_file.exists():
                        issues.append(f"Missing domain metadata: {domain_dir}")
            
            # Check cache entries for DDD format
            cache_files = list(cache_dir.glob("*.json"))
            for cache_file in cache_files:
                if cache_file.name == "cache_metadata.json":
                    continue
                    
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    if isinstance(cache_data, dict):
                        if not cache_data.get("workspace_isolated"):
                            issues.append(f"Cache entry not workspace isolated: {cache_file.name}")
                        
                        if cache_data.get("cache_version") != "2.0":
                            issues.append(f"Cache entry version not updated: {cache_file.name}")
                
                except Exception:
                    # Skip invalid cache files
                    continue
            
            return issues
            
        except Exception as e:
            issues.append(f"Cache validation error: {e}")
            return issues
    
    def rollback_cache_format_update(self, workspace_path: Path) -> bool:
        """Rollback cache format update.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Find backup files
            cache_dir = workspace_path / "cache"
            backup_pattern = f"{cache_dir}/*_backup_*"
            backup_files = list(cache_dir.parent.glob(backup_pattern))
            
            if not backup_files:
                self.log_update("No cache backup found for rollback", "error")
                return False
            
            # Use most recent backup
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            
            self.log_update(f"Rolling back cache update using backup: {latest_backup}")
            
            # Remove current cache directory
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            
            # Restore from backup
            shutil.copytree(latest_backup, cache_dir)
            
            self.log_update("Successfully rolled back cache format update")
            return True
            
        except Exception as e:
            self.log_update(f"Cache rollback failed: {str(e)}", "error")
            return False


def create_cache_format_updater(cache_migration_manager: CacheMigrationManager) -> CacheFormatUpdater:
    """Create cache format updater instance.
    
    Args:
        cache_migration_manager: Cache migration manager instance
        
    Returns:
        CacheFormatUpdater instance
    """
    return CacheFormatUpdater(cache_migration_manager)