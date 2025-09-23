"""Workspace template resolution service.

Domain service responsible for template resolution across workspace scopes,
managing template visibility, and coordinating with the content domain.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from ..entities.workspace import Workspace
from ..value_objects.workspace_name import WorkspaceName
from ..repositories.workspace_repository import WorkspaceRepository
from ...content.repositories.content_template_repository import ContentTemplateRepository
from ...content.entities.template import Template
from ...content.value_objects.template_name import TemplateName
from ...content.value_objects.content_type import ContentType
from ....shared.repository import RepositoryError


class TemplateScope(Enum):
    """Template resolution scope enumeration."""
    WORKSPACE_ONLY = "workspace_only"
    GLOBAL_ONLY = "global_only"
    WORKSPACE_FIRST = "workspace_first"  # Workspace, then global
    GLOBAL_FIRST = "global_first"  # Global, then workspace
    ALL_SCOPES = "all_scopes"  # Both workspace and global


class TemplateVisibility(Enum):
    """Template visibility levels."""
    PRIVATE = "private"  # Workspace-only
    SHARED = "shared"  # Available across workspaces
    GLOBAL = "global"  # System-wide templates


@dataclass(frozen=True)
class TemplateResolutionResult:
    """Result of template resolution operation."""
    template: Template
    workspace_name: Optional[WorkspaceName]
    scope: TemplateScope
    is_global: bool
    path: Path
    
    @property
    def display_name(self) -> str:
        """Human-readable template location."""
        if self.is_global:
            return f"{self.template.name.value} [Global]"
        elif self.workspace_name:
            return f"{self.template.name.value} [Workspace: {self.workspace_name.value}]"
        else:
            return self.template.name.value


@dataclass
class TemplateSearchCriteria:
    """Criteria for template search operations."""
    name_pattern: Optional[str] = None
    content_type: Optional[ContentType] = None
    tags: Optional[List[str]] = None
    scope: TemplateScope = TemplateScope.WORKSPACE_FIRST
    include_global: bool = True
    workspace_names: Optional[List[WorkspaceName]] = None


class WorkspaceTemplateError(Exception):
    """Base exception for workspace template operations."""
    pass


class TemplateNotFoundError(WorkspaceTemplateError):
    """Template could not be found in specified scope."""
    
    def __init__(self, name: TemplateName, scope: TemplateScope, workspace: Optional[WorkspaceName] = None):
        self.name = name
        self.scope = scope
        self.workspace = workspace
        
        workspace_info = f" in workspace '{workspace.value}'" if workspace else ""
        super().__init__(f"Template '{name.value}' not found in scope '{scope.value}'{workspace_info}")


class TemplateConflictError(WorkspaceTemplateError):
    """Template conflicts exist between scopes."""
    
    def __init__(self, name: TemplateName, conflicting_workspaces: List[WorkspaceName]):
        self.name = name
        self.conflicting_workspaces = conflicting_workspaces
        
        workspaces_str = ", ".join(ws.value for ws in conflicting_workspaces)
        super().__init__(f"Template '{name.value}' conflicts found in workspaces: {workspaces_str}")


class WorkspaceTemplateService:
    """Domain service for workspace-aware template resolution.
    
    This service coordinates template resolution across workspace boundaries,
    manages template visibility, and provides workspace-aware template operations.
    It bridges the workspace and content domains while maintaining proper isolation.
    """
    
    def __init__(
        self, 
        workspace_repository: WorkspaceRepository,
        content_template_repository: ContentTemplateRepository
    ):
        """Initialize workspace template service.
        
        Args:
            workspace_repository: Repository for workspace operations
            content_template_repository: Repository for template content operations
        """
        self._workspace_repository = workspace_repository
        self._content_template_repository = content_template_repository
    
    async def resolve_template(
        self, 
        name: TemplateName, 
        workspace_name: Optional[WorkspaceName] = None,
        scope: TemplateScope = TemplateScope.WORKSPACE_FIRST
    ) -> Optional[TemplateResolutionResult]:
        """Resolve a template by name across workspace scopes.
        
        Args:
            name: Template name to resolve
            workspace_name: Workspace to search in (None for current)
            scope: Resolution scope strategy
            
        Returns:
            TemplateResolutionResult if found, None otherwise
            
        Raises:
            WorkspaceTemplateError: If resolution operation fails
        """
        try:
            # Determine target workspace
            if workspace_name is None:
                workspace_name = await self._get_current_workspace()
            
            # Execute resolution strategy based on scope
            if scope == TemplateScope.WORKSPACE_ONLY:
                return await self._resolve_workspace_only(name, workspace_name)
            elif scope == TemplateScope.GLOBAL_ONLY:
                return await self._resolve_global_only(name)
            elif scope == TemplateScope.WORKSPACE_FIRST:
                return await self._resolve_workspace_first(name, workspace_name)
            elif scope == TemplateScope.GLOBAL_FIRST:
                return await self._resolve_global_first(name, workspace_name)
            else:
                raise ValueError(f"Unsupported resolution scope: {scope}")
                
        except RepositoryError as e:
            raise WorkspaceTemplateError(f"Template resolution failed: {e}") from e
    
    async def list_available_templates(
        self, 
        workspace_name: Optional[WorkspaceName] = None,
        scope: TemplateScope = TemplateScope.ALL_SCOPES,
        content_type: Optional[ContentType] = None
    ) -> List[TemplateResolutionResult]:
        """List all available templates in specified scope.
        
        Args:
            workspace_name: Workspace to search in (None for current)
            scope: Scope to list templates from
            content_type: Filter by content type
            
        Returns:
            List of available templates with resolution metadata
            
        Raises:
            WorkspaceTemplateError: If listing operation fails
        """
        try:
            results = []
            
            # Determine target workspace
            if workspace_name is None:
                workspace_name = await self._get_current_workspace()
            
            # Collect templates based on scope
            if scope in (TemplateScope.WORKSPACE_ONLY, TemplateScope.ALL_SCOPES):
                workspace_templates = await self._list_workspace_templates(
                    workspace_name, content_type
                )
                results.extend(workspace_templates)
            
            if scope in (TemplateScope.GLOBAL_ONLY, TemplateScope.ALL_SCOPES):
                global_templates = await self._list_global_templates(content_type)
                results.extend(global_templates)
            
            # Remove duplicates (workspace takes precedence)
            seen_names = set()
            unique_results = []
            
            # Sort to ensure workspace templates come first
            results.sort(key=lambda r: (r.is_global, r.template.name.value))
            
            for result in results:
                if result.template.name not in seen_names:
                    unique_results.append(result)
                    seen_names.add(result.template.name)
            
            return unique_results
            
        except RepositoryError as e:
            raise WorkspaceTemplateError(f"Template listing failed: {e}") from e
    
    async def search_templates(
        self, 
        criteria: TemplateSearchCriteria
    ) -> List[TemplateResolutionResult]:
        """Search templates using specified criteria.
        
        Args:
            criteria: Search criteria and filters
            
        Returns:
            List of matching templates with resolution metadata
            
        Raises:
            WorkspaceTemplateError: If search operation fails
        """
        try:
            all_templates = await self.list_available_templates(
                scope=criteria.scope
            )
            
            # Apply filters
            filtered_results = []
            
            for result in all_templates:
                if self._matches_criteria(result, criteria):
                    filtered_results.append(result)
            
            return filtered_results
            
        except RepositoryError as e:
            raise WorkspaceTemplateError(f"Template search failed: {e}") from e
    
    async def validate_template_accessibility(
        self, 
        name: TemplateName,
        requesting_workspace: WorkspaceName
    ) -> bool:
        """Validate if template is accessible from requesting workspace.
        
        Args:
            name: Template name to check
            requesting_workspace: Workspace requesting access
            
        Returns:
            True if template is accessible, False otherwise
            
        Raises:
            WorkspaceTemplateError: If validation operation fails
        """
        try:
            # Try to resolve template from the requesting workspace
            result = await self.resolve_template(
                name, 
                requesting_workspace, 
                TemplateScope.WORKSPACE_FIRST
            )
            
            return result is not None
            
        except WorkspaceTemplateError:
            return False
    
    async def detect_template_conflicts(
        self, 
        workspace_names: Optional[List[WorkspaceName]] = None
    ) -> Dict[TemplateName, List[WorkspaceName]]:
        """Detect template name conflicts across workspaces.
        
        Args:
            workspace_names: Workspaces to check (None for all)
            
        Returns:
            Dictionary mapping template names to conflicting workspace names
            
        Raises:
            WorkspaceTemplateError: If conflict detection fails
        """
        try:
            if workspace_names is None:
                # Get all workspaces
                all_workspaces = await self._workspace_repository.find_all()
                workspace_names = [ws.name for ws in all_workspaces]
            
            # Track templates per workspace
            template_locations: Dict[TemplateName, List[WorkspaceName]] = {}
            
            for workspace_name in workspace_names:
                workspace_templates = await self._list_workspace_templates(
                    workspace_name, None
                )
                
                for result in workspace_templates:
                    template_name = result.template.name
                    if template_name not in template_locations:
                        template_locations[template_name] = []
                    template_locations[template_name].append(workspace_name)
            
            # Return only conflicts (templates in multiple workspaces)
            conflicts = {
                name: workspaces 
                for name, workspaces in template_locations.items() 
                if len(workspaces) > 1
            }
            
            return conflicts
            
        except RepositoryError as e:
            raise WorkspaceTemplateError(f"Conflict detection failed: {e}") from e
    
    async def get_template_visibility(
        self, 
        name: TemplateName,
        workspace_name: Optional[WorkspaceName] = None
    ) -> TemplateVisibility:
        """Determine template visibility level.
        
        Args:
            name: Template name to check
            workspace_name: Workspace context (None for current)
            
        Returns:
            TemplateVisibility level
            
        Raises:
            TemplateNotFoundError: If template not found
            WorkspaceTemplateError: If visibility determination fails
        """
        try:
            if workspace_name is None:
                workspace_name = await self._get_current_workspace()
            
            # Check if template exists globally
            global_result = await self._resolve_global_only(name)
            if global_result:
                return TemplateVisibility.GLOBAL
            
            # Check if template exists in workspace
            workspace_result = await self._resolve_workspace_only(name, workspace_name)
            if workspace_result:
                return TemplateVisibility.PRIVATE
            
            # Template not found
            raise TemplateNotFoundError(name, TemplateScope.ALL_SCOPES, workspace_name)
            
        except RepositoryError as e:
            raise WorkspaceTemplateError(f"Visibility determination failed: {e}") from e
    
    # Private helper methods
    
    async def _resolve_workspace_only(
        self, 
        name: TemplateName, 
        workspace_name: WorkspaceName
    ) -> Optional[TemplateResolutionResult]:
        """Resolve template from workspace scope only."""
        template = await self._content_template_repository.find_by_name_and_workspace(
            name, workspace_name
        )
        
        if template:
            return TemplateResolutionResult(
                template=template,
                workspace_name=workspace_name,
                scope=TemplateScope.WORKSPACE_ONLY,
                is_global=False,
                path=Path("workspace_templates") / workspace_name.value / f"{name.value}.yaml"
            )
        
        return None
    
    async def _resolve_global_only(
        self, 
        name: TemplateName
    ) -> Optional[TemplateResolutionResult]:
        """Resolve template from global scope only."""
        global_templates = await self._content_template_repository.find_global_templates()
        
        for template in global_templates:
            if template.name == name:
                return TemplateResolutionResult(
                    template=template,
                    workspace_name=None,
                    scope=TemplateScope.GLOBAL_ONLY,
                    is_global=True,
                    path=Path("global_templates") / f"{name.value}.yaml"
                )
        
        return None
    
    async def _resolve_workspace_first(
        self, 
        name: TemplateName, 
        workspace_name: WorkspaceName
    ) -> Optional[TemplateResolutionResult]:
        """Resolve template with workspace-first strategy."""
        # Try workspace first
        workspace_result = await self._resolve_workspace_only(name, workspace_name)
        if workspace_result:
            return workspace_result
        
        # Fall back to global
        return await self._resolve_global_only(name)
    
    async def _resolve_global_first(
        self, 
        name: TemplateName, 
        workspace_name: WorkspaceName
    ) -> Optional[TemplateResolutionResult]:
        """Resolve template with global-first strategy."""
        # Try global first
        global_result = await self._resolve_global_only(name)
        if global_result:
            return global_result
        
        # Fall back to workspace
        return await self._resolve_workspace_only(name, workspace_name)
    
    async def _list_workspace_templates(
        self, 
        workspace_name: WorkspaceName,
        content_type: Optional[ContentType] = None
    ) -> List[TemplateResolutionResult]:
        """List templates from specific workspace."""
        # Set workspace context in repository
        self._content_template_repository.set_workspace(workspace_name)
        
        try:
            if content_type:
                templates = await self._content_template_repository.find_by_content_type(content_type)
            else:
                templates = await self._content_template_repository.find_all()
            
            results = []
            for template in templates:
                result = TemplateResolutionResult(
                    template=template,
                    workspace_name=workspace_name,
                    scope=TemplateScope.WORKSPACE_ONLY,
                    is_global=False,
                    path=Path("workspace_templates") / workspace_name.value / f"{template.name.value}.yaml"
                )
                results.append(result)
            
            return results
        finally:
            # Reset workspace context
            self._content_template_repository.clear_workspace()
    
    async def _list_global_templates(
        self, 
        content_type: Optional[ContentType] = None
    ) -> List[TemplateResolutionResult]:
        """List templates from global scope."""
        global_templates = await self._content_template_repository.find_global_templates()
        
        results = []
        for template in global_templates:
            if content_type is None or template.content_type == content_type:
                result = TemplateResolutionResult(
                    template=template,
                    workspace_name=None,
                    scope=TemplateScope.GLOBAL_ONLY,
                    is_global=True,
                    path=Path("global_templates") / f"{template.name.value}.yaml"
                )
                results.append(result)
        
        return results
    
    async def _get_current_workspace(self) -> WorkspaceName:
        """Get current active workspace name."""
        # This would typically get the current workspace from context
        # For now, return default workspace
        return WorkspaceName("default")
    
    def _matches_criteria(
        self, 
        result: TemplateResolutionResult, 
        criteria: TemplateSearchCriteria
    ) -> bool:
        """Check if template result matches search criteria."""
        template = result.template
        
        # Name pattern matching
        if criteria.name_pattern:
            if criteria.name_pattern.lower() not in template.name.value.lower():
                return False
        
        # Content type matching
        if criteria.content_type:
            if template.content_type != criteria.content_type:
                return False
        
        # Tag matching
        if criteria.tags:
            if not any(tag in template.tags for tag in criteria.tags):
                return False
        
        # Global inclusion
        if not criteria.include_global and result.is_global:
            return False
        
        # Workspace filtering
        if criteria.workspace_names:
            if result.workspace_name not in criteria.workspace_names:
                return False
        
        return True
