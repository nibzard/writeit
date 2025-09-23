"""Step dependency service.

Provides advanced dependency resolution logic for pipeline steps,
including topological sorting, cycle detection, optimization
suggestions, and parallel execution planning.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Any, Optional, Tuple, DefaultDict
from collections import defaultdict, deque
from enum import Enum

from ..entities.pipeline_template import PipelineTemplate, PipelineStepTemplate
from ..value_objects.step_id import StepId
from ..value_objects.prompt_template import PromptTemplate


class DependencyType(str, Enum):
    """Types of step dependencies."""
    EXPLICIT = "explicit"  # Declared in depends_on
    IMPLICIT = "implicit"  # Inferred from template variables
    DATA = "data"  # Data flow dependency
    CONDITIONAL = "conditional"  # Conditional dependency


class OptimizationLevel(str, Enum):
    """Dependency optimization levels."""
    CONSERVATIVE = "conservative"  # No changes, preserve all dependencies
    MODERATE = "moderate"  # Safe optimizations only
    AGGRESSIVE = "aggressive"  # Maximum parallelization


@dataclass
class StepDependency:
    """Represents a dependency between two steps."""
    from_step: StepId
    to_step: StepId
    dependency_type: DependencyType
    required_outputs: Set[str]  # What outputs are needed
    strength: float = 1.0  # Dependency strength (0.0 to 1.0)
    
    def __hash__(self) -> int:
        return hash((self.from_step, self.to_step, self.dependency_type))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StepDependency):
            return False
        return (
            self.from_step == other.from_step
            and self.to_step == other.to_step
            and self.dependency_type == other.dependency_type
        )


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph for a pipeline."""
    steps: Dict[str, PipelineStepTemplate]
    dependencies: Set[StepDependency]
    adjacency_list: DefaultDict[str, List[str]]  # step -> [dependent_steps]
    reverse_adjacency_list: DefaultDict[str, List[str]]  # step -> [dependency_steps]
    
    def __post_init__(self) -> None:
        """Build adjacency lists from dependencies."""
        self.adjacency_list = defaultdict(list)
        self.reverse_adjacency_list = defaultdict(list)
        
        for dep in self.dependencies:
            from_step = dep.from_step.value
            to_step = dep.to_step.value
            
            self.adjacency_list[from_step].append(to_step)
            self.reverse_adjacency_list[to_step].append(from_step)
    
    def get_step_dependencies(self, step_id: str) -> List[str]:
        """Get all steps that this step depends on."""
        return self.reverse_adjacency_list.get(step_id, [])
    
    def get_step_dependents(self, step_id: str) -> List[str]:
        """Get all steps that depend on this step."""
        return self.adjacency_list.get(step_id, [])
    
    def has_dependency(self, from_step: str, to_step: str) -> bool:
        """Check if there's a dependency from one step to another."""
        return to_step in self.adjacency_list.get(from_step, [])
    
    def get_root_steps(self) -> List[str]:
        """Get steps with no dependencies."""
        return [step_id for step_id in self.steps if not self.get_step_dependencies(step_id)]
    
    def get_leaf_steps(self) -> List[str]:
        """Get steps with no dependents."""
        return [step_id for step_id in self.steps if not self.get_step_dependents(step_id)]


@dataclass
class ParallelExecutionPlan:
    """Plan for parallel execution of pipeline steps."""
    execution_groups: List[List[str]]  # Groups of steps that can run in parallel
    critical_path: List[str]  # Longest dependency chain
    estimated_time_savings: float  # Percentage time savings from parallelization
    bottlenecks: List[str]  # Steps that limit parallelization
    
    @property
    def total_groups(self) -> int:
        """Total number of execution groups."""
        return len(self.execution_groups)
    
    @property
    def max_parallel_steps(self) -> int:
        """Maximum number of steps that can run in parallel."""
        return max(len(group) for group in self.execution_groups) if self.execution_groups else 0
    
    @property
    def total_steps(self) -> int:
        """Total number of steps in the plan."""
        return sum(len(group) for group in self.execution_groups)


@dataclass
class DependencyIssue:
    """Represents an issue with step dependencies."""
    issue_type: str  # 'cycle', 'unreachable', 'inefficient', 'redundant'
    steps_involved: List[str]
    description: str
    suggestion: Optional[str] = None
    severity: str = "warning"  # 'error', 'warning', 'info'


