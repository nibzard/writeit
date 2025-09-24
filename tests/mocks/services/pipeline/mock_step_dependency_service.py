"""Mock implementation of StepDependencyService for testing."""

from typing import Dict, List, Set, Any, Optional, Tuple
from unittest.mock import Mock

from writeit.domains.pipeline.services.step_dependency_service import (
    StepDependencyService,
    DependencyGraph,
    DependencyResolution,
    CircularDependencyError
)
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.value_objects.step_id import StepId


class MockStepDependencyService(StepDependencyService):
    """Mock implementation of StepDependencyService.
    
    Provides configurable dependency resolution behavior for testing
    step dependency scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock dependency service."""
        self._mock = Mock()
        self._dependency_graphs: Dict[str, DependencyGraph] = {}
        self._execution_orders: Dict[str, List[StepId]] = {}
        self._has_circular_dependencies = False
        self._should_fail = False
        
    def configure_dependency_graph(self, template_id: str, graph: DependencyGraph) -> None:
        """Configure dependency graph for template."""
        self._dependency_graphs[template_id] = graph
        
    def configure_execution_order(self, template_id: str, order: List[StepId]) -> None:
        """Configure execution order for template."""
        self._execution_orders[template_id] = order
        
    def configure_circular_dependencies(self, has_circular: bool) -> None:
        """Configure if circular dependencies should be detected."""
        self._has_circular_dependencies = has_circular
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if dependency resolution should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._dependency_graphs.clear()
        self._execution_orders.clear()
        self._has_circular_dependencies = False
        self._should_fail = False
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def build_dependency_graph(self, template: PipelineTemplate) -> DependencyGraph:
        """Build dependency graph from template."""
        self._mock.build_dependency_graph(template)
        
        template_id = str(template.id.value)
        
        # Return configured graph if available
        if template_id in self._dependency_graphs:
            return self._dependency_graphs[template_id]
            
        # Create mock dependency graph
        step_ids = [StepId(step.id) for step in template.steps]
        dependencies = {}
        
        # Simple mock dependencies - each step depends on previous one
        for i, step_id in enumerate(step_ids):
            if i > 0:
                dependencies[step_id] = [step_ids[i-1]]
            else:
                dependencies[step_id] = []
                
        return DependencyGraph(
            steps=set(step_ids),
            dependencies=dependencies
        )
        
    async def resolve_execution_order(self, template: PipelineTemplate) -> List[StepId]:
        """Resolve step execution order."""
        self._mock.resolve_execution_order(template)
        
        if self._should_fail:
            raise ValueError("Mock dependency resolution error")
            
        template_id = str(template.id.value)
        
        # Return configured order if available
        if template_id in self._execution_orders:
            return self._execution_orders[template_id]
            
        # Create mock execution order
        return [StepId(step.id) for step in template.steps]
        
    async def detect_circular_dependencies(self, template: PipelineTemplate) -> List[List[StepId]]:
        """Detect circular dependencies."""
        self._mock.detect_circular_dependencies(template)
        
        if self._has_circular_dependencies:
            # Return mock circular dependency
            step_ids = [StepId(step.id) for step in template.steps[:2]]
            return [step_ids]  # Mock circular dependency between first two steps
            
        return []  # No circular dependencies
        
    async def validate_dependencies(self, template: PipelineTemplate) -> List[str]:
        """Validate all dependencies."""
        self._mock.validate_dependencies(template)
        
        if self._should_fail:
            return ["Mock dependency validation error"]
            
        if self._has_circular_dependencies:
            return ["Circular dependency detected"]
            
        return []  # No validation errors
        
    async def get_step_dependencies(self, template: PipelineTemplate, step_id: StepId) -> List[StepId]:
        """Get dependencies for specific step."""
        self._mock.get_step_dependencies(template, step_id)
        
        # Find step index and return previous steps as dependencies
        step_ids = [StepId(step.id) for step in template.steps]
        try:
            step_index = step_ids.index(step_id)
            return step_ids[:step_index]  # All previous steps are dependencies
        except ValueError:
            return []  # Step not found
            
    async def get_step_dependents(self, template: PipelineTemplate, step_id: StepId) -> List[StepId]:
        """Get steps that depend on given step."""
        self._mock.get_step_dependents(template, step_id)
        
        # Find step index and return subsequent steps as dependents
        step_ids = [StepId(step.id) for step in template.steps]
        try:
            step_index = step_ids.index(step_id)
            return step_ids[step_index + 1:]  # All subsequent steps are dependents
        except ValueError:
            return []  # Step not found
            
    async def can_execute_step(self, template: PipelineTemplate, step_id: StepId, completed_steps: Set[StepId]) -> bool:
        """Check if step can be executed given completed steps."""
        self._mock.can_execute_step(template, step_id, completed_steps)
        
        dependencies = await self.get_step_dependencies(template, step_id)
        return all(dep in completed_steps for dep in dependencies)
        
    async def get_next_executable_steps(
        self, 
        template: PipelineTemplate, 
        completed_steps: Set[StepId]
    ) -> List[StepId]:
        """Get steps that can be executed next."""
        self._mock.get_next_executable_steps(template, completed_steps)
        
        executable_steps = []
        all_step_ids = [StepId(step.id) for step in template.steps]
        
        for step_id in all_step_ids:
            if step_id not in completed_steps:
                if await self.can_execute_step(template, step_id, completed_steps):
                    executable_steps.append(step_id)
                    
        return executable_steps
        
    async def estimate_parallel_execution_time(
        self, 
        template: PipelineTemplate,
        step_durations: Dict[StepId, float]
    ) -> float:
        """Estimate total execution time with parallel execution."""
        self._mock.estimate_parallel_execution_time(template, step_durations)
        
        # Simple mock estimation - sum of all step durations
        return sum(step_durations.values())
        
    async def optimize_execution_plan(
        self, 
        template: PipelineTemplate,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[List[StepId]]:
        """Optimize execution plan for parallel execution."""
        self._mock.optimize_execution_plan(template, constraints)
        
        # Simple mock plan - each step in its own batch
        step_ids = [StepId(step.id) for step in template.steps]
        return [[step_id] for step_id in step_ids]
