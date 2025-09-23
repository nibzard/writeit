"""Style primer entity.

Domain entity representing a style configuration for content generation."""

from dataclasses import dataclass, field, replace as dataclass_replace
from datetime import datetime
from typing import Dict, Any, Optional, List, Self

from ..value_objects.content_id import ContentId
from ..value_objects.style_name import StyleName
from ..value_objects.content_type import ContentType


@dataclass
class StylePrimer:
    """Domain entity representing a style primer for content generation.
    
    A style primer defines the tone, voice, formatting preferences,
    and stylistic guidelines for generating content. Style primers can
    be applied to templates to ensure consistent output quality and
    branding across different content types.
    
    Examples:
        style = StylePrimer.create(
            name=StyleName.from_user_input("formal-technical"),
            description="Formal technical writing style",
            tone="professional",
            voice="third_person"
        )
        
        style = style.add_guideline(
            "Use clear, concise sentences"
        ).set_target_audience("software developers")
    """
    
    id: ContentId
    name: StyleName
    description: Optional[str] = None
    tone: Optional[str] = None  # formal, casual, friendly, professional, etc.
    voice: Optional[str] = None  # first_person, second_person, third_person
    writing_style: Optional[str] = None  # conversational, academic, journalistic, etc.
    target_audience: Optional[str] = None
    language: str = "en"  # ISO language code
    guidelines: List[str] = field(default_factory=list)
    formatting_preferences: Dict[str, Any] = field(default_factory=dict)
    vocabulary_preferences: Dict[str, Any] = field(default_factory=dict)
    applicable_content_types: List[ContentType] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_published: bool = False
    is_deprecated: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    usage_count: int = 0
    author: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate style primer entity."""
        if not isinstance(self.id, ContentId):
            raise TypeError("Style primer ID must be a ContentId")
            
        if not isinstance(self.name, StyleName):
            raise TypeError("Style primer name must be a StyleName")
            
        if self.language and not isinstance(self.language, str):
            raise TypeError("Language must be a string")
            
        # Validate content types
        for content_type in self.applicable_content_types:
            if not isinstance(content_type, ContentType):
                raise TypeError("All applicable content types must be ContentType instances")
    
    def set_tone(self, tone: str) -> Self:
        """Set the tone for this style primer.
        
        Args:
            tone: Writing tone (formal, casual, friendly, professional, etc.)
            
        Returns:
            Updated style primer
        """
        if not tone or not tone.strip():
            raise ValueError("Tone cannot be empty")
            
        return dataclass_replace(
            self,
            tone=tone.strip().lower(),
            updated_at=datetime.now()
        )
    
    def set_voice(self, voice: str) -> Self:
        """Set the voice for this style primer.
        
        Args:
            voice: Writing voice (first_person, second_person, third_person)
            
        Returns:
            Updated style primer
        """
        if not voice or not voice.strip():
            raise ValueError("Voice cannot be empty")
            
        valid_voices = {"first_person", "second_person", "third_person"}
        normalized_voice = voice.strip().lower()
        if normalized_voice not in valid_voices:
            raise ValueError(f"Invalid voice '{voice}'. Valid voices: {', '.join(sorted(valid_voices))}")
            
        return dataclass_replace(
            self,
            voice=normalized_voice,
            updated_at=datetime.now()
        )
    
    def set_writing_style(self, writing_style: str) -> Self:
        """Set the writing style for this style primer.
        
        Args:
            writing_style: Writing style (conversational, academic, journalistic, etc.)
            
        Returns:
            Updated style primer
        """
        if not writing_style or not writing_style.strip():
            raise ValueError("Writing style cannot be empty")
            
        return dataclass_replace(
            self,
            writing_style=writing_style.strip().lower(),
            updated_at=datetime.now()
        )
    
    def set_target_audience(self, audience: str) -> Self:
        """Set the target audience for this style primer.
        
        Args:
            audience: Target audience description
            
        Returns:
            Updated style primer
        """
        if not audience or not audience.strip():
            raise ValueError("Target audience cannot be empty")
            
        return dataclass_replace(
            self,
            target_audience=audience.strip(),
            updated_at=datetime.now()
        )
    
    def add_guideline(self, guideline: str) -> Self:
        """Add a style guideline.
        
        Args:
            guideline: Style guideline text
            
        Returns:
            Updated style primer
        """
        if not guideline or not guideline.strip():
            raise ValueError("Guideline cannot be empty")
            
        guideline_text = guideline.strip()
        if guideline_text in self.guidelines:
            return self
            
        new_guidelines = self.guidelines.copy()
        new_guidelines.append(guideline_text)
        
        return dataclass_replace(
            self,
            guidelines=new_guidelines,
            updated_at=datetime.now()
        )
    
    def remove_guideline(self, guideline: str) -> Self:
        """Remove a style guideline.
        
        Args:
            guideline: Style guideline text to remove
            
        Returns:
            Updated style primer
        """
        guideline_text = guideline.strip()
        if guideline_text not in self.guidelines:
            return self
            
        new_guidelines = [g for g in self.guidelines if g != guideline_text]
        
        return dataclass_replace(
            self,
            guidelines=new_guidelines,
            updated_at=datetime.now()
        )
    
    def set_formatting_preference(self, key: str, value: Any) -> Self:
        """Set a formatting preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            Updated style primer
        """
        new_preferences = self.formatting_preferences.copy()
        new_preferences[key] = value
        
        return dataclass_replace(
            self,
            formatting_preferences=new_preferences,
            updated_at=datetime.now()
        )
    
    def set_vocabulary_preference(self, key: str, value: Any) -> Self:
        """Set a vocabulary preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            Updated style primer
        """
        new_preferences = self.vocabulary_preferences.copy()
        new_preferences[key] = value
        
        return dataclass_replace(
            self,
            vocabulary_preferences=new_preferences,
            updated_at=datetime.now()
        )
    
    def add_applicable_content_type(self, content_type: ContentType) -> Self:
        """Add an applicable content type.
        
        Args:
            content_type: Content type this style applies to
            
        Returns:
            Updated style primer
        """
        if not isinstance(content_type, ContentType):
            raise TypeError("Content type must be a ContentType")
            
        if content_type in self.applicable_content_types:
            return self
            
        new_types = self.applicable_content_types.copy()
        new_types.append(content_type)
        
        return dataclass_replace(
            self,
            applicable_content_types=new_types,
            updated_at=datetime.now()
        )
    
    def remove_applicable_content_type(self, content_type: ContentType) -> Self:
        """Remove an applicable content type.
        
        Args:
            content_type: Content type to remove
            
        Returns:
            Updated style primer
        """
        if content_type not in self.applicable_content_types:
            return self
            
        new_types = [ct for ct in self.applicable_content_types if ct != content_type]
        
        return dataclass_replace(
            self,
            applicable_content_types=new_types,
            updated_at=datetime.now()
        )
    
    def add_example(self, example: str) -> Self:
        """Add a style example.
        
        Args:
            example: Example text demonstrating the style
            
        Returns:
            Updated style primer
        """
        if not example or not example.strip():
            raise ValueError("Example cannot be empty")
            
        example_text = example.strip()
        if example_text in self.examples:
            return self
            
        new_examples = self.examples.copy()
        new_examples.append(example_text)
        
        return dataclass_replace(
            self,
            examples=new_examples,
            updated_at=datetime.now()
        )
    
    def add_tag(self, tag: str) -> Self:
        """Add a tag to the style primer.
        
        Args:
            tag: Tag to add
            
        Returns:
            Updated style primer
        """
        if not tag or not tag.strip():
            raise ValueError("Tag cannot be empty")
            
        normalized_tag = tag.strip().lower()
        if normalized_tag in self.tags:
            return self
            
        new_tags = self.tags.copy()
        new_tags.append(normalized_tag)
        
        return dataclass_replace(
            self,
            tags=new_tags,
            updated_at=datetime.now()
        )
    
    def publish(self, published_by: Optional[str] = None) -> Self:
        """Publish the style primer.
        
        Args:
            published_by: User who published the style primer
            
        Returns:
            Updated style primer
        """
        if self.is_published:
            return self
            
        return dataclass_replace(
            self,
            is_published=True,
            published_at=datetime.now(),
            author=published_by or self.author,
            updated_at=datetime.now()
        )
    
    def deprecate(self, reason: Optional[str] = None, deprecated_by: Optional[str] = None) -> Self:
        """Deprecate the style primer.
        
        Args:
            reason: Reason for deprecation
            deprecated_by: User who deprecated the style primer
            
        Returns:
            Updated style primer
        """
        if self.is_deprecated:
            return self
            
        metadata_update = self.metadata.copy()
        if reason:
            metadata_update["deprecation_reason"] = reason
        if deprecated_by:
            metadata_update["deprecated_by"] = deprecated_by
            
        return dataclass_replace(
            self,
            is_deprecated=True,
            deprecated_at=datetime.now(),
            is_published=False,  # Unpublish when deprecated
            metadata=metadata_update,
            updated_at=datetime.now()
        )
    
    def increment_usage(self) -> Self:
        """Increment the usage count.
        
        Returns:
            Updated style primer
        """
        return dataclass_replace(
            self,
            usage_count=self.usage_count + 1
        )
    
    def is_applicable_to_content_type(self, content_type: ContentType) -> bool:
        """Check if this style primer applies to the given content type.
        
        Args:
            content_type: Content type to check
            
        Returns:
            True if style applies to content type
        """
        # If no specific content types are defined, applies to all
        if not self.applicable_content_types:
            return True
            
        return content_type in self.applicable_content_types
    
    def get_style_summary(self) -> str:
        """Get a human-readable summary of the style.
        
        Returns:
            Style summary text
        """
        parts = []
        
        if self.tone:
            parts.append(f"Tone: {self.tone}")
        if self.voice:
            parts.append(f"Voice: {self.voice.replace('_', ' ')}")
        if self.writing_style:
            parts.append(f"Style: {self.writing_style}")
        if self.target_audience:
            parts.append(f"Audience: {self.target_audience}")
            
        return ", ".join(parts) if parts else "No style preferences defined"
    
    @classmethod
    def create(
        cls,
        name: StyleName,
        description: Optional[str] = None,
        tone: Optional[str] = None,
        voice: Optional[str] = None,
        writing_style: Optional[str] = None,
        target_audience: Optional[str] = None,
        language: str = "en",
        author: Optional[str] = None
    ) -> Self:
        """Create a new style primer.
        
        Args:
            name: Style primer name
            description: Style description
            tone: Writing tone
            voice: Writing voice
            writing_style: Writing style
            target_audience: Target audience
            language: Language code
            author: Style primer author
            
        Returns:
            New style primer instance
        """
        return cls(
            id=ContentId.generate(),
            name=name,
            description=description,
            tone=tone.lower() if tone else None,
            voice=voice.lower() if voice else None,
            writing_style=writing_style.lower() if writing_style else None,
            target_audience=target_audience,
            language=language,
            author=author,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def __str__(self) -> str:
        """String representation."""
        status = "published" if self.is_published else "draft"
        if self.is_deprecated:
            status = "deprecated"
        return f"StylePrimer({self.name}, {status})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"StylePrimer(id={self.id}, name={self.name}, "
                f"tone={self.tone}, voice={self.voice}, "
                f"published={self.is_published}, created={self.created_at})")
