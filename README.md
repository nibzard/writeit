# WriteIt

> LLM-powered article pipeline TUI application for guided writing workflows

WriteIt transforms raw content into polished articles through an interactive, 4-step AI-powered pipeline with human-in-the-loop feedback. Build better content faster with streaming AI responses, branching workflows, and complete pipeline history.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## ✨ Features

- **🎯 4-Step Pipeline**: angles → outline → draft → polish
- **🤖 Multi-Model AI**: OpenAI, Anthropic, and local models
- **⚡ Real-Time Streaming**: Watch content generate live
- **🔄 Human-in-the-Loop**: Guide AI at every step with feedback
- **🌲 Branching & Rewind**: Explore alternatives without losing work
- **📚 Complete History**: Every decision and response saved
- **🎨 Beautiful CLI**: Rich-formatted terminal interface with colors & tables
- **⌨️ Shell Completion**: Tab-complete commands, workspaces, and pipelines
- **🏠 Centralized Workspaces**: Organized project management with `~/.writeit`
- **🌐 Run from Anywhere**: Access all your content from any directory

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

### Create Your First Article
```bash
# Initialize WriteIt (creates ~/.writeit with beautiful progress display)
writeit init

# Create a workspace for your project
writeit workspace create my-blog

# Switch to your workspace  
writeit workspace use my-blog

# View available pipelines in a nice table
writeit list-pipelines

# Start writing! (runs from anywhere now)
writeit run tech-article
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

**Pipeline Operations** ⚡ *(work from any directory!)*
```bash
writeit list-pipelines           # Show available pipelines in a table
writeit run tech-article         # Execute pipeline in TUI mode (.yaml optional)
writeit run tech-article --cli   # Execute in CLI mode (simple prompts)
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

## 🖥️ Execution Modes

WriteIt supports two execution modes to fit different workflows:

### TUI Mode (Default) 
The full interactive experience with rich visual feedback:
- Real-time streaming responses
- Visual progress indicators  
- Step-by-step navigation
- Branching and rewind capabilities
- Full pipeline history

```bash
writeit run tech-article         # Interactive TUI mode
```

### CLI Mode
Streamlined command-line interface for automation and simplicity:
- Simple text prompts (y/n, numbered choices)
- Non-interactive execution
- Perfect for scripts and automation
- Lighter resource usage
- Same powerful pipeline logic

```bash
writeit run tech-article --cli   # Simple CLI prompts
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