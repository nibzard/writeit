"""Unit tests for ContentValidationService.

Tests the content validation domain service for validating generated content
against rules, quality standards, and format requirements.
"""

import pytest
from unittest.mock import Mock

from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.services.content_validation_service import (
    ContentValidationService,
    ValidationSeverity,
    ValidationCategory,
    ValidationIssue,
    ValidationResult,
    ValidationContext,
    ContentValidationError,
    ValidationConfigurationError,
    FormatValidationError,
)
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat, ContentFormatEnum
from writeit.domains.content.value_objects.validation_rule import ValidationRule, ValidationRuleType


@pytest.fixture
def validation_service():
    """Create content validation service."""
    return ContentValidationService()


@pytest.fixture
def sample_markdown_content():
    """Create sample markdown content for testing."""
    return GeneratedContent(
        id=ContentId.generate(),
        content_text="""# Introduction

This is a sample article about machine learning. It contains multiple paragraphs
and proper markdown structure.

## What is Machine Learning?

Machine learning is a subset of artificial intelligence that focuses on algorithms
that can learn from data without being explicitly programmed.

### Key Concepts

- Supervised learning
- Unsupervised learning  
- Reinforcement learning

## Applications

Machine learning has many applications in:

1. Healthcare
2. Finance
3. Technology

## Conclusion

Machine learning continues to evolve and impact various industries.
""",
        template_name=TemplateName.from_user_input("ml-article"),
        content_type=ContentType.from_string("article"),
        format=ContentFormat.from_string("markdown")
    )


@pytest.fixture
def sample_json_content():
    """Create sample JSON content for testing."""
    return GeneratedContent(
        id=ContentId.generate(),
        content_text='{"title": "Sample Article", "content": "This is content", "tags": ["ml", "ai"]}',
        template_name=TemplateName.from_user_input("json-output"),
        content_type=ContentType.from_string("api_docs"),
        format=ContentFormat.from_string("json")
    )


@pytest.fixture
def malformed_json_content():
    """Create malformed JSON content for testing."""
    return GeneratedContent(
        id=ContentId.generate(),
        content_text='{"title": "Sample Article", "content": "Missing closing brace"',
        template_name=TemplateName.from_user_input("json-output"),
        content_type=ContentType.from_string("api_docs"),
        format=ContentFormat.from_string("json")
    )


@pytest.fixture
def basic_validation_context():
    """Create basic validation context."""
    rules = [
        ValidationRule.length_min(100),
        ValidationRule.word_count_min(20),
        ValidationRule.markdown_valid()
    ]
    return ValidationContext(
        rules=rules,
        content_type=ContentType.from_string("article"),
        content_format=ContentFormat.from_string("markdown"),
        strict_mode=True
    )


@pytest.fixture
def permissive_validation_context():
    """Create permissive validation context."""
    rules = [
        ValidationRule.length_min(50),
        ValidationRule.word_count_min(10)
    ]
    return ValidationContext(
        rules=rules,
        content_type=ContentType.from_string("article"),
        content_format=ContentFormat.from_string("markdown"),
        strict_mode=False
    )


class TestContentValidationService:
    """Test suite for ContentValidationService."""
    
    @pytest.mark.asyncio
    async def test_init(self, validation_service):
        """Test service initialization."""
        assert validation_service._format_validators is not None
        assert ContentFormatEnum.MARKDOWN.value in validation_service._format_validators
        assert ContentFormatEnum.JSON.value in validation_service._format_validators
        assert validation_service._validation_cache == {}
    
    @pytest.mark.asyncio
    async def test_validate_content_success(
        self, 
        validation_service, 
        sample_markdown_content, 
        basic_validation_context
    ):
        """Test successful content validation."""
        result = await validation_service.validate_content(
            sample_markdown_content, 
            basic_validation_context
        )
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.content_id == str(sample_markdown_content.id)
        assert len(result.rules_applied) > 0
        assert ValidationRuleType.LENGTH_MIN in result.rules_applied
        assert ValidationRuleType.WORD_COUNT_MIN in result.rules_applied
    
    @pytest.mark.asyncio
    async def test_validate_content_length_failure(
        self, 
        validation_service, 
        basic_validation_context
    ):
        """Test content validation failure due to length."""
        short_content = GeneratedContent(
            id=ContentId.generate(),
            content_text="Too short",  # Only 9 characters
            template_name=TemplateName.from_user_input("test"),
            content_type=ContentType.from_string("article"),
            format=ContentFormat.from_string("markdown")
        )
        
        result = await validation_service.validate_content(short_content, basic_validation_context)
        
        assert result.is_valid is False
        assert result.has_errors is True
        assert any(
            issue.rule_type == ValidationRuleType.LENGTH_MIN
            for issue in result.issues
        )
    
    @pytest.mark.asyncio
    async def test_validate_content_word_count_failure(
        self, 
        validation_service,
        basic_validation_context
    ):
        """Test content validation failure due to word count."""
        content = GeneratedContent(
            id=ContentId.generate(),
            content_text="A" * 200,  # Long enough in characters but only one word
            template_name=TemplateName.from_user_input("test"),
            content_type=ContentType.from_string("article"),
            format=ContentFormat.from_string("markdown")
        )
        
        result = await validation_service.validate_content(content, basic_validation_context)
        
        assert result.is_valid is False
        assert any(
            issue.rule_type == ValidationRuleType.WORD_COUNT_MIN
            for issue in result.issues
        )
    
    @pytest.mark.asyncio
    async def test_validate_content_warnings_strict_mode(
        self, 
        validation_service, 
        sample_markdown_content
    ):
        """Test that warnings make content invalid in strict mode."""
        # Create context with a rule that will generate warnings
        rules = [
            ValidationRule.word_count_max(50)  # Content has more than 50 words
        ]
        strict_context = ValidationContext(
            rules=rules,
            content_type=ContentType.from_string("article"),
            content_format=ContentFormat.from_string("markdown"),
            strict_mode=True
        )
        
        result = await validation_service.validate_content(sample_markdown_content, strict_context)
        
        assert result.is_valid is False  # Warnings make it invalid in strict mode
        assert result.has_warnings is True
    
    @pytest.mark.asyncio
    async def test_validate_content_warnings_permissive_mode(
        self, 
        validation_service, 
        sample_markdown_content,
        permissive_validation_context
    ):
        """Test that warnings don't make content invalid in permissive mode."""
        # Add a rule that will generate warnings
        permissive_validation_context.rules.append(
            ValidationRule.word_count_max(50)  # Content has more than 50 words
        )
        
        result = await validation_service.validate_content(
            sample_markdown_content, 
            permissive_validation_context
        )
        
        assert result.is_valid is True  # Warnings don't affect validity in permissive mode
        assert result.has_warnings is True
    
    @pytest.mark.asyncio
    async def test_validate_format_only_valid_json(self, validation_service):
        """Test format-only validation with valid JSON."""
        json_text = '{"valid": "json", "number": 42}'
        content_format = ContentFormat.from_string("json")
        
        result = await validation_service.validate_format_only(json_text, content_format)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    @pytest.mark.asyncio
    async def test_validate_format_only_invalid_json(self, validation_service):
        """Test format-only validation with invalid JSON."""
        json_text = '{"invalid": "json", "missing": "brace"'
        content_format = ContentFormat.from_string("json")
        
        result = await validation_service.validate_format_only(json_text, content_format)
        
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any(
            issue.category == ValidationCategory.FORMAT
            for issue in result.issues
        )
    
    @pytest.mark.asyncio
    async def test_validate_format_only_valid_markdown(self, validation_service):
        """Test format-only validation with valid markdown."""
        markdown_text = """# Title\n\nThis is a paragraph with [link](http://example.com).\n\n```python\ncode_block()\n```"""
        content_format = ContentFormat.from_string("markdown")
        
        result = await validation_service.validate_format_only(markdown_text, content_format)
        
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_format_only_invalid_markdown(self, validation_service):
        """Test format-only validation with invalid markdown."""
        markdown_text = "# Title\n\nUnclosed code block:\n```python\ncode_without_closing"
        content_format = ContentFormat.from_string("markdown")
        
        result = await validation_service.validate_format_only(markdown_text, content_format)
        
        assert result.is_valid is False
        assert any(
            "code block" in issue.message.lower()
            for issue in result.issues
        )
    
    @pytest.mark.asyncio
    async def test_create_validation_context(self, validation_service):
        """Test validation context creation."""
        rules = [ValidationRule.length_min(100)]
        content_type = ContentType.from_string("article")
        content_format = ContentFormat.from_string("markdown")
        
        context = await validation_service.create_validation_context(
            rules=rules,
            content_type=content_type,
            content_format=content_format,
            strict_mode=False
        )
        
        assert context.rules == rules
        assert context.content_type == content_type
        assert context.content_format == content_format
        assert context.strict_mode is False
    
    @pytest.mark.asyncio
    async def test_get_recommended_rules_article_markdown(self, validation_service):
        """Test getting recommended rules for article in markdown format."""
        content_type = ContentType.from_string("article")
        content_format = ContentFormat.from_string("markdown")
        
        rules = await validation_service.get_recommended_rules(content_type, content_format)
        
        assert len(rules) > 0
        rule_types = [rule.type for rule in rules]
        assert ValidationRuleType.LENGTH_MIN in rule_types
        assert ValidationRuleType.MARKDOWN_VALID in rule_types
        assert ValidationRuleType.WORD_COUNT_MIN in rule_types
    
    @pytest.mark.asyncio
    async def test_get_recommended_rules_json_format(self, validation_service):
        """Test getting recommended rules for JSON format."""
        content_type = ContentType.from_string("api_docs")
        content_format = ContentFormat.from_string("json")
        
        rules = await validation_service.get_recommended_rules(content_type, content_format)
        
        rule_types = [rule.type for rule in rules]
        assert ValidationRuleType.JSON_SCHEMA in rule_types
    
    @pytest.mark.asyncio
    async def test_validate_configuration_error_no_rules(self, validation_service):
        """Test validation configuration error when no rules provided."""
        invalid_context = ValidationContext(
            rules=[],  # Empty rules
            content_type=ContentType.from_string("article"),
            content_format=ContentFormat.from_string("markdown")
        )
        
        content = Mock()
        content.id = ContentId.generate()
        
        with pytest.raises(ValidationConfigurationError) as exc_info:
            await validation_service.validate_content(content, invalid_context)
        
        assert "No validation rules specified" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_keyword_presence_validation(self, validation_service):
        """Test keyword presence validation."""
        content = GeneratedContent(
            id=ContentId.generate(),
            content_text="This is an article about artificial intelligence and neural networks.",
            template_name=TemplateName.from_user_input("test"),
            content_type=ContentType.from_string("article"),
            format=ContentFormat.from_string("markdown")
        )
        
        # Rule requiring specific keywords
        rules = [
            ValidationRule.create(
                type=ValidationRuleType.KEYWORD_PRESENCE,
                value=["machine learning", "python"],  # Missing keywords
                description="Required keywords"
            )
        ]
        
        context = ValidationContext(
            rules=rules,
            content_type=ContentType.from_string("article"),
            content_format=ContentFormat.from_string("markdown")
        )
        
        result = await validation_service.validate_content(content, context)
        
        assert any(
            issue.rule_type == ValidationRuleType.KEYWORD_PRESENCE
            for issue in result.issues
        )
    
    @pytest.mark.asyncio
    async def test_repetition_detection(self, validation_service, basic_validation_context):
        """Test detection of excessive word repetition."""
        repetitive_content = GeneratedContent(
            id=ContentId.generate(),
            content_text=" ".join(["machine"] * 20 + ["learning"] * 80),  # Very repetitive
            template_name=TemplateName.from_user_input("test"),
            content_type=ContentType.from_string("article"),
            format=ContentFormat.from_string("markdown")
        )
        
        result = await validation_service.validate_content(repetitive_content, basic_validation_context)
        
        # Should detect repetition in quality validation
        quality_issues = result.get_issues_by_category(ValidationCategory.CONTENT_QUALITY)
        assert len(quality_issues) > 0
        assert any("frequently" in issue.message for issue in quality_issues)
    
    def test_clear_cache(self, validation_service):
        """Test cache clearing."""
        # Add some dummy cache data
        validation_service._validation_cache["test"] = Mock()
        
        validation_service.clear_cache()
        
        assert validation_service._validation_cache == {}
    
    def test_get_cache_stats(self, validation_service):
        """Test cache statistics."""
        # Add some dummy cache data
        validation_service._validation_cache["test1"] = Mock()
        validation_service._validation_cache["test2"] = Mock()
        
        stats = validation_service.get_cache_stats()
        
        assert stats["cached_validations"] == 2


class TestValidationResult:
    """Test suite for ValidationResult."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        issues = [
            ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Format error",
                rule_type=ValidationRuleType.MARKDOWN_VALID
            ),
            ValidationIssue(
                category=ValidationCategory.CONTENT_QUALITY,
                severity=ValidationSeverity.WARNING,
                message="Quality warning",
                rule_type=ValidationRuleType.WORD_COUNT_MIN
            )
        ]
        
        result = ValidationResult(
            is_valid=False,
            issues=issues,
            content_id="test-id"
        )
        
        assert result.is_valid is False
        assert result.issues == issues
        assert result.content_id == "test-id"
    
    def test_has_errors_property(self):
        """Test has_errors property."""
        # With errors
        error_issue = ValidationIssue(
            category=ValidationCategory.FORMAT,
            severity=ValidationSeverity.ERROR,
            message="Error",
            rule_type=ValidationRuleType.JSON_SCHEMA
        )
        result_with_errors = ValidationResult(True, [error_issue])
        assert result_with_errors.has_errors is True
        
        # Without errors
        warning_issue = ValidationIssue(
            category=ValidationCategory.CONTENT_QUALITY,
            severity=ValidationSeverity.WARNING,
            message="Warning",
            rule_type=ValidationRuleType.WORD_COUNT_MAX
        )
        result_without_errors = ValidationResult(True, [warning_issue])
        assert result_without_errors.has_errors is False
    
    def test_has_warnings_property(self):
        """Test has_warnings property."""
        warning_issue = ValidationIssue(
            category=ValidationCategory.CONTENT_QUALITY,
            severity=ValidationSeverity.WARNING,
            message="Warning",
            rule_type=ValidationRuleType.WORD_COUNT_MAX
        )
        result = ValidationResult(True, [warning_issue])
        assert result.has_warnings is True
    
    def test_error_and_warning_counts(self):
        """Test error and warning count properties."""
        issues = [
            ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Error 1",
                rule_type=ValidationRuleType.JSON_SCHEMA
            ),
            ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.CRITICAL,
                message="Critical error",
                rule_type=ValidationRuleType.YAML_VALID
            ),
            ValidationIssue(
                category=ValidationCategory.CONTENT_QUALITY,
                severity=ValidationSeverity.WARNING,
                message="Warning 1",
                rule_type=ValidationRuleType.WORD_COUNT_MAX
            ),
            ValidationIssue(
                category=ValidationCategory.CONTENT_QUALITY,
                severity=ValidationSeverity.WARNING,
                message="Warning 2",
                rule_type=ValidationRuleType.LENGTH_MAX
            )
        ]
        
        result = ValidationResult(False, issues)
        
        assert result.error_count == 2  # ERROR + CRITICAL
        assert result.warning_count == 2
    
    def test_get_issues_by_category(self):
        """Test getting issues by category."""
        format_issue = ValidationIssue(
            category=ValidationCategory.FORMAT,
            severity=ValidationSeverity.ERROR,
            message="Format error",
            rule_type=ValidationRuleType.MARKDOWN_VALID
        )
        quality_issue = ValidationIssue(
            category=ValidationCategory.CONTENT_QUALITY,
            severity=ValidationSeverity.WARNING,
            message="Quality warning",
            rule_type=ValidationRuleType.WORD_COUNT_MIN
        )
        
        result = ValidationResult(False, [format_issue, quality_issue])
        
        format_issues = result.get_issues_by_category(ValidationCategory.FORMAT)
        assert len(format_issues) == 1
        assert format_issues[0] == format_issue
        
        quality_issues = result.get_issues_by_category(ValidationCategory.CONTENT_QUALITY)
        assert len(quality_issues) == 1
        assert quality_issues[0] == quality_issue
    
    def test_get_issues_by_severity(self):
        """Test getting issues by severity."""
        error_issue = ValidationIssue(
            category=ValidationCategory.FORMAT,
            severity=ValidationSeverity.ERROR,
            message="Error",
            rule_type=ValidationRuleType.JSON_SCHEMA
        )
        warning_issue = ValidationIssue(
            category=ValidationCategory.CONTENT_QUALITY,
            severity=ValidationSeverity.WARNING,
            message="Warning",
            rule_type=ValidationRuleType.WORD_COUNT_MAX
        )
        
        result = ValidationResult(False, [error_issue, warning_issue])
        
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        assert len(errors) == 1
        assert errors[0] == error_issue
        
        warnings = result.get_issues_by_severity(ValidationSeverity.WARNING)
        assert len(warnings) == 1
        assert warnings[0] == warning_issue


class TestValidationContext:
    """Test suite for ValidationContext."""
    
    def test_validation_context_creation(self):
        """Test ValidationContext creation."""
        rules = [ValidationRule.length_min(100)]
        content_type = ContentType.from_string("article")
        content_format = ContentFormat.from_string("markdown")
        
        context = ValidationContext(
            rules=rules,
            content_type=content_type,
            content_format=content_format,
            strict_mode=False
        )
        
        assert context.rules == rules
        assert context.content_type == content_type
        assert context.content_format == content_format
        assert context.strict_mode is False
        assert context.custom_validators == {}
        assert context.metadata == {}


class TestValidationIssue:
    """Test suite for ValidationIssue."""
    
    def test_validation_issue_creation(self):
        """Test ValidationIssue creation."""
        issue = ValidationIssue(
            category=ValidationCategory.FORMAT,
            severity=ValidationSeverity.ERROR,
            message="Invalid format",
            rule_type=ValidationRuleType.JSON_SCHEMA,
            location="line 5",
            suggestion="Fix JSON syntax",
            metadata={"error_code": "JSON001"}
        )
        
        assert issue.category == ValidationCategory.FORMAT
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.message == "Invalid format"
        assert issue.rule_type == ValidationRuleType.JSON_SCHEMA
        assert issue.location == "line 5"
        assert issue.suggestion == "Fix JSON syntax"
        assert issue.metadata["error_code"] == "JSON001"


class TestContentValidationError:
    """Test suite for ContentValidationError."""
    
    def test_content_validation_error_creation(self):
        """Test ContentValidationError creation."""
        error = ContentValidationError(
            "Validation failed",
            content_id="test-id",
            validation_context={"rule": "length_min"}
        )
        
        assert str(error) == "Validation failed"
        assert error.content_id == "test-id"
        assert error.validation_context["rule"] == "length_min"
    
    def test_content_validation_error_minimal(self):
        """Test ContentValidationError creation with minimal arguments."""
        error = ContentValidationError("Validation failed")
        
        assert str(error) == "Validation failed"
        assert error.content_id is None
        assert error.validation_context == {}