"""Content length value object.

Provides strong typing and validation for content length constraints."""

from dataclasses import dataclass
from typing import Self, Optional


@dataclass(frozen=True)
class ContentLength:
    """Strongly-typed content length with validation and constraints.
    
    Content length represents the size constraints for generated content,
    including character count, word count, and paragraph count limits.
    This helps ensure content meets specific requirements for different
    platforms and use cases.
    
    Examples:
        ContentLength.characters(500, 2000)
        ContentLength.words(100, 500)
        ContentLength.paragraphs(3, 10)
        ContentLength.twitter_post()  # 280 characters
        ContentLength.blog_post()     # 800-2000 words
    """
    
    min_characters: Optional[int] = None
    max_characters: Optional[int] = None
    min_words: Optional[int] = None
    max_words: Optional[int] = None
    min_paragraphs: Optional[int] = None
    max_paragraphs: Optional[int] = None
    
    def __post_init__(self) -> None:
        """Validate content length constraints."""
        # Validate character constraints
        if self.min_characters is not None:
            if not isinstance(self.min_characters, int) or self.min_characters < 0:
                raise ValueError("Minimum characters must be a non-negative integer")
                
        if self.max_characters is not None:
            if not isinstance(self.max_characters, int) or self.max_characters < 0:
                raise ValueError("Maximum characters must be a non-negative integer")
                
        if (self.min_characters is not None and self.max_characters is not None 
            and self.min_characters > self.max_characters):
            raise ValueError("Minimum characters cannot be greater than maximum characters")
        
        # Validate word constraints
        if self.min_words is not None:
            if not isinstance(self.min_words, int) or self.min_words < 0:
                raise ValueError("Minimum words must be a non-negative integer")
                
        if self.max_words is not None:
            if not isinstance(self.max_words, int) or self.max_words < 0:
                raise ValueError("Maximum words must be a non-negative integer")
                
        if (self.min_words is not None and self.max_words is not None 
            and self.min_words > self.max_words):
            raise ValueError("Minimum words cannot be greater than maximum words")
        
        # Validate paragraph constraints
        if self.min_paragraphs is not None:
            if not isinstance(self.min_paragraphs, int) or self.min_paragraphs < 0:
                raise ValueError("Minimum paragraphs must be a non-negative integer")
                
        if self.max_paragraphs is not None:
            if not isinstance(self.max_paragraphs, int) or self.max_paragraphs < 0:
                raise ValueError("Maximum paragraphs must be a non-negative integer")
                
        if (self.min_paragraphs is not None and self.max_paragraphs is not None 
            and self.min_paragraphs > self.max_paragraphs):
            raise ValueError("Minimum paragraphs cannot be greater than maximum paragraphs")
            
        # At least one constraint must be specified
        if all(constraint is None for constraint in [
            self.min_characters, self.max_characters,
            self.min_words, self.max_words,
            self.min_paragraphs, self.max_paragraphs
        ]):
            raise ValueError("At least one length constraint must be specified")
    
    @classmethod
    def characters(cls, min_chars: Optional[int] = None, max_chars: Optional[int] = None) -> Self:
        """Create content length with character constraints."""
        return cls(min_characters=min_chars, max_characters=max_chars)
    
    @classmethod
    def words(cls, min_words: Optional[int] = None, max_words: Optional[int] = None) -> Self:
        """Create content length with word constraints."""
        return cls(min_words=min_words, max_words=max_words)
    
    @classmethod
    def paragraphs(cls, min_paragraphs: Optional[int] = None, max_paragraphs: Optional[int] = None) -> Self:
        """Create content length with paragraph constraints."""
        return cls(min_paragraphs=min_paragraphs, max_paragraphs=max_paragraphs)
    
    @classmethod
    def combined(
        cls,
        min_chars: Optional[int] = None,
        max_chars: Optional[int] = None,
        min_words: Optional[int] = None,
        max_words: Optional[int] = None,
        min_paragraphs: Optional[int] = None,
        max_paragraphs: Optional[int] = None
    ) -> Self:
        """Create content length with multiple constraint types."""
        return cls(
            min_characters=min_chars,
            max_characters=max_chars,
            min_words=min_words,
            max_words=max_words,
            min_paragraphs=min_paragraphs,
            max_paragraphs=max_paragraphs
        )
    
    @classmethod
    def twitter_post(cls) -> Self:
        """Create content length for Twitter posts (280 characters)."""
        return cls(max_characters=280)
    
    @classmethod
    def linkedin_post(cls) -> Self:
        """Create content length for LinkedIn posts (3000 characters)."""
        return cls(max_characters=3000)
    
    @classmethod
    def slack_message(cls) -> Self:
        """Create content length for Slack messages (4000 characters)."""
        return cls(max_characters=4000)
    
    @classmethod
    def discord_message(cls) -> Self:
        """Create content length for Discord messages (2000 characters)."""
        return cls(max_characters=2000)
    
    @classmethod
    def email_subject(cls) -> Self:
        """Create content length for email subjects (50-78 characters)."""
        return cls(min_characters=10, max_characters=78)
    
    @classmethod
    def meta_description(cls) -> Self:
        """Create content length for meta descriptions (150-160 characters)."""
        return cls(min_characters=120, max_characters=160)
    
    @classmethod
    def blog_post(cls) -> Self:
        """Create content length for blog posts (800-2000 words)."""
        return cls(min_words=800, max_words=2000)
    
    @classmethod
    def short_article(cls) -> Self:
        """Create content length for short articles (300-800 words)."""
        return cls(min_words=300, max_words=800)
    
    @classmethod
    def long_article(cls) -> Self:
        """Create content length for long articles (2000-5000 words)."""
        return cls(min_words=2000, max_words=5000)
    
    @classmethod
    def documentation_page(cls) -> Self:
        """Create content length for documentation pages (500-1500 words)."""
        return cls(min_words=500, max_words=1500)
    
    @classmethod
    def tutorial(cls) -> Self:
        """Create content length for tutorials (1000-3000 words)."""
        return cls(min_words=1000, max_words=3000)
    
    @classmethod
    def readme(cls) -> Self:
        """Create content length for README files (200-1000 words)."""
        return cls(min_words=200, max_words=1000)
    
    def has_character_constraints(self) -> bool:
        """Check if character constraints are specified."""
        return self.min_characters is not None or self.max_characters is not None
    
    def has_word_constraints(self) -> bool:
        """Check if word constraints are specified."""
        return self.min_words is not None or self.max_words is not None
    
    def has_paragraph_constraints(self) -> bool:
        """Check if paragraph constraints are specified."""
        return self.min_paragraphs is not None or self.max_paragraphs is not None
    
    def is_within_character_limit(self, char_count: int) -> bool:
        """Check if character count is within limits."""
        if self.min_characters is not None and char_count < self.min_characters:
            return False
        if self.max_characters is not None and char_count > self.max_characters:
            return False
        return True
    
    def is_within_word_limit(self, word_count: int) -> bool:
        """Check if word count is within limits."""
        if self.min_words is not None and word_count < self.min_words:
            return False
        if self.max_words is not None and word_count > self.max_words:
            return False
        return True
    
    def is_within_paragraph_limit(self, paragraph_count: int) -> bool:
        """Check if paragraph count is within limits."""
        if self.min_paragraphs is not None and paragraph_count < self.min_paragraphs:
            return False
        if self.max_paragraphs is not None and paragraph_count > self.max_paragraphs:
            return False
        return True
    
    def get_character_range_description(self) -> str:
        """Get human-readable character range description."""
        if not self.has_character_constraints():
            return "No character limit"
            
        if self.min_characters is not None and self.max_characters is not None:
            return f"{self.min_characters}-{self.max_characters} characters"
        elif self.min_characters is not None:
            return f"At least {self.min_characters} characters"
        elif self.max_characters is not None:
            return f"At most {self.max_characters} characters"
        else:
            return "No character limit"
    
    def get_word_range_description(self) -> str:
        """Get human-readable word range description."""
        if not self.has_word_constraints():
            return "No word limit"
            
        if self.min_words is not None and self.max_words is not None:
            return f"{self.min_words}-{self.max_words} words"
        elif self.min_words is not None:
            return f"At least {self.min_words} words"
        elif self.max_words is not None:
            return f"At most {self.max_words} words"
        else:
            return "No word limit"
    
    def get_paragraph_range_description(self) -> str:
        """Get human-readable paragraph range description."""
        if not self.has_paragraph_constraints():
            return "No paragraph limit"
            
        if self.min_paragraphs is not None and self.max_paragraphs is not None:
            return f"{self.min_paragraphs}-{self.max_paragraphs} paragraphs"
        elif self.min_paragraphs is not None:
            return f"At least {self.min_paragraphs} paragraphs"
        elif self.max_paragraphs is not None:
            return f"At most {self.max_paragraphs} paragraphs"
        else:
            return "No paragraph limit"
    
    def __str__(self) -> str:
        """String representation."""
        constraints = []
        if self.has_character_constraints():
            constraints.append(self.get_character_range_description())
        if self.has_word_constraints():
            constraints.append(self.get_word_range_description())
        if self.has_paragraph_constraints():
            constraints.append(self.get_paragraph_range_description())
        
        return ", ".join(constraints)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((
            self.min_characters, self.max_characters,
            self.min_words, self.max_words,
            self.min_paragraphs, self.max_paragraphs
        ))
