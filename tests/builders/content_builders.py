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
        self._name = StyleName("test_style")
        self._tone = "professional"
        self._style_guide = "Use clear and concise language"
        self._examples = {}
        self._rules = []
        self._metadata = {}
        self._version = "1.0.0"
        self._description = "A test style primer"
        self._tags = []
        self._author = None
        self._file_path = None
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_name(self, name: str | StyleName) -> Self:
        """Set the style name."""
        if isinstance(name, str):
            name = StyleName(name)
        self._name = name
        return self
    
    def with_tone(self, tone: str) -> Self:
        """Set the style tone."""
        self._tone = tone
        return self
    
    def with_style_guide(self, guide: str) -> Self:
        """Set the style guide."""
        self._style_guide = guide
        return self
    
    def with_examples(self, examples: Dict[str, str]) -> Self:
        """Set style examples."""
        self._examples = examples
        return self
    
    def with_rules(self, rules: List[ValidationRule]) -> Self:
        """Set style rules."""
        self._rules = rules
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata
        return self
    
    def with_version(self, version: str) -> Self:
        """Set the version."""
        self._version = version
        return self
    
    def with_description(self, description: str) -> Self:
        """Set the description."""
        self._description = description
        return self
    
    def with_tags(self, tags: List[str]) -> Self:
        """Set the tags."""
        self._tags = tags
        return self
    
    def with_author(self, author: str) -> Self:
        """Set the author."""
        self._author = author
        return self
    
    def with_file_path(self, file_path: str | Path) -> Self:
        """Set the file path."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        self._file_path = file_path
        return self
    
    def build(self) -> StylePrimer:
        """Build the StylePrimer."""
        return StylePrimer(
            name=self._name,
            tone=self._tone,
            style_guide=self._style_guide,
            examples=self._examples,
            rules=self._rules,
            metadata=self._metadata,
            version=self._version,
            description=self._description,
            tags=self._tags,
            author=self._author,
            file_path=self._file_path,
            created_at=self._created_at,
            updated_at=self._updated_at
        )
    
    @classmethod
    def professional(cls, name: str = "professional") -> Self:
        """Create a professional style primer."""
        return (cls()
                .with_name(name)
                .with_tone("professional")
                .with_style_guide("Use formal language, avoid contractions, be concise")
                .with_examples({
                    "good": "We recommend implementing this solution.",
                    "bad": "We'd suggest implementing this solution."
                })
                .with_tags(["professional", "formal"]))
    
    @classmethod
    def casual(cls, name: str = "casual") -> Self:
        """Create a casual style primer."""
        return (cls()
                .with_name(name)
                .with_tone("casual")
                .with_style_guide("Use conversational language, contractions are fine")
                .with_examples({
                    "good": "Let's implement this solution!",
                    "bad": "We shall implement this solution."
                })
                .with_tags(["casual", "conversational"]))
    
    @classmethod
    def technical(cls, name: str = "technical") -> Self:
        """Create a technical style primer."""
        return (cls()
                .with_name(name)
                .with_tone("technical")
                .with_style_guide("Use precise terminology, include code examples, be specific")
                .with_examples({
                    "good": "The function returns a Promise<string> object.",
                    "bad": "The function returns something."
                })
                .with_tags(["technical", "documentation"]))


class GeneratedContentBuilder:
    """Builder for GeneratedContent test data."""
    
    def __init__(self) -> None:
        self._id = ContentId.generate()
        self._content_format = ContentFormat.MARKDOWN
        self._content = "# Test Content\n\nThis is test content."
        self._source_template = None
        self._source_inputs = {}
        self._metadata = {}
        self._version = "1.0.0"
        self._workspace_name = "test_workspace"
        self._tags = []
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_id(self, content_id: str | ContentId) -> Self:
        """Set the content ID."""
        if isinstance(content_id, str):
            content_id = ContentId(content_id)
        self._id = content_id
        return self
    
    def with_format(self, content_format: ContentFormat) -> Self:
        """Set the content format."""
        self._content_format = content_format
        return self
    
    def with_content(self, content: str) -> Self:
        """Set the content."""
        self._content = content
        return self
    
    def with_source_template(self, template_name: str | TemplateName) -> Self:
        """Set the source template."""
        if isinstance(template_name, str):
            template_name = TemplateName(template_name)
        self._source_template = template_name
        return self
    
    def with_source_inputs(self, inputs: Dict[str, Any]) -> Self:
        """Set the source inputs."""
        self._source_inputs = inputs
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata
        return self
    
    def with_version(self, version: str) -> Self:
        """Set the version."""
        self._version = version
        return self
    
    def with_workspace(self, workspace_name: str) -> Self:
        """Set the workspace name."""
        self._workspace_name = workspace_name
        return self
    
    def with_tags(self, tags: List[str]) -> Self:
        """Set the tags."""
        self._tags = tags
        return self
    
    def with_generation_info(self, template: str, inputs: Dict[str, Any]) -> Self:
        """Set generation information."""
        return (self
                .with_source_template(template)
                .with_source_inputs(inputs)
                .with_metadata({
                    "generated_from": template,
                    "generation_time": datetime.now().isoformat()
                }))
    
    def build(self) -> GeneratedContent:
        """Build the GeneratedContent."""
        return GeneratedContent(
            id=self._id,
            content_format=self._content_format,
            content=self._content,
            source_template=self._source_template,
            source_inputs=self._source_inputs,
            metadata=self._metadata,
            version=self._version,
            workspace_name=self._workspace_name,
            tags=self._tags,
            created_at=self._created_at,
            updated_at=self._updated_at
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
                .with_format(ContentFormat.MARKDOWN)
                .with_content(content)
                .with_source_inputs({"title": title})
                .with_tags(["article", "markdown"]))
    
    @classmethod
    def json_data(cls, data: Dict[str, Any] = None) -> Self:
        """Create a JSON data builder."""
        test_data = data or {"test": "data", "number": 42}
        import json
        content = json.dumps(test_data, indent=2)
        return (cls()
                .with_format(ContentFormat.JSON)
                .with_content(content)
                .with_source_inputs(test_data)
                .with_tags(["data", "json"]))
    
    @classmethod
    def yaml_config(cls, config: Dict[str, Any] = None) -> Self:
        """Create a YAML config builder."""
        test_config = config or {"setting1": "value1", "setting2": 42}
        import yaml
        content = yaml.dump(test_config, indent=2)
        return (cls()
                .with_format(ContentFormat.YAML)
                .with_content(content)
                .with_source_inputs(test_config)
                .with_tags(["config", "yaml"]))
    
    @classmethod
    def from_template(cls, template_name: str, inputs: Dict[str, Any]) -> Self:
        """Create content from template inputs."""
        content = f"Generated from {template_name} with inputs: {inputs}"
        return (cls()
                .with_content(content)
                .with_generation_info(template_name, inputs)
                .with_tags(["generated", "template"]))
    
    @classmethod
    def large_content(cls, size_kb: int = 10) -> Self:
        """Create large content for testing."""
        content = "Large content test. " * (size_kb * 50)  # Rough KB estimate
        return (cls()
                .with_content(content)
                .with_metadata({"size_estimate_kb": size_kb})
                .with_tags(["large", "test"]))