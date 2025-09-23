"""Pipeline validation service.

Provides comprehensive validation logic for pipeline templates,
including structural validation, business rule enforcement,
and compatibility checking.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Any, Optional, Tuple
from enum import Enum

from ..entities.pipeline_template import PipelineTemplate, PipelineStepTemplate, PipelineInput
from ..value_objects.pipeline_id import PipelineId
from ..value_objects.step_id import StepId
from ..value_objects.prompt_template import PromptTemplate
from ..value_objects.model_preference import ModelPreference, ModelProvider


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    ERROR = "error"  # Blocks execution
    WARNING = "warning"  # Potential issues
    INFO = "info"  # Recommendations


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    severity: ValidationSeverity
    message: str
    location: str  # e.g., "step.outline", "input.topic"
    suggestion: Optional[str] = None
    code: Optional[str] = None  # Error code for programmatic handling

    def __str__(self) -> str:
        """String representation."""
        prefix = self.severity.value.upper()
        result = f"[{prefix}] {self.location}: {self.message}"
        if self.suggestion:
            result += f" Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Complete validation result."""
    issues: List[ValidationIssue]
    is_valid: bool
    summary: str
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    @property
    def info(self) -> List[ValidationIssue]:
        """Get only info-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.INFO]
    
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return len(self.warnings) > 0


class PipelineValidationService:
    """Service for validating pipeline templates and related entities.
    
    Provides comprehensive validation beyond basic entity validation,
    including business rules, best practices, and compatibility checks.
    
    Examples:
        validator = PipelineValidationService()
        result = validator.validate_template(template)
        
        if result.has_errors():
            print("Validation failed:", result.errors)
        else:
            print("Template is valid")
    """
    
    def __init__(self) -> None:
        """Initialize validation service."""
        self._max_steps = 50
        self._max_inputs = 20
        self._max_template_length = 10000
        self._recommended_step_types = {'llm_generate', 'user_input', 'transform', 'validate'}
    
    def validate_template(self, template: PipelineTemplate) -> ValidationResult:
        """Validate a complete pipeline template.
        
        Args:
            template: Pipeline template to validate
            
        Returns:
            Comprehensive validation result
        """
        issues = []
        
        # Structural validation
        issues.extend(self._validate_structure(template))
        
        # Business rule validation
        issues.extend(self._validate_business_rules(template))
        
        # Step validation
        issues.extend(self._validate_steps(template))
        
        # Input validation
        issues.extend(self._validate_inputs(template))
        
        # Template consistency validation
        issues.extend(self._validate_template_consistency(template))
        
        # Performance and best practice validation
        issues.extend(self._validate_best_practices(template))
        
        # Security validation
        issues.extend(self._validate_security(template))
        
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        is_valid = not has_errors
        
        # Generate summary
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        info_count = len([i for i in issues if i.severity == ValidationSeverity.INFO])
        
        if is_valid:
            if warning_count > 0 or info_count > 0:
                summary = f"Valid with {warning_count} warnings, {info_count} suggestions"
            else:
                summary = "Valid - no issues found"
        else:
            summary = f"Invalid - {error_count} errors, {warning_count} warnings"
        
        return ValidationResult(
            issues=issues,
            is_valid=is_valid,
            summary=summary
        )
    
    def validate_step(self, step: PipelineStepTemplate, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate an individual pipeline step.
        
        Args:
            step: Step template to validate
            context: Optional context (available variables, etc.)
            
        Returns:
            Validation result for the step
        """
        issues = []
        
        # Basic step validation
        issues.extend(self._validate_step_structure(step))
        
        # Template validation
        issues.extend(self._validate_step_template(step))
        
        # Model preference validation
        issues.extend(self._validate_step_model_preference(step))
        
        # Context-specific validation
        if context:
            issues.extend(self._validate_step_context(step, context))
        
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        is_valid = not has_errors
        
        summary = f"Step '{step.name}' - {'Valid' if is_valid else 'Invalid'}"
        
        return ValidationResult(
            issues=issues,
            is_valid=is_valid,
            summary=summary
        )
    
    def validate_inputs(self, inputs: Dict[str, PipelineInput], user_values: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate pipeline inputs and optionally user-provided values.
        
        Args:
            inputs: Input definitions
            user_values: Optional user-provided values to validate
            
        Returns:
            Validation result for inputs
        """
        issues = []
        
        # Validate input definitions
        for key, input_def in inputs.items():
            issues.extend(self._validate_input_definition(key, input_def))
        
        # Validate user values if provided
        if user_values is not None:
            issues.extend(self._validate_user_inputs(inputs, user_values))
        
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        is_valid = not has_errors
        
        summary = f"Inputs - {'Valid' if is_valid else 'Invalid'}"
        
        return ValidationResult(
            issues=issues,
            is_valid=is_valid,
            summary=summary
        )
    
    def _validate_structure(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate basic template structure."""
        issues = []
        
        # Check step count
        if len(template.steps) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Pipeline must have at least one step",
                location="pipeline.steps",
                code="EMPTY_PIPELINE"
            ))
        elif len(template.steps) > self._max_steps:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Pipeline has {len(template.steps)} steps, consider breaking into smaller pipelines",
                location="pipeline.steps",
                suggestion=f"Keep pipelines under {self._max_steps} steps for maintainability",
                code="TOO_MANY_STEPS"
            ))
        
        # Check input count
        if len(template.inputs) > self._max_inputs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Pipeline has {len(template.inputs)} inputs, consider simplification",
                location="pipeline.inputs",
                suggestion=f"Keep pipelines under {self._max_inputs} inputs for usability",
                code="TOO_MANY_INPUTS"
            ))
        
        # Check for required metadata
        if not template.description:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Pipeline description is missing",
                location="pipeline.description",
                suggestion="Add a clear description for documentation",
                code="MISSING_DESCRIPTION"
            ))
        
        return issues
    
    def _validate_business_rules(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate business rules and constraints."""
        issues = []
        
        # Check for at least one LLM generation step
        llm_steps = [step for step in template.steps.values() if step.type == 'llm_generate']
        if not llm_steps:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Pipeline has no LLM generation steps",
                location="pipeline.steps",
                suggestion="Consider adding at least one llm_generate step",
                code="NO_LLM_STEPS"
            ))
        
        # Check for meaningful step progression
        execution_order = template.get_execution_order()
        if len(execution_order) > 1:
            first_step = template.steps[execution_order[0]]
            last_step = template.steps[execution_order[-1]]
            
            if first_step.type == last_step.type == 'llm_generate':
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Pipeline starts and ends with LLM generation",
                    location="pipeline.flow",
                    suggestion="Consider adding validation or transformation steps",
                    code="LLM_BOOKENDS"
                ))
        
        return issues
    
    def _validate_steps(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate all steps in the template."""
        issues = []
        
        for step_key, step in template.steps.items():
            step_issues = self._validate_step_structure(step)
            # Prefix location with step key
            for issue in step_issues:
                issue.location = f"step.{step_key}.{issue.location}"
            issues.extend(step_issues)
        
        # Validate step dependencies
        issues.extend(self._validate_step_dependencies(template))
        
        return issues
    
    def _validate_step_structure(self, step: PipelineStepTemplate) -> List[ValidationIssue]:
        """Validate individual step structure."""
        issues = []
        
        # Check step type
        if step.type not in self._recommended_step_types:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Unknown step type '{step.type}'",
                location="type",
                suggestion=f"Use one of {self._recommended_step_types}",
                code="UNKNOWN_STEP_TYPE"
            ))
        
        # Check name and description
        if len(step.name) < 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Step name is very short",
                location="name",
                suggestion="Use descriptive names for clarity",
                code="SHORT_NAME"
            ))
        
        if len(step.description) < 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Step description is brief",
                location="description",
                suggestion="Add more detailed description for documentation",
                code="BRIEF_DESCRIPTION"
            ))
        
        return issues
    
    def _validate_step_template(self, step: PipelineStepTemplate) -> List[ValidationIssue]:
        """Validate step's prompt template."""
        issues = []
        
        # Check template length
        if len(step.prompt_template.template) > self._max_template_length:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Prompt template is very long ({len(step.prompt_template.template)} chars)",
                location="prompt_template",
                suggestion=f"Consider breaking into smaller templates (limit: {self._max_template_length})",
                code="LONG_TEMPLATE"
            ))
        
        # Check for common template issues
        template_text = step.prompt_template.template.lower()
        
        if "please" in template_text:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Template contains 'please' - may be unnecessary for LLMs",
                location="prompt_template",
                suggestion="LLMs work well with direct instructions",
                code="POLITE_LANGUAGE"
            ))
        
        if len(step.prompt_template.variables) == 0 and step.type == 'llm_generate':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="LLM generation step has no template variables",
                location="prompt_template",
                suggestion="Consider using variables for dynamic content",
                code="NO_VARIABLES"
            ))
        
        return issues
    
    def _validate_step_model_preference(self, step: PipelineStepTemplate) -> List[ValidationIssue]:
        """Validate step's model preference."""
        issues = []
        
        # Check for model availability
        if not step.model_preference.has_fallbacks:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Step has no fallback models configured",
                location="model_preference",
                suggestion="Consider adding fallback models for reliability",
                code="NO_FALLBACKS"
            ))
        
        # Check for expensive models in simple tasks
        primary_model = step.model_preference.primary_model.lower()
        if "gpt-4" in primary_model and len(step.prompt_template.template) < 100:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Using powerful model for simple task",
                location="model_preference",
                suggestion="Consider using gpt-4o-mini for simple tasks",
                code="OVERENGINEERED_MODEL"
            ))
        
        return issues
    
    def _validate_step_dependencies(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate step dependency relationships."""
        issues = []
        
        # Check for orphaned steps (steps that don't use their dependencies)
        for step_key, step in template.steps.items():
            if step.depends_on:
                step_variables = step.prompt_template.variables
                
                # Check if step actually uses its dependencies
                uses_deps = False
                for dep in step.depends_on:
                    dep_key = dep.value
                    if f"steps.{dep_key}" in step.prompt_template.nested_variables:
                        uses_deps = True
                        break
                
                if not uses_deps:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Step declares dependencies but doesn't use them in template",
                        location=f"step.{step_key}.depends_on",
                        suggestion="Remove unused dependencies or reference them in template",
                        code="UNUSED_DEPENDENCIES"
                    ))
        
        # Check for long dependency chains
        execution_order = template.get_execution_order()
        if len(execution_order) > 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message=f"Long dependency chain ({len(execution_order)} steps)",
                location="pipeline.dependencies",
                suggestion="Consider parallel execution where possible",
                code="LONG_CHAIN"
            ))
        
        return issues
    
    def _validate_inputs(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate pipeline input definitions."""
        issues = []
        
        for key, input_def in template.inputs.items():
            issues.extend(self._validate_input_definition(key, input_def))
        
        # Check if inputs are actually used in steps
        all_step_variables = set()
        for step in template.steps.values():
            all_step_variables.update(step.prompt_template.variables)
        
        for input_key in template.inputs:
            if "inputs" not in all_step_variables and f"inputs.{input_key}" not in \
               set().union(*[step.prompt_template.nested_variables for step in template.steps.values()]):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Input '{input_key}' is defined but not used in any step",
                    location=f"input.{input_key}",
                    suggestion="Remove unused inputs or reference them in step templates",
                    code="UNUSED_INPUT"
                ))
        
        return issues
    
    def _validate_input_definition(self, key: str, input_def: PipelineInput) -> List[ValidationIssue]:
        """Validate a single input definition."""
        issues = []
        
        # Check for user-friendly labels
        if input_def.label == input_def.key:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message=f"Input label same as key",
                location=f"input.{key}.label",
                suggestion="Use a more user-friendly label",
                code="GENERIC_LABEL"
            ))
        
        # Check choice inputs
        if input_def.type == 'choice':
            if len(input_def.options) < 2:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Choice input must have at least 2 options",
                    location=f"input.{key}.options",
                    code="INSUFFICIENT_OPTIONS"
                ))
            elif len(input_def.options) > 10:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Choice input has many options ({len(input_def.options)})",
                    location=f"input.{key}.options",
                    suggestion="Consider grouping or using text input with validation",
                    code="TOO_MANY_OPTIONS"
                ))
        
        return issues
    
    def _validate_user_inputs(self, inputs: Dict[str, PipelineInput], user_values: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate user-provided input values."""
        issues = []
        
        # Check required inputs
        for key, input_def in inputs.items():
            if input_def.required and key not in user_values:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Required input '{key}' is missing",
                    location=f"user_input.{key}",
                    code="MISSING_REQUIRED"
                ))
            elif key in user_values and not input_def.validate_value(user_values[key]):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid value for input '{key}'",
                    location=f"user_input.{key}",
                    code="INVALID_VALUE"
                ))
        
        # Check for unexpected inputs
        for key in user_values:
            if key not in inputs:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unexpected input '{key}'",
                    location=f"user_input.{key}",
                    suggestion="Remove unused inputs",
                    code="UNEXPECTED_INPUT"
                ))
        
        return issues
    
    def _validate_template_consistency(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate consistency across the template."""
        issues = []
        
        # Check that all referenced variables are available
        available_vars = set(template.inputs.keys())
        
        execution_order = template.get_execution_order()
        for step_key in execution_order:
            step = template.steps[step_key]
            required_vars = step.prompt_template.variables
            
            # Check for undefined variables
            undefined_vars = required_vars - available_vars - {'inputs', 'steps', 'defaults'}
            for var in undefined_vars:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Step references undefined variable '{var}'",
                    location=f"step.{step_key}.prompt_template",
                    suggestion="Define the variable in inputs or previous steps",
                    code="UNDEFINED_VARIABLE"
                ))
            
            # Add this step's output to available variables for next steps
            available_vars.add(step_key)
        
        return issues
    
    def _validate_best_practices(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate against best practices and recommendations."""
        issues = []
        
        # Check for version semantics
        if template.version == "1.0.0" and not template.author:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Consider adding author information",
                location="pipeline.author",
                suggestion="Add author for better template attribution",
                code="MISSING_AUTHOR"
            ))
        
        # Check for tags
        if not template.tags:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="No tags defined for template",
                location="pipeline.tags",
                suggestion="Add tags for better discoverability",
                code="NO_TAGS"
            ))
        
        # Check for parallel execution opportunities
        parallel_groups = template.get_parallel_groups()
        if len(parallel_groups) == len(template.steps):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="All steps run sequentially",
                location="pipeline.steps",
                suggestion="Consider enabling parallel execution where possible",
                code="NO_PARALLELISM"
            ))
        
        return issues
    
    def _validate_security(self, template: PipelineTemplate) -> List[ValidationIssue]:
        """Validate security aspects of the template."""
        issues = []
        
        # Check for potential prompt injection patterns
        dangerous_patterns = [
            "ignore previous instructions",
            "forget everything",
            "system prompt",
            "jailbreak",
            "developer mode"
        ]
        
        for step_key, step in template.steps.items():
            template_lower = step.prompt_template.template.lower()
            for pattern in dangerous_patterns:
                if pattern in template_lower:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Template contains potentially dangerous pattern: '{pattern}'",
                        location=f"step.{step_key}.prompt_template",
                        suggestion="Review template for prompt injection vulnerabilities",
                        code="SECURITY_PATTERN"
                    ))
        
        # Check for overly permissive inputs
        for key, input_def in template.inputs.items():
            if input_def.type == 'text' and not input_def.max_length:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message=f"Text input '{key}' has no length limit",
                    location=f"input.{key}.max_length",
                    suggestion="Consider adding max_length for security",
                    code="NO_LENGTH_LIMIT"
                ))
        
        return issues
    
    def _validate_step_context(self, step: PipelineStepTemplate, context: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate step against execution context."""
        issues = []
        
        # Check if required variables are available in context
        available_vars = set(context.keys())
        required_vars = step.prompt_template.variables
        
        missing_vars = required_vars - available_vars
        for var in missing_vars:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Required variable '{var}' not available in context",
                location="context",
                code="MISSING_CONTEXT_VAR"
            ))
        
        return issues
