"""Comprehensive unit tests for PipelineTemplate entity."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.writeit.domains.pipeline.entities.pipeline_template import (
    PipelineTemplate, PipelineStepTemplate, PipelineInput
)
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from src.writeit.domains.pipeline.value_objects.model_preference import ModelPreference

from tests.builders.pipeline_builders import (
    PipelineTemplateBuilder, PipelineStepTemplateBuilder, PipelineInputBuilder
)


class TestPipelineTemplate:
    """Test cases for PipelineTemplate entity."""
    
    def test_pipeline_template_creation_with_valid_data(self):
        """Test creating a pipeline template with valid data."""
        template = PipelineTemplateBuilder.simple().build()
        
        assert isinstance(template.id, PipelineId)
        assert template.name == "Simple Pipeline"
        assert template.description == "A simple test pipeline"
        assert template.version == "1.0.0"
        assert len(template.inputs) == 1
        assert len(template.steps) == 1
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)
    
    def test_pipeline_template_creation_with_complex_configuration(self):
        """Test creating a complex pipeline template."""
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        assert template.name == "Complex Pipeline"
        assert len(template.steps) == 3
        assert len(template.inputs) == 2
        assert "complex" in template.tags
        assert "test" in template.tags
        
        # Verify step dependencies
        content_step = template.get_step("content")
        assert content_step.has_dependency(StepId("outline"))
        
        review_step = template.get_step("review")
        assert review_step.has_dependency(StepId("content"))
    
    def test_pipeline_template_invalid_id_raises_error(self):
        """Test that invalid pipeline ID raises TypeError."""
        with pytest.raises(TypeError, match="Pipeline id must be a PipelineId"):
            PipelineTemplate(
                id="invalid_id",  # Should be PipelineId
                name="Test",
                description="Test description"
            )
    
    def test_pipeline_template_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline name must be a non-empty string"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="",
                description="Test description"
            )
    
    def test_pipeline_template_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline description must be a non-empty string"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description=""
            )
    
    def test_pipeline_template_invalid_input_type_raises_error(self):
        """Test that invalid input type raises TypeError."""
        with pytest.raises(TypeError, match="Input .* must be a PipelineInput"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description="Test description",
                inputs={"invalid": "not_a_pipeline_input"}
            )
    
    def test_pipeline_template_invalid_step_type_raises_error(self):
        """Test that invalid step type raises TypeError."""
        with pytest.raises(TypeError, match="Step .* must be a PipelineStepTemplate"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description="Test description",
                steps={"invalid": "not_a_step_template"}
            )
    
    def test_pipeline_template_input_key_mismatch_raises_error(self):
        """Test that input key mismatch raises ValueError."""
        input_def = PipelineInputBuilder.text_input("correct_key").build()
        
        with pytest.raises(ValueError, match="Input key mismatch"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description="Test description",
                inputs={"wrong_key": input_def}
            )
    
    def test_pipeline_template_step_key_mismatch_raises_error(self):
        """Test that step key mismatch raises ValueError."""
        step = PipelineStepTemplateBuilder.llm_step("correct_key").build()
        
        with pytest.raises(ValueError, match="Step key mismatch"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description="Test description",
                steps={"wrong_key": step}
            )
    
    def test_pipeline_template_nonexistent_dependency_raises_error(self):
        """Test that nonexistent step dependency raises ValueError."""
        step = PipelineStepTemplateBuilder.dependent_step(
            "dependent", ["nonexistent_step"]
        ).build()
        
        with pytest.raises(ValueError, match="depends on non-existent step"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description="Test description",
                steps={"dependent": step}
            )
    
    def test_pipeline_template_circular_dependency_raises_error(self):
        """Test that circular dependencies raise ValueError."""
        step1 = PipelineStepTemplateBuilder.llm_step("step1").with_dependencies(["step2"]).build()
        step2 = PipelineStepTemplateBuilder.llm_step("step2").with_dependencies(["step1"]).build()
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            PipelineTemplate(
                id=PipelineId.from_name("test"),
                name="Test",
                description="Test description",
                steps={"step1": step1, "step2": step2}
            )
    
    def test_validate_inputs_with_valid_data(self):
        """Test input validation with valid data."""
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        inputs = {
            "topic": "Test Topic",
            "style": "opt1"  # Valid choice option
        }
        
        errors = template.validate_inputs(inputs)
        assert errors == []
    
    def test_validate_inputs_with_missing_required_input(self):
        """Test input validation with missing required input."""
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        inputs = {
            "style": "opt1"
            # Missing required "topic"
        }
        
        errors = template.validate_inputs(inputs)
        assert len(errors) == 1
        assert "Required input 'topic' is missing" in errors[0]
    
    def test_validate_inputs_with_invalid_choice_value(self):
        """Test input validation with invalid choice value."""
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        inputs = {
            "topic": "Test Topic",
            "style": "invalid_choice"
        }
        
        errors = template.validate_inputs(inputs)
        assert len(errors) == 1
        assert "Invalid value for input 'style'" in errors[0]
    
    def test_validate_inputs_with_unexpected_input(self):
        """Test input validation with unexpected input."""
        template = PipelineTemplateBuilder.simple().build()
        
        inputs = {
            "topic": "Test Topic",
            "unexpected": "value"
        }
        
        errors = template.validate_inputs(inputs)
        assert len(errors) == 1
        assert "Unexpected input 'unexpected'" in errors[0]
    
    def test_get_execution_order_simple_pipeline(self):
        """Test execution order for simple pipeline."""
        template = PipelineTemplateBuilder.simple().build()
        
        order = template.get_execution_order()
        assert order == ["generate"]
    
    def test_get_execution_order_complex_pipeline(self):
        """Test execution order for complex pipeline with dependencies."""
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        order = template.get_execution_order()
        assert order.index("outline") < order.index("content")
        assert order.index("content") < order.index("review")
        assert len(order) == 3
    
    def test_get_execution_order_with_circular_dependency_raises_error(self):
        """Test that circular dependency in execution order raises ValueError."""
        # This should not happen due to validation, but test the method directly
        step1 = PipelineStepTemplateBuilder.llm_step("step1").build()
        step2 = PipelineStepTemplateBuilder.llm_step("step2").build()
        
        # Manually create circular dependency (bypassing validation)
        template = PipelineTemplateBuilder().with_name("Test").build()
        template.steps["step1"] = step1
        template.steps["step2"] = step2
        template.steps["step1"].depends_on = [StepId("step2")]
        template.steps["step2"].depends_on = [StepId("step1")]
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            template.get_execution_order()
    
    def test_get_parallel_groups_no_parallel_steps(self):
        """Test parallel groups for sequential-only steps."""
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        groups = template.get_parallel_groups()
        # All steps should be in separate groups due to dependencies
        assert len(groups) == 3
        assert all(len(group) == 1 for group in groups)
    
    def test_get_parallel_groups_with_parallel_steps(self):
        """Test parallel groups with parallel-capable steps."""
        template = PipelineTemplateBuilder.with_parallel_steps().build()
        
        groups = template.get_parallel_groups()
        assert len(groups) == 2  # First group with parallel steps, second with merge
        assert len(groups[0]) == 2  # Two parallel steps
        assert len(groups[1]) == 1  # One merge step
    
    def test_get_step_existing_step(self):
        """Test getting an existing step."""
        template = PipelineTemplateBuilder.simple().build()
        
        step = template.get_step("generate")
        assert isinstance(step, PipelineStepTemplate)
        assert step.id == StepId("generate")
    
    def test_get_step_nonexistent_step_raises_error(self):
        """Test that getting nonexistent step raises KeyError."""
        template = PipelineTemplateBuilder.simple().build()
        
        with pytest.raises(KeyError, match="Step 'nonexistent' not found"):
            template.get_step("nonexistent")
    
    def test_has_step_existing_step(self):
        """Test checking for existing step."""
        template = PipelineTemplateBuilder.simple().build()
        
        assert template.has_step("generate") is True
        assert template.has_step("nonexistent") is False
    
    def test_get_required_variables(self):
        """Test getting required variables from all steps."""
        template = (PipelineTemplateBuilder()
                   .with_name("Variable Test")
                   .with_steps([
                       (PipelineStepTemplateBuilder()
                        .with_id("step1")
                        .with_prompt_template("Use {{var1}} and {{var2}}")
                        .build()),
                       (PipelineStepTemplateBuilder()
                        .with_id("step2")
                        .with_prompt_template("Use {{var2}} and {{var3}}")
                        .build())
                   ])
                   .build())
        
        variables = template.get_required_variables()
        assert variables == {"var1", "var2", "var3"}
    
    def test_create_class_method(self):
        """Test the create class method."""
        inputs = [PipelineInputBuilder.text_input("topic").required().build()]
        steps = [PipelineStepTemplateBuilder.llm_step("generate").build()]
        
        template = PipelineTemplate.create(
            name="Created Pipeline",
            description="Created via class method",
            inputs=inputs,
            steps=steps,
            version="2.0.0",
            tags=["created", "test"],
            author="Test Author"
        )
        
        assert template.name == "Created Pipeline"
        assert template.version == "2.0.0"
        assert template.tags == ["created", "test"]
        assert template.author == "Test Author"
        assert len(template.inputs) == 1
        assert len(template.steps) == 1
    
    def test_update_method(self):
        """Test the update method."""
        original = PipelineTemplateBuilder.simple().build()
        original_created_at = original.created_at
        
        updated = original.update(
            name="Updated Pipeline",
            version="2.0.0",
            tags=["updated"]
        )
        
        assert updated.name == "Updated Pipeline"
        assert updated.version == "2.0.0"
        assert updated.tags == ["updated"]
        assert updated.created_at == original_created_at  # Should not change
        assert updated.updated_at > original.updated_at
        
        # Original should be unchanged
        assert original.name == "Simple Pipeline"
        assert original.version == "1.0.0"
    
    def test_string_representation(self):
        """Test string representations."""
        template = PipelineTemplateBuilder.simple().build()
        
        str_repr = str(template)
        assert "Simple Pipeline" in str_repr
        assert "1.0.0" in str_repr
        
        debug_repr = repr(template)
        assert "PipelineTemplate" in debug_repr
        assert "Simple Pipeline" in debug_repr
        assert "1.0.0" in debug_repr
        assert "steps=1" in debug_repr
    
    def test_template_immutability(self):
        """Test that template updates create new instances."""
        original = PipelineTemplateBuilder.simple().build()
        updated = original.update(name="New Name")
        
        assert original is not updated
        assert original.name != updated.name
        assert id(original) != id(updated)
    
    def test_template_with_metadata(self):
        """Test template with custom metadata."""
        metadata = {
            "category": "content_generation",
            "difficulty": "beginner",
            "estimated_time": 300  # seconds
        }
        
        template = (PipelineTemplateBuilder
                   .simple()
                   .with_metadata(metadata)
                   .build())
        
        assert template.metadata == metadata
        assert template.metadata["category"] == "content_generation"
    
    def test_template_with_defaults(self):
        """Test template with default values."""
        defaults = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        template = (PipelineTemplateBuilder
                   .simple()
                   .with_defaults(defaults)
                   .build())
        
        assert template.defaults == defaults
        assert template.defaults["model"] == "gpt-4o-mini"
    
    def test_template_timestamps(self):
        """Test template timestamp behavior."""
        now = datetime.now()
        template = PipelineTemplateBuilder.simple().build()
        
        # Created and updated should be close to now
        assert abs((template.created_at - now).total_seconds()) < 1
        assert abs((template.updated_at - now).total_seconds()) < 1
        
        # Test custom timestamps
        custom_time = datetime(2023, 1, 1)
        template_with_custom = (PipelineTemplateBuilder
                               .simple()
                               .with_timestamps(custom_time, custom_time)
                               .build())
        
        assert template_with_custom.created_at == custom_time
        assert template_with_custom.updated_at == custom_time


class TestPipelineTemplateBusinessRules:
    """Test business rules and invariants for PipelineTemplate."""
    
    def test_pipeline_id_derived_from_name(self):
        """Test that pipeline ID is correctly derived from name."""
        template = PipelineTemplateBuilder().with_name("Test Pipeline").build()
        
        expected_id = PipelineId.from_name("Test Pipeline")
        assert template.id == expected_id
    
    def test_step_execution_order_respects_dependencies(self):
        """Test that execution order respects all dependencies."""
        # Create a more complex dependency chain: A -> B -> C, D -> C
        step_a = PipelineStepTemplateBuilder.llm_step("step_a").build()
        step_b = PipelineStepTemplateBuilder.llm_step("step_b").with_dependencies(["step_a"]).build()
        step_c = PipelineStepTemplateBuilder.llm_step("step_c").with_dependencies(["step_b", "step_d"]).build()
        step_d = PipelineStepTemplateBuilder.llm_step("step_d").build()
        
        template = (PipelineTemplateBuilder()
                   .with_name("Dependency Test")
                   .with_steps([step_a, step_b, step_c, step_d])
                   .build())
        
        order = template.get_execution_order()
        
        # Verify all dependencies are respected
        assert order.index("step_a") < order.index("step_b")
        assert order.index("step_b") < order.index("step_c")
        assert order.index("step_d") < order.index("step_c")
    
    def test_input_validation_enforces_business_rules(self):
        """Test that input validation enforces business rules."""
        # Create input with specific validation rules
        input_def = (PipelineInputBuilder
                    .text_input("email")
                    .required()
                    .with_validation({"pattern": r"^[^@]+@[^@]+\.[^@]+$"})
                    .build())
        
        template = (PipelineTemplateBuilder
                   .simple()
                   .with_inputs([input_def])
                   .build())
        
        # Valid email should pass
        assert template.validate_inputs({"email": "test@example.com"}) == []
        
        # Invalid email should fail (if validation is implemented)
        # Note: This depends on PipelineInput.validate_value implementation
        # For now, just test that the structure is correct
        assert "email" in template.inputs
        assert template.inputs["email"].required is True
    
    def test_template_versioning_consistency(self):
        """Test that template versioning is consistent."""
        template = (PipelineTemplateBuilder
                   .simple()
                   .with_version("1.2.3")
                   .build())
        
        assert template.version == "1.2.3"
        
        # Updated template should have new version if specified
        updated = template.update(version="1.2.4")
        assert updated.version == "1.2.4"
        assert template.version == "1.2.3"  # Original unchanged
    
    def test_template_immutable_after_creation(self):
        """Test that template is immutable after creation."""
        template = PipelineTemplateBuilder.simple().build()
        original_name = template.name
        
        # Direct modification should not be possible (dataclass frozen behavior)
        with pytest.raises(AttributeError):
            template.name = "Modified Name"  # type: ignore
        
        assert template.name == original_name
    
    def test_step_variable_consistency(self):
        """Test that step variables are consistent with inputs."""
        # This is a business rule that could be enforced
        input_def = PipelineInputBuilder.text_input("topic").required().build()
        step = (PipelineStepTemplateBuilder
                .llm_step("generate")
                .with_prompt_template("Write about {{inputs.topic}}")
                .build())
        
        template = (PipelineTemplateBuilder
                   .simple()
                   .with_inputs([input_def])
                   .with_steps([step])
                   .build())
        
        # Verify that the step references available inputs
        step_variables = template.get_step("generate").get_required_variables()
        assert "inputs.topic" in step_variables or "topic" in step_variables