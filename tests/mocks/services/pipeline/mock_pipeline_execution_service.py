"""Mock implementation of PipelineExecutionService for testing."""

from typing import Dict, List, Any, Optional, AsyncGenerator, Callable, Awaitable
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from writeit.domains.pipeline.services.pipeline_execution_service import (
    PipelineExecutionService,
    ExecutionMode,
    ExecutionContext,
    ExecutionResult,
    StepExecutionResult,
    ExecutionOptions
)
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.entities.pipeline_step import StepExecution
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus


class MockPipelineExecutionService(PipelineExecutionService):
    """Mock implementation of PipelineExecutionService.
    
    Provides configurable execution behavior for testing pipeline
    execution scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock execution service."""
        self._mock = AsyncMock()
        self._execution_results: Dict[str, ExecutionResult] = {}
        self._step_results: Dict[str, StepExecutionResult] = {}
        self._should_fail = False
        self._execution_delay = 0.0
        self._progress_callbacks: List[Callable] = []
        
    def configure_execution_result(self, run_id: str, result: ExecutionResult) -> None:
        """Configure execution result for specific run."""
        self._execution_results[run_id] = result
        
    def configure_step_result(self, step_id: str, result: StepExecutionResult) -> None:
        """Configure step execution result."""
        self._step_results[step_id] = result
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if execution should fail."""
        self._should_fail = should_fail
        
    def configure_delay(self, delay_seconds: float) -> None:
        """Configure execution delay for testing timing."""
        self._execution_delay = delay_seconds
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._execution_results.clear()
        self._step_results.clear()
        self._should_fail = False
        self._execution_delay = 0.0
        self._progress_callbacks.clear()
        self._mock.reset_mock()
        
    @property
    def mock(self) -> AsyncMock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def execute_pipeline(
        self, 
        template: PipelineTemplate, 
        inputs: Dict[str, Any],
        options: Optional[ExecutionOptions] = None
    ) -> AsyncGenerator[ExecutionResult, None]:
        """Execute pipeline template."""
        await self._mock.execute_pipeline(template, inputs, options)
        
        # Simulate execution delay
        if self._execution_delay > 0:
            import asyncio
            await asyncio.sleep(self._execution_delay)
            
        run_id = str(template.id.value)
        
        # Return configured result if available
        if run_id in self._execution_results:
            yield self._execution_results[run_id]
            return
            
        # Create mock execution result
        if self._should_fail:
            result = ExecutionResult(
                run_id=run_id,
                status=ExecutionStatus.FAILED,
                error="Mock execution error",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                step_results=[]
            )
        else:
            result = ExecutionResult(
                run_id=run_id,
                status=ExecutionStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                step_results=[]
            )
            
        yield result
        
    async def execute_step(
        self,
        step: StepExecution,
        context: ExecutionContext
    ) -> StepExecutionResult:
        """Execute individual step."""
        await self._mock.execute_step(step, context)
        
        step_id = str(step.step_id.value)
        
        # Return configured result if available
        if step_id in self._step_results:
            return self._step_results[step_id]
            
        # Create mock step result
        if self._should_fail:
            return StepExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                error="Mock step error",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                output=None
            )
        else:
            return StepExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                output=f"Mock output for step {step_id}"
            )
            
    async def prepare_execution_context(
        self,
        template: PipelineTemplate,
        inputs: Dict[str, Any]
    ) -> ExecutionContext:
        """Prepare execution context."""
        await self._mock.prepare_execution_context(template, inputs)
        
        return ExecutionContext(
            template=template,
            inputs=inputs,
            variables={},
            step_outputs={},
            execution_mode=ExecutionMode.SEQUENTIAL
        )
        
    async def validate_execution_preconditions(
        self,
        template: PipelineTemplate,
        inputs: Dict[str, Any]
    ) -> List[str]:
        """Validate execution preconditions."""
        await self._mock.validate_execution_preconditions(template, inputs)
        
        if self._should_fail:
            return ["Mock precondition error"]
        return []
        
    async def estimate_execution_time(
        self,
        template: PipelineTemplate,
        inputs: Dict[str, Any]
    ) -> float:
        """Estimate execution time in seconds."""
        await self._mock.estimate_execution_time(template, inputs)
        return self._execution_delay or 10.0
        
    async def cancel_execution(self, run_id: str) -> bool:
        """Cancel running execution."""
        await self._mock.cancel_execution(run_id)
        return True
        
    async def pause_execution(self, run_id: str) -> bool:
        """Pause running execution."""
        await self._mock.pause_execution(run_id)
        return True
        
    async def resume_execution(self, run_id: str) -> bool:
        """Resume paused execution."""
        await self._mock.resume_execution(run_id)
        return True
        
    async def get_execution_progress(self, run_id: str) -> Dict[str, Any]:
        """Get execution progress."""
        await self._mock.get_execution_progress(run_id)
        
        return {
            "run_id": run_id,
            "status": "running" if not self._should_fail else "failed",
            "progress": 0.5,
            "current_step": "mock-step",
            "completed_steps": 1,
            "total_steps": 2
        }
