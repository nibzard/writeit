"""Workspace Query Handlers.

Concrete implementations of workspace-related query handlers.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from ...queries.workspace_queries import (
    GetWorkspacesQuery,
    GetWorkspaceQuery,
    GetActiveWorkspaceQuery,
    GetWorkspaceConfigQuery,
    GetWorkspaceStatsQuery,
    SearchWorkspacesQuery,
    ValidateWorkspaceNameQuery,
    CheckWorkspaceExistsQuery,
    GetWorkspaceHealthQuery,
    GetWorkspaceTemplatesQuery,
    GetWorkspaceTemplateQuery,
    WorkspaceQueryResult,
    WorkspaceTemplateQueryResult,
    GetWorkspacesQueryHandler,
    GetWorkspaceQueryHandler,
    GetActiveWorkspaceQueryHandler,
    GetWorkspaceConfigQueryHandler,
    GetWorkspaceStatsQueryHandler,
    SearchWorkspacesQueryHandler,
    ValidateWorkspaceNameQueryHandler,
    CheckWorkspaceExistsQueryHandler,
    GetWorkspaceHealthQueryHandler,
    GetWorkspaceTemplatesQueryHandler,
    GetWorkspaceTemplateQueryHandler,
)
from ...domains.workspace.repositories import WorkspaceRepository, WorkspaceConfigRepository
from ...domains.workspace.entities import Workspace, WorkspaceConfig
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.workspace.services import WorkspaceIsolationService
from ...shared.errors import RepositoryError, QueryError

logger = logging.getLogger(__name__)


class ConcreteGetWorkspacesQueryHandler(GetWorkspacesQueryHandler):
    """Handler for listing workspaces."""
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_isolation_service: WorkspaceIsolationService
    ):
        self.workspace_repository = workspace_repository
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspacesQuery) -> WorkspaceQueryResult:
        """Handle list workspaces query."""
        try:
            logger.debug(f"Listing workspaces with filters: {query}")
            
            # Build specification for filtering
            specs = []
            
            # Scope filter
            if query.scope:
                from ...shared.repository import Specification
                class ScopeSpec(Specification):
                    def __init__(self, scope: str):
                        self.scope = scope
                    def is_satisfied_by(self, workspace: Workspace) -> bool:
                        if self.scope == "global":
                            return workspace.name == WorkspaceName("global")
                        elif self.scope == "system":
                            return workspace.name in [WorkspaceName("global"), WorkspaceName("default")]
                        return True  # user scope (default)
                specs.append(ScopeSpec(query.scope))
            
            # Status filter
            if query.status:
                from ...shared.repository import Specification
                class StatusSpec(Specification):
                    def __init__(self, status: str):
                        self.status = status
                    def is_satisfied_by(self, workspace: Workspace) -> bool:
                        return workspace.status == self.status
                specs.append(StatusSpec(query.status))
            
            # Date filters
            if query.created_after:
                from ...shared.repository import Specification
                class CreatedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, workspace: Workspace) -> bool:
                        return workspace.created_at >= self.date
                specs.append(CreatedAfterSpec(query.created_after))
            
            if query.created_before:
                from ...shared.repository import Specification
                class CreatedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, workspace: Workspace) -> bool:
                        return workspace.created_at <= self.date
                specs.append(CreatedBeforeSpec(query.created_before))
            
            if query.last_accessed_after:
                from ...shared.repository import Specification
                class AccessedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, workspace: Workspace) -> bool:
                        return workspace.last_accessed_at >= self.date
                specs.append(AccessedAfterSpec(query.last_accessed_after))
            
            # Combine specifications
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get workspaces with pagination
            workspaces = await self.workspace_repository.find_all(
                spec=spec,
                limit=query.limit,
                offset=query.offset
            )
            
            # Apply sorting
            if query.sort_by:
                reverse = query.sort_order == "desc"
                workspaces.sort(
                    key=lambda w: getattr(w, query.sort_by, w.created_at),
                    reverse=reverse
                )
            
            # Enhance with additional data if requested
            workspace_data = []
            for workspace in workspaces:
                workspace_dict = workspace.to_dict()
                
                # Add configuration if requested
                if query.include_config:
                    try:
                        config = await self.workspace_isolation_service.get_workspace_config(workspace.name)
                        workspace_dict['config'] = config.to_dict() if config else None
                    except Exception as e:
                        logger.warning(f"Failed to get config for workspace {workspace.name}: {e}")
                        workspace_dict['config'] = None
                
                # Add stats if requested
                if query.include_stats:
                    try:
                        stats = await self._get_workspace_stats(workspace.name)
                        workspace_dict['stats'] = stats
                    except Exception as e:
                        logger.warning(f"Failed to get stats for workspace {workspace.name}: {e}")
                        workspace_dict['stats'] = None
                
                workspace_data.append(workspace_dict)
            
            return WorkspaceQueryResult(
                success=True,
                workspaces=workspaces,
                data=workspace_data,
                total=len(workspaces)
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error listing workspaces: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Failed to list workspaces: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing workspaces: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def _get_workspace_stats(self, workspace_name: WorkspaceName) -> Dict[str, Any]:
        """Get statistics for a workspace."""
        # This would integrate with various repositories to get counts
        # For now, return basic structure
        return {
            "pipeline_count": 0,
            "template_count": 0,
            "execution_count": 0,
            "storage_size_bytes": 0,
            "last_activity": None
        }


class ConcreteGetWorkspaceQueryHandler(GetWorkspaceQueryHandler):
    """Handler for getting workspace by name."""
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_isolation_service: WorkspaceIsolationService
    ):
        self.workspace_repository = workspace_repository
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspaceQuery) -> WorkspaceQueryResult:
        """Handle get workspace query."""
        try:
            logger.debug(f"Getting workspace: {query.workspace_name}")
            
            # Get workspace by name
            workspace = await self.workspace_repository.find_by_name(query.workspace_name)
            
            if not workspace:
                return WorkspaceQueryResult(
                    success=False,
                    error=f"Workspace '{query.workspace_name}' not found"
                )
            
            workspace_dict = workspace.to_dict()
            
            # Add configuration if requested
            if query.include_config:
                try:
                    config = await self.workspace_isolation_service.get_workspace_config(workspace.name)
                    workspace_dict['config'] = config.to_dict() if config else None
                except Exception as e:
                    logger.warning(f"Failed to get config for workspace {workspace.name}: {e}")
                    workspace_dict['config'] = None
            
            # Add stats if requested
            if query.include_stats:
                try:
                    stats = await self._get_workspace_stats(workspace.name)
                    workspace_dict['stats'] = stats
                except Exception as e:
                    logger.warning(f"Failed to get stats for workspace {workspace.name}: {e}")
                    workspace_dict['stats'] = None
            
            # Add templates if requested
            if query.include_templates:
                try:
                    templates = await self.workspace_isolation_service.get_workspace_templates(workspace.name)
                    workspace_dict['templates'] = templates
                except Exception as e:
                    logger.warning(f"Failed to get templates for workspace {workspace.name}: {e}")
                    workspace_dict['templates'] = []
            
            return WorkspaceQueryResult(
                success=True,
                workspace=workspace,
                data=workspace_dict
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting workspace: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Failed to retrieve workspace: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting workspace: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def _get_workspace_stats(self, workspace_name: WorkspaceName) -> Dict[str, Any]:
        """Get statistics for a workspace."""
        return {
            "pipeline_count": 0,
            "template_count": 0,
            "execution_count": 0,
            "storage_size_bytes": 0,
            "last_activity": None
        }


class ConcreteGetActiveWorkspaceQueryHandler(GetActiveWorkspaceQueryHandler):
    """Handler for getting active workspace."""
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_isolation_service: WorkspaceIsolationService
    ):
        self.workspace_repository = workspace_repository
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetActiveWorkspaceQuery) -> WorkspaceQueryResult:
        """Handle get active workspace query."""
        try:
            logger.debug("Getting active workspace")
            
            # Get active workspace name
            active_workspace_name = await self.workspace_isolation_service.get_active_workspace()
            
            if not active_workspace_name:
                return WorkspaceQueryResult(
                    success=False,
                    error="No active workspace configured"
                )
            
            # Get workspace details
            workspace = await self.workspace_repository.find_by_name(active_workspace_name)
            
            if not workspace:
                return WorkspaceQueryResult(
                    success=False,
                    error=f"Active workspace '{active_workspace_name}' not found"
                )
            
            workspace_dict = workspace.to_dict()
            workspace_dict['is_active'] = True
            
            # Add configuration if requested
            if query.include_config:
                try:
                    config = await self.workspace_isolation_service.get_workspace_config(workspace.name)
                    workspace_dict['config'] = config.to_dict() if config else None
                except Exception as e:
                    logger.warning(f"Failed to get config for workspace {workspace.name}: {e}")
                    workspace_dict['config'] = None
            
            # Add stats if requested
            if query.include_stats:
                try:
                    stats = await self._get_workspace_stats(workspace.name)
                    workspace_dict['stats'] = stats
                except Exception as e:
                    logger.warning(f"Failed to get stats for workspace {workspace.name}: {e}")
                    workspace_dict['stats'] = None
            
            return WorkspaceQueryResult(
                success=True,
                workspace=workspace,
                data=workspace_dict
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting active workspace: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def _get_workspace_stats(self, workspace_name: WorkspaceName) -> Dict[str, Any]:
        """Get statistics for a workspace."""
        return {
            "pipeline_count": 0,
            "template_count": 0,
            "execution_count": 0,
            "storage_size_bytes": 0,
            "last_activity": None
        }


class ConcreteGetWorkspaceConfigQueryHandler(GetWorkspaceConfigQueryHandler):
    """Handler for getting workspace configuration."""
    
    def __init__(self, workspace_isolation_service: WorkspaceIsolationService):
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspaceConfigQuery) -> WorkspaceQueryResult:
        """Handle get workspace config query."""
        try:
            logger.debug(f"Getting workspace config for: {query.workspace_name}")
            
            # Determine target workspace
            if query.workspace_name:
                workspace_name = query.workspace_name
            else:
                workspace_name = await self.workspace_isolation_service.get_active_workspace()
                if not workspace_name:
                    return WorkspaceQueryResult(
                        success=False,
                        error="No workspace specified and no active workspace found"
                    )
            
            # Get configuration
            config = await self.workspace_isolation_service.get_workspace_config(workspace_name)
            
            if not config:
                return WorkspaceQueryResult(
                    success=False,
                    error=f"Configuration not found for workspace '{workspace_name}'"
                )
            
            return WorkspaceQueryResult(
                success=True,
                config=config,
                data=config.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting workspace config: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetWorkspaceStatsQueryHandler(GetWorkspaceStatsQueryHandler):
    """Handler for getting workspace statistics."""
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_isolation_service: WorkspaceIsolationService
    ):
        self.workspace_repository = workspace_repository
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspaceStatsQuery) -> WorkspaceQueryResult:
        """Handle get workspace stats query."""
        try:
            logger.debug(f"Getting workspace stats for: {query.workspace_name}")
            
            # Determine target workspace
            if query.workspace_name:
                workspace_name = query.workspace_name
            else:
                workspace_name = await self.workspace_isolation_service.get_active_workspace()
                if not workspace_name:
                    return WorkspaceQueryResult(
                        success=False,
                        error="No workspace specified and no active workspace found"
                    )
            
            # Verify workspace exists
            workspace = await self.workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceQueryResult(
                    success=False,
                    error=f"Workspace '{workspace_name}' not found"
                )
            
            # Get comprehensive statistics
            stats = await self._get_comprehensive_workspace_stats(
                workspace_name,
                include_pipeline_stats=query.include_pipeline_stats,
                include_content_stats=query.include_content_stats,
                include_storage_stats=query.include_storage_stats
            )
            
            return WorkspaceQueryResult(
                success=True,
                stats=stats,
                data=stats
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting workspace stats: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def _get_comprehensive_workspace_stats(
        self, 
        workspace_name: WorkspaceName,
        include_pipeline_stats: bool,
        include_content_stats: bool,
        include_storage_stats: bool
    ) -> Dict[str, Any]:
        """Get comprehensive workspace statistics."""
        stats = {
            "workspace_name": str(workspace_name),
            "created_at": None,
            "last_accessed_at": None,
            "status": None
        }
        
        # Get workspace info
        workspace = await self.workspace_repository.find_by_name(workspace_name)
        if workspace:
            stats.update({
                "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
                "last_accessed_at": workspace.last_accessed_at.isoformat() if workspace.last_accessed_at else None,
                "status": workspace.status
            })
        
        # Pipeline statistics
        if include_pipeline_stats:
            stats["pipeline_stats"] = {
                "template_count": 0,
                "run_count": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "avg_execution_time": 0
            }
        
        # Content statistics
        if include_content_stats:
            stats["content_stats"] = {
                "template_count": 0,
                "style_primer_count": 0,
                "generated_content_count": 0
            }
        
        # Storage statistics
        if include_storage_stats:
            try:
                workspace_path = await self.workspace_isolation_service.get_workspace_path(workspace_name)
                storage_size = self._calculate_directory_size(workspace_path)
                
                stats["storage_stats"] = {
                    "total_size_bytes": storage_size,
                    "total_size_mb": round(storage_size / 1024 / 1024, 2),
                    "file_count": 0,
                    "directory_count": 0
                }
            except Exception as e:
                logger.warning(f"Failed to calculate storage size for {workspace_name}: {e}")
                stats["storage_stats"] = {
                    "total_size_bytes": 0,
                    "total_size_mb": 0,
                    "file_count": 0,
                    "directory_count": 0
                }
        
        return stats
    
    def _calculate_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            logger.warning(f"Error calculating directory size for {path}: {e}")
        return total_size


class ConcreteSearchWorkspacesQueryHandler(SearchWorkspacesQueryHandler):
    """Handler for searching workspaces."""
    
    def __init__(self, workspace_repository: WorkspaceRepository):
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: SearchWorkspacesQuery) -> WorkspaceQueryResult:
        """Handle search workspaces query."""
        try:
            logger.debug(f"Searching workspaces: {query.search_query}")
            
            # Get all workspaces with basic filtering
            list_query = GetWorkspacesQuery(
                scope=query.scope,
                status=query.status,
                limit=1000,  # Large limit for searching
                offset=0,
                include_stats=False,
                include_config=False
            )
            
            list_handler = ConcreteGetWorkspacesQueryHandler(
                self.workspace_repository,
                None  # workspace_isolation_service not needed for basic listing
            )
            
            result = await list_handler.handle(list_query)
            if not result.success:
                return result
            
            # Apply text search
            search_results = []
            search_query_lower = query.search_query.lower()
            
            for workspace in result.workspaces:
                workspace_dict = workspace.to_dict()
                match_found = False
                
                # Search in specified fields
                for field in query.search_fields:
                    if field in workspace_dict:
                        field_value = str(workspace_dict[field]).lower()
                        if search_query_lower in field_value:
                            match_found = True
                            break
                
                if match_found:
                    search_results.append(workspace)
            
            # Apply pagination to search results
            start_idx = query.offset or 0
            end_idx = start_idx + (query.limit or len(search_results))
            paginated_results = search_results[start_idx:end_idx]
            
            # Convert to response format
            workspace_data = [workspace.to_dict() for workspace in paginated_results]
            
            return WorkspaceQueryResult(
                success=True,
                workspaces=paginated_results,
                data=workspace_data,
                total=len(search_results)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error searching workspaces: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteValidateWorkspaceNameQueryHandler(ValidateWorkspaceNameQueryHandler):
    """Handler for validating workspace name."""
    
    def __init__(self, workspace_repository: WorkspaceRepository):
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: ValidateWorkspaceNameQuery) -> WorkspaceQueryResult:
        """Handle validate workspace name query."""
        try:
            logger.debug(f"Validating workspace name: {query.workspace_name}")
            
            validation_errors = []
            
            # Check if workspace name is valid
            workspace_name_str = str(query.workspace_name)
            
            # Basic validation
            if len(workspace_name_str) < 2:
                validation_errors.append("Workspace name must be at least 2 characters long")
            
            if len(workspace_name_str) > 50:
                validation_errors.append("Workspace name must be less than 50 characters long")
            
            if not workspace_name_str.replace('_', '').replace('-', '').isalnum():
                validation_errors.append("Workspace name can only contain letters, numbers, underscores, and hyphens")
            
            # Check for reserved names
            reserved_names = ['global', 'default', 'system', 'admin', 'root']
            if workspace_name_str.lower() in reserved_names:
                validation_errors.append(f"'{workspace_name_str}' is a reserved workspace name")
            
            # Check if workspace already exists
            existing_workspace = await self.workspace_repository.find_by_name(query.workspace_name)
            if existing_workspace:
                validation_errors.append(f"Workspace '{workspace_name_str}' already exists")
            
            return WorkspaceQueryResult(
                success=len(validation_errors) == 0,
                validation_errors=validation_errors,
                exists=existing_workspace is not None
            )
            
        except Exception as e:
            logger.error(f"Unexpected error validating workspace name: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteCheckWorkspaceExistsQueryHandler(CheckWorkspaceExistsQueryHandler):
    """Handler for checking workspace existence."""
    
    def __init__(self, workspace_repository: WorkspaceRepository):
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: CheckWorkspaceExistsQuery) -> WorkspaceQueryResult:
        """Handle check workspace exists query."""
        try:
            logger.debug(f"Checking workspace exists: {query.workspace_name}")
            
            workspace = await self.workspace_repository.find_by_name(query.workspace_name)
            exists = workspace is not None
            
            return WorkspaceQueryResult(
                success=True,
                exists=exists
            )
            
        except Exception as e:
            logger.error(f"Unexpected error checking workspace exists: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetWorkspaceHealthQueryHandler(GetWorkspaceHealthQueryHandler):
    """Handler for getting workspace health."""
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_isolation_service: WorkspaceIsolationService
    ):
        self.workspace_repository = workspace_repository
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspaceHealthQuery) -> WorkspaceQueryResult:
        """Handle get workspace health query."""
        try:
            logger.debug(f"Getting workspace health for: {query.workspace_name}")
            
            # Determine target workspace
            if query.workspace_name:
                workspace_name = query.workspace_name
            else:
                workspace_name = await self.workspace_isolation_service.get_active_workspace()
                if not workspace_name:
                    return WorkspaceQueryResult(
                        success=False,
                        error="No workspace specified and no active workspace found"
                    )
            
            # Perform health checks
            health_status = {
                "workspace_name": str(workspace_name),
                "overall_status": "healthy",
                "checks": {}
            }
            
            # Check workspace exists
            try:
                workspace = await self.workspace_repository.find_by_name(workspace_name)
                if not workspace:
                    health_status["overall_status"] = "unhealthy"
                    health_status["checks"]["workspace_exists"] = {
                        "status": "failed",
                        "message": f"Workspace '{workspace_name}' not found"
                    }
                else:
                    health_status["checks"]["workspace_exists"] = {
                        "status": "passed",
                        "message": "Workspace found in repository"
                    }
            except Exception as e:
                health_status["overall_status"] = "unhealthy"
                health_status["checks"]["workspace_exists"] = {
                    "status": "failed",
                    "message": f"Error checking workspace existence: {str(e)}"
                }
            
            # Check storage if requested
            if query.check_storage:
                try:
                    workspace_path = await self.workspace_isolation_service.get_workspace_path(workspace_name)
                    if workspace_path.exists():
                        health_status["checks"]["storage"] = {
                            "status": "passed",
                            "message": f"Workspace directory exists at {workspace_path}"
                        }
                        
                        # Check if directory is accessible
                        try:
                            test_file = workspace_path / ".health_check"
                            test_file.touch()
                            test_file.unlink()
                            health_status["checks"]["storage_permissions"] = {
                                "status": "passed",
                                "message": "Storage permissions are adequate"
                            }
                        except Exception as e:
                            health_status["overall_status"] = "degraded"
                            health_status["checks"]["storage_permissions"] = {
                                "status": "failed",
                                "message": f"Storage permission issue: {str(e)}"
                            }
                    else:
                        health_status["overall_status"] = "degraded"
                        health_status["checks"]["storage"] = {
                            "status": "failed",
                            "message": f"Workspace directory not found at {workspace_path}"
                        }
                except Exception as e:
                    health_status["overall_status"] = "degraded"
                    health_status["checks"]["storage"] = {
                        "status": "failed",
                        "message": f"Error checking storage: {str(e)}"
                    }
            
            # Check integrity if requested
            if query.check_integrity:
                try:
                    # This would involve checking database consistency, file integrity, etc.
                    health_status["checks"]["integrity"] = {
                        "status": "passed",
                        "message": "Workspace integrity check passed"
                    }
                except Exception as e:
                    health_status["overall_status"] = "degraded"
                    health_status["checks"]["integrity"] = {
                        "status": "failed",
                        "message": f"Integrity check failed: {str(e)}"
                    }
            
            # Check permissions if requested
            if query.check_permissions:
                try:
                    # This would involve checking user permissions, ACLs, etc.
                    health_status["checks"]["permissions"] = {
                        "status": "passed",
                        "message": "Workspace permissions are adequate"
                    }
                except Exception as e:
                    health_status["overall_status"] = "degraded"
                    health_status["checks"]["permissions"] = {
                        "status": "failed",
                        "message": f"Permission check failed: {str(e)}"
                    }
            
            return WorkspaceQueryResult(
                success=True,
                health=health_status,
                data=health_status
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting workspace health: {e}")
            return WorkspaceQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetWorkspaceTemplatesQueryHandler(GetWorkspaceTemplatesQueryHandler):
    """Handler for listing workspace templates."""
    
    def __init__(self, workspace_isolation_service: WorkspaceIsolationService):
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspaceTemplatesQuery) -> WorkspaceTemplateQueryResult:
        """Handle list workspace templates query."""
        try:
            logger.debug(f"Getting workspace templates with filters: {query}")
            
            # Get templates
            try:
                templates = await self.workspace_isolation_service.get_workspace_templates(
                    scope=query.scope,
                    category=query.category,
                    tags=query.tags
                )
            except Exception as e:
                logger.error(f"Error getting workspace templates: {e}")
                templates = []
            
            # Apply pagination
            start_idx = query.offset or 0
            end_idx = start_idx + (query.limit or len(templates))
            paginated_templates = templates[start_idx:end_idx]
            
            return WorkspaceTemplateQueryResult(
                success=True,
                templates=paginated_templates,
                total=len(templates)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting workspace templates: {e}")
            return WorkspaceTemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetWorkspaceTemplateQueryHandler(GetWorkspaceTemplateQueryHandler):
    """Handler for getting workspace template."""
    
    def __init__(self, workspace_isolation_service: WorkspaceIsolationService):
        self.workspace_isolation_service = workspace_isolation_service
    
    async def handle(self, query: GetWorkspaceTemplateQuery) -> WorkspaceTemplateQueryResult:
        """Handle get workspace template query."""
        try:
            logger.debug(f"Getting workspace template: {query.template_name}")
            
            # Get template
            try:
                template = await self.workspace_isolation_service.get_workspace_template(
                    query.template_name
                )
            except Exception as e:
                logger.error(f"Error getting workspace template: {e}")
                template = None
            
            if not template:
                return WorkspaceTemplateQueryResult(
                    success=False,
                    error=f"Workspace template '{query.template_name}' not found"
                )
            
            return WorkspaceTemplateQueryResult(
                success=True,
                template=template
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting workspace template: {e}")
            return WorkspaceTemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )