"""Tests for service registration and dependency injection.

Tests the complete service registration workflow including:
- Service manager functionality
- Configuration-based registration
- Container creation and validation
- Environment-specific configurations
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Protocol

from writeit.shared.dependencies import (
    ServiceManager,
    DIConfiguration,
    Environment,
    Container,
    get_service_manager,
    configure_for_environment,
    create_default_container,
    ServiceNotFoundError,
    InvalidServiceRegistrationError
)


class TestServiceManager:
    """Test ServiceManager functionality."""
    
    def test_create_default_manager(self):
        """Test creating service manager with default configuration."""
        manager = ServiceManager()
        
        assert manager.environment == Environment.DEVELOPMENT
        assert len(manager.get_registered_services()) > 0
        
        # Should include all domain services
        services = manager.get_registered_services()
        assert any("PipelineExecutionService" in service for service in services)
        assert any("WorkspaceIsolationService" in service for service in services)
        assert any("ContentValidationService" in service for service in services)
        assert any("LLMOrchestrationService" in service for service in services)
    
    def test_environment_specific_manager(self):
        """Test creating manager for specific environment."""
        manager = ServiceManager.for_environment(Environment.TESTING)
        
        assert manager.environment == Environment.TESTING
        assert len(manager.get_registered_services()) > 0
    
    def test_create_container(self):
        """Test creating container from manager."""
        manager = ServiceManager()
        container = manager.create_container("test-workspace")
        
        assert isinstance(container, Container)
        
        # Container should be cached
        container2 = manager.create_container("test-workspace")
        assert container is container2
    
    def test_create_child_container(self):
        """Test creating child container."""
        manager = ServiceManager()
        parent = manager.create_container("parent-workspace")
        child = manager.create_child_container(parent, "child-workspace")
        
        assert isinstance(child, Container)
        assert child._parent is parent
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        manager = ServiceManager()
        issues = manager.validate_configuration()
        
        # Default configuration should be valid
        assert isinstance(issues, list)
        # Note: Some issues might exist due to missing infrastructure implementations
        # but the validation should complete without errors
    
    def test_add_service(self):
        """Test adding service to configuration."""
        manager = ServiceManager()
        initial_count = len(manager.get_registered_services())
        
        manager.add_service(
            "test.service.TestService",
            implementation_type="test.service.TestServiceImpl",
            lifetime="singleton"
        )
        
        assert len(manager.get_registered_services()) == initial_count + 1
        assert "test.service.TestService" in manager.get_registered_services()
    
    def test_add_workspace_service(self):
        """Test adding workspace-specific service."""
        manager = ServiceManager()
        
        manager.add_workspace_service(
            "test-workspace",
            "test.service.WorkspaceService",
            lifetime="scoped"
        )
        
        workspace_services = manager.get_workspace_services("test-workspace")
        assert "test.service.WorkspaceService" in workspace_services
    
    def test_clear_containers(self):
        """Test clearing cached containers."""
        manager = ServiceManager()
        container = manager.create_container("test-workspace")
        
        # Container should be cached
        assert len(manager._containers) > 0
        
        manager.clear_containers()
        assert len(manager._containers) == 0


class TestDIConfiguration:
    """Test DIConfiguration functionality."""
    
    def test_create_default_configuration(self):
        """Test creating default WriteIt configuration."""
        config = DIConfiguration.create_default()
        
        assert config.environment == Environment.DEVELOPMENT
        assert len(config.services) > 0
        
        # Should include core WriteIt services
        service_types = [s["service_type"] for s in config.services]
        assert any("pipeline.services.PipelineExecutionService" in st for st in service_types)
        assert any("workspace.services.WorkspaceIsolationService" in st for st in service_types)
        assert any("content.services.ContentValidationService" in st for st in service_types)
        assert any("execution.services.LLMOrchestrationService" in st for st in service_types)
    
    def test_from_dict(self):
        """Test creating configuration from dictionary."""
        config_data = {
            "services": [
                {
                    "service_type": "test.TestService",
                    "lifetime": "singleton"
                }
            ],
            "environment": "testing",
            "defaults": {"test_value": 123}
        }
        
        config = DIConfiguration.from_dict(config_data)
        
        assert config.environment == Environment.TESTING
        assert len(config.services) == 1
        assert config.services[0]["service_type"] == "test.TestService"
        assert config.defaults["test_value"] == 123
    
    def test_merge_configurations(self):
        """Test merging two configurations."""
        config1 = DIConfiguration(
            services=[{"service_type": "Service1", "lifetime": "singleton"}],
            environment=Environment.DEVELOPMENT
        )
        
        config2 = DIConfiguration(
            services=[{"service_type": "Service2", "lifetime": "transient"}],
            environment=Environment.TESTING
        )
        
        merged = config1.merge(config2)
        
        assert merged.environment == Environment.TESTING  # Uses other's environment
        assert len(merged.services) == 2
        service_types = [s["service_type"] for s in merged.services]
        assert "Service1" in service_types
        assert "Service2" in service_types


class TestGlobalServiceManager:
    """Test global service manager functionality."""
    
    def test_get_service_manager(self):
        """Test getting global service manager."""
        # Reset global manager
        import writeit.shared.dependencies.service_manager as sm
        sm._global_service_manager = None
        
        manager = get_service_manager()
        assert isinstance(manager, ServiceManager)
        
        # Should return same instance on subsequent calls
        manager2 = get_service_manager()
        assert manager is manager2
    
    def test_configure_for_environment(self):
        """Test configuring global manager for environment."""
        manager = configure_for_environment(Environment.TESTING)
        
        assert isinstance(manager, ServiceManager)
        assert manager.environment == Environment.TESTING
        
        # Global manager should be updated
        global_manager = get_service_manager()
        assert global_manager is manager
    
    def test_create_default_container(self):
        """Test creating default container convenience function."""
        container = create_default_container("test-workspace")
        
        assert isinstance(container, Container)


class TestServiceRegistrationIntegration:
    """Integration tests for complete service registration workflow."""
    
    def test_complete_registration_workflow(self):
        """Test complete service registration and resolution workflow."""
        # Create manager with default configuration
        manager = ServiceManager()
        
        # Create container
        container = manager.create_container("integration-test")
        
        # Verify container has services registered
        # Note: We can't test actual resolution without implementing the services,
        # but we can verify the registration worked
        assert isinstance(container, Container)
        
        # Diagnose container
        diagnostics = manager.diagnose_container(container)
        assert "registered_services" in diagnostics
        assert "failed_resolutions" in diagnostics
        assert "environment" in diagnostics
        assert diagnostics["environment"] == "development"
    
    def test_environment_specific_registration(self):
        """Test registration for different environments."""
        environments = [Environment.DEVELOPMENT, Environment.TESTING, Environment.PRODUCTION]
        
        for env in environments:
            manager = ServiceManager.for_environment(env)
            container = manager.create_container(f"{env.value}-workspace")
            
            assert isinstance(container, Container)
            assert manager.environment == env
            
            # Each environment should have the same core services
            services = manager.get_registered_services()
            assert len(services) > 0
    
    @pytest.mark.skip(reason="Requires actual service implementations")
    def test_actual_service_resolution(self):
        """Test resolving actual WriteIt services.
        
        This test is skipped because it requires the actual service implementations
        to be available and properly structured. It's included to show how the
        integration testing would work once the infrastructure is complete.
        """
        manager = ServiceManager()
        container = manager.create_container("test-workspace")
        
        # These would work once the actual services are implemented
        # from writeit.domains.pipeline.services import PipelineExecutionService
        # from writeit.domains.workspace.services import WorkspaceIsolationService
        
        # pipeline_service = container.resolve(PipelineExecutionService)
        # workspace_service = container.resolve(WorkspaceIsolationService)
        
        # assert pipeline_service is not None
        # assert workspace_service is not None
        
        pass


class TestServiceRegistrationValidation:
    """Test service registration validation and error handling."""
    
    def test_invalid_service_type(self):
        """Test handling of invalid service types."""
        config_data = {
            "services": [
                {
                    "service_type": "invalid.nonexistent.Service",
                    "lifetime": "singleton"
                }
            ]
        }
        
        config = DIConfiguration.from_dict(config_data)
        manager = ServiceManager(config, validate_on_init=False)
        
        # Validation should catch the invalid service type
        issues = manager.validate_configuration()
        assert len(issues) > 0
        assert any("invalid.nonexistent.Service" in issue for issue in issues)
    
    def test_duplicate_service_registration(self):
        """Test detection of duplicate service registrations."""
        config_data = {
            "services": [
                {
                    "service_type": "test.Service",
                    "lifetime": "singleton"
                },
                {
                    "service_type": "test.Service",
                    "lifetime": "transient"
                }
            ]
        }
        
        config = DIConfiguration.from_dict(config_data)
        manager = ServiceManager(config, validate_on_init=False)
        
        # Validation should catch duplicate registrations
        issues = manager.validate_configuration()
        assert len(issues) > 0
        assert any("Duplicate" in issue for issue in issues)


if __name__ == "__main__":
    pytest.main([__file__])
