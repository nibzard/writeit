"""Pipeline CQRS Commands.

Commands for write operations related to pipeline management,
execution, and lifecycle operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum

from ...shared.command import Command, CommandHandler, CommandResult
from ...domains.pipeline.value_objects import PipelineId, StepId, PipelineName
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.pipeline.entities import PipelineTemplate, PipelineRun


class PipelineExecutionMode(str, Enum):
    """Pipeline execution modes."""
    CLI = "cli"
    TUI = "tui" 
    API = "api"
    BACKGROUND = "background"


class PipelineSource(str, Enum):
    """Source of pipeline templates."""
    LOCAL = "local"
    WORKSPACE = "workspace"
    GLOBAL = "global"
    REMOTE = "remote"


# Commands for Pipeline Template Management

@dataclass(frozen=True)
class CreatePipelineTemplateCommand(Command):
    """Command to create a new pipeline template."""
    
    name: str = ""
    description: str = ""
    content: str = ""
    workspace_name: Optional[str] = None
    template_path: Optional[Path] = None
    validation_level: str = "strict"
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])


@dataclass(frozen=True)
class UpdatePipelineTemplateCommand(Command):
    """Command to update an existing pipeline template."""
    
    pipeline_id: PipelineId = None
    workspace_name: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    validation_level: str = "strict"


@dataclass(frozen=True)
class DeletePipelineTemplateCommand(Command):
    """Command to delete a pipeline template."""
    
    pipeline_id: PipelineId = None
    workspace_name: Optional[str] = None
    force: bool = False


@dataclass(frozen=True)
class PublishPipelineTemplateCommand(Command):
    """Command to publish a pipeline template."""
    
    pipeline_id: PipelineId = None
    workspace_name: Optional[str] = None
    target_scope: str = "workspace"  # workspace, global


@dataclass(frozen=True)
class ValidatePipelineTemplateCommand(Command):
    """Command to validate a pipeline template."""
    
    pipeline_id: Optional[PipelineId] = None
    content: Optional[str] = None
    template_path: Optional[Path] = None
    validation_level: str = "strict"


# Commands for Pipeline Execution

@dataclass(frozen=True)
class ExecutePipelineCommand(Command):
    """Command to execute a pipeline."""
    
    pipeline_name: str = ""
    workspace_name: Optional[str] = None
    source: PipelineSource = PipelineSource.WORKSPACE
    mode: PipelineExecutionMode = PipelineExecutionMode.CLI
    inputs: Optional[Dict[str, Any]] = None
    execution_options: Optional[Dict[str, Any]] = None
    template_path: Optional[Path] = None
    
    def __post_init__(self):
        if self.inputs is None:
            object.__setattr__(self, 'inputs', {})
        if self.execution_options is None:
            object.__setattr__(self, 'execution_options', {})


@dataclass(frozen=True)
class CancelPipelineExecutionCommand(Command):
    """Command to cancel a running pipeline execution."""
    
    run_id: str = ""
    reason: Optional[str] = None
    force: bool = False


@dataclass(frozen=True)
class RetryPipelineExecutionCommand(Command):
    """Command to retry a failed pipeline execution."""
    
    run_id: str = ""
    from_step: Optional[StepId] = None
    skip_failed_steps: bool = False
    execution_options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.execution_options is None:
            object.__setattr__(self, 'execution_options', {})


@dataclass(frozen=True)
class ResumePipelineExecutionCommand(Command):
    """Command to resume a paused pipeline execution."""
    
    run_id: str = ""
    execution_options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.execution_options is None:
            object.__setattr__(self, 'execution_options', {})


# Commands for Step Execution

@dataclass(frozen=True)
class ExecuteStepCommand(Command):
    """Command to execute a single pipeline step."""
    
    run_id: str = ""
    step_id: StepId = None
    inputs: Dict[str, Any] = None
    execution_options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.execution_options is None:
            object.__setattr__(self, 'execution_options', {})
        if self.inputs is None:
            object.__setattr__(self, 'inputs', {})


@dataclass(frozen=True)
class RetryStepExecutionCommand(Command):
    """Command to retry a failed step execution."""
    
    run_id: str = ""
    step_id: StepId = None
    attempt_number: int = 0
    execution_options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.execution_options is None:
            object.__setattr__(self, 'execution_options', {})


# Command Results

@dataclass(frozen=True)
class PipelineTemplateCommandResult(CommandResult):
    """Result of pipeline template command operations."""
    
    pipeline_id: Optional[PipelineId] = None
    template: Optional[PipelineTemplate] = None
    validation_errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            object.__setattr__(self, 'validation_errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


@dataclass(frozen=True)
class PipelineExecutionCommandResult(CommandResult):
    """Result of pipeline execution command operations."""
    
    run_id: Optional[str] = None
    pipeline_run: Optional[PipelineRun] = None
    execution_status: Optional[str] = None
    step_results: Optional[Dict[str, Any]] = None
    execution_metrics: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


# Command Handler Interfaces

class PipelineTemplateCommandHandler(CommandHandler[PipelineTemplateCommandResult], ABC):
    """Base interface for pipeline template command handlers."""
    pass


class PipelineExecutionCommandHandler(CommandHandler[PipelineExecutionCommandResult], ABC):
    """Base interface for pipeline execution command handlers."""
    pass


# Specific Command Handlers

class CreatePipelineTemplateCommandHandler(PipelineTemplateCommandHandler):
    """Handler for creating pipeline templates."""
    
    @abstractmethod
    async def handle(self, command: CreatePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template creation."""
        pass


