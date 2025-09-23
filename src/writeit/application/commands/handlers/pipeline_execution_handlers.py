"""Concrete implementations of Pipeline Execution command handlers.

These handlers implement the business logic for pipeline execution operations,
coordinating between domain services, repositories, and the event bus.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio

from ....shared.command import CommandHandler
from ....shared.events import EventBus
from ....domains.pipeline.entities import PipelineRun, PipelineTemplate
from ....domains.pipeline.repositories import PipelineRunRepository, PipelineTemplateRepository
from ....domains.pipeline.services import PipelineExecutionService, PipelineValidationService
from ....domains.pipeline.value_objects import PipelineId, PipelineName, StepId
from ....domains.workspace.value_objects import WorkspaceName
from ....domains.pipeline.events import (
    PipelineExecutionStarted, 
    PipelineExecutionCompleted, 
    PipelineExecutionFailed,
    PipelineExecutionCancelled,
    StepExecutionStarted,
    StepExecutionCompleted,
    StepExecutionFailed
)

from ..pipeline_commands import (
    ExecutePipelineCommand,
    CancelPipelineExecutionCommand,
    RetryPipelineExecutionCommand,
    ResumePipelineExecutionCommand,
    ExecuteStepCommand,
    RetryStepExecutionCommand,
    PipelineExecutionCommandResult,
    PipelineExecutionProgress,
    ExecutePipelineCommandHandler,
    CancelPipelineExecutionCommandHandler,
    RetryPipelineExecutionCommandHandler,
    StreamingPipelineExecutionCommandHandler,
    PipelineSource,
    PipelineExecutionMode,
)

logger = logging.getLogger(__name__)


class ConcretePipelineExecutionCommandHandler(CommandHandler[PipelineExecutionCommandResult]):
    """Base class for concrete pipeline execution command handlers."""
    
    def __init__(
        self,
        run_repository: PipelineRunRepository,
        template_repository: PipelineTemplateRepository,
        execution_service: PipelineExecutionService,
        validation_service: PipelineValidationService,
        event_bus: EventBus,
    ):
        """Initialize handler with dependencies.
        
        Args:
            run_repository: Repository for pipeline runs
            template_repository: Repository for pipeline templates
            execution_service: Service for pipeline execution
            validation_service: Service for validation
            event_bus: Event bus for publishing domain events
        """
        self._run_repository = run_repository
        self._template_repository = template_repository
        self._execution_service = execution_service
        self._validation_service = validation_service
        self._event_bus = event_bus


class ConcreteExecutePipelineCommandHandler(
    ConcretePipelineExecutionCommandHandler,
    ExecutePipelineCommandHandler
):
    """Concrete handler for executing pipelines."""
    
    async def handle(self, command: ExecutePipelineCommand) -> PipelineExecutionCommandResult:
        """Handle pipeline execution."""
        logger.info(f"Executing pipeline: {command.pipeline_name}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find pipeline template
            template = await self._find_pipeline_template(
                command.pipeline_name, 
                command.source, 
                workspace_name,
                command.template_path
            )
            
            if not template:
                return PipelineExecutionCommandResult(
                    success=False,
                    message=f"Pipeline template '{command.pipeline_name}' not found",
                    errors=[f"Template '{command.pipeline_name}' not found in {command.source.value} scope"]
                )
            
            # Validate template before execution
            validation_result = await self._validation_service.validate_template_content(
                content=template.content,
                validation_level="runtime"
            )
            
            if not validation_result.is_valid:
                return PipelineExecutionCommandResult(
                    success=False,
                    message="Pipeline template validation failed",
                    errors=validation_result.errors,
                    warnings=validation_result.warnings
                )
            
            # Create pipeline run
            run_id = f"run-{uuid.uuid4().hex[:8]}"
            pipeline_run = PipelineRun.create(
                id=run_id,
                pipeline_id=template.id,
                pipeline_name=template.name,
                workspace_name=workspace_name,
                inputs=command.inputs,
                execution_options=command.execution_options,
                mode=command.mode
            )
            
            # Save pipeline run
            await self._run_repository.save(pipeline_run)
            
            # Publish execution started event
            started_event = PipelineExecutionStarted(
                run_id=run_id,
                pipeline_id=template.id,
                pipeline_name=template.name,
                workspace_name=workspace_name,
                mode=command.mode,
                inputs=command.inputs,
                started_at=datetime.now(),
                metadata={
                    "source": command.source.value,
                    "execution_options": command.execution_options
                }
            )
            await self._event_bus.publish(started_event)
            
            # Execute pipeline using domain service
            execution_result = await self._execution_service.execute_pipeline(
                pipeline_run=pipeline_run,
                template=template,
                inputs=command.inputs
            )
            
            # Update pipeline run with results
            updated_run = pipeline_run.complete_execution(
                results=execution_result.step_results,
                status=execution_result.status,
                metrics=execution_result.metrics
            )
            
            await self._run_repository.save(updated_run)
            
            # Publish completion event
            if execution_result.success:
                completed_event = PipelineExecutionCompleted(
                    run_id=run_id,
                    pipeline_id=template.id,
                    pipeline_name=template.name,
                    status=execution_result.status,
                    step_results=execution_result.step_results,
                    execution_metrics=execution_result.metrics,
                    completed_at=datetime.now()
                )
                await self._event_bus.publish(completed_event)
            else:
                failed_event = PipelineExecutionFailed(
                    run_id=run_id,
                    pipeline_id=template.id,
                    pipeline_name=template.name,
                    error_message=execution_result.error_message,
                    failed_step=execution_result.failed_step,
                    step_results=execution_result.step_results,
                    failed_at=datetime.now()
                )
                await self._event_bus.publish(failed_event)
            
            logger.info(f"Pipeline execution completed: {run_id}")
            
            return PipelineExecutionCommandResult(
                success=execution_result.success,
                message=execution_result.message,
                run_id=str(run_id),
                pipeline_run=updated_run,
                execution_status=execution_result.status,
                step_results=execution_result.step_results,
                execution_metrics=execution_result.metrics,
                errors=execution_result.errors,
                warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to execute pipeline: {e}", exc_info=True)
            return PipelineExecutionCommandResult(
                success=False,
                message=f"Failed to execute pipeline: {str(e)}",
                errors=[str(e)]
            )
    
    async def _find_pipeline_template(
        self, 
        pipeline_name: str, 
        source: PipelineSource,
        workspace_name: Optional[WorkspaceName],
        template_path: Optional[str] = None
    ) -> Optional[PipelineTemplate]:
        """Find pipeline template based on source and name."""
        
        # Parse pipeline name
        name = PipelineName.from_string(pipeline_name)
        
        if source == PipelineSource.LOCAL and template_path:
            # Load from local file
            try:
                from pathlib import Path
                content = Path(template_path).read_text(encoding='utf-8')
                
                # Create temporary template for execution
                return PipelineTemplate.create(
                    id=PipelineId.generate(),
                    name=name,
                    description="Local pipeline template",
                    content=content,
                    workspace_name=workspace_name
                )
            except Exception as e:
                logger.error(f"Failed to load local template: {e}")
                return None
        
        # Find in repository (workspace, global, etc.)
        return await self._template_repository.find_by_name(name)
    
    async def validate(self, command: ExecutePipelineCommand) -> list[str]:
        """Validate execute pipeline command."""
        errors = []
        
        # Validate required fields
        if not command.pipeline_name or not command.pipeline_name.strip():
            errors.append("Pipeline name is required")
        
        # Validate pipeline name format
        if command.pipeline_name:
            try:
                PipelineName.from_string(command.pipeline_name)
            except ValueError as e:
                errors.append(f"Invalid pipeline name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate template path for local source
        if command.source == PipelineSource.LOCAL:
            if not command.template_path:
                errors.append("Template path is required for local source")
            else:
                from pathlib import Path
                path = Path(command.template_path)
                if not path.exists():
                    errors.append(f"Template file does not exist: {command.template_path}")
                elif not path.is_file():
                    errors.append(f"Template path is not a file: {command.template_path}")
        
        return errors


class ConcreteCancelPipelineExecutionCommandHandler(
    ConcretePipelineExecutionCommandHandler,
    CancelPipelineExecutionCommandHandler
):
    """Concrete handler for canceling pipeline executions."""
    
    async def handle(self, command: CancelPipelineExecutionCommand) -> PipelineExecutionCommandResult:
        """Handle pipeline execution cancellation."""
        logger.info(f"Canceling pipeline execution: {command.run_id}")
        
        try:
            # Find pipeline run
            pipeline_run = await self._run_repository.find_by_id(command.run_id)
            
            if not pipeline_run:
                return PipelineExecutionCommandResult(
                    success=False,
                    message=f"Pipeline run not found: {command.run_id}",
                    errors=[f"Run with ID {command.run_id} does not exist"]
                )
            
            # Check if run can be cancelled
            if pipeline_run.is_completed:
                return PipelineExecutionCommandResult(
                    success=False,
                    message="Cannot cancel completed pipeline run",
                    errors=["Pipeline execution has already completed"]
                )
            
            # Cancel execution using domain service
            cancel_result = await self._execution_service.cancel_pipeline_execution(
                run_id=run_id,
                reason=command.reason,
                force=command.force
            )
            
            if not cancel_result.success:
                return PipelineExecutionCommandResult(
                    success=False,
                    message=cancel_result.message,
                    errors=cancel_result.errors
                )
            
            # Update pipeline run status
            cancelled_run = pipeline_run.cancel_execution(command.reason)
            await self._run_repository.save(cancelled_run)
            
            # Publish cancellation event
            cancelled_event = PipelineExecutionCancelled(
                run_id=run_id,
                pipeline_id=pipeline_run.pipeline_id,
                pipeline_name=pipeline_run.pipeline_name,
                reason=command.reason,
                cancelled_by=None,  # TODO: Extract from command context
                cancelled_at=datetime.now()
            )
            await self._event_bus.publish(cancelled_event)
            
            logger.info(f"Pipeline execution cancelled: {command.run_id}")
            
            return PipelineExecutionCommandResult(
                success=True,
                message="Pipeline execution cancelled successfully",
                run_id=command.run_id,
                pipeline_run=cancelled_run,
                execution_status="cancelled"
            )
            
        except Exception as e:
            logger.error(f"Failed to cancel pipeline execution: {e}", exc_info=True)
            return PipelineExecutionCommandResult(
                success=False,
                message=f"Failed to cancel pipeline execution: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CancelPipelineExecutionCommand) -> list[str]:
        """Validate cancel pipeline execution command."""
        errors = []
        
        if not command.run_id or not command.run_id.strip():
            errors.append("Run ID is required")
        
        # Validate run ID format
        if command.run_id:
            try:
                str(command.run_id)  # Run ID validation
            except ValueError as e:
                errors.append(f"Invalid run ID: {e}")
        
        return errors


class ConcreteRetryPipelineExecutionCommandHandler(
    ConcretePipelineExecutionCommandHandler,
    RetryPipelineExecutionCommandHandler
):
    """Concrete handler for retrying pipeline executions."""
    
    async def handle(self, command: RetryPipelineExecutionCommand) -> PipelineExecutionCommandResult:
        """Handle pipeline execution retry."""
        logger.info(f"Retrying pipeline execution: {command.run_id}")
        
        try:
            # Find original pipeline run
            original_run = await self._run_repository.find_by_id(command.run_id)
            
            if not original_run:
                return PipelineExecutionCommandResult(
                    success=False,
                    message=f"Pipeline run not found: {command.run_id}",
                    errors=[f"Run with ID {command.run_id} does not exist"]
                )
            
            # Find pipeline template
            template = await self._template_repository.find_by_id(original_run.pipeline_id)
            if not template:
                return PipelineExecutionCommandResult(
                    success=False,
                    message=f"Pipeline template not found: {original_run.pipeline_id}",
                    errors=[f"Template with ID {original_run.pipeline_id} does not exist"]
                )
            
            # Create new pipeline run for retry
            retry_run_id = f"run-{uuid.uuid4().hex[:8]}"
            retry_run = PipelineRun.create_retry(
                id=retry_run_id,
                original_run=original_run,
                from_step=command.from_step,
                skip_failed_steps=command.skip_failed_steps,
                execution_options=command.execution_options or {}
            )
            
            # Save retry run
            await self._run_repository.save(retry_run)
            
            # Execute retry using domain service
            execution_result = await self._execution_service.retry_pipeline_execution(
                original_run=original_run,
                retry_run=retry_run,
                template=template,
                from_step=command.from_step,
                skip_failed_steps=command.skip_failed_steps
            )
            
            # Update retry run with results
            updated_retry_run = retry_run.complete_execution(
                results=execution_result.step_results,
                status=execution_result.status,
                metrics=execution_result.metrics
            )
            
            await self._run_repository.save(updated_retry_run)
            
            # Publish completion event
            if execution_result.success:
                completed_event = PipelineExecutionCompleted(
                    run_id=retry_run_id,
                    pipeline_id=template.id,
                    pipeline_name=template.name,
                    status=execution_result.status,
                    step_results=execution_result.step_results,
                    execution_metrics=execution_result.metrics,
                    completed_at=datetime.now()
                )
                await self._event_bus.publish(completed_event)
            else:
                failed_event = PipelineExecutionFailed(
                    run_id=retry_run_id,
                    pipeline_id=template.id,
                    pipeline_name=template.name,
                    error_message=execution_result.error_message,
                    failed_step=execution_result.failed_step,
                    step_results=execution_result.step_results,
                    failed_at=datetime.now()
                )
                await self._event_bus.publish(failed_event)
            
            logger.info(f"Pipeline retry completed: {retry_run_id}")
            
            return PipelineExecutionCommandResult(
                success=execution_result.success,
                message=execution_result.message,
                run_id=str(retry_run_id),
                pipeline_run=updated_retry_run,
                execution_status=execution_result.status,
                step_results=execution_result.step_results,
                execution_metrics=execution_result.metrics,
                errors=execution_result.errors
            )
            
        except Exception as e:
            logger.error(f"Failed to retry pipeline execution: {e}", exc_info=True)
            return PipelineExecutionCommandResult(
                success=False,
                message=f"Failed to retry pipeline execution: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: RetryPipelineExecutionCommand) -> list[str]:
        """Validate retry pipeline execution command."""
        errors = []
        
        if not command.run_id or not command.run_id.strip():
            errors.append("Run ID is required")
        
        # Validate run ID format
        if command.run_id:
            try:
                lambda x: str(x)  # RunId is just a string(command.run_id)
            except ValueError as e:
                errors.append(f"Invalid run ID: {e}")
        
        # Validate from_step if provided
        if command.from_step:
            try:
                StepId.from_string(str(command.from_step))
            except ValueError as e:
                errors.append(f"Invalid step ID: {e}")
        
        return errors


class ConcreteStreamingPipelineExecutionCommandHandler(
    ConcretePipelineExecutionCommandHandler,
    StreamingPipelineExecutionCommandHandler
):
    """Concrete handler for streaming pipeline execution with real-time progress."""
    
    async def handle(self, command: ExecutePipelineCommand) -> AsyncGenerator[PipelineExecutionProgress, None]:
        """Handle pipeline execution with streaming progress updates."""
        logger.info(f"Starting streaming execution of pipeline: {command.pipeline_name}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find pipeline template
            template = await self._find_pipeline_template(
                command.pipeline_name, 
                command.source, 
                workspace_name,
                command.template_path
            )
            
            if not template:
                yield PipelineExecutionProgress(
                    run_id="",
                    status_message=f"Pipeline template '{command.pipeline_name}' not found",
                    overall_progress=0.0
                )
                return
            
            # Create pipeline run
            run_id = f"run-{uuid.uuid4().hex[:8]}"
            pipeline_run = PipelineRun.create(
                id=run_id,
                pipeline_id=template.id,
                pipeline_name=template.name,
                workspace_name=workspace_name,
                inputs=command.inputs,
                execution_options=command.execution_options,
                mode=command.mode
            )
            
            # Save pipeline run
            await self._run_repository.save(pipeline_run)
            
            # Yield initial progress
            yield PipelineExecutionProgress(
                run_id=str(run_id),
                status_message="Pipeline execution started",
                overall_progress=0.0
            )
            
            # Publish execution started event
            started_event = PipelineExecutionStarted(
                run_id=run_id,
                pipeline_id=template.id,
                pipeline_name=template.name,
                workspace_name=workspace_name,
                mode=command.mode,
                inputs=command.inputs,
                started_at=datetime.now(),
                metadata={
                    "source": command.source.value,
                    "execution_options": command.execution_options
                }
            )
            await self._event_bus.publish(started_event)
            
            # Execute pipeline with streaming updates
            total_steps = len(template.steps)
            step_results = {}
            
            for i, step in enumerate(template.steps):
                step_progress = i / total_steps
                
                # Yield step start progress
                yield PipelineExecutionProgress(
                    run_id=str(run_id),
                    current_step=step.id,
                    step_progress=0.0,
                    overall_progress=step_progress,
                    status_message=f"Executing step: {step.name}",
                    step_results=step_results
                )
                
                # Execute step
                try:
                    step_result = await self._execution_service.execute_step(
                        step=step,
                        pipeline_run=pipeline_run,
                        inputs=command.inputs,
                        previous_results=step_results
                    )
                    
                    step_results[str(step.id)] = step_result
                    
                    # Yield step completion progress
                    yield PipelineExecutionProgress(
                        run_id=str(run_id),
                        current_step=step.id,
                        step_progress=1.0,
                        overall_progress=(i + 1) / total_steps,
                        status_message=f"Completed step: {step.name}",
                        step_results=step_results
                    )
                    
                except Exception as step_error:
                    logger.error(f"Step execution failed: {step_error}")
                    
                    # Yield error progress
                    yield PipelineExecutionProgress(
                        run_id=str(run_id),
                        current_step=step.id,
                        step_progress=0.0,
                        overall_progress=step_progress,
                        status_message=f"Step failed: {step.name} - {str(step_error)}",
                        step_results=step_results
                    )
                    
                    # Update pipeline run with failure
                    failed_run = pipeline_run.fail_execution(
                        error_message=str(step_error),
                        failed_step=step.id,
                        step_results=step_results
                    )
                    await self._run_repository.save(failed_run)
                    
                    # Publish failure event
                    failed_event = PipelineExecutionFailed(
                        run_id=run_id,
                        pipeline_id=template.id,
                        pipeline_name=template.name,
                        error_message=str(step_error),
                        failed_step=step.id,
                        step_results=step_results,
                        failed_at=datetime.now()
                    )
                    await self._event_bus.publish(failed_event)
                    return
            
            # Update pipeline run with success
            completed_run = pipeline_run.complete_execution(
                results=step_results,
                status="completed",
                metrics={"total_steps": total_steps, "execution_time": "unknown"}
            )
            await self._run_repository.save(completed_run)
            
            # Publish completion event
            completed_event = PipelineExecutionCompleted(
                run_id=run_id,
                pipeline_id=template.id,
                pipeline_name=template.name,
                status="completed",
                step_results=step_results,
                execution_metrics={"total_steps": total_steps},
                completed_at=datetime.now()
            )
            await self._event_bus.publish(completed_event)
            
            # Yield final progress
            yield PipelineExecutionProgress(
                run_id=str(run_id),
                overall_progress=1.0,
                status_message="Pipeline execution completed successfully",
                step_results=step_results
            )
            
            logger.info(f"Streaming pipeline execution completed: {run_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute streaming pipeline: {e}", exc_info=True)
            yield PipelineExecutionProgress(
                run_id="",
                status_message=f"Pipeline execution failed: {str(e)}",
                overall_progress=0.0
            )
    
    async def _find_pipeline_template(
        self, 
        pipeline_name: str, 
        source: PipelineSource,
        workspace_name: Optional[WorkspaceName],
        template_path: Optional[str] = None
    ) -> Optional[PipelineTemplate]:
        """Find pipeline template based on source and name."""
        
        # Parse pipeline name
        name = PipelineName.from_string(pipeline_name)
        
        if source == PipelineSource.LOCAL and template_path:
            # Load from local file
            try:
                from pathlib import Path
                content = Path(template_path).read_text(encoding='utf-8')
                
                # Create temporary template for execution
                return PipelineTemplate.create(
                    id=PipelineId.generate(),
                    name=name,
                    description="Local pipeline template",
                    content=content,
                    workspace_name=workspace_name
                )
            except Exception as e:
                logger.error(f"Failed to load local template: {e}")
                return None
        
        # Find in repository (workspace, global, etc.)
        return await self._template_repository.find_by_name(name)