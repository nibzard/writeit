# ABOUTME: Unit tests for token usage tracking functionality

from datetime import datetime
from unittest.mock import Mock
from writeit.llm.token_usage import (
    TokenUsage, 
    PipelineRunTokens, 
    TokenUsageTracker
)


class TestTokenUsage:
    """Test TokenUsage model and methods."""
    
    def test_token_usage_creation(self):
        """Test creating a TokenUsage instance."""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )
        
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150
        assert usage.details is None
        assert usage.cost_estimate is None
    
    def test_token_usage_from_llm_response(self):
        """Test creating TokenUsage from mock LLM response."""
        # Mock response with usage data
        mock_usage = Mock()
        mock_usage.input = 75
        mock_usage.output = 25
        mock_usage.details = {"model": "test-model"}
        
        mock_response = Mock()
        mock_response.usage.return_value = mock_usage
        
        usage = TokenUsage.from_llm_response(mock_response)
        
        assert usage.input_tokens == 75
        assert usage.output_tokens == 25
        assert usage.total_tokens == 100
        assert usage.details == {"model": "test-model"}
    
    def test_token_usage_from_llm_response_fallback(self):
        """Test fallback when LLM response doesn't have usage."""
        mock_response = Mock()
        mock_response.usage.side_effect = AttributeError("No usage method")
        
        usage = TokenUsage.from_llm_response(mock_response)
        
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0


class TestPipelineRunTokens:
    """Test PipelineRunTokens aggregation."""
    
    def test_pipeline_run_creation(self):
        """Test creating a pipeline run."""
        run = PipelineRunTokens(
            pipeline_name="Test Pipeline",
            run_id="test-123",
            start_time=datetime.now()
        )
        
        assert run.pipeline_name == "Test Pipeline"
        assert run.run_id == "test-123"
        assert run.total_input_tokens == 0
        assert run.total_output_tokens == 0
        assert run.total_tokens == 0
        assert len(run.steps) == 0
    
    def test_add_step_usage(self):
        """Test adding step usage to a pipeline run."""
        run = PipelineRunTokens(
            pipeline_name="Test Pipeline",
            run_id="test-123",
            start_time=datetime.now()
        )
        
        # Mock response
        mock_usage = Mock()
        mock_usage.input = 50
        mock_usage.output = 30
        
        mock_response = Mock()
        mock_response.usage.return_value = mock_usage
        
        step_usage = run.add_step_usage(
            step_key="step1",
            step_name="Test Step",
            model_name="test-model",
            response=mock_response
        )
        
        assert len(run.steps) == 1
        assert step_usage.step_key == "step1"
        assert step_usage.step_name == "Test Step"
        assert step_usage.model_name == "test-model"
        assert step_usage.usage.input_tokens == 50
        assert step_usage.usage.output_tokens == 30
        assert step_usage.regeneration_count == 0
        
        # Test totals
        assert run.total_input_tokens == 50
        assert run.total_output_tokens == 30
        assert run.total_tokens == 80
    
    def test_regeneration_tracking(self):
        """Test that step regeneration is tracked correctly."""
        run = PipelineRunTokens(
            pipeline_name="Test Pipeline", 
            run_id="test-123",
            start_time=datetime.now()
        )
        
        # Mock response
        mock_usage = Mock()
        mock_usage.input = 50
        mock_usage.output = 30
        mock_response = Mock()
        mock_response.usage.return_value = mock_usage
        
        # First execution
        step1 = run.add_step_usage("step1", "Test Step", "model", mock_response)
        assert step1.regeneration_count == 0
        assert len(run.steps) == 1
        
        # Regeneration (same step key)
        step2 = run.add_step_usage("step1", "Test Step", "model", mock_response) 
        assert step2.regeneration_count == 1
        assert len(run.steps) == 1  # Should replace, not add new
    
    def test_by_model_aggregation(self):
        """Test grouping token usage by model."""
        run = PipelineRunTokens(
            pipeline_name="Test Pipeline",
            run_id="test-123", 
            start_time=datetime.now()
        )
        
        # Add usage for different models
        mock_response = Mock()
        
        # Model A: 50 input, 30 output
        mock_usage_a = Mock()
        mock_usage_a.input = 50
        mock_usage_a.output = 30
        mock_response.usage.return_value = mock_usage_a
        run.add_step_usage("step1", "Step 1", "model-a", mock_response)
        
        # Model B: 100 input, 60 output  
        mock_usage_b = Mock()
        mock_usage_b.input = 100
        mock_usage_b.output = 60
        mock_response.usage.return_value = mock_usage_b
        run.add_step_usage("step2", "Step 2", "model-b", mock_response)
        
        # Another step with Model A: 25 input, 15 output
        mock_usage_a2 = Mock() 
        mock_usage_a2.input = 25
        mock_usage_a2.output = 15
        mock_response.usage.return_value = mock_usage_a2
        run.add_step_usage("step3", "Step 3", "model-a", mock_response)
        
        by_model = run.by_model
        
        assert len(by_model) == 2
        assert by_model["model-a"].input_tokens == 75  # 50 + 25
        assert by_model["model-a"].output_tokens == 45  # 30 + 15
        assert by_model["model-b"].input_tokens == 100
        assert by_model["model-b"].output_tokens == 60
    
    def test_to_dict(self):
        """Test converting pipeline run to dictionary."""
        start_time = datetime.now()
        run = PipelineRunTokens(
            pipeline_name="Test Pipeline",
            run_id="test-123",
            start_time=start_time
        )
        
        mock_usage = Mock()
        mock_usage.input = 50
        mock_usage.output = 30
        mock_response = Mock()
        mock_response.usage.return_value = mock_usage
        
        run.add_step_usage("step1", "Test Step", "model", mock_response)
        run.finish_run()
        
        data = run.to_dict()
        
        assert data["pipeline_name"] == "Test Pipeline"
        assert data["run_id"] == "test-123"
        assert data["total_input_tokens"] == 50
        assert data["total_output_tokens"] == 30
        assert data["total_tokens"] == 80
        assert len(data["steps"]) == 1
        assert data["by_model"]["model"]["input_tokens"] == 50
        assert data["start_time"] == start_time.isoformat()
        assert data["end_time"] is not None


class TestTokenUsageTracker:
    """Test TokenUsageTracker functionality."""
    
    def test_start_pipeline_run(self):
        """Test starting a pipeline run."""
        tracker = TokenUsageTracker()
        
        run = tracker.start_pipeline_run("Test Pipeline", "run-123")
        
        assert tracker.current_run is not None
        assert tracker.current_run.pipeline_name == "Test Pipeline"
        assert tracker.current_run.run_id == "run-123"
        assert run == tracker.current_run
    
    def test_track_step_usage(self):
        """Test tracking step usage."""
        tracker = TokenUsageTracker()
        tracker.start_pipeline_run("Test Pipeline", "run-123")
        
        mock_usage = Mock()
        mock_usage.input = 40
        mock_usage.output = 20
        mock_response = Mock()
        mock_response.usage.return_value = mock_usage
        
        step_usage = tracker.track_step_usage(
            "step1", "Test Step", "model", mock_response
        )
        
        assert step_usage is not None
        assert step_usage.step_key == "step1"
        assert len(tracker.current_run.steps) == 1
    
    def test_finish_current_run(self):
        """Test finishing a pipeline run."""
        tracker = TokenUsageTracker()
        tracker.start_pipeline_run("Test Pipeline", "run-123")
        
        finished_run = tracker.finish_current_run()
        
        assert finished_run is not None
        assert finished_run.end_time is not None
        assert tracker.current_run is None
        assert len(tracker.completed_runs) == 1
    
    def test_get_total_usage(self):
        """Test getting total usage across runs."""
        tracker = TokenUsageTracker()
        
        # First run
        tracker.start_pipeline_run("Pipeline A", "run-1")
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.input = 50
        mock_usage.output = 30
        mock_response.usage.return_value = mock_usage
        tracker.track_step_usage("step1", "Step 1", "model", mock_response)
        tracker.finish_current_run()
        
        # Second run  
        tracker.start_pipeline_run("Pipeline B", "run-2")
        mock_usage.input = 25
        mock_usage.output = 15
        mock_response.usage.return_value = mock_usage
        tracker.track_step_usage("step1", "Step 1", "model", mock_response)
        tracker.finish_current_run()
        
        totals = tracker.get_total_usage()
        
        assert totals["total_input_tokens"] == 75
        assert totals["total_output_tokens"] == 45
        assert totals["total_tokens"] == 120
        assert totals["completed_runs"] == 2