class StepDependencyService:
    """Service for analyzing and optimizing step dependencies.
    
    Provides comprehensive dependency analysis including:
    - Automatic dependency detection from template variables
    - Cycle detection and resolution suggestions
    - Optimization recommendations for parallel execution
    - Critical path analysis
    - Dependency validation and cleanup
    
    Examples:
        service = StepDependencyService()
        graph = service.build_dependency_graph(template)
        
        # Check for issues
        issues = service.analyze_dependencies(graph)
        
        # Get execution plan
        plan = service.create_parallel_execution_plan(graph)
        
        # Optimize dependencies
        optimized = service.optimize_dependencies(graph, OptimizationLevel.MODERATE)
    """
    
    def __init__(self) -> None:
        """Initialize dependency service."""
        self._max_dependency_depth = 20
        self._parallel_efficiency_threshold = 0.1  # 10% minimum improvement
    
    def build_dependency_graph(self, template: PipelineTemplate) -> DependencyGraph:
        """Build complete dependency graph for a pipeline template.
        
        Args:
            template: Pipeline template to analyze
            
        Returns:
            Complete dependency graph with explicit and implicit dependencies
        """
        dependencies = set()
        
        # Add explicit dependencies
        for step_key, step in template.steps.items():
            for dep_id in step.depends_on:
                dependencies.add(StepDependency(
                    from_step=dep_id,
                    to_step=step.id,
                    dependency_type=DependencyType.EXPLICIT,
                    required_outputs=set(),  # Will be determined by variable analysis
                    strength=1.0
                ))
        
        # Add implicit dependencies from template variables
        implicit_deps = self._detect_implicit_dependencies(template)
        dependencies.update(implicit_deps)
        
        # Add data flow dependencies
        data_deps = self._detect_data_dependencies(template)
        dependencies.update(data_deps)
        
        return DependencyGraph(
            steps=template.steps,
            dependencies=dependencies,
            adjacency_list=defaultdict(list),
            reverse_adjacency_list=defaultdict(list)
        )
    
    def analyze_dependencies(self, graph: DependencyGraph) -> List[DependencyIssue]:
        """Analyze dependency graph for issues and optimization opportunities.
        
        Args:
            graph: Dependency graph to analyze
            
        Returns:
            List of identified issues and suggestions
        """
        issues = []
        
        # Check for cycles
        cycles = self._detect_cycles(graph)
        for cycle in cycles:
            issues.append(DependencyIssue(
                issue_type="cycle",
                steps_involved=cycle,
                description=f"Circular dependency detected: {' -> '.join(cycle + [cycle[0]])}",
                suggestion="Remove one of the dependencies to break the cycle",
                severity="error"
            ))
        
        # Check for unreachable steps
        unreachable = self._detect_unreachable_steps(graph)
        for step in unreachable:
            issues.append(DependencyIssue(
                issue_type="unreachable",
                steps_involved=[step],
                description=f"Step '{step}' has dependencies that cannot be satisfied",
                suggestion="Check dependency declarations and template variables",
                severity="error"
            ))
        
        # Check for redundant dependencies
        redundant = self._detect_redundant_dependencies(graph)
        for from_step, to_step in redundant:
            issues.append(DependencyIssue(
                issue_type="redundant",
                steps_involved=[from_step, to_step],
                description=f"Redundant dependency: {from_step} -> {to_step} (indirect path exists)",
                suggestion="Remove redundant dependency to simplify graph",
                severity="info"
            ))
        
        # Check for inefficient sequencing
        inefficient = self._detect_inefficient_sequencing(graph)
        for steps in inefficient:
            issues.append(DependencyIssue(
                issue_type="inefficient",
                steps_involved=steps,
                description=f"Steps {steps} could run in parallel but are sequential",
                suggestion="Enable parallel execution for these steps",
                severity="warning"
            ))
        
        return issues
    
    def create_parallel_execution_plan(
        self,
        graph: DependencyGraph,
        optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    ) -> ParallelExecutionPlan:
        """Create optimal parallel execution plan.
        
        Args:
            graph: Dependency graph
            optimization_level: Level of optimization to apply
            
        Returns:
            Parallel execution plan with groups and analysis
        """
        # Get topological ordering
        topological_order = self._topological_sort(graph)
        if not topological_order:
            raise ValueError("Cannot create execution plan: dependency cycles detected")
        
        # Group steps by execution level
        execution_groups = self._create_execution_groups(graph, topological_order, optimization_level)
        
        # Find critical path
        critical_path = self._find_critical_path(graph)
        
        # Calculate time savings
        sequential_time = len(topological_order)
        parallel_time = len(execution_groups)
        time_savings = (sequential_time - parallel_time) / sequential_time * 100
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(graph, execution_groups)
        
        return ParallelExecutionPlan(
            execution_groups=execution_groups,
            critical_path=critical_path,
            estimated_time_savings=time_savings,
            bottlenecks=bottlenecks
        )
    
    def optimize_dependencies(
        self,
        graph: DependencyGraph,
        optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    ) -> DependencyGraph:
        """Optimize dependency graph for better parallelization.
        
        Args:
            graph: Original dependency graph
            optimization_level: Level of optimization to apply
            
        Returns:
            Optimized dependency graph
        """
        optimized_dependencies = set(graph.dependencies)
        
        if optimization_level == OptimizationLevel.CONSERVATIVE:
            # No optimizations, return original
            return graph
        
        # Remove redundant dependencies
        redundant = self._detect_redundant_dependencies(graph)
        for from_step, to_step in redundant:
            # Find and remove the redundant dependency
            for dep in list(optimized_dependencies):
                if dep.from_step.value == from_step and dep.to_step.value == to_step:
                    if dep.dependency_type != DependencyType.EXPLICIT:
                        optimized_dependencies.remove(dep)
                        break
        
        if optimization_level == OptimizationLevel.AGGRESSIVE:
            # Weaken implicit dependencies that don't affect correctness
            for dep in list(optimized_dependencies):
                if dep.dependency_type == DependencyType.IMPLICIT and dep.strength < 0.5:
                    # Check if removing this dependency would create issues
                    temp_deps = optimized_dependencies - {dep}
                    temp_graph = DependencyGraph(
                        steps=graph.steps,
                        dependencies=temp_deps,
                        adjacency_list=defaultdict(list),
                        reverse_adjacency_list=defaultdict(list)
                    )
                    
                    # Only remove if it doesn't break critical functionality
                    if not self._would_break_functionality(graph, temp_graph, dep):
                        optimized_dependencies.remove(dep)
        
        return DependencyGraph(
            steps=graph.steps,
            dependencies=optimized_dependencies,
            adjacency_list=defaultdict(list),
            reverse_adjacency_list=defaultdict(list)
        )
    
    def get_execution_order(
        self,
        graph: DependencyGraph,
        prefer_parallel: bool = True
    ) -> List[str]:
        """Get optimal execution order for steps.
        
        Args:
            graph: Dependency graph
            prefer_parallel: Whether to optimize for parallel execution
            
        Returns:
            List of step IDs in execution order
            
        Raises:
            ValueError: If cycles are detected
        """
        order = self._topological_sort(graph)
        if not order:
            raise ValueError("Cannot determine execution order: cycles detected")
        
        if prefer_parallel:
            # Reorder to maximize parallelization opportunities
            order = self._reorder_for_parallelization(graph, order)
        
        return order
    
    def calculate_dependency_metrics(self, graph: DependencyGraph) -> Dict[str, Any]:
        """Calculate various metrics about the dependency graph.
        
        Args:
            graph: Dependency graph to analyze
            
        Returns:
            Dictionary of metrics
        """
        total_steps = len(graph.steps)
        total_dependencies = len(graph.dependencies)
        
        # Calculate dependency density
        max_possible_deps = total_steps * (total_steps - 1)
        dependency_density = total_dependencies / max_possible_deps if max_possible_deps > 0 else 0
        
        # Calculate depth
        critical_path = self._find_critical_path(graph)
        dependency_depth = len(critical_path)
        
        # Calculate fan-in/fan-out
        fan_in_values = [len(graph.get_step_dependencies(step)) for step in graph.steps]
        fan_out_values = [len(graph.get_step_dependents(step)) for step in graph.steps]
        
        avg_fan_in = sum(fan_in_values) / len(fan_in_values) if fan_in_values else 0
        avg_fan_out = sum(fan_out_values) / len(fan_out_values) if fan_out_values else 0
        max_fan_in = max(fan_in_values) if fan_in_values else 0
        max_fan_out = max(fan_out_values) if fan_out_values else 0
        
        # Calculate parallelization potential
        execution_plan = self.create_parallel_execution_plan(graph)
        parallelization_factor = execution_plan.max_parallel_steps / total_steps if total_steps > 0 else 0
        
        return {
            "total_steps": total_steps,
            "total_dependencies": total_dependencies,
            "dependency_density": dependency_density,
            "dependency_depth": dependency_depth,
            "average_fan_in": avg_fan_in,
            "average_fan_out": avg_fan_out,
            "max_fan_in": max_fan_in,
            "max_fan_out": max_fan_out,
            "parallelization_factor": parallelization_factor,
            "critical_path_length": len(critical_path),
            "estimated_time_savings": execution_plan.estimated_time_savings,
            "root_steps": graph.get_root_steps(),
            "leaf_steps": graph.get_leaf_steps()
        }
    
    def _detect_implicit_dependencies(self, template: PipelineTemplate) -> Set[StepDependency]:
        """Detect implicit dependencies from template variables."""
        dependencies = set()
        
        # Create execution order to determine what outputs are available when
        execution_order = template.get_execution_order()
        available_outputs = set()
        
        for step_key in execution_order:
            step = template.steps[step_key]
            required_vars = step.prompt_template.nested_variables
            
            # Check for step output references (e.g., steps.outline)
            for var in required_vars:
                if var.startswith("steps."):
                    referenced_step = var.split(".")[1]
                    if referenced_step != step_key and referenced_step in template.steps:
                        # This is an implicit dependency
                        dep_step_id = template.steps[referenced_step].id
                        if dep_step_id not in step.depends_on:  # Not already explicit
                            dependencies.add(StepDependency(
                                from_step=dep_step_id,
                                to_step=step.id,
                                dependency_type=DependencyType.IMPLICIT,
                                required_outputs={var.split(".", 2)[2] if len(var.split(".")) > 2 else "output"},
                                strength=0.8  # Strong but not as strong as explicit
                            ))
            
            # This step's outputs are now available
            available_outputs.add(step_key)
        
        return dependencies
    
    def _detect_data_dependencies(self, template: PipelineTemplate) -> Set[StepDependency]:
        """Detect data flow dependencies."""
        dependencies = set()
        
        # Analyze data flow between steps
        for step_key, step in template.steps.items():
            # Check if this step's outputs are used by other steps
            for other_key, other_step in template.steps.items():
                if step_key == other_key:
                    continue
                
                # Check if other step references this step's outputs
                other_vars = other_step.prompt_template.nested_variables
                step_output_refs = {var for var in other_vars if var.startswith(f"steps.{step_key}.")}
                
                if step_output_refs:
                    dependencies.add(StepDependency(
                        from_step=step.id,
                        to_step=other_step.id,
                        dependency_type=DependencyType.DATA,
                        required_outputs={ref.split(".", 2)[2] for ref in step_output_refs},
                        strength=0.9  # Data dependencies are very strong
                    ))
        
        return dependencies
    
    def _detect_cycles(self, graph: DependencyGraph) -> List[List[str]]:
        """Detect cycles in the dependency graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.adjacency_list[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for step in graph.steps:
            if step not in visited:
                dfs(step)
        
        return cycles
    
    def _detect_unreachable_steps(self, graph: DependencyGraph) -> List[str]:
        """Detect steps that cannot be reached due to missing dependencies."""
        unreachable = []
        
        for step_id in graph.steps:
            dependencies = graph.get_step_dependencies(step_id)
            
            # Check if all dependencies exist
            for dep in dependencies:
                if dep not in graph.steps:
                    unreachable.append(step_id)
                    break
        
        return unreachable
    
    def _detect_redundant_dependencies(self, graph: DependencyGraph) -> List[Tuple[str, str]]:
        """Detect redundant dependencies (transitive dependencies)."""
        redundant = []
        
        for step_id in graph.steps:
            direct_deps = set(graph.get_step_dependencies(step_id))
            
            # Find all transitive dependencies
            transitive_deps = set()
            for dep in direct_deps:
                transitive_deps.update(self._get_all_dependencies(graph, dep))
            
            # Any direct dependency that's also a transitive dependency is redundant
            for dep in direct_deps:
                if dep in transitive_deps:
                    redundant.append((dep, step_id))
        
        return redundant
    
    def _detect_inefficient_sequencing(self, graph: DependencyGraph) -> List[List[str]]:
        """Detect groups of steps that could run in parallel but are sequential."""
        inefficient = []
        
        # Find steps that have no dependencies between them
        steps = list(graph.steps.keys())
        
        for i, step1 in enumerate(steps):
            for j, step2 in enumerate(steps[i+1:], i+1):
                # Check if these steps could run in parallel
                if (not graph.has_dependency(step1, step2) and 
                    not graph.has_dependency(step2, step1)):
                    
                    # Check if they're not already marked as parallel
                    step1_template = graph.steps[step1]
                    step2_template = graph.steps[step2]
                    
                    if not (step1_template.parallel and step2_template.parallel):
                        inefficient.append([step1, step2])
        
        return inefficient
    
    def _topological_sort(self, graph: DependencyGraph) -> Optional[List[str]]:
        """Perform topological sort using Kahn's algorithm."""
        # Calculate in-degrees
        in_degree = {step: 0 for step in graph.steps}
        for step in graph.steps:
            for dependent in graph.adjacency_list[step]:
                in_degree[dependent] += 1
        
        # Queue of steps with no dependencies
        queue = deque([step for step, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Remove this step and update in-degrees
            for dependent in graph.adjacency_list[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check if all steps were processed (no cycles)
        if len(result) != len(graph.steps):
            return None  # Cycle detected
        
        return result
    
    def _create_execution_groups(
        self,
        graph: DependencyGraph,
        topological_order: List[str],
        optimization_level: OptimizationLevel
    ) -> List[List[str]]:
        """Create groups of steps that can execute in parallel."""
        groups = []
        remaining_steps = set(topological_order)
        
        while remaining_steps:
            # Find all steps that can start now (dependencies satisfied)
            ready_steps = []
            for step in remaining_steps:
                dependencies = graph.get_step_dependencies(step)
                if all(dep not in remaining_steps for dep in dependencies):
                    ready_steps.append(step)
            
            if not ready_steps:
                # Should not happen with valid topological order
                break
            
            # Apply optimization level
            if optimization_level == OptimizationLevel.CONSERVATIVE:
                # Only one step per group
                groups.append([ready_steps[0]])
                remaining_steps.remove(ready_steps[0])
            else:
                # Group parallel-eligible steps
                parallel_group = []
                for step in ready_steps:
                    step_template = graph.steps[step]
                    if step_template.parallel or optimization_level == OptimizationLevel.AGGRESSIVE:
                        parallel_group.append(step)
                    elif not parallel_group:  # First step is always included
                        parallel_group.append(step)
                
                groups.append(parallel_group)
                for step in parallel_group:
                    remaining_steps.remove(step)
        
        return groups
    
    def _find_critical_path(self, graph: DependencyGraph) -> List[str]:
        """Find the critical path (longest dependency chain)."""
        # Use dynamic programming to find longest path
        distances = {step: 0 for step in graph.steps}
        predecessors = {step: None for step in graph.steps}
        
        # Process steps in topological order
        topological_order = self._topological_sort(graph)
        if not topological_order:
            return []  # No valid path due to cycles
        
        for step in topological_order:
            for dependent in graph.adjacency_list[step]:
                new_distance = distances[step] + 1
                if new_distance > distances[dependent]:
                    distances[dependent] = new_distance
                    predecessors[dependent] = step
        
        # Find the step with maximum distance
        end_step = max(distances, key=distances.get)
        
        # Reconstruct path
        path = []
        current = end_step
        while current is not None:
            path.append(current)
            current = predecessors[current]
        
        return list(reversed(path))
    
    def _identify_bottlenecks(self, graph: DependencyGraph, execution_groups: List[List[str]]) -> List[str]:
        """Identify steps that are bottlenecks for parallelization."""
        bottlenecks = []
        
        # Steps that appear in single-step groups are potential bottlenecks
        single_step_groups = [group[0] for group in execution_groups if len(group) == 1]
        
        for step in single_step_groups:
            # Check if this step has many dependents
            dependents = graph.get_step_dependents(step)
            if len(dependents) > 2:  # Arbitrary threshold
                bottlenecks.append(step)
        
        return bottlenecks
    
    def _get_all_dependencies(self, graph: DependencyGraph, step: str) -> Set[str]:
        """Get all transitive dependencies of a step."""
        all_deps = set()
        to_visit = [step]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            
            deps = graph.get_step_dependencies(current)
            all_deps.update(deps)
            to_visit.extend(deps)
        
        return all_deps
    
    def _would_break_functionality(self, original: DependencyGraph, modified: DependencyGraph, removed_dep: StepDependency) -> bool:
        """Check if removing a dependency would break pipeline functionality."""
        # Simple heuristic: if the dependency involves required outputs, it's critical
        return len(removed_dep.required_outputs) > 0 and removed_dep.strength > 0.7
    
    def _reorder_for_parallelization(self, graph: DependencyGraph, order: List[str]) -> List[str]:
        """Reorder steps to maximize parallelization opportunities."""
        # Group steps by their dependency level
        levels = {}
        for step in order:
            # Calculate the longest path to this step
            deps = graph.get_step_dependencies(step)
            if not deps:
                levels[step] = 0
            else:
                levels[step] = max(levels.get(dep, 0) for dep in deps) + 1
        
        # Sort by level, then by preference for parallel steps
        def sort_key(step: str) -> Tuple[int, int]:
            step_template = graph.steps[step]
            parallel_priority = 0 if step_template.parallel else 1
            return (levels[step], parallel_priority)
        
        return sorted(order, key=sort_key)
