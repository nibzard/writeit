"""Modern TUI Entry Point for WriteIt.

Provides a modern, DDD-integrated TUI application that leverages the new
architecture while maintaining backward compatibility with existing features.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from ..infrastructure.tui.components import ModernWriteItTUI, run_modern_tui
from ..infrastructure.tui.integration import TUIRunner, create_tui_runner
from ..infrastructure.tui.context import TUIContext, TUIContextManager, TUIMode
from ..shared.dependencies.container import create_container


async def run_modern_writeit_tui(workspace_name: str = "default") -> None:
    """Run the modern WriteIt TUI application.
    
    Args:
        workspace_name: Name of the workspace to use
        
    This function creates the necessary container, initializes the TUI context,
    and runs the modern TUI application with full DDD integration.
    """
    try:
        # Create the dependency injection container
        container = create_container()
        
        # Run the modern TUI
        await run_modern_tui(container, workspace_name)
        
    except KeyboardInterrupt:
        print("\n👋 WriteIt TUI closed by user")
    except Exception as e:
        print(f"❌ Error running WriteIt TUI: {e}")
        sys.exit(1)


async def run_advanced_pipeline_tui(pipeline_path: Path, workspace_name: str = "default") -> None:
    """Run the advanced pipeline execution TUI.
    
    Args:
        pipeline_path: Path to the pipeline configuration file
        workspace_name: Name of the workspace to use
        
    This function runs the advanced pipeline execution interface with
    real-time monitoring, step-by-step execution, and comprehensive metrics.
    """
    try:
        # Create the dependency injection container
        container = create_container()
        
        # Create TUI runner
        runner = create_tui_runner(container)
        
        # Run the pipeline TUI
        await runner.integration_service.run_pipeline_tui(pipeline_path, workspace_name)
        
    except KeyboardInterrupt:
        print("\n👋 Pipeline execution stopped by user")
    except Exception as e:
        print(f"❌ Error running pipeline TUI: {e}")
        sys.exit(1)


class WriteItTUIApp:
    """Main TUI application class for WriteIt.
    
    This class provides a high-level interface for running WriteIt's TUI
    applications with various modes and configurations.
    """
    
    def __init__(self, workspace_name: str = "default"):
        self.workspace_name = workspace_name
        self.container: Optional[object] = None
        self.runner: Optional[TUIRunner] = None
        self.context: Optional[TUIContext] = None
    
    async def initialize(self) -> None:
        """Initialize the TUI application with all dependencies."""
        try:
            # Create the dependency injection container
            self.container = create_container()
            
            # Create the TUI runner
            self.runner = create_tui_runner(self.container)
            
            # Initialize TUI context
            self.context = TUIContext(
                workspace_name=self.workspace_name,
                container=self.container,
                mode=TUIMode.PIPELINE,
            )
            
            # Set the context for the session
            TUIContextManager.set_context(self.context)
            
        except Exception as e:
            print(f"❌ Failed to initialize TUI: {e}")
            raise
    
    async def run_modern_interface(self) -> None:
        """Run the modern TUI interface with tabbed navigation."""
        if not self.runner:
            await self.initialize()
        
        await self.runner.run_modern_tui(self.workspace_name)
    
    async def run_pipeline_execution(self, pipeline_path: Path) -> None:
        """Run the advanced pipeline execution interface."""
        if not self.runner:
            await self.initialize()
        
        await self.runner.run_pipeline_tui(pipeline_path, self.workspace_name)
    
    async def run_workspace_management(self) -> None:
        """Run the workspace management interface."""
        if not self.runner:
            await self.initialize()
        
        # Set the context mode to workspace management
        if self.context:
            self.context.mode = TUIMode.WORKSPACE
        
        await self.runner.run_modern_tui(self.workspace_name)
    
    async def run_template_browser(self) -> None:
        """Run the template browser interface."""
        if not self.runner:
            await self.initialize()
        
        # Set the context mode to template browsing
        if self.context:
            self.context.mode = TUIMode.TEMPLATE
        
        await self.runner.run_modern_tui(self.workspace_name)
    
    async def run_configuration(self) -> None:
        """Run the configuration interface."""
        if not self.runner:
            await self.initialize()
        
        # Set the context mode to configuration
        if self.context:
            self.context.mode = TUIMode.CONFIGURATION
        
        await self.runner.run_modern_tui(self.workspace_name)
    
    def get_context(self) -> Optional[TUIContext]:
        """Get the current TUI context."""
        return self.context
    
    def get_workspace_name(self) -> str:
        """Get the current workspace name."""
        return self.workspace_name
    
    def set_workspace_name(self, workspace_name: str) -> None:
        """Set the workspace name."""
        self.workspace_name = workspace_name
        if self.context:
            self.context.workspace_name = workspace_name


# Convenience functions for easy access
def create_tui_app(workspace_name: str = "default") -> WriteItTUIApp:
    """Create a WriteIt TUI application instance.
    
    Args:
        workspace_name: Name of the workspace to use
        
    Returns:
        WriteItTUIApp instance
    """
    return WriteItTUIApp(workspace_name)


async def run_tui_app(app: WriteItTUIApp, mode: str = "modern") -> None:
    """Run a WriteIt TUI application in the specified mode.
    
    Args:
        app: WriteItTUIApp instance
        mode: TUI mode to run ('modern', 'workspace', 'template', 'config')
    """
    try:
        if mode == "modern":
            await app.run_modern_interface()
        elif mode == "workspace":
            await app.run_workspace_management()
        elif mode == "template":
            await app.run_template_browser()
        elif mode == "config":
            await app.run_configuration()
        else:
            print(f"❌ Unknown TUI mode: {mode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 WriteIt TUI closed by user")
    except Exception as e:
        print(f"❌ Error running TUI: {e}")
        sys.exit(1)


# Main entry point functions
def main_modern_tui(workspace_name: str = "default") -> None:
    """Main entry point for the modern TUI."""
    asyncio.run(run_modern_writeit_tui(workspace_name))


def main_pipeline_tui(pipeline_path: Path, workspace_name: str = "default") -> None:
    """Main entry point for the pipeline TUI."""
    asyncio.run(run_advanced_pipeline_tui(pipeline_path, workspace_name))


def main_workspace_tui(workspace_name: str = "default") -> None:
    """Main entry point for the workspace management TUI."""
    app = create_tui_app(workspace_name)
    asyncio.run(app.run_workspace_management())


def main_template_tui(workspace_name: str = "default") -> None:
    """Main entry point for the template browser TUI."""
    app = create_tui_app(workspace_name)
    asyncio.run(app.run_template_browser())


def main_config_tui(workspace_name: str = "default") -> None:
    """Main entry point for the configuration TUI."""
    app = create_tui_app(workspace_name)
    asyncio.run(app.run_configuration())


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        workspace = sys.argv[2] if len(sys.argv) > 2 else "default"
        
        if mode == "modern":
            main_modern_tui(workspace)
        elif mode == "workspace":
            main_workspace_tui(workspace)
        elif mode == "template":
            main_template_tui(workspace)
        elif mode == "config":
            main_config_tui(workspace)
        else:
            print("Usage: python modern_tui_entry.py [mode] [workspace]")
            print("Modes: modern, workspace, template, config")
            sys.exit(1)
    else:
        main_modern_tui()