# ABOUTME: Unit tests for WriteIt configuration loading functionality
# ABOUTME: Tests hierarchical config loading with environment overrides
import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
import yaml

from writeit.workspace.config import (
    ConfigLoader,
    get_writeit_home,
    get_active_workspace,
)
from writeit.workspace.workspace import Workspace


class TestConfigLoader:
    """Test suite for ConfigLoader class."""

    @pytest.fixture
    def temp_home(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def workspace_manager(self, temp_home):
        """Create workspace manager with temporary directory."""
        workspace = Workspace(temp_home / ".writeit")
        workspace.initialize()
        return workspace

    @pytest.fixture
    def config_loader(self, workspace_manager):
        """Create ConfigLoader instance."""
        return ConfigLoader(workspace_manager)

    @pytest.fixture
    def temp_local_dir(self):
        """Create temporary local directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_load_config_global_only(self, config_loader):
        """Test loading configuration with only global config."""
        config = config_loader.load_config()

        # Should contain global config fields
        assert "active_workspace" in config
        assert "workspaces" in config
        assert "writeit_version" in config
        assert config["active_workspace"] == "default"

    def test_load_config_with_workspace(self, config_loader, workspace_manager):
        """Test loading configuration with workspace config."""
        workspace_manager.create_workspace("test_workspace")

        config = config_loader.load_config(workspace="test_workspace")

        # Should contain both global and workspace config
        assert "active_workspace" in config  # From global
        assert "name" in config  # From workspace
        assert config["name"] == "test_workspace"

    def test_load_config_with_local_config(self, config_loader, temp_local_dir):
        """Test loading configuration with local .writeit/config.yaml."""
        # Create local config
        local_writeit = temp_local_dir / ".writeit"
        local_writeit.mkdir()
        local_config = local_writeit / "config.yaml"

        local_data = {
            "local_setting": "test_value",
            "active_workspace": "local_override",
        }

        with open(local_config, "w") as f:
            yaml.dump(local_data, f)

        config = config_loader.load_config(local_dir=temp_local_dir)

        # Local config should override global
        assert config["active_workspace"] == "local_override"
        assert config["local_setting"] == "test_value"

    def test_load_config_environment_overrides(self, config_loader):
        """Test that environment variables override other config."""
        with patch.dict(
            os.environ,
            {
                "WRITEIT_WORKSPACE": "env_workspace",
                "WRITEIT_LLM_PROVIDER": "env_provider",
            },
        ):
            config = config_loader.load_config()

            assert config["workspace"] == "env_workspace"
            assert config["llm"]["provider"] == "env_provider"

    def test_load_config_hierarchical_override(
        self, config_loader, workspace_manager, temp_local_dir
    ):
        """Test complete hierarchical config loading."""
        # Create workspace with config
        workspace_manager.create_workspace("test_workspace")

        # Create local config that overrides workspace
        local_writeit = temp_local_dir / ".writeit"
        local_writeit.mkdir()
        local_config = local_writeit / "config.yaml"

        with open(local_config, "w") as f:
            yaml.dump({"local_override": True, "active_workspace": "local"}, f)

        # Set environment variable that overrides everything
        with patch.dict(os.environ, {"WRITEIT_HOME": "env_home"}):
            config = config_loader.load_config(
                workspace="test_workspace", local_dir=temp_local_dir
            )

            # Check precedence: env > local > workspace > global
            assert config["home"] == "env_home"  # From env
            assert (
                config["active_workspace"] == "local"
            )  # From local (overrides global)
            assert config["local_override"] is True  # From local only

    def test_get_setting_dot_notation(self, config_loader):
        """Test getting nested settings with dot notation."""
        with patch.dict(os.environ, {"WRITEIT_LLM_PROVIDER": "openai"}):
            # Should create nested structure from env var
            value = config_loader.get_setting("llm.provider")
            assert value == "openai"

    def test_get_setting_default_value(self, config_loader):
        """Test getting setting with default value."""
        value = config_loader.get_setting(
            "nonexistent.setting", default="default_value"
        )
        assert value == "default_value"

    def test_get_setting_existing_value(self, config_loader):
        """Test getting existing setting."""
        value = config_loader.get_setting("active_workspace")
        assert value == "default"  # From global config

    def test_load_local_config_nonexistent(self, config_loader, temp_local_dir):
        """Test loading local config when file doesn't exist."""
        result = config_loader._load_local_config(temp_local_dir)
        assert result is None

    def test_load_local_config_invalid_yaml(self, config_loader, temp_local_dir):
        """Test loading local config with invalid YAML."""
        local_writeit = temp_local_dir / ".writeit"
        local_writeit.mkdir()
        local_config = local_writeit / "config.yaml"

        # Write invalid YAML
        with open(local_config, "w") as f:
            f.write("invalid: yaml: content:")

        result = config_loader._load_local_config(temp_local_dir)
        assert result is None

    def test_load_env_config_simple(self, config_loader):
        """Test loading environment configuration."""
        with patch.dict(
            os.environ,
            {"WRITEIT_HOME": "/custom/home", "WRITEIT_WORKSPACE": "custom_workspace"},
        ):
            env_config = config_loader._load_env_config()

            assert env_config["home"] == "/custom/home"
            assert env_config["workspace"] == "custom_workspace"

    def test_load_env_config_nested(self, config_loader):
        """Test loading nested environment configuration."""
        with patch.dict(
            os.environ,
            {"WRITEIT_LLM_PROVIDER": "openai", "WRITEIT_LLM_API_KEY": "secret_key"},
        ):
            env_config = config_loader._load_env_config()

            assert env_config["llm"]["provider"] == "openai"
            assert env_config["llm"]["api"]["key"] == "secret_key"

    def test_get_nested_value(self, config_loader):
        """Test getting nested values from dictionary."""
        data = {"level1": {"level2": {"level3": "deep_value"}}}

        assert (
            config_loader._get_nested_value(data, "level1.level2.level3")
            == "deep_value"
        )
        assert config_loader._get_nested_value(data, "level1.level2") == {
            "level3": "deep_value"
        }
        assert (
            config_loader._get_nested_value(data, "nonexistent", "default") == "default"
        )

    def test_set_nested_value(self, config_loader):
        """Test setting nested values in dictionary."""
        data = {}

        config_loader._set_nested_value(data, "level1.level2.level3", "value")

        assert data == {"level1": {"level2": {"level3": "value"}}}

    def test_config_caching(self, config_loader):
        """Test that configuration is cached."""
        # Load config twice with same parameters
        config1 = config_loader.load_config()
        config2 = config_loader.load_config()

        # Should be same object due to caching
        assert config1 is config2

    def test_clear_cache(self, config_loader):
        """Test clearing configuration cache."""
        config1 = config_loader.load_config()
        config_loader.clear_cache()
        config2 = config_loader.load_config()

        # Should be different objects after cache clear
        assert config1 is not config2


class TestConfigUtilityFunctions:
    """Test suite for configuration utility functions."""

    def test_get_writeit_home_default(self):
        """Test getting WriteIt home directory with default value."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove WRITEIT_HOME if it exists
            if "WRITEIT_HOME" in os.environ:
                del os.environ["WRITEIT_HOME"]

            home = get_writeit_home()
            assert home == Path.home() / ".writeit"

    def test_get_writeit_home_from_env(self):
        """Test getting WriteIt home directory from environment."""
        with patch.dict(os.environ, {"WRITEIT_HOME": "/custom/writeit"}):
            home = get_writeit_home()
            assert home == Path("/custom/writeit")

    def test_get_active_workspace_from_env(self):
        """Test getting active workspace from environment."""
        with patch.dict(os.environ, {"WRITEIT_WORKSPACE": "env_workspace"}):
            workspace = get_active_workspace()
            assert workspace == "env_workspace"

    def test_get_active_workspace_from_config(self):
        """Test getting active workspace from global config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a workspace manager with config
            workspace_manager = Workspace(Path(temp_dir) / ".writeit")
            workspace_manager.initialize()
            workspace_manager.set_active_workspace("default")

            with patch.dict(os.environ, {}, clear=True):
                if "WRITEIT_WORKSPACE" in os.environ:
                    del os.environ["WRITEIT_WORKSPACE"]

                # Mock the workspace manager creation
                with patch("writeit.workspace.workspace.Workspace") as mock_workspace:
                    mock_workspace.return_value = workspace_manager

                    workspace = get_active_workspace()
                    assert workspace == "default"

    def test_get_active_workspace_fallback(self):
        """Test getting active workspace fallback to default."""
        with patch.dict(os.environ, {}, clear=True):
            if "WRITEIT_WORKSPACE" in os.environ:
                del os.environ["WRITEIT_WORKSPACE"]

            # Mock workspace manager that doesn't have config
            with patch("writeit.workspace.workspace.Workspace") as mock_workspace:
                mock_instance = Mock()
                mock_instance.config_file.exists.return_value = False
                mock_workspace.return_value = mock_instance

                workspace = get_active_workspace()
                assert workspace == "default"
