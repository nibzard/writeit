"""Integration tests for repository implementations with real LMDB storage.

Tests repository implementations against real LMDB databases to ensure
proper persistence, transaction behavior, workspace isolation, and
concurrency safety.
"""

import asyncio
import lmdb
import pytest
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional
from uuid import uuid4, UUID

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.base.storage_manager import LMDBStorageManager
from writeit.infrastructure.base.serialization import DomainEntitySerializer
from writeit.infrastructure.pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository

from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration

from writeit.shared.repository import RepositoryError, EntityNotFoundError


class TestLMDBRepositoryIntegration:
    """Integration tests for LMDB repository implementations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary directory for LMDB testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def storage_manager(self, temp_db_path):
        """Create storage manager with temporary database."""
        # Mock workspace manager for testing
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path

            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        workspace_manager = MockWorkspaceManager(temp_db_path)
        return LMDBStorageManager(
            workspace_manager=workspace_manager,
            workspace_name="test",
            map_size_mb=50,  # Small for testing
            max_dbs=10
        )

    @pytest.fixture
    def test_workspace_name(self):
        """Standard test workspace name."""
        return WorkspaceName("test_workspace")

    @pytest.fixture
    def pipeline_repository(self, storage_manager, test_workspace_name):
        """Create pipeline template repository."""
        return LMDBPipelineTemplateRepository(storage_manager, test_workspace_name)


    @pytest.fixture
    def sample_pipeline_template(self):
        """Create sample pipeline template for testing."""
        return PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="Test Pipeline",
            description="Test pipeline description",
            version="1.0.0",
            inputs={
                "topic": PipelineInput(
                    key="topic",
                    type="text",
                    label="Topic",
                    required=True,
                    placeholder="Enter topic..."
                )
            },
            steps={
                "outline": PipelineStepTemplate(
                    id=StepId("outline"),
                    name="Create Outline",
                    description="Generate outline",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Create outline for {{ inputs.topic }}"),
                    model_preference=ModelPreference(["gpt-4"])
                )
            },
            tags=["test", "sample"],
            author="test_author"
        )

    @pytest.fixture
    def sample_workspace(self):
        """Create sample workspace for testing."""
        return Workspace(
            name=WorkspaceName("integration_test"),
            root_path=WorkspacePath("/tmp/test_workspace"),
            configuration=WorkspaceConfiguration.default(),
            is_active=True
        )

    async def test_pipeline_repository_persistence(self, pipeline_repository, sample_pipeline_template):
        """Test basic CRUD operations with real LMDB persistence."""
        # Test save
        await pipeline_repository.save(sample_pipeline_template)
        
        # Test exists
        assert await pipeline_repository.exists(sample_pipeline_template.id)
        
        # Test find_by_id
        loaded_template = await pipeline_repository.find_by_id(sample_pipeline_template.id)
        assert loaded_template is not None
        assert loaded_template.id == sample_pipeline_template.id
        assert loaded_template.name == sample_pipeline_template.name
        assert loaded_template.description == sample_pipeline_template.description
        assert loaded_template.version == sample_pipeline_template.version
        
        # Test find_all
        all_templates = await pipeline_repository.find_all()
        assert len(all_templates) == 1
        assert all_templates[0].id == sample_pipeline_template.id
        
        # Test update
        sample_pipeline_template.description = "Updated description"
        await pipeline_repository.save(sample_pipeline_template)
        
        updated_template = await pipeline_repository.find_by_id(sample_pipeline_template.id)
        assert updated_template.description == "Updated description"
        
        # Test delete
        await pipeline_repository.delete(sample_pipeline_template)
        assert not await pipeline_repository.exists(sample_pipeline_template.id)
        assert await pipeline_repository.find_by_id(sample_pipeline_template.id) is None

    async def test_workspace_isolation(self, temp_db_path):
        """Test that different workspaces have isolated data."""
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        workspace_manager = MockWorkspaceManager(temp_db_path)

        # Create repositories for different workspaces
        workspace1 = WorkspaceName("workspace1")
        workspace2 = WorkspaceName("workspace2")
        
        storage1 = LMDBStorageManager(workspace_manager, "workspace1", map_size_mb=50)
        storage2 = LMDBStorageManager(workspace_manager, "workspace2", map_size_mb=50)
        
        repo1 = LMDBPipelineTemplateRepository(storage1, workspace1)
        repo2 = LMDBPipelineTemplateRepository(storage2, workspace2)
        
        # Create different templates for each workspace
        template1 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("workspace1_template"),
            description="Template for workspace 1",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["workspace1"],
            author="author1"
        )
        
        template2 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("workspace2_template"),
            description="Template for workspace 2",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["workspace2"],
            author="author2"
        )
        
        # Save templates to respective workspaces
        await repo1.save(template1)
        await repo2.save(template2)
        
        # Verify isolation - each workspace should only see its own data
        workspace1_templates = await repo1.find_all()
        workspace2_templates = await repo2.find_all()
        
        assert len(workspace1_templates) == 1
        assert len(workspace2_templates) == 1
        assert workspace1_templates[0].name.value == "workspace1_template"
        assert workspace2_templates[0].name.value == "workspace2_template"
        
        # Cross-workspace lookup should return None
        assert await repo1.find_by_id(template2.id) is None
        assert await repo2.find_by_id(template1.id) is None

    async def test_transaction_behavior(self, pipeline_repository, sample_pipeline_template):
        """Test ACID transaction properties."""
        # Test successful transaction
        await pipeline_repository.save(sample_pipeline_template)
        assert await pipeline_repository.exists(sample_pipeline_template.id)
        
        # Test transaction rollback on error
        # This is tricky to test directly, but we can test that corrupted data doesn't get saved
        original_serializer = pipeline_repository._storage._serializer
        
        class FailingSerializer:
            def serialize(self, obj):
                raise Exception("Serialization failed")
            
            def deserialize(self, data, entity_type):
                return original_serializer.deserialize(data, entity_type)
        
        # Temporarily replace serializer
        pipeline_repository._storage._serializer = FailingSerializer()
        
        # Create new template that should fail to save
        failing_template = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("failing_template"),
            description="This should fail",
            version="1.0.0",
            inputs={},
            steps={},
            tags=[],
            author="test"
        )
        
        # Attempt to save should fail
        with pytest.raises(RepositoryError):
            await pipeline_repository.save(failing_template)
        
        # Template should not exist in database
        assert not await pipeline_repository.exists(failing_template.id)
        
        # Restore original serializer
        pipeline_repository._storage._serializer = original_serializer

    async def test_concurrent_access(self, temp_db_path):
        """Test concurrent access patterns and thread safety."""
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        workspace_manager = MockWorkspaceManager(temp_db_path)
        workspace_name = WorkspaceName("concurrent_test")
        
        # Create multiple storage managers and repositories
        # Each thread gets its own storage manager to simulate real concurrency
        def create_repository():
            storage = LMDBStorageManager(workspace_manager, "concurrent_test", map_size_mb=50)
            return LMDBPipelineTemplateRepository(storage, workspace_name)
        
        # Function to save templates concurrently
        async def save_templates(repo_factory, start_id: int, count: int):
            repo = repo_factory()
            tasks = []
            for i in range(count):
                template = PipelineTemplate(
                    id=PipelineId(str(uuid4())),
                    name=PipelineName(f"concurrent_template_{start_id + i}"),
                    description=f"Template {start_id + i}",
                    version="1.0.0",
                    inputs={},
                    steps={},
                    tags=[f"batch_{start_id // 10}"],
                    author=f"author_{start_id + i}"
                )
                tasks.append(repo.save(template))
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run concurrent saves
        tasks = []
        batch_size = 10
        num_batches = 5
        
        for batch in range(num_batches):
            start_id = batch * batch_size
            task = save_templates(create_repository, start_id, batch_size)
            tasks.append(task)
        
        # Execute all batches concurrently
        await asyncio.gather(*tasks)
        
        # Verify all templates were saved
        verification_repo = create_repository()
        all_templates = await verification_repo.find_all()
        
        expected_count = batch_size * num_batches
        assert len(all_templates) == expected_count
        
        # Verify no data corruption
        names = {t.name.value for t in all_templates}
        assert len(names) == expected_count  # No duplicates
        
        # Verify all expected templates exist
        for batch in range(num_batches):
            for i in range(batch_size):
                expected_name = f"concurrent_template_{batch * batch_size + i}"
                assert expected_name in names

    async def test_specification_queries(self, pipeline_repository, test_workspace_name):
        """Test specification-based queries with real data."""
        # Create multiple test templates
        templates = []
        for i in range(5):
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=PipelineName(f"spec_test_template_{i}"),
                description=f"Template for specification testing {i}",
                version=f"1.{i}.0",
                inputs={},
                steps={},
                tags=["spec_test"] + ([f"tag_{i}"] if i % 2 == 0 else []),
                author="spec_test_author"
            )
            templates.append(template)
            await pipeline_repository.save(template)
        
        # Test find by name
        found_template = await pipeline_repository.find_by_name(PipelineName("spec_test_template_2"))
        assert found_template is not None
        assert found_template.name.value == "spec_test_template_2"
        
        # Test search by tag
        tagged_templates = await pipeline_repository.search_by_tag("tag_2")
        assert len(tagged_templates) == 1
        assert tagged_templates[0].name.value == "spec_test_template_2"
        
        # Test search by description
        desc_templates = await pipeline_repository.search_by_description("specification testing")
        assert len(desc_templates) == 5  # All templates match
        
        # Test find by author
        author_templates = await pipeline_repository.find_templates_by_author("spec_test_author")
        assert len(author_templates) == 5  # All templates match
        
        # Test latest version
        latest = await pipeline_repository.find_latest_version(PipelineName("spec_test_template_3"))
        assert latest is not None
        assert latest.version == "1.3.0"

    async def test_error_handling(self, pipeline_repository):
        """Test proper error handling and recovery."""
        # Test EntityNotFoundError
        non_existent_id = PipelineId(str(uuid4()))
        result = await pipeline_repository.find_by_id(non_existent_id)
        assert result is None
        
        # Test deleting non-existent entity
        success = await pipeline_repository.delete_by_id(non_existent_id)
        assert not success
        
        # Test invalid data handling
        class InvalidTemplate:
            def __init__(self):
                self.id = "not_a_proper_id"
        
        invalid = InvalidTemplate()
        
        # Should handle gracefully without crashing
        with pytest.raises(Exception):  # Could be RepositoryError or serialization error
            await pipeline_repository.save(invalid)


    async def test_batch_operations(self, pipeline_repository):
        """Test batch save and delete operations."""
        # Create multiple templates
        templates = []
        for i in range(10):
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=PipelineName(f"batch_template_{i}"),
                description=f"Batch template {i}",
                version="1.0.0",
                inputs={},
                steps={},
                tags=["batch"],
                author="batch_author"
            )
            templates.append(template)
        
        # Test batch save
        await pipeline_repository.batch_save(templates)
        
        # Verify all were saved
        all_templates = await pipeline_repository.find_all()
        assert len(all_templates) == 10
        
        # Test batch delete
        template_ids = [t.id for t in templates[:5]]  # Delete first 5
        deleted_count = await pipeline_repository.batch_delete(template_ids)
        assert deleted_count == 5
        
        # Verify deletion
        remaining_templates = await pipeline_repository.find_all()
        assert len(remaining_templates) == 5

    async def test_pagination(self, pipeline_repository):
        """Test pagination functionality."""
        # Create test templates
        templates = []
        for i in range(25):
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=PipelineName(f"page_template_{i:02d}"),
                description=f"Pagination template {i}",
                version="1.0.0",
                inputs={},
                steps={},
                tags=["pagination"],
                author="page_author"
            )
            templates.append(template)
            await pipeline_repository.save(template)
        
        # Test pagination
        page_1 = await pipeline_repository.find_with_limit(10, 0)
        page_2 = await pipeline_repository.find_with_limit(10, 10)
        page_3 = await pipeline_repository.find_with_limit(10, 20)
        
        assert len(page_1) == 10
        assert len(page_2) == 10
        assert len(page_3) == 5  # Remaining items
        
        # Verify no overlap between pages
        page_1_ids = {t.id for t in page_1}
        page_2_ids = {t.id for t in page_2}
        page_3_ids = {t.id for t in page_3}
        
        assert len(page_1_ids & page_2_ids) == 0
        assert len(page_1_ids & page_3_ids) == 0
        assert len(page_2_ids & page_3_ids) == 0

    async def test_database_recovery(self, temp_db_path):
        """Test database recovery after corruption or interruption."""
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        workspace_manager = MockWorkspaceManager(temp_db_path)
        workspace_name = WorkspaceName("recovery_test")
        
        # Create and populate database
        storage = LMDBStorageManager(workspace_manager, "recovery_test", map_size_mb=50)
        repo = LMDBPipelineTemplateRepository(storage, workspace_name)
        
        template = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("recovery_template"),
            description="Template for recovery testing",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["recovery"],
            author="recovery_author"
        )
        
        await repo.save(template)
        
        # Close the database connection
        storage.close()
        
        # Reopen database and verify data persistence
        storage2 = LMDBStorageManager(workspace_manager, "recovery_test", map_size_mb=50)
        repo2 = LMDBPipelineTemplateRepository(storage2, workspace_name)
        
        recovered_templates = await repo2.find_all()
        assert len(recovered_templates) == 1
        assert recovered_templates[0].name.value == "recovery_template"
        
        # Clean up
        storage2.close()


if __name__ == "__main__":
    # Run tests manually for debugging
    import sys
    
    async def run_tests():
        """Run basic integration tests."""
        test_instance = TestLMDBRepositoryIntegration()
        
        print("🧪 Running LMDB Repository Integration Tests...")
        
        try:
            # Create fixtures manually
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_db_path = Path(temp_dir)
                
                # Mock workspace manager
                class MockWorkspaceManager:
                    def __init__(self, base_path: Path):
                        self.base_path = base_path
                    def get_workspace_path(self, workspace_name: str) -> Path:
                        return self.base_path / "workspaces" / workspace_name

                workspace_manager = MockWorkspaceManager(temp_db_path)
                storage_manager = LMDBStorageManager(
                    workspace_manager=workspace_manager,
                    workspace_name="test",
                    map_size_mb=50,
                    max_dbs=10
                )
                
                test_workspace_name = WorkspaceName("test_workspace")
                pipeline_repository = LMDBPipelineTemplateRepository(storage_manager, test_workspace_name)
                
                sample_pipeline_template = PipelineTemplate(
                    id=PipelineId(str(uuid4())),
                    name="Test Pipeline",
                    description="Test pipeline description",
                    version="1.0.0",
                    inputs={
                        "topic": PipelineInput(
                            key="topic",
                            type="text",
                            label="Topic",
                            required=True,
                            placeholder="Enter topic..."
                        )
                    },
                    steps={
                        "outline": PipelineStepTemplate(
                            id=StepId("outline"),
                            name="Create Outline",
                            description="Generate outline",
                            type="llm_generate",
                            prompt_template=PromptTemplate("Create outline for {{ inputs.topic }}"),
                            model_preference=ModelPreference(["gpt-4"])
                        )
                    },
                    tags=["test", "sample"],
                    author="test_author"
                )
                
                # Run basic persistence test
                print("Testing basic persistence...")
                await test_instance.test_pipeline_repository_persistence(
                    pipeline_repository, 
                    sample_pipeline_template
                )
                print("✅ Basic persistence test passed")
                
                print("\n🎉 Integration tests completed successfully!")
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(run_tests())