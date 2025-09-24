# WriteIt

> LLM-powered writing pipeline application with real-time execution and workspace management

WriteIt transforms raw content into polished articles through multi-step AI-powered pipelines with human-in-the-loop feedback. Features a complete FastAPI backend with WebSocket streaming, intelligent LLM response caching, and event sourcing for reliable state management. Build better content faster with real-time AI responses, workspace isolation, and comprehensive execution tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=flat&logo=websocket)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

## ✨ Features

### 🏗️ **Complete Backend Architecture**
- **🚀 FastAPI Server**: REST API + WebSocket streaming for real-time execution
- **⚡ Async Pipeline Engine**: Multi-step workflows with LLM integration
- **💾 Event Sourcing**: Immutable state management with replay capabilities
- **🧠 Smart Caching**: Intelligent LLM response caching with workspace isolation
- **🔧 Client Libraries**: Python and JavaScript SDKs for easy integration

### 🎯 **Pipeline Execution**
- **📋 Multi-Step Workflows**: Define complex AI-powered content generation pipelines
- **🤖 Multi-Model Support**: OpenAI, Anthropic, and local models via llm.datasette.io
- **⚡ Real-Time Streaming**: Watch content generate live via WebSocket
- **🔄 Human-in-the-Loop**: Guide AI at every step with feedback and selections
- **📊 Progress Tracking**: Detailed execution monitoring and error handling

### 🏠 **Workspace Management**
- **🌐 Multi-Tenant**: Isolated workspaces with separate storage and caching
- **📚 Template System**: Global and workspace-specific pipeline templates
- **🎨 Style Primers**: Reusable style configurations for consistent output
- **📈 Analytics**: Token usage tracking and performance metrics

### 🎨 **Developer Experience**  
- **🖥️ Interactive TUI**: Rich terminal interface with real-time updates
- **⌨️ Shell Completion**: Tab-complete commands, workspaces, and pipelines
- **🧪 Comprehensive Tests**: Integration, unit, and contract test coverage
- **📖 API Documentation**: Complete OpenAPI documentation with examples

## 🚀 Quick Start

### Install uv (if not already installed)
```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install WriteIt
```bash
# Install globally
uv tool install writeit[openai,anthropic]

# Or install in a project
uv init my-articles && cd my-articles
uv add writeit[openai,anthropic]
```

### Configure AI Providers
```bash
# Set up your API keys
llm keys set openai    # Enter your OpenAI API key
llm keys set anthropic # Enter your Anthropic API key

# Verify providers are working
llm models list
```

### Create Your First Pipeline
```bash
# Initialize WriteIt (creates ~/.writeit directory structure)
writeit init

# Create a workspace for your project
writeit workspace create my-blog
writeit workspace use my-blog

# Start the WriteIt server (in background)
writeit server start

# Create and run your first pipeline
writeit run examples/article.yaml
```

### Using the API Directly

```python
import asyncio
from pathlib import Path
from writeit.server import PipelineClient

async def generate_article():
    client = PipelineClient()
    
    # Define your inputs
    inputs = {
        "topic": "The Future of AI",
        "style": "technical",
        "length": "medium"
    }
    
    # Run pipeline with real-time callbacks
    result = await client.run_pipeline(
        pipeline_path=Path("examples/article.yaml"),
        inputs=inputs,
        progress_callback=lambda event, data: print(f"Step: {data.get('step_name')}"),
        response_callback=lambda type, content: print(f"AI: {content[:100]}...")
    )
    
    print(f"✅ Article completed! Status: {result['status']}")
    return result

# Run the pipeline
asyncio.run(generate_article())
```

**✨ Pro Tip**: Enable shell completion for tab-completion of commands, workspaces, and pipelines:
```bash
# One-time setup for your shell
writeit completion --install

# Or add to your shell config manually
eval "$(writeit completion --show)"
```

## 🏗️ Workspace Management

WriteIt organizes all your content in a centralized `~/.writeit` directory, making it accessible from anywhere:

```bash
~/.writeit/
├── config.yaml          # Global settings & API keys
├── templates/           # Global pipeline templates  
├── styles/             # Shared style primers
├── workspaces/         # Your organized projects
│   ├── my-blog/        # Blog articles workspace
│   ├── technical/      # Technical documentation
│   └── personal/       # Personal writing
└── cache/              # LLM response cache
```

### Key Commands

**Workspace Management** 🏠
```bash
writeit workspace create my-project    # Create new workspace
writeit workspace list                # Show all workspaces in a table
writeit workspace use my-project      # Switch active workspace
writeit workspace info               # Show current workspace details
writeit workspace remove old-project # Delete workspace (with confirmation)
```

**Server Operations** 🚀
```bash
writeit server start            # Start FastAPI server (port 8000)
writeit server stop             # Stop running server  
writeit server status           # Check server health
```

**Pipeline Operations** ⚡ *(work from any directory!)*
```bash
writeit list-pipelines           # Show available pipelines in a table
writeit run tech-article         # Execute pipeline in TUI mode (.yaml optional)
writeit run --global quick-post  # Use global template
writeit run --workspace my-blog article-template  # Use specific workspace
```

**Template & Style Validation** ✅ *(with Rich syntax highlighting)*
```bash
writeit validate article-template               # Auto-detect type (.yaml optional)
writeit validate --type pipeline my-template    # Validate pipeline template
writeit validate --type style technical-expert  # Validate style primer
writeit validate --detailed template1 template2 # Show suggestions for multiple files
writeit validate --show-content my-template     # Display YAML with syntax highlighting
```

**Shell Completion** ⌨️
```bash
writeit completion --install        # Install completion for current shell
writeit completion --show --shell bash  # Show completion script
```

## 🏗️ Pipeline Architecture

WriteIt uses a YAML-based pipeline definition system with real-time execution:

### Sample Pipeline: `article.yaml`

```yaml
metadata:
  name: "Technical Article Generator"
  description: "Creates comprehensive technical articles"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"
  style: "technical"

inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
    placeholder: "Enter the main topic..."
    help: "The core subject your article will cover"
  
  audience:
    type: choice
    label: "Target Audience" 
    required: true
    options:
      - {label: "Beginners", value: "beginner"}
      - {label: "Intermediate", value: "intermediate"}
      - {label: "Advanced", value: "advanced"}
    default: "intermediate"
  
  length:
    type: choice
    label: "Article Length"
    options:
      - {label: "Short (500-800 words)", value: "short"}
      - {label: "Medium (800-1500 words)", value: "medium"}
      - {label: "Long (1500+ words)", value: "long"}
    default: "medium"

steps:
  outline:
    name: "Create Outline"
    description: "Generate a structured article outline"
    type: llm_generate
    prompt_template: |
      Create a detailed outline for a {{ inputs.audience }}-level article about {{ inputs.topic }}.
      
      Target length: {{ inputs.length }}
      Writing style: {{ defaults.style }}
      
      Include:
      1. Compelling introduction hook
      2. 3-5 main sections with subsections
      3. Practical examples and code snippets
      4. Conclusion with key takeaways
      
      Format as a nested list with brief descriptions for each section.
    model_preference: ["{{ defaults.model }}"]
    
  content:
    name: "Write Article"
    description: "Generate the complete article content"
    type: llm_generate
    prompt_template: |
      Based on this outline:
      {{ steps.outline }}
      
      Write a complete {{ inputs.length }} {{ defaults.style }} article about {{ inputs.topic }} 
      for {{ inputs.audience }} developers.
      
      Requirements:
      - Use clear, engaging language appropriate for {{ inputs.audience }} level
      - Include practical code examples where relevant
      - Add section headers and proper formatting
      - Ensure smooth transitions between sections
      - End with actionable takeaways
      
      Write the full article now:
    model_preference: ["{{ defaults.model }}"]
    depends_on: ["outline"]
    
  review:
    name: "Review & Polish"
    description: "Review and improve the article"
    type: llm_generate
    prompt_template: |
      Review this article and suggest specific improvements:
      
      {{ steps.content }}
      
      Focus on:
      1. Clarity and readability for {{ inputs.audience }} audience
      2. Technical accuracy
      3. Flow and structure
      4. Missing important points
      5. Code example quality
      
      Provide specific, actionable feedback.
    model_preference: ["{{ defaults.model }}"]
    depends_on: ["content"]
```

### Real-Time Execution Flow

1. **Input Collection**: Dynamic form based on pipeline inputs
2. **Step Execution**: Sequential LLM calls with dependency resolution
3. **Progress Streaming**: WebSocket updates for real-time feedback
4. **Response Caching**: Intelligent caching to avoid duplicate LLM calls
5. **State Management**: Event sourcing for reliable execution tracking

## 🚀 FastAPI Server & WebSocket

### Starting the Server

```bash
# Start development server with auto-reload
uv run uvicorn writeit.server.app:app --reload --port 8000

# Production deployment
uv run uvicorn writeit.server.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### REST API Usage

```bash
# Check server health
curl http://localhost:8000/health

# Create a pipeline
curl -X POST http://localhost:8000/api/pipelines \
  -H "Content-Type: application/json" \
  -d '{"pipeline_path": "article.yaml", "workspace_name": "default"}'

# Create and execute a run
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "pipeline_123",
    "inputs": {"topic": "FastAPI", "audience": "intermediate"},
    "workspace_name": "default"
  }'
```

### WebSocket Streaming

```javascript
// Connect to real-time execution updates
const ws = new WebSocket('ws://localhost:8000/ws/run_456');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'progress':
      console.log(`Step: ${message.data.step_name}`);
      break;
    case 'response':
      console.log(`AI Response: ${message.content}`);
      break;
    case 'completed':
      console.log('Pipeline completed!');
      break;
  }
};
```

## 🧠 Intelligent Caching

WriteIt includes sophisticated LLM response caching:

### Cache Features
- **Context-Aware**: Cache keys include prompt, model, and execution context
- **Workspace Isolation**: Separate cache namespaces per workspace
- **Smart TTL**: Configurable cache expiration (24h default)
- **Two-Tier Storage**: Memory + persistent LMDB caching
- **Analytics**: Hit/miss tracking and performance metrics

### Cache Management

```python
from writeit.llm.cache import LLMCache
from writeit.storage import StorageManager  # Now aliases LMDBStorageManager

# Create cache instance
cache = LLMCache(storage_manager, workspace_name="my-blog")

# Get cache statistics
stats = await cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Total requests: {stats['total_requests']}")

# Manual cache management
await cache.clear()  # Clear all cached responses
await cache.cleanup_expired()  # Remove expired entries
```

## 🔧 Development & Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/integration/ -v    # Integration tests
uv run pytest tests/unit/ -v           # Unit tests

# Run with coverage
uv run pytest tests/ --cov=src/writeit --cov-report=html
```

### API Documentation

When the server is running, interactive documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Development Commands
#!/bin/bash
# Generate multiple articles from a list
articles=(
  "Python Best Practices"
  "Docker Fundamentals"
  "API Design Patterns"
)

for topic in "${articles[@]}"; do
  echo -e "${topic}\n2\ny" | writeit run tech-article --cli --workspace dev-blog
done
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Generate Documentation
  run: |
    echo -e "API Documentation\n1\ny" | \
      writeit run api-docs --cli --workspace production
```

### Environment Variables
```bash
export WRITEIT_WORKSPACE=my-blog
export WRITEIT_HOME=/custom/path
writeit run article-template --cli
```

## 🎯 How It Works

WriteIt guides you through a structured 4-step process:

### 1. **Angles** 
Generate multiple article approaches from your source material
```
Input: Raw content + target audience
Output: 3-5 different article angles to choose from
```

### 2. **Outline**
Create a detailed structure for your chosen angle
```
Input: Selected angle + your feedback
Output: Complete article outline with sections and key points
```

### 3. **Draft**
Write the full article based on your outline
```
Input: Approved outline + style preferences
Output: Complete first draft with multiple model options
```

### 4. **Polish**
Refine and perfect the final article
```
Input: Selected draft + final feedback
Output: Publication-ready article with improved flow and clarity
```

## 📖 Documentation

