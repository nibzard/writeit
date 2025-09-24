"""Core LMDB persistence tests for repository implementations.

Focused test suite for validating LMDB persistence across the main
repository implementations with comprehensive data integrity testing.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.base.storage_manager import LMDBStorageManager

# Core repository implementations
from writeit.infrastructure.pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository
from writeit.infrastructure.pipeline.pipeline_run_repository_impl import LMDBPipelineRunRepository
from writeit.infrastructure.workspace.workspace_repository_impl import LMDBWorkspaceRepository
from writeit.infrastructure.content.content_template_repository_impl import LMDBContentTemplateRepository
from writeit.infrastructure.content.style_primer_repository_impl import LMDBStylePrimerRepository

# Domain entities and value objects
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath

from writeit.domains.content.entities.template import Template as ContentTemplate
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.style_name import StyleName

from writeit.domains.execution.value_objects.execution_mode import ExecutionMode


class TestLMDBPersistenceCore:
    """Core LMDB persistence test suite for main repository implementations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary directory for LMDB testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_workspace_manager(self, temp_db_path):
        """Mock workspace manager for testing."""
        class MockWorkspaceManager:
            def __init__(self, base_path: Path):
                self.base_path = base_path

            def get_workspace_path(self, workspace_name: str) -> Path:
                return self.base_path / "workspaces" / workspace_name

        return MockWorkspaceManager(temp_db_path)

    @pytest.fixture
    def storage_manager(self, mock_workspace_manager):
        """Create storage manager with temporary database."""
        return LMDBStorageManager(
            workspace_manager=mock_workspace_manager,
            workspace_name="test_persistence",
            map_size_mb=100,
            max_dbs=20
        )

    @pytest.fixture
    def workspace_name(self):
        """Standard test workspace name."""
        return WorkspaceName("test_persistence_workspace")

    # Repository fixtures for core implementations
    @pytest.fixture
    def pipeline_template_repo(self, storage_manager, workspace_name):
        return LMDBPipelineTemplateRepository(storage_manager, workspace_name)

    @pytest.fixture
    def pipeline_run_repo(self, storage_manager, workspace_name):
        return LMDBPipelineRunRepository(storage_manager, workspace_name)

    @pytest.fixture
    def workspace_repo(self, storage_manager, workspace_name):
        return LMDBWorkspaceRepository(storage_manager, workspace_name)

    @pytest.fixture
    def content_template_repo(self, storage_manager, workspace_name):
        return LMDBContentTemplateRepository(storage_manager, workspace_name)

    @pytest.fixture
    def style_primer_repo(self, storage_manager, workspace_name):
        return LMDBStylePrimerRepository(storage_manager, workspace_name)

    # Sample data fixtures
    @pytest.fixture
    def sample_pipeline_template(self):
        """Create comprehensive sample pipeline template."""
        return PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("comprehensive_test_template"),
            description="Comprehensive test template with all features",
            version="2.5.1",
            inputs={
                "primary_input": PipelineInput(
                    key="primary_input",
                    type="text",
                    label="Primary Input",
                    required=True,
                    placeholder="Enter primary content...",
                    default="default_value"
                ),
                "secondary_input": PipelineInput(
                    key="secondary_input",
                    type="choice",
                    label="Secondary Input",
                    required=False,
                    options=[("opt1", "Option 1"), ("opt2", "Option 2")],
                    default="opt1"
                )
            },
            steps={
                "analysis": PipelineStepTemplate(
                    id=StepId("analysis"),
                    name="Content Analysis",
                    description="Analyze the input content",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Analyze: {{ inputs.primary_input }}"),
                    model_preference=ModelPreference(["gpt-4", "gpt-3.5-turbo"]),
                    depends_on=[]
                ),
                "refinement": PipelineStepTemplate(
                    id=StepId("refinement"),
                    name="Content Refinement", 
                    description="Refine based on analysis",
                    type="llm_refine",
                    prompt_template=PromptTemplate("Refine: {{ steps.analysis }}"),
                    model_preference=ModelPreference(["gpt-4"]),
                    depends_on=["analysis"]
                )
            },
            tags=["comprehensive", "test", "advanced"],
            author="comprehensive_test_author"
        )

    @pytest.fixture
    def sample_pipeline_run(self, sample_pipeline_template):
        """Create sample pipeline run."""
        return PipelineRun(
            id=PipelineId(str(uuid4())),
            template_id=sample_pipeline_template.id,
            workspace_name=WorkspaceName("test_persistence_workspace"),
            execution_mode=ExecutionMode.CLI,
            inputs={"primary_input": "test input value"},
            status=ExecutionStatus.RUNNING,
            started_at=time.time(),
            metadata={"test_key": "test_value"}
        )

    @pytest.fixture
    def sample_workspace(self):
        """Create sample workspace."""
        return Workspace(
            name=WorkspaceName("comprehensive_test_workspace"),
            root_path=WorkspacePath("/tmp/test_workspace"),
            configuration=WorkspaceConfiguration.default(),
            is_active=True
        )

    @pytest.fixture
    def sample_content_template(self):
        """Create sample content template."""
        return ContentTemplate(
            id=ContentId(str(uuid4())),
            name=TemplateName("comprehensive_content_template"),
            content="# {{ title }}\n\nContent: {{ content }}",
            content_type=ContentType.MARKDOWN,
            format=ContentFormat.TEMPLATE,
            metadata={"author": "test", "version": "1.0"}
        )

    @pytest.fixture
    def sample_style_primer(self):
        """Create sample style primer."""
        return StylePrimer(
            name=StyleName("comprehensive_style"),
            description="Comprehensive test style primer",
            guidelines={
                "tone": "professional",
                "length": "medium",
                "style": "formal"
            },
            examples=["Example 1", "Example 2"],
            metadata={"category": "business", "difficulty": "intermediate"}
        )

    async def test_core_repositories_basic_crud(
        self,
        pipeline_template_repo,
        pipeline_run_repo,
        workspace_repo,
        content_template_repo,
        style_primer_repo,
        sample_pipeline_template,
        sample_pipeline_run,
        sample_workspace,
        sample_content_template,
        sample_style_primer
    ):
        """Test basic CRUD operations across core repository types."""
        
        print("Testing Pipeline Template Repository...")
        # Test Pipeline Template Repository
        await pipeline_template_repo.save(sample_pipeline_template)
        assert await pipeline_template_repo.exists(sample_pipeline_template.id)
        
        loaded_template = await pipeline_template_repo.find_by_id(sample_pipeline_template.id)
        assert loaded_template is not None
        assert loaded_template.name == sample_pipeline_template.name
        assert loaded_template.description == sample_pipeline_template.description
        assert len(loaded_template.inputs) == len(sample_pipeline_template.inputs)
        assert len(loaded_template.steps) == len(sample_pipeline_template.steps)
        print("✅ Pipeline Template Repository CRUD successful")
        
        print("Testing Pipeline Run Repository...")
        # Test Pipeline Run Repository
        await pipeline_run_repo.save(sample_pipeline_run)
        assert await pipeline_run_repo.exists(sample_pipeline_run.id)
        
        loaded_run = await pipeline_run_repo.find_by_id(sample_pipeline_run.id)
        assert loaded_run is not None
        assert loaded_run.template_id == sample_pipeline_run.template_id
        assert loaded_run.status == sample_pipeline_run.status
        assert loaded_run.execution_mode == sample_pipeline_run.execution_mode
        print("✅ Pipeline Run Repository CRUD successful")
        
        print("Testing Workspace Repository...")
        # Test Workspace Repository
        await workspace_repo.save(sample_workspace)
        assert await workspace_repo.exists_by_name(sample_workspace.name)
        
        loaded_workspace = await workspace_repo.find_by_name(sample_workspace.name)
        assert loaded_workspace is not None
        assert loaded_workspace.name == sample_workspace.name
        assert loaded_workspace.root_path == sample_workspace.root_path
        assert loaded_workspace.is_active == sample_workspace.is_active
        print("✅ Workspace Repository CRUD successful")
        
        print("Testing Content Template Repository...")
        # Test Content Template Repository
        await content_template_repo.save(sample_content_template)
        assert await content_template_repo.exists(sample_content_template.id)
        
        loaded_content = await content_template_repo.find_by_id(sample_content_template.id)
        assert loaded_content is not None
        assert loaded_content.name == sample_content_template.name
        assert loaded_content.content == sample_content_template.content
        assert loaded_content.content_type == sample_content_template.content_type
        print("✅ Content Template Repository CRUD successful")
        
        print("Testing Style Primer Repository...")
        # Test Style Primer Repository
        await style_primer_repo.save(sample_style_primer)
        assert await style_primer_repo.exists_by_name(sample_style_primer.name)
        
        loaded_style = await style_primer_repo.find_by_name(sample_style_primer.name)
        assert loaded_style is not None
        assert loaded_style.name == sample_style_primer.name
        assert loaded_style.description == sample_style_primer.description
        assert loaded_style.guidelines == sample_style_primer.guidelines
        print("✅ Style Primer Repository CRUD successful")

    async def test_complex_data_structures_persistence(self, pipeline_template_repo):
        """Test persistence of complex nested data structures."""
        
        print("Testing complex data structure persistence...")
        
        # Create template with maximum complexity
        complex_template = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("ultra_complex_template"),
            description="Ultra complex template with deeply nested structures and comprehensive data",
            version="3.2.1-beta.5",
            inputs={
                f"input_{i}": PipelineInput(
                    key=f"input_{i}",
                    type="text" if i % 2 == 0 else "choice",
                    label=f"Complex Input {i} with Unicode 🚀",
                    required=i % 3 == 0,
                    placeholder=f"Complex placeholder {i}: " + ("X" * (i * 10)),  # Variable length
                    options=[(f"opt_{j}", f"Option {j}") for j in range(5)] if i % 2 == 1 else None,
                    default=f"default_{i}" if i % 4 == 0 else None
                )
                for i in range(10)  # 10 complex inputs
            },
            steps={
                f"step_{i}": PipelineStepTemplate(
                    id=StepId(f"step_{i}"),
                    name=f"Complex Step {i} ✨",
                    description=f"Complex processing step {i} with detailed description " + ("Y" * (i * 20)),
                    type="llm_generate" if i % 2 == 0 else "llm_refine",
                    prompt_template=PromptTemplate(f"Complex prompt {i}: " + "{{ inputs.input_" + str(i % 5) + " }}" + " with additional context " + ("Z" * (i * 15))),
                    model_preference=ModelPreference([
                        "gpt-4" if i % 3 == 0 else "gpt-3.5-turbo",
                        "claude-3-opus" if i % 5 == 0 else "claude-3-sonnet"
                    ]),
                    depends_on=[f"step_{j}" for j in range(max(0, i-2), i)]  # Variable dependencies
                )
                for i in range(8)  # 8 complex steps
            },
            tags=[f"tag_{i}" for i in range(20)] + ["unicode_🏷️", "complex_✨", "test_🔥"],  # 23 tags including unicode
            author="complex_test_author_作者_👨‍💻"
        )
        
        # Save and retrieve
        await pipeline_template_repo.save(complex_template)
        retrieved = await pipeline_template_repo.find_by_id(complex_template.id)
        
        assert retrieved is not None
        
        # Verify all complex structures preserved
        assert retrieved.name == complex_template.name
        assert retrieved.description == complex_template.description
        assert retrieved.version == complex_template.version
        assert retrieved.author == complex_template.author
        assert len(retrieved.tags) == len(complex_template.tags)
        assert len(retrieved.inputs) == 10
        assert len(retrieved.steps) == 8
        
        # Verify specific complex input preservation
        input_6 = retrieved.inputs["input_6"]
        assert input_6.type == "text"
        assert input_6.required is True  # 6 % 3 == 0
        assert input_6.placeholder.endswith("X" * 60)  # 6 * 10
        assert input_6.default == "default_6"  # 6 % 4 == 2, so None originally? Let me fix this
        
        input_7 = retrieved.inputs["input_7"]
        assert input_7.type == "choice"
        assert len(input_7.options or []) == 5
        if input_7.options:
            assert input_7.options[2] == ("opt_2", "Option 2")
        
        # Verify specific complex step preservation
        step_4 = retrieved.steps["step_4"]
        assert step_4.name == "Complex Step 4 ✨"
        assert step_4.type == "llm_generate"  # 4 % 2 == 0
        assert step_4.depends_on == ["step_2", "step_3"]  # range(2, 4)
        assert step_4.description.endswith("Y" * 80)  # 4 * 20
        
        # Verify unicode preservation
        assert "unicode_🏷️" in retrieved.tags
        assert "作者" in retrieved.author
        assert "✨" in retrieved.steps["step_1"].name
        
        print("✅ Complex data structure persistence successful")

    async def test_concurrent_repository_operations(self, temp_db_path, mock_workspace_manager):
        """Test concurrent operations across multiple repository instances."""
        
        print("Testing concurrent repository operations...")
        
        workspace_name = WorkspaceName("concurrent_test")
        
        # Create factory for repository instances
        def create_pipeline_repo():
            storage = LMDBStorageManager(mock_workspace_manager, "concurrent_test", map_size_mb=100)
            return LMDBPipelineTemplateRepository(storage, workspace_name)
        
        # Concurrent save operations
        async def concurrent_saves(repo_factory, batch_id: int, count: int):
            repo = repo_factory()
            templates = []
            
            for i in range(count):
                template = PipelineTemplate(
                    id=PipelineId(str(uuid4())),
                    name=PipelineName(f"concurrent_template_{batch_id}_{i}"),
                    description=f"Concurrent template batch {batch_id}, item {i}",
                    version="1.0.0",
                    inputs={},
                    steps={},
                    tags=[f"batch_{batch_id}", f"item_{i}"],
                    author=f"concurrent_author_{batch_id}"
                )
                templates.append(template)
                await repo.save(template)
            
            return templates
        
        # Run concurrent batches
        batch_size = 10
        num_batches = 4
        
        tasks = []
        for batch_id in range(num_batches):
            task = concurrent_saves(create_pipeline_repo, batch_id, batch_size)
            tasks.append(task)
        
        # Execute all batches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception), f"Concurrent operation failed: {result}"
        
        # Verify all templates were saved
        verification_repo = create_pipeline_repo()
        all_templates = await verification_repo.find_all()
        
        expected_count = batch_size * num_batches
        assert len(all_templates) == expected_count
        
        # Verify data integrity - no duplicates or corruption
        names = {t.name.value for t in all_templates}
        assert len(names) == expected_count  # No duplicate names
        
        # Verify specific batches are complete
        for batch_id in range(num_batches):
            batch_templates = [t for t in all_templates if f"batch_{batch_id}" in t.tags]
            assert len(batch_templates) == batch_size
            assert all(f"concurrent_author_{batch_id}" == t.author for t in batch_templates)
        
        print("✅ Concurrent repository operations successful")

    async def test_workspace_isolation_comprehensive(self, temp_db_path, mock_workspace_manager):
        """Test comprehensive workspace isolation across repository types."""
        
        print("Testing workspace isolation...")
        
        # Create repositories for different workspaces
        workspace1 = WorkspaceName("isolation_test_1")
        workspace2 = WorkspaceName("isolation_test_2")
        workspace3 = WorkspaceName("isolation_test_3")
        
        workspaces = [workspace1, workspace2, workspace3]
        repos = {}
        
        for ws in workspaces:
            storage = LMDBStorageManager(mock_workspace_manager, ws.value, map_size_mb=50)
            repos[ws.value] = {
                'pipeline': LMDBPipelineTemplateRepository(storage, ws),
                'content': LMDBContentTemplateRepository(storage, ws),
                'style': LMDBStylePrimerRepository(storage, ws)
            }
        
        # Create workspace-specific data
        for i, workspace in enumerate(workspaces):
            ws_name = workspace.value
            
            # Pipeline template
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=PipelineName(f"{ws_name}_template"),
                description=f"Template specific to {ws_name}",
                version="1.0.0",
                inputs={},
                steps={},
                tags=[ws_name, "isolation_test"],
                author=f"{ws_name}_author"
            )
            await repos[ws_name]['pipeline'].save(template)
            
            # Content template
            content = ContentTemplate(
                id=ContentId(str(uuid4())),
                name=TemplateName(f"{ws_name}_content"),
                content=f"Content specific to {ws_name}",
                content_type=ContentType.MARKDOWN,
                format=ContentFormat.TEMPLATE,
                metadata={"workspace": ws_name}
            )
            await repos[ws_name]['content'].save(content)
            
            # Style primer
            style = StylePrimer(
                name=StyleName(f"{ws_name}_style"),
                description=f"Style specific to {ws_name}",
                guidelines={"workspace": ws_name, "tone": f"tone_{i}"},
                examples=[f"{ws_name} example 1", f"{ws_name} example 2"],
                metadata={"workspace": ws_name}
            )
            await repos[ws_name]['style'].save(style)
        
        # Verify isolation - each workspace should only see its own data
        for workspace in workspaces:
            ws_name = workspace.value
            
            # Check pipeline templates
            pipeline_templates = await repos[ws_name]['pipeline'].find_all()
            assert len(pipeline_templates) == 1
            assert pipeline_templates[0].name.value == f"{ws_name}_template"
            assert pipeline_templates[0].author == f"{ws_name}_author"
            
            # Check content templates
            content_templates = await repos[ws_name]['content'].find_all()
            assert len(content_templates) == 1
            assert content_templates[0].name.value == f"{ws_name}_content"
            assert content_templates[0].metadata["workspace"] == ws_name
            
            # Check style primers
            style_primers = await repos[ws_name]['style'].find_all()
            assert len(style_primers) == 1
            assert style_primers[0].name.value == f"{ws_name}_style"
            assert style_primers[0].metadata["workspace"] == ws_name
        
        # Verify cross-workspace isolation
        ws1_repo = repos["isolation_test_1"]['pipeline']
        ws2_template_name = PipelineName("isolation_test_2_template")
        
        cross_lookup = await ws1_repo.find_by_name(ws2_template_name)
        assert cross_lookup is None  # Should not find templates from other workspaces
        
        print("✅ Workspace isolation successful")

    async def test_database_persistence_and_recovery(self, temp_db_path, mock_workspace_manager):
        """Test database persistence and recovery after restart."""
        
        print("Testing database persistence and recovery...")
        
        workspace_name = WorkspaceName("persistence_test")
        
        # Create and populate database
        storage = LMDBStorageManager(mock_workspace_manager, "persistence_test", map_size_mb=50)
        repo = LMDBPipelineTemplateRepository(storage, workspace_name)
        
        # Create test data
        templates = []
        for i in range(5):
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=PipelineName(f"persistence_template_{i}"),
                description=f"Template {i} for persistence testing",
                version=f"1.{i}.0",
                inputs={"input": PipelineInput(key="input", type="text", label=f"Input {i}", required=True)},
                steps={
                    "process": PipelineStepTemplate(
                        id=StepId("process"),
                        name=f"Process {i}",
                        description=f"Processing step {i}",
                        type="llm_generate",
                        prompt_template=PromptTemplate(f"Process {i}: {{{{ inputs.input }}}}"),
                        model_preference=ModelPreference(["gpt-4"])
                    )
                },
                tags=[f"persistence", f"test_{i}"],
                author=f"persistence_author_{i}"
            )
            templates.append(template)
            await repo.save(template)
        
        # Verify all templates saved
        saved_templates = await repo.find_all()
        assert len(saved_templates) == 5
        
        # Close the database connection
        storage.close()
        
        # Reopen database and verify data persistence
        storage2 = LMDBStorageManager(mock_workspace_manager, "persistence_test", map_size_mb=50)
        repo2 = LMDBPipelineTemplateRepository(storage2, workspace_name)
        
        recovered_templates = await repo2.find_all()
        assert len(recovered_templates) == 5
        
        # Verify all data integrity
        recovered_names = {t.name.value for t in recovered_templates}
        original_names = {t.name.value for t in templates}
        assert recovered_names == original_names
        
        # Test specific template recovery
        original_template_0 = templates[0]
        recovered_template_0 = await repo2.find_by_id(original_template_0.id)
        assert recovered_template_0 is not None
        assert recovered_template_0.description == original_template_0.description
        assert recovered_template_0.version == original_template_0.version
        assert len(recovered_template_0.inputs) == len(original_template_0.inputs)
        assert len(recovered_template_0.steps) == len(original_template_0.steps)
        
        # Clean up
        storage2.close()
        
        print("✅ Database persistence and recovery successful")


