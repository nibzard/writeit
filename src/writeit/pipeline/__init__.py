# ABOUTME: WriteIt pipeline execution engine
# ABOUTME: Orchestrates multi-step writing workflows with LLM interactions
# DEPRECATED: This module is deprecated. Use writeit.domains.pipeline and writeit.application.services instead.

import warnings
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

# Import from DDD structure
from writeit.domains.pipeline.entities import PipelineTemplate, PipelineRun
from writeit.domains.pipeline.value_objects import PipelineId, StepId
from writeit.application.services.pipeline_application_service import PipelineApplicationService
from writeit.application.services.execution_application_service import ExecutionApplicationService
from writeit.infrastructure.factory import InfrastructureFactory

# Issue deprecation warning
warnings.warn(
    "writeit.pipeline is deprecated. Use writeit.domains.pipeline and writeit.application.services instead.",
    DeprecationWarning,
    stacklevel=2
)

@dataclass
class ExecutionContext:
    """Context passed between pipeline steps."""
    
    pipeline_id: str
    run_id: str
    workspace_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_tracker: Optional[Any] = None

@dataclass
class StepResult:
    """Result of executing a single step."""
    
    step_key: str
    responses: List[str]
    selected_response: Optional[str] = None
    user_feedback: str = ""
    tokens_used: Dict[str, int] = field(default_factory=dict)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class PipelineExecutor:
    """Backward compatibility wrapper for PipelineExecutor."""
    
    def __init__(self, workspace=None, storage=None, workspace_name=None):
        # Create simple services for backward compatibility
        self._workspace = workspace
        self._storage = storage
        self._workspace_name = workspace_name
        self._pipeline_service = self._create_simple_pipeline_service()
        self._execution_service = self._create_simple_execution_service()
        
        # Fallback to legacy executor if parameters are provided (for backward compatibility)
        if workspace and storage and workspace_name:
            self._legacy_executor = self._create_legacy_executor()
        else:
            self._legacy_executor = None
    
    def execute_pipeline(self, pipeline_template: Any, workspace_name: str, inputs: Dict[str, Any]) -> List[StepResult]:
        """Execute a pipeline with backward compatibility."""
        # Use legacy executor if available (for backward compatibility with tests)
        if self._legacy_executor:
            return self._legacy_executor.execute_pipeline(pipeline_template, workspace_name, inputs)
        
        try:
            # Convert legacy pipeline template to DDD format if needed
            pipeline_id = PipelineId.generate()
            
            # Execute using DDD services
            run = self._execution_service.execute_pipeline(
                pipeline_id=pipeline_id,
                workspace_name=workspace_name,
                inputs=inputs
            )
            
            # Convert results to legacy format
            results = []
            for step_execution in run.step_executions:
                result = StepResult(
                    step_key=step_execution.step_id.value,
                    responses=step_execution.responses or [],
                    selected_response=step_execution.selected_response,
                    tokens_used=step_execution.tokens_used or {},
                    execution_time=step_execution.execution_time,
                    metadata=step_execution.metadata or {}
                )
                results.append(result)
            
            return results
        except Exception as e:
            # Fallback to legacy execution if DDD fails
            from .legacy_executor import PipelineExecutor as LegacyPipelineExecutor
            legacy_executor = LegacyPipelineExecutor()
            return legacy_executor.execute_pipeline(pipeline_template, workspace_name, inputs)
    
    def _create_simple_pipeline_service(self):
        """Create a simple pipeline service for backward compatibility."""
        class SimplePipelineService:
            def get_pipeline_template(self, pipeline_id):
                # Simple implementation
                return None
        
        return SimplePipelineService()
    
    def _create_legacy_executor(self):
        """Create legacy executor with proper parameters."""
        from .legacy_executor import PipelineExecutor as LegacyPipelineExecutor
        return LegacyPipelineExecutor(self._workspace, self._storage, self._workspace_name)
    
    def _create_simple_pipeline_service(self):
        """Create a simple pipeline service for backward compatibility."""
        class SimplePipelineService:
            def get_pipeline_template(self, pipeline_id):
                # Simple implementation
                return None
        
        return SimplePipelineService()
    
    def _create_simple_execution_service(self):
        """Create a simple execution service for backward compatibility."""
        class SimpleExecutionService:
            def execute_pipeline(self, pipeline_id, workspace_name, inputs):
                # Simple implementation - fallback to legacy
                from .legacy_executor import PipelineExecutor as LegacyExecutor
                return LegacyExecutor().execute_pipeline(None, workspace_name, inputs)
        
        return SimpleExecutionService()

__all__ = ["PipelineExecutor", "ExecutionContext", "StepResult"]
