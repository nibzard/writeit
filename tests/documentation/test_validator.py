"""
Tests for documentation validator
"""

from writeit.docs import DocumentationValidator
from writeit.docs.models import (
    DocumentationSet,
    APIDocumentation,
    ModuleDocumentation,
    CLIDocumentation,
    APIEndpointDocumentation,
    CommandDocumentation,
    ParameterDocumentation,
    ValidationResult,
)


class TestDocumentationValidator:
    """Test documentation validation functionality"""

    def test_validator_initialization(self):
        """Test validator initializes correctly"""
        validator = DocumentationValidator()
        assert validator is not None

    def test_validate_empty_documentation(self):
        """Test validating empty documentation set"""
        validator = DocumentationValidator()
        empty_docs = DocumentationSet()

        result = validator.validate_all(empty_docs)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True  # Empty docs are technically valid
        assert result.coverage_percentage == 0.0

    def test_validate_api_documentation(self):
        """Test validating API documentation"""
        # Create sample API documentation
        api_docs = APIDocumentation(
            title="Test API",
            description="Test API Description",
            version="1.0.0",
            base_url="http://localhost:8000",
            endpoints=[
                APIEndpointDocumentation(
                    path="/test",
                    method="GET",
                    summary="Test endpoint",
                    description="Test endpoint description",
                    parameters=[],
                    status_codes={200: "Success"},
                )
            ],
            models=[],
        )

        docs = DocumentationSet(api_docs=api_docs)

        validator = DocumentationValidator()
        result = validator.validate_all(docs)

        assert isinstance(result, ValidationResult)
        # Should validate successfully with proper API docs
        assert len(result.errors) == 0

    def test_validate_invalid_api_endpoint(self):
        """Test validating invalid API endpoint"""
        # Create invalid endpoint (missing path)
        invalid_endpoint = APIEndpointDocumentation(
            path="",  # Invalid: empty path
            method="INVALID_METHOD",  # Invalid: bad method
            summary="",
            description="",
            parameters=[],
            status_codes={},
        )

        api_docs = APIDocumentation(
            title="Test API",
            description="",
            version="1.0.0",
            base_url="",
            endpoints=[invalid_endpoint],
            models=[],
        )

        docs = DocumentationSet(api_docs=api_docs)

        validator = DocumentationValidator()
        result = validator.validate_all(docs)

        assert isinstance(result, ValidationResult)
        assert len(result.errors) > 0  # Should have validation errors

        # Check for specific error types
        error_types = [error.type for error in result.errors]
        assert (
            "endpoint_missing_path" in error_types
            or "endpoint_invalid_path" in error_types
        )
        assert "endpoint_invalid_method" in error_types

    def test_validate_module_documentation(self):
        """Test validating module documentation"""
        from writeit.docs.models import ClassDocumentation, FunctionDocumentation

        # Create sample module documentation
        module_docs = [
            ModuleDocumentation(
                name="test.module",
                description="Test module description",
                purpose="Test module purpose",
                classes=[
                    ClassDocumentation(
                        name="TestClass",
                        description="Test class description",
                        purpose="Test class purpose",
                        methods=[
                            FunctionDocumentation(
                                name="test_method",
                                signature="test_method(self) -> None",
                                description="Test method description",
                                parameters=[],
                                return_type="None",
                                return_description="",
                            )
                        ],
                    )
                ],
                functions=[
                    FunctionDocumentation(
                        name="test_function",
                        signature="test_function() -> str",
                        description="Test function description",
                        parameters=[],
                        return_type="str",
                        return_description="Returns test string",
                    )
                ],
            )
        ]

        docs = DocumentationSet(module_docs=module_docs)

        validator = DocumentationValidator()
        result = validator.validate_all(docs)

        assert isinstance(result, ValidationResult)
        # Well-formed module docs should validate
        assert len(result.errors) == 0

    def test_validate_cli_documentation(self):
        """Test validating CLI documentation"""
        # Create sample CLI documentation
        cli_docs = CLIDocumentation(
            app_name="test-cli",
            description="Test CLI description",
            commands=[
                CommandDocumentation(
                    name="test-command",
                    description="Test command description",
                    usage="test-cli test-command [options]",
                    arguments=[
                        ParameterDocumentation(
                            name="arg1",
                            type_annotation="str",
                            description="Test argument",
                            required=True,
                        )
                    ],
                    options=[
                        ParameterDocumentation(
                            name="option1",
                            type_annotation="bool",
                            description="Test option",
                            required=False,
                            default_value="False",
                        )
                    ],
                    examples=["test-cli test-command value"],
                )
            ],
        )

        docs = DocumentationSet(cli_docs=cli_docs)

        validator = DocumentationValidator()
        result = validator.validate_all(docs)

        assert isinstance(result, ValidationResult)
        # Well-formed CLI docs should validate
        assert len(result.errors) == 0

    def test_validation_with_warnings(self):
        """Test validation that produces warnings"""
        # Create API documentation with missing descriptions (should warn)
        api_docs = APIDocumentation(
            title="Test API",
            description="",  # Empty description should warn
            version="1.0.0",
            base_url="http://localhost:8000",
            endpoints=[
                APIEndpointDocumentation(
                    path="/test",
                    method="GET",
                    summary="Test endpoint",
                    description="",  # Empty description should warn
                    parameters=[],
                    status_codes={200: "Success"},
                )
            ],
            models=[],
        )

        docs = DocumentationSet(api_docs=api_docs)

        validator = DocumentationValidator()
        result = validator.validate_all(docs)

        assert isinstance(result, ValidationResult)
        # Should be valid but have warnings
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert result.has_warnings is True

    def test_validation_result_properties(self):
        """Test ValidationResult properties"""
        result = ValidationResult(is_valid=True)

        # Test error/warning detection
        assert result.has_errors is False
        assert result.has_warnings is False

        result.add_error("test_error", "Test error message")
        assert result.has_errors is True
        assert len(result.errors) == 1

        result.add_warning("test_warning", "Test warning message")
        assert result.has_warnings is True
        assert len(result.warnings) == 1

        result.add_info("test_info", "Test info message")
        assert len(result.info) == 1

    def test_coverage_calculation(self):
        """Test documentation coverage calculation"""
        # Create documentation with mixed coverage
        from writeit.docs.models import ClassDocumentation, FunctionDocumentation

        module_docs = [
            ModuleDocumentation(
                name="good.module",
                description="Good description",
                purpose="Good purpose",
                classes=[
                    ClassDocumentation(
                        name="GoodClass",
                        description="Good class description",
                        purpose="Good class purpose",
                        methods=[],
                    )
                ],
                functions=[
                    FunctionDocumentation(
                        name="good_function",
                        signature="good_function() -> str",
                        description="Good function description",
                        parameters=[],
                        return_type="str",
                        return_description="Returns string",
                    )
                ],
            ),
            ModuleDocumentation(
                name="poor.module",
                description="",  # Poor: no description
                purpose="",  # Poor: no purpose
                classes=[],
                functions=[],
            ),
        ]

        docs = DocumentationSet(module_docs=module_docs)

        validator = DocumentationValidator()
        result = validator.validate_all(docs)

        assert isinstance(result, ValidationResult)
        # Coverage should be calculated
        assert result.total_items > 0
        assert result.documented_items >= 0
        assert result.coverage_percentage >= 0.0
        assert result.coverage_percentage <= 100.0
