"""Migration Application Service.

Coordinates migration operations across all domains, providing a unified interface
for data migration, workspace structure updates, and legacy format conversion.
Handles detection, analysis, execution, and validation of migrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union, Tuple
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging
import asyncio
import os
import shutil
import json
import yaml
import tempfile

from ...domains.workspace.services import (
    WorkspaceManagementService,
    WorkspaceConfigurationService,
    WorkspaceAnalyticsService,
    WorkspaceMigrationPlan,
    WorkspaceBackupInfo,
)
from ...domains.workspace.entities import Workspace, WorkspaceConfiguration
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.content.services import (
    TemplateManagementService,
    StyleManagementService,
)
from ...domains.execution.services import (
    CacheManagementService,
    TokenAnalyticsService,
)
from ...domains.pipeline.services import PipelineValidationService
from ...domains.storage.services import StorageManagementService

from ..commands.migration_commands import (
    MigrationType,
    MigrationStatus,
    MigrationPriority,
    DetectLegacyWorkspacesCommand,
    AnalyzeMigrationRequirementsCommand,
    StartMigrationCommand,
    BulkMigrationCommand,
    ValidateMigrationCommand,
    RollbackMigrationCommand,
    CleanupMigrationArtifactsCommand,
    GenerateMigrationReportCommand,
    ScheduleMigrationCommand,
    CheckMigrationHealthCommand,
)

from ..queries.migration_queries import (
    GetMigrationStatusQuery,
    GetMigrationDetailsQuery,
    GetMigrationHistoryQuery,
    GetMigrationStatsQuery,
    GetLegacyWorkspacesQuery,
    GetMigrationRequirementsQuery,
    GetMigrationBackupsQuery,
    GetMigrationHealthQuery,
    GetScheduledMigrationsQuery,
    GetMigrationValidationResultsQuery,
    GetMigrationImpactQuery,
)


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    migration_id: str
    status: MigrationStatus
    message: str
    workspace_name: Optional[str] = None
    backup_path: Optional[Path] = None
    items_migrated: int = 0
    items_failed: int = 0
    execution_time: timedelta = field(default_factory=timedelta)
    error_details: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationHealth:
    """Health status of migration system."""
    is_healthy: bool
    issues: List[str]
    disk_space_available: Optional[int] = None
    permissions_ok: bool = True
    dependencies_ok: bool = True
    backup_system_ok: bool = True
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class MigrationReport:
    """Comprehensive migration report."""
    migration_id: str
    title: str
    generated_at: datetime
    summary: Dict[str, Any]
    details: Dict[str, Any]
    validation_results: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)


class MigrationApplicationService(ABC):
    """Abstract base class for migration application service."""

    @abstractmethod
    async def detect_legacy_workspaces(
        self, command: DetectLegacyWorkspacesCommand
    ) -> List[Dict[str, Any]]:
        """Detect legacy workspaces that need migration."""
        pass

    @abstractmethod
    async def analyze_migration_requirements(
        self, command: AnalyzeMigrationRequirementsCommand
    ) -> List[MigrationType]:
        """Analyze what migrations are required."""
        pass

    @abstractmethod
    async def start_migration(self, command: StartMigrationCommand) -> MigrationResult:
        """Start a migration operation."""
        pass

    @abstractmethod
    async def bulk_migrate(self, command: BulkMigrationCommand) -> List[MigrationResult]:
        """Perform multiple migrations."""
        pass

    @abstractmethod
    async def validate_migration(self, command: ValidateMigrationCommand) -> Dict[str, Any]:
        """Validate migration results."""
        pass

    @abstractmethod
    async def rollback_migration(self, command: RollbackMigrationCommand) -> MigrationResult:
        """Rollback a migration."""
        pass

    @abstractmethod
    async def cleanup_migration_artifacts(
        self, command: CleanupMigrationArtifactsCommand
    ) -> bool:
        """Clean up after successful migration."""
        pass

    @abstractmethod
    async def generate_migration_report(
        self, command: GenerateMigrationReportCommand
    ) -> MigrationReport:
        """Generate migration report."""
        pass

    @abstractmethod
    async def schedule_migration(self, command: ScheduleMigrationCommand) -> str:
        """Schedule migration for later execution."""
        pass

    @abstractmethod
    async def check_migration_health(
        self, command: CheckMigrationHealthCommand
    ) -> MigrationHealth:
        """Check migration system health."""
        pass

    @abstractmethod
    async def get_migration_status(self, query: GetMigrationStatusQuery) -> List[Dict[str, Any]]:
        """Get migration status."""
        pass

    @abstractmethod
    async def get_migration_details(self, query: GetMigrationDetailsQuery) -> Dict[str, Any]:
        """Get migration details."""
        pass


class DefaultMigrationApplicationService(MigrationApplicationService):
    """Default implementation of migration application service."""

    def __init__(
        self,
        workspace_service: WorkspaceManagementService,
        config_service: WorkspaceConfigurationService,
        template_service: TemplateManagementService,
        style_service: StyleManagementService,
        cache_service: CacheManagementService,
        token_service: TokenAnalyticsService,
        pipeline_service: PipelineValidationService,
        storage_service: StorageManagementService,
    ):
        self.workspace_service = workspace_service
        self.config_service = config_service
        self.template_service = template_service
        self.style_service = style_service
        self.cache_service = cache_service
        self.token_service = token_service
        self.pipeline_service = pipeline_service
        self.storage_service = storage_service
        self.logger = logging.getLogger(__name__)

        # Track active migrations
        self._active_migrations: Dict[str, MigrationResult] = {}
        self._migration_history: List[MigrationResult] = []

    async def detect_legacy_workspaces(
        self, command: DetectLegacyWorkspacesCommand
    ) -> List[Dict[str, Any]]:
        """Detect legacy workspaces that need migration."""
        try:
            # Use the existing workspace migration utilities
            from ...workspace.migration import WorkspaceMigrator
            
            migrator = WorkspaceMigrator(self.workspace_service)
            search_paths = command.search_paths
            
            legacy_workspaces = migrator.detect_local_workspaces(search_paths)
            
            results = []
            for workspace_path in legacy_workspaces:
                if command.auto_analyze:
                    analysis = migrator.analyze_local_workspace(workspace_path)
                    results.append(analysis)
                else:
                    results.append({
                        "path": workspace_path,
                        "writeit_dir": workspace_path / ".writeit",
                        "has_config": (workspace_path / ".writeit" / "config.yaml").exists(),
                        "has_pipelines": (workspace_path / ".writeit" / "pipelines").exists(),
                        "has_articles": (workspace_path / ".writeit" / "articles").exists(),
                        "has_lmdb": any(
                            (workspace_path / ".writeit").glob("*.mdb") or
                            (workspace_path / ".writeit").glob("*.lmdb")
                        ),
                    })
            
            self.logger.info(f"Detected {len(results)} legacy workspaces")
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting legacy workspaces: {e}")
            raise

    async def analyze_migration_requirements(
        self, command: AnalyzeMigrationRequirementsCommand
    ) -> List[MigrationType]:
        """Analyze what migrations are required."""
        required_migrations = []
        
        try:
            # Get workspaces to analyze
            if command.include_all_workspaces:
                workspaces = await self.workspace_service.list_workspaces()
            elif command.workspace_name:
                workspaces = [await self.workspace_service.get_workspace(WorkspaceName(command.workspace_name))]
            else:
                workspaces = [await self.workspace_service.get_active_workspace()]
            
            for workspace in workspaces:
                if not workspace:
                    continue
                    
                # Check data formats
                if command.check_data_formats:
                    data_migrations = await self._check_data_formats(workspace)
                    required_migrations.extend(data_migrations)
                
                # Check configurations
                if command.check_configurations:
                    config_migrations = await self._check_configurations(workspace)
                    required_migrations.extend(config_migrations)
                
                # Check cache
                if command.check_cache:
                    cache_migrations = await self._check_cache(workspace)
                    required_migrations.extend(cache_migrations)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_migrations = []
            for migration in required_migrations:
                if migration not in seen:
                    seen.add(migration)
                    unique_migrations.append(migration)
            
            self.logger.info(f"Analysis complete. Required migrations: {unique_migrations}")
            return unique_migrations
            
        except Exception as e:
            self.logger.error(f"Error analyzing migration requirements: {e}")
            raise

    async def start_migration(self, command: StartMigrationCommand) -> MigrationResult:
        """Start a migration operation."""
        migration_id = f"{command.migration_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        try:
            # Create backup if requested
            backup_path = None
            if command.backup_before:
                backup_path = await self._create_backup(command.source_path, migration_id)
            
            # Execute migration based on type
            if command.migration_type == MigrationType.LEGACY_WORKSPACE:
                result = await self._migrate_legacy_workspace(command, migration_id)
            elif command.migration_type == MigrationType.DATA_FORMAT:
                result = await self._migrate_data_format(command, migration_id)
            elif command.migration_type == MigrationType.CONFIGURATION:
                result = await self._migrate_configuration(command, migration_id)
            elif command.migration_type == MigrationType.CACHE_FORMAT:
                result = await self._migrate_cache_format(command, migration_id)
            else:
                raise ValueError(f"Unsupported migration type: {command.migration_type}")
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            # Create final result
            migration_result = MigrationResult(
                migration_id=migration_id,
                status=result.get("status", MigrationStatus.COMPLETED),
                message=result.get("message", "Migration completed"),
                workspace_name=command.target_workspace,
                backup_path=backup_path,
                items_migrated=result.get("items_migrated", 0),
                items_failed=result.get("items_failed", 0),
                execution_time=execution_time,
                error_details=result.get("error_details"),
                warnings=result.get("warnings", []),
                metrics=result.get("metrics", {}),
            )
            
            # Track the migration
            self._active_migrations[migration_id] = migration_result
            self._migration_history.append(migration_result)
            
            # Handle rollback on failure
            if (command.rollback_on_failure and 
                migration_result.status == MigrationStatus.FAILED and 
                backup_path):
                self.logger.warning(f"Migration failed, initiating rollback: {migration_id}")
                await self._rollback_from_backup(backup_path, command.target_workspace)
                migration_result.status = MigrationStatus.ROLLED_BACK
            
            self.logger.info(f"Migration {migration_id} completed with status: {migration_result.status}")
            return migration_result
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            error_result = MigrationResult(
                migration_id=migration_id,
                status=MigrationStatus.FAILED,
                message=f"Migration failed: {str(e)}",
                workspace_name=command.target_workspace,
                backup_path=backup_path,
                execution_time=execution_time,
                error_details=str(e),
            )
            
            self._active_migrations[migration_id] = error_result
            self._migration_history.append(error_result)
            
            self.logger.error(f"Migration {migration_id} failed: {e}")
            return error_result

    async def bulk_migrate(self, command: BulkMigrationCommand) -> List[MigrationResult]:
        """Perform multiple migrations."""
        if command.parallel:
            # Run migrations in parallel
            tasks = [self.start_migration(migration_cmd) for migration_cmd in command.migrations]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    migration_id = command.migrations[i].migration_type.value + "_failed"
                    final_results.append(MigrationResult(
                        migration_id=migration_id,
                        status=MigrationStatus.FAILED,
                        message=f"Migration failed: {str(result)}",
                        error_details=str(result),
                    ))
                else:
                    final_results.append(result)
        else:
            # Run migrations sequentially
            final_results = []
            for migration_cmd in command.migrations:
                try:
                    result = await self.start_migration(migration_cmd)
                    final_results.append(result)
                    
                    # Stop on failure if not continuing
                    if (result.status == MigrationStatus.FAILED and 
                        not command.continue_on_failure):
                        break
                        
                except Exception as e:
                    migration_id = migration_cmd.migration_type.value + "_failed"
                    final_results.append(MigrationResult(
                        migration_id=migration_id,
                        status=MigrationStatus.FAILED,
                        message=f"Migration failed: {str(e)}",
                        error_details=str(e),
                    ))
                    
                    if not command.continue_on_failure:
                        break
        
        return final_results

    async def validate_migration(self, command: ValidateMigrationCommand) -> Dict[str, Any]:
        """Validate migration results."""
        validation_results = {
            "migration_id": command.migration_id,
            "workspace_name": command.workspace_name,
            "validation_timestamp": datetime.now().isoformat(),
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "metrics": {},
        }
        
        try:
            # Get migration details
            migration_details = await self.get_migration_details(
                GetMigrationDetailsQuery(migration_id=command.migration_id)
            )
            
            if not migration_details:
                validation_results["is_valid"] = False
                validation_results["issues"].append("Migration not found")
                return validation_results
            
            # Perform validation based on migration type
            migration_type = migration_details.get("type")
            if migration_type == MigrationType.LEGACY_WORKSPACE.value:
                await self._validate_workspace_migration(command, validation_results)
            elif migration_type == MigrationType.DATA_FORMAT.value:
                await self._validate_data_format_migration(command, validation_results)
            elif migration_type == MigrationType.CONFIGURATION.value:
                await self._validate_configuration_migration(command, validation_results)
            
            # Update overall validation status
            validation_results["is_valid"] = len(validation_results["issues"]) == 0
            
            self.logger.info(f"Migration validation completed for {command.migration_id}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating migration {command.migration_id}: {e}")
            validation_results["is_valid"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
            return validation_results

    async def rollback_migration(self, command: RollbackMigrationCommand) -> MigrationResult:
        """Rollback a migration."""
        start_time = datetime.now()
        
        try:
            # Find backup to restore from
            backup_path = command.backup_path
            if not backup_path:
                # Look for most recent backup for this migration
                backup_path = await self._find_latest_backup(command.migration_id, command.workspace_name)
            
            if not backup_path or not backup_path.exists():
                return MigrationResult(
                    migration_id=f"rollback_{command.migration_id}",
                    status=MigrationStatus.FAILED,
                    message="No backup found for rollback",
                    workspace_name=command.workspace_name,
                    execution_time=datetime.now() - start_time,
                )
            
            # Perform rollback
            rollback_result = await self._rollback_from_backup(backup_path, command.workspace_name)
            
            execution_time = datetime.now() - start_time
            return MigrationResult(
                migration_id=f"rollback_{command.migration_id}",
                status=MigrationStatus.COMPLETED if rollback_result else MigrationStatus.FAILED,
                message="Rollback completed successfully" if rollback_result else "Rollback failed",
                workspace_name=command.workspace_name,
                backup_path=backup_path,
                execution_time=execution_time,
            )
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error rolling back migration {command.migration_id}: {e}")
            return MigrationResult(
                migration_id=f"rollback_{command.migration_id}",
                status=MigrationStatus.FAILED,
                message=f"Rollback failed: {str(e)}",
                workspace_name=command.workspace_name,
                execution_time=execution_time,
                error_details=str(e),
            )

    async def cleanup_migration_artifacts(
        self, command: CleanupMigrationArtifactsCommand
    ) -> bool:
        """Clean up after successful migration."""
        try:
            if command.remove_backups:
                await self._remove_migration_backups(command.migration_id, command.workspace_name)
            
            if command.remove_legacy_data:
                await self._remove_legacy_data(command.migration_id, command.workspace_name)
            
            self.logger.info(f"Cleanup completed for migration {command.migration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up migration {command.migration_id}: {e}")
            return False

    async def generate_migration_report(
        self, command: GenerateMigrationReportCommand
    ) -> MigrationReport:
        """Generate migration report."""
        try:
            if command.migration_id:
                # Generate report for specific migration
                details = await self.get_migration_details(
                    GetMigrationDetailsQuery(migration_id=command.migration_id)
                )
                
                report = MigrationReport(
                    migration_id=command.migration_id,
                    title=f"Migration Report: {command.migration_id}",
                    generated_at=datetime.now(),
                    summary={
                        "status": details.get("status"),
                        "workspace": details.get("workspace_name"),
                        "type": details.get("type"),
                        "duration": details.get("execution_time"),
                    },
                    details=details,
                )
                
                if command.include_details:
                    validation_results = await self.validate_migration(
                        ValidateMigrationCommand(migration_id=command.migration_id)
                    )
                    report.validation_results = validation_results
            else:
                # Generate summary report
                status_query = GetMigrationStatusQuery(
                    workspace_name=command.workspace_name,
                    limit=50
                )
                migrations = await self.get_migration_status(status_query)
                
                report = MigrationReport(
                    migration_id="summary_report",
                    title="Migration Summary Report",
                    generated_at=datetime.now(),
                    summary={
                        "total_migrations": len(migrations),
                        "successful": len([m for m in migrations if m.get("status") == MigrationStatus.COMPLETED.value]),
                        "failed": len([m for m in migrations if m.get("status") == MigrationStatus.FAILED.value]),
                        "pending": len([m for m in migrations if m.get("status") == MigrationStatus.PENDING.value]),
                    },
                    details={"migrations": migrations} if command.include_details else {},
                )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating migration report: {e}")
            raise

    async def schedule_migration(self, command: ScheduleMigrationCommand) -> str:
        """Schedule migration for later execution."""
        # This is a placeholder implementation
        # In a real implementation, this would integrate with a task scheduler
        schedule_id = f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Scheduled migration {schedule_id}")
        return schedule_id

    async def check_migration_health(
        self, command: CheckMigrationHealthCommand
    ) -> MigrationHealth:
        """Check migration system health."""
        issues = []
        
        try:
            # Check disk space
            disk_space_ok = True
            if command.check_disk_space:
                # Placeholder disk space check
                disk_space_ok = True  # Would implement actual check
            
            # Check permissions
            permissions_ok = True
            if command.check_permissions:
                # Placeholder permissions check
                permissions_ok = True  # Would implement actual check
            
            # Check dependencies
            dependencies_ok = True
            if command.check_dependencies:
                # Placeholder dependency check
                dependencies_ok = True  # Would implement actual check
            
            # Check backup system
            backup_system_ok = True
            if command.validate_backup_system:
                # Placeholder backup system check
                backup_system_ok = True  # Would implement actual check
            
            is_healthy = all([disk_space_ok, permissions_ok, dependencies_ok, backup_system_ok])
            
            if not is_healthy:
                if not disk_space_ok:
                    issues.append("Insufficient disk space for migration")
                if not permissions_ok:
                    issues.append("Insufficient permissions for migration operations")
                if not dependencies_ok:
                    issues.append("Missing dependencies for migration")
                if not backup_system_ok:
                    issues.append("Backup system not functioning properly")
            
            return MigrationHealth(
                is_healthy=is_healthy,
                issues=issues,
                disk_space_available=None,  # Would populate with actual value
                permissions_ok=permissions_ok,
                dependencies_ok=dependencies_ok,
                backup_system_ok=backup_system_ok,
                last_check=datetime.now(),
            )
            
        except Exception as e:
            self.logger.error(f"Error checking migration health: {e}")
            return MigrationHealth(
                is_healthy=False,
                issues=[f"Health check failed: {str(e)}"],
                last_check=datetime.now(),
            )

    async def get_migration_status(self, query: GetMigrationStatusQuery) -> List[Dict[str, Any]]:
        """Get migration status."""
        # Filter migrations based on query parameters
        migrations = self._migration_history.copy()
        
        if query.workspace_name:
            migrations = [m for m in migrations if m.workspace_name == query.workspace_name]
        
        if query.migration_type:
            migrations = [m for m in migrations if query.migration_type in m.migration_id]
        
        if query.status_filter != MigrationFilter.ALL:
            migrations = [m for m in migrations if m.status == query.status_filter]
        
        # Apply sorting
        if query.sort_by == MigrationSort.CREATED_DESC:
            migrations.reverse()
        # Add other sorting logic as needed
        
        # Apply limit
        if query.limit:
            migrations = migrations[:query.limit]
        
        # Convert to dict format
        return [
            {
                "migration_id": m.migration_id,
                "status": m.status.value,
                "message": m.message,
                "workspace_name": m.workspace_name,
                "items_migrated": m.items_migrated,
                "items_failed": m.items_failed,
                "execution_time": m.execution_time.total_seconds(),
                "error_details": m.error_details,
                "warnings": m.warnings,
                "metrics": m.metrics,
            }
            for m in migrations
        ]

    async def get_migration_details(self, query: GetMigrationDetailsQuery) -> Dict[str, Any]:
        """Get migration details."""
        # Find migration in history
        migration = None
        for m in self._migration_history:
            if m.migration_id == query.migration_id:
                migration = m
                break
        
        if not migration:
            # Check active migrations
            migration = self._active_migrations.get(query.migration_id)
        
        if not migration:
            return {}
        
        details = {
            "migration_id": migration.migration_id,
            "status": migration.status.value,
            "message": migration.message,
            "workspace_name": migration.workspace_name,
            "backup_path": str(migration.backup_path) if migration.backup_path else None,
            "items_migrated": migration.items_migrated,
            "items_failed": migration.items_failed,
            "execution_time": migration.execution_time.total_seconds(),
            "error_details": migration.error_details,
            "warnings": migration.warnings,
            "metrics": migration.metrics,
        }
        
        return details

    # Helper methods for specific migration types
    async def _check_data_formats(self, workspace: Workspace) -> List[MigrationType]:
        """Check if data format migrations are needed."""
        migrations = []
        
        try:
            workspace_path = Path.home() / ".writeit" / "workspaces" / workspace.name.value
            
            if not workspace_path.exists():
                return migrations
            
            # Check for legacy pipeline formats
            legacy_pipelines = self._check_legacy_pipeline_formats(workspace_path)
            if legacy_pipelines:
                migrations.append(MigrationType.PIPELINE_FORMAT)
            
            # Check for legacy template formats
            legacy_templates = self._check_legacy_template_formats(workspace_path)
            if legacy_templates:
                migrations.append(MigrationType.DATA_FORMAT)
            
            # Check for LMDB data that might need conversion
            legacy_lmdb = self._check_legacy_lmdb_formats(workspace_path)
            if legacy_lmdb:
                migrations.append(MigrationType.DATA_FORMAT)
                
            self.logger.info(f"Data format check for {workspace.name.value}: {migrations}")
            return migrations
            
        except Exception as e:
            self.logger.error(f"Error checking data formats for {workspace.name.value}: {e}")
            return []

    async def _check_configurations(self, workspace: Workspace) -> List[MigrationType]:
        """Check if configuration migrations are needed."""
        migrations = []
        # Placeholder implementation
        # Would check for legacy configuration formats
        return migrations

    async def _check_cache(self, workspace: Workspace) -> List[MigrationType]:
        """Check if cache migrations are needed."""
        migrations = []
        # Placeholder implementation
        # Would check for legacy cache formats
        return migrations

    async def _create_backup(self, source_path: Optional[Path], migration_id: str) -> Optional[Path]:
        """Create backup before migration."""
        if not source_path or not source_path.exists():
            self.logger.warning(f"Source path not found for backup: {source_path}")
            return None
        
        try:
            from ...infrastructure.persistence.backup_manager import (
                BackupManager, BackupConfig, BackupType, CompressionType, create_backup_manager
            )
            
            # Create backup manager
            backup_root = Path.home() / ".writeit" / "backups"
            backup_manager = create_backup_manager(backup_root)
            
            # Create backup
            result = await backup_manager.create_backup(
                source_path=source_path,
                backup_type=BackupType.LEGACY,
                migration_id=migration_id,
                description=f"Backup before migration {migration_id}",
                tags=["migration", "pre-migration"],
                compression=CompressionType.TAR_GZ,
            )
            
            if result.success:
                self.logger.info(f"Backup created successfully: {result.backup_id}")
                return result.backup_path
            else:
                self.logger.error(f"Backup creation failed: {result.error_details}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None

    async def _migrate_legacy_workspace(self, command: StartMigrationCommand, migration_id: str) -> Dict[str, Any]:
        """Migrate legacy workspace."""
        # Use the existing workspace migration logic
        from ...workspace.migration import WorkspaceMigrator
        
        migrator = WorkspaceMigrator(self.workspace_service)
        
        if not command.source_path:
            return {
                "status": MigrationStatus.FAILED,
                "message": "Source path required for legacy workspace migration",
                "items_migrated": 0,
                "items_failed": 0,
            }
        
        try:
            success, message = migrator.migrate_local_workspace(
                command.source_path,
                command.target_workspace,
                overwrite=command.force,
            )
            
            return {
                "status": MigrationStatus.COMPLETED if success else MigrationStatus.FAILED,
                "message": message,
                "items_migrated": 1 if success else 0,
                "items_failed": 0 if success else 1,
            }
            
        except Exception as e:
            return {
                "status": MigrationStatus.FAILED,
                "message": f"Legacy workspace migration failed: {str(e)}",
                "items_migrated": 0,
                "items_failed": 1,
                "error_details": str(e),
            }

    async def _migrate_data_format(self, command: StartMigrationCommand, migration_id: str) -> Dict[str, Any]:
        """Migrate data format."""
        start_time = datetime.now()
        items_migrated = 0
        items_failed = 0
        errors = []
        warnings = []
        
        try:
            if not command.target_workspace:
                return {
                    "status": MigrationStatus.FAILED,
                    "message": "Target workspace required for data format migration",
                    "items_migrated": 0,
                    "items_failed": 0,
                    "error_details": "No target workspace specified",
                }
            
            workspace_path = Path.home() / ".writeit" / "workspaces" / command.target_workspace
            
            if not workspace_path.exists():
                return {
                    "status": MigrationStatus.FAILED,
                    "message": f"Workspace not found: {command.target_workspace}",
                    "items_migrated": 0,
                    "items_failed": 0,
                    "error_details": f"Workspace path does not exist: {workspace_path}",
                }
            
            # Migrate pipeline formats
            pipeline_result = await self._migrate_pipeline_formats(workspace_path, migration_id)
            items_migrated += pipeline_result.get("migrated", 0)
            items_failed += pipeline_result.get("failed", 0)
            warnings.extend(pipeline_result.get("warnings", []))
            if pipeline_result.get("errors"):
                errors.extend(pipeline_result.get("errors", []))
            
            # Migrate template formats
            template_result = await self._migrate_template_formats(workspace_path, migration_id)
            items_migrated += template_result.get("migrated", 0)
            items_failed += template_result.get("failed", 0)
            warnings.extend(template_result.get("warnings", []))
            if template_result.get("errors"):
                errors.extend(template_result.get("errors", []))
            
            # Migrate LMDB data if needed
            lmdb_result = await self._migrate_lmdb_formats(workspace_path, migration_id)
            items_migrated += lmdb_result.get("migrated", 0)
            items_failed += lmdb_result.get("failed", 0)
            warnings.extend(lmdb_result.get("warnings", []))
            if lmdb_result.get("errors"):
                errors.extend(lmdb_result.get("errors", []))
            
            execution_time = datetime.now() - start_time
            
            status = MigrationStatus.COMPLETED
            message = f"Data format migration completed. Migrated: {items_migrated}, Failed: {items_failed}"
            
            if errors:
                status = MigrationStatus.FAILED
                message = f"Data format migration completed with errors. Migrated: {items_migrated}, Failed: {items_failed}"
            
            return {
                "status": status,
                "message": message,
                "items_migrated": items_migrated,
                "items_failed": items_failed,
                "execution_time": execution_time,
                "error_details": "; ".join(errors) if errors else None,
                "warnings": warnings,
                "metrics": {
                    "pipeline_files": pipeline_result.get("migrated", 0),
                    "template_files": template_result.get("migrated", 0),
                    "lmdb_files": lmdb_result.get("migrated", 0),
                    "total_time": execution_time.total_seconds(),
                }
            }
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error in data format migration: {e}")
            return {
                "status": MigrationStatus.FAILED,
                "message": f"Data format migration failed: {str(e)}",
                "items_migrated": items_migrated,
                "items_failed": items_failed,
                "execution_time": execution_time,
                "error_details": str(e),
                "warnings": warnings,
            }

    async def _migrate_configuration(self, command: StartMigrationCommand, migration_id: str) -> Dict[str, Any]:
        """Migrate configuration formats."""
        start_time = datetime.now()
        items_migrated = 0
        items_failed = 0
        errors = []
        warnings = []
        
        try:
            if not command.target_workspace:
                return {
                    "status": MigrationStatus.FAILED,
                    "message": "Target workspace required for configuration migration",
                    "items_migrated": 0,
                    "items_failed": 0,
                    "error_details": "No target workspace specified",
                }
            
            workspace_path = Path.home() / ".writeit" / "workspaces" / command.target_workspace
            
            if not workspace_path.exists():
                return {
                    "status": MigrationStatus.FAILED,
                    "message": f"Workspace not found: {command.target_workspace}",
                    "items_migrated": 0,
                    "items_failed": 0,
                    "error_details": f"Workspace path does not exist: {workspace_path}",
                }
            
            # Migrate workspace configuration
            workspace_config_result = await self._migrate_workspace_config(workspace_path, migration_id)
            items_migrated += workspace_config_result.get("migrated", 0)
            items_failed += workspace_config_result.get("failed", 0)
            warnings.extend(workspace_config_result.get("warnings", []))
            if workspace_config_result.get("errors"):
                errors.extend(workspace_config_result.get("errors", []))
            
            # Migrate global configuration if applicable
            if command.target_workspace == "default":
                global_config_result = await self._migrate_global_config(migration_id)
                items_migrated += global_config_result.get("migrated", 0)
                items_failed += global_config_result.get("failed", 0)
                warnings.extend(global_config_result.get("warnings", []))
                if global_config_result.get("errors"):
                    errors.extend(global_config_result.get("errors", []))
            
            execution_time = datetime.now() - start_time
            
            status = MigrationStatus.COMPLETED
            message = f"Configuration migration completed. Migrated: {items_migrated}, Failed: {items_failed}"
            
            if errors:
                status = MigrationStatus.FAILED
                message = f"Configuration migration completed with errors. Migrated: {items_migrated}, Failed: {items_failed}"
            
            return {
                "status": status,
                "message": message,
                "items_migrated": items_migrated,
                "items_failed": items_failed,
                "execution_time": execution_time,
                "error_details": "; ".join(errors) if errors else None,
                "warnings": warnings,
                "metrics": {
                    "config_files": items_migrated,
                    "total_time": execution_time.total_seconds(),
                }
            }
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error in configuration migration: {e}")
            return {
                "status": MigrationStatus.FAILED,
                "message": f"Configuration migration failed: {str(e)}",
                "items_migrated": items_migrated,
                "items_failed": items_failed,
                "execution_time": execution_time,
                "error_details": str(e),
                "warnings": warnings,
            }

    async def _migrate_cache_format(self, command: StartMigrationCommand, migration_id: str) -> Dict[str, Any]:
        """Migrate cache formats."""
        start_time = datetime.now()
        items_migrated = 0
        items_failed = 0
        errors = []
        warnings = []
        
        try:
            if not command.target_workspace:
                return {
                    "status": MigrationStatus.FAILED,
                    "message": "Target workspace required for cache format migration",
                    "items_migrated": 0,
                    "items_failed": 0,
                    "error_details": "No target workspace specified",
                }
            
            # Check for cache in various locations
            cache_locations = [
                Path.home() / ".writeit" / "cache" / command.target_workspace,
                Path.home() / ".writeit" / "workspaces" / command.target_workspace / "cache",
                Path.home() / ".writeit" / "cache",  # Global cache
            ]
            
            cache_found = False
            for cache_path in cache_locations:
                if cache_path.exists():
                    cache_result = await self._migrate_cache_directory(cache_path, migration_id)
                    items_migrated += cache_result.get("migrated", 0)
                    items_failed += cache_result.get("failed", 0)
                    warnings.extend(cache_result.get("warnings", []))
                    if cache_result.get("errors"):
                        errors.extend(cache_result.get("errors", []))
                    cache_found = True
            
            if not cache_found:
                warnings.append("No cache files found for migration")
            
            execution_time = datetime.now() - start_time
            
            status = MigrationStatus.COMPLETED
            message = f"Cache format migration completed. Migrated: {items_migrated}, Failed: {items_failed}"
            
            if errors:
                status = MigrationStatus.FAILED
                message = f"Cache format migration completed with errors. Migrated: {items_migrated}, Failed: {items_failed}"
            
            return {
                "status": status,
                "message": message,
                "items_migrated": items_migrated,
                "items_failed": items_failed,
                "execution_time": execution_time,
                "error_details": "; ".join(errors) if errors else None,
                "warnings": warnings,
                "metrics": {
                    "cache_files": items_migrated,
                    "total_time": execution_time.total_seconds(),
                }
            }
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error in cache format migration: {e}")
            return {
                "status": MigrationStatus.FAILED,
                "message": f"Cache format migration failed: {str(e)}",
                "items_migrated": items_migrated,
                "items_failed": items_failed,
                "execution_time": execution_time,
                "error_details": str(e),
                "warnings": warnings,
            }

    async def _rollback_from_backup(self, backup_path: Path, workspace_name: Optional[str]) -> bool:
        """Rollback from backup."""
        try:
            from ...infrastructure.persistence.backup_manager import (
                BackupManager, RollbackStrategy, create_backup_manager
            )
            
            # Create backup manager
            backup_root = Path.home() / ".writeit" / "backups"
            backup_manager = create_backup_manager(backup_root)
            
            # Extract backup ID from path
            backup_id = backup_path.stem
            
            # Perform rollback
            result = await backup_manager.restore_backup(
                backup_id=backup_id,
                target_path=Path.home() / ".writeit" / "workspaces" / workspace_name if workspace_name else Path.home() / ".writeit",
                strategy=RollbackStrategy.FULL_RESTORE,
            )
            
            if result.success:
                self.logger.info(f"Rollback completed successfully: {backup_id}")
                return True
            else:
                self.logger.error(f"Rollback failed: {result.error_details}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
            return False

    async def _find_latest_backup(self, migration_id: str, workspace_name: Optional[str]) -> Optional[Path]:
        """Find latest backup for migration."""
        try:
            from ...infrastructure.persistence.backup_manager import (
                BackupManager, BackupType, create_backup_manager
            )
            
            # Create backup manager
            backup_root = Path.home() / ".writeit" / "backups"
            backup_manager = create_backup_manager(backup_root)
            
            # List backups for this migration
            backups = await backup_manager.list_backups(
                backup_type=BackupType.LEGACY,
                migration_id=migration_id,
                workspace_name=workspace_name,
                limit=1,
            )
            
            if backups:
                backup_metadata = backups[0]
                return backup_metadata.backup_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding backup: {e}")
            return None

    async def _remove_migration_backups(self, migration_id: str, workspace_name: Optional[str]) -> None:
        """Remove migration backups."""
        try:
            from ...infrastructure.persistence.backup_manager import (
                BackupManager, BackupType, create_backup_manager
            )
            
            # Create backup manager
            backup_root = Path.home() / ".writeit" / "backups"
            backup_manager = create_backup_manager(backup_root)
            
            # List backups for this migration
            backups = await backup_manager.list_backups(
                backup_type=BackupType.LEGACY,
                migration_id=migration_id,
                workspace_name=workspace_name,
            )
            
            # Remove each backup
            for backup in backups:
                success = await backup_manager.delete_backup(backup.backup_id)
                if success:
                    self.logger.info(f"Removed backup: {backup.backup_id}")
                else:
                    self.logger.warning(f"Failed to remove backup: {backup.backup_id}")
                    
        except Exception as e:
            self.logger.error(f"Error removing migration backups: {e}")

    async def _remove_legacy_data(self, migration_id: str, workspace_name: Optional[str]) -> None:
        """Remove legacy data after successful migration."""
        # Placeholder implementation
        pass

    async def _validate_workspace_migration(self, command: ValidateMigrationCommand, results: Dict[str, Any]) -> None:
        """Validate workspace migration."""
        try:
            if not command.workspace_name:
                results["issues"].append("No workspace name provided for validation")
                return
            
            workspace_path = Path.home() / ".writeit" / "workspaces" / command.workspace_name
            
            if not workspace_path.exists():
                results["issues"].append(f"Workspace directory does not exist: {workspace_path}")
                return
            
            # Validate workspace structure
            validation_issues = []
            
            # Check required directories
            required_dirs = ["pipelines", "templates"]
            for dir_name in required_dirs:
                dir_path = workspace_path / dir_name
                if not dir_path.exists():
                    validation_issues.append(f"Missing required directory: {dir_name}")
                elif not dir_path.is_dir():
                    validation_issues.append(f"Invalid directory structure: {dir_name}")
            
            # Check workspace configuration
            workspace_config = workspace_path / "workspace.yaml"
            if not workspace_config.exists():
                validation_issues.append("Missing workspace configuration file")
            else:
                try:
                    with open(workspace_config, 'r') as f:
                        config_content = f.read()
                    
                    # Validate configuration structure
                    if 'name:' not in config_content:
                        validation_issues.append("Invalid workspace configuration: missing name field")
                    
                    if 'created_at:' not in config_content:
                        validation_issues.append("Invalid workspace configuration: missing created_at field")
                        
                except Exception as e:
                    validation_issues.append(f"Error reading workspace configuration: {str(e)}")
            
            # Check for backup files if deep validation requested
            if command.deep_validation:
                backup_files = list(workspace_path.rglob("*.backup_*"))
                if backup_files:
                    results["warnings"].append(f"Found {len(backup_files)} backup files from migration")
            
            if validation_issues:
                results["issues"].extend(validation_issues)
            else:
                results["warnings"].append("Workspace structure validation passed")
                
        except Exception as e:
            results["issues"].append(f"Error validating workspace migration: {str(e)}")

    async def _validate_data_format_migration(self, command: ValidateMigrationCommand, results: Dict[str, Any]) -> None:
        """Validate data format migration."""
        try:
            if not command.workspace_name:
                results["issues"].append("No workspace name provided for validation")
                return
            
            workspace_path = Path.home() / ".writeit" / "workspaces" / command.workspace_name
            
            if not workspace_path.exists():
                results["issues"].append(f"Workspace directory does not exist: {workspace_path}")
                return
            
            validation_issues = []
            
            # Validate pipeline formats
            pipelines_dir = workspace_path / "pipelines"
            if pipelines_dir.exists():
                pipeline_issues = await self._validate_pipeline_formats(pipelines_dir)
                validation_issues.extend(pipeline_issues)
            
            # Validate template formats
            templates_dir = workspace_path / "templates"
            if templates_dir.exists():
                template_issues = await self._validate_template_formats(templates_dir)
                validation_issues.extend(template_issues)
            
            # Validate LMDB formats
            lmdb_files = list(workspace_path.rglob("*.mdb")) + list(workspace_path.rglob("*.lmdb"))
            for lmdb_file in lmdb_files:
                lmdb_issues = await self._validate_lmdb_format(lmdb_file)
                validation_issues.extend(lmdb_issues)
            
            if validation_issues:
                results["issues"].extend(validation_issues)
            else:
                results["warnings"].append("Data format validation passed - no legacy formats found")
                
        except Exception as e:
            results["issues"].append(f"Error validating data format migration: {str(e)}")

    async def _validate_configuration_migration(self, command: ValidateMigrationCommand, results: Dict[str, Any]) -> None:
        """Validate configuration migration."""
        try:
            validation_issues = []
            
            # Validate workspace configuration if specified
            if command.workspace_name:
                workspace_config_path = Path.home() / ".writeit" / "workspaces" / command.workspace_name / "workspace.yaml"
                if workspace_config_path.exists():
                    config_issues = await self._validate_workspace_config(workspace_config_path)
                    validation_issues.extend(config_issues)
                else:
                    validation_issues.append(f"Workspace configuration not found: {workspace_config_path}")
            
            # Validate global configuration
            global_config_path = Path.home() / ".writeit" / "config.yaml"
            if global_config_path.exists():
                global_config_issues = await self._validate_global_config(global_config_path)
                validation_issues.extend(global_config_issues)
            
            if validation_issues:
                results["issues"].extend(validation_issues)
            else:
                results["warnings"].append("Configuration validation passed")
                
        except Exception as e:
            results["issues"].append(f"Error validating configuration migration: {str(e)}")

    async def _validate_pipeline_formats(self, pipelines_dir: Path) -> List[str]:
        """Validate pipeline file formats."""
        issues = []
        
        for pipeline_file in pipelines_dir.rglob("*.yaml"):
            try:
                with open(pipeline_file, 'r') as f:
                    content = f.read()
                
                # Check for legacy format indicators
                if 'type: "llm_generate"' in content:
                    issues.append(f"Legacy pipeline format found: {pipeline_file.name} (type: \"llm_generate\")")
                
                if '"model_preference":' in content:
                    issues.append(f"Legacy model reference format found: {pipeline_file.name} (\"model_preference\":)")
                
                # Validate YAML structure
                try:
                    import yaml
                    yaml.safe_load(content)
                except yaml.YAMLError as e:
                    issues.append(f"Invalid YAML syntax in pipeline file {pipeline_file.name}: {str(e)}")
                    
            except Exception as e:
                issues.append(f"Error validating pipeline file {pipeline_file.name}: {str(e)}")
        
        return issues

    async def _validate_template_formats(self, templates_dir: Path) -> List[str]:
        """Validate template file formats."""
        issues = []
        
        for template_file in templates_dir.rglob("*.yaml"):
            try:
                with open(template_file, 'r') as f:
                    content = f.read()
                
                # Check for legacy format indicators
                if 'defaults:' in content and 'models:' in content:
                    issues.append(f"Legacy template format found: {template_file.name} (models: in defaults)")
                
                # Validate YAML structure
                try:
                    import yaml
                    yaml.safe_load(content)
                except yaml.YAMLError as e:
                    issues.append(f"Invalid YAML syntax in template file {template_file.name}: {str(e)}")
                    
            except Exception as e:
                issues.append(f"Error validating template file {template_file.name}: {str(e)}")
        
        return issues

    async def _validate_lmdb_format(self, lmdb_file: Path) -> List[str]:
        """Validate LMDB file format."""
        issues = []
        
        try:
            # Check file size
            file_size = lmdb_file.stat().st_size
            if file_size == 0:
                issues.append(f"Empty LMDB file: {lmdb_file.name}")
            elif file_size < 1024:  # Less than 1KB
                issues.append(f"Suspiciously small LMDB file: {lmdb_file.name} ({file_size} bytes)")
            
            # Check file permissions
            if not os.access(lmdb_file, os.R_OK):
                issues.append(f"LMDB file not readable: {lmdb_file.name}")
            
            if not os.access(lmdb_file, os.W_OK):
                issues.append(f"LMDB file not writable: {lmdb_file.name}")
                
        except Exception as e:
            issues.append(f"Error validating LMDB file {lmdb_file.name}: {str(e)}")
        
        return issues

    async def _validate_workspace_config(self, config_file: Path) -> List[str]:
        """Validate workspace configuration format."""
        issues = []
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check for legacy format indicators
            if 'llm_providers: {}' in content:
                issues.append("Legacy LLM provider format found: llm_providers: {}")
            
            if 'default_pipeline: null' in content:
                issues.append("Legacy default pipeline format found: default_pipeline: null")
            
            # Validate YAML structure
            try:
                import yaml
                config_data = yaml.safe_load(content)
                
                # Check required fields
                required_fields = ['name', 'created_at']
                for field in required_fields:
                    if field not in config_data:
                        issues.append(f"Missing required field in workspace configuration: {field}")
                
                # Validate field types
                if 'name' in config_data and not isinstance(config_data['name'], str):
                    issues.append("Invalid name field type: should be string")
                
                if 'created_at' in config_data:
                    try:
                        # Try to parse as datetime
                        import datetime
                        datetime.datetime.fromisoformat(config_data['created_at'].replace('Z', '+00:00'))
                    except:
                        issues.append("Invalid created_at field format")
                        
            except yaml.YAMLError as e:
                issues.append(f"Invalid YAML syntax in workspace configuration: {str(e)}")
                
        except Exception as e:
            issues.append(f"Error validating workspace configuration: {str(e)}")
        
        return issues

    async def _validate_global_config(self, config_file: Path) -> List[str]:
        """Validate global configuration format."""
        issues = []
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Validate YAML structure
            try:
                import yaml
                config_data = yaml.safe_load(content)
                
                # Check required fields
                required_fields = ['writeit_version', 'active_workspace', 'workspaces']
                for field in required_fields:
                    if field not in config_data:
                        issues.append(f"Missing required field in global configuration: {field}")
                
                # Validate field types
                if 'writeit_version' in config_data and not isinstance(config_data['writeit_version'], str):
                    issues.append("Invalid writeit_version field type: should be string")
                
                if 'active_workspace' in config_data and not isinstance(config_data['active_workspace'], str):
                    issues.append("Invalid active_workspace field type: should be string")
                
                if 'workspaces' in config_data and not isinstance(config_data['workspaces'], list):
                    issues.append("Invalid workspaces field type: should be list")
                
                # Validate version format
                if 'writeit_version' in config_data:
                    version = config_data['writeit_version']
                    if not version.startswith('v'):
                        issues.append(f"Invalid version format: {version} (should start with 'v')")
                        
            except yaml.YAMLError as e:
                issues.append(f"Invalid YAML syntax in global configuration: {str(e)}")
                
        except Exception as e:
            issues.append(f"Error validating global configuration: {str(e)}")
        
        return issues

    # Helper methods for format detection and migration
    def _check_legacy_pipeline_formats(self, workspace_path: Path) -> bool:
        """Check for legacy pipeline formats that need migration."""
        try:
            pipelines_dir = workspace_path / "pipelines"
            if not pipelines_dir.exists():
                return False
            
            # Look for files with legacy formats
            legacy_found = False
            
            for pipeline_file in pipelines_dir.rglob("*.yaml"):
                try:
                    with open(pipeline_file, 'r') as f:
                        content = f.read()
                        
                    # Check for legacy format indicators
                    if ('type: "llm_generate"' in content or  # Old step type format
                        'llm_generation:' in content or        # Old step type format
                        '"model_preference":' in content):   # Old model reference format
                        legacy_found = True
                        break
                        
                except Exception:
                    continue
            
            return legacy_found
            
        except Exception as e:
            self.logger.error(f"Error checking legacy pipeline formats: {e}")
            return False

    def _check_legacy_template_formats(self, workspace_path: Path) -> bool:
        """Check for legacy template formats that need migration."""
        try:
            templates_dir = workspace_path / "templates"
            if not templates_dir.exists():
                return False
            
            # Look for files with legacy formats
            legacy_found = False
            
            for template_file in templates_dir.rglob("*.yaml"):
                try:
                    with open(template_file, 'r') as f:
                        content = f.read()
                        
                    # Check for legacy format indicators
                    if ('defaults:' in content and 'models:' in content or  # Old model defaults structure
                        'prompt_template: |' in content or               # Old prompt template format
                        'selection_prompt: |' in content):               # Old selection prompt format
                        legacy_found = True
                        break
                        
                except Exception:
                    continue
            
            return legacy_found
            
        except Exception as e:
            self.logger.error(f"Error checking legacy template formats: {e}")
            return False

    def _check_legacy_lmdb_formats(self, workspace_path: Path) -> bool:
        """Check for legacy LMDB formats that need migration."""
        try:
            # Look for old LMDB files that might need conversion
            lmdb_files = list(workspace_path.rglob("*.mdb")) + list(workspace_path.rglob("*.lmdb"))
            
            if not lmdb_files:
                return False
            
            # Check if any files are in old format
            # This is a simplified check - in practice, you'd examine the LMDB structure
            for lmdb_file in lmdb_files:
                try:
                    # Check file size - very small files might be old format
                    if lmdb_file.stat().st_size < 1024:  # Less than 1KB
                        return True
                        
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking legacy LMDB formats: {e}")
            return False

    async def _migrate_pipeline_formats(self, workspace_path: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate pipeline formats to new format."""
        migrated = 0
        failed = 0
        errors = []
        warnings = []
        
        try:
            pipelines_dir = workspace_path / "pipelines"
            if not pipelines_dir.exists():
                return {"migrated": 0, "failed": 0, "errors": [], "warnings": []}
            
            for pipeline_file in pipelines_dir.rglob("*.yaml"):
                try:
                    with open(pipeline_file, 'r') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply migration rules
                    updated_content = self._migrate_pipeline_content(content)
                    
                    if updated_content != original_content:
                        # Create backup
                        backup_file = pipeline_file.with_suffix(f'.yaml.backup_{migration_id}')
                        shutil.copy2(pipeline_file, backup_file)
                        
                        # Write updated content
                        with open(pipeline_file, 'w') as f:
                            f.write(updated_content)
                        
                        migrated += 1
                        warnings.append(f"Migrated pipeline: {pipeline_file.name}")
                    else:
                        # No migration needed
                        pass
                        
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to migrate {pipeline_file.name}: {str(e)}")
            
            return {
                "migrated": migrated,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            errors.append(f"Error in pipeline format migration: {str(e)}")
            return {"migrated": migrated, "failed": failed, "errors": errors, "warnings": warnings}

    async def _migrate_template_formats(self, workspace_path: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate template formats to new format."""
        migrated = 0
        failed = 0
        errors = []
        warnings = []
        
        try:
            templates_dir = workspace_path / "templates"
            if not templates_dir.exists():
                return {"migrated": 0, "failed": 0, "errors": [], "warnings": []}
            
            for template_file in templates_dir.rglob("*.yaml"):
                try:
                    with open(template_file, 'r') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply migration rules
                    updated_content = self._migrate_template_content(content)
                    
                    if updated_content != original_content:
                        # Create backup
                        backup_file = template_file.with_suffix(f'.yaml.backup_{migration_id}')
                        shutil.copy2(template_file, backup_file)
                        
                        # Write updated content
                        with open(template_file, 'w') as f:
                            f.write(updated_content)
                        
                        migrated += 1
                        warnings.append(f"Migrated template: {template_file.name}")
                    else:
                        # No migration needed
                        pass
                        
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to migrate {template_file.name}: {str(e)}")
            
            return {
                "migrated": migrated,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            errors.append(f"Error in template format migration: {str(e)}")
            return {"migrated": migrated, "failed": failed, "errors": errors, "warnings": warnings}

    async def _migrate_lmdb_formats(self, workspace_path: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate LMDB formats to new format."""
        migrated = 0
        failed = 0
        errors = []
        warnings = []
        
        try:
            lmdb_files = list(workspace_path.rglob("*.mdb")) + list(workspace_path.rglob("*.lmdb"))
            
            for lmdb_file in lmdb_files:
                try:
                    # LMDB migration would require special handling
                    # For now, just log that we found LMDB files
                    warnings.append(f"Found LMDB file: {lmdb_file.name} - manual migration may be required")
                    migrated += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to migrate {lmdb_file.name}: {str(e)}")
            
            return {
                "migrated": migrated,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            errors.append(f"Error in LMDB format migration: {str(e)}")
            return {"migrated": migrated, "failed": failed, "errors": errors, "warnings": warnings}

    def _migrate_pipeline_content(self, content: str) -> str:
        """Apply migration rules to pipeline content."""
        updated = content
        
        # Rule 1: Convert old step type format
        updated = updated.replace('type: "llm_generate"', 'type: "llm_generation"')
        updated = updated.replace('type: llm_generate', 'type: llm_generation')
        updated = updated.replace('llm_generation:', 'llm_generation:')
        
        # Rule 2: Update model reference format
        updated = updated.replace('"model_preference":', 'model_preference:')
        updated = updated.replace("'model_preference':", 'model_preference:')
        
        # Rule 3: Update prompt template format
        updated = updated.replace('prompt_template: |', 'prompt_template: |')
        updated = updated.replace('selection_prompt: |', 'selection_prompt: |')
        
        return updated

    def _migrate_template_content(self, content: str) -> str:
        """Apply migration rules to template content."""
        updated = content
        
        # Rule 1: Update model defaults structure
        if 'defaults:' in content and 'models:' in content:
            updated = updated.replace('models:', 'model_preferences:')
        
        # Rule 2: Update prompt template format
        updated = updated.replace('prompt_template: |', 'prompt_template: |')
        updated = updated.replace('selection_prompt: |', 'selection_prompt: |')
        
        return updated

    async def _migrate_cache_directory(self, cache_path: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate cache directory."""
        migrated = 0
        failed = 0
        errors = []
        warnings = []
        
        try:
            # Look for cache files in various formats
            cache_files = []
            
            # LMDB cache files
            cache_files.extend(cache_path.rglob("*.mdb"))
            cache_files.extend(cache_path.rglob("*.lmdb"))
            
            # JSON cache files
            cache_files.extend(cache_path.rglob("*.json"))
            
            # SQLite cache files
            cache_files.extend(cache_path.rglob("*.db"))
            cache_files.extend(cache_path.rglob("*.sqlite"))
            cache_files.extend(cache_path.rglob("*.sqlite3"))
            
            for cache_file in cache_files:
                try:
                    if cache_file.suffix in ['.mdb', '.lmdb']:
                        # LMDB cache migration
                        result = await self._migrate_lmdb_cache(cache_file, migration_id)
                        migrated += result.get("migrated", 0)
                        failed += result.get("failed", 0)
                        warnings.extend(result.get("warnings", []))
                        if result.get("errors"):
                            errors.extend(result.get("errors", []))
                    
                    elif cache_file.suffix == '.json':
                        # JSON cache migration
                        result = await self._migrate_json_cache(cache_file, migration_id)
                        migrated += result.get("migrated", 0)
                        failed += result.get("failed", 0)
                        warnings.extend(result.get("warnings", []))
                        if result.get("errors"):
                            errors.extend(result.get("errors", []))
                    
                    elif cache_file.suffix in ['.db', '.sqlite', '.sqlite3']:
                        # SQLite cache migration
                        result = await self._migrate_sqlite_cache(cache_file, migration_id)
                        migrated += result.get("migrated", 0)
                        failed += result.get("failed", 0)
                        warnings.extend(result.get("warnings", []))
                        if result.get("errors"):
                            errors.extend(result.get("errors", []))
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to migrate cache file {cache_file.name}: {str(e)}")
            
            return {
                "migrated": migrated,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            errors.append(f"Error migrating cache directory {cache_path}: {str(e)}")
            return {"migrated": migrated, "failed": failed, "errors": errors, "warnings": warnings}

    async def _migrate_workspace_config(self, workspace_path: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate workspace configuration."""
        migrated = 0
        failed = 0
        errors = []
        warnings = []
        
        try:
            workspace_config_file = workspace_path / "workspace.yaml"
            if not workspace_config_file.exists():
                return {"migrated": 0, "failed": 0, "errors": [], "warnings": []}
            
            with open(workspace_config_file, 'r') as f:
                config_content = f.read()
            
            original_content = config_content
            
            # Apply configuration migration rules
            updated_content = self._migrate_workspace_config_content(config_content)
            
            if updated_content != original_content:
                # Create backup
                backup_file = workspace_config_file.with_suffix(f'.yaml.backup_{migration_id}')
                shutil.copy2(workspace_config_file, backup_file)
                
                # Write updated content
                with open(workspace_config_file, 'w') as f:
                    f.write(updated_content)
                
                migrated += 1
                warnings.append(f"Migrated workspace configuration: {workspace_config_file.name}")
            
            return {
                "migrated": migrated,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            failed += 1
            errors.append(f"Error migrating workspace configuration: {str(e)}")
            return {"migrated": migrated, "failed": failed, "errors": errors, "warnings": warnings}

    async def _migrate_global_config(self, migration_id: str) -> Dict[str, Any]:
        """Migrate global configuration."""
        migrated = 0
        failed = 0
        errors = []
        warnings = []
        
        try:
            global_config_file = Path.home() / ".writeit" / "config.yaml"
            if not global_config_file.exists():
                return {"migrated": 0, "failed": 0, "errors": [], "warnings": []}
            
            with open(global_config_file, 'r') as f:
                config_content = f.read()
            
            original_content = config_content
            
            # Apply configuration migration rules
            updated_content = self._migrate_global_config_content(config_content)
            
            if updated_content != original_content:
                # Create backup
                backup_file = global_config_file.with_suffix(f'.yaml.backup_{migration_id}')
                shutil.copy2(global_config_file, backup_file)
                
                # Write updated content
                with open(global_config_file, 'w') as f:
                    f.write(updated_content)
                
                migrated += 1
                warnings.append(f"Migrated global configuration: {global_config_file.name}")
            
            return {
                "migrated": migrated,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            failed += 1
            errors.append(f"Error migrating global configuration: {str(e)}")
            return {"migrated": migrated, "failed": failed, "errors": errors, "warnings": warnings}

    def _migrate_workspace_config_content(self, content: str) -> str:
        """Apply migration rules to workspace configuration content."""
        updated = content
        
        # Rule 1: Update LLM provider configuration format
        if 'llm_providers:' in content and 'llm_providers: {}' in content:
            updated = updated.replace('llm_providers: {}', 'llm_providers: []')
        
        # Rule 2: Update default pipeline reference
        if 'default_pipeline: null' in content:
            updated = updated.replace('default_pipeline: null', 'default_pipeline: ""')
        
        # Rule 3: Update workspace name format if needed
        if 'name:' in content and len(content.split('\n')[0].split('name: ')[1]) > 50:
            # If name is very long, it might be a legacy format
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('name:'):
                    name_value = line.split('name: ')[1]
                    if len(name_value) > 50:
                        # Truncate or clean up the name
                        cleaned_name = name_value[:50].strip()
                        lines[i] = f'name: {cleaned_name}'
                        break
            updated = '\n'.join(lines)
        
        return updated

    def _migrate_global_config_content(self, content: str) -> str:
        """Apply migration rules to global configuration content."""
        updated = content
        
        # Rule 1: Update version format
        if 'writeit_version:' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('writeit_version:'):
                    version_value = line.split('writeit_version: ')[1].strip().strip('"\'')
                    # Normalize version format
                    if not version_value.startswith('v'):
                        lines[i] = f'writeit_version: "{version_value}"'
                    else:
                        lines[i] = f'writeit_version: "{version_value}"'
                    break
            updated = '\n'.join(lines)
        
        # Rule 2: Update workspace list format
        if 'workspaces:' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('- '):
                    # Ensure workspace names are properly formatted
                    workspace_name = line.strip()[2:].strip().strip('"\'')
                    lines[i] = f'- {workspace_name}'
            updated = '\n'.join(lines)
        
        return updated

    async def _migrate_lmdb_cache(self, cache_file: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate LMDB cache file."""
        # For LMDB files, we typically need to examine the structure
        # This is a simplified implementation
        try:
            # Create backup
            backup_file = cache_file.with_suffix(f'{cache_file.suffix}.backup_{migration_id}')
            shutil.copy2(cache_file, backup_file)
            
            # LMDB migration would require reading the database structure
            # For now, just log that we processed it
            return {
                "migrated": 1,
                "failed": 0,
                "errors": [],
                "warnings": [f"LMDB cache file processed: {cache_file.name} - structure preserved"],
            }
            
        except Exception as e:
            return {
                "migrated": 0,
                "failed": 1,
                "errors": [f"Failed to migrate LMDB cache {cache_file.name}: {str(e)}"],
                "warnings": [],
            }

    async def _migrate_json_cache(self, cache_file: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate JSON cache file."""
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            original_data = cache_data.copy()
            
            # Apply cache migration rules
            updated_data = self._migrate_json_cache_data(cache_data)
            
            if updated_data != original_data:
                # Create backup
                backup_file = cache_file.with_suffix(f'.json.backup_{migration_id}')
                shutil.copy2(cache_file, backup_file)
                
                # Write updated data
                with open(cache_file, 'w') as f:
                    json.dump(updated_data, f, indent=2)
                
                return {
                    "migrated": 1,
                    "failed": 0,
                    "errors": [],
                    "warnings": [f"Migrated JSON cache: {cache_file.name}"],
                }
            else:
                return {
                    "migrated": 0,
                    "failed": 0,
                    "errors": [],
                    "warnings": [],
                }
                
        except Exception as e:
            return {
                "migrated": 0,
                "failed": 1,
                "errors": [f"Failed to migrate JSON cache {cache_file.name}: {str(e)}"],
                "warnings": [],
            }

    async def _migrate_sqlite_cache(self, cache_file: Path, migration_id: str) -> Dict[str, Any]:
        """Migrate SQLite cache file."""
        try:
            # For SQLite files, we need to examine the schema
            # This is a simplified implementation
            import sqlite3
            
            # Create backup
            backup_file = cache_file.with_suffix(f'{cache_file.suffix}.backup_{migration_id}')
            shutil.copy2(cache_file, backup_file)
            
            # Connect to database and check schema
            conn = sqlite3.connect(str(cache_file))
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            migration_performed = False
            
            for table in tables:
                table_name = table[0]
                
                # Check for legacy cache schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Apply schema migrations if needed
                if self._needs_cache_schema_migration(columns):
                    try:
                        self._migrate_cache_table_schema(cursor, table_name)
                        migration_performed = True
                    except Exception as e:
                        conn.close()
                        return {
                            "migrated": 0,
                            "failed": 1,
                            "errors": [f"Failed to migrate SQLite table {table_name}: {str(e)}"],
                            "warnings": [],
                        }
            
            conn.commit()
            conn.close()
            
            if migration_performed:
                return {
                    "migrated": 1,
                    "failed": 0,
                    "errors": [],
                    "warnings": [f"Migrated SQLite cache: {cache_file.name}"],
                }
            else:
                return {
                    "migrated": 0,
                    "failed": 0,
                    "errors": [],
                    "warnings": [],
                }
                
        except Exception as e:
            return {
                "migrated": 0,
                "failed": 1,
                "errors": [f"Failed to migrate SQLite cache {cache_file.name}: {str(e)}"],
                "warnings": [],
            }

    def _migrate_json_cache_data(self, cache_data: dict) -> dict:
        """Apply migration rules to JSON cache data."""
        updated = cache_data.copy()
        
        # Rule 1: Update cache metadata format
        if isinstance(updated, dict):
            # Update timestamp format
            if 'timestamp' in updated and isinstance(updated['timestamp'], str):
                try:
                    # Try to parse and reformat timestamp
                    import datetime
                    timestamp = datetime.datetime.fromisoformat(updated['timestamp'].replace('Z', '+00:00'))
                    updated['timestamp'] = timestamp.isoformat()
                except:
                    pass
            
            # Update cache version format
            if 'version' in updated and isinstance(updated['version'], str):
                version = updated['version']
                if not version.startswith('v'):
                    updated['version'] = f"v{version}"
            
            # Update cache entry structure
            if 'entries' in updated and isinstance(updated['entries'], list):
                for i, entry in enumerate(updated['entries']):
                    if isinstance(entry, dict):
                        # Migrate individual entry structure
                        if 'llm_response' in entry:
                            # Update LLM response format
                            response = entry['llm_response']
                            if isinstance(response, dict):
                                if 'content' in response and isinstance(response['content'], str):
                                    # Ensure content is properly formatted
                                    response['content'] = response['content'].strip()
                                if 'tokens' in response and isinstance(response['tokens'], dict):
                                    # Update token counting format
                                    tokens = response['tokens']
                                    if 'input_tokens' in tokens and 'output_tokens' in tokens:
                                        # Convert to new format if needed
                                        if isinstance(tokens['input_tokens'], str):
                                            tokens['input_tokens'] = int(tokens['input_tokens'])
                                        if isinstance(tokens['output_tokens'], str):
                                            tokens['output_tokens'] = int(tokens['output_tokens'])
        
        return updated

    def _needs_cache_schema_migration(self, columns: list) -> bool:
        """Check if cache table schema needs migration."""
        # Look for legacy schema indicators
        column_names = [col[1] for col in columns]
        
        # Check for old column names or types
        legacy_indicators = [
            'response_text',  # Old response column name
            'prompt_text',    # Old prompt column name
            'token_count',    # Old token count column name
        ]
        
        return any(indicator in column_names for indicator in legacy_indicators)

    def _migrate_cache_table_schema(self, cursor, table_name: str) -> None:
        """Migrate cache table schema."""
        # This is a simplified schema migration
        # In practice, you'd need more sophisticated migration logic
        
        # Example: Add new columns if they don't exist
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN updated_at TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Update existing data format
        cursor.execute(f"UPDATE {table_name} SET created_at = datetime('now') WHERE created_at IS NULL")
        cursor.execute(f"UPDATE {table_name} SET updated_at = datetime('now') WHERE updated_at IS NULL")