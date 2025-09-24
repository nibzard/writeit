"""Unit tests for TokenAnalyticsService.

Tests comprehensive token usage analytics including:
- Token consumption tracking and aggregation
- Cost calculation and billing analytics
- Usage pattern analysis and optimization suggestions
- Rate limiting and quota management
- Performance metrics and monitoring
- Anomaly detection and alerting
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import replace
from decimal import Decimal

from src.writeit.domains.execution.services.token_analytics_service import (
    TokenAnalyticsService,
    TokenUsageRecord,
    TokenUsageAggregation,
    CostAnalysis,
    UsagePattern,
    UsageAlert,
    OptimizationSuggestion,
    BillingPeriod,
    UsageQuota,
    AnomalyDetectionResult,
    TokenAnalyticsError,
    QuotaExceededError,
    InvalidUsageDataError
)
from src.writeit.domains.execution.value_objects.token_count import TokenCount
from src.writeit.domains.execution.value_objects.model_name import ModelName
from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName

from tests.builders.execution_builders import (
    TokenUsageRecordBuilder,
    TokenUsageAggregationBuilder
)


class MockTokenUsageRepository:
    """Mock token usage repository for testing."""
    
    def __init__(self):
        self._records: List[TokenUsageRecord] = []
        self._aggregations: Dict[str, TokenUsageAggregation] = {}
    
    async def store_usage_record(self, record: TokenUsageRecord) -> None:
        """Store usage record."""
        self._records.append(record)
    
    async def get_usage_records(
        self,
        workspace_name: Optional[str] = None,
        model_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[TokenUsageRecord]:
        """Get filtered usage records."""
        filtered_records = self._records
        
        if workspace_name:
            filtered_records = [r for r in filtered_records if r.workspace_name == workspace_name]
        
        if model_name:
            filtered_records = [r for r in filtered_records if r.model_name.value == model_name]
        
        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]
        
        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]
        
        return filtered_records[:limit]
    
    async def get_aggregated_usage(
        self,
        workspace_name: Optional[str] = None,
        model_name: Optional[str] = None,
        period: BillingPeriod = BillingPeriod.MONTHLY
    ) -> TokenUsageAggregation:
        """Get aggregated usage data."""
        key = f"{workspace_name or 'all'}_{model_name or 'all'}_{period.value}"
        
        if key not in self._aggregations:
            # Generate default aggregation
            records = await self.get_usage_records(workspace_name, model_name)
            total_tokens = sum(r.usage.total_tokens for r in records)
            total_cost = sum(r.cost for r in records)
            
            self._aggregations[key] = TokenUsageAggregation(
                workspace_name=workspace_name,
                model_name=model_name,
                period=period,
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                total_requests=len(records),
                total_prompt_tokens=sum(r.usage.prompt_tokens for r in records),
                total_completion_tokens=sum(r.usage.completion_tokens for r in records),
                total_tokens=total_tokens,
                total_cost=Decimal(str(total_cost)),
                avg_tokens_per_request=total_tokens / len(records) if records else 0,
                avg_cost_per_request=total_cost / len(records) if records else 0.0
            )
        
        return self._aggregations[key]
    
    async def clear_all(self) -> None:
        """Clear all data."""
        self._records.clear()
        self._aggregations.clear()
    
    def add_mock_aggregation(self, key: str, aggregation: TokenUsageAggregation) -> None:
        """Add mock aggregation for testing."""
        self._aggregations[key] = aggregation


class TestTokenUsageRecord:
    """Test TokenUsageRecord behavior."""
    
    def test_create_token_usage_record(self):
        """Test creating token usage record."""
        model_name = ModelName.from_string("gpt-4o-mini")
        usage = TokenCount(prompt_tokens=100, completion_tokens=200, total_tokens=300)
        
        record = TokenUsageRecord(
            request_id="req-123",
            workspace_name="test-workspace",
            model_name=model_name,
            usage=usage,
            cost=0.015,
            timestamp=datetime.now(),
            execution_time_ms=1500.0,
            prompt_hash="abc123",
            metadata={"temperature": 0.7}
        )
        
        assert record.request_id == "req-123"
        assert record.workspace_name == "test-workspace"
        assert record.model_name == model_name
        assert record.usage == usage
        assert record.cost == 0.015
        assert isinstance(record.timestamp, datetime)
        assert record.execution_time_ms == 1500.0
        assert record.prompt_hash == "abc123"
        assert record.metadata["temperature"] == 0.7
    
    def test_token_usage_record_properties(self):
        """Test calculated properties."""
        usage = TokenCount(100, 200, 300)
        record = TokenUsageRecord(
            request_id="req-123",
            workspace_name="test-workspace",
            model_name=ModelName.from_string("gpt-4o-mini"),
            usage=usage,
            cost=0.015,
            timestamp=datetime.now(),
            execution_time_ms=1500.0
        )
        
        # Test cost per token
        assert record.cost_per_token == 0.015 / 300
        
        # Test tokens per second
        assert record.tokens_per_second == 300 / 1.5  # 1500ms = 1.5s
    
    def test_token_usage_record_efficiency_score(self):
        """Test efficiency score calculation."""
        # Efficient usage (low cost, high tokens per second)
        efficient_record = TokenUsageRecord(
            request_id="efficient",
            workspace_name="test",
            model_name=ModelName.from_string("gpt-4o-mini"),
            usage=TokenCount(100, 200, 300),
            cost=0.005,  # Low cost
            execution_time_ms=500.0,  # Fast execution
            timestamp=datetime.now()
        )
        
        assert efficient_record.efficiency_score > 0.5
        
        # Inefficient usage (high cost, low tokens per second)
        inefficient_record = TokenUsageRecord(
            request_id="inefficient",
            workspace_name="test",
            model_name=ModelName.from_string("gpt-4o-mini"),
            usage=TokenCount(100, 200, 300),
            cost=0.050,  # High cost
            execution_time_ms=5000.0,  # Slow execution
            timestamp=datetime.now()
        )
        
        assert inefficient_record.efficiency_score < 0.5
        assert efficient_record.efficiency_score > inefficient_record.efficiency_score


class TestTokenUsageAggregation:
    """Test TokenUsageAggregation behavior."""
    
    def test_create_token_usage_aggregation(self):
        """Test creating token usage aggregation."""
        aggregation = TokenUsageAggregation(
            workspace_name="test-workspace",
            model_name="gpt-4o-mini",
            period=BillingPeriod.MONTHLY,
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2025, 1, 31),
            total_requests=1000,
            total_prompt_tokens=50000,
            total_completion_tokens=75000,
            total_tokens=125000,
            total_cost=Decimal("125.50"),
            avg_tokens_per_request=125.0,
            avg_cost_per_request=0.1255
        )
        
        assert aggregation.workspace_name == "test-workspace"
        assert aggregation.model_name == "gpt-4o-mini"
        assert aggregation.period == BillingPeriod.MONTHLY
        assert aggregation.total_requests == 1000
        assert aggregation.total_tokens == 125000
        assert aggregation.total_cost == Decimal("125.50")
        assert aggregation.avg_tokens_per_request == 125.0
        assert aggregation.avg_cost_per_request == 0.1255
    
    def test_aggregation_calculated_properties(self):
        """Test calculated properties."""
        aggregation = TokenUsageAggregation(
            workspace_name="test",
            period=BillingPeriod.MONTHLY,
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2025, 1, 31),
            total_requests=1000,
            total_prompt_tokens=40000,
            total_completion_tokens=60000,
            total_tokens=100000,
            total_cost=Decimal("100.00")
        )
        
        # Test completion ratio
        assert aggregation.completion_ratio == 0.6  # 60000 / 100000
        
        # Test cost per thousand tokens
        assert aggregation.cost_per_1k_tokens == 1.0  # $100 / 100k tokens * 1000
        
        # Test period duration
        assert aggregation.period_duration_days == 30


class TestCostAnalysis:
    """Test CostAnalysis behavior."""
    
    def test_create_cost_analysis(self):
        """Test creating cost analysis."""
        analysis = CostAnalysis(
            period=BillingPeriod.MONTHLY,
            total_cost=Decimal("250.75"),
            cost_by_model={"gpt-4o-mini": Decimal("150.50"), "gpt-3.5-turbo": Decimal("100.25")},
            cost_by_workspace={"workspace1": Decimal("175.25"), "workspace2": Decimal("75.50")},
            projected_monthly_cost=Decimal("275.00"),
            cost_trends=[10.5, 12.3, 15.2, 18.1, 22.4],
            top_cost_drivers=[
                {"type": "model", "name": "gpt-4o-mini", "cost": Decimal("150.50")},
                {"type": "workspace", "name": "workspace1", "cost": Decimal("175.25")}
            ]
        )
        
        assert analysis.period == BillingPeriod.MONTHLY
        assert analysis.total_cost == Decimal("250.75")
        assert len(analysis.cost_by_model) == 2
        assert analysis.projected_monthly_cost == Decimal("275.00")
        assert len(analysis.cost_trends) == 5
        assert len(analysis.top_cost_drivers) == 2
    
    def test_cost_analysis_calculations(self):
        """Test cost analysis calculations."""
        analysis = CostAnalysis(
            period=BillingPeriod.MONTHLY,
            total_cost=Decimal("100.00"),
            cost_by_model={"model1": Decimal("70.00"), "model2": Decimal("30.00")},
            cost_trends=[80.0, 85.0, 90.0, 95.0, 100.0]
        )
        
        # Test cost growth rate
        growth_rate = analysis.calculate_growth_rate()
        assert growth_rate > 0  # Should show positive growth
        
        # Test most expensive model
        most_expensive = analysis.get_most_expensive_model()
        assert most_expensive == "model1"
        
        # Test cost distribution
        distribution = analysis.get_cost_distribution()
        assert distribution["model1"] == 0.7  # 70% of total cost
        assert distribution["model2"] == 0.3  # 30% of total cost


class TestUsagePattern:
    """Test UsagePattern behavior."""
    
    def test_create_usage_pattern(self):
        """Test creating usage pattern."""
        pattern = UsagePattern(
            name="High Volume Batch Processing",
            description="Large batches of requests during off-peak hours",
            characteristics={
                "batch_size_avg": 50,
                "peak_hour": "02:00",
                "tokens_per_request_avg": 1500,
                "cost_efficiency": 0.85
            },
            frequency="weekly",
            impact_score=0.75,
            recommendations=[
                "Consider using cheaper models for batch processing",
                "Optimize batch timing to reduce costs"
            ]
        )
        
        assert pattern.name == "High Volume Batch Processing"
        assert "batch_size_avg" in pattern.characteristics
        assert pattern.frequency == "weekly"
        assert pattern.impact_score == 0.75
        assert len(pattern.recommendations) == 2


class TestTokenAnalyticsService:
    """Test TokenAnalyticsService business logic."""
    
    def test_create_service(self):
        """Test creating token analytics service."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        assert service._repository == repository
        assert service._anomaly_threshold == 2.0
        assert service._cost_alert_threshold == 100.0
    
    @pytest.mark.asyncio
    async def test_record_token_usage(self):
        """Test recording token usage."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        usage = TokenCount(100, 200, 300)
        model_name = ModelName.from_string("gpt-4o-mini")
        
        await service.record_token_usage(
            request_id="req-123",
            workspace_name="test-workspace",
            model_name=model_name,
            usage=usage,
            cost=0.015,
            execution_time_ms=1500.0,
            metadata={"temperature": 0.7}
        )
        
        # Verify record was stored
        records = await repository.get_usage_records()
        assert len(records) == 1
        
        record = records[0]
        assert record.request_id == "req-123"
        assert record.workspace_name == "test-workspace"
        assert record.model_name == model_name
        assert record.usage == usage
        assert record.cost == 0.015
    
    @pytest.mark.asyncio
    async def test_get_usage_summary(self):
        """Test getting usage summary."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add some mock data
        usage1 = TokenUsageRecord(
            request_id="req-1",
            workspace_name="workspace1",
            model_name=ModelName.from_string("gpt-4o-mini"),
            usage=TokenCount(100, 150, 250),
            cost=0.025,
            timestamp=datetime.now()
        )
        
        usage2 = TokenUsageRecord(
            request_id="req-2",
            workspace_name="workspace1",
            model_name=ModelName.from_string("gpt-3.5-turbo"),
            usage=TokenCount(200, 300, 500),
            cost=0.015,
            timestamp=datetime.now()
        )
        
        await repository.store_usage_record(usage1)
        await repository.store_usage_record(usage2)
        
        # Get usage summary
        summary = await service.get_usage_summary(
            workspace_name="workspace1",
            period=BillingPeriod.MONTHLY
        )
        
        assert summary["total_requests"] == 2
        assert summary["total_tokens"] == 750  # 250 + 500
        assert summary["total_cost"] == 0.040  # 0.025 + 0.015
        assert len(summary["models"]) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_costs(self):
        """Test cost analysis."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add mock aggregation data
        aggregation = TokenUsageAggregation(
            workspace_name="test-workspace",
            period=BillingPeriod.MONTHLY,
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            total_requests=1000,
            total_tokens=125000,
            total_cost=Decimal("125.00")
        )
        
        repository.add_mock_aggregation("test-workspace_None_monthly", aggregation)
        
        # Analyze costs
        analysis = await service.analyze_costs(
            workspace_name="test-workspace",
            period=BillingPeriod.MONTHLY
        )
        
        assert isinstance(analysis, CostAnalysis)
        assert analysis.total_cost == Decimal("125.00")
        assert analysis.period == BillingPeriod.MONTHLY
    
    @pytest.mark.asyncio
    async def test_detect_usage_patterns(self):
        """Test usage pattern detection."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add records with a clear pattern (high usage during specific hours)
        base_time = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
        
        # Pattern: High usage at 2 AM daily
        for i in range(7):  # 7 days
            timestamp = base_time + timedelta(days=i)
            for j in range(10):  # 10 requests per day at this hour
                record = TokenUsageRecord(
                    request_id=f"batch-{i}-{j}",
                    workspace_name="batch-workspace",
                    model_name=ModelName.from_string("gpt-4o-mini"),
                    usage=TokenCount(500, 1000, 1500),
                    cost=0.075,
                    timestamp=timestamp + timedelta(minutes=j*5)
                )
                await repository.store_usage_record(record)
        
        # Detect patterns
        patterns = await service.detect_usage_patterns(
            workspace_name="batch-workspace",
            days_back=7
        )
        
        assert len(patterns) > 0
        
        # Should detect the batch processing pattern
        batch_pattern = next((p for p in patterns if "batch" in p.name.lower()), None)
        assert batch_pattern is not None
        assert batch_pattern.impact_score > 0.5
    
    @pytest.mark.asyncio
    async def test_generate_optimization_suggestions(self):
        """Test optimization suggestion generation."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add records showing inefficient usage (expensive model for simple tasks)
        for i in range(100):
            record = TokenUsageRecord(
                request_id=f"simple-{i}",
                workspace_name="test-workspace",
                model_name=ModelName.from_string("gpt-4o"),  # Expensive model
                usage=TokenCount(20, 30, 50),  # Small requests
                cost=0.005,  # High cost per token
                timestamp=datetime.now() - timedelta(hours=i),
                prompt_hash="simple_task_hash"
            )
            await repository.store_usage_record(record)
        
        # Generate suggestions
        suggestions = await service.generate_optimization_suggestions(
            workspace_name="test-workspace"
        )
        
        assert len(suggestions) > 0
        
        # Should suggest using cheaper model for simple tasks
        model_suggestion = next((s for s in suggestions if "model" in s.suggestion_type.lower()), None)
        assert model_suggestion is not None
        assert model_suggestion.potential_savings > 0
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self):
        """Test anomaly detection."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add normal usage pattern
        base_time = datetime.now() - timedelta(days=7)
        for i in range(6):  # 6 days of normal usage
            for j in range(10):  # 10 requests per day
                record = TokenUsageRecord(
                    request_id=f"normal-{i}-{j}",
                    workspace_name="test-workspace",
                    model_name=ModelName.from_string("gpt-4o-mini"),
                    usage=TokenCount(100, 200, 300),  # Normal usage
                    cost=0.015,
                    timestamp=base_time + timedelta(days=i, hours=j)
                )
                await repository.store_usage_record(record)
        
        # Add anomalous usage (sudden spike)
        anomaly_time = base_time + timedelta(days=6)
        for j in range(50):  # Sudden spike to 50 requests
            record = TokenUsageRecord(
                request_id=f"anomaly-{j}",
                workspace_name="test-workspace",
                model_name=ModelName.from_string("gpt-4o-mini"),
                usage=TokenCount(1000, 2000, 3000),  # 10x normal usage
                cost=0.150,
                timestamp=anomaly_time + timedelta(minutes=j*10)
            )
            await repository.store_usage_record(record)
        
        # Detect anomalies
        anomalies = await service.detect_anomalies(
            workspace_name="test-workspace",
            hours_back=168  # 7 days
        )
        
        assert len(anomalies) > 0
        
        # Should detect the usage spike
        spike_anomaly = next((a for a in anomalies if a.anomaly_type == "usage_spike"), None)
        assert spike_anomaly is not None
        assert spike_anomaly.severity_score > 0.5
    
    @pytest.mark.asyncio
    async def test_check_quota_limits(self):
        """Test quota limit checking."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Set quota limits
        quota = UsageQuota(
            workspace_name="test-workspace",
            period=BillingPeriod.MONTHLY,
            max_tokens=10000,
            max_cost=Decimal("50.00"),
            max_requests=100
        )
        
        service.set_usage_quota("test-workspace", quota)
        
        # Add usage that approaches quota
        for i in range(80):  # 80 requests (close to 100 limit)
            record = TokenUsageRecord(
                request_id=f"quota-{i}",
                workspace_name="test-workspace",
                model_name=ModelName.from_string("gpt-4o-mini"),
                usage=TokenCount(50, 75, 125),  # Total: 10k tokens for 80 requests
                cost=0.0625,  # Total: $50 for 80 requests
                timestamp=datetime.now() - timedelta(hours=i)
            )
            await repository.store_usage_record(record)
        
        # Check quota status
        quota_status = await service.check_quota_status("test-workspace")
        
        assert quota_status["requests_used"] == 80
        assert quota_status["tokens_used"] == 10000  # 80 * 125
        assert quota_status["cost_used"] == 5.0  # 80 * 0.0625
        
        # Should be close to limits
        assert quota_status["requests_utilization"] == 0.8  # 80/100
        assert quota_status["tokens_utilization"] == 1.0  # 10000/10000
        
        # Test quota exceeded scenario
        with pytest.raises(QuotaExceededError):
            # Try to add more usage that would exceed quota
            await service.validate_usage_against_quota(
                workspace_name="test-workspace",
                additional_tokens=1000,
                additional_cost=10.0,
                additional_requests=25
            )
    
    @pytest.mark.asyncio
    async def test_generate_usage_alerts(self):
        """Test usage alert generation."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository, cost_alert_threshold=10.0)
        
        # Add high-cost usage
        for i in range(10):
            record = TokenUsageRecord(
                request_id=f"expensive-{i}",
                workspace_name="expensive-workspace",
                model_name=ModelName.from_string("gpt-4o"),
                usage=TokenCount(500, 1000, 1500),
                cost=2.5,  # Total: $25 for 10 requests
                timestamp=datetime.now() - timedelta(hours=i)
            )
            await repository.store_usage_record(record)
        
        # Generate alerts
        alerts = await service.generate_usage_alerts(
            workspace_name="expensive-workspace"
        )
        
        assert len(alerts) > 0
        
        # Should generate cost alert
        cost_alert = next((a for a in alerts if a.alert_type == "high_cost"), None)
        assert cost_alert is not None
        assert cost_alert.severity == "warning" or cost_alert.severity == "critical"
        assert cost_alert.threshold_exceeded is True
    
    @pytest.mark.asyncio
    async def test_get_efficiency_metrics(self):
        """Test efficiency metrics calculation."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add mixed efficiency usage
        # Efficient requests
        for i in range(50):
            record = TokenUsageRecord(
                request_id=f"efficient-{i}",
                workspace_name="test-workspace",
                model_name=ModelName.from_string("gpt-4o-mini"),
                usage=TokenCount(100, 200, 300),
                cost=0.005,  # Low cost
                execution_time_ms=500.0,  # Fast
                timestamp=datetime.now() - timedelta(hours=i)
            )
            await repository.store_usage_record(record)
        
        # Inefficient requests
        for i in range(25):
            record = TokenUsageRecord(
                request_id=f"inefficient-{i}",
                workspace_name="test-workspace",
                model_name=ModelName.from_string("gpt-4o"),
                usage=TokenCount(100, 200, 300),
                cost=0.050,  # High cost
                execution_time_ms=5000.0,  # Slow
                timestamp=datetime.now() - timedelta(hours=i+50)
            )
            await repository.store_usage_record(record)
        
        # Get efficiency metrics
        metrics = await service.get_efficiency_metrics(
            workspace_name="test-workspace"
        )
        
        assert "avg_efficiency_score" in metrics
        assert "cost_efficiency" in metrics
        assert "time_efficiency" in metrics
        assert "efficiency_trend" in metrics
        
        # Should show decent efficiency (more efficient than inefficient requests)
        assert metrics["avg_efficiency_score"] > 0.4
    
    @pytest.mark.asyncio
    async def test_export_usage_data(self):
        """Test usage data export."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add sample data
        for i in range(10):
            record = TokenUsageRecord(
                request_id=f"export-{i}",
                workspace_name="export-workspace",
                model_name=ModelName.from_string("gpt-4o-mini"),
                usage=TokenCount(100, 150, 250),
                cost=0.025,
                timestamp=datetime.now() - timedelta(hours=i),
                metadata={"batch_id": f"batch_{i//5}"}
            )
            await repository.store_usage_record(record)
        
        # Export data
        export_data = await service.export_usage_data(
            workspace_name="export-workspace",
            format="json",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        assert export_data is not None
        assert "records" in export_data
        assert "summary" in export_data
        assert len(export_data["records"]) == 10
        
        # Verify summary data
        summary = export_data["summary"]
        assert summary["total_requests"] == 10
        assert summary["total_tokens"] == 2500  # 10 * 250
        assert summary["total_cost"] == 0.25  # 10 * 0.025
    
    @pytest.mark.asyncio
    async def test_compare_periods(self):
        """Test period-to-period comparison."""
        repository = MockTokenUsageRepository()
        service = TokenAnalyticsService(repository)
        
        # Add data for two periods
        # Current period (last 30 days)
        current_start = datetime.now() - timedelta(days=30)
        for i in range(100):  # Higher usage in current period
            record = TokenUsageRecord(
                request_id=f"current-{i}",
                workspace_name="comparison-workspace",
                model_name=ModelName.from_string("gpt-4o-mini"),
                usage=TokenCount(200, 300, 500),
                cost=0.025,
                timestamp=current_start + timedelta(hours=i*7)  # Spread over 30 days
            )
            await repository.store_usage_record(record)
        
        # Previous period (30-60 days ago)
        previous_start = datetime.now() - timedelta(days=60)
        for i in range(75):  # Lower usage in previous period
            record = TokenUsageRecord(
                request_id=f"previous-{i}",
                workspace_name="comparison-workspace",
                model_name=ModelName.from_string("gpt-4o-mini"),
                usage=TokenCount(150, 225, 375),
                cost=0.019,
                timestamp=previous_start + timedelta(hours=i*9)  # Spread over 30 days
            )
            await repository.store_usage_record(record)
        
        # Compare periods
        comparison = await service.compare_periods(
            workspace_name="comparison-workspace",
            current_period_days=30,
            previous_period_days=30
        )
        
        assert "current_period" in comparison
        assert "previous_period" in comparison
        assert "changes" in comparison
        
        # Verify growth calculations
        changes = comparison["changes"]
        assert changes["requests_change_percent"] > 0  # 100 vs 75 requests
        assert changes["tokens_change_percent"] > 0  # Higher token usage
        assert changes["cost_change_percent"] > 0  # Higher cost
    
    def test_calculate_model_costs(self):
        """Test model cost calculations."""
        service = TokenAnalyticsService(MockTokenUsageRepository())
        
        # Test GPT-4 pricing
        gpt4_cost = service.calculate_model_cost(
            model_name="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert gpt4_cost > 0
        
        # Test GPT-3.5 pricing (should be cheaper)
        gpt35_cost = service.calculate_model_cost(
            model_name="gpt-3.5-turbo",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert gpt35_cost > 0
        assert gpt35_cost < gpt4_cost  # GPT-3.5 should be cheaper
    
    def test_estimate_monthly_cost(self):
        """Test monthly cost estimation."""
        service = TokenAnalyticsService(MockTokenUsageRepository())
        
        # Estimate based on daily usage
        daily_tokens = 10000
        daily_requests = 100
        avg_cost_per_request = 0.05
        
        monthly_estimate = service.estimate_monthly_cost(
            daily_tokens=daily_tokens,
            daily_requests=daily_requests,
            avg_cost_per_request=avg_cost_per_request
        )
        
        # Should be approximately daily_requests * avg_cost * 30 days
        expected_estimate = 100 * 0.05 * 30  # $150
        assert abs(monthly_estimate - expected_estimate) < 10  # Allow some variance
