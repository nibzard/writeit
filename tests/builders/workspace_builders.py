"""Test data builders for Workspace domain entities."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Self

from src.writeit.domains.workspace.entities.workspace import Workspace
from src.writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from src.writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from src.writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue


class WorkspaceConfigurationBuilder:
    """Builder for WorkspaceConfiguration test data."""
    
    def __init__(self) -> None:
        self._workspace_name = WorkspaceName("test_workspace")
        self._values = {}
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_workspace_name(self, name: str | WorkspaceName) -> Self:
        """Set the workspace name."""
        if isinstance(name, str):
            name = WorkspaceName(name)
        self._workspace_name = name
        return self
    
    def with_value(self, key: str, value: Any) -> Self:
        """Add a configuration value."""
        self._values[key] = ConfigurationValue(value)
        return self
    
    def with_values(self, values: Dict[str, Any]) -> Self:
        """Set multiple configuration values."""
        self._values = {k: ConfigurationValue(v) for k, v in values.items()}
        return self
    
    def with_llm_config(self, default_model: str = "gpt-4o-mini", api_key: str = "test-key") -> Self:
        """Add LLM configuration."""
        return (self
                .with_value("llm.default_model", default_model)
                .with_value("llm.api_key", api_key)
                .with_value("llm.timeout", 30)
                .with_value("llm.max_retries", 3))
    
    def with_ui_config(self, theme: str = "dark", auto_save: bool = True) -> Self:
        """Add UI configuration."""
        return (self
                .with_value("ui.theme", theme)
                .with_value("ui.auto_save", auto_save)
                .with_value("ui.show_tips", True))
    
    def with_execution_config(self, parallel: bool = False, cache_enabled: bool = True) -> Self:
        """Add execution configuration."""
        return (self
                .with_value("execution.allow_parallel", parallel)
                .with_value("execution.cache_enabled", cache_enabled)
                .with_value("execution.timeout", 300))
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> Self:
        """Set the configuration timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def build(self) -> WorkspaceConfiguration:
        """Build the WorkspaceConfiguration."""
        return WorkspaceConfiguration(
            values=self._values,
            created_at=self._created_at,
            updated_at=self._updated_at
        )
    
    @classmethod
    def default(cls, workspace_name: str = "test-workspace") -> Self:
        """Create a default workspace configuration."""
        return (cls()
                .with_workspace_name(workspace_name)
                .with_llm_config()
                .with_ui_config()
                .with_execution_config())
    
    @classmethod
    def minimal(cls, workspace_name: str = "minimal") -> Self:
        """Create a minimal workspace configuration."""
        return cls().with_workspace_name(workspace_name).with_value("minimal", True)
    
    @classmethod
    def with_custom_model(cls, workspace_name: str = "custom", model: str = "claude-3-haiku") -> Self:
        """Create a configuration with custom LLM model."""
        return (cls()
                .with_workspace_name(workspace_name)
                .with_llm_config(default_model=model)
                .with_ui_config()
                .with_execution_config())


class WorkspaceBuilder:
    """Builder for Workspace test data."""
    
    def __init__(self) -> None:
        self._name = WorkspaceName("test_workspace")
        self._path = WorkspacePath(Path("/tmp/test_workspace"))
        self._is_active = False
        self._metadata = {}
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._last_accessed = None
    
    def with_name(self, name: str | WorkspaceName) -> Self:
        """Set the workspace name."""
        if isinstance(name, str):
            name = WorkspaceName(name)
        self._name = name
        return self
    
    def with_path(self, path: str | WorkspacePath) -> Self:
        """Set the workspace path."""
        if isinstance(path, str):
            path = WorkspacePath.from_string(path)
        self._path = path
        return self
    
    def mark_active(self) -> Self:
        """Mark the workspace as active."""
        self._is_active = True
        self._last_accessed = datetime.now()
        return self
    
    def inactive(self) -> Self:
        """Mark the workspace as inactive."""
        self._is_active = False
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the workspace metadata."""
        self._metadata = metadata
        return self
    
    def with_description(self, description: str) -> Self:
        """Add a description to metadata."""
        self._metadata["description"] = description
        return self
    
    def with_tags(self, tags: list[str]) -> Self:
        """Add tags to metadata."""
        self._metadata["tags"] = tags
        return self
    
    def with_project_info(self, project_name: str, version: str = "1.0.0") -> Self:
        """Add project information to metadata."""
        self._metadata.update({
            "project_name": project_name,
            "project_version": version
        })
        return self
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> Self:
        """Set the workspace timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def with_last_accessed(self, last_accessed: datetime) -> Self:
        """Set the last accessed timestamp."""
        self._last_accessed = last_accessed
        return self
    
    def recently_accessed(self) -> Self:
        """Set the workspace as recently accessed."""
        self._last_accessed = datetime.now()
        return self
    
    def build(self) -> Workspace:
        """Build the Workspace."""
        from src.writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
        from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
        
        # Create a default configuration for the workspace
        default_config = WorkspaceConfiguration(
            values={},
            created_at=self._created_at,
            updated_at=self._updated_at
        )
        
        return Workspace(
            name=self._name,
            root_path=self._path,
            configuration=default_config,
            is_active=self._is_active,
            metadata=self._metadata,
            created_at=self._created_at,
            updated_at=self._updated_at,
            last_accessed=self._last_accessed
        )
    
    @classmethod
    def default(cls, name: str = "test-workspace") -> Self:
        """Create a default workspace builder."""
        return (cls()
                .with_name(name)
                .with_path(f"/tmp/{name}")
                .with_description("Default test workspace"))
    
    @classmethod
    def active(cls, name: str = "active_workspace") -> Self:
        """Create an active workspace builder."""
        return (cls()
                .with_name(name)
                .with_path(f"/tmp/{name}")
                .mark_active()
                .recently_accessed()
                .with_description("Active test workspace"))
    
    @classmethod
    def project_workspace(cls, name: str = "project", project_name: str = "TestProject") -> Self:
        """Create a project workspace builder."""
        return (cls()
                .with_name(name)
                .with_path(f"/projects/{name}")
                .with_project_info(project_name)
                .with_tags(["project", "development"])
                .with_description(f"Workspace for {project_name} project"))
    
    @classmethod
    def temporary(cls, name: str = "temp") -> Self:
        """Create a temporary workspace builder."""
        return (cls()
                .with_name(name)
                .with_path(f"/tmp/{name}")
                .with_tags(["temporary", "test"])
                .with_description("Temporary test workspace"))
    
    @classmethod
    def archived(cls, name: str = "archived") -> Self:
        """Create an archived workspace builder."""
        old_date = datetime(2023, 1, 1)
        return (cls()
                .with_name(name)
                .with_path(f"/archive/{name}")
                .with_tags(["archived"])
                .with_description("Archived workspace")
                .with_timestamps(old_date, old_date)
                .with_last_accessed(old_date))
    
    @classmethod
    def with_custom_path(cls, name: str = "custom", path: str = "/custom/path") -> Self:
        """Create a workspace with custom path."""
        return (cls()
                .with_name(name)
                .with_path(path)
                .with_description("Workspace with custom path"))