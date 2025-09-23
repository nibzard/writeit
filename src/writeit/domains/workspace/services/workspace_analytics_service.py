"""Workspace analytics service.

Provides comprehensive usage tracking, performance monitoring,
resource utilization analysis, and health diagnostics for workspaces.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import defaultdict, Counter

from ....shared.repository import RepositoryError
from ..entities.workspace import Workspace
from ..entities.workspace_configuration import WorkspaceConfiguration
from ..value_objects.workspace_name import WorkspaceName
from ..repositories.workspace_repository import WorkspaceRepository
from ..repositories.workspace_config_repository import WorkspaceConfigRepository


class AnalyticsScope(str, Enum):
    """Analytics scope for data collection."""
    WORKSPACE = "workspace"      # Single workspace
    GLOBAL = "global"           # All workspaces
    COMPARATIVE = "comparative"  # Compare multiple workspaces


class MetricType(str, Enum):
    """Types of metrics collected."""
    USAGE = "usage"             # Usage patterns and frequency
    PERFORMANCE = "performance"  # Performance metrics
    RESOURCE = "resource"       # Resource utilization
    HEALTH = "health"          # Health and diagnostics
    BEHAVIOR = "behavior"      # User behavior patterns


class HealthStatus(str, Enum):
    """Workspace health status levels."""
    EXCELLENT = "excellent"     # No issues, optimal performance
    GOOD = "good"              # Minor issues, good performance
    WARNING = "warning"        # Some issues, degraded performance
    CRITICAL = "critical"      # Major issues, poor performance
    UNKNOWN = "unknown"        # Unable to determine status


@dataclass
class UsageMetrics:
    """Workspace usage metrics."""
    total_sessions: int = 0
    total_pipelines_run: int = 0
    total_templates_used: int = 0
    unique_templates: Set[str] = field(default_factory=set)
    average_session_duration: timedelta = timedelta()
    last_active: Optional[datetime] = None
    peak_usage_time: Optional[str] = None  # Hour of day
    most_used_templates: List[Tuple[str, int]] = field(default_factory=list)
    pipeline_success_rate: float = 0.0
    error_count: int = 0
    cache_hit_rate: float = 0.0


@dataclass
class PerformanceMetrics:
    """Workspace performance metrics."""
    average_pipeline_duration: timedelta = timedelta()
    average_step_duration: timedelta = timedelta()
    slowest_pipelines: List[Tuple[str, timedelta]] = field(default_factory=list)
    fastest_pipelines: List[Tuple[str, timedelta]] = field(default_factory=list)
    llm_response_times: List[float] = field(default_factory=list)
    cache_performance: Dict[str, float] = field(default_factory=dict)
    resource_efficiency: float = 0.0
    throughput_per_hour: float = 0.0
    concurrent_execution_avg: float = 0.0


@dataclass
class ResourceMetrics:
    """Workspace resource utilization metrics."""
    storage_usage_bytes: int = 0
    cache_size_bytes: int = 0
    template_count: int = 0
    pipeline_count: int = 0
    configuration_complexity: int = 0
    storage_growth_rate: float = 0.0  # bytes per day
    storage_efficiency: float = 0.0   # useful data / total data
    cleanup_potential_bytes: int = 0
    backup_size_bytes: int = 0


@dataclass
class HealthDiagnostics:
    """Workspace health diagnostics."""
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    integrity_score: float = 0.0  # 0.0 to 1.0
    security_score: float = 0.0   # 0.0 to 1.0
    performance_score: float = 0.0  # 0.0 to 1.0
    maintainability_score: float = 0.0  # 0.0 to 1.0
    last_health_check: Optional[datetime] = None


@dataclass
class BehaviorMetrics:
    """User behavior metrics."""
    preferred_models: Counter = field(default_factory=Counter)
    template_usage_patterns: Dict[str, List[datetime]] = field(default_factory=dict)
    configuration_changes: List[Tuple[datetime, str, Any, Any]] = field(default_factory=list)
    error_patterns: Counter = field(default_factory=Counter)
    session_patterns: Dict[str, int] = field(default_factory=dict)  # hour -> count
    workflow_efficiency: float = 0.0
    learning_curve_progress: float = 0.0


@dataclass
class WorkspaceAnalytics:
    """Complete workspace analytics data."""
    workspace_name: WorkspaceName
    collection_time: datetime
    time_range: Tuple[datetime, datetime]
    usage: UsageMetrics
    performance: PerformanceMetrics
    resources: ResourceMetrics
    health: HealthDiagnostics
    behavior: BehaviorMetrics
    comparative_rank: Optional[int] = None  # Rank among all workspaces
    trends: Dict[str, List[Tuple[datetime, float]]] = field(default_factory=dict)


@dataclass
class AnalyticsReport:
    """Analytics report with insights and recommendations."""
    workspace_analytics: WorkspaceAnalytics
    insights: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    success_indicators: List[str] = field(default_factory=list)
    report_generated_at: datetime = field(default_factory=datetime.now)


class WorkspaceAnalyticsService:
    """Service for workspace usage tracking and analytics.
    
    Provides comprehensive analytics including usage patterns, performance
    monitoring, resource utilization, health diagnostics, and behavioral analysis.
    
    Examples:
        service = WorkspaceAnalyticsService(workspace_repo, config_repo)
        
        # Collect analytics for workspace
        analytics = await service.collect_workspace_analytics(workspace)
        
        # Generate health report
        health = await service.diagnose_workspace_health(workspace)
        
        # Get usage trends
        trends = await service.get_usage_trends(workspace, days=30)
        
        # Compare workspaces
        comparison = await service.compare_workspaces([ws1, ws2, ws3])
    """
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        config_repository: WorkspaceConfigRepository
    ) -> None:
        """Initialize analytics service.
        
        Args:
            workspace_repository: Repository for workspace data
            config_repository: Repository for configuration data
        """
        self._workspace_repo = workspace_repository
        self._config_repo = config_repository
        self._metrics_cache = {}
        self._analytics_retention_days = 90
        self._health_check_interval = timedelta(hours=6)
        
        # Analytics collectors
        self._usage_collectors = []
        self._performance_collectors = []
        self._resource_collectors = []
        self._health_collectors = []
        self._behavior_collectors = []
    
    async def collect_workspace_analytics(
        self,
        workspace: Workspace,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        include_trends: bool = True
    ) -> WorkspaceAnalytics:
        """Collect comprehensive analytics for a workspace.
        
        Args:
            workspace: Workspace to analyze
            time_range: Optional time range for analysis
            include_trends: Whether to include trend analysis
            
        Returns:
            Complete workspace analytics
            
        Raises:
            RepositoryError: If data collection fails
        """
        if time_range is None:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            time_range = (start_time, end_time)
        
        # Collect all metric types
        usage_metrics = await self._collect_usage_metrics(workspace, time_range)
        performance_metrics = await self._collect_performance_metrics(workspace, time_range)
        resource_metrics = await self._collect_resource_metrics(workspace, time_range)
        health_diagnostics = await self._collect_health_diagnostics(workspace)
        behavior_metrics = await self._collect_behavior_metrics(workspace, time_range)
        
        # Calculate trends if requested
        trends = {}
        if include_trends:
            trends = await self._calculate_trends(workspace, time_range)
        
        # Get comparative ranking
        comparative_rank = await self._get_workspace_ranking(workspace)
        
        analytics = WorkspaceAnalytics(
            workspace_name=workspace.name,
            collection_time=datetime.now(),
            time_range=time_range,
            usage=usage_metrics,
            performance=performance_metrics,
            resources=resource_metrics,
            health=health_diagnostics,
            behavior=behavior_metrics,
            comparative_rank=comparative_rank,
            trends=trends
        )
        
        # Cache analytics
        self._metrics_cache[workspace.name] = analytics
        
        return analytics
    
    async def diagnose_workspace_health(
        self,
        workspace: Workspace,
        detailed: bool = True
    ) -> HealthDiagnostics:
        """Diagnose workspace health and identify issues.
        
        Args:
            workspace: Workspace to diagnose
            detailed: Whether to include detailed analysis
            
        Returns:
            Health diagnostics with issues and recommendations
            
        Raises:
            RepositoryError: If health check fails
        """
        diagnostics = HealthDiagnostics(last_health_check=datetime.now())
        
        # Check workspace integrity
        integrity_issues = await self._workspace_repo.validate_workspace_integrity(workspace)
        diagnostics.issues.extend(integrity_issues)
        diagnostics.integrity_score = max(0.0, 1.0 - len(integrity_issues) * 0.1)
        
        # Check configuration health
        config = await self._config_repo.find_by_workspace(workspace)
        if config:
            config_issues = await self._config_repo.validate_config(config)
            diagnostics.warnings.extend(config_issues)
        
        # Check storage health
        storage_issues = await self._check_storage_health(workspace)
        diagnostics.issues.extend(storage_issues)
        
        # Check performance health
        performance_issues = await self._check_performance_health(workspace)
        diagnostics.warnings.extend(performance_issues)
        
        # Check security
        security_score = await self._calculate_security_score(workspace)
        diagnostics.security_score = security_score
        
        # Check performance score
        performance_score = await self._calculate_performance_score(workspace)
        diagnostics.performance_score = performance_score
        
        # Check maintainability
        maintainability_score = await self._calculate_maintainability_score(workspace)
        diagnostics.maintainability_score = maintainability_score
        
        # Determine overall health status
        diagnostics.overall_status = await self._determine_health_status(diagnostics)
        
        # Generate recommendations if detailed
        if detailed:
            diagnostics.recommendations = await self._generate_health_recommendations(workspace, diagnostics)
        
        return diagnostics
    
    async def get_usage_trends(
        self,
        workspace: Workspace,
        days: int = 30,
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Get usage trends for workspace over time.
        
        Args:
            workspace: Workspace to analyze
            days: Number of days to analyze
            metric_types: Specific metrics to include
            
        Returns:
            Dictionary of metric trends over time
            
        Raises:
            RepositoryError: If trend analysis fails
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        if metric_types is None:
            metric_types = [
                "pipelines_per_day",
                "templates_used_per_day",
                "session_duration_avg",
                "error_rate",
                "cache_hit_rate",
                "storage_size"
            ]
        
        trends = {}
        
        # Calculate daily metrics
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            
            # Collect metrics for this day
            daily_metrics = await self._collect_daily_metrics(workspace, (day_start, day_end))
            
            for metric_type in metric_types:
                if metric_type not in trends:
                    trends[metric_type] = []
                
                value = daily_metrics.get(metric_type, 0.0)
                trends[metric_type].append((day_start, value))
            
            current_date += timedelta(days=1)
        
        return trends
    
    async def compare_workspaces(
        self,
        workspaces: List[Workspace],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Dict[WorkspaceName, float]]:
        """Compare multiple workspaces across metrics.
        
        Args:
            workspaces: Workspaces to compare
            metrics: Specific metrics to compare
            
        Returns:
            Comparison data with workspace rankings
            
        Raises:
            RepositoryError: If comparison analysis fails
        """
        if metrics is None:
            metrics = [
                "total_pipelines",
                "success_rate",
                "average_duration",
                "storage_efficiency",
                "health_score"
            ]
        
        comparison = {}
        
        # Collect analytics for each workspace
        workspace_analytics = {}
        for workspace in workspaces:
            analytics = await self.collect_workspace_analytics(workspace, include_trends=False)
            workspace_analytics[workspace.name] = analytics
        
        # Compare each metric
        for metric in metrics:
            comparison[metric] = {}
            
            for workspace_name, analytics in workspace_analytics.items():
                value = await self._extract_metric_value(analytics, metric)
                comparison[metric][workspace_name] = value
        
        return comparison
    
    async def generate_analytics_report(
        self,
        workspace: Workspace,
        include_recommendations: bool = True
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report with insights.
        
        Args:
            workspace: Workspace to analyze
            include_recommendations: Whether to include actionable recommendations
            
        Returns:
            Comprehensive analytics report
            
        Raises:
            RepositoryError: If report generation fails
        """
        # Collect comprehensive analytics
        analytics = await self.collect_workspace_analytics(workspace, include_trends=True)
        
        # Generate insights
        insights = await self._generate_insights(analytics)
        
        # Generate recommendations
        action_items = []
        optimization_opportunities = []
        risk_factors = []
        success_indicators = []
        
        if include_recommendations:
            action_items = await self._generate_action_items(analytics)
            optimization_opportunities = await self._identify_optimization_opportunities(analytics)
            risk_factors = await self._identify_risk_factors(analytics)
            success_indicators = await self._identify_success_indicators(analytics)
        
        report = AnalyticsReport(
            workspace_analytics=analytics,
            insights=insights,
            action_items=action_items,
            optimization_opportunities=optimization_opportunities,
            risk_factors=risk_factors,
            success_indicators=success_indicators
        )
        
        return report
    
    async def track_usage_event(
        self,
        workspace: Workspace,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Track a usage event for analytics.
        
        Args:
            workspace: Workspace where event occurred
            event_type: Type of event (e.g., "pipeline_run", "template_used")
            event_data: Event-specific data
            
        Raises:
            RepositoryError: If event tracking fails
        """
        # This would integrate with an event tracking system
        # For now, we'll store in workspace metadata
        event_record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": event_data
        }
        
        # Add to workspace metadata events list
        events_key = "analytics_events"
        current_events = workspace.metadata.get(events_key, [])
        current_events.append(event_record)
        
        # Keep only recent events (last 1000)
        if len(current_events) > 1000:
            current_events = current_events[-1000:]
        
        updated_workspace = workspace.set_metadata(events_key, current_events)
        await self._workspace_repo.update(updated_workspace)
    
    async def get_workspace_rankings(
        self,
        metric: str = "overall_score",
        limit: int = 10
    ) -> List[Tuple[WorkspaceName, float]]:
        """Get workspace rankings by metric.
        
        Args:
            metric: Metric to rank by
            limit: Maximum number of results
            
        Returns:
            List of (workspace_name, metric_value) tuples
            
        Raises:
            RepositoryError: If ranking calculation fails
        """
        all_workspaces = await self._workspace_repo.find_all()
        workspace_scores = []
        
        for workspace in all_workspaces:
            try:
                if metric == "overall_score":
                    score = await self._calculate_overall_score(workspace)
                else:
                    analytics = await self.collect_workspace_analytics(workspace, include_trends=False)
                    score = await self._extract_metric_value(analytics, metric)
                
                workspace_scores.append((workspace.name, score))
            except Exception:
                # Skip workspaces with errors
                continue
        
        # Sort by score (descending)
        workspace_scores.sort(key=lambda x: x[1], reverse=True)
        
        return workspace_scores[:limit]
    
    async def cleanup_analytics_data(
        self,
        older_than_days: Optional[int] = None
    ) -> int:
        """Clean up old analytics data.
        
        Args:
            older_than_days: Clean data older than this many days
            
        Returns:
            Number of records cleaned up
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        if older_than_days is None:
            older_than_days = self._analytics_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # Clean up cached metrics
        cleaned_count = 0
        for workspace_name in list(self._metrics_cache.keys()):
            cached_analytics = self._metrics_cache[workspace_name]
            if cached_analytics.collection_time < cutoff_date:
                del self._metrics_cache[workspace_name]
                cleaned_count += 1
        
        # Clean up workspace event metadata
        all_workspaces = await self._workspace_repo.find_all()
        for workspace in all_workspaces:
            events = workspace.metadata.get("analytics_events", [])
            if events:
                original_count = len(events)
                # Keep only events newer than cutoff
                recent_events = [
                    event for event in events
                    if datetime.fromisoformat(event["timestamp"]) > cutoff_date
                ]
                
                if len(recent_events) < original_count:
                    updated_workspace = workspace.set_metadata("analytics_events", recent_events)
                    await self._workspace_repo.update(updated_workspace)
                    cleaned_count += (original_count - len(recent_events))
        
        return cleaned_count
    
    # Private helper methods
    
    async def _collect_usage_metrics(
        self,
        workspace: Workspace,
        time_range: Tuple[datetime, datetime]
    ) -> UsageMetrics:
        """Collect usage metrics for workspace."""
        metrics = UsageMetrics()
        
        # Get events from workspace metadata
        events = workspace.metadata.get("analytics_events", [])
        
        # Filter events by time range
        start_time, end_time = time_range
        relevant_events = [
            event for event in events
            if start_time <= datetime.fromisoformat(event["timestamp"]) <= end_time
        ]
        
        # Calculate metrics from events
        pipeline_events = [e for e in relevant_events if e["event_type"] == "pipeline_run"]
        template_events = [e for e in relevant_events if e["event_type"] == "template_used"]
        session_events = [e for e in relevant_events if e["event_type"] == "session"]
        
        metrics.total_pipelines_run = len(pipeline_events)
        metrics.total_templates_used = len(template_events)
        metrics.total_sessions = len(session_events)
        
        # Calculate unique templates
        metrics.unique_templates = set(
            event["data"].get("template_name", "unknown")
            for event in template_events
        )
        
        # Calculate success rate
        successful_pipelines = len([
            e for e in pipeline_events
            if e["data"].get("status") == "success"
        ])
        if pipeline_events:
            metrics.pipeline_success_rate = successful_pipelines / len(pipeline_events)
        
        # Calculate error count
        metrics.error_count = len([
            e for e in relevant_events
            if e["event_type"] == "error"
        ])
        
        # Set last active time
        if relevant_events:
            latest_event = max(relevant_events, key=lambda e: e["timestamp"])
            metrics.last_active = datetime.fromisoformat(latest_event["timestamp"])
        
        return metrics
    
    async def _collect_performance_metrics(
        self,
        workspace: Workspace,
        time_range: Tuple[datetime, datetime]
    ) -> PerformanceMetrics:
        """Collect performance metrics for workspace."""
        metrics = PerformanceMetrics()
        
        # Get pipeline execution events
        events = workspace.metadata.get("analytics_events", [])
        pipeline_events = [
            e for e in events
            if e["event_type"] == "pipeline_run" and "duration" in e["data"]
        ]
        
        if pipeline_events:
            durations = [e["data"]["duration"] for e in pipeline_events]
            metrics.average_pipeline_duration = timedelta(seconds=sum(durations) / len(durations))
            
            # Find slowest and fastest pipelines
            pipeline_durations = [
                (e["data"].get("pipeline_name", "unknown"), timedelta(seconds=e["data"]["duration"]))
                for e in pipeline_events
            ]
            pipeline_durations.sort(key=lambda x: x[1], reverse=True)
            
            metrics.slowest_pipelines = pipeline_durations[:5]
            metrics.fastest_pipelines = pipeline_durations[-5:]
        
        return metrics
    
    async def _collect_resource_metrics(
        self,
        workspace: Workspace,
        time_range: Tuple[datetime, datetime]
    ) -> ResourceMetrics:
        """Collect resource utilization metrics for workspace."""
        metrics = ResourceMetrics()
        
        # Calculate current storage usage
        metrics.storage_usage_bytes = workspace.get_size_on_disk()
        
        # Count templates and pipelines
        templates_path = workspace.get_templates_path()
        if templates_path.exists():
            metrics.template_count = len(list(templates_path.value.glob("*.yaml")))
        
        pipelines_path = workspace.get_pipelines_path()
        if pipelines_path.exists():
            metrics.pipeline_count = len(list(pipelines_path.value.glob("*.yaml")))
        
        # Calculate cache size
        cache_path = workspace.get_cache_path()
        if cache_path.exists():
            cache_size = 0
            for file_path in cache_path.value.rglob("*"):
                if file_path.is_file():
                    cache_size += file_path.stat().st_size
            metrics.cache_size_bytes = cache_size
        
        return metrics
    
    async def _collect_health_diagnostics(self, workspace: Workspace) -> HealthDiagnostics:
        """Collect health diagnostics for workspace."""
        return await self.diagnose_workspace_health(workspace, detailed=False)
    
    async def _collect_behavior_metrics(
        self,
        workspace: Workspace,
        time_range: Tuple[datetime, datetime]
    ) -> BehaviorMetrics:
        """Collect user behavior metrics for workspace."""
        metrics = BehaviorMetrics()
        
        # Get events from workspace metadata
        events = workspace.metadata.get("analytics_events", [])
        
        # Filter by time range
        start_time, end_time = time_range
        relevant_events = [
            event for event in events
            if start_time <= datetime.fromisoformat(event["timestamp"]) <= end_time
        ]
        
        # Analyze model preferences
        llm_events = [e for e in relevant_events if e["event_type"] == "llm_request"]
        for event in llm_events:
            model = event["data"].get("model", "unknown")
            metrics.preferred_models[model] += 1
        
        # Analyze template usage patterns
        template_events = [e for e in relevant_events if e["event_type"] == "template_used"]
        for event in template_events:
            template_name = event["data"].get("template_name", "unknown")
            timestamp = datetime.fromisoformat(event["timestamp"])
            
            if template_name not in metrics.template_usage_patterns:
                metrics.template_usage_patterns[template_name] = []
            metrics.template_usage_patterns[template_name].append(timestamp)
        
        return metrics
    
    async def _calculate_trends(
        self,
        workspace: Workspace,
        time_range: Tuple[datetime, datetime]
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Calculate trend data for workspace metrics."""
        return await self.get_usage_trends(workspace, days=30)
    
    async def _get_workspace_ranking(self, workspace: Workspace) -> int:
        """Get workspace ranking among all workspaces."""
        rankings = await self.get_workspace_rankings()
        for rank, (workspace_name, _) in enumerate(rankings, 1):
            if workspace_name == workspace.name:
                return rank
        return len(rankings) + 1  # Not in top rankings
    
    async def _check_storage_health(self, workspace: Workspace) -> List[str]:
        """Check storage health and identify issues."""
        issues = []
        
        storage_size = workspace.get_size_on_disk()
        if storage_size > 1024 * 1024 * 1024:  # 1GB
            issues.append("Workspace storage size is very large (>1GB)")
        
        # Check for empty directories
        required_dirs = [
            workspace.get_templates_path(),
            workspace.get_storage_path(),
            workspace.get_cache_path()
        ]
        
        for dir_path in required_dirs:
            if dir_path.exists() and not any(dir_path.value.iterdir()):
                issues.append(f"Empty directory: {dir_path.value.name}")
        
        return issues
    
    async def _check_performance_health(self, workspace: Workspace) -> List[str]:
        """Check performance health and identify issues."""
        issues = []
        
        # Check for recent errors
        events = workspace.metadata.get("analytics_events", [])
        recent_errors = [
            e for e in events[-100:]  # Last 100 events
            if e["event_type"] == "error"
        ]
        
        if len(recent_errors) > 10:
            issues.append(f"High error rate: {len(recent_errors)} errors in recent activity")
        
        return issues
    
    async def _calculate_security_score(self, workspace: Workspace) -> float:
        """Calculate security score for workspace."""
        score = 1.0
        
        # Check directory permissions
        try:
            import stat
            mode = workspace.root_path.value.stat().st_mode
            if stat.S_IMODE(mode) & 0o077:  # World/group writable
                score -= 0.3
        except (OSError, AttributeError):
            score -= 0.1
        
        # Check for sensitive data in configuration
        config = await self._config_repo.find_by_workspace(workspace)
        if config:
            sensitive_patterns = ["password", "token", "key", "secret"]
            config_data = config.to_dict()
            for key, value in config_data.items():
                if any(pattern in key.lower() for pattern in sensitive_patterns):
                    if isinstance(value, str) and len(value) > 10:
                        score -= 0.2  # Potential exposed credential
        
        return max(0.0, score)
    
    async def _calculate_performance_score(self, workspace: Workspace) -> float:
        """Calculate performance score for workspace."""
        score = 1.0
        
        # Check recent pipeline success rate
        events = workspace.metadata.get("analytics_events", [])
        recent_pipelines = [
            e for e in events[-50:]  # Last 50 pipeline runs
            if e["event_type"] == "pipeline_run"
        ]
        
        if recent_pipelines:
            successful = len([e for e in recent_pipelines if e["data"].get("status") == "success"])
            success_rate = successful / len(recent_pipelines)
            score = success_rate
        
        return score
    
    async def _calculate_maintainability_score(self, workspace: Workspace) -> float:
        """Calculate maintainability score for workspace."""
        score = 1.0
        
        # Check template organization
        templates_path = workspace.get_templates_path()
        if templates_path.exists():
            template_files = list(templates_path.value.glob("*.yaml"))
            if len(template_files) > 20:
                score -= 0.2  # Too many templates might be hard to maintain
        
        # Check configuration complexity
        config = await self._config_repo.find_by_workspace(workspace)
        if config:
            non_default_count = len(config.get_non_default_values())
            if non_default_count > 15:
                score -= 0.1  # Complex configuration
        
        return max(0.0, score)
    
    async def _determine_health_status(self, diagnostics: HealthDiagnostics) -> HealthStatus:
        """Determine overall health status from diagnostics."""
        if diagnostics.issues:
            if len(diagnostics.issues) > 5:
                return HealthStatus.CRITICAL
            else:
                return HealthStatus.WARNING
        elif diagnostics.warnings:
            if len(diagnostics.warnings) > 3:
                return HealthStatus.WARNING
            else:
                return HealthStatus.GOOD
        else:
            # Check scores
            avg_score = (
                diagnostics.integrity_score +
                diagnostics.security_score +
                diagnostics.performance_score +
                diagnostics.maintainability_score
            ) / 4
            
            if avg_score >= 0.9:
                return HealthStatus.EXCELLENT
            elif avg_score >= 0.7:
                return HealthStatus.GOOD
            else:
                return HealthStatus.WARNING
    
    async def _generate_health_recommendations(
        self,
        workspace: Workspace,
        diagnostics: HealthDiagnostics
    ) -> List[str]:
        """Generate health recommendations based on diagnostics."""
        recommendations = []
        
        # Address issues
        if diagnostics.issues:
            recommendations.append("Address critical issues to improve workspace health")
        
        # Performance recommendations
        if diagnostics.performance_score < 0.7:
            recommendations.append("Review failed pipelines and optimize templates")
        
        # Security recommendations
        if diagnostics.security_score < 0.8:
            recommendations.append("Review workspace permissions and configuration security")
        
        # Storage recommendations
        storage_size = workspace.get_size_on_disk()
        if storage_size > 500 * 1024 * 1024:  # 500MB
            recommendations.append("Consider cleaning up old data to reduce storage usage")
        
        return recommendations
    
    async def _collect_daily_metrics(
        self,
        workspace: Workspace,
        day_range: Tuple[datetime, datetime]
    ) -> Dict[str, float]:
        """Collect metrics for a specific day."""
        events = workspace.metadata.get("analytics_events", [])
        
        # Filter events for the day
        start_time, end_time = day_range
        day_events = [
            event for event in events
            if start_time <= datetime.fromisoformat(event["timestamp"]) <= end_time
        ]
        
        metrics = {}
        
        # Count pipelines run
        pipeline_events = [e for e in day_events if e["event_type"] == "pipeline_run"]
        metrics["pipelines_per_day"] = len(pipeline_events)
        
        # Count templates used
        template_events = [e for e in day_events if e["event_type"] == "template_used"]
        metrics["templates_used_per_day"] = len(template_events)
        
        # Calculate error rate
        error_events = [e for e in day_events if e["event_type"] == "error"]
        total_events = len(day_events)
        metrics["error_rate"] = len(error_events) / max(1, total_events)
        
        # Calculate average session duration
        session_events = [e for e in day_events if e["event_type"] == "session"]
        if session_events:
            durations = [e["data"].get("duration", 0) for e in session_events]
            metrics["session_duration_avg"] = sum(durations) / len(durations)
        else:
            metrics["session_duration_avg"] = 0.0
        
        # Storage size (current)
        metrics["storage_size"] = workspace.get_size_on_disk()
        
        return metrics
    
    async def _extract_metric_value(self, analytics: WorkspaceAnalytics, metric: str) -> float:
        """Extract specific metric value from analytics."""
        if metric == "total_pipelines":
            return float(analytics.usage.total_pipelines_run)
        elif metric == "success_rate":
            return analytics.usage.pipeline_success_rate
        elif metric == "storage_efficiency":
            return analytics.resources.storage_efficiency
        elif metric == "health_score":
            return (
                analytics.health.integrity_score +
                analytics.health.security_score +
                analytics.health.performance_score +
                analytics.health.maintainability_score
            ) / 4
        else:
            return 0.0
    
    async def _calculate_overall_score(self, workspace: Workspace) -> float:
        """Calculate overall workspace score."""
        analytics = await self.collect_workspace_analytics(workspace, include_trends=False)
        return await self._extract_metric_value(analytics, "health_score")
    
    async def _generate_insights(self, analytics: WorkspaceAnalytics) -> List[str]:
        """Generate insights from analytics data."""
        insights = []
        
        # Usage insights
        if analytics.usage.total_pipelines_run > 100:
            insights.append("High workspace activity - this is a well-utilized workspace")
        elif analytics.usage.total_pipelines_run < 10:
            insights.append("Low activity detected - consider workspace optimization or training")
        
        # Performance insights
        if analytics.usage.pipeline_success_rate > 0.9:
            insights.append("Excellent pipeline reliability - maintain current practices")
        elif analytics.usage.pipeline_success_rate < 0.7:
            insights.append("Pipeline reliability issues detected - review error patterns")
        
        # Health insights
        if analytics.health.overall_status == HealthStatus.EXCELLENT:
            insights.append("Workspace is in excellent health")
        elif analytics.health.overall_status == HealthStatus.CRITICAL:
            insights.append("Critical health issues require immediate attention")
        
        return insights
    
    async def _generate_action_items(self, analytics: WorkspaceAnalytics) -> List[str]:
        """Generate actionable items from analytics."""
        actions = []
        
        if analytics.health.issues:
            actions.append("Resolve workspace integrity issues")
        
        if analytics.usage.error_count > 10:
            actions.append("Investigate and fix recurring errors")
        
        if analytics.resources.storage_usage_bytes > 1024 * 1024 * 1024:
            actions.append("Clean up large files to reduce storage usage")
        
        return actions
    
    async def _identify_optimization_opportunities(self, analytics: WorkspaceAnalytics) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        if analytics.usage.cache_hit_rate < 0.5:
            opportunities.append("Improve cache configuration to reduce LLM API calls")
        
        if analytics.performance.average_pipeline_duration.total_seconds() > 300:
            opportunities.append("Optimize slow-running pipelines for better performance")
        
        return opportunities
    
    async def _identify_risk_factors(self, analytics: WorkspaceAnalytics) -> List[str]:
        """Identify risk factors."""
        risks = []
        
        if analytics.health.security_score < 0.7:
            risks.append("Security vulnerabilities detected")
        
        if analytics.usage.pipeline_success_rate < 0.8:
            risks.append("Low pipeline success rate may impact productivity")
        
        return risks
    
    async def _identify_success_indicators(self, analytics: WorkspaceAnalytics) -> List[str]:
        """Identify success indicators."""
        indicators = []
        
        if analytics.usage.pipeline_success_rate > 0.9:
            indicators.append("High pipeline success rate indicates good template quality")
        
        if analytics.health.overall_status in [HealthStatus.EXCELLENT, HealthStatus.GOOD]:
            indicators.append("Good workspace health indicates effective management")
        
        return indicators