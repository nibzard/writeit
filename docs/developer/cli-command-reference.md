# WriteIt CLI Command Reference

This document provides a comprehensive reference for all WriteIt CLI commands, organized by functional area.

## 📋 Quick Reference

| Command | Description | Examples |
|---------|-------------|----------|
| `writeit init` | Initialize WriteIt workspace | `writeit init`, `writeit init --migrate` |
| `writeit workspace create` | Create new workspace | `writeit workspace create my-project` |
| `writeit workspace use` | Switch active workspace | `writeit workspace use my-project` |
| `writeit workspace list` | List all workspaces | `writeit workspace list` |
| `writeit run` | Execute pipeline | `writeit run article.yaml`, `writeit run article.yaml --tui` |
| `writeit list-pipelines` | List available pipelines | `writeit list-pipelines` |
| `writeit validate` | Validate templates/styles | `writeit validate tech-article` |
| `writeit template` | Template management | `writeit template list` |
| `writeit style` | Style primer management | `writeit style list` |

---

## 🏗️ Initialization

### `writeit init`

Initialize WriteIt global workspace structure.

```bash
# Basic initialization
writeit init

# Initialize with migration from existing data
writeit init --migrate

# Force reinitialization (warning: may overwrite existing data)
writeit init --force
```

**Options:**
- `--migrate`: Migrate existing workspace data to new structure
- `--force`: Force initialization even if WriteIt is already initialized

**What it creates:**
```
~/.writeit/
├── config.yaml                 # Global configuration
├── templates/                  # Global pipeline templates
├── styles/                     # Global style primers
├── workspaces/                 # User workspace directory
│   ├── default/               # Default workspace
│   └── project1/              # Example project workspace
└── cache/                     # LLM response cache
```

---

## 🗂️ Workspace Management

### `writeit workspace create`

Create a new workspace.

```bash
# Create workspace
writeit workspace create my-project

# Create and set as active
writeit workspace create my-project --set-active

# Create with description
writeit workspace create my-project --description "My blog project"
```

**Options:**
- `--set-active, -s`: Set as active workspace after creation
- `--description`: Workspace description
- `--template`: Create from workspace template

### `writeit workspace list`

List all available workspaces.

```bash
# List all workspaces
writeit workspace list

# List with detailed information
writeit workspace list --verbose

# List in JSON format
writeit workspace list --format json
```

**Options:**
- `--verbose, -v`: Show detailed workspace information
- `--format`: Output format (table, json)

### `writeit workspace use`

Switch to a different workspace.

```bash
# Switch to workspace
writeit workspace use my-project

# Switch and verify
writeit workspace use my-project --verify
```

**Options:**
- `--verify`: Verify workspace structure after switching

### `writeit workspace info`

Show information about current or specified workspace.

```bash
# Show current workspace info
writeit workspace info

# Show specific workspace info
writeit workspace info my-project

# Show with storage details
writeit workspace info my-project --include-storage
```

**Options:**
- `--include-storage`: Include storage usage information
- `--format`: Output format (table, json)

### `writeit workspace remove`

Delete a workspace.

```bash
# Delete workspace (with confirmation)
writeit workspace remove my-project

# Force delete without confirmation
writeit workspace remove my-project --force

# Delete and cleanup storage
writeit workspace remove my-project --cleanup-storage
```

**Options:**
- `--force`: Skip confirmation prompt
- `--cleanup-storage`: Remove all storage data

---

## 🚀 Pipeline Execution

### `writeit run`

Execute a pipeline template.

```bash
# Basic pipeline execution
writeit run article.yaml

# Execute with TUI interface
writeit run article.yaml --tui

# Execute with custom inputs
writeit run article.yaml --inputs topic="AI Ethics" style="academic"

# Execute with specific workspace
writeit run article.yaml --workspace blog-project

# Execute global template
writeit run --global tech-article
```

**Options:**
- `--tui`: Use Terminal User Interface for rich interaction
- `--workspace, -w`: Workspace to execute in (default: current active)
- `--global`: Use global template instead of workspace-specific
- `--inputs, -i`: Pipeline inputs as key=value pairs
- `--dry-run`: Show what would be executed without running
- `--verbose, -v`: Verbose output

**Input Examples:**
```bash
# Multiple inputs
writeit run article.yaml --inputs topic="WebAssembly" style="technical" audience="developers"

# JSON input for complex data
writeit run article.yaml --inputs '{"topic": "AI", "style": "academic", "keywords": ["ML", "ethics"]}'
```

### `writeit list-pipelines`

List available pipeline templates.

```bash
# List pipelines in current workspace
writeit list-pipelines

# List global pipelines
writeit list-pipelines --global

# List with descriptions
writeit list-pipelines --verbose

# List in JSON format
writeit list-pipelines --format json
```

**Options:**
- `--global`: List global templates instead of workspace templates
- `--verbose, -v`: Show template descriptions and metadata
- `--format`: Output format (table, json)
- `--workspace`: Specify workspace (default: current active)

---

## ✅ Validation

### `writeit validate`

Validate pipeline templates and style primers.

```bash
# Validate pipeline template
writeit validate tech-article

# Validate style primer
writeit validate --type style academic-voice

# Validate with detailed output
writeit validate --detailed tech-article

# Validate global template
writeit validate --global tech-article

# Validate local file
writeit validate --local ./my-template.yaml
```

**Options:**
- `--type`: Validation type (pipeline, style, auto-detect)
- `--detailed`: Show detailed validation issues and suggestions
- `--global`: Validate global template/style
- `--local`: Validate local file instead of registered template
- `--workspace`: Workspace context for validation

**Validation Types:**
- `pipeline`: Validate pipeline template structure and business rules
- `style`: Validate style primer format and guidelines
- `auto`: Auto-detect based on template name

---

## 📄 Template Management

### `writeit template list`

List available templates.

```bash
# List all templates
writeit template list

# List pipeline templates only
writeit template list --type pipeline

# List style templates only
writeit template list --type style

# List with source information
writeit template list --show-source
```

**Options:**
- `--type`: Filter by template type (pipeline, style, all)
- `--show-source`: Show template source (global/workspace)
- `--format`: Output format (table, json)

### `writeit template show`

Show template content.

```bash
# Show template content
writeit template show tech-article

# Show style primer content
writeit template show academic-voice --type style

# Show raw YAML
writeit template show tech-article --raw
```

**Options:**
- `--type`: Template type (pipeline, style)
- `--raw`: Show raw content without formatting
- `--workspace`: Workspace context

### `writeit template create`

Create new template.

```bash
# Create pipeline template
writeit template create my-pipeline --type pipeline

# Create style primer
writeit template create my-style --type style

# Create from template
writeit template create my-pipeline --type pipeline --from-template tech-article
```

**Options:**
- `--type`: Template type (pipeline, style)
- `--from-template`: Create from existing template
- `--workspace`: Target workspace (default: current)

### `writeit template update`

Update existing template.

```bash
# Update template from file
writeit template update tech-article --file ./updated-template.yaml

# Update template content
writeit template update tech-article --editor
```

**Options:**
- `--file`: Update from file
- `--editor`: Open in editor for manual update
- `--workspace`: Workspace context

### `writeit template remove`

Remove template.

```bash
# Remove template
writeit template remove old-template

# Remove without confirmation
writeit template remove old-template --force
```

**Options:**
- `--force`: Skip confirmation prompt
- `--workspace`: Workspace context

---

## 🎨 Style Management

### `writeit style list`

List available style primers.

```bash
# List all style primers
writeit style list

# List with descriptions
writeit style list --verbose

# List in categories
writeit style list --by-category
```

**Options:**
- `--verbose, -v`: Show style descriptions and examples
- `--by-category`: Group by style categories
- `--format`: Output format (table, json)

### `writeit style show`

Show style primer details.

```bash
# Show style primer
writeit style show academic-voice

# Show with examples
writeit style show academic-voice --include-examples

# Show validation rules
writeit style show academic-voice --show-rules
```

**Options:**
- `--include-examples`: Include writing examples
- `--show-rules`: Show validation rules
- `--workspace`: Workspace context

### `writeit style create`

Create new style primer.

```bash
# Create style primer interactively
writeit style create my-style

# Create from template
writeit style create my-style --from academic-voice

# Create with predefined tone
writeit style create my-style --tone formal --audience technical
```

**Options:**
- `--from`: Create from existing style primer
- `--tone`: Set tone (formal, casual, academic, etc.)
- `--audience`: Set target audience
- `--workspace`: Target workspace

### `writeit style test`

Test style primer with sample content.

```bash
# Test style primer
writeit style test academic-voice --sample "This is a test document."

# Test with file
writeit style test academic-voice --file sample.txt

# Test with validation
writeit style test academic-voice --sample "Test" --validate
```

