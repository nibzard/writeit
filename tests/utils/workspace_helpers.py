"""Workspace testing utilities.

Provides helpers for creating test workspaces, isolation testing,
and workspace-aware test scenarios.
"""

import tempfile
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any
from unittest.mock import Mock, AsyncMock

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration  
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.workspace import WorkspaceManager


class WorkspaceTestHelper:
    """Helper for workspace-related testing."""
    
    def __init__(self):
        self.temp_dirs: list[Path] = []
        self.workspaces: list[Workspace] = []
    
    def create_temp_workspace_root(self) -> Path:
        """Create a temporary workspace root directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix="writeit_workspace_test_"))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_test_workspace(
        self,
        name: str = "test-workspace",
        root_path: Optional[Path] = None,
        config: Optional[WorkspaceConfiguration] = None,
        is_active: bool = True
    ) -> Workspace:
        """Create a test workspace with proper setup."""
        if root_path is None:
            root_path = self.create_temp_workspace_root() / name
        
        if config is None:
            config = WorkspaceConfiguration.default()
        
        # Ensure workspace directory exists
        root_path.mkdir(parents=True, exist_ok=True)
        
        workspace_name = WorkspaceName(name)
        workspace_path = WorkspacePath.from_string(str(root_path))
        
        workspace = Workspace(
            name=workspace_name,
            root_path=workspace_path,
            configuration=config,
            is_active=is_active
        )
        
        # Mock initialization check for testing
        workspace.is_initialized = Mock(return_value=True)
        
        self.workspaces.append(workspace)
        return workspace
    
    def create_workspace_manager(self, root_path: Optional[Path] = None) -> WorkspaceManager:
        """Create a workspace manager for testing."""
        if root_path is None:
            root_path = self.create_temp_workspace_root()
        
        return WorkspaceManager(str(root_path))
    
    async def cleanup(self):
        """Clean up all test workspaces and temporary directories."""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        self.temp_dirs.clear()
        self.workspaces.clear()


def create_test_workspace(
    name: str = "test-workspace",
    root_path: Optional[Path] = None,
    **config_overrides
) -> Workspace:
    """Create a test workspace with optional configuration overrides.
    
    Args:
        name: Workspace name
        root_path: Optional root path (temp dir created if None)
        **config_overrides: Configuration overrides
    
    Returns:
        Configured test workspace
    """
    if root_path is None:
        root_path = Path(tempfile.mkdtemp(prefix=f"writeit_test_{name}_"))
    
    # Ensure directory exists
    root_path.mkdir(parents=True, exist_ok=True)
    
    # Create configuration with overrides
    config = WorkspaceConfiguration.default()
    if config_overrides:
        # Apply overrides to configuration
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    workspace_name = WorkspaceName(name)
    workspace_path = WorkspacePath.from_string(str(root_path))
    
    workspace = Workspace(
        name=workspace_name,
        root_path=workspace_path,
        configuration=config,
        is_active=True
    )
    
    # Mock initialization for testing
    workspace.is_initialized = Mock(return_value=True)
    
    return workspace


@asynccontextmanager
async def with_isolated_workspace(
    name: str = "isolated-test-workspace",
    **config_overrides
) -> AsyncGenerator[Workspace, None]:
    """Context manager for isolated workspace testing.
    
    Creates a temporary workspace, yields it for testing,
    and automatically cleans up afterward.
    
    Args:
        name: Workspace name
        **config_overrides: Configuration overrides
    
    Usage:
        async with with_isolated_workspace("my-test") as workspace:
            # Use workspace for testing
            assert workspace.name.value == "my-test"
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=f"writeit_isolated_{name}_"))
    
    try:
        workspace = create_test_workspace(
            name=name,
            root_path=temp_dir,
            **config_overrides
        )
        yield workspace
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


class MockWorkspaceRepository:
    """Mock workspace repository for testing."""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.integrity_errors: Dict[str, list[str]] = {}
        self.access_logs: list[tuple[str, str]] = []  # (workspace_name, operation)
    
    async def find_by_name(self, name: WorkspaceName) -> Optional[Workspace]:
        """Find workspace by name."""
        self.access_logs.append((name.value, "find_by_name"))
        return self.workspaces.get(name.value)
    
    async def save(self, workspace: Workspace) -> None:
        """Save workspace."""
        self.access_logs.append((workspace.name.value, "save"))
        self.workspaces[workspace.name.value] = workspace
    
    async def delete(self, workspace: Workspace) -> None:
        """Delete workspace."""
        self.access_logs.append((workspace.name.value, "delete"))
        if workspace.name.value in self.workspaces:
            del self.workspaces[workspace.name.value]
    
    async def list_all(self) -> list[Workspace]:
        """List all workspaces."""
        self.access_logs.append(("*", "list_all"))
        return list(self.workspaces.values())
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> list[str]:
        """Validate workspace integrity."""
        self.access_logs.append((workspace.name.value, "validate_integrity"))
        return self.integrity_errors.get(workspace.name.value, [])
    
    async def update_last_accessed(self, workspace: Workspace) -> None:
        """Update last accessed timestamp."""
        self.access_logs.append((workspace.name.value, "update_last_accessed"))
        # In real implementation, this would update the workspace
        pass
    
    # Test helper methods
    def add_workspace(self, workspace: Workspace) -> None:
        """Add a workspace to the mock repository."""
        self.workspaces[workspace.name.value] = workspace
    
    def set_integrity_errors(self, workspace_name: str, errors: list[str]) -> None:
        """Set integrity errors for a workspace."""
        self.integrity_errors[workspace_name] = errors
    
    def clear_access_logs(self) -> None:
        """Clear access logs."""
        self.access_logs.clear()
    
    def get_access_count(self, workspace_name: str, operation: str) -> int:
        """Get count of specific operations for a workspace."""
        return len([
            log for log in self.access_logs 
            if log[0] == workspace_name and log[1] == operation
        ])


class WorkspaceContextMock:
    """Mock workspace context for testing."""
    
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.resource_scope = "test"
        self.operation_id = "test-op-123"
        self.metadata = {"test": True}
        self.isolation_active = False
    
    async def __aenter__(self):
        self.isolation_active = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.isolation_active = False
    
    def get_workspace_path(self, subpath: str = "") -> str:
        """Get workspace path for testing."""
        if not self.isolation_active:
            raise RuntimeError("Cannot access workspace paths outside isolation context")
        
        base_path = self.workspace.root_path.path
        if subpath:
            return str(base_path / subpath)
        return str(base_path)
    
    def get_workspace_name(self) -> WorkspaceName:
        """Get workspace name."""
        return self.workspace.name


def create_workspace_config(**overrides) -> WorkspaceConfiguration:
    """Create a workspace configuration with overrides.
    
    Args:
        **overrides: Configuration values to override
    
    Returns:
        Workspace configuration with applied overrides
    """
    config = WorkspaceConfiguration.default()
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            # Handle nested configuration
            parts = key.split('.')
            current = config
            for part in parts[:-1]:
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    break
            else:
                setattr(current, parts[-1], value)
    
    return config


async def assert_workspace_isolation(
    workspace1: Workspace,
    workspace2: Workspace,
    operation: callable
) -> None:
    """Assert that operations on different workspaces are isolated.
    
    Args:
        workspace1: First workspace
        workspace2: Second workspace  
        operation: Operation to test for isolation
    
    Raises:
        AssertionError: If isolation is violated
    """
    # This is a framework for testing isolation
    # Implementation depends on specific isolation mechanisms
    pass


class WorkspaceTestFixtures:
    """Collection of common workspace test fixtures."""
    
    @staticmethod
    def minimal_workspace() -> Workspace:
        """Create minimal test workspace."""
        return create_test_workspace("minimal")
    
    @staticmethod
    def workspace_with_templates() -> Workspace:
        """Create workspace with template configuration."""
        return create_test_workspace(
            "with-templates",
            template_enabled=True,
            default_template_source="local"
        )
    
    @staticmethod
    def workspace_with_strict_isolation() -> Workspace:
        """Create workspace with strict isolation settings."""
        return create_test_workspace(
            "strict-isolation",
            isolation_enabled=True,
            security_mode="strict"
        )
    
    @staticmethod
    def workspace_collection() -> list[Workspace]:
        """Create a collection of test workspaces."""
        return [
            WorkspaceTestFixtures.minimal_workspace(),
            WorkspaceTestFixtures.workspace_with_templates(),
            WorkspaceTestFixtures.workspace_with_strict_isolation(),
        ]