"""Content type value object.

Provides strong typing and validation for content types."""

from dataclasses import dataclass
from enum import Enum
from typing import Self, List


class ContentTypeEnum(Enum):
    """Enumeration of supported content types."""
    
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    DOCUMENTATION = "documentation"
    TECHNICAL_DOCS = "technical_docs"
    TUTORIAL = "tutorial"
    README = "readme"
    API_DOCS = "api_docs"
    USER_GUIDE = "user_guide"
    MEETING_NOTES = "meeting_notes"
    PROPOSAL = "proposal"
    REPORT = "report"
    EMAIL = "email"
    MARKETING_COPY = "marketing_copy"
    SOCIAL_POST = "social_post"
    PRESS_RELEASE = "press_release"
    ANNOUNCEMENT = "announcement"
    NEWSLETTER = "newsletter"
    CREATIVE_WRITING = "creative_writing"
    ACADEMIC_PAPER = "academic_paper"
    RESEARCH_NOTES = "research_notes"
    CODE_COMMENTS = "code_comments"
    CHANGELOG = "changelog"
    FAQ = "faq"
    GLOSSARY = "glossary"
    MANUAL = "manual"
    SPECIFICATION = "specification"
    
    @classmethod
    def all_values(cls) -> List[str]:
        """Get all enum values as strings."""
        return [item.value for item in cls]
    
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.value.replace('_', ' ').title()


@dataclass(frozen=True)
class ContentType:
    """Strongly-typed content type with validation.
    
    Content types categorize the kind of content being generated,
    which affects template selection, validation rules, and formatting.
    
    Examples:
        ContentType.article()
        ContentType.from_string("blog_post")
        ContentType.documentation()
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate content type."""
        if not self.value:
            raise ValueError("Content type cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Content type must be string, got {type(self.value)}")
            
        # Validate against known content types
        valid_types = ContentTypeEnum.all_values()
        if self.value not in valid_types:
            raise ValueError(
                f"Invalid content type '{self.value}'. "
                f"Valid types: {', '.join(sorted(valid_types))}"
            )
    
    @classmethod
    def from_string(cls, content_type: str) -> Self:
        """Create content type from string with normalization."""
        # Normalize input
        normalized = content_type.strip().lower().replace('-', '_').replace(' ', '_')
        return cls(normalized)
    
    @classmethod
    def article(cls) -> Self:
        """Create article content type."""
        return cls(ContentTypeEnum.ARTICLE.value)
    
    @classmethod
    def blog_post(cls) -> Self:
        """Create blog post content type."""
        return cls(ContentTypeEnum.BLOG_POST.value)
    
    @classmethod
    def documentation(cls) -> Self:
        """Create documentation content type."""
        return cls(ContentTypeEnum.DOCUMENTATION.value)
    
    @classmethod
    def technical_docs(cls) -> Self:
        """Create technical documentation content type."""
        return cls(ContentTypeEnum.TECHNICAL_DOCS.value)
    
    @classmethod
    def tutorial(cls) -> Self:
        """Create tutorial content type."""
        return cls(ContentTypeEnum.TUTORIAL.value)
    
    @classmethod
    def readme(cls) -> Self:
        """Create README content type."""
        return cls(ContentTypeEnum.README.value)
    
    def display_name(self) -> str:
        """Get human-readable display name."""
        try:
            enum_value = ContentTypeEnum(self.value)
            return enum_value.display_name()
        except ValueError:
            return self.value.replace('_', ' ').title()
    
    def is_technical(self) -> bool:
        """Check if this is a technical content type."""
        technical_types = {
            ContentTypeEnum.TECHNICAL_DOCS.value,
            ContentTypeEnum.API_DOCS.value,
            ContentTypeEnum.USER_GUIDE.value,
            ContentTypeEnum.TUTORIAL.value,
            ContentTypeEnum.DOCUMENTATION.value,
            ContentTypeEnum.MANUAL.value,
            ContentTypeEnum.SPECIFICATION.value,
            ContentTypeEnum.CODE_COMMENTS.value
        }
        return self.value in technical_types
    
    def is_marketing(self) -> bool:
        """Check if this is a marketing content type."""
        marketing_types = {
            ContentTypeEnum.MARKETING_COPY.value,
            ContentTypeEnum.SOCIAL_POST.value,
            ContentTypeEnum.PRESS_RELEASE.value,
            ContentTypeEnum.ANNOUNCEMENT.value,
            ContentTypeEnum.NEWSLETTER.value
        }
        return self.value in marketing_types
    
    def is_formal(self) -> bool:
        """Check if this content type typically requires formal tone."""
        formal_types = {
            ContentTypeEnum.ACADEMIC_PAPER.value,
            ContentTypeEnum.SPECIFICATION.value,
            ContentTypeEnum.PROPOSAL.value,
            ContentTypeEnum.REPORT.value,
            ContentTypeEnum.MANUAL.value
        }
        return self.value in formal_types
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
