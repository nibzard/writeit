"""Concurrent execution tests with multiple pipelines.

This module provides comprehensive testing for:
- Multiple pipeline execution concurrency
- Resource contention and synchronization
- Performance under high concurrency
- Thread safety and isolation
- Deadlock detection
"""

import asyncio
import pytest
import time
import threading
from typing import Dict, List, Any, Optional, AsyncGenerator
import tempfile
import shutil
from pathlib import Path
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

from tests.utils.workspace_helpers import create_test_workspace
from tests.utils.storage_helpers import setup_test_storage


class ConcurrentExecutionTest:
    """Test concurrent execution of multiple pipelines."""
    
    @pytest.fixture
    async def concurrent_test_workspaces(self):
        """Create multiple workspaces for concurrent testing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="concurrent_test_"))
        workspaces = []
        
        try:
            for i in range(5):
                workspace_name = f"concurrent_workspace_{i}"
                workspace = await create_test_workspace(workspace_name, temp_dir)
                workspaces.append(workspace)
            yield workspaces
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    async def concurrent_test_storage(self, concurrent_test_workspaces):
        """Set up storage for concurrent workspaces."""
        storage_managers = []
        for workspace in concurrent_test_workspaces:
            storage = await setup_test_storage(workspace.name)
            storage_managers.append(storage)
        return storage_managers
    
    async def create_concurrent_pipeline_template(
        self, 
        pipeline_id: int,
        duration_seconds: float = 1.0,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """Create pipeline template for concurrent testing."""
        
        if complexity == "simple":
            steps_count = 2
            step_duration = duration_seconds / 2
        elif complexity == "medium":
            steps_count = 4
            step_duration = duration_seconds / 4
        elif complexity == "complex":
            steps_count = 6
            step_duration = duration_seconds / 6
        else:
            steps_count = 3
            step_duration = duration_seconds / 3
        
        steps = {}
        for i in range(steps_count):
            step_name = f"step_{i+1}"
            steps[step_name] = {
                "name": f"Step {i+1}",
                "description": f"Concurrent test step {i+1}",
                "type": "llm_generate",
                "prompt_template": f"Process content for pipeline {pipeline_id}, step {i+1}",
                "model_preference": ["mock-model"],
                "depends_on": [f"step_{j}" for j in range(i)] if i > 0 else []
            }
        
        return {
            "metadata": {
                "name": f"concurrent_pipeline_{pipeline_id}",
                "description": f"Concurrent test pipeline {pipeline_id}",
                "version": "1.0.0"
            },
            "defaults": {
                "model": "mock-model"
            },
            "inputs": {
                "content": {
                    "type": "text",
                    "label": "Content",
                    "required": True,
                    "default": f"Test content for pipeline {pipeline_id}"
                }
            },
            "steps": steps
        }
    
    async def execute_single_pipeline(
        self,
        pipeline_id: int,
        workspace,
        storage,
        duration_seconds: float = 1.0
    ):
        """Execute a single pipeline for concurrent testing."""
        
        template = await self.create_concurrent_pipeline_template(
            pipeline_id,
            duration_seconds
        )
        
        # Simulate pipeline execution
        execution_start = time.time()
        
        for step_name, step_config in template.get("steps", {}).items():
            # Simulate step execution with realistic timing
            await asyncio.sleep(duration_seconds / len(template["steps"]))
            
            # Simulate storage operations
            await asyncio.sleep(0.01)
        
        execution_time = time.time() - execution_start
        
        return {
            "pipeline_id": pipeline_id,
            "execution_time": execution_time,
            "workspace": workspace.name,
            "steps_count": len(template.get("steps", [])),
            "success": True
        }
    
    async def benchmark_concurrent_pipeline_execution(
        self,
        concurrent_test_workspaces,
        concurrent_test_storage,
        concurrency_level: int = 10,
        pipeline_duration: float = 1.0
    ):
        """Benchmark concurrent pipeline execution performance."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        async def execute_pipeline_op(op_id: int):
            """Execute a pipeline operation."""
            workspace_index = op_id % len(concurrent_test_workspaces)
            storage_index = op_id % len(concurrent_test_storage)
            
            return await self.execute_single_pipeline(
                op_id,
                concurrent_test_workspaces[workspace_index],
                concurrent_test_storage[storage_index],
                pipeline_duration
            )
        
        # Run concurrent operations
        total_operations = concurrency_level * 2  # 2 operations per concurrency level
        metrics_list = await run_concurrent_operations(
            execute_pipeline_op,
            concurrency_level,
            total_operations
        )
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"concurrent_pipelines_{concurrency_level}",
            metrics_list,
            monitor_results
        )
        
        return report
    
    async def benchmark_resource_contention(
        self,
        concurrent_test_workspaces,
        concurrent_test_storage,
        contention_level: int = 20
    ):
        """Benchmark performance under resource contention."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Shared resource simulation
        shared_resource = {
            "lock": asyncio.Lock(),
            "access_count": 0,
            "contention_events": []
        }
        
        async def contend_for_resource(op_id: int):
            """Operation that contends for shared resource."""
            start_time = time.time()
            contention_time = None
            
            async with shared_resource["lock"]:
                contention_time = time.time() - start_time
                shared_resource["access_count"] += 1
                
                # Simulate resource usage
                await asyncio.sleep(0.1)
                
                if contention_time > 0.05:  # 50ms contention threshold
                    shared_resource["contention_events"].append({
                        "operation_id": op_id,
                        "contention_time": contention_time
                    })
            
            # Simulate additional processing
            await asyncio.sleep(0.05)
            
            return {
                "operation_id": op_id,
                "contention_time": contention_time or 0,
                "access_count": shared_resource["access_count"]
            }
        
        # Run contending operations
        metrics_list = await run_concurrent_operations(
            contend_for_resource,
            contention_level,
            contention_level
        )
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"resource_contention_{contention_level}",
            metrics_list,
            monitor_results
        )
        
        # Add contention-specific metrics
        report.additional_metrics = {
            "total_contention_events": len(shared_resource["contention_events"]),
            "average_contention_time": sum(e["contention_time"] for e in shared_resource["contention_events"]) / len(shared_resource["contention_events"]) if shared_resource["contention_events"] else 0,
            "max_contention_time": max(e["contention_time"] for e in shared_resource["contention_events"]) if shared_resource["contention_events"] else 0,
            "contention_events": shared_resource["contention_events"]
        }
        
        return report
    
    async def benchmark_thread_safety(
        self,
        concurrent_test_workspaces,
        concurrent_test_storage
    ):
        """Benchmark thread safety of concurrent operations."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Shared data structure for testing
        shared_counter = {"value": 0, "lock": threading.Lock()}
        thread_results = []
        
        def thread_operation(thread_id: int, operations_count: int):
            """Thread-safe operation."""
            local_results = []
            
            for i in range(operations_count):
                start_time = time.time()
                
                # Thread-safe counter increment
                with shared_counter["lock"]:
                    shared_counter["value"] += 1
                    current_value = shared_counter["value"]
                
                # Simulate work
                time.sleep(0.001)
                
                local_results.append({
                    "thread_id": thread_id,
                    "operation_id": i,
                    "counter_value": current_value,
                    "duration": time.time() - start_time
                })
            
            thread_results.extend(local_results)
        
        # Create and run threads
        threads = []
        thread_count = 10
        operations_per_thread = 100
        
        for i in range(thread_count):
            thread = threading.Thread(
                target=thread_operation,
                args=(i, operations_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        start_time = time.time()
        for thread in threads:
            thread.join()
        
        total_duration = time.time() - start_time
        
        # Analyze thread safety
        expected_counter = thread_count * operations_per_thread
        actual_counter = shared_counter["value"]
        thread_safety_issues = expected_counter != actual_counter
        
        # Create metrics for reporting
        metrics_list = []
        for result in thread_results[:1000]:  # Limit for reporting
            metrics_list.append(PerformanceMetrics(
                operation=f"thread_op_{result['thread_id']}_{result['operation_id']}",
                duration_seconds=result['duration'],
                memory_usage_mb=0,
                cpu_usage_percent=0,
                success=True
            ))
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "thread_safety_benchmark",
            metrics_list,
            monitor_results
        )
        
        # Add thread-safety specific metrics
        report.additional_metrics = {
            "thread_count": thread_count,
            "operations_per_thread": operations_per_thread,
            "expected_counter_value": expected_counter,
            "actual_counter_value": actual_counter,
            "thread_safety_issues": thread_safety_issues,
            "total_duration_seconds": total_duration,
            "throughput_ops_per_sec": (thread_count * operations_per_thread) / total_duration
        }
        
        return report
    
    async def benchmark_deadlock_detection(
        self,
        concurrent_test_workspaces,
        concurrent_test_storage
    ):
        """Benchmark deadlock detection and prevention."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Create potential deadlock scenario
        lock1 = asyncio.Lock()
        lock2 = asyncio.Lock()
        deadlock_detected = False
        deadlock_operations = []
        
        async def operation_with_potential_deadlock(op_id: int, first_lock: asyncio.Lock, second_lock: asyncio.Lock):
            """Operation that could cause deadlock if not properly ordered."""
            start_time = time.time()
            
            try:
                # Use asyncio.wait_for to detect potential deadlocks
                async with asyncio.wait_for(first_lock.acquire(), timeout=1.0):
                    # Small delay to increase deadlock probability
                    await asyncio.sleep(0.01)
                    
                    async with asyncio.wait_for(second_lock.acquire(), timeout=1.0):
                        # Critical section
                        await asyncio.sleep(0.01)
                        second_lock.release()
                    
                    first_lock.release()
                
                success = True
                
            except asyncio.TimeoutError:
                # Potential deadlock detected
                deadlock_detected = True
                success = False
                
                # Release locks if held
                if first_lock.locked():
                    first_lock.release()
                if second_lock.locked():
                    second_lock.release()
            
            duration = time.time() - start_time
            deadlock_operations.append({
                "operation_id": op_id,
                "duration": duration,
                "success": success,
                "deadlock_detected": deadlock_detected
            })
            
            return success
        
        # Run operations with potential deadlock
        tasks = []
        for i in range(10):
            if i % 2 == 0:
                # Operations that acquire locks in different orders
                task1 = operation_with_potential_deadlock(i * 2, lock1, lock2)
                task2 = operation_with_potential_deadlock(i * 2 + 1, lock2, lock1)
                tasks.extend([task1, task2])
            else:
                # Safe operations
                task = operation_with_potential_deadlock(i, lock1, lock2)
                tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time
        
        # Create metrics for reporting
        metrics_list = []
        for i, result in enumerate(results):
            if isinstance(result, bool):
                metrics_list.append(PerformanceMetrics(
                    operation=f"deadlock_test_{i}",
                    duration_seconds=total_duration / len(results),
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    success=result
                ))
            else:
                metrics_list.append(PerformanceMetrics(
                    operation=f"deadlock_test_{i}",
                    duration_seconds=total_duration / len(results),
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(result)
                ))
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "deadlock_detection_benchmark",
            metrics_list,
            monitor_results
        )
        
        # Add deadlock-specific metrics
        successful_operations = sum(1 for r in results if isinstance(r, bool) and r)
        report.additional_metrics = {
            "deadlock_detected": deadlock_detected,
            "successful_operations": successful_operations,
            "failed_operations": len(results) - successful_operations,
            "deadlock_operations": deadlock_operations,
            "total_duration_seconds": total_duration
        }
        
        return report


class TestConcurrentExecution:
    """Test class for concurrent execution."""
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.parametrize("concurrency_level", [5, 10, 20, 50])
    async def test_concurrent_pipeline_execution(
        self,
        concurrency_level,
        concurrent_test_workspaces,
        concurrent_test_storage,
        benchmark_output_dir
    ):
        """Test concurrent pipeline execution performance."""
        
        test_instance = ConcurrentExecutionTest()
        
        report = await test_instance.benchmark_concurrent_pipeline_execution(
            concurrent_test_workspaces,
            concurrent_test_storage,
            concurrency_level=concurrency_level,
            pipeline_duration=0.5  # Shorter for CI
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"concurrent_pipelines_{concurrency_level}.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.successful_operations > 0, "No successful operations"
        
        # Throughput should scale with concurrency (with diminishing returns)
        expected_min_throughput = concurrency_level * 0.5  # Conservative estimate
        assert report.throughput_ops_per_sec > expected_min_throughput, f"Low throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.parametrize("contention_level", [10, 20, 50])
    async def test_resource_contention(
        self,
        contention_level,
        concurrent_test_workspaces,
        concurrent_test_storage,
        benchmark_output_dir
    ):
        """Test performance under resource contention."""
        
        test_instance = ConcurrentExecutionTest()
        
        report = await test_instance.benchmark_resource_contention(
            concurrent_test_workspaces,
            concurrent_test_storage,
            contention_level=contention_level
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"resource_contention_{contention_level}.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        
        # Check contention-specific metrics
        additional_metrics = report.additional_metrics or {}
        avg_contention = additional_metrics.get("average_contention_time", 0)
        max_contention = additional_metrics.get("max_contention_time", 0)
        
        # Contention should be reasonable
        assert avg_contention < 0.1, f"High average contention time: {avg_contention:.3f}s"
        assert max_contention < 0.5, f"High max contention time: {max_contention:.3f}s"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    async def test_thread_safety(
        self,
        concurrent_test_workspaces,
        concurrent_test_storage,
        benchmark_output_dir
    ):
        """Test thread safety of concurrent operations."""
        
        test_instance = ConcurrentExecutionTest()
        
        report = await test_instance.benchmark_thread_safety(
            concurrent_test_workspaces,
            concurrent_test_storage
        )
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "thread_safety_benchmark.json"
        )
        
        # Assertions
        # Thread safety should be maintained
        additional_metrics = report.additional_metrics or {}
        thread_safety_issues = additional_metrics.get("thread_safety_issues", False)
        
        assert not thread_safety_issues, "Thread safety issues detected"
        
        # Performance should be reasonable
        assert report.throughput_ops_per_sec > 100, f"Low thread-safe throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    async def test_deadlock_detection(
        self,
        concurrent_test_workspaces,
        concurrent_test_storage,
        benchmark_output_dir
    ):
        """Test deadlock detection and prevention."""
        
        test_instance = ConcurrentExecutionTest()
        
        report = await test_instance.benchmark_deadlock_detection(
            concurrent_test_workspaces,
            concurrent_test_storage
        )
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "deadlock_detection_benchmark.json"
        )
        
        # Assertions
        # Deadlock detection should work
        additional_metrics = report.additional_metrics or {}
        deadlock_detected = additional_metrics.get("deadlock_detected", False)
        successful_operations = additional_metrics.get("successful_operations", 0)
        
        # Either no deadlock was detected, or it was handled properly
        if deadlock_detected:
            # If deadlock was detected, most operations should still succeed
            success_rate = successful_operations / report.total_operations
            assert success_rate > 0.8, f"Low success rate during deadlock test: {success_rate:.2%}"
        else:
            # If no deadlock detected, all operations should succeed
            assert successful_operations == report.total_operations, "Not all operations succeeded without deadlock"
        
        # Performance should be reasonable
        assert report.duration_seconds < 5.0, f"Deadlock test took too long: {report.duration_seconds:.2f}s"
        
        return report


@pytest.fixture
def benchmark_output_dir(tmp_path):
    """Create directory for benchmark outputs."""
    output_dir = tmp_path / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir