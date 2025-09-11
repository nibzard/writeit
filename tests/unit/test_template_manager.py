# ABOUTME: Unit tests for TemplateManager
# ABOUTME: Tests template resolution, creation, and management across workspace/global scopes

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from writeit.workspace.workspace import Workspace
from writeit.workspace.template_manager import (
    TemplateManager,
    TemplateType,
    TemplateScope,
    TemplateLocation,
)


@pytest.fixture
def temp_home() -> Generator[Path, None, None]:
    """Create temporary home directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def workspace_manager(temp_home: Path) -> Workspace:
    """Create workspace manager with temporary home."""
    workspace = Workspace(temp_home)
    workspace.initialize()
    return workspace


@pytest.fixture
def template_manager(workspace_manager: Workspace) -> TemplateManager:
    """Create template manager with workspace."""
    return TemplateManager(workspace_manager)


@pytest.fixture
def sample_pipeline_content() -> str:
    """Sample pipeline template content."""
    return """metadata:
  name: "Test Pipeline"
  description: "Test pipeline template"

inputs:
  topic:
    type: "text"
    description: "Article topic"

steps:
  - name: "generate"
    description: "Generate content"
    prompt_template: "Write about {{ topic }}"
"""


@pytest.fixture
def sample_style_content() -> str:
    """Sample style primer content."""
    return """metadata:
  name: "Test Style"
  description: "Test style primer"

voice:
  personality: "Professional"
  tone: "Informative"

language:
  formality: "professional_casual"
