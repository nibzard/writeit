# ABOUTME: Validation result classes for WriteIt template validation
# ABOUTME: Defines data structures for validation issues, results, and reporting
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


class IssueType(Enum):
    """Types of validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    issue_type: IssueType
    message: str
    location: Optional[str] = None  # e.g., "steps.draft.prompt_template"
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    @property
    def is_error(self) -> bool:
        """Check if this is an error issue."""
        return self.issue_type == IssueType.ERROR

    @property
    def is_warning(self) -> bool:
        """Check if this is a warning issue."""
        return self.issue_type == IssueType.WARNING

    @property
    def is_info(self) -> bool:
        """Check if this is an info issue."""
        return self.issue_type == IssueType.INFO

    def format(self, show_suggestions: bool = True) -> str:
        """Format the issue for display."""
        icon = {"error": "❌", "warning": "⚠️ ", "info": "ℹ️ "}[self.issue_type.value]

        location_str = ""
        if self.location:
            location_str = f" at {self.location}"
        if self.line_number:
            location_str += f" (line {self.line_number})"

        base_message = f"{icon} {self.message}{location_str}"

        if show_suggestions and self.suggestion:
            base_message += f"\n   💡 {self.suggestion}"

        return base_message


@dataclass
class ValidationResult:
    """Results of validating a template file."""

    file_path: Path
    is_valid: bool
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]
    file_type: Optional[str] = None

    def __post_init__(self):
        """Ensure is_valid reflects the actual issues."""
        self.is_valid = not self.has_errors

    @property
    def has_errors(self) -> bool:
        """Check if there are any error issues."""
        return any(issue.is_error for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning issues."""
        return any(issue.is_warning for issue in self.issues)

    @property
    def error_count(self) -> int:
        """Count of error issues."""
        return len([issue for issue in self.issues if issue.is_error])

    @property
    def warning_count(self) -> int:
        """Count of warning issues."""
        return len([issue for issue in self.issues if issue.is_warning])

    @property
    def info_count(self) -> int:
        """Count of info issues."""
        return len([issue for issue in self.issues if issue.is_info])

    def add_error(
        self,
        message: str,
        location: Optional[str] = None,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add an error issue."""
        self.issues.append(
            ValidationIssue(IssueType.ERROR, message, location, line_number, suggestion)
        )
        self.is_valid = False

    def add_warning(
        self,
        message: str,
        location: Optional[str] = None,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a warning issue."""
        self.issues.append(
            ValidationIssue(
                IssueType.WARNING, message, location, line_number, suggestion
            )
        )

    def add_info(
        self,
        message: str,
        location: Optional[str] = None,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add an info issue."""
        self.issues.append(
            ValidationIssue(IssueType.INFO, message, location, line_number, suggestion)
        )

    def format_summary(self) -> str:
        """Format a summary of the validation results."""
        status_icon = "✅" if self.is_valid else "❌"
        status_text = "PASSED" if self.is_valid else "FAILED"

        summary = f"{status_icon} {self.file_path.name}: {status_text}"

        if self.issues:
            counts = []
            if self.error_count > 0:
                counts.append(
                    f"{self.error_count} error{'s' if self.error_count != 1 else ''}"
                )
            if self.warning_count > 0:
                counts.append(
                    f"{self.warning_count} warning{'s' if self.warning_count != 1 else ''}"
                )
            if self.info_count > 0:
                counts.append(f"{self.info_count} info")

            if counts:
                summary += f" ({', '.join(counts)})"

        return summary

    def format_detailed(self, show_suggestions: bool = True) -> str:
        """Format detailed validation results."""
        lines = [self.format_summary()]

        if self.issues:
            lines.append("")
            for issue in self.issues:
                lines.append(issue.format(show_suggestions))

        # Add metadata if available
        if self.metadata:
            lines.append("")
            lines.append("📊 Metadata:")
            for key, value in self.metadata.items():
                lines.append(f"   {key}: {value}")

        return "\n".join(lines)


@dataclass
class ValidationSummary:
    """Summary of validating multiple templates."""

    results: List[ValidationResult]

    @property
    def total_files(self) -> int:
        """Total number of files validated."""
        return len(self.results)

    @property
    def passed_files(self) -> int:
        """Number of files that passed validation."""
        return len([r for r in self.results if r.is_valid])

    @property
    def failed_files(self) -> int:
        """Number of files that failed validation."""
        return len([r for r in self.results if not r.is_valid])

    @property
    def total_errors(self) -> int:
        """Total error count across all files."""
        return sum(r.error_count for r in self.results)

    @property
    def total_warnings(self) -> int:
        """Total warning count across all files."""
        return sum(r.warning_count for r in self.results)

    def format_summary(self) -> str:
        """Format overall summary."""
        status_icon = "✅" if self.failed_files == 0 else "❌"

        lines = [
            f"{status_icon} Validation Summary",
            f"   Files: {self.passed_files}/{self.total_files} passed",
        ]

        if self.total_errors > 0:
            lines.append(f"   Errors: {self.total_errors}")
        if self.total_warnings > 0:
            lines.append(f"   Warnings: {self.total_warnings}")

        return "\n".join(lines)

    def format_detailed(self, show_suggestions: bool = True) -> str:
        """Format detailed results for all files."""
        lines = []

        # Group by status
        passed = [r for r in self.results if r.is_valid]
        failed = [r for r in self.results if not r.is_valid]

        if passed:
            lines.append("✅ Passed:")
            for result in passed:
                lines.append(f"   {result.format_summary()}")

        if failed:
            if passed:
                lines.append("")
            lines.append("❌ Failed:")
            for result in failed:
                lines.append(f"   {result.format_summary()}")
                if show_suggestions:
                    lines.append("")
                    lines.append(result.format_detailed(show_suggestions))
                    lines.append("")

        lines.append("")
        lines.append(self.format_summary())

        return "\n".join(lines)
