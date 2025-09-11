# Contributing to WriteIt Documentation

This guide explains how to contribute to WriteIt's documentation system and maintain high-quality, up-to-date documentation.

## Documentation Architecture

WriteIt uses an automated documentation system that generates comprehensive documentation from code, templates, and user guides.

### Components

- **Code Documentation**: Auto-extracted from docstrings and type hints
- **API Documentation**: Generated from FastAPI OpenAPI specifications
- **CLI Documentation**: Extracted from Typer command definitions
- **Templates**: Jinja2 templates for customizable output
- **User Guides**: Manually written guides and tutorials

## Documentation Workflow

### 1. Automated Generation

Documentation is automatically generated from:
- Python docstrings in source code
- FastAPI route definitions and models
- Typer CLI command definitions
- YAML pipeline templates
- Test examples and usage patterns

### 2. Manual Content

Create user guides and tutorials in the appropriate directories:
- `docs/user/` - User-focused guides
- `docs/developer/` - Developer documentation
- `docs/examples/` - Code examples and tutorials

### 3. Templates

Customize documentation output using Jinja2 templates in `docs/templates/`:
- `main.md.j2` - Main documentation template
- `api.md.j2` - API documentation template
- `modules.md.j2` - Module documentation template
- `cli.md.j2` - CLI documentation template

## Writing Good Documentation

### Code Documentation

```python
def process_pipeline(pipeline_config: dict, workspace: str = "default") -> PipelineResult:
    """
    Execute a pipeline with the given configuration.
    
    This function processes a complete pipeline by executing each step
    in sequence, handling dependencies and error conditions.
    
    Args:
        pipeline_config: Pipeline configuration dictionary containing
            metadata, inputs, and step definitions
        workspace: Workspace name for execution context
        
    Returns:
        PipelineResult containing execution status, outputs, and metrics
        
    Raises:
        ValidationError: If pipeline configuration is invalid
        ExecutionError: If pipeline execution fails
        
    Example:
        ```python
        config = {
            "metadata": {"name": "test-pipeline"},
            "steps": [{"name": "step1", "type": "llm_generate"}]
        }
        result = process_pipeline(config, "my-workspace")
        print(f"Status: {result.status}")
        ```
    """
```

### API Documentation

FastAPI automatically generates OpenAPI documentation. Enhance it with:

```python
@app.post("/api/runs", response_model=PipelineRun, tags=["execution"])
async def create_run(
    request: CreateRunRequest,
    workspace: str = Query(default="default", description="Target workspace")
) -> PipelineRun:
    """
    Create a new pipeline run.
    
    Creates and initializes a new pipeline run in the specified workspace.
    The run will be ready for execution after creation.
    
    - **pipeline_id**: ID of the pipeline to run
    - **inputs**: Input values for the pipeline
    - **workspace**: Workspace context for execution
    """
```

### CLI Documentation

Typer commands are automatically documented. Use clear descriptions:

```python
@app.command()
def generate(
    output: Path = typer.Option(
        Path("docs/generated"), 
        "--output", "-o",
        help="Output directory for generated documentation"
    ),
    format: List[str] = typer.Option(
        ["markdown"], 
        "--format", "-f",
        help="Output format(s): markdown, html, pdf"
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate documentation after generation"
    )
):
    """
    Generate documentation from source code.
    
    This command analyzes the codebase and generates comprehensive
    documentation in the specified formats. It extracts information
    from docstrings, type hints, and API definitions.
    
    Examples:
        writeit docs generate --format html --format pdf
        writeit docs generate --output ./custom-docs --no-validate
    """
```

## Local Development

### Setup

```bash
# Install pre-commit hooks
uv run pre-commit install

# Generate documentation locally
uv run writeit docs generate --verbose

# Validate documentation
uv run writeit docs validate --detailed

# Preview documentation
uv run writeit docs preview
```

### Testing Documentation

```bash
# Run documentation tests
uv run pytest tests/documentation/

# Test specific components
uv run pytest tests/documentation/test_generator.py -v

# Test with coverage
uv run pytest tests/documentation/ --cov=src/writeit/docs
```

## CI/CD Integration

### Pre-commit Hooks

The following hooks run automatically before commits:

1. **Code formatting** (Ruff)
2. **Type checking** (mypy)
3. **Documentation generation** (validates and regenerates)
4. **Documentation validation** (checks quality and links)
5. **Template validation** (validates Jinja2 templates)

### GitHub Actions

Three workflows handle documentation:

1. **Documentation Workflow** (`docs.yml`):
   - Generates documentation on every push
   - Validates links and examples
   - Deploys to GitHub Pages
   - Creates PDF versions

2. **Test Workflow** (`tests.yml`):
   - Runs documentation tests
   - Validates code quality
   - Checks test coverage

3. **Release Workflow** (`release.yml`):
   - Generates comprehensive release documentation
   - Attaches documentation to GitHub releases
   - Creates archived documentation

## Quality Standards

### Documentation Coverage

Maintain high documentation coverage:
- **API Endpoints**: >95% documented
- **Public Classes**: >90% documented
- **Public Functions**: >90% documented
- **CLI Commands**: 100% documented

### Link Health

- All external links must be valid
- Internal references must resolve correctly
- Examples must be syntactically correct
- Code examples should be executable

### Style Guidelines

1. **Clear and Concise**: Write for your audience
2. **Examples**: Include practical examples
3. **Structure**: Use consistent formatting
4. **Updates**: Keep documentation current with code

## Troubleshooting

### Common Issues

1. **Generation Failures**:
   ```bash
   # Check for syntax errors in docstrings
   uv run python -m py_compile src/writeit/**/*.py
   
   # Validate templates
   uv run writeit validate --type template --detailed
   ```

2. **Link Validation Failures**:
   ```bash
   # Test specific links
   curl -I https://example.com/broken-link
   
   # Skip external link validation
   uv run writeit docs validate --no-links
   ```

3. **PDF Generation Issues**:
   ```bash
   # Install system dependencies
   sudo apt-get install libcairo2-dev libpango1.0-dev
   
   # Install Python dependencies
   uv add weasyprint reportlab
   ```

### Getting Help

- Check the [GitHub Issues](https://github.com/nibzard/writeit/issues) for known issues
- Use `writeit docs --help` for command-line help
- Run `writeit docs validate --detailed` for validation details

## Contributing Guidelines

1. **Code First**: Write clear, documented code
2. **Test Documentation**: Ensure examples work
3. **Validate Locally**: Run validation before committing
4. **Update Templates**: Customize output as needed
5. **Review Process**: Documentation changes go through PR review

## Advanced Topics

### Custom Templates

Create custom Jinja2 templates for specialized output:

```jinja2
# docs/templates/custom-api.md.j2
# {{ api_docs.title }} API Reference

{{ api_docs.description }}

{% for endpoint in api_docs.endpoints %}
## {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

### Parameters
{% for param in endpoint.parameters %}
- **{{ param.name }}** ({{ param.type_annotation }}): {{ param.description }}
{% endfor %}
{% endfor %}
```

### Extension Points

The documentation system supports:
- Custom extractors for new content types
- Custom validators for specialized checks
- Custom deployment targets
- Integration with external tools

### Performance Optimization

For large codebases:
- Use selective generation with filters
- Cache generated content
- Parallelize extraction processes
- Optimize template rendering

---

**Remember**: Great documentation is a living part of the codebase. Keep it updated, accurate, and useful for your users!