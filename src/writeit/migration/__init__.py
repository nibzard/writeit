# ABOUTME: Migration module for WriteIt data transformation
# ABOUTME: Provides comprehensive data migration from legacy formats to DDD entities

from .data_migrator import (
    MigrationManager,
    MigrationResult,
    DataFormatDetector,
    WorkspaceDataMigrator,
    create_migration_manager
)

from .config_migrator import (
    ConfigMigrationManager,
    ConfigMigrationResult,
    LegacyConfigAnalysis
)

from .cache_migrator import (
    CacheMigrationManager,
    CacheMigrationResult,
    CacheAnalysis
)

from .rollback_manager import (
    MigrationRollbackManager,
    RollbackResult,
    MigrationBackup
)

from .data_migration import (
    DataMigrator,
    DataMigrationError
)

from .legacy_format_converter import (
    LegacyFormatConverter
)

from .migration_runner import (
    MigrationRunner
)

from .integrated_migration import (
    IntegratedMigration,
    IntegratedMigrationError
)

__all__ = [
    "MigrationManager",
    "MigrationResult",
    "DataFormatDetector",
    "WorkspaceDataMigrator",
    "create_migration_manager",
    "ConfigMigrationManager",
    "ConfigMigrationResult",
    "LegacyConfigAnalysis", 
    "CacheMigrationManager",
    "CacheMigrationResult",
    "CacheAnalysis",
    "MigrationRollbackManager",
    "RollbackResult",
    "MigrationBackup",
    "DataMigrator",
    "DataMigrationError",
    "LegacyFormatConverter",
    "MigrationRunner",
    "IntegratedMigration",
    "IntegratedMigrationError"
]