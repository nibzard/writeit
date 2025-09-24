"""Unit tests for StepDependencyService.

Tests comprehensive step dependency resolution logic including:
- Dependency graph construction and analysis
- Topological sorting and execution order
- Circular dependency detection and resolution
- Parallel execution planning and optimization
- Template variable dependency inference
- Performance optimization suggestions
"""

import pytest
from typing import Dict, List, Set
from dataclasses import replace

from src.writeit.domains.pipeline.services.step_dependency_service import (
    StepDependencyService,
    DependencyGraph,
    StepDependency,
    DependencyType,
    OptimizationLevel,
    ParallelExecutionPlan,
    CircularDependencyError,
    InvalidDependencyError,
    OptimizationAnalysis
)
from src.writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineStepTemplate
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate

from tests.builders.pipeline_builders import (
    PipelineTemplateBuilder,
    PipelineStepTemplateBuilder
)


class TestStepDependency:
    """Test StepDependency behavior."""
    
    def test_create_step_dependency(self):
        """Test creating step dependency."""
        from_step = StepId("step1")
        to_step = StepId("step2")
        required_outputs = {"result", "metadata"}
        
        dependency = StepDependency(
            from_step=from_step,
            to_step=to_step,
            dependency_type=DependencyType.EXPLICIT,
            required_outputs=required_outputs,
            strength=0.8
        )
        
        assert dependency.from_step == from_step
        assert dependency.to_step == to_step
        assert dependency.dependency_type == DependencyType.EXPLICIT
        assert dependency.required_outputs == required_outputs
        assert dependency.strength == 0.8
    
    def test_step_dependency_equality(self):
        """Test step dependency equality."""
        dep1 = StepDependency(
            from_step=StepId("step1"),
            to_step=StepId("step2"),
            dependency_type=DependencyType.EXPLICIT,
            required_outputs={"result"}
        )
        
        dep2 = StepDependency(
            from_step=StepId("step1"),
            to_step=StepId("step2"),
            dependency_type=DependencyType.EXPLICIT,
            required_outputs={"different"}  # Different outputs but same core identity
        )
        
        dep3 = StepDependency(
            from_step=StepId("step1"),
            to_step=StepId("step3"),
            dependency_type=DependencyType.EXPLICIT,
            required_outputs={"result"}
        )
        
        assert dep1 == dep2  # Same from/to/type
        assert dep1 != dep3  # Different to_step
        assert dep1 != "not_a_dependency"
    
    def test_step_dependency_hashable(self):
        """Test step dependency can be used in sets."""
        dep1 = StepDependency(
            from_step=StepId("step1"),
            to_step=StepId("step2"),
            dependency_type=DependencyType.EXPLICIT,
            required_outputs={"result"}
        )
        
        dep2 = StepDependency(
            from_step=StepId("step1"),
            to_step=StepId("step2"),
            dependency_type=DependencyType.IMPLICIT,
            required_outputs={"result"}
        )
        
        dependency_set = {dep1, dep2}
        assert len(dependency_set) == 2


class TestDependencyGraph:
    """Test DependencyGraph behavior."""
    
    def test_create_dependency_graph(self):
        """Test creating dependency graph."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        
        steps = {"step1": step1, "step2": step2}
        dependencies = {
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step2"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            )
        }
        
        graph = DependencyGraph(
            steps=steps,
            dependencies=dependencies,
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        assert len(graph.steps) == 2
        assert len(graph.dependencies) == 1
        assert graph.adjacency_list["step1"] == ["step2"]
        assert graph.reverse_adjacency_list["step2"] == ["step1"]
    
    def test_get_step_dependencies(self):
        """Test getting step dependencies."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        steps = {"step1": step1, "step2": step2, "step3": step3}
        dependencies = {
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step3"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result1"}
            ),
            StepDependency(
                from_step=StepId("step2"),
                to_step=StepId("step3"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result2"}
            )
        }
        
        graph = DependencyGraph(
            steps=steps,
            dependencies=dependencies,
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        step3_deps = graph.get_step_dependencies("step3")
        assert set(step3_deps) == {"step1", "step2"}
        
        step1_deps = graph.get_step_dependencies("step1")
        assert step1_deps == []
    
    def test_get_step_dependents(self):
        """Test getting step dependents."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        steps = {"step1": step1, "step2": step2, "step3": step3}
        dependencies = {
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step2"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            ),
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step3"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            )
        }
        
        graph = DependencyGraph(
            steps=steps,
            dependencies=dependencies,
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        step1_dependents = graph.get_step_dependents("step1")
        assert set(step1_dependents) == {"step2", "step3"}
        
        step3_dependents = graph.get_step_dependents("step3")
        assert step3_dependents == []
    
    def test_has_dependency(self):
        """Test checking for dependencies."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        
        steps = {"step1": step1, "step2": step2}
        dependencies = {
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step2"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            )
        }
        
        graph = DependencyGraph(
            steps=steps,
            dependencies=dependencies,
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        assert graph.has_dependency("step1", "step2") is True
        assert graph.has_dependency("step2", "step1") is False
        assert graph.has_dependency("step1", "nonexistent") is False
    
    def test_get_root_steps(self):
        """Test getting root steps (no dependencies)."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        steps = {"step1": step1, "step2": step2, "step3": step3}
        dependencies = {
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step3"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            ),
            StepDependency(
                from_step=StepId("step2"),
                to_step=StepId("step3"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            )
        }
        
        graph = DependencyGraph(
            steps=steps,
            dependencies=dependencies,
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        root_steps = graph.get_root_steps()
        assert set(root_steps) == {"step1", "step2"}
    
    def test_get_leaf_steps(self):
        """Test getting leaf steps (no dependents)."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        steps = {"step1": step1, "step2": step2, "step3": step3}
        dependencies = {
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step2"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            ),
            StepDependency(
                from_step=StepId("step1"),
                to_step=StepId("step3"),
                dependency_type=DependencyType.EXPLICIT,
                required_outputs={"result"}
            )
        }
        
        graph = DependencyGraph(
            steps=steps,
            dependencies=dependencies,
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        leaf_steps = graph.get_leaf_steps()
        assert set(leaf_steps) == {"step2", "step3"}


class TestParallelExecutionPlan:
    """Test ParallelExecutionPlan behavior."""
    
    def test_create_parallel_execution_plan(self):
        """Test creating parallel execution plan."""
        execution_groups = [
            ["step1", "step2"],  # Can run in parallel
            ["step3"],           # Depends on both step1 and step2
            ["step4"]            # Depends on step3
        ]
        critical_path = ["step1", "step3", "step4"]
        estimated_time = 45.0
        parallelism_factor = 0.6
        
        plan = ParallelExecutionPlan(
            execution_groups=execution_groups,
            critical_path=critical_path,
            estimated_execution_time=estimated_time,
            parallelism_factor=parallelism_factor,
            optimization_suggestions=[]
        )
        
        assert len(plan.execution_groups) == 3
        assert len(plan.execution_groups[0]) == 2  # Parallel group
        assert plan.critical_path == critical_path
        assert plan.estimated_execution_time == estimated_time
        assert plan.parallelism_factor == parallelism_factor
    
    def test_parallel_execution_plan_properties(self):
        """Test parallel execution plan computed properties."""
        execution_groups = [
            ["step1", "step2", "step3"],  # 3 parallel
            ["step4", "step5"],           # 2 parallel
            ["step6"]                     # 1 sequential
        ]
        
        plan = ParallelExecutionPlan(
            execution_groups=execution_groups,
            critical_path=["step1", "step4", "step6"],
            estimated_execution_time=30.0,
            parallelism_factor=0.5,
            optimization_suggestions=[]
        )
        
        assert plan.total_steps == 6
        assert plan.max_parallelism == 3
        assert plan.depth == 3  # 3 execution groups


class TestStepDependencyService:
    """Test StepDependencyService business logic."""
    
    def test_create_service(self):
        """Test creating step dependency service."""
        service = StepDependencyService()
        
        # Check default values
        assert service._optimization_level == OptimizationLevel.MODERATE
        assert service._enable_implicit_dependencies is True
        assert service._max_execution_groups == 10
    
    def test_analyze_dependencies_simple_chain(self):
        """Test analyzing simple dependency chain."""
        # Create pipeline: step1 -> step2 -> step3
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step2"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        
        assert len(graph.steps) == 3
        assert len(graph.dependencies) == 2
        
        # Verify structure
        assert graph.get_step_dependencies("step1") == []
        assert graph.get_step_dependencies("step2") == ["step1"]
        assert graph.get_step_dependencies("step3") == ["step2"]
        
        assert graph.get_root_steps() == ["step1"]
        assert graph.get_leaf_steps() == ["step3"]
    
    def test_analyze_dependencies_parallel_branches(self):
        """Test analyzing pipeline with parallel branches."""
        # Create pipeline: step1 -> (step2, step3) -> step4
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step1"]).build()
        step4 = PipelineStepTemplateBuilder().with_id("step4").with_dependencies(["step2", "step3"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        
        assert len(graph.steps) == 4
        assert len(graph.dependencies) == 4  # step1->step2, step1->step3, step2->step4, step3->step4
        
        # Verify structure
        assert graph.get_step_dependencies("step1") == []
        assert set(graph.get_step_dependencies("step4")) == {"step2", "step3"}
        
        assert graph.get_root_steps() == ["step1"]
        assert graph.get_leaf_steps() == ["step4"]
    
    def test_topological_sort_simple(self):
        """Test topological sort of simple dependency chain."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step2"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        sorted_steps = service.topological_sort(graph)
        
        assert sorted_steps == ["step1", "step2", "step3"]
    
    def test_topological_sort_parallel(self):
        """Test topological sort with parallel steps."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step1"]).build()
        step4 = PipelineStepTemplateBuilder().with_id("step4").with_dependencies(["step2", "step3"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        sorted_steps = service.topological_sort(graph)
        
        # step1 must be first, step4 must be last
        assert sorted_steps[0] == "step1"
        assert sorted_steps[-1] == "step4"
        
        # step2 and step3 can be in any order but both before step4
        step2_idx = sorted_steps.index("step2")
        step3_idx = sorted_steps.index("step3")
        step4_idx = sorted_steps.index("step4")
        
        assert step2_idx < step4_idx
        assert step3_idx < step4_idx
    
    def test_detect_circular_dependency(self):
        """Test detection of circular dependencies."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").with_dependencies(["step3"]).build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step2"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService()
        
        with pytest.raises(CircularDependencyError) as exc_info:
            service.analyze_dependencies(template)
        
        assert "Circular dependency detected" in str(exc_info.value)
        assert "step1" in str(exc_info.value) or "step2" in str(exc_info.value) or "step3" in str(exc_info.value)
    
    def test_create_parallel_execution_plan(self):
        """Test creating parallel execution plan."""
        # Create diamond dependency: step1 -> (step2, step3) -> step4
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step1"]).build()
        step4 = PipelineStepTemplateBuilder().with_id("step4").with_dependencies(["step2", "step3"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        plan = service.create_parallel_execution_plan(graph)
        
        # Should have 3 execution groups:
        # Group 1: [step1]
        # Group 2: [step2, step3] (parallel)
        # Group 3: [step4]
        assert len(plan.execution_groups) == 3
        assert plan.execution_groups[0] == ["step1"]
        assert set(plan.execution_groups[1]) == {"step2", "step3"}
        assert plan.execution_groups[2] == ["step4"]
        
        # Critical path should include longest chain
        assert len(plan.critical_path) >= 3
        assert plan.critical_path[0] == "step1"
        assert plan.critical_path[-1] == "step4"
    
    def test_validate_dependencies_missing_step(self):
        """Test validation with missing dependency step."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").with_dependencies(["missing_step"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1
        }).build()
        
        service = StepDependencyService()
        
        with pytest.raises(InvalidDependencyError) as exc_info:
            service.analyze_dependencies(template)
        
        assert "Step 'step1' depends on 'missing_step' which does not exist" in str(exc_info.value)
    
    def test_infer_implicit_dependencies_from_templates(self):
        """Test inferring dependencies from template variables."""
        # step2 uses output from step1 in its template
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_prompt_template(
            PromptTemplate("Use result from step1: {{ steps.step1.result }}")
        ).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2
        }).build()
        
        service = StepDependencyService(enable_implicit_dependencies=True)
        graph = service.analyze_dependencies(template)
        
        # Should detect implicit dependency from step1 to step2
        implicit_deps = [dep for dep in graph.dependencies if dep.dependency_type == DependencyType.IMPLICIT]
        assert len(implicit_deps) >= 1
        
        # step2 should depend on step1
        assert "step1" in graph.get_step_dependencies("step2")
    
    def test_analyze_optimization_opportunities(self):
        """Test optimization analysis."""
        # Create suboptimal pipeline with unnecessary sequential execution
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()  # Could be parallel
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()  # Independent, could be parallel with step1
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        analysis = service.analyze_optimization_opportunities(graph)
        
        assert isinstance(analysis, OptimizationAnalysis)
        assert analysis.current_parallelism_factor < 1.0
        assert len(analysis.optimization_suggestions) > 0
        
        # Should suggest making step1 and step3 parallel
        suggestions = [s.suggestion_type for s in analysis.optimization_suggestions]
        assert "PARALLELIZE_INDEPENDENT_STEPS" in suggestions
    
    def test_get_step_execution_order_conservative(self):
        """Test conservative execution order (fully sequential)."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService(optimization_level=OptimizationLevel.CONSERVATIVE)
        execution_order = service.get_step_execution_order(template)
        
        # Conservative mode should maintain original order
        assert len(execution_order) == 3
        assert all(len(group) == 1 for group in execution_order)  # All sequential
    
    def test_get_step_execution_order_aggressive(self):
        """Test aggressive execution order (maximum parallelization)."""
        # Create independent steps
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService(optimization_level=OptimizationLevel.AGGRESSIVE)
        execution_order = service.get_step_execution_order(template)
        
        # Aggressive mode should parallelize independent steps
        assert len(execution_order) == 1  # Single execution group
        assert len(execution_order[0]) == 3  # All steps in parallel
        assert set(execution_order[0]) == {"step1", "step2", "step3"}
    
    def test_estimate_execution_time(self):
        """Test execution time estimation."""
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step1"]).build()
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        plan = service.create_parallel_execution_plan(graph)
        
        # Should estimate time based on critical path
        assert plan.estimated_execution_time > 0
        assert isinstance(plan.estimated_execution_time, float)
    
    def test_find_critical_path(self):
        """Test finding critical path in dependency graph."""
        # Create chain with different path lengths
        step1 = PipelineStepTemplateBuilder().with_id("step1").build()
        step2 = PipelineStepTemplateBuilder().with_id("step2").with_dependencies(["step1"]).build()
        step3 = PipelineStepTemplateBuilder().with_id("step3").with_dependencies(["step2"]).build()
        step4 = PipelineStepTemplateBuilder().with_id("step4").with_dependencies(["step1"]).build()  # Shorter path
        
        template = PipelineTemplateBuilder().with_steps({
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4
        }).build()
        
        service = StepDependencyService()
        graph = service.analyze_dependencies(template)
        critical_path = service._find_critical_path(graph)
        
        # Critical path should be the longest: step1 -> step2 -> step3
        assert len(critical_path) >= 3
        assert critical_path[0] == "step1"
        assert "step3" in critical_path
        assert len(critical_path) > 2  # Longer than step1 -> step4
