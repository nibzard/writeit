"""Pytest fixtures for mock domain service implementations.

Provides easy-to-use fixtures for all domain service mocks with proper
dependency injection support and configurable behavior.
"""

import pytest
from typing import Dict, Any

# Import all mock service implementations
from ..mocks.services import (
    MockPipelineValidationService,
    MockPipelineExecutionService,
    MockStepDependencyService,
    MockWorkspaceIsolationService,
    MockWorkspaceTemplateService,
    MockTemplateRenderingService,
    MockContentValidationService,
    MockLLMOrchestrationService,
    MockCacheManagementService,
    MockTokenAnalyticsService,
)


# ============================================================================
# Pipeline Domain Mock Services
# ============================================================================

@pytest.fixture
def mock_pipeline_validation_service() -> MockPipelineValidationService:
    """Provide mock pipeline validation service."""
    return MockPipelineValidationService()


@pytest.fixture
def mock_pipeline_execution_service() -> MockPipelineExecutionService:
    """Provide mock pipeline execution service."""
    return MockPipelineExecutionService()


@pytest.fixture
def mock_step_dependency_service() -> MockStepDependencyService:
    """Provide mock step dependency service."""
    return MockStepDependencyService()


# ============================================================================
# Workspace Domain Mock Services
# ============================================================================

@pytest.fixture
def mock_workspace_isolation_service() -> MockWorkspaceIsolationService:
    """Provide mock workspace isolation service."""
    return MockWorkspaceIsolationService()


@pytest.fixture
def mock_workspace_template_service() -> MockWorkspaceTemplateService:
    """Provide mock workspace template service."""
    return MockWorkspaceTemplateService()


# ============================================================================
# Content Domain Mock Services
# ============================================================================

@pytest.fixture
def mock_template_rendering_service() -> MockTemplateRenderingService:
    """Provide mock template rendering service."""
    return MockTemplateRenderingService()


@pytest.fixture
def mock_content_validation_service() -> MockContentValidationService:
    """Provide mock content validation service."""
    return MockContentValidationService()


# ============================================================================
# Execution Domain Mock Services
# ============================================================================

@pytest.fixture
def mock_llm_orchestration_service() -> MockLLMOrchestrationService:
    """Provide mock LLM orchestration service."""
    return MockLLMOrchestrationService()


@pytest.fixture
def mock_cache_management_service() -> MockCacheManagementService:
    """Provide mock cache management service."""
    return MockCacheManagementService()


@pytest.fixture
def mock_token_analytics_service() -> MockTokenAnalyticsService:
    """Provide mock token analytics service."""
    return MockTokenAnalyticsService()


# ============================================================================
# Service Collections
# ============================================================================

@pytest.fixture
def mock_pipeline_services(
    mock_pipeline_validation_service: MockPipelineValidationService,
    mock_pipeline_execution_service: MockPipelineExecutionService,
    mock_step_dependency_service: MockStepDependencyService
) -> Dict[str, Any]:
    """Provide collection of all pipeline domain mock services."""
    return {
        "validation": mock_pipeline_validation_service,
        "execution": mock_pipeline_execution_service,
        "dependency": mock_step_dependency_service
    }


@pytest.fixture
def mock_workspace_services(
    mock_workspace_isolation_service: MockWorkspaceIsolationService,
    mock_workspace_template_service: MockWorkspaceTemplateService
) -> Dict[str, Any]:
    """Provide collection of all workspace domain mock services."""
    return {
        "isolation": mock_workspace_isolation_service,
        "template": mock_workspace_template_service
    }


@pytest.fixture
def mock_content_services(
    mock_template_rendering_service: MockTemplateRenderingService,
    mock_content_validation_service: MockContentValidationService
) -> Dict[str, Any]:
    """Provide collection of all content domain mock services."""
    return {
        "rendering": mock_template_rendering_service,
        "validation": mock_content_validation_service
    }


@pytest.fixture
def mock_execution_services(
    mock_llm_orchestration_service: MockLLMOrchestrationService,
    mock_cache_management_service: MockCacheManagementService,
    mock_token_analytics_service: MockTokenAnalyticsService
) -> Dict[str, Any]:
    """Provide collection of all execution domain mock services."""
    return {
        "orchestration": mock_llm_orchestration_service,
        "cache": mock_cache_management_service,
        "analytics": mock_token_analytics_service
    }


@pytest.fixture
def all_mock_services(
    mock_pipeline_services: Dict[str, Any],
    mock_workspace_services: Dict[str, Any],
    mock_content_services: Dict[str, Any],
    mock_execution_services: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Provide collection of ALL mock services organized by domain."""
    return {
        "pipeline": mock_pipeline_services,
        "workspace": mock_workspace_services,
        "content": mock_content_services,
        "execution": mock_execution_services
    }


# ============================================================================
# Service Configuration Helpers
# ============================================================================

@pytest.fixture
def configure_mock_service_behavior():
    """Provide helper function to configure mock service behavior."""
    
    def _configure(service, method_name: str, **kwargs):
        """Configure mock service behavior.
        
        Args:
            service: Mock service instance
            method_name: Method to configure
            **kwargs: Configuration options:
                - should_fail: Boolean to make service fail
                - return_value: Fixed return value
                - delay: Delay in seconds (for execution service)
        """
        if hasattr(service, 'configure_failure') and 'should_fail' in kwargs:
            service.configure_failure(kwargs['should_fail'])
            
        if hasattr(service, 'configure_delay') and 'delay' in kwargs:
            service.configure_delay(kwargs['delay'])
            
        # Method-specific configuration based on service type
        if 'return_value' in kwargs:
            if hasattr(service, f'configure_{method_name}_result'):
                getattr(service, f'configure_{method_name}_result')(kwargs['return_value'])
                
    return _configure


@pytest.fixture
def clear_mock_service_state():
    """Provide helper function to clear mock service state."""
    
    def _clear(*services):
        """Clear state of one or more mock services."""
        for service in services:
            if hasattr(service, 'clear_configuration'):
                service.clear_configuration()
                
    return _clear


@pytest.fixture
def mock_service_assertions():
    """Provide helper functions for asserting mock service behavior."""
    
    class MockServiceAssertions:
        @staticmethod
        def assert_service_called(service, method_name: str, expected_count: int = 1):
            """Assert that service method was called expected number of times."""
            if hasattr(service, 'mock'):
                mock_obj = service.mock
                actual_calls = getattr(mock_obj, method_name).call_count
                assert actual_calls == expected_count, (
                    f"Expected {method_name} to be called {expected_count} times, "
                    f"but was called {actual_calls} times"
                )
            
        @staticmethod
        def assert_service_not_called(service, method_name: str):
            """Assert that service method was not called."""
            MockServiceAssertions.assert_service_called(service, method_name, 0)
            
        @staticmethod
        def assert_service_called_with(service, method_name: str, *args, **kwargs):
            """Assert that service method was called with specific arguments."""
            if hasattr(service, 'mock'):
                mock_obj = service.mock
                getattr(mock_obj, method_name).assert_called_with(*args, **kwargs)
                
        @staticmethod
        def get_service_call_args(service, method_name: str, call_index: int = 0):
            """Get arguments from specific service call."""
            if hasattr(service, 'mock'):
                mock_obj = service.mock
                calls = getattr(mock_obj, method_name).call_args_list
                if call_index < len(calls):
                    return calls[call_index]
            return None
            
    return MockServiceAssertions()


# ============================================================================
# Pre-configured Mock Scenarios
# ============================================================================

@pytest.fixture
def failing_services_scenario(all_mock_services, configure_mock_service_behavior):
    """Configure all services to simulate failure conditions."""
    for domain_services in all_mock_services.values():
        for service in domain_services.values():
            configure_mock_service_behavior(service, "default", should_fail=True)
            
    return all_mock_services


@pytest.fixture
def slow_services_scenario(all_mock_services, configure_mock_service_behavior):
    """Configure services to simulate slow response times."""
    for domain_services in all_mock_services.values():
        for service in domain_services.values():
            if hasattr(service, 'configure_delay'):
                configure_mock_service_behavior(service, "default", delay=0.1)
                
    return all_mock_services


@pytest.fixture
def realistic_services_scenario(all_mock_services):
    """Configure services with realistic behavior for integration testing."""
    # Pipeline services with realistic validation and execution
    pipeline_services = all_mock_services["pipeline"]
    
    # Configure realistic validation results
    validation_service = pipeline_services["validation"]
    validation_service.configure_failure(False)  # Most validations pass
    
    # Configure realistic execution behavior
    execution_service = pipeline_services["execution"]
    execution_service.configure_failure(False)
    execution_service.configure_delay(0.05)  # Realistic execution delay
    
    # Configure other services for realistic behavior
    content_services = all_mock_services["content"]
    content_services["rendering"].configure_failure(False)
    content_services["validation"].configure_failure(False)
    
    execution_services = all_mock_services["execution"]
    execution_services["orchestration"].configure_failure(False)
    execution_services["cache"].configure_cache_hit_rate(0.8)  # 80% cache hit rate
    execution_services["analytics"].configure_failure(False)
    
    return all_mock_services


# ============================================================================
# Integration Test Helpers
# ============================================================================

@pytest.fixture
def service_integration_test_setup(all_mock_services):
    """Setup for integration tests requiring multiple services."""
    
    class ServiceIntegrationTestSetup:
        def __init__(self, services):
            self.services = services
            
        def get_service(self, domain: str, service_type: str):
            """Get specific service by domain and type."""
            return self.services[domain][service_type]
            
        def configure_cross_service_scenario(self, scenario_name: str):
            """Configure services for specific cross-service scenarios."""
            if scenario_name == "pipeline_execution_success":
                # Configure services for successful pipeline execution
                self.get_service("pipeline", "validation").configure_failure(False)
                self.get_service("pipeline", "execution").configure_failure(False)
                self.get_service("content", "rendering").configure_failure(False)
                self.get_service("execution", "orchestration").configure_failure(False)
                
            elif scenario_name == "validation_failure":
                # Configure validation to fail
                self.get_service("pipeline", "validation").configure_failure(True)
                
            elif scenario_name == "execution_failure":
                # Configure execution to fail after validation succeeds
                self.get_service("pipeline", "validation").configure_failure(False)
                self.get_service("pipeline", "execution").configure_failure(True)
                
    return ServiceIntegrationTestSetup(all_mock_services)
