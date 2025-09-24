# ABOUTME: Integration tests for validation system with real template files
# ABOUTME: Tests the validation system against actual pipeline templates and style primers
import pytest
from pathlib import Path
from writeit.shared.validation import PipelineValidator, StyleValidator


class TestValidationIntegration:
    """Integration tests for validation system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline_validator = PipelineValidator()
        self.style_validator = StyleValidator()
        self.repo_root = Path(__file__).parent.parent.parent

    def test_tech_article_pipeline_validates(self):
        """Test that tech-article.yaml template validates successfully."""
        template_path = self.repo_root / "templates" / "tech-article.yaml"

        if not template_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        result = self.pipeline_validator.validate_file(template_path)

        # Print details if validation fails
        if not result.is_valid:
            print(f"\n{result.format_detailed()}")

        assert result.is_valid, (
            f"tech-article.yaml should be valid. Issues: {[issue.message for issue in result.issues if issue.is_error]}"
        )

        # Check expected metadata
        assert result.metadata["step_count"] >= 4  # Should have multiple steps
        assert result.metadata["llm_step_count"] >= 3  # Should have multiple LLM steps
        assert result.metadata["input_count"] >= 1  # Should have inputs

    def test_quick_article_pipeline_validates(self):
        """Test that quick-article.yaml template validates successfully."""
        template_path = self.repo_root / "templates" / "quick-article.yaml"

        if not template_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        result = self.pipeline_validator.validate_file(template_path)

        # Print details if validation fails
        if not result.is_valid:
            print(f"\n{result.format_detailed()}")

        assert result.is_valid, (
            f"quick-article.yaml should be valid. Issues: {[issue.message for issue in result.issues if issue.is_error]}"
        )

        # Check expected metadata for simple template
        assert result.metadata["step_count"] >= 3  # Should have at least 3 steps
        assert result.metadata["llm_step_count"] >= 2  # Should have multiple LLM steps

    def test_technical_expert_style_validates(self):
        """Test that technical-expert.yaml style validates successfully."""
        # Try multiple possible locations
        possible_paths = [
            self.repo_root / "styles" / "technical-expert.yaml",
            Path.home() / ".writeit" / "styles" / "technical-expert.yaml",
        ]

        style_path = None
        for path in possible_paths:
            if path.exists():
                style_path = path
                break

        if not style_path:
            pytest.skip("technical-expert.yaml style not found in expected locations")

        result = self.style_validator.validate_file(style_path)

        # Print details if validation fails
        if not result.is_valid:
            print(f"\n{result.format_detailed()}")

        assert result.is_valid, (
            f"technical-expert.yaml should be valid. Issues: {[issue.message for issue in result.issues if issue.is_error]}"
        )

        # Check expected metadata
        assert result.metadata["has_voice_section"]
        assert result.metadata["section_count"] >= 4  # Should have main sections

    def test_conversational_blog_style_validates(self):
        """Test that conversational-blog.yaml style validates successfully."""
        possible_paths = [
            self.repo_root / "styles" / "conversational-blog.yaml",
            Path.home() / ".writeit" / "styles" / "conversational-blog.yaml",
        ]

        style_path = None
        for path in possible_paths:
            if path.exists():
                style_path = path
                break

        if not style_path:
            pytest.skip(
                "conversational-blog.yaml style not found in expected locations"
            )

        result = self.style_validator.validate_file(style_path)

        # Print details if validation fails
        if not result.is_valid:
            print(f"\n{result.format_detailed()}")

        assert result.is_valid, (
            f"conversational-blog.yaml should be valid. Issues: {[issue.message for issue in result.issues if issue.is_error]}"
        )

        assert result.metadata["has_voice_section"]
        assert result.metadata["section_count"] >= 4

    def test_business_executive_style_validates(self):
        """Test that business-executive.yaml style validates successfully."""
        possible_paths = [
            self.repo_root / "styles" / "business-executive.yaml",
            Path.home() / ".writeit" / "styles" / "business-executive.yaml",
        ]

        style_path = None
        for path in possible_paths:
            if path.exists():
                style_path = path
                break

        if not style_path:
            pytest.skip("business-executive.yaml style not found")

        result = self.style_validator.validate_file(style_path)

        # Print details if validation fails
        if not result.is_valid:
            print(f"\n{result.format_detailed()}")

        assert result.is_valid, (
            f"business-executive.yaml should be valid. Issues: {[issue.message for issue in result.issues if issue.is_error]}"
        )

    def test_file_type_detection(self):
        """Test automatic file type detection."""
        from writeit.cli.main import detect_file_type

        # Test pipeline detection
        template_path = self.repo_root / "templates" / "tech-article.yaml"
        if template_path.exists():
            detected_type = detect_file_type(template_path)
            assert detected_type == "pipeline", (
                f"Expected 'pipeline' but got '{detected_type}'"
            )

        # Test style detection
        style_paths = [
            self.repo_root / "styles" / "technical-expert.yaml",
            Path.home() / ".writeit" / "styles" / "technical-expert.yaml",
        ]

        for style_path in style_paths:
            if style_path.exists():
                detected_type = detect_file_type(style_path)
                assert detected_type == "style", (
                    f"Expected 'style' but got '{detected_type}'"
                )
                break

    def test_validation_system_comprehensive(self):
        """Test validation system with multiple files."""
        from writeit.shared.validation import ValidationSummary

        results = []

        # Validate all available templates
        template_dir = self.repo_root / "templates"
        if template_dir.exists():
            for template_file in template_dir.glob("*.yaml"):
                result = self.pipeline_validator.validate_file(template_file)
                results.append(result)

        # Validate all available styles
        style_dirs = [self.repo_root / "styles", Path.home() / ".writeit" / "styles"]

        for style_dir in style_dirs:
            if style_dir.exists():
                for style_file in style_dir.glob("*.yaml"):
                    result = self.style_validator.validate_file(style_file)
                    results.append(result)

        if not results:
            pytest.skip("No template or style files found for comprehensive validation")

        summary = ValidationSummary(results)

        # Print summary for visibility
        print(f"\n{summary.format_summary()}")

        if summary.failed_files > 0:
            print(f"\n{summary.format_detailed()}")

        # All our shipped templates and styles should be valid
        assert summary.failed_files == 0, (
            f"All shipped templates and styles should be valid. {summary.failed_files} files failed validation."
        )
