"""Memory usage profiling for long-running operations.

This module provides comprehensive memory testing for:
- Long-running pipeline execution
- Memory leak detection
- Memory usage patterns over time
- Garbage collection efficiency
- Memory pressure simulation
"""

import asyncio
import pytest
import gc
import tracemalloc
import psutil
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
import tempfile
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from tests.performance.test_performance_framework import (
    measure_performance,
    generate_performance_report,
    save_benchmark_results,
    PerformanceMonitor,
    TestConfiguration,
    validate_performance_thresholds,
    PerformanceMetrics
)

from tests.utils.workspace_helpers import create_test_workspace
from tests.utils.storage_helpers import setup_test_storage


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a specific time."""
    
    timestamp: datetime
    rss_memory_mb: float
    vms_memory_mb: float
    heap_memory_mb: float
    python_objects_count: int
    gc_objects_count: int
    tracemalloc_snapshot: Optional[Any] = None


@dataclass
class MemoryProfile:
    """Complete memory usage profile over time."""
    
    test_name: str
    duration_seconds: float
    snapshots: List[MemorySnapshot]
    memory_growth_rate_mb_per_hour: float
    peak_memory_mb: float
    average_memory_mb: float
    memory_leak_detected: bool
    leak_rate_mb_per_hour: float
    gc_efficiency_stats: Dict[str, float]
    memory_pressure_stats: Dict[str, Any]


class MemoryProfiler:
    """Advanced memory profiling for long-running operations."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.snapshots = []
        self.start_time = None
        self.initial_memory = None
        
    def start_profiling(self):
        """Start memory profiling."""
        tracemalloc.start()
        self.start_time = datetime.now()
        self.initial_memory = self._take_memory_snapshot()
        
    def stop_profiling(self) -> MemoryProfile:
        """Stop profiling and return memory profile."""
        final_snapshot = self._take_memory_snapshot()
        tracemalloc.stop()
        
        # Calculate growth rate
        duration_hours = (final_snapshot.timestamp - self.start_time).total_seconds() / 3600
        memory_growth = final_snapshot.rss_memory_mb - self.initial_memory.rss_memory_mb
        growth_rate = memory_growth / duration_hours if duration_hours > 0 else 0
        
        # Detect memory leaks
        leak_detected, leak_rate = self._detect_memory_leak()
        
        # Calculate statistics
        memory_values = [s.rss_memory_mb for s in self.snapshots]
        peak_memory = max(memory_values) if memory_values else 0
        average_memory = sum(memory_values) / len(memory_values) if memory_values else 0
        
        return MemoryProfile(
            test_name=f"memory_profile_{uuid.uuid4().hex[:8]}",
            duration_seconds=(final_snapshot.timestamp - self.start_time).total_seconds(),
            snapshots=self.snapshots,
            memory_growth_rate_mb_per_hour=growth_rate,
            peak_memory_mb=peak_memory,
            average_memory_mb=average_memory,
            memory_leak_detected=leak_detected,
            leak_rate_mb_per_hour=leak_rate,
            gc_efficiency_stats=self._calculate_gc_efficiency(),
            memory_pressure_stats=self._analyze_memory_pressure()
        )
    
    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory snapshot."""
        snapshot = self._take_memory_snapshot()
        self.snapshots.append(snapshot)
        return snapshot
    
    def _take_memory_snapshot(self) -> MemorySnapshot:
        """Take detailed memory snapshot."""
        memory_info = self.process.memory_info()
        
        # Count Python objects
        python_objects = len(gc.get_objects())
        
        # Count GC objects
        gc.collect()  # Force collection before counting
        gc_objects = len(gc.garbage)
        
        # Get tracemalloc snapshot if active
        tracemalloc_snapshot = None
        if tracemalloc.is_tracing():
            tracemalloc_snapshot = tracemalloc.take_snapshot()
        
        return MemorySnapshot(
            timestamp=datetime.now(),
            rss_memory_mb=memory_info.rss / 1024 / 1024,  # Convert to MB
            vms_memory_mb=memory_info.vms / 1024 / 1024,
            heap_memory_mb=tracemalloc.get_traced_memory()[0] / 1024 / 1024 if tracemalloc.is_tracing() else 0,
            python_objects_count=python_objects,
            gc_objects_count=gc_objects,
            tracemalloc_snapshot=tracemalloc_snapshot
        )
    
    def _detect_memory_leak(self) -> tuple[bool, float]:
        """Detect memory leaks from snapshot history."""
        if len(self.snapshots) < 3:
            return False, 0.0
        
        # Use linear regression to detect growth trend
        times = [(s.timestamp - self.snapshots[0].timestamp).total_seconds() / 3600 for s in self.snapshots]
        memories = [s.rss_memory_mb for s in self.snapshots]
        
        # Simple linear regression
        n = len(times)
        if n == 0:
            return False, 0.0
        
        sum_x = sum(times)
        sum_y = sum(memories)
        sum_xy = sum(t * m for t, m in zip(times, memories))
        sum_x2 = sum(t * t for t in times)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        
        # Consider it a leak if growth rate > 1MB/hour
        leak_detected = slope > 1.0
        
        return leak_detected, slope
    
    def _calculate_gc_efficiency(self) -> Dict[str, float]:
        """Calculate garbage collection efficiency."""
        if len(self.snapshots) < 2:
            return {"collection_rate": 0.0, "efficiency": 0.0}
        
        # Calculate object growth vs. GC collection
        object_counts = [s.python_objects_count for s in self.snapshots]
        growth_rate = (object_counts[-1] - object_counts[0]) / len(object_counts) if len(object_counts) > 1 else 0
        
        # Simulate GC efficiency
        gc_objects = [s.gc_objects_count for s in self.snapshots]
        avg_gc_objects = sum(gc_objects) / len(gc_objects)
        
        efficiency = max(0.0, 1.0 - (avg_gc_objects / (object_counts[-1] + 1)))
        
        return {
            "collection_rate": growth_rate,
            "efficiency": efficiency,
            "avg_gc_objects": avg_gc_objects
        }
    
    def _analyze_memory_pressure(self) -> Dict[str, Any]:
        """Analyze memory pressure patterns."""
        if not self.snapshots:
            return {"pressure_level": "low", "spikes_detected": 0}
        
        memory_values = [s.rss_memory_mb for s in self.snapshots]
        
        # Detect memory spikes
        avg_memory = sum(memory_values) / len(memory_values)
        spike_threshold = avg_memory * 1.2  # 20% above average
        spikes = [m for m in memory_values if m > spike_threshold]
        
        # Calculate pressure level
        peak_memory = max(memory_values)
        available_memory = psutil.virtual_memory().available / 1024 / 1024  # MB
        memory_usage_percent = (peak_memory / (peak_memory + available_memory)) * 100
        
        if memory_usage_percent > 80:
            pressure_level = "critical"
        elif memory_usage_percent > 60:
            pressure_level = "high"
        elif memory_usage_percent > 40:
            pressure_level = "medium"
        else:
            pressure_level = "low"
        
        return {
            "pressure_level": pressure_level,
            "spikes_detected": len(spikes),
            "memory_usage_percent": memory_usage_percent,
            "average_memory_mb": avg_memory,
            "peak_memory_mb": peak_memory
        }


class MemoryUsageTest:
    """Memory usage profiling for long-running operations."""
    
    @pytest.fixture
    async def memory_test_workspace(self):
        """Create isolated workspace for memory testing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="mem_test_"))
        workspace_name = f"mem_test_{uuid.uuid4().hex[:8]}"
        
        try:
            workspace = await create_test_workspace(workspace_name, temp_dir)
            yield workspace
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def simulate_long_running_operation(
        self,
        duration_minutes: int,
        operation_type: str = "pipeline_execution"
    ):
        """Simulate a long-running operation for memory testing."""
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        operation_count = 0
        memory_samples = []
        
        while time.time() < end_time:
            # Simulate operation
            if operation_type == "pipeline_execution":
                await self._simulate_pipeline_step()
            elif operation_type == "data_processing":
                await self._simulate_data_processing()
            elif operation_type == "cache_operations":
                await self._simulate_cache_operations()
            
            operation_count += 1
            
            # Sample memory every 10 seconds
            if operation_count % 10 == 0:
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_samples.append({
                    "timestamp": time.time(),
                    "rss_mb": memory_info.rss / 1024 / 1024,
                    "operation_count": operation_count
                })
            
            # Small delay to prevent 100% CPU usage
            await asyncio.sleep(0.1)
        
        return {
            "duration_seconds": time.time() - start_time,
            "operations_completed": operation_count,
            "memory_samples": memory_samples
        }
    
    async def _simulate_pipeline_step(self):
        """Simulate a pipeline step with memory allocation."""
        # Create temporary objects
        temp_data = {
            "step_id": str(uuid.uuid4()),
            "content": "x" * 1000,  # 1KB of data
            "metadata": {f"key_{i}": f"value_{i}" for i in range(20)},
            "results": list(range(100))
        }
        
        # Simulate processing
        await asyncio.sleep(0.01)
        
        # Clean up
        del temp_data
    
    async def _simulate_data_processing(self):
        """Simulate data processing operations."""
        # Create larger data structures
        data_list = [str(uuid.uuid4()) for _ in range(1000)]
        data_dict = {str(i): f"data_{i}" for i in range(500)}
        
        # Simulate processing
        processed_data = [item.upper() for item in data_list[:100]]
        
        # Clean up
        del data_list, data_dict, processed_data
    
    async def _simulate_cache_operations(self):
        """Simulate cache operations."""
        # Simulate cache with growing data
        cache_data = {}
        
        for i in range(50):
            key = f"cache_key_{i}"
            value = {"data": f"value_{i}", "timestamp": time.time()}
            cache_data[key] = value
            
            # Simulate cache eviction
            if len(cache_data) > 20:
                oldest_key = min(cache_data.keys())
                del cache_data[oldest_key]
            
            await asyncio.sleep(0.001)
    
    async def benchmark_memory_usage_patterns(
        self,
        memory_test_workspace,
        duration_minutes: int = 5,
        operation_type: str = "pipeline_execution"
    ):
        """Benchmark memory usage patterns during long-running operations."""
        
        profiler = MemoryProfiler()
        profiler.start_profiling()
        
        # Take initial snapshot
        profiler.take_snapshot()
        
        # Run long-running operation
        operation_results = await self.simulate_long_running_operation(
            duration_minutes,
            operation_type
        )
        
        # Take final snapshot
        profiler.take_snapshot()
        
        # Get memory profile
        memory_profile = profiler.stop_profiling()
        
        # Add operation results to profile
        memory_profile.test_name = f"{operation_type}_{duration_minutes}min"
        memory_profile.additional_metrics = {
            "operations_completed": operation_results["operations_completed"],
            "operations_per_second": operation_results["operations_completed"] / operation_results["duration_seconds"],
            "operation_memory_samples": operation_results["memory_samples"]
        }
        
        return memory_profile
    
    async def benchmark_memory_leak_detection(
        self,
        memory_test_workspace,
        iterations: int = 1000
    ):
        """Benchmark memory leak detection with repeated operations."""
        
        profiler = MemoryProfiler()
        profiler.start_profiling()
        
        # Take initial snapshot
        profiler.take_snapshot()
        
        # Create growing data structure that should be cleaned up
        leak_test_data = []
        
        for i in range(iterations):
            # Simulate operation with potential memory leak
            temp_data = {
                "iteration": i,
                "large_content": "x" * 5000,  # 5KB
                "complex_structure": {
                    "nested": [f"item_{j}" for j in range(100)]
                }
            }
            
            # Some operations that might leak
            if i % 10 == 0:
                # This could accumulate if not cleaned up properly
                leak_test_data.append(temp_data.copy())
            
            # Simulate processing
            await asyncio.sleep(0.001)
            
            # Take periodic snapshots
            if i % 100 == 0:
                profiler.take_snapshot()
                
                # Force garbage collection periodically
                gc.collect()
        
        # Take final snapshot
        profiler.take_snapshot()
        
        # Get memory profile
        memory_profile = profiler.stop_profiling()
        memory_profile.test_name = f"memory_leak_test_{iterations}_iterations"
        
        # Add leak-specific analysis
        memory_profile.additional_metrics = {
            "test_iterations": iterations,
            "accumulated_objects": len(leak_test_data),
            "leak_test_data_size": sum(len(str(d)) for d in leak_test_data) / 1024  # KB
        }
        
        return memory_profile
    
    async def benchmark_memory_pressure_simulation(
        self,
        memory_test_workspace,
        memory_pressure_mb: int = 100
    ):
        """Benchmark performance under memory pressure."""
        
        profiler = MemoryProfiler()
        profiler.start_profiling()
        
        # Take initial snapshot
        profiler.take_snapshot()
        
        # Create memory pressure
        pressure_data = []
        chunk_size = 10 * 1024 * 1024  # 10MB chunks
        
        try:
            # Allocate memory gradually
            allocated_mb = 0
            while allocated_mb < memory_pressure_mb:
                chunk = ["x" * 1000] * (chunk_size // 1000)  # 10MB chunk
                pressure_data.append(chunk)
                allocated_mb += 10
                
                # Take snapshot after each chunk
                profiler.take_snapshot()
                
                # Simulate some work
                await self._simulate_pipeline_step()
                
                # Small delay
                await asyncio.sleep(0.1)
        
        except MemoryError:
            # Handle memory allocation failure
            pass
        
        # Take final snapshot
        profiler.take_snapshot()
        
        # Get memory profile
        memory_profile = profiler.stop_profiling()
        memory_profile.test_name = f"memory_pressure_{memory_pressure_mb}MB"
        
        # Add pressure-specific analysis
        memory_profile.additional_metrics = {
            "target_pressure_mb": memory_pressure_mb,
            "actual_allocated_mb": len(pressure_data) * 10,
            "chunks_allocated": len(pressure_data),
            "memory_error_occurred": allocated_mb < memory_pressure_mb
        }
        
        # Clean up
        del pressure_data
        gc.collect()
        
        return memory_profile


class TestMemoryProfiling:
    """Test class for memory profiling."""
    
    @pytest.mark.slow
    @pytest.mark.memory
    @pytest.mark.parametrize("operation_type", ["pipeline_execution", "data_processing", "cache_operations"])
    async def test_memory_usage_patterns(
        self,
        operation_type,
        memory_test_workspace,
        benchmark_output_dir
    ):
        """Test memory usage patterns for different operation types."""
        
        test_instance = MemoryUsageTest()
        
        memory_profile = await test_instance.benchmark_memory_usage_patterns(
            memory_test_workspace,
            duration_minutes=2,  # Shorter for CI
            operation_type=operation_type
        )
        
        # Save results
        profile_data = {
            "test_name": memory_profile.test_name,
            "duration_seconds": memory_profile.duration_seconds,
            "peak_memory_mb": memory_profile.peak_memory_mb,
            "average_memory_mb": memory_profile.average_memory_mb,
            "memory_growth_rate_mb_per_hour": memory_profile.memory_growth_rate_mb_per_hour,
            "memory_leak_detected": memory_profile.memory_leak_detected,
            "leak_rate_mb_per_hour": memory_profile.leak_rate_mb_per_hour,
            "gc_efficiency": memory_profile.gc_efficiency_stats,
            "memory_pressure": memory_profile.memory_pressure_stats,
            "additional_metrics": memory_profile.additional_metrics,
            "snapshots": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "rss_memory_mb": s.rss_memory_mb,
                    "vms_memory_mb": s.vms_memory_mb,
                    "heap_memory_mb": s.heap_memory_mb,
                    "python_objects_count": s.python_objects_count,
                    "gc_objects_count": s.gc_objects_count
                }
                for s in memory_profile.snapshots
            ]
        }
        
        import json
        output_path = benchmark_output_dir / f"memory_usage_patterns_{operation_type}.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Assertions
        assert not memory_profile.memory_leak_detected, f"Memory leak detected: {memory_profile.leak_rate_mb_per_hour:.2f} MB/hour"
        assert memory_profile.peak_memory_mb < 512, f"Peak memory too high: {memory_profile.peak_memory_mb:.2f} MB"
        assert memory_profile.memory_growth_rate_mb_per_hour < 10, f"Memory growth rate too high: {memory_profile.memory_growth_rate_mb_per_hour:.2f} MB/hour"
        
        # GC efficiency
        gc_efficiency = memory_profile.gc_efficiency_stats.get("efficiency", 0)
        assert gc_efficiency > 0.5, f"Low GC efficiency: {gc_efficiency:.2f}"
        
        return memory_profile
    
    @pytest.mark.slow
    @pytest.mark.memory
    async def test_memory_leak_detection(
        self,
        memory_test_workspace,
        benchmark_output_dir
    ):
        """Test memory leak detection capabilities."""
        
        test_instance = MemoryUsageTest()
        
        memory_profile = await test_instance.benchmark_memory_leak_detection(
            memory_test_workspace,
            iterations=500
        )
        
        # Save results
        profile_data = {
            "test_name": memory_profile.test_name,
            "memory_leak_detected": memory_profile.memory_leak_detected,
            "leak_rate_mb_per_hour": memory_profile.leak_rate_mb_per_hour,
            "peak_memory_mb": memory_profile.peak_memory_mb,
            "additional_metrics": memory_profile.additional_metrics,
            "gc_efficiency": memory_profile.gc_efficiency_stats,
            "memory_pressure": memory_profile.memory_pressure_stats
        }
        
        import json
        output_path = benchmark_output_dir / "memory_leak_detection.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Assertions
        # Allow some memory growth but it should be reasonable
        assert memory_profile.leak_rate_mb_per_hour < 50, f"High leak rate: {memory_profile.leak_rate_mb_per_hour:.2f} MB/hour"
        assert memory_profile.peak_memory_mb < 256, f"Peak memory too high: {memory_profile.peak_memory_mb:.2f} MB"
        
        return memory_profile
    
    @pytest.mark.slow
    @pytest.mark.memory
    async def test_memory_pressure_simulation(
        self,
        memory_test_workspace,
        benchmark_output_dir
    ):
        """Test performance under memory pressure."""
        
        test_instance = MemoryUsageTest()
        
        memory_profile = await test_instance.benchmark_memory_pressure_simulation(
            memory_test_workspace,
            memory_pressure_mb=50  # Conservative for CI
        )
        
        # Save results
        profile_data = {
            "test_name": memory_profile.test_name,
            "peak_memory_mb": memory_profile.peak_memory_mb,
            "memory_pressure_level": memory_profile.memory_pressure_stats.get("pressure_level"),
            "spikes_detected": memory_profile.memory_pressure_stats.get("spikes_detected"),
            "additional_metrics": memory_profile.additional_metrics,
            "gc_efficiency": memory_profile.gc_efficiency_stats
        }
        
        import json
        output_path = benchmark_output_dir / "memory_pressure_simulation.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Assertions
        # System should handle memory pressure gracefully
        pressure_level = memory_profile.memory_pressure_stats.get("pressure_level", "low")
        assert pressure_level in ["low", "medium"], f"High memory pressure: {pressure_level}"
        
        # Should not crash under memory pressure
        additional_metrics = memory_profile.additional_metrics or {}
        assert not additional_metrics.get("memory_error_occurred", True), "Memory error occurred during pressure test"
        
        return memory_profile


@pytest.fixture
def benchmark_output_dir(tmp_path):
    """Create directory for benchmark outputs."""
    output_dir = tmp_path / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir