"""TUI Integration Layer.

Provides integration between the new DDD-based TUI components and the existing
CLI entry points, ensuring backward compatibility while enabling modern TUI features.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from pathlib import Path
import asyncio
import sys

from .components import (
    ModernWriteItTUI,
    AdvancedPipelineExecutionScreen,
    PipelineTemplateInfo,
    ExecutionPhase,
)
from ...infrastructure.tui.context import (
    TUIContext,
    TUIMode,
    NavigationState,
    TUIContextManager,
)
from ...shared.dependencies.container import Container
from ...domains.workspace.value_objects import WorkspaceName


class TUIIntegrationService:
    """Service for integrating TUI components with the application."""
    
    def __init__(self, container: Container):
        self.container = container
        self.context: Optional[TUIContext] = None
    
    async def run_modern_tui(self, workspace_name: str = "default") -> None:
        """Run the modern TUI application."""
        # Initialize TUI context
        self.context = TUIContext(
            workspace_name=workspace_name,
            container=self.container,
            mode=TUIMode.PIPELINE,
            navigation_state=NavigationState.HOME,
        )
        
        # Set context for the session
        TUIContextManager.set_context(self.context)
        
        # Run the modern TUI
        await ModernWriteItTUI.run_async(
            app_class=ModernWriteItTUI,
            container=self.container,
            workspace_name=workspace_name,
        )
    
    async def run_pipeline_tui(self, pipeline_path: Path, workspace_name: str = "default") -> None:
        """Run the advanced pipeline execution TUI."""
        # Initialize TUI context
        self.context = TUIContext(
            workspace_name=workspace_name,
            container=self.container,
            mode=TUIMode.PIPELINE,
            navigation_state=NavigationState.EXECUTION,
        )
        
        # Set context for the session
        TUIContextManager.set_context(self.context)
        
        # Create a mock template info for the pipeline
        template_info = PipelineTemplateInfo(
            id=pipeline_path.stem,
            name=pipeline_path.stem.replace("-", " ").title(),
            description=f"Pipeline from {pipeline_path.name}",
            source="local",  # Would be determined from actual source
            workspace_name=workspace_name,
            created_at=None,  # Would get from file stats
            updated_at=None,  # Would get from file stats
            steps_count=3,  # Would get from actual pipeline
            estimated_duration=60,  # Would estimate from complexity
            tags=[],  # Would get from pipeline metadata
            metadata={"path": str(pipeline_path)},  # Additional metadata
        )
        
        # Create and run the advanced execution screen
        execution_screen = AdvancedPipelineExecutionScreen(self.context, template_info)
        
        # Create a minimal app to host the screen
        from textual.app import App
        
        class MinimalTUIApp(App):
            def compose(self):
                yield execution_screen
        
        app = MinimalTUIApp()
        await app.run_async()
    
    def get_current_context(self) -> Optional[TUIContext]:
        """Get the current TUI context."""
        return self.context
    
    def get_workspace_name(self) -> str:
        """Get the current workspace name."""
        if self.context:
            return self.context.workspace_name
        return "default"


class TUIRunner:
    """Runner class for launching TUI applications."""
    
    def __init__(self, container: Container):
        self.container = container
        self.integration_service = TUIIntegrationService(container)
    
    def run_modern_tui(self, workspace_name: str = "default") -> None:
        """Run the modern TUI application (sync wrapper)."""
        try:
            asyncio.run(self.integration_service.run_modern_tui(workspace_name))
        except KeyboardInterrupt:
            print("\n👋 TUI application closed by user")
        except Exception as e:
            print(f"❌ Error running TUI: {e}")
            sys.exit(1)
    
    def run_pipeline_tui(self, pipeline_path: Path, workspace_name: str = "default") -> None:
        """Run the pipeline TUI application (sync wrapper)."""
        try:
            asyncio.run(self.integration_service.run_pipeline_tui(pipeline_path, workspace_name))
        except KeyboardInterrupt:
            print("\n👋 Pipeline execution stopped by user")
        except Exception as e:
            print(f"❌ Error running pipeline TUI: {e}")
            sys.exit(1)


def create_tui_runner(container: Container) -> TUIRunner:
    """Create a TUI runner instance with the given container."""
    return TUIRunner(container)


# Legacy compatibility functions
def run_pipeline_tui_legacy(pipeline_path: Path, workspace_name: str = "default") -> None:
    """Legacy function for backward compatibility.
    
    This function provides a bridge between the old TUI system and the new DDD-based system.
    It creates the necessary container and runs the modern TUI.
    """
    try:
        # Import the container factory
        from ...shared.dependencies.service_manager import create_default_container
        
        # Create the container with all services
        container = create_default_container()
        
        # Create and run the TUI runner
        runner = create_tui_runner(container)
        runner.run_pipeline_tui(pipeline_path, workspace_name)
        
    except ImportError as e:
        print(f"❌ Failed to import dependencies: {e}")
        print("Please ensure WriteIt is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to run TUI: {e}")
        sys.exit(1)


def run_modern_tui_legacy(workspace_name: str = "default") -> None:
    """Legacy function for running the modern TUI.
    
    This function provides backward compatibility for launching the modern TUI
    without requiring the full DDD setup to be manually configured.
    """
    try:
        # Import the container factory
        from ...shared.dependencies.service_manager import create_default_container
        
        # Create the container with all services
        container = create_default_container()
        
        # Create and run the TUI runner
        runner = create_tui_runner(container)
        runner.run_modern_tui(workspace_name)
        
    except ImportError as e:
        print(f"❌ Failed to import dependencies: {e}")
        print("Please ensure WriteIt is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to run modern TUI: {e}")
        sys.exit(1)