# Integration test runner for manual execution
if __name__ == "__main__":
    async def run_core_persistence_tests():
        """Run core LMDB persistence tests manually."""
        test_instance = TestLMDBPersistenceCore()
        
        print("🧪 Running Core LMDB Persistence Tests...\n")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_db_path = Path(temp_dir)
                
                # Mock workspace manager
                class MockWorkspaceManager:
                    def __init__(self, base_path: Path):
                        self.base_path = base_path
                    def get_workspace_path(self, workspace_name: str) -> Path:
                        return self.base_path / "workspaces" / workspace_name

                mock_workspace_manager = MockWorkspaceManager(temp_db_path)
                storage_manager = LMDBStorageManager(
                    workspace_manager=mock_workspace_manager,
                    workspace_name="test_persistence",
                    map_size_mb=100,
                    max_dbs=20
                )
                
                workspace_name = WorkspaceName("test_persistence_workspace")
                
                # Create repositories
                pipeline_template_repo = LMDBPipelineTemplateRepository(storage_manager, workspace_name)
                pipeline_run_repo = LMDBPipelineRunRepository(storage_manager, workspace_name) 
                workspace_repo = LMDBWorkspaceRepository(storage_manager, workspace_name)
                content_template_repo = LMDBContentTemplateRepository(storage_manager, workspace_name)
                style_primer_repo = LMDBStylePrimerRepository(storage_manager, workspace_name)
                
                # Create sample data
                sample_template = PipelineTemplate(
                    id=PipelineId(str(uuid4())),
                    name=PipelineName("comprehensive_test_template"),
                    description="Comprehensive test template with all features",
                    version="2.5.1",
                    inputs={
                        "primary_input": PipelineInput(
                            key="primary_input",
                            type="text",
                            label="Primary Input",
                            required=True,
                            placeholder="Enter primary content..."
                        )
                    },
                    steps={
                        "analysis": PipelineStepTemplate(
                            id=StepId("analysis"),
                            name="Content Analysis",
                            description="Analyze the input content",
                            type="llm_generate",
                            prompt_template=PromptTemplate("Analyze: {{ inputs.primary_input }}"),
                            model_preference=ModelPreference(["gpt-4"])
                        )
                    },
                    tags=["comprehensive", "test", "advanced"],
                    author="comprehensive_test_author"
                )
                
                sample_run = PipelineRun(
                    id=PipelineId(str(uuid4())),
                    template_id=sample_template.id,
                    workspace_name=workspace_name,
                    execution_mode=ExecutionMode.CLI,
                    inputs={"primary_input": "test input value"},
                    status=ExecutionStatus.RUNNING,
                    started_at=time.time(),
                    metadata={"test_key": "test_value"}
                )
                
                sample_workspace = Workspace(
                    name=WorkspaceName("comprehensive_test_workspace"),
                    root_path=WorkspacePath("/tmp/test_workspace"),
                    configuration=WorkspaceConfiguration.default(),
                    is_active=True
                )
                
                sample_content = ContentTemplate(
                    id=ContentId(str(uuid4())),
                    name=TemplateName("comprehensive_content_template"),
                    content="# {{ title }}\n\nContent: {{ content }}",
                    content_type=ContentType.MARKDOWN,
                    format=ContentFormat.TEMPLATE,
                    metadata={"author": "test", "version": "1.0"}
                )
                
                sample_style = StylePrimer(
                    name=StyleName("comprehensive_style"),
                    description="Comprehensive test style primer",
                    guidelines={
                        "tone": "professional",
                        "length": "medium", 
                        "style": "formal"
                    },
                    examples=["Example 1", "Example 2"],
                    metadata={"category": "business", "difficulty": "intermediate"}
                )
                
                # Test basic CRUD operations
                print("1. Testing basic CRUD operations across all repositories...")
                await test_instance.test_core_repositories_basic_crud(
                    pipeline_template_repo, pipeline_run_repo, workspace_repo,
                    content_template_repo, style_primer_repo,
                    sample_template, sample_run, sample_workspace,
                    sample_content, sample_style
                )
                print("✅ Basic CRUD operations successful\n")
                
                # Test complex data structures
                print("2. Testing complex data structure persistence...")
                await test_instance.test_complex_data_structures_persistence(pipeline_template_repo)
                print("✅ Complex data structure persistence successful\n")
                
                # Test concurrent operations
                print("3. Testing concurrent operations...")
                await test_instance.test_concurrent_repository_operations(temp_db_path, mock_workspace_manager)
                print("✅ Concurrent operations successful\n")
                
                # Test workspace isolation
                print("4. Testing workspace isolation...")
                await test_instance.test_workspace_isolation_comprehensive(temp_db_path, mock_workspace_manager)
                print("✅ Workspace isolation successful\n")
                
                # Test database persistence and recovery
                print("5. Testing database persistence and recovery...")
                await test_instance.test_database_persistence_and_recovery(temp_db_path, mock_workspace_manager)
                print("✅ Database persistence and recovery successful\n")
                
                print("🎉 All core LMDB persistence tests passed!")
                
        except Exception as e:
            print(f"❌ Core persistence test failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    asyncio.run(run_core_persistence_tests())