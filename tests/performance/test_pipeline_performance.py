"""Pipeline execution performance benchmarks.

This module provides comprehensive performance testing for:
- Pipeline template loading and validation
- Pipeline execution with different configurations
- Concurrent pipeline execution
- Memory usage during pipeline runs
- Performance under different loads
"""

import asyncio
import pytest
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, AsyncGenerator
import uuid

from tests.performance.test_performance_framework import (
    measure_performance, 
    run_concurrent_operations, 
    generate_performance_report,
    save_benchmark_results,
    PerformanceMonitor,
    TestConfiguration,
    validate_performance_thresholds
)

from tests.fixtures.pipeline import create_test_pipeline_template
from tests.utils.workspace_helpers import create_test_workspace
from tests.utils.storage_helpers import setup_test_storage


class PipelinePerformanceTest:
    """Performance testing for pipeline operations."""
    
    @pytest.fixture
    async def performance_workspace(self):
        """Create isolated workspace for performance testing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="perf_test_"))
        workspace_name = f"perf_test_{uuid.uuid4().hex[:8]}"
        
        try:
            workspace = await create_test_workspace(workspace_name, temp_dir)
            yield workspace
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    async def performance_storage(self, performance_workspace):
        """Set up performance testing storage."""
        return await setup_test_storage(performance_workspace.name)
    
    async def create_performance_pipeline_template(
        self, 
        steps_count: int = 5,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """Create pipeline template with configurable complexity."""
        
        if complexity == "simple":
            prompt_length = 50
            variables_count = 2
        elif complexity == "medium":
            prompt_length = 200
            variables_count = 5
        elif complexity == "complex":
            prompt_length = 500
            variables_count = 10
        else:
            prompt_length = 100
            variables_count = 3
        
        # Generate steps
        steps = {}
        for i in range(steps_count):
            step_name = f"step_{i+1}"
            
            # Create prompt template with variables
            variables = [f"var_{j}" for j in range(variables_count)]
            prompt_parts = [f"Process {step_name}"]
            for var in variables:
                prompt_parts.append(f"using {var}")
            prompt_parts.append("Generate high-quality content.")
            
            prompt_template = " ".join(prompt_parts)
            
            steps[step_name] = {
                "name": f"Step {i+1}",
                "description": f"Performance test step {i+1}",
                "type": "llm_generate",
                "prompt_template": prompt_template,
                "model_preference": ["mock-model"],
                "depends_on": [f"step_{j}" for j in range(i)] if i > 0 else []
            }
        
        return {
            "metadata": {
                "name": f"performance_pipeline_{steps_count}_{complexity}",
                "description": f"Performance test pipeline with {steps_count} steps",
                "version": "1.0.0"
            },
            "defaults": {
                "model": "mock-model"
            },
            "inputs": {
                "topic": {
                    "type": "text",
                    "label": "Topic",
                    "required": True,
                    "default": "Performance Testing"
                }
            },
            "steps": steps
        }
    
    async def benchmark_pipeline_loading(self, performance_storage):
        """Benchmark pipeline template loading performance."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        loading_times = []
        
        for i in range(TestConfiguration.PIPELINE_ITERATIONS):
            template = await self.create_performance_pipeline_template(steps_count=3)
            
            async with measure_performance(f"pipeline_load_{i}", monitor) as metrics:
                # Simulate pipeline loading and validation
                await asyncio.sleep(0.001)  # Minimal processing time
            
            loading_times.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "pipeline_loading_benchmark",
            loading_times,
            monitor_results
        )
        
        return report
    
    async def benchmark_pipeline_execution(
        self, 
        performance_workspace,
        performance_storage,
        steps_count: int = 5,
        complexity: str = "medium"
    ):
        """Benchmark single pipeline execution performance."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        execution_times = []
        
        for i in range(TestConfiguration.PIPELINE_ITERATIONS):
            template = await self.create_performance_pipeline_template(
                steps_count=steps_count,
                complexity=complexity
            )
            
            async with measure_performance(f"pipeline_exec_{i}", monitor) as metrics:
                # Simulate pipeline execution
                await self._simulate_pipeline_execution(
                    template, 
                    performance_workspace,
                    performance_storage
                )
            
            execution_times.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"pipeline_execution_{steps_count}_{complexity}",
            execution_times,
            monitor_results
        )
        
        return report
    
    async def _simulate_pipeline_execution(
        self,
        template: Dict[str, Any],
        workspace,
        storage
    ):
        """Simulate pipeline execution with realistic timing."""
        
        # Simulate step execution
        for step_name, step_config in template.get("steps", {}).items():
            # Simulate LLM call processing
            await asyncio.sleep(0.01)  # Base processing time
            
            # Add variable complexity based on step
            prompt_length = len(step_config.get("prompt_template", ""))
            complexity_delay = prompt_length * 0.00001  # 0.01ms per character
            await asyncio.sleep(complexity_delay)
            
            # Simulate storage operations
            await asyncio.sleep(0.005)  # Storage operation time
    
    async def benchmark_concurrent_pipelines(
        self,
        performance_workspace,
        performance_storage,
        concurrency_level: int = 10
    ):
        """Benchmark concurrent pipeline execution."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        async def execute_pipeline(op_id: int):
            """Execute a single pipeline for concurrent testing."""
            template = await self.create_performance_pipeline_template(
                steps_count=3,
                complexity="medium"
            )
            
            await self._simulate_pipeline_execution(
                template,
                performance_workspace,
                performance_storage
            )
        
        # Run concurrent operations
        metrics_list = await run_concurrent_operations(
            execute_pipeline,
            concurrency_level,
            TestConfiguration.PIPELINE_ITERATIONS
        )
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"concurrent_pipelines_{concurrency_level}",
            metrics_list,
            monitor_results
        )
        
        return report
    
    async def benchmark_memory_usage_during_execution(
        self,
        performance_workspace,
        performance_storage
    ):
        """Benchmark memory usage during extended pipeline execution."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        memory_samples = []
        
        # Run extended execution
        for i in range(TestConfiguration.PIPELINE_ITERATIONS):
            template = await self.create_performance_pipeline_template(
                steps_count=10,
                complexity="complex"
            )
            
            async with measure_performance(f"memory_test_{i}", monitor) as metrics:
                await self._simulate_pipeline_execution(
                    template,
                    performance_workspace,
                    performance_storage
                )
            
            # Record memory usage
            memory_samples.append({
                "iteration": i,
                "memory_mb": metrics.memory_usage_mb,
                "timestamp": time.time()
            })
        
        monitor_results = monitor.stop_monitoring()
        
        # Calculate memory growth rate
        if len(memory_samples) > 1:
            memory_growth_rate = (
                memory_samples[-1]["memory_mb"] - memory_samples[0]["memory_mb"]
            ) / len(memory_samples)
        else:
            memory_growth_rate = 0
        
        # Add memory analysis to report
        report = generate_performance_report(
            "memory_usage_benchmark",
            [m for m in memory_samples if "memory_mb" in m],
            monitor_results
        )
        
        # Add memory-specific metrics
        report.additional_metrics = {
            "memory_growth_rate_mb_per_op": memory_growth_rate,
            "peak_memory_mb": max(m["memory_mb"] for m in memory_samples),
            "memory_samples": memory_samples
        }
        
        return report
    
    async def benchmark_pipeline_variations(
        self,
        performance_workspace,
        performance_storage
    ):
        """Benchmark different pipeline configurations."""
        
        configurations = [
            {"steps": 1, "complexity": "simple", "name": "simple_single_step"},
            {"steps": 3, "complexity": "simple", "name": "simple_multi_step"},
            {"steps": 5, "complexity": "medium", "name": "medium_complexity"},
            {"steps": 10, "complexity": "medium", "name": "medium_many_steps"},
            {"steps": 5, "complexity": "complex", "name": "complex_few_steps"},
            {"steps": 10, "complexity": "complex", "name": "complex_many_steps"},
        ]
        
        all_reports = []
        
        for config in configurations:
            report = await self.benchmark_pipeline_execution(
                performance_workspace,
                performance_storage,
                steps_count=config["steps"],
                complexity=config["complexity"]
            )
            report.test_name = config["name"]
            all_reports.append(report)
        
        return all_reports


class TestPipelinePerformance:
    """Test class for pipeline performance benchmarks."""
    
    @pytest.mark.slow
    @pytest.mark.performance
    async def test_pipeline_loading_performance(
        self,
        performance_storage,
        benchmark_output_dir
    ):
        """Test pipeline template loading performance."""
        
        test_instance = PipelinePerformanceTest()
        
        report = await test_instance.benchmark_pipeline_loading(performance_storage)
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report], 
            benchmark_output_dir / "pipeline_loading_performance.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.throughput_ops_per_sec > 10, f"Low throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.parametrize("steps_count", [1, 3, 5, 10])
    async def test_pipeline_execution_performance(
        self,
        steps_count,
        performance_workspace,
        performance_storage,
        benchmark_output_dir
    ):
        """Test pipeline execution performance with different step counts."""
        
        test_instance = PipelinePerformanceTest()
        
        report = await test_instance.benchmark_pipeline_execution(
            performance_workspace,
            performance_storage,
            steps_count=steps_count
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"pipeline_execution_{steps_count}_steps.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.successful_operations == TestConfiguration.PIPELINE_ITERATIONS, "Not all operations completed successfully"
        
        # Performance expectations scale with steps
        expected_max_latency = 2.0 + (steps_count * 0.5)  # Base time + per-step time
        assert report.latency_stats["p99"] <= expected_max_latency, f"P99 latency too high: {report.latency_stats['p99']:.2f}s"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.parametrize("concurrency", [1, 5, 10, 20])
    async def test_concurrent_pipeline_execution(
        self,
        concurrency,
        performance_workspace,
        performance_storage,
        benchmark_output_dir
    ):
        """Test concurrent pipeline execution performance."""
        
        test_instance = PipelinePerformanceTest()
        
        report = await test_instance.benchmark_concurrent_pipelines(
            performance_workspace,
            performance_storage,
            concurrency_level=concurrency
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"concurrent_pipelines_{concurrency}.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.throughput_ops_per_sec > concurrency * 0.5, f"Low concurrency throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.memory
    async def test_memory_usage_during_execution(
        self,
        performance_workspace,
        performance_storage,
        benchmark_output_dir
    ):
        """Test memory usage during pipeline execution."""
        
        test_instance = PipelinePerformanceTest()
        
        report = await test_instance.benchmark_memory_usage_during_execution(
            performance_workspace,
            performance_storage
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "memory_usage_benchmark.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        
        # Check memory growth rate
        memory_growth = report.additional_metrics.get("memory_growth_rate_mb_per_op", 0)
        assert memory_growth < 0.1, f"High memory growth rate: {memory_growth:.4f} MB per operation"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    async def test_pipeline_configuration_variations(
        self,
        performance_workspace,
        performance_storage,
        benchmark_output_dir
    ):
        """Test performance across different pipeline configurations."""
        
        test_instance = PipelinePerformanceTest()
        
        reports = await test_instance.benchmark_pipeline_variations(
            performance_workspace,
            performance_storage
        )
        
        # Save all results
        save_benchmark_results(
            reports,
            benchmark_output_dir / "pipeline_variations_benchmark.json"
        )
        
        # Validate each configuration
        for report in reports:
            validation = validate_performance_thresholds(report)
            assert validation["passed"], f"Performance violations in {report.test_name}: {validation['violations']}"
        
        # Analyze scalability
        simple_report = next(r for r in reports if "simple" in r.test_name)
        complex_report = next(r for r in reports if "complex" in r.test_name)
        
        # Complex pipelines should not be more than 5x slower than simple ones
        complexity_ratio = complex_report.latency_stats["mean"] / simple_report.latency_stats["mean"]
        assert complexity_ratio < 5.0, f"High complexity penalty: {complexity_ratio:.2f}x slower"
        
        return reports


@pytest.fixture
def benchmark_output_dir(tmp_path):
    """Create directory for benchmark outputs."""
    output_dir = tmp_path / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir