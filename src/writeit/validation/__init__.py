# ABOUTME: WriteIt validation module
# ABOUTME: Validates pipeline templates and style primers for quality and correctness
# DEPRECATED: This module is deprecated. Use writeit.shared.validation instead.

from writeit.shared.validation import (
    PipelineValidator,
    StyleValidator,
    TemplateValidationResult as ValidationResult,
    ValidationIssue,
    IssueType,
    ValidationSummary,
)

__all__ = [
    "PipelineValidator",
    "StyleValidator",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSummary",
    "IssueType",
]
