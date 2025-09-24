"""Pytest fixtures for mock repository implementations.

Provides easy-to-use fixtures for all domain repository mocks with proper
dependency injection support and workspace configuration.
"""

import pytest
from typing import Dict, Any

from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName

# Import all mock repository implementations
from ..mocks import (
    MockPipelineTemplateRepository,
    MockPipelineRunRepository,
    MockStepExecutionRepository,
    MockWorkspaceRepository,
    MockWorkspaceConfigRepository,
    MockContentTemplateRepository,
    MockStylePrimerRepository,
    MockGeneratedContentRepository,
    MockLLMCacheRepository,
    MockTokenUsageRepository,
)


# ============================================================================
# Default Test Workspace
# ============================================================================

@pytest.fixture
def test_workspace_name() -> WorkspaceName:
    """Provide test workspace name."""
    return WorkspaceName("test-workspace")


# ============================================================================
# Pipeline Domain Mock Repositories
# ============================================================================

@pytest.fixture
def mock_pipeline_template_repository(test_workspace_name: WorkspaceName) -> MockPipelineTemplateRepository:
    """Provide mock pipeline template repository."""
    repo = MockPipelineTemplateRepository(test_workspace_name)
    return repo


@pytest.fixture
def mock_pipeline_run_repository(test_workspace_name: WorkspaceName) -> MockPipelineRunRepository:
    """Provide mock pipeline run repository."""
    repo = MockPipelineRunRepository(test_workspace_name)
    return repo


@pytest.fixture
def mock_step_execution_repository(test_workspace_name: WorkspaceName) -> MockStepExecutionRepository:
    """Provide mock step execution repository."""
    repo = MockStepExecutionRepository(test_workspace_name)
    return repo


# ============================================================================
# Workspace Domain Mock Repositories
# ============================================================================

@pytest.fixture
def mock_workspace_repository() -> MockWorkspaceRepository:
    """Provide mock workspace repository."""
    repo = MockWorkspaceRepository()
    return repo


@pytest.fixture
def mock_workspace_config_repository() -> MockWorkspaceConfigRepository:
    """Provide mock workspace configuration repository."""
    repo = MockWorkspaceConfigRepository()
    return repo


# ============================================================================
# Content Domain Mock Repositories
# ============================================================================

@pytest.fixture
def mock_content_template_repository(test_workspace_name: WorkspaceName) -> MockContentTemplateRepository:
    """Provide mock content template repository."""
    repo = MockContentTemplateRepository(test_workspace_name)
    return repo


@pytest.fixture
def mock_style_primer_repository(test_workspace_name: WorkspaceName) -> MockStylePrimerRepository:
    """Provide mock style primer repository."""
    repo = MockStylePrimerRepository(test_workspace_name)
    return repo


@pytest.fixture
def mock_generated_content_repository(test_workspace_name: WorkspaceName) -> MockGeneratedContentRepository:
    """Provide mock generated content repository."""
    repo = MockGeneratedContentRepository(test_workspace_name)
    return repo


# ============================================================================
# Execution Domain Mock Repositories
# ============================================================================

@pytest.fixture
def mock_llm_cache_repository() -> MockLLMCacheRepository:
    """Provide mock LLM cache repository."""
    repo = MockLLMCacheRepository()
    return repo


@pytest.fixture
def mock_token_usage_repository() -> MockTokenUsageRepository:
    """Provide mock token usage repository."""
    repo = MockTokenUsageRepository()
    return repo


# ============================================================================
# Repository Collections
# ============================================================================

@pytest.fixture
def mock_pipeline_repositories(
    mock_pipeline_template_repository: MockPipelineTemplateRepository,
    mock_pipeline_run_repository: MockPipelineRunRepository,
    mock_step_execution_repository: MockStepExecutionRepository
) -> Dict[str, Any]:
    """Provide collection of all pipeline domain mock repositories."""
    return {
        "template": mock_pipeline_template_repository,
        "run": mock_pipeline_run_repository,
        "step_execution": mock_step_execution_repository
    }


@pytest.fixture
def mock_workspace_repositories(
    mock_workspace_repository: MockWorkspaceRepository,
    mock_workspace_config_repository: MockWorkspaceConfigRepository
) -> Dict[str, Any]:
    """Provide collection of all workspace domain mock repositories."""
    return {
        "workspace": mock_workspace_repository,
        "config": mock_workspace_config_repository
    }


@pytest.fixture
def mock_content_repositories(
    mock_content_template_repository: MockContentTemplateRepository,
    mock_style_primer_repository: MockStylePrimerRepository,
    mock_generated_content_repository: MockGeneratedContentRepository
) -> Dict[str, Any]:
    """Provide collection of all content domain mock repositories."""
    return {
        "template": mock_content_template_repository,
        "style_primer": mock_style_primer_repository,
        "generated_content": mock_generated_content_repository
    }


@pytest.fixture
def mock_execution_repositories(
    mock_llm_cache_repository: MockLLMCacheRepository,
    mock_token_usage_repository: MockTokenUsageRepository
) -> Dict[str, Any]:
    """Provide collection of all execution domain mock repositories."""
    return {
        "llm_cache": mock_llm_cache_repository,
        "token_usage": mock_token_usage_repository
    }


@pytest.fixture
def all_mock_repositories(
    mock_pipeline_repositories: Dict[str, Any],
    mock_workspace_repositories: Dict[str, Any],
    mock_content_repositories: Dict[str, Any],
    mock_execution_repositories: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Provide collection of ALL mock repositories organized by domain."""
    return {
        "pipeline": mock_pipeline_repositories,
        "workspace": mock_workspace_repositories,
        "content": mock_content_repositories,
        "execution": mock_execution_repositories
    }


# ============================================================================
# Repository Configuration Helpers
# ============================================================================

@pytest.fixture
def configure_mock_behavior():
    """Provide helper function to configure mock repository behavior."""
    
    def _configure(repository, method_name: str, **kwargs):
        """Configure mock repository behavior.
        
        Args:
            repository: Mock repository instance
            method_name: Method to configure
            **kwargs: Configuration options:
                - error: Exception to raise
                - delay: Delay in seconds
                - return_value: Fixed return value
        """
        if "error" in kwargs:
            repository.behavior.set_error_condition(method_name, kwargs["error"])
        if "delay" in kwargs:
            repository.behavior.set_call_delay(method_name, kwargs["delay"])
        if "return_value" in kwargs:
            repository.behavior.set_return_value(method_name, kwargs["return_value"])
            
    return _configure


@pytest.fixture
def clear_mock_state():
    """Provide helper function to clear mock repository state."""
    
    def _clear(*repositories):
        """Clear state of one or more mock repositories."""
        for repo in repositories:
            repo.clear_state()
            
    return _clear


@pytest.fixture
def mock_behavior_assertions():
    """Provide helper functions for asserting mock behavior."""
    
    class MockAssertions:
        @staticmethod
        def assert_called(repository, method_name: str, expected_count: int = 1):
            """Assert that method was called expected number of times."""
            actual_count = repository.behavior.get_call_count(method_name)
            assert actual_count == expected_count, (
                f"Expected {method_name} to be called {expected_count} times, "
                f"but was called {actual_count} times"
            )
            
        @staticmethod
        def assert_not_called(repository, method_name: str):
            """Assert that method was not called."""
            MockAssertions.assert_called(repository, method_name, 0)
            
        @staticmethod
        def assert_event_logged(repository, operation: str, entity_type: str = None):
            """Assert that specific event was logged."""
            events = repository.event_log
            matching_events = [
                e for e in events 
                if e["operation"] == operation and 
                (entity_type is None or e["entity_type"] == entity_type)
            ]
            assert len(matching_events) > 0, (
                f"Expected event with operation '{operation}' "
                f"{'and entity_type ' + entity_type if entity_type else ''} "
                f"but found {len(matching_events)} matching events"
            )
            
        @staticmethod
        def get_logged_events(repository, operation: str = None):
            """Get logged events, optionally filtered by operation."""
            events = repository.event_log
            if operation:
                return [e for e in events if e["operation"] == operation]
            return events
            
    return MockAssertions()


# ============================================================================
# Pre-configured Mock Scenarios
# ============================================================================

@pytest.fixture
def slow_repository_scenario(all_mock_repositories, configure_mock_behavior):
    """Configure all repositories to have slow response times for performance testing."""
    delay_seconds = 0.1
    
    for domain_repos in all_mock_repositories.values():
        for repo in domain_repos.values():
            # Add delay to common operations
            configure_mock_behavior(repo, "save", delay=delay_seconds)
            configure_mock_behavior(repo, "find_by_id", delay=delay_seconds)
            configure_mock_behavior(repo, "find_all", delay=delay_seconds)
            
    return all_mock_repositories


@pytest.fixture
def error_prone_repository_scenario(all_mock_repositories, configure_mock_behavior):
    """Configure repositories to simulate various error conditions."""
    from ..mocks.base_mock_repository import MockRepositoryError
    
    # Configure different repositories to fail on different operations
    for domain_name, domain_repos in all_mock_repositories.items():
        for repo_name, repo in domain_repos.items():
            # Make save operations fail occasionally
            if repo_name in ["template", "workspace"]:
                configure_mock_behavior(
                    repo, 
                    "save", 
                    error=MockRepositoryError(f"Mock {domain_name} {repo_name} save error")
                )
                
    return all_mock_repositories


@pytest.fixture
def populated_mock_repositories(all_mock_repositories):
    """Provide mock repositories pre-populated with test data."""
    # This would be populated with actual test entities in a real implementation
    # For now, return empty repositories that can be populated by individual tests
    return all_mock_repositories


# ============================================================================
# Integration Test Helpers
# ============================================================================

@pytest.fixture
def repository_integration_test_setup(all_mock_repositories, test_workspace_name):
    """Setup for integration tests requiring multiple repositories."""
    
    class IntegrationTestSetup:
        def __init__(self, repositories, workspace_name):
            self.repositories = repositories
            self.workspace_name = workspace_name
            
        async def create_test_workspace(self):
            """Create a test workspace using mock repositories."""
            from writeit.domains.workspace.entities.workspace import Workspace
            from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
            from datetime import datetime
            
            workspace = Workspace(
                name=self.workspace_name,
                path=WorkspacePath(f"/test/{self.workspace_name.value}"),
                created_at=datetime.now(),
                description="Test workspace for integration tests"
            )
            
            await self.repositories["workspace"]["workspace"].save(workspace)
            return workspace
            
        async def create_test_pipeline_template(self):
            """Create a test pipeline template."""
            from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
            from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
            from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
            from writeit.domains.pipeline.entities.pipeline_metadata import PipelineMetadata
            
            template = PipelineTemplate(
                id=PipelineId(),
                name=PipelineName("test-template"),
                metadata=PipelineMetadata(
                    name="Test Template",
                    description="Test pipeline template",
                    version="1.0.0"
                ),
                workspace=self.workspace_name
            )
            
            await self.repositories["pipeline"]["template"].save(template)
            return template
            
        def get_repository(self, domain: str, repo_type: str):
            """Get specific repository by domain and type."""
            return self.repositories[domain][repo_type]
            
    return IntegrationTestSetup(all_mock_repositories, test_workspace_name)