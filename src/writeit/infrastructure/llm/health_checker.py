"""LLM Provider Health Checker.

Monitors the health and availability of LLM providers.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum

from .base_provider import BaseLLMProvider, ProviderError, ProviderUnavailableError
from .provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    
    provider_name: str
    status: HealthStatus
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Additional metrics
    success_rate: Optional[float] = None
    avg_response_time: Optional[float] = None
    consecutive_failures: int = 0


@dataclass
class ProviderHealthStats:
    """Health statistics for a provider."""
    
    provider_name: str
    current_status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    
    # Statistics tracking
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    # Response time tracking
    total_response_time: float = 0.0
    min_response_time: Optional[float] = None
    max_response_time: Optional[float] = None
    
    # Health history (keep last 100 results)
    health_history: List[HealthCheckResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_checks == 0:
            return 0.0
        return self.successful_checks / self.total_checks
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.successful_checks == 0:
            return 0.0
        return self.total_response_time / self.successful_checks
    
    def add_result(self, result: HealthCheckResult) -> None:
        """Add a health check result."""
        self.last_check = result.timestamp
        self.total_checks += 1
        
        if result.status == HealthStatus.HEALTHY:
            self.successful_checks += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            
            if result.response_time_ms:
                response_time = result.response_time_ms
                self.total_response_time += response_time
                
                if self.min_response_time is None or response_time < self.min_response_time:
                    self.min_response_time = response_time
                
                if self.max_response_time is None or response_time > self.max_response_time:
                    self.max_response_time = response_time
        else:
            self.failed_checks += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
        
        # Update current status
        self.current_status = result.status
        
        # Add to history (keep last 100)
        self.health_history.append(result)
        if len(self.health_history) > 100:
            self.health_history.pop(0)


class LLMHealthChecker:
    """Health checker for LLM providers."""
    
    def __init__(
        self,
        provider_factory: ProviderFactory,
        check_interval: int = 60,  # seconds
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        timeout: int = 30  # seconds
    ):
        """Initialize the health checker.
        
        Args:
            provider_factory: Factory for creating providers
            check_interval: Interval between health checks in seconds
            failure_threshold: Number of consecutive failures before marking unhealthy
            recovery_threshold: Number of consecutive successes needed for recovery
            timeout: Timeout for health checks in seconds
        """
        self.provider_factory = provider_factory
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.timeout = timeout
        
        self._stats: Dict[str, ProviderHealthStats] = {}
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
        self._monitored_providers: Set[str] = set()
    
    def add_provider(self, provider_name: str) -> None:
        """Add a provider to health monitoring.
        
        Args:
            provider_name: Name of provider to monitor
        """
        self._monitored_providers.add(provider_name)
        if provider_name not in self._stats:
            self._stats[provider_name] = ProviderHealthStats(provider_name)
        logger.info(f"Added provider '{provider_name}' to health monitoring")
    
    def remove_provider(self, provider_name: str) -> None:
        """Remove a provider from health monitoring.
        
        Args:
            provider_name: Name of provider to stop monitoring
        """
        self._monitored_providers.discard(provider_name)
        logger.info(f"Removed provider '{provider_name}' from health monitoring")
    
    async def check_provider_health(self, provider_name: str) -> HealthCheckResult:
        """Check the health of a specific provider.
        
        Args:
            provider_name: Name of provider to check
            
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            provider = self.provider_factory.get_provider(provider_name, auto_initialize=False)
            
            # Perform health check with timeout
            is_healthy = await asyncio.wait_for(
                provider.health_check(),
                timeout=self.timeout
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if is_healthy:
                status = HealthStatus.HEALTHY
                error_message = None
            else:
                status = HealthStatus.DEGRADED
                error_message = "Provider health check returned False"
            
        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = HealthStatus.UNHEALTHY
            error_message = f"Health check timed out after {self.timeout}s"
            
        except ProviderUnavailableError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = HealthStatus.UNHEALTHY
            error_message = f"Provider unavailable: {str(e)}"
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = HealthStatus.UNHEALTHY
            error_message = f"Health check failed: {str(e)}"
        
        # Get current stats for enhanced result
        stats = self._stats.get(provider_name)
        success_rate = stats.success_rate if stats else None
        avg_response_time = stats.average_response_time if stats else None
        consecutive_failures = stats.consecutive_failures if stats else 0
        
        result = HealthCheckResult(
            provider_name=provider_name,
            status=status,
            response_time_ms=response_time_ms,
            error_message=error_message,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            consecutive_failures=consecutive_failures
        )
        
        # Update stats
        if provider_name not in self._stats:
            self._stats[provider_name] = ProviderHealthStats(provider_name)
        self._stats[provider_name].add_result(result)
        
        # Apply thresholds for status determination
        if stats:
            if status == HealthStatus.HEALTHY and stats.consecutive_failures >= self.failure_threshold:
                # Still in recovery period
                result.status = HealthStatus.DEGRADED
            elif status != HealthStatus.HEALTHY and stats.consecutive_successes >= self.recovery_threshold:
                # Sufficient recovery
                result.status = HealthStatus.HEALTHY
        
        return result
    
    async def check_all_providers(self) -> Dict[str, HealthCheckResult]:
        """Check health of all monitored providers.
        
        Returns:
            Dictionary mapping provider names to health results
        """
        results = {}
        
        tasks = []
        for provider_name in self._monitored_providers:
            task = asyncio.create_task(
                self.check_provider_health(provider_name),
                name=f"health_check_{provider_name}"
            )
            tasks.append((provider_name, task))
        
        # Wait for all checks to complete
        for provider_name, task in tasks:
            try:
                result = await task
                results[provider_name] = result
                
                if result.status == HealthStatus.UNHEALTHY:
                    logger.warning(f"Provider '{provider_name}' is unhealthy: {result.error_message}")
                elif result.status == HealthStatus.DEGRADED:
                    logger.info(f"Provider '{provider_name}' is degraded")
                
            except Exception as e:
                logger.error(f"Failed to check health of provider '{provider_name}': {e}")
                results[provider_name] = HealthCheckResult(
                    provider_name=provider_name,
                    status=HealthStatus.UNHEALTHY,
                    error_message=f"Health check task failed: {str(e)}"
                )
        
        return results
    
    def get_provider_stats(self, provider_name: str) -> Optional[ProviderHealthStats]:
        """Get health statistics for a provider.
        
        Args:
            provider_name: Name of provider
            
        Returns:
            Provider health statistics, None if not monitored
        """
        return self._stats.get(provider_name)
    
    def get_all_stats(self) -> Dict[str, ProviderHealthStats]:
        """Get health statistics for all monitored providers."""
        return dict(self._stats)
    
    def get_healthy_providers(self) -> List[str]:
        """Get list of currently healthy provider names."""
        healthy = []
        for provider_name, stats in self._stats.items():
            if stats.current_status == HealthStatus.HEALTHY:
                healthy.append(provider_name)
        return healthy
    
    def get_unhealthy_providers(self) -> List[str]:
        """Get list of currently unhealthy provider names."""
        unhealthy = []
        for provider_name, stats in self._stats.items():
            if stats.current_status == HealthStatus.UNHEALTHY:
                unhealthy.append(provider_name)
        return unhealthy
    
    def is_provider_healthy(self, provider_name: str) -> bool:
        """Check if a specific provider is currently healthy.
        
        Args:
            provider_name: Name of provider
            
        Returns:
            True if healthy, False otherwise
        """
        stats = self._stats.get(provider_name)
        return stats is not None and stats.current_status == HealthStatus.HEALTHY
    
    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._running:
            logger.warning("Health monitoring is already running")
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started health monitoring with {self.check_interval}s interval")
    
    async def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None
        
        logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self.check_all_providers()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                # Continue monitoring after error
                await asyncio.sleep(min(self.check_interval, 30))
    
    def reset_stats(self, provider_name: Optional[str] = None) -> None:
        """Reset health statistics.
        
        Args:
            provider_name: Specific provider to reset, or None for all
        """
        if provider_name:
            if provider_name in self._stats:
                self._stats[provider_name] = ProviderHealthStats(provider_name)
                logger.info(f"Reset health stats for provider '{provider_name}'")
        else:
            for name in self._stats:
                self._stats[name] = ProviderHealthStats(name)
            logger.info("Reset health stats for all providers")