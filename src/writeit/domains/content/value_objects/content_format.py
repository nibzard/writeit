"""Content format value object.

Provides strong typing and validation for content output formats."""

from dataclasses import dataclass
from enum import Enum
from typing import Self, List


class ContentFormatEnum(Enum):
    """Enumeration of supported content output formats."""
    
    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    PDF = "pdf"
    DOCX = "docx"
    RTF = "rtf"
    LATEX = "latex"
    ASCIIDOC = "asciidoc"
    RESTRUCTUREDTEXT = "rst"
    CONFLUENCE = "confluence"
    NOTION = "notion"
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL_HTML = "email_html"
    EMAIL_TEXT = "email_text"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    
    @classmethod
    def all_values(cls) -> List[str]:
        """Get all enum values as strings."""
        return [item.value for item in cls]
    
    def display_name(self) -> str:
        """Get human-readable display name."""
        name_map = {
            'markdown': 'Markdown',
            'html': 'HTML',
            'text': 'Plain Text',
            'json': 'JSON',
            'yaml': 'YAML',
            'xml': 'XML',
            'pdf': 'PDF',
            'docx': 'Microsoft Word',
            'rtf': 'Rich Text Format',
            'latex': 'LaTeX',
            'asciidoc': 'AsciiDoc',
            'rst': 'reStructuredText',
            'confluence': 'Confluence Wiki',
            'notion': 'Notion',
            'slack': 'Slack Message',
            'discord': 'Discord Message',
            'email_html': 'HTML Email',
            'email_text': 'Text Email',
            'twitter': 'Twitter Post',
            'linkedin': 'LinkedIn Post'
        }
        return name_map.get(self.value, self.value.title())
    
    def file_extension(self) -> str:
        """Get typical file extension for this format."""
        extension_map = {
            'markdown': 'md',
            'html': 'html',
            'text': 'txt',
            'json': 'json',
            'yaml': 'yaml',
            'xml': 'xml',
            'pdf': 'pdf',
            'docx': 'docx',
            'rtf': 'rtf',
            'latex': 'tex',
            'asciidoc': 'adoc',
            'rst': 'rst',
            'confluence': 'html',
            'notion': 'md',
            'slack': 'txt',
            'discord': 'txt',
            'email_html': 'html',
            'email_text': 'txt',
            'twitter': 'txt',
            'linkedin': 'txt'
        }
        return extension_map.get(self.value, self.value)


@dataclass(frozen=True)
class ContentFormat:
    """Strongly-typed content format with validation.
    
    Content formats determine how the generated content is structured
    and presented. Different formats may have different validation rules,
    length constraints, and formatting requirements.
    
    Examples:
        ContentFormat.markdown()
        ContentFormat.from_string("html")
        ContentFormat.plain_text()
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate content format."""
        if not self.value:
            raise ValueError("Content format cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Content format must be string, got {type(self.value)}")
            
        # Validate against known content formats
        valid_formats = ContentFormatEnum.all_values()
        if self.value not in valid_formats:
            raise ValueError(
                f"Invalid content format '{self.value}'. "
                f"Valid formats: {', '.join(sorted(valid_formats))}"
            )
    
    @classmethod
    def from_string(cls, content_format: str) -> Self:
        """Create content format from string with normalization."""
        # Normalize input
        normalized = content_format.strip().lower().replace('-', '_')
        return cls(normalized)
    
    @classmethod
    def from_file_extension(cls, extension: str) -> Self:
        """Create content format from file extension."""
        # Remove leading dot if present
        extension = extension.lstrip('.')
        
        # Map common extensions to formats
        extension_map = {
            'md': 'markdown',
            'html': 'html',
            'htm': 'html',
            'txt': 'text',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'xml': 'xml',
            'pdf': 'pdf',
            'docx': 'docx',
            'doc': 'docx',
            'rtf': 'rtf',
            'tex': 'latex',
            'adoc': 'asciidoc',
            'rst': 'rst'
        }
        
        format_value = extension_map.get(extension.lower(), extension.lower())
        return cls.from_string(format_value)
    
    @classmethod
    def markdown(cls) -> Self:
        """Create markdown format."""
        return cls(ContentFormatEnum.MARKDOWN.value)
    
    @classmethod
    def html(cls) -> Self:
        """Create HTML format."""
        return cls(ContentFormatEnum.HTML.value)
    
    @classmethod
    def plain_text(cls) -> Self:
        """Create plain text format."""
        return cls(ContentFormatEnum.PLAIN_TEXT.value)
    
    @classmethod
    def json(cls) -> Self:
        """Create JSON format."""
        return cls(ContentFormatEnum.JSON.value)
    
    def display_name(self) -> str:
        """Get human-readable display name."""
        try:
            enum_value = ContentFormatEnum(self.value)
            return enum_value.display_name()
        except ValueError:
            return self.value.title()
    
    def file_extension(self) -> str:
        """Get typical file extension for this format."""
        try:
            enum_value = ContentFormatEnum(self.value)
            return enum_value.file_extension()
        except ValueError:
            return self.value
    
    def is_structured(self) -> bool:
        """Check if this is a structured data format."""
        structured_formats = {
            ContentFormatEnum.JSON.value,
            ContentFormatEnum.YAML.value,
            ContentFormatEnum.XML.value
        }
        return self.value in structured_formats
    
    def is_markup(self) -> bool:
        """Check if this is a markup format."""
        markup_formats = {
            ContentFormatEnum.MARKDOWN.value,
            ContentFormatEnum.HTML.value,
            ContentFormatEnum.LATEX.value,
            ContentFormatEnum.ASCIIDOC.value,
            ContentFormatEnum.RESTRUCTUREDTEXT.value
        }
        return self.value in markup_formats
    
    def is_binary(self) -> bool:
        """Check if this is a binary format."""
        binary_formats = {
            ContentFormatEnum.PDF.value,
            ContentFormatEnum.DOCX.value
        }
        return self.value in binary_formats
    
    def is_social_platform(self) -> bool:
        """Check if this is a social media platform format."""
        social_formats = {
            ContentFormatEnum.TWITTER.value,
            ContentFormatEnum.LINKEDIN.value,
            ContentFormatEnum.SLACK.value,
            ContentFormatEnum.DISCORD.value
        }
        return self.value in social_formats
    
    def supports_length_limit(self) -> bool:
        """Check if this format has character/length limits."""
        limited_formats = {
            ContentFormatEnum.TWITTER.value,
            ContentFormatEnum.SLACK.value,
            ContentFormatEnum.DISCORD.value
        }
        return self.value in limited_formats
    
    def get_character_limit(self) -> int | None:
        """Get character limit for this format if applicable."""
        limits = {
            ContentFormatEnum.TWITTER.value: 280,
            ContentFormatEnum.SLACK.value: 4000,
            ContentFormatEnum.DISCORD.value: 2000
        }
        return limits.get(self.value)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
