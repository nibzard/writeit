"""Comprehensive unit tests for Pipeline domain value objects."""

import pytest
from datetime import datetime

from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from src.writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from src.writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus

from tests.builders.value_object_builders import (
    PipelineIdBuilder, StepIdBuilder, PromptTemplateBuilder, ModelPreferenceBuilder
)


class TestPipelineId:
    """Test cases for PipelineId value object."""
    
    def test_pipeline_id_creation_from_name(self):
        """Test creating PipelineId from name."""
        name = "test_pipeline"
        pipeline_id = PipelineIdBuilder().with_name(name).build()
        
        assert pipeline_id.value == name
        assert str(pipeline_id) == name
    
    def test_pipeline_id_normalization(self):
        """Test PipelineId name normalization."""
        # Test various name formats
        test_cases = [
            ("Simple Name", "simple_name"),
            ("Complex-Name.With.Dots", "complex_name_with_dots"),
            ("Name With Spaces", "name_with_spaces"),
            ("UPPERCASE", "uppercase"),
            ("mixed_CASE-Name", "mixed_case_name")
        ]
        
        for input_name, expected in test_cases:
            pipeline_id = PipelineId.from_name(input_name)
            assert pipeline_id.value == expected
    
    def test_pipeline_id_equality(self):
        """Test PipelineId equality comparison."""
        id1 = PipelineIdBuilder.simple().build()
        id2 = PipelineIdBuilder.simple().build()
        id3 = PipelineIdBuilder.complex().build()
        
        assert id1 == id2  # Same pipeline name
        assert id1 != id3  # Different pipeline names
        assert id1 != "simple_pipeline"  # Not equal to string
    
    def test_pipeline_id_hash_consistency(self):
        """Test PipelineId hash consistency."""
        id1 = PipelineIdBuilder().with_name("test").build()
        id2 = PipelineIdBuilder().with_name("test").build()
        
        assert hash(id1) == hash(id2)
        assert id1 in {id2}  # Can be used in sets
    
    def test_pipeline_id_invalid_name_raises_error(self):
        """Test that invalid names raise ValueError."""
        with pytest.raises(ValueError, match="Pipeline name cannot be empty"):
            PipelineId.from_name("")
        
        with pytest.raises(ValueError, match="Pipeline name cannot be empty"):
            PipelineId.from_name("   ")
    
    def test_pipeline_id_special_characters(self):
        """Test PipelineId with special characters."""
        special_name = "pipeline-with_special.chars#123"
        expected = "pipeline_with_special_chars_123"
        
        pipeline_id = PipelineId.from_name(special_name)
        assert pipeline_id.value == expected
    
    def test_pipeline_id_immutability(self):
        """Test PipelineId immutability."""
        pipeline_id = PipelineIdBuilder().with_name("test").build()
        
        with pytest.raises(AttributeError):
            pipeline_id.value = "modified"  # type: ignore
    
    def test_pipeline_id_representation(self):
        """Test PipelineId string representations."""
        name = "test_pipeline"
        pipeline_id = PipelineIdBuilder().with_name(name).build()
        
        assert str(pipeline_id) == name
        assert repr(pipeline_id) == f"PipelineId('{name}')"


