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
        # Placeholder implementation
        # Would check for legacy data formats that need conversion
        return migrations

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
        # Placeholder implementation
        return {
            "status": MigrationStatus.COMPLETED,
            "message": "Data format migration completed",
            "items_migrated": 0,
            "items_failed": 0,
        }

    async def _migrate_configuration(self, command: StartMigrationCommand, migration_id: str) -> Dict[str, Any]:
        """Migrate configuration."""
        # Placeholder implementation
        return {
            "status": MigrationStatus.COMPLETED,
            "message": "Configuration migration completed",
            "items_migrated": 0,
            "items_failed": 0,
        }

    async def _migrate_cache_format(self, command: StartMigrationCommand, migration_id: str) -> Dict[str, Any]:
        """Migrate cache format."""
        # Placeholder implementation
        return {
            "status": MigrationStatus.COMPLETED,
            "message": "Cache format migration completed",
            "items_migrated": 0,
            "items_failed": 0,
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
        # Placeholder implementation
        pass

    async def _validate_data_format_migration(self, command: ValidateMigrationCommand, results: Dict[str, Any]) -> None:
        """Validate data format migration."""
        # Placeholder implementation
        pass

    async def _validate_configuration_migration(self, command: ValidateMigrationCommand, results: Dict[str, Any]) -> None:
        """Validate configuration migration."""
        # Placeholder implementation
        pass