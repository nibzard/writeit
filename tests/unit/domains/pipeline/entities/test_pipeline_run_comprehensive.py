"""Comprehensive unit tests for PipelineRun entity."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from src.writeit.domains.pipeline.entities.step_execution import StepExecution
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus

from tests.builders.pipeline_builders import PipelineRunBuilder, StepExecutionBuilder


class TestPipelineRun:
    """Test cases for PipelineRun entity."""
    
    def test_pipeline_run_creation_with_valid_data(self):
        """Test creating a pipeline run with valid data."""
        run = PipelineRunBuilder.pending().build()
        
        assert run.id == "pending_run"
        assert isinstance(run.pipeline_template_id, PipelineId)
        assert run.workspace_name == "test_workspace"
        assert run.status == ExecutionStatus.PENDING
        assert run.inputs == {}
        assert run.step_executions == {}
        assert run.execution_plan == []
        assert run.results == {}
        assert run.error is None
        assert isinstance(run.created_at, datetime)
        assert isinstance(run.updated_at, datetime)
    
    def test_pipeline_run_creation_with_custom_data(self):
        """Test creating a pipeline run with custom data."""
        inputs = {"topic": "Test Topic", "style": "professional"}
        execution_plan = ["outline", "content", "review"]
        
        run = (PipelineRunBuilder
               .pending("custom_run")
               .with_pipeline_template_id("custom_pipeline")
               .with_workspace("custom_workspace")
               .with_inputs(inputs)
               .with_execution_plan(execution_plan)
               .build())
        
        assert run.id == "custom_run"
        assert run.pipeline_template_id.value == "custom_pipeline"
        assert run.workspace_name == "custom_workspace"
        assert run.inputs == inputs
        assert run.execution_plan == execution_plan
    
    def test_pipeline_run_status_transitions(self):
        """Test pipeline run status transitions."""
        # Start with pending
        run = PipelineRunBuilder.pending().build()
        assert run.status == ExecutionStatus.PENDING
        assert run.started_at is None
        assert run.completed_at is None
        
        # Transition to running
        running_run = PipelineRunBuilder.running().build()
        assert running_run.status == ExecutionStatus.RUNNING
        assert running_run.started_at is not None
        assert running_run.completed_at is None
        
        # Transition to completed
        completed_run = PipelineRunBuilder.completed().build()
        assert completed_run.status == ExecutionStatus.COMPLETED
        assert completed_run.completed_at is not None
        
        # Transition to failed
        failed_run = PipelineRunBuilder.failed("test_run", "Test error").build()
        assert failed_run.status == ExecutionStatus.FAILED
        assert failed_run.error == "Test error"
    
    def test_pipeline_run_with_step_executions(self):
        """Test pipeline run with step executions."""
        step_exec1 = StepExecutionBuilder.completed("step1", "Response 1").build()
        step_exec2 = StepExecutionBuilder.pending("step2").build()
        
        run = (PipelineRunBuilder
               .running("run_with_steps")
               .build())
        
        # Add step executions (simulating how they would be added during execution)
        run.step_executions["step1"] = step_exec1
        run.step_executions["step2"] = step_exec2
        
        assert len(run.step_executions) == 2
        assert "step1" in run.step_executions
        assert "step2" in run.step_executions
        assert run.step_executions["step1"].status == ExecutionStatus.COMPLETED
        assert run.step_executions["step2"].status == ExecutionStatus.PENDING
    
    def test_pipeline_run_current_step_tracking(self):
        """Test current step tracking."""
        run = (PipelineRunBuilder
               .running("step_tracking")
               .with_current_step("outline")
               .with_execution_plan(["outline", "content", "review"])
               .build())
        
        assert run.current_step == "outline"
        assert run.execution_plan == ["outline", "content", "review"]
    
    def test_pipeline_run_results_collection(self):
        """Test results collection."""
        results = {
            "outline": "1. Introduction\n2. Main Content\n3. Conclusion",
            "content": "Full article content here...",
            "final_output": "Complete article with outline and content"
        }
        
        run = (PipelineRunBuilder
               .completed("results_run")
               .with_results(results)
               .build())
        
        assert run.results == results
        assert "outline" in run.results
        assert "content" in run.results
        assert "final_output" in run.results
    
    def test_pipeline_run_metadata(self):
        """Test pipeline run metadata."""
        metadata = {
            "execution_time_ms": 5000,
            "token_count": 1500,
            "cost_estimate": 0.05,
            "model_used": "gpt-4o-mini"
        }
        
        run = (PipelineRunBuilder
               .completed("metadata_run")
               .with_metadata(metadata)
               .build())
        
        assert run.metadata == metadata
        assert run.metadata["execution_time_ms"] == 5000
        assert run.metadata["token_count"] == 1500
    
    def test_pipeline_run_error_handling(self):
        """Test error handling in pipeline run."""
        error_message = "LLM API connection failed"
        
        run = PipelineRunBuilder.failed("error_run", error_message).build()
        
        assert run.status == ExecutionStatus.FAILED
        assert run.error == error_message
        assert run.completed_at is None  # Failed runs don't have completion time
    
    def test_pipeline_run_workspace_isolation(self):
        """Test workspace isolation."""
        run1 = (PipelineRunBuilder
                .pending("run1")
                .with_workspace("workspace1")
                .build())
        
        run2 = (PipelineRunBuilder
                .pending("run2")
                .with_workspace("workspace2")
                .build())
        
        assert run1.workspace_name == "workspace1"
        assert run2.workspace_name == "workspace2"
        assert run1.workspace_name != run2.workspace_name
    
    def test_pipeline_run_timestamps(self):
        """Test pipeline run timestamps."""
        now = datetime.now()
        
        # Pending run
        pending_run = PipelineRunBuilder.pending().build()
        assert abs((pending_run.created_at - now).total_seconds()) < 1
        assert abs((pending_run.updated_at - now).total_seconds()) < 1
        assert pending_run.started_at is None
        assert pending_run.completed_at is None
        
        # Running run
        running_run = PipelineRunBuilder.running().build()
        assert running_run.started_at is not None
        assert abs((running_run.started_at - now).total_seconds()) < 1
        assert running_run.completed_at is None
        
        # Completed run
        completed_run = PipelineRunBuilder.completed().build()
        assert completed_run.completed_at is not None
        assert abs((completed_run.completed_at - now).total_seconds()) < 1
    
    def test_pipeline_run_input_validation(self):
        """Test that pipeline run stores input validation results."""
        # This would be populated by the pipeline executor after validation
        inputs = {"topic": "Valid Topic", "style": "professional"}
        
        run = (PipelineRunBuilder
               .pending("validated_run")
               .with_inputs(inputs)
               .build())
        
        assert run.inputs == inputs
        assert "topic" in run.inputs
        assert "style" in run.inputs
    
    def test_pipeline_run_execution_plan(self):
        """Test execution plan tracking."""
        plan = ["validate_inputs", "generate_outline", "write_content", "review_content"]
        
        run = (PipelineRunBuilder
               .pending("planned_run")
               .with_execution_plan(plan)
               .build())
        
        assert run.execution_plan == plan
        assert len(run.execution_plan) == 4
        assert run.execution_plan[0] == "validate_inputs"
        assert run.execution_plan[-1] == "review_content"


class TestPipelineRunBusinessLogic:
    """Test business logic and state management for PipelineRun."""
    
    def test_pipeline_run_state_consistency(self):
        """Test that pipeline run state is consistent."""
        # Running run should have started_at
        running_run = PipelineRunBuilder.running().build()
        assert running_run.status == ExecutionStatus.RUNNING
        assert running_run.started_at is not None
        assert running_run.completed_at is None
        assert running_run.error is None
        
        # Completed run should have completed_at
        completed_run = PipelineRunBuilder.completed().build()
        assert completed_run.status == ExecutionStatus.COMPLETED
        assert completed_run.completed_at is not None
        assert completed_run.error is None
        
        # Failed run should have error
        failed_run = PipelineRunBuilder.failed().build()
        assert failed_run.status == ExecutionStatus.FAILED
        assert failed_run.error is not None
    
    def test_pipeline_run_step_progression(self):
        """Test step progression tracking."""
        execution_plan = ["step1", "step2", "step3"]
        
        # Start with first step
        run = (PipelineRunBuilder
               .running("progression_test")
               .with_execution_plan(execution_plan)
               .with_current_step("step1")
               .build())
        
        assert run.current_step == "step1"
        assert run.execution_plan.index(run.current_step) == 0
        
        # Progress to second step
        run_step2 = (PipelineRunBuilder
                    .running("progression_test")
                    .with_execution_plan(execution_plan)
                    .with_current_step("step2")
                    .build())
        
        assert run_step2.current_step == "step2"
        assert run_step2.execution_plan.index(run_step2.current_step) == 1
    
    def test_pipeline_run_partial_results(self):
        """Test that partial results are tracked properly."""
        # Simulate a pipeline with intermediate results
        results = {
            "step1_output": "First step result",
            "step2_output": "Second step result"
        }
        
        run = (PipelineRunBuilder
               .running("partial_results")
               .with_results(results)
               .with_current_step("step3")
               .build())
        
        assert len(run.results) == 2
        assert "step1_output" in run.results
        assert "step2_output" in run.results
        assert run.current_step == "step3"  # Still processing
    
    def test_pipeline_run_error_context(self):
        """Test error context preservation."""
        error_msg = "Step 'generate_content' failed: API rate limit exceeded"
        
        run = (PipelineRunBuilder
               .failed("error_context", error_msg)
               .with_current_step("generate_content")
               .with_metadata({
                   "error_step": "generate_content",
                   "error_type": "rate_limit",
                   "retry_count": 3
               })
               .build())
        
        assert run.error == error_msg
        assert run.current_step == "generate_content"
        assert run.metadata["error_step"] == "generate_content"
        assert run.metadata["retry_count"] == 3
    
    def test_pipeline_run_workspace_context(self):
        """Test workspace context preservation."""
        run = (PipelineRunBuilder
               .pending("workspace_context")
               .with_workspace("project_alpha")
               .with_metadata({
                   "workspace_config": {"model": "gpt-4o", "temperature": 0.7},
                   "workspace_templates": ["template1", "template2"]
               })
               .build())
        
        assert run.workspace_name == "project_alpha"
        assert "workspace_config" in run.metadata
        assert "workspace_templates" in run.metadata
    
    def test_pipeline_run_resumability(self):
        """Test that pipeline run contains information for resumability."""
        # A partially completed run that could be resumed
        step_executions = {
            "step1": StepExecutionBuilder.completed("step1", "Result 1").build(),
            "step2": StepExecutionBuilder.failed("step2", "Temporary error").build()
        }
        
        run = (PipelineRunBuilder
               .failed("resumable_run", "Step 2 failed")
               .with_current_step("step2")
               .with_execution_plan(["step1", "step2", "step3"])
               .build())
        
        # Add the step executions
        run.step_executions.update(step_executions)
        
        assert run.current_step == "step2"
        assert len(run.execution_plan) == 3
        assert "step1" in run.step_executions
        assert "step2" in run.step_executions
        assert run.step_executions["step1"].status == ExecutionStatus.COMPLETED
        assert run.step_executions["step2"].status == ExecutionStatus.FAILED
    
    def test_pipeline_run_unique_identification(self):
        """Test that pipeline runs have unique identification."""
        run1 = PipelineRunBuilder.pending("unique_1").build()
        run2 = PipelineRunBuilder.pending("unique_2").build()
        
        assert run1.id != run2.id
        assert run1.created_at != run2.created_at  # Different creation times
    
    def test_pipeline_run_template_reference(self):
        """Test pipeline template reference integrity."""
        template_id = PipelineId.from_name("test_template")
        
        run = (PipelineRunBuilder
               .pending("template_ref")
               .with_pipeline_template_id(template_id)
               .build())
        
        assert run.pipeline_template_id == template_id
        assert isinstance(run.pipeline_template_id, PipelineId)
    
    def test_pipeline_run_immutable_history(self):
        """Test that pipeline run preserves execution history."""
        # Test that timestamps create an immutable history
        creation_time = datetime.now() - timedelta(minutes=10)
        start_time = creation_time + timedelta(minutes=2)
        
        run = (PipelineRunBuilder
               .running("history_test")
               .build())
        
        # Simulate timestamps
        run.created_at = creation_time
        run.started_at = start_time
        
        assert run.created_at < run.started_at
        # In a real implementation, these would be immutable after creation
    
    def test_pipeline_run_resource_tracking(self):
        """Test resource usage tracking in metadata."""
        resource_metadata = {
            "total_tokens": 2500,
            "estimated_cost": 0.075,
            "execution_time_seconds": 45,
            "api_calls": 8,
            "cache_hits": 3,
            "cache_misses": 5
        }
        
        run = (PipelineRunBuilder
               .completed("resource_tracking")
               .with_metadata(resource_metadata)
               .build())
        
        assert run.metadata["total_tokens"] == 2500
        assert run.metadata["estimated_cost"] == 0.075
        assert run.metadata["api_calls"] == 8
        assert run.metadata["cache_hits"] == 3