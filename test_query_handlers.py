"""Test CQRS Query Handlers.

Basic integration tests for query handler implementations.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from src.writeit.application.di_config import DIConfiguration
from src.writeit.application.queries import (
    GetWorkspacesQuery,
    GetTemplatesQuery,
    GetPipelineTemplatesQuery,
    ListPipelineTemplatesQuery,
    GetWorkspaceQuery,
    WorkspaceStatus,
    TemplateScope,
    PipelineStatus,
)
from src.writeit.domains.workspace.value_objects import WorkspaceName
from src.writeit.domains.pipeline.value_objects import PipelineId


async def test_workspace_query_handlers(di_container):
    """Test workspace query handlers."""
    
    # Test GetWorkspacesQuery
    get_workspaces_handler = di_container.get_service("get_workspaces_handler")
    query = GetWorkspacesQuery(
        limit=10,
        offset=0,
        include_stats=True,
        include_config=False
    )
    
    result = await get_workspaces_handler.handle(query)
    
    assert result is not None
    assert result.success is not None
    assert result.workspaces is not None
    assert isinstance(result.workspaces, list)
    
    print(f"✓ GetWorkspacesQuery: Found {len(result.workspaces)} workspaces")


async def test_pipeline_query_handlers(di_container):
    """Test pipeline query handlers."""
    
    # Test ListPipelineTemplatesQuery
    list_templates_handler = di_container.get_service("list_pipeline_templates_handler")
    query = ListPipelineTemplatesQuery(
        scope=TemplateScope.ALL,
        limit=10,
        offset=0
    )
    
    result = await list_templates_handler.handle(query)
    
    assert result is not None
    assert result.success is not None
    assert result.templates is not None
    assert isinstance(result.templates, list)
    
    print(f"✓ ListPipelineTemplatesQuery: Found {len(result.templates)} templates")
    
    # Test GetPipelineTemplateQuery with a non-existent ID
    get_template_handler = di_container.get_service("get_pipeline_template_handler")
    from src.writeit.application.queries.pipeline_queries import GetPipelineTemplateQuery
    get_query = GetPipelineTemplateQuery(
        pipeline_id=PipelineId("non-existent-id"),
        include_steps=True,
        include_inputs=True,
        include_metadata=True
    )
    
    get_result = await get_template_handler.handle(get_query)
    
    assert get_result is not None
    assert get_result.success is False  # Should fail for non-existent ID
    assert get_result.error is not None
    
    print(f"✓ GetPipelineTemplateQuery: Correctly handled non-existent template")


async def test_content_query_handlers(di_container):
    """Test content query handlers."""
    
    # Test GetTemplatesQuery
    get_templates_handler = di_container.get_service("get_templates_handler")
    query = GetTemplatesQuery(
        scope=TemplateScope.ALL,
        limit=10,
        offset=0
    )
    
    result = await get_templates_handler.handle(query)
    
    assert result is not None
    assert result.success is not None
    assert result.templates is not None
    assert isinstance(result.templates, list)
    
    print(f"✓ GetTemplatesQuery: Found {len(result.templates)} templates")


async def test_query_with_time_filters(di_container):
    """Test query handlers with time-based filters."""
    
    # Test with recent time range
    time_start = datetime.now() - timedelta(days=7)
    time_end = datetime.now()
    
    # Test Pipeline Analytics with time filter
    analytics_handler = di_container.get_service("get_pipeline_analytics_handler")
    from src.writeit.application.queries.pipeline_queries import GetPipelineAnalyticsQuery
    
    query = GetPipelineAnalyticsQuery(
        time_range_start=time_start,
        time_range_end=time_end,
        group_by="day"
    )
    
    result = await analytics_handler.handle(query)
    
    assert result is not None
    assert result.success is not None
    assert result.analytics is not None
    
    analytics_data = result.analytics
    assert "total_runs" in analytics_data
    assert "success_rate" in analytics_data
    assert "time_range" in analytics_data
    
    print(f"✓ GetPipelineAnalyticsQuery: {analytics_data['total_runs']} runs in time range")


async def test_query_error_handling(di_container):
    """Test query handler error handling."""
    
    # Test with invalid parameters
    list_handler = di_container.get_service("list_pipeline_templates_handler")
    
    # Test with invalid limit
    query = ListPipelineTemplatesQuery(
        limit=-1,  # Invalid limit
        offset=0
    )
    
    result = await list_handler.handle(query)
    
    # Should handle gracefully
    assert result is not None
    # The handler should either succeed with empty results or fail gracefully
    if not result.success:
        assert result.error is not None
        print(f"✓ Error handling: {result.error}")
    else:
        print("✓ Invalid limit handled gracefully")


async def test_dependency_injection_completeness(di_container):
    """Test that all query handlers are properly registered."""
    
    # Test that we can get all expected query handlers
    expected_handlers = [
        "get_workspaces_handler",
        "get_workspace_handler", 
        "get_active_workspace_handler",
        "get_workspace_config_handler",
        "get_workspace_stats_handler",
        "search_workspaces_handler",
        "validate_workspace_name_handler",
        "check_workspace_exists_handler",
        "get_workspace_health_handler",
        "get_workspace_templates_handler",
        "get_workspace_template_handler",
        "get_pipeline_template_handler",
        "list_pipeline_templates_handler",
        "search_pipeline_templates_handler",
        "get_pipeline_run_handler",
        "list_pipeline_runs_handler",
        "get_pipeline_analytics_handler",
        "get_templates_handler",
        "get_template_handler",
        "get_template_by_name_handler",
        "search_templates_handler",
        "get_generated_content_handler",
        "list_generated_content_handler",
        "search_generated_content_handler",
        "get_style_primers_handler",
        "get_style_primer_handler",
        "get_content_analytics_handler",
        "get_popular_templates_handler",
        "validate_template_handler",
        "check_template_exists_handler",
    ]
    
    missing_handlers = []
    for handler_name in expected_handlers:
        try:
            handler = di_container.get_service(handler_name)
            assert handler is not None, f"Handler {handler_name} is None"
        except Exception as e:
            missing_handlers.append(f"{handler_name}: {e}")
    
    if missing_handlers:
        print(f"Missing handlers: {missing_handlers}")
        assert False, f"Missing {len(missing_handlers)} handlers"
    
    print(f"✓ All {len(expected_handlers)} query handlers are properly registered")


async def run_query_handler_tests():
    """Run all query handler tests."""
    print("🧪 Testing CQRS Query Handlers Implementation...")
    
    try:
        di_container = await DIConfiguration.create_container(
            base_path=Path("/tmp/test_writeit"),
            workspace_name="test"
        )
        
        print("\n📋 Testing Workspace Query Handlers...")
        await test_workspace_query_handlers(di_container)
        
        print("\n📋 Testing Pipeline Query Handlers...")
        await test_pipeline_query_handlers(di_container)
        
        print("\n📋 Testing Content Query Handlers...")
        await test_content_query_handlers(di_container)
        
        print("\n📋 Testing Time-based Filters...")
        await test_query_with_time_filters(di_container)
        
        print("\n📋 Testing Error Handling...")
        await test_query_error_handling(di_container)
        
        print("\n📋 Testing Dependency Injection...")
        await test_dependency_injection_completeness(di_container)
        
        print("\n✅ All query handler tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Query handler tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(run_query_handler_tests())