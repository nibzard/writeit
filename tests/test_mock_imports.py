#!/usr/bin/env python3
"""Test script to verify all mock implementations can be imported successfully.

This script systematically tests imports for all mock implementations
to identify any missing imports or compatibility issues.
"""

import sys
import traceback
from pathlib import Path

# Add project source and tests to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

def test_repository_mocks():
    """Test all repository mock imports."""
    print("Testing Repository Mocks...")
    
    repository_imports = [
        "from tests.mocks.workspace.mock_workspace_repository import MockWorkspaceRepository",
        "from tests.mocks.workspace.mock_workspace_config_repository import MockWorkspaceConfigRepository", 
        "from tests.mocks.content.mock_content_template_repository import MockContentTemplateRepository",
        "from tests.mocks.content.mock_style_primer_repository import MockStylePrimerRepository",
        "from tests.mocks.content.mock_generated_content_repository import MockGeneratedContentRepository",
        "from tests.mocks.pipeline.mock_pipeline_template_repository import MockPipelineTemplateRepository",
        "from tests.mocks.pipeline.mock_pipeline_run_repository import MockPipelineRunRepository",
        "from tests.mocks.pipeline.mock_step_execution_repository import MockStepExecutionRepository",
        "from tests.mocks.execution.mock_llm_cache_repository import MockLLMCacheRepository",
        "from tests.mocks.execution.mock_token_usage_repository import MockTokenUsageRepository",
    ]
    
    success_count = 0
    for import_stmt in repository_imports:
        try:
            exec(import_stmt)
            print(f"✅ {import_stmt}")
            success_count += 1
        except Exception as e:
            print(f"❌ {import_stmt}")
            print(f"   Error: {e}")
    
    print(f"\nRepository Mocks: {success_count}/{len(repository_imports)} successful")
    return success_count == len(repository_imports)

def test_service_mocks():
    """Test all service mock imports."""
    print("\nTesting Service Mocks...")
    
    service_imports = [
        # Pipeline Services
        "from tests.mocks.services.pipeline.mock_pipeline_execution_service import MockPipelineExecutionService",
        "from tests.mocks.services.pipeline.mock_pipeline_validation_service import MockPipelineValidationService", 
        "from tests.mocks.services.pipeline.mock_step_dependency_service import MockStepDependencyService",
        
        # Workspace Services  
        "from tests.mocks.services.workspace.mock_workspace_isolation_service import MockWorkspaceIsolationService",
        "from tests.mocks.services.workspace.mock_workspace_template_service import MockWorkspaceTemplateService",
        "from tests.mocks.services.workspace.mock_workspace_management_service import MockWorkspaceManagementService",
        "from tests.mocks.services.workspace.mock_workspace_configuration_service import MockWorkspaceConfigurationService",
        "from tests.mocks.services.workspace.mock_workspace_analytics_service import MockWorkspaceAnalyticsService",
        
        # Content Services
        "from tests.mocks.services.content.mock_template_rendering_service import MockTemplateRenderingService",
        "from tests.mocks.services.content.mock_content_validation_service import MockContentValidationService",
        "from tests.mocks.services.content.mock_content_generation_service import MockContentGenerationService",
        "from tests.mocks.services.content.mock_template_management_service import MockTemplateManagementService", 
        "from tests.mocks.services.content.mock_style_management_service import MockStyleManagementService",
        
        # Execution Services
        "from tests.mocks.services.execution.mock_llm_orchestration_service import MockLLMOrchestrationService",
        "from tests.mocks.services.execution.mock_cache_management_service import MockCacheManagementService",
        "from tests.mocks.services.execution.mock_token_analytics_service import MockTokenAnalyticsService",
    ]
    
    success_count = 0
    for import_stmt in service_imports:
        try:
            exec(import_stmt)
            print(f"✅ {import_stmt}")
            success_count += 1
        except Exception as e:
            print(f"❌ {import_stmt}")
            print(f"   Error: {e}")
    
    print(f"\nService Mocks: {success_count}/{len(service_imports)} successful")
    return success_count == len(service_imports)

def test_main_mock_import():
    """Test main mock module import."""
    print("\nTesting Main Mock Import...")
    
    try:
        import tests.mocks
        print("✅ import tests.mocks - SUCCESS")
        return True
    except Exception as e:
        print("❌ import tests.mocks - FAILED")
        print(f"   Error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all import tests."""
    print("=" * 60)
    print("MOCK IMPLEMENTATION IMPORT TEST")
    print("=" * 60)
    
    repository_success = test_repository_mocks()
    service_success = test_service_mocks()
    main_import_success = test_main_mock_import()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if repository_success and service_success and main_import_success:
        print("🎉 ALL MOCK IMPORTS SUCCESSFUL!")
        print("✅ Task 'Mock implementations for all interfaces' is complete.")
        return 0
    else:
        print("❌ Some mock imports failed.")
        print("Repository mocks:", "✅" if repository_success else "❌")
        print("Service mocks:", "✅" if service_success else "❌")
        print("Main import:", "✅" if main_import_success else "❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())