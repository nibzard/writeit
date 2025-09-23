"""Pipeline execution service.

Provides core orchestration logic for executing pipeline templates,
managing step dependencies, coordinating execution flow, and handling
error recovery and state management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Set, Any, Optional, Callable, Awaitable, AsyncGenerator, Union
from enum import Enum
import asyncio
from datetime import datetime

from ..entities.pipeline_template import PipelineTemplate, PipelineStepTemplate
from ..entities.pipeline_run import PipelineRun
from ..entities.pipeline_step import StepExecution, PipelineStep
from ..value_objects.step_id import StepId
from ..value_objects.execution_status import ExecutionStatus, StepExecutionStatus, PipelineExecutionStatus
from ..value_objects.prompt_template import PromptTemplate
from ..repositories.pipeline_template_repository import PipelineTemplateRepository
from ..repositories.pipeline_run_repository import PipelineRunRepository
from ..repositories.step_execution_repository import StepExecutionRepository


class ExecutionMode(str, Enum):
    """Pipeline execution modes."""
    SEQUENTIAL = "sequential"  # Execute steps one by one
    PARALLEL = "parallel"  # Execute independent steps in parallel
    ADAPTIVE = "adaptive"  # Automatically choose based on dependencies


class StepExecutionStrategy(str, Enum):
    """Step execution strategies."""
    IMMEDIATE = "immediate"  # Execute step immediately when ready
    BATCH = "batch"  # Batch steps for efficient execution
    STREAMING = "streaming"  # Stream results as they become available


@dataclass
class ExecutionContext:
    """Context for pipeline execution."""
    pipeline_run: PipelineRun
    template: PipelineTemplate
    mode: ExecutionMode
    strategy: StepExecutionStrategy
    variables: Dict[str, Any]  # Available variables for template rendering
    step_executions: Dict[str, StepExecution]  # Current step execution states
    completed_steps: Set[str]  # Steps that have completed
    failed_steps: Set[str]  # Steps that have failed
    cancelled: bool = False
    paused: bool = False
    
    def is_step_ready(self, step_key: str) -> bool:
        """Check if a step is ready to execute."""
        if step_key in self.completed_steps or step_key in self.failed_steps:
            return False
            
        step_template = self.template.steps[step_key]
        
        # Check if all dependencies are completed
        for dep in step_template.depends_on:
            if dep.value not in self.completed_steps:
                return False
                
        return True
    
    def get_ready_steps(self) -> List[str]:
        """Get all steps that are ready to execute."""
        ready_steps = []
        for step_key in self.template.steps:
            if self.is_step_ready(step_key):
                step_execution = self.step_executions.get(step_key)
                if step_execution is None or step_execution.is_pending:
                    ready_steps.append(step_key)
        return ready_steps
    
    def get_parallel_ready_steps(self) -> List[str]:
        """Get steps that can run in parallel."""
        ready_steps = self.get_ready_steps()
        parallel_steps = []
        
        for step_key in ready_steps:
            step_template = self.template.steps[step_key]
            if step_template.parallel:
                parallel_steps.append(step_key)
                
        return parallel_steps
    
    def add_step_output(self, step_key: str, outputs: Dict[str, Any]) -> None:
        """Add step outputs to available variables."""
        if "steps" not in self.variables:
            self.variables["steps"] = {}
        self.variables["steps"][step_key] = outputs
    
    def render_step_template(self, step_template: PipelineStepTemplate) -> str:
        """Render a step's prompt template with current variables."""
        return step_template.prompt_template.render(self.variables)


