# ABOUTME: Unit tests for WriteIt workspace management functionality
# ABOUTME: Tests Workspace class creation, configuration, and workspace operations
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from writeit.workspace.workspace import Workspace, WorkspaceConfig, GlobalConfig


class TestWorkspace:
    """Test suite for Workspace class."""
    
    @pytest.fixture
    def temp_home(self):
        """Create temporary directory for testing workspace operations."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def workspace(self, temp_home):
        """Create Workspace instance with temporary home directory."""
        return Workspace(temp_home / ".writeit")
    
    def test_workspace_initialization_properties(self, workspace, temp_home):
        """Test that workspace properties return correct paths."""
        expected_home = temp_home / ".writeit"
        
        assert workspace.home_dir == expected_home
        assert workspace.config_file == expected_home / "config.yaml"
        assert workspace.templates_dir == expected_home / "templates"
        assert workspace.styles_dir == expected_home / "styles"
        assert workspace.workspaces_dir == expected_home / "workspaces"
        assert workspace.cache_dir == expected_home / "cache"
    
    def test_initialize_creates_directory_structure(self, workspace):
        """Test that initialize() creates all required directories."""
        workspace.initialize()
        
        # Check all directories exist
        assert workspace.home_dir.exists()
        assert workspace.templates_dir.exists()
        assert workspace.styles_dir.exists()
        assert workspace.workspaces_dir.exists()
        assert workspace.cache_dir.exists()
        
        # Check default workspace was created
        assert workspace.workspace_exists("default")
        
        # Check global config was created
        assert workspace.config_file.exists()
    
    def test_initialize_creates_global_config(self, workspace):
        """Test that initialize() creates proper global configuration."""
        workspace.initialize()
        
        config = workspace.load_global_config()
        assert isinstance(config, GlobalConfig)
        assert config.active_workspace == "default"
        assert "default" in config.workspaces
        assert config.writeit_version == "0.1.0"
    
    def test_create_workspace_success(self, workspace):
        """Test successful workspace creation."""
        workspace.initialize()
        
        workspace_path = workspace.create_workspace("test_workspace")
        
        # Check workspace directory exists
        assert workspace_path.exists()
        assert workspace_path == workspace.workspaces_dir / "test_workspace"
        
        # Check subdirectories were created
        assert (workspace_path / "pipelines").exists()
        assert (workspace_path / "articles").exists()
        
        # Check workspace config was created
        config_file = workspace_path / "workspace.yaml"
        assert config_file.exists()
        
        # Check workspace was added to global config
        global_config = workspace.load_global_config()
        assert "test_workspace" in global_config.workspaces
    
    def test_create_workspace_duplicate_raises_error(self, workspace):
        """Test that creating duplicate workspace raises ValueError."""
        workspace.initialize()
        workspace.create_workspace("test_workspace")
        
        with pytest.raises(ValueError, match="Workspace 'test_workspace' already exists"):
            workspace.create_workspace("test_workspace")
    
    def test_workspace_exists(self, workspace):
        """Test workspace existence checking."""
        workspace.initialize()
        
        assert workspace.workspace_exists("default")
        assert not workspace.workspace_exists("nonexistent")
        
        workspace.create_workspace("new_workspace")
        assert workspace.workspace_exists("new_workspace")
    
    def test_get_workspace_path(self, workspace):
        """Test getting workspace path."""
        workspace.initialize()
        workspace.create_workspace("test_workspace")
        
        # Test with specific workspace name
        path = workspace.get_workspace_path("test_workspace")
        assert path == workspace.workspaces_dir / "test_workspace"
        
        # Test with default (active) workspace
        path = workspace.get_workspace_path()
        assert path == workspace.workspaces_dir / "default"
    
    def test_get_workspace_path_nonexistent_raises_error(self, workspace):
        """Test that getting path for nonexistent workspace raises error."""
        workspace.initialize()
        
        with pytest.raises(ValueError, match="Workspace 'nonexistent' does not exist"):
            workspace.get_workspace_path("nonexistent")
    
    def test_list_workspaces(self, workspace):
        """Test listing workspaces."""
        workspace.initialize()
        
        # Initially only default workspace
        workspaces = workspace.list_workspaces()
        assert workspaces == ["default"]
        
        # Add more workspaces
        workspace.create_workspace("workspace1")
        workspace.create_workspace("workspace2")
        
        workspaces = workspace.list_workspaces()
        assert set(workspaces) == {"default", "workspace1", "workspace2"}
    
    def test_list_workspaces_empty_directory(self, workspace):
        """Test listing workspaces when directory doesn't exist."""
        workspaces = workspace.list_workspaces()
        assert workspaces == []
    
    def test_get_active_workspace(self, workspace):
        """Test getting active workspace."""
        workspace.initialize()
        
        assert workspace.get_active_workspace() == "default"
    
    def test_set_active_workspace(self, workspace):
        """Test setting active workspace."""
        workspace.initialize()
        workspace.create_workspace("test_workspace")
        
        workspace.set_active_workspace("test_workspace")
        assert workspace.get_active_workspace() == "test_workspace"
    
    def test_set_active_workspace_nonexistent_raises_error(self, workspace):
        """Test that setting nonexistent workspace as active raises error."""
        workspace.initialize()
        
        with pytest.raises(ValueError, match="Workspace 'nonexistent' does not exist"):
            workspace.set_active_workspace("nonexistent")
    
    def test_remove_workspace(self, workspace):
        """Test workspace removal."""
        workspace.initialize()
        workspace.create_workspace("to_remove")
        
        assert workspace.workspace_exists("to_remove")
        
        # Switch to different workspace first
        workspace.set_active_workspace("default")
        workspace.remove_workspace("to_remove")
        
        assert not workspace.workspace_exists("to_remove")
        
        # Check it was removed from global config
        global_config = workspace.load_global_config()
        assert "to_remove" not in global_config.workspaces
    
    def test_remove_workspace_nonexistent_raises_error(self, workspace):
        """Test that removing nonexistent workspace raises error."""
        workspace.initialize()
        
        with pytest.raises(ValueError, match="Workspace 'nonexistent' does not exist"):
            workspace.remove_workspace("nonexistent")
    
    def test_remove_active_workspace_raises_error(self, workspace):
        """Test that removing active workspace raises error."""
        workspace.initialize()
        workspace.create_workspace("active_workspace")
        workspace.set_active_workspace("active_workspace")
        
        with pytest.raises(ValueError, match="Cannot remove active workspace"):
            workspace.remove_workspace("active_workspace")
    
    def test_load_workspace_config(self, workspace):
        """Test loading workspace configuration."""
        workspace.initialize()
        workspace.create_workspace("test_workspace")
        
        config = workspace.load_workspace_config("test_workspace")
        assert isinstance(config, WorkspaceConfig)
        assert config.name == "test_workspace"
        assert config.created_at is not None
    
    def test_load_workspace_config_nonexistent_raises_error(self, workspace):
        """Test that loading config for nonexistent workspace raises error."""
        workspace.initialize()
        
        with pytest.raises(ValueError, match="Workspace 'nonexistent' does not exist"):
            workspace.load_workspace_config("nonexistent")
    
    def test_global_config_caching(self, workspace):
        """Test that global config is cached properly."""
        workspace.initialize()
        
        # Load config twice, should be same object
        config1 = workspace.load_global_config()
        config2 = workspace.load_global_config()
        
        assert config1 is config2  # Same object due to caching
    
    def test_workspace_config_creation_with_timestamp(self, workspace):
        """Test that workspace config includes proper timestamp."""
        workspace.initialize()
        
        # Mock datetime to control timestamp
        with patch('writeit.workspace.workspace.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"
            
            workspace.create_workspace("timestamped")
            config = workspace.load_workspace_config("timestamped")
            
            assert config.created_at == "2023-01-01T12:00:00"


class TestWorkspaceConfig:
    """Test suite for WorkspaceConfig model."""
    
    def test_workspace_config_creation(self):
        """Test WorkspaceConfig creation with required fields."""
        config = WorkspaceConfig(
            name="test",
            created_at="2023-01-01T12:00:00"
        )
        
        assert config.name == "test"
        assert config.created_at == "2023-01-01T12:00:00"
        assert config.default_pipeline is None
        assert config.llm_providers == {}
    
    def test_workspace_config_with_optional_fields(self):
        """Test WorkspaceConfig creation with optional fields."""
        config = WorkspaceConfig(
            name="test",
            created_at="2023-01-01T12:00:00",
            default_pipeline="tech-article.yaml",
            llm_providers={"openai": "configured"}
        )
        
        assert config.default_pipeline == "tech-article.yaml"
        assert config.llm_providers == {"openai": "configured"}


class TestGlobalConfig:
    """Test suite for GlobalConfig model."""
    
    def test_global_config_defaults(self):
        """Test GlobalConfig creation with default values."""
        config = GlobalConfig()
        
        assert config.active_workspace == "default"
        assert config.workspaces == []
        assert config.writeit_version == "0.1.0"
    
    def test_global_config_with_custom_values(self):
        """Test GlobalConfig creation with custom values."""
        config = GlobalConfig(
            active_workspace="custom",
            workspaces=["default", "custom"],
            writeit_version="0.2.0"
        )
        
        assert config.active_workspace == "custom"
        assert config.workspaces == ["default", "custom"]
        assert config.writeit_version == "0.2.0"