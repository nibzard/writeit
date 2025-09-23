"""Tests for the validation framework."""

import pytest

from writeit.shared.validation import (
    ValidationContext,
    ValidationFramework, 
    ValidationResult,
    ValidationRule,
    CompositeValidationRule,
    NotNullValidator,
    StringLengthValidator,
    RegexValidator,
)


class MockValidator(ValidationRule[str]):
    """Mock validator for testing."""
    
    def __init__(self, should_pass: bool = True, error_msg: str = "Mock error"):
        self._should_pass = should_pass
        self._error_msg = error_msg
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if self._should_pass:
            return ValidationResult.success()
        return ValidationResult.failure([self._error_msg])
    
    @property
    def description(self) -> str:
        return "Mock validator for testing"


class TestValidationResult:
    """Test ValidationResult functionality."""
    
    def test_success_creation(self):
        result = ValidationResult.success()
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}
    
    def test_success_with_warnings(self):
        warnings = ["Warning 1", "Warning 2"]
        metadata = {"key": "value"}
        result = ValidationResult.success(warnings, metadata)
        
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == warnings
        assert result.metadata == metadata
    
    def test_failure_creation(self):
        errors = ["Error 1", "Error 2"]
        result = ValidationResult.failure(errors)
        
        assert not result.is_valid
        assert result.errors == errors
        assert result.warnings == []
        assert result.metadata == {}
    
    def test_combine_valid_results(self):
        result1 = ValidationResult.success(["Warning 1"], {"key1": "value1"})
        result2 = ValidationResult.success(["Warning 2"], {"key2": "value2"})
        
        combined = result1.combine(result2)
        
        assert combined.is_valid
        assert combined.errors == []
        assert combined.warnings == ["Warning 1", "Warning 2"]
        assert combined.metadata == {"key1": "value1", "key2": "value2"}
    
    def test_combine_with_failure(self):
        result1 = ValidationResult.success(["Warning 1"])
        result2 = ValidationResult.failure(["Error 1"])
        
        combined = result1.combine(result2)
        
        assert not combined.is_valid
        assert combined.errors == ["Error 1"]
        assert combined.warnings == ["Warning 1"]
    
    def test_combine_multiple_failures(self):
        result1 = ValidationResult.failure(["Error 1"], ["Warning 1"])
        result2 = ValidationResult.failure(["Error 2"], ["Warning 2"])
        
        combined = result1.combine(result2)
        
        assert not combined.is_valid
        assert combined.errors == ["Error 1", "Error 2"]
        assert combined.warnings == ["Warning 1", "Warning 2"]


class TestValidationContext:
    """Test ValidationContext functionality."""
    
    def test_default_creation(self):
        context = ValidationContext()
        
        assert context.workspace_name is None
        assert context.user_id is None
        assert context.environment == "production"
        assert not context.strict_mode
        assert context.custom_data == {}
    
    def test_with_workspace(self):
        context = ValidationContext()
        new_context = context.with_workspace("test_workspace")
        
        assert new_context.workspace_name == "test_workspace"
        assert new_context.user_id == context.user_id
        assert new_context.environment == context.environment
        assert new_context.strict_mode == context.strict_mode
    
    def test_with_strict_mode(self):
        context = ValidationContext()
        strict_context = context.with_strict_mode(True)
        
        assert strict_context.strict_mode
        assert strict_context.workspace_name == context.workspace_name
        
        non_strict_context = strict_context.with_strict_mode(False)
        assert not non_strict_context.strict_mode


class TestValidationFramework:
    """Test ValidationFramework functionality."""
    
    def test_register_and_validate(self):
        framework = ValidationFramework()
        validator = MockValidator(should_pass=True)
        
        framework.register_validator("test_entity", validator)
        result = framework.validate("test_entity", "test_value", ValidationContext())
        
        assert result.is_valid
    
    def test_validate_unknown_entity_type(self):
        framework = ValidationFramework()
        result = framework.validate("unknown_entity", "test_value", ValidationContext())
        
        assert result.is_valid  # No validators = success
    
    def test_multiple_validators_all_pass(self):
        framework = ValidationFramework()
        validator1 = MockValidator(should_pass=True)
        validator2 = MockValidator(should_pass=True)
        
        framework.register_validator("test_entity", validator1)
        framework.register_validator("test_entity", validator2)
        
        result = framework.validate("test_entity", "test_value", ValidationContext())
        assert result.is_valid
    
    def test_multiple_validators_one_fails(self):
        framework = ValidationFramework()
        validator1 = MockValidator(should_pass=True)
        validator2 = MockValidator(should_pass=False, error_msg="Validation failed")
        
        framework.register_validator("test_entity", validator1)
        framework.register_validator("test_entity", validator2)
        
        result = framework.validate("test_entity", "test_value", ValidationContext())
        assert not result.is_valid
        assert "Validation failed" in result.errors
    
    def test_strict_mode_continues_after_failure(self):
        framework = ValidationFramework()
        validator1 = MockValidator(should_pass=False, error_msg="Error 1")
        validator2 = MockValidator(should_pass=False, error_msg="Error 2")
        
        framework.register_validator("test_entity", validator1)
        framework.register_validator("test_entity", validator2)
        
        context = ValidationContext().with_strict_mode(True)
        result = framework.validate("test_entity", "test_value", context)
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors
    
    def test_non_strict_mode_stops_at_first_failure(self):
        framework = ValidationFramework()
        validator1 = MockValidator(should_pass=False, error_msg="Error 1")
        validator2 = MockValidator(should_pass=False, error_msg="Error 2")
        
        framework.register_validator("test_entity", validator1)
        framework.register_validator("test_entity", validator2)
        
        context = ValidationContext().with_strict_mode(False)
        result = framework.validate("test_entity", "test_value", context)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "Error 1" in result.errors
    
    def test_get_validators(self):
        framework = ValidationFramework()
        validator = MockValidator()
        
        framework.register_validator("test_entity", validator)
        validators = framework.get_validators("test_entity")
        
        assert len(validators) == 1
        assert validators[0] is validator
        
        # Ensure it returns a copy
        validators.clear()
        assert len(framework.get_validators("test_entity")) == 1


class TestCompositeValidationRule:
    """Test CompositeValidationRule functionality."""
    
    def test_and_composition_all_pass(self):
        validator1 = MockValidator(should_pass=True)
        validator2 = MockValidator(should_pass=True)
        
        composite = CompositeValidationRule([validator1, validator2], "AND")
        result = composite.validate("test", ValidationContext())
        
        assert result.is_valid
    
    def test_and_composition_one_fails(self):
        validator1 = MockValidator(should_pass=True)
        validator2 = MockValidator(should_pass=False, error_msg="Validator 2 failed")
        
        composite = CompositeValidationRule([validator1, validator2], "AND")
        result = composite.validate("test", ValidationContext())
        
        assert not result.is_valid
        assert "Validator 2 failed" in result.errors
    
    def test_or_composition_one_passes(self):
        validator1 = MockValidator(should_pass=False, error_msg="Validator 1 failed")
        validator2 = MockValidator(should_pass=True)
        
        composite = CompositeValidationRule([validator1, validator2], "OR")
        result = composite.validate("test", ValidationContext())
        
        assert result.is_valid
    
    def test_or_composition_all_fail(self):
        validator1 = MockValidator(should_pass=False, error_msg="Validator 1 failed")
        validator2 = MockValidator(should_pass=False, error_msg="Validator 2 failed")
        
        composite = CompositeValidationRule([validator1, validator2], "OR")
        result = composite.validate("test", ValidationContext())
        
        assert not result.is_valid
        assert "Validator 1 failed" in result.errors
        assert "Validator 2 failed" in result.errors
    
    def test_invalid_operator(self):
        with pytest.raises(ValueError, match="Operator must be 'AND' or 'OR'"):
            CompositeValidationRule([MockValidator()], "INVALID")
    
    def test_empty_rules_list(self):
        composite = CompositeValidationRule([], "AND")
        result = composite.validate("test", ValidationContext())
        
        assert result.is_valid
    
    def test_description(self):
        validator1 = MockValidator()
        validator2 = MockValidator()
        
        composite_and = CompositeValidationRule([validator1, validator2], "AND")
        assert "Mock validator for testing AND Mock validator for testing" in composite_and.description
        
        composite_or = CompositeValidationRule([validator1, validator2], "OR")
        assert "Mock validator for testing OR Mock validator for testing" in composite_or.description


class TestValidationRuleOperators:
    """Test ValidationRule operator overloading."""
    
    def test_and_operator(self):
        validator1 = MockValidator(should_pass=True)
        validator2 = MockValidator(should_pass=True)
        
        composite = validator1 & validator2
        result = composite.validate("test", ValidationContext())
        
        assert result.is_valid
        assert isinstance(composite, CompositeValidationRule)
    
    def test_or_operator(self):
        validator1 = MockValidator(should_pass=False)
        validator2 = MockValidator(should_pass=True)
        
        composite = validator1 | validator2
        result = composite.validate("test", ValidationContext())
        
        assert result.is_valid
        assert isinstance(composite, CompositeValidationRule)


class TestBaseValidators:
    """Test built-in base validators."""
    
    def test_not_null_validator_success(self):
        validator = NotNullValidator()
        result = validator.validate("test", ValidationContext())
        
        assert result.is_valid
    
    def test_not_null_validator_failure(self):
        validator = NotNullValidator()
        result = validator.validate(None, ValidationContext())
        
        assert not result.is_valid
        assert "cannot be null" in result.errors[0]
    
    def test_string_length_validator_success(self):
        validator = StringLengthValidator(min_length=2, max_length=10)
        result = validator.validate("test", ValidationContext())
        
        assert result.is_valid
    
    def test_string_length_validator_too_short(self):
        validator = StringLengthValidator(min_length=5)
        result = validator.validate("test", ValidationContext())
        
        assert not result.is_valid
        assert "at least 5 characters" in result.errors[0]
    
    def test_string_length_validator_too_long(self):
        validator = StringLengthValidator(max_length=3)
        result = validator.validate("test", ValidationContext())
        
        assert not result.is_valid
        assert "at most 3 characters" in result.errors[0]
    
    def test_string_length_validator_non_string(self):
        validator = StringLengthValidator()
        result = validator.validate(123, ValidationContext())
        
        assert not result.is_valid
        assert "must be a string" in result.errors[0]
    
    def test_regex_validator_success(self):
        validator = RegexValidator(r'^[a-z]+$')
        result = validator.validate("test", ValidationContext())
        
        assert result.is_valid
    
    def test_regex_validator_failure(self):
        validator = RegexValidator(r'^[a-z]+$')
        result = validator.validate("Test123", ValidationContext())
        
        assert not result.is_valid
        assert "must match pattern" in result.errors[0]
    
    def test_regex_validator_custom_error(self):
        validator = RegexValidator(r'^[a-z]+$', "Must be lowercase letters only")
        result = validator.validate("Test123", ValidationContext())
        
        assert not result.is_valid
        assert "Must be lowercase letters only" in result.errors[0]
    
    def test_regex_validator_non_string(self):
        validator = RegexValidator(r'^[a-z]+$')
        result = validator.validate(123, ValidationContext())
        
        assert not result.is_valid
        assert "must be a string" in result.errors[0]