@dataclass
class ExecutionResult:
    """Result of pipeline or step execution."""
    success: bool
    outputs: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: Dict[str, int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        if self.tokens_used is None:
            self.tokens_used = {}
        if self.metadata is None:
            self.metadata = {}


class StepExecutor(ABC):
    """Abstract base class for step execution."""
    
    @abstractmethod
    async def execute_step(
        self,
        step_template: PipelineStepTemplate,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single pipeline step.
        
        Args:
            step_template: Step template to execute
            context: Execution context
            inputs: Step input values
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    def can_handle_step_type(self, step_type: str) -> bool:
        """Check if this executor can handle the given step type."""
        pass


class ExecutionEventType(str, Enum):
    """Types of execution events."""
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_PAUSED = "pipeline_paused"
    PIPELINE_RESUMED = "pipeline_resumed"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    PIPELINE_CANCELLED = "pipeline_cancelled"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_RETRYING = "step_retrying"
    STEP_SKIPPED = "step_skipped"
    VARIABLES_UPDATED = "variables_updated"


@dataclass
class ExecutionEvent:
    """Event during pipeline execution."""
    event_type: ExecutionEventType
    pipeline_run_id: str
    step_id: Optional[str] = None
    data: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self) -> None:
        if self.data is None:
            self.data = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PipelineExecutionService:
    """Service for orchestrating pipeline execution.
    
    Provides comprehensive pipeline execution capabilities including:
    - Step dependency resolution and ordering
    - Parallel and sequential execution modes
    - Error handling and retry logic
    - State management and persistence
    - Event streaming and progress tracking
    
    Examples:
        executor = PipelineExecutionService(
            template_repo=template_repo,
            run_repo=run_repo,
            step_repo=step_repo
        )
        
        # Execute pipeline
        async for event in executor.execute_pipeline(
            template_id=template_id,
            inputs=inputs,
            workspace_name=workspace
        ):
            print(f"Event: {event.event_type}")
    """
    
    def __init__(
        self,
        template_repository: PipelineTemplateRepository,
        run_repository: PipelineRunRepository,
        step_repository: StepExecutionRepository,
        step_executors: Optional[List[StepExecutor]] = None
    ) -> None:
        """Initialize execution service.
        
        Args:
            template_repository: Repository for pipeline templates
            run_repository: Repository for pipeline runs
            step_repository: Repository for step executions
            step_executors: List of step executors for different step types
        """
        self._template_repo = template_repository
        self._run_repo = run_repository
        self._step_repo = step_repository
        self._step_executors = step_executors or []
        self._default_execution_mode = ExecutionMode.ADAPTIVE
        self._default_execution_strategy = StepExecutionStrategy.STREAMING
        self._max_parallel_steps = 5
        self._step_timeout_seconds = 300  # 5 minutes
    
    async def execute_pipeline(
        self,
        template_id: str,
        inputs: Dict[str, Any],
        workspace_name: str,
        mode: Optional[ExecutionMode] = None,
        strategy: Optional[StepExecutionStrategy] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute a pipeline with given inputs.
        
        Args:
            template_id: Pipeline template identifier
            inputs: User-provided input values
            workspace_name: Workspace name
            mode: Execution mode (defaults to adaptive)
            strategy: Execution strategy (defaults to streaming)
            metadata: Additional metadata
            
        Yields:
            Execution events during pipeline execution
            
        Raises:
            ValueError: If template not found or inputs invalid
            RuntimeError: If execution fails
        """
        # Load template
        template = await self._template_repo.get_by_id(template_id, workspace_name)
        if not template:
            raise ValueError(f"Pipeline template '{template_id}' not found")
        
        # Validate inputs
        validation_errors = template.validate_inputs(inputs)
        if validation_errors:
            raise ValueError(f"Input validation failed: {validation_errors}")
        
        # Create pipeline run
        pipeline_run = PipelineRun.create(
            pipeline_id=template.id,
            workspace_name=workspace_name,
            inputs=inputs,
            metadata=metadata
        )
        
        # Start execution
        pipeline_run = pipeline_run.start()
        await self._run_repo.save(pipeline_run, workspace_name)
        
        # Send start event
        yield ExecutionEvent(
            event_type=ExecutionEventType.PIPELINE_STARTED,
            pipeline_run_id=pipeline_run.id,
            data={"template_id": template_id, "inputs": inputs}
        )
        
        try:
            # Execute pipeline
            async for event in self._execute_pipeline_internal(
                pipeline_run=pipeline_run,
                template=template,
                mode=mode or self._default_execution_mode,
                strategy=strategy or self._default_execution_strategy
            ):
                yield event
                
        except Exception as e:
            # Handle execution failure
            pipeline_run = pipeline_run.fail(str(e))
            await self._run_repo.save(pipeline_run, workspace_name)
            
            yield ExecutionEvent(
                event_type=ExecutionEventType.PIPELINE_FAILED,
                pipeline_run_id=pipeline_run.id,
                data={"error": str(e)}
            )
            raise
    
    async def pause_pipeline(self, run_id: str, workspace_name: str) -> None:
        """Pause pipeline execution.
        
        Args:
            run_id: Pipeline run identifier
            workspace_name: Workspace name
            
        Raises:
            ValueError: If pipeline run not found or not running
        """
        pipeline_run = await self._run_repo.get_by_id(run_id, workspace_name)
        if not pipeline_run:
            raise ValueError(f"Pipeline run '{run_id}' not found")
        
        if not pipeline_run.is_running:
            raise ValueError(f"Pipeline run '{run_id}' is not running")
        
        pipeline_run = pipeline_run.pause()
        await self._run_repo.save(pipeline_run, workspace_name)
    
    async def resume_pipeline(self, run_id: str, workspace_name: str) -> AsyncGenerator[ExecutionEvent, None]:
        """Resume paused pipeline execution.
        
        Args:
            run_id: Pipeline run identifier
            workspace_name: Workspace name
            
        Yields:
            Execution events during resumed execution
            
        Raises:
            ValueError: If pipeline run not found or not paused
        """
        pipeline_run = await self._run_repo.get_by_id(run_id, workspace_name)
        if not pipeline_run:
            raise ValueError(f"Pipeline run '{run_id}' not found")
        
        if pipeline_run.status.status != PipelineExecutionStatus.PAUSED:
            raise ValueError(f"Pipeline run '{run_id}' is not paused")
        
        # Load template
        template = await self._template_repo.get_by_id(str(pipeline_run.pipeline_id), workspace_name)
        if not template:
            raise ValueError(f"Pipeline template not found for run '{run_id}'")
        
        # Resume execution
        pipeline_run = pipeline_run.resume()
        await self._run_repo.save(pipeline_run, workspace_name)
        
        yield ExecutionEvent(
            event_type=ExecutionEventType.PIPELINE_RESUMED,
            pipeline_run_id=pipeline_run.id
        )
        
        # Continue execution from where it left off
        async for event in self._execute_pipeline_internal(
            pipeline_run=pipeline_run,
            template=template,
            mode=ExecutionMode.ADAPTIVE,
            strategy=StepExecutionStrategy.STREAMING,
            resume=True
        ):
            yield event
    
    async def cancel_pipeline(self, run_id: str, workspace_name: str) -> None:
        """Cancel pipeline execution.
        
        Args:
            run_id: Pipeline run identifier
            workspace_name: Workspace name
            
        Raises:
            ValueError: If pipeline run not found
        """
        pipeline_run = await self._run_repo.get_by_id(run_id, workspace_name)
        if not pipeline_run:
            raise ValueError(f"Pipeline run '{run_id}' not found")
        
        pipeline_run = pipeline_run.cancel()
        await self._run_repo.save(pipeline_run, workspace_name)
    
    async def get_execution_status(
        self,
        run_id: str,
        workspace_name: str
    ) -> Dict[str, Any]:
        """Get current execution status.
        
        Args:
            run_id: Pipeline run identifier
            workspace_name: Workspace name
            
        Returns:
            Current execution status and progress
            
        Raises:
            ValueError: If pipeline run not found
        """
        pipeline_run = await self._run_repo.get_by_id(run_id, workspace_name)
        if not pipeline_run:
            raise ValueError(f"Pipeline run '{run_id}' not found")
        
        # Get step executions
        step_executions = await self._step_repo.get_by_pipeline_run_id(run_id, workspace_name)
        
        # Calculate progress
        total_steps = len(step_executions)
        completed_steps = len([s for s in step_executions if s.is_completed])
        failed_steps = len([s for s in step_executions if s.is_failed])
        
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "run_id": run_id,
            "status": str(pipeline_run.status.status),
            "progress": progress,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "started_at": pipeline_run.started_at.isoformat() if pipeline_run.started_at else None,
            "duration": pipeline_run.duration,
            "total_tokens": pipeline_run.get_total_tokens(),
            "outputs": pipeline_run.outputs
        }
    
    def register_step_executor(self, executor: StepExecutor) -> None:
        """Register a step executor.
        
        Args:
            executor: Step executor to register
        """
        self._step_executors.append(executor)
    
    def _get_step_executor(self, step_type: str) -> Optional[StepExecutor]:
        """Get appropriate step executor for step type."""
        for executor in self._step_executors:
            if executor.can_handle_step_type(step_type):
                return executor
        return None
    
    async def _execute_pipeline_internal(
        self,
        pipeline_run: PipelineRun,
        template: PipelineTemplate,
        mode: ExecutionMode,
        strategy: StepExecutionStrategy,
        resume: bool = False
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Internal pipeline execution logic."""
        # Initialize execution context
        context = ExecutionContext(
            pipeline_run=pipeline_run,
            template=template,
            mode=mode,
            strategy=strategy,
            variables={
                "inputs": pipeline_run.inputs,
                "defaults": template.defaults,
                "steps": {}
            },
            step_executions={},
            completed_steps=set(),
            failed_steps=set()
        )
        
        # Load existing step executions if resuming
        if resume:
            existing_executions = await self._step_repo.get_by_pipeline_run_id(
                pipeline_run.id, pipeline_run.workspace_name
            )
            for execution in existing_executions:
                context.step_executions[execution.step_id.value] = execution
                if execution.is_completed:
                    context.completed_steps.add(execution.step_id.value)
                    context.add_step_output(execution.step_id.value, execution.outputs)
                elif execution.is_failed:
                    context.failed_steps.add(execution.step_id.value)
        
        try:
            # Execute based on mode
            if mode == ExecutionMode.SEQUENTIAL:
                async for event in self._execute_sequential(context):
                    yield event
            elif mode == ExecutionMode.PARALLEL:
                async for event in self._execute_parallel(context):
                    yield event
            else:  # ADAPTIVE
                async for event in self._execute_adaptive(context):
                    yield event
            
            # Complete pipeline
            pipeline_run = context.pipeline_run.complete(context.variables.get("steps", {}))
            await self._run_repo.save(pipeline_run, pipeline_run.workspace_name)
            
            yield ExecutionEvent(
                event_type=ExecutionEventType.PIPELINE_COMPLETED,
                pipeline_run_id=pipeline_run.id,
                data={"outputs": pipeline_run.outputs}
            )
            
        except Exception as e:
            # Pipeline execution failed
            pipeline_run = context.pipeline_run.fail(str(e))
            await self._run_repo.save(pipeline_run, pipeline_run.workspace_name)
            
            yield ExecutionEvent(
                event_type=ExecutionEventType.PIPELINE_FAILED,
                pipeline_run_id=pipeline_run.id,
                data={"error": str(e)}
            )
            raise
    
    async def _execute_sequential(self, context: ExecutionContext) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute steps sequentially."""
        execution_order = context.template.get_execution_order()
        
        for step_key in execution_order:
            if step_key in context.completed_steps:
                continue  # Skip already completed steps
                
            async for event in self._execute_step(context, step_key):
                yield event
                
            # Check if step failed and handle accordingly
            step_execution = context.step_executions.get(step_key)
            if step_execution and step_execution.is_failed:
                if not step_execution.can_retry:
                    raise RuntimeError(f"Step '{step_key}' failed: {step_execution.error_message}")
    
    async def _execute_parallel(self, context: ExecutionContext) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute steps in parallel where possible."""
        parallel_groups = context.template.get_parallel_groups()
        
        for group in parallel_groups:
            # Filter out already completed steps
            remaining_steps = [s for s in group if s not in context.completed_steps]
            
            if not remaining_steps:
                continue
            
            if len(remaining_steps) == 1:
                # Single step - execute normally
                async for event in self._execute_step(context, remaining_steps[0]):
                    yield event
            else:
                # Multiple steps - execute in parallel
                tasks = []
                for step_key in remaining_steps:
                    task = asyncio.create_task(self._execute_step_task(context, step_key))
                    tasks.append((step_key, task))
                
                # Wait for all steps to complete
                for step_key, task in tasks:
                    try:
                        events = await task
                        for event in events:
                            yield event
                    except Exception as e:
                        yield ExecutionEvent(
                            event_type=ExecutionEventType.STEP_FAILED,
                            pipeline_run_id=context.pipeline_run.id,
                            step_id=step_key,
                            data={"error": str(e)}
                        )
    
    async def _execute_adaptive(self, context: ExecutionContext) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute steps adaptively based on dependencies."""
        while len(context.completed_steps) < len(context.template.steps):
            ready_steps = context.get_ready_steps()
            
            if not ready_steps:
                # No ready steps - check if we're stuck
                remaining_steps = set(context.template.steps.keys()) - context.completed_steps - context.failed_steps
                if remaining_steps:
                    raise RuntimeError(f"No ready steps available, but {len(remaining_steps)} steps remain")
                break
            
            # Execute ready steps
            if len(ready_steps) == 1 or context.strategy == StepExecutionStrategy.IMMEDIATE:
                # Execute one step at a time
                step_key = ready_steps[0]
                async for event in self._execute_step(context, step_key):
                    yield event
            else:
                # Execute multiple steps in parallel (up to limit)
                parallel_steps = ready_steps[:self._max_parallel_steps]
                tasks = []
                
                for step_key in parallel_steps:
                    task = asyncio.create_task(self._execute_step_task(context, step_key))
                    tasks.append((step_key, task))
                
                # Wait for at least one step to complete
                done, pending = await asyncio.wait(
                    [task for _, task in tasks],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for step_key, task in tasks:
                    if task in done:
                        try:
                            events = await task
                            for event in events:
                                yield event
                        except Exception as e:
                            yield ExecutionEvent(
                                event_type=ExecutionEventType.STEP_FAILED,
                                pipeline_run_id=context.pipeline_run.id,
                                step_id=step_key,
                                data={"error": str(e)}
                            )
                
                # Cancel pending tasks
                for step_key, task in tasks:
                    if task in pending:
                        task.cancel()
    
    async def _execute_step_task(self, context: ExecutionContext, step_key: str) -> List[ExecutionEvent]:
        """Execute a step as an async task."""
        events = []
        async for event in self._execute_step(context, step_key):
            events.append(event)
        return events
    
    async def _execute_step(self, context: ExecutionContext, step_key: str) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute a single step."""
        step_template = context.template.steps[step_key]
        
        # Create or get step execution
        if step_key not in context.step_executions:
            step_execution = StepExecution.from_template(step_template)
            context.step_executions[step_key] = step_execution
        else:
            step_execution = context.step_executions[step_key]
        
        # Skip if already completed
        if step_execution.is_completed:
            return
        
        # Start step execution
        step_inputs = self._prepare_step_inputs(context, step_template)
        step_execution = step_execution.start(step_inputs)
        context.step_executions[step_key] = step_execution
        
        # Save step execution
        await self._step_repo.save(step_execution, context.pipeline_run.workspace_name)
        
        yield ExecutionEvent(
            event_type=ExecutionEventType.STEP_STARTED,
            pipeline_run_id=context.pipeline_run.id,
            step_id=step_key,
            data={"step_name": step_template.name, "inputs": step_inputs}
        )
        
        try:
            # Execute step
            executor = self._get_step_executor(step_template.type)
            if not executor:
                raise RuntimeError(f"No executor found for step type '{step_template.type}'")
            
            result = await asyncio.wait_for(
                executor.execute_step(step_template, context, step_inputs),
                timeout=self._step_timeout_seconds
            )
            
            # Complete step execution
            step_execution = step_execution.complete(result.outputs)
            
            # Add token usage
            for provider, tokens in result.tokens_used.items():
                step_execution = step_execution.add_token_usage(provider, tokens)
                context.pipeline_run = context.pipeline_run.add_token_usage(provider, tokens)
            
            context.step_executions[step_key] = step_execution
            context.completed_steps.add(step_key)
            context.add_step_output(step_key, result.outputs)
            
            # Save updated state
            await self._step_repo.save(step_execution, context.pipeline_run.workspace_name)
            await self._run_repo.save(context.pipeline_run, context.pipeline_run.workspace_name)
            
            yield ExecutionEvent(
                event_type=ExecutionEventType.STEP_COMPLETED,
                pipeline_run_id=context.pipeline_run.id,
                step_id=step_key,
                data={
                    "outputs": result.outputs,
                    "execution_time": result.execution_time,
                    "tokens_used": result.tokens_used
                }
            )
            
        except asyncio.TimeoutError:
            # Step timed out
            error_msg = f"Step '{step_key}' timed out after {self._step_timeout_seconds} seconds"
            step_execution = step_execution.fail(error_msg)
            context.step_executions[step_key] = step_execution
            context.failed_steps.add(step_key)
            
            await self._step_repo.save(step_execution, context.pipeline_run.workspace_name)
            
            yield ExecutionEvent(
                event_type=ExecutionEventType.STEP_FAILED,
                pipeline_run_id=context.pipeline_run.id,
                step_id=step_key,
                data={"error": error_msg}
            )
            
            # Try to retry if possible
            if step_execution.can_retry:
                yield ExecutionEvent(
                    event_type=ExecutionEventType.STEP_RETRYING,
                    pipeline_run_id=context.pipeline_run.id,
                    step_id=step_key,
                    data={"retry_count": step_execution.retry_count + 1}
                )
                
                step_execution = step_execution.retry()
                context.step_executions[step_key] = step_execution
                context.failed_steps.discard(step_key)
                
                # Retry execution
                async for event in self._execute_step(context, step_key):
                    yield event
            else:
                raise RuntimeError(error_msg)
                
        except Exception as e:
            # Step failed
            error_msg = str(e)
            step_execution = step_execution.fail(error_msg)
            context.step_executions[step_key] = step_execution
            context.failed_steps.add(step_key)
            
            await self._step_repo.save(step_execution, context.pipeline_run.workspace_name)
            
            yield ExecutionEvent(
                event_type=ExecutionEventType.STEP_FAILED,
                pipeline_run_id=context.pipeline_run.id,
                step_id=step_key,
                data={"error": error_msg}
            )
            
            # Try to retry if possible
            if step_execution.can_retry:
                yield ExecutionEvent(
                    event_type=ExecutionEventType.STEP_RETRYING,
                    pipeline_run_id=context.pipeline_run.id,
                    step_id=step_key,
                    data={"retry_count": step_execution.retry_count + 1}
                )
                
                step_execution = step_execution.retry()
                context.step_executions[step_key] = step_execution
                context.failed_steps.discard(step_key)
                
                # Retry execution
                async for event in self._execute_step(context, step_key):
                    yield event
            else:
                raise RuntimeError(error_msg)
    
    def _prepare_step_inputs(self, context: ExecutionContext, step_template: PipelineStepTemplate) -> Dict[str, Any]:
        """Prepare inputs for step execution."""
        inputs = {
            "rendered_prompt": context.render_step_template(step_template),
            "step_type": step_template.type,
            "model_preference": step_template.model_preference,
            "selection_prompt": step_template.selection_prompt,
            "variables": context.variables
        }
        
        # Add step-specific configuration
        if hasattr(step_template, 'ui_config'):
            inputs["ui_config"] = step_template.ui_config
        if hasattr(step_template, 'validation'):
            inputs["validation"] = step_template.validation
        if hasattr(step_template, 'retry_config'):
            inputs["retry_config"] = step_template.retry_config
            
        return inputs
