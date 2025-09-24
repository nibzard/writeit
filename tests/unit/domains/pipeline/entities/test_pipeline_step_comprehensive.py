"""Comprehensive unit tests for Pipeline Step entities.

Tests entity behavior, state transitions, and business rules for
StepExecution and PipelineStep domain entities.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.writeit.domains.pipeline.entities.pipeline_step import (
    StepExecution, PipelineStep
)
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.step_name import StepName
from src.writeit.domains.pipeline.value_objects.execution_status import (
    ExecutionStatus, StepExecutionStatus
)
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from src.writeit.domains.pipeline.value_objects.model_preference import ModelPreference

from tests.builders.pipeline_builders import (
    StepExecutionBuilder, PipelineStepBuilder
)


class TestStepExecution:
    """Test cases for StepExecution entity."""
    
    def test_step_execution_creation_with_minimal_data(self):
        """Test creating step execution with minimal valid data."""
        execution = StepExecutionBuilder.pending().build()
        
        assert isinstance(execution.step_id, StepId)
        assert isinstance(execution.step_name, StepName)
        assert isinstance(execution.status, ExecutionStatus)
        assert execution.status.status == StepExecutionStatus.PENDING
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
    
    def test_step_execution_creation_with_all_fields(self):
        """Test creating step execution with all fields specified."""
        inputs = {"topic": "AI Ethics", "style": "formal"}
        outputs = {"content": "Generated content", "word_count": 500}
        tokens_used = {"openai": 150, "anthropic": 200}
        metadata = {"model": "gpt-4o-mini", "temperature": 0.7}
        
        execution = (StepExecutionBuilder
                    .pending()
                    .with_inputs(inputs)
                    .with_outputs(outputs)
                    .with_tokens_used(tokens_used)
                    .with_metadata(metadata)
                    .with_max_retries(5)
                    .build())
        
        assert execution.inputs == inputs
        assert execution.outputs == outputs
        assert execution.tokens_used == tokens_used
        assert execution.metadata == metadata
        assert execution.max_retries == 5
    
    def test_step_execution_invalid_types_raise_errors(self):
        """Test that invalid field types raise appropriate errors."""
        # Invalid step_id
        with pytest.raises(TypeError, match="Step id must be a StepId"):
            StepExecution(
                step_id="invalid",
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending()
            )
        
        # Invalid step_name
        with pytest.raises(TypeError, match="Step name must be a StepName"):
            StepExecution(
                step_id=StepId("test"),
                step_name="invalid",
                status=ExecutionStatus.step_pending()
            )
        
        # Invalid status
        with pytest.raises(TypeError, match="Status must be an ExecutionStatus"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status="invalid"
            )
        
        # Invalid inputs
        with pytest.raises(TypeError, match="Inputs must be a dictionary"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                inputs="invalid"
            )
        
        # Invalid outputs
        with pytest.raises(TypeError, match="Outputs must be a dictionary"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                outputs="invalid"
            )
    
    def test_step_execution_validation_rules(self):
        """Test validation rules for step execution."""
        # Negative execution time
        with pytest.raises(ValueError, match="Execution time cannot be negative"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                execution_time=-1.0
            )
        
        # Negative retry count
        with pytest.raises(ValueError, match="Retry count cannot be negative"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                retry_count=-1
            )
        
        # Negative max retries
        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            StepExecution(
                step_id=StepId("test"),
                step_name=StepName("Test"),
                status=ExecutionStatus.step_pending(),
                max_retries=-1
            )
    
    def test_step_execution_lifecycle_transitions(self):
        """Test complete step execution lifecycle."""
        # Start with pending
        execution = StepExecutionBuilder.pending().build()
        
        # Start execution
        started = execution.start({"topic": "AI Ethics"})
        assert started.is_running is True
        assert started.started_at is not None
        assert started.inputs["topic"] == "AI Ethics"
        
        # Complete execution
        completed = started.complete({"content": "Generated content"})
        assert completed.is_completed is True
        assert completed.completed_at is not None
        assert completed.outputs["content"] == "Generated content"
        assert completed.duration is not None
        assert completed.duration >= 0


class TestPipelineStep:
    """Test cases for PipelineStep entity."""
    
    def test_pipeline_step_creation_with_minimal_data(self):
        """Test creating pipeline step with minimal valid data."""
        step = PipelineStepBuilder.llm_step("test").build()
        
        assert isinstance(step.step_id, StepId)
        assert isinstance(step.name, StepName)
        assert isinstance(step.prompt_template, PromptTemplate)
        assert isinstance(step.model_preference, ModelPreference)
        assert step.step_type == "llm_generate"
        assert step.description != ""
        assert len(step.depends_on) == 0
        assert step.parallel is False
        assert step.timeout_seconds is None
        assert isinstance(step.retry_config, dict)
        assert isinstance(step.validation, dict)
        assert isinstance(step.ui_config, dict)
        assert isinstance(step.metadata, dict)
    
    def test_pipeline_step_type_properties(self):
        """Test step type property methods."""
        # LLM step
        llm_step = PipelineStepBuilder.llm_step("test").build()
        assert llm_step.is_llm_step is True
        assert llm_step.is_user_input_step is False
        assert llm_step.is_transform_step is False
        assert llm_step.is_validation_step is False
        assert llm_step.is_conditional_step is False
        
        # User input step
        user_step = PipelineStepBuilder.user_input_step("input").build()
        assert user_step.is_llm_step is False
        assert user_step.is_user_input_step is True


class TestPipelineStepBusinessRules:
    """Test business rules and invariants for Pipeline Step entities."""
    
    def test_step_execution_state_transitions_are_valid(self):
        """Test that state transitions follow valid state machine rules."""
        execution = StepExecutionBuilder.pending().build()
        
        # Valid transitions from pending
        assert execution.is_pending
        started = execution.start()
        assert started.is_running
        
        skipped = execution.skip()
        assert skipped.is_skipped
        
        cancelled = execution.cancel()
        assert cancelled.is_cancelled
    
    def test_step_execution_immutability(self):
        """Test that step executions follow immutability patterns."""
        original = StepExecutionBuilder.pending().build()
        
        # State transitions create new instances
        started = original.start()
        assert original is not started
        assert original.is_pending
        assert started.is_running