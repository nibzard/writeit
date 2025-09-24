"""Test data builders for Content domain entities."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Self
from pathlib import Path

from src.writeit.domains.content.entities.template import Template
from src.writeit.domains.content.entities.style_primer import StylePrimer
from src.writeit.domains.content.entities.generated_content import GeneratedContent
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.content_format import ContentFormat
from src.writeit.domains.content.value_objects.content_id import ContentId
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.domains.content.value_objects.validation_rule import ValidationRule


class TemplateBuilder:
    """Builder for Template test data."""
    
    def __init__(self) -> None:
        self._name = TemplateName("test_template")
        self._content_type = ContentType.documentation()
        self._content = "# {{title}}\n\n{{content}}"
        self._version = "1.0.0"
        self._description = "A test template"
        self._metadata = {}
        self._variables = {"title", "content"}
        self._validation_rules = []
        self._dependencies = []
        self._tags = []
        self._author = None
        self._file_path = None
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_name(self, name: str | TemplateName) -> Self:
        """Set the template name."""
        if isinstance(name, str):
            name = TemplateName(name)
        self._name = name
        return self
    
    def with_content_type(self, content_type: ContentType) -> Self:
        """Set the content type."""
        self._content_type = content_type
        return self
    
    def with_content(self, content: str) -> Self:
        """Set the template content."""
        self._content = content
        # Extract variables from content (simplified)
        import re
        self._variables = set(re.findall(r'\{\{(\w+)\}\}', content))
        return self
    
    def with_version(self, version: str) -> Self:
        """Set the template version."""
        self._version = version
        return self
    
    def with_description(self, description: str) -> Self:
        """Set the template description."""
        self._description = description
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the template metadata."""
        self._metadata = metadata
        return self
    
    def with_variables(self, variables: set[str]) -> Self:
        """Set the template variables."""
        self._variables = variables
        return self
    
    def with_validation_rules(self, rules: List[ValidationRule]) -> Self:
        """Set the validation rules."""
        self._validation_rules = rules
        return self
    
    def with_dependencies(self, dependencies: List[str]) -> Self:
        """Set the template dependencies."""
        self._dependencies = dependencies
        return self
    
    def with_tags(self, tags: List[str]) -> Self:
        """Set the template tags."""
        self._tags = tags
        return self
    
    def with_author(self, author: str) -> Self:
        """Set the template author."""
        self._author = author
        return self
    
    def with_file_path(self, file_path: str | Path) -> Self:
        """Set the template file path."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        self._file_path = file_path
        return self
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> Self:
        """Set the template timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def build(self) -> Template:
        """Build the Template."""
        from src.writeit.domains.content.value_objects.content_id import ContentId
        
        # Generate a ContentId
        content_id = ContentId.generate()
        
        return Template(
            id=content_id,
            name=self._name,
            content_type=self._content_type,
            yaml_content=self._content,
            version=self._version,
            description=self._description,
            tags=self._tags,
            validation_rules=self._validation_rules,
            author=self._author,
            created_at=self._created_at,
            updated_at=self._updated_at,
            metadata=self._metadata
        )
    
    @classmethod
    def pipeline_template(cls, name: str = "pipeline_template") -> Self:
        """Create a pipeline template builder."""
        return (cls()
                .with_name(name)
                .with_content_type(ContentType.documentation())
                .with_content("""
metadata:
  name: "{{name}}"
  description: "{{description}}"

inputs:
  topic:
    type: text
    label: "Topic"
    required: true

steps:
  generate:
    name: "Generate Content"
    type: llm_generate
    prompt_template: "Write about {{inputs.topic}}"
""".strip())
                .with_description("A pipeline template for testing")
                .with_tags(["pipeline", "test"]))
    
    @classmethod
    def style_template(cls, name: str = "style_template") -> Self:
        """Create a style template builder."""
        return (cls()
                .with_name(name)
                .with_content_type(ContentType.documentation())
                .with_content("""
tone: {{tone}}
style_guide: |
  Use {{tone}} tone throughout the content.
  Keep sentences {{length}}.
  Focus on {{focus}}.
""".strip())
                .with_description("A style template for testing")
                .with_tags(["style", "test"]))
    
    @classmethod
    def article_template(cls, name: str = "article_template") -> Self:
        """Create an article template builder."""
        return (cls()
                .with_name(name)
                .with_content_type(ContentType.article())
                .with_content("""
# {{title}}

## Introduction
{{introduction}}

## Main Content
{{main_content}}

## Conclusion
{{conclusion}}
""".strip())
                .with_description("An article template for testing")
                .with_tags(["article", "markdown", "test"]))
    
    @classmethod
    def with_dependencies(cls, name: str = "dependent_template", deps: List[str] = None) -> Self:
        """Create a template with dependencies."""
        dependencies = deps or ["base_template", "common_styles"]
        return (cls()
                .with_name(name)
                .with_content("Based on: {{base}}\nContent: {{content}}")
                .with_dependencies(dependencies)
                .with_description("A template with dependencies")
                .with_tags(["dependent", "test"]))


class StylePrimerBuilder:
    """Builder for StylePrimer test data."""
    
    def __init__(self) -> None:
        self._name = StyleName("test-style")
        self._description = "A test style primer"
        self._tone = "professional"
        self._voice = None
        self._writing_style = None
        self._target_audience = None
        self._language = "en"
        self._guidelines = []
        self._formatting_preferences = {}
        self._vocabulary_preferences = {}
        self._applicable_content_types = []
        self._examples = []
        self._tags = []
        self._is_published = False
        self._is_deprecated = False
        self._usage_count = 0
        self._author = None
        self._version = "1.0.0"
        self._metadata = {}
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_name(self, name: str | StyleName) -> Self:
        """Set the style name."""
        if isinstance(name, str):
            name = StyleName.from_user_input(name)
        self._name = name
        return self
    
    def with_description(self, description: str) -> Self:
        """Set the style description."""
        self._description = description
        return self
    
    def with_tone(self, tone: str) -> Self:
        """Set the style tone."""
        self._tone = tone
        return self
    
    def with_voice(self, voice: str) -> Self:
        """Set the style voice."""
        self._voice = voice
        return self
    
    def with_writing_style(self, writing_style: str) -> Self:
        """Set the writing style."""
        self._writing_style = writing_style
        return self
    
    def with_target_audience(self, target_audience: str) -> Self:
        """Set the target audience."""
        self._target_audience = target_audience
        return self
    
    def with_language(self, language: str) -> Self:
        """Set the language."""
        self._language = language
        return self
    
    def with_guidelines(self, guidelines: List[str]) -> Self:
        """Set the guidelines."""
        self._guidelines = guidelines.copy()
        return self
    
    def with_formatting_preferences(self, preferences: Dict[str, Any]) -> Self:
        """Set formatting preferences."""
        self._formatting_preferences = preferences.copy()
        return self
    
    def with_vocabulary_preferences(self, preferences: Dict[str, Any]) -> Self:
        """Set vocabulary preferences."""
        self._vocabulary_preferences = preferences.copy()
        return self
    
    def with_applicable_content_types(self, content_types: List[ContentType]) -> Self:
        """Set applicable content types."""
        self._applicable_content_types = content_types.copy()
        return self
    
    def with_examples(self, examples: List[str]) -> Self:
        """Set style examples."""
        self._examples = examples.copy()
        return self
    
    def with_tags(self, tags: List[str]) -> Self:
        """Set the tags."""
        self._tags = tags.copy()
        return self
    
    def with_published(self, is_published: bool = True) -> Self:
        """Set published status."""
        self._is_published = is_published
        return self
    
    def with_deprecated(self, is_deprecated: bool = True) -> Self:
        """Set deprecated status."""
        self._is_deprecated = is_deprecated
        return self
    
    def with_usage_count(self, usage_count: int) -> Self:
        """Set usage count."""
        self._usage_count = usage_count
        return self
    
    def with_author(self, author: str) -> Self:
        """Set the author."""
        self._author = author
        return self
    
    def with_version(self, version: str) -> Self:
        """Set the version."""
        self._version = version
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata.copy()
        return self
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> Self:
        """Set timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def build(self) -> StylePrimer:
        """Build the StylePrimer."""
        return StylePrimer(
            id=ContentId.generate(),
            name=self._name,
            description=self._description,
            tone=self._tone,
            voice=self._voice,
            writing_style=self._writing_style,
            target_audience=self._target_audience,
            language=self._language,
            guidelines=self._guidelines,
            formatting_preferences=self._formatting_preferences,
            vocabulary_preferences=self._vocabulary_preferences,
            applicable_content_types=self._applicable_content_types,
            examples=self._examples,
            tags=self._tags,
            is_published=self._is_published,
            is_deprecated=self._is_deprecated,
            created_at=self._created_at,
            updated_at=self._updated_at,
            published_at=datetime.now() if self._is_published else None,
            deprecated_at=datetime.now() if self._is_deprecated else None,
            usage_count=self._usage_count,
            author=self._author,
            version=self._version,
            metadata=self._metadata
        )
    
    @classmethod
    def professional(cls, name: str = "professional") -> Self:
        """Create a professional style primer."""
        return (cls()
                .with_name(name)
                .with_tone("professional")
                .with_voice("third_person")
                .with_writing_style("formal")
                .with_target_audience("business professionals")
                .with_guidelines([
                    "Use formal language throughout",
                    "Avoid contractions and colloquialisms",
                    "Be concise and direct",
                    "Maintain professional tone"
                ])
                .with_examples([
                    "We recommend implementing this solution to improve efficiency.",
                    "Please find the quarterly report attached for your review."
                ])
                .with_tags(["professional", "formal", "business"]))
    
    @classmethod
    def casual(cls, name: str = "casual") -> Self:
        """Create a casual style primer."""
        return (cls()
                .with_name(name)
                .with_tone("casual")
                .with_voice("second_person")
                .with_writing_style("conversational")
                .with_target_audience("general audience")
                .with_guidelines([
                    "Use conversational language",
                    "Contractions are welcome",
                    "Keep it friendly and approachable",
                    "Use active voice"
                ])
                .with_examples([
                    "Let's implement this solution together!",
                    "You'll find this approach much easier to work with."
                ])
                .with_tags(["casual", "conversational", "friendly"]))
    
    @classmethod
    def technical(cls, name: str = "technical") -> Self:
        """Create a technical style primer."""
        return (cls()
                .with_name(name)
                .with_tone("technical")
                .with_voice("third_person")
                .with_writing_style("academic")
                .with_target_audience("software developers")
                .with_guidelines([
                    "Use precise technical terminology",
                    "Include code examples where appropriate",
                    "Be specific and detailed",
                    "Reference standards and best practices"
                ])
                .with_examples([
                    "The function returns a Promise<string> object that resolves with the API response.",
                    "Implement the Observer pattern to handle state changes efficiently."
                ])
                .with_applicable_content_types([ContentType.documentation(), ContentType.code()])
                .with_tags(["technical", "documentation", "programming"]))


class GeneratedContentBuilder:
    """Builder for GeneratedContent test data."""
    
    def __init__(self) -> None:
        self._id = ContentId.generate()
        self._content_text = "# Test Content\n\nThis is test content."
        self._template_name = TemplateName("test-template")
        self._content_type = ContentType.article()
        self._format = ContentFormat.markdown()
        self._title = None
        self._summary = None
        self._style_name = None
        self._word_count = 0
        self._character_count = 0
        self._content_length = None
        
        # Generation metadata
        self._pipeline_run_id = None
        self._step_count = 0
        self._total_generation_time_seconds = 0.0
        self._llm_model_used = None
        self._total_tokens_used = 0
        self._generation_cost = 0.0
        
        # Quality and approval
        self._quality_metrics = {}
        self._approval_status = None
        self._approved_by = None
        self._approved_at = None
        self._feedback = []
        
        # Versioning and tracking
        self._version = "1.0.0"
        self._revision_count = 0
        self._parent_content_id = None
        self._tags = []
        
        # Timestamps
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._published_at = None
        
        # Additional metadata
        self._author = None
        self._metadata = {}
    
    def with_id(self, content_id: str | ContentId) -> Self:
        """Set the content ID."""
        if isinstance(content_id, str):
            content_id = ContentId(content_id)
        self._id = content_id
        return self
    
    def with_content_text(self, content_text: str) -> Self:
        """Set the content text."""
        self._content_text = content_text
        return self
    
    def with_template_name(self, template_name: str | TemplateName) -> Self:
        """Set the template name."""
        if isinstance(template_name, str):
            template_name = TemplateName(template_name)
        self._template_name = template_name
        return self
    
    def with_content_type(self, content_type: ContentType) -> Self:
        """Set the content type."""
        self._content_type = content_type
        return self
    
    def with_format(self, format: ContentFormat) -> Self:
        """Set the content format."""
        self._format = format
        return self
    
    def with_title(self, title: str) -> Self:
        """Set the title."""
        self._title = title
        return self
    
    def with_summary(self, summary: str) -> Self:
        """Set the summary."""
        self._summary = summary
        return self
    
    def with_style_name(self, style_name: str | StyleName) -> Self:
        """Set the style name."""
        if isinstance(style_name, str):
            style_name = StyleName(style_name)
        self._style_name = style_name
        return self
    
    def with_word_count(self, word_count: int) -> Self:
        """Set the word count."""
        self._word_count = word_count
        return self
    
    def with_character_count(self, character_count: int) -> Self:
        """Set the character count."""
        self._character_count = character_count
        return self
    
    def with_pipeline_run_id(self, pipeline_run_id: str) -> Self:
        """Set the pipeline run ID."""
        self._pipeline_run_id = pipeline_run_id
        return self
    
    def with_generation_metadata(
        self,
        step_count: int = 0,
        generation_time: float = 0.0,
        model_used: str = None,
        tokens_used: int = 0,
        cost: float = 0.0
    ) -> Self:
        """Set generation metadata."""
        self._step_count = step_count
        self._total_generation_time_seconds = generation_time
        self._llm_model_used = model_used
        self._total_tokens_used = tokens_used
        self._generation_cost = cost
        return self
    
    def with_quality_metrics(self, quality_metrics: Dict[str, Any]) -> Self:
        """Set quality metrics."""
        self._quality_metrics = quality_metrics.copy()
        return self
    
    def with_approval_status(self, status: str, approved_by: str = None) -> Self:
        """Set approval status."""
        self._approval_status = status
        self._approved_by = approved_by
        if status in {"approved", "rejected"}:
            self._approved_at = datetime.now()
        return self
    
    def with_feedback(self, feedback: List[str]) -> Self:
        """Set feedback."""
        self._feedback = feedback.copy()
        return self
    
    def with_version(self, version: str) -> Self:
        """Set the version."""
        self._version = version
        return self
    
    def with_revision_count(self, revision_count: int) -> Self:
        """Set revision count."""
        self._revision_count = revision_count
        return self
    
    def with_parent_content_id(self, parent_id: str | ContentId) -> Self:
        """Set parent content ID."""
        if isinstance(parent_id, str):
            parent_id = ContentId(parent_id)
        self._parent_content_id = parent_id
        return self
    
    def with_tags(self, tags: List[str]) -> Self:
        """Set the tags."""
        self._tags = tags.copy()
        return self
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> Self:
        """Set timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def with_published_at(self, published_at: datetime) -> Self:
        """Set published timestamp."""
        self._published_at = published_at
        return self
    
    def with_author(self, author: str) -> Self:
        """Set the author."""
        self._author = author
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata.copy()
        return self
    
    def build(self) -> GeneratedContent:
        """Build the GeneratedContent."""
        return GeneratedContent(
            id=self._id,
            content_text=self._content_text,
            template_name=self._template_name,
            content_type=self._content_type,
            format=self._format,
            title=self._title,
            summary=self._summary,
            style_name=self._style_name,
            word_count=self._word_count,
            character_count=self._character_count,
            content_length=self._content_length,
            pipeline_run_id=self._pipeline_run_id,
            step_count=self._step_count,
            total_generation_time_seconds=self._total_generation_time_seconds,
            llm_model_used=self._llm_model_used,
            total_tokens_used=self._total_tokens_used,
            generation_cost=self._generation_cost,
            quality_metrics=self._quality_metrics,
            approval_status=self._approval_status,
            approved_by=self._approved_by,
            approved_at=self._approved_at,
            feedback=self._feedback,
            version=self._version,
            revision_count=self._revision_count,
            parent_content_id=self._parent_content_id,
            tags=self._tags,
            created_at=self._created_at,
            updated_at=self._updated_at,
            published_at=self._published_at,
            author=self._author,
            metadata=self._metadata
        )
    
    @classmethod
    def markdown_article(cls, title: str = "Test Article") -> Self:
        """Create a markdown article builder."""
        content = f"""# {title}

## Introduction
This is the introduction to {title}.

## Main Content
Here is the main content of the article.

## Conclusion
This concludes {title}.
"""
        return (cls()
                .with_content_text(content)
                .with_template_name("article-template")
                .with_content_type(ContentType.article())
                .with_format(ContentFormat.markdown())
                .with_title(title)
                .with_tags(["article", "markdown"]))
    
    @classmethod
    def blog_post(cls, title: str = "Test Blog Post") -> Self:
        """Create a blog post builder."""
        content = f"""# {title}

This is a test blog post about {title.lower()}.

Here's some engaging content for readers to enjoy.

## Key Points

- Point one about {title.lower()}
- Point two with more details
- Point three for conclusion

Thanks for reading!
"""
        return (cls()
                .with_content_text(content)
                .with_template_name("blog-post-template")
                .with_content_type(ContentType.blog_post())
                .with_format(ContentFormat.markdown())
                .with_title(title)
                .with_tags(["blog", "post", "markdown"]))
    
    @classmethod
    def technical_doc(cls, topic: str = "API Documentation") -> Self:
        """Create a technical documentation builder."""
        content = f"""# {topic}

## Overview
This document describes the {topic.lower()}.

## Usage
```python
# Example code for {topic.lower()}
import api
result = api.call()
```

## Parameters
- `param1`: Description of parameter 1
- `param2`: Description of parameter 2

## Returns
Returns a result object with the following structure:
```json
{{"status": "success", "data": "..."}}
```
"""
        return (cls()
                .with_content_text(content)
                .with_template_name("tech-doc-template")
                .with_content_type(ContentType.documentation())
                .with_format(ContentFormat.markdown())
                .with_title(topic)
                .with_tags(["technical", "documentation", "api"]))
    
    @classmethod
    def email_content(cls, subject: str = "Test Email") -> Self:
        """Create an email content builder."""
        content = f"""Subject: {subject}

Dear Recipient,

This is a test email regarding {subject.lower()}.

Please find the important information below:

- Item 1: Important detail
- Item 2: Another detail
- Item 3: Final note

Best regards,
Test Author
"""
        return (cls()
                .with_content_text(content)
                .with_template_name("email-template")
                .with_content_type(ContentType.email())
                .with_format(ContentFormat.plain_text())
                .with_title(subject)
                .with_tags(["email", "communication"]))
    
    @classmethod
    def approved_content(cls, title: str = "Approved Content") -> Self:
        """Create approved content builder."""
        return (cls.markdown_article(title)
                .with_approval_status("approved", "reviewer@example.com")
                .with_quality_metrics({
                    "overall_score": 8.5,
                    "readability_score": 9.0,
                    "seo_score": 7.5
                }))
    
    @classmethod
    def published_content(cls, title: str = "Published Content") -> Self:
        """Create published content builder."""
        now = datetime.now()
        return (cls.approved_content(title)
                .with_published_at(now))
    
    @classmethod
    def with_generation_stats(cls, title: str = "Generated Content") -> Self:
        """Create content with generation statistics."""
        return (cls.markdown_article(title)
                .with_generation_metadata(
                    step_count=3,
                    generation_time=45.2,
                    model_used="gpt-4o-mini",
                    tokens_used=1250,
                    cost=0.025
                )
                .with_pipeline_run_id("run-12345"))