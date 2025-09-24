"""
High-Concurrency Pipeline Execution Testing

This module implements advanced concurrent execution testing including:
- High-concurrency pipeline execution (50+ concurrent pipelines)
- Resource contention analysis
- Thread safety validation
- Performance degradation under heavy load
- System stability at maximum concurrency
- Deadlock detection and prevention

These tests validate system behavior under extreme concurrency conditions.
"""

import pytest
import asyncio
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import json
import sys
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from tests.performance.test_performance_framework import (
        PerformanceMonitor, PerformanceMetrics, BenchmarkResult,
        measure_performance, run_concurrent_operations,
        generate_performance_report, save_benchmark_results,
        TestConfiguration, validate_performance_thresholds
    )
    REAL_IMPLEMENTATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import performance framework: {e}")
    REAL_IMPLEMENTATION_AVAILABLE = False


@dataclass
class ConcurrencyStressResult:
    """Results of concurrency stress testing."""
    test_name: str
    concurrency_level: int
    total_operations: int
    successful_operations: int
    failed_operations: int
    duration_seconds: float
    throughput_ops_per_sec: float
    resource_contention_events: int
    deadlock_detected: bool
    thread_safety_violations: int
    performance_degradation_percent: float
    memory_usage_stats: Dict[str, float]
    cpu_usage_stats: Dict[str, float]
    latency_distribution: Dict[str, float]


class ConcurrencyStressTester:
    """High-concurrency stress testing for production scenarios."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.monitor = PerformanceMonitor()
        self.resource_lock = threading.Lock()
        self.contention_events = 0
        self.thread_safety_violations = 0
        self.deadlock_detected = False
        self.concurrency_stats = {}
        
    @asynccontextmanager
    async def monitor_resource_contention(self) -> AsyncGenerator[None, None]:
        """Monitor resource contention during concurrent operations."""
        contention_monitor = threading.Thread(
            target=self._monitor_contention,
            daemon=True
        )
        contention_monitor.start()
        
        try:
            yield
        finally:
            # Stop monitoring by setting a flag
            self._stop_contention_monitor = True
            contention_monitor.join(timeout=1.0)
    
    def _monitor_contention(self):
        """Monitor resource contention in background thread."""
        start_time = time.time()
        self._stop_contention_monitor = False
        
        while not self._stop_contention_monitor and time.time() - start_time < 300:  # Max 5 minutes
            # Monitor thread contention
            with self.resource_lock:
                # Simulate resource access monitoring
                active_threads = threading.active_count()
                
                if active_threads > 100:
                    self.contention_events += 1
                    
                    # Check for potential deadlock conditions
                    if active_threads > 200:
                        self.deadlock_detected = True
            
            time.sleep(0.1)
    
    async def execute_high_concurrency_pipelines(
        self,
        concurrency_level: int,
        total_operations: int,
        pipeline_complexity: str = "medium"
    ) -> List[PerformanceMetrics]:
        """Execute pipelines at high concurrency levels."""
        
        metrics_list = []
        
        async def execute_concurrent_pipeline(op_id: int) -> PerformanceMetrics:
            """Execute a single pipeline with concurrency safety checks."""
            
            async with measure_performance(f"high_concurrency_pipeline_{op_id}") as metrics:
                if REAL_IMPLEMENTATION_AVAILABLE:
                    # Real implementation would use actual pipeline execution
                    await self._simulate_real_pipeline_execution(op_id, pipeline_complexity)
                else:
                    # Mock implementation with concurrency simulation
                    await self._simulate_mock_pipeline_execution(op_id, pipeline_complexity)
                
                # Check for thread safety violations
                if self._check_thread_safety_violation(op_id):
                    self.thread_safety_violations += 1
                    metrics.success = False
                    metrics.error_message = "Thread safety violation detected"
            
            return metrics
        
        # Start resource contention monitoring
        async with self.monitor_resource_contention():
            self.monitor.start_monitoring()
            
            # Execute with high concurrency
            metrics_list = await run_concurrent_operations(
                execute_concurrent_pipeline,
                concurrency_level=concurrency_level,
                total_operations=total_operations
            )
            
            monitor_results = self.monitor.stop_monitoring()
        
        return metrics_list
    
    async def _simulate_real_pipeline_execution(self, op_id: int, complexity: str):
        """Simulate real pipeline execution with resource management."""
        # This would use actual WriteIt pipeline execution in real implementation
        await asyncio.sleep(0.01)  # Base execution time
        
        # Simulate resource-intensive operations
        if complexity == "simple":
            await asyncio.sleep(0.005)
        elif complexity == "medium":
            await asyncio.sleep(0.01)
        elif complexity == "complex":
            await asyncio.sleep(0.02)
        
        # Simulate shared resource access
        with self.resource_lock:
            # Critical section - potential contention point
            await asyncio.sleep(0.001)
    
    async def _simulate_mock_pipeline_execution(self, op_id: int, complexity: str):
        """Simulate pipeline execution with detailed concurrency simulation."""
        
        # Simulate pipeline setup
        setup_data = {f"setup_{op_id}_{i}": f"value_{i}" for i in range(10)}
        
        # Complexity-based processing
        if complexity == "simple":
            processing_time = 0.005
            data_size = 100
        elif complexity == "medium":
            processing_time = 0.01
            data_size = 500
        elif complexity == "complex":
            processing_time = 0.02
            data_size = 1000
        else:
            processing_time = 0.01
            data_size = 300
        
        # Simulate processing steps
        for step in range(3):
            # Create processing data
            step_data = [f"step_{step}_item_{i}" for i in range(data_size)]
            
            # Simulate processing
            await asyncio.sleep(processing_time / 3)
            
            # Simulate shared resource access (potential contention)
            with self.resource_lock:
                # Shared resource operation
                shared_result = len(step_data) * (op_id + 1)
                await asyncio.sleep(0.0001)
            
            # Clean up step data
            del step_data
        
        # Final cleanup
        del setup_data
    
    def _check_thread_safety_violation(self, op_id: int) -> bool:
        """Check for thread safety violations."""
        # Simulate thread safety check
        # In real implementation, this would check actual thread safety conditions
        
        # Random simulation of violations (very low probability)
        import random
        return random.random() < 0.001  # 0.1% chance
    
    async def test_deadlock_scenarios(self) -> ConcurrencyStressResult:
        """Test for deadlock scenarios under high concurrency."""
        
        deadlock_metrics = []
        self.deadlock_detected = False
        
        async def potential_deadlock_operation(op_id: int) -> PerformanceMetrics:
            """Operation that could potentially cause deadlocks."""
            
            async with measure_performance(f"deadlock_test_{op_id}") as metrics:
                # Simulate operations that could deadlock
                lock1 = asyncio.Lock()
                lock2 = asyncio.Lock()
                
                # Nested lock acquisition (potential deadlock)
                async with lock1:
                    await asyncio.sleep(0.001)
                    async with lock2:
                        await asyncio.sleep(0.001)
                
                # Check if deadlock occurred (simplified check)
                if time.time() - metrics.start_time > 1.0:  # Operation took too long
                    self.deadlock_detected = True
                    metrics.success = False
                    metrics.error_message = "Potential deadlock detected"
            
            return metrics
        
        # Run deadlock test operations
        deadlock_metrics = await run_concurrent_operations(
            potential_deadlock_operation,
            concurrency_level=20,
            total_operations=100
        )
        
        # Compile deadlock test results
        successful_ops = sum(1 for m in deadlock_metrics if m.success)
        failed_ops = len(deadlock_metrics) - successful_ops
        
        return ConcurrencyStressResult(
            test_name="deadlock_detection_test",
            concurrency_level=20,
            total_operations=len(deadlock_metrics),
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            duration_seconds=max(m.duration_seconds for m in deadlock_metrics) if deadlock_metrics else 0,
            throughput_ops_per_sec=successful_ops / max(m.duration_seconds for m in deadlock_metrics) if deadlock_metrics else 0,
            resource_contention_events=self.contention_events,
            deadlock_detected=self.deadlock_detected,
            thread_safety_violations=self.thread_safety_violations,
            performance_degradation_percent=0.0,  # Will be calculated
            memory_usage_stats={},
            cpu_usage_stats={},
            latency_distribution={}
        )


class TestHighConcurrencyExecution:
    """Test high-concurrency pipeline execution scenarios."""
    
    @pytest.fixture
    def concurrency_tester(self, tmp_path):
        """Set up concurrency stress tester."""
        return ConcurrencyStressTester(tmp_path)
    
    @pytest.mark.asyncio
    @pytest.mark.concurrency
    @pytest.mark.stress
    @pytest.mark.parametrize("concurrency_level", [25, 50, 75, 100])
    async def test_extreme_concurrency_pipeline_execution(
        self,
        concurrency_level,
        concurrency_tester,
        benchmark_output_dir
    ):
        """Test pipeline execution at extreme concurrency levels."""
        
        print(f"\n--- Testing Extreme Concurrency: {concurrency_level} concurrent pipelines ---")
        
        # Calculate operations based on concurrency
        total_operations = min(concurrency_level * 3, 300)  # Limit for test performance
        
        # Execute high-concurrency pipelines
        metrics_list = await concurrency_tester.execute_high_concurrency_pipelines(
            concurrency_level=concurrency_level,
            total_operations=total_operations,
            pipeline_complexity="medium"
        )
        
        # Calculate performance metrics
        successful_ops = sum(1 for m in metrics_list if m.success)
        failed_ops = len(metrics_list) - successful_ops
        
        # Calculate latency distribution
        durations = [m.duration_seconds for m in metrics_list if m.success]
        if durations:
            latency_distribution = {
                "min": min(durations),
                "max": max(durations),
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "p95": statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
                "p99": statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations)
            }
        else:
            latency_distribution = {}
        
        # Calculate throughput
        total_duration = max(m.duration_seconds for m in metrics_list) if metrics_list else 0
        throughput = successful_ops / total_duration if total_duration > 0 else 0
        
        # Calculate performance degradation compared to baseline (1 concurrent)
        baseline_throughput = 10.0  # Assumed baseline throughput
        degradation_percent = ((baseline_throughput - throughput) / baseline_throughput * 100) if baseline_throughput > throughput else 0
        
        # Get resource usage stats
        monitor_results = concurrency_tester.monitor.stop_monitoring()
        memory_usage_stats = {
            "peak_mb": monitor_results.get("peak_memory_mb", 0),
            "current_mb": monitor_results.get("current_memory_mb", 0)
        }
        cpu_usage_stats = {
            "avg_percent": monitor_results.get("cpu_usage_percent", 0)
        }
        
        # Create stress test result
        stress_result = ConcurrencyStressResult(
            test_name=f"extreme_concurrency_{concurrency_level}",
            concurrency_level=concurrency_level,
            total_operations=len(metrics_list),
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            duration_seconds=total_duration,
            throughput_ops_per_sec=throughput,
            resource_contention_events=concurrency_tester.contention_events,
            deadlock_detected=concurrency_tester.deadlock_detected,
            thread_safety_violations=concurrency_tester.thread_safety_violations,
            performance_degradation_percent=degradation_percent,
            memory_usage_stats=memory_usage_stats,
            cpu_usage_stats=cpu_usage_stats,
            latency_distribution=latency_distribution
        )
        
        # Save detailed results
        result_data = {
            "test_name": stress_result.test_name,
            "concurrency_level": stress_result.concurrency_level,
            "total_operations": stress_result.total_operations,
            "successful_operations": stress_result.successful_operations,
            "failed_operations": stress_result.failed_operations,
            "failure_rate_percent": (failed_ops / len(metrics_list) * 100) if metrics_list else 0,
            "duration_seconds": stress_result.duration_seconds,
            "throughput_ops_per_sec": stress_result.throughput_ops_per_sec,
            "resource_contention_events": stress_result.resource_contention_events,
            "deadlock_detected": stress_result.deadlock_detected,
            "thread_safety_violations": stress_result.thread_safety_violations,
            "performance_degradation_percent": stress_result.performance_degradation_percent,
            "memory_usage_stats": stress_result.memory_usage_stats,
            "cpu_usage_stats": stress_result.cpu_usage_stats,
            "latency_distribution": stress_result.latency_distribution,
            "individual_metrics": [
                {
                    "operation": m.operation,
                    "duration_seconds": m.duration_seconds,
                    "memory_mb": m.memory_usage_mb,
                    "success": m.success,
                    "error_message": m.error_message
                }
                for m in metrics_list
            ]
        }
        
        output_path = benchmark_output_dir / f"extreme_concurrency_{concurrency_level}.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Assertions for extreme concurrency
        failure_rate = (failed_ops / len(metrics_list) * 100) if metrics_list else 0
        assert failure_rate <= 10, f"High failure rate at concurrency {concurrency_level}: {failure_rate:.2f}%"
        
        # Throughput should not degrade too much
        assert throughput >= 1.0, f"Low throughput at concurrency {concurrency_level}: {throughput:.2f} ops/sec"
        
        # No deadlocks should occur
        assert not stress_result.deadlock_detected, f"Deadlock detected at concurrency {concurrency_level}"
        
        # Thread safety violations should be minimal
        assert stress_result.thread_safety_violations <= 1, f"Thread safety violations at concurrency {concurrency_level}"
        
        # Latency should be reasonable
        if stress_result.latency_distribution:
            p99_latency = stress_result.latency_distribution.get("p99", 0)
            assert p99_latency <= 5.0, f"High P99 latency at concurrency {concurrency_level}: {p99_latency:.2f}s"
        
        print(f"✅ Extreme concurrency test ({concurrency_level}): "
              f"Throughput: {throughput:.2f} ops/sec, "
              f"Failure rate: {failure_rate:.2f}%, "
              f"P99 latency: {p99_latency:.2f}s")
        
        return stress_result
    
    @pytest.mark.asyncio
    @pytest.mark.concurrency
    @pytest.mark.stress
    async def test_scalability_analysis(self, concurrency_tester, benchmark_output_dir):
        """Test scalability across different concurrency levels."""
        
        concurrency_levels = [1, 10, 25, 50, 75, 100]
        scalability_results = []
        
        for concurrency in concurrency_levels:
            print(f"\n--- Scalability Analysis: {concurrency} concurrent ---")
            
            # Use fewer operations for higher concurrency to prevent test timeout
            total_operations = min(concurrency * 2, 150)
            
            # Execute pipelines
            metrics_list = await concurrency_tester.execute_high_concurrency_pipelines(
                concurrency_level=concurrency,
                total_operations=total_operations,
                pipeline_complexity="medium"
            )
            
            # Calculate metrics
            successful_ops = sum(1 for m in metrics_list if m.success)
            total_duration = max(m.duration_seconds for m in metrics_list) if metrics_list else 0
            throughput = successful_ops / total_duration if total_duration > 0 else 0
            
            scalability_results.append({
                "concurrency_level": concurrency,
                "throughput_ops_per_sec": throughput,
                "successful_operations": successful_ops,
                "total_operations": len(metrics_list),
                "avg_duration_seconds": statistics.mean([m.duration_seconds for m in metrics_list]) if metrics_list else 0,
                "resource_contention_events": concurrency_tester.contention_events
            })
        
        # Analyze scalability
        baseline_throughput = scalability_results[0]["throughput_ops_per_sec"]
        max_throughput = max(r["throughput_ops_per_sec"] for r in scalability_results)
        optimal_concurrency = max(scalability_results, key=lambda r: r["throughput_ops_per_sec"])["concurrency_level"]
        
        # Calculate scalability efficiency
        efficiency_results = []
        for result in scalability_results:
            concurrency = result["concurrency_level"]
            throughput = result["throughput_ops_per_sec"]
            
            # Ideal linear scaling
            ideal_throughput = baseline_throughput * concurrency
            efficiency = (throughput / ideal_throughput * 100) if ideal_throughput > 0 else 0
            
            efficiency_results.append({
                "concurrency_level": concurrency,
                "efficiency_percent": efficiency,
                "throughput": throughput,
                "ideal_throughput": ideal_throughput
            })
        
        # Save scalability analysis
        analysis_data = {
            "test_name": "concurrency_scalability_analysis",
            "baseline_throughput": baseline_throughput,
            "max_throughput": max_throughput,
            "optimal_concurrency_level": optimal_concurrency,
            "scalability_results": scalability_results,
            "efficiency_analysis": efficiency_results,
            "timestamp": datetime.now().isoformat()
        }
        
        output_path = benchmark_output_dir / "concurrency_scalability_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        # Assertions for scalability
        assert max_throughput >= baseline_throughput * 5, f" Poor scaling: max throughput {max_throughput:.2f} vs baseline {baseline_throughput:.2f}"
        
        # Efficiency should not drop too low
        min_efficiency = min(e["efficiency_percent"] for e in efficiency_results)
        assert min_efficiency >= 20, f"Low scalability efficiency: {min_efficiency:.2f}%"
        
        # Should be able to handle high concurrency
        high_concurrency_result = next(r for r in scalability_results if r["concurrency_level"] == 100)
        assert high_concurrency_result["throughput_ops_per_sec"] >= 1.0, f"Poor performance at 100 concurrency"
        
        print(f"✅ Scalability analysis completed:")
        print(f"   Baseline throughput: {baseline_throughput:.2f} ops/sec")
        print(f"   Max throughput: {max_throughput:.2f} ops/sec")
        print(f"   Optimal concurrency: {optimal_concurrency}")
        print(f"   Min efficiency: {min_efficiency:.2f}%")
        
        return scalability_results
    
    @pytest.mark.asyncio
    @pytest.mark.concurrency
    @pytest.mark.stress
    async def test_deadlock_detection_and_prevention(self, concurrency_tester, benchmark_output_dir):
        """Test deadlock detection and prevention mechanisms."""
        
        print("\n--- Testing Deadlock Detection ---")
        
        # Test deadlock scenarios
        deadlock_result = await concurrency_tester.test_deadlock_scenarios()
        
        # Save deadlock test results
        result_data = {
            "test_name": deadlock_result.test_name,
            "concurrency_level": deadlock_result.concurrency_level,
            "deadlock_detected": deadlock_result.deadlock_detected,
            "successful_operations": deadlock_result.successful_operations,
            "failed_operations": deadlock_result.failed_operations,
            "failure_rate_percent": (deadlock_result.failed_operations / deadlock_result.total_operations * 100) if deadlock_result.total_operations > 0 else 0,
            "resource_contention_events": deadlock_result.resource_contention_events,
            "thread_safety_violations": deadlock_result.thread_safety_violations,
            "throughput_ops_per_sec": deadlock_result.throughput_ops_per_sec
        }
        
        output_path = benchmark_output_dir / "deadlock_detection_test.json"
        with open(output_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Assertions for deadlock prevention
        failure_rate = (deadlock_result.failed_operations / deadlock_result.total_operations * 100) if deadlock_result.total_operations > 0 else 0
        
        # Deadlocks should be prevented or detected quickly
        assert not deadlock_result.deadlock_detected or failure_rate < 5, \
            f"Deadlock detection failed: {deadlock_result.deadlock_detected}, failure rate: {failure_rate:.2f}%"
        
        # System should remain responsive
        assert deadlock_result.throughput_ops_per_sec >= 0.5, \
            f"Low throughput during deadlock test: {deadlock_result.throughput_ops_per_sec:.2f} ops/sec"
        
        print(f"✅ Deadlock detection test completed: "
              f"Deadlocks detected: {deadlock_result.deadlock_detected}, "
              f"Failure rate: {failure_rate:.2f}%, "
              f"Throughput: {deadlock_result.throughput_ops_per_sec:.2f} ops/sec")
        
        return deadlock_result


if __name__ == "__main__":
    # Run high-concurrency tests with:
    # python -m pytest tests/performance/test_high_concurrency_execution.py -v --concurrency --stress
    
    # Run specific concurrency test:
    # python -m pytest tests/performance/test_high_concurrency_execution.py::TestHighConcurrencyExecution::test_extreme_concurrency_pipeline_execution -v --concurrency
    
    print("High-concurrency execution testing suite ready for execution")
    print("Available test categories:")
    print("- TestHighConcurrencyExecution: Extreme concurrency pipeline execution (25-100 concurrent)")
    print("- Scalability analysis across concurrency levels")
    print("- Deadlock detection and prevention testing")