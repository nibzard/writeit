"""Unit tests for PipelineTemplate entity.

Tests entity behavior, validation, and business rules for the pipeline template domain entity.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from writeit.domains.pipeline.entities.pipeline_template import (
    PipelineTemplate,
    PipelineInput,
    PipelineStepTemplate
)
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference


class TestPipelineInput:
    """Test PipelineInput behavior and validation."""
    
    def test_create_valid_text_input(self):
        """Test creating a valid text input."""
        input_def = PipelineInput(
            key="topic",
            type="text",
            label="Article Topic",
            required=True,
            placeholder="Enter topic...",
            max_length=100
        )
        
        assert input_def.key == "topic"
        assert input_def.type == "text"
        assert input_def.label == "Article Topic"
        assert input_def.required is True
        assert input_def.placeholder == "Enter topic..."
        assert input_def.max_length == 100
    
    def test_create_valid_choice_input(self):
        """Test creating a valid choice input."""
        input_def = PipelineInput(
            key="style",
            type="choice",
            label="Writing Style",
            options=[
                {"label": "Formal", "value": "formal"},
                {"label": "Casual", "value": "casual"}
            ]
        )
        
        assert input_def.key == "style"
        assert input_def.type == "choice"
        assert len(input_def.options) == 2
    
    def test_invalid_input_key_raises_error(self):
        """Test that empty input key raises ValueError."""
        with pytest.raises(ValueError, match="Input key must be a non-empty string"):
            PipelineInput(key="", type="text", label="Test")
    
    def test_invalid_input_type_raises_error(self):
        """Test that invalid input type raises ValueError."""
        with pytest.raises(ValueError, match="Input type must be one of"):
            PipelineInput(key="test", type="invalid", label="Test")
    
    def test_choice_input_without_options_raises_error(self):
        """Test that choice input without options raises ValueError."""
        with pytest.raises(ValueError, match="Choice input must have options"):
            PipelineInput(key="choice", type="choice", label="Test Choice")
    
    def test_negative_max_length_raises_error(self):
        """Test that negative max length raises ValueError."""
        with pytest.raises(ValueError, match="Max length must be positive"):
            PipelineInput(key="text", type="text", label="Test", max_length=-1)
    
    def test_validate_text_value(self):
        """Test text value validation."""
        input_def = PipelineInput(
            key="topic",
            type="text",
            label="Topic",
            required=True,
            max_length=10
        )
        
        # Valid values
        assert input_def.validate_value("test") is True
        assert input_def.validate_value("1234567890") is True
        
        # Invalid values
        assert input_def.validate_value("") is False  # Required but empty
        assert input_def.validate_value(None) is False  # Required but None
        assert input_def.validate_value("12345678901") is False  # Too long
        assert input_def.validate_value(123) is False  # Wrong type
    
    def test_validate_choice_value(self):
        """Test choice value validation."""
        input_def = PipelineInput(
            key="style",
            type="choice",
            label="Style",
            options=[
                {"label": "Formal", "value": "formal"},
                {"label": "Casual", "value": "casual"}
            ]
        )
        
        # Valid values
        assert input_def.validate_value("formal") is True
        assert input_def.validate_value("casual") is True
        
        # Invalid values
        assert input_def.validate_value("invalid") is False
        assert input_def.validate_value("") is False
        assert input_def.validate_value(None) is True  # Not required
    
    def test_validate_number_value(self):
        """Test number value validation."""
        input_def = PipelineInput(key="count", type="number", label="Count")
        
        # Valid values
        assert input_def.validate_value("123") is True
        assert input_def.validate_value("123.45") is True
        assert input_def.validate_value(123) is True
        assert input_def.validate_value(123.45) is True
        
        # Invalid values
        assert input_def.validate_value("invalid") is False
        assert input_def.validate_value("") is False
    
    def test_validate_boolean_value(self):
        """Test boolean value validation."""
        input_def = PipelineInput(key="enabled", type="boolean", label="Enabled")
        
        # Valid values
        assert input_def.validate_value(True) is True
        assert input_def.validate_value(False) is True
        
        # Invalid values
        assert input_def.validate_value("true") is False
        assert input_def.validate_value(1) is False
        assert input_def.validate_value(0) is False


class TestPipelineStepTemplate:
    """Test PipelineStepTemplate behavior and validation."""
    
    def test_create_valid_step(self):
        """Test creating a valid pipeline step."""
        step_id = StepId("outline")
        prompt_template = PromptTemplate("Create outline for {{ topic }}")
        model_preference = ModelPreference(["gpt-4o-mini"])
        
        step = PipelineStepTemplate(
            id=step_id,
            name="Create Outline",
            description="Generate article outline",
            type="llm_generate",
            prompt_template=prompt_template,
            model_preference=model_preference
        )
        
        assert step.id == step_id
        assert step.name == "Create Outline"
        assert step.description == "Generate article outline"
        assert step.type == "llm_generate"
        assert step.prompt_template == prompt_template
        assert step.model_preference == model_preference
        assert step.depends_on == []
        assert step.parallel is False
    
    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        dep_id = StepId("outline")
        step_id = StepId("content")
        
        step = PipelineStepTemplate(
            id=step_id,
            name="Write Content",
            description="Generate article content",
            type="llm_generate",
            prompt_template=PromptTemplate("Write content based on {{ steps.outline }}"),
            depends_on=[dep_id]
        )
        
        assert step.depends_on == [dep_id]
        assert step.has_dependency(dep_id) is True
        assert step.has_dependency(StepId("other")) is False
    
    def test_invalid_step_id_type_raises_error(self):
        """Test that invalid step ID type raises TypeError."""
        with pytest.raises(TypeError, match="Step id must be a StepId"):
            PipelineStepTemplate(
                id="invalid",  # Should be StepId
                name="Test",
                description="Test step",
                type="llm_generate",
                prompt_template=PromptTemplate("test")
            )
    
    def test_empty_step_name_raises_error(self):
        """Test that empty step name raises ValueError."""
        with pytest.raises(ValueError, match="Step name must be a non-empty string"):
            PipelineStepTemplate(
                id=StepId("test"),
                name="",  # Empty name
                description="Test step",
                type="llm_generate",
                prompt_template=PromptTemplate("test")
            )
    
    def test_invalid_step_type_raises_error(self):
        """Test that invalid step type raises ValueError."""
        with pytest.raises(ValueError, match="Step type must be one of"):
            PipelineStepTemplate(
                id=StepId("test"),
                name="Test",
                description="Test step",
                type="invalid_type",  # Invalid type
                prompt_template=PromptTemplate("test")
            )
    
    def test_invalid_prompt_template_type_raises_error(self):
        """Test that invalid prompt template type raises TypeError."""
        with pytest.raises(TypeError, match="Prompt template must be a PromptTemplate"):
            PipelineStepTemplate(
                id=StepId("test"),
                name="Test",
                description="Test step",
                type="llm_generate",
                prompt_template="invalid"  # Should be PromptTemplate
            )
    
    def test_invalid_dependency_type_raises_error(self):
        """Test that invalid dependency type raises TypeError."""
        with pytest.raises(TypeError, match="Dependencies must be StepId instances"):
            PipelineStepTemplate(
                id=StepId("test"),
                name="Test",
                description="Test step",
                type="llm_generate",
                prompt_template=PromptTemplate("test"),
                depends_on=["invalid"]  # Should be StepId instances
            )
    
    def test_can_run_in_parallel(self):
        """Test parallel execution capability."""
        # Step with no dependencies can run in parallel if marked
        parallel_step = PipelineStepTemplate(
            id=StepId("parallel"),
            name="Parallel Step",
            description="Can run in parallel",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            parallel=True
        )
        assert parallel_step.can_run_in_parallel() is True
        
        # Step with dependencies cannot run in parallel
        dependent_step = PipelineStepTemplate(
            id=StepId("dependent"),
            name="Dependent Step",
            description="Has dependencies",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            parallel=True,
            depends_on=[StepId("other")]
        )
        assert dependent_step.can_run_in_parallel() is False
        
        # Step not marked as parallel cannot run in parallel
        serial_step = PipelineStepTemplate(
            id=StepId("serial"),
            name="Serial Step",
            description="Must run serially",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            parallel=False
        )
        assert serial_step.can_run_in_parallel() is False
    
    def test_get_required_variables(self):
        """Test getting required variables from prompt template."""
        step = PipelineStepTemplate(
            id=StepId("test"),
            name="Test",
            description="Test step",
            type="llm_generate",
            prompt_template=PromptTemplate("Write about {{ topic }} in {{ style }} style")
        )
        
        variables = step.get_required_variables()
        assert "topic" in variables
        assert "style" in variables


class TestPipelineTemplate:
    """Test PipelineTemplate entity behavior and validation."""
    
    def test_create_minimal_pipeline(self):
        """Test creating a minimal valid pipeline."""
        pipeline_id = PipelineId("test-pipeline")
        
        pipeline = PipelineTemplate(
            id=pipeline_id,
            name="Test Pipeline",
            description="A test pipeline"
        )
        
        assert pipeline.id == pipeline_id
        assert pipeline.name == "Test Pipeline"
        assert pipeline.description == "A test pipeline"
        assert pipeline.version == "1.0.0"
        assert len(pipeline.inputs) == 0
        assert len(pipeline.steps) == 0
    
    def test_create_pipeline_with_inputs_and_steps(self):
        """Test creating pipeline with inputs and steps."""
        pipeline_id = PipelineId("article-pipeline")
        
        # Create input
        topic_input = PipelineInput(
            key="topic",
            type="text",
            label="Article Topic",
            required=True
        )
        
        # Create step
        outline_step = PipelineStepTemplate(
            id=StepId("outline"),
            name="Create Outline",
            description="Generate article outline",
            type="llm_generate",
            prompt_template=PromptTemplate("Create outline for {{ inputs.topic }}")
        )
        
        pipeline = PipelineTemplate(
            id=pipeline_id,
            name="Article Pipeline",
            description="Generate articles",
            inputs={"topic": topic_input},
            steps={"outline": outline_step}
        )
        
        assert len(pipeline.inputs) == 1
        assert "topic" in pipeline.inputs
        assert len(pipeline.steps) == 1
        assert "outline" in pipeline.steps
    
    def test_invalid_pipeline_id_type_raises_error(self):
        """Test that invalid pipeline ID type raises TypeError."""
        with pytest.raises(TypeError, match="Pipeline id must be a PipelineId"):
            PipelineTemplate(
                id="invalid",  # Should be PipelineId
                name="Test",
                description="Test pipeline"
            )
    
    def test_empty_pipeline_name_raises_error(self):
        """Test that empty pipeline name raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline name must be a non-empty string"):
            PipelineTemplate(
                id=PipelineId("test"),
                name="",  # Empty name
                description="Test pipeline"
            )
    
    def test_input_key_mismatch_raises_error(self):
        """Test that input key mismatch raises ValueError."""
        topic_input = PipelineInput(key="topic", type="text", label="Topic")
        
        with pytest.raises(ValueError, match="Input key mismatch"):
            PipelineTemplate(
                id=PipelineId("test"),
                name="Test",
                description="Test pipeline",
                inputs={"wrong_key": topic_input}  # Key doesn't match input.key
            )
    
    def test_step_key_mismatch_raises_error(self):
        """Test that step key mismatch raises ValueError."""
        step = PipelineStepTemplate(
            id=StepId("outline"),
            name="Outline",
            description="Create outline",
            type="llm_generate",
            prompt_template=PromptTemplate("test")
        )
        
        with pytest.raises(ValueError, match="Step key mismatch"):
            PipelineTemplate(
                id=PipelineId("test"),
                name="Test",
                description="Test pipeline",
                steps={"wrong_key": step}  # Key doesn't match step.id.value
            )
    
    def test_nonexistent_dependency_raises_error(self):
        """Test that referencing non-existent step dependency raises ValueError."""
        step = PipelineStepTemplate(
            id=StepId("content"),
            name="Content",
            description="Generate content",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("nonexistent")]  # Dependency doesn't exist
        )
        
        with pytest.raises(ValueError, match="depends on non-existent step"):
            PipelineTemplate(
                id=PipelineId("test"),
                name="Test",
                description="Test pipeline",
                steps={"content": step}
            )
    
    def test_circular_dependency_raises_error(self):
        """Test that circular dependencies raise ValueError."""
        step_a = PipelineStepTemplate(
            id=StepId("step_a"),
            name="Step A",
            description="Step A",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("step_b")]
        )
        
        step_b = PipelineStepTemplate(
            id=StepId("step_b"),
            name="Step B",
            description="Step B",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("step_a")]  # Circular dependency
        )
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            PipelineTemplate(
                id=PipelineId("test"),
                name="Test",
                description="Test pipeline",
                steps={"step_a": step_a, "step_b": step_b}
            )
    
    def test_validate_inputs_success(self):
        """Test successful input validation."""
        topic_input = PipelineInput(key="topic", type="text", label="Topic", required=True)
        style_input = PipelineInput(
            key="style",
            type="choice",
            label="Style",
            options=[{"label": "Formal", "value": "formal"}]
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            inputs={"topic": topic_input, "style": style_input}
        )
        
        # Valid inputs
        errors = pipeline.validate_inputs({"topic": "Test Topic", "style": "formal"})
        assert len(errors) == 0
    
    def test_validate_inputs_missing_required(self):
        """Test input validation with missing required input."""
        topic_input = PipelineInput(key="topic", type="text", label="Topic", required=True)
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            inputs={"topic": topic_input}
        )
        
        # Missing required input
        errors = pipeline.validate_inputs({})
        assert len(errors) == 1
        assert "Required input 'topic' is missing" in errors
    
    def test_validate_inputs_invalid_value(self):
        """Test input validation with invalid value."""
        style_input = PipelineInput(
            key="style",
            type="choice",
            label="Style",
            options=[{"label": "Formal", "value": "formal"}]
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            inputs={"style": style_input}
        )
        
        # Invalid choice value
        errors = pipeline.validate_inputs({"style": "invalid"})
        assert len(errors) == 1
        assert "Invalid value for input 'style'" in errors
    
    def test_validate_inputs_unexpected_input(self):
        """Test input validation with unexpected input."""
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline"
        )
        
        # Unexpected input
        errors = pipeline.validate_inputs({"unexpected": "value"})
        assert len(errors) == 1
        assert "Unexpected input 'unexpected'" in errors
    
    def test_get_execution_order_simple(self):
        """Test getting execution order for simple pipeline."""
        step_a = PipelineStepTemplate(
            id=StepId("step_a"),
            name="Step A",
            description="First step",
            type="llm_generate",
            prompt_template=PromptTemplate("test")
        )
        
        step_b = PipelineStepTemplate(
            id=StepId("step_b"),
            name="Step B",
            description="Second step",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("step_a")]
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            steps={"step_a": step_a, "step_b": step_b}
        )
        
        execution_order = pipeline.get_execution_order()
        assert execution_order == ["step_a", "step_b"]
    
    def test_get_execution_order_complex(self):
        """Test getting execution order for complex pipeline."""
        outline = PipelineStepTemplate(
            id=StepId("outline"),
            name="Outline",
            description="Create outline",
            type="llm_generate",
            prompt_template=PromptTemplate("test")
        )
        
        content = PipelineStepTemplate(
            id=StepId("content"),
            name="Content",
            description="Generate content",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("outline")]
        )
        
        review = PipelineStepTemplate(
            id=StepId("review"),
            name="Review",
            description="Review content",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("content")]
        )
        
        metadata = PipelineStepTemplate(
            id=StepId("metadata"),
            name="Metadata",
            description="Generate metadata",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("outline")]
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            steps={
                "outline": outline,
                "content": content,
                "review": review,
                "metadata": metadata
            }
        )
        
        execution_order = pipeline.get_execution_order()
        
        # outline should come first
        assert execution_order[0] == "outline"
        
        # content and metadata should come after outline
        outline_idx = execution_order.index("outline")
        content_idx = execution_order.index("content")
        metadata_idx = execution_order.index("metadata")
        assert content_idx > outline_idx
        assert metadata_idx > outline_idx
        
        # review should come after content
        review_idx = execution_order.index("review")
        assert review_idx > content_idx
    
    def test_get_parallel_groups(self):
        """Test getting parallel execution groups."""
        # Independent steps that can run in parallel
        step_a = PipelineStepTemplate(
            id=StepId("step_a"),
            name="Step A",
            description="Independent step A",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            parallel=True
        )
        
        step_b = PipelineStepTemplate(
            id=StepId("step_b"),
            name="Step B",
            description="Independent step B",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            parallel=True
        )
        
        # Dependent step
        step_c = PipelineStepTemplate(
            id=StepId("step_c"),
            name="Step C",
            description="Dependent step",
            type="llm_generate",
            prompt_template=PromptTemplate("test"),
            depends_on=[StepId("step_a"), StepId("step_b")]
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            steps={"step_a": step_a, "step_b": step_b, "step_c": step_c}
        )
        
        groups = pipeline.get_parallel_groups()
        
        # step_a and step_b should be in the same parallel group
        # step_c should be in its own group
        assert len(groups) >= 2
        
        # Find the group containing parallel steps
        parallel_group = None
        for group in groups:
            if len(group) > 1:
                parallel_group = group
                break
        
        assert parallel_group is not None
        assert "step_a" in parallel_group
        assert "step_b" in parallel_group
    
    def test_get_step(self):
        """Test getting step by key."""
        step = PipelineStepTemplate(
            id=StepId("test_step"),
            name="Test Step",
            description="Test step",
            type="llm_generate",
            prompt_template=PromptTemplate("test")
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            steps={"test_step": step}
        )
        
        retrieved_step = pipeline.get_step("test_step")
        assert retrieved_step == step
        
        # Test non-existent step
        with pytest.raises(KeyError, match="Step 'nonexistent' not found"):
            pipeline.get_step("nonexistent")
    
    def test_has_step(self):
        """Test checking if pipeline has step."""
        step = PipelineStepTemplate(
            id=StepId("test_step"),
            name="Test Step",
            description="Test step",
            type="llm_generate",
            prompt_template=PromptTemplate("test")
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            steps={"test_step": step}
        )
        
        assert pipeline.has_step("test_step") is True
        assert pipeline.has_step("nonexistent") is False
    
    def test_get_required_variables(self):
        """Test getting all required variables from pipeline steps."""
        step_a = PipelineStepTemplate(
            id=StepId("step_a"),
            name="Step A",
            description="Uses topic variable",
            type="llm_generate",
            prompt_template=PromptTemplate("Write about {{ inputs.topic }}")
        )
        
        step_b = PipelineStepTemplate(
            id=StepId("step_b"),
            name="Step B",
            description="Uses style and tone variables",
            type="llm_generate",
            prompt_template=PromptTemplate("Write in {{ inputs.style }} with {{ inputs.tone }}")
        )
        
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Test",
            description="Test pipeline",
            steps={"step_a": step_a, "step_b": step_b}
        )
        
        variables = pipeline.get_required_variables()
        
        # Should contain all unique variables from all steps
        expected_variables = {"inputs.topic", "inputs.style", "inputs.tone"}
        assert variables == expected_variables
    
    def test_create_factory_method(self):
        """Test creating pipeline using factory method."""
        inputs = [
            PipelineInput(key="topic", type="text", label="Topic", required=True)
        ]
        
        steps = [
            PipelineStepTemplate(
                id=StepId("outline"),
                name="Create Outline",
                description="Generate outline",
                type="llm_generate",
                prompt_template=PromptTemplate("Create outline for {{ inputs.topic }}")
            )
        ]
        
        pipeline = PipelineTemplate.create(
            name="Test Pipeline",
            description="A test pipeline",
            inputs=inputs,
            steps=steps,
            version="2.0.0",
            tags=["test", "article"],
            author="Test Author"
        )
        
        assert pipeline.name == "Test Pipeline"
        assert pipeline.description == "A test pipeline"
        assert pipeline.version == "2.0.0"
        assert pipeline.tags == ["test", "article"]
        assert pipeline.author == "Test Author"
        assert len(pipeline.inputs) == 1
        assert len(pipeline.steps) == 1
        assert "topic" in pipeline.inputs
        assert "outline" in pipeline.steps
    
    def test_update_method(self):
        """Test updating pipeline with new values."""
        pipeline = PipelineTemplate(
            id=PipelineId("test"),
            name="Original Name",
            description="Original Description",
            version="1.0.0"
        )
        
        updated_pipeline = pipeline.update(
            name="Updated Name",
            version="2.0.0",
            tags=["updated"]
        )
        
        # Original pipeline unchanged
        assert pipeline.name == "Original Name"
        assert pipeline.version == "1.0.0"
        
        # Updated pipeline has new values
        assert updated_pipeline.name == "Updated Name"
        assert updated_pipeline.description == "Original Description"  # Unchanged
        assert updated_pipeline.version == "2.0.0"
        assert updated_pipeline.tags == ["updated"]
        assert updated_pipeline.updated_at > pipeline.updated_at
    
    def test_string_representations(self):
        """Test string and repr methods."""
        pipeline = PipelineTemplate(
            id=PipelineId("test-pipeline"),
            name="Test Pipeline",
            description="A test pipeline",
            version="1.0.0"
        )
        
        str_repr = str(pipeline)
        assert "Test Pipeline" in str_repr
        assert "1.0.0" in str_repr
        
        debug_repr = repr(pipeline)
        assert "PipelineTemplate" in debug_repr
        assert "test-pipeline" in debug_repr
        assert "Test Pipeline" in debug_repr
        assert "1.0.0" in debug_repr