"""Test data builders for WriteIt domain entities.

This module provides the Builder pattern implementation for creating
test data for all domain entities, value objects, and aggregates.

The builders allow for flexible, readable test data creation with
sensible defaults and easy customization for specific test scenarios.

Example:
    # Simple usage with defaults
    template = PipelineTemplateBuilder().build()
    
    # Customized usage
    template = (PipelineTemplateBuilder()
                .with_name("Custom Pipeline")
                .with_steps([
                    StepTemplateBuilder().with_name("Step 1").build(),
                    StepTemplateBuilder().with_name("Step 2").build()
                ])
                .build())
    
    # Factory methods for common scenarios
    template = PipelineTemplateBuilder.simple()
    template = PipelineTemplateBuilder.complex_with_dependencies()
"""

from .pipeline_builders import (
    PipelineTemplateBuilder,
    PipelineRunBuilder,
    PipelineStepTemplateBuilder,
    StepExecutionBuilder,
    PipelineInputBuilder,
)
from .workspace_builders import (
    WorkspaceBuilder,
    WorkspaceConfigurationBuilder,
)
from .content_builders import (
    TemplateBuilder,
    StylePrimerBuilder,
    GeneratedContentBuilder,
)
from .execution_builders import (
    LLMProviderBuilder,
    ExecutionContextBuilder,
    TokenUsageBuilder,
)
from .value_object_builders import (
    PipelineIdBuilder,
    StepIdBuilder,
    WorkspaceNameBuilder,
    TemplateNameBuilder,
    ModelNameBuilder,
    TokenCountBuilder,
)

__all__ = [
    # Pipeline builders
    "PipelineTemplateBuilder",
    "PipelineRunBuilder",
    "PipelineStepTemplateBuilder",
    "StepExecutionBuilder",
    "PipelineInputBuilder",

    # Workspace builders
    "WorkspaceBuilder",
    "WorkspaceConfigurationBuilder",

    # Content builders
    "TemplateBuilder",
    "StylePrimerBuilder",
    "GeneratedContentBuilder",

    # Execution builders
    "LLMProviderBuilder",
    "ExecutionContextBuilder",
    "TokenUsageBuilder",

    # Value object builders
    "PipelineIdBuilder",
    "StepIdBuilder",
    "WorkspaceNameBuilder",
    "TemplateNameBuilder",
    "ModelNameBuilder",
    "TokenCountBuilder",
]