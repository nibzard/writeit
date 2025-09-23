"""Workspace Application Service.

Manages workspace operations, configuration management, analytics, and user
interactions. Coordinates workspace domain services with other domains.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Union
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

from ...domains.workspace.services import (
    WorkspaceManagementService,
    WorkspaceConfigurationService,
    WorkspaceAnalyticsService,
    WorkspaceCreationOptions,
    WorkspaceMigrationPlan,
    WorkspaceBackupInfo,
    ConfigurationScope,
    WorkspaceAnalytics,
    AnalyticsReport,
    AnalyticsScope,
    MetricType,
    HealthStatus,
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


class WorkspaceInitializationMode(str, Enum):
    """Workspace initialization modes."""
    MINIMAL = "minimal"      # Basic workspace structure
    STANDARD = "standard"    # Standard templates and styles
    FULL = "full"           # Complete setup with samples
    MIGRATION = "migration"  # Initialize from existing data


class WorkspaceBackupScope(str, Enum):
    """Workspace backup scopes."""
    CONFIGURATION = "configuration"  # Only configuration files
    TEMPLATES = "templates"          # Templates and styles
    DATA = "data"                   # Pipeline runs and cache
    FULL = "full"                   # Everything


class WorkspaceReportType(str, Enum):
    """Types of workspace reports."""
    USAGE = "usage"           # Usage statistics and patterns
    PERFORMANCE = "performance"  # Performance metrics
    COSTS = "costs"          # Cost analysis and optimization
    HEALTH = "health"        # Health diagnostics
    SUMMARY = "summary"      # Executive summary


@dataclass
class WorkspaceCreationRequest:
    """Request for workspace creation."""
    name: str
    description: Optional[str] = None
    initialization_mode: WorkspaceInitializationMode = WorkspaceInitializationMode.STANDARD
    copy_from_workspace: Optional[str] = None
    include_sample_templates: bool = True
    include_sample_styles: bool = True
    custom_configuration: Optional[Dict[str, Any]] = None


@dataclass
class WorkspaceListingOptions:
    """Options for listing workspaces."""
    include_inactive: bool = False
    include_system: bool = False
    filter_pattern: Optional[str] = None
    sort_by: str = "name"  # name, created_at, last_used
    include_analytics: bool = False


@dataclass
class WorkspaceBackupRequest:
    """Request for workspace backup."""
    workspace_name: str
    backup_path: Path
    scope: WorkspaceBackupScope = WorkspaceBackupScope.FULL
    include_cache: bool = False
    compress: bool = True
    encryption: bool = False


@dataclass
class WorkspaceMigrationRequest:
    """Request for workspace migration."""
    source_workspace: str
    target_workspace: str
    migration_options: Dict[str, Any]
    dry_run: bool = True
    backup_before_migration: bool = True


@dataclass
class WorkspaceReportRequest:
    """Request for workspace report generation."""
    workspace_name: str
    report_type: WorkspaceReportType
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    include_recommendations: bool = True
    format: str = "json"  # json, html, pdf


class WorkspaceApplicationError(Exception):
    """Base exception for workspace application service errors."""
    pass


class WorkspaceCreationError(WorkspaceApplicationError):
    """Workspace creation failed."""
    pass


class WorkspaceNotFoundError(WorkspaceApplicationError):
    """Workspace not found."""
    pass


class WorkspaceBackupError(WorkspaceApplicationError):
    """Workspace backup failed."""
    pass


class WorkspaceMigrationError(WorkspaceApplicationError):
    """Workspace migration failed."""
    pass


class WorkspaceApplicationService:
    """
    Application service for workspace operations.
    
    Manages workspace lifecycle, configuration, analytics, and cross-domain
    coordination. Provides high-level use cases for workspace management
    across CLI, TUI, and API interfaces.
    """
    
    def __init__(
        self,
        # Workspace domain services
        workspace_management_service: WorkspaceManagementService,
        workspace_configuration_service: WorkspaceConfigurationService,
        workspace_analytics_service: WorkspaceAnalyticsService,
        
        # Other domain services for coordination
        template_management_service: TemplateManagementService,
        style_management_service: StyleManagementService,
        cache_management_service: CacheManagementService,
        token_analytics_service: TokenAnalyticsService,
        pipeline_validation_service: PipelineValidationService,
    ):
        """Initialize the workspace application service."""
        # Workspace domain services
        self._workspace_management = workspace_management_service
        self._workspace_configuration = workspace_configuration_service
        self._workspace_analytics = workspace_analytics_service
        
        # Cross-domain services
        self._template_management = template_management_service
        self._style_management = style_management_service
        self._cache_management = cache_management_service
        self._token_analytics = token_analytics_service
        self._pipeline_validation = pipeline_validation_service

    async def create_workspace(
        self, 
        request: WorkspaceCreationRequest
    ) -> Workspace:
        """
        Create a new workspace with comprehensive setup.
        
        Coordinates workspace creation across all domains, including
        configuration, templates, styles, and initial setup.
        
        Args:
            request: Workspace creation request
            
        Returns:
            Created workspace
            
        Raises:
            WorkspaceCreationError: If workspace creation fails
        """
        try:
            # Validate workspace name
            workspace_name = WorkspaceName(request.name)
            
            # Check if workspace already exists
            existing = await self._workspace_management.get_workspace(workspace_name)
            if existing:
                raise WorkspaceCreationError(f"Workspace '{request.name}' already exists")
            
            # Prepare creation options
            creation_options = WorkspaceCreationOptions(
                description=request.description,
                copy_from=request.copy_from_workspace,
                initialize_templates=request.include_sample_templates,
                initialize_styles=request.include_sample_styles,
                custom_config=request.custom_configuration or {}
            )
            
            # Create workspace
            workspace = await self._workspace_management.create_workspace(
                workspace_name,
                creation_options
            )
            
            # Initialize based on mode
            await self._initialize_workspace_content(workspace, request)
            
            # Set up analytics tracking
            await self._workspace_analytics.initialize_workspace_tracking(
                workspace_name
            )
            
            # Initialize cache system
            await self._cache_management.initialize_workspace_cache(
                workspace_name
            )
            
            # Initialize token tracking
            await self._token_analytics.initialize_workspace_tracking(
                workspace_name
            )
            
            return workspace
            
        except Exception as e:
            raise WorkspaceCreationError(f"Failed to create workspace: {e}") from e

    async def list_workspaces(
        self, 
        options: WorkspaceListingOptions
    ) -> List[Dict[str, Any]]:
        """
        List available workspaces with enriched information.
        
        Args:
            options: Listing options
            
        Returns:
            List of workspace information dictionaries
        """
        try:
            # Get base workspace list
            workspaces = await self._workspace_management.list_workspaces(
                include_inactive=options.include_inactive,
                filter_pattern=options.filter_pattern
            )
            
            # Enrich with additional information
            enriched_workspaces = []
            for workspace in workspaces:
                workspace_info = {
                    "name": workspace.name.value,
                    "description": workspace.description,
                    "created_at": workspace.created_at,
                    "last_used": workspace.last_used_at,
                    "is_active": await self._workspace_management.is_active_workspace(
                        workspace.name
                    ),
                }
                
                # Add analytics if requested
                if options.include_analytics:
                    analytics = await self._workspace_analytics.get_workspace_summary(
                        workspace.name
                    )
                    workspace_info.update({
                        "analytics": {
                            "pipeline_count": analytics.total_pipelines,
                            "execution_count": analytics.total_executions,
                            "last_execution": analytics.last_execution_time,
                            "storage_usage": analytics.storage_usage,
                            "health_status": analytics.health_status.value
                        }
                    })
                
                enriched_workspaces.append(workspace_info)
            
            # Sort based on options
            if options.sort_by == "created_at":
                enriched_workspaces.sort(key=lambda x: x["created_at"], reverse=True)
            elif options.sort_by == "last_used":
                enriched_workspaces.sort(
                    key=lambda x: x["last_used"] or datetime.min, 
                    reverse=True
                )
            else:  # sort by name
                enriched_workspaces.sort(key=lambda x: x["name"])
            
            return enriched_workspaces
            
        except Exception as e:
            raise WorkspaceApplicationError(f"Failed to list workspaces: {e}") from e

    async def switch_workspace(self, workspace_name: str) -> Workspace:
        """
        Switch to a different workspace.
        
        Args:
            workspace_name: Name of workspace to switch to
            
        Returns:
            Activated workspace
            
        Raises:
            WorkspaceNotFoundError: If workspace doesn't exist
        """
        try:
            workspace = await self._workspace_management.get_workspace(
                WorkspaceName(workspace_name)
            )
            
            if not workspace:
                raise WorkspaceNotFoundError(f"Workspace '{workspace_name}' not found")
            
            # Switch active workspace
            await self._workspace_management.set_active_workspace(workspace.name)
            
            # Update workspace usage tracking
            await self._workspace_analytics.record_workspace_access(workspace.name)
            
            return workspace
            
        except Exception as e:
            raise WorkspaceApplicationError(f"Failed to switch workspace: {e}") from e

    async def get_workspace_info(
        self, 
        workspace_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive workspace information.
        
        Args:
            workspace_name: Optional workspace name (uses active if not provided)
            
        Returns:
            Comprehensive workspace information
        """
        try:
            # Resolve workspace
            if workspace_name:
                workspace = await self._workspace_management.get_workspace(
                    WorkspaceName(workspace_name)
                )
            else:
                workspace = await self._workspace_management.get_active_workspace()
            
            if not workspace:
                raise WorkspaceNotFoundError("No workspace available")
            
            # Get configuration
            config = await self._workspace_configuration.get_configuration(
                workspace.name
            )
            
            # Get analytics
            analytics = await self._workspace_analytics.get_workspace_analytics(
                workspace.name
            )
            
            # Get template and style counts
            template_count = len(await self._template_management.list_templates(workspace))
            style_count = len(await self._style_management.list_styles(workspace))
            
            # Get cache statistics
            cache_stats = await self._cache_management.get_workspace_cache_stats(
                workspace.name
            )
            
            # Get token usage
            token_usage = await self._token_analytics.get_workspace_usage(
                workspace.name
            )
            
            return {
                "workspace": {
                    "name": workspace.name.value,
                    "description": workspace.description,
                    "created_at": workspace.created_at,
                    "last_used": workspace.last_used_at,
                    "is_active": await self._workspace_management.is_active_workspace(
                        workspace.name
                    ),
                },
                "configuration": {
                    "default_model": config.default_model,
                    "cache_enabled": config.cache_enabled,
                    "custom_settings": config.custom_settings,
                },
                "content": {
                    "template_count": template_count,
                    "style_count": style_count,
                },
                "analytics": {
                    "total_pipelines": analytics.usage_metrics.total_pipelines,
                    "total_executions": analytics.usage_metrics.total_executions,
                    "last_execution": analytics.usage_metrics.last_execution_time,
                    "performance": {
                        "average_execution_time": analytics.performance_metrics.average_execution_time,
                        "success_rate": analytics.performance_metrics.success_rate,
                        "error_rate": analytics.performance_metrics.error_rate,
                    },
                    "resources": {
                        "storage_usage": analytics.resource_metrics.storage_usage_mb,
                        "cache_size": analytics.resource_metrics.cache_size_mb,
                        "memory_usage": analytics.resource_metrics.memory_usage_mb,
                    },
                    "health": {
                        "status": analytics.health_diagnostics.overall_health.value,
                        "issues": analytics.health_diagnostics.health_issues,
                    }
                },
                "cache_performance": {
                    "hit_rate": cache_stats.hit_rate,
                    "total_requests": cache_stats.total_requests,
                    "cache_size": cache_stats.cache_size_mb,
                },
                "token_usage": {
                    "total_tokens": token_usage.total_tokens_used,
                    "total_cost": token_usage.total_cost,
                    "monthly_usage": token_usage.current_month_usage,
                }
            }
            
        except Exception as e:
            raise WorkspaceApplicationError(f"Failed to get workspace info: {e}") from e

    async def backup_workspace(
        self, 
        request: WorkspaceBackupRequest
    ) -> WorkspaceBackupInfo:
        """
        Create a backup of workspace data.
        
        Args:
            request: Backup request
            
        Returns:
            Backup information
            
        Raises:
            WorkspaceBackupError: If backup fails
        """
        try:
            workspace_name = WorkspaceName(request.workspace_name)
            
            # Validate workspace exists
            workspace = await self._workspace_management.get_workspace(workspace_name)
            if not workspace:
                raise WorkspaceNotFoundError(f"Workspace '{request.workspace_name}' not found")
            
            # Create backup
            backup_info = await self._workspace_management.backup_workspace(
                workspace_name,
                backup_path=request.backup_path,
                include_cache=request.include_cache,
                compress=request.compress
            )
            
            # Add cross-domain data to backup if full scope
            if request.scope == WorkspaceBackupScope.FULL:
                # Backup templates and styles
                await self._backup_workspace_content(workspace, request.backup_path)
                
                # Backup analytics data
                await self._backup_workspace_analytics(workspace, request.backup_path)
            
            return backup_info
            
        except Exception as e:
            raise WorkspaceBackupError(f"Workspace backup failed: {e}") from e

    async def migrate_workspace(
        self, 
        request: WorkspaceMigrationRequest
    ) -> WorkspaceMigrationPlan:
        """
        Migrate workspace data between workspaces.
        
        Args:
            request: Migration request
            
        Returns:
            Migration plan and results
            
        Raises:
            WorkspaceMigrationError: If migration fails
        """
        try:
            source_name = WorkspaceName(request.source_workspace)
            target_name = WorkspaceName(request.target_workspace)
            
            # Validate workspaces
            source_workspace = await self._workspace_management.get_workspace(source_name)
            if not source_workspace:
                raise WorkspaceNotFoundError(f"Source workspace '{request.source_workspace}' not found")
            
            # Create migration plan
            migration_plan = await self._workspace_management.create_migration_plan(
                source_name,
                target_name,
                request.migration_options
            )
            
            if not request.dry_run:
                # Backup source workspace if requested
                if request.backup_before_migration:
                    backup_path = Path(f"./backup_{request.source_workspace}_{datetime.now().isoformat()}")
                    await self.backup_workspace(WorkspaceBackupRequest(
                        workspace_name=request.source_workspace,
                        backup_path=backup_path
                    ))
                
                # Execute migration
                await self._workspace_management.execute_migration(migration_plan)
                
                # Migrate cross-domain data
                await self._migrate_workspace_content(source_workspace, target_name)
                await self._migrate_workspace_analytics(source_workspace, target_name)
            
            return migration_plan
            
        except Exception as e:
            raise WorkspaceMigrationError(f"Workspace migration failed: {e}") from e

    async def generate_workspace_report(
        self, 
        request: WorkspaceReportRequest
    ) -> Dict[str, Any]:
        """
        Generate comprehensive workspace report.
        
        Args:
            request: Report request
            
        Returns:
            Generated report data
        """
        try:
            workspace_name = WorkspaceName(request.workspace_name)
            
            # Validate workspace exists
            workspace = await self._workspace_management.get_workspace(workspace_name)
            if not workspace:
                raise WorkspaceNotFoundError(f"Workspace '{request.workspace_name}' not found")
            
            # Generate base report
            report = await self._workspace_analytics.generate_report(
                workspace_name,
                report_type=request.report_type.value,
                period_start=request.period_start,
                period_end=request.period_end
            )
            
            # Enhance with cross-domain data
            enhanced_report = await self._enhance_workspace_report(
                report, workspace, request
            )
            
            # Add recommendations if requested
            if request.include_recommendations:
                recommendations = await self._generate_workspace_recommendations(
                    workspace, enhanced_report
                )
                enhanced_report["recommendations"] = recommendations
            
            return enhanced_report
            
        except Exception as e:
            raise WorkspaceApplicationError(f"Failed to generate workspace report: {e}") from e

    async def delete_workspace(
        self, 
        workspace_name: str, 
        force: bool = False,
        backup_before_delete: bool = True
    ) -> bool:
        """
        Delete a workspace with safety checks.
        
        Args:
            workspace_name: Name of workspace to delete
            force: Force deletion without confirmation
            backup_before_delete: Create backup before deletion
            
        Returns:
            True if deletion was successful
            
        Raises:
            WorkspaceApplicationError: If deletion fails
        """
        try:
            workspace = await self._workspace_management.get_workspace(
                WorkspaceName(workspace_name)
            )
            
            if not workspace:
                raise WorkspaceNotFoundError(f"Workspace '{workspace_name}' not found")
            
            # Check if it's the active workspace
            is_active = await self._workspace_management.is_active_workspace(workspace.name)
            if is_active and not force:
                raise WorkspaceApplicationError(
                    "Cannot delete active workspace. Switch to another workspace first."
                )
            
            # Create backup if requested
            if backup_before_delete:
                backup_path = Path(f"./backup_{workspace_name}_{datetime.now().isoformat()}")
                await self.backup_workspace(WorkspaceBackupRequest(
                    workspace_name=workspace_name,
                    backup_path=backup_path
                ))
            
            # Clean up cross-domain data
            await self._cleanup_workspace_data(workspace)
            
            # Delete workspace
            await self._workspace_management.delete_workspace(workspace.name)
            
            return True
            
        except Exception as e:
            raise WorkspaceApplicationError(f"Failed to delete workspace: {e}") from e

    # Private helper methods
    
    async def _initialize_workspace_content(
        self, 
        workspace: Workspace, 
        request: WorkspaceCreationRequest
    ) -> None:
        """Initialize workspace with templates and styles based on mode."""
        if request.initialization_mode == WorkspaceInitializationMode.MINIMAL:
            return  # No additional setup
        
        if request.include_sample_templates:
            await self._template_management.initialize_workspace_templates(
                workspace,
                include_samples=(request.initialization_mode == WorkspaceInitializationMode.FULL)
            )
        
        if request.include_sample_styles:
            await self._style_management.initialize_workspace_styles(
                workspace,
                include_samples=(request.initialization_mode == WorkspaceInitializationMode.FULL)
            )

    async def _backup_workspace_content(
        self, 
        workspace: Workspace, 
        backup_path: Path
    ) -> None:
        """Backup workspace templates and styles."""
        templates = await self._template_management.list_templates(workspace)
        styles = await self._style_management.list_styles(workspace)
        
        content_backup = {
            "templates": [t.to_dict() for t in templates],
            "styles": [s.to_dict() for s in styles],
        }
        
        content_path = backup_path / "content.json"
        content_path.write_text(str(content_backup))

    async def _backup_workspace_analytics(
        self, 
        workspace: Workspace, 
        backup_path: Path
    ) -> None:
        """Backup workspace analytics data."""
        analytics = await self._workspace_analytics.export_workspace_data(workspace.name)
        token_usage = await self._token_analytics.export_workspace_data(workspace.name)
        
        analytics_path = backup_path / "analytics.json"
        analytics_path.write_text(str({
            "workspace_analytics": analytics,
            "token_usage": token_usage,
        }))

    async def _migrate_workspace_content(
        self, 
        source_workspace: Workspace, 
        target_name: WorkspaceName
    ) -> None:
        """Migrate content between workspaces."""
        # Get target workspace
        target_workspace = await self._workspace_management.get_workspace(target_name)
        
        # Migrate templates
        templates = await self._template_management.list_templates(source_workspace)
        for template in templates:
            await self._template_management.copy_template_to_workspace(
                template, target_workspace
            )
        
        # Migrate styles
        styles = await self._style_management.list_styles(source_workspace)
        for style in styles:
            await self._style_management.copy_style_to_workspace(
                style, target_workspace
            )

    async def _migrate_workspace_analytics(
        self, 
        source_workspace: Workspace, 
        target_name: WorkspaceName
    ) -> None:
        """Migrate analytics data between workspaces."""
        # Export from source
        analytics_data = await self._workspace_analytics.export_workspace_data(
            source_workspace.name
        )
        token_data = await self._token_analytics.export_workspace_data(
            source_workspace.name
        )
        
        # Import to target
        await self._workspace_analytics.import_workspace_data(target_name, analytics_data)
        await self._token_analytics.import_workspace_data(target_name, token_data)

    async def _enhance_workspace_report(
        self, 
        base_report: AnalyticsReport, 
        workspace: Workspace,
        request: WorkspaceReportRequest
    ) -> Dict[str, Any]:
        """Enhance workspace report with cross-domain data."""
        enhanced = {
            "workspace": workspace.name.value,
            "report_type": request.report_type.value,
            "generated_at": datetime.now(),
            "period": {
                "start": request.period_start,
                "end": request.period_end
            },
            "base_report": base_report.to_dict()
        }
        
        # Add content metrics
        templates = await self._template_management.list_templates(workspace)
        styles = await self._style_management.list_styles(workspace)
        
        enhanced["content_metrics"] = {
            "template_count": len(templates),
            "style_count": len(styles),
            "template_usage": await self._template_management.get_usage_statistics(workspace),
            "style_usage": await self._style_management.get_usage_statistics(workspace)
        }
        
        # Add execution metrics
        if request.report_type in [WorkspaceReportType.PERFORMANCE, WorkspaceReportType.SUMMARY]:
            cache_stats = await self._cache_management.get_workspace_cache_stats(workspace.name)
            token_usage = await self._token_analytics.get_workspace_usage(workspace.name)
            
            enhanced["execution_metrics"] = {
                "cache_performance": cache_stats.to_dict(),
                "token_usage": token_usage.to_dict(),
            }
        
        return enhanced

    async def _generate_workspace_recommendations(
        self, 
        workspace: Workspace, 
        report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations for workspace."""
        recommendations = []
        
        # Performance recommendations
        if "execution_metrics" in report:
            cache_hit_rate = report["execution_metrics"]["cache_performance"].get("hit_rate", 0)
            if cache_hit_rate < 0.3:
                recommendations.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "Low Cache Hit Rate",
                    "description": "Cache hit rate is below 30%. Consider enabling more aggressive caching.",
                    "action": "Review cache configuration and enable template caching"
                })
        
        # Cost recommendations
        if "execution_metrics" in report:
            monthly_cost = report["execution_metrics"]["token_usage"].get("monthly_cost", 0)
            if monthly_cost > 50:  # Example threshold
                recommendations.append({
                    "type": "cost",
                    "priority": "medium",
                    "title": "High Monthly Costs",
                    "description": f"Monthly token costs are ${monthly_cost:.2f}. Consider optimization.",
                    "action": "Review model selection and prompt optimization opportunities"
                })
        
        # Storage recommendations
        storage_usage = report.get("base_report", {}).get("resource_metrics", {}).get("storage_usage_mb", 0)
        if storage_usage > 1000:  # 1GB threshold
            recommendations.append({
                "type": "storage",
                "priority": "low",
                "title": "High Storage Usage",
                "description": f"Workspace storage is {storage_usage:.1f}MB. Consider cleanup.",
                "action": "Review and archive old pipeline runs and cache data"
            })
        
        return recommendations

    async def _cleanup_workspace_data(self, workspace: Workspace) -> None:
        """Clean up cross-domain data before workspace deletion."""
        # Clean up cache
        await self._cache_management.clear_workspace_cache(workspace.name)
        
        # Clean up token analytics
        await self._token_analytics.clear_workspace_data(workspace.name)
        
        # Clean up templates and styles
        await self._template_management.clear_workspace_templates(workspace)
        await self._style_management.clear_workspace_styles(workspace)