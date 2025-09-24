"""Mock implementation of PipelineValidationService for testing."""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock
from dataclasses import dataclass

from writeit.domains.pipeline.services.pipeline_validation_service import (
    PipelineValidationService,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity
)
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId


class MockPipelineValidationService(PipelineValidationService):
    """Mock implementation of PipelineValidationService.
    
    Provides configurable validation behavior for testing pipeline
    validation scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock validation service."""
        self._mock = Mock()
        self._validation_results: Dict[str, ValidationResult] = {}
        self._configured_issues: List[ValidationIssue] = []
        self._should_fail = False
        
    def configure_validation_result(self, template_id: str, result: ValidationResult) -> None:
        """Configure validation result for specific template."""
        self._validation_results[template_id] = result
        
    def configure_issues(self, issues: List[ValidationIssue]) -> None:
        """Configure validation issues to return."""
        self._configured_issues = issues
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if validation should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._validation_results.clear()
        self._configured_issues.clear()
        self._should_fail = False
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def validate_template(self, template: PipelineTemplate) -> ValidationResult:
        """Validate pipeline template."""
        self._mock.validate_template(template)
        
        template_id = str(template.id.value)
        
        # Return configured result if available
        if template_id in self._validation_results:
            return self._validation_results[template_id]
            
        # Return result based on configuration
        if self._should_fail:
            issues = self._configured_issues or [
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Mock validation error",
                    location="template",
                    code="MOCK_ERROR"
                )
            ]
        else:
            issues = self._configured_issues
            
        return ValidationResult(
            is_valid=not self._should_fail,
            issues=issues,
            template_id=template.id
        )
        
    async def validate_structure(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate template structure."""
        self._mock.validate_structure(template)
        return self._configured_issues
        
    async def validate_dependencies(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate step dependencies."""
        self._mock.validate_dependencies(template)
        return self._configured_issues
        
    async def validate_template_variables(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate template variables."""
        self._mock.validate_template_variables(template)
        return self._configured_issues
        
    async def validate_model_preferences(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate model preferences."""
        self._mock.validate_model_preferences(template)
        return self._configured_issues
        
    async def check_circular_dependencies(self, template: PipelineTemplate) -> bool:
        """Check for circular dependencies."""
        self._mock.check_circular_dependencies(template)
        return not self._should_fail
        
    async def validate_step_configuration(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate individual step configurations."""
        self._mock.validate_step_configuration(template)
        return self._configured_issues
        
    async def validate_input_schema(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate input schema."""
        self._mock.validate_input_schema(template)
        return self._configured_issues
        
    async def validate_output_schema(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate output schema."""
        self._mock.validate_output_schema(template)
        return self._configured_issues
        
    async def validate_compatibility(self, template: PipelineTemplate, target_version: str) -> List[ValidationIssue]:
        """Validate compatibility with target version."""
        self._mock.validate_compatibility(template, target_version)
        return self._configured_issues
