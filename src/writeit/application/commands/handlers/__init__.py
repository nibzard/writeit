"""Concrete Command Handlers.

This module contains the concrete implementations of command handlers
that execute the business logic for write operations.
"""

from .pipeline_template_handlers import (
    ConcreteCreatePipelineTemplateCommandHandler,
    ConcreteUpdatePipelineTemplateCommandHandler,
    ConcreteDeletePipelineTemplateCommandHandler,
    ConcretePublishPipelineTemplateCommandHandler,
    ConcreteValidatePipelineTemplateCommandHandler,
)

from .pipeline_execution_handlers import (
    ConcreteExecutePipelineCommandHandler,
    ConcreteCancelPipelineExecutionCommandHandler,
    ConcreteRetryPipelineExecutionCommandHandler,
    ConcreteStreamingPipelineExecutionCommandHandler,
)

from .workspace_handlers import (
    ConcreteCreateWorkspaceCommandHandler,
    ConcreteSwitchWorkspaceCommandHandler,
    ConcreteDeleteWorkspaceCommandHandler,
    ConcreteConfigureWorkspaceCommandHandler,
    ConcreteInitializeWorkspaceCommandHandler,
    ConcreteArchiveWorkspaceCommandHandler,
    ConcreteRestoreWorkspaceCommandHandler,
    ConcreteCreateWorkspaceTemplateCommandHandler,
    ConcreteApplyWorkspaceTemplateCommandHandler,
)

from .content_handlers import (
    ConcreteCreateTemplateCommandHandler,
    ConcreteUpdateTemplateCommandHandler,
    ConcreteDeleteTemplateCommandHandler,
    ConcreteValidateTemplateCommandHandler,
    ConcreteCreateStylePrimerCommandHandler,
    ConcreteCreateGeneratedContentCommandHandler,
)

__all__ = [
    # Pipeline Template Handlers
    "ConcreteCreatePipelineTemplateCommandHandler",
    "ConcreteUpdatePipelineTemplateCommandHandler",
    "ConcreteDeletePipelineTemplateCommandHandler",
    "ConcretePublishPipelineTemplateCommandHandler",
    "ConcreteValidatePipelineTemplateCommandHandler",
    
    # Pipeline Execution Handlers
    "ConcreteExecutePipelineCommandHandler",
    "ConcreteCancelPipelineExecutionCommandHandler",
    "ConcreteRetryPipelineExecutionCommandHandler",
    "ConcreteStreamingPipelineExecutionCommandHandler",
    
    # Workspace Handlers
    "ConcreteCreateWorkspaceCommandHandler",
    "ConcreteSwitchWorkspaceCommandHandler",
    "ConcreteDeleteWorkspaceCommandHandler",
    "ConcreteConfigureWorkspaceCommandHandler",
    "ConcreteInitializeWorkspaceCommandHandler",
    "ConcreteArchiveWorkspaceCommandHandler",
    "ConcreteRestoreWorkspaceCommandHandler",
    "ConcreteCreateWorkspaceTemplateCommandHandler",
    "ConcreteApplyWorkspaceTemplateCommandHandler",
    
    # Content Handlers
    "ConcreteCreateTemplateCommandHandler",
    "ConcreteUpdateTemplateCommandHandler",
    "ConcreteDeleteTemplateCommandHandler",
    "ConcreteValidateTemplateCommandHandler",
    "ConcreteCreateStylePrimerCommandHandler",
    "ConcreteCreateGeneratedContentCommandHandler",
]