"""Simplified integration tests for repository implementations with real LMDB storage.

Tests core repository functionality against real LMDB databases to ensure
proper persistence and transaction behavior.
"""

import asyncio
import tempfile
from pathlib import Path
from uuid import uuid4

# Fix import paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.base.storage_manager import LMDBStorageManager
from writeit.infrastructure.pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository

from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName

from writeit.shared.repository import RepositoryError, EntityNotFoundError


async def test_basic_repository_operations():
    """Test basic CRUD operations with real LMDB persistence."""
    
    # Create temporary database
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
        repository = LMDBPipelineTemplateRepository(storage_manager, test_workspace_name)
        
        # Create test template
        template = PipelineTemplate(
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
        
        print("Testing save operation...")
        await repository.save(template)
        print("✅ Save successful")
        
        print("Testing exists check...")
        exists = await repository.exists(template.id)
        assert exists, "Template should exist after save"
        print("✅ Exists check successful")
        
        print("Testing find_by_id...")
        loaded_template = await repository.find_by_id(template.id)
        assert loaded_template is not None, "Template should be found"
        assert loaded_template.id == template.id, "IDs should match"
        assert loaded_template.name == template.name, "Names should match"
        print("✅ Find by ID successful")
        
        print("Testing find_all...")
        all_templates = await repository.find_all()
        assert len(all_templates) == 1, "Should have one template"
        assert all_templates[0].id == template.id, "Template ID should match"
        print("✅ Find all successful")
        
        print("Testing update...")
        template.description = "Updated description"
        await repository.save(template)
        
        updated_template = await repository.find_by_id(template.id)
        assert updated_template.description == "Updated description", "Description should be updated"
        print("✅ Update successful")
        
        print("Testing delete...")
        await repository.delete(template)
        exists_after_delete = await repository.exists(template.id)
        assert not exists_after_delete, "Template should not exist after delete"
        print("✅ Delete successful")
        
        print("Testing count...")
        count = await repository.count()
        assert count == 0, "Count should be 0 after delete"
        print("✅ Count successful")
        
        # Clean up
        storage_manager.close()


async def test_workspace_isolation():
    """Test that different workspaces have isolated data."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
                
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name
        
        workspace_manager = MockWorkspaceManager(temp_db_path)
        
        # Create repositories for different workspaces
        workspace1_name = WorkspaceName("workspace1")
        workspace2_name = WorkspaceName("workspace2")
        
        storage1 = LMDBStorageManager(workspace_manager, "workspace1", map_size_mb=50)
        storage2 = LMDBStorageManager(workspace_manager, "workspace2", map_size_mb=50)
        
        repo1 = LMDBPipelineTemplateRepository(storage1, workspace1_name)
        repo2 = LMDBPipelineTemplateRepository(storage2, workspace2_name)
        
        # Create different templates for each workspace
        template1 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="Workspace 1 Template",
            description="Template for workspace 1",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["workspace1"],
            author="author1"
        )
        
        template2 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="Workspace 2 Template", 
            description="Template for workspace 2",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["workspace2"],
            author="author2"
        )
        
        print("Testing workspace isolation...")
        
        # Save templates to respective workspaces
        await repo1.save(template1)
        await repo2.save(template2)
        
        # Verify isolation - each workspace should only see its own data
        workspace1_templates = await repo1.find_all()
        workspace2_templates = await repo2.find_all()
        
        assert len(workspace1_templates) == 1, "Workspace 1 should have 1 template"
        assert len(workspace2_templates) == 1, "Workspace 2 should have 1 template"
        assert workspace1_templates[0].name == "Workspace 1 Template"
        assert workspace2_templates[0].name == "Workspace 2 Template"
        
        # Cross-workspace lookup should return None
        template2_in_ws1 = await repo1.find_by_id(template2.id)
        template1_in_ws2 = await repo2.find_by_id(template1.id)
        
        assert template2_in_ws1 is None, "Template 2 should not be visible in workspace 1"
        assert template1_in_ws2 is None, "Template 1 should not be visible in workspace 2"
        
        print("✅ Workspace isolation successful")
        
        # Clean up
        storage1.close()
        storage2.close()


async def test_batch_operations():
    """Test batch save and delete operations."""
    
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
        repository = LMDBPipelineTemplateRepository(storage_manager, test_workspace_name)
        
        print("Testing batch operations...")
        
        # Create multiple templates
        templates = []
        for i in range(5):
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=f"Batch Template {i}",
                description=f"Batch template {i}",
                version="1.0.0",
                inputs={},
                steps={},
                tags=["batch"],
                author="batch_author"
            )
            templates.append(template)
        
        # Test batch save
        await repository.batch_save(templates)
        
        # Verify all were saved
        all_templates = await repository.find_all()
        assert len(all_templates) == 5, "Should have 5 templates after batch save"
        
        # Test batch delete
        template_ids = [t.id for t in templates[:3]]  # Delete first 3
        deleted_count = await repository.batch_delete(template_ids)
        assert deleted_count == 3, "Should delete 3 templates"
        
        # Verify deletion
        remaining_templates = await repository.find_all()
        assert len(remaining_templates) == 2, "Should have 2 templates remaining"
        
        print("✅ Batch operations successful")
        
        # Clean up
        storage_manager.close()


async def run_all_tests():
    """Run all integration tests."""
    print("🧪 Running LMDB Repository Integration Tests...\n")
    
    try:
        await test_basic_repository_operations()
        print()
        
        await test_workspace_isolation() 
        print()
        
        await test_batch_operations()
        print()
        
        print("🎉 All repository integration tests passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())