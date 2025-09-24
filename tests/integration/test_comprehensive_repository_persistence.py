"""Comprehensive LMDB persistence tests for all repository implementations.

This test suite validates LMDB persistence across all repository implementations,
testing data integrity, serialization, concurrency, and performance.
"""

import asyncio
import pytest
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.base.storage_manager import LMDBStorageManager

# Repository implementations
from writeit.infrastructure.pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository
from writeit.infrastructure.pipeline.pipeline_run_repository_impl import LMDBPipelineRunRepository
from writeit.infrastructure.pipeline.step_execution_repository_impl import LMDBStepExecutionRepository
from writeit.infrastructure.workspace.workspace_repository_impl import LMDBWorkspaceRepository
from writeit.infrastructure.workspace.workspace_config_repository_impl import LMDBWorkspaceConfigRepository
from writeit.infrastructure.content.content_template_repository_impl import LMDBContentTemplateRepository
from writeit.infrastructure.content.style_primer_repository_impl import LMDBStylePrimerRepository
from writeit.infrastructure.content.generated_content_repository_impl import LMDBGeneratedContentRepository
from writeit.infrastructure.execution.llm_cache_repository_impl import LMDBLLMCacheRepository
from writeit.infrastructure.execution.token_usage_repository_impl import LMDBTokenUsageRepository

# Domain entities and value objects
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.entities.step_execution import StepExecution
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
from writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue

from writeit.domains.content.entities.template import Template as ContentTemplate
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.style_name import StyleName

from writeit.domains.execution.entities.llm_provider import LLMProvider
from writeit.domains.execution.entities.execution_context import ExecutionContext
from writeit.domains.execution.entities.token_usage import TokenUsage as TokenUsageEntity
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount
from writeit.domains.execution.value_objects.cache_key import CacheKey
from writeit.domains.execution.value_objects.execution_mode import ExecutionMode