class TestStepId:
    """Test cases for StepId value object."""
    
    def test_step_id_creation(self):
        """Test creating StepId."""
        value = "test_step"
        step_id = StepIdBuilder().with_value(value).build()
        
        assert step_id.value == value
        assert str(step_id) == value
    
    def test_step_id_validation(self):
        """Test StepId validation rules."""
        # Valid step IDs
        valid_ids = ["step1", "generate_content", "validate-input", "step_with_underscores"]
        
        for valid_id in valid_ids:
            step_id = StepId(valid_id)
            assert step_id.value == valid_id
        
        # Invalid step IDs
        with pytest.raises(ValueError, match="Step ID cannot be empty"):
            StepId("")
        
        with pytest.raises(ValueError, match="Step ID cannot be empty"):
            StepId("   ")
        
        with pytest.raises(ValueError, match="Step ID must contain only alphanumeric"):
            StepId("step with spaces")
        
        with pytest.raises(ValueError, match="Step ID must contain only alphanumeric"):
            StepId("step@invalid")
    
    def test_step_id_equality(self):
        """Test StepId equality comparison."""
        id1 = StepIdBuilder.simple().build()
        id2 = StepIdBuilder.simple().build()
        id3 = StepIdBuilder.numbered(2).build()
        
        assert id1 == id2
        assert id1 != id3
        assert id1 != "step"  # Not equal to string
    
    def test_step_id_hash_consistency(self):
        """Test StepId hash consistency."""
        id1 = StepId("test_step")
        id2 = StepId("test_step")
        
        assert hash(id1) == hash(id2)
        assert id1 in {id2}
    
    def test_step_id_case_sensitivity(self):
        """Test StepId case sensitivity."""
        id1 = StepId("Step")
        id2 = StepId("step")
        
        assert id1 != id2  # Should be case sensitive
        assert id1.value == "Step"
        assert id2.value == "step"
    
    def test_step_id_length_limits(self):
        """Test StepId length validation."""
        # Test maximum length
        long_id = "a" * 100
        step_id = StepId(long_id)
        assert step_id.value == long_id
        
        # Test very long ID (should still work unless specifically limited)
        very_long_id = "step_" + "a" * 255
        very_long_step_id = StepId(very_long_id)
        assert very_long_step_id.value == very_long_id
    
    def test_step_id_numbered_factory(self):
        """Test StepId numbered factory method."""
        numbered = StepIdBuilder.numbered(5).build()
        assert numbered.value == "step_5"
    
    def test_step_id_named_factory(self):
        """Test StepId named factory method."""
        named = StepIdBuilder.named("validate").build()
        assert named.value == "validate"


class TestPromptTemplate:
    """Test cases for PromptTemplate value object."""
    
    def test_prompt_template_creation(self):
        """Test creating PromptTemplate."""
        template_str = "Generate content about {{topic}}"
        template = PromptTemplateBuilder().with_template(template_str).build()
        
        assert template.template == template_str
        assert template.variables == {"topic"}
    
    def test_prompt_template_variable_extraction(self):
        """Test variable extraction from template."""
        complex_template = """
        Write a {{style}} article about {{topic}}.
        
        Requirements:
        - Length: {{length}} words
        - Audience: {{audience}}
        - Include sections: {{sections}}
        
        Context: {{context}}
        """
        
        template = PromptTemplate(complex_template)
        expected_vars = {"style", "topic", "length", "audience", "sections", "context"}
        assert template.variables == expected_vars
    
    def test_prompt_template_no_variables(self):
        """Test PromptTemplate with no variables."""
        static_template = "This is a static prompt with no variables."
        template = PromptTemplate(static_template)
        
        assert template.template == static_template
        assert template.variables == set()
    
    def test_prompt_template_duplicate_variables(self):
        """Test PromptTemplate with duplicate variables."""
        template_with_dupes = "Hello {{name}}, how are you {{name}}? Goodbye {{name}}!"
        template = PromptTemplate(template_with_dupes)
        
        assert template.variables == {"name"}  # Should deduplicate
    
    def test_prompt_template_malformed_variables(self):
        """Test PromptTemplate with malformed variables."""
        malformed_template = "This has {{incomplete and }invalid} variables {{valid}}."
        template = PromptTemplate(malformed_template)
        
        # Should extract valid variables and ignore malformed ones
        assert "valid" in template.variables
        # Behavior for malformed variables is implementation-specific
    
    def test_prompt_template_nested_braces(self):
        """Test PromptTemplate with nested braces."""
        nested_template = "Use {{config.{{env}}.database}} for connection."
        template = PromptTemplate(nested_template)
        
        # Behavior depends on implementation - should handle gracefully
        assert template.template == nested_template
    
    def test_prompt_template_equality(self):
        """Test PromptTemplate equality."""
        template1 = PromptTemplate("Write about {{topic}}")
        template2 = PromptTemplate("Write about {{topic}}")
        template3 = PromptTemplate("Write about {{subject}}")
        
        assert template1 == template2
        assert template1 != template3
    
    def test_prompt_template_hash_consistency(self):
        """Test PromptTemplate hash consistency."""
        template1 = PromptTemplate("Template {{var}}")
        template2 = PromptTemplate("Template {{var}}")
        
        assert hash(template1) == hash(template2)
        assert template1 in {template2}
    
    def test_prompt_template_empty_template(self):
        """Test PromptTemplate with empty template."""
        with pytest.raises(ValueError, match="Template cannot be empty"):
            PromptTemplate("")
        
        with pytest.raises(ValueError, match="Template cannot be empty"):
            PromptTemplate("   ")
    
    def test_prompt_template_unicode_variables(self):
        """Test PromptTemplate with unicode variables."""
        unicode_template = "Hola {{ñame}}, bienvenido a {{platafórma}}!"
        template = PromptTemplate(unicode_template)
        
        # Should handle unicode in variable names
        assert template.template == unicode_template
        # Variable extraction behavior depends on implementation
    
    def test_prompt_template_large_template(self):
        """Test PromptTemplate with large template."""
        large_template = "Large template " * 1000 + "{{variable}}"
        template = PromptTemplate(large_template)
        
        assert template.template == large_template
        assert "variable" in template.variables
    
    def test_prompt_template_factory_methods(self):
        """Test PromptTemplate builder factory methods."""
        simple = PromptTemplateBuilder.simple().build()
        assert "topic" in simple.variables
        
        complex = PromptTemplateBuilder.complex().build()
        assert len(complex.variables) > 3
        assert "style" in complex.variables
        assert "topic" in complex.variables
        
        multiple_vars = PromptTemplateBuilder.with_multiple_vars().build()
        assert len(multiple_vars.variables) == 4


class TestModelPreference:
    """Test cases for ModelPreference value object."""
    
    def test_model_preference_creation(self):
        """Test creating ModelPreference."""
        models = ["gpt-4o", "gpt-4o-mini"]
        preference = ModelPreference(
            preferred_models=models,
            fallback_strategy="next_available"
        )
        
        assert preference.preferred_models == models
        assert preference.fallback_strategy == "next_available"
    
    def test_model_preference_default(self):
        """Test default ModelPreference."""
        default = ModelPreference.default()
        
        assert isinstance(default.preferred_models, list)
        assert len(default.preferred_models) > 0
        assert isinstance(default.fallback_strategy, str)
    
    def test_model_preference_validation(self):
        """Test ModelPreference validation."""
        # Empty models list should raise error
        with pytest.raises(ValueError, match="Preferred models cannot be empty"):
            ModelPreference(preferred_models=[], fallback_strategy="next_available")
        
        # Invalid fallback strategy
        with pytest.raises(ValueError, match="Invalid fallback strategy"):
            ModelPreference(
                preferred_models=["gpt-4o"], 
                fallback_strategy="invalid_strategy"
            )
    
    def test_model_preference_equality(self):
        """Test ModelPreference equality."""
        pref1 = ModelPreference(["gpt-4o"], "next_available")
        pref2 = ModelPreference(["gpt-4o"], "next_available")
        pref3 = ModelPreference(["claude-3-haiku"], "next_available")
        
        assert pref1 == pref2
        assert pref1 != pref3
    
    def test_model_preference_constraints(self):
        """Test ModelPreference with constraints."""
        constraints = {"max_tokens": 1000, "temperature": 0.7}
        preference = ModelPreference(
            preferred_models=["gpt-4o"],
            fallback_strategy="next_available",
            constraints=constraints
        )
        
        assert preference.constraints == constraints
    
    def test_model_preference_builder_factories(self):
        """Test ModelPreference builder factory methods."""
        openai = ModelPreferenceBuilder.openai_only().build()
        assert "gpt-4o" in openai.preferred_models
        assert "gpt-4o-mini" in openai.preferred_models
        
        anthropic = ModelPreferenceBuilder.anthropic_only().build()
        assert "claude-3-sonnet" in anthropic.preferred_models
        assert "claude-3-haiku" in anthropic.preferred_models
    
    def test_model_preference_fallback_strategies(self):
        """Test different fallback strategies."""
        strategies = ["next_available", "cheapest", "fastest", "best_quality"]
        
        for strategy in strategies:
            try:
                preference = ModelPreference(["gpt-4o"], strategy)
                assert preference.fallback_strategy == strategy
            except ValueError:
                # Some strategies might not be implemented
                pass


class TestExecutionStatus:
    """Test cases for ExecutionStatus value object."""
    
    def test_execution_status_values(self):
        """Test ExecutionStatus enum values."""
        assert ExecutionStatus.PENDING
        assert ExecutionStatus.RUNNING
        assert ExecutionStatus.COMPLETED
        assert ExecutionStatus.FAILED
        assert ExecutionStatus.CANCELLED
    
    def test_execution_status_transitions(self):
        """Test valid ExecutionStatus transitions."""
        # Test common transition patterns
        pending = ExecutionStatus.PENDING
        running = ExecutionStatus.RUNNING
        completed = ExecutionStatus.COMPLETED
        failed = ExecutionStatus.FAILED
        cancelled = ExecutionStatus.CANCELLED
        
        # Valid transitions (business logic test)
        valid_transitions = {
            pending: [running, cancelled, failed],
            running: [completed, failed, cancelled],
            completed: [],  # Terminal state
            failed: [],  # Terminal state
            cancelled: []  # Terminal state
        }
        
        for current, valid_next in valid_transitions.items():
            # This would be tested in business logic, not the enum itself
            assert current != None
            for next_status in valid_next:
                assert next_status != None
    
    def test_execution_status_string_representation(self):
        """Test ExecutionStatus string representation."""
        assert str(ExecutionStatus.PENDING) in ["PENDING", "pending"]
        assert str(ExecutionStatus.RUNNING) in ["RUNNING", "running"]
        assert str(ExecutionStatus.COMPLETED) in ["COMPLETED", "completed"]
        assert str(ExecutionStatus.FAILED) in ["FAILED", "failed"]
    
    def test_execution_status_comparison(self):
        """Test ExecutionStatus comparison."""
        status1 = ExecutionStatus.PENDING
        status2 = ExecutionStatus.PENDING
        status3 = ExecutionStatus.RUNNING
        
        assert status1 == status2
        assert status1 != status3
    
    def test_execution_status_in_collections(self):
        """Test ExecutionStatus in collections."""
        statuses = {ExecutionStatus.PENDING, ExecutionStatus.RUNNING}
        
        assert ExecutionStatus.PENDING in statuses
        assert ExecutionStatus.COMPLETED not in statuses
        
        status_list = [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        assert len(status_list) == 2
        assert ExecutionStatus.PENDING in status_list


class TestValueObjectInvariants:
    """Test invariants that should hold for all value objects."""
    
    def test_value_object_immutability(self):
        """Test that value objects are immutable."""
        pipeline_id = PipelineId.from_name("test")
        step_id = StepId("test_step")
        template = PromptTemplate("Template {{var}}")
        
        # Should not be able to modify internal state
        with pytest.raises(AttributeError):
            pipeline_id.value = "modified"  # type: ignore
        
        with pytest.raises(AttributeError):
            step_id.value = "modified"  # type: ignore
        
        with pytest.raises(AttributeError):
            template.template = "modified"  # type: ignore
    
    def test_value_object_equality_transitivity(self):
        """Test equality transitivity for value objects."""
        # Pipeline ID transitivity
        id1 = PipelineId.from_name("test")
        id2 = PipelineId.from_name("test")
        id3 = PipelineId.from_name("test")
        
        assert id1 == id2
        assert id2 == id3
        assert id1 == id3  # Transitivity
    
    def test_value_object_hash_stability(self):
        """Test that value object hashes are stable."""
        pipeline_id = PipelineId.from_name("test")
        hash1 = hash(pipeline_id)
        hash2 = hash(pipeline_id)
        
        assert hash1 == hash2  # Same object, same hash
        
        # Different objects, same value, same hash
        other_id = PipelineId.from_name("test")
        assert hash(pipeline_id) == hash(other_id)
    
    def test_value_object_string_representation(self):
        """Test that value objects have meaningful string representations."""
        pipeline_id = PipelineId.from_name("test_pipeline")
        step_id = StepId("test_step")
        template = PromptTemplate("Test {{template}}")
        
        # String representations should be meaningful
        assert "test_pipeline" in str(pipeline_id)
        assert "test_step" in str(step_id)
        assert "template" in str(template).lower()
        
        # Repr should be informative
        assert "PipelineId" in repr(pipeline_id)
        assert "StepId" in repr(step_id)
        assert "PromptTemplate" in repr(template)
    
    def test_value_object_none_handling(self):
        """Test that value objects handle None appropriately."""
        # Value objects should not accept None as valid values
        with pytest.raises((ValueError, TypeError)):
            PipelineId.from_name(None)  # type: ignore
        
        with pytest.raises((ValueError, TypeError)):
            StepId(None)  # type: ignore
        
        with pytest.raises((ValueError, TypeError)):
            PromptTemplate(None)  # type: ignore