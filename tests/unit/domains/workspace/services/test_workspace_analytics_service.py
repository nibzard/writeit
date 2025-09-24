"""Unit tests for WorkspaceAnalyticsService.

Tests comprehensive analytics including usage tracking, performance monitoring,
resource utilization analysis, and health diagnostics for workspaces.
"""

import pytest
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from collections import Counter

from writeit.domains.workspace.services.workspace_analytics_service import (
    WorkspaceAnalyticsService,
    AnalyticsScope,
    MetricType,
    HealthStatus,
    UsageMetrics,
    PerformanceMetrics,
    ResourceMetrics,
    HealthDiagnostics,
    BehaviorMetrics,
    WorkspaceAnalytics,
    AnalyticsReport
)
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath


class TestWorkspaceAnalyticsService:
    """Test WorkspaceAnalyticsService core functionality."""
    
    def test_create_service(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test creating analytics service."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        assert service._workspace_repo == mock_workspace_repository
        assert service._config_repo == mock_workspace_config_repository
        assert service._analytics_retention_days == 90
        assert service._health_check_interval == timedelta(hours=6)
        assert isinstance(service._metrics_cache, dict)
    
    @pytest.mark.asyncio
    async def test_collect_workspace_analytics(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test collecting comprehensive workspace analytics."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create mock workspace with analytics events
        workspace = Mock()
        workspace.name = WorkspaceName("test-workspace")
        workspace.metadata = {
            "analytics_events": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "pipeline_run",
                    "data": {"status": "success", "duration": 30}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "template_used",
                    "data": {"template_name": "test-template"}
                }
            ]
        }
        workspace.get_size_on_disk.return_value = 1024 * 1024  # 1MB
        workspace.get_templates_path.return_value = Mock()
        workspace.get_pipelines_path.return_value = Mock()
        workspace.get_cache_path.return_value = Mock()
        workspace.root_path = Mock()
        
        # Mock repository methods
        mock_workspace_repository.validate_workspace_integrity = AsyncMock(return_value=[])
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        mock_workspace_repository.find_all = AsyncMock(return_value=[workspace])
        
        with patch.object(service, '_calculate_security_score', return_value=0.9), \
             patch.object(service, '_calculate_performance_score', return_value=0.8), \
             patch.object(service, '_calculate_maintainability_score', return_value=0.85):
            
            analytics = await service.collect_workspace_analytics(workspace)
            
            assert isinstance(analytics, WorkspaceAnalytics)
            assert analytics.workspace_name == workspace.name
            assert isinstance(analytics.collection_time, datetime)
            assert isinstance(analytics.usage, UsageMetrics)
            assert isinstance(analytics.performance, PerformanceMetrics)
            assert isinstance(analytics.resources, ResourceMetrics)
            assert isinstance(analytics.health, HealthDiagnostics)
            assert isinstance(analytics.behavior, BehaviorMetrics)
    
    @pytest.mark.asyncio
    async def test_diagnose_workspace_health_excellent(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test workspace health diagnosis with excellent health."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        workspace = Mock()
        workspace.name = WorkspaceName("healthy-workspace")
        workspace.metadata = {"analytics_events": []}
        workspace.root_path = Mock()
        
        # Mock all health checks to return good results
        mock_workspace_repository.validate_workspace_integrity = AsyncMock(return_value=[])
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        mock_workspace_config_repository.validate_config = AsyncMock(return_value=[])
        
        with patch.object(service, '_check_storage_health', return_value=[]), \
             patch.object(service, '_check_performance_health', return_value=[]), \
             patch.object(service, '_calculate_security_score', return_value=1.0), \
             patch.object(service, '_calculate_performance_score', return_value=1.0), \
             patch.object(service, '_calculate_maintainability_score', return_value=1.0):
            
            health = await service.diagnose_workspace_health(workspace)
            
            assert isinstance(health, HealthDiagnostics)
            assert health.overall_status == HealthStatus.EXCELLENT
            assert health.integrity_score == 1.0
            assert health.security_score == 1.0
            assert health.performance_score == 1.0
            assert health.maintainability_score == 1.0
            assert isinstance(health.last_health_check, datetime)
    
    @pytest.mark.asyncio
    async def test_diagnose_workspace_health_critical(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test workspace health diagnosis with critical issues."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        workspace = Mock()
        workspace.name = WorkspaceName("unhealthy-workspace")
        workspace.metadata = {"analytics_events": []}
        workspace.root_path = Mock()
        
        # Mock health checks to return many issues
        critical_issues = [
            "Directory structure corrupted",
            "Missing required files",
            "Permission errors",
            "Storage corruption",
            "Configuration invalid",
            "Security vulnerabilities"
        ]
        
        mock_workspace_repository.validate_workspace_integrity = AsyncMock(return_value=critical_issues)
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        
        with patch.object(service, '_check_storage_health', return_value=["Storage issues"]), \
             patch.object(service, '_check_performance_health', return_value=["Performance issues"]), \
             patch.object(service, '_calculate_security_score', return_value=0.3), \
             patch.object(service, '_calculate_performance_score', return_value=0.2), \
             patch.object(service, '_calculate_maintainability_score', return_value=0.1):
            
            health = await service.diagnose_workspace_health(workspace)
            
            assert health.overall_status == HealthStatus.CRITICAL
            assert len(health.issues) >= 6
            assert health.integrity_score < 0.5
            assert health.security_score == 0.3
            assert health.performance_score == 0.2
            assert health.maintainability_score == 0.1
    
    @pytest.mark.asyncio
    async def test_get_usage_trends(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test getting usage trends over time."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create workspace with events spread over time
        base_time = datetime.now() - timedelta(days=5)
        events = []
        for i in range(5):
            day_time = base_time + timedelta(days=i)
            events.extend([
                {
                    "timestamp": day_time.isoformat(),
                    "event_type": "pipeline_run",
                    "data": {"status": "success", "duration": 30}
                },
                {
                    "timestamp": day_time.isoformat(),
                    "event_type": "template_used",
                    "data": {"template_name": f"template-{i}"}
                }
            ])
        
        workspace = Mock()
        workspace.name = WorkspaceName("trending-workspace")
        workspace.metadata = {"analytics_events": events}
        workspace.get_size_on_disk.return_value = 1024 * 1024
        
        trends = await service.get_usage_trends(workspace, days=7)
        
        assert isinstance(trends, dict)
        assert "pipelines_per_day" in trends
        assert "templates_used_per_day" in trends
        assert "session_duration_avg" in trends
        assert "error_rate" in trends
        assert "storage_size" in trends
        
        # Each trend should have data points
        for metric_name, trend_data in trends.items():
            assert isinstance(trend_data, list)
            assert len(trend_data) == 8  # 7 days + 1
            for timestamp, value in trend_data:
                assert isinstance(timestamp, datetime)
                assert isinstance(value, (int, float))
    
    @pytest.mark.asyncio
    async def test_compare_workspaces(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test comparing multiple workspaces."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create mock workspaces with different characteristics
        workspace1 = Mock()
        workspace1.name = WorkspaceName("workspace-1")
        workspace1.metadata = {
            "analytics_events": [
                {"timestamp": datetime.now().isoformat(), "event_type": "pipeline_run", "data": {"status": "success"}}
            ] * 10
        }
        
        workspace2 = Mock()
        workspace2.name = WorkspaceName("workspace-2") 
        workspace2.metadata = {
            "analytics_events": [
                {"timestamp": datetime.now().isoformat(), "event_type": "pipeline_run", "data": {"status": "success"}}
            ] * 20
        }
        
        workspaces = [workspace1, workspace2]
        
        # Mock the analytics collection
        with patch.object(service, 'collect_workspace_analytics') as mock_collect:
            mock_collect.side_effect = [
                WorkspaceAnalytics(
                    workspace_name=workspace1.name,
                    collection_time=datetime.now(),
                    time_range=(datetime.now() - timedelta(days=30), datetime.now()),
                    usage=UsageMetrics(total_pipelines_run=10, pipeline_success_rate=0.9),
                    performance=PerformanceMetrics(),
                    resources=ResourceMetrics(storage_efficiency=0.8),
                    health=HealthDiagnostics(integrity_score=0.9, security_score=0.9, performance_score=0.9, maintainability_score=0.9),
                    behavior=BehaviorMetrics()
                ),
                WorkspaceAnalytics(
                    workspace_name=workspace2.name,
                    collection_time=datetime.now(),
                    time_range=(datetime.now() - timedelta(days=30), datetime.now()),
                    usage=UsageMetrics(total_pipelines_run=20, pipeline_success_rate=0.95),
                    performance=PerformanceMetrics(),
                    resources=ResourceMetrics(storage_efficiency=0.85),
                    health=HealthDiagnostics(integrity_score=0.95, security_score=0.95, performance_score=0.95, maintainability_score=0.95),
                    behavior=BehaviorMetrics()
                )
            ]
            
            comparison = await service.compare_workspaces(workspaces)
            
            assert isinstance(comparison, dict)
            assert "total_pipelines" in comparison
            assert "success_rate" in comparison
            assert "storage_efficiency" in comparison
            assert "health_score" in comparison
            
            # Check that workspace2 has higher values
            assert comparison["total_pipelines"][workspace2.name] > comparison["total_pipelines"][workspace1.name]
            assert comparison["success_rate"][workspace2.name] > comparison["success_rate"][workspace1.name]
    
    @pytest.mark.asyncio
    async def test_generate_analytics_report(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test generating comprehensive analytics report."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        workspace = Mock()
        workspace.name = WorkspaceName("report-workspace")
        workspace.metadata = {
            "analytics_events": [
                {"timestamp": datetime.now().isoformat(), "event_type": "pipeline_run", "data": {"status": "success"}}
            ] * 50
        }
        
        # Mock analytics collection
        with patch.object(service, 'collect_workspace_analytics') as mock_collect:
            mock_analytics = WorkspaceAnalytics(
                workspace_name=workspace.name,
                collection_time=datetime.now(),
                time_range=(datetime.now() - timedelta(days=30), datetime.now()),
                usage=UsageMetrics(total_pipelines_run=50, pipeline_success_rate=0.92),
                performance=PerformanceMetrics(),
                resources=ResourceMetrics(storage_usage_bytes=2*1024*1024*1024),  # 2GB
                health=HealthDiagnostics(overall_status=HealthStatus.GOOD, issues=[], warnings=["Minor warning"]),
                behavior=BehaviorMetrics()
            )
            mock_collect.return_value = mock_analytics
            
            report = await service.generate_analytics_report(workspace, include_recommendations=True)
            
            assert isinstance(report, AnalyticsReport)
            assert report.workspace_analytics == mock_analytics
            assert isinstance(report.insights, list)
            assert isinstance(report.action_items, list)
            assert isinstance(report.optimization_opportunities, list)
            assert isinstance(report.risk_factors, list)
            assert isinstance(report.success_indicators, list)
            assert isinstance(report.report_generated_at, datetime)
            
            # Should have some insights for high-activity workspace
            assert len(report.insights) > 0
            assert len(report.action_items) > 0  # Should suggest storage cleanup
    
    @pytest.mark.asyncio
    async def test_track_usage_event(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test tracking usage events."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        workspace = Mock()
        workspace.name = WorkspaceName("tracked-workspace")
        workspace.metadata = {"analytics_events": []}
        workspace.set_metadata = Mock(return_value=workspace)
        
        mock_workspace_repository.update = AsyncMock(return_value=workspace)
        
        event_data = {
            "pipeline_name": "test-pipeline",
            "status": "success",
            "duration": 45
        }
        
        await service.track_usage_event(workspace, "pipeline_run", event_data)
        
        # Verify event was added to metadata
        workspace.set_metadata.assert_called_once()
        args = workspace.set_metadata.call_args[0]
        assert args[0] == "analytics_events"
        assert len(args[1]) == 1
        
        event = args[1][0]
        assert event["event_type"] == "pipeline_run"
        assert event["data"] == event_data
        assert "timestamp" in event
        
        mock_workspace_repository.update.assert_called_once_with(workspace)
    
    @pytest.mark.asyncio
    async def test_get_workspace_rankings(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test getting workspace rankings."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create mock workspaces with different scores
        workspace1 = Mock()
        workspace1.name = WorkspaceName("high-score")
        workspace2 = Mock()
        workspace2.name = WorkspaceName("medium-score")
        workspace3 = Mock()
        workspace3.name = WorkspaceName("low-score")
        
        mock_workspace_repository.find_all = AsyncMock(return_value=[workspace1, workspace2, workspace3])
        
        # Mock overall score calculation
        with patch.object(service, '_calculate_overall_score') as mock_calc:
            mock_calc.side_effect = [0.95, 0.75, 0.55]  # High, medium, low scores
            
            rankings = await service.get_workspace_rankings(limit=5)
            
            assert isinstance(rankings, list)
            assert len(rankings) == 3
            
            # Check rankings are in descending order
            assert rankings[0][0] == WorkspaceName("high-score")
            assert rankings[0][1] == 0.95
            assert rankings[1][0] == WorkspaceName("medium-score")
            assert rankings[1][1] == 0.75
            assert rankings[2][0] == WorkspaceName("low-score")
            assert rankings[2][1] == 0.55
    
    @pytest.mark.asyncio
    async def test_cleanup_analytics_data(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test cleanup of old analytics data."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Add old cached data
        old_analytics = WorkspaceAnalytics(
            workspace_name=WorkspaceName("old-workspace"),
            collection_time=datetime.now() - timedelta(days=100),  # Very old
            time_range=(datetime.now() - timedelta(days=130), datetime.now() - timedelta(days=100)),
            usage=UsageMetrics(),
            performance=PerformanceMetrics(),
            resources=ResourceMetrics(),
            health=HealthDiagnostics(),
            behavior=BehaviorMetrics()
        )
        service._metrics_cache[WorkspaceName("old-workspace")] = old_analytics
        
        # Create workspace with old events
        workspace = Mock()
        workspace.name = WorkspaceName("event-workspace")
        old_events = [
            {"timestamp": (datetime.now() - timedelta(days=100)).isoformat(), "event_type": "old_event"},
            {"timestamp": datetime.now().isoformat(), "event_type": "recent_event"}
        ]
        workspace.metadata = {"analytics_events": old_events}
        workspace.set_metadata = Mock(return_value=workspace)
        
        mock_workspace_repository.find_all = AsyncMock(return_value=[workspace])
        mock_workspace_repository.update = AsyncMock()
        
        cleaned_count = await service.cleanup_analytics_data(older_than_days=30)
        
        # Should have cleaned up cache and old events
        assert cleaned_count >= 2  # At least cache + some events
        assert WorkspaceName("old-workspace") not in service._metrics_cache
        
        # Workspace should have been updated with only recent events
        workspace.set_metadata.assert_called()
        mock_workspace_repository.update.assert_called()


class TestUsageMetrics:
    """Test UsageMetrics data class."""
    
    def test_create_usage_metrics(self):
        """Test creating usage metrics."""
        metrics = UsageMetrics()
        
        assert metrics.total_sessions == 0
        assert metrics.total_pipelines_run == 0
        assert metrics.total_templates_used == 0
        assert isinstance(metrics.unique_templates, set)
        assert metrics.average_session_duration == timedelta()
        assert metrics.last_active is None
        assert metrics.pipeline_success_rate == 0.0
        assert metrics.error_count == 0
        assert metrics.cache_hit_rate == 0.0
    
    def test_usage_metrics_with_data(self):
        """Test usage metrics with actual data."""
        metrics = UsageMetrics(
            total_sessions=50,
            total_pipelines_run=100,
            unique_templates={"template1", "template2"},
            pipeline_success_rate=0.95,
            error_count=3
        )
        
        assert metrics.total_sessions == 50
        assert metrics.total_pipelines_run == 100
        assert len(metrics.unique_templates) == 2
        assert metrics.pipeline_success_rate == 0.95
        assert metrics.error_count == 3


class TestPerformanceMetrics:
    """Test PerformanceMetrics data class."""
    
    def test_create_performance_metrics(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics()
        
        assert metrics.average_pipeline_duration == timedelta()
        assert metrics.average_step_duration == timedelta()
        assert isinstance(metrics.slowest_pipelines, list)
        assert isinstance(metrics.fastest_pipelines, list)
        assert isinstance(metrics.llm_response_times, list)
        assert isinstance(metrics.cache_performance, dict)
        assert metrics.resource_efficiency == 0.0
    
    def test_performance_metrics_with_data(self):
        """Test performance metrics with data."""
        slowest = [("slow-pipeline", timedelta(minutes=10))]
        fastest = [("fast-pipeline", timedelta(seconds=5))]
        
        metrics = PerformanceMetrics(
            average_pipeline_duration=timedelta(minutes=2),
            slowest_pipelines=slowest,
            fastest_pipelines=fastest,
            resource_efficiency=0.85
        )
        
        assert metrics.average_pipeline_duration == timedelta(minutes=2)
        assert metrics.slowest_pipelines == slowest
        assert metrics.fastest_pipelines == fastest
        assert metrics.resource_efficiency == 0.85


class TestHealthDiagnostics:
    """Test HealthDiagnostics data class."""
    
    def test_create_health_diagnostics(self):
        """Test creating health diagnostics."""
        diagnostics = HealthDiagnostics()
        
        assert diagnostics.overall_status == HealthStatus.UNKNOWN
        assert isinstance(diagnostics.issues, list)
        assert isinstance(diagnostics.warnings, list)
        assert isinstance(diagnostics.recommendations, list)
        assert diagnostics.integrity_score == 0.0
        assert diagnostics.security_score == 0.0
        assert diagnostics.performance_score == 0.0
        assert diagnostics.maintainability_score == 0.0
    
    def test_health_diagnostics_with_data(self):
        """Test health diagnostics with data."""
        diagnostics = HealthDiagnostics(
            overall_status=HealthStatus.GOOD,
            issues=["Issue 1"],
            warnings=["Warning 1"],
            integrity_score=0.9,
            security_score=0.85,
            performance_score=0.88,
            maintainability_score=0.92
        )
        
        assert diagnostics.overall_status == HealthStatus.GOOD
        assert len(diagnostics.issues) == 1
        assert len(diagnostics.warnings) == 1
        assert diagnostics.integrity_score == 0.9
        assert diagnostics.security_score == 0.85
        assert diagnostics.performance_score == 0.88
        assert diagnostics.maintainability_score == 0.92


class TestBehaviorMetrics:
    """Test BehaviorMetrics data class."""
    
    def test_create_behavior_metrics(self):
        """Test creating behavior metrics."""
        metrics = BehaviorMetrics()
        
        assert isinstance(metrics.preferred_models, Counter)
        assert isinstance(metrics.template_usage_patterns, dict)
        assert isinstance(metrics.configuration_changes, list)
        assert isinstance(metrics.error_patterns, Counter)
        assert isinstance(metrics.session_patterns, dict)
        assert metrics.workflow_efficiency == 0.0
        assert metrics.learning_curve_progress == 0.0
    
    def test_behavior_metrics_with_data(self):
        """Test behavior metrics with data."""
        preferred_models = Counter({"gpt-4o": 10, "claude-3-sonnet": 5})
        template_patterns = {"template1": [datetime.now()]}
        
        metrics = BehaviorMetrics(
            preferred_models=preferred_models,
            template_usage_patterns=template_patterns,
            workflow_efficiency=0.78
        )
        
        assert metrics.preferred_models == preferred_models
        assert metrics.template_usage_patterns == template_patterns
        assert metrics.workflow_efficiency == 0.78


class TestWorkspaceAnalytics:
    """Test WorkspaceAnalytics data class."""
    
    def test_create_workspace_analytics(self):
        """Test creating workspace analytics."""
        workspace_name = WorkspaceName("test-workspace")
        collection_time = datetime.now()
        time_range = (datetime.now() - timedelta(days=30), datetime.now())
        
        analytics = WorkspaceAnalytics(
            workspace_name=workspace_name,
            collection_time=collection_time,
            time_range=time_range,
            usage=UsageMetrics(),
            performance=PerformanceMetrics(),
            resources=ResourceMetrics(),
            health=HealthDiagnostics(),
            behavior=BehaviorMetrics()
        )
        
        assert analytics.workspace_name == workspace_name
        assert analytics.collection_time == collection_time
        assert analytics.time_range == time_range
        assert isinstance(analytics.usage, UsageMetrics)
        assert isinstance(analytics.performance, PerformanceMetrics)
        assert isinstance(analytics.resources, ResourceMetrics)
        assert isinstance(analytics.health, HealthDiagnostics)
        assert isinstance(analytics.behavior, BehaviorMetrics)
        assert analytics.comparative_rank is None
        assert isinstance(analytics.trends, dict)


class TestAnalyticsReport:
    """Test AnalyticsReport data class."""
    
    def test_create_analytics_report(self):
        """Test creating analytics report."""
        workspace_analytics = WorkspaceAnalytics(
            workspace_name=WorkspaceName("test-workspace"),
            collection_time=datetime.now(),
            time_range=(datetime.now() - timedelta(days=30), datetime.now()),
            usage=UsageMetrics(),
            performance=PerformanceMetrics(),
            resources=ResourceMetrics(),
            health=HealthDiagnostics(),
            behavior=BehaviorMetrics()
        )
        
        report = AnalyticsReport(
            workspace_analytics=workspace_analytics,
            insights=["Insight 1", "Insight 2"],
            action_items=["Action 1"],
            optimization_opportunities=["Optimization 1"],
            risk_factors=["Risk 1"],
            success_indicators=["Success 1"]
        )
        
        assert report.workspace_analytics == workspace_analytics
        assert len(report.insights) == 2
        assert len(report.action_items) == 1
        assert len(report.optimization_opportunities) == 1
        assert len(report.risk_factors) == 1
        assert len(report.success_indicators) == 1
        assert isinstance(report.report_generated_at, datetime)


class TestAnalyticsEnums:
    """Test analytics enumeration classes."""
    
    def test_analytics_scope(self):
        """Test AnalyticsScope enum values."""
        assert AnalyticsScope.WORKSPACE == "workspace"
        assert AnalyticsScope.GLOBAL == "global"
        assert AnalyticsScope.COMPARATIVE == "comparative"
    
    def test_metric_type(self):
        """Test MetricType enum values."""
        assert MetricType.USAGE == "usage"
        assert MetricType.PERFORMANCE == "performance"
        assert MetricType.RESOURCE == "resource"
        assert MetricType.HEALTH == "health"
        assert MetricType.BEHAVIOR == "behavior"
    
    def test_health_status(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.EXCELLENT == "excellent"
        assert HealthStatus.GOOD == "good"
        assert HealthStatus.WARNING == "warning"
        assert HealthStatus.CRITICAL == "critical"
        assert HealthStatus.UNKNOWN == "unknown"


class TestWorkspaceAnalyticsServicePrivateMethods:
    """Test private methods of WorkspaceAnalyticsService."""
    
    @pytest.mark.asyncio
    async def test_collect_usage_metrics_from_events(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test collecting usage metrics from workspace events."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create workspace with analytics events
        now = datetime.now()
        events = [
            {"timestamp": now.isoformat(), "event_type": "pipeline_run", "data": {"status": "success", "duration": 30}},
            {"timestamp": now.isoformat(), "event_type": "pipeline_run", "data": {"status": "failed", "duration": 15}},
            {"timestamp": now.isoformat(), "event_type": "template_used", "data": {"template_name": "template1"}},
            {"timestamp": now.isoformat(), "event_type": "template_used", "data": {"template_name": "template2"}},
            {"timestamp": now.isoformat(), "event_type": "session", "data": {"duration": 300}},
            {"timestamp": now.isoformat(), "event_type": "error", "data": {"error_type": "validation"}}
        ]
        
        workspace = Mock()
        workspace.metadata = {"analytics_events": events}
        
        time_range = (now - timedelta(hours=1), now + timedelta(hours=1))
        metrics = await service._collect_usage_metrics(workspace, time_range)
        
        assert metrics.total_pipelines_run == 2
        assert metrics.total_templates_used == 2
        assert metrics.total_sessions == 1
        assert len(metrics.unique_templates) == 2
        assert "template1" in metrics.unique_templates
        assert "template2" in metrics.unique_templates
        assert metrics.pipeline_success_rate == 0.5  # 1 success out of 2
        assert metrics.error_count == 1
        assert isinstance(metrics.last_active, datetime)
    
    @pytest.mark.asyncio
    async def test_collect_performance_metrics_from_events(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test collecting performance metrics from workspace events."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        now = datetime.now()
        events = [
            {"timestamp": now.isoformat(), "event_type": "pipeline_run", 
             "data": {"pipeline_name": "fast-pipeline", "duration": 10}},
            {"timestamp": now.isoformat(), "event_type": "pipeline_run", 
             "data": {"pipeline_name": "slow-pipeline", "duration": 120}},
            {"timestamp": now.isoformat(), "event_type": "pipeline_run", 
             "data": {"pipeline_name": "medium-pipeline", "duration": 60}}
        ]
        
        workspace = Mock()
        workspace.metadata = {"analytics_events": events}
        
        time_range = (now - timedelta(hours=1), now + timedelta(hours=1))
        metrics = await service._collect_performance_metrics(workspace, time_range)
        
        # Average should be (10 + 120 + 60) / 3 = 63.33 seconds
        expected_avg = timedelta(seconds=63.33333333333333)
        assert abs(metrics.average_pipeline_duration.total_seconds() - expected_avg.total_seconds()) < 0.1
        
        # Check slowest and fastest pipelines
        assert len(metrics.slowest_pipelines) == 3
        assert metrics.slowest_pipelines[0][0] == "slow-pipeline"
        assert metrics.slowest_pipelines[0][1] == timedelta(seconds=120)
        
        assert len(metrics.fastest_pipelines) == 3
        assert metrics.fastest_pipelines[-1][0] == "fast-pipeline"
        assert metrics.fastest_pipelines[-1][1] == timedelta(seconds=10)
    
    @pytest.mark.asyncio
    async def test_collect_resource_metrics(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test collecting resource metrics."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test workspace structure
        workspace_path = temp_dir / "resource-test"
        templates_path = workspace_path / "templates"
        pipelines_path = workspace_path / "pipelines"
        cache_path = workspace_path / "cache"
        
        templates_path.mkdir(parents=True)
        pipelines_path.mkdir(parents=True)
        cache_path.mkdir(parents=True)
        
        # Create some test files
        (templates_path / "template1.yaml").write_text("template: content")
        (templates_path / "template2.yaml").write_text("template: content")
        (pipelines_path / "pipeline1.yaml").write_text("pipeline: content")
        (cache_path / "cache_file").write_text("cached data")
        
        workspace = Mock()
        workspace.get_size_on_disk.return_value = 1024 * 1024  # 1MB
        workspace.get_templates_path.return_value = WorkspacePath.from_string(str(templates_path))
        workspace.get_pipelines_path.return_value = WorkspacePath.from_string(str(pipelines_path))
        workspace.get_cache_path.return_value = WorkspacePath.from_string(str(cache_path))
        
        time_range = (datetime.now() - timedelta(days=1), datetime.now())
        metrics = await service._collect_resource_metrics(workspace, time_range)
        
        assert metrics.storage_usage_bytes == 1024 * 1024
        assert metrics.template_count == 2
        assert metrics.pipeline_count == 1
        assert metrics.cache_size_bytes > 0  # Should have some cache data
    
    @pytest.mark.asyncio
    async def test_extract_metric_value(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test extracting specific metric values from analytics."""
        service = WorkspaceAnalyticsService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        analytics = WorkspaceAnalytics(
            workspace_name=WorkspaceName("test"),
            collection_time=datetime.now(),
            time_range=(datetime.now() - timedelta(days=30), datetime.now()),
            usage=UsageMetrics(total_pipelines_run=50, pipeline_success_rate=0.9),
            performance=PerformanceMetrics(),
            resources=ResourceMetrics(storage_efficiency=0.8),
            health=HealthDiagnostics(
                integrity_score=0.9,
                security_score=0.85,
                performance_score=0.88,
                maintainability_score=0.92
            ),
            behavior=BehaviorMetrics()
        )
        
        assert await service._extract_metric_value(analytics, "total_pipelines") == 50.0
        assert await service._extract_metric_value(analytics, "success_rate") == 0.9
        assert await service._extract_metric_value(analytics, "storage_efficiency") == 0.8
        
        # Health score should be average of all health scores
        health_score = await service._extract_metric_value(analytics, "health_score")
        expected_health = (0.9 + 0.85 + 0.88 + 0.92) / 4
        assert abs(health_score - expected_health) < 0.01
        
        # Unknown metric should return 0.0
        assert await service._extract_metric_value(analytics, "unknown_metric") == 0.0