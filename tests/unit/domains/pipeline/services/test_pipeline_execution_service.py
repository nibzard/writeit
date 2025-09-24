"""Unit tests for PipelineExecutionService.

Tests comprehensive domain service business logic including:
- Pipeline orchestration and execution flow
- Step dependency resolution and ordering
- Execution modes (sequential, parallel, adaptive)
- Error handling and retry logic
- State management and persistence
- Event streaming and progress tracking
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime, timedelta

from src.writeit.domains.pipeline.services.pipeline_execution_service import (
    PipelineExecutionService,
    ExecutionMode,
    StepExecutionStrategy,
    ExecutionContext,
    ExecutionResult,
    ExecutionEvent,
    ExecutionEventType,
    StepExecutor
)
from src.writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineStepTemplate
from src.writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from src.writeit.domains.pipeline.entities.pipeline_step import StepExecution
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from src.writeit.domains.pipeline.value_objects.execution_status import PipelineExecutionStatus, StepExecutionStatus
from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName

from tests.mocks import (
    MockPipelineTemplateRepository,
    MockPipelineRunRepository,
    MockStepExecutionRepository
)
from tests.builders.pipeline_builders import (
    PipelineTemplateBuilder,
    PipelineStepTemplateBuilder,
    PipelineRunBuilder,
    StepExecutionBuilder
)


class MockStepExecutor(StepExecutor):
    """Mock step executor for testing."""
    
    def __init__(self, step_types: List[str], execution_time: float = 0.1, success: bool = True):
        self._step_types = step_types
        self._execution_time = execution_time
        self._success = success
        self._call_count = 0
        self._executions = []
    
    async def execute_step(
        self,
        step_template: PipelineStepTemplate,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> ExecutionResult:
        """Mock step execution."""
        self._call_count += 1
        execution_data = {
            "step_template": step_template,
            "context": context,
            "inputs": inputs,
            "call_count": self._call_count
        }
        self._executions.append(execution_data)
        
        # Simulate execution time
        await asyncio.sleep(self._execution_time)
        
        if self._success:
            outputs = {
                "result": f"Output from {step_template.name}",
                "step_id": step_template.id.value,
                "rendered_prompt": inputs.get("rendered_prompt", "")
            }
            return ExecutionResult(
                success=True,
                outputs=outputs,
                execution_time=self._execution_time,
                tokens_used={"test_model": 100}
            )
        else:
            return ExecutionResult(
                success=False,
                outputs={},
                error_message=f"Mock execution failed for {step_template.name}",
                execution_time=self._execution_time
            )
    
    def can_handle_step_type(self, step_type: str) -> bool:
        """Check if this executor can handle the step type."""
        return step_type in self._step_types
    
    def reset(self):
        """Reset mock state."""
        self._call_count = 0
        self._executions.clear()


class TestExecutionContext:
    """Test ExecutionContext behavior."""
    
    def test_create_execution_context(self):
        """Test creating execution context."""
        pipeline_run = PipelineRunBuilder().build()
        template = PipelineTemplateBuilder().build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={"inputs": {"topic": "test"}},
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        assert context.pipeline_run == pipeline_run
        assert context.template == template
        assert context.mode == ExecutionMode.SEQUENTIAL
        assert context.strategy == StepExecutionStrategy.IMMEDIATE
        assert context.variables["inputs"]["topic"] == "test"
        assert len(context.step_executions) == 0
        assert len(context.completed_steps) == 0
        assert len(context.failed_steps) == 0
    
    def test_is_step_ready_simple(self):
        """Test step readiness with no dependencies."""
        pipeline_run = PipelineRunBuilder().build()
        step = PipelineStepTemplateBuilder().with_id("step1").build()
        template = PipelineTemplateBuilder().with_steps({"step1": step}).build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={},
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        assert context.is_step_ready("step1") is True
    
    def test_is_step_ready_with_dependencies(self):
        """Test step readiness with dependencies."""
        pipeline_run = PipelineRunBuilder().build()
        
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2
        }).build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={},
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        # step1 should be ready (no dependencies)
        assert context.is_step_ready("step1") is True
        
        # step2 should not be ready (depends on step1)
        assert context.is_step_ready("step2") is False
        
        # After step1 completes, step2 should be ready
        context.completed_steps.add("step1")
        assert context.is_step_ready("step2") is True
    
    def test_is_step_ready_already_completed(self):
        """Test that completed steps are not ready."""
        pipeline_run = PipelineRunBuilder().build()
        step = PipelineStepTemplateBuilder().with_id("step1").build()
        template = PipelineTemplateBuilder().with_steps({"step1": step}).build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={},
            step_executions={},
            completed_steps={"step1"},
            failed_steps=set()
        )
        
        assert context.is_step_ready("step1") is False
    
    def test_is_step_ready_failed(self):
        """Test that failed steps are not ready."""
        pipeline_run = PipelineRunBuilder().build()
        step = PipelineStepTemplateBuilder().with_id("step1").build()
        template = PipelineTemplateBuilder().with_steps({"step1": step}).build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={},
            step_executions={},
            completed_steps=set(),
            failed_steps={"step1"}
        )
        
        assert context.is_step_ready("step1") is False
    
    def test_get_ready_steps(self):
        """Test getting all ready steps."""
        pipeline_run = PipelineRunBuilder().build()
        
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={},
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        ready_steps = context.get_ready_steps()
        assert set(ready_steps) == {"step1", "step3"}
    
    def test_add_step_output(self):
        """Test adding step outputs to variables."""
        pipeline_run = PipelineRunBuilder().build()
        template = PipelineTemplateBuilder().build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={},
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        outputs = {"result": "test output", "tokens": 100}
        context.add_step_output("step1", outputs)
        
        assert "steps" in context.variables
        assert context.variables["steps"]["step1"] == outputs
    
    def test_render_step_template(self):
        """Test rendering step template with variables."""
        pipeline_run = PipelineRunBuilder().build()
        template = PipelineTemplateBuilder().build()
        
        step = PipelineStepTemplateBuilder().with_prompt_template(
            PromptTemplate("Generate content about {{ inputs.topic }} in {{ inputs.style }} style")
        ).build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={
                "inputs": {
                    "topic": "AI",
                    "style": "formal"
                }
            },
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        rendered = context.render_step_template(step)
        assert "Generate content about AI in formal style" == rendered


class TestExecutionResult:
    """Test ExecutionResult behavior."""
    
    def test_create_execution_result_success(self):
        """Test creating successful execution result."""
        outputs = {"result": "test output"}
        tokens_used = {"gpt-4": 150}
        metadata = {"timestamp": "2025-01-15T10:00:00"}
        
        result = ExecutionResult(
            success=True,
            outputs=outputs,
            execution_time=1.5,
            tokens_used=tokens_used,
            metadata=metadata
        )
        
        assert result.success is True
        assert result.outputs == outputs
        assert result.error_message is None
        assert result.execution_time == 1.5
        assert result.tokens_used == tokens_used
        assert result.metadata == metadata
    
    def test_create_execution_result_failure(self):
        """Test creating failed execution result."""
        result = ExecutionResult(
            success=False,
            outputs={},
            error_message="Execution failed",
            execution_time=0.5
        )
        
        assert result.success is False
        assert result.outputs == {}
        assert result.error_message == "Execution failed"
        assert result.execution_time == 0.5
        assert result.tokens_used == {}
        assert result.metadata == {}
    
    def test_execution_result_post_init_defaults(self):
        """Test that post_init sets default values."""
        result = ExecutionResult(success=True, outputs={})
        
        assert result.tokens_used == {}
        assert result.metadata == {}


class TestPipelineExecutionService:
    """Test PipelineExecutionService business logic."""
    
    def test_create_execution_service(self):
        """Test creating execution service."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        assert service._template_repo == template_repo
        assert service._run_repo == run_repo
        assert service._step_repo == step_repo
        assert len(service._step_executors) == 0
        assert service._default_execution_mode == ExecutionMode.ADAPTIVE
        assert service._default_execution_strategy == StepExecutionStrategy.STREAMING
        assert service._max_parallel_steps == 5
        assert service._step_timeout_seconds == 300
    
    def test_register_step_executor(self):
        """Test registering step executors."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        executor = MockStepExecutor(["llm_generate"])
        service.register_step_executor(executor)
        
        assert len(service._step_executors) == 1
        assert service._step_executors[0] == executor
    
    def test_get_step_executor(self):
        """Test getting appropriate step executor."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        llm_executor = MockStepExecutor(["llm_generate"])
        transform_executor = MockStepExecutor(["transform", "filter"])
        
        service.register_step_executor(llm_executor)
        service.register_step_executor(transform_executor)
        
        assert service._get_step_executor("llm_generate") == llm_executor
        assert service._get_step_executor("transform") == transform_executor
        assert service._get_step_executor("unknown") is None
    
    @pytest.mark.asyncio
    async def test_execute_simple_pipeline_success(self):
        """Test executing a simple single-step pipeline successfully."""
        # Setup repositories
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create test template
        step = PipelineStepTemplateBuilder().with_id("generate").with_name("Generate Content").build()
        template = PipelineTemplateBuilder().with_id("simple-pipeline").with_steps({"generate": step}).build()
        template_repo.add_template(template)
        
        # Create service with executor
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        executor = MockStepExecutor(["llm_generate"], success=True)
        service.register_step_executor(executor)
        
        # Execute pipeline
        events = []
        async for event in service.execute_pipeline(
            template_id="simple-pipeline",
            inputs={"topic": "test"},
            workspace_name="test-workspace"
        ):
            events.append(event)
        
        # Verify events
        event_types = [event.event_type for event in events]
        assert ExecutionEventType.PIPELINE_STARTED in event_types
        assert ExecutionEventType.STEP_STARTED in event_types
        assert ExecutionEventType.STEP_COMPLETED in event_types
        assert ExecutionEventType.PIPELINE_COMPLETED in event_types
        
        # Verify pipeline run was saved
        saved_runs = run_repo.get_all_runs()
        assert len(saved_runs) == 1
        
        pipeline_run = saved_runs[0]
        assert pipeline_run.status.status == PipelineExecutionStatus.COMPLETED
        assert "generate" in pipeline_run.outputs
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_template_not_found(self):
        """Test pipeline execution with missing template."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        with pytest.raises(ValueError, match="Pipeline template 'missing' not found"):
            async for _ in service.execute_pipeline(
                template_id="missing",
                inputs={},
                workspace_name="test-workspace"
            ):
                pass
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_input_validation_failure(self):
        """Test pipeline execution with invalid inputs."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template with required input
        step = PipelineStepTemplateBuilder().with_id("generate").build()
        template = (PipelineTemplateBuilder()
                   .with_id("validation-pipeline")
                   .with_required_input("topic", "text")
                   .with_steps({"generate": step})
                   .build())
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        with pytest.raises(ValueError, match="Input validation failed"):
            async for _ in service.execute_pipeline(
                template_id="validation-pipeline",
                inputs={},  # Missing required 'topic'
                workspace_name="test-workspace"
            ):
                pass
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_step_failure(self):
        """Test pipeline execution with step failure."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create test template
        step = PipelineStepTemplateBuilder().with_id("failing_step").build()
        template = PipelineTemplateBuilder().with_id("failing-pipeline").with_steps({"failing_step": step}).build()
        template_repo.add_template(template)
        
        # Create service with failing executor
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        executor = MockStepExecutor(["llm_generate"], success=False)
        service.register_step_executor(executor)
        
        # Execute pipeline - should fail
        events = []
        with pytest.raises(RuntimeError):
            async for event in service.execute_pipeline(
                template_id="failing-pipeline",
                inputs={},
                workspace_name="test-workspace"
            ):
                events.append(event)
        
        # Verify failure events
        event_types = [event.event_type for event in events]
        assert ExecutionEventType.PIPELINE_STARTED in event_types
        assert ExecutionEventType.STEP_FAILED in event_types
        assert ExecutionEventType.PIPELINE_FAILED in event_types
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_no_executor_for_step_type(self):
        """Test pipeline execution with no suitable executor."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template with custom step type
        step = PipelineStepTemplateBuilder().with_id("custom_step").with_type("custom_type").build()
        template = PipelineTemplateBuilder().with_id("custom-pipeline").with_steps({"custom_step": step}).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        # No executor registered for 'custom_type'
        with pytest.raises(RuntimeError, match="No executor found for step type 'custom_type'"):
            async for _ in service.execute_pipeline(
                template_id="custom-pipeline",
                inputs={},
                workspace_name="test-workspace"
            ):
                pass
    
    @pytest.mark.asyncio
    async def test_execute_multi_step_pipeline_with_dependencies(self):
        """Test executing multi-step pipeline with dependencies."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create multi-step template
        step1 = PipelineStepTemplateBuilder().with_id("step1").with_name("First Step").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_name("Second Step").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_name("Third Step").with_dependencies(["step2"]).build()
        
        template = PipelineTemplateBuilder().with_id("multi-step").with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        executor = MockStepExecutor(["llm_generate"], success=True, execution_time=0.01)
        service.register_step_executor(executor)
        
        # Execute pipeline
        events = []
        async for event in service.execute_pipeline(
            template_id="multi-step",
            inputs={},
            workspace_name="test-workspace",
            mode=ExecutionMode.SEQUENTIAL
        ):
            events.append(event)
        
        # Verify execution order through events
        step_started_events = [e for e in events if e.event_type == ExecutionEventType.STEP_STARTED]
        step_completed_events = [e for e in events if e.event_type == ExecutionEventType.STEP_COMPLETED]
        
        assert len(step_started_events) == 3
        assert len(step_completed_events) == 3
        
        # Verify order (should be step1, step2, step3)
        started_order = [e.step_id for e in step_started_events]
        assert started_order == ["step1", "step2", "step3"]
        
        # Verify all 3 steps were executed
        assert executor._call_count == 3
    
    @pytest.mark.asyncio
    async def test_pause_and_resume_pipeline(self):
        """Test pausing and resuming pipeline execution."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create test pipeline
        step = PipelineStepTemplateBuilder().with_id("step1").build()
        template = PipelineTemplateBuilder().with_id("pausable-pipeline").with_steps({"step1": step}).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        executor = MockStepExecutor(["llm_generate"], success=True)
        service.register_step_executor(executor)
        
        # Start execution (but don't complete it)
        pipeline_run = PipelineRun.create(
            pipeline_id=PipelineId("pausable-pipeline"),
            workspace_name="test-workspace",
            inputs={}
        )
        pipeline_run = pipeline_run.start()
        run_repo.save_run(pipeline_run)
        
        # Pause pipeline
        await service.pause_pipeline(pipeline_run.id, "test-workspace")
        
        # Verify it was paused
        paused_run = run_repo.get_run_by_id(pipeline_run.id)
        assert paused_run.status.status == PipelineExecutionStatus.PAUSED
        
        # Resume pipeline
        events = []
        async for event in service.resume_pipeline(pipeline_run.id, "test-workspace"):
            events.append(event)
        
        # Verify resume event
        event_types = [event.event_type for event in events]
        assert ExecutionEventType.PIPELINE_RESUMED in event_types
    
    @pytest.mark.asyncio
    async def test_pause_non_existent_pipeline(self):
        """Test pausing non-existent pipeline."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        with pytest.raises(ValueError, match="Pipeline run 'missing' not found"):
            await service.pause_pipeline("missing", "test-workspace")
    
    @pytest.mark.asyncio
    async def test_pause_non_running_pipeline(self):
        """Test pausing non-running pipeline."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create completed pipeline run
        pipeline_run = PipelineRun.create(
            pipeline_id=PipelineId("completed-pipeline"),
            workspace_name="test-workspace",
            inputs={}
        )
        pipeline_run = pipeline_run.complete({})
        run_repo.save_run(pipeline_run)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        with pytest.raises(ValueError, match="is not running"):
            await service.pause_pipeline(pipeline_run.id, "test-workspace")
    
    @pytest.mark.asyncio
    async def test_cancel_pipeline(self):
        """Test cancelling pipeline execution."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create running pipeline
        pipeline_run = PipelineRun.create(
            pipeline_id=PipelineId("cancellable-pipeline"),
            workspace_name="test-workspace",
            inputs={}
        )
        pipeline_run = pipeline_run.start()
        run_repo.save_run(pipeline_run)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        # Cancel pipeline
        await service.cancel_pipeline(pipeline_run.id, "test-workspace")
        
        # Verify it was cancelled
        cancelled_run = run_repo.get_run_by_id(pipeline_run.id)
        assert cancelled_run.status.status == PipelineExecutionStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self):
        """Test getting execution status."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create pipeline run with steps
        pipeline_run = PipelineRun.create(
            pipeline_id=PipelineId("status-pipeline"),
            workspace_name="test-workspace",
            inputs={"topic": "test"}
        )
        pipeline_run = pipeline_run.start()
        run_repo.save_run(pipeline_run)
        
        # Add some step executions
        step1 = StepExecutionBuilder().with_step_id("step1").completed().build()
        step2 = StepExecutionBuilder().with_step_id("step2").running().build()
        step3 = StepExecutionBuilder().with_step_id("step3").failed("Error").build()
        
        step_repo.save_step_execution(step1, pipeline_run.id)
        step_repo.save_step_execution(step2, pipeline_run.id)
        step_repo.save_step_execution(step3, pipeline_run.id)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        # Get execution status
        status = await service.get_execution_status(pipeline_run.id, "test-workspace")
        
        assert status["run_id"] == pipeline_run.id
        assert status["status"] == "running"
        assert status["total_steps"] == 3
        assert status["completed_steps"] == 1
        assert status["failed_steps"] == 1
        assert status["progress"] == pytest.approx(33.33, rel=0.01)
    
    @pytest.mark.asyncio
    async def test_step_timeout_handling(self):
        """Test handling step execution timeout."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template
        step = PipelineStepTemplateBuilder().with_id("slow_step").build()
        template = PipelineTemplateBuilder().with_id("timeout-pipeline").with_steps({"slow_step": step}).build()
        template_repo.add_template(template)
        
        # Create service with very short timeout
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        service._step_timeout_seconds = 0.1  # 100ms timeout
        
        # Register slow executor
        slow_executor = MockStepExecutor(["llm_generate"], execution_time=0.2, success=True)
        service.register_step_executor(slow_executor)
        
        # Execute pipeline - should timeout
        events = []
        with pytest.raises(RuntimeError, match="timed out"):
            async for event in service.execute_pipeline(
                template_id="timeout-pipeline",
                inputs={},
                workspace_name="test-workspace"
            ):
                events.append(event)
        
        # Verify timeout event was generated
        event_types = [event.event_type for event in events]
        assert ExecutionEventType.STEP_FAILED in event_types
        
        # Find the timeout event
        timeout_events = [e for e in events if e.event_type == ExecutionEventType.STEP_FAILED]
        assert any("timed out" in e.data.get("error", "") for e in timeout_events)
    
    @pytest.mark.asyncio
    async def test_step_retry_logic(self):
        """Test step retry logic on failure."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template
        step = PipelineStepTemplateBuilder().with_id("retry_step").build()
        template = PipelineTemplateBuilder().with_id("retry-pipeline").with_steps({"retry_step": step}).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        # Create executor that fails first time then succeeds
        class FailThenSucceedExecutor(StepExecutor):
            def __init__(self):
                self.attempt_count = 0
                
            async def execute_step(self, step_template, context, inputs) -> ExecutionResult:
                self.attempt_count += 1
                if self.attempt_count == 1:
                    return ExecutionResult(success=False, outputs={}, error_message="First attempt failed")
                else:
                    return ExecutionResult(success=True, outputs={"result": "success on retry"})
            
            def can_handle_step_type(self, step_type: str) -> bool:
                return step_type == "llm_generate"
        
        retry_executor = FailThenSucceedExecutor()
        service.register_step_executor(retry_executor)
        
        # Execute pipeline
        events = []
        async for event in service.execute_pipeline(
            template_id="retry-pipeline",
            inputs={},
            workspace_name="test-workspace"
        ):
            events.append(event)
        
        # Verify retry events
        event_types = [event.event_type for event in events]
        assert ExecutionEventType.STEP_FAILED in event_types
        assert ExecutionEventType.STEP_RETRYING in event_types
        assert ExecutionEventType.STEP_COMPLETED in event_types
        assert ExecutionEventType.PIPELINE_COMPLETED in event_types
        
        # Should have been called twice (fail + retry)
        assert retry_executor.attempt_count == 2
    
    @pytest.mark.asyncio 
    async def test_parallel_execution_mode(self):
        """Test parallel execution of independent steps."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template with parallel steps
        step1 = PipelineStepTemplateBuilder().with_id("parallel1").with_parallel(True).build()
        step2 = PipelineStepTemplateBuilder().with_id("parallel2").with_parallel(True).build()
        step3 = PipelineStepTemplateBuilder().with_id("sequential").with_dependencies(["parallel1", "parallel2"]).build()
        
        template = PipelineTemplateBuilder().with_id("parallel-pipeline").with_steps({
            "parallel1": step1,
            "parallel2": step2,
            "sequential": step3
        }).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        # Use executor with measurable execution time
        executor = MockStepExecutor(["llm_generate"], execution_time=0.05, success=True)
        service.register_step_executor(executor)
        
        # Execute in parallel mode
        start_time = datetime.now()
        events = []
        async for event in service.execute_pipeline(
            template_id="parallel-pipeline",
            inputs={},
            workspace_name="test-workspace",
            mode=ExecutionMode.PARALLEL
        ):
            events.append(event)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Verify all steps completed
        event_types = [event.event_type for event in events]
        completed_events = [e for e in events if e.event_type == ExecutionEventType.STEP_COMPLETED]
        assert len(completed_events) == 3
        
        # Execution time should be less than sequential (roughly 2 * step_time instead of 3 * step_time)
        # This is approximate due to async overhead
        assert execution_time < 0.2  # Should be much less than 3 * 0.05 = 0.15
    
    def test_prepare_step_inputs(self):
        """Test preparation of step inputs."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        
        # Create step template and context
        step_template = PipelineStepTemplateBuilder().with_prompt_template(
            PromptTemplate("Generate {{ inputs.topic }}")
        ).build()
        
        pipeline_run = PipelineRunBuilder().build()
        template = PipelineTemplateBuilder().build()
        
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.SEQUENTIAL,
            strategy=StepExecutionStrategy.IMMEDIATE,
            variables={
                "inputs": {"topic": "AI"},
                "defaults": {"model": "gpt-4"}
            },
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        # Prepare inputs
        inputs = service._prepare_step_inputs(context, step_template)
        
        assert "rendered_prompt" in inputs
        assert inputs["rendered_prompt"] == "Generate AI"
        assert inputs["step_type"] == "llm_generate"
        assert inputs["model_preference"] == step_template.model_preference
        assert inputs["variables"] == context.variables


class TestExecutionModesBehavior:
    """Test different execution mode behaviors."""
    
    @pytest.mark.asyncio
    async def test_sequential_mode_execution_order(self):
        """Test that sequential mode executes steps in order."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template with dependency chain: A -> B -> C
        step_a = PipelineStepTemplateBuilder().with_id("step_a").build()
        step_b = PipelineStepTemplateBuilder().with_id("step_b").with_dependencies(["step_a"]).build()
        step_c = PipelineStepTemplateBuilder().with_id("step_c").with_dependencies(["step_b"]).build()
        
        template = PipelineTemplateBuilder().with_id("sequential-test").with_steps({
            "step_a": step_a,
            "step_b": step_b, 
            "step_c": step_c
        }).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        executor = MockStepExecutor(["llm_generate"], success=True)
        service.register_step_executor(executor)
        
        # Execute in sequential mode
        events = []
        async for event in service.execute_pipeline(
            template_id="sequential-test",
            inputs={},
            workspace_name="test-workspace",
            mode=ExecutionMode.SEQUENTIAL
        ):
            events.append(event)
        
        # Extract step execution order
        start_events = [e for e in events if e.event_type == ExecutionEventType.STEP_STARTED]
        execution_order = [e.step_id for e in start_events]
        
        assert execution_order == ["step_a", "step_b", "step_c"]
    
    @pytest.mark.asyncio
    async def test_adaptive_mode_optimizes_execution(self):
        """Test that adaptive mode optimizes execution based on dependencies."""
        workspace_name = WorkspaceName("test-workspace")
        template_repo = MockPipelineTemplateRepository(workspace_name)
        run_repo = MockPipelineRunRepository(workspace_name)
        step_repo = MockStepExecutionRepository(workspace_name)
        
        # Create template with mixed dependencies
        # step_a and step_b can run in parallel
        # step_c depends on step_a only
        # step_d depends on both step_b and step_c
        step_a = PipelineStepTemplateBuilder().with_id("step_a").build()
        step_b = PipelineStepTemplateBuilder().with_id("step_b").build()
        step_c = PipelineStepTemplateBuilder().with_id("step_c").with_dependencies(["step_a"]).build()
        step_d = PipelineStepTemplateBuilder().with_id("step_d").with_dependencies(["step_b", "step_c"]).build()
        
        template = PipelineTemplateBuilder().with_id("adaptive-test").with_steps({
            "step_a": step_a,
            "step_b": step_b,
            "step_c": step_c,
            "step_d": step_d
        }).build()
        template_repo.add_template(template)
        
        service = PipelineExecutionService(
            template_repository=template_repo,
            run_repository=run_repo,
            step_repository=step_repo
        )
        executor = MockStepExecutor(["llm_generate"], execution_time=0.01, success=True)
        service.register_step_executor(executor)
        
        # Execute in adaptive mode
        events = []
        start_time = datetime.now()
        async for event in service.execute_pipeline(
            template_id="adaptive-test",
            inputs={},
            workspace_name="test-workspace",
            mode=ExecutionMode.ADAPTIVE
        ):
            events.append(event)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Verify all steps completed
        completed_events = [e for e in events if e.event_type == ExecutionEventType.STEP_COMPLETED]
        assert len(completed_events) == 4
        
        # Adaptive should be faster than pure sequential but may not be as fast as pure parallel
        # due to dependencies
        assert execution_time < 0.1  # Should be reasonable