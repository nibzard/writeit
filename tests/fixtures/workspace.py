"""Workspace domain entity fixtures for testing.

Provides comprehensive test fixtures for workspace domain entities including
workspaces, configurations, and workspace management scenarios.
"""

import pytest
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Dict, Any, Optional

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue


# ============================================================================
# Basic Workspace Fixtures
# ============================================================================

@pytest.fixture
def workspace_name_fixture():
    """Valid workspace name for testing."""
    return WorkspaceName.from_user_input("test-workspace")

@pytest.fixture
def workspace_path_fixture(tmp_path):
    """Valid workspace path using temporary directory."""
    workspace_dir = tmp_path / "test-workspace"
    workspace_dir.mkdir()
    return WorkspacePath.from_string(str(workspace_dir))

@pytest.fixture
def configuration_value_fixture():
    """Valid configuration value."""
    return ConfigurationValue.create("auto_save", True, "boolean")

@pytest.fixture
def workspace_configuration_fixture():
    """Valid workspace configuration with common settings."""
    settings = {
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
        "max_retries": ConfigurationValue.create("max_retries", 3, "integer"),
        "timeout_seconds": ConfigurationValue.create("timeout_seconds", 30.0, "float"),
        "debug_mode": ConfigurationValue.create("debug_mode", False, "boolean"),
        "theme": ConfigurationValue.create("theme", "dark", "string"),
        "language": ConfigurationValue.create("language", "en", "string"),
        "tags": ConfigurationValue.create("tags", ["development", "testing"], "list")
    }
    
    return WorkspaceConfiguration.create(
        settings=settings,
        description="Test workspace configuration",
        version="1.0.0"
    )

@pytest.fixture
def workspace_fixture(workspace_name_fixture, workspace_path_fixture, workspace_configuration_fixture):
    """Valid workspace with configuration."""
    return Workspace.create(
        name=workspace_name_fixture,
        root_path=workspace_path_fixture,
        configuration=workspace_configuration_fixture,
        metadata={"created_by": "test_user", "purpose": "testing"}
    )


# ============================================================================
# Workspace State Fixtures
# ============================================================================

@pytest.fixture
def active_workspace(workspace_fixture):
    """Active workspace."""
    return workspace_fixture.activate()

@pytest.fixture
def inactive_workspace(workspace_fixture):
    """Inactive workspace."""
    active = workspace_fixture.activate()
    return active.deactivate()

@pytest.fixture
def initialized_workspace(workspace_fixture):
    """Workspace with initialized directory structure."""
    workspace = workspace_fixture
    workspace.ensure_directory_structure()
    return workspace


# ============================================================================
# Configuration Variants
# ============================================================================

@pytest.fixture
def minimal_configuration():
    """Minimal workspace configuration."""
    return WorkspaceConfiguration.create(
        settings={
            "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string")
        },
        description="Minimal configuration"
    )

@pytest.fixture
def comprehensive_configuration():
    """Comprehensive workspace configuration with all settings."""
    settings = {
        # Model settings
        "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
        "fallback_models": ConfigurationValue.create("fallback_models", ["gpt-3.5-turbo", "claude-3-haiku"], "list"),
        "max_tokens": ConfigurationValue.create("max_tokens", 4000, "integer"),
        "temperature": ConfigurationValue.create("temperature", 0.7, "float"),
        
        # Execution settings
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "max_retries": ConfigurationValue.create("max_retries", 3, "integer"),
        "timeout_seconds": ConfigurationValue.create("timeout_seconds", 120.0, "float"),
        "parallel_execution": ConfigurationValue.create("parallel_execution", True, "boolean"),
        "cache_enabled": ConfigurationValue.create("cache_enabled", True, "boolean"),
        
        # UI settings
        "theme": ConfigurationValue.create("theme", "dark", "string"),
        "language": ConfigurationValue.create("language", "en", "string"),
        "show_tokens": ConfigurationValue.create("show_tokens", True, "boolean"),
        "show_timing": ConfigurationValue.create("show_timing", True, "boolean"),
        "auto_scroll": ConfigurationValue.create("auto_scroll", True, "boolean"),
        
        # Development settings
        "debug_mode": ConfigurationValue.create("debug_mode", False, "boolean"),
        "log_level": ConfigurationValue.create("log_level", "INFO", "string"),
        "enable_profiling": ConfigurationValue.create("enable_profiling", False, "boolean"),
        
        # Content settings
        "default_format": ConfigurationValue.create("default_format", "markdown", "string"),
        "word_wrap": ConfigurationValue.create("word_wrap", 80, "integer"),
        "spell_check": ConfigurationValue.create("spell_check", True, "boolean"),
        
        # Metadata
        "tags": ConfigurationValue.create("tags", ["production", "content"], "list"),
        "owner": ConfigurationValue.create("owner", "test_user", "string"),
        "department": ConfigurationValue.create("department", "engineering", "string")
    }
    
    return WorkspaceConfiguration.create(
        settings=settings,
        description="Comprehensive workspace configuration",
        version="2.0.0"
    )

