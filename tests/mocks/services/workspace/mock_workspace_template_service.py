"""Mock implementation of WorkspaceTemplateService for testing."""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock

from writeit.domains.workspace.services.workspace_template_service import (
    WorkspaceTemplateService,
    TemplateScope,
    TemplateResolution,
    TemplateConflict
)
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.content.entities.template import Template
from writeit.domains.content.value_objects.template_name import TemplateName


class MockWorkspaceTemplateService(WorkspaceTemplateService):
    """Mock implementation of WorkspaceTemplateService.
    
    Provides configurable template resolution behavior for testing
    workspace template scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock template service."""
        self._mock = Mock()
        self._template_resolutions: Dict[str, TemplateResolution] = {}
        self._available_templates: Dict[str, List[Template]] = {}
        self._template_conflicts: List[TemplateConflict] = []
        self._should_fail = False
        
    def configure_template_resolution(
        self, 
        template_name: str, 
        resolution: TemplateResolution
    ) -> None:
        """Configure template resolution for specific template."""
        self._template_resolutions[template_name] = resolution
        
    def configure_available_templates(
        self, 
        workspace: str, 
        templates: List[Template]
    ) -> None:
        """Configure available templates for workspace."""
        self._available_templates[workspace] = templates
        
    def configure_template_conflicts(self, conflicts: List[TemplateConflict]) -> None:
        """Configure template conflicts to return."""
        self._template_conflicts = conflicts
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if template operations should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._template_resolutions.clear()
        self._available_templates.clear()
        self._template_conflicts.clear()
        self._should_fail = False
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def resolve_template(
        self,
        template_name: TemplateName,
        workspace: Workspace,
        scope: Optional[TemplateScope] = None
    ) -> Optional[TemplateResolution]:
        """Resolve template across scopes."""
        self._mock.resolve_template(template_name, workspace, scope)
        
        if self._should_fail:
            return None
            
        template_key = str(template_name.value)
        
        # Return configured resolution if available
        if template_key in self._template_resolutions:
            return self._template_resolutions[template_key]
            
        # Create mock resolution
        return TemplateResolution(
            template_name=template_name,
            resolved_scope=scope or TemplateScope.WORKSPACE,
            template_path=f"/mock/path/{template_name.value}.yaml",
            workspace=workspace.name
        )
        
    async def list_available_templates(
        self,
        workspace: Workspace,
        scope: Optional[TemplateScope] = None
    ) -> List[Template]:
        """List templates available in workspace."""
        self._mock.list_available_templates(workspace, scope)
        
        workspace_key = str(workspace.name.value)
        
        # Return configured templates if available
        if workspace_key in self._available_templates:
            return self._available_templates[workspace_key]
            
        # Return empty list
        return []
        
    async def check_template_conflicts(
        self,
        workspace: Workspace
    ) -> List[TemplateConflict]:
        """Check for template name conflicts."""
        self._mock.check_template_conflicts(workspace)
        
        return self._template_conflicts
        
    async def get_template_inheritance_chain(
        self,
        template_name: TemplateName,
        workspace: Workspace
    ) -> List[TemplateResolution]:
        """Get template inheritance chain."""
        self._mock.get_template_inheritance_chain(template_name, workspace)
        
        # Return simple mock chain
        base_resolution = TemplateResolution(
            template_name=template_name,
            resolved_scope=TemplateScope.GLOBAL,
            template_path=f"/global/{template_name.value}.yaml",
            workspace=None
        )
        
        workspace_resolution = TemplateResolution(
            template_name=template_name,
            resolved_scope=TemplateScope.WORKSPACE,
            template_path=f"/workspace/{workspace.name.value}/{template_name.value}.yaml",
            workspace=workspace.name
        )
        
        return [base_resolution, workspace_resolution]
        
    async def validate_template_scope(
        self,
        template: Template,
        target_scope: TemplateScope,
        workspace: Workspace
    ) -> List[str]:
        """Validate template can be used in target scope."""
        self._mock.validate_template_scope(template, target_scope, workspace)
        
        if self._should_fail:
            return ["Mock template scope validation error"]
            
        return []  # No validation errors
        
    async def copy_template_to_workspace(
        self,
        template_name: TemplateName,
        source_workspace: Optional[WorkspaceName],
        target_workspace: WorkspaceName
    ) -> bool:
        """Copy template between workspaces."""
        self._mock.copy_template_to_workspace(template_name, source_workspace, target_workspace)
        
        return not self._should_fail
        
    async def promote_template_to_global(
        self,
        template_name: TemplateName,
        workspace: Workspace
    ) -> bool:
        """Promote workspace template to global scope."""
        self._mock.promote_template_to_global(template_name, workspace)
        
        return not self._should_fail
        
    async def get_template_usage_stats(
        self,
        template_name: TemplateName,
        workspace: Optional[Workspace] = None
    ) -> Dict[str, Any]:
        """Get template usage statistics."""
        self._mock.get_template_usage_stats(template_name, workspace)
        
        return {
            "template_name": str(template_name.value),
            "usage_count": 42,
            "last_used": "2025-01-15T10:00:00Z",
            "workspaces_using": ["workspace1", "workspace2"],
            "total_executions": 100
        }
        
    async def find_template_dependencies(
        self,
        template_name: TemplateName,
        workspace: Workspace
    ) -> List[TemplateName]:
        """Find templates that depend on given template."""
        self._mock.find_template_dependencies(template_name, workspace)
        
        # Return mock dependencies
        return [
            TemplateName(f"dependent-template-1"),
            TemplateName(f"dependent-template-2")
        ]
        
    async def update_template_metadata(
        self,
        template_name: TemplateName,
        workspace: Workspace,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update template metadata."""
        self._mock.update_template_metadata(template_name, workspace, metadata)
        
        return not self._should_fail
