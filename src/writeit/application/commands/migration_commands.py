"""Migration commands for WriteIt application layer.

Provides CQRS command pattern for data migration operations, ensuring
proper separation between command execution and query handling.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum


class MigrationType(str, Enum):
    """Types of migration operations."""
    LEGACY_WORKSPACE = "legacy_workspace"      # Migrate legacy .writeit directories
    DATA_FORMAT = "data_format"              # Convert data formats
    CONFIGURATION = "configuration"          # Migrate configuration formats
    CACHE_FORMAT = "cache_format"            # Migrate cache data
    PIPELINE_FORMAT = "pipeline_format"      # Migrate pipeline formats
    WORKSPACE_STRUCTURE = "workspace_structure"  # Migrate workspace structures


class MigrationStatus(str, Enum):
    """Migration operation status."""
    PENDING = "pending"          # Migration ready to start
    IN_PROGRESS = "in_progress"  # Migration in progress
    COMPLETED = "completed"     # Migration completed successfully
    FAILED = "failed"          # Migration failed
    ROLLED_BACK = "rolled_back"  # Migration was rolled back


class MigrationPriority(str, Enum):
    """Migration priority levels."""
    CRITICAL = "critical"      # Must be completed before normal operation
    HIGH = "high"             # Should be completed soon
    NORMAL = "normal"         # Can be completed when convenient
    LOW = "low"              # Optional migration


@dataclass
class DetectLegacyWorkspacesCommand:
    """Command to detect legacy workspaces for migration."""
    search_paths: Optional[List[Path]] = None
    auto_analyze: bool = True


@dataclass
class AnalyzeMigrationRequirementsCommand:
    """Command to analyze what migrations are required."""
    workspace_name: Optional[str] = None
    include_all_workspaces: bool = False
    check_data_formats: bool = True
    check_configurations: bool = True
    check_cache: bool = True


@dataclass
class StartMigrationCommand:
    """Command to start a migration operation."""
    migration_type: MigrationType
    source_path: Optional[Path] = None
    target_workspace: Optional[str] = None
    backup_before: bool = True
    rollback_on_failure: bool = True
    dry_run: bool = False
    force: bool = False


@dataclass
class BulkMigrationCommand:
    """Command to perform multiple migrations."""
    migrations: List[StartMigrationCommand]
    parallel: bool = False
    continue_on_failure: bool = False
    priority: MigrationPriority = MigrationPriority.NORMAL


@dataclass
class ValidateMigrationCommand:
    """Command to validate migration results."""
    migration_id: str
    workspace_name: Optional[str] = None
    deep_validation: bool = False
    compare_with_source: bool = True


@dataclass
class RollbackMigrationCommand:
    """Command to rollback a migration."""
    migration_id: str
    workspace_name: Optional[str] = None
    backup_path: Optional[Path] = None
    force: bool = False


@dataclass
class CleanupMigrationArtifactsCommand:
    """Command to clean up after successful migration."""
    migration_id: str
    remove_backups: bool = False
    remove_legacy_data: bool = False
    workspace_name: Optional[str] = None


@dataclass
class GenerateMigrationReportCommand:
    """Command to generate migration report."""
    migration_id: Optional[str] = None
    workspace_name: Optional[str] = None
    include_details: bool = True
    format: str = "text"  # text, json, html


@dataclass
class ScheduleMigrationCommand:
    """Command to schedule migration for later execution."""
    migration_command: StartMigrationCommand
    scheduled_time: Optional[Any] = None  # datetime
    recurring: bool = False
    recurrence_interval: Optional[str] = None


@dataclass
class CheckMigrationHealthCommand:
    """Command to check migration system health."""
    check_disk_space: bool = True
    check_permissions: bool = True
    check_dependencies: bool = True
    validate_backup_system: bool = True