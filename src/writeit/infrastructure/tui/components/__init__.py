"""TUI Components Package Initialization.

Provides modern TUI components for WriteIt with full DDD integration,
including pipeline execution, workspace management, template browsing,
and advanced monitoring interfaces.
"""

from .modern_tui import (
    ModernWriteItTUI,
    ModernPipelineRunnerScreen,
    run_modern_tui,
    
    # Message types
    TUIComponentMessage,
    PipelineExecutionStarted,
    PipelineExecutionProgress,
    PipelineExecutionCompleted,
    WorkspaceSwitched,
    TemplateSelected,
    
    # Data classes
    PipelineTemplateInfo,
    PipelineInputData,
    PipelineStepData,
)

from .specialized import (
    WorkspaceManagementScreen,
    TemplateBrowserScreen,
    ConfigurationScreen,
)

from .advanced_execution import (
    AdvancedPipelineExecutionScreen,
    ExecutionPhase,
    ExecutionMetrics,
    StepExecutionDetail,
)

# Re-export key classes for easier imports
__all__ = [
    # Main application
    "ModernWriteItTUI",
    "ModernPipelineRunnerScreen",
    "run_modern_tui",
    
    # Messages
    "TUIComponentMessage",
    "PipelineExecutionStarted",
    "PipelineExecutionProgress",
    "PipelineExecutionCompleted",
    "WorkspaceSwitched",
    "TemplateSelected",
    
    # Data structures
    "PipelineTemplateInfo",
    "PipelineInputData",
    "PipelineStepData",
    
    # Specialized screens
    "WorkspaceManagementScreen",
    "TemplateBrowserScreen",
    "ConfigurationScreen",
    
    # Advanced execution
    "AdvancedPipelineExecutionScreen",
    "ExecutionPhase",
    "ExecutionMetrics",
    "StepExecutionDetail",
]