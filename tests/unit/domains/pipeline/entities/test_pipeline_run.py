"""Unit tests for PipelineRun entity.

Tests entity behavior, state transitions, and business rules for the pipeline run domain entity.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.execution_status import (
    ExecutionStatus,
    PipelineExecutionStatus
)


class TestPipelineRun:
    """Test PipelineRun entity behavior and validation."""
    
    def test_create_minimal_pipeline_run(self):
        """Test creating a minimal valid pipeline run."""
        pipeline_id = PipelineId("test-pipeline")
        
        run = PipelineRun(
            id="run-123",
            pipeline_id=pipeline_id,
            workspace_name="test-workspace",
            status=ExecutionStatus.created()
        )
        
        assert run.id == "run-123"
        assert run.pipeline_id == pipeline_id
        assert run.workspace_name == "test-workspace"
        assert run.status.status == PipelineExecutionStatus.CREATED
        assert isinstance(run.created_at, datetime)
        assert run.started_at is None
        assert run.completed_at is None
        assert len(run.inputs) == 0
        assert len(run.outputs) == 0
        assert run.error is None
    
    def test_create_pipeline_run_with_inputs(self):
        """Test creating pipeline run with inputs."""
        pipeline_id = PipelineId("article-pipeline")
        inputs = {"topic": "AI ethics", "style": "formal"}
        
        run = PipelineRun(
            id="run-456",
            pipeline_id=pipeline_id,
            workspace_name="my-project",
            status=ExecutionStatus.created(),
            inputs=inputs
        )
        
        assert run.inputs == inputs
        assert run.get_input("topic") == "AI ethics"
        assert run.get_input("style") == "formal"
        assert run.get_input("nonexistent") is None
        assert run.get_input("nonexistent", "default") == "default"
    
    def test_invalid_pipeline_run_id_raises_error(self):
        """Test that empty run ID raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline run id must be a non-empty string"):
            PipelineRun(
                id="",  # Empty ID
                pipeline_id=PipelineId("test"),
                workspace_name="test",
                status=ExecutionStatus.created()
            )
    
    def test_invalid_pipeline_id_type_raises_error(self):
        """Test that invalid pipeline ID type raises TypeError."""
        with pytest.raises(TypeError, match="Pipeline id must be a PipelineId"):
            PipelineRun(
                id="run-123",
                pipeline_id="invalid",  # Should be PipelineId
                workspace_name="test",
                status=ExecutionStatus.created()
            )
    
    def test_empty_workspace_name_raises_error(self):
        """Test that empty workspace name raises ValueError."""
        with pytest.raises(ValueError, match="Workspace name must be a non-empty string"):
            PipelineRun(
                id="run-123",
                pipeline_id=PipelineId("test"),
                workspace_name="",  # Empty workspace
                status=ExecutionStatus.created()
            )
    
    def test_invalid_status_type_raises_error(self):
        """Test that invalid status type raises TypeError."""
        with pytest.raises(TypeError, match="Status must be an ExecutionStatus"):
            PipelineRun(
                id="run-123",
                pipeline_id=PipelineId("test"),
                workspace_name="test",
                status="invalid"  # Should be ExecutionStatus
            )
    
    def test_active_run_without_started_at_raises_error(self):
        """Test that active run without started_at raises ValueError."""
        with pytest.raises(ValueError, match="Active pipeline run must have started_at set"):
            PipelineRun(
                id="run-123",
                pipeline_id=PipelineId("test"),
                workspace_name="test",
                status=ExecutionStatus.running(),
                started_at=None  # Active but no started_at
            )
    
    def test_terminal_run_without_completed_at_raises_error(self):
        """Test that completed run without completed_at raises ValueError."""
        start_time = datetime.now()
        completed_status = ExecutionStatus.created().transition_to(PipelineExecutionStatus.RUNNING).transition_to(PipelineExecutionStatus.COMPLETED)
        with pytest.raises(ValueError, match="Completed pipeline run must have completed_at set"):
            PipelineRun(
                id="run-123",
                pipeline_id=PipelineId("test"),
                workspace_name="test",
                status=completed_status,
                started_at=start_time,
                completed_at=None  # Completed but no completed_at
            )
    
    def test_failed_run_without_error_raises_error(self):
        """Test that failed run without error message raises ValueError."""
        start_time = datetime.now()
        with pytest.raises(ValueError, match="Failed pipeline run must have error message"):
            PipelineRun(
                id="run-123",
                pipeline_id=PipelineId("test"),
                workspace_name="test",
                status=ExecutionStatus.failed("Test error"),
                started_at=start_time,
                completed_at=datetime.now(),
                error=""  # Failed but no error message
            )
    
    def test_pipeline_run_properties(self):
        """Test pipeline run state properties."""
        # Created run
        created_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        
        assert created_run.is_running is False
        assert created_run.is_completed is False
        assert created_run.is_failed is False
        assert created_run.is_cancelled is False
        
        # Running run
        running_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        assert running_run.is_running is True
        assert running_run.is_completed is False
        assert running_run.is_failed is False
        assert running_run.is_cancelled is False
        
        # Completed run
        start_time = datetime.now()
        completed_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.completed(),
            started_at=start_time,
            completed_at=datetime.now()
        )
        
        assert completed_run.is_running is False
        assert completed_run.is_completed is True
        assert completed_run.is_failed is False
        assert completed_run.is_cancelled is False
        
        # Failed run
        failed_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.failed("Error"),
            started_at=start_time,
            completed_at=datetime.now(),
            error="Error"
        )
        
        assert failed_run.is_running is False
        assert failed_run.is_completed is False
        assert failed_run.is_failed is True
        assert failed_run.is_cancelled is False
        
        # Cancelled run
        cancelled_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.cancelled(),
            completed_at=datetime.now()
        )
        
        assert cancelled_run.is_running is False
        assert cancelled_run.is_completed is False
        assert cancelled_run.is_failed is False
        assert cancelled_run.is_cancelled is True
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        start_time = datetime.now()
        
        # Not started run
        not_started = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        assert not_started.duration is None
        
        # Running run
        running_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=start_time
        )
        duration = running_run.duration
        assert duration is not None
        assert duration >= 0
        
        # Completed run
        end_time = start_time + timedelta(seconds=30)
        completed_run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.completed(),
            started_at=start_time,
            completed_at=end_time
        )
        assert completed_run.duration == 30.0
    
    def test_start_pipeline_run(self):
        """Test starting a pipeline run."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        
        started_run = run.start()
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.CREATED
        assert run.started_at is None
        
        # New run has updated state
        assert started_run.status.status == PipelineExecutionStatus.RUNNING
        assert started_run.started_at is not None
        assert isinstance(started_run.started_at, datetime)
    
    def test_start_already_started_run_raises_error(self):
        """Test that starting already started run raises ValueError."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Pipeline run is already started"):
            run.start()
    
    def test_pause_running_pipeline(self):
        """Test pausing a running pipeline."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        paused_run = run.pause()
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.RUNNING
        
        # New run has paused status
        assert paused_run.status.status == PipelineExecutionStatus.PAUSED
    
    def test_pause_non_running_pipeline_raises_error(self):
        """Test that pausing non-running pipeline raises ValueError."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        
        with pytest.raises(ValueError, match="Can only pause running pipeline"):
            run.pause()
    
    def test_resume_paused_pipeline(self):
        """Test resuming a paused pipeline."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.paused(),
            started_at=datetime.now()
        )
        
        resumed_run = run.resume()
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.PAUSED
        
        # New run has running status
        assert resumed_run.status.status == PipelineExecutionStatus.RUNNING
    
    def test_resume_non_paused_pipeline_raises_error(self):
        """Test that resuming non-paused pipeline raises ValueError."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Can only resume paused pipeline"):
            run.resume()
    
    def test_complete_running_pipeline(self):
        """Test completing a running pipeline."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        outputs = {"article": "Generated article content"}
        completed_run = run.complete(outputs)
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.RUNNING
        assert len(run.outputs) == 0
        assert run.completed_at is None
        
        # New run has completed state
        assert completed_run.status.status == PipelineExecutionStatus.COMPLETED
        assert completed_run.outputs == outputs
        assert completed_run.completed_at is not None
        assert isinstance(completed_run.completed_at, datetime)
    
    def test_complete_non_active_pipeline_raises_error(self):
        """Test that completing non-active pipeline raises ValueError."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        
        with pytest.raises(ValueError, match="Can only complete active pipeline"):
            run.complete()
    
    def test_fail_pipeline_run(self):
        """Test failing a pipeline run."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        error_message = "Step failed due to validation error"
        failed_run = run.fail(error_message)
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.RUNNING
        assert run.error is None
        assert run.completed_at is None
        
        # New run has failed state
        assert failed_run.status.status == PipelineExecutionStatus.FAILED
        assert failed_run.error == error_message
        assert failed_run.completed_at is not None
        assert isinstance(failed_run.completed_at, datetime)
    
    def test_cancel_pipeline_run(self):
        """Test cancelling a pipeline run."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        cancelled_run = run.cancel()
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.RUNNING
        assert run.completed_at is None
        
        # New run has cancelled state
        assert cancelled_run.status.status == PipelineExecutionStatus.CANCELLED
        assert cancelled_run.completed_at is not None
        assert isinstance(cancelled_run.completed_at, datetime)
    
    def test_update_status(self):
        """Test updating pipeline status with valid status that doesn't require constraints."""
        # Start with a paused run (which has started_at set)
        paused_status = ExecutionStatus.created().transition_to(PipelineExecutionStatus.RUNNING).transition_to(PipelineExecutionStatus.PAUSED)
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=paused_status,
            started_at=datetime.now()
        )
        
        # Update to a different compatible status
        new_status = ExecutionStatus.created()
        updated_run = run.update_status(new_status)
        
        # Original run unchanged
        assert run.status.status == PipelineExecutionStatus.PAUSED
        
        # New run has updated status
        assert updated_run.status.status == PipelineExecutionStatus.CREATED
    
    def test_update_status_invalid_type_raises_error(self):
        """Test that updating status with invalid type raises TypeError."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        
        with pytest.raises(TypeError, match="Status must be an ExecutionStatus"):
            run.update_status("invalid")
    
    def test_update_metadata(self):
        """Test updating pipeline metadata."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created(),
            metadata={"version": "1.0", "mode": "test"}
        )
        
        new_metadata = {"user": "test_user", "mode": "prod"}
        updated_run = run.update_metadata(new_metadata)
        
        # Original run unchanged
        assert run.metadata == {"version": "1.0", "mode": "test"}
        
        # New run has merged metadata
        expected_metadata = {"version": "1.0", "mode": "prod", "user": "test_user"}
        assert updated_run.metadata == expected_metadata
    
    def test_add_token_usage(self):
        """Test adding token usage."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created(),
            total_tokens_used={"openai": 100}
        )
        
        # Add tokens for existing provider
        updated_run = run.add_token_usage("openai", 50)
        assert updated_run.total_tokens_used["openai"] == 150
        assert run.total_tokens_used["openai"] == 100  # Original unchanged
        
        # Add tokens for new provider
        updated_run2 = updated_run.add_token_usage("anthropic", 200)
        assert updated_run2.total_tokens_used["openai"] == 150
        assert updated_run2.total_tokens_used["anthropic"] == 200
    
    def test_update_execution_time(self):
        """Test updating execution time."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created(),
            total_execution_time=10.5
        )
        
        updated_run = run.update_execution_time(5.2)
        
        # Original run unchanged
        assert run.total_execution_time == 10.5
        
        # New run has updated time
        assert updated_run.total_execution_time == 15.7
    
    def test_set_outputs(self):
        """Test setting pipeline outputs."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created()
        )
        
        outputs = {"result": "success", "data": {"count": 42}}
        updated_run = run.set_outputs(outputs)
        
        # Original run unchanged
        assert len(run.outputs) == 0
        
        # New run has outputs
        assert updated_run.outputs == outputs
        assert updated_run.get_output("result") == "success"
        assert updated_run.get_output("data") == {"count": 42}
        assert updated_run.get_output("nonexistent") is None
        assert updated_run.get_output("nonexistent", "default") == "default"
    
    def test_get_total_tokens(self):
        """Test getting total tokens used."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.created(),
            total_tokens_used={"openai": 150, "anthropic": 200, "groq": 75}
        )
        
        assert run.get_total_tokens() == 425
    
    def test_create_factory_method(self):
        """Test creating pipeline run using factory method."""
        pipeline_id = PipelineId("test-pipeline")
        inputs = {"topic": "AI", "style": "formal"}
        metadata = {"version": "1.0"}
        
        run = PipelineRun.create(
            id="custom-run",
            pipeline_id=pipeline_id,
            pipeline_name="Test Pipeline",
            workspace_name="my-workspace",
            inputs=inputs,
            metadata=metadata
        )
        
        assert run.id == "custom-run"
        assert run.pipeline_id == pipeline_id
        assert run.pipeline_name == "Test Pipeline"
        assert run.workspace_name == "my-workspace"
        assert run.inputs == inputs
        assert run.metadata == metadata
        assert run.status.status == PipelineExecutionStatus.CREATED
        assert isinstance(run.created_at, datetime)
    
    def test_create_with_auto_generated_id(self):
        """Test creating pipeline run with auto-generated ID."""
        pipeline_id = PipelineId("test-pipeline")
        
        run = PipelineRun.create(
            id="",  # Empty ID should generate one
            pipeline_id=pipeline_id,
            workspace_name="test"
        )
        
        assert run.id.startswith("run-")
        assert len(run.id) == 12  # "run-" + 8 hex chars
    
    def test_create_retry_run(self):
        """Test creating a retry pipeline run."""
        original_run = PipelineRun.create(
            id="original-run",
            pipeline_id=PipelineId("test-pipeline"),
            workspace_name="test",
            inputs={"topic": "AI"},
            metadata={"attempt": 1}
        )
        
        retry_run = PipelineRun.create_retry(
            id="retry-run",
            original_run=original_run,
            from_step=StepId("failed-step"),
            skip_failed_steps=True
        )
        
        assert retry_run.id == "retry-run"
        assert retry_run.pipeline_id == original_run.pipeline_id
        assert retry_run.workspace_name == original_run.workspace_name
        assert retry_run.inputs == original_run.inputs
        
        # Check retry metadata
        assert retry_run.metadata["retry_of"] == "original-run"
        assert retry_run.metadata["from_step"] == "failed-step"
        assert retry_run.metadata["skip_failed_steps"] is True
        assert retry_run.metadata["attempt"] == 1  # Original metadata preserved
    
    def test_complete_execution_with_results(self):
        """Test completing execution with results."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        results = {"output": "Generated content"}
        metrics = {"tokens": 100, "time": 30.5}
        
        completed_run = run.complete_execution(
            results=results,
            metrics=metrics
        )
        
        assert completed_run.status.status == PipelineExecutionStatus.COMPLETED
        assert completed_run.outputs == results
        assert completed_run.metadata["tokens"] == 100
        assert completed_run.metadata["time"] == 30.5
    
    def test_cancel_execution_with_reason(self):
        """Test cancelling execution with reason."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        reason = "User requested cancellation"
        cancelled_run = run.cancel_execution(reason)
        
        assert cancelled_run.status.status == PipelineExecutionStatus.CANCELLED
        assert cancelled_run.metadata["cancel_reason"] == reason
    
    def test_fail_execution_with_step_info(self):
        """Test failing execution with step information."""
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test"),
            workspace_name="test",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        error_message = "Validation failed"
        failed_step = StepId("validation-step")
        step_results = {"partial": "output"}
        
        failed_run = run.fail_execution(
            error_message=error_message,
            failed_step=failed_step,
            step_results=step_results
        )
        
        assert failed_run.status.status == PipelineExecutionStatus.FAILED
        assert failed_run.error == error_message
        assert failed_run.outputs == step_results
        assert failed_run.metadata["failed_step"] == "validation-step"
    
    def test_from_template_factory(self):
        """Test creating run from template."""
        pipeline_id = PipelineId("template-pipeline")
        workspace_name = "my-workspace"
        template_inputs = {"topic": "Machine Learning", "length": "long"}
        metadata = {"source": "template"}
        
        run = PipelineRun.from_template(
            pipeline_id=pipeline_id,
            workspace_name=workspace_name,
            template_inputs=template_inputs,
            metadata=metadata
        )
        
        assert run.pipeline_id == pipeline_id
        assert run.workspace_name == workspace_name
        assert run.inputs == template_inputs
        assert run.metadata == metadata
        assert run.status.status == PipelineExecutionStatus.CREATED
    
    def test_to_dict_serialization(self):
        """Test converting pipeline run to dictionary."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=30)
        
        run = PipelineRun(
            id="run-123",
            pipeline_id=PipelineId("test-pipeline"),
            pipeline_name="Test Pipeline",
            workspace_name="test-workspace",
            status=ExecutionStatus.completed(),
            inputs={"topic": "AI"},
            outputs={"result": "success"},
            started_at=start_time,
            completed_at=end_time,
            metadata={"version": "1.0"},
            total_tokens_used={"openai": 100},
            total_execution_time=30.5
        )
        
        result_dict = run.to_dict()
        
        assert result_dict["id"] == "run-123"
        assert result_dict["pipeline_id"] == "test-pipeline"
        assert result_dict["pipeline_name"] == "Test Pipeline"
        assert result_dict["workspace_name"] == "test-workspace"
        assert result_dict["status"] == "completed"
        assert result_dict["inputs"] == {"topic": "AI"}
        assert result_dict["outputs"] == {"result": "success"}
        assert result_dict["started_at"] == start_time.isoformat()
        assert result_dict["completed_at"] == end_time.isoformat()
        assert result_dict["error"] is None
        assert result_dict["metadata"] == {"version": "1.0"}
        assert result_dict["total_tokens_used"] == {"openai": 100}
        assert result_dict["total_execution_time"] == 30.5
    
    def test_string_representations(self):
        """Test string and repr methods."""
        run = PipelineRun(
            id="run-test-123",
            pipeline_id=PipelineId("test-pipeline"),
            workspace_name="test-workspace",
            status=ExecutionStatus.running(),
            started_at=datetime.now()
        )
        
        str_repr = str(run)
        assert "run-test-123" in str_repr
        assert "running" in str_repr
        
        debug_repr = repr(run)
        assert "PipelineRun" in debug_repr
        assert "run-test-123" in debug_repr
        assert "test-pipeline" in debug_repr
        assert "running" in debug_repr
        assert "test-workspace" in debug_repr