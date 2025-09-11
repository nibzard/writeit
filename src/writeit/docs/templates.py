"""
Template system for customizable documentation output
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import jinja2
from jinja2 import Environment, FileSystemLoader, Template

from .models import (
    DocumentationSet,
    APIDocumentation,
    ModuleDocumentation,
    CLIDocumentation,
    TemplateDocumentationSet,
    UserGuide,
    CodeExample
)


@dataclass
class TemplateConfig:
    """Configuration for template system"""
    templates_dir: Path
    output_format: str = "markdown"
    custom_filters: Dict[str, Any] = None
    variables: Dict[str, Any] = None


class DocumentationTemplateSystem:
    """Template system for generating documentation"""
    
    def __init__(self, config: TemplateConfig):
        self.config = config
        self._setup_jinja_environment()
    
    def _setup_jinja_environment(self):
        """Setup Jinja2 environment with templates"""
        # Create templates directory if it doesn't exist
        self.config.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.config.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._register_custom_filters()
        
        # Add global variables
        if self.config.variables:
            self.env.globals.update(self.config.variables)
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters"""
        default_filters = {
            'code_block': self._code_block_filter,
            'sanitize_filename': self._sanitize_filename_filter,
            'format_signature': self._format_signature_filter,
            'extract_first_sentence': self._extract_first_sentence_filter,
            'titlecase': self._titlecase_filter,
            'slugify': self._slugify_filter,
            'word_wrap': self._word_wrap_filter,
            'indent_code': self._indent_code_filter
        }
        
        # Add custom filters from config
        if self.config.custom_filters:
            default_filters.update(self.config.custom_filters)
        
        for name, filter_func in default_filters.items():
            self.env.filters[name] = filter_func
    
    def _code_block_filter(self, code: str, language: str = "python") -> str:
        """Generate code block with syntax highlighting"""
        return f"```{language}\n{code}\n```"
    
    def _sanitize_filename_filter(self, filename: str) -> str:
        """Sanitize string for use as filename"""
        import re
        # Replace special characters with underscores
        return re.sub(r'[^\w\-_.]', '_', filename)
    
    def _format_signature_filter(self, signature: str) -> str:
        """Format function signature for display"""
        # Add line breaks for long signatures
        if len(signature) > 80:
            # Simple line breaking at commas
            return signature.replace(', ', ',\n    ')
        return signature
    
    def _extract_first_sentence_filter(self, text: str) -> str:
        """Extract first sentence from text"""
        if not text:
            return ""
        sentences = text.split('.')
        if sentences:
            return sentences[0].strip() + '.'
        return text
    
    def _titlecase_filter(self, text: str) -> str:
        """Convert text to title case"""
        return text.title()
    
    def _slugify_filter(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        import re
        return re.sub(r'[^\w\s-]', '', text.lower()).strip().replace(' ', '-')
    
    def _word_wrap_filter(self, text: str, width: int = 80) -> str:
        """Word wrap text to specified width"""
        import textwrap
        return '\n'.join(textwrap.wrap(text, width=width))
    
    def _indent_code_filter(self, code: str, spaces: int = 4) -> str:
        """Indent code block"""
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in code.split('\n'))
    
    def render_documentation(self, docs: DocumentationSet, template_name: str = "main.md.j2") -> str:
        """Render complete documentation using template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(
                docs=docs,
                api_docs=docs.api_docs,
                module_docs=docs.module_docs,
                cli_docs=docs.cli_docs,
                template_docs=docs.template_docs,
                user_guides=docs.user_guides,
                generated_at=docs.generated_at,
                version=docs.version
            )
        except jinja2.TemplateNotFound:
            # Fallback to default template
            return self._render_default_template(docs)
    
    def render_api_documentation(self, api_docs: APIDocumentation, template_name: str = "api.md.j2") -> str:
        """Render API documentation using template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(api_docs=api_docs)
        except jinja2.TemplateNotFound:
            return self._render_default_api_template(api_docs)
    
    def render_module_documentation(self, module_docs: List[ModuleDocumentation], template_name: str = "modules.md.j2") -> str:
        """Render module documentation using template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(modules=module_docs)
        except jinja2.TemplateNotFound:
            return self._render_default_modules_template(module_docs)
    
    def render_cli_documentation(self, cli_docs: CLIDocumentation, template_name: str = "cli.md.j2") -> str:
        """Render CLI documentation using template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(cli_docs=cli_docs)
        except jinja2.TemplateNotFound:
            return self._render_default_cli_template(cli_docs)
    
    def render_user_guide(self, guide: UserGuide, template_name: str = "guide.md.j2") -> str:
        """Render user guide using template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(guide=guide)
        except jinja2.TemplateNotFound:
            return self._render_default_guide_template(guide)
    
    def create_default_templates(self):
        """Create default template files if they don't exist"""
        templates = {
            "main.md.j2": self._get_main_template(),
            "api.md.j2": self._get_api_template(),
            "modules.md.j2": self._get_modules_template(),
            "cli.md.j2": self._get_cli_template(),
            "guide.md.j2": self._get_guide_template(),
            "module.md.j2": self._get_module_template(),
            "endpoint.md.j2": self._get_endpoint_template(),
            "class.md.j2": self._get_class_template(),
            "function.md.j2": self._get_function_template()
        }
        
        for filename, template_content in templates.items():
            template_file = self.config.templates_dir / filename
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    f.write(template_content)
    
    def _render_default_template(self, docs: DocumentationSet) -> str:
        """Fallback default template rendering"""
        template_content = self._get_main_template()
        template = self.env.from_string(template_content)
        return template.render(
            docs=docs,
            api_docs=docs.api_docs,
            module_docs=docs.module_docs,
            cli_docs=docs.cli_docs,
            template_docs=docs.template_docs,
            user_guides=docs.user_guides,
            generated_at=docs.generated_at,
            version=docs.version
        )
    
    def _render_default_api_template(self, api_docs: APIDocumentation) -> str:
        """Fallback API template rendering"""
        template_content = self._get_api_template()
        template = self.env.from_string(template_content)
        return template.render(api_docs=api_docs)
    
    def _render_default_modules_template(self, module_docs: List[ModuleDocumentation]) -> str:
        """Fallback modules template rendering"""
        template_content = self._get_modules_template()
        template = self.env.from_string(template_content)
        return template.render(modules=module_docs)
    
    def _render_default_cli_template(self, cli_docs: CLIDocumentation) -> str:
        """Fallback CLI template rendering"""
        template_content = self._get_cli_template()
        template = self.env.from_string(template_content)
        return template.render(cli_docs=cli_docs)
    
    def _render_default_guide_template(self, guide: UserGuide) -> str:
        """Fallback guide template rendering"""
        template_content = self._get_guide_template()
        template = self.env.from_string(template_content)
        return template.render(guide=guide)
    
    def _get_main_template(self) -> str:
        """Get main documentation template"""
        return '''# {{ docs.api_docs.title if docs.api_docs else "WriteIt" }} Documentation

Welcome to auto-generated documentation. This documentation is generated directly from source code.

## Quick Links

{% if docs.api_docs -%}
- [API Documentation](#api-documentation) - {{ docs.api_docs.endpoints|length }} endpoints
{% endif -%}
{% if docs.module_docs -%}
- [Module Documentation](#module-documentation) - {{ docs.module_docs|length }} modules
{% endif -%}
{% if docs.cli_docs -%}
- [CLI Documentation](#cli-documentation) - {{ docs.cli_docs.commands|length }} commands
{% endif -%}
{% if docs.template_docs -%}
- [Pipeline Templates](#pipeline-templates) - {{ docs.template_docs.templates|length }} templates
{% endif -%}
{% if docs.user_guides -%}
- [User Guides](#user-guides) - {{ docs.user_guides|length }} guides
{% endif %}

## Generated Information

- **Generated**: {{ generated_at.strftime("%Y-%m-%d %H:%M:%S") }}
- **Version**: {{ version }}
- **Total Coverage**: {{ ((docs.module_docs|length) + (docs.api_docs.endpoints|length if docs.api_docs else 0))|string }} items documented

{% if docs.api_docs %}
## API Documentation

{{ docs.api_docs.description }}

**Base URL**: `{{ docs.api_docs.base_url }}`  
**Version**: `{{ docs.api_docs.version }}`

### Endpoints

{% for endpoint in docs.api_docs.endpoints %}
#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type_annotation }}): {{ param.description }}{% if param.required %} *Required*{% endif %}
{% endfor %}
{% endif %}

{% if endpoint.examples %}
**Examples:**
{% for example in endpoint.examples %}
{{ example.code | code_block(example.language) }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if docs.module_docs %}
## Module Documentation

{% for module in docs.module_docs %}
### {{ module.name }}

{{ module.description }}

**Purpose**: {{ module.purpose }}

{% if module.classes %}
#### Classes

{% for class_doc in module.classes %}
##### {{ class_doc.name }}

{{ class_doc.description }}

{% if class_doc.methods %}
**Methods:**
{% for method in class_doc.methods %}
- `{{ method.name }}{{ method.signature | format_signature }}`: {{ method.description | extract_first_sentence }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if module.functions %}
#### Functions

{% for func in module.functions %}
##### {{ func.name }}

{{ func.signature | code_block }}

{{ func.description }}

{% if func.parameters %}
**Parameters:**
{% for param in func.parameters %}
- `{{ param.name }}` ({{ param.type_annotation }}): {{ param.description }}
{% endfor %}
{% endif %}

**Returns**: {{ func.return_type }} - {{ func.return_description }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if docs.cli_docs %}
## CLI Documentation

{{ docs.cli_docs.description }}

{% for command in docs.cli_docs.commands %}
### {{ command.name }}

{{ command.description }}

**Usage**: `{{ command.usage }}`

{% if command.arguments %}
**Arguments:**
{% for arg in command.arguments %}
- `{{ arg.name }}` ({{ arg.type_annotation }}): {{ arg.description }}{% if arg.required %} *Required*{% endif %}
{% endfor %}
{% endif %}

{% if command.options %}
**Options:**
{% for option in command.options %}
- `--{{ option.name }}` ({{ option.type_annotation }}): {{ option.description }}{% if option.default_value %} (default: {{ option.default_value }}){% endif %}
{% endfor %}
{% endif %}

{% if command.examples %}
**Examples:**
{% for example in command.examples %}
```bash
{{ example }}
```
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if docs.template_docs and docs.template_docs.templates %}
## Pipeline Templates

{% for template in docs.template_docs.templates %}
### {{ template.name }}

{{ template.description }}

**Version**: {{ template.version }}

{% if template.inputs %}
**Inputs:**
{% for input_field in template.inputs %}
- `{{ input_field.name }}` ({{ input_field.type }}): {{ input_field.description }}{% if input_field.required %} *Required*{% endif %}
{% endfor %}
{% endif %}

{% if template.steps %}
**Steps:**
{% for step in template.steps %}
1. **{{ step.name }}** ({{ step.type }}): {{ step.description }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if docs.user_guides %}
## User Guides

{% for guide in docs.user_guides %}
### {{ guide.title }}

{{ guide.description }}

**Audience**: {{ guide.audience }}  
**Difficulty**: {{ guide.difficulty }}  
**Time**: {{ guide.estimated_time }}

---
{% endfor %}
{% endif %}

---

*This documentation is automatically generated. Please report any issues or inconsistencies.*
'''
    
    def _get_api_template(self) -> str:
        """Get API documentation template"""
        return '''# API Documentation

{{ api_docs.description }}

**Base URL**: `{{ api_docs.base_url }}`  
**Version**: `{{ api_docs.version }}`

## Endpoints

{% for endpoint in api_docs.endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type_annotation }}): {{ param.description }}{% if param.required %} *Required*{% endif %}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
**Request Body:**
{{ endpoint.request_body | code_block("json") }}
{% endif %}

{% if endpoint.status_codes %}
**Status Codes:**
{% for code, description in endpoint.status_codes.items() %}
- `{{ code }}`: {{ description }}
{% endfor %}
{% endif %}

{% if endpoint.examples %}
**Examples:**
{% for example in endpoint.examples %}
##### {{ example.description }}
{{ example.code | code_block(example.language) }}
{% endfor %}
{% endif %}

---
{% endfor %}

{% if api_docs.models %}
## Models

{% for model in api_docs.models %}
### {{ model.name }}

{{ model.description }}

{% if model.fields %}
**Fields:**
{% for field, description in model.fields.items() %}
- `{{ field }}`: {{ description }}
{% endfor %}
{% endif %}

{% if model.examples %}
**Examples:**
{% for example in model.examples %}
{{ example | code_block("json") }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}
'''
    
    def _get_modules_template(self) -> str:
        """Get modules documentation template"""
        return '''# Module Documentation

{% for module in modules %}
## {{ module.name }}

{{ module.description }}

**Purpose**: {{ module.purpose }}
**File**: `{{ module.source_file }}`

{% if module.dependencies %}
**Dependencies:**
{% for dep in module.dependencies %}
- {{ dep }}
{% endfor %}
{% endif %}

{% if module.classes %}
### Classes

{% for class_doc in module.classes %}
#### {{ class_doc.name }}

{{ class_doc.description }}

**Purpose**: {{ class_doc.purpose }}

{% if class_doc.inheritance %}
**Inherits from**: {{ class_doc.inheritance | join(", ") }}
{% endif %}

{% if class_doc.methods %}
##### Methods

{% for method in class_doc.methods %}
###### {{ method.name }}

```python
{{ method.signature }}
```

{{ method.description }}

{% if method.parameters %}
**Parameters:**
{% for param in method.parameters %}
- `{{ param.name }}` ({{ param.type_annotation }}): {{ param.description }}
{% endfor %}
{% endif %}

**Returns**: {{ method.return_type }} - {{ method.return_description }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if module.functions %}
### Functions

{% for func in module.functions %}
#### {{ func.name }}

```python
{{ func.signature }}
```

{{ func.description }}

{% if func.parameters %}
**Parameters:**
{% for param in func.parameters %}
- `{{ param.name }}` ({{ param.type_annotation }}): {{ param.description }}
{% endfor %}
{% endif %}

**Returns**: {{ func.return_type }} - {{ func.return_description }}
{% endfor %}
{% endif %}

---
{% endfor %}
'''
    
    def _get_cli_template(self) -> str:
        """Get CLI documentation template"""
        return '''# CLI Documentation

{{ cli_docs.description }}

{% for command in cli_docs.commands %}
## {{ command.name }}

{{ command.description }}

**Usage**: `{{ command.usage }}`

{% if command.arguments %}
### Arguments

{% for arg in command.arguments %}
- `{{ arg.name }}` ({{ arg.type_annotation }}): {{ arg.description }}{% if arg.required %} *Required*{% endif %}
{% endfor %}
{% endif %}

{% if command.options %}
### Options

{% for option in command.options %}
- `--{{ option.name }}` ({{ option.type_annotation }}): {{ option.description }}{% if option.default_value %} (default: {{ option.default_value }}){% endif %}
{% endfor %}
{% endif %}

{% if command.examples %}
### Examples

{% for example in command.examples %}
```bash
{{ example }}
```
{% endfor %}
{% endif %}

---
{% endfor %}
'''
    
    def _get_guide_template(self) -> str:
        """Get user guide template"""
        return '''# {{ guide.title }}

{{ guide.description }}

**Audience**: {{ guide.audience }}  
**Difficulty**: {{ guide.difficulty }}  
**Estimated Time**: {{ guide.estimated_time }}

{% if guide.prerequisites %}
## Prerequisites

{% for prereq in guide.prerequisites %}
- {{ prereq }}
{% endfor %}
{% endif %}

## Content

{{ guide.content }}

{% if guide.examples %}
## Examples

{% for example in guide.examples %}
### {{ example.description }}

{{ example.code | code_block(example.language) }}
{% endfor %}
{% endif %}

{% if guide.related_guides %}
## Related Guides

{% for related in guide.related_guides %}
- {{ related }}
{% endfor %}
{% endif %}
'''
    
    def _get_module_template(self) -> str:
        """Get individual module template"""
        return '''# {{ module.name }}

{{ module.description }}

**Purpose**: {{ module.purpose }}

{% if module.classes or module.functions %}
## API Reference

{% for class_doc in module.classes %}
### {{ class_doc.name }}

{{ class_doc.description }}
{% endfor %}

{% for func in module.functions %}
### {{ func.name }}

{{ func.signature | code_block }}

{{ func.description }}
{% endfor %}
{% endif %}
'''
    
    def _get_endpoint_template(self) -> str:
        """Get API endpoint template"""
        return '''# {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{{ endpoint.summary }}

{% if endpoint.parameters %}
## Parameters

{% for param in endpoint.parameters %}
- **{{ param.name }}** ({{ param.type_annotation }}): {{ param.description }}{% if param.required %} *Required*{% endif %}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
## Request Body

{{ endpoint.request_body | code_block("json") }}
{% endif %}

{% if endpoint.status_codes %}
## Response Codes

{% for code, description in endpoint.status_codes.items() %}
- **{{ code }}**: {{ description }}
{% endfor %}
{% endif %}
'''
    
    def _get_class_template(self) -> str:
        """Get class documentation template"""
        return '''# {{ class_doc.name }}

{{ class_doc.description }}

**Purpose**: {{ class_doc.purpose }}

{% if class_doc.methods %}
## Methods

{% for method in class_doc.methods %}
### {{ method.name }}

{{ method.signature | code_block }}

{{ method.description }}
{% endfor %}
{% endif %}
'''
    
    def _get_function_template(self) -> str:
        """Get function documentation template"""
        return '''# {{ func.name }}

{{ func.signature | code_block }}

{{ func.description }}

{% if func.parameters %}
## Parameters

{% for param in func.parameters %}
- **{{ param.name }}** ({{ param.type_annotation }}): {{ param.description }}
{% endfor %}
{% endif %}

**Returns**: {{ func.return_type }} - {{ func.return_description }}
'''


class TemplateManager:
    """Manage documentation templates"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def create_template_structure(self):
        """Create complete template directory structure"""
        # Create subdirectories
        subdirs = ["api", "modules", "cli", "templates", "guides"]
        for subdir in subdirs:
            (self.templates_dir / subdir).mkdir(exist_ok=True)
        
        # Create template system
        config = TemplateConfig(templates_dir=self.templates_dir)
        template_system = DocumentationTemplateSystem(config)
        template_system.create_default_templates()
    
    def list_templates(self) -> List[Path]:
        """List all available templates"""
        return list(self.templates_dir.rglob("*.j2"))
    
    def validate_template(self, template_path: Path) -> bool:
        """Validate template syntax"""
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            env = Environment()
            env.parse(template_content)
            return True
        except Exception as e:
            print(f"Template validation failed: {e}")
            return False