- **[Installation Guide](docs/user/installation.md)** - Complete setup instructions
- **[Quick Start Tutorial](docs/user/quickstart.md)** - Your first article in 10 minutes
- **[CLI Mode Guide](docs/user/cli-mode.md)** - Automation & scripting with CLI mode
- **[CLI Examples](docs/user/cli-examples.md)** - Screenshots & command examples
- **[Developer Guide](docs/developer/getting-started.md)** - Contributing and development
- **[API Documentation](docs/api/rest-api.md)** - REST and WebSocket APIs

## 💻 Development

WriteIt is built with modern Python practices:

```bash
# Clone and setup
git clone https://github.com/nibzard/writeit.git
cd writeit

# Install dependencies (uv handles virtual environments automatically)
uv sync

# Run tests
uv run pytest tests/

# Start development TUI
uv run writeit run pipelines/tech-article.yaml
```

### Tech Stack
- **Python 3.11+** with async/await
- **FastAPI** for REST/WebSocket APIs  
- **Textual** for the terminal UI
- **Typer + Rich** for beautiful CLI with completion
- **LMDB** for efficient storage
- **llm.datasette.io** for multi-provider AI

## 🔧 Configuration

WriteIt uses a hierarchical configuration system that loads settings in this order:

1. **Global config** (`~/.writeit/config.yaml`)
2. **Workspace config** (`~/.writeit/workspaces/{name}/workspace.yaml`)
3. **Local config** (`.writeit/config.yaml` in current directory)
4. **Environment variables** (`WRITEIT_*`)

### Environment Variables
```bash
export WRITEIT_HOME=/custom/path        # Override default ~/.writeit
export WRITEIT_WORKSPACE=my-project    # Override active workspace
export WRITEIT_LLM_PROVIDER=openai     # Default LLM provider
```

### Deployment Patterns
WriteIt supports multiple deployment patterns:

- **Desktop**: Single-user TUI application with centralized storage
- **Server**: Multi-user web interface  
- **Container**: Docker/Kubernetes deployments
- **Enterprise**: SSO integration and monitoring

See [Deployment Guide](docs/deployment/deployment.md) for details.

## 🛠️ Development

For development and testing, use `uv run` to execute commands:

### Development Setup
```bash
# Clone the repository
git clone https://github.com/your-org/writeit.git
cd writeit

# Install dependencies and setup environment
uv sync

# Install in development mode
uv run pip install -e .
```

### Development Commands
```bash
# Run WriteIt commands in development
uv run writeit init                              # Initialize for testing
uv run writeit workspace create test-workspace  # Create test workspace
uv run writeit validate tech-article            # Validate templates (no .yaml needed)
uv run writeit run quick-article               # Test pipelines

# Validation examples for template authors
uv run writeit validate --type pipeline --detailed my-template
uv run writeit validate --type style --detailed my-style
uv run writeit validate --global quick-article --summary-only
uv run writeit validate --local ./local-template

# Run tests
uv run pytest tests/                    # All tests
uv run pytest tests/unit/             # Unit tests only  
uv run pytest tests/integration/      # Integration tests only
uv run ruff check src/ tests/         # Linting
uv run mypy src/                       # Type checking
```

### Testing Template Validation
```bash
# Test your pipeline templates
uv run writeit validate my-pipeline --detailed

# Test your style primers  
uv run writeit validate my-style --type style --detailed

# Validate multiple files at once (extensions optional)
uv run writeit validate tech-article quick-article technical-expert --summary-only
```

## 🤝 Contributing

We welcome contributions! WriteIt follows **Test-Driven Development** with a **library-first architecture**.

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write tests** first (TDD approach)
4. **Implement** your feature
5. **Test** everything (`uv run pytest tests/`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

See [Contributing Guide](docs/developer/getting-started.md) for detailed development setup.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Astral](https://astral.sh/) for the amazing uv package manager
- [Textual](https://textual.textualize.io/) for the beautiful TUI framework
- [Simon Willison](https://simonwillison.net/) for the excellent llm tool
- The open source community for continuous inspiration

---

**Ready to transform your writing process?** [Get started now](docs/user/quickstart.md) ✍️