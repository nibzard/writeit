"""Template entity.

Domain entity representing a content template with metadata and versioning."""

from dataclasses import dataclass, field, replace as dataclass_replace
from datetime import datetime
from typing import Dict, Any, Optional, List, Self

from ..value_objects.content_id import ContentId
from ..value_objects.template_name import TemplateName
from ..value_objects.content_type import ContentType
from ..value_objects.content_format import ContentFormat
from ..value_objects.validation_rule import ValidationRule
from ..value_objects.content_length import ContentLength


@dataclass
class Template:
    """Domain entity representing a content template.
    
    A template defines the structure, prompts, and configuration for
    generating specific types of content. Templates include:
    - YAML configuration with steps and prompts
    - Metadata about content type and formatting
    - Validation rules for quality assurance
    - Versioning and author information
    
    Examples:
        template = Template.create(
            name=TemplateName.from_user_input("blog-post"),
            content_type=ContentType.blog_post(),
            yaml_content="metadata:\n  name: Blog Post\n...",
            author="user@example.com"
        )
        
        template = template.add_validation_rule(
            ValidationRule.word_count_range(800, 2000)
        )
        
        template = template.update_content(new_yaml_content)
    """
    
    id: ContentId
    name: TemplateName
    content_type: ContentType
    yaml_content: str
    version: str = "1.0.0"
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    output_format: Optional[ContentFormat] = None
    content_length: Optional[ContentLength] = None
    validation_rules: List[ValidationRule] = field(default_factory=list)
    is_published: bool = False
    is_deprecated: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate template entity."""
        if not isinstance(self.id, ContentId):
            raise TypeError("Template ID must be a ContentId")
            
        if not isinstance(self.name, TemplateName):
            raise TypeError("Template name must be a TemplateName")
            
        if not isinstance(self.content_type, ContentType):
            raise TypeError("Template content type must be a ContentType")
            
        if not self.yaml_content or not self.yaml_content.strip():
            raise ValueError("Template YAML content cannot be empty")
            
        if not isinstance(self.yaml_content, str):
            raise TypeError("Template YAML content must be a string")
            
        if self.output_format is not None and not isinstance(self.output_format, ContentFormat):
            raise TypeError("Output format must be a ContentFormat")
            
        if self.content_length is not None and not isinstance(self.content_length, ContentLength):
            raise TypeError("Content length must be a ContentLength")
            
        # Validate validation rules
        for rule in self.validation_rules:
            if not isinstance(rule, ValidationRule):
                raise TypeError("All validation rules must be ValidationRule instances")
    
    def update_content(self, yaml_content: str, author: Optional[str] = None) -> Self:
        """Update template content.
        
        Args:
            yaml_content: New YAML content
            author: Author of the update
            
        Returns:
            Updated template with new version
        """
        if not yaml_content or not yaml_content.strip():
            raise ValueError("YAML content cannot be empty")
            
        # Increment patch version
        version_parts = self.version.split('.')
        if len(version_parts) == 3:
            patch = int(version_parts[2]) + 1
            new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
        else:
            new_version = f"{self.version}.1"
        
        return dataclass_replace(
            self,
            yaml_content=yaml_content,
            version=new_version,
            author=author or self.author,
            updated_at=datetime.now(),
            is_published=False  # Unpublish when content changes
        )
    
    def add_validation_rule(self, rule: ValidationRule) -> Self:
        """Add a validation rule to the template.
        
        Args:
            rule: Validation rule to add
            
        Returns:
            Updated template
        """
        if not isinstance(rule, ValidationRule):
            raise TypeError("Rule must be a ValidationRule")
            
        # Check if rule already exists
        if rule in self.validation_rules:
            return self
            
        new_rules = self.validation_rules.copy()
        new_rules.append(rule)
        
        return dataclass_replace(
            self,
            validation_rules=new_rules,
            updated_at=datetime.now()
        )
    
    def remove_validation_rule(self, rule: ValidationRule) -> Self:
        """Remove a validation rule from the template.
        
        Args:
            rule: Validation rule to remove
            
        Returns:
            Updated template
        """
        if rule not in self.validation_rules:
            return self
            
        new_rules = [r for r in self.validation_rules if r != rule]
        
        return dataclass_replace(
            self,
            validation_rules=new_rules,
            updated_at=datetime.now()
        )
    
    def set_output_format(self, output_format: ContentFormat) -> Self:
        """Set the default output format for this template.
        
        Args:
            output_format: Content format
            
        Returns:
            Updated template
        """
        if not isinstance(output_format, ContentFormat):
            raise TypeError("Output format must be a ContentFormat")
            
        return dataclass_replace(
            self,
            output_format=output_format,
            updated_at=datetime.now()
        )
    
    def set_content_length(self, content_length: ContentLength) -> Self:
        """Set the content length constraints for this template.
        
        Args:
            content_length: Content length constraints
            
        Returns:
            Updated template
        """
        if not isinstance(content_length, ContentLength):
            raise TypeError("Content length must be a ContentLength")
            
        return dataclass_replace(
            self,
            content_length=content_length,
            updated_at=datetime.now()
        )
    
    def add_tag(self, tag: str) -> Self:
        """Add a tag to the template.
        
        Args:
            tag: Tag to add
            
        Returns:
            Updated template
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
    
    def remove_tag(self, tag: str) -> Self:
        """Remove a tag from the template.
        
        Args:
            tag: Tag to remove
            
        Returns:
            Updated template
        """
        normalized_tag = tag.strip().lower()
        if normalized_tag not in self.tags:
            return self
            
        new_tags = [t for t in self.tags if t != normalized_tag]
        
        return dataclass_replace(
            self,
            tags=new_tags,
            updated_at=datetime.now()
        )
    
    def publish(self, published_by: Optional[str] = None) -> Self:
        """Publish the template.
        
        Args:
            published_by: User who published the template
            
        Returns:
            Updated template
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
    
    def unpublish(self) -> Self:
        """Unpublish the template.
        
        Returns:
            Updated template
        """
        if not self.is_published:
            return self
            
        return dataclass_replace(
            self,
            is_published=False,
            updated_at=datetime.now()
        )
    
    def deprecate(self, reason: Optional[str] = None, deprecated_by: Optional[str] = None) -> Self:
        """Deprecate the template.
        
        Args:
            reason: Reason for deprecation
            deprecated_by: User who deprecated the template
            
        Returns:
            Updated template
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
            Updated template
        """
        return dataclass_replace(
            self,
            usage_count=self.usage_count + 1
        )
    
    def set_metadata(self, key: str, value: Any) -> Self:
        """Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Updated template
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        
        return dataclass_replace(
            self,
            metadata=new_metadata,
            updated_at=datetime.now()
        )
    
    def get_validation_rules_by_type(self, rule_type: str) -> List[ValidationRule]:
        """Get validation rules of a specific type.
        
        Args:
            rule_type: Type of validation rule
            
        Returns:
            List of matching validation rules
        """
        return [rule for rule in self.validation_rules if rule.rule_type == rule_type]
    
    def has_validation_rule_type(self, rule_type: str) -> bool:
        """Check if template has a validation rule of the specified type.
        
        Args:
            rule_type: Type of validation rule
            
        Returns:
            True if rule type exists
        """
        return any(rule.rule_type == rule_type for rule in self.validation_rules)
    
    def is_valid_for_content_type(self, content_type: ContentType) -> bool:
        """Check if template is suitable for the given content type.
        
        Args:
            content_type: Content type to check
            
        Returns:
            True if template is suitable
        """
        return self.content_type == content_type
    
    def get_estimated_word_count(self) -> Optional[int]:
        """Get estimated word count based on content length constraints.
        
        Returns:
            Estimated word count or None if not specified
        """
        if self.content_length is None:
            return None
            
        if self.content_length.max_words is not None:
            return self.content_length.max_words
        elif self.content_length.min_words is not None:
            return self.content_length.min_words
        else:
            return None
    
    @classmethod
    def create(
        cls,
        name: TemplateName,
        content_type: ContentType,
        yaml_content: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        output_format: Optional[ContentFormat] = None,
        content_length: Optional[ContentLength] = None,
        validation_rules: Optional[List[ValidationRule]] = None
    ) -> Self:
        """Create a new template.
        
        Args:
            name: Template name
            content_type: Content type
            yaml_content: YAML configuration content
            author: Template author
            description: Template description
            tags: Template tags
            output_format: Default output format
            content_length: Content length constraints
            validation_rules: Validation rules
            
        Returns:
            New template instance
        """
        return cls(
            id=ContentId.generate(),
            name=name,
            content_type=content_type,
            yaml_content=yaml_content,
            author=author,
            description=description,
            tags=tags or [],
            output_format=output_format,
            content_length=content_length,
            validation_rules=validation_rules or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def __str__(self) -> str:
        """String representation."""
        status = "published" if self.is_published else "draft"
        if self.is_deprecated:
            status = "deprecated"
        return f"Template({self.name} v{self.version}, {status})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"Template(id={self.id}, name={self.name}, "
                f"content_type={self.content_type}, version={self.version}, "
                f"published={self.is_published}, created={self.created_at})")
