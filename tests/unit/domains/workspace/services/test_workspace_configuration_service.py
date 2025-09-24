"""Unit tests for WorkspaceConfigurationService.

Tests comprehensive configuration management including validation,
merging, schema management, and environment-specific overrides.
"""

import pytest
import os
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from writeit.domains.workspace.services.workspace_configuration_service import (
    WorkspaceConfigurationService,
    ConfigurationScope,
    ConfigurationValidationIssue,
    ConfigurationMergeConflict,
    ConfigurationSchema,
    ConfigurationValidationError,
    ConfigurationMergeError,
    ConfigurationSchemaError
)
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.value_objects.configuration_value import (
    string_config,
    int_config,
    bool_config,
    list_config
)


class TestWorkspaceConfigurationService:
    """Test WorkspaceConfigurationService core functionality."""
    
    def test_create_service(self, mock_workspace_config_repository):
        """Test creating configuration service."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        assert service._config_repo == mock_workspace_config_repository
        assert service._environment_prefix == "WRITEIT_"
        assert "override" in service._merge_strategies
        assert "merge" in service._merge_strategies
        assert "append" in service._merge_strategies
        assert "preserve" in service._merge_strategies
    
    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self, mock_workspace_config_repository):
        """Test validation of valid configuration."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Create valid configuration
        config = WorkspaceConfiguration.default()
        config = config.set_value("default_model", "gpt-4o-mini")
        config = config.set_value("max_tokens", 2000)
        config = config.set_value("enable_cache", True)
        
        workspace = Mock()
        workspace.name = WorkspaceName("test-workspace")
        workspace.root_path = WorkspacePath.from_string("/test/path")
        
        issues = await service.validate_configuration(workspace, config)
        
        # Should have no critical errors for valid configuration
        error_issues = [issue for issue in issues if issue.severity == "error"]
        assert len(error_issues) == 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_invalid_type(self, mock_workspace_config_repository):
        """Test validation detects type errors."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Create configuration with invalid type
        config = WorkspaceConfiguration.default()
        config = config.set_value("max_tokens", "invalid")  # Should be int
        
        workspace = Mock()
        
        issues = await service.validate_configuration(workspace, config, strict=True)
        
        # Should have error for invalid type
        error_issues = [issue for issue in issues if issue.severity == "error"]
        assert len(error_issues) > 0
        assert any("invalid type" in issue.message.lower() for issue in error_issues)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_out_of_range(self, mock_workspace_config_repository):
        """Test validation detects out of range values."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Create configuration with out of range value
        config = WorkspaceConfiguration.default()
        config = config.set_value("max_tokens", 99999)  # Above maximum
        
        workspace = Mock()
        
        issues = await service.validate_configuration(workspace, config)
        
        # Should have error for out of range value
        error_issues = [issue for issue in issues if issue.severity == "error"]
        assert len(error_issues) > 0
        assert any("above maximum" in issue.message.lower() for issue in error_issues)
    
    @pytest.mark.asyncio
    async def test_merge_configurations_override(self, mock_workspace_config_repository):
        """Test configuration merging with override strategy."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Create base configuration
        base_config = WorkspaceConfiguration.default()
        base_config = base_config.set_value("default_model", "gpt-4o-mini")
        base_config = base_config.set_value("max_tokens", 1000)
        
        # Create override configuration
        override_config = WorkspaceConfiguration.default()
        override_config = override_config.set_value("default_model", "gpt-4o")
        override_config = override_config.set_value("temperature", "0.8")
        
        configs = [
            (base_config, ConfigurationScope.GLOBAL),
            (override_config, ConfigurationScope.WORKSPACE)
        ]
        
        merged = await service.merge_configurations(configs, strategy="override")
        
        # Override values should win
        assert merged.get_string("default_model") == "gpt-4o"
        assert merged.get_int("max_tokens") == 1000  # Base value preserved
        assert merged.get_string("temperature") == "0.8"  # New value added
    
    @pytest.mark.asyncio
    async def test_merge_configurations_append_lists(self, mock_workspace_config_repository):
        """Test configuration merging with append strategy for lists."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Create configurations with list values
        base_config = WorkspaceConfiguration.default()
        base_config = base_config.set_value("template_search_paths", ["templates"])
        
        override_config = WorkspaceConfiguration.default() 
        override_config = override_config.set_value("template_search_paths", ["custom_templates"])
        
        configs = [
            (base_config, ConfigurationScope.GLOBAL),
            (override_config, ConfigurationScope.WORKSPACE)
        ]
        
        merged = await service.merge_configurations(configs, strategy="append")
        
        # Lists should be appended
        search_paths = merged.get_list("template_search_paths")
        assert "templates" in search_paths
        assert "custom_templates" in search_paths
        assert len(search_paths) == 2
    
    @pytest.mark.asyncio
    async def test_merge_configurations_preserve(self, mock_workspace_config_repository):
        """Test configuration merging with preserve strategy."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        base_config = WorkspaceConfiguration.default()
        base_config = base_config.set_value("default_model", "gpt-4o-mini")
        
        override_config = WorkspaceConfiguration.default()
        override_config = override_config.set_value("default_model", "gpt-4o")
        
        configs = [
            (base_config, ConfigurationScope.GLOBAL),
            (override_config, ConfigurationScope.WORKSPACE)
        ]
        
        merged = await service.merge_configurations(configs, strategy="preserve")
        
        # Base value should be preserved
        assert merged.get_string("default_model") == "gpt-4o-mini"
    
    @pytest.mark.asyncio
    async def test_apply_environment_overrides(self, mock_workspace_config_repository):
        """Test applying environment variable overrides."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("default_model", "gpt-4o-mini")
        config = config.set_value("max_tokens", 1000)
        config = config.set_value("enable_cache", True)
        
        # Mock environment variables
        env_vars = {
            "WRITEIT_DEFAULT_MODEL": "gpt-4o",
            "WRITEIT_MAX_TOKENS": "2000",
            "WRITEIT_ENABLE_CACHE": "false",
            "OTHER_VAR": "ignored"
        }
        
        result = await service.apply_environment_overrides(config, env_vars)
        
        # Environment overrides should be applied
        assert result.get_string("default_model") == "gpt-4o"
        assert result.get_int("max_tokens") == 2000
        assert result.get_bool("enable_cache") is False
    
    @pytest.mark.asyncio
    async def test_apply_environment_overrides_list_values(self, mock_workspace_config_repository):
        """Test environment overrides for list values."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("template_search_paths", ["templates"])
        
        env_vars = {
            "WRITEIT_TEMPLATE_SEARCH_PATHS": "custom,global,local"
        }
        
        result = await service.apply_environment_overrides(config, env_vars)
        
        # List should be parsed from comma-separated values
        search_paths = result.get_list("template_search_paths")
        assert search_paths == ["custom", "global", "local"]
    
    @pytest.mark.asyncio
    async def test_get_effective_configuration(self, mock_workspace_config_repository):
        """Test getting effective configuration with hierarchy."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Setup mock repository
        global_config = WorkspaceConfiguration.default()
        global_config = global_config.set_value("default_model", "gpt-4o-mini")
        global_config = global_config.set_value("max_tokens", 1000)
        
        workspace_config = WorkspaceConfiguration.default()
        workspace_config = workspace_config.set_value("default_model", "gpt-4o")
        workspace_config = workspace_config.set_value("temperature", "0.8")
        
        mock_workspace_config_repository.get_global_config = AsyncMock(return_value=global_config)
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=workspace_config)
        
        workspace = Mock()
        
        with patch.dict(os.environ, {"WRITEIT_MAX_TOKENS": "2000"}):
            effective = await service.get_effective_configuration(workspace)
            
            # Should have correct precedence: environment > workspace > global
            assert effective.get_string("default_model") == "gpt-4o"  # Workspace override
            assert effective.get_int("max_tokens") == 2000  # Environment override
            assert effective.get_string("temperature") == "0.8"  # Workspace value
    
    @pytest.mark.asyncio
    async def test_export_configuration_yaml(self, mock_workspace_config_repository, temp_dir):
        """Test configuration export as YAML."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("default_model", "gpt-4o")
        config = config.set_value("max_tokens", 2000)
        
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=config)
        
        workspace = Mock()
        
        yaml_output = await service.export_configuration(
            workspace, 
            scope=ConfigurationScope.WORKSPACE,
            format_type="yaml"
        )
        
        assert isinstance(yaml_output, str)
        assert "default_model" in yaml_output
        assert "gpt-4o" in yaml_output
        assert "max_tokens" in yaml_output
        assert "2000" in yaml_output
    
    @pytest.mark.asyncio
    async def test_export_configuration_env(self, mock_workspace_config_repository):
        """Test configuration export as environment variables."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("default_model", "gpt-4o")
        config = config.set_value("enable_cache", True)
        
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=config)
        
        workspace = Mock()
        
        env_output = await service.export_configuration(
            workspace,
            scope=ConfigurationScope.WORKSPACE,
            format_type="env"
        )
        
        assert "WRITEIT_DEFAULT_MODEL=gpt-4o" in env_output
        assert "WRITEIT_ENABLE_CACHE=True" in env_output
    
    @pytest.mark.asyncio
    async def test_import_configuration_yaml(self, mock_workspace_config_repository):
        """Test configuration import from YAML."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        yaml_data = """
        default_model: gpt-4o
        max_tokens: 2000
        enable_cache: false
        """
        
        # Mock existing configuration
        existing_config = WorkspaceConfiguration.default()
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=existing_config)
        mock_workspace_config_repository.update_config = AsyncMock(return_value=existing_config)
        
        workspace = Mock()
        
        imported = await service.import_configuration(
            workspace,
            yaml_data,
            format_type="yaml",
            validate=False
        )
        
        # Should successfully import and merge
        assert imported is not None
        mock_workspace_config_repository.update_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_import_configuration_invalid(self, mock_workspace_config_repository):
        """Test import configuration validation fails."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Invalid YAML with out-of-range value
        yaml_data = """
        max_tokens: 999999
        """
        
        workspace = Mock()
        
        with pytest.raises(ConfigurationValidationError):
            await service.import_configuration(
                workspace,
                yaml_data,
                format_type="yaml",
                validate=True
            )
    
    @pytest.mark.asyncio
    async def test_reset_configuration(self, mock_workspace_config_repository):
        """Test configuration reset to defaults."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        reset_config = WorkspaceConfiguration.default()
        mock_workspace_config_repository.reset_to_defaults = AsyncMock(return_value=reset_config)
        
        workspace = Mock()
        
        result = await service.reset_configuration(
            workspace, 
            keys=["default_model", "max_tokens"]
        )
        
        assert result == reset_config
        mock_workspace_config_repository.reset_to_defaults.assert_called_once_with(
            workspace, 
            ["default_model", "max_tokens"]
        )
    
    @pytest.mark.asyncio
    async def test_get_configuration_diff(self, mock_workspace_config_repository):
        """Test configuration difference detection."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config1 = WorkspaceConfiguration.default()
        config1 = config1.set_value("default_model", "gpt-4o-mini")
        config1 = config1.set_value("max_tokens", 1000)
        config1 = config1.set_value("temperature", "0.7")
        
        config2 = WorkspaceConfiguration.default()
        config2 = config2.set_value("default_model", "gpt-4o")  # Changed
        config2 = config2.set_value("max_tokens", 1000)  # Unchanged
        config2 = config2.set_value("enable_cache", True)  # Added
        # temperature removed
        
        diff = await service.get_configuration_diff(config1, config2)
        
        # Should detect changes correctly
        assert "changed" in diff
        assert "unchanged" in diff
        assert "added" in diff
        assert "removed" in diff
        
        # Check specific changes
        assert "default_model" in diff["changed"]
        assert "max_tokens" in diff["unchanged"]
        assert "enable_cache" in diff["added"]
        assert "temperature" in diff["removed"]
    
    @pytest.mark.asyncio
    async def test_update_configuration_schema(self, mock_workspace_config_repository):
        """Test configuration schema updates."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        schema_updates = {
            "custom_setting": {
                "type": "string",
                "description": "Custom workspace setting",
                "default": "default_value"
            }
        }
        
        updated_schema = await service.update_configuration_schema(schema_updates)
        
        assert isinstance(updated_schema, ConfigurationSchema)
        assert "custom_setting" in updated_schema.keys
        assert updated_schema.keys["custom_setting"]["type"] == "string"
        assert updated_schema.version != "1.0.0"  # Should be incremented
    
    @pytest.mark.asyncio
    async def test_validate_configuration_consistency_parallel_settings(self, mock_workspace_config_repository):
        """Test configuration consistency validation for parallel execution."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        # Create inconsistent configuration
        config = WorkspaceConfiguration.default()
        config = config.set_value("parallel_execution", False)
        config = config.set_value("max_parallel_steps", 5)  # Inconsistent
        
        workspace = Mock()
        
        issues = await service.validate_configuration(workspace, config)
        
        # Should detect inconsistency
        warning_issues = [issue for issue in issues if issue.severity == "warning"]
        assert any("parallel_execution" in issue.message for issue in warning_issues)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_missing_template_paths(self, mock_workspace_config_repository, temp_dir):
        """Test validation detects missing template paths."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        workspace_path = temp_dir / "test_workspace"
        workspace_path.mkdir()
        
        workspace = Mock()
        workspace.name = WorkspaceName("test-workspace")
        workspace.root_path = WorkspacePath.from_string(str(workspace_path))
        
        # Configuration with non-existent template path
        config = WorkspaceConfiguration.default()
        config = config.set_value("template_search_paths", ["missing_templates"])
        
        issues = await service.validate_configuration(workspace, config)
        
        # Should detect missing paths
        path_issues = [issue for issue in issues if "template_search_paths" in issue.key]
        assert len(path_issues) > 0
        assert any("does not exist" in issue.message for issue in path_issues)


class TestConfigurationValidationIssue:
    """Test ConfigurationValidationIssue behavior."""
    
    def test_create_validation_issue(self):
        """Test creating validation issue."""
        issue = ConfigurationValidationIssue(
            key="test_key",
            severity="error",
            message="Test error message",
            suggestion="Fix the issue",
            current_value="invalid",
            expected_type="string"
        )
        
        assert issue.key == "test_key"
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.suggestion == "Fix the issue"
        assert issue.current_value == "invalid"
        assert issue.expected_type == "string"


class TestConfigurationMergeConflict:
    """Test ConfigurationMergeConflict behavior."""
    
    def test_create_merge_conflict(self):
        """Test creating merge conflict."""
        conflict = ConfigurationMergeConflict(
            key="test_key",
            source_value="source",
            target_value="target",
            source_scope=ConfigurationScope.GLOBAL,
            target_scope=ConfigurationScope.WORKSPACE,
            resolution_strategy="override"
        )
        
        assert conflict.key == "test_key"
        assert conflict.source_value == "source"
        assert conflict.target_value == "target"
        assert conflict.source_scope == ConfigurationScope.GLOBAL
        assert conflict.target_scope == ConfigurationScope.WORKSPACE
        assert conflict.resolution_strategy == "override"


class TestConfigurationSchema:
    """Test ConfigurationSchema behavior."""
    
    def test_validate_key_valid(self):
        """Test validating valid key."""
        schema = ConfigurationSchema(
            keys={
                "test_key": {
                    "type": "string",
                    "allowed_values": ["value1", "value2"]
                }
            },
            version="1.0.0",
            created_at=datetime.now(),
            description="Test schema"
        )
        
        issues = schema.validate_key("test_key", "value1")
        
        assert len(issues) == 0
    
    def test_validate_key_invalid_type(self):
        """Test validating key with invalid type."""
        schema = ConfigurationSchema(
            keys={
                "test_key": {
                    "type": "int",
                    "min_value": 0,
                    "max_value": 100
                }
            },
            version="1.0.0",
            created_at=datetime.now(),
            description="Test schema"
        )
        
        issues = schema.validate_key("test_key", "not_an_int")
        
        assert len(issues) > 0
        assert any("invalid type" in issue.lower() for issue in issues)
    
    def test_validate_key_out_of_range(self):
        """Test validating key with out of range value."""
        schema = ConfigurationSchema(
            keys={
                "test_key": {
                    "type": "int",
                    "min_value": 10,
                    "max_value": 100
                }
            },
            version="1.0.0",
            created_at=datetime.now(),
            description="Test schema"
        )
        
        # Test below minimum
        issues = schema.validate_key("test_key", 5)
        assert len(issues) > 0
        assert any("below minimum" in issue.lower() for issue in issues)
        
        # Test above maximum
        issues = schema.validate_key("test_key", 150)
        assert len(issues) > 0
        assert any("above maximum" in issue.lower() for issue in issues)
    
    def test_validate_key_pattern_mismatch(self):
        """Test validating key with pattern mismatch."""
        schema = ConfigurationSchema(
            keys={
                "test_key": {
                    "type": "string",
                    "pattern": r"^[a-z]+$"
                }
            },
            version="1.0.0",
            created_at=datetime.now(),
            description="Test schema"
        )
        
        issues = schema.validate_key("test_key", "Invalid123")
        
        assert len(issues) > 0
        assert any("doesn't match pattern" in issue.lower() for issue in issues)
    
    def test_validate_key_unknown(self):
        """Test validating unknown key."""
        schema = ConfigurationSchema(
            keys={},
            version="1.0.0",
            created_at=datetime.now(),
            description="Test schema"
        )
        
        issues = schema.validate_key("unknown_key", "value")
        
        assert len(issues) > 0
        assert any("unknown" in issue.lower() for issue in issues)


class TestConfigurationScope:
    """Test ConfigurationScope enum."""
    
    def test_scope_values(self):
        """Test configuration scope values."""
        assert ConfigurationScope.GLOBAL == "global"
        assert ConfigurationScope.WORKSPACE == "workspace"
        assert ConfigurationScope.ENVIRONMENT == "environment"
        assert ConfigurationScope.RUNTIME == "runtime"


class TestWorkspaceConfigurationServicePrivateMethods:
    """Test private methods of WorkspaceConfigurationService."""
    
    @pytest.mark.asyncio
    async def test_parse_environment_value_bool(self, mock_workspace_config_repository):
        """Test parsing boolean environment values."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("enable_cache", True)
        
        # Test various boolean representations
        assert await service._parse_environment_value(config, "enable_cache", "true") is True
        assert await service._parse_environment_value(config, "enable_cache", "1") is True
        assert await service._parse_environment_value(config, "enable_cache", "yes") is True
        assert await service._parse_environment_value(config, "enable_cache", "on") is True
        assert await service._parse_environment_value(config, "enable_cache", "false") is False
        assert await service._parse_environment_value(config, "enable_cache", "0") is False
    
    @pytest.mark.asyncio
    async def test_parse_environment_value_int(self, mock_workspace_config_repository):
        """Test parsing integer environment values."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("max_tokens", 1000)
        
        result = await service._parse_environment_value(config, "max_tokens", "2000")
        assert result == 2000
    
    @pytest.mark.asyncio
    async def test_parse_environment_value_list(self, mock_workspace_config_repository):
        """Test parsing list environment values."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        config = WorkspaceConfiguration.default()
        config = config.set_value("template_search_paths", ["templates"])
        
        result = await service._parse_environment_value(
            config, 
            "template_search_paths", 
            "path1,path2,path3"
        )
        assert result == ["path1", "path2", "path3"]
    
    def test_increment_schema_version(self, mock_workspace_config_repository):
        """Test schema version increment."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        assert service._increment_schema_version("1.0.0") == "1.0.1"
        assert service._increment_schema_version("2.1.5") == "2.1.6"
        assert service._increment_schema_version("invalid") == "1.0.1"
    
    def test_determine_issue_severity(self, mock_workspace_config_repository):
        """Test issue severity determination."""
        service = WorkspaceConfigurationService(mock_workspace_config_repository)
        
        assert service._determine_issue_severity("key", "unknown configuration key") == "error"
        assert service._determine_issue_severity("key", "invalid type for key") == "error"
        assert service._determine_issue_severity("key", "value below minimum") == "error"
        assert service._determine_issue_severity("key", "value above maximum") == "error"
        assert service._determine_issue_severity("key", "doesn't match pattern") == "error"
        assert service._determine_issue_severity("key", "value not in allowed values") == "warning"
        assert service._determine_issue_severity("key", "other message") == "info"