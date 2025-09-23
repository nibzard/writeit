"""Version compatibility handling for safe serialization.

Provides mechanisms to handle schema version migrations and ensure
backward compatibility when deserializing data from older versions.
"""

import json
from typing import Any, Dict, List, Optional, Callable, Type, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

T = TypeVar('T')


class VersionCompatibilityError(Exception):
    """Version compatibility error."""
    pass


class MigrationStrategy(Enum):
    """Migration strategy types."""
    STRICT = "strict"          # Reject any version mismatch
    BACKWARD = "backward"      # Support backward compatibility only
    FORWARD = "forward"        # Support forward compatibility only
    FLEXIBLE = "flexible"      # Support both backward and forward


@dataclass
class VersionInfo:
    """Version information."""
    major: int
    minor: int
    patch: int
    
    @classmethod
    def from_string(cls, version_str: str) -> 'VersionInfo':
        """Parse version from string.
        
        Args:
            version_str: Version string (e.g., "1.2.3")
            
        Returns:
            VersionInfo instance
            
        Raises:
            ValueError: If version format is invalid
        """
        try:
            parts = version_str.split('.')
            if len(parts) != 3:
                raise ValueError(f"Version must have 3 parts: {version_str}")
            
            major, minor, patch = map(int, parts)
            return cls(major, minor, patch)
        except ValueError as e:
            raise ValueError(f"Invalid version format '{version_str}': {e}") from e
    
    def to_string(self) -> str:
        """Convert to string representation."""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other) -> bool:
        return self < other or self == other
    
    def __gt__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
    
    def __ge__(self, other) -> bool:
        return self > other or self == other
    
    def is_compatible_with(self, other: 'VersionInfo', strategy: MigrationStrategy) -> bool:
        """Check if this version is compatible with another.
        
        Args:
            other: Other version to check compatibility with
            strategy: Migration strategy to use
            
        Returns:
            True if compatible
        """
        if strategy == MigrationStrategy.STRICT:
            return self == other
        elif strategy == MigrationStrategy.BACKWARD:
            # Can read older versions
            return other <= self
        elif strategy == MigrationStrategy.FORWARD:
            # Can read newer versions
            return other >= self
        elif strategy == MigrationStrategy.FLEXIBLE:
            # Compatible within same major version
            return self.major == other.major
        else:
            return False


class DataMigration(ABC):
    """Base class for data migrations."""
    
    @property
    @abstractmethod
    def from_version(self) -> VersionInfo:
        """Source version for this migration."""
        pass
    
    @property
    @abstractmethod
    def to_version(self) -> VersionInfo:
        """Target version for this migration."""
        pass
    
    @abstractmethod
    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data from source to target version.
        
        Args:
            data: Data in source version format
            
        Returns:
            Data in target version format
            
        Raises:
            VersionCompatibilityError: If migration fails
        """
        pass
    
    def can_migrate(self, from_version: VersionInfo, to_version: VersionInfo) -> bool:
        """Check if this migration can handle the version transition.
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            True if this migration applies
        """
        return self.from_version == from_version and self.to_version == to_version


class FieldRenameMigration(DataMigration):
    """Migration that renames fields."""
    
    def __init__(self, from_version: VersionInfo, to_version: VersionInfo, 
                 field_mappings: Dict[str, str]):
        """Initialize field rename migration.
        
        Args:
            from_version: Source version
            to_version: Target version
            field_mappings: Mapping from old field names to new field names
        """
        self._from_version = from_version
        self._to_version = to_version
        self._field_mappings = field_mappings
    
    @property
    def from_version(self) -> VersionInfo:
        return self._from_version
    
    @property
    def to_version(self) -> VersionInfo:
        return self._to_version
    
    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rename fields according to mapping."""
        try:
            migrated = data.copy()
            
            # Rename fields in the data section
            if 'data' in migrated and isinstance(migrated['data'], dict):
                entity_data = migrated['data'].copy()
                
                for old_name, new_name in self._field_mappings.items():
                    if old_name in entity_data:
                        entity_data[new_name] = entity_data.pop(old_name)
                
                migrated['data'] = entity_data
            
            # Update version in metadata
            migrated['__schema_version__'] = self.to_version.to_string()
            
            return migrated
        except Exception as e:
            raise VersionCompatibilityError(
                f"Field rename migration failed from {self.from_version} to {self.to_version}: {e}"
            ) from e


class FieldAddMigration(DataMigration):
    """Migration that adds new fields with default values."""
    
    def __init__(self, from_version: VersionInfo, to_version: VersionInfo,
                 new_fields: Dict[str, Any]):
        """Initialize field add migration.
        
        Args:
            from_version: Source version
            to_version: Target version
            new_fields: New fields with their default values
        """
        self._from_version = from_version
        self._to_version = to_version
        self._new_fields = new_fields
    
    @property
    def from_version(self) -> VersionInfo:
        return self._from_version
    
    @property
    def to_version(self) -> VersionInfo:
        return self._to_version
    
    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new fields with default values."""
        try:
            migrated = data.copy()
            
            # Add fields to the data section
            if 'data' in migrated and isinstance(migrated['data'], dict):
                entity_data = migrated['data'].copy()
                
                for field_name, default_value in self._new_fields.items():
                    if field_name not in entity_data:
                        entity_data[field_name] = default_value
                
                migrated['data'] = entity_data
            
            # Update version in metadata
            migrated['__schema_version__'] = self.to_version.to_string()
            
            return migrated
        except Exception as e:
            raise VersionCompatibilityError(
                f"Field add migration failed from {self.from_version} to {self.to_version}: {e}"
            ) from e


class FieldRemoveMigration(DataMigration):
    """Migration that removes fields."""
    
    def __init__(self, from_version: VersionInfo, to_version: VersionInfo,
                 removed_fields: List[str]):
        """Initialize field remove migration.
        
        Args:
            from_version: Source version
            to_version: Target version
            removed_fields: List of field names to remove
        """
        self._from_version = from_version
        self._to_version = to_version
        self._removed_fields = removed_fields
    
    @property
    def from_version(self) -> VersionInfo:
        return self._from_version
    
    @property
    def to_version(self) -> VersionInfo:
        return self._to_version
    
    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove specified fields."""
        try:
            migrated = data.copy()
            
            # Remove fields from the data section
            if 'data' in migrated and isinstance(migrated['data'], dict):
                entity_data = migrated['data'].copy()
                
                for field_name in self._removed_fields:
                    entity_data.pop(field_name, None)
                
                migrated['data'] = entity_data
            
            # Update version in metadata
            migrated['__schema_version__'] = self.to_version.to_string()
            
            return migrated
        except Exception as e:
            raise VersionCompatibilityError(
                f"Field remove migration failed from {self.from_version} to {self.to_version}: {e}"
            ) from e


class CustomMigration(DataMigration):
    """Custom migration with user-defined logic."""
    
    def __init__(self, from_version: VersionInfo, to_version: VersionInfo,
                 migration_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Initialize custom migration.
        
        Args:
            from_version: Source version
            to_version: Target version
            migration_func: Function to perform the migration
        """
        self._from_version = from_version
        self._to_version = to_version
        self._migration_func = migration_func
    
    @property
    def from_version(self) -> VersionInfo:
        return self._from_version
    
    @property
    def to_version(self) -> VersionInfo:
        return self._to_version
    
    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom migration function."""
        try:
            migrated = self._migration_func(data.copy())
            
            # Ensure version is updated
            if isinstance(migrated, dict):
                migrated['__schema_version__'] = self.to_version.to_string()
            
            return migrated
        except Exception as e:
            raise VersionCompatibilityError(
                f"Custom migration failed from {self.from_version} to {self.to_version}: {e}"
            ) from e


class VersionMigrationManager:
    """Manages version migrations for serialized data."""
    
    def __init__(self, current_version: VersionInfo, 
                 strategy: MigrationStrategy = MigrationStrategy.BACKWARD):
        """Initialize migration manager.
        
        Args:
            current_version: Current schema version
            strategy: Migration strategy to use
        """
        self._current_version = current_version
        self._strategy = strategy
        self._migrations: List[DataMigration] = []
    
    @property
    def current_version(self) -> VersionInfo:
        """Get current schema version."""
        return self._current_version
    
    @property
    def strategy(self) -> MigrationStrategy:
        """Get migration strategy."""
        return self._strategy
    
    def add_migration(self, migration: DataMigration) -> None:
        """Add a data migration.
        
        Args:
            migration: Migration to add
        """
        self._migrations.append(migration)
    
    def can_handle_version(self, version: VersionInfo) -> bool:
        """Check if a version can be handled.
        
        Args:
            version: Version to check
            
        Returns:
            True if version can be handled
        """
        return self._current_version.is_compatible_with(version, self._strategy)
    
    def migrate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data to current version.
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
            
        Raises:
            VersionCompatibilityError: If migration fails or is not supported
        """
        # Extract source version
        source_version_str = data.get('__schema_version__')
        if not source_version_str:
            raise VersionCompatibilityError("No schema version found in data")
        
        try:
            source_version = VersionInfo.from_string(source_version_str)
        except ValueError as e:
            raise VersionCompatibilityError(f"Invalid schema version '{source_version_str}': {e}") from e
        
        # Check if migration is needed
        if source_version == self._current_version:
            return data
        
        # Check if version is compatible
        if not self.can_handle_version(source_version):
            raise VersionCompatibilityError(
                f"Version {source_version} is not compatible with current version {self._current_version} "
                f"using strategy {self._strategy.value}"
            )
        
        # Find migration path
        migration_path = self._find_migration_path(source_version, self._current_version)
        if not migration_path:
            raise VersionCompatibilityError(
                f"No migration path found from {source_version} to {self._current_version}"
            )
        
        # Apply migrations in sequence
        migrated_data = data
        for migration in migration_path:
            migrated_data = migration.migrate(migrated_data)
        
        return migrated_data
    
    def _find_migration_path(self, from_version: VersionInfo, 
                           to_version: VersionInfo) -> Optional[List[DataMigration]]:
        """Find a path of migrations from one version to another.
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of migrations to apply, or None if no path found
        """
        if from_version == to_version:
            return []
        
        # Simple direct migration lookup for now
        # In a more complex scenario, we could implement graph traversal
        for migration in self._migrations:
            if migration.can_migrate(from_version, to_version):
                return [migration]
        
        # Try to find a multi-step path (simplified implementation)
        for migration in self._migrations:
            if migration.from_version == from_version:
                # Try to find a path from the intermediate version
                sub_path = self._find_migration_path(migration.to_version, to_version)
                if sub_path is not None:
                    return [migration] + sub_path
        
        return None
    
    def register_common_migrations(self) -> None:
        """Register common migration patterns."""
        # Example migrations - these would be specific to your domain
        # This is just to show the pattern
        pass


def create_version_manager(current_version_str: str = "1.0.0",
                          strategy: MigrationStrategy = MigrationStrategy.BACKWARD) -> VersionMigrationManager:
    """Create a version migration manager.
    
    Args:
        current_version_str: Current schema version string
        strategy: Migration strategy
        
    Returns:
        Configured version migration manager
    """
    current_version = VersionInfo.from_string(current_version_str)
    return VersionMigrationManager(current_version, strategy)