class TestComprehensiveLMDBPersistence:
    """Comprehensive test suite for all LMDB repository implementations."""

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
            map_size_mb=100,  # Larger for comprehensive tests
            max_dbs=20
        )

    @pytest.fixture
    def workspace_name(self):
        """Standard test workspace name."""
        return WorkspaceName("test_persistence_workspace")

    # Repository fixtures
    @pytest.fixture
    def pipeline_template_repo(self, storage_manager, workspace_name):
        return LMDBPipelineTemplateRepository(storage_manager, workspace_name)

    @pytest.fixture
    def pipeline_run_repo(self, storage_manager, workspace_name):
        return LMDBPipelineRunRepository(storage_manager, workspace_name)

    @pytest.fixture
    def step_execution_repo(self, storage_manager, workspace_name):
        return LMDBStepExecutionRepository(storage_manager, workspace_name)

    @pytest.fixture
    def workspace_repo(self, storage_manager, workspace_name):
        return LMDBWorkspaceRepository(storage_manager, workspace_name)

    @pytest.fixture
    def workspace_config_repo(self, storage_manager, workspace_name):
        return LMDBWorkspaceConfigRepository(storage_manager, workspace_name)

    @pytest.fixture
    def content_template_repo(self, storage_manager, workspace_name):
        return LMDBContentTemplateRepository(storage_manager, workspace_name)

    @pytest.fixture
    def style_primer_repo(self, storage_manager, workspace_name):
        return LMDBStylePrimerRepository(storage_manager, workspace_name)

    @pytest.fixture
    def generated_content_repo(self, storage_manager, workspace_name):
        return LMDBGeneratedContentRepository(storage_manager, workspace_name)

    @pytest.fixture
    def llm_cache_repo(self, storage_manager, workspace_name):
        return LMDBLLMCacheRepository(storage_manager, workspace_name)

    @pytest.fixture
    def token_usage_repo(self, storage_manager, workspace_name):
        return LMDBTokenUsageRepository(storage_manager, workspace_name)

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

    async def test_all_repositories_basic_crud(
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
        """Test basic CRUD operations across all repository types."""
        
        # Test Pipeline Template Repository
        await pipeline_template_repo.save(sample_pipeline_template)
        assert await pipeline_template_repo.exists(sample_pipeline_template.id)
        
        loaded_template = await pipeline_template_repo.find_by_id(sample_pipeline_template.id)
        assert loaded_template is not None
        assert loaded_template.name == sample_pipeline_template.name
        assert loaded_template.description == sample_pipeline_template.description
        assert len(loaded_template.inputs) == len(sample_pipeline_template.inputs)
        assert len(loaded_template.steps) == len(sample_pipeline_template.steps)
        
        # Test Pipeline Run Repository
        await pipeline_run_repo.save(sample_pipeline_run)
        assert await pipeline_run_repo.exists(sample_pipeline_run.id)
        
        loaded_run = await pipeline_run_repo.find_by_id(sample_pipeline_run.id)
        assert loaded_run is not None
        assert loaded_run.template_id == sample_pipeline_run.template_id
        assert loaded_run.status == sample_pipeline_run.status
        assert loaded_run.execution_mode == sample_pipeline_run.execution_mode
        
        # Test Workspace Repository
        await workspace_repo.save(sample_workspace)
        assert await workspace_repo.exists_by_name(sample_workspace.name)
        
        loaded_workspace = await workspace_repo.find_by_name(sample_workspace.name)
        assert loaded_workspace is not None
        assert loaded_workspace.name == sample_workspace.name
        assert loaded_workspace.root_path == sample_workspace.root_path
        assert loaded_workspace.is_active == sample_workspace.is_active
        
        # Test Content Template Repository
        await content_template_repo.save(sample_content_template)
        assert await content_template_repo.exists(sample_content_template.id)
        
        loaded_content = await content_template_repo.find_by_id(sample_content_template.id)
        assert loaded_content is not None
        assert loaded_content.name == sample_content_template.name
        assert loaded_content.content == sample_content_template.content
        assert loaded_content.content_type == sample_content_template.content_type
        
        # Test Style Primer Repository
        await style_primer_repo.save(sample_style_primer)
        assert await style_primer_repo.exists_by_name(sample_style_primer.name)
        
        loaded_style = await style_primer_repo.find_by_name(sample_style_primer.name)
        assert loaded_style is not None
        assert loaded_style.name == sample_style_primer.name
        assert loaded_style.description == sample_style_primer.description
        assert loaded_style.guidelines == sample_style_primer.guidelines

    async def test_complex_data_structures_persistence(self, pipeline_template_repo):
        """Test persistence of complex nested data structures."""
        
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
                    label=f"Complex Input {i} with Unicode \ud83d\ude80",
                    required=i % 3 == 0,
                    placeholder=f"Complex placeholder {i}: " + ("X" * (i * 10)),  # Variable length
                    options=[(f"opt_{j}", f"Option {j}") for j in range(5)] if i % 2 == 1 else None,
                    default=f"default_{i}" if i % 4 == 0 else None
                )
                for i in range(25)  # 25 complex inputs
            },
            steps={
                f"step_{i}": PipelineStepTemplate(
                    id=StepId(f"step_{i}"),
                    name=f"Complex Step {i} \u2728",
                    description=f"Complex processing step {i} with detailed description " + ("Y" * (i * 20)),
                    type="llm_generate" if i % 2 == 0 else "llm_refine",
                    prompt_template=PromptTemplate(f"Complex prompt {i}: " + "{{ inputs.input_" + str(i % 5) + " }}" + " with additional context " + ("Z" * (i * 15))),
                    model_preference=ModelPreference([
                        "gpt-4" if i % 3 == 0 else "gpt-3.5-turbo",
                        "claude-3-opus" if i % 5 == 0 else "claude-3-sonnet"
                    ]),
                    depends_on=[f"step_{j}" for j in range(max(0, i-3), i)]  # Variable dependencies
                )
                for i in range(15)  # 15 complex steps
            },
            tags=[f"tag_{i}" for i in range(50)] + ["unicode_\ud83c\udff7\ufe0f", "complex_\u2728", "test_\ud83d\udd25"],  # 53 tags including unicode
            author="complex_test_author_\u4f5c\u8005_\ud83d\udc68\u200d\ud83d\udcbb"
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
        assert len(retrieved.inputs) == 25
        assert len(retrieved.steps) == 15
        
        # Verify specific complex input preservation
        input_12 = retrieved.inputs["input_12"]
        assert input_12.type == "text"
        assert input_12.required is True  # 12 % 3 == 0
        assert input_12.placeholder.endswith("X" * 120)  # 12 * 10
        assert input_12.default == "default_12"  # 12 % 4 == 0
        
        input_13 = retrieved.inputs["input_13"]
        assert input_13.type == "choice"
        assert len(input_13.options) == 5
        assert input_13.options[2] == ("opt_2", "Option 2")
        
        # Verify specific complex step preservation
        step_8 = retrieved.steps["step_8"]
        assert step_8.name == "Complex Step 8 \u2728"
        assert step_8.type == "llm_generate"  # 8 % 2 == 0
        assert step_8.depends_on == ["step_5", "step_6", "step_7"]  # range(5, 8)
        assert step_8.description.endswith("Y" * 160)  # 8 * 20
        
        # Verify unicode preservation
        assert "unicode_\ud83c\udff7\ufe0f" in retrieved.tags
        assert "\u4f5c\u8005" in retrieved.author
        assert "\u2728" in retrieved.steps["step_1"].name

    async def test_concurrent_repository_operations(self, temp_db_path, mock_workspace_manager):
        """Test concurrent operations across multiple repository instances."""
        
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
        batch_size = 20
        num_batches = 8
        
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

    async def test_repository_performance_benchmarks(self, pipeline_template_repo):
        """Test repository performance with large datasets."""
        
        # Create large dataset
        templates = []
        for i in range(100):  # 100 templates
            template = PipelineTemplate(
                id=PipelineId(str(uuid4())),
                name=PipelineName(f"perf_template_{i:03d}"),
                description=f"Performance test template {i} with substantial content " + ("X" * 500),
                version=f"1.{i}.0",
                inputs={
                    f"input_{j}": PipelineInput(
                        key=f"input_{j}",
                        type="text",
                        label=f"Input {j}",
                        required=True,
                        placeholder="Placeholder " + ("Y" * 100)
                    )
                    for j in range(10)  # 10 inputs per template
                },
                steps={
                    f"step_{j}": PipelineStepTemplate(
                        id=StepId(f"step_{j}"),
                        name=f"Step {j}",
                        description=f"Processing step {j}",
                        type="llm_generate",
                        prompt_template=PromptTemplate(f"Process step {j}: " + "Z" * 200),
                        model_preference=ModelPreference(["gpt-4"])
                    )
                    for j in range(5)  # 5 steps per template
                },
                tags=[f"perf", f"test_{i}", f"category_{i % 10}"],
                author=f"perf_author_{i % 5}"
            )
            templates.append(template)
        
        # Benchmark batch save
        start_time = time.time()
        await pipeline_template_repo.batch_save(templates)
        batch_save_time = time.time() - start_time
        
        print(f"Batch save of 100 complex templates: {batch_save_time:.3f}s")
        assert batch_save_time < 10.0  # Should complete within 10 seconds
        
        # Benchmark individual retrieval
        start_time = time.time()
        for template in templates[:20]:  # Test first 20
            retrieved = await pipeline_template_repo.find_by_id(template.id)
            assert retrieved is not None
        retrieval_time = time.time() - start_time
        
        print(f"Individual retrieval of 20 templates: {retrieval_time:.3f}s")
        assert retrieval_time < 2.0  # Should complete within 2 seconds
        
        # Benchmark find_all
        start_time = time.time()
        all_templates = await pipeline_template_repo.find_all()
        find_all_time = time.time() - start_time
        
        print(f"Find all 100 templates: {find_all_time:.3f}s")
        assert len(all_templates) == 100
        assert find_all_time < 3.0  # Should complete within 3 seconds
        
        # Benchmark search operations
        start_time = time.time()
        search_results = await pipeline_template_repo.search_by_tag("perf")
        search_time = time.time() - start_time
        
        print(f"Search by tag across 100 templates: {search_time:.3f}s")
        assert len(search_results) == 100  # All templates have "perf" tag
        assert search_time < 1.0  # Should complete within 1 second

    async def test_workspace_isolation_comprehensive(self, temp_db_path, mock_workspace_manager):
        """Test comprehensive workspace isolation across all repository types."""
        
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

    async def test_error_recovery_and_data_integrity(self, pipeline_template_repo, sample_pipeline_template):
        """Test error recovery and data integrity preservation."""
        
        # Save initial data
        await pipeline_template_repo.save(sample_pipeline_template)
        initial_templates = await pipeline_template_repo.find_all()
        assert len(initial_templates) == 1
        
        # Test recovery from serialization errors
        original_serializer = pipeline_template_repo._storage._serializer
        
        class FlakySerializer:
            def __init__(self, original):
                self.original = original
                self.call_count = 0
                
            def serialize(self, obj):
                self.call_count += 1
                if self.call_count == 2:  # Fail on second call
                    raise Exception("Simulated serialization failure")
                return self.original.serialize(obj)
                
            def deserialize(self, data, entity_type):
                return self.original.deserialize(data, entity_type)
        
        flaky_serializer = FlakySerializer(original_serializer)
        pipeline_template_repo._storage._serializer = flaky_serializer
        
        # First save should succeed
        template1 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("recovery_test_1"),
            description="First template",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["recovery"],
            author="recovery_author"
        )
        await pipeline_template_repo.save(template1)
        
        # Second save should fail
        template2 = PipelineTemplate(
            id=PipelineId(str(uuid4())),
            name=PipelineName("recovery_test_2"), 
            description="Second template",
            version="1.0.0",
            inputs={},
            steps={},
            tags=["recovery"],
            author="recovery_author"
        )
        
        with pytest.raises(Exception, match="Simulated serialization failure"):
            await pipeline_template_repo.save(template2)
        
        # Verify data integrity - original data should be preserved
        all_templates = await pipeline_template_repo.find_all()
        assert len(all_templates) == 2  # Original + first successful save
        
        template_names = {t.name.value for t in all_templates}
        assert "comprehensive_test_template" in template_names
        assert "recovery_test_1" in template_names
        assert "recovery_test_2" not in template_names
        
        # Restore original serializer and verify system recovery
        pipeline_template_repo._storage._serializer = original_serializer
        
        # Should be able to save successfully now
        await pipeline_template_repo.save(template2)
        final_templates = await pipeline_template_repo.find_all()
        assert len(final_templates) == 3
        
        final_names = {t.name.value for t in final_templates}
        assert "recovery_test_2" in final_names


