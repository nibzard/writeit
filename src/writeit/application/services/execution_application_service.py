"""Execution Application Service.

Coordinates LLM execution, cache management, token analytics, and performance
optimization across the execution domain and other domains.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Union, AsyncGenerator
from enum import Enum
from datetime import datetime, timedelta
import asyncio

from ...domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
    TokenAnalyticsService,
    ProviderSelectionStrategy,
    FallbackTrigger,
    RequestPriority,
    CacheStrategy,
    CacheOptimizationGoal,
    AnalyticsPeriod,
    CostOptimizationLevel,
    UsageAlert,
)
from ...domains.execution.entities import LLMProvider, ExecutionContext
from ...domains.execution.value_objects import (
    TokenCount,
)
from ...domains.workspace.services import (
    WorkspaceManagementService,
    WorkspaceAnalyticsService,
)
from ...domains.workspace.entities import Workspace
from ...domains.workspace.value_objects import WorkspaceName


class ExecutionStrategy(str, Enum):
    """Execution strategies."""
    FASTEST = "fastest"          # Optimize for speed
    CHEAPEST = "cheapest"        # Optimize for cost
    BALANCED = "balanced"        # Balance speed and cost
    HIGHEST_QUALITY = "highest_quality"  # Optimize for quality
    CUSTOM = "custom"           # Custom strategy


class MonitoringLevel(str, Enum):
    """Monitoring levels."""
    BASIC = "basic"             # Basic monitoring
    DETAILED = "detailed"       # Detailed metrics
    COMPREHENSIVE = "comprehensive"  # Full monitoring
    DEBUG = "debug"             # Debug-level monitoring


class OptimizationGoal(str, Enum):
    """Optimization goals."""
    COST = "cost"               # Minimize costs
    LATENCY = "latency"         # Minimize latency
    THROUGHPUT = "throughput"   # Maximize throughput
    RELIABILITY = "reliability" # Maximize reliability
    QUALITY = "quality"         # Maximize quality


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ExecutionRequest:
    """Request for LLM execution."""
    prompt: str
    model_preference: List[str]
    workspace_name: Optional[str] = None
    execution_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED
    priority: RequestPriority = RequestPriority.NORMAL
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    streaming: bool = False
    cache_enabled: bool = True
    timeout: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionConfiguration:
    """Configuration for execution environment."""
    workspace_name: str
    default_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED
    cache_strategy: CacheStrategy = CacheStrategy.ADAPTIVE
    monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED
    cost_limit_daily: Optional[float] = None
    cost_limit_monthly: Optional[float] = None
    alert_thresholds: Optional[Dict[str, float]] = None
    preferred_providers: Optional[List[str]] = None
    fallback_providers: Optional[List[str]] = None


@dataclass
class PerformanceAnalysisRequest:
    """Request for performance analysis."""
    workspace_name: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    analysis_scope: str = "all"  # "all", "llm", "cache", "tokens"
    include_recommendations: bool = True
    include_predictions: bool = False


@dataclass
class OptimizationRequest:
    """Request for execution optimization."""
    workspace_name: str
    optimization_goal: OptimizationGoal
    optimization_level: CostOptimizationLevel = CostOptimizationLevel.MODERATE
    target_improvement: Optional[float] = None  # Percentage improvement target
    dry_run: bool = True


@dataclass
class MonitoringSetupRequest:
    """Request for monitoring setup."""
    workspace_name: str
    monitoring_level: MonitoringLevel
    alert_rules: List[Dict[str, Any]]
    dashboard_config: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class ExecutionApplicationError(Exception):
    """Base exception for execution application service errors."""
    pass


class ExecutionConfigurationError(ExecutionApplicationError):
    """Execution configuration error."""
    pass


class ExecutionFailedError(ExecutionApplicationError):
    """Execution failed error."""
    pass


class OptimizationError(ExecutionApplicationError):
    """Optimization error."""
    pass


class MonitoringError(ExecutionApplicationError):
    """Monitoring error."""
    pass


class ExecutionApplicationService:
    """
    Application service for execution operations.
    
    Coordinates LLM execution, cache management, token analytics, and
    performance optimization. Provides high-level use cases for execution
    management across CLI, TUI, and API interfaces.
    """
    
    def __init__(
        self,
        # Execution domain services
        llm_orchestration_service: LLMOrchestrationService,
        cache_management_service: CacheManagementService,
        token_analytics_service: TokenAnalyticsService,
        
        # Cross-domain services
        workspace_management_service: WorkspaceManagementService,
        workspace_analytics_service: WorkspaceAnalyticsService,
    ):
        """Initialize the execution application service."""
        # Execution domain services
        self._llm_orchestration = llm_orchestration_service
        self._cache_management = cache_management_service
        self._token_analytics = token_analytics_service
        
        # Cross-domain services
        self._workspace_management = workspace_management_service
        self._workspace_analytics = workspace_analytics_service

    async def execute_llm_request(
        self, 
        request: ExecutionRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute LLM request with comprehensive orchestration.
        
        Args:
            request: Execution request
            
        Yields:
            Execution progress and results
            
        Raises:
            ExecutionFailedError: If execution fails
        """
        try:
            # Resolve workspace
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Configure execution context
            execution_context = await self._create_execution_context(request, workspace)
            
            # Check cache if enabled
            if request.cache_enabled:
                cached_result = await self._cache_management.get_cached_response(
                    prompt=request.prompt,
                    model=request.model_preference[0] if request.model_preference else None,
                    workspace=workspace.name
                )
                if cached_result:
                    yield {
                        "status": "cached",
                        "source": "cache",
                        "content": cached_result.content,
                        "metadata": cached_result.metadata,
                        "cache_hit": True
                    }
                    return
            
            # Execute with orchestration
            async for execution_state in self._llm_orchestration.execute_with_orchestration(
                execution_context
            ):
                # Track token usage
                if execution_state.token_usage:
                    await self._token_analytics.record_token_usage(
                        workspace.name,
                        execution_state.token_usage
                    )
                
                # Cache successful responses
                if request.cache_enabled and execution_state.status == "completed":
                    await self._cache_management.cache_response(
                        prompt=request.prompt,
                        response=execution_state.content,
                        model=execution_state.model_used,
                        workspace=workspace.name,
                        metadata=execution_state.metadata
                    )
                
                # Record execution in analytics
                await self._workspace_analytics.record_llm_execution(
                    workspace.name,
                    execution_state
                )
                
                # Yield progress
                yield {
                    "status": execution_state.status,
                    "provider": execution_state.provider_used,
                    "model": execution_state.model_used,
                    "content": execution_state.content,
                    "partial_content": execution_state.partial_content,
                    "token_usage": execution_state.token_usage,
                    "execution_time": execution_state.execution_time,
                    "cache_hit": False,
                    "metadata": execution_state.metadata
                }
                
        except Exception as e:
            raise ExecutionFailedError(f"LLM execution failed: {e}") from e

    async def configure_execution_environment(
        self, 
        config: ExecutionConfiguration
    ) -> Dict[str, Any]:
        """
        Configure execution environment for workspace.
        
        Args:
            config: Execution configuration
            
        Returns:
            Configuration status and details
            
        Raises:
            ExecutionConfigurationError: If configuration fails
        """
        try:
            workspace = await self._resolve_workspace(config.workspace_name)
            
            # Configure LLM orchestration
            orchestration_config = {
                "default_strategy": self._map_execution_strategy(config.default_strategy),
                "preferred_providers": config.preferred_providers or [],
                "fallback_providers": config.fallback_providers or [],
                "cost_limits": {
                    "daily": config.cost_limit_daily,
                    "monthly": config.cost_limit_monthly
                }
            }
            
            await self._llm_orchestration.configure_workspace(
                workspace.name,
                orchestration_config
            )
            
            # Configure cache management
            await self._cache_management.configure_workspace_cache(
                workspace.name,
                strategy=config.cache_strategy
            )
            
            # Configure token analytics
            analytics_config = {
                "monitoring_level": config.monitoring_level.value,
                "alert_thresholds": config.alert_thresholds or {},
                "cost_tracking": True,
                "usage_optimization": True
            }
            
            await self._token_analytics.configure_workspace_analytics(
                workspace.name,
                analytics_config
            )
            
            # Set up monitoring
            if config.monitoring_level != MonitoringLevel.BASIC:
                await self._setup_advanced_monitoring(workspace, config)
            
            return {
                "workspace": workspace.name.value,
                "configuration_status": "success",
                "orchestration_enabled": True,
                "cache_enabled": True,
                "analytics_enabled": True,
                "monitoring_level": config.monitoring_level.value,
                "applied_settings": {
                    "default_strategy": config.default_strategy.value,
                    "cache_strategy": config.cache_strategy.value,
                    "cost_limits": orchestration_config["cost_limits"],
                    "preferred_providers": config.preferred_providers,
                }
            }
            
        except Exception as e:
            raise ExecutionConfigurationError(f"Failed to configure execution environment: {e}") from e

    async def analyze_performance(
        self, 
        request: PerformanceAnalysisRequest
    ) -> Dict[str, Any]:
        """
        Analyze execution performance across domains.
        
        Args:
            request: Performance analysis request
            
        Returns:
            Comprehensive performance analysis
        """
        try:
            workspace = await self._resolve_workspace(request.workspace_name)
            
            analysis = {
                "workspace": workspace.name.value,
                "analysis_period": {
                    "start": request.period_start,
                    "end": request.period_end
                },
                "analysis_scope": request.analysis_scope,
                "generated_at": datetime.now()
            }
            
            # LLM performance analysis
            if request.analysis_scope in ["all", "llm"]:
                llm_analysis = await self._llm_orchestration.analyze_performance(
                    workspace.name,
                    period_start=request.period_start,
                    period_end=request.period_end
                )
                analysis["llm_performance"] = llm_analysis.to_dict()
            
            # Cache performance analysis
            if request.analysis_scope in ["all", "cache"]:
                cache_analysis = await self._cache_management.analyze_cache_performance(
                    workspace.name,
                    period_start=request.period_start,
                    period_end=request.period_end
                )
                analysis["cache_performance"] = cache_analysis.to_dict()
            
            # Token usage analysis
            if request.analysis_scope in ["all", "tokens"]:
                token_analysis = await self._token_analytics.analyze_usage_patterns(
                    workspace.name,
                    period_start=request.period_start,
                    period_end=request.period_end
                )
                analysis["token_usage"] = token_analysis.to_dict()
            
            # Cross-domain insights
            analysis["insights"] = await self._generate_performance_insights(
                analysis, workspace
            )
            
            # Recommendations
            if request.include_recommendations:
                analysis["recommendations"] = await self._generate_performance_recommendations(
                    analysis, workspace
                )
            
            # Predictions
            if request.include_predictions:
                analysis["predictions"] = await self._generate_performance_predictions(
                    analysis, workspace
                )
            
            return analysis
            
        except Exception as e:
            raise ExecutionApplicationError(f"Performance analysis failed: {e}") from e

    async def optimize_execution(
        self, 
        request: OptimizationRequest
    ) -> Dict[str, Any]:
        """
        Optimize execution performance based on goals.
        
        Args:
            request: Optimization request
            
        Returns:
            Optimization results and plan
            
        Raises:
            OptimizationError: If optimization fails
        """
        try:
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Analyze current performance
            current_performance = await self.analyze_performance(
                PerformanceAnalysisRequest(
                    workspace_name=request.workspace_name,
                    include_recommendations=False,
                    include_predictions=False
                )
            )
            
            optimization_results = {
                "workspace": workspace.name.value,
                "optimization_goal": request.optimization_goal.value,
                "optimization_level": request.optimization_level.value,
                "dry_run": request.dry_run,
                "current_performance": current_performance,
                "optimization_plan": {},
                "expected_improvements": {},
                "implementation_status": {}
            }
            
            # Generate optimization plan based on goal
            if request.optimization_goal == OptimizationGoal.COST:
                cost_optimization = await self._token_analytics.generate_cost_optimization_plan(
                    workspace.name,
                    optimization_level=request.optimization_level,
                    target_savings=request.target_improvement
                )
                optimization_results["optimization_plan"]["cost"] = cost_optimization.to_dict()
                
            elif request.optimization_goal == OptimizationGoal.LATENCY:
                latency_optimization = await self._generate_latency_optimization_plan(
                    workspace, current_performance, request
                )
                optimization_results["optimization_plan"]["latency"] = latency_optimization
                
            elif request.optimization_goal == OptimizationGoal.THROUGHPUT:
                throughput_optimization = await self._generate_throughput_optimization_plan(
                    workspace, current_performance, request
                )
                optimization_results["optimization_plan"]["throughput"] = throughput_optimization
                
            elif request.optimization_goal == OptimizationGoal.RELIABILITY:
                reliability_optimization = await self._generate_reliability_optimization_plan(
                    workspace, current_performance, request
                )
                optimization_results["optimization_plan"]["reliability"] = reliability_optimization
                
            elif request.optimization_goal == OptimizationGoal.QUALITY:
                quality_optimization = await self._generate_quality_optimization_plan(
                    workspace, current_performance, request
                )
                optimization_results["optimization_plan"]["quality"] = quality_optimization
            
            # Execute optimization if not dry run
            if not request.dry_run:
                implementation_status = await self._implement_optimization_plan(
                    workspace, optimization_results["optimization_plan"]
                )
                optimization_results["implementation_status"] = implementation_status
            
            return optimization_results
            
        except Exception as e:
            raise OptimizationError(f"Execution optimization failed: {e}") from e

    async def setup_monitoring(
        self, 
        request: MonitoringSetupRequest
    ) -> Dict[str, Any]:
        """
        Set up comprehensive monitoring for workspace.
        
        Args:
            request: Monitoring setup request
            
        Returns:
            Monitoring setup status
            
        Raises:
            MonitoringError: If monitoring setup fails
        """
        try:
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Set up analytics monitoring
            analytics_monitoring = await self._token_analytics.setup_monitoring(
                workspace.name,
                monitoring_level=request.monitoring_level.value,
                alert_rules=request.alert_rules
            )
            
            # Set up cache monitoring
            cache_monitoring = await self._cache_management.setup_monitoring(
                workspace.name,
                monitoring_level=request.monitoring_level.value
            )
            
            # Set up LLM orchestration monitoring
            orchestration_monitoring = await self._llm_orchestration.setup_monitoring(
                workspace.name,
                monitoring_level=request.monitoring_level.value,
                alert_rules=request.alert_rules
            )
            
            # Set up workspace analytics integration
            workspace_monitoring = await self._workspace_analytics.setup_execution_monitoring(
                workspace.name,
                monitoring_config={
                    "level": request.monitoring_level.value,
                    "dashboard_config": request.dashboard_config,
                    "notification_settings": request.notification_settings
                }
            )
            
            return {
                "workspace": workspace.name.value,
                "monitoring_level": request.monitoring_level.value,
                "setup_status": "success",
                "components": {
                    "token_analytics": analytics_monitoring["status"],
                    "cache_management": cache_monitoring["status"],
                    "llm_orchestration": orchestration_monitoring["status"],
                    "workspace_analytics": workspace_monitoring["status"]
                },
                "alert_rules_configured": len(request.alert_rules),
                "dashboard_enabled": bool(request.dashboard_config),
                "notifications_enabled": bool(request.notification_settings)
            }
            
        except Exception as e:
            raise MonitoringError(f"Monitoring setup failed: {e}") from e

    async def get_execution_status(
        self, 
        workspace_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current execution environment status.
        
        Args:
            workspace_name: Optional workspace name
            
        Returns:
            Comprehensive execution status
        """
        try:
            workspace = await self._resolve_workspace(workspace_name)
            
            # Get provider status
            provider_status = await self._llm_orchestration.get_provider_status()
            
            # Get cache status
            cache_status = await self._cache_management.get_workspace_cache_status(
                workspace.name
            )
            
            # Get token usage status
            token_status = await self._token_analytics.get_current_usage_status(
                workspace.name
            )
            
            # Get recent alerts
            recent_alerts = await self._get_recent_alerts(workspace)
            
            return {
                "workspace": workspace.name.value,
                "timestamp": datetime.now(),
                "overall_status": "healthy",  # Computed based on components
                "providers": {
                    "available_providers": len(provider_status.available_providers),
                    "active_providers": len(provider_status.active_providers),
                    "provider_details": provider_status.provider_details
                },
                "cache": {
                    "status": cache_status.status,
                    "hit_rate": cache_status.hit_rate,
                    "size_mb": cache_status.size_mb,
                    "entries": cache_status.entry_count
                },
                "token_usage": {
                    "daily_usage": token_status.daily_usage,
                    "monthly_usage": token_status.monthly_usage,
                    "daily_cost": token_status.daily_cost,
                    "monthly_cost": token_status.monthly_cost,
                    "budget_status": token_status.budget_status
                },
                "recent_alerts": recent_alerts,
                "performance_metrics": {
                    "average_latency": cache_status.average_latency,
                    "success_rate": provider_status.overall_success_rate,
                    "throughput": provider_status.average_throughput
                }
            }
            
        except Exception as e:
            raise ExecutionApplicationError(f"Failed to get execution status: {e}") from e

    async def handle_usage_alerts(
        self, 
        workspace_name: str
    ) -> List[Dict[str, Any]]:
        """
        Handle and process usage alerts for workspace.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            List of active alerts with recommended actions
        """
        try:
            workspace = await self._resolve_workspace(workspace_name)
            
            # Get active alerts
            token_alerts = await self._token_analytics.get_active_alerts(workspace.name)
            cache_alerts = await self._cache_management.get_active_alerts(workspace.name)
            orchestration_alerts = await self._llm_orchestration.get_active_alerts(workspace.name)
            
            all_alerts = []
            
            # Process token alerts
            for alert in token_alerts:
                alert_info = {
                    "id": alert.id,
                    "type": "token_usage",
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "data": alert.data,
                    "recommended_actions": await self._get_token_alert_actions(alert)
                }
                all_alerts.append(alert_info)
            
            # Process cache alerts
            for alert in cache_alerts:
                alert_info = {
                    "id": alert.id,
                    "type": "cache_performance",
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "data": alert.data,
                    "recommended_actions": await self._get_cache_alert_actions(alert)
                }
                all_alerts.append(alert_info)
            
            # Process orchestration alerts
            for alert in orchestration_alerts:
                alert_info = {
                    "id": alert.id,
                    "type": "llm_orchestration",
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "data": alert.data,
                    "recommended_actions": await self._get_orchestration_alert_actions(alert)
                }
                all_alerts.append(alert_info)
            
            # Sort by severity and timestamp
            all_alerts.sort(key=lambda x: (
                self._severity_order(x["severity"]),
                x["timestamp"]
            ), reverse=True)
            
            return all_alerts
            
        except Exception as e:
            raise ExecutionApplicationError(f"Failed to handle usage alerts: {e}") from e

    # Private helper methods
    
    async def _resolve_workspace(self, workspace_name: Optional[str]) -> Workspace:
        """Resolve workspace, using active workspace if none specified."""
        if workspace_name:
            workspace = await self._workspace_management.get_workspace(
                WorkspaceName(workspace_name)
            )
        else:
            workspace = await self._workspace_management.get_active_workspace()
        
        if not workspace:
            raise ExecutionApplicationError("No workspace available")
        
        return workspace

    async def _create_execution_context(
        self, 
        request: ExecutionRequest, 
        workspace: Workspace
    ) -> ExecutionContext:
        """Create execution context from request."""
        return ExecutionContext(
            prompt=request.prompt,
            model_preferences=request.model_preference,
            workspace_name=workspace.name,
            execution_strategy=self._map_execution_strategy(request.execution_strategy),
            priority=request.priority,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            streaming=request.streaming,
            timeout=request.timeout,
            metadata=request.metadata or {}
        )

    def _map_execution_strategy(self, strategy: ExecutionStrategy) -> ProviderSelectionStrategy:
        """Map application execution strategy to domain strategy."""
        mapping = {
            ExecutionStrategy.FASTEST: ProviderSelectionStrategy.LOWEST_LATENCY,
            ExecutionStrategy.CHEAPEST: ProviderSelectionStrategy.LOWEST_COST,
            ExecutionStrategy.BALANCED: ProviderSelectionStrategy.BALANCED,
            ExecutionStrategy.HIGHEST_QUALITY: ProviderSelectionStrategy.HIGHEST_QUALITY,
            ExecutionStrategy.CUSTOM: ProviderSelectionStrategy.CUSTOM
        }
        return mapping.get(strategy, ProviderSelectionStrategy.BALANCED)

    async def _setup_advanced_monitoring(
        self, 
        workspace: Workspace, 
        config: ExecutionConfiguration
    ) -> None:
        """Set up advanced monitoring based on configuration."""
        # Set up alerting thresholds
        if config.alert_thresholds:
            await self._token_analytics.configure_alert_thresholds(
                workspace.name,
                config.alert_thresholds
            )
        
        # Set up performance monitoring
        if config.monitoring_level in [MonitoringLevel.COMPREHENSIVE, MonitoringLevel.DEBUG]:
            await self._llm_orchestration.enable_detailed_monitoring(workspace.name)
            await self._cache_management.enable_detailed_monitoring(workspace.name)

    async def _generate_performance_insights(
        self, 
        analysis: Dict[str, Any], 
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """Generate cross-domain performance insights."""
        insights = []
        
        # Cache-token correlation insight
        if "cache_performance" in analysis and "token_usage" in analysis:
            cache_hit_rate = analysis["cache_performance"].get("hit_rate", 0)
            token_savings = cache_hit_rate * analysis["token_usage"].get("total_tokens", 0)
            cost_savings = token_savings * 0.001  # Rough estimate
            
            insights.append({
                "type": "cost_optimization",
                "title": "Cache Impact on Costs",
                "description": f"Cache is saving approximately {token_savings:.0f} tokens and ${cost_savings:.2f}",
                "impact": "positive" if cache_hit_rate > 0.2 else "negative",
                "data": {
                    "cache_hit_rate": cache_hit_rate,
                    "estimated_token_savings": token_savings,
                    "estimated_cost_savings": cost_savings
                }
            })
        
        # Provider performance insight
        if "llm_performance" in analysis:
            provider_performance = analysis["llm_performance"].get("provider_metrics", {})
            if provider_performance:
                best_provider = max(provider_performance.items(), 
                                  key=lambda x: x[1].get("success_rate", 0))
                insights.append({
                    "type": "provider_optimization",
                    "title": "Best Performing Provider",
                    "description": f"Provider '{best_provider[0]}' has the highest success rate at {best_provider[1].get('success_rate', 0):.1%}",
                    "impact": "informational",
                    "data": {
                        "provider": best_provider[0],
                        "metrics": best_provider[1]
                    }
                })
        
        return insights

    async def _generate_performance_recommendations(
        self, 
        analysis: Dict[str, Any], 
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Cache recommendations
        if "cache_performance" in analysis:
            cache_hit_rate = analysis["cache_performance"].get("hit_rate", 0)
            if cache_hit_rate < 0.3:
                recommendations.append({
                    "type": "cache_optimization",
                    "priority": "high",
                    "title": "Low Cache Hit Rate",
                    "description": f"Cache hit rate is {cache_hit_rate:.1%}. Consider enabling more aggressive caching.",
                    "action": "Enable template-based caching and increase cache TTL",
                    "estimated_impact": "20-40% cost reduction"
                })
        
        # Cost recommendations
        if "token_usage" in analysis:
            monthly_cost = analysis["token_usage"].get("monthly_cost", 0)
            if monthly_cost > 100:  # Threshold for high costs
                recommendations.append({
                    "type": "cost_optimization",
                    "priority": "medium",
                    "title": "High Monthly Costs",
                    "description": f"Monthly costs are ${monthly_cost:.2f}. Consider optimization strategies.",
                    "action": "Review model selection and implement prompt optimization",
                    "estimated_impact": "10-25% cost reduction"
                })
        
        # Performance recommendations
        if "llm_performance" in analysis:
            avg_latency = analysis["llm_performance"].get("average_latency", 0)
            if avg_latency > 5000:  # 5 seconds threshold
                recommendations.append({
                    "type": "performance_optimization",
                    "priority": "medium",
                    "title": "High Latency",
                    "description": f"Average response time is {avg_latency/1000:.1f}s. Consider optimization.",
                    "action": "Review provider selection and enable parallel processing",
                    "estimated_impact": "30-50% latency reduction"
                })
        
        return recommendations

    async def _generate_performance_predictions(
        self, 
        analysis: Dict[str, Any], 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Generate performance predictions based on historical data."""
        predictions = {}
        
        # Cost prediction
        if "token_usage" in analysis:
            current_monthly = analysis["token_usage"].get("monthly_cost", 0)
            growth_rate = 0.1  # Could be calculated from historical data
            predictions["cost"] = {
                "next_month_estimate": current_monthly * (1 + growth_rate),
                "quarterly_estimate": current_monthly * 3 * (1 + growth_rate),
                "growth_rate": growth_rate,
                "confidence": 0.8
            }
        
        # Usage prediction
        if "token_usage" in analysis:
            current_tokens = analysis["token_usage"].get("monthly_tokens", 0)
            predictions["usage"] = {
                "next_month_tokens": current_tokens * 1.1,
                "peak_usage_forecast": current_tokens * 1.5,
                "efficiency_trend": "improving"  # Could be calculated
            }
        
        return predictions

    async def _generate_latency_optimization_plan(
        self, 
        workspace: Workspace, 
        performance: Dict[str, Any], 
        request: OptimizationRequest
    ) -> Dict[str, Any]:
        """Generate latency optimization plan."""
        return {
            "current_latency": performance.get("llm_performance", {}).get("average_latency", 0),
            "target_improvement": request.target_improvement or 30,
            "strategies": [
                {
                    "name": "Provider Optimization",
                    "description": "Switch to faster providers for time-sensitive requests",
                    "estimated_improvement": "20-40%",
                    "implementation_effort": "low"
                },
                {
                    "name": "Parallel Processing",
                    "description": "Enable parallel execution for independent requests",
                    "estimated_improvement": "30-60%",
                    "implementation_effort": "medium"
                },
                {
                    "name": "Cache Warming",
                    "description": "Pre-populate cache with common requests",
                    "estimated_improvement": "50-80%",
                    "implementation_effort": "medium"
                }
            ]
        }

    async def _generate_throughput_optimization_plan(
        self, 
        workspace: Workspace, 
        performance: Dict[str, Any], 
        request: OptimizationRequest
    ) -> Dict[str, Any]:
        """Generate throughput optimization plan."""
        return {
            "current_throughput": performance.get("llm_performance", {}).get("requests_per_minute", 0),
            "target_improvement": request.target_improvement or 50,
            "strategies": [
                {
                    "name": "Batch Processing",
                    "description": "Group similar requests for batch processing",
                    "estimated_improvement": "40-80%",
                    "implementation_effort": "medium"
                },
                {
                    "name": "Connection Pooling",
                    "description": "Optimize connection management for providers",
                    "estimated_improvement": "20-30%",
                    "implementation_effort": "low"
                },
                {
                    "name": "Load Balancing",
                    "description": "Distribute requests across multiple providers",
                    "estimated_improvement": "50-100%",
                    "implementation_effort": "high"
                }
            ]
        }

    async def _generate_reliability_optimization_plan(
        self, 
        workspace: Workspace, 
        performance: Dict[str, Any], 
        request: OptimizationRequest
    ) -> Dict[str, Any]:
        """Generate reliability optimization plan."""
        return {
            "current_success_rate": performance.get("llm_performance", {}).get("success_rate", 0),
            "target_improvement": request.target_improvement or 99,
            "strategies": [
                {
                    "name": "Enhanced Fallbacks",
                    "description": "Configure multiple fallback providers",
                    "estimated_improvement": "5-15%",
                    "implementation_effort": "low"
                },
                {
                    "name": "Retry Logic",
                    "description": "Implement intelligent retry mechanisms",
                    "estimated_improvement": "10-20%",
                    "implementation_effort": "medium"
                },
                {
                    "name": "Health Monitoring",
                    "description": "Real-time provider health monitoring",
                    "estimated_improvement": "3-8%",
                    "implementation_effort": "medium"
                }
            ]
        }

    async def _generate_quality_optimization_plan(
        self, 
        workspace: Workspace, 
        performance: Dict[str, Any], 
        request: OptimizationRequest
    ) -> Dict[str, Any]:
        """Generate quality optimization plan."""
        return {
            "current_quality_score": performance.get("llm_performance", {}).get("average_quality", 0),
            "target_improvement": request.target_improvement or 20,
            "strategies": [
                {
                    "name": "Model Selection",
                    "description": "Use higher-quality models for important requests",
                    "estimated_improvement": "15-30%",
                    "implementation_effort": "low"
                },
                {
                    "name": "Prompt Optimization",
                    "description": "Optimize prompts based on quality feedback",
                    "estimated_improvement": "20-40%",
                    "implementation_effort": "high"
                },
                {
                    "name": "Quality Monitoring",
                    "description": "Implement continuous quality assessment",
                    "estimated_improvement": "10-25%",
                    "implementation_effort": "medium"
                }
            ]
        }

    async def _implement_optimization_plan(
        self, 
        workspace: Workspace, 
        optimization_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implement optimization plan."""
        implementation_status = {}
        
        for plan_type, plan_details in optimization_plan.items():
            try:
                if plan_type == "cost":
                    status = await self._token_analytics.implement_cost_optimization(
                        workspace.name, plan_details
                    )
                elif plan_type == "latency":
                    status = await self._llm_orchestration.implement_latency_optimization(
                        workspace.name, plan_details
                    )
                elif plan_type == "cache":
                    status = await self._cache_management.implement_cache_optimization(
                        workspace.name, plan_details
                    )
                else:
                    status = {"status": "skipped", "reason": f"Unknown plan type: {plan_type}"}
                
                implementation_status[plan_type] = status
                
            except Exception as e:
                implementation_status[plan_type] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return implementation_status

    async def _get_recent_alerts(self, workspace: Workspace) -> List[Dict[str, Any]]:
        """Get recent alerts for workspace."""
        # Get alerts from last 24 hours
        since = datetime.now() - timedelta(hours=24)
        
        token_alerts = await self._token_analytics.get_alerts_since(workspace.name, since)
        cache_alerts = await self._cache_management.get_alerts_since(workspace.name, since)
        orchestration_alerts = await self._llm_orchestration.get_alerts_since(workspace.name, since)
        
        all_alerts = []
        
        for alert in token_alerts:
            all_alerts.append({
                "type": "token_usage",
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp
            })
        
        for alert in cache_alerts:
            all_alerts.append({
                "type": "cache",
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp
            })
        
        for alert in orchestration_alerts:
            all_alerts.append({
                "type": "orchestration",
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp
            })
        
        # Sort by timestamp, most recent first
        all_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return all_alerts[:10]  # Return last 10 alerts

    async def _get_token_alert_actions(self, alert: UsageAlert) -> List[str]:
        """Get recommended actions for token usage alerts."""
        actions = []
        
        if alert.alert_type == "budget_exceeded":
            actions.extend([
                "Review high-usage periods and optimize prompts",
                "Consider switching to more cost-effective models",
                "Implement stricter usage controls"
            ])
        elif alert.alert_type == "unusual_usage":
            actions.extend([
                "Investigate spike in usage patterns",
                "Check for automated processes consuming tokens",
                "Review recent pipeline executions"
            ])
        
        return actions

    async def _get_cache_alert_actions(self, alert: Any) -> List[str]:
        """Get recommended actions for cache alerts."""
        actions = []
        
        if "low_hit_rate" in alert.message.lower():
            actions.extend([
                "Enable more aggressive caching policies",
                "Review cache TTL settings",
                "Analyze cache key patterns for optimization"
            ])
        elif "high_memory" in alert.message.lower():
            actions.extend([
                "Clear old cache entries",
                "Reduce cache size limits",
                "Implement cache eviction policies"
            ])
        
        return actions

    async def _get_orchestration_alert_actions(self, alert: Any) -> List[str]:
        """Get recommended actions for orchestration alerts."""
        actions = []
        
        if "provider_failure" in alert.message.lower():
            actions.extend([
                "Check provider API status",
                "Review fallback configuration",
                "Consider adding additional providers"
            ])
        elif "rate_limit" in alert.message.lower():
            actions.extend([
                "Implement request throttling",
                "Distribute load across providers",
                "Review rate limit configurations"
            ])
        
        return actions

    def _severity_order(self, severity: str) -> int:
        """Map severity to numeric order for sorting."""
        order = {
            "critical": 4,
            "error": 3,
            "warning": 2,
            "info": 1
        }
        return order.get(severity.lower(), 0)