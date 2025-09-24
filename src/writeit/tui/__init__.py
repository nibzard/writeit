# ABOUTME: WriteIt Textual UI components
# ABOUTME: Interactive terminal user interface for pipeline execution

# Legacy TUI (requires llm dependency)
# from .pipeline_runner import run_pipeline_tui

# Modern TUI with DDD integration
from .modern_pipeline_runner import run_modern_pipeline_tui, ModernPipelineRunnerApp, TUIExecutionConfig
from .template_browser_editor import (
    run_template_browser_editor,
    TemplateBrowserEditorApp,
    TemplateEditorConfig,
    TemplateEditorMode,
    ContentType
)
from .workspace_switcher import (
    run_workspace_switcher,
    WorkspaceSwitcherApp,
    WorkspaceSwitcherConfig,
    WorkspaceAction,
    WorkspaceInfo,
    WorkspaceSelected,
    WorkspaceCreated,
    WorkspaceDeleted
)
from .configuration_interface import (
    run_configuration_interface,
    ConfigurationInterfaceApp,
    ConfigurationInterfaceConfig,
    ConfigAction,
    ConfigurationEntry,
    ConfigurationSelected,
    ConfigurationUpdated,
    ConfigurationReset
)

__all__ = [
    # "run_pipeline_tui",  # Commented out due to external dependency
    "run_modern_pipeline_tui", 
    "ModernPipelineRunnerApp",
    "TUIExecutionConfig",
    "run_template_browser_editor",
    "TemplateBrowserEditorApp",
    "TemplateEditorConfig",
    "TemplateEditorMode",
    "ContentType",
    "run_workspace_switcher",
    "WorkspaceSwitcherApp",
    "WorkspaceSwitcherConfig",
    "WorkspaceAction",
    "WorkspaceInfo",
    "WorkspaceSelected",
    "WorkspaceCreated",
    "WorkspaceDeleted",
    "run_configuration_interface",
    "ConfigurationInterfaceApp",
    "ConfigurationInterfaceConfig",
    "ConfigAction",
    "ConfigurationEntry",
    "ConfigurationSelected",
    "ConfigurationUpdated",
    "ConfigurationReset"
]