# Integration test runner for manual execution
if __name__ == "__main__":
    async def run_comprehensive_tests():
        """Run comprehensive LMDB persistence tests manually."""
        test_instance = TestComprehensiveLMDBPersistence()
        
        print("🧪 Running Comprehensive LMDB Persistence Tests...\n")
        
        try:
            import tempfile
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
                
                # Test basic persistence
                print("1. Testing basic CRUD operations...")
                await pipeline_template_repo.save(sample_template)
                loaded = await pipeline_template_repo.find_by_id(sample_template.id)
                assert loaded is not None
                assert loaded.name == sample_template.name
                print("✅ Basic CRUD operations successful")
                
                # Test complex data structures
                print("2. Testing complex data structure persistence...")
                await test_instance.test_complex_data_structures_persistence(pipeline_template_repo)
                print("✅ Complex data structure persistence successful")
                
                # Test performance
                print("3. Testing performance benchmarks...")
                await test_instance.test_repository_performance_benchmarks(pipeline_template_repo)
                print("✅ Performance benchmarks successful")
                
                # Test workspace isolation
                print("4. Testing workspace isolation...")
                await test_instance.test_workspace_isolation_comprehensive(temp_db_path, mock_workspace_manager)
                print("✅ Workspace isolation successful")
                
                print("\n🎉 All comprehensive LMDB persistence tests passed!")
                
        except Exception as e:
            print(f"❌ Comprehensive persistence test failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    asyncio.run(run_comprehensive_tests())