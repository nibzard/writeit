"""Migration queries for WriteIt application layer.

Provides CQRS query pattern for migration-related operations, ensuring
proper separation between read operations and command execution.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum
from datetime import datetime


class MigrationFilter(str, Enum):
    """Filter options for migration queries."""
    ALL = "all"                    # All migrations
    PENDING = "pending"           # Pending migrations
    IN_PROGRESS = "in_progress"   # Active migrations
    COMPLETED = "completed"       # Successful migrations
    FAILED = "failed"            # Failed migrations
    ROLLED_BACK = "rolled_back"   # Rolled back migrations


class MigrationSort(str, Enum):
    """Sort options for migration queries."""
    CREATED_ASC = "created_asc"      # Oldest first
    CREATED_DESC = "created_desc"    # Newest first
    MODIFIED_ASC = "modified_asc"    # Last modified oldest first
    MODIFIED_DESC = "modified_desc"  # Last modified newest first
    PRIORITY_ASC = "priority_asc"    # Lowest priority first
    PRIORITY_DESC = "priority_desc"  # Highest priority first


@dataclass
class GetMigrationStatusQuery:
    """Query to get status of migrations."""
    workspace_name: Optional[str] = None
    migration_type: Optional[str] = None
    status_filter: MigrationFilter = MigrationFilter.ALL
    sort_by: MigrationSort = MigrationSort.CREATED_DESC
    limit: Optional[int] = None


@dataclass
class GetMigrationDetailsQuery:
    """Query to get detailed information about a specific migration."""
    migration_id: str
    include_logs: bool = True
    include_metrics: bool = True
    include_validation_results: bool = True


@dataclass
class GetMigrationHistoryQuery:
    """Query to get migration history."""
    workspace_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    migration_types: Optional[List[str]] = None
    include_failed: bool = True
    limit: Optional[int] = 100


@dataclass
class GetMigrationStatsQuery:
    """Query to get migration statistics."""
    workspace_name: Optional[str] = None
    include_all_workspaces: bool = False
    time_period: Optional[str] = None  # day, week, month, year, all


@dataclass
class GetLegacyWorkspacesQuery:
    """Query to find legacy workspaces."""
    search_paths: Optional[List[Path]] = None
    recursive: bool = True
    include_analysis: bool = True


@dataclass
class GetMigrationRequirementsQuery:
    """Query to get migration requirements."""
    workspace_name: Optional[str] = None
    check_data_formats: bool = True
    check_configurations: bool = True
    check_cache: bool = True
    check_workspace_structure: bool = True


@dataclass
class GetMigrationBackupsQuery:
    """Query to get migration backup information."""
    workspace_name: Optional[str] = None
    migration_id: Optional[str] = None
    include_size_info: bool = True
    include_creation_date: bool = True


@dataclass
class GetMigrationHealthQuery:
    """Query to get migration system health status."""
    include_disk_space: bool = True
    include_permissions: bool = True
    include_dependencies: bool = True
    include_backup_system: bool = True


@dataclass
class GetScheduledMigrationsQuery:
    """Query to get scheduled migrations."""
    workspace_name: Optional[str] = None
    include_pending: bool = True
    include_completed: bool = False
    limit: Optional[int] = None


@dataclass
class GetMigrationValidationResultsQuery:
    """Query to get migration validation results."""
    migration_id: str
    workspace_name: Optional[str] = None
    include_detailed_issues: bool = True


@dataclass
class GetMigrationImpactQuery:
    """Query to estimate migration impact."""
    migration_type: str
    workspace_name: Optional[str] = None
    source_path: Optional[Path] = None
    include_disk_usage: bool = True
    include_time_estimate: bool = True


@dataclass
class SearchMigrationsQuery:
    """Query to search migrations by various criteria."""
    search_term: str
    search_in: List[str]  # id, type, status, workspace, description
    workspace_name: Optional[str] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    status_filter: Optional[MigrationFilter] = None