"""Unit tests for StepExecution entity.

Tests entity behavior, state transitions, and business rules for the step execution domain entity.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from writeit.domains.pipeline.entities.pipeline_step import StepExecution
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.step_name import StepName
from writeit.domains.pipeline.value_objects.execution_status import (
    ExecutionStatus,
    StepExecutionStatus
)


class TestStepExecution:
    """Test StepExecution entity behavior and validation."""
    
    def test_create_minimal_step_execution(self):
        """Test creating a minimal valid step execution."""
        step_id = StepId("outline")
        step_name = StepName("Create Outline")
        status = ExecutionStatus.step_pending()
        
        execution = StepExecution(
            step_id=step_id,
            step_name=step_name,
            status=status
        )
        
        assert execution.step_id == step_id
        assert execution.step_name == step_name
        assert execution.status == status
        assert len(execution.inputs) == 0
        assert len(execution.outputs) == 0
        assert execution.error_message is None
        assert execution.started_at is None
        assert execution.completed_at is None
        assert execution.execution_time == 0.0
        assert len(execution.tokens_used) == 0
        assert len(execution.metadata) == 0
        assert execution.retry_count == 0
        assert execution.max_retries == 3
    
    def test_create_step_execution_with_all_fields(self):
        """Test creating step execution with all fields specified."""
        step_id = StepId("content")
        step_name = StepName("Generate Content")
        status = ExecutionStatus.step_pending()
        inputs = {"topic": "AI Ethics", "style": "formal"}
        metadata = {"model": "gpt-4o-mini", "temperature": 0.7}
        
        execution = StepExecution(
            step_id=step_id,
            step_name=step_name,
            status=status,
            inputs=inputs,
            metadata=metadata,
            max_retries=5
        )
        
        assert execution.inputs == inputs
        assert execution.metadata == metadata
        assert execution.max_retries == 5
    
    def test_invalid_step_id_type_raises_error(self):
        """Test that invalid step ID type raises TypeError."""
        with pytest.raises(TypeError, match="Step id must be a StepId"):
            StepExecution(
                step_id="invalid",  # Should be StepId
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending()
            )
    
    def test_invalid_step_name_type_raises_error(self):
        """Test that invalid step name type raises TypeError."""
        with pytest.raises(TypeError, match="Step name must be a StepName"):
            StepExecution(
                step_id=StepId("test"),
                step_name="invalid",  # Should be StepName
                status=ExecutionStatus.step_pending()
            )
    
    def test_invalid_status_type_raises_error(self):
        """Test that invalid status type raises TypeError."""
        with pytest.raises(TypeError, match="Status must be an ExecutionStatus"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status="invalid"  # Should be ExecutionStatus
            )
    
    def test_invalid_inputs_type_raises_error(self):
        """Test that invalid inputs type raises TypeError."""
        with pytest.raises(TypeError, match="Inputs must be a dictionary"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                inputs="invalid"  # Should be dict
            )
    
    def test_invalid_outputs_type_raises_error(self):
        """Test that invalid outputs type raises TypeError."""
        with pytest.raises(TypeError, match="Outputs must be a dictionary"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                outputs="invalid"  # Should be dict
            )
    
    def test_negative_execution_time_raises_error(self):
        """Test that negative execution time raises ValueError."""
        with pytest.raises(ValueError, match="Execution time cannot be negative"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                execution_time=-1.0  # Negative time
            )
    
    def test_negative_retry_count_raises_error(self):
        """Test that negative retry count raises ValueError."""
        with pytest.raises(ValueError, match="Retry count cannot be negative"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                retry_count=-1  # Negative count
            )
    
    def test_negative_max_retries_raises_error(self):
        """Test that negative max retries raises ValueError."""
        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                max_retries=-1  # Negative max retries
            )
    
    def test_active_step_without_started_at_raises_error(self):
        """Test that active step without started_at raises ValueError."""
        running_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING)
        with pytest.raises(ValueError, match="Active step execution must have started_at set"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=running_status,
                started_at=None  # Active but no started_at
            )
    
    def test_terminal_step_without_completed_at_raises_error(self):
        """Test that completed step without completed_at raises ValueError."""
        completed_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING).transition_to(StepExecutionStatus.COMPLETED)
        start_time = datetime.now()
        with pytest.raises(ValueError, match="Completed step execution must have completed_at set"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=completed_status,
                started_at=start_time,
                completed_at=None  # Completed but no completed_at
            )
    
    def test_failed_step_without_error_raises_error(self):
        """Test that failed step without error message raises ValueError."""
        failed_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING).transition_to(StepExecutionStatus.FAILED, error_message="Test error")
        start_time = datetime.now()
        with pytest.raises(ValueError, match="Failed step execution must have error message"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=failed_status,
                started_at=start_time,
                completed_at=datetime.now(),
                error_message=""  # Failed but no error message
            )
    
    def test_step_execution_properties(self):
        """Test step execution state properties."""
        # Pending step
        pending_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=ExecutionStatus.step_pending()
        )
        
        assert pending_step.is_pending is True
        assert pending_step.is_running is False
        assert pending_step.is_completed is False
        assert pending_step.is_failed is False
        assert pending_step.is_skipped is False
        assert pending_step.is_cancelled is False
        
        # Running step
        running_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING)
        running_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=running_status,
            started_at=datetime.now()
        )
        
        assert running_step.is_pending is False
        assert running_step.is_running is True
        assert running_step.is_completed is False
        assert running_step.is_failed is False
        assert running_step.is_skipped is False
        assert running_step.is_cancelled is False
        
        # Completed step
        completed_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING).transition_to(StepExecutionStatus.COMPLETED)
        start_time = datetime.now()
        completed_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=completed_status,
            started_at=start_time,
            completed_at=datetime.now()
        )
        
        assert completed_step.is_pending is False
        assert completed_step.is_running is False
        assert completed_step.is_completed is True
        assert completed_step.is_failed is False
        assert completed_step.is_skipped is False
        assert completed_step.is_cancelled is False
        
        # Failed step
        failed_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING).transition_to(StepExecutionStatus.FAILED, error_message="Error")
        failed_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=failed_status,
            started_at=start_time,
            completed_at=datetime.now(),
            error_message="Error"
        )
        
        assert failed_step.is_pending is False
        assert failed_step.is_running is False
        assert failed_step.is_completed is False
        assert failed_step.is_failed is True
        assert failed_step.is_skipped is False
        assert failed_step.is_cancelled is False
        
        # Skipped step
        skipped_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.SKIPPED)
        skipped_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=skipped_status,
            completed_at=datetime.now()
        )
        
        assert skipped_step.is_pending is False
        assert skipped_step.is_running is False
        assert skipped_step.is_completed is True  # Skipped is considered successful
        assert skipped_step.is_failed is False
        assert skipped_step.is_skipped is True
        assert skipped_step.is_cancelled is False
        
        # Cancelled step
        cancelled_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.CANCELLED)
        cancelled_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=cancelled_status,
            completed_at=datetime.now()
        )
        
        assert cancelled_step.is_pending is False
        assert cancelled_step.is_running is False
        assert cancelled_step.is_completed is False
        assert cancelled_step.is_failed is False
        assert cancelled_step.is_skipped is False
        assert cancelled_step.is_cancelled is True
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        start_time = datetime.now()
        
        # Not started step
        not_started = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=ExecutionStatus.step_pending()
        )
        assert not_started.duration is None
        
        # Running step
        running_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING)
        running_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=running_status,
            started_at=start_time
        )
        duration = running_step.duration
        assert duration is not None
        assert duration >= 0
        
        # Completed step
        end_time = start_time + timedelta(seconds=15)
        completed_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING).transition_to(StepExecutionStatus.COMPLETED)
        completed_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=completed_status,
            started_at=start_time,
            completed_at=end_time
        )
        assert completed_step.duration == 15.0
    
    def test_can_retry(self):
        """Test retry capability checking."""
        # Failed step with no retries (can retry)
        failed_status = ExecutionStatus.step_pending().transition_to(StepExecutionStatus.RUNNING).transition_to(StepExecutionStatus.FAILED, error_message="Error")
        step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=failed_status,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message="Error",
            retry_count=0,
            max_retries=3
        )
        assert step.can_retry is True
        
        # Failed step at max retries (cannot retry)
        step_max = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=failed_status,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message="Error",
            retry_count=3,
            max_retries=3
        )
        assert step_max.can_retry is False
        
        # Failed step beyond max retries (cannot retry)
        step_over = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=failed_status,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message="Error",
            retry_count=5,
            max_retries=3
        )
        assert step_over.can_retry is False
        
        # Non-failed step cannot retry
        pending_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=ExecutionStatus.step_pending(),
            retry_count=0,
            max_retries=3
        )
        assert pending_step.can_retry is False
    
    def test_get_input_and_output(self):
        """Test getting inputs and outputs."""
        inputs = {"topic": "AI", "style": "formal"}
        outputs = {"content": "Generated content", "word_count": 500}
        
        step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=ExecutionStatus.step_pending(),
            inputs=inputs,
            outputs=outputs
        )
        
        # Test input access
        assert step.get_input("topic") == "AI"
        assert step.get_input("style") == "formal"
        assert step.get_input("nonexistent") is None
        assert step.get_input("nonexistent", "default") == "default"
        
        # Test output access
        assert step.get_output("content") == "Generated content"
        assert step.get_output("word_count") == 500
        assert step.get_output("nonexistent") is None
        assert step.get_output("nonexistent", "default") == "default"
    
    def test_get_total_tokens(self):
        """Test getting total tokens used."""
        step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=ExecutionStatus.step_pending(),
            tokens_used={"openai": 150, "anthropic": 200, "groq": 75}
        )
        
        assert step.get_total_tokens() == 425
        
        # Test with empty tokens
        empty_step = StepExecution(
            step_id=StepId("test"),
            step_name=StepName("Test"),
            status=ExecutionStatus.step_pending()
        )
        assert empty_step.get_total_tokens() == 0