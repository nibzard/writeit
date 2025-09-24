"""Mock workspace analytics service for testing."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from unittest.mock import AsyncMock

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.services.workspace_analytics_service import (
    WorkspaceAnalyticsService,
    WorkspaceAnalytics,
    UsageMetrics,
    PerformanceMetrics,
    ResourceMetrics,
    HealthDiagnostics,
    BehaviorMetrics,
    AnalyticsReport,
    AnalyticsScope,
    MetricType,
    HealthStatus
)


class MockWorkspaceAnalyticsService(WorkspaceAnalyticsService):
    """Mock implementation of WorkspaceAnalyticsService for testing."""
    
    def __init__(self):
        """Initialize mock service with test data."""
        # Don't call super().__init__ to avoid dependency injection
        self._analytics_data: Dict[WorkspaceName, WorkspaceAnalytics] = {}
        self._usage_events: Dict[WorkspaceName, List[Dict[str, Any]]] = defaultdict(list)
        self._workspace_rankings: List[Tuple[WorkspaceName, float]] = []
        
        # Mock state for testing
        self._should_fail_collection = False
        self._should_fail_health_check = False
        self._custom_health_status: Optional[HealthStatus] = None
        self._custom_metrics: Dict[str, Any] = {}
        
        # Setup default test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Setup default test data."""
        # Create sample analytics for default workspace
        default_name = WorkspaceName.from_user_input("default")
        
        usage_metrics = UsageMetrics(
            total_sessions=25,
            total_pipelines_run=150,
            total_templates_used=75,
            unique_templates={"blog-post", "documentation", "email"},
            average_session_duration=timedelta(minutes=45),
            last_active=datetime.now() - timedelta(hours=2),
            peak_usage_time="14:00",
            most_used_templates=[("blog-post", 50), ("documentation", 35), ("email", 20)],
            pipeline_success_rate=0.92,
            error_count=12,
            cache_hit_rate=0.78
        )
        
        performance_metrics = PerformanceMetrics(
            average_pipeline_duration=timedelta(seconds=45),
            average_step_duration=timedelta(seconds=8),
            slowest_pipelines=[("complex-analysis", timedelta(minutes=5))],
            fastest_pipelines=[("quick-note", timedelta(seconds=10))],
            llm_response_times=[2.5, 3.1, 1.8, 4.2],
            cache_performance={"hit_rate": 0.78, "miss_rate": 0.22},
            resource_efficiency=0.85,
            throughput_per_hour=12.5,
            concurrent_execution_avg=2.3
        )
        
        resource_metrics = ResourceMetrics(
            storage_usage_bytes=50 * 1024 * 1024,  # 50MB
            cache_size_bytes=10 * 1024 * 1024,    # 10MB
            template_count=15,
            pipeline_count=8,
            configuration_complexity=7,
            storage_growth_rate=1024 * 1024,      # 1MB per day
            storage_efficiency=0.88,
            cleanup_potential_bytes=5 * 1024 * 1024,  # 5MB
            backup_size_bytes=45 * 1024 * 1024        # 45MB
        )
        
        health_diagnostics = HealthDiagnostics(
            overall_status=HealthStatus.GOOD,
            issues=[],
            warnings=["Large cache size detected"],
            recommendations=["Consider cache cleanup", "Review template organization"],
            integrity_score=0.95,
            security_score=0.88,
            performance_score=0.92,
            maintainability_score=0.85,
            last_health_check=datetime.now() - timedelta(hours=1)
        )
        
        behavior_metrics = BehaviorMetrics(
            preferred_models=Counter({"gpt-4o-mini": 120, "claude-3-haiku": 30}),
            template_usage_patterns={
                "blog-post": [datetime.now() - timedelta(days=i) for i in range(5)],
                "documentation": [datetime.now() - timedelta(days=i*2) for i in range(3)]
            },
            configuration_changes=[
                (datetime.now() - timedelta(days=7), "max_tokens", 2000, 4000),
                (datetime.now() - timedelta(days=14), "default_model", "gpt-4o", "gpt-4o-mini")
            ],
            error_patterns=Counter({"template_validation": 8, "llm_timeout": 4}),
            session_patterns={"09": 5, "14": 12, "16": 8},
            workflow_efficiency=0.82,
            learning_curve_progress=0.75
        )
        
        analytics = WorkspaceAnalytics(
            workspace_name=default_name,
            collection_time=datetime.now(),
            time_range=(datetime.now() - timedelta(days=30), datetime.now()),
            usage=usage_metrics,
            performance=performance_metrics,
            resources=resource_metrics,
            health=health_diagnostics,
            behavior=behavior_metrics,
            comparative_rank=1,
            trends={
                "pipelines_per_day": [(datetime.now() - timedelta(days=i), 5.0 - i*0.1) for i in range(7)],
                "error_rate": [(datetime.now() - timedelta(days=i), 0.08 + i*0.01) for i in range(7)]
            }
        )
        
        self._analytics_data[default_name] = analytics
        
        # Setup workspace rankings
        self._workspace_rankings = [
            (WorkspaceName.from_user_input("default"), 0.92),
            (WorkspaceName.from_user_input("project1"), 0.85),
            (WorkspaceName.from_user_input("project2"), 0.78)
        ]
    
    # Mock control methods for testing
    
    def set_should_fail_collection(self, should_fail: bool):
        """Control whether analytics collection should fail."""
        self._should_fail_collection = should_fail
    
    def set_should_fail_health_check(self, should_fail: bool):
        """Control whether health check should fail."""
        self._should_fail_health_check = should_fail
    
    def set_custom_health_status(self, status: Optional[HealthStatus]):
        """Set custom health status for testing."""
        self._custom_health_status = status
    
    def set_custom_metric(self, metric_name: str, value: Any):
        """Set custom metric value for testing."""
        self._custom_metrics[metric_name] = value
    
    def add_usage_event(
        self,
        workspace_name: WorkspaceName,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Add usage event for testing."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": event_data
        }
        self._usage_events[workspace_name].append(event)
    
    def get_analytics_data(self, workspace_name: WorkspaceName) -> Optional[WorkspaceAnalytics]:
        """Get analytics data for testing."""
        return self._analytics_data.get(workspace_name)
    
    def set_analytics_data(self, workspace_name: WorkspaceName, analytics: WorkspaceAnalytics):
        """Set analytics data for testing."""
        self._analytics_data[workspace_name] = analytics
    
    # Implementation of WorkspaceAnalyticsService interface
    
    async def collect_workspace_analytics(
        self,
        workspace: Workspace,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        include_trends: bool = True
    ) -> WorkspaceAnalytics:
        """Collect comprehensive analytics for a workspace."""
        if self._should_fail_collection:
            raise Exception("Forced analytics collection failure for testing")
        
        # Return existing analytics if available
        if workspace.name in self._analytics_data:
            analytics = self._analytics_data[workspace.name]
            
            # Update collection time
            analytics.collection_time = datetime.now()
            
            # Update time range if provided
            if time_range:
                analytics.time_range = time_range
            
            # Apply custom metrics if set
            for metric_name, value in self._custom_metrics.items():
                if hasattr(analytics.usage, metric_name):
                    setattr(analytics.usage, metric_name, value)
                elif hasattr(analytics.performance, metric_name):
                    setattr(analytics.performance, metric_name, value)
                elif hasattr(analytics.resources, metric_name):
                    setattr(analytics.resources, metric_name, value)
            
            return analytics
        
        # Create new analytics for unknown workspace
        if time_range is None:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            time_range = (start_time, end_time)
        
        # Create minimal analytics
        usage_metrics = UsageMetrics(
            total_sessions=0,
            total_pipelines_run=0,
            total_templates_used=0,
            unique_templates=set(),
            pipeline_success_rate=1.0,
            error_count=0,
            cache_hit_rate=0.5
        )
        
        performance_metrics = PerformanceMetrics()
        resource_metrics = ResourceMetrics()
        
        health_diagnostics = HealthDiagnostics(
            overall_status=self._custom_health_status or HealthStatus.UNKNOWN,
            integrity_score=1.0,
            security_score=1.0,
            performance_score=1.0,
            maintainability_score=1.0,
            last_health_check=datetime.now()
        )
        
        behavior_metrics = BehaviorMetrics()
        
        analytics = WorkspaceAnalytics(
            workspace_name=workspace.name,
            collection_time=datetime.now(),
            time_range=time_range,
            usage=usage_metrics,
            performance=performance_metrics,
            resources=resource_metrics,
            health=health_diagnostics,
            behavior=behavior_metrics,
            trends={} if not include_trends else {
                "pipelines_per_day": [(datetime.now(), 0.0)]
            }
        )
        
        self._analytics_data[workspace.name] = analytics
        return analytics
    
    async def diagnose_workspace_health(
        self,
        workspace: Workspace,
        detailed: bool = True
    ) -> HealthDiagnostics:
        """Diagnose workspace health and identify issues."""
        if self._should_fail_health_check:
            raise Exception("Forced health check failure for testing")
        
        # Return custom health status if set
        if self._custom_health_status:
            status = self._custom_health_status
        else:
            status = HealthStatus.GOOD
        
        # Create health diagnostics
        diagnostics = HealthDiagnostics(
            overall_status=status,
            issues=[],
            warnings=[],
            recommendations=[],
            integrity_score=0.95,
            security_score=0.88,
            performance_score=0.92,
            maintainability_score=0.85,
            last_health_check=datetime.now()
        )
        
        # Add issues based on status
        if status == HealthStatus.CRITICAL:
            diagnostics.issues = ["Critical storage corruption detected", "Security vulnerabilities found"]
            diagnostics.integrity_score = 0.3
            diagnostics.security_score = 0.4
        elif status == HealthStatus.WARNING:
            diagnostics.warnings = ["High storage usage", "Performance degradation"]
            diagnostics.performance_score = 0.6
        elif status == HealthStatus.EXCELLENT:
            diagnostics.integrity_score = 1.0
            diagnostics.security_score = 1.0
            diagnostics.performance_score = 1.0
            diagnostics.maintainability_score = 1.0
        
        # Add recommendations if detailed
        if detailed:
            if status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                diagnostics.recommendations = [
                    "Review workspace configuration",
                    "Clean up old data",
                    "Update security settings"
                ]
        
        return diagnostics
    
    async def get_usage_trends(
        self,
        workspace: Workspace,
        days: int = 30,
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Get usage trends for workspace over time."""
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
        
        # Generate sample trend data
        for metric_type in metric_types:
            trend_data = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                
                # Generate trend values based on metric type
                if metric_type == "pipelines_per_day":
                    value = max(0, 5.0 - i * 0.1 + (i % 7) * 0.5)
                elif metric_type == "error_rate":
                    value = 0.05 + (i % 3) * 0.02
                elif metric_type == "cache_hit_rate":
                    value = 0.75 + (i % 5) * 0.05
                elif metric_type == "storage_size":
                    value = 50 * 1024 * 1024 + i * 1024 * 100  # Growing storage
                else:
                    value = float(i % 10)
                
                trend_data.append((date, value))
            
            trends[metric_type] = trend_data
        
        return trends
    
    async def compare_workspaces(
        self,
        workspaces: List[Workspace],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Dict[WorkspaceName, float]]:
        """Compare multiple workspaces across metrics."""
        if metrics is None:
            metrics = [
                "total_pipelines",
                "success_rate",
                "average_duration",
                "storage_efficiency",
                "health_score"
            ]
        
        comparison = {}
        
        for metric in metrics:
            comparison[metric] = {}
            
            for workspace in workspaces:
                # Get or create analytics for workspace
                analytics = await self.collect_workspace_analytics(workspace, include_trends=False)
                
                # Extract metric value
                if metric == "total_pipelines":
                    value = float(analytics.usage.total_pipelines_run)
                elif metric == "success_rate":
                    value = analytics.usage.pipeline_success_rate
                elif metric == "average_duration":
                    value = analytics.performance.average_pipeline_duration.total_seconds()
                elif metric == "storage_efficiency":
                    value = analytics.resources.storage_efficiency
                elif metric == "health_score":
                    value = (
                        analytics.health.integrity_score +
                        analytics.health.security_score +
                        analytics.health.performance_score +
                        analytics.health.maintainability_score
                    ) / 4
                else:
                    value = 0.5  # Default value
                
                comparison[metric][workspace.name] = value
        
        return comparison
    
    async def generate_analytics_report(
        self,
        workspace: Workspace,
        include_recommendations: bool = True
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report with insights."""
        # Collect analytics
        analytics = await self.collect_workspace_analytics(workspace, include_trends=True)
        
        # Generate insights
        insights = []
        if analytics.usage.total_pipelines_run > 100:
            insights.append("High workspace activity indicates good adoption")
        if analytics.usage.pipeline_success_rate > 0.9:
            insights.append("Excellent pipeline reliability")
        if analytics.health.overall_status == HealthStatus.EXCELLENT:
            insights.append("Workspace is in optimal condition")
        
        # Generate recommendations
        action_items = []
        optimization_opportunities = []
        risk_factors = []
        success_indicators = []
        
        if include_recommendations:
            if analytics.usage.error_count > 10:
                action_items.append("Investigate and fix recurring errors")
            
            if analytics.usage.cache_hit_rate < 0.5:
                optimization_opportunities.append("Improve caching configuration")
            
            if analytics.health.security_score < 0.8:
                risk_factors.append("Security vulnerabilities detected")
            
            if analytics.usage.pipeline_success_rate > 0.9:
                success_indicators.append("High reliability indicates good practices")
        
        return AnalyticsReport(
            workspace_analytics=analytics,
            insights=insights,
            action_items=action_items,
            optimization_opportunities=optimization_opportunities,
            risk_factors=risk_factors,
            success_indicators=success_indicators
        )
    
    async def track_usage_event(
        self,
        workspace: Workspace,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Track a usage event for analytics."""
        self.add_usage_event(workspace.name, event_type, event_data)
    
    async def get_workspace_rankings(
        self,
        metric: str = "overall_score",
        limit: int = 10
    ) -> List[Tuple[WorkspaceName, float]]:
        """Get workspace rankings by metric."""
        # Return predefined rankings for testing
        rankings = self._workspace_rankings.copy()
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings[:limit]
    
    async def cleanup_analytics_data(
        self,
        older_than_days: Optional[int] = None
    ) -> int:
        """Clean up old analytics data."""
        if older_than_days is None:
            older_than_days = 90
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # Clean up old usage events
        cleaned_count = 0
        for workspace_name in self._usage_events:
            events = self._usage_events[workspace_name]
            original_count = len(events)
            
            # Keep only recent events
            recent_events = [
                event for event in events
                if datetime.fromisoformat(event["timestamp"]) > cutoff_date
            ]
            
            self._usage_events[workspace_name] = recent_events
            cleaned_count += (original_count - len(recent_events))
        
        return cleaned_count
    
    # Additional helper methods for testing
    
    def clear_all_analytics_data(self):
        """Clear all analytics data for testing."""
        self._analytics_data.clear()
        self._usage_events.clear()
        self._workspace_rankings.clear()
    
    def get_usage_events(self, workspace_name: WorkspaceName) -> List[Dict[str, Any]]:
        """Get usage events for testing."""
        return self._usage_events[workspace_name].copy()
    
    def set_workspace_rankings(self, rankings: List[Tuple[WorkspaceName, float]]):
        """Set workspace rankings for testing."""
        self._workspace_rankings = rankings.copy()
    
    def reset_mock_state(self):
        """Reset mock state for testing."""
        self._should_fail_collection = False
        self._should_fail_health_check = False
        self._custom_health_status = None
        self._custom_metrics.clear()
        self.clear_all_analytics_data()
        self._setup_test_data()