**Options:**
- `--sample`: Test with sample text
- `--file`: Test with file content
- `--validate`: Validate output against style rules
- `--workspace`: Workspace context

---

## 📚 Documentation

### `writeit docs generate`

Generate documentation for templates and styles.

```bash
# Generate documentation for current workspace
writeit docs generate

# Generate specific template docs
writeit docs generate --template tech-article

# Generate in different formats
writeit docs generate --format markdown
writeit docs generate --format html
```

**Options:**
- `--template`: Generate docs for specific template
- `--format`: Output format (markdown, html, json)
- `--output`: Output directory
- `--workspace`: Workspace context

### `writeit docs serve`

Serve documentation locally.

```bash
# Serve docs on default port
writeit docs serve

# Serve on custom port
writeit docs serve --port 8080

# Serve with live reload
writeit docs serve --reload
```

**Options:**
- `--port`: Port to serve on (default: 8000)
- `--reload`: Enable live reload
- `--host`: Host to bind to (default: localhost)

---

## 🔧 Advanced Options

### Global Options

These options work with all commands:

```bash
# Verbose output
writeit --verbose run article.yaml

# Quiet mode (errors only)
writeit --quiet list-pipelines

# Custom workspace
writeit --workspace blog-project run article.yaml

# Debug mode
writeit --debug validate tech-article

# Version information
writeit --version

# Help
writeit --help
writeit run --help
```

### Configuration Files

WriteIt supports configuration files for customization:

**Global Configuration** (`~/.writeit/config.yaml`):
```yaml
default_workspace: "default"
llm:
  default_model: "gpt-4o-mini"
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
storage:
  max_cache_size: 1000
  cache_ttl: 86400
ui:
  default_tui: true
  color_theme: "dark"
```

**Workspace Configuration** (`~/.writeit/workspaces/{name}/config.yaml`):
```yaml
workspace:
  description: "My blog project"
  template_paths:
    - "./templates"
    - "../shared/templates"
  style_paths:
    - "./styles"
  inherit_global: true
```

### Environment Variables

```bash
# WriteIt configuration
export WRITEIT_HOME="/custom/writeit/path"
export WRITEIT_DEFAULT_WORKSPACE="my-project"
export WRITEIT_LOG_LEVEL="DEBUG"

# LLM Provider Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Storage configuration
export WRITEIT_CACHE_SIZE="2000"
export WRITEIT_STORAGE_PATH="/custom/storage"
```

### Error Handling

WriteIt provides clear error messages and recovery suggestions:

```bash
# Common errors and solutions
writeit run article.yaml
# Error: Workspace not found: 'my-project'
# Solution: Create workspace with 'writeit workspace create my-project'

writeit validate unknown-template
# Error: Template not found: 'unknown-template'
# Solution: Check template name with 'writeit template list'

writeit run article.yaml --tui
# Error: TUI dependencies not installed
# Solution: Install with 'pip install writeit[tui]'
```

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Command completed successfully |
| 1 | General Error | Command failed due to error |
| 2 | Invalid Usage | Invalid command or arguments |
| 3 | Workspace Error | Workspace not found or invalid |
| 4 | Template Error | Template not found or invalid |
| 5 | Validation Error | Template validation failed |
| 6 | Execution Error | Pipeline execution failed |
| 130 | Interrupted | Command interrupted by user (Ctrl+C) |

---

## 🎯 Usage Patterns

### Common Workflows

**New Project Setup:**
```bash
# 1. Initialize WriteIt (first time only)
writeit init

# 2. Create workspace for project
writeit workspace create my-blog --set-active

# 3. Add project templates
writeit template create blog-article --type pipeline --from-template tech-article

# 4. Run pipeline
writeit run blog-article.yaml --inputs topic="AI in Healthcare" style="blog"
```

**Template Development:**
```bash
# 1. Create and test template
writeit template create my-template --type pipeline
writeit validate --detailed my-template

# 2. Test execution
writeit run my-template --dry-run

# 3. Iterate with TUI
writeit run my-template --tui --inputs topic="Test topic"

# 4. Generate documentation
writeit docs generate --template my-template
```

**Workspace Management:**
```bash
# List all workspaces
writeit workspace list --verbose

# Switch context
writeit workspace use project-a

# Compare workspaces
writeit workspace info project-a
writeit workspace info project-b
```

This comprehensive CLI reference covers all WriteIt commands and their usage patterns. For additional help, use `writeit --help` or `writeit <command> --help` for specific command information.