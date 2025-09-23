"""Command handler registration for dependency injection container.

This module provides functions to register all CQRS command handlers
with the dependency injection container.
"""

from typing import Type, Dict, Any
from ...shared.dependencies.container import Container, ServiceLifetime
from ...shared.dependencies.registry import ServiceRegistry

from .handlers.pipeline_execution_handlers import (
    ConcreteExecutePipelineCommandHandler,
    ConcreteCancelPipelineExecutionCommandHandler,
    ConcreteRetryPipelineExecutionCommandHandler,
    ConcreteStopPipelineCommandHandler,
    ConcreteStreamingPipelineExecutionCommandHandler,
)
from .handlers.pipeline_template_handlers import (
    ConcreteCreatePipelineTemplateCommandHandler,
    ConcreteUpdatePipelineTemplateCommandHandler,
    ConcreteDeletePipelineTemplateCommandHandler,
    ConcretePublishPipelineTemplateCommandHandler,
    ConcreteValidatePipelineTemplateCommandHandler,
)
from .handlers.workspace_handlers import (
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
from .handlers.content_handlers import (
    ConcreteCreateTemplateCommandHandler,
    ConcreteUpdateTemplateCommandHandler,
    ConcreteDeleteTemplateCommandHandler,
    ConcreteValidateTemplateCommandHandler,
    ConcreteCreateStylePrimerCommandHandler,
    ConcreteUpdateStylePrimerCommandHandler,
    ConcreteDeleteStylePrimerCommandHandler,
    ConcreteCreateGeneratedContentCommandHandler,
    ConcreteUpdateGeneratedContentCommandHandler,
    ConcreteDeleteGeneratedContentCommandHandler,
    ConcreteValidateContentCommandHandler,
    ConcretePublishTemplateCommandHandler,
    ConcreteDeprecateTemplateCommandHandler,
)

from .pipeline_commands import (
    ExecutePipelineCommandHandler,
    CancelPipelineExecutionCommandHandler,
    RetryPipelineExecutionCommandHandler,
    StopPipelineCommandHandler,
    StreamingPipelineExecutionCommandHandler,
    CreatePipelineTemplateCommandHandler,
    UpdatePipelineTemplateCommandHandler,
    DeletePipelineTemplateCommandHandler,
    PublishPipelineTemplateCommandHandler,
    ValidatePipelineTemplateCommandHandler,
)

from .workspace_commands import (
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
)


def register_command_handlers(container: Container) -> None:
    """Register all CQRS command handlers with the dependency injection container.
    
    Args:
        container: The dependency injection container to register handlers with
    """
    # Pipeline Execution Command Handlers
    container.register_transient(
        ExecutePipelineCommandHandler,
        ConcreteExecutePipelineCommandHandler
    )
    
    container.register_transient(
        CancelPipelineExecutionCommandHandler,
        ConcreteCancelPipelineExecutionCommandHandler
    )
    
    container.register_transient(
        RetryPipelineExecutionCommandHandler,
        ConcreteRetryPipelineExecutionCommandHandler
    )
    
    container.register_transient(
        StopPipelineCommandHandler,
        ConcreteStopPipelineCommandHandler
    )
    
    container.register_transient(
        StreamingPipelineExecutionCommandHandler,
        ConcreteStreamingPipelineExecutionCommandHandler
    )
    
    # Pipeline Template Command Handlers
    container.register_transient(
        CreatePipelineTemplateCommandHandler,
        ConcreteCreatePipelineTemplateCommandHandler
    )
    
    container.register_transient(
        UpdatePipelineTemplateCommandHandler,
        ConcreteUpdatePipelineTemplateCommandHandler
    )
    
    container.register_transient(
        DeletePipelineTemplateCommandHandler,
        ConcreteDeletePipelineTemplateCommandHandler
    )
    
    container.register_transient(
        PublishPipelineTemplateCommandHandler,
        ConcretePublishPipelineTemplateCommandHandler
    )
    
    container.register_transient(
        ValidatePipelineTemplateCommandHandler,
        ConcreteValidatePipelineTemplateCommandHandler
    )
    
    # Workspace Command Handlers
    container.register_transient(
        CreateWorkspaceCommandHandler,
        ConcreteCreateWorkspaceCommandHandler
    )
    
    container.register_transient(
        SwitchWorkspaceCommandHandler,
        ConcreteSwitchWorkspaceCommandHandler
    )
    
    container.register_transient(
        DeleteWorkspaceCommandHandler,
        ConcreteDeleteWorkspaceCommandHandler
    )
    
    container.register_transient(
        ConfigureWorkspaceCommandHandler,
        ConcreteConfigureWorkspaceCommandHandler
    )
    
    container.register_transient(
        InitializeWorkspaceCommandHandler,
        ConcreteInitializeWorkspaceCommandHandler
    )
    
    container.register_transient(
        ArchiveWorkspaceCommandHandler,
        ConcreteArchiveWorkspaceCommandHandler
    )
    
    container.register_transient(
        RestoreWorkspaceCommandHandler,
        ConcreteRestoreWorkspaceCommandHandler
    )
    
    container.register_transient(
        CreateWorkspaceTemplateCommandHandler,
        ConcreteCreateWorkspaceTemplateCommandHandler
    )
    
    container.register_transient(
        ApplyWorkspaceTemplateCommandHandler,
        ConcreteApplyWorkspaceTemplateCommandHandler
    )
    
    # Content Command Handlers
    container.register_transient(
        CreateTemplateCommandHandler,
        ConcreteCreateTemplateCommandHandler
    )
    
    container.register_transient(
        UpdateTemplateCommandHandler,
        ConcreteUpdateTemplateCommandHandler
    )
    
    container.register_transient(
        DeleteTemplateCommandHandler,
        ConcreteDeleteTemplateCommandHandler
    )
    
    container.register_transient(
        ValidateTemplateCommandHandler,
        ConcreteValidateTemplateCommandHandler
    )
    
    container.register_transient(
        CreateStylePrimerCommandHandler,
        ConcreteCreateStylePrimerCommandHandler
    )
    
    container.register_transient(
        UpdateStylePrimerCommandHandler,
        ConcreteUpdateStylePrimerCommandHandler
    )
    
    container.register_transient(
        DeleteStylePrimerCommandHandler,
        ConcreteDeleteStylePrimerCommandHandler
    )
    
    container.register_transient(
        CreateGeneratedContentCommandHandler,
        ConcreteCreateGeneratedContentCommandHandler
    )
    
    container.register_transient(
        UpdateGeneratedContentCommandHandler,
        ConcreteUpdateGeneratedContentCommandHandler
    )
    
    container.register_transient(
        DeleteGeneratedContentCommandHandler,
        ConcreteDeleteGeneratedContentCommandHandler
    )
    
    container.register_transient(
        ValidateContentCommandHandler,
        ConcreteValidateContentCommandHandler
    )
    
    container.register_transient(
        PublishTemplateCommandHandler,
        ConcretePublishTemplateCommandHandler
    )
    
    container.register_transient(
        DeprecateTemplateCommandHandler,
        ConcreteDeprecateTemplateCommandHandler
    )


def get_command_handler_registrations() -> Dict[Type, Dict[str, Any]]:
    """Get all command handler registrations as a dictionary.
    
    Returns:
        Dictionary mapping command handler interfaces to their implementations
    """
    return {
        # Pipeline Execution Handlers
        ExecutePipelineCommandHandler: {
            'implementation': ConcreteExecutePipelineCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        CancelPipelineExecutionCommandHandler: {
            'implementation': ConcreteCancelPipelineExecutionCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        RetryPipelineExecutionCommandHandler: {
            'implementation': ConcreteRetryPipelineExecutionCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        StopPipelineCommandHandler: {
            'implementation': ConcreteStopPipelineCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        StreamingPipelineExecutionCommandHandler: {
            'implementation': ConcreteStreamingPipelineExecutionCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        
        # Pipeline Template Handlers
        CreatePipelineTemplateCommandHandler: {
            'implementation': ConcreteCreatePipelineTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        UpdatePipelineTemplateCommandHandler: {
            'implementation': ConcreteUpdatePipelineTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        DeletePipelineTemplateCommandHandler: {
            'implementation': ConcreteDeletePipelineTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        PublishPipelineTemplateCommandHandler: {
            'implementation': ConcretePublishPipelineTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        ValidatePipelineTemplateCommandHandler: {
            'implementation': ConcreteValidatePipelineTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        
        # Workspace Handlers
        CreateWorkspaceCommandHandler: {
            'implementation': ConcreteCreateWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        SwitchWorkspaceCommandHandler: {
            'implementation': ConcreteSwitchWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        DeleteWorkspaceCommandHandler: {
            'implementation': ConcreteDeleteWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        ConfigureWorkspaceCommandHandler: {
            'implementation': ConcreteConfigureWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        InitializeWorkspaceCommandHandler: {
            'implementation': ConcreteInitializeWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        ArchiveWorkspaceCommandHandler: {
            'implementation': ConcreteArchiveWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        RestoreWorkspaceCommandHandler: {
            'implementation': ConcreteRestoreWorkspaceCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        CreateWorkspaceTemplateCommandHandler: {
            'implementation': ConcreteCreateWorkspaceTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        ApplyWorkspaceTemplateCommandHandler: {
            'implementation': ConcreteApplyWorkspaceTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        
        # Content Handlers
        CreateTemplateCommandHandler: {
            'implementation': ConcreteCreateTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        UpdateTemplateCommandHandler: {
            'implementation': ConcreteUpdateTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        DeleteTemplateCommandHandler: {
            'implementation': ConcreteDeleteTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        ValidateTemplateCommandHandler: {
            'implementation': ConcreteValidateTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        CreateStylePrimerCommandHandler: {
            'implementation': ConcreteCreateStylePrimerCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        UpdateStylePrimerCommandHandler: {
            'implementation': ConcreteUpdateStylePrimerCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        DeleteStylePrimerCommandHandler: {
            'implementation': ConcreteDeleteStylePrimerCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        CreateGeneratedContentCommandHandler: {
            'implementation': ConcreteCreateGeneratedContentCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        UpdateGeneratedContentCommandHandler: {
            'implementation': ConcreteUpdateGeneratedContentCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        DeleteGeneratedContentCommandHandler: {
            'implementation': ConcreteDeleteGeneratedContentCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        ValidateContentCommandHandler: {
            'implementation': ConcreteValidateContentCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        PublishTemplateCommandHandler: {
            'implementation': ConcretePublishTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
        DeprecateTemplateCommandHandler: {
            'implementation': ConcreteDeprecateTemplateCommandHandler,
            'lifetime': ServiceLifetime.TRANSIENT
        },
    }