"""


class TestTemplateManager:
    """Test cases for TemplateManager."""

    def test_template_manager_initialization(self, workspace_manager: Workspace):
        """Test template manager initialization."""
        template_manager = TemplateManager(workspace_manager)
        assert template_manager.workspace_manager == workspace_manager

    def test_template_manager_without_workspace(self):
        """Test template manager with default workspace."""
        template_manager = TemplateManager()
        assert template_manager.workspace_manager is not None

    def test_create_global_pipeline_template(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test creating a global pipeline template."""
        location = template_manager.create_template(
            name="test-pipeline",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        assert location.scope == TemplateScope.GLOBAL
        assert location.name == "test-pipeline"
        assert location.path.exists()
        assert location.workspace_name is None

        # Verify content
        with open(location.path, "r") as f:
            assert f.read() == sample_pipeline_content

    def test_create_workspace_pipeline_template(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test creating a workspace pipeline template."""
        # Create workspace first
        template_manager.workspace_manager.create_workspace("test-workspace")

        location = template_manager.create_template(
            name="workspace-pipeline",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        assert location.scope == TemplateScope.WORKSPACE
        assert location.name == "workspace-pipeline"
        assert location.path.exists()
        assert location.workspace_name == "test-workspace"

    def test_create_global_style_template(
        self, template_manager: TemplateManager, sample_style_content: str
    ):
        """Test creating a global style template."""
        location = template_manager.create_template(
            name="test-style",
            template_type=TemplateType.STYLE,
            content=sample_style_content,
            scope=TemplateScope.GLOBAL,
        )

        assert location.scope == TemplateScope.GLOBAL
        assert location.name == "test-style"
        assert location.path.exists()
        assert location.workspace_name is None

    def test_create_workspace_style_template(
        self, template_manager: TemplateManager, sample_style_content: str
    ):
        """Test creating a workspace style template."""
        # Create workspace first
        template_manager.workspace_manager.create_workspace("test-workspace")

        location = template_manager.create_template(
            name="workspace-style",
            template_type=TemplateType.STYLE,
            content=sample_style_content,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        assert location.scope == TemplateScope.WORKSPACE
        assert location.name == "workspace-style"
        assert location.path.exists()
        assert location.workspace_name == "test-workspace"

    def test_create_duplicate_template_fails(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test that creating duplicate template fails."""
        # Create first template
        template_manager.create_template(
            name="duplicate",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        # Attempt to create duplicate should fail
        with pytest.raises(ValueError, match="already exists"):
            template_manager.create_template(
                name="duplicate",
                template_type=TemplateType.PIPELINE,
                content=sample_pipeline_content,
                scope=TemplateScope.GLOBAL,
            )

    def test_resolve_global_template(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test resolving global template."""
        # Create global template
        template_manager.create_template(
            name="global-template",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        # Resolve template
        location = template_manager.resolve_template(
            name="global-template",
            template_type=TemplateType.PIPELINE,
            scope=TemplateScope.AUTO,
        )

        assert location is not None
        assert location.scope == TemplateScope.GLOBAL
        assert location.name == "global-template"
        assert location.exists

    def test_resolve_workspace_template_priority(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test that workspace template takes priority over global."""
        # Create workspace
        template_manager.workspace_manager.create_workspace("test-workspace")

        # Create global template
        template_manager.create_template(
            name="priority-test",
            template_type=TemplateType.PIPELINE,
            content="global content",
            scope=TemplateScope.GLOBAL,
        )

        # Create workspace template with same name
        template_manager.create_template(
            name="priority-test",
            template_type=TemplateType.PIPELINE,
            content="workspace content",
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        # Resolve should return workspace template
        location = template_manager.resolve_template(
            name="priority-test",
            template_type=TemplateType.PIPELINE,
            workspace_name="test-workspace",
            scope=TemplateScope.AUTO,
        )

        assert location is not None
        assert location.scope == TemplateScope.WORKSPACE
        assert location.workspace_name == "test-workspace"

        # Verify content
        with open(location.path, "r") as f:
            assert f.read() == "workspace content"

    def test_resolve_global_scope_only(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test resolving with global scope only."""
        # Create workspace
        template_manager.workspace_manager.create_workspace("test-workspace")

        # Create both global and workspace templates
        template_manager.create_template(
            name="scope-test",
            template_type=TemplateType.PIPELINE,
            content="global content",
            scope=TemplateScope.GLOBAL,
        )

        template_manager.create_template(
            name="scope-test",
            template_type=TemplateType.PIPELINE,
            content="workspace content",
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        # Resolve with global scope should return global template
        location = template_manager.resolve_template(
            name="scope-test",
            template_type=TemplateType.PIPELINE,
            workspace_name="test-workspace",
            scope=TemplateScope.GLOBAL,
        )

        assert location is not None
        assert location.scope == TemplateScope.GLOBAL

        # Verify content
        with open(location.path, "r") as f:
            assert f.read() == "global content"

    def test_resolve_nonexistent_template(self, template_manager: TemplateManager):
        """Test resolving nonexistent template returns None."""
        location = template_manager.resolve_template(
            name="nonexistent",
            template_type=TemplateType.PIPELINE,
            scope=TemplateScope.AUTO,
        )

        assert location is None

    def test_list_templates_empty(self, template_manager: TemplateManager):
        """Test listing templates when none exist."""
        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE, scope=TemplateScope.AUTO
        )

        assert templates == []

    def test_list_global_templates_only(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test listing global templates only."""
        # Create global templates
        template_manager.create_template(
            name="global1",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        template_manager.create_template(
            name="global2",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE, scope=TemplateScope.GLOBAL
        )

        assert len(templates) == 2
        assert all(t.scope == TemplateScope.GLOBAL for t in templates)
        names = [t.name for t in templates]
        assert "global1" in names
        assert "global2" in names

    def test_list_workspace_templates_only(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test listing workspace templates only."""
        # Create workspace
        template_manager.workspace_manager.create_workspace("test-workspace")

        # Create workspace templates
        template_manager.create_template(
            name="workspace1",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        template_manager.create_template(
            name="workspace2",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        assert len(templates) == 2
        assert all(t.scope == TemplateScope.WORKSPACE for t in templates)
        assert all(t.workspace_name == "test-workspace" for t in templates)
        names = [t.name for t in templates]
        assert "workspace1" in names
        assert "workspace2" in names

    def test_list_all_templates_with_priority(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test listing all templates with workspace priority."""
        # Create workspace
        template_manager.workspace_manager.create_workspace("test-workspace")

        # Create global templates
        template_manager.create_template(
            name="global-only",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        template_manager.create_template(
            name="both-scopes",
            template_type=TemplateType.PIPELINE,
            content="global content",
            scope=TemplateScope.GLOBAL,
        )

        # Create workspace templates
        template_manager.create_template(
            name="workspace-only",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        template_manager.create_template(
            name="both-scopes",
            template_type=TemplateType.PIPELINE,
            content="workspace content",
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE,
            workspace_name="test-workspace",
            scope=TemplateScope.AUTO,
        )

        # Should have 3 templates: global-only, workspace-only, and workspace version of both-scopes
        assert len(templates) == 3
        names = [t.name for t in templates]
        assert "global-only" in names
        assert "workspace-only" in names
        assert "both-scopes" in names

        # Verify workspace template takes priority for both-scopes
        both_scopes_template = next(t for t in templates if t.name == "both-scopes")
        assert both_scopes_template.scope == TemplateScope.WORKSPACE

    def test_copy_template_global_to_workspace(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test copying template from global to workspace."""
        # Create workspace
        template_manager.workspace_manager.create_workspace("test-workspace")

        # Create global template
        template_manager.create_template(
            name="source-template",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        # Copy to workspace
        location = template_manager.copy_template(
            source_name="source-template",
            dest_name="copied-template",
            template_type=TemplateType.PIPELINE,
            dest_workspace="test-workspace",
            dest_scope=TemplateScope.WORKSPACE,
        )

        assert location.scope == TemplateScope.WORKSPACE
        assert location.name == "copied-template"
        assert location.workspace_name == "test-workspace"
        assert location.exists

        # Verify content was copied
        with open(location.path, "r") as f:
            assert f.read() == sample_pipeline_content

    def test_copy_template_workspace_to_global(
        self, template_manager: TemplateManager, sample_style_content: str
    ):
        """Test copying template from workspace to global."""
        # Create workspace
        template_manager.workspace_manager.create_workspace("test-workspace")

        # Create workspace template
        template_manager.create_template(
            name="workspace-source",
            template_type=TemplateType.STYLE,
            content=sample_style_content,
            workspace_name="test-workspace",
            scope=TemplateScope.WORKSPACE,
        )

        # Copy to global
        location = template_manager.copy_template(
            source_name="workspace-source",
            dest_name="global-copy",
            template_type=TemplateType.STYLE,
            source_workspace="test-workspace",
            dest_scope=TemplateScope.GLOBAL,
        )

        assert location.scope == TemplateScope.GLOBAL
        assert location.name == "global-copy"
        assert location.workspace_name is None
        assert location.exists

        # Verify content was copied
        with open(location.path, "r") as f:
            assert f.read() == sample_style_content

    def test_copy_nonexistent_template_fails(self, template_manager: TemplateManager):
        """Test that copying nonexistent template fails."""
        with pytest.raises(ValueError, match="not found"):
            template_manager.copy_template(
                source_name="nonexistent",
                dest_name="destination",
                template_type=TemplateType.PIPELINE,
                dest_scope=TemplateScope.GLOBAL,
            )

    def test_copy_to_existing_template_fails(
        self, template_manager: TemplateManager, sample_pipeline_content: str
    ):
        """Test that copying to existing template fails."""
        # Create source and destination templates
        template_manager.create_template(
            name="source",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        template_manager.create_template(
            name="existing-dest",
            template_type=TemplateType.PIPELINE,
            content=sample_pipeline_content,
            scope=TemplateScope.GLOBAL,
        )

        # Copy to existing should fail
        with pytest.raises(ValueError, match="already exists"):
            template_manager.copy_template(
                source_name="source",
                dest_name="existing-dest",
                template_type=TemplateType.PIPELINE,
                dest_scope=TemplateScope.GLOBAL,
            )


class TestTemplateLocation:
    """Test cases for TemplateLocation."""

    def test_template_location_creation(self, temp_home: Path):
        """Test TemplateLocation creation."""
        path = temp_home / "test.yaml"
        location = TemplateLocation(path, TemplateScope.GLOBAL)

        assert location.path == path
        assert location.scope == TemplateScope.GLOBAL
        assert location.workspace_name is None
        assert location.name == "test"
        assert not location.exists  # File doesn't exist yet

    def test_template_location_with_workspace(self, temp_home: Path):
        """Test TemplateLocation with workspace."""
        path = temp_home / "test.yaml"
        location = TemplateLocation(path, TemplateScope.WORKSPACE, "my-workspace")

        assert location.workspace_name == "my-workspace"
        assert str(location) == "test [Workspace: my-workspace]"

    def test_template_location_global_display(self, temp_home: Path):
        """Test TemplateLocation global display."""
        path = temp_home / "test.yaml"
        location = TemplateLocation(path, TemplateScope.GLOBAL)

        assert str(location) == "test [Global]"

    def test_template_location_exists_check(self, temp_home: Path):
        """Test TemplateLocation exists check."""
        path = temp_home / "test.yaml"
        location = TemplateLocation(path, TemplateScope.GLOBAL)

        assert not location.exists

        # Create file
        path.write_text("test content")

        # Create new location instance to check existence
        location2 = TemplateLocation(path, TemplateScope.GLOBAL)
        assert location2.exists
