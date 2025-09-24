"""Validation framework implementation."""

from typing import Any, Dict, List, TypeVar, Union

from .interfaces import ValidationContext, ValidationResult, ValidationRule

T = TypeVar('T')


class ValidationFramework:
    """Main validation framework for coordinating validation operations."""
    
    def __init__(self) -> None:
        self._validators: Dict[str, List[ValidationRule[Any]]] = {}
    
    def register_validator(self, entity_type: str, validator: ValidationRule[Any]) -> None:
        """Register a validator for a specific entity type."""
        if entity_type not in self._validators:
            self._validators[entity_type] = []
        self._validators[entity_type].append(validator)
    
    def validate(self, entity_type: str, value: Any, 
                context: ValidationContext) -> ValidationResult:
        """Validate a value using all registered validators for the entity type."""
        if entity_type not in self._validators:
            return ValidationResult.success()
        
        overall_result = ValidationResult.success()
        
        for validator in self._validators[entity_type]:
            result = validator.validate(value, context)
            overall_result = overall_result.combine(result)
            
            # Stop on first error if not in strict mode and error found
            if not context.strict_mode and not result.is_valid:
                break
        
        return overall_result
    
    def get_validators(self, entity_type: str) -> List[ValidationRule[Any]]:
        """Get all validators for a specific entity type."""
        return self._validators.get(entity_type, []).copy()


class CompositeValidationRule(ValidationRule[T]):
    """Combines multiple validation rules with logical operators."""
    
    def __init__(self, rules: List[ValidationRule[T]], operator: str = "AND"):
        if operator not in ("AND", "OR"):
            raise ValueError("Operator must be 'AND' or 'OR'")
        
        self._rules = rules.copy()
        self._operator = operator
    
    def validate(self, value: T, context: ValidationContext) -> ValidationResult:
        """Validate using composite logic."""
        if not self._rules:
            return ValidationResult.success()
        
        results = [rule.validate(value, context) for rule in self._rules]
        
        if self._operator == "AND":
            return self._combine_and(results)
        else:  # OR
            return self._combine_or(results)
    
    def _combine_and(self, results: List[ValidationResult]) -> ValidationResult:
        """Combine results with AND logic - all must be valid."""
        overall_result = ValidationResult.success()
        for result in results:
            overall_result = overall_result.combine(result)
        return overall_result
    
    def _combine_or(self, results: List[ValidationResult]) -> ValidationResult:
        """Combine results with OR logic - at least one must be valid."""
        # If any result is valid, the overall result is valid
        valid_results = [r for r in results if r.is_valid]
        
        if valid_results:
            # Take the first valid result and combine warnings
            overall_result = valid_results[0]
            for result in valid_results[1:]:
                overall_result = ValidationResult(
                    is_valid=True,
                    errors=overall_result.errors,
                    warnings=overall_result.warnings + result.warnings,
                    metadata={**overall_result.metadata, **result.metadata}
                )
            return overall_result
        else:
            # All failed, combine all errors
            all_errors = []
            all_warnings = []
            all_metadata = {}
            
            for result in results:
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
                all_metadata.update(result.metadata)
            
            return ValidationResult.failure(
                errors=all_errors,
                warnings=all_warnings,
                metadata=all_metadata
            )
    
    @property
    def description(self) -> str:
        """Description of the composite rule."""
        rule_descriptions = [rule.description for rule in self._rules]
        connector = " AND " if self._operator == "AND" else " OR "
        return f"({connector.join(rule_descriptions)})"