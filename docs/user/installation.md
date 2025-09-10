# Installation Guide

Get WriteIt up and running on your system in under 5 minutes. WriteIt works on macOS, Linux, and Windows with Python 3.11+.

## 🚀 Quick Install

### Option 1: uv (Recommended)
```bash
# Install uv first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install WriteIt globally with all providers
uv tool install writeit[openai,anthropic,local]

# Verify installation
writeit --version
# Expected: WriteIt 0.1.0

# Initialize WriteIt (creates centralized ~/.writeit)
writeit init
```

### Option 2: Project-local Installation
```bash
# Create new project with WriteIt
uv init writeIt-workspace
cd writeIt-workspace
uv add writeit[openai,anthropic]

# Run WriteIt
uv run writeit --version
```

### Option 3: From Source
```bash
# Clone repository
git clone https://github.com/writeIt/writeIt.git
cd writeIt

# Install dependencies and sync environment
uv sync

# Verify installation
uv run writeit --version
```

## 🔧 System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **Memory**: 512MB RAM available
- **Storage**: 200MB disk space
- **Terminal**: Any terminal with 256 color support

### Recommended Requirements  
- **Python**: 3.12+ (better performance)
- **Memory**: 1GB+ RAM (for multiple concurrent pipelines)
- **Storage**: 2GB+ disk space (for artifact history)
- **Terminal**: Modern terminal with true color support

### Platform Support
| Platform | Status | Notes |
|----------|--------|--------|
| **macOS** | ✅ Full Support | Tested on macOS 12+ |
| **Linux** | ✅ Full Support | Ubuntu 20.04+, CentOS 8+ |
| **Windows** | ✅ Full Support | Windows 10+, WSL2 recommended |

## 🌐 AI Provider Setup

WriteIt supports multiple AI providers. Configure at least one for full functionality:

### OpenAI Setup
```bash
# Install OpenAI provider (if not already included)
uv add writeit[openai]  # or uv tool install writeit[openai] for global

# Set API key
llm keys set openai
# Prompt: Enter API key: sk-...

# Verify connection
llm models list | grep gpt
# Expected: gpt-4o, gpt-4o-mini, etc.
```

### Anthropic (Claude) Setup
```bash
# Install Anthropic provider (if not already included)
uv add writeit[anthropic]  # or uv tool install writeit[anthropic] for global

# Set API key  
llm keys set anthropic
# Prompt: Enter API key: sk-ant-...

# Verify connection
llm models list | grep claude
# Expected: claude-3-5-sonnet-20241022, etc.
```

### Local Models (Optional)
```bash
# Install Ollama for local models
curl -fsSL https://ollama.ai/install.sh | sh

# Install local models
ollama pull llama3.2:3b
ollama pull qwen2.5:3b

# Verify in WriteIt
llm models list | grep ollama
# Expected: ollama:llama3.2:3b, etc.
```

## 🏠 Workspace Setup

### Initialize WriteIt
```bash
# Initialize centralized WriteIt storage
writeit init

# Optional: Auto-migrate existing local workspaces
writeit init --migrate

# Centralized structure created at ~/.writeit:
# ~/.writeit/
# ├── config.yaml         # Global configuration
# ├── templates/          # Global pipeline templates
# ├── styles/             # Global style primers
# ├── workspaces/         # Your organized projects
# │   └── default/        # Default workspace
# └── cache/              # LLM response cache
```

### Create and Manage Workspaces
```bash
# Create workspace for your project
writeit workspace create my-blog

# Switch to your workspace  
writeit workspace use my-blog

# List all workspaces
writeit workspace list
# Output:
#   default
# * my-blog

# Show workspace info
writeit workspace info
# Output:
# Workspace: my-blog
# Path: ~/.writeit/workspaces/my-blog
# Created: 2025-01-15T10:30:00Z
```

### Workspace Structure
```
~/.writeit/                         # Centralized WriteIt home
├── config.yaml                    # Global settings & active workspace
├── templates/                      # Global pipeline templates
│   ├── tech-article.yaml         # Technical article pipeline
│   ├── blog-post.yaml            # Blog post pipeline
│   └── research-summary.yaml     # Research summary pipeline
├── styles/                         # Global style primers
│   ├── tech-journalist.yaml      # Technical writing style
│   ├── conversational.yaml       # Casual blog style
│   └── academic.yaml             # Academic paper style
├── workspaces/                     # Your organized projects
│   ├── default/                   # Default workspace
│   │   ├── pipelines/            # Workspace-specific pipelines
│   │   ├── articles/             # Generated articles
│   │   ├── workspace.yaml        # Workspace configuration
│   │   └── *.lmdb               # Pipeline artifacts & history
│   └── my-blog/                   # Your blog workspace
│       ├── pipelines/            # Blog-specific pipelines
│       ├── articles/             # Blog articles
│       ├── workspace.yaml        # Blog workspace config
│       └── *.lmdb               # Blog pipeline history
└── cache/                          # Shared LLM response cache
```

## ⚙️ Configuration

### Global Configuration
```bash
# Set default preferences
writeit config set --default-style tech-journalist
writeit config set --max-concurrent 3
writeit config set --auto-save true

# View current configuration
writeit config show
```

### Environment Variables
```bash
# Optional: Set in ~/.bashrc or ~/.zshrc
export WRITEIT_HOME=~/.writeit           # Override default home directory
export WRITEIT_WORKSPACE=my-project      # Override active workspace
export WRITEIT_DEFAULT_MODEL=gpt-4o      # Default LLM model
export WRITEIT_LOG_LEVEL=INFO            # Logging level
```