@pytest.fixture
def development_configuration():
    """Development-focused workspace configuration."""
    settings = {
        "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
        "debug_mode": ConfigurationValue.create("debug_mode", True, "boolean"),
        "log_level": ConfigurationValue.create("log_level", "DEBUG", "string"),
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "enable_profiling": ConfigurationValue.create("enable_profiling", True, "boolean"),
        "cache_enabled": ConfigurationValue.create("cache_enabled", False, "boolean"),  # Disable for testing
        "max_retries": ConfigurationValue.create("max_retries", 1, "integer"),  # Faster failure
        "timeout_seconds": ConfigurationValue.create("timeout_seconds", 10.0, "float"),  # Quick timeout
        "tags": ConfigurationValue.create("tags", ["development", "debug"], "list")
    }
    
    return WorkspaceConfiguration.create(
        settings=settings,
        description="Development workspace configuration",
        version="1.0.0-dev"
    )

@pytest.fixture
def production_configuration():
    """Production-focused workspace configuration."""
    settings = {
        "default_model": ConfigurationValue.create("default_model", "gpt-4o", "string"),  # Best model
        "fallback_models": ConfigurationValue.create("fallback_models", ["gpt-4o-mini", "gpt-3.5-turbo"], "list"),
        "debug_mode": ConfigurationValue.create("debug_mode", False, "boolean"),
        "log_level": ConfigurationValue.create("log_level", "INFO", "string"),
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "cache_enabled": ConfigurationValue.create("cache_enabled", True, "boolean"),
        "max_retries": ConfigurationValue.create("max_retries", 5, "integer"),  # More resilient
        "timeout_seconds": ConfigurationValue.create("timeout_seconds", 300.0, "float"),  # Longer timeout
        "parallel_execution": ConfigurationValue.create("parallel_execution", True, "boolean"),
        "enable_profiling": ConfigurationValue.create("enable_profiling", False, "boolean"),
        "tags": ConfigurationValue.create("tags", ["production", "stable"], "list")
    }
    
    return WorkspaceConfiguration.create(
        settings=settings,
        description="Production workspace configuration",
        version="1.0.0"
    )


# ============================================================================
# Workspace Variants
# ============================================================================

@pytest.fixture
def personal_workspace(tmp_path):
    """Personal workspace for individual use."""
    workspace_dir = tmp_path / "personal-workspace"
    workspace_dir.mkdir()
    
    settings = {
        "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
        "theme": ConfigurationValue.create("theme", "light", "string"),
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "tags": ConfigurationValue.create("tags", ["personal"], "list")
    }
    
    config = WorkspaceConfiguration.create(
        settings=settings,
        description="Personal workspace"
    )
    
    return Workspace.create(
        name=WorkspaceName.from_user_input("personal"),
        root_path=WorkspacePath.from_string(str(workspace_dir)),
        configuration=config,
        metadata={"type": "personal", "owner": "user"}
    )

@pytest.fixture
def team_workspace(tmp_path):
    """Team workspace for collaborative use."""
    workspace_dir = tmp_path / "team-workspace"
    workspace_dir.mkdir()
    
    settings = {
        "default_model": ConfigurationValue.create("default_model", "gpt-4o", "string"),
        "fallback_models": ConfigurationValue.create("fallback_models", ["gpt-4o-mini"], "list"),
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "cache_enabled": ConfigurationValue.create("cache_enabled", True, "boolean"),
        "parallel_execution": ConfigurationValue.create("parallel_execution", True, "boolean"),
        "tags": ConfigurationValue.create("tags", ["team", "collaborative"], "list"),
        "max_retries": ConfigurationValue.create("max_retries", 3, "integer"),
        "timeout_seconds": ConfigurationValue.create("timeout_seconds", 120.0, "float")
    }
    
    config = WorkspaceConfiguration.create(
        settings=settings,
        description="Team collaboration workspace",
        version="1.1.0"
    )
    
    return Workspace.create(
        name=WorkspaceName.from_user_input("team-project"),
        root_path=WorkspacePath.from_string(str(workspace_dir)),
        configuration=config,
        metadata={
            "type": "team",
            "team_members": ["alice", "bob", "charlie"],
            "project": "content-generation"
        }
    )

@pytest.fixture
def project_workspace(tmp_path):
    """Project-specific workspace."""
    workspace_dir = tmp_path / "project-workspace"
    workspace_dir.mkdir()
    
    settings = {
        "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
        "default_format": ConfigurationValue.create("default_format", "markdown", "string"),
        "auto_save": ConfigurationValue.create("auto_save", True, "boolean"),
        "spell_check": ConfigurationValue.create("spell_check", True, "boolean"),
        "word_wrap": ConfigurationValue.create("word_wrap", 100, "integer"),
        "tags": ConfigurationValue.create("tags", ["project", "documentation"], "list")
    }
    
    config = WorkspaceConfiguration.create(
        settings=settings,
        description="Project documentation workspace"
    )
    
    return Workspace.create(
        name=WorkspaceName.from_user_input("project-docs"),
        root_path=WorkspacePath.from_string(str(workspace_dir)),
        configuration=config,
        metadata={
            "type": "project",
            "project_name": "WriteIt",
            "project_phase": "development"
        }
    )


# ============================================================================
# Error/Edge Case Fixtures
# ============================================================================

@pytest.fixture
def invalid_workspace_configurations():
    """Invalid workspace configurations for negative testing."""
    return {
        "empty_settings": {
            "settings": {},
            "description": "Empty configuration"
        },
        "invalid_value_types": {
            "settings": {
                "invalid_boolean": ConfigurationValue.create("invalid_boolean", "not_a_boolean", "boolean"),
                "invalid_integer": ConfigurationValue.create("invalid_integer", "not_an_integer", "integer"),
                "invalid_float": ConfigurationValue.create("invalid_float", "not_a_float", "float")
            },
            "description": "Configuration with invalid value types"
        },
        "duplicate_keys": {
            "settings": {
                "setting1": ConfigurationValue.create("setting1", "value1", "string"),
                "setting1": ConfigurationValue.create("setting1", "value2", "string")  # Duplicate key
            },
            "description": "Configuration with duplicate keys"
        }
    }

@pytest.fixture
def invalid_workspaces(tmp_path):
    """Invalid workspace configurations for negative testing."""
    return {
        "invalid_name": {
            "name": "ab",  # Too short
            "path": str(tmp_path / "invalid-name"),
            "error": "Workspace name too short"
        },
        "invalid_path": {
            "name": "valid-workspace",
            "path": "/invalid/path/that/does/not/exist",
            "error": "Workspace path does not exist"
        },
        "name_with_invalid_chars": {
            "name": "invalid workspace!",  # Invalid characters
            "path": str(tmp_path / "invalid-chars"),
            "error": "Workspace name contains invalid characters"
        },
        "extremely_long_name": {
            "name": "x" * 100,  # Too long
            "path": str(tmp_path / "long-name"),
            "error": "Workspace name too long"
        }
    }

@pytest.fixture
def edge_case_workspace_metadata():
    """Edge case metadata for workspace testing."""
    return {
        "empty_metadata": {},
        "very_large_metadata": {f"key_{i}": f"value_{i}" for i in range(1000)},
        "unicode_metadata": {
            "unicode_key_🚀": "unicode_value_émojis",
            "chinese": "中文测试",
            "emojis": "🎉🎊🎈"
        },
        "nested_metadata": {
            "level1": {
                "level2": {
                    "level3": {
                        "deep_value": "nested_data"
                    }
                }
            }
        },
        "null_values": {
            "null_value": None,
            "empty_string": "",
            "zero": 0,
            "false": False
        }
    }


# ============================================================================
# Workspace Collections & Scenarios
# ============================================================================

@pytest.fixture
def multiple_workspaces(tmp_path):
    """Collection of different workspace types."""
    workspaces = {}
    
    # Create different workspace types
    workspace_configs = [
        ("default", "Default workspace", {}),
        ("development", "Development workspace", {"debug_mode": True}),
        ("production", "Production workspace", {"cache_enabled": True}),
        ("testing", "Testing workspace", {"max_retries": 1})
    ]
    
    for name, description, extra_settings in workspace_configs:
        workspace_dir = tmp_path / f"{name}-workspace"
        workspace_dir.mkdir()
        
        base_settings = {
            "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
            "auto_save": ConfigurationValue.create("auto_save", True, "boolean")
        }
        
        # Add extra settings
        for key, value in extra_settings.items():
            if isinstance(value, bool):
                base_settings[key] = ConfigurationValue.create(key, value, "boolean")
            elif isinstance(value, int):
                base_settings[key] = ConfigurationValue.create(key, value, "integer")
            elif isinstance(value, str):
                base_settings[key] = ConfigurationValue.create(key, value, "string")
        
        config = WorkspaceConfiguration.create(
            settings=base_settings,
            description=description
        )
        
        workspace = Workspace.create(
            name=WorkspaceName.from_user_input(name),
            root_path=WorkspacePath.from_string(str(workspace_dir)),
            configuration=config,
            metadata={"type": name}
        )
        
        workspaces[name] = workspace
    
    return workspaces

@pytest.fixture
def workspace_with_templates(workspace_fixture, tmp_path):
    """Workspace with directory structure and template files."""
    workspace = workspace_fixture
    workspace.ensure_directory_structure()
    
    # Create some template files
    templates_dir = workspace.get_templates_path().value
    templates_dir.mkdir(exist_ok=True)
    
    template_files = [
        ("article.yaml", "Article template"),
        ("blog-post.yaml", "Blog post template"),
        ("email.yaml", "Email template")
    ]
    
    for filename, content in template_files:
        template_file = templates_dir / filename
        template_file.write_text(f"# {content}\nname: {filename.split('.')[0]}\n")
    
    return workspace


# ============================================================================
# Factory Fixtures
# ============================================================================

@pytest.fixture
def workspace_factory():
    """Factory for creating workspaces with custom parameters."""
    class WorkspaceFactory:
        @staticmethod
        def create_workspace(
            name: str = None,
            workspace_type: str = "default",
            tmp_path: Path = None,
            **kwargs
        ) -> Workspace:
            """Create workspace with specified characteristics."""
            if tmp_path is None:
                import tempfile
                tmp_path = Path(tempfile.mkdtemp())
            
            workspace_name = name or f"test-workspace-{uuid4().hex[:8]}"
            workspace_dir = tmp_path / workspace_name
            workspace_dir.mkdir(exist_ok=True)
            
            # Configuration based on type
            if workspace_type == "minimal":
                settings = {
                    "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string")
                }
            elif workspace_type == "development":
                settings = {
                    "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
                    "debug_mode": ConfigurationValue.create("debug_mode", True, "boolean"),
                    "log_level": ConfigurationValue.create("log_level", "DEBUG", "string")
                }
            elif workspace_type == "production":
                settings = {
                    "default_model": ConfigurationValue.create("default_model", "gpt-4o", "string"),
                    "cache_enabled": ConfigurationValue.create("cache_enabled", True, "boolean"),
                    "max_retries": ConfigurationValue.create("max_retries", 5, "integer")
                }
            else:  # default
                settings = {
                    "default_model": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
                    "auto_save": ConfigurationValue.create("auto_save", True, "boolean")
                }
            
            config = WorkspaceConfiguration.create(
                settings=settings,
                description=f"{workspace_type.title()} workspace"
            )
            
            return Workspace.create(
                name=WorkspaceName.from_user_input(workspace_name),
                root_path=WorkspacePath.from_string(str(workspace_dir)),
                configuration=config,
                metadata=kwargs.get("metadata", {"type": workspace_type})
            )
    
    return WorkspaceFactory()


# ============================================================================
# Valid/Invalid Entity Collections
# ============================================================================

@pytest.fixture
def valid_workspace(workspace_fixture):
    """Valid workspace for positive testing."""
    return workspace_fixture

@pytest.fixture
def invalid_workspace():
    """Invalid workspace data for negative testing."""
    return {
        "missing_name": None,
        "invalid_name": "ab",
        "missing_path": None,
        "missing_configuration": None
    }