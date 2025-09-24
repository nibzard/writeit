"""Mock implementation of WorkspaceIsolationService for testing."""

from typing import Dict, List, Any, Optional, Set
from unittest.mock import Mock

from writeit.domains.workspace.services.workspace_isolation_service import (
    WorkspaceIsolationService,
    WorkspaceContext,
    WorkspaceIsolationError,
    IsolatedWorkspaceOperations
)
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName


class MockWorkspaceIsolationService(WorkspaceIsolationService):
    """Mock implementation of WorkspaceIsolationService.
    
    Provides configurable isolation behavior for testing workspace
    isolation scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock isolation service."""
        self._mock = Mock()
        self._isolation_violations: List[Dict[str, Any]] = []
        self._access_permissions: Dict[str, Set[str]] = {}
        self._should_fail = False
        self._isolation_level = "STRICT"
        
    def configure_isolation_violations(self, violations: List[Dict[str, Any]]) -> None:
        """Configure isolation violations to return."""
        self._isolation_violations = violations
        
    def configure_access_permissions(self, workspace: str, permissions: Set[str]) -> None:
        """Configure access permissions for workspace."""
        self._access_permissions[workspace] = permissions
        
    def configure_isolation_level(self, level: str) -> None:
        """Configure isolation level."""
        self._isolation_level = level
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if isolation checks should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._isolation_violations.clear()
        self._access_permissions.clear()
        self._should_fail = False
        self._isolation_level = "STRICT"
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def validate_workspace_isolation(
        self, 
        workspace: Workspace,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate workspace isolation."""
        self._mock.validate_workspace_isolation(workspace, context)
        
        if self._should_fail:
            return self._isolation_violations or [
                {
                    "workspace_name": workspace.name.value if hasattr(workspace.name, 'value') else str(workspace.name),
                    "violation_type": "access",
                    "description": "Mock isolation violation",
                    "severity": "error"
                }
            ]
            
        return self._isolation_violations
        
    async def check_cross_workspace_access(
        self,
        source_workspace: WorkspaceName,
        target_workspace: WorkspaceName,
        operation: str
    ) -> bool:
        """Check if cross-workspace access is allowed."""
        self._mock.check_cross_workspace_access(source_workspace, target_workspace, operation)
        
        if self._should_fail:
            return False
            
        # Check configured permissions
        source_perms = self._access_permissions.get(str(source_workspace.value), set())
        return f"{target_workspace.value}:{operation}" in source_perms or "*" in source_perms
        
    async def enforce_resource_limits(
        self,
        workspace: Workspace,
        resource_type: str,
        usage: Any
    ) -> bool:
        """Enforce resource limits for workspace."""
        self._mock.enforce_resource_limits(workspace, resource_type, usage)
        
        return not self._should_fail
        
    async def get_isolation_level(self, workspace: Workspace) -> str:
        """Get current isolation level for workspace."""
        self._mock.get_isolation_level(workspace)
        
        return self._isolation_level
        
    async def set_isolation_level(
        self,
        workspace: Workspace,
        level: str
    ) -> None:
        """Set isolation level for workspace."""
        self._mock.set_isolation_level(workspace, level)
        
        self._isolation_level = level
        
    async def create_isolation_boundary(
        self,
        workspace: Workspace,
        boundary_config: Dict[str, Any]
    ) -> str:
        """Create isolation boundary for workspace."""
        self._mock.create_isolation_boundary(workspace, boundary_config)
        
        return f"mock-boundary-{workspace.name.value}"
        
    async def remove_isolation_boundary(
        self,
        workspace: Workspace,
        boundary_id: str
    ) -> bool:
        """Remove isolation boundary."""
        self._mock.remove_isolation_boundary(workspace, boundary_id)
        
        return not self._should_fail
        
    async def audit_workspace_access(
        self,
        workspace: Workspace,
        time_period: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Audit workspace access patterns."""
        self._mock.audit_workspace_access(workspace, time_period)
        
        return [
            {
                "timestamp": "2025-01-15T10:00:00Z",
                "operation": "read",
                "resource": "template",
                "user": "test-user",
                "status": "allowed"
            }
        ]
        
    async def get_workspace_permissions(self, workspace: Workspace) -> Dict[str, Any]:
        """Get current workspace permissions."""
        self._mock.get_workspace_permissions(workspace)
        
        workspace_key = str(workspace.name.value)
        permissions = self._access_permissions.get(workspace_key, set())
        
        return {
            "workspace": workspace_key,
            "permissions": list(permissions),
            "isolation_level": self._isolation_level.value
        }
        
    async def update_workspace_permissions(
        self,
        workspace: Workspace,
        permissions: Dict[str, Any]
    ) -> None:
        """Update workspace permissions."""
        self._mock.update_workspace_permissions(workspace, permissions)
        
        workspace_key = str(workspace.name.value)
        self._access_permissions[workspace_key] = set(permissions.get("permissions", []))
