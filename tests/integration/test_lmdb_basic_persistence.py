"""Basic LMDB persistence tests for core repository implementations.

Simple focused tests for validating LMDB persistence, data integrity,
workspace isolation, and concurrency safety.
"""

import asyncio
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.base.storage_manager import LMDBStorageManager
from writeit.infrastructure.pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository

# Domain entities and value objects
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName


async def test_basic_pipeline_template_persistence():
    """Test basic pipeline template persistence operations."""
    
    print("🧪 Testing Basic Pipeline Template Persistence...")
    
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
            workspace_name="test_persistence",
            map_size_mb=50,
            max_dbs=10
        )
        
        workspace_name = WorkspaceName("test_workspace")
        repo = LMDBPipelineTemplateRepository(storage_manager, workspace_name)
        
        # Create test template
        template = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="basic_test_template",
            description="Basic test template for persistence validation",
            version="1.0.0",
            inputs={
                "test_input": PipelineInput(
                    key="test_input",
                    type="text",
                    label="Test Input",
                    required=True,
                    placeholder="Enter test value..."
                )
            },
            steps={
                "process": PipelineStepTemplate(
                    id=StepId("process"),
                    name="Process Step",
                    description="Process the input",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Process: {{ inputs.test_input }}"),
                    model_preference=ModelPreference(["gpt-4"])
                )
            },
            tags=["test", "basic"],
            author="test_author"
        )
        
        # Test save
        await repo.save(template)
        print("✅ Template saved successfully")
        
        # Test exists
        assert await repo.exists(template.id)
        print("✅ Template existence check successful")
        
        # Test load
        loaded = await repo.find_by_id(template.id)
        assert loaded is not None
        assert loaded.name == template.name
        assert loaded.description == template.description
        assert loaded.version == template.version
        assert loaded.author == template.author
        assert len(loaded.inputs) == len(template.inputs)
        assert len(loaded.steps) == len(template.steps)
        assert loaded.tags == template.tags
        print("✅ Template loading and integrity check successful")
        
        # Test find_all
        all_templates = await repo.find_all()
        assert len(all_templates) == 1
        assert all_templates[0].id == template.id
        print("✅ Find all templates successful")
        
        # Test delete
        await repo.delete(template)
        assert not await repo.exists(template.id)
        assert await repo.find_by_id(template.id) is None
        print("✅ Template deletion successful")
        
        # Clean up
        storage_manager.close()


async def test_complex_data_structure_persistence():
    """Test persistence of complex nested data structures."""
    
    print("🧪 Testing Complex Data Structure Persistence...")
    
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
            workspace_name="complex_test",
            map_size_mb=50,
            max_dbs=10
        )
        
        workspace_name = WorkspaceName("complex_workspace")
        repo = LMDBPipelineTemplateRepository(storage_manager, workspace_name)
        
        # Create complex template
        complex_template = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="complex_unicode_template_🚀",
            description="Complex template with unicode: 你好世界 🌍 ñáéíóú çğş αβγ δεζ ηθι κλμ",
            version="2.1.0-beta",
            inputs={
                "text_input": PipelineInput(
                    key="text_input",
                    type="text",
                    label="Text Input with Emoji 🎉",
                    required=True,
                    placeholder="Enter text with unicode: 💻🔥⚡",
                    default="默认值 (Default)"
                ),
                "choice_input": PipelineInput(
                    key="choice_input",
                    type="choice",
                    label="Choice Input",
                    required=False,
                    options=[("option1", "选项一"), ("option2", "Opción 2"), ("option3", "Επιλογή 3")],
                    default="option1"
                ),
                "large_input": PipelineInput(
                    key="large_input",
                    type="text",
                    label="Large Input",
                    required=False,
                    placeholder="Large placeholder: " + ("X" * 1000)  # 1KB placeholder
                )
            },
            steps={
                "analysis": PipelineStepTemplate(
                    id=StepId("analysis"),
                    name="Analysis Step ✨",
                    description="Analyze content with special chars: @#$%^&*()+={}[]|\\:;\"'<>,.?/~`",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Analyze: {{ inputs.text_input }} with 中文字符 & symbols"),
                    model_preference=ModelPreference(["gpt-4", "claude-3-opus", "gpt-3.5-turbo"])
                ),
                "synthesis": PipelineStepTemplate(
                    id=StepId("synthesis"),
                    name="Synthesis Step",
                    description="Synthesize based on analysis " + ("Y" * 500),  # Long description
                    type="llm_refine",
                    prompt_template=PromptTemplate("Synthesize: {{ steps.analysis }} using العربية, עברית, हिन्दी"),
                    model_preference=ModelPreference(["gpt-4"]),
                    depends_on=["analysis"]
                )
            },
            tags=["complex", "unicode", "特殊字符", "🏷️", "тест"] + [f"tag_{i}" for i in range(20)],  # 25 tags total
            author="complex_author_作者_👨‍💻"
        )
        
        # Save and retrieve
        await repo.save(complex_template)
        retrieved = await repo.find_by_id(complex_template.id)
        
        assert retrieved is not None
        
        # Verify all complex structures preserved
        assert retrieved.name == "complex_unicode_template_🚀"
        assert "你好世界 🌍" in retrieved.description
        assert retrieved.version == "2.1.0-beta"
        assert retrieved.author == "complex_author_作者_👨‍💻"
        assert len(retrieved.tags) == 25
        assert len(retrieved.inputs) == 3
        assert len(retrieved.steps) == 2
        
        # Verify specific input preservation
        text_input = retrieved.inputs["text_input"]
        assert text_input.label == "Text Input with Emoji 🎉"
        assert "💻🔥⚡" in text_input.placeholder
        assert text_input.default == "默认值 (Default)"
        
        choice_input = retrieved.inputs["choice_input"]
        assert choice_input.options == [("option1", "选项一"), ("option2", "Opción 2"), ("option3", "Επιλογή 3")]
        
        large_input = retrieved.inputs["large_input"]
        assert large_input.placeholder.endswith("X" * 1000)
        
        # Verify specific step preservation
        analysis = retrieved.steps["analysis"]
        assert analysis.name == "Analysis Step ✨"
        assert "@#$%^&*()+={}[]|\\:;\"'<>,.?/~`" in analysis.description
        assert "中文字符" in analysis.prompt_template.value
        assert analysis.model_preference.preferences == ["gpt-4", "claude-3-opus", "gpt-3.5-turbo"]
        
        synthesis = retrieved.steps["synthesis"]
        assert synthesis.description.endswith("Y" * 500)
        assert "العربية, עברית, हिन्दी" in synthesis.prompt_template.value
        assert synthesis.depends_on == ["analysis"]
        
        # Verify unicode tags
        assert "特殊字符" in retrieved.tags
        assert "🏷️" in retrieved.tags
        assert "тест" in retrieved.tags
        
        print("✅ Complex data structure persistence successful")
        
        # Clean up
        storage_manager.close()


async def test_concurrent_operations():
    """Test concurrent repository operations."""
    
    print("🧪 Testing Concurrent Operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        workspace_manager = MockWorkspaceManager(temp_db_path)
        workspace_name = WorkspaceName("concurrent_test")
        
        # Create factory for repository instances
        def create_repo():
            storage = LMDBStorageManager(workspace_manager, "concurrent_test", map_size_mb=50)
            return LMDBPipelineTemplateRepository(storage, workspace_name)
        
        # Concurrent save operations
        async def concurrent_saves(batch_id: int, count: int):
            repo = create_repo()
            for i in range(count):
                template = PipelineTemplate(
                    id=PipelineId(str(uuid4())),
                    name=f"concurrent_{batch_id}_{i}",
                    description=f"Concurrent template batch {batch_id}, item {i}",
                    version="1.0.0",
                    inputs={},
                    steps={},
                    tags=[f"batch_{batch_id}", f"item_{i}", "concurrent"],
                    author=f"author_{batch_id}"
                )
                await repo.save(template)
            return count
        
        # Run concurrent batches
        batch_size = 5
        num_batches = 4
        
        tasks = []
        for batch_id in range(num_batches):
            task = concurrent_saves(batch_id, batch_size)
            tasks.append(task)
        
        # Execute all batches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception), f"Concurrent operation failed: {result}"
            assert result == batch_size
        
        # Verify all templates were saved
        verification_repo = create_repo()
        all_templates = await verification_repo.find_all()
        
        expected_count = batch_size * num_batches
        assert len(all_templates) == expected_count
        
        # Verify data integrity - no duplicates or corruption
        names = {t.name for t in all_templates}
        assert len(names) == expected_count  # No duplicate names
        
        # Verify all tags are present
        all_tags = set()
        for template in all_templates:
            all_tags.update(template.tags)
        
        assert "concurrent" in all_tags
        for batch_id in range(num_batches):
            assert f"batch_{batch_id}" in all_tags
            
        print("✅ Concurrent operations successful")


async def test_workspace_isolation():
    """Test workspace isolation."""
    
    print("🧪 Testing Workspace Isolation...")
    
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
        workspace1 = WorkspaceName("workspace1")
        workspace2 = WorkspaceName("workspace2")
        
        storage1 = LMDBStorageManager(workspace_manager, "workspace1", map_size_mb=50)
        storage2 = LMDBStorageManager(workspace_manager, "workspace2", map_size_mb=50)
        
        repo1 = LMDBPipelineTemplateRepository(storage1, workspace1)
        repo2 = LMDBPipelineTemplateRepository(storage2, workspace2)
        
        # Create workspace-specific templates
        template1 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="workspace1_template",
            description="Template for workspace1",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["workspace1", "isolation"],
            author="author1"
        )
        
        template2 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name="workspace2_template",
            description="Template for workspace2",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["workspace2", "isolation"],
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
        assert workspace1_templates[0].name == "workspace1_template"
        assert workspace2_templates[0].name == "workspace2_template"
        
        # Cross-workspace lookup should return None
        assert await repo1.find_by_id(template2.id) is None
        assert await repo2.find_by_id(template1.id) is None
        
        # Search by name should also respect isolation
        assert await repo1.find_by_name("workspace2_template") is None
        assert await repo2.find_by_name("workspace1_template") is None
        
        print("✅ Workspace isolation successful")
        
        # Clean up
        storage1.close()
        storage2.close()


async def test_database_persistence_recovery():
    """Test database persistence and recovery after restart."""
    
    print("🧪 Testing Database Persistence and Recovery...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir)
        
        # Mock workspace manager
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path
            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        workspace_manager = MockWorkspaceManager(temp_db_path)
        workspace_name = WorkspaceName("persistence_test")
        
        # Phase 1: Create and populate database
        storage1 = LMDBStorageManager(workspace_manager, "persistence_test", map_size_mb=50)
        repo1 = LMDBPipelineTemplateRepository(storage1, workspace_name)
        
        templates = []
        for i in range(3):
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=f"persistent_template_{i}",
                description=f"Template {i} should persist after database restart",
                version=f"1.{i}.0",
                inputs={
                    f"input_{i}": PipelineInput(
                        key=f"input_{i}",
                        type="text",
                        label=f"Input {i}",
                        required=True,
                        default=f"default_value_{i}"
                    )
                },
                steps={
                    f"step_{i}": PipelineStepTemplate(
                        id=StepId(f"step_{i}"),
                        name=f"Step {i}",
                        description=f"Processing step {i}",
                        type="llm_generate",
                        prompt_template=PromptTemplate(f"Process {i}: {{{{ inputs.input_{i} }}}}"),
                        model_preference=ModelPreference(["gpt-4"])
                    )
                },
                tags=[f"persistent_{i}", "recovery_test"],
                author=f"persistent_author_{i}"
            )
            templates.append(template)
            await repo1.save(template)
        
        # Verify initial save
        saved_templates = await repo1.find_all()
        assert len(saved_templates) == 3
        
        # Close database connection
        storage1.close()
        
        # Phase 2: Reopen database and verify persistence
        storage2 = LMDBStorageManager(workspace_manager, "persistence_test", map_size_mb=50)
        repo2 = LMDBPipelineTemplateRepository(storage2, workspace_name)
        
        # Verify all data persisted
        recovered_templates = await repo2.find_all()
        assert len(recovered_templates) == 3
        
        # Verify data integrity
        recovered_names = {t.name for t in recovered_templates}
        original_names = {t.name for t in templates}
        assert recovered_names == original_names
        
        # Test specific template integrity
        original_template = templates[1]  # Test middle template
        recovered_template = await repo2.find_by_id(original_template.id)
        assert recovered_template is not None
        assert recovered_template.description == original_template.description
        assert recovered_template.version == original_template.version
        assert recovered_template.author == original_template.author
        assert len(recovered_template.inputs) == len(original_template.inputs)
        assert len(recovered_template.steps) == len(original_template.steps)
        
        # Verify specific input preservation
        input_key = f"input_1"
        assert input_key in recovered_template.inputs
        recovered_input = recovered_template.inputs[input_key]
        original_input = original_template.inputs[input_key]
        assert recovered_input.key == original_input.key
        assert recovered_input.label == original_input.label
        assert recovered_input.default == original_input.default
        
        # Verify specific step preservation
        step_key = f"step_1"
        assert step_key in recovered_template.steps
        recovered_step = recovered_template.steps[step_key]
        original_step = original_template.steps[step_key]
        assert recovered_step.name == original_step.name
        assert recovered_step.description == original_step.description
        assert recovered_step.prompt_template.value == original_step.prompt_template.value
        
        print("✅ Database persistence and recovery successful")
        
        # Clean up
        storage2.close()


async def run_all_basic_tests():
    """Run all basic LMDB persistence tests."""
    
    print("🚀 Running All Basic LMDB Persistence Tests\n")
    
    try:
        await test_basic_pipeline_template_persistence()
        print()
        
        await test_complex_data_structure_persistence()
        print()
        
        await test_concurrent_operations()
        print()
        
        await test_workspace_isolation()
        print()
        
        await test_database_persistence_recovery()
        print()
        
        print("🎉 All basic LMDB persistence tests passed!")
        
    except Exception as e:
        print(f"❌ Basic persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_all_basic_tests())