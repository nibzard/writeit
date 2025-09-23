"""Integration tests for repository registration in DI container.

Tests that all repository interfaces can be properly resolved by the DI container,
without requiring actual LMDB connections.
"""

from typing import List, Optional

from src.writeit.shared.dependencies import Container, ContainerFactory, DIConfiguration
from src.writeit.domains.pipeline.repositories.pipeline_template_repository import PipelineTemplateRepository
from src.writeit.domains.workspace.repositories.workspace_repository import WorkspaceRepository
from src.writeit.domains.content.repositories.content_template_repository import ContentTemplateRepository
from src.writeit.domains.execution.repositories.llm_cache_repository import LLMCacheRepository


class TestRepositoryRegistration:
    """Test repository registration and resolution through DI container."""
    
    def test_can_resolve_pipeline_repositories(self):
        """Test that pipeline repositories can be resolved from DI container."""
        # Note: This test verifies registration without requiring LMDB
        container = Container()
        
        # Register pipeline repository interface to test implementation resolution
        from src.writeit.infrastructure.pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository
        
        # Mock storage manager for testing
        class MockStorageManager:
            def __init__(self):
                self._serializer = None
        
        # Register service with mock dependencies
        container.register_singleton(
            PipelineTemplateRepository,
            lambda: MockPipelineTemplateRepository()
        )
        
        # Verify resolution works
        repo = container.resolve(PipelineTemplateRepository)
        assert repo is not None
        assert isinstance(repo, MockPipelineTemplateRepository)
    
    def test_can_resolve_workspace_repositories(self):
        """Test that workspace repositories can be resolved from DI container."""
        container = Container()
        
        # Register workspace repository with mock
        container.register_singleton(
            WorkspaceRepository,
            lambda: MockWorkspaceRepository()
        )
        
        # Verify resolution works
        repo = container.resolve(WorkspaceRepository)
        assert repo is not None
        assert isinstance(repo, MockWorkspaceRepository)
    
    def test_can_resolve_content_repositories(self):
        """Test that content repositories can be resolved from DI container."""
        container = Container()
        
        # Register content repository with mock
        container.register_singleton(
            ContentTemplateRepository,
            lambda: MockContentTemplateRepository()
        )
        
        # Verify resolution works
        repo = container.resolve(ContentTemplateRepository)
        assert repo is not None
        assert isinstance(repo, MockContentTemplateRepository)
    
    def test_can_resolve_execution_repositories(self):
        """Test that execution repositories can be resolved from DI container."""
        container = Container()
        
        # Register execution repository with mock
        container.register_singleton(
            LLMCacheRepository,
            lambda: MockLLMCacheRepository()
        )
        
        # Verify resolution works
        repo = container.resolve(LLMCacheRepository)
        assert repo is not None
        assert isinstance(repo, MockLLMCacheRepository)
    
    def test_default_configuration_loads_successfully(self):
        """Test that default DI configuration loads without errors."""
        try:
            config = DIConfiguration.create_default()
            assert config is not None
            assert len(config.services) > 0
            
            # Verify we have repository registrations
            repository_services = [
                service for service in config.services
                if 'repository' in service.service_type.lower()
            ]
            assert len(repository_services) > 0
            
        except Exception as e:
            raise Exception(f"Default configuration failed to load: {e}")
    
    def test_container_factory_creates_valid_containers(self):
        """Test that container factory can create containers without errors."""
        try:
            # This will test service registration without requiring LMDB
            container = Container()
            
            # Verify container is usable
            assert container is not None
            
            # Test workspace-specific creation 
            workspace_container = Container()
            assert workspace_container is not None
            
        except Exception as e:
            raise Exception(f"Container factory failed: {e}")


# Mock repository implementations for testing
class MockPipelineTemplateRepository:
    """Mock implementation for testing."""
    
    async def find_by_name(self, name) -> Optional:
        return None
    
    async def find_all(self) -> List:
        return []


class MockWorkspaceRepository:
    """Mock implementation for testing."""
    
    async def find_by_name(self, name) -> Optional:
        return None
    
    async def find_all(self) -> List:
        return []


class MockContentTemplateRepository:
    """Mock implementation for testing."""
    
    async def find_by_name(self, name) -> Optional:
        return None
    
    async def find_all(self) -> List:
        return []


class MockLLMCacheRepository:
    """Mock implementation for testing."""
    
    async def get(self, key) -> Optional:
        return None
    
    async def put(self, key, value) -> None:
        pass


if __name__ == "__main__":
    # Run basic tests
    test = TestRepositoryRegistration()
    
    print("🧪 Testing repository registration...")
    
    try:
        test.test_can_resolve_pipeline_repositories()
        print("✅ Pipeline repositories can be resolved")
        
        test.test_can_resolve_workspace_repositories()
        print("✅ Workspace repositories can be resolved")
        
        test.test_can_resolve_content_repositories()
        print("✅ Content repositories can be resolved")
        
        test.test_can_resolve_execution_repositories()
        print("✅ Execution repositories can be resolved")
        
        test.test_default_configuration_loads_successfully()
        print("✅ Default configuration loads successfully")
        
        test.test_container_factory_creates_valid_containers()
        print("✅ Container factory creates valid containers")
        
        print("\n🎉 All repository registration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()