class UpdatePipelineTemplateCommandHandler(PipelineTemplateCommandHandler):
    """Handler for updating pipeline templates."""
    
    @abstractmethod
    async def handle(self, command: UpdatePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template updates."""
        pass


class DeletePipelineTemplateCommandHandler(PipelineTemplateCommandHandler):
    """Handler for deleting pipeline templates."""
    
    @abstractmethod
    async def handle(self, command: DeletePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template deletion."""
        pass


class ValidatePipelineTemplateCommandHandler(PipelineTemplateCommandHandler):
    """Handler for validating pipeline templates."""
    
    @abstractmethod
    async def handle(self, command: ValidatePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template validation."""
        pass


class PublishPipelineTemplateCommandHandler(PipelineTemplateCommandHandler):
    """Handler for publishing pipeline templates."""
    
    @abstractmethod
    async def handle(self, command: PublishPipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template publishing."""
        pass


class ExecutePipelineCommandHandler(PipelineExecutionCommandHandler):
    """Handler for executing pipelines."""
    
    @abstractmethod
    async def handle(self, command: ExecutePipelineCommand) -> PipelineExecutionCommandResult:
        """Handle pipeline execution."""
        pass


class CancelPipelineExecutionCommandHandler(PipelineExecutionCommandHandler):
    """Handler for canceling pipeline executions."""
    
    @abstractmethod
    async def handle(self, command: CancelPipelineExecutionCommand) -> PipelineExecutionCommandResult:
        """Handle pipeline execution cancellation."""
        pass


class RetryPipelineExecutionCommandHandler(PipelineExecutionCommandHandler):
    """Handler for retrying pipeline executions."""
    
    @abstractmethod
    async def handle(self, command: RetryPipelineExecutionCommand) -> PipelineExecutionCommandResult:
        """Handle pipeline execution retry."""
        pass


# Streaming Command Results for Real-time Updates

@dataclass(frozen=True)
class PipelineExecutionProgress:
    """Progress update for pipeline execution."""
    
    run_id: str
    current_step: Optional[StepId] = None
    step_progress: float = 0.0
    overall_progress: float = 0.0
    status_message: str = ""
    step_results: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())


class StreamingPipelineExecutionCommandHandler(CommandHandler[AsyncGenerator[PipelineExecutionProgress, None]], ABC):
    """Handler for streaming pipeline execution with real-time progress."""
    
    @abstractmethod
    async def handle(self, command: ExecutePipelineCommand) -> AsyncGenerator[PipelineExecutionProgress, None]:
        """Handle pipeline execution with streaming progress updates."""
        pass