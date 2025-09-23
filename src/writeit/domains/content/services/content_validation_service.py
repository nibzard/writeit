"""Content validation service.

Domain service responsible for validating generated content against defined
rules, quality standards, and format requirements.
"""

import json
import re
import yaml
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, Pattern
from xml.etree import ElementTree as ET

from ..entities.generated_content import GeneratedContent
from ..entities.template import Template
from ..value_objects.content_type import ContentType
from ..value_objects.content_format import ContentFormat, ContentFormatEnum
from ..value_objects.validation_rule import ValidationRule, ValidationRuleType
from ....shared.repository import RepositoryError


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    FORMAT = "format"
    STRUCTURE = "structure"
    CONTENT_QUALITY = "content_quality"
    BUSINESS_RULES = "business_rules"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"


@dataclass
class ValidationIssue:
    """Individual validation issue found during content validation."""
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    rule_type: ValidationRuleType
    location: Optional[str] = None  # Line number, character position, etc.
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of content validation operation."""
    is_valid: bool
    issues: List[ValidationIssue]
    content_id: Optional[str] = None
    validation_timestamp: Optional[str] = None
    rules_applied: List[ValidationRuleType] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has any errors or critical issues."""
        return any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for issue in self.issues
        )
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return any(
            issue.severity == ValidationSeverity.WARNING
            for issue in self.issues
        )
    
    @property
    def error_count(self) -> int:
        """Get count of error and critical issues."""
        return len([
            issue for issue in self.issues
            if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        ])
    
    @property
    def warning_count(self) -> int:
        """Get count of warning issues."""
        return len([
            issue for issue in self.issues
            if issue.severity == ValidationSeverity.WARNING
        ])
    
    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get all issues in a specific category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues with a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]


