"""Multiple workspace operations performance testing.

This module provides comprehensive testing for:
- Multi-workspace concurrent operations
- Workspace isolation performance
- Cross-workspace resource sharing
- Workspace switching overhead
- Scalability with increasing workspace count
"""

import asyncio
import pytest
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, List, Any, AsyncGenerator, Optional
import uuid
import json

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


class MultiWorkspacePerformanceTest:
    """Performance testing for multiple workspace operations."""
    
    @pytest.fixture
    async def multi_workspaces_setup(self):
        """Create multiple workspaces for testing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="multi_workspace_test_"))
        workspaces = []
        
        try:
            workspace_counts = [5, 10, 25, 50]
            all_workspaces = {}
            
            for count in workspace_counts:
                workspaces_for_count = []
                for i in range(count):
                    workspace_name = f"multi_ws_{count}_{i}"
                    workspace = await create_test_workspace(workspace_name, temp_dir)
                    workspaces_for_count.append(workspace)
                all_workspaces[count] = workspaces_for_count
            
            yield all_workspaces
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    async def multi_workspace_storage(self, multi_workspaces_setup):
        """Set up storage for multiple workspaces."""
        storage_managers = {}
        
        for count, workspaces in multi_workspaces_setup.items():
            managers_for_count = []
            for workspace in workspaces:
                storage = await setup_test_storage(workspace.name)
                managers_for_count.append(storage)
            storage_managers[count] = managers_for_count
        
        return storage_managers
    
    async def benchmark_workspace_creation_performance(
        self,
        workspace_counts: List[int] = [5, 10, 25, 50]
    ):
        """Benchmark workspace creation performance at different scales."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        results_by_count = {}
        
        for count in workspace_counts:
            temp_dir = Path(tempfile.mkdtemp(prefix=f"ws_creation_{count}_"))
            creation_times = []
            
            try:
                for i in range(count):
                    workspace_name = f"perf_ws_{count}_{i}"
                    
                    async with measure_performance(f"workspace_creation_{count}_{i}", monitor) as metrics:
                        await create_test_workspace(workspace_name, temp_dir)
                    
                    creation_times.append(metrics)
                
                # Generate report for this count
                monitor_results = monitor.stop_monitoring()
                report = generate_performance_report(
                    f"workspace_creation_{count}_workspaces",
                    creation_times,
                    monitor_results
                )
                
                results_by_count[count] = report
                
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Create combined report
        all_metrics = []
        for count, report in results_by_count.items():
            for metric in creation_times:
                all_metrics.append(PerformanceMetrics(
                    operation=f"workspace_creation_scalability",
                    duration_seconds=report.latency_stats["mean"],
                    memory_usage_mb=report.memory_stats["avg_mb"],
                    cpu_usage_percent=report.cpu_stats["avg_percent"],
                    success=True
                ))
        
        combined_report = generate_performance_report(
            "workspace_creation_scalability",
            all_metrics,
            None
        )
        
        # Add scalability analysis
        combined_report.additional_metrics = {
            "creation_times_by_count": {
                count: {
                    "mean_creation_time": report.latency_stats["mean"],
                    "total_creation_time": report.latency_stats["mean"] * count,
                    "throughput_workspaces_per_sec": count / report.latency_stats["mean"] if report.latency_stats["mean"] > 0 else 0
                }
                for count, report in results_by_count.items()
            }
        }
        
        return combined_report
    
    async def benchmark_concurrent_workspace_operations(
        self,
        multi_workspaces_setup,
        multi_workspace_storage,
        workspace_count: int = 10,
        operations_per_workspace: int = 20
    ):
        """Benchmark concurrent operations across multiple workspaces."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        workspaces = multi_workspaces_setup.get(workspace_count, [])
        storage_managers = multi_workspace_storage.get(workspace_count, [])
        
        if not workspaces:
            raise ValueError(f"No workspaces available for count {workspace_count}")
        
        async def workspace_operation(op_id: int):
            """Single operation across workspaces."""
            workspace_index = op_id % len(workspaces)
            storage_index = op_id % len(storage_managers)
            
            workspace = workspaces[workspace_index]
            storage = storage_managers[storage_index]
            
            # Simulate workspace-specific operation
            await self._simulate_workspace_operation(
                workspace,
                storage,
                f"operation_{op_id}"
            )
        
        total_operations = workspace_count * operations_per_workspace
        concurrency_level = min(workspace_count * 2, 50)  # Reasonable concurrency
        
        metrics_list = await run_concurrent_operations(
            workspace_operation,
            concurrency_level,
            total_operations
        )
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"concurrent_workspace_operations_{workspace_count}",
            metrics_list,
            monitor_results
        )
        
        return report
    
    async def _simulate_workspace_operation(
        self,
        workspace,
        storage,
        operation_id: str
    ):
        """Simulate a workspace-specific operation."""
        
        # Simulate workspace data access
        await asyncio.sleep(0.01)
        
        # Simulate storage operation
        await asyncio.sleep(0.005)
        
        # Simulate processing
        await asyncio.sleep(0.02)
    
    async def benchmark_workspace_switching_performance(
        self,
        multi_workspaces_setup,
        multi_workspace_storage
    ):
        """Benchmark workspace switching overhead."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Use a moderate number of workspaces for switching test
        workspaces = multi_workspaces_setup.get(10, [])
        storage_managers = multi_workspace_storage.get(10, [])
        
        if not workspaces:
            # Create workspaces if not available
            temp_dir = Path(tempfile.mkdtemp(prefix="ws_switching_test_"))
            try:
                workspaces = []
                storage_managers = []
                
                for i in range(10):
                    workspace_name = f"switching_ws_{i}"
                    workspace = await create_test_workspace(workspace_name, temp_dir)
                    storage = await setup_test_storage(workspace_name)
                    workspaces.append(workspace)
                    storage_managers.append(storage)
            finally:
                # Note: In real implementation, we'd clean up properly
                pass
        
        switching_times = []
        switch_sequences = 100  # Number of workspace switches to test
        
        for i in range(switch_sequences):
            # Switch between workspaces
            from_workspace_idx = i % len(workspaces)
            to_workspace_idx = (i + 1) % len(workspaces)
            
            from_workspace = workspaces[from_workspace_idx]
            to_workspace = workspaces[to_workspace_idx]
            from_storage = storage_managers[from_workspace_idx]
            to_storage = storage_managers[to_workspace_idx]
            
            async with measure_performance(f"workspace_switch_{i}", monitor) as metrics:
                # Simulate workspace switching operations
                await self._simulate_workspace_switch(
                    from_workspace,
                    to_workspace,
                    from_storage,
                    to_storage
                )
            
            switching_times.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "workspace_switching_performance",
            switching_times,
            monitor_results
        )
        
        return report
    
    async def _simulate_workspace_switch(
        self,
        from_workspace,
        to_workspace,
        from_storage,
        to_storage
    ):
        """Simulate workspace switching operations."""
        
        # Simulate context cleanup for from_workspace
        await asyncio.sleep(0.001)
        
        # Simulate context setup for to_workspace
        await asyncio.sleep(0.001)
        
        # Simulate storage context switch
        await asyncio.sleep(0.002)
        
        # Simulate operation in new workspace
        await asyncio.sleep(0.01)
    
    async def benchmark_cross_workspace_data_transfer(
        self,
        multi_workspaces_setup,
        multi_workspace_storage
    ):
        """Benchmark performance of data transfer between workspaces."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Use a subset of workspaces for transfer testing
        workspaces = multi_workspaces_setup.get(5, [])
        storage_managers = multi_workspace_storage.get(5, [])
        
        if len(workspaces) < 2:
            raise ValueError("Need at least 2 workspaces for transfer testing")
        
        transfer_operations = []
        
        for i in range(50):  # 50 transfer operations
            from_workspace_idx = i % len(workspaces)
            to_workspace_idx = (i + 1) % len(workspaces)
            
            from_workspace = workspaces[from_workspace_idx]
            to_workspace = workspaces[to_workspace_idx]
            from_storage = storage_managers[from_workspace_idx]
            to_storage = storage_managers[to_workspace_idx]
            
            # Create test data to transfer
            data_size = 1000 + (i % 5) * 1000  # 1KB to 5KB
            test_data = {
                "transfer_id": f"transfer_{i}",
                "data": "x" * data_size,
                "metadata": {
                    "source_workspace": from_workspace.name,
                    "target_workspace": to_workspace.name,
                    "timestamp": time.time()
                }
            }
            
            async with measure_performance(f"data_transfer_{i}", monitor) as metrics:
                await self._simulate_data_transfer(
                    from_workspace,
                    to_workspace,
                    from_storage,
                    to_storage,
                    test_data
                )
            
            transfer_operations.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "cross_workspace_data_transfer",
            transfer_operations,
            monitor_results
        )
        
        return report
    
    async def _simulate_data_transfer(
        self,
        from_workspace,
        to_workspace,
        from_storage,
        to_storage,
        data: Dict[str, Any]
    ):
        """Simulate data transfer between workspaces."""
        
        # Simulate data read from source
        await asyncio.sleep(0.001)
        
        # Simulate data serialization
        data_size = len(str(data))
        serialization_time = data_size * 0.000001  # 1ms per MB
        await asyncio.sleep(serialization_time)
        
        # Simulate data validation
        await asyncio.sleep(0.002)
        
        # Simulate data write to target
        await asyncio.sleep(0.001)
        
        # Simulate metadata update
        await asyncio.sleep(0.001)
    
    async def benchmark_workspace_isolation_performance(
        self,
        multi_workspaces_setup,
        multi_workspace_storage
    ):
        """Benchmark performance with workspace isolation."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        workspaces = multi_workspaces_setup.get(10, [])
        storage_managers = multi_workspace_storage.get(10, [])
        
        if not workspaces:
            raise ValueError("No workspaces available for isolation testing")
        
        isolation_tests = []
        
        # Test concurrent isolated operations
        async def isolated_operation(workspace_idx: int, op_id: int):
            """Operation that should be isolated to specific workspace."""
            workspace = workspaces[workspace_idx]
            storage = storage_managers[workspace_idx]
            
            async with measure_performance(f"isolated_op_{workspace_idx}_{op_id}", monitor) as metrics:
                await self._simulate_isolated_operation(
                    workspace,
                    storage,
                    f"isolated_{workspace_idx}_{op_id}"
                )
            
            return metrics
        
        # Run isolated operations in parallel
        tasks = []
        for workspace_idx in range(len(workspaces)):
            for op_id in range(10):  # 10 operations per workspace
                tasks.append(isolated_operation(workspace_idx, op_id))
        
        isolation_tests = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to PerformanceMetrics
        metrics_list = []
        for result in isolation_tests:
            if isinstance(result, PerformanceMetrics):
                metrics_list.append(result)
            elif isinstance(result, Exception):
                metrics_list.append(PerformanceMetrics(
                    operation="isolated_operation_error",
                    duration_seconds=0,
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(result)
                ))
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "workspace_isolation_performance",
            metrics_list,
            monitor_results
        )
        
        return report
    
    async def _simulate_isolated_operation(
        self,
        workspace,
        storage,
        operation_id: str
    ):
        """Simulate isolated operation within a workspace."""
        
        # Simulate workspace-specific data access
        await asyncio.sleep(0.01)
        
        # Simulate isolated processing
        await asyncio.sleep(0.02)
        
        # Simulate workspace-specific storage
        await asyncio.sleep(0.005)


class TestMultiWorkspacePerformance:
    """Test class for multi-workspace performance."""
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.workspace
    async def test_workspace_creation_scalability(
        self,
        benchmark_output_dir
    ):
        """Test workspace creation performance at different scales."""
        
        test_instance = MultiWorkspacePerformanceTest()
        
        report = await test_instance.benchmark_workspace_creation_performance()
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "workspace_creation_scalability.json"
        )
        
        # Assertions
        additional_metrics = report.additional_metrics or {}
        creation_stats = additional_metrics.get("creation_times_by_count", {})
        
        # Check scalability
        for count, stats in creation_stats.items():
            mean_time = stats["mean_creation_time"]
            assert mean_time < 1.0, f"Slow workspace creation for {count} workspaces: {mean_time:.2f}s"
            
            throughput = stats["throughput_workspaces_per_sec"]
            assert throughput > 1.0, f"Low workspace creation throughput for {count} workspaces: {throughput:.2f} ws/sec"
        
        # Check that larger workspace counts don't have disproportionately bad performance
        if len(creation_stats) >= 2:
            counts = sorted(creation_stats.keys())
            small_count = counts[0]
            large_count = counts[-1]
            
            small_mean = creation_stats[small_count]["mean_creation_time"]
            large_mean = creation_stats[large_count]["mean_creation_time"]
            
            # Large workspace creation shouldn't be more than 3x slower per workspace
            per_workspace_ratio = (large_mean / large_count) / (small_mean / small_count)
            assert per_workspace_ratio < 3.0, f"Poor workspace creation scalability: {per_workspace_ratio:.2f}x slower per workspace"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.workspace
    @pytest.mark.parametrize("workspace_count", [5, 10, 25])
    async def test_concurrent_workspace_operations(
        self,
        workspace_count,
        multi_workspaces_setup,
        multi_workspace_storage,
        benchmark_output_dir
    ):
        """Test concurrent operations across multiple workspaces."""
        
        test_instance = MultiWorkspacePerformanceTest()
        
        report = await test_instance.benchmark_concurrent_workspace_operations(
            multi_workspaces_setup,
            multi_workspace_storage,
            workspace_count=workspace_count,
            operations_per_workspace=10
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"concurrent_workspace_operations_{workspace_count}.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        
        # Throughput should scale with workspace count (with diminishing returns)
        expected_min_throughput = workspace_count * 2  # Conservative estimate
        assert report.throughput_ops_per_sec > expected_min_throughput, f"Low throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.workspace
    async def test_workspace_switching_performance(
        self,
        multi_workspaces_setup,
        multi_workspace_storage,
        benchmark_output_dir
    ):
        """Test workspace switching overhead."""
        
        test_instance = MultiWorkspacePerformanceTest()
        
        report = await test_instance.benchmark_workspace_switching_performance(
            multi_workspaces_setup,
            multi_workspace_storage
        )
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "workspace_switching_performance.json"
        )
        
        # Assertions
        # Workspace switching should be fast
        assert report.latency_stats["mean"] < 0.1, f"Slow workspace switching: {report.latency_stats['mean']:.3f}s"
        assert report.latency_stats["p99"] < 0.2, f"High P99 switching latency: {report.latency_stats['p99']:.3f}s"
        
        # Should have high success rate
        success_rate = report.successful_operations / report.total_operations
        assert success_rate > 0.95, f"Low workspace switching success rate: {success_rate:.2%}"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.workspace
    async def test_cross_workspace_data_transfer(
        self,
        multi_workspaces_setup,
        multi_workspace_storage,
        benchmark_output_dir
    ):
        """Test data transfer performance between workspaces."""
        
        test_instance = MultiWorkspacePerformanceTest()
        
        report = await test_instance.benchmark_cross_workspace_data_transfer(
            multi_workspaces_setup,
            multi_workspace_storage
        )
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "cross_workspace_data_transfer.json"
        )
        
        # Assertions
        # Data transfer should be reasonably fast
        assert report.latency_stats["mean"] < 0.05, f"Slow data transfer: {report.latency_stats['mean']:.3f}s"
        assert report.latency_stats["p99"] < 0.1, f"High P99 transfer latency: {report.latency_stats['p99']:.3f}s"
        
        # Should have high success rate
        success_rate = report.successful_operations / report.total_operations
        assert success_rate > 0.95, f"Low data transfer success rate: {success_rate:.2%}"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.workspace
    async def test_workspace_isolation_performance(
        self,
        multi_workspaces_setup,
        multi_workspace_storage,
        benchmark_output_dir
    ):
        """Test workspace isolation performance."""
        
        test_instance = MultiWorkspacePerformanceTest()
        
        report = await test_instance.benchmark_workspace_isolation_performance(
            multi_workspaces_setup,
            multi_workspace_storage
        )
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "workspace_isolation_performance.json"
        )
        
        # Assertions
        # Isolated operations should be performant
        assert report.latency_stats["mean"] < 0.1, f"Slow isolated operations: {report.latency_stats['mean']:.3f}s"
        
        # Should have high success rate
        success_rate = report.successful_operations / report.total_operations
        assert success_rate > 0.95, f"Low isolated operation success rate: {success_rate:.2%}"
        
        # Throughput should be good for concurrent isolated operations
        expected_min_throughput = 50  # 50 ops/sec minimum
        assert report.throughput_ops_per_sec > expected_min_throughput, f"Low isolation throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report


@pytest.fixture
def benchmark_output_dir(tmp_path):
    """Create directory for benchmark outputs."""
    output_dir = tmp_path / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir