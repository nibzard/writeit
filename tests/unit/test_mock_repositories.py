"""Unit tests for mock repository implementations.

Tests that verify mock repositories behave correctly and provide
expected functionality for testing domain logic.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.execution.value_objects.cache_key import CacheKey
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount

from ..mocks.base_mock_repository import MockRepositoryError, MockEntityNotFoundError


class TestBaseMockRepository:
    """Test the base mock repository functionality."""
    
    def test_workspace_isolation(self, mock_pipeline_template_repository):
        """Test that workspace isolation works correctly."""
        repo = mock_pipeline_template_repository
        
        # Mock repositories should isolate by workspace
        assert repo.workspace_name == "test-workspace"
        
        # Different workspaces should have separate storage
        workspace1_storage = repo._get_workspace_storage("workspace1") 
        workspace2_storage = repo._get_workspace_storage("workspace2")
        assert workspace1_storage is not workspace2_storage
        
    def test_behavior_configuration(self, mock_pipeline_template_repository):
        """Test mock behavior configuration."""
        repo = mock_pipeline_template_repository
        
        # Configure error condition
        test_error = MockRepositoryError("Test error")
        repo.behavior.set_error_condition("save", test_error)
        
        # Configure return value
        repo.behavior.set_return_value("count", 42)
        
        # Verify configuration
        assert repo.behavior.error_conditions["save"] == test_error
        assert repo.behavior.return_values["count"] == 42
        
    def test_call_tracking(self, mock_pipeline_template_repository):
        """Test that method calls are tracked correctly."""
        repo = mock_pipeline_template_repository
        
        # Initially no calls
        assert repo.behavior.get_call_count("save") == 0
        
        # Simulate calls
        repo._increment_call_count("save")
        repo._increment_call_count("save")
        repo._increment_call_count("find_by_id")
        
        # Verify tracking
        assert repo.behavior.get_call_count("save") == 2
        assert repo.behavior.get_call_count("find_by_id") == 1
        assert repo.behavior.get_call_count("delete") == 0
        
    def test_event_logging(self, mock_pipeline_template_repository):
        """Test that repository operations are logged."""
        repo = mock_pipeline_template_repository
        
        # Initially no events
        assert len(repo.event_log) == 0
        
        # Log some events
        repo._log_event("save", "TestEntity", "test-id", extra_data="test")
        repo._log_event("find_by_id", "TestEntity", "test-id", found=True)
        
        # Verify logging
        events = repo.event_log
        assert len(events) == 2
        
        save_event = events[0]
        assert save_event["operation"] == "save"
        assert save_event["entity_type"] == "TestEntity"
        assert save_event["entity_id"] == "test-id"
        assert save_event["extra_data"] == "test"
        assert save_event["workspace"] == "test-workspace"
        
        find_event = events[1]
        assert find_event["operation"] == "find_by_id"
        assert find_event["found"] is True
        
    def test_state_management(self, mock_pipeline_template_repository):
        """Test state management and clearing."""
        repo = mock_pipeline_template_repository
        
        # Add some state
        repo._store_entity("test-entity", "test-id")
        repo._log_event("test", "TestEntity", "test-id")
        repo._increment_call_count("save")
        
        # Verify state exists
        assert repo._get_entity("test-id") == "test-entity"
        assert len(repo.event_log) == 1
        assert repo.behavior.get_call_count("save") == 1
        
        # Clear state
        repo.clear_state()
        
        # Verify state cleared
        assert repo._get_entity("test-id") is None
        assert len(repo.event_log) == 0
        assert repo.behavior.get_call_count("save") == 0


class TestMockRepositoryFixtures:
    """Test that pytest fixtures work correctly."""
    
    def test_workspace_fixture(self, test_workspace_name):
        """Test workspace name fixture."""
        assert isinstance(test_workspace_name, WorkspaceName)
        assert test_workspace_name.value == "test-workspace"
        
    def test_repository_fixtures(self, all_mock_repositories):
        """Test that all repository fixtures are available."""
        repos = all_mock_repositories
        
        # Verify all domains present
        assert "pipeline" in repos
        assert "workspace" in repos
        assert "content" in repos
        assert "execution" in repos
        
        # Verify pipeline repositories
        pipeline_repos = repos["pipeline"]
        assert "template" in pipeline_repos
        assert "run" in pipeline_repos
        assert "step_execution" in pipeline_repos
        
        # Verify workspace repositories
        workspace_repos = repos["workspace"]
        assert "workspace" in workspace_repos
        assert "config" in workspace_repos
        
        # Verify content repositories
        content_repos = repos["content"]
        assert "template" in content_repos
        assert "style_primer" in content_repos
        assert "generated_content" in content_repos
        
        # Verify execution repositories
        execution_repos = repos["execution"]
        assert "llm_cache" in execution_repos
        assert "token_usage" in execution_repos
        
    def test_behavior_configuration_helper(self, mock_pipeline_template_repository, configure_mock_behavior):
        """Test behavior configuration helper."""
        repo = mock_pipeline_template_repository
        test_error = MockRepositoryError("Test error")
        
        # Configure using helper
        configure_mock_behavior(repo, "save", error=test_error, delay=0.1, return_value="test")
        
        # Verify configuration
        assert repo.behavior.error_conditions["save"] == test_error
        assert repo.behavior.call_delays["save"] == 0.1
        assert repo.behavior.return_values["save"] == "test"
        
    def test_mock_assertions_helper(self, mock_pipeline_template_repository, mock_behavior_assertions):
        """Test mock behavior assertions helper."""
        repo = mock_pipeline_template_repository
        assertions = mock_behavior_assertions
        
        # Initially not called
        assertions.assert_not_called(repo, "save")
        
        # Simulate call
        repo._increment_call_count("save")
        assertions.assert_called(repo, "save", 1)
        
        # Log event
        repo._log_event("save", "TestEntity", "test-id")
        assertions.assert_event_logged(repo, "save", "TestEntity")
        
        # Get events
        events = assertions.get_logged_events(repo, "save")
        assert len(events) == 1


class TestMockRepositoryBehavior:
    """Test mock repository specific behavior."""
    
    @pytest.mark.asyncio
    async def test_error_conditions(self, mock_pipeline_template_repository, configure_mock_behavior):
        """Test that configured error conditions are raised."""
        repo = mock_pipeline_template_repository
        test_error = MockRepositoryError("Test error")
        
        # Configure error
        configure_mock_behavior(repo, "save", error=test_error)
        
        # Mock entity for testing
        class MockEntity:
            def __init__(self):
                self.id = PipelineId()
                self.name = PipelineName("test")
                
        entity = MockEntity()
        
        # Verify error is raised
        with pytest.raises(MockRepositoryError, match="Test error"):
            await repo.save(entity)
            
    @pytest.mark.asyncio
    async def test_call_delays(self, mock_pipeline_template_repository, configure_mock_behavior):
        """Test that configured delays are applied."""
        repo = mock_pipeline_template_repository
        delay_seconds = 0.1
        
        # Configure delay
        configure_mock_behavior(repo, "count", delay=delay_seconds)
        
        # Measure execution time
        start_time = datetime.now()
        await repo.count()
        end_time = datetime.now()
        
        # Verify delay was applied (with some tolerance)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time >= delay_seconds * 0.9  # Allow 10% tolerance
        
    @pytest.mark.asyncio
    async def test_return_values(self, mock_pipeline_template_repository, configure_mock_behavior):
        """Test that configured return values are used."""
        repo = mock_pipeline_template_repository
        expected_count = 42
        
        # Configure return value
        configure_mock_behavior(repo, "count", return_value=expected_count)
        
        # Verify return value
        actual_count = await repo.count()
        assert actual_count == expected_count


class TestLLMCacheRepository:
    """Test LLM cache repository specific functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_hit_miss_tracking(self, mock_llm_cache_repository):
        """Test cache hit/miss tracking."""
        repo = mock_llm_cache_repository
        
        cache_key = CacheKey("test-key")
        model_name = ModelName("test-model")
        
        # Initially empty cache - should be miss
        result = await repo.get_cached_response(cache_key)
        assert result is None
        assert repo._cache_misses == 1
        assert repo._cache_hits == 0
        
        # Store response
        await repo.store_response(
            cache_key=cache_key,
            model_name=model_name,
            prompt="test prompt",
            response="test response",
            ttl_seconds=3600
        )
        
        # Should be hit now
        result = await repo.get_cached_response(cache_key)
        assert result is not None
        assert result.response == "test response"
        assert repo._cache_hits == 1
        assert repo._cache_misses == 1
        
    @pytest.mark.asyncio
    async def test_cache_expiration(self, mock_llm_cache_repository):
        """Test cache entry expiration."""
        repo = mock_llm_cache_repository
        
        cache_key = CacheKey("test-key")
        model_name = ModelName("test-model")
        
        # Store with very short TTL
        entry = await repo.store_response(
            cache_key=cache_key,
            model_name=model_name,
            prompt="test prompt",
            response="test response",
            ttl_seconds=1  # 1 second TTL
        )
        
        # Should exist immediately
        assert not entry.is_expired
        result = await repo.get_cached_response(cache_key)
        assert result is not None
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired now
        assert entry.is_expired
        result = await repo.get_cached_response(cache_key)
        assert result is None  # Expired entries should be filtered out


class TestTokenUsageRepository:
    """Test token usage repository specific functionality."""
    
    @pytest.mark.asyncio
    async def test_usage_recording(self, mock_token_usage_repository):
        """Test token usage recording."""
        repo = mock_token_usage_repository
        
        workspace = WorkspaceName("test-workspace")
        model = ModelName("test-model")
        prompt_tokens = TokenCount(100)
        completion_tokens = TokenCount(50)
        
        # Record usage
        record = await repo.record_usage(
            workspace=workspace,
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate=0.01,
            cache_hit=False
        )
        
        # Verify record
        assert record.workspace == workspace
        assert record.model_name == model
        assert record.prompt_tokens == prompt_tokens
        assert record.completion_tokens == completion_tokens
        assert record.total_tokens.value == 150
        assert record.cost_estimate == 0.01
        assert not record.cache_hit
        
        # Verify it was stored
        found_record = await repo.find_by_id(record.usage_id)
        assert found_record is not None
        assert found_record.usage_id == record.usage_id
        
    @pytest.mark.asyncio
    async def test_usage_analytics(self, mock_token_usage_repository):
        """Test usage analytics and summaries."""
        repo = mock_token_usage_repository
        
        workspace = WorkspaceName("test-workspace")
        model = ModelName("test-model")
        
        # Record multiple usage events
        for i in range(5):
            await repo.record_usage(
                workspace=workspace,
                model_name=model,
                prompt_tokens=TokenCount(100),
                completion_tokens=TokenCount(50),
                cost_estimate=0.01,
                cache_hit=i % 2 == 0  # Alternate cache hits
            )
            
        # Get usage summary
        summary = await repo.get_usage_summary(workspace=workspace)
        
        # Verify summary
        assert summary["total_tokens"] == 750  # 5 * 150
        assert summary["prompt_tokens"] == 500  # 5 * 100
        assert summary["completion_tokens"] == 250  # 5 * 50
        assert summary["total_cost"] == 0.05  # 5 * 0.01
        assert summary["requests_count"] == 5
        assert summary["cache_hit_rate"] == 60.0  # 3 hits out of 5
        assert summary["average_tokens_per_request"] == 150.0


# ============================================================================
# Integration Test Example
# ============================================================================

class TestRepositoryIntegration:
    """Test integration between multiple mock repositories."""
    
    @pytest.mark.asyncio
    async def test_workspace_and_pipeline_integration(self, repository_integration_test_setup):
        """Test integration between workspace and pipeline repositories."""
        setup = repository_integration_test_setup
        
        # Create test workspace
        workspace = await setup.create_test_workspace()
        assert workspace.name.value == "test-workspace"
        
        # Verify workspace was stored
        workspace_repo = setup.get_repository("workspace", "workspace")
        found_workspace = await workspace_repo.find_by_name(workspace.name)
        assert found_workspace is not None
        assert found_workspace.name == workspace.name
        
        # Create pipeline template in that workspace
        template = await setup.create_test_pipeline_template()
        assert template.workspace == workspace.name
        
        # Verify template was stored
        template_repo = setup.get_repository("pipeline", "template")
        found_template = await template_repo.find_by_name(template.name)
        assert found_template is not None
        assert found_template.workspace == workspace.name