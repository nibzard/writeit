# ABOUTME: Unit tests for ValidationResult and related classes
# ABOUTME: Tests validation result formatting, issue management, and summary generation
from pathlib import Path
from writeit.shared.validation import (
    TemplateValidationResult as ValidationResult,
    ValidationIssue,
    ValidationSummary,
    IssueType,
)


class TestValidationIssue:
    """Test cases for ValidationIssue."""

    def test_issue_creation(self):
        """Test creating validation issues."""
        issue = ValidationIssue(
            issue_type=IssueType.ERROR,
            message="Test error message",
            location="test.location",
            line_number=42,
            suggestion="Fix the issue",
        )

        assert issue.issue_type == IssueType.ERROR
        assert issue.message == "Test error message"
        assert issue.location == "test.location"
        assert issue.line_number == 42
        assert issue.suggestion == "Fix the issue"

    def test_issue_type_properties(self):
        """Test issue type property checks."""
        error_issue = ValidationIssue(IssueType.ERROR, "Error message")
        warning_issue = ValidationIssue(IssueType.WARNING, "Warning message")
        info_issue = ValidationIssue(IssueType.INFO, "Info message")

        assert error_issue.is_error
        assert not error_issue.is_warning
        assert not error_issue.is_info

        assert not warning_issue.is_error
        assert warning_issue.is_warning
        assert not warning_issue.is_info

        assert not info_issue.is_error
        assert not info_issue.is_warning
        assert info_issue.is_info

    def test_issue_formatting(self):
        """Test issue formatting for display."""
        issue = ValidationIssue(
            issue_type=IssueType.WARNING,
            message="Test warning",
            location="test.section",
            line_number=10,
            suggestion="Try this fix",
        )

        formatted = issue.format()
        assert "⚠️" in formatted
        assert "Test warning" in formatted
        assert "test.section" in formatted
        assert "line 10" in formatted
        assert "💡 Try this fix" in formatted

    def test_issue_formatting_without_suggestions(self):
        """Test issue formatting without suggestions."""
        issue = ValidationIssue(
            issue_type=IssueType.ERROR, message="Test error", location="test.section"
        )

        formatted = issue.format(show_suggestions=False)
        assert "❌" in formatted
        assert "Test error" in formatted
        assert "test.section" in formatted
        assert "💡" not in formatted

    def test_issue_formatting_minimal(self):
        """Test issue formatting with minimal information."""
        issue = ValidationIssue(IssueType.INFO, "Simple info message")

        formatted = issue.format()
        assert "ℹ️" in formatted
        assert "Simple info message" in formatted


class TestValidationResult:
    """Test cases for ValidationResult."""

    def test_empty_result_creation(self):
        """Test creating empty validation result."""
        result = ValidationResult(
            file_path=Path("test.yaml"), is_valid=True, issues=[], metadata={}
        )

        assert result.file_path == Path("test.yaml")
        assert result.is_valid
        assert len(result.issues) == 0
        assert not result.has_errors
        assert not result.has_warnings
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.info_count == 0

    def test_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult(
            file_path=Path("test.yaml"),
            is_valid=True,  # Will be overridden by __post_init__
            issues=[],
            metadata={},
        )

        result.add_error("Test error 1")
        result.add_error("Test error 2", location="test.section")

        assert not result.is_valid  # Should be False due to errors
        assert result.has_errors
        assert result.error_count == 2
        assert result.warning_count == 0
        assert len(result.issues) == 2

    def test_result_with_warnings(self):
        """Test validation result with warnings only."""
        result = ValidationResult(
            file_path=Path("test.yaml"), is_valid=True, issues=[], metadata={}
        )

        result.add_warning("Test warning 1")
        result.add_warning("Test warning 2", suggestion="Fix this")

        assert result.is_valid  # Should still be valid with only warnings
        assert not result.has_errors
        assert result.has_warnings
        assert result.error_count == 0
        assert result.warning_count == 2
        assert len(result.issues) == 2

    def test_result_with_mixed_issues(self):
        """Test validation result with mixed issue types."""
        result = ValidationResult(
            file_path=Path("test.yaml"), is_valid=True, issues=[], metadata={}
        )

        result.add_error("Test error")
        result.add_warning("Test warning")
        result.add_info("Test info")

        assert not result.is_valid
        assert result.has_errors
        assert result.has_warnings
        assert result.error_count == 1
        assert result.warning_count == 1
        assert result.info_count == 1
        assert len(result.issues) == 3

    def test_result_summary_formatting(self):
        """Test validation result summary formatting."""
        result = ValidationResult(
            file_path=Path("test.yaml"), is_valid=True, issues=[], metadata={}
        )

        result.add_error("Test error")
        result.add_warning("Test warning")

        summary = result.format_summary()
        assert "❌" in summary
        assert "test.yaml" in summary
        assert "FAILED" in summary
        assert "1 error" in summary
        assert "1 warning" in summary

    def test_result_detailed_formatting(self):
        """Test validation result detailed formatting."""
        result = ValidationResult(
            file_path=Path("test.yaml"),
            is_valid=True,
            issues=[],
            metadata={"test_key": "test_value"},
        )

        result.add_warning("Test warning", suggestion="Fix this")

        detailed = result.format_detailed()
        assert "test.yaml" in detailed
        assert "Test warning" in detailed
        assert "Fix this" in detailed
        assert "📊 Metadata:" in detailed
        assert "test_key: test_value" in detailed

    def test_result_valid_summary(self):
        """Test validation result for valid file."""
        result = ValidationResult(
            file_path=Path("valid.yaml"), is_valid=True, issues=[], metadata={}
        )

        # Only add info, no errors or warnings
        result.add_info("Everything looks good")

        summary = result.format_summary()
        assert "✅" in summary
        assert "valid.yaml" in summary
        assert "PASSED" in summary


class TestValidationSummary:
    """Test cases for ValidationSummary."""

    def test_empty_summary(self):
        """Test validation summary with no results."""
        summary = ValidationSummary([])

        assert summary.total_files == 0
        assert summary.passed_files == 0
        assert summary.failed_files == 0
        assert summary.total_errors == 0
        assert summary.total_warnings == 0

    def test_summary_with_mixed_results(self):
        """Test validation summary with mixed results."""
        # Create passing result
        pass_result = ValidationResult(
            file_path=Path("pass.yaml"), is_valid=True, issues=[], metadata={}
        )
        pass_result.add_info("All good")

        # Create failing result
        fail_result = ValidationResult(
            file_path=Path("fail.yaml"), is_valid=True, issues=[], metadata={}
        )
        fail_result.add_error("Test error")
        fail_result.add_warning("Test warning")

        summary = ValidationSummary([pass_result, fail_result])

        assert summary.total_files == 2
        assert summary.passed_files == 1
        assert summary.failed_files == 1
        assert summary.total_errors == 1
        assert summary.total_warnings == 1

    def test_summary_formatting(self):
        """Test validation summary formatting."""
        # Create results
        result1 = ValidationResult(Path("file1.yaml"), True, [], {})
        result1.add_error("Error in file 1")

        result2 = ValidationResult(Path("file2.yaml"), True, [], {})
        result2.add_warning("Warning in file 2")

        summary = ValidationSummary([result1, result2])

        formatted = summary.format_summary()
        assert "❌" in formatted  # Should show failed icon
        assert "1/2 passed" in formatted
        assert "Errors: 1" in formatted
        assert "Warnings: 1" in formatted

    def test_summary_all_passed(self):
        """Test validation summary when all files pass."""
        result1 = ValidationResult(Path("file1.yaml"), True, [], {})
        result2 = ValidationResult(Path("file2.yaml"), True, [], {})

        summary = ValidationSummary([result1, result2])

        formatted = summary.format_summary()
        assert "✅" in formatted
        assert "2/2 passed" in formatted

    def test_detailed_summary_formatting(self):
        """Test detailed validation summary formatting."""
        # Create passing result
        pass_result = ValidationResult(Path("pass.yaml"), True, [], {})

        # Create failing result
        fail_result = ValidationResult(Path("fail.yaml"), True, [], {})
        fail_result.add_error("Critical error", suggestion="Fix this")

        summary = ValidationSummary([pass_result, fail_result])

        detailed = summary.format_detailed()

        # Should show passed and failed sections
        assert "✅ Passed:" in detailed
        assert "❌ Failed:" in detailed
        assert "pass.yaml" in detailed
        assert "fail.yaml" in detailed
        assert "Critical error" in detailed
        assert "Fix this" in detailed

    def test_detailed_summary_no_suggestions(self):
        """Test detailed summary without suggestions."""
        fail_result = ValidationResult(Path("fail.yaml"), True, [], {})
        fail_result.add_error("Error without suggestion")

        summary = ValidationSummary([fail_result])

        detailed = summary.format_detailed(show_suggestions=False)
        assert "fail.yaml" in detailed
        assert "Error without suggestion" in detailed
