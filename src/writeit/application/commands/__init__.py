"""Application Commands - CQRS Write Operations.

Commands represent write operations that change system state.
Each command has a corresponding handler that executes the business logic.
"""

from .pipeline_commands import (
    # Pipeline Template Commands
    CreatePipelineTemplateCommand,
    UpdatePipelineTemplateCommand,
    DeletePipelineTemplateCommand,
    PublishPipelineTemplateCommand,
    ValidatePipelineTemplateCommand,
    
    # Pipeline Execution Commands
    ExecutePipelineCommand,
    CancelPipelineExecutionCommand,
    RetryPipelineExecutionCommand,
    ResumePipelineExecutionCommand,
    
    # Step Execution Commands
    ExecuteStepCommand,
    RetryStepExecutionCommand,
    
    # Command Results
    PipelineTemplateCommandResult,
    PipelineExecutionCommandResult,
    PipelineExecutionProgress,
    
    # Command Handlers
    CreatePipelineTemplateCommandHandler,
    UpdatePipelineTemplateCommandHandler,
    DeletePipelineTemplateCommandHandler,
    PublishPipelineTemplateCommandHandler,
    ValidatePipelineTemplateCommandHandler,
    ExecutePipelineCommandHandler,
    CancelPipelineExecutionCommandHandler,
    RetryPipelineExecutionCommandHandler,
    StreamingPipelineExecutionCommandHandler,
    
    # Enums
    PipelineExecutionMode,
    PipelineSource,
)

from .workspace_commands import (
    # Workspace Management Commands
    CreateWorkspaceCommand,
    SwitchWorkspaceCommand,
    DeleteWorkspaceCommand,
    ConfigureWorkspaceCommand,
    
    # Workspace Lifecycle Commands
    InitializeWorkspaceCommand,
    ArchiveWorkspaceCommand,
    RestoreWorkspaceCommand,
    
    # Workspace Template Commands
    CreateWorkspaceTemplateCommand,
    ApplyWorkspaceTemplateCommand,
    
    # Command Results
    WorkspaceCommandResult,
    
    # Command Handlers
    CreateWorkspaceCommandHandler,
    SwitchWorkspaceCommandHandler,
    DeleteWorkspaceCommandHandler,
    ConfigureWorkspaceCommandHandler,
    InitializeWorkspaceCommandHandler,
    ArchiveWorkspaceCommandHandler,
    RestoreWorkspaceCommandHandler,
    CreateWorkspaceTemplateCommandHandler,
    ApplyWorkspaceTemplateCommandHandler,
)

from .content_commands import (
    # Template Management Commands
    CreateTemplateCommand,
    UpdateTemplateCommand,
    DeleteTemplateCommand,
    ValidateTemplateCommand,
    
    # Style Primer Commands
    CreateStylePrimerCommand,
    UpdateStylePrimerCommand,
    DeleteStylePrimerCommand,
    
    # Generated Content Commands
    CreateGeneratedContentCommand,
    UpdateGeneratedContentCommand,
    DeleteGeneratedContentCommand,
    ValidateContentCommand,
    
    # Template Publishing Commands
    PublishTemplateCommand,
    DeprecateTemplateCommand,
    
    # Command Results
    ContentCommandResult,
    
    # Command Handlers
    CreateTemplateCommandHandler,
    UpdateTemplateCommandHandler,
    DeleteTemplateCommandHandler,
    ValidateTemplateCommandHandler,
    CreateStylePrimerCommandHandler,
    UpdateStylePrimerCommandHandler,
    DeleteStylePrimerCommandHandler,
    CreateGeneratedContentCommandHandler,
    UpdateGeneratedContentCommandHandler,
    DeleteGeneratedContentCommandHandler,
    ValidateContentCommandHandler,
    PublishTemplateCommandHandler,
    DeprecateTemplateCommandHandler,
    
    # Enums
    ContentValidationLevel,
    TemplateScope,
)

__all__ = [
    # Pipeline Template Commands
    "CreatePipelineTemplateCommand",
    "UpdatePipelineTemplateCommand", 
    "DeletePipelineTemplateCommand",
    "PublishPipelineTemplateCommand",
    "ValidatePipelineTemplateCommand",
    
    # Pipeline Execution Commands
    "ExecutePipelineCommand",
    "CancelPipelineExecutionCommand",
    "RetryPipelineExecutionCommand",
    "ResumePipelineExecutionCommand",
    
    # Step Execution Commands
    "ExecuteStepCommand",
    "RetryStepExecutionCommand",
    
    # Command Results
    "PipelineTemplateCommandResult",
    "PipelineExecutionCommandResult",
    "PipelineExecutionProgress",
    
    # Command Handlers
    "CreatePipelineTemplateCommandHandler",
    "UpdatePipelineTemplateCommandHandler",
    "DeletePipelineTemplateCommandHandler", 
    "PublishPipelineTemplateCommandHandler",
    "ValidatePipelineTemplateCommandHandler",
    "ExecutePipelineCommandHandler",
    "CancelPipelineExecutionCommandHandler",
    "RetryPipelineExecutionCommandHandler",
    "StreamingPipelineExecutionCommandHandler",
    
    # Enums
    "PipelineExecutionMode",
    "PipelineSource",
    
    # Workspace Management Commands
    "CreateWorkspaceCommand",
    "SwitchWorkspaceCommand",
    "DeleteWorkspaceCommand",
    "ConfigureWorkspaceCommand",
    
    # Workspace Lifecycle Commands
    "InitializeWorkspaceCommand",
    "ArchiveWorkspaceCommand",
    "RestoreWorkspaceCommand",
    
    # Workspace Template Commands
    "CreateWorkspaceTemplateCommand",
    "ApplyWorkspaceTemplateCommand",
    
    # Workspace Command Results
    "WorkspaceCommandResult",
    
    # Workspace Command Handlers
    "CreateWorkspaceCommandHandler",
    "SwitchWorkspaceCommandHandler",
    "DeleteWorkspaceCommandHandler",
    "ConfigureWorkspaceCommandHandler",
    "InitializeWorkspaceCommandHandler",
    "ArchiveWorkspaceCommandHandler",
    "RestoreWorkspaceCommandHandler",
    "CreateWorkspaceTemplateCommandHandler",
    "ApplyWorkspaceTemplateCommandHandler",
    
    # Template Management Commands
    "CreateTemplateCommand",
    "UpdateTemplateCommand",
    "DeleteTemplateCommand",
    "ValidateTemplateCommand",
    
    # Style Primer Commands
    "CreateStylePrimerCommand",
    "UpdateStylePrimerCommand",
    "DeleteStylePrimerCommand",
    
    # Generated Content Commands
    "CreateGeneratedContentCommand",
    "UpdateGeneratedContentCommand",
    "DeleteGeneratedContentCommand",
    "ValidateContentCommand",
    
    # Template Publishing Commands
    "PublishTemplateCommand",
    "DeprecateTemplateCommand",
    
    # Content Command Results
    "ContentCommandResult",
    
    # Content Command Handlers
    "CreateTemplateCommandHandler",
    "UpdateTemplateCommandHandler",
    "DeleteTemplateCommandHandler",
    "ValidateTemplateCommandHandler",
    "CreateStylePrimerCommandHandler",
    "UpdateStylePrimerCommandHandler",
    "DeleteStylePrimerCommandHandler",
    "CreateGeneratedContentCommandHandler",
    "UpdateGeneratedContentCommandHandler",
    "DeleteGeneratedContentCommandHandler",
    "ValidateContentCommandHandler",
    "PublishTemplateCommandHandler",
    "DeprecateTemplateCommandHandler",
    
    # Content Enums
    "ContentValidationLevel",
    "TemplateScope",
]