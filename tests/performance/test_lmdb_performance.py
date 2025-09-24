"""LMDB operation benchmarks and stress testing.

This module provides comprehensive performance testing for:
- Database read/write operations
- Concurrent database access
- Large dataset handling
- Memory usage during intensive operations
- Database performance under stress
"""

import asyncio
import pytest
import tempfile
import shutil
import lmdb
import json
from pathlib import Path
from typing import Dict, List, Any, AsyncGenerator, Optional
import uuid
import time

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


class LMDBPerformanceTest:
    """Performance testing for LMDB storage operations."""
    
    @pytest.fixture
    async def performance_lmdb_env(self):
        """Create isolated LMDB environment for performance testing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="lmdb_perf_test_"))
        
        try:
            env = lmdb.open(
                str(temp_dir / "test.lmdb"),
                map_size=1024 * 1024 * 1024,  # 1GB
                max_dbs=10,
                sync=False,
                lock=False
            )
            yield env
        finally:
            env.close()
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    async def test_data_generator(self):
        """Generate test data for LMDB operations."""
        
        def generate_test_data(size: str = "small") -> Dict[str, Any]:
            """Generate test data of different sizes."""
            
            if size == "small":
                data_size = 100  # 100 bytes
            elif size == "medium":
                data_size = 1000  # 1KB
            elif size == "large":
                data_size = 10000  # 10KB
            elif size == "xlarge":
                data_size = 100000  # 100KB
            else:
                data_size = 500
            
            # Create structured test data
            return {
                "id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "content": "x" * data_size,
                "metadata": {
                    "size": size,
                    "created_at": time.time(),
                    "tags": [f"tag_{i}" for i in range(5)],
                    "nested_data": {
                        "field1": "value1",
                        "field2": list(range(10)),
                        "field3": {"nested": "deeply nested data"}
                    }
                }
            }
        
        return generate_test_data
    
    async def benchmark_single_write_operations(
        self,
        performance_lmdb_env,
        test_data_generator
    ):
        """Benchmark single write operations performance."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        write_times = []
        
        with performance_lmdb_env.begin(write=True) as txn:
            db = txn.open_db(name="test_writes")
            
            for i in range(TestConfiguration.LMDB_OPERATIONS):
                data = test_data_generator("medium")
                key = f"key_{i}".encode()
                value = json.dumps(data).encode()
                
                async with measure_performance(f"single_write_{i}", monitor) as metrics:
                    txn.put(key, value, db=db)
                
                write_times.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "lmdb_single_write_benchmark",
            write_times,
            monitor_results
        )
        
        return report
    
    async def benchmark_batch_write_operations(
        self,
        performance_lmdb_env,
        test_data_generator,
        batch_size: int = 100
    ):
        """Benchmark batch write operations performance."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        batch_times = []
        operations_count = TestConfiguration.LMDB_OPERATIONS
        
        batches = operations_count // batch_size
        
        for batch_num in range(batches):
            batch_data = []
            
            # Prepare batch data
            for i in range(batch_size):
                data = test_data_generator("medium")
                key = f"batch_{batch_num}_key_{i}".encode()
                value = json.dumps(data).encode()
                batch_data.append((key, value))
            
            async with measure_performance(f"batch_write_{batch_num}", monitor) as metrics:
                with performance_lmdb_env.begin(write=True) as txn:
                    db = txn.open_db(name="batch_writes")
                    for key, value in batch_data:
                        txn.put(key, value, db=db)
            
            batch_times.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"lmdb_batch_write_benchmark_{batch_size}",
            batch_times,
            monitor_results
        )
        
        return report
    
    async def benchmark_read_operations(
        self,
        performance_lmdb_env,
        test_data_generator
    ):
        """Benchmark read operations performance."""
        
        # First, populate the database
        with performance_lmdb_env.begin(write=True) as txn:
            db = txn.open_db(name="read_test")
            
            for i in range(TestConfiguration.LMDB_OPERATIONS):
                data = test_data_generator("medium")
                key = f"read_key_{i}".encode()
                value = json.dumps(data).encode()
                txn.put(key, value, db=db)
        
        # Now benchmark reads
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        read_times = []
        
        with performance_lmdb_env.begin() as txn:
            db = txn.open_db(name="read_test")
            
            for i in range(TestConfiguration.LMDB_OPERATIONS):
                key = f"read_key_{i}".encode()
                
                async with measure_performance(f"read_operation_{i}", monitor) as metrics:
                    value = txn.get(key, db=db)
                    if value:
                        # Parse the JSON to simulate real usage
                        parsed_data = json.loads(value.decode())
                
                read_times.append(metrics)
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            "lmdb_read_operations_benchmark",
            read_times,
            monitor_results
        )
        
        return report
    
    async def benchmark_concurrent_operations(
        self,
        performance_lmdb_env,
        test_data_generator,
        concurrency_level: int = 10
    ):
        """Benchmark concurrent LMDB operations."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Prepare data for concurrent operations
        total_ops = TestConfiguration.LMDB_OPERATIONS
        
        async def concurrent_operation(op_id: int):
            """Single concurrent LMDB operation."""
            
            data = test_data_generator("small")
            key = f"concurrent_key_{op_id}".encode()
            value = json.dumps(data).encode()
            
            async with measure_performance(f"concurrent_op_{op_id}", monitor) as metrics:
                with performance_lmdb_env.begin(write=True) as txn:
                    db = txn.open_db(name="concurrent_test")
                    txn.put(key, value, db=db)
                    
                    # Read it back
                    read_value = txn.get(key, db=db)
                    if read_value:
                        json.loads(read_value.decode())
        
        # Run concurrent operations
        metrics_list = await run_concurrent_operations(
            concurrent_operation,
            concurrency_level,
            total_ops
        )
        
        monitor_results = monitor.stop_monitoring()
        report = generate_performance_report(
            f"lmdb_concurrent_operations_{concurrency_level}",
            metrics_list,
            monitor_results
        )
        
        return report
    
    async def benchmark_large_data_operations(
        self,
        performance_lmdb_env,
        test_data_generator
    ):
        """Benchmark operations with large data objects."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        sizes = ["small", "medium", "large", "xlarge"]
        size_results = {}
        
        for size in sizes:
            size_times = []
            
            for i in range(100):  # 100 operations per size
                data = test_data_generator(size)
                key = f"large_{size}_{i}".encode()
                value = json.dumps(data).encode()
                
                async with measure_performance(f"large_data_{size}_{i}", monitor) as metrics:
                    with performance_lmdb_env.begin(write=True) as txn:
                        db = txn.open_db(name=f"large_data_{size}")
                        txn.put(key, value, db=db)
                        
                        # Read it back
                        read_value = txn.get(key, db=db)
                        if read_value:
                            json.loads(read_value.decode())
                
                size_times.append(metrics)
            
            # Generate report for this size
            size_report = generate_performance_report(
                f"lmdb_large_data_{size}",
                size_times,
                None
            )
            size_results[size] = size_report
        
        monitor_results = monitor.stop_monitoring()
        
        # Create combined report
        all_metrics = []
        for size_report in size_results.values():
            all_metrics.extend(size_report.total_operations * [PerformanceMetrics(
                operation=size_report.test_name,
                duration_seconds=size_report.latency_stats["mean"],
                memory_usage_mb=size_report.memory_stats["avg_mb"],
                cpu_usage_percent=size_report.cpu_stats["avg_percent"],
                success=True
            )])
        
        combined_report = generate_performance_report(
            "lmdb_large_data_operations",
            all_metrics,
            monitor_results
        )
        
        # Store size-specific results
        combined_report.additional_metrics = {
            "size_breakdown": {
                size: {
                    "mean_latency": report.latency_stats["mean"],
                    "mean_memory": report.memory_stats["avg_mb"]
                }
                for size, report in size_results.items()
            }
        }
        
        return combined_report
    
    async def benchmark_database_growth(
        self,
        performance_lmdb_env,
        test_data_generator
    ):
        """Benchmark performance as database grows."""
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        growth_points = [100, 500, 1000, 5000, 10000]  # Number of records
        performance_samples = []
        
        current_records = 0
        
        for target_records in growth_points:
            # Grow database to target size
            records_to_add = target_records - current_records
            
            for i in range(records_to_add):
                data = test_data_generator("medium")
                key = f"growth_key_{current_records + i}".encode()
                value = json.dumps(data).encode()
                
                with performance_lmdb_env.begin(write=True) as txn:
                    db = txn.open_db(name="growth_test")
                    txn.put(key, value, db=db)
            
            current_records = target_records
            
            # Benchmark performance at this size
            sample_times = []
            
            for j in range(100):  # Sample 100 operations
                key = f"growth_key_{j % current_records}".encode()
                
                async with measure_performance(f"growth_test_{target_records}_{j}", monitor) as metrics:
                    with performance_lmdb_env.begin() as txn:
                        db = txn.open_db(name="growth_test")
                        value = txn.get(key, db=db)
                        if value:
                            json.loads(value.decode())
                
                sample_times.append(metrics)
            
            # Calculate performance at this size
            size_report = generate_performance_report(
                f"growth_benchmark_{target_records}",
                sample_times,
                None
            )
            
            performance_samples.append({
                "record_count": target_records,
                "mean_latency": size_report.latency_stats["mean"],
                "p99_latency": size_report.latency_stats["p99"],
                "throughput": size_report.throughput_ops_per_sec
            })
        
        monitor_results = monitor.stop_monitoring()
        
        # Create growth analysis report
        all_metrics = []
        for sample in performance_samples:
            for _ in range(100):  # 100 samples per growth point
                all_metrics.append(PerformanceMetrics(
                    operation=f"growth_analysis",
                    duration_seconds=sample["mean_latency"],
                    memory_usage_mb=monitor_results.get("current_memory_mb", 0),
                    cpu_usage_percent=monitor_results.get("cpu_usage_percent", 0),
                    success=True
                ))
        
        report = generate_performance_report(
            "lmdb_database_growth_analysis",
            all_metrics,
            monitor_results
        )
        
        # Add growth analysis
        report.additional_metrics = {
            "growth_analysis": performance_samples,
            "performance_degradation": self._calculate_performance_degradation(performance_samples)
        }
        
        return report
    
    def _calculate_performance_degradation(self, samples: List[Dict]) -> Dict[str, float]:
        """Calculate performance degradation as database grows."""
        
        if len(samples) < 2:
            return {"degradation_rate": 0.0}
        
        initial_performance = samples[0]["throughput"]
        final_performance = samples[-1]["throughput"]
        
        if initial_performance > 0:
            degradation_rate = (initial_performance - final_performance) / initial_performance
        else:
            degradation_rate = 0.0
        
        return {
            "initial_throughput": initial_performance,
            "final_throughput": final_performance,
            "degradation_rate": degradation_rate,
            "growth_factor": samples[-1]["record_count"] / samples[0]["record_count"]
        }


class TestLMDBPerformance:
    """Test class for LMDB performance benchmarks."""
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.storage
    async def test_single_write_performance(
        self,
        performance_lmdb_env,
        test_data_generator,
        benchmark_output_dir
    ):
        """Test single write operation performance."""
        
        test_instance = LMDBPerformanceTest()
        
        report = await test_instance.benchmark_single_write_operations(
            performance_lmdb_env,
            test_data_generator
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "lmdb_single_write_performance.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.throughput_ops_per_sec > 1000, f"Low write throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        assert report.latency_stats["p99"] < 0.01, f"High P99 latency: {report.latency_stats['p99']:.4f}s"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.storage
    @pytest.mark.parametrize("batch_size", [10, 50, 100, 500])
    async def test_batch_write_performance(
        self,
        batch_size,
        performance_lmdb_env,
        test_data_generator,
        benchmark_output_dir
    ):
        """Test batch write operation performance."""
        
        test_instance = LMDBPerformanceTest()
        
        report = await test_instance.benchmark_batch_write_operations(
            performance_lmdb_env,
            test_data_generator,
            batch_size=batch_size
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"lmdb_batch_write_{batch_size}.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        
        # Batch operations should be more efficient than single operations
        expected_throughput = batch_size * 500  # 500 ops/sec per batch member
        assert report.throughput_ops_per_sec > expected_throughput, f"Low batch throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.storage
    async def test_read_operations_performance(
        self,
        performance_lmdb_env,
        test_data_generator,
        benchmark_output_dir
    ):
        """Test read operation performance."""
        
        test_instance = LMDBPerformanceTest()
        
        report = await test_instance.benchmark_read_operations(
            performance_lmdb_env,
            test_data_generator
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "lmdb_read_operations_performance.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.throughput_ops_per_sec > 5000, f"Low read throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        assert report.latency_stats["p99"] < 0.002, f"High P99 read latency: {report.latency_stats['p99']:.4f}s"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.storage
    @pytest.mark.parametrize("concurrency", [5, 10, 20, 50])
    async def test_concurrent_operations_performance(
        self,
        concurrency,
        performance_lmdb_env,
        test_data_generator,
        benchmark_output_dir
    ):
        """Test concurrent operation performance."""
        
        test_instance = LMDBPerformanceTest()
        
        report = await test_instance.benchmark_concurrent_operations(
            performance_lmdb_env,
            test_data_generator,
            concurrency_level=concurrency
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / f"lmdb_concurrent_operations_{concurrency}.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        assert report.throughput_ops_per_sec > concurrency * 100, f"Low concurrent throughput: {report.throughput_ops_per_sec:.2f} ops/sec"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.storage
    @pytest.mark.memory
    async def test_large_data_operations_performance(
        self,
        performance_lmdb_env,
        test_data_generator,
        benchmark_output_dir
    ):
        """Test large data operation performance."""
        
        test_instance = LMDBPerformanceTest()
        
        report = await test_instance.benchmark_large_data_operations(
            performance_lmdb_env,
            test_data_generator
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "lmdb_large_data_operations.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        
        # Check size-specific performance
        size_breakdown = report.additional_metrics.get("size_breakdown", {})
        assert "xlarge" in size_breakdown, "XLarge data performance not measured"
        
        # Large data should not be more than 50x slower than small data
        small_latency = size_breakdown["small"]["mean_latency"]
        xlarge_latency = size_breakdown["xlarge"]["mean_latency"]
        latency_ratio = xlarge_latency / small_latency if small_latency > 0 else 0
        assert latency_ratio < 50, f"High large data penalty: {latency_ratio:.2f}x slower"
        
        return report
    
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.storage
    async def test_database_growth_performance(
        self,
        performance_lmdb_env,
        test_data_generator,
        benchmark_output_dir
    ):
        """Test performance as database grows."""
        
        test_instance = LMDBPerformanceTest()
        
        report = await test_instance.benchmark_database_growth(
            performance_lmdb_env,
            test_data_generator
        )
        
        # Validate performance
        validation = validate_performance_thresholds(report)
        
        # Save results
        save_benchmark_results(
            [report],
            benchmark_output_dir / "lmdb_database_growth_performance.json"
        )
        
        # Assertions
        assert validation["passed"], f"Performance violations: {validation['violations']}"
        
        # Check performance degradation
        degradation = report.additional_metrics.get("performance_degradation", {})
        degradation_rate = degradation.get("degradation_rate", 0)
        assert degradation_rate < 0.5, f"High performance degradation: {degradation_rate:.2%}"
        
        return report


@pytest.fixture
def benchmark_output_dir(tmp_path):
    """Create directory for benchmark outputs."""
    output_dir = tmp_path / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir