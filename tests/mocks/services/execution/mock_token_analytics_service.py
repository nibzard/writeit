"""Mock implementation of TokenAnalyticsService for testing."""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock
from datetime import datetime, timedelta

from writeit.domains.execution.services.token_analytics_service import (
    TokenAnalyticsService,
    TokenUsageReport,
    TokenTrend,
    CostAnalysis,
    UsageAlert
)
from writeit.domains.execution.entities.token_usage import TokenUsage
from writeit.domains.execution.value_objects.token_count import TokenCount


class MockTokenAnalyticsService(TokenAnalyticsService):
    """Mock implementation of TokenAnalyticsService.
    
    Provides configurable token analytics behavior for testing
    token analytics scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock token analytics service."""
        self._mock = Mock()
        self._usage_reports: Dict[str, TokenUsageReport] = {}
        self._token_trends: List[TokenTrend] = []
        self._cost_analyses: Dict[str, CostAnalysis] = {}
        self._usage_alerts: List[UsageAlert] = []
        self._should_fail = False
        
    def configure_usage_report(self, period: str, report: TokenUsageReport) -> None:
        """Configure usage report for specific period."""
        self._usage_reports[period] = report
        
    def configure_token_trends(self, trends: List[TokenTrend]) -> None:
        """Configure token usage trends."""
        self._token_trends = trends
        
    def configure_cost_analysis(self, provider: str, analysis: CostAnalysis) -> None:
        """Configure cost analysis for provider."""
        self._cost_analyses[provider] = analysis
        
    def configure_usage_alerts(self, alerts: List[UsageAlert]) -> None:
        """Configure usage alerts."""
        self._usage_alerts = alerts
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if analytics operations should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._usage_reports.clear()
        self._token_trends.clear()
        self._cost_analyses.clear()
        self._usage_alerts.clear()
        self._should_fail = False
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def generate_usage_report(
        self,
        start_date: datetime,
        end_date: datetime,
        workspace: Optional[str] = None
    ) -> TokenUsageReport:
        """Generate token usage report for period."""
        self._mock.generate_usage_report(start_date, end_date, workspace)
        
        if self._should_fail:
            raise Exception("Mock usage report generation error")
            
        period_key = f"{start_date.date()}_to_{end_date.date()}"
        
        # Return configured report if available
        if period_key in self._usage_reports:
            return self._usage_reports[period_key]
            
        # Create mock usage report
        return TokenUsageReport(
            period_start=start_date,
            period_end=end_date,
            workspace=workspace,
            total_tokens=TokenCount(10000),
            input_tokens=TokenCount(6000),
            output_tokens=TokenCount(4000),
            total_requests=50,
            unique_models=3,
            total_cost=50.0,
            average_tokens_per_request=200.0,
            peak_usage_hour=14  # 2 PM
        )
        
    async def analyze_token_trends(
        self,
        time_period: timedelta,
        granularity: str = "daily"
    ) -> List[TokenTrend]:
        """Analyze token usage trends."""
        self._mock.analyze_token_trends(time_period, granularity)
        
        if self._should_fail:
            return []
            
        # Return configured trends if available
        if self._token_trends:
            return self._token_trends
            
        # Create mock trends
        trends = []
        days = time_period.days or 1
        
        for i in range(min(days, 7)):
            trend_date = datetime.now() - timedelta(days=i)
            trends.append(TokenTrend(
                date=trend_date,
                total_tokens=TokenCount(1000 + i * 100),
                requests_count=10 + i * 2,
                average_cost=5.0 + i * 0.5,
                trend_direction="increasing" if i < 3 else "stable"
            ))
            
        return trends
        
    async def calculate_cost_analysis(
        self,
        provider: str,
        model: Optional[str] = None,
        time_period: Optional[timedelta] = None
    ) -> CostAnalysis:
        """Calculate cost analysis for provider/model."""
        self._mock.calculate_cost_analysis(provider, model, time_period)
        
        if self._should_fail:
            raise Exception("Mock cost analysis error")
            
        analysis_key = f"{provider}_{model or 'all'}"
        
        # Return configured analysis if available
        if analysis_key in self._cost_analyses:
            return self._cost_analyses[analysis_key]
            
        # Create mock cost analysis
        return CostAnalysis(
            provider=provider,
            model=model,
            period_start=datetime.now() - (time_period or timedelta(days=30)),
            period_end=datetime.now(),
            total_cost=100.0,
            input_token_cost=60.0,
            output_token_cost=40.0,
            cost_per_request=2.0,
            cost_trend="increasing",
            projected_monthly_cost=120.0
        )
        
    async def detect_usage_anomalies(
        self,
        threshold_multiplier: float = 2.0,
        lookback_days: int = 7
    ) -> List[UsageAlert]:
        """Detect usage anomalies and generate alerts."""
        self._mock.detect_usage_anomalies(threshold_multiplier, lookback_days)
        
        if self._should_fail:
            return []
            
        # Return configured alerts if available
        if self._usage_alerts:
            return self._usage_alerts
            
        # Create mock alerts based on threshold
        if threshold_multiplier < 1.5:  # Low threshold = more alerts
            return [
                UsageAlert(
                    alert_type="high_usage",
                    severity="warning",
                    message="Token usage 150% above normal",
                    timestamp=datetime.now(),
                    affected_workspace="test-workspace",
                    metric_value=1500.0,
                    threshold_value=1000.0
                )
            ]
        else:
            return []  # No anomalies detected
            
    async def get_top_consumers(
        self,
        metric: str = "tokens",
        limit: int = 10,
        time_period: Optional[timedelta] = None
    ) -> List[Dict[str, Any]]:
        """Get top token consumers."""
        self._mock.get_top_consumers(metric, limit, time_period)
        
        # Create mock top consumers list
        consumers = []
        for i in range(min(limit, 5)):
            consumers.append({
                "name": f"workspace-{i+1}",
                "tokens_used": 1000 - (i * 100),
                "requests_count": 50 - (i * 5),
                "total_cost": 10.0 - (i * 1.0),
                "rank": i + 1
            })
            
        return consumers
        
    async def predict_future_usage(
        self,
        prediction_days: int = 30,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Predict future token usage."""
        self._mock.predict_future_usage(prediction_days, confidence_level)
        
        if self._should_fail:
            return {"error": "Mock prediction error"}
            
        # Create mock prediction
        base_daily_usage = 1000
        predicted_total = base_daily_usage * prediction_days
        
        return {
            "prediction_period_days": prediction_days,
            "predicted_total_tokens": predicted_total,
            "predicted_daily_average": base_daily_usage,
            "confidence_level": confidence_level,
            "prediction_accuracy": 0.85,
            "factors_considered": ["historical_trends", "seasonal_patterns"],
            "cost_projection": predicted_total * 0.001  # $0.001 per token
        }
        
    async def optimize_token_usage(
        self,
        optimization_target: str = "cost"
    ) -> Dict[str, Any]:
        """Provide token usage optimization recommendations."""
        self._mock.optimize_token_usage(optimization_target)
        
        if self._should_fail:
            return {"error": "Mock optimization error"}
            
        return {
            "optimization_target": optimization_target,
            "potential_savings": {
                "cost_reduction": "15%",
                "token_reduction": "10%"
            },
            "recommendations": [
                {
                    "category": "model_selection",
                    "suggestion": "Use smaller model for simple tasks",
                    "impact": "High"
                },
                {
                    "category": "prompt_optimization",
                    "suggestion": "Reduce prompt length",
                    "impact": "Medium"
                },
                {
                    "category": "caching",
                    "suggestion": "Increase cache TTL",
                    "impact": "Low"
                }
            ]
        }
        
    async def export_usage_data(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Export usage data for external analysis."""
        self._mock.export_usage_data(start_date, end_date, format)
        
        if self._should_fail:
            return {"success": False, "error": "Mock export error"}
            
        return {
            "success": True,
            "format": format,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "records_count": 1000,
            "file_size_bytes": 50000,
            "download_url": "mock://download/usage_data.csv"
        }
        
    async def set_usage_budgets(
        self,
        budgets: Dict[str, Any]
    ) -> bool:
        """Set usage budgets and alerts."""
        self._mock.set_usage_budgets(budgets)
        
        return not self._should_fail
        
    async def get_real_time_usage(
        self,
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get real-time usage statistics."""
        self._mock.get_real_time_usage(workspace)
        
        return {
            "workspace": workspace,
            "current_hour_tokens": 150,
            "current_hour_requests": 5,
            "current_hour_cost": 0.15,
            "daily_tokens_so_far": 1200,
            "daily_budget_remaining": 0.8,  # 80% remaining
            "active_requests": 2,
            "last_updated": datetime.now().isoformat()
        }
