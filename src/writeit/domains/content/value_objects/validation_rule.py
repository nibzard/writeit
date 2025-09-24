"""Validation rule value object.

Provides strong typing and validation for content validation rules."""

from dataclasses import dataclass
from enum import Enum
from typing import Self, Any, Dict, Optional, List


class ValidationRuleType(Enum):
    """Types of validation rules."""
    
    LENGTH_MIN = "length_min"
    LENGTH_MAX = "length_max"
    WORD_COUNT_MIN = "word_count_min"
    WORD_COUNT_MAX = "word_count_max"
    PARAGRAPH_COUNT_MIN = "paragraph_count_min"
    PARAGRAPH_COUNT_MAX = "paragraph_count_max"
    READABILITY_LEVEL = "readability_level"
    SENTIMENT_SCORE = "sentiment_score"
    KEYWORD_PRESENCE = "keyword_presence"
    KEYWORD_DENSITY = "keyword_density"
    HEADING_STRUCTURE = "heading_structure"
    LINK_COUNT = "link_count"
    IMAGE_COUNT = "image_count"
    LANGUAGE_DETECTION = "language_detection"
    GRAMMAR_CHECK = "grammar_check"
    SPELL_CHECK = "spell_check"
    PLAGIARISM_CHECK = "plagiarism_check"
    TOXICITY_CHECK = "toxicity_check"
    PROFANITY_CHECK = "profanity_check"
    CUSTOM_REGEX = "custom_regex"
    JSON_SCHEMA = "json_schema"
    MARKDOWN_VALID = "markdown_valid"
    HTML_VALID = "html_valid"
    XML_VALID = "xml_valid"
    YAML_VALID = "yaml_valid"
    
    def display_name(self) -> str:
        """Get human-readable display name."""
        name_map = {
            'length_min': 'Minimum Length',
            'length_max': 'Maximum Length',
            'word_count_min': 'Minimum Word Count',
            'word_count_max': 'Maximum Word Count',
            'paragraph_count_min': 'Minimum Paragraph Count',
            'paragraph_count_max': 'Maximum Paragraph Count',
            'readability_level': 'Readability Level',
            'sentiment_score': 'Sentiment Score',
            'keyword_presence': 'Keyword Presence',
            'keyword_density': 'Keyword Density',
            'heading_structure': 'Heading Structure',
            'link_count': 'Link Count',
            'image_count': 'Image Count',
            'language_detection': 'Language Detection',
            'grammar_check': 'Grammar Check',
            'spell_check': 'Spell Check',
            'plagiarism_check': 'Plagiarism Check',
            'toxicity_check': 'Toxicity Check',
            'profanity_check': 'Profanity Check',
            'custom_regex': 'Custom Regex',
            'json_schema': 'JSON Schema',
            'markdown_valid': 'Valid Markdown',
            'html_valid': 'Valid HTML',
            'xml_valid': 'Valid XML',
            'yaml_valid': 'Valid YAML'
        }
        return name_map.get(self.value, self.value.replace('_', ' ').title())


@dataclass(frozen=True)
class ValidationRule:
    """Strongly-typed validation rule with parameters.
    
    Validation rules define quality criteria that generated content
    must meet. Each rule has a type and optional parameters that
    control how the validation is performed.
    
    Examples:
        ValidationRule.length_min(500)
        ValidationRule.word_count_range(100, 500)
        ValidationRule.keyword_presence(["python", "tutorial"])
        ValidationRule.readability_level("college")
    """
    
    rule_type: str
    parameters: Dict[str, Any]
    description: Optional[str] = None
    severity: str = "error"  # error, warning, info
    
    def __post_init__(self) -> None:
        """Validate validation rule."""
        if not self.rule_type:
            raise ValueError("Validation rule type cannot be empty")
            
        if not isinstance(self.rule_type, str):
            raise TypeError(f"Rule type must be string, got {type(self.rule_type)}")
            
        if not isinstance(self.parameters, dict):
            raise TypeError(f"Parameters must be dict, got {type(self.parameters)}")
            
        # Validate rule type
        valid_types = [rule.value for rule in ValidationRuleType]
        if self.rule_type not in valid_types:
            raise ValueError(
                f"Invalid rule type '{self.rule_type}'. "
                f"Valid types: {', '.join(sorted(valid_types))}"
            )
            
        # Validate severity
        valid_severities = {"error", "warning", "info"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Valid severities: {', '.join(sorted(valid_severities))}"
            )
    
    @classmethod
    def length_min(cls, min_length: int, description: Optional[str] = None) -> Self:
        """Create minimum length validation rule."""
        return cls(
            rule_type=ValidationRuleType.LENGTH_MIN.value,
            parameters={"min_length": min_length},
            description=description or f"Content must be at least {min_length} characters"
        )
    
    @classmethod
    def length_max(cls, max_length: int, description: Optional[str] = None) -> Self:
        """Create maximum length validation rule."""
        return cls(
            rule_type=ValidationRuleType.LENGTH_MAX.value,
            parameters={"max_length": max_length},
            description=description or f"Content must be at most {max_length} characters"
        )
    
    @classmethod
    def length_range(cls, min_length: int, max_length: int, description: Optional[str] = None) -> List[Self]:
        """Create length range validation rules (returns list of two rules)."""
        return [
            cls.length_min(min_length, description),
            cls.length_max(max_length, description)
        ]
    
    @classmethod
    def word_count_min(cls, min_words: int, description: Optional[str] = None) -> Self:
        """Create minimum word count validation rule."""
        return cls(
            rule_type=ValidationRuleType.WORD_COUNT_MIN.value,
            parameters={"min_words": min_words},
            description=description or f"Content must have at least {min_words} words"
        )
    
    @classmethod
    def word_count_max(cls, max_words: int, description: Optional[str] = None) -> Self:
        """Create maximum word count validation rule."""
        return cls(
            rule_type=ValidationRuleType.WORD_COUNT_MAX.value,
            parameters={"max_words": max_words},
            description=description or f"Content must have at most {max_words} words"
        )
    
    @classmethod
    def word_count_range(cls, min_words: int, max_words: int, description: Optional[str] = None) -> List[Self]:
        """Create word count range validation rules (returns list of two rules)."""
        return [
            cls.word_count_min(min_words, description),
            cls.word_count_max(max_words, description)
        ]
    
    @classmethod
    def keyword_presence(cls, keywords: List[str], min_occurrences: int = 1, description: Optional[str] = None) -> Self:
        """Create keyword presence validation rule."""
        return cls(
            rule_type=ValidationRuleType.KEYWORD_PRESENCE.value,
            parameters={"keywords": keywords, "min_occurrences": min_occurrences},
            description=description or f"Content must contain keywords: {', '.join(keywords)}"
        )
    
    @classmethod
    def keyword_density(cls, keyword: str, min_density: float, max_density: float, description: Optional[str] = None) -> Self:
        """Create keyword density validation rule."""
        return cls(
            rule_type=ValidationRuleType.KEYWORD_DENSITY.value,
            parameters={"keyword": keyword, "min_density": min_density, "max_density": max_density},
            description=description or f"Keyword '{keyword}' density must be between {min_density}% and {max_density}%"
        )
    
    @classmethod
    def readability_level(cls, level: str, description: Optional[str] = None) -> Self:
        """Create readability level validation rule."""
        valid_levels = {"elementary", "middle_school", "high_school", "college", "graduate"}
        if level not in valid_levels:
            raise ValueError(f"Invalid readability level '{level}'. Valid levels: {', '.join(sorted(valid_levels))}")
            
        return cls(
            rule_type=ValidationRuleType.READABILITY_LEVEL.value,
            parameters={"level": level},
            description=description or f"Content must be readable at {level.replace('_', ' ')} level"
        )
    
    @classmethod
    def grammar_check(cls, strict: bool = True, description: Optional[str] = None) -> Self:
        """Create grammar check validation rule."""
        return cls(
            rule_type=ValidationRuleType.GRAMMAR_CHECK.value,
            parameters={"strict": strict},
            description=description or "Content must pass grammar validation"
        )
    
    @classmethod
    def spell_check(cls, strict: bool = True, description: Optional[str] = None) -> Self:
        """Create spell check validation rule."""
        return cls(
            rule_type=ValidationRuleType.SPELL_CHECK.value,
            parameters={"strict": strict},
            description=description or "Content must pass spell check"
        )
    
    @classmethod
    def custom_regex(cls, pattern: str, must_match: bool = True, description: Optional[str] = None) -> Self:
        """Create custom regex validation rule."""
        return cls(
            rule_type=ValidationRuleType.CUSTOM_REGEX.value,
            parameters={"pattern": pattern, "must_match": must_match},
            description=description or f"Content must {'match' if must_match else 'not match'} pattern: {pattern}"
        )
    
    @classmethod
    def markdown_valid(cls, description: Optional[str] = None) -> Self:
        """Create valid markdown validation rule."""
        return cls(
            rule_type=ValidationRuleType.MARKDOWN_VALID.value,
            parameters={},
            description=description or "Content must be valid Markdown"
        )
    
    @classmethod
    def json_schema(cls, schema: Dict[str, Any], description: Optional[str] = None) -> Self:
        """Create JSON schema validation rule."""
        return cls(
            rule_type=ValidationRuleType.JSON_SCHEMA.value,
            parameters={"schema": schema},
            description=description or "Content must conform to JSON schema"
        )
    
    @classmethod
    def create(
        cls, 
        type: ValidationRuleType, 
        value: Any, 
        description: Optional[str] = None
    ) -> Self:
        """Create a generic validation rule.
        
        Args:
            type: Type of validation rule
            value: Value parameter for the rule
            description: Optional description
            
        Returns:
            New validation rule instance
        """
        return cls(
            rule_type=type.value,
            parameters={"value": value},
            description=description
        )
    
    @property
    def type(self) -> ValidationRuleType:
        """Get the validation rule type enum."""
        return ValidationRuleType(self.rule_type)
    
    @property
    def value(self) -> Any:
        """Get the primary value parameter."""
        if "value" in self.parameters:
            return self.parameters["value"]
        elif "min_length" in self.parameters:
            return self.parameters["min_length"]
        elif "max_length" in self.parameters:
            return self.parameters["max_length"]
        elif "min_words" in self.parameters:
            return self.parameters["min_words"]
        elif "max_words" in self.parameters:
            return self.parameters["max_words"]
        else:
            return True  # Default for boolean rules
    
    def display_name(self) -> str:
        """Get human-readable display name."""
        try:
            rule_type_enum = ValidationRuleType(self.rule_type)
            return rule_type_enum.display_name()
        except ValueError:
            return self.rule_type.replace('_', ' ').title()
    
    def is_error(self) -> bool:
        """Check if this is an error-level rule."""
        return self.severity == "error"
    
    def is_warning(self) -> bool:
        """Check if this is a warning-level rule."""
        return self.severity == "warning"
    
    def is_info(self) -> bool:
        """Check if this is an info-level rule."""
        return self.severity == "info"
    
    def with_severity(self, severity: str) -> 'ValidationRule':
        """Create a copy with different severity."""
        return ValidationRule(
            rule_type=self.rule_type,
            parameters=self.parameters,
            description=self.description,
            severity=severity
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.display_name()} ({self.severity})"
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        # Convert parameters dict to a hashable tuple
        params_tuple = tuple(sorted(self.parameters.items()))
        return hash((self.rule_type, params_tuple, self.severity))
