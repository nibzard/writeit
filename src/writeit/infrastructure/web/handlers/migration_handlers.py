"""Migration handlers for WriteIt Web API.

Provides REST API endpoints for migration operations, including detection,
analysis, execution, and monitoring of migrations.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...application.commands.migration_commands import (
    MigrationType,
    MigrationPriority,
    DetectLegacyWorkspacesCommand,
    AnalyzeMigrationRequirementsCommand,
    StartMigrationCommand,
    BulkMigrationCommand,
    ValidateMigrationCommand,
    RollbackMigrationCommand,
    CleanupMigrationArtifactsCommand,
    GenerateMigrationReportCommand,
    CheckMigrationHealthCommand,
)

from ...application.queries.migration_queries import (
    GetMigrationStatusQuery,
    GetMigrationDetailsQuery,
    GetMigrationHistoryQuery,
    GetMigrationStatsQuery,
    GetLegacyWorkspacesQuery,
    GetMigrationRequirementsQuery,
    GetMigrationBackupsQuery,
    GetMigrationHealthQuery,
    MigrationFilter,
    MigrationSort,
)

from ...application.services.migration_application_service import (
    MigrationApplicationService,
    MigrationResult,
    MigrationHealth,
    MigrationReport,
)

from ..context import APIContext
from ...shared.dependencies.container import Container


# Request/Response Models
class MigrationRequest(BaseModel):
    """Base migration request model."""
    workspace_name: Optional[str] = Field(None, description="Target workspace name")
    dry_run: bool = Field(False, description="Run in dry-run mode")
    force: bool = Field(False, description="Force operation even with warnings")


class DetectLegacyRequest(BaseModel):
    """Request to detect legacy workspaces."""
    search_paths: Optional[List[str]] = Field(None, description="Paths to search")
    auto_analyze: bool = Field(True, description="Auto-analyze detected workspaces")


class MigrationStartRequest(MigrationRequest):
    """Request to start a migration."""
    migration_type: MigrationType = Field(..., description="Type of migration")
    source_path: Optional[str] = Field(None, description="Source path for migration")
    backup_before: bool = Field(True, description="Create backup before migration")
    rollback_on_failure: bool = Field(True, description="Rollback on failure")


class BulkMigrationRequest(MigrationRequest):
    """Request for bulk migration."""
    migrations: List[MigrationStartRequest] = Field(..., description="Migrations to run")
    parallel: bool = Field(False, description="Run migrations in parallel")
    continue_on_failure: bool = Field(False, description="Continue on failure")
    priority: MigrationPriority = Field(MigrationPriority.NORMAL, description="Migration priority")


class ValidationRequest(BaseModel):
    """Request to validate migration."""
    migration_id: str = Field(..., description="Migration ID to validate")
    deep_validation: bool = Field(False, description="Perform deep validation")
    compare_with_source: bool = Field(True, description="Compare with source data")


class RollbackRequest(BaseModel):
    """Request to rollback migration."""
    migration_id: str = Field(..., description="Migration ID to rollback")
    backup_path: Optional[str] = Field(None, description="Specific backup path")
    force: bool = Field(False, description="Force rollback")


class CleanupRequest(BaseModel):
    """Request to cleanup migration artifacts."""
    migration_id: str = Field(..., description="Migration ID to cleanup")
    remove_backups: bool = Field(False, description="Remove migration backups")
    remove_legacy_data: bool = Field(False, description="Remove legacy data")


class ReportRequest(BaseModel):
    """Request to generate migration report."""
    migration_id: Optional[str] = Field(None, description="Migration ID (None for summary)")
    workspace_name: Optional[str] = Field(None, description="Filter by workspace")
    include_details: bool = Field(True, description="Include detailed information")
    format: str = Field("json", description="Output format")


class MigrationStatusResponse(BaseModel):
    """Migration status response."""
    migration_id: str
    status: str
    message: str
    workspace_name: Optional[str]
    items_migrated: int
    items_failed: int
    execution_time: float
    error_details: Optional[str]
    warnings: List[str]
    metrics: Dict[str, Any]


class MigrationHealthResponse(BaseModel):
    """Migration health response."""
    is_healthy: bool
    issues: List[str]
    disk_space_available: Optional[int]
    permissions_ok: bool
    dependencies_ok: bool
    backup_system_ok: bool
    last_check: datetime


class MigrationEndpoints:
    """Migration API endpoints."""
    
    def __init__(self, container: Container):
        self.container = container
        self.router = APIRouter(prefix="/migration", tags=["migration"])
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Set up migration routes."""
        
        @self.router.post("/detect", response_model=List[Dict[str, Any]])
        async def detect_legacy_workspaces(
            request: DetectLegacyRequest,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Detect legacy workspaces and data formats."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = DetectLegacyWorkspacesCommand(
                    search_paths=[Path(p) for p in request.search_paths] if request.search_paths else None,
                    auto_analyze=request.auto_analyze,
                )
                
                legacy_workspaces = await migration_service.detect_legacy_workspaces(command)
                
                return legacy_workspaces
                
            except Exception as e:
                context.logger.error(f"Error detecting legacy workspaces: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/analyze", response_model=List[str])
        async def analyze_migration_requirements(
            workspace: Optional[str] = None,
            all_workspaces: bool = False,
            check_data: bool = True,
            check_config: bool = True,
            check_cache: bool = True,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Analyze migration requirements."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = AnalyzeMigrationRequirementsCommand(
                    workspace_name=workspace,
                    include_all_workspaces=all_workspaces,
                    check_data_formats=check_data,
                    check_configurations=check_config,
                    check_cache=check_cache,
                )
                
                required_migrations = await migration_service.analyze_migration_requirements(command)
                
                return [migration_type.value for migration_type in required_migrations]
                
            except Exception as e:
                context.logger.error(f"Error analyzing migration requirements: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/start", response_model=MigrationStatusResponse)
        async def start_migration(
            request: MigrationStartRequest,
            background_tasks: BackgroundTasks,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Start a migration operation."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = StartMigrationCommand(
                    migration_type=request.migration_type,
                    source_path=Path(request.source_path) if request.source_path else None,
                    target_workspace=request.workspace_name,
                    backup_before=request.backup_before,
                    rollback_on_failure=request.rollback_on_failure,
                    dry_run=request.dry_run,
                    force=request.force,
                )
                
                # For long-running migrations, run in background
                if request.migration_type in [MigrationType.LEGACY_WORKSPACE, MigrationType.DATA_FORMAT]:
                    background_tasks.add_task(migration_service.start_migration, command)
                    return MigrationStatusResponse(
                        migration_id="scheduled",
                        status="scheduled",
                        message="Migration scheduled for background execution",
                        workspace_name=request.workspace_name,
                        items_migrated=0,
                        items_failed=0,
                        execution_time=0.0,
                        warnings=["Migration running in background"],
                        metrics={}
                    )
                else:
                    result = await migration_service.start_migration(command)
                    
                    return MigrationStatusResponse(
                        migration_id=result.migration_id,
                        status=result.status.value,
                        message=result.message,
                        workspace_name=result.workspace_name,
                        items_migrated=result.items_migrated,
                        items_failed=result.items_failed,
                        execution_time=result.execution_time.total_seconds(),
                        error_details=result.error_details,
                        warnings=result.warnings,
                        metrics=result.metrics
                    )
                
            except Exception as e:
                context.logger.error(f"Error starting migration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/bulk", response_model=List[MigrationStatusResponse])
        async def bulk_migrate(
            request: BulkMigrationRequest,
            background_tasks: BackgroundTasks,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Perform multiple migrations."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                # Convert MigrationStartRequest to StartMigrationCommand
                migrations = [
                    StartMigrationCommand(
                        migration_type=migration.migration_type,
                        source_path=Path(migration.source_path) if migration.source_path else None,
                        target_workspace=migration.workspace_name,
                        backup_before=migration.backup_before,
                        rollback_on_failure=migration.rollback_on_failure,
                        dry_run=migration.dry_run,
                        force=migration.force,
                    )
                    for migration in request.migrations
                ]
                
                command = BulkMigrationCommand(
                    migrations=migrations,
                    parallel=request.parallel,
                    continue_on_failure=request.continue_on_failure,
                    priority=request.priority,
                )
                
                # For bulk migrations, always run in background
                background_tasks.add_task(migration_service.bulk_migrate, command)
                
                return [
                    MigrationStatusResponse(
                        migration_id=f"scheduled_{i}",
                        status="scheduled",
                        message="Migration scheduled for background execution",
                        workspace_name=migration.workspace_name,
                        items_migrated=0,
                        items_failed=0,
                        execution_time=0.0,
                        warnings=["Migration running in background"],
                        metrics={}
                    )
                    for i, migration in enumerate(request.migrations)
                ]
                
            except Exception as e:
                context.logger.error(f"Error starting bulk migration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/status", response_model=List[MigrationStatusResponse])
        async def get_migration_status(
            workspace: Optional[str] = None,
            migration_type: Optional[str] = None,
            status: str = "all",
            limit: Optional[int] = None,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Get migration status."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                query = GetMigrationStatusQuery(
                    workspace_name=workspace,
                    migration_type=migration_type,
                    status_filter=MigrationFilter(status),
                    limit=limit,
                )
                
                migrations = await migration_service.get_migration_status(query)
                
                return [
                    MigrationStatusResponse(**migration)
                    for migration in migrations
                ]
                
            except Exception as e:
                context.logger.error(f"Error getting migration status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/status/{migration_id}", response_model=Dict[str, Any])
        async def get_migration_details(
            migration_id: str,
            include_logs: bool = True,
            include_metrics: bool = True,
            include_validation: bool = True,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Get detailed migration information."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                query = GetMigrationDetailsQuery(
                    migration_id=migration_id,
                    include_logs=include_logs,
                    include_metrics=include_metrics,
                    include_validation_results=include_validation,
                )
                
                details = await migration_service.get_migration_details(query)
                
                if not details:
                    raise HTTPException(status_code=404, detail="Migration not found")
                
                return details
                
            except HTTPException:
                raise
            except Exception as e:
                context.logger.error(f"Error getting migration details: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/history", response_model=List[MigrationStatusResponse])
        async def get_migration_history(
            workspace: Optional[str] = None,
            limit: int = 50,
            include_failed: bool = True,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Get migration history."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                query = GetMigrationHistoryQuery(
                    workspace_name=workspace,
                    limit=limit,
                    include_failed=include_failed,
                )
                
                # Note: This would need to be implemented in the service
                # For now, return status with history filter
                status_query = GetMigrationStatusQuery(
                    workspace_name=workspace,
                    limit=limit,
                )
                
                migrations = await migration_service.get_migration_status(status_query)
                
                return [
                    MigrationStatusResponse(**migration)
                    for migration in migrations
                ]
                
            except Exception as e:
                context.logger.error(f"Error getting migration history: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/validate", response_model=Dict[str, Any])
        async def validate_migration(
            request: ValidationRequest,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Validate migration results."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = ValidateMigrationCommand(
                    migration_id=request.migration_id,
                    deep_validation=request.deep_validation,
                    compare_with_source=request.compare_with_source,
                )
                
                validation_results = await migration_service.validate_migration(command)
                
                return validation_results
                
            except Exception as e:
                context.logger.error(f"Error validating migration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/rollback", response_model=MigrationStatusResponse)
        async def rollback_migration(
            request: RollbackRequest,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Rollback a migration."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = RollbackMigrationCommand(
                    migration_id=request.migration_id,
                    backup_path=Path(request.backup_path) if request.backup_path else None,
                    force=request.force,
                )
                
                result = await migration_service.rollback_migration(command)
                
                return MigrationStatusResponse(
                    migration_id=result.migration_id,
                    status=result.status.value,
                    message=result.message,
                    workspace_name=result.workspace_name,
                    items_migrated=result.items_migrated,
                    items_failed=result.items_failed,
                    execution_time=result.execution_time.total_seconds(),
                    error_details=result.error_details,
                    warnings=result.warnings,
                    metrics=result.metrics
                )
                
            except Exception as e:
                context.logger.error(f"Error rolling back migration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/cleanup", response_model=Dict[str, bool])
        async def cleanup_migration_artifacts(
            request: CleanupRequest,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Clean up migration artifacts."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = CleanupMigrationArtifactsCommand(
                    migration_id=request.migration_id,
                    remove_backups=request.remove_backups,
                    remove_legacy_data=request.remove_legacy_data,
                )
                
                success = await migration_service.cleanup_migration_artifacts(command)
                
                return {"success": success}
                
            except Exception as e:
                context.logger.error(f"Error cleaning up migration artifacts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/health", response_model=MigrationHealthResponse)
        async def check_migration_health(
            check_disk: bool = True,
            check_permissions: bool = True,
            check_dependencies: bool = True,
            check_backup: bool = True,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Check migration system health."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = CheckMigrationHealthCommand(
                    check_disk_space=check_disk,
                    check_permissions=check_permissions,
                    check_dependencies=check_dependencies,
                    validate_backup_system=check_backup,
                )
                
                health = await migration_service.check_migration_health(command)
                
                return MigrationHealthResponse(
                    is_healthy=health.is_healthy,
                    issues=health.issues,
                    disk_space_available=health.disk_space_available,
                    permissions_ok=health.permissions_ok,
                    dependencies_ok=health.dependencies_ok,
                    backup_system_ok=health.backup_system_ok,
                    last_check=health.last_check,
                )
                
            except Exception as e:
                context.logger.error(f"Error checking migration health: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/report")
        async def generate_migration_report(
            request: ReportRequest,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Generate migration report."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                command = GenerateMigrationReportCommand(
                    migration_id=request.migration_id,
                    workspace_name=request.workspace_name,
                    include_details=request.include_details,
                    format=request.format,
                )
                
                report = await migration_service.generate_migration_report(command)
                
                # Return report in the requested format
                if request.format == "json":
                    return JSONResponse(content={
                        "migration_id": report.migration_id,
                        "title": report.title,
                        "generated_at": report.generated_at.isoformat(),
                        "summary": report.summary,
                        "details": report.details,
                        "validation_results": report.validation_results,
                        "recommendations": report.recommendations,
                    })
                else:
                    # For other formats, return as text
                    return JSONResponse(content={
                        "migration_id": report.migration_id,
                        "title": report.title,
                        "generated_at": report.generated_at.isoformat(),
                        "summary": report.summary,
                        "details": report.details,
                        "validation_results": report.validation_results,
                        "recommendations": report.recommendations,
                    })
                
            except Exception as e:
                context.logger.error(f"Error generating migration report: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/stats")
        async def get_migration_stats(
            workspace: Optional[str] = None,
            include_all_workspaces: bool = False,
            time_period: Optional[str] = None,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Get migration statistics."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                query = GetMigrationStatsQuery(
                    workspace_name=workspace,
                    include_all_workspaces=include_all_workspaces,
                    time_period=time_period,
                )
                
                # Note: This would need to be implemented in the service
                # For now, return basic stats
                status_query = GetMigrationStatusQuery(
                    workspace_name=workspace,
                )
                
                migrations = await migration_service.get_migration_status(status_query)
                
                stats = {
                    "total_migrations": len(migrations),
                    "successful": len([m for m in migrations if m.get("status") == "completed"]),
                    "failed": len([m for m in migrations if m.get("status") == "failed"]),
                    "pending": len([m for m in migrations if m.get("status") == "pending"]),
                    "in_progress": len([m for m in migrations if m.get("status") == "in_progress"]),
                }
                
                return stats
                
            except Exception as e:
                context.logger.error(f"Error getting migration stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/backups")
        async def get_migration_backups(
            workspace: Optional[str] = None,
            migration_id: Optional[str] = None,
            include_size: bool = True,
            include_date: bool = True,
            context: APIContext = Depends(APIContext.get_current)
        ):
            """Get migration backup information."""
            try:
                migration_service = self.container.get(MigrationApplicationService)
                
                query = GetMigrationBackupsQuery(
                    workspace_name=workspace,
                    migration_id=migration_id,
                    include_size_info=include_size,
                    include_creation_date=include_date,
                )
                
                # Note: This would need to be implemented in the service
                # For now, return empty list
                return []
                
            except Exception as e:
                context.logger.error(f"Error getting migration backups: {e}")
                raise HTTPException(status_code=500, detail=str(e))