@dataclass
class ValidationContext:
    """Context for content validation operations."""
    rules: List[ValidationRule]
    content_type: ContentType
    content_format: ContentFormat
    strict_mode: bool = True
    custom_validators: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentValidationError(Exception):
    """Base exception for content validation operations."""
    
    def __init__(
        self, 
        message: str, 
        content_id: Optional[str] = None,
        validation_context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.content_id = content_id
        self.validation_context = validation_context or {}


class ValidationConfigurationError(ContentValidationError):
    """Raised when validation configuration is invalid."""
    pass


class FormatValidationError(ContentValidationError):
    """Raised when content format validation fails critically."""
    pass


class ContentValidationService:
    """Service for validating generated content against rules and standards.
    
    This service provides comprehensive content validation including:
    - Format validation (markdown, JSON, YAML, etc.)
    - Content quality validation (length, readability, etc.)
    - Business rule validation (custom rules, constraints)
    - Structure validation (headings, links, etc.)
    - Security validation (toxicity, profanity checks)
    
    Examples:
        service = ContentValidationService()
        
        # Define validation rules
        rules = [
            ValidationRule.word_count_range(500, 2000),
            ValidationRule.markdown_valid(),
            ValidationRule.readability_level(7.0, 12.0)
        ]
        
        context = ValidationContext(
            rules=rules,
            content_type=ContentType.from_string("article"),
            content_format=ContentFormat.markdown()
        )
        
        # Validate content
        result = await service.validate_content(generated_content, context)
        
        if result.is_valid:
            print("Content is valid!")
        else:
            for issue in result.issues:
                print(f"{issue.severity}: {issue.message}")
    """
    
    def __init__(self):
        """Initialize content validation service."""
        self._format_validators = {
            ContentFormatEnum.MARKDOWN.value: self._validate_markdown,
            ContentFormatEnum.JSON.value: self._validate_json,
            ContentFormatEnum.YAML.value: self._validate_yaml,
            ContentFormatEnum.XML.value: self._validate_xml,
            ContentFormatEnum.HTML.value: self._validate_html,
        }
        
        self._validation_cache: Dict[str, ValidationResult] = {}
    
    async def validate_content(
        self, 
        content: GeneratedContent, 
        context: ValidationContext
    ) -> ValidationResult:
        """Validate generated content against validation rules.
        
        Args:
            content: Generated content to validate
            context: Validation context with rules and settings
            
        Returns:
            Validation result with issues and overall status
            
        Raises:
            ContentValidationError: If validation operation fails
            ValidationConfigurationError: If validation config is invalid
        """
        try:
            issues: List[ValidationIssue] = []
            rules_applied: List[ValidationRuleType] = []
            
            # Validate configuration
            self._validate_context(context)
            
            # Format validation
            format_issues = await self._validate_format(content, context)
            issues.extend(format_issues)
            
            # Apply validation rules
            for rule in context.rules:
                rule_issues = await self._apply_validation_rule(content, rule, context)
                issues.extend(rule_issues)
                rules_applied.append(rule.type)
            
            # Structure validation
            structure_issues = await self._validate_structure(content, context)
            issues.extend(structure_issues)
            
            # Content quality validation
            quality_issues = await self._validate_content_quality(content, context)
            issues.extend(quality_issues)
            
            # Determine overall validity
            is_valid = not any(
                issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
                for issue in issues
            )
            
            # In strict mode, warnings also make content invalid
            if context.strict_mode and any(
                issue.severity == ValidationSeverity.WARNING for issue in issues
            ):
                is_valid = False
            
            return ValidationResult(
                is_valid=is_valid,
                issues=issues,
                content_id=str(content.id),
                rules_applied=rules_applied
            )
            
        except Exception as e:
            if isinstance(e, (ContentValidationError, ValidationConfigurationError)):
                raise
            
            raise ContentValidationError(
                f"Content validation failed: {e}",
                str(content.id) if content.id else None,
                {"original_error": str(e)}
            ) from e
    
    async def validate_format_only(
        self, 
        content_text: str, 
        content_format: ContentFormat
    ) -> ValidationResult:
        """Validate only the format of content text.
        
        Args:
            content_text: Content text to validate
            content_format: Expected format
            
        Returns:
            Validation result focusing on format issues
        """
        issues: List[ValidationIssue] = []
        
        if content_format.value in self._format_validators:
            validator = self._format_validators[content_format.value]
            format_issues = await validator(content_text)
            issues.extend(format_issues)
        
        is_valid = not any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for issue in issues
        )
        
        # Determine applied rule based on format
        applied_rule = ValidationRuleType.MARKDOWN_VALID  # Default
        if content_format.value == ContentFormatEnum.JSON.value:
            applied_rule = ValidationRuleType.JSON_SCHEMA
        elif content_format.value == ContentFormatEnum.YAML.value:
            applied_rule = ValidationRuleType.YAML_VALID
        elif content_format.value == ContentFormatEnum.XML.value:
            applied_rule = ValidationRuleType.XML_VALID
        elif content_format.value == ContentFormatEnum.HTML.value:
            applied_rule = ValidationRuleType.HTML_VALID
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            rules_applied=[applied_rule]
        )
    
    async def create_validation_context(
        self,
        rules: List[ValidationRule],
        content_type: ContentType,
        content_format: ContentFormat,
        strict_mode: bool = True
    ) -> ValidationContext:
        """Create validation context with specified parameters.
        
        Args:
            rules: Validation rules to apply
            content_type: Type of content being validated
            content_format: Format of content
            strict_mode: Whether to treat warnings as failures
            
        Returns:
            Configured validation context
        """
        return ValidationContext(
            rules=rules,
            content_type=content_type,
            content_format=content_format,
            strict_mode=strict_mode
        )
    
    async def get_recommended_rules(
        self,
        content_type: ContentType,
        content_format: ContentFormat
    ) -> List[ValidationRule]:
        """Get recommended validation rules for content type and format.
        
        Args:
            content_type: Type of content
            content_format: Format of content
            
        Returns:
            List of recommended validation rules
        """
        rules = []
        
        # Basic length rules for all content
        rules.append(ValidationRule.create(
            type=ValidationRuleType.LENGTH_MIN,
            value=100,
            description="Minimum content length"
        ))
        
        # Format-specific rules
        if content_format.value == ContentFormatEnum.MARKDOWN.value:
            rules.append(ValidationRule.markdown_valid())
        elif content_format.value == ContentFormatEnum.JSON.value:
            rules.append(ValidationRule.create(
                type=ValidationRuleType.JSON_SCHEMA,
                value=True,
                description="Valid JSON structure"
            ))
        
        # Content type specific rules
        content_type_str = str(content_type).lower()
        if "article" in content_type_str or "blog" in content_type_str:
            rules.extend([
                ValidationRule.word_count_min(300),
                ValidationRule.create(
                    type=ValidationRuleType.HEADING_STRUCTURE,
                    value=True,
                    description="Proper heading structure"
                )
            ])
        
        return rules
    
    def _validate_context(self, context: ValidationContext) -> None:
        """Validate the validation context configuration."""
        if not context.rules:
            raise ValidationConfigurationError("No validation rules specified")
        
        if not context.content_type:
            raise ValidationConfigurationError("Content type not specified")
        
        if not context.content_format:
            raise ValidationConfigurationError("Content format not specified")
    
    async def _validate_format(
        self, 
        content: GeneratedContent, 
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """Validate content format."""
        issues = []
        
        format_enum = context.content_format.value
        if format_enum in self._format_validators:
            validator = self._format_validators[format_enum]
            format_issues = await validator(content.content_text)
            issues.extend(format_issues)
        
        return issues
    
    async def _validate_markdown(self, content_text: str) -> List[ValidationIssue]:
        """Validate markdown format."""
        issues = []
        
        # Check for unclosed code blocks
        code_block_pattern = r'```'
        code_blocks = re.findall(code_block_pattern, content_text)
        if len(code_blocks) % 2 != 0:
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Unclosed code block detected",
                rule_type=ValidationRuleType.MARKDOWN_VALID,
                suggestion="Ensure all code blocks are properly closed with ```"
            ))
        
        # Check for malformed links
        link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
        links = re.findall(link_pattern, content_text)
        for link_text, link_url in links:
            if not link_url.strip():
                issues.append(ValidationIssue(
                    category=ValidationCategory.FORMAT,
                    severity=ValidationSeverity.WARNING,
                    message=f"Empty link URL for text '{link_text}'",
                    rule_type=ValidationRuleType.MARKDOWN_VALID,
                    suggestion="Provide a valid URL for the link"
                ))
        
        # Check heading structure
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content_text.split('\n')
        heading_levels = []
        
        for i, line in enumerate(lines):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                heading_levels.append((i + 1, level))
        
        # Check for skipped heading levels
        for i in range(1, len(heading_levels)):
            prev_level = heading_levels[i-1][1]
            curr_level = heading_levels[i][1]
            
            if curr_level > prev_level + 1:
                issues.append(ValidationIssue(
                    category=ValidationCategory.STRUCTURE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Heading level skipped from {prev_level} to {curr_level} at line {heading_levels[i][0]}",
                    rule_type=ValidationRuleType.HEADING_STRUCTURE,
                    location=f"line {heading_levels[i][0]}",
                    suggestion="Use consecutive heading levels for better document structure"
                ))
        
        return issues
    
    async def _validate_json(self, content_text: str) -> List[ValidationIssue]:
        """Validate JSON format."""
        issues = []
        
        try:
            json.loads(content_text)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid JSON format: {e.msg}",
                rule_type=ValidationRuleType.JSON_SCHEMA,
                location=f"line {e.lineno}, column {e.colno}",
                suggestion="Fix JSON syntax errors"
            ))
        
        return issues
    
    async def _validate_yaml(self, content_text: str) -> List[ValidationIssue]:
        """Validate YAML format."""
        issues = []
        
        try:
            yaml.safe_load(content_text)
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid YAML format: {e}",
                rule_type=ValidationRuleType.YAML_VALID,
                suggestion="Fix YAML syntax errors"
            ))
        
        return issues
    
    async def _validate_xml(self, content_text: str) -> List[ValidationIssue]:
        """Validate XML format."""
        issues = []
        
        try:
            ET.fromstring(content_text)
        except ET.ParseError as e:
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid XML format: {e}",
                rule_type=ValidationRuleType.XML_VALID,
                suggestion="Fix XML syntax errors"
            ))
        
        return issues
    
    async def _validate_html(self, content_text: str) -> List[ValidationIssue]:
        """Validate HTML format."""
        issues = []
        
        # Basic HTML validation - check for unclosed tags
        tag_pattern = r'<(/?)(\w+)(?:\s[^>]*)?/?>'
        tags = re.findall(tag_pattern, content_text)
        
        tag_stack: List[str] = []
        self_closing_tags = {'img', 'br', 'hr', 'input', 'meta', 'link'}
        
        for is_closing, tag_name in tags:
            tag_name = tag_name.lower()
            
            if tag_name in self_closing_tags:
                continue
            
            if is_closing:
                if not tag_stack or tag_stack[-1] != tag_name:
                    issues.append(ValidationIssue(
                        category=ValidationCategory.FORMAT,
                        severity=ValidationSeverity.ERROR,
                        message=f"Mismatched closing tag: </{tag_name}>",
                        rule_type=ValidationRuleType.HTML_VALID,
                        suggestion="Ensure all HTML tags are properly matched"
                    ))
                else:
                    tag_stack.pop()
            else:
                tag_stack.append(tag_name)
        
        # Check for unclosed tags
        if tag_stack:
            issues.append(ValidationIssue(
                category=ValidationCategory.FORMAT,
                severity=ValidationSeverity.ERROR,
                message=f"Unclosed HTML tags: {', '.join(tag_stack)}",
                rule_type=ValidationRuleType.HTML_VALID,
                suggestion="Close all opened HTML tags"
            ))
        
        return issues
    
    async def _apply_validation_rule(
        self,
        content: GeneratedContent,
        rule: ValidationRule,
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """Apply a single validation rule to content."""
        issues = []
        
        if rule.type == ValidationRuleType.LENGTH_MIN:
            if len(content.content_text) < rule.value:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Content too short: {len(content.content_text)} characters (minimum: {rule.value})",
                    rule_type=rule.type,
                    suggestion=f"Add more content to reach minimum length of {rule.value} characters"
                ))
        
        elif rule.type == ValidationRuleType.LENGTH_MAX:
            if len(content.content_text) > rule.value:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Content too long: {len(content.content_text)} characters (maximum: {rule.value})",
                    rule_type=rule.type,
                    suggestion=f"Reduce content to stay within maximum length of {rule.value} characters"
                ))
        
        elif rule.type == ValidationRuleType.WORD_COUNT_MIN:
            word_count = len(content.content_text.split())
            if word_count < rule.value:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Word count too low: {word_count} words (minimum: {rule.value})",
                    rule_type=rule.type,
                    suggestion=f"Add more content to reach minimum word count of {rule.value}"
                ))
        
        elif rule.type == ValidationRuleType.WORD_COUNT_MAX:
            word_count = len(content.content_text.split())
            if word_count > rule.value:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CONTENT_QUALITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Word count too high: {word_count} words (maximum: {rule.value})",
                    rule_type=rule.type,
                    suggestion=f"Consider reducing content to stay within {rule.value} words"
                ))
        
        elif rule.type == ValidationRuleType.KEYWORD_PRESENCE:
            if isinstance(rule.value, list):
                missing_keywords = []
                for keyword in rule.value:
                    if keyword.lower() not in content.content_text.lower():
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    issues.append(ValidationIssue(
                        category=ValidationCategory.BUSINESS_RULES,
                        severity=ValidationSeverity.WARNING,
                        message=f"Missing required keywords: {', '.join(missing_keywords)}",
                        rule_type=rule.type,
                        suggestion=f"Include the following keywords: {', '.join(missing_keywords)}"
                    ))
        
        return issues
    
    async def _validate_structure(
        self,
        content: GeneratedContent,
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """Validate content structure."""
        issues: List[ValidationIssue] = []
        
        # Basic structure checks
        text = content.content_text
        
        # Check for very short paragraphs if it's markdown
        if context.content_format.value == ContentFormatEnum.MARKDOWN:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            short_paragraphs = [p for p in paragraphs if len(p.split()) < 3]
            
            if len(short_paragraphs) > len(paragraphs) * 0.3:  # More than 30% short paragraphs
                issues.append(ValidationIssue(
                    category=ValidationCategory.STRUCTURE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many short paragraphs: {len(short_paragraphs)} out of {len(paragraphs)}",
                    rule_type=ValidationRuleType.PARAGRAPH_COUNT_MIN,
                    suggestion="Consider combining short paragraphs or adding more detail"
                ))
        
        return issues
    
    async def _validate_content_quality(
        self,
        content: GeneratedContent,
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """Validate content quality metrics."""
        issues = []
        
        text = content.content_text
        
        # Check for excessive repetition
        words = text.lower().split()
        if len(words) > 20:  # Only check if there's enough content
            word_freq: Dict[str, int] = {}
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Find words that appear too frequently
            total_words = len(words)
            for word, count in word_freq.items():
                frequency = count / total_words
                if frequency > 0.10:  # More than 10% frequency (more reasonable threshold)
                    issues.append(ValidationIssue(
                        category=ValidationCategory.CONTENT_QUALITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"Word '{word}' appears too frequently ({count} times, {frequency:.1%})",
                        rule_type=ValidationRuleType.KEYWORD_DENSITY,
                        suggestion=f"Consider using synonyms or reducing usage of '{word}'"
                    ))
        
        return issues
    
    def clear_cache(self) -> None:
        """Clear validation cache."""
        self._validation_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get validation cache statistics."""
        return {
            "cached_validations": len(self._validation_cache)
        }