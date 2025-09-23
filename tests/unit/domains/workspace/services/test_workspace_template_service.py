"""Tests for WorkspaceTemplateService.

Comprehensive test suite covering template resolution, scope management,
conflict detection, and workspace isolation for template operations.
"""

import pytest
from pathlib import Path
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock

from writeit.domains.workspace.services.workspace_template_service import (
    WorkspaceTemplateService,
    TemplateScope,
    TemplateVisibility,
    TemplateResolutionResult,
    TemplateSearchCriteria,
    WorkspaceTemplateError,
    TemplateNotFoundError,
    TemplateConflictError
)
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.repositories.workspace_repository import WorkspaceRepository
from writeit.domains.content.entities.template import Template
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.repositories.content_template_repository import ContentTemplateRepository
from writeit.shared.repository import RepositoryError


class TestWorkspaceTemplateService:
    """Test suite for WorkspaceTemplateService."""
    
    @pytest.fixture
    def workspace_repository(self):
        """Mock workspace repository."""
        return AsyncMock(spec=WorkspaceRepository)
    
    @pytest.fixture
    def content_template_repository(self):
        """Mock content template repository."""
        return AsyncMock(spec=ContentTemplateRepository)
    
    @pytest.fixture
    def service(self, workspace_repository, content_template_repository):
        """WorkspaceTemplateService instance with mocked dependencies."""
        return WorkspaceTemplateService(
            workspace_repository=workspace_repository,
            content_template_repository=content_template_repository
        )
    
    @pytest.fixture
    def sample_workspace_template(self):
        """Sample workspace template for testing."""
        return Template(
            id=ContentId("ws-template-1"),
            name=TemplateName("article-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Article pipeline template",
            tags=["article", "content"],
            variables=["topic", "style"],
            is_global=False
        )
    
    @pytest.fixture
    def sample_global_template(self):
        """Sample global template for testing."""
        return Template(
            id=ContentId("global-template-1"),
            name=TemplateName("global-article-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Global article pipeline template",
            tags=["article", "global"],
            variables=["topic", "style", "author"],
            is_global=True
        )
    
    @pytest.fixture
    def workspace_name(self):
        """Sample workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.fixture
    def template_name(self):
        """Sample template name."""
        return TemplateName("article-template")

    # Template Resolution Tests
    
    @pytest.mark.asyncio
    async def test_resolve_template_workspace_only_found(self, service, content_template_repository, 
                                                        sample_workspace_template, workspace_name, template_name):
        """Test successful workspace-only template resolution."""
        # Arrange
        content_template_repository.find_by_name_and_workspace.return_value = sample_workspace_template
        
        # Act
        result = await service.resolve_template(
            template_name, workspace_name, TemplateScope.WORKSPACE_ONLY
        )
        
        # Assert
        assert result is not None
        assert result.template == sample_workspace_template
        assert result.workspace_name == workspace_name
        assert result.scope == TemplateScope.WORKSPACE_ONLY
        assert not result.is_global
        assert result.display_name == f"article-template [Workspace: test-workspace]"
        
        content_template_repository.find_by_name_and_workspace.assert_called_once_with(
            template_name, workspace_name
        )
    
    @pytest.mark.asyncio
    async def test_resolve_template_workspace_only_not_found(self, service, content_template_repository, 
                                                            workspace_name, template_name):
        """Test workspace-only template resolution when not found."""
        # Arrange
        content_template_repository.find_by_name_and_workspace.return_value = None
        
        # Act
        result = await service.resolve_template(
            template_name, workspace_name, TemplateScope.WORKSPACE_ONLY
        )
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_resolve_template_global_only_found(self, service, content_template_repository, 
                                                     sample_global_template, template_name):
        """Test successful global-only template resolution."""
        # Arrange
        content_template_repository.find_global_templates.return_value = [sample_global_template]
        global_template_name = TemplateName("global-article-template")
        
        # Act
        result = await service.resolve_template(
            global_template_name, None, TemplateScope.GLOBAL_ONLY
        )
        
        # Assert
        assert result is not None
        assert result.template == sample_global_template
        assert result.workspace_name is None
        assert result.scope == TemplateScope.GLOBAL_ONLY
        assert result.is_global
        assert result.display_name == "global-article-template [Global]"
    
    @pytest.mark.asyncio
    async def test_resolve_template_global_only_not_found(self, service, content_template_repository, template_name):
        """Test global-only template resolution when not found."""
        # Arrange
        content_template_repository.find_global_templates.return_value = []
        
        # Act
        result = await service.resolve_template(
            template_name, None, TemplateScope.GLOBAL_ONLY
        )
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_resolve_template_workspace_first_found_in_workspace(self, service, content_template_repository, 
                                                                      sample_workspace_template, workspace_name, template_name):
        """Test workspace-first resolution finding template in workspace."""
        # Arrange
        content_template_repository.find_by_name_and_workspace.return_value = sample_workspace_template
        
        # Act
        result = await service.resolve_template(
            template_name, workspace_name, TemplateScope.WORKSPACE_FIRST
        )
        
        # Assert
        assert result is not None
        assert result.template == sample_workspace_template
        assert result.workspace_name == workspace_name
        assert not result.is_global
        
        content_template_repository.find_by_name_and_workspace.assert_called_once()
        content_template_repository.find_global_templates.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_resolve_template_workspace_first_fallback_to_global(self, service, content_template_repository, 
                                                                      sample_global_template, workspace_name):
        """Test workspace-first resolution falling back to global."""
        # Arrange
        global_template_name = TemplateName("global-article-template")
        content_template_repository.find_by_name_and_workspace.return_value = None
        content_template_repository.find_global_templates.return_value = [sample_global_template]
        
        # Act
        result = await service.resolve_template(
            global_template_name, workspace_name, TemplateScope.WORKSPACE_FIRST
        )
        
        # Assert
        assert result is not None
        assert result.template == sample_global_template
        assert result.workspace_name is None
        assert result.is_global
        
        content_template_repository.find_by_name_and_workspace.assert_called_once()
        content_template_repository.find_global_templates.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resolve_template_global_first_found_in_global(self, service, content_template_repository, 
                                                                sample_global_template, workspace_name):
        """Test global-first resolution finding template in global scope."""
        # Arrange
        global_template_name = TemplateName("global-article-template")
        content_template_repository.find_global_templates.return_value = [sample_global_template]
        
        # Act
        result = await service.resolve_template(
            global_template_name, workspace_name, TemplateScope.GLOBAL_FIRST
        )
        
        # Assert
        assert result is not None
        assert result.template == sample_global_template
        assert result.workspace_name is None
        assert result.is_global
        
        content_template_repository.find_global_templates.assert_called_once()
        content_template_repository.find_by_name_and_workspace.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_resolve_template_global_first_fallback_to_workspace(self, service, content_template_repository, 
                                                                      sample_workspace_template, workspace_name, template_name):
        """Test global-first resolution falling back to workspace."""
        # Arrange
        content_template_repository.find_global_templates.return_value = []
        content_template_repository.find_by_name_and_workspace.return_value = sample_workspace_template
        
        # Act
        result = await service.resolve_template(
            template_name, workspace_name, TemplateScope.GLOBAL_FIRST
        )
        
        # Assert
        assert result is not None
        assert result.template == sample_workspace_template
        assert result.workspace_name == workspace_name
        assert not result.is_global
        
        content_template_repository.find_global_templates.assert_called_once()
        content_template_repository.find_by_name_and_workspace.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resolve_template_repository_error(self, service, content_template_repository, template_name):
        """Test repository error handling during template resolution."""
        # Arrange
        content_template_repository.find_by_name_and_workspace.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(WorkspaceTemplateError, match="Template resolution failed"):
            await service.resolve_template(template_name, WorkspaceName("test"), TemplateScope.WORKSPACE_ONLY)
    
    @pytest.mark.asyncio
    async def test_resolve_template_unsupported_scope(self, service, template_name):
        """Test error handling for unsupported resolution scope."""
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported resolution scope"):
            await service.resolve_template(template_name, WorkspaceName("test"), "invalid_scope")

    # Template Listing Tests
    
    @pytest.mark.asyncio
    async def test_list_available_templates_workspace_only(self, service, content_template_repository, 
                                                          sample_workspace_template, workspace_name):
        """Test listing templates from workspace scope only."""
        # Arrange
        content_template_repository.find_all.return_value = [sample_workspace_template]
        
        # Act
        result = await service.list_available_templates(
            workspace_name, TemplateScope.WORKSPACE_ONLY
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].template == sample_workspace_template
        assert result[0].workspace_name == workspace_name
        assert not result[0].is_global
        
        content_template_repository.set_workspace.assert_called_once_with(workspace_name)
        content_template_repository.find_all.assert_called_once()
        content_template_repository.clear_workspace.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_available_templates_global_only(self, service, content_template_repository, sample_global_template):
        """Test listing templates from global scope only."""
        # Arrange
        content_template_repository.find_global_templates.return_value = [sample_global_template]
        
        # Act
        result = await service.list_available_templates(
            scope=TemplateScope.GLOBAL_ONLY
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].template == sample_global_template
        assert result[0].workspace_name is None
        assert result[0].is_global
        
        content_template_repository.find_global_templates.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_available_templates_all_scopes_with_deduplication(self, service, content_template_repository, 
                                                                         sample_workspace_template, sample_global_template):
        """Test listing templates from all scopes with proper deduplication."""
        # Arrange - create templates with same name to test deduplication
        workspace_template = Template(
            id=ContentId("ws-same-name"),
            name=TemplateName("shared-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Workspace version",
            tags=["workspace"],
            variables=["topic"],
            is_global=False
        )
        
        global_template = Template(
            id=ContentId("global-same-name"),
            name=TemplateName("shared-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Global version",
            tags=["global"],
            variables=["topic", "author"],
            is_global=True
        )
        
        content_template_repository.find_all.return_value = [workspace_template]
        content_template_repository.find_global_templates.return_value = [global_template]
        
        # Act
        result = await service.list_available_templates(
            WorkspaceName("test"), TemplateScope.ALL_SCOPES
        )
        
        # Assert - workspace template should take precedence
        assert len(result) == 1
        assert result[0].template == workspace_template
        assert not result[0].is_global
    
    @pytest.mark.asyncio
    async def test_list_available_templates_with_content_type_filter(self, service, content_template_repository, workspace_name):
        """Test listing templates with content type filtering."""
        # Arrange
        pipeline_template = Template(
            id=ContentId("pipeline-template"),
            name=TemplateName("pipeline-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Pipeline template",
            tags=["pipeline"],
            variables=["topic"],
            is_global=False
        )
        
        content_template_repository.find_by_content_type.return_value = [pipeline_template]
        
        # Act
        result = await service.list_available_templates(
            workspace_name, TemplateScope.WORKSPACE_ONLY, ContentType.PIPELINE
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].template.content_type == ContentType.PIPELINE
        content_template_repository.find_by_content_type.assert_called_once_with(ContentType.PIPELINE)
    
    @pytest.mark.asyncio
    async def test_list_available_templates_repository_error(self, service, content_template_repository, workspace_name):
        """Test repository error handling during template listing."""
        # Arrange
        content_template_repository.find_all.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(WorkspaceTemplateError, match="Template listing failed"):
            await service.list_available_templates(workspace_name, TemplateScope.WORKSPACE_ONLY)

    # Template Search Tests
    
    @pytest.mark.asyncio
    async def test_search_templates_by_name_pattern(self, service, content_template_repository, 
                                                   sample_workspace_template, workspace_name):
        """Test template search by name pattern."""
        # Arrange
        content_template_repository.find_all.return_value = [sample_workspace_template]
        
        criteria = TemplateSearchCriteria(
            name_pattern="article",
            scope=TemplateScope.WORKSPACE_ONLY
        )
        
        # Act
        result = await service.search_templates(criteria)
        
        # Assert
        assert len(result) == 1
        assert "article" in result[0].template.name.value.lower()
    
    @pytest.mark.asyncio
    async def test_search_templates_by_content_type(self, service, content_template_repository, 
                                                   sample_workspace_template, workspace_name):
        """Test template search by content type."""
        # Arrange
        content_template_repository.find_all.return_value = [sample_workspace_template]
        
        criteria = TemplateSearchCriteria(
            content_type=ContentType.PIPELINE,
            scope=TemplateScope.WORKSPACE_ONLY
        )
        
        # Act
        result = await service.search_templates(criteria)
        
        # Assert
        assert len(result) == 1
        assert result[0].template.content_type == ContentType.PIPELINE
    
    @pytest.mark.asyncio
    async def test_search_templates_by_tags(self, service, content_template_repository, 
                                           sample_workspace_template, workspace_name):
        """Test template search by tags."""
        # Arrange
        content_template_repository.find_all.return_value = [sample_workspace_template]
        
        criteria = TemplateSearchCriteria(
            tags=["article"],
            scope=TemplateScope.WORKSPACE_ONLY
        )
        
        # Act
        result = await service.search_templates(criteria)
        
        # Assert
        assert len(result) == 1
        assert "article" in result[0].template.tags
    
    @pytest.mark.asyncio
    async def test_search_templates_exclude_global(self, service, content_template_repository, 
                                                  sample_global_template):
        """Test template search excluding global templates."""
        # Arrange
        content_template_repository.find_global_templates.return_value = [sample_global_template]
        
        criteria = TemplateSearchCriteria(
            include_global=False,
            scope=TemplateScope.GLOBAL_ONLY
        )
        
        # Act
        result = await service.search_templates(criteria)
        
        # Assert
        assert len(result) == 0  # Global template excluded
    
    @pytest.mark.asyncio
    async def test_search_templates_no_matches(self, service, content_template_repository, 
                                              sample_workspace_template, workspace_name):
        """Test template search with no matches."""
        # Arrange
        content_template_repository.find_all.return_value = [sample_workspace_template]
        
        criteria = TemplateSearchCriteria(
            name_pattern="nonexistent",
            scope=TemplateScope.WORKSPACE_ONLY
        )
        
        # Act
        result = await service.search_templates(criteria)
        
        # Assert
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_search_templates_repository_error(self, service, content_template_repository):
        """Test repository error handling during template search."""
        # Arrange
        content_template_repository.find_all.side_effect = RepositoryError("Database error")
        
        criteria = TemplateSearchCriteria(scope=TemplateScope.WORKSPACE_ONLY)
        
        # Act & Assert
        with pytest.raises(WorkspaceTemplateError, match="Template search failed"):
            await service.search_templates(criteria)

    # Template Accessibility Tests
    
    @pytest.mark.asyncio
    async def test_validate_template_accessibility_accessible(self, service, content_template_repository, 
                                                             sample_workspace_template, workspace_name, template_name):
        """Test template accessibility validation when template is accessible."""
        # Arrange
        content_template_repository.find_by_name_and_workspace.return_value = sample_workspace_template
        
        # Act
        result = await service.validate_template_accessibility(template_name, workspace_name)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_template_accessibility_not_accessible(self, service, content_template_repository, 
                                                                 workspace_name, template_name):
        """Test template accessibility validation when template is not accessible."""
        # Arrange
        content_template_repository.find_by_name_and_workspace.return_value = None
        content_template_repository.find_global_templates.return_value = []
        
        # Act
        result = await service.validate_template_accessibility(template_name, workspace_name)
        
        # Assert
        assert result is False

    # Template Conflict Detection Tests
    
    @pytest.mark.asyncio
    async def test_detect_template_conflicts_with_conflicts(self, service, workspace_repository, content_template_repository):
        """Test template conflict detection when conflicts exist."""
        # Arrange
        workspace1 = Workspace(
            id="ws1",
            name=WorkspaceName("workspace1"),
            description="Test workspace 1",
            is_active=True
        )
        workspace2 = Workspace(
            id="ws2",
            name=WorkspaceName("workspace2"),
            description="Test workspace 2",
            is_active=False
        )
        
        workspace_repository.find_all.return_value = [workspace1, workspace2]
        
        # Template exists in both workspaces
        conflicting_template = Template(
            id=ContentId("conflict-template"),
            name=TemplateName("shared-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Conflicting template",
            tags=["shared"],
            variables=["topic"],
            is_global=False
        )
        
        content_template_repository.find_all.return_value = [conflicting_template]
        
        # Act
        conflicts = await service.detect_template_conflicts()
        
        # Assert
        assert len(conflicts) == 1
        template_name = TemplateName("shared-template")
        assert template_name in conflicts
        assert set(conflicts[template_name]) == {WorkspaceName("workspace1"), WorkspaceName("workspace2")}
    
    @pytest.mark.asyncio
    async def test_detect_template_conflicts_no_conflicts(self, service, workspace_repository, content_template_repository):
        """Test template conflict detection when no conflicts exist."""
        # Arrange
        workspace1 = Workspace(
            id="ws1",
            name=WorkspaceName("workspace1"),
            description="Test workspace 1",
            is_active=True
        )
        
        workspace_repository.find_all.return_value = [workspace1]
        
        unique_template = Template(
            id=ContentId("unique-template"),
            name=TemplateName("unique-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Unique template",
            tags=["unique"],
            variables=["topic"],
            is_global=False
        )
        
        content_template_repository.find_all.return_value = [unique_template]
        
        # Act
        conflicts = await service.detect_template_conflicts()
        
        # Assert
        assert len(conflicts) == 0
    
    @pytest.mark.asyncio
    async def test_detect_template_conflicts_specific_workspaces(self, service, content_template_repository):
        """Test template conflict detection for specific workspaces."""
        # Arrange
        target_workspaces = [WorkspaceName("workspace1"), WorkspaceName("workspace2")]
        
        conflicting_template = Template(
            id=ContentId("conflict-template"),
            name=TemplateName("shared-template"),
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Conflicting template",
            tags=["shared"],
            variables=["topic"],
            is_global=False
        )
        
        content_template_repository.find_all.return_value = [conflicting_template]
        
        # Act
        conflicts = await service.detect_template_conflicts(target_workspaces)
        
        # Assert
        assert len(conflicts) == 1
        template_name = TemplateName("shared-template")
        assert template_name in conflicts
        assert set(conflicts[template_name]) == set(target_workspaces)
        
        # Verify repository calls for each workspace
        assert content_template_repository.set_workspace.call_count == 2
        assert content_template_repository.find_all.call_count == 2
        assert content_template_repository.clear_workspace.call_count == 2
    
    @pytest.mark.asyncio
    async def test_detect_template_conflicts_repository_error(self, service, workspace_repository):
        """Test repository error handling during conflict detection."""
        # Arrange
        workspace_repository.find_all.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(WorkspaceTemplateError, match="Conflict detection failed"):
            await service.detect_template_conflicts()

    # Template Visibility Tests
    
    @pytest.mark.asyncio
    async def test_get_template_visibility_global(self, service, content_template_repository, sample_global_template):
        """Test getting template visibility for global template."""
        # Arrange
        global_template_name = TemplateName("global-article-template")
        content_template_repository.find_global_templates.return_value = [sample_global_template]
        
        # Act
        visibility = await service.get_template_visibility(global_template_name)
        
        # Assert
        assert visibility == TemplateVisibility.GLOBAL
    
    @pytest.mark.asyncio
    async def test_get_template_visibility_private(self, service, content_template_repository, 
                                                  sample_workspace_template, template_name):
        """Test getting template visibility for workspace-private template."""
        # Arrange
        content_template_repository.find_global_templates.return_value = []
        content_template_repository.find_by_name_and_workspace.return_value = sample_workspace_template
        
        # Act
        visibility = await service.get_template_visibility(template_name)
        
        # Assert
        assert visibility == TemplateVisibility.PRIVATE
    
    @pytest.mark.asyncio
    async def test_get_template_visibility_not_found(self, service, content_template_repository, template_name):
        """Test getting template visibility when template not found."""
        # Arrange
        content_template_repository.find_global_templates.return_value = []
        content_template_repository.find_by_name_and_workspace.return_value = None
        
        # Act & Assert
        with pytest.raises(TemplateNotFoundError):
            await service.get_template_visibility(template_name)
    
    @pytest.mark.asyncio
    async def test_get_template_visibility_repository_error(self, service, content_template_repository, template_name):
        """Test repository error handling during visibility determination."""
        # Arrange
        content_template_repository.find_global_templates.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(WorkspaceTemplateError, match="Visibility determination failed"):
            await service.get_template_visibility(template_name)

    # Helper Method Tests
    
    @pytest.mark.asyncio
    async def test_matches_criteria_all_filters(self, service, sample_workspace_template):
        """Test criteria matching with all filters applied."""
        # Arrange
        result = TemplateResolutionResult(
            template=sample_workspace_template,
            workspace_name=WorkspaceName("test-workspace"),
            scope=TemplateScope.WORKSPACE_ONLY,
            is_global=False,
            path=Path("/workspace/templates/template.yaml")
        )
        
        criteria = TemplateSearchCriteria(
            name_pattern="article",
            content_type=ContentType.PIPELINE,
            tags=["article"],
            include_global=True,
            workspace_names=[WorkspaceName("test-workspace")]
        )
        
        # Act
        matches = service._matches_criteria(result, criteria)
        
        # Assert
        assert matches is True
    
    @pytest.mark.asyncio
    async def test_matches_criteria_no_match(self, service, sample_workspace_template):
        """Test criteria matching with no match."""
        # Arrange
        result = TemplateResolutionResult(
            template=sample_workspace_template,
            workspace_name=WorkspaceName("test-workspace"),
            scope=TemplateScope.WORKSPACE_ONLY,
            is_global=False,
            path=Path("/workspace/templates/template.yaml")
        )
        
        criteria = TemplateSearchCriteria(
            name_pattern="nonexistent",  # Won't match "article-template"
        )
        
        # Act
        matches = service._matches_criteria(result, criteria)
        
        # Assert
        assert matches is False

    # Error Handling Tests
    
    def test_template_not_found_error_creation(self):
        """Test TemplateNotFoundError creation and message formatting."""
        # Arrange
        name = TemplateName("missing-template")
        scope = TemplateScope.WORKSPACE_ONLY
        workspace = WorkspaceName("test-workspace")
        
        # Act
        error = TemplateNotFoundError(name, scope, workspace)
        
        # Assert
        assert "missing-template" in str(error)
        assert "workspace_only" in str(error)
        assert "test-workspace" in str(error)
    
    def test_template_conflict_error_creation(self):
        """Test TemplateConflictError creation and message formatting."""
        # Arrange
        name = TemplateName("conflicting-template")
        workspaces = [WorkspaceName("workspace1"), WorkspaceName("workspace2")]
        
        # Act
        error = TemplateConflictError(name, workspaces)
        
        # Assert
        assert "conflicting-template" in str(error)
        assert "workspace1" in str(error)
        assert "workspace2" in str(error)

    # Integration-style Tests
    
    @pytest.mark.asyncio
    async def test_full_template_resolution_workflow(self, service, content_template_repository, 
                                                    sample_workspace_template, sample_global_template):
        """Test complete template resolution workflow."""
        # Arrange - template exists in workspace and globally
        workspace_name = WorkspaceName("test-workspace")
        shared_template_name = TemplateName("shared-template")
        
        workspace_template = Template(
            id=ContentId("ws-shared"),
            name=shared_template_name,
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Workspace version",
            tags=["workspace"],
            variables=["topic"],
            is_global=False
        )
        
        global_template = Template(
            id=ContentId("global-shared"),
            name=shared_template_name,
            content_type=ContentType.PIPELINE,
            format=ContentFormat.YAML,
            description="Global version",
            tags=["global"],
            variables=["topic", "author"],
            is_global=True
        )
        
        content_template_repository.find_by_name_and_workspace.return_value = workspace_template
        content_template_repository.find_global_templates.return_value = [global_template]
        
        # Act - Test different resolution strategies
        workspace_first_result = await service.resolve_template(
            shared_template_name, workspace_name, TemplateScope.WORKSPACE_FIRST
        )
        global_first_result = await service.resolve_template(
            shared_template_name, workspace_name, TemplateScope.GLOBAL_FIRST
        )
        
        # Assert - Workspace-first should return workspace version
        assert workspace_first_result is not None
        assert workspace_first_result.template.description == "Workspace version"
        assert not workspace_first_result.is_global
        
        # Global-first should return global version
        assert global_first_result is not None
        assert global_first_result.template.description == "Global version"
        assert global_first_result.is_global