### Provider Configuration
```yaml
# ~/.writeit/providers.yaml (auto-created)
providers:
  openai:
    models:
      gpt-4o: {cost_per_1k_input: 0.005, cost_per_1k_output: 0.015}
      gpt-4o-mini: {cost_per_1k_input: 0.00015, cost_per_1k_output: 0.0006}
  anthropic:
    models:
      claude-3-5-sonnet: {cost_per_1k_input: 0.003, cost_per_1k_output: 0.015}
  local:
    models:
      llama3.2: {cost_per_1k_input: 0.0, cost_per_1k_output: 0.0}
```

## 🧪 Verify Installation

### Basic Functionality Test
```bash
# Test 1: Version and help
writeit --version
writeit --help

# Test 2: Create and list workspaces
writeit workspace create test-workspace
writeit workspace list

# Test 3: List available pipelines (works from any directory!)
writeit list-pipelines
# Expected: tech-article.yaml, blog-post.yaml, research-summary.yaml

# Test 4: Test AI provider connection
llm models list
# Expected: List of available models from configured providers

# Test 5: Start test pipeline (will prompt for input)
writeit run tech-article.yaml
# Press Ctrl+Q to quit after TUI loads
```

### Comprehensive Test
```bash
# Run built-in verification
writeit verify

# Expected output:
✅ Python 3.11+ detected
✅ Dependencies installed correctly  
✅ Workspace initialized
✅ AI providers configured: openai, anthropic
✅ Terminal supports required features
✅ LMDB storage working
✅ Example pipelines loaded
✅ All systems ready
```

## 🔧 Troubleshooting

### Common Issues

#### "writeit: command not found"
```bash
# Solution 1: Ensure uv tools are in PATH
echo $PATH
# uv automatically adds ~/.local/bin to PATH

# Solution 2: Use uv run (for project-local installs)
uv run writeit --version

# Solution 3: Reinstall globally with uv tool
uv tool install writeit
```

#### "No module named 'lmdb'"
```bash
# Install system dependencies (Linux)
sudo apt-get install python3-dev liblmdb-dev

# Install system dependencies (macOS)
brew install lmdb

# Reinstall WriteIt
uv tool install --force writeit
# or for project-local: uv sync --reinstall
```

#### "Permission denied: ~/.writeit/"
```bash
# Fix permissions
chmod 755 ~/.writeit
chmod 644 ~/.writeit/*

# Or recreate workspace
rm -rf ~/.writeit
writeit init ~/articles
```

#### "AI provider authentication failed"
```bash
# Check API key format
llm keys list

# Test key manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Reset and re-enter key
llm keys set openai
```

#### "Terminal doesn't support colors"
```bash
# Check terminal capabilities
echo $TERM
tput colors

# Set better terminal
export TERM=xterm-256color

# Or use basic mode
writeit --no-color run pipelines/tech-article.yaml
```

### System-Specific Issues

#### macOS Issues
```bash
# Install Xcode command line tools
xcode-select --install

# uv can manage Python versions automatically
uv python install 3.12
uv tool install writeit
```

#### Linux Issues
```bash
# Ubuntu/Debian: Install build essentials
sudo apt-get update
sudo apt-get install build-essential python3-dev

# CentOS/RHEL: Install development tools  
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# uv handles virtual environments automatically
```

#### Windows Issues
```bash
# Use Windows Subsystem for Linux (WSL2) - Recommended
wsl --install Ubuntu

# Or install Visual Studio Build Tools for native Windows
# Download from: https://visualstudio.microsoft.com/build-tools/

# Use Windows Terminal for best experience
# Download from Microsoft Store
```

### Performance Issues

#### Slow startup
```bash
# Check disk space
df -h ~/.writeit

# Clear old artifacts (keeps last 100 runs)
writeit cleanup --keep 100

# Disable startup verification
writeit config set --skip-verify true
```

#### High memory usage
```bash
# Reduce concurrent pipelines
writeit config set --max-concurrent 1

# Enable memory optimization
writeit config set --memory-optimize true

# Monitor usage
writeit status --memory
```

## 🔄 Upgrading

### Upgrade WriteIt
```bash
# Upgrade to latest version
uv tool upgrade writeit  # for global installs
# or: uv add writeit@latest  # for project installs

# Verify upgrade
writeit --version

# Migrate workspace if needed
writeit migrate-workspace ~/articles
```

### Backup Before Upgrade
```bash
# Backup workspace
cp -r ~/articles ~/articles-backup-$(date +%Y%m%d)

# Export important pipelines
writeit export-all ~/articles/backup/
```

## 🆘 Getting Help

### Built-in Help
```bash
writeit --help                    # General help
writeit run --help               # Pipeline execution help
writeit config --help            # Configuration help
```

### Diagnostic Information
```bash
# Generate diagnostic report
writeit diagnostic > writeit-diagnostic.txt

# Include in bug reports:
# - WriteIt version
# - Python version  
# - Operating system
# - Error messages
# - Diagnostic report
```

### Community Support
- **Documentation**: [docs.writeIt.ai](https://docs.writeIt.ai)
- **GitHub Issues**: [github.com/writeIt/writeIt/issues](https://github.com/writeIt/writeIt/issues)
- **Discord**: [discord.gg/writeIt](https://discord.gg/writeIt)
- **Email**: support@writeIt.ai

---

**Ready to write?** Once installation is complete, check out the [Quick Start Tutorial](quickstart.md) to create your first article! ✍️