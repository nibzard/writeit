"""Example of integrating the DI container with WriteIt services.

This file demonstrates how to use the dependency injection container
with WriteIt's domain services and repositories.
"""

import asyncio
from typing import Optional
from pathlib import Path

from .factory import ContainerFactory, workspace_containers
from .resolver import ServiceResolver
from .configuration import DIConfiguration, Environment
from .service_manager import (
    ServiceManager,
    get_service_manager,
    configure_for_environment,
    create_default_container
)

# Import domain services (these would be the actual imports)
# from writeit.domains.pipeline.services import PipelineExecutionService
# from writeit.domains.workspace.services import WorkspaceIsolationService
# from writeit.application.services import PipelineApplicationService


async def example_pipeline_execution(workspace_name: str = "default") -> None:
    """Example of executing a pipeline using DI container."""
    print(f"Executing pipeline in workspace: {workspace_name}")
    
    # Get workspace-specific container
    container = ContainerFactory.create_for_workspace(workspace_name)
    
    # Create resolver for easier service access
    resolver = ServiceResolver(container)
    
    try:
        # Resolve pipeline execution service with all dependencies injected
        # pipeline_service = resolver.resolve(PipelineExecutionService)
        print("Pipeline execution service resolved with all dependencies")
        
        # The service would have all repositories and dependencies injected automatically
        # async for event in pipeline_service.execute_pipeline(
        #     template_id="example-pipeline",
        #     inputs={"topic": "Dependency Injection"}, 
        #     workspace_name=workspace_name
        # ):
        #     print(f"Pipeline event: {event.event_type}")
        
        print("Pipeline execution completed")
        
    except Exception as e:
        print(f"Pipeline execution failed: {e}")


def example_workspace_services(workspace_name: str = "test-workspace") -> None:
    """Example of using workspace services."""
    print(f"Working with workspace services for: {workspace_name}")
    
    # Use the workspace container manager
    container = workspace_containers.get_container(workspace_name)
    resolver = ServiceResolver(container)
    
    try:
        # Resolve workspace isolation service
        # isolation_service = resolver.resolve(WorkspaceIsolationService)
        print("Workspace isolation service resolved")
        
        # Service has all workspace-specific repositories injected
        # workspace_info = isolation_service.get_workspace_info(workspace_name)
        # print(f"Workspace info: {workspace_info}")
        
    except Exception as e:
        print(f"Workspace service error: {e}")


def example_testing_setup() -> None:
    """Example of setting up DI container for testing."""
    print("Setting up testing container")
    
    # Create testing container with mocks
    container = ContainerFactory.create_testing(
        workspace_name="test",
        use_mocks=True
    )
    
    resolver = ServiceResolver(container)
    
    try:
        # All services resolved will use mock implementations
        # pipeline_service = resolver.resolve(PipelineExecutionService)
        # app_service = resolver.resolve(PipelineApplicationService)
        
        print("Testing services resolved with mock implementations")
        
        # Mock services can be configured for predictable test behavior
        # mock_llm_service = resolver.resolve(LLMOrchestrationService)
        # mock_llm_service.set_mock_response("Test response")
        
    except Exception as e:
        print(f"Testing setup error: {e}")


def example_scoped_services() -> None:
    """Example of using scoped services."""
    print("Working with scoped services")
    
    container = ContainerFactory.create_default("scoped-workspace")
    
    # Create scope for scoped services
    with container.create_scope() as scope:
        resolver = ServiceResolver(container)
        
        try:
            # Scoped services will be the same instance within this scope
            # service1 = resolver.resolve(ScopedService)
            # service2 = resolver.resolve(ScopedService)
            # assert service1 is service2  # Same instance within scope
            
            print("Scoped services resolved within scope")
            
        except Exception as e:
            print(f"Scoped service error: {e}")
    
    print("Scope disposed, scoped services cleaned up")


async def example_async_services() -> None:
    """Example of resolving async services."""
    print("Resolving async services")
    
    container = ContainerFactory.create_default("async-workspace")
    resolver = ServiceResolver(container)
    
    try:
        # Async resolution for services with async factories
        # async_service = await resolver.aresolve(AsyncLLMService)
        print("Async service resolved")
        
        # Async services can have async initialization
        # await async_service.initialize()
        # result = await async_service.process_request("test")
        
    except Exception as e:
        print(f"Async service error: {e}")


def example_configuration_based_setup() -> None:
    """Example of using configuration-based service registration."""
    print("Setting up services from configuration")
    
    # Create custom configuration
    config_data = {
        "services": [
            {
                "service_type": "writeit.domains.pipeline.services.PipelineExecutionService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.execution.services.LLMOrchestrationService",
                "factory": "writeit.infrastructure.llm.create_openai_service",
                "lifetime": "singleton"
            }
        ],
        "environment": "development",
        "defaults": {
            "cache_size": 500,
            "timeout_seconds": 60
        }
    }
    
    try:
        config = DIConfiguration.from_dict(config_data)
        container = ContainerFactory.create_from_config(
            "/path/to/config.yaml",  # Would load from actual file
            workspace_name="config-workspace"
        )
        
        resolver = ServiceResolver(container)
        print("Services configured from configuration file")
        
    except Exception as e:
        print(f"Configuration setup error: {e}")


def example_service_manager_usage() -> None:
    """Example of using the new ServiceManager."""
    print("Working with ServiceManager")
    
    try:
        # Get the global service manager (creates default if none exists)
        manager = get_service_manager()
        print(f"Service manager environment: {manager.environment}")
        
        # Create container with default services
        container = manager.create_container(workspace_name="example-workspace")
        print(f"Created container with {len(manager.get_registered_services())} services")
        
        # Diagnose container health
        diagnostics = manager.diagnose_container(container)
        print(f"Container diagnostics:")
        print(f"  - Registered services: {len(diagnostics['registered_services'])}")
        print(f"  - Failed resolutions: {len(diagnostics['failed_resolutions'])}")
        print(f"  - Circular dependencies: {len(diagnostics['circular_dependencies'])}")
        
        # Configure for specific environment
        test_manager = configure_for_environment(Environment.TESTING)
        test_container = test_manager.create_container("test-workspace")
        print(f"Created testing container for environment: {test_manager.environment}")
        
    except Exception as e:
        print(f"Service manager error: {e}")


def example_environment_specific_setup() -> None:
    """Example of environment-specific service configuration."""
    print("Setting up environment-specific services")
    
    try:
        # Development environment
        dev_manager = ServiceManager.for_environment(Environment.DEVELOPMENT)
        dev_container = dev_manager.create_container("dev-workspace")
        print(f"Development container created with {len(dev_manager.get_registered_services())} services")
        
        # Testing environment (could have mock services)
        test_manager = ServiceManager.for_environment(Environment.TESTING) 
        test_container = test_manager.create_container("test-workspace")
        print(f"Testing container created with {len(test_manager.get_registered_services())} services")
        
        # Production environment
        prod_manager = ServiceManager.for_environment(Environment.PRODUCTION)
        prod_container = prod_manager.create_container("prod-workspace")
        print(f"Production container created with {len(prod_manager.get_registered_services())} services")
        
        # Validate configurations
        for name, manager in [("dev", dev_manager), ("test", test_manager), ("prod", prod_manager)]:
            issues = manager.validate_configuration()
            if issues:
                print(f"{name} configuration issues: {issues}")
            else:
                print(f"{name} configuration is valid")
        
    except Exception as e:
        print(f"Environment setup error: {e}")


def example_default_container() -> None:
    """Example of using the convenience function for default container."""
    print("Using default container convenience function")
    
    try:
        # Simple way to get a container with all default services
        container = create_default_container("simple-workspace")
        resolver = ServiceResolver(container)
        
        print("Default container created with all registered services")
        
        # This container has all the WriteIt services automatically registered
        # pipeline_service = resolver.resolve(PipelineExecutionService)
        # workspace_service = resolver.resolve(WorkspaceIsolationService)
        # content_service = resolver.resolve(ContentValidationService)
        
        print("All domain services available for resolution")
        
    except Exception as e:
        print(f"Default container error: {e}")


def example_child_containers() -> None:
    """Example of using child containers for isolation."""
    print("Working with child containers")
    
    # Parent container with shared services
    parent = ContainerFactory.create_default()
    
    # Child containers for different contexts
    request_container = parent.create_child_container()
    batch_container = parent.create_child_container()
    
    # Child containers inherit parent services but can override
    try:
        parent_resolver = ServiceResolver(parent)
        request_resolver = ServiceResolver(request_container)
        batch_resolver = ServiceResolver(batch_container)
        
        # All resolvers can access shared services from parent
        # shared_service = parent_resolver.resolve(SharedService)
        # same_service = request_resolver.resolve(SharedService)
        # assert shared_service is same_service  # Inherited from parent
        
        print("Child containers inherit parent services")
        
    except Exception as e:
        print(f"Child container error: {e}")


def main() -> None:
    """Run all examples."""
    print("WriteIt Dependency Injection Examples")
    print("=====================================")
    
    try:
        # Synchronous examples
        example_workspace_services()
        print()
        
        example_testing_setup()
        print()
        
        example_scoped_services()
        print()
        
        example_configuration_based_setup()
        print()
        
        example_child_containers()
        print()
        
        example_service_manager_usage()
        print()
        
        example_environment_specific_setup()
        print()
        
        example_default_container()
        print()
        
        # Asynchronous examples
        print("Running async examples...")
        asyncio.run(example_pipeline_execution())
        asyncio.run(example_async_services())
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Example execution failed: {e}")


if __name__ == "__main__":
    main()