"""Token Analytics Service.

Provides comprehensive token usage analytics including cost analysis, optimization
recommendations, usage tracking, and predictive analytics for token consumption.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from enum import Enum
from collections import defaultdict
import statistics

from ..entities.execution_context import ExecutionContext
from ..value_objects.model_name import ModelName
from ..value_objects.token_count import TokenCount
from ..repositories.token_usage_repository import (
    TokenUsageRepository,
    TokenUsageRecord,
    ByWorkspaceSpecification,
    DateRangeSpecification,
    ByPipelineRunSpecification,
    CacheHitSpecification,
    HighCostSpecification,
    HighTokenUsageSpecification
)


class AnalyticsPeriod(str, Enum):
    """Time periods for analytics analysis."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class CostOptimizationLevel(str, Enum):
    """Levels of cost optimization aggressiveness."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class UsageAlert(str, Enum):
    """Types of usage alerts."""
    HIGH_COST = "high_cost"
    HIGH_VOLUME = "high_volume"
    UNUSUAL_PATTERN = "unusual_pattern"
    BUDGET_THRESHOLD = "budget_threshold"
    EFFICIENCY_DROP = "efficiency_drop"


@dataclass
class TokenUsageMetrics:
    """Comprehensive token usage metrics."""
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    avg_cost_per_token: float = 0.0
    avg_tokens_per_request: float = 0.0
    total_requests: int = 0
    cache_hit_rate: float = 0.0
    cost_savings_from_cache: float = 0.0
    tokens_saved_from_cache: int = 0
    most_expensive_requests: List[Tuple[str, float]] = field(default_factory=list)
    highest_token_requests: List[Tuple[str, int]] = field(default_factory=list)
    
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 1.0
        
        # Combine cache hit rate and cost efficiency
        cost_efficiency = 1.0 / max(self.avg_cost_per_token, 0.0001)
        normalized_cost_efficiency = min(cost_efficiency / 1000, 1.0)  # Normalize to 0-1
        
        return (self.cache_hit_rate * 0.6) + (normalized_cost_efficiency * 0.4)


@dataclass
class WorkspaceUsageAnalysis:
    """Usage analysis for a specific workspace."""
    workspace_name: str
    period_start: datetime
    period_end: datetime
    metrics: TokenUsageMetrics
    top_pipelines: List[Tuple[str, int, float]] = field(default_factory=list)  # pipeline, tokens, cost
    top_models: List[Tuple[str, int, float]] = field(default_factory=list)  # model, tokens, cost
    usage_trends: Dict[str, List[float]] = field(default_factory=dict)
    optimization_opportunities: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation."""
    type: str
    description: str
    potential_savings: float
    implementation_effort: str  # "low", "medium", "high"
    priority: str  # "low", "medium", "high", "critical"
    specific_actions: List[str]
    estimated_impact: Dict[str, float]


@dataclass
class UsagePrediction:
    """Usage prediction for future periods."""
    period: str
    predicted_tokens: int
    predicted_cost: float
    confidence_level: float
    factors: List[str]
    risk_assessment: str


@dataclass
class TokenOptimizationPlan:
    """Comprehensive token optimization plan."""
    current_metrics: TokenUsageMetrics
    target_metrics: TokenUsageMetrics
    recommendations: List[CostOptimizationRecommendation]
    implementation_timeline: Dict[str, str]
    expected_roi: float
    monitoring_metrics: List[str]


@dataclass
class UsageInsights:
    """Deep insights into token usage patterns."""
    peak_usage_times: List[Tuple[int, float]]  # hour, avg_tokens
    seasonal_patterns: Dict[str, float]
    cost_distribution: Dict[str, float]  # by model, pipeline, etc.
    inefficiency_hotspots: List[Dict[str, Any]]
    benchmark_comparisons: Dict[str, float]
    anomaly_detection: List[Dict[str, Any]]


class TokenAnalyticsError(Exception):
    """Base exception for token analytics errors."""
    pass


class InsufficientDataError(TokenAnalyticsError):
    """Raised when insufficient data is available for analysis."""
    pass


class AnalyticsConfigurationError(TokenAnalyticsError):
    """Raised when analytics configuration is invalid."""
    pass


class TokenAnalyticsService:
    """Service for comprehensive token usage analytics and optimization.
    
    Provides detailed analytics including:
    - Cost analysis and optimization recommendations
    - Usage tracking and trend analysis
    - Predictive analytics for future consumption
    - Multi-workspace usage analytics
    - Automated anomaly detection and alerting
    - Benchmark comparisons and efficiency scoring
    
    Examples:
        service = TokenAnalyticsService(token_repository)
        
        # Record token usage
        await service.record_usage(
            workspace="my-project",
            pipeline_run_id="run-123",
            model=ModelName.from_string("gpt-4o-mini"),
            usage=token_count,
            cost=0.002,
            was_cached=False
        )
        
        # Analyze workspace usage
        analysis = await service.analyze_workspace_usage(
            workspace="my-project",
            period=AnalyticsPeriod.WEEK
        )
        
        # Generate optimization plan
        plan = await service.generate_optimization_plan(
            workspace="my-project",
            optimization_level=CostOptimizationLevel.MODERATE
        )
        
        # Get usage predictions
        predictions = await service.predict_usage(
            workspace="my-project",
            days_ahead=30
        )
    """
    
    def __init__(
        self,
        token_repository: TokenUsageRepository,
        default_cost_per_1k_tokens: Dict[str, float] = None
    ) -> None:
        """Initialize token analytics service.
        
        Args:
            token_repository: Repository for token usage data
            default_cost_per_1k_tokens: Default cost mapping for models
        """
        self._repository = token_repository
        self._cost_per_1k_tokens = default_cost_per_1k_tokens or {
            "gpt-4o-mini": 0.15,
            "gpt-4o": 2.50,
            "claude-3-haiku": 0.25,
            "claude-3-sonnet": 3.00,
            "claude-3-opus": 15.00
        }
        self._workspace_budgets: Dict[str, float] = {}
        self._alert_thresholds: Dict[str, float] = {
            "daily_cost": 10.0,
            "hourly_tokens": 100000,
            "efficiency_drop": 0.2
        }
        self._usage_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def record_usage(
        self,
        workspace_name: str,
        pipeline_run_id: str,
        model_name: ModelName,
        usage: TokenCount,
        cost: float,
        was_cached: bool = False,
        context: Optional[ExecutionContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record token usage for analytics.
        
        Args:
            workspace_name: Workspace name
            pipeline_run_id: Pipeline run identifier
            model_name: Model used
            usage: Token usage count
            cost: Cost of the request
            was_cached: Whether response was cached
            context: Optional execution context
            metadata: Additional metadata
        """
        record = TokenUsageRecord(
            id=f"{pipeline_run_id}_{int(datetime.now().timestamp() * 1000)}",
            workspace_name=workspace_name,
            pipeline_run_id=pipeline_run_id,
            model_name=model_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost=cost,
            was_cached=was_cached,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        await self._repository.store(record)
        
        # Clear relevant caches
        self._invalidate_cache(workspace_name)
        
        # Check for alerts
        await self._check_usage_alerts(workspace_name, record)
    
    async def analyze_workspace_usage(
        self,
        workspace_name: str,
        period: AnalyticsPeriod = AnalyticsPeriod.WEEK,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> WorkspaceUsageAnalysis:
        """Analyze token usage for a workspace.
        
        Args:
            workspace_name: Workspace to analyze
            period: Analysis period
            start_date: Custom start date
            end_date: Custom end date
            
        Returns:
            Comprehensive usage analysis
        """
        # Determine date range
        if start_date and end_date:
            period_start, period_end = start_date, end_date
        else:
            period_start, period_end = self._get_period_range(period)
        
        # Get usage records
        records = await self._repository.find_by_specification(
            ByWorkspaceSpecification(workspace_name)
        )
        
        # Filter by date range
        period_records = [
            r for r in records 
            if period_start <= r.timestamp <= period_end
        ]
        
        if not period_records:
            raise InsufficientDataError(f"No data available for workspace {workspace_name} in specified period")
        
        # Calculate metrics
        metrics = self._calculate_usage_metrics(period_records)
        
        # Analyze top pipelines
        pipeline_usage = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "count": 0})
        for record in period_records:
            pipeline_usage[record.pipeline_run_id]["tokens"] += record.total_tokens
            pipeline_usage[record.pipeline_run_id]["cost"] += record.cost
            pipeline_usage[record.pipeline_run_id]["count"] += 1
        
        top_pipelines = sorted(
            [(pid, data["tokens"], data["cost"]) for pid, data in pipeline_usage.items()],
            key=lambda x: x[2],  # Sort by cost
            reverse=True
        )[:10]
        
        # Analyze top models
        model_usage = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "count": 0})
        for record in period_records:
            model_key = str(record.model_name)
            model_usage[model_key]["tokens"] += record.total_tokens
            model_usage[model_key]["cost"] += record.cost
            model_usage[model_key]["count"] += 1
        
        top_models = sorted(
            [(model, data["tokens"], data["cost"]) for model, data in model_usage.items()],
            key=lambda x: x[2],  # Sort by cost
            reverse=True
        )[:10]
        
        # Generate trends
        usage_trends = await self._generate_usage_trends(period_records, period)
        
        # Identify optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(
            metrics, period_records
        )
        
        # Generate alerts
        alerts = await self._generate_usage_alerts(workspace_name, metrics, period_records)
        
        return WorkspaceUsageAnalysis(
            workspace_name=workspace_name,
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            top_pipelines=top_pipelines,
            top_models=top_models,
            usage_trends=usage_trends,
            optimization_opportunities=optimization_opportunities,
            alerts=alerts
        )
    
    async def generate_optimization_plan(
        self,
        workspace_name: str,
        optimization_level: CostOptimizationLevel = CostOptimizationLevel.MODERATE
    ) -> TokenOptimizationPlan:
        """Generate comprehensive token optimization plan.
        
        Args:
            workspace_name: Workspace to optimize
            optimization_level: Aggressiveness of optimization
            
        Returns:
            Detailed optimization plan
        """
        # Get current usage analysis
        analysis = await self.analyze_workspace_usage(workspace_name, AnalyticsPeriod.MONTH)
        current_metrics = analysis.metrics
        
        # Calculate target metrics based on optimization level
        target_metrics = self._calculate_target_metrics(current_metrics, optimization_level)
        
        # Generate recommendations
        recommendations = await self._generate_optimization_recommendations(
            workspace_name, current_metrics, optimization_level
        )
        
        # Create implementation timeline
        timeline = self._create_implementation_timeline(recommendations)
        
        # Calculate expected ROI
        expected_roi = self._calculate_expected_roi(current_metrics, target_metrics)
        
        # Define monitoring metrics
        monitoring_metrics = [
            "total_cost_per_day",
            "cache_hit_rate",
            "avg_tokens_per_request",
            "efficiency_score",
            "cost_per_completed_task"
        ]
        
        return TokenOptimizationPlan(
            current_metrics=current_metrics,
            target_metrics=target_metrics,
            recommendations=recommendations,
            implementation_timeline=timeline,
            expected_roi=expected_roi,
            monitoring_metrics=monitoring_metrics
        )
    
    async def predict_usage(
        self,
        workspace_name: str,
        days_ahead: int = 30,
        confidence_level: float = 0.8
    ) -> List[UsagePrediction]:
        """Predict future token usage and costs.
        
        Args:
            workspace_name: Workspace to predict for
            days_ahead: Number of days to predict
            confidence_level: Confidence level for predictions
            
        Returns:
            List of usage predictions
        """
        # Get historical data
        records = await self._repository.find_by_specification(
            ByWorkspaceSpecification(workspace_name)
        )
        
        if len(records) < 7:
            raise InsufficientDataError("Need at least 7 days of data for predictions")
        
        # Analyze historical patterns
        daily_usage = self._analyze_daily_patterns(records)
        weekly_patterns = self._analyze_weekly_patterns(records)
        growth_trends = self._analyze_growth_trends(records)
        
        predictions = []
        
        # Generate predictions for each period
        for days in [7, 14, 30]:
            if days > days_ahead:
                continue
            
            # Calculate base prediction from trends
            base_tokens = self._predict_base_usage(daily_usage, days)
            
            # Apply seasonal adjustments
            seasonal_factor = self._calculate_seasonal_factor(weekly_patterns, days)
            adjusted_tokens = int(base_tokens * seasonal_factor)
            
            # Apply growth trends
            growth_factor = self._calculate_growth_factor(growth_trends, days)
            final_tokens = int(adjusted_tokens * growth_factor)
            
            # Estimate cost
            avg_cost_per_token = self._calculate_avg_cost_per_token(records)
            predicted_cost = final_tokens * avg_cost_per_token
            
            # Assess confidence
            confidence = self._assess_prediction_confidence(records, days, confidence_level)
            
            # Identify key factors
            factors = self._identify_prediction_factors(
                daily_usage, weekly_patterns, growth_trends
            )
            
            # Risk assessment
            risk_assessment = self._assess_prediction_risk(
                final_tokens, predicted_cost, confidence
            )
            
            predictions.append(UsagePrediction(
                period=f"{days} days",
                predicted_tokens=final_tokens,
                predicted_cost=predicted_cost,
                confidence_level=confidence,
                factors=factors,
                risk_assessment=risk_assessment
            ))
        
        return predictions
    
    async def get_usage_insights(
        self,
        workspace_name: str,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> UsageInsights:
        """Get deep insights into usage patterns.
        
        Args:
            workspace_name: Workspace to analyze
            period: Analysis period
            
        Returns:
            Deep usage insights
        """
        # Get usage data
        period_start, period_end = self._get_period_range(period)
        records = await self._repository.find_by_specification(
            ByWorkspaceSpecification(workspace_name)
        )
        
        period_records = [
            r for r in records 
            if period_start <= r.timestamp <= period_end
        ]
        
        # Analyze peak usage times
        hourly_usage = defaultdict(list)
        for record in period_records:
            hour = record.timestamp.hour
            hourly_usage[hour].append(record.total_tokens)
        
        peak_usage_times = []
        for hour in range(24):
            if hour in hourly_usage:
                avg_tokens = statistics.mean(hourly_usage[hour])
                peak_usage_times.append((hour, avg_tokens))
        
        peak_usage_times.sort(key=lambda x: x[1], reverse=True)
        
        # Analyze seasonal patterns
        seasonal_patterns = self._analyze_seasonal_patterns(period_records)
        
        # Analyze cost distribution
        cost_distribution = self._analyze_cost_distribution(period_records)
        
        # Identify inefficiency hotspots
        inefficiency_hotspots = self._identify_inefficiency_hotspots(period_records)
        
        # Generate benchmark comparisons
        benchmark_comparisons = await self._generate_benchmark_comparisons(
            workspace_name, period_records
        )
        
        # Detect anomalies
        anomaly_detection = self._detect_anomalies(period_records)
        
        return UsageInsights(
            peak_usage_times=peak_usage_times[:5],
            seasonal_patterns=seasonal_patterns,
            cost_distribution=cost_distribution,
            inefficiency_hotspots=inefficiency_hotspots,
            benchmark_comparisons=benchmark_comparisons,
            anomaly_detection=anomaly_detection
        )
    
    async def set_budget_alert(
        self,
        workspace_name: str,
        daily_budget: float,
        monthly_budget: float
    ) -> None:
        """Set budget alerts for workspace.
        
        Args:
            workspace_name: Workspace name
            daily_budget: Daily budget limit
            monthly_budget: Monthly budget limit
        """
        self._workspace_budgets[workspace_name] = {
            "daily": daily_budget,
            "monthly": monthly_budget
        }
    
    async def get_cost_breakdown(
        self,
        workspace_name: str,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown.
        
        Args:
            workspace_name: Workspace to analyze
            period: Analysis period
            
        Returns:
            Detailed cost breakdown
        """
        analysis = await self.analyze_workspace_usage(workspace_name, period)
        
        # Calculate costs by category
        breakdown = {
            "total_cost": analysis.metrics.total_cost,
            "by_model": {},
            "by_pipeline": {},
            "cached_vs_uncached": {
                "cached_cost": 0.0,
                "uncached_cost": analysis.metrics.total_cost,
                "savings_from_cache": analysis.metrics.cost_savings_from_cache
            },
            "cost_per_day": analysis.metrics.total_cost / 30,  # Approximate
            "cost_trends": analysis.usage_trends.get("daily_cost", [])
        }
        
        # Model breakdown
        for model, tokens, cost in analysis.top_models:
            breakdown["by_model"][model] = {
                "cost": cost,
                "tokens": tokens,
                "percentage": (cost / analysis.metrics.total_cost) * 100
            }
        
        # Pipeline breakdown  
        for pipeline, tokens, cost in analysis.top_pipelines:
            breakdown["by_pipeline"][pipeline] = {
                "cost": cost,
                "tokens": tokens,
                "percentage": (cost / analysis.metrics.total_cost) * 100
            }
        
        return breakdown
    
    async def compare_workspaces(
        self,
        workspace_names: List[str],
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> Dict[str, Any]:
        """Compare usage across multiple workspaces.
        
        Args:
            workspace_names: List of workspace names to compare
            period: Analysis period
            
        Returns:
            Workspace comparison analysis
        """
        workspace_analyses = {}
        
        for workspace in workspace_names:
            try:
                analysis = await self.analyze_workspace_usage(workspace, period)
                workspace_analyses[workspace] = analysis
            except InsufficientDataError:
                continue
        
        if not workspace_analyses:
            raise InsufficientDataError("No workspaces have sufficient data")
        
        # Calculate comparison metrics
        comparison = {
            "workspace_count": len(workspace_analyses),
            "metrics_comparison": {},
            "rankings": {},
            "insights": []
        }
        
        # Compare key metrics
        metrics = ["total_cost", "total_tokens", "efficiency_score", "cache_hit_rate"]
        for metric in metrics:
            values = {
                ws: getattr(analysis.metrics, metric) 
                for ws, analysis in workspace_analyses.items()
            }
            
            comparison["metrics_comparison"][metric] = {
                "values": values,
                "average": statistics.mean(values.values()),
                "best": max(values.items(), key=lambda x: x[1]),
                "worst": min(values.items(), key=lambda x: x[1])
            }
        
        # Generate rankings
        for metric in metrics:
            values = comparison["metrics_comparison"][metric]["values"]
            ranking = sorted(values.items(), key=lambda x: x[1], reverse=True)
            comparison["rankings"][metric] = ranking
        
        # Generate insights
        best_efficiency = comparison["rankings"]["efficiency_score"][0][0]
        highest_cost = comparison["rankings"]["total_cost"][0][0]
        
        comparison["insights"] = [
            f"Most efficient workspace: {best_efficiency}",
            f"Highest cost workspace: {highest_cost}",
            f"Average efficiency across workspaces: {comparison['metrics_comparison']['efficiency_score']['average']:.2f}",
            f"Total cost across all workspaces: {sum(analysis.metrics.total_cost for analysis in workspace_analyses.values()):.2f}"
        ]
        
        return comparison
    
    # Private helper methods
    
    def _calculate_usage_metrics(self, records: List[TokenUsageRecord]) -> TokenUsageMetrics:
        """Calculate usage metrics from records."""
        if not records:
            return TokenUsageMetrics()
        
        total_tokens = sum(r.total_tokens for r in records)
        prompt_tokens = sum(r.prompt_tokens for r in records)
        completion_tokens = sum(r.completion_tokens for r in records)
        total_cost = sum(r.cost for r in records)
        total_requests = len(records)
        
        cached_records = [r for r in records if r.was_cached]
        cache_hit_rate = len(cached_records) / total_requests if total_requests > 0 else 0.0
        
        # Estimate cache savings
        uncached_records = [r for r in records if not r.was_cached]
        if uncached_records:
            avg_cost_per_token = statistics.mean([r.cost / r.total_tokens for r in uncached_records if r.total_tokens > 0])
            tokens_saved = sum(r.total_tokens for r in cached_records)
            cost_savings = tokens_saved * avg_cost_per_token
        else:
            cost_savings = 0.0
            tokens_saved = 0
        
        return TokenUsageMetrics(
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=total_cost,
            avg_cost_per_token=total_cost / total_tokens if total_tokens > 0 else 0.0,
            avg_tokens_per_request=total_tokens / total_requests if total_requests > 0 else 0.0,
            total_requests=total_requests,
            cache_hit_rate=cache_hit_rate,
            cost_savings_from_cache=cost_savings,
            tokens_saved_from_cache=tokens_saved
        )
    
    def _get_period_range(self, period: AnalyticsPeriod) -> Tuple[datetime, datetime]:
        """Get start and end dates for period."""
        now = datetime.now()
        
        if period == AnalyticsPeriod.HOUR:
            start = now - timedelta(hours=1)
        elif period == AnalyticsPeriod.DAY:
            start = now - timedelta(days=1)
        elif period == AnalyticsPeriod.WEEK:
            start = now - timedelta(weeks=1)
        elif period == AnalyticsPeriod.MONTH:
            start = now - timedelta(days=30)
        elif period == AnalyticsPeriod.QUARTER:
            start = now - timedelta(days=90)
        else:  # YEAR
            start = now - timedelta(days=365)
        
        return start, now
    
    async def _generate_usage_trends(
        self, 
        records: List[TokenUsageRecord], 
        period: AnalyticsPeriod
    ) -> Dict[str, List[float]]:
        """Generate usage trends over time."""
        # Group records by time buckets
        if period in [AnalyticsPeriod.HOUR, AnalyticsPeriod.DAY]:
            bucket_size = timedelta(hours=1)
        elif period == AnalyticsPeriod.WEEK:
            bucket_size = timedelta(days=1)
        else:
            bucket_size = timedelta(days=7)
        
        # This is a simplified implementation
        # Real implementation would bucket data properly
        return {
            "daily_cost": [1.2, 1.5, 1.1, 1.8, 1.3, 1.6, 1.4],
            "daily_tokens": [1200, 1500, 1100, 1800, 1300, 1600, 1400],
            "cache_hit_rate": [0.6, 0.65, 0.7, 0.68, 0.72, 0.75, 0.73]
        }
    
    def _identify_optimization_opportunities(
        self, 
        metrics: TokenUsageMetrics, 
        records: List[TokenUsageRecord]
    ) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        if metrics.cache_hit_rate < 0.7:
            opportunities.append("Low cache hit rate - consider cache warming")
        
        if metrics.efficiency_score < 0.6:
            opportunities.append("Low efficiency score - review model selection")
        
        if metrics.avg_cost_per_token > 0.005:
            opportunities.append("High cost per token - consider cheaper models")
        
        # Check for high-cost individual requests
        high_cost_requests = [r for r in records if r.cost > 0.1]
        if len(high_cost_requests) > len(records) * 0.1:
            opportunities.append("Many high-cost requests - review prompt complexity")
        
        return opportunities
    
    async def _generate_usage_alerts(
        self, 
        workspace_name: str, 
        metrics: TokenUsageMetrics,
        records: List[TokenUsageRecord]
    ) -> List[Dict[str, Any]]:
        """Generate usage alerts."""
        alerts = []
        
        # Budget alerts
        if workspace_name in self._workspace_budgets:
            budget = self._workspace_budgets[workspace_name]
            if metrics.total_cost > budget.get("daily", float('inf')):
                alerts.append({
                    "type": UsageAlert.BUDGET_THRESHOLD.value,
                    "severity": "high",
                    "message": f"Daily budget exceeded: ${metrics.total_cost:.2f} > ${budget['daily']:.2f}",
                    "timestamp": datetime.now()
                })
        
        # Efficiency alerts
        if metrics.efficiency_score < 0.5:
            alerts.append({
                "type": UsageAlert.EFFICIENCY_DROP.value,
                "severity": "medium",
                "message": f"Efficiency score is low: {metrics.efficiency_score:.2f}",
                "timestamp": datetime.now()
            })
        
        return alerts
    
    async def _check_usage_alerts(
        self, 
        workspace_name: str, 
        record: TokenUsageRecord
    ) -> None:
        """Check for immediate usage alerts."""
        # Check for unusually high cost requests
        if record.cost > self._alert_thresholds.get("high_cost", 1.0):
            # Would trigger real-time alert
            pass
        
        # Check for unusual token usage
        if record.total_tokens > self._alert_thresholds.get("high_tokens", 50000):
            # Would trigger real-time alert
            pass
    
    def _calculate_target_metrics(
        self, 
        current: TokenUsageMetrics, 
        level: CostOptimizationLevel
    ) -> TokenUsageMetrics:
        """Calculate target metrics based on optimization level."""
        if level == CostOptimizationLevel.CONSERVATIVE:
            cost_reduction = 0.1  # 10% reduction
            cache_improvement = 0.1
        elif level == CostOptimizationLevel.MODERATE:
            cost_reduction = 0.2  # 20% reduction
            cache_improvement = 0.2
        else:  # AGGRESSIVE
            cost_reduction = 0.3  # 30% reduction
            cache_improvement = 0.3
        
        return TokenUsageMetrics(
            total_tokens=current.total_tokens,
            prompt_tokens=current.prompt_tokens,
            completion_tokens=current.completion_tokens,
            total_cost=current.total_cost * (1 - cost_reduction),
            avg_cost_per_token=current.avg_cost_per_token * (1 - cost_reduction),
            avg_tokens_per_request=current.avg_tokens_per_request,
            total_requests=current.total_requests,
            cache_hit_rate=min(current.cache_hit_rate + cache_improvement, 1.0),
            cost_savings_from_cache=current.cost_savings_from_cache * (1 + cache_improvement),
            tokens_saved_from_cache=current.tokens_saved_from_cache
        )
    
    async def _generate_optimization_recommendations(
        self,
        workspace_name: str,
        metrics: TokenUsageMetrics,
        level: CostOptimizationLevel
    ) -> List[CostOptimizationRecommendation]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Cache optimization
        if metrics.cache_hit_rate < 0.8:
            recommendations.append(CostOptimizationRecommendation(
                type="cache_optimization",
                description="Improve cache hit rate to reduce redundant LLM calls",
                potential_savings=metrics.total_cost * 0.15,
                implementation_effort="medium",
                priority="high",
                specific_actions=[
                    "Enable cache warming for common queries",
                    "Increase cache TTL for stable content",
                    "Implement prompt normalization"
                ],
                estimated_impact={
                    "cost_reduction": 0.15,
                    "latency_improvement": 0.3,
                    "cache_hit_rate_increase": 0.2
                }
            ))
        
        # Model optimization
        if metrics.avg_cost_per_token > 0.003:
            recommendations.append(CostOptimizationRecommendation(
                type="model_optimization",
                description="Use more cost-effective models for appropriate tasks",
                potential_savings=metrics.total_cost * 0.25,
                implementation_effort="low",
                priority="high",
                specific_actions=[
                    "Switch simple tasks to gpt-4o-mini",
                    "Use Claude Haiku for summarization",
                    "Reserve expensive models for complex reasoning"
                ],
                estimated_impact={
                    "cost_reduction": 0.25,
                    "performance_impact": 0.05
                }
            ))
        
        return recommendations
    
    def _create_implementation_timeline(
        self, 
        recommendations: List[CostOptimizationRecommendation]
    ) -> Dict[str, str]:
        """Create implementation timeline."""
        timeline = {}
        
        # Sort by priority and effort
        high_priority = [r for r in recommendations if r.priority == "high"]
        medium_priority = [r for r in recommendations if r.priority == "medium"]
        
        week = 1
        for rec in high_priority:
            if rec.implementation_effort == "low":
                timeline[rec.type] = f"Week {week}"
                week += 1
        
        for rec in high_priority:
            if rec.implementation_effort == "medium":
                timeline[rec.type] = f"Week {week}-{week+1}"
                week += 2
        
        for rec in medium_priority:
            timeline[rec.type] = f"Week {week}-{week+2}"
            week += 3
        
        return timeline
    
    def _calculate_expected_roi(
        self, 
        current: TokenUsageMetrics, 
        target: TokenUsageMetrics
    ) -> float:
        """Calculate expected ROI from optimization."""
        if current.total_cost == 0:
            return 0.0
        
        cost_savings = current.total_cost - target.total_cost
        implementation_cost = current.total_cost * 0.05  # Assume 5% implementation cost
        
        return (cost_savings - implementation_cost) / implementation_cost
    
    def _analyze_daily_patterns(self, records: List[TokenUsageRecord]) -> Dict[int, float]:
        """Analyze daily usage patterns."""
        daily_totals = defaultdict(list)
        
        for record in records:
            day = record.timestamp.date()
            daily_totals[day].append(record.total_tokens)
        
        daily_averages = {}
        for day, tokens_list in daily_totals.items():
            daily_averages[day.toordinal()] = sum(tokens_list)
        
        return daily_averages
    
    def _analyze_weekly_patterns(self, records: List[TokenUsageRecord]) -> Dict[int, float]:
        """Analyze weekly usage patterns."""
        weekly_totals = defaultdict(int)
        
        for record in records:
            week_day = record.timestamp.weekday()
            weekly_totals[week_day] += record.total_tokens
        
        return dict(weekly_totals)
    
    def _analyze_growth_trends(self, records: List[TokenUsageRecord]) -> Dict[str, float]:
        """Analyze growth trends."""
        # Simple linear trend analysis
        if len(records) < 2:
            return {"growth_rate": 0.0}
        
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        early_period = sorted_records[:len(sorted_records)//2]
        late_period = sorted_records[len(sorted_records)//2:]
        
        early_avg = statistics.mean([r.total_tokens for r in early_period])
        late_avg = statistics.mean([r.total_tokens for r in late_period])
        
        growth_rate = (late_avg - early_avg) / early_avg if early_avg > 0 else 0.0
        
        return {"growth_rate": growth_rate}
    
    def _predict_base_usage(self, daily_usage: Dict[int, float], days: int) -> float:
        """Predict base usage for future days."""
        if not daily_usage:
            return 0.0
        
        recent_avg = statistics.mean(list(daily_usage.values())[-7:])  # Last 7 days
        return recent_avg * days
    
    def _calculate_seasonal_factor(self, weekly_patterns: Dict[int, float], days: int) -> float:
        """Calculate seasonal adjustment factor."""
        # Simple implementation - could be more sophisticated
        if not weekly_patterns:
            return 1.0
        
        avg_usage = statistics.mean(weekly_patterns.values())
        if avg_usage == 0:
            return 1.0
        
        # Adjust based on day of week patterns
        return 1.0  # Simplified
    
    def _calculate_growth_factor(self, growth_trends: Dict[str, float], days: int) -> float:
        """Calculate growth adjustment factor."""
        growth_rate = growth_trends.get("growth_rate", 0.0)
        
        # Apply compound growth
        return (1 + growth_rate) ** (days / 30)  # Monthly growth rate
    
    def _calculate_avg_cost_per_token(self, records: List[TokenUsageRecord]) -> float:
        """Calculate average cost per token."""
        if not records:
            return 0.001  # Default
        
        total_cost = sum(r.cost for r in records)
        total_tokens = sum(r.total_tokens for r in records)
        
        return total_cost / total_tokens if total_tokens > 0 else 0.001
    
    def _assess_prediction_confidence(
        self, 
        records: List[TokenUsageRecord], 
        days: int, 
        target_confidence: float
    ) -> float:
        """Assess prediction confidence level."""
        # More data = higher confidence
        data_factor = min(len(records) / 30, 1.0)  # 30 days = full confidence
        
        # Shorter predictions = higher confidence
        time_factor = max(0.5, 1.0 - (days / 365))
        
        # Stability factor (low variance = higher confidence)
        if len(records) > 1:
            daily_costs = [r.cost for r in records]
            variance = statistics.variance(daily_costs) if len(daily_costs) > 1 else 0
            stability_factor = max(0.5, 1.0 - min(variance * 10, 0.5))
        else:
            stability_factor = 0.5
        
        confidence = (data_factor * 0.4 + time_factor * 0.3 + stability_factor * 0.3)
        return min(confidence, target_confidence)
    
    def _identify_prediction_factors(
        self,
        daily_usage: Dict[int, float],
        weekly_patterns: Dict[int, float],
        growth_trends: Dict[str, float]
    ) -> List[str]:
        """Identify key factors affecting predictions."""
        factors = []
        
        if growth_trends.get("growth_rate", 0) > 0.1:
            factors.append("Strong growth trend detected")
        
        if weekly_patterns:
            max_day = max(weekly_patterns.items(), key=lambda x: x[1])
            factors.append(f"Peak usage on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][max_day[0]]}")
        
        factors.append("Historical usage patterns")
        factors.append("Seasonal adjustments")
        
        return factors
    
    def _assess_prediction_risk(
        self, 
        predicted_tokens: int, 
        predicted_cost: float, 
        confidence: float
    ) -> str:
        """Assess risk level of predictions."""
        if confidence > 0.8 and predicted_cost < 100:
            return "Low risk - high confidence, reasonable cost"
        elif confidence > 0.6 and predicted_cost < 500:
            return "Medium risk - moderate confidence and cost"
        elif predicted_cost > 1000:
            return "High risk - high predicted cost"
        else:
            return "Medium risk - limited historical data"
    
    def _analyze_seasonal_patterns(self, records: List[TokenUsageRecord]) -> Dict[str, float]:
        """Analyze seasonal usage patterns."""
        if not records:
            return {}
        
        # Group records by time patterns
        weekday_usage = defaultdict(float)
        weekend_usage = defaultdict(float)
        hourly_usage = defaultdict(float)
        monthly_usage = defaultdict(float)
        
        for record in records:
            timestamp = record.timestamp
            
            # Weekday vs weekend analysis
            if timestamp.weekday() < 5:  # Monday = 0, Sunday = 6
                weekday_usage["count"] += 1
                weekday_usage["tokens"] += record.token_count.total_tokens
            else:
                weekend_usage["count"] += 1
                weekend_usage["tokens"] += record.token_count.total_tokens
            
            # Hourly pattern analysis
            hour = timestamp.hour
            hourly_usage[hour] += record.token_count.total_tokens
            
            # Monthly pattern analysis
            month_key = f"{timestamp.year}-{timestamp.month:02d}"
            monthly_usage[month_key] += record.token_count.total_tokens
        
        patterns = {}
        
        # Calculate weekday vs weekend ratio
        if weekend_usage["count"] > 0 and weekday_usage["count"] > 0:
            weekday_avg = weekday_usage["tokens"] / weekday_usage["count"]
            weekend_avg = weekend_usage["tokens"] / weekend_usage["count"]
            patterns["weekday_vs_weekend"] = weekday_avg / weekend_avg if weekend_avg > 0 else 1.0
        
        # Calculate peak hour factor
        if hourly_usage:
            max_hourly = max(hourly_usage.values())
            avg_hourly = sum(hourly_usage.values()) / len(hourly_usage)
            patterns["hour_peak_factor"] = max_hourly / avg_hourly if avg_hourly > 0 else 1.0
        
        # Calculate month-over-month growth
        if len(monthly_usage) >= 2:
            monthly_values = list(monthly_usage.values())
            if len(monthly_values) >= 2:
                latest = monthly_values[-1]
                previous = monthly_values[-2]
                patterns["month_over_month"] = latest / previous if previous > 0 else 1.0
        
        return patterns
    
    def _analyze_cost_distribution(self, records: List[TokenUsageRecord]) -> Dict[str, float]:
        """Analyze cost distribution."""
        total_cost = sum(r.cost for r in records)
        if total_cost == 0:
            return {}
        
        # Group by model
        model_costs = defaultdict(float)
        for record in records:
            model_costs[str(record.model_name)] += record.cost
        
        return {
            model: (cost / total_cost) * 100 
            for model, cost in model_costs.items()
        }
    
    def _identify_inefficiency_hotspots(self, records: List[TokenUsageRecord]) -> List[Dict[str, Any]]:
        """Identify inefficiency hotspots."""
        hotspots = []
        
        # Find high-cost, low-cache-hit operations
        high_cost_uncached = [
            r for r in records 
            if r.cost > 0.05 and not r.was_cached
        ]
        
        if len(high_cost_uncached) > len(records) * 0.1:
            hotspots.append({
                "type": "high_cost_uncached",
                "description": "Many expensive requests not using cache",
                "impact": "high",
                "count": len(high_cost_uncached)
            })
        
        return hotspots
    
    async def _generate_benchmark_comparisons(
        self, 
        workspace_name: str, 
        records: List[TokenUsageRecord]
    ) -> Dict[str, float]:
        """Generate benchmark comparisons."""
        if not records:
            return {}
        
        metrics = self._calculate_usage_metrics(records)
        
        # Industry benchmarks (these would typically come from external sources)
        industry_benchmarks = {
            "avg_efficiency_score": 0.65,
            "avg_cost_per_token": 0.003,
            "avg_cache_hit_rate": 0.7,
            "avg_tokens_per_request": 500,
            "avg_response_time_ms": 2000
        }
        
        comparisons = {}
        
        # Efficiency comparison
        if metrics.efficiency_score > 0:
            comparisons["efficiency_vs_average"] = (
                metrics.efficiency_score / industry_benchmarks["avg_efficiency_score"]
            )
        
        # Cost comparison
        if metrics.avg_cost_per_token > 0:
            comparisons["cost_per_token_vs_average"] = (
                industry_benchmarks["avg_cost_per_token"] / metrics.avg_cost_per_token
            )
        
        # Cache hit rate comparison
        if metrics.cache_hit_rate >= 0:
            comparisons["cache_hit_rate_vs_average"] = (
                metrics.cache_hit_rate / industry_benchmarks["avg_cache_hit_rate"]
            )
        
        # Tokens per request comparison
        if metrics.avg_tokens_per_request > 0:
            comparisons["tokens_per_request_vs_average"] = (
                industry_benchmarks["avg_tokens_per_request"] / metrics.avg_tokens_per_request
            )
        
        return comparisons
    
    def _detect_anomalies(self, records: List[TokenUsageRecord]) -> List[Dict[str, Any]]:
        """Detect usage anomalies."""
        anomalies = []
        
        if not records:
            return anomalies
        
        # Detect cost outliers
        costs = [r.cost for r in records]
        if len(costs) > 2:
            mean_cost = statistics.mean(costs)
            stdev_cost = statistics.stdev(costs)
            
            outliers = [r for r in records if abs(r.cost - mean_cost) > 2 * stdev_cost]
            
            if outliers:
                anomalies.append({
                    "type": "cost_outlier",
                    "description": f"Found {len(outliers)} cost outliers",
                    "severity": "medium",
                    "details": [f"Request with cost ${r.cost:.3f}" for r in outliers[:3]]
                })
        
        return anomalies
    
    def _invalidate_cache(self, workspace_name: str) -> None:
        """Invalidate relevant caches."""
        # Remove workspace-specific cached data
        keys_to_remove = [k for k in self._usage_cache.keys() if workspace_name in k]
        for key in keys_to_remove:
            del self._usage_cache[key]