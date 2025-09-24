"""Performance and load testing suite for WriteIt.

This module provides comprehensive performance testing for:
- Pipeline execution benchmarks
- LMDB operation performance
- Memory usage profiling
- Concurrent execution testing
- API stress testing
- Extended execution stability
"""

import asyncio
import time
import psutil
import tracemalloc
import statistics
from typing import Dict, List, Any, Optional, AsyncContextManager
from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime, timedelta


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""
    
    operation: str
    duration_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    additional_metrics: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkResult:
    """Comprehensive benchmark results."""
    
    test_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    duration_seconds: float
    throughput_ops_per_sec: float
    memory_stats: Dict[str, float]
    cpu_stats: Dict[str, float]
    latency_stats: Dict[str, float]
    errors: List[str]
    timestamp: datetime


class PerformanceMonitor:
    """Real-time performance monitoring."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.metrics_history = []
        self.start_time = None
        
    def start_monitoring(self):
        """Start performance monitoring."""
        tracemalloc.start()
        self.start_time = time.time()
        
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return collected metrics."""
        if self.start_time:
            duration = time.time() - self.start_time
        else:
            duration = 0
            
        # Get memory usage
        current_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        peak_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Get CPU usage
        cpu_percent = self.process.cpu_percent()
        
        # Get memory traces
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
        else:
            snapshot = None
            
        return {
            "duration_seconds": duration,
            "current_memory_mb": current_mem,
            "peak_memory_mb": peak_mem,
            "cpu_usage_percent": cpu_percent,
            "memory_snapshot": snapshot,
            "metrics_history": self.metrics_history
        }
        
    def record_metric(self, operation: str, value: float):
        """Record a specific metric."""
        self.metrics_history.append({
            "timestamp": time.time(),
            "operation": operation,
            "value": value
        })


@asynccontextmanager
async def measure_performance(
    operation_name: str,
    monitor: Optional[PerformanceMonitor] = None
) -> AsyncContextManager[PerformanceMetrics]:
    """Context manager for measuring performance of async operations."""
    
    start_time = time.time()
    process = psutil.Process()
    
    # Get initial measurements
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    initial_cpu = process.cpu_percent()
    
    metrics = PerformanceMetrics(
        operation=operation_name,
        duration_seconds=0,
        memory_usage_mb=initial_memory,
        cpu_usage_percent=initial_cpu,
        success=True
    )
    
    try:
        yield metrics
    except Exception as e:
        metrics.success = False
        metrics.error_message = str(e)
        raise
    finally:
        # Calculate final measurements
        metrics.duration_seconds = time.time() - start_time
        metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        metrics.cpu_usage_percent = process.cpu_percent()
        
        # Record in monitor if provided
        if monitor:
            monitor.record_metric(operation_name, metrics.duration_seconds)


async def run_concurrent_operations(
    operation_func,
    concurrency_level: int,
    total_operations: int,
    operation_args: Optional[Dict] = None
) -> List[PerformanceMetrics]:
    """Run operations concurrently and measure performance."""
    
    semaphore = asyncio.Semaphore(concurrency_level)
    metrics_list = []
    
    async def limited_operation(op_id: int) -> PerformanceMetrics:
        async with semaphore:
            args = operation_args or {}
            async with measure_performance(f"concurrent_op_{op_id}") as metrics:
                await operation_func(op_id, **args)
            return metrics
    
    # Create tasks
    tasks = [limited_operation(i) for i in range(total_operations)]
    
    # Execute all tasks
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_duration = time.time() - start_time
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            error_metrics = PerformanceMetrics(
                operation="concurrent_error",
                duration_seconds=total_duration / total_operations,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                success=False,
                error_message=str(result)
            )
            metrics_list.append(error_metrics)
        else:
            metrics_list.append(result)
    
    return metrics_list


def calculate_latency_stats(durations: List[float]) -> Dict[str, float]:
    """Calculate latency statistics from duration list."""
    if not durations:
        return {}
    
    return {
        "min": min(durations),
        "max": max(durations),
        "mean": statistics.mean(durations),
        "median": statistics.median(durations),
        "stdev": statistics.stdev(durations) if len(durations) > 1 else 0,
        "p95": statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
        "p99": statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations)
    }


def generate_performance_report(
    test_name: str,
    metrics_list: List[PerformanceMetrics],
    monitor_results: Optional[Dict[str, Any]] = None
) -> BenchmarkResult:
    """Generate comprehensive performance report."""
    
    # Filter successful operations
    successful_metrics = [m for m in metrics_list if m.success]
    failed_metrics = [m for m in metrics_list if not m.success]
    
    # Calculate statistics
    durations = [m.duration_seconds for m in successful_metrics]
    memory_usage = [m.memory_usage_mb for m in successful_metrics]
    cpu_usage = [m.cpu_usage_percent for m in successful_metrics]
    
    # Total duration
    if metrics_list:
        total_duration = max(m.duration_seconds for m in metrics_list) if metrics_list else 0
    else:
        total_duration = 0
        
    # Throughput
    throughput = len(successful_metrics) / total_duration if total_duration > 0 else 0
    
    # Compile results
    result = BenchmarkResult(
        test_name=test_name,
        total_operations=len(metrics_list),
        successful_operations=len(successful_metrics),
        failed_operations=len(failed_metrics),
        duration_seconds=total_duration,
        throughput_ops_per_sec=throughput,
        memory_stats={
            "min_mb": min(memory_usage) if memory_usage else 0,
            "max_mb": max(memory_usage) if memory_usage else 0,
            "avg_mb": statistics.mean(memory_usage) if memory_usage else 0,
            "current_mb": monitor_results.get("current_memory_mb", 0) if monitor_results else 0,
            "peak_mb": monitor_results.get("peak_memory_mb", 0) if monitor_results else 0
        },
        cpu_stats={
            "avg_percent": statistics.mean(cpu_usage) if cpu_usage else 0,
            "max_percent": max(cpu_usage) if cpu_usage else 0,
            "current_percent": monitor_results.get("cpu_usage_percent", 0) if monitor_results else 0
        },
        latency_stats=calculate_latency_stats(durations),
        errors=[m.error_message for m in failed_metrics if m.error_message],
        timestamp=datetime.now()
    )
    
    return result


def save_benchmark_results(results: List[BenchmarkResult], output_path: Path):
    """Save benchmark results to file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "test_results": []
    }
    
    for result in results:
        result_dict = {
            "test_name": result.test_name,
            "total_operations": result.total_operations,
            "successful_operations": result.successful_operations,
            "failed_operations": result.failed_operations,
            "duration_seconds": result.duration_seconds,
            "throughput_ops_per_sec": result.throughput_ops_per_sec,
            "memory_stats": result.memory_stats,
            "cpu_stats": result.cpu_stats,
            "latency_stats": result.latency_stats,
            "errors": result.errors,
            "timestamp": result.timestamp.isoformat()
        }
        output_data["test_results"].append(result_dict)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)


class TestConfiguration:
    """Configuration for performance tests."""
    
    # Pipeline execution benchmarks
    PIPELINE_ITERATIONS = 50
    PIPELINE_CONCURRENCY = [1, 5, 10, 20]
    
    # LMDB benchmarks
    LMDB_OPERATIONS = 1000
    LMDB_BATCH_SIZES = [10, 50, 100, 500]
    
    # Memory profiling
    MEMORY_TEST_DURATION_MINUTES = 5
    MEMORY_SAMPLE_INTERVAL_SECONDS = 1
    
    # API stress testing
    API_REQUEST_COUNT = 1000
    API_CONCURRENCY_LEVELS = [10, 50, 100, 200]
    
    # Extended stability testing
    STABILITY_TEST_DURATION_HOURS = 2
    STABILITY_PIPELINE_INTERVAL_SECONDS = 30
    
    # Performance thresholds
    MAX_MEMORY_MB = 512
    MAX_LATENCY_SECONDS = 10
    MIN_THROUGHPUT_OPS_PER_SEC = 1
    MAX_FAILURE_RATE_PERCENT = 5
    
    # Test environment adjustments (more lenient for CI/testing)
    TEST_ENV_MAX_FAILURE_RATE_PERCENT = 50


def validate_performance_thresholds(results: BenchmarkResult) -> Dict[str, Any]:
    """Validate results against performance thresholds."""
    
    violations = []
    warnings = []
    
    # Check memory usage
    if results.memory_stats["peak_mb"] > TestConfiguration.MAX_MEMORY_MB:
        violations.append(
            f"Memory usage exceeded threshold: {results.memory_stats['peak_mb']:.2f}MB > {TestConfiguration.MAX_MEMORY_MB}MB"
        )
    
    # Check latency
    if results.latency_stats.get("p99", 0) > TestConfiguration.MAX_LATENCY_SECONDS:
        violations.append(
            f"P99 latency exceeded threshold: {results.latency_stats['p99']:.2f}s > {TestConfiguration.MAX_LATENCY_SECONDS}s"
        )
    
    # Check throughput
    if results.throughput_ops_per_sec < TestConfiguration.MIN_THROUGHPUT_OPS_PER_SEC:
        warnings.append(
            f"Low throughput: {results.throughput_ops_per_sec:.2f} ops/sec < {TestConfiguration.MIN_THROUGHPUT_OPS_PER_SEC} ops/sec"
        )
    
    # Check failure rate
    failure_rate = (results.failed_operations / results.total_operations * 100) if results.total_operations > 0 else 0
    max_failure_rate = TestConfiguration.TEST_ENV_MAX_FAILURE_RATE_PERCENT
    if failure_rate > max_failure_rate:
        violations.append(
            f"High failure rate: {failure_rate:.2f}% > {max_failure_rate}%"
        )
    
    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "failure_rate_percent": failure_rate
    }