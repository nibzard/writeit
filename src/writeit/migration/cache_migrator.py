# ABOUTME: Cache migration system for WriteIt
# ABOUTME: Handles migration from legacy cache formats to new secure cache format
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import json
import yaml
import shutil
from dataclasses import dataclass, field
import lmdb

# Cache value objects are not needed for migration


@dataclass
class CacheMigrationResult:
    """Result of a cache migration."""
    
    success: bool
    message: str
    migrated_entries: int = 0
    skipped_entries: int = 0
    failed_entries: int = 0
    pickle_entries: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    old_cache_path: Optional[Path] = None
    new_cache_path: Optional[Path] = None
    backup_path: Optional[Path] = None


@dataclass
class CacheAnalysis:
    """Analysis of legacy cache."""
    
    cache_path: Path
    cache_format: str  # "lmdb", "file", or "unknown"
    total_entries: int = 0
    estimated_size_mb: float = 0.0
    has_pickle_data: bool = False
    pickle_entries: int = 0
    has_expired_entries: bool = False
    expired_entries: int = 0
    cache_age_days: float = 0.0
    migration_complexity: str = "simple"


class CacheFormatDetector:
    """Detects and analyzes legacy cache formats."""
    
    @staticmethod
    def detect_cache_format(cache_path: Path) -> str:
        """Detect cache storage format.
        
        Args:
            cache_path: Path to cache directory or file
            
        Returns:
            Format type: "lmdb", "file", or "unknown"
        """
        if not cache_path.exists():
            return "unknown"
        
        if cache_path.is_file():
            # Check for LMDB files
            if cache_path.suffix in ['.mdb', '.lmdb']:
                return "lmdb"
            return "file"
        
        if cache_path.is_dir():
            # Check for LMDB files in directory
            mdb_files = list(cache_path.glob("*.mdb"))
            if mdb_files:
                return "lmdb"
            
            # Check for file-based cache
            cache_files = list(cache_path.glob("*.cache")) + list(cache_path.glob("*.json"))
            if cache_files:
                return "file"
        
        return "unknown"
    
    @staticmethod
    def analyze_legacy_cache(cache_path: Path) -> CacheAnalysis:
        """Analyze legacy cache storage.
        
        Args:
            cache_path: Path to cache directory or file
            
        Returns:
            Analysis results
        """
        analysis = CacheAnalysis(
            cache_path=cache_path,
            cache_format=CacheFormatDetector.detect_cache_format(cache_path)
        )
        
        if not cache_path.exists():
            return analysis
        
        try:
            if analysis.cache_format == "lmdb":
                analysis = CacheFormatDetector._analyze_lmdb_cache(cache_path, analysis)
            elif analysis.cache_format == "file":
                analysis = CacheFormatDetector._analyze_file_cache(cache_path, analysis)
            
            # Calculate cache age
            analysis.cache_age_days = CacheFormatDetector._calculate_cache_age(cache_path)
            
        except Exception as e:
            analysis.errors = [f"Failed to analyze cache: {str(e)}"]
        
        return analysis
    
    @staticmethod
    def _analyze_lmdb_cache(cache_path: Path, analysis: CacheAnalysis) -> CacheAnalysis:
        """Analyze LMDB cache storage."""
        if cache_path.is_file():
            # Single LMDB file
            mdb_files = [cache_path]
        else:
            # Directory with LMDB files
            mdb_files = list(cache_path.glob("*.mdb"))
        
        for mdb_file in mdb_files:
            try:
                with lmdb.open(str(mdb_file), readonly=True, lock=False) as env:
                    with env.begin() as txn:
                        stats = txn.stat()
                        analysis.total_entries += stats.get("entries", 0)
                        
                        # Check for pickle data
                        cursor = txn.cursor()
                        for key, value in cursor:
                            if value.startswith(b'\x80\x03') or value.startswith(b'\x80\x04'):
                                analysis.has_pickle_data = True
                                analysis.pickle_entries += 1
                                
                                # Check for expiration if stored in value
                                try:
                                    data = json.loads(value.decode('utf-8'))
                                    if 'expires_at' in data:
                                        expires_at = datetime.fromisoformat(data['expires_at'])
                                        if expires_at < datetime.now():
                                            analysis.has_expired_entries = True
                                            analysis.expired_entries += 1
                                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                                    pass
                
                # Estimate size
                analysis.estimated_size_mb += mdb_file.stat().st_size / (1024 * 1024)
                
            except (lmdb.Error, OSError):
                continue
        
        return analysis
    
    @staticmethod
    def _analyze_file_cache(cache_path: Path, analysis: CacheAnalysis) -> CacheAnalysis:
        """Analyze file-based cache storage."""
        cache_files = list(cache_path.glob("*.cache")) + list(cache_path.glob("*.json"))
        
        for cache_file in cache_files:
            try:
                # Count entries and check size
                analysis.total_entries += 1
                analysis.estimated_size_mb += cache_file.stat().st_size / (1024 * 1024)
                
                # Check for pickle data
                with open(cache_file, 'rb') as f:
                    content = f.read(1024)  # Read first 1KB
                    if content.startswith(b'\x80\x03') or content.startswith(b'\x80\x04'):
                        analysis.has_pickle_data = True
                        analysis.pickle_entries += 1
                
                # Check expiration for JSON files
                if cache_file.suffix == '.json':
                    try:
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                            if 'expires_at' in data:
                                expires_at = datetime.fromisoformat(data['expires_at'])
                                if expires_at < datetime.now():
                                    analysis.has_expired_entries = True
                                    analysis.expired_entries += 1
                    except (json.JSONDecodeError, ValueError):
                        pass
                
            except (OSError, UnicodeDecodeError):
                continue
        
        return analysis
    
    @staticmethod
    def _calculate_cache_age(cache_path: Path) -> float:
        """Calculate cache age in days."""
        try:
            if cache_path.is_file():
                mtime = cache_path.stat().st_mtime
            else:
                # For directories, use the oldest file
                mtime = min(f.stat().st_mtime for f in cache_path.rglob('*') if f.is_file())
            
            file_time = datetime.fromtimestamp(mtime)
            age = (datetime.now() - file_time).total_seconds() / (24 * 3600)
            return max(0.0, age)
        except (OSError, ValueError):
            return 0.0


class CacheMigrator:
    """Migrates cache data from legacy to new secure format."""
    
    def __init__(self):
        """Initialize cache migrator."""
        self.detector = CacheFormatDetector()
    
    def migrate_cache(
        self, 
        legacy_cache_path: Path,
        new_cache_path: Path,
        backup: bool = True,
        skip_pickle: bool = True,  # Skip pickle data for security
        cleanup_expired: bool = True,
        dry_run: bool = False
    ) -> CacheMigrationResult:
        """Migrate legacy cache to new secure format.
        
        Args:
            legacy_cache_path: Path to legacy cache
            new_cache_path: Path for new cache
            backup: Whether to create backup
            skip_pickle: Whether to skip pickle data (recommended for security)
            cleanup_expired: Whether to skip expired entries
            dry_run: Whether to only show what would be done
            
        Returns:
            Migration result
        """
        result = CacheMigrationResult(
            old_cache_path=legacy_cache_path,
            new_cache_path=new_cache_path
        )
        
        try:
            # Analyze legacy cache
            analysis = self.detector.analyze_legacy_cache(legacy_cache_path)
            
            if analysis.total_entries == 0:
                result.success = True
                result.message = "No cache entries to migrate"
                return result
            
            # Create backup if requested
            if backup and not dry_run:
                backup_path = self._create_cache_backup(legacy_cache_path)
                result.backup_path = backup_path
                result.warnings.append(f"Backup created at: {backup_path}")
            
            # Create new cache directory
            if not dry_run:
                new_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Migrate based on format
            if analysis.cache_format == "lmdb":
                migration_result = self._migrate_lmdb_cache(
                    legacy_cache_path, new_cache_path, analysis,
                    skip_pickle, cleanup_expired, dry_run
                )
            elif analysis.cache_format == "file":
                migration_result = self._migrate_file_cache(
                    legacy_cache_path, new_cache_path, analysis,
                    skip_pickle, cleanup_expired, dry_run
                )
            else:
                result.success = False
                result.message = f"Unknown cache format: {analysis.cache_format}"
                return result
            
            result.migrated_entries = migration_result.migrated_entries
            result.skipped_entries = migration_result.skipped_entries
            result.failed_entries = migration_result.failed_entries
            result.pickle_entries = migration_result.pickle_entries
            result.warnings.extend(migration_result.warnings)
            result.errors.extend(migration_result.errors)
            
            result.success = result.failed_entries == 0
            result.message = f"Successfully migrated {result.migrated_entries} cache entries" if result.success else \
                           f"Cache migration completed with {result.failed_entries} failures"
            
            if result.pickle_entries > 0 and skip_pickle:
                result.warnings.append(
                    f"Skipped {result.pickle_entries} pickle entries for security reasons"
                )
            
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"Cache migration failed: {str(e)}"
            result.errors.append(str(e))
            return result
    
    def _create_cache_backup(self, cache_path: Path) -> Path:
        """Create backup of cache directory or file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if cache_path.is_file():
            backup_name = f"{cache_path.stem}_cache_backup_{timestamp}{cache_path.suffix}"
            backup_path = cache_path.parent / backup_name
            shutil.copy2(cache_path, backup_path)
        else:
            backup_name = f"cache_backup_{timestamp}"
            backup_path = cache_path.parent / backup_name
            shutil.copytree(cache_path, backup_path)
        
        return backup_path
    
    def _migrate_lmdb_cache(
        self, 
        legacy_path: Path,
        new_path: Path,
        analysis: CacheAnalysis,
        skip_pickle: bool,
        cleanup_expired: bool,
        dry_run: bool
    ) -> CacheMigrationResult:
        """Migrate LMDB cache."""
        result = CacheMigrationResult()
        
        if legacy_path.is_file():
            mdb_files = [legacy_path]
        else:
            mdb_files = list(legacy_path.glob("*.mdb"))
        
        for mdb_file in mdb_files:
            try:
                with lmdb.open(str(mdb_file), readonly=True, lock=False) as env:
                    with env.begin() as txn:
                        cursor = txn.cursor()
                        
                        for key, value in cursor:
                            try:
                                # Check for pickle data
                                if value.startswith(b'\x80\x03') or value.startswith(b'\x80\x04'):
                                    result.pickle_entries += 1
                                    if skip_pickle:
                                        result.skipped_entries += 1
                                        result.warnings.append(
                                            f"Skipped pickle entry: {key.decode('utf-8', errors='ignore')}"
                                        )
                                        continue
                                
                                # Parse and validate cache entry
                                cache_entry = self._parse_cache_entry(key, value)
                                
                                # Check expiration
                                if cleanup_expired and cache_entry.get('expires_at'):
                                    expires_at = datetime.fromisoformat(cache_entry['expires_at'])
                                    if expires_at < datetime.now():
                                        result.skipped_entries += 1
                                        continue
                                
                                # Migrate to new format
                                if not dry_run:
                                    self._store_cache_entry(new_path, cache_entry)
                                
                                result.migrated_entries += 1
                                
                            except Exception as e:
                                result.failed_entries += 1
                                result.errors.append(
                                    f"Failed to migrate entry {key.decode('utf-8', errors='ignore')}: {str(e)}"
                                )
                
            except (lmdb.Error, OSError) as e:
                result.failed_entries += analysis.total_entries
                result.errors.append(f"Failed to read LMDB file {mdb_file}: {str(e)}")
        
        return result
    
    def _migrate_file_cache(
        self,
        legacy_path: Path,
        new_path: Path,
        analysis: CacheAnalysis,
        skip_pickle: bool,
        cleanup_expired: bool,
        dry_run: bool
    ) -> CacheMigrationResult:
        """Migrate file-based cache."""
        result = CacheMigrationResult()
        
        cache_files = list(legacy_path.glob("*.cache")) + list(legacy_path.glob("*.json"))
        
        for cache_file in cache_files:
            try:
                # Read cache file
                with open(cache_file, 'rb') as f:
                    content = f.read()
                
                # Check for pickle data
                if content.startswith(b'\x80\x03') or content.startswith(b'\x80\x04'):
                    result.pickle_entries += 1
                    if skip_pickle:
                        result.skipped_entries += 1
                        result.warnings.append(f"Skipped pickle file: {cache_file.name}")
                        continue
                
                # Parse cache entry
                if cache_file.suffix == '.json':
                    try:
                        cache_entry = json.loads(content.decode('utf-8'))
                    except json.JSONDecodeError:
                        cache_entry = {"content": content.decode('utf-8', errors='ignore')}
                else:
                    cache_entry = {"content": content.decode('utf-8', errors='ignore')}
                
                # Add metadata
                cache_entry["source_file"] = cache_file.name
                cache_entry["migration_timestamp"] = datetime.now().isoformat()
                
                # Check expiration
                if cleanup_expired and cache_entry.get('expires_at'):
                    expires_at = datetime.fromisoformat(cache_entry['expires_at'])
                    if expires_at < datetime.now():
                        result.skipped_entries += 1
                        continue
                
                # Migrate to new format
                if not dry_run:
                    self._store_cache_entry(new_path, cache_entry)
                
                result.migrated_entries += 1
                
            except Exception as e:
                result.failed_entries += 1
                result.errors.append(f"Failed to migrate {cache_file.name}: {str(e)}")
        
        return result
    
    def _parse_cache_entry(self, key: bytes, value: bytes) -> Dict[str, Any]:
        """Parse cache entry from LMDB."""
        cache_entry = {}
        
        try:
            # Try to parse as JSON first
            json_data = json.loads(value.decode('utf-8'))
            if isinstance(json_data, dict):
                cache_entry.update(json_data)
            else:
                cache_entry["content"] = str(json_data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not JSON, treat as raw content
            cache_entry["content"] = value.decode('utf-8', errors='ignore')
        
        # Add key as metadata
        cache_entry["original_key"] = key.decode('utf-8', errors='ignore')
        cache_entry["migration_timestamp"] = datetime.now().isoformat()
        
        return cache_entry
    
    def _store_cache_entry(self, cache_path: Path, cache_entry: Dict[str, Any]) -> None:
        """Store cache entry in new format."""
        # Generate cache key
        cache_key = self._generate_cache_key(cache_entry)
        
        # Create cache file
        cache_file = cache_path / f"{cache_key}.json"
        
        # Add metadata
        cache_entry["format_version"] = "2.0"
        cache_entry["migrated"] = True
        
        # Store as JSON
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_entry, f, indent=2, ensure_ascii=False)
    
    def _generate_cache_key(self, cache_entry: Dict[str, Any]) -> str:
        """Generate unique cache key for entry."""
        import hashlib
        
        # Use original key if available
        if "original_key" in cache_entry:
            key_base = cache_entry["original_key"]
        elif "content" in cache_entry:
            key_base = cache_entry["content"][:100]  # Use first 100 chars of content
        else:
            key_base = str(cache_entry.get("migration_timestamp", ""))
        
        # Generate hash to ensure valid filename
        key_hash = hashlib.md5(key_base.encode('utf-8')).hexdigest()
        timestamp = int(datetime.now().timestamp())
        
        return f"cache_{timestamp}_{key_hash[:16]}"


class CacheMigrationManager:
    """High-level cache migration manager."""
    
    def __init__(self):
        """Initialize cache migration manager."""
        self.migrator = CacheMigrator()
        self.detector = CacheFormatDetector()
    
    def migrate_workspace_cache(
        self,
        workspace_path: Path,
        backup: bool = True,
        skip_pickle: bool = True,
        cleanup_expired: bool = True,
        dry_run: bool = False
    ) -> List[CacheMigrationResult]:
        """Migrate cache for a workspace.
        
        Args:
            workspace_path: Path to workspace directory
            backup: Whether to create backups
            skip_pickle: Whether to skip pickle data
            cleanup_expired: Whether to skip expired entries
            dry_run: Whether to only show what would be done
            
        Returns:
            List of migration results
        """
        results = []
        
        # Look for legacy cache locations
        cache_locations = [
            workspace_path / ".writeit" / "cache",
            workspace_path / "cache",
            workspace_path / ".cache",
        ]
        
        # Also look for LMDB files in workspace
        cache_locations.extend([
            workspace_path / ".writeit" / "cache.mdb",
            workspace_path / ".writeit" / "cache.lmdb",
            workspace_path / "cache.mdb",
            workspace_path / "cache.lmdb",
        ])
        
        new_cache_path = workspace_path / "cache"
        
        for cache_location in cache_locations:
            if cache_location.exists():
                result = self.migrator.migrate_cache(
                    cache_location,
                    new_cache_path,
                    backup=backup,
                    skip_pickle=skip_pickle,
                    cleanup_expired=cleanup_expired,
                    dry_run=dry_run
                )
                results.append(result)
        
        return results
    
    def analyze_cache_migration_needs(self, workspace_path: Path) -> List[CacheAnalysis]:
        """Analyze cache migration needs for a workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            List of cache analyses
        """
        analyses = []
        
        cache_locations = [
            workspace_path / ".writeit" / "cache",
            workspace_path / "cache",
            workspace_path / ".cache",
            workspace_path / ".writeit" / "cache.mdb",
            workspace_path / ".writeit" / "cache.lmdb",
            workspace_path / "cache.mdb",
            workspace_path / "cache.lmdb",
        ]
        
        for cache_location in cache_locations:
            if cache_location.exists():
                analysis = self.detector.analyze_legacy_cache(cache_location)
                analyses.append(analysis)
        
        return analyses
    
    def cleanup_legacy_cache(self, workspace_path: Path, force: bool = False) -> List[str]:
        """Clean up legacy cache files after successful migration.
        
        Args:
            workspace_path: Path to workspace directory
            force: Whether to force cleanup without confirmation
            
        Returns:
            List of cleaned up paths
        """
        cleaned_paths = []
        
        legacy_cache_locations = [
            workspace_path / ".writeit" / "cache",
            workspace_path / ".cache",
            workspace_path / ".writeit" / "cache.mdb",
            workspace_path / ".writeit" / "cache.lmdb",
        ]
        
        for cache_location in legacy_cache_locations:
            if cache_location.exists():
                if force:
                    if cache_location.is_file():
                        cache_location.unlink()
                    else:
                        shutil.rmtree(cache_location)
                    cleaned_paths.append(str(cache_location))
                else:
                    # Would implement interactive confirmation here
                    pass
        
        return cleaned_paths


def create_cache_migration_manager() -> CacheMigrationManager:
    """Create cache migration manager instance."""
    return CacheMigrationManager()