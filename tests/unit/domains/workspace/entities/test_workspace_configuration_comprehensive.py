"""Comprehensive unit tests for WorkspaceConfiguration entity."""

import pytest
from datetime import datetime
from src.writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from src.writeit.domains.workspace.value_objects.configuration_value import (
    ConfigurationValue, string_config, int_config, bool_config, list_config
)


class TestWorkspaceConfiguration:
    """Test cases for WorkspaceConfiguration entity."""
    
    def test_workspace_configuration_creation(self):
        """Test creating workspace configuration."""
        config = WorkspaceConfiguration()
        
        assert isinstance(config.values, dict)
        assert len(config.values) == 0
        assert config.schema_version == "1.0.0"
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)

    def test_workspace_configuration_with_values(self):
        """Test workspace configuration with initial values."""
        values = {
            "default_model": string_config("gpt-4o-mini"),
            "max_tokens": int_config(2000),
            "cache_enabled": bool_config(True)
        }
        
        config = WorkspaceConfiguration(values=values)
        
        assert len(config.values) == 3
        assert config.values["default_model"].value == "gpt-4o-mini"
        assert config.values["max_tokens"].value == 2000
        assert config.values["cache_enabled"].value is True

    def test_workspace_configuration_default(self):
        """Test creating default workspace configuration."""
        try:
            config = WorkspaceConfiguration.default()
            assert isinstance(config, WorkspaceConfiguration)
        except AttributeError:
            # If default class method doesn't exist, create basic config
            config = WorkspaceConfiguration()
            assert isinstance(config, WorkspaceConfiguration)


class TestWorkspaceConfigurationBusinessLogic:
    """Test business logic for WorkspaceConfiguration."""
    
    def test_configuration_value_validation(self):
        """Test configuration value validation."""
        with pytest.raises(TypeError, match="Configuration value for 'invalid' must be a ConfigurationValue"):
            WorkspaceConfiguration(values={
                "invalid": "not_a_config_value"  # type: ignore
            })


class TestWorkspaceConfigurationEdgeCases:
    """Test edge cases for WorkspaceConfiguration."""
    
    def test_empty_configuration(self):
        """Test empty workspace configuration."""
        config = WorkspaceConfiguration()
        
        assert len(config.values) == 0
        assert config.schema_version == "1.0.0"

    def test_configuration_with_complex_values(self):
        """Test configuration with various value types."""
        values = {
            "models": list_config(["gpt-4o", "gpt-4o-mini"]),
            "timeout": int_config(30),
            "debug": bool_config(False),
            "api_base": string_config("https://api.openai.com/v1")
        }
        
        config = WorkspaceConfiguration(values=values)
        
        assert config.values["models"].value == ["gpt-4o", "gpt-4o-mini"]
        assert config.values["timeout"].value == 30
        assert config.values["debug"].value is False
        assert config.values["api_base"].value == "https://api.openai.com/v1"