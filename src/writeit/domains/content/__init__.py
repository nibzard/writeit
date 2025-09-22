"""
Content Domain - Template and Content Management

This domain handles all aspects of content creation, template management,
validation, and content generation artifacts.

## Responsibilities

- Template creation, validation, and management
- Style primer definition and application
- Content generation artifact storage
- Template variable substitution and rendering
- Content validation and quality assurance

## Key Entities

- **ContentTemplate**: Template definition with metadata and validation
- **StylePrimer**: Style configuration and formatting rules
- **GeneratedContent**: Output content with metadata and versioning
- **TemplateValidation**: Validation results and issue reporting

## Key Value Objects

- **TemplateName**: Validated template name with naming constraints
- **ContentType**: Content type enumeration (article, documentation, etc.)
- **StyleSettings**: Style configuration object with validation
- **TemplateVariable**: Template variable definition with type information

## Domain Services

- **TemplateRenderingService**: Template variable substitution
- **ContentValidationService**: Output validation and quality checks
- **StyleApplicationService**: Style primer application
- **TemplateDiscoveryService**: Template discovery and cataloging

## Domain Events

- **TemplateCreated**: New template added
- **ContentGenerated**: New content created
- **TemplateValidated**: Validation completed
- **StylePrimerUpdated**: Style configuration changed

## Boundaries

This domain owns:
- Template definitions and metadata
- Content generation artifacts
- Template validation logic
- Style primer management
- Template variable handling

This domain does NOT own:
- File system storage (Storage Domain)
- Pipeline execution (Pipeline Domain)
- LLM integration for content generation (Execution Domain)
"""