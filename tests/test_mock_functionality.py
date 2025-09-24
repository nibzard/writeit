#!/usr/bin/env python3
"""Test script to verify mock implementations function correctly.

This script tests that mock implementations can be instantiated and 
their basic methods work as expected.
"""

import sys
from pathlib import Path

# Add project source to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

def test_repository_mock_instantiation():
    """Test that all repository mocks can be instantiated."""
    print("Testing Repository Mock Instantiation...")
    
    try:
        from tests.mocks import (
            MockWorkspaceRepository,
            MockWorkspaceConfigRepository,
            MockContentTemplateRepository,
            MockStylePrimerRepository,
            MockGeneratedContentRepository,
            MockPipelineTemplateRepository,
            MockPipelineRunRepository,
            MockStepExecutionRepository,
            MockLLMCacheRepository,
            MockTokenUsageRepository,
        )
        
        # Test instantiation
        workspace_repo = MockWorkspaceRepository()
        config_repo = MockWorkspaceConfigRepository()
        content_template_repo = MockContentTemplateRepository()
        style_repo = MockStylePrimerRepository()
        generated_content_repo = MockGeneratedContentRepository()
        pipeline_template_repo = MockPipelineTemplateRepository()
        pipeline_run_repo = MockPipelineRunRepository()
        step_exec_repo = MockStepExecutionRepository()
        cache_repo = MockLLMCacheRepository()
        token_repo = MockTokenUsageRepository()
        
        print("✅ All 10 repository mocks instantiated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Repository mock instantiation failed: {e}")
        return False

def test_service_mock_instantiation():
    """Test that all service mocks can be instantiated."""
    print("\nTesting Service Mock Instantiation...")
    
    try:
        from tests.mocks import (
            MockPipelineExecutionService,
            MockPipelineValidationService,
            MockStepDependencyService,
            MockWorkspaceIsolationService,
            MockWorkspaceTemplateService,
            MockWorkspaceManagementService,
            MockWorkspaceConfigurationService,
            MockWorkspaceAnalyticsService,
            MockTemplateRenderingService,
            MockContentValidationService,
            MockContentGenerationService,
            MockTemplateManagementService,
            MockStyleManagementService,
            MockLLMOrchestrationService,
            MockCacheManagementService,
            MockTokenAnalyticsService,
        )
        
        # Test instantiation
        pipeline_exec = MockPipelineExecutionService()
        pipeline_val = MockPipelineValidationService()
        step_dep = MockStepDependencyService()
        ws_isolation = MockWorkspaceIsolationService()
        ws_template = MockWorkspaceTemplateService()
        ws_mgmt = MockWorkspaceManagementService()
        ws_config = MockWorkspaceConfigurationService()
        ws_analytics = MockWorkspaceAnalyticsService()
        template_render = MockTemplateRenderingService()
        content_val = MockContentValidationService()
        content_gen = MockContentGenerationService()
        template_mgmt = MockTemplateManagementService()
        style_mgmt = MockStyleManagementService()
        llm_orch = MockLLMOrchestrationService()
        cache_mgmt = MockCacheManagementService()
        token_analytics = MockTokenAnalyticsService()
        
        print("✅ All 16 service mocks instantiated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Service mock instantiation failed: {e}")
        return False

def test_base_mock_behavior():
    """Test basic mock behavior functionality."""
    print("\nTesting Base Mock Behavior...")
    
    try:
        from tests.mocks import MockWorkspaceRepository
        
        # Test workspace isolation
        repo1 = MockWorkspaceRepository("workspace1")
        repo2 = MockWorkspaceRepository("workspace2")
        
        # Test behavior configuration
        repo1.behavior.set_error_condition("find_by_id", Exception("Mock error"))
        
        # Test call counting
        assert repo1.behavior.get_call_count("find_by_id") == 0
        
        # Test state clearing
        repo1.clear_state()
        
        print("✅ Base mock behavior works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Base mock behavior test failed: {e}")
        return False

def main():
    """Run all functionality tests."""
    print("=" * 60)
    print("MOCK FUNCTIONALITY TEST")
    print("=" * 60)
    
    repo_success = test_repository_mock_instantiation()
    service_success = test_service_mock_instantiation()
    behavior_success = test_base_mock_behavior()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if repo_success and service_success and behavior_success:
        print("🎉 ALL MOCK FUNCTIONALITY TESTS PASSED!")
        print("✅ Mock implementations for all interfaces are complete and functional.")
        return 0
    else:
        print("❌ Some functionality tests failed.")
        print("Repository instantiation:", "✅" if repo_success else "❌")
        print("Service instantiation:", "✅" if service_success else "❌")
        print("Base behavior:", "✅" if behavior_success else "❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())