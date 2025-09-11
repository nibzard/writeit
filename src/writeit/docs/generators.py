"""
User guide generator for documentation
"""

from pathlib import Path
from typing import List, Dict, Any

from .models import UserGuide, CodeExample


class UserGuideGenerator:
    """Generate user guides for documentation"""
    
    def generate_guides(self) -> List[UserGuide]:
        """Generate all user guides"""
        guides = []
        
        # Getting Started Guide
        getting_started = self._generate_getting_started_guide()
        guides.append(getting_started)
        
        # Configuration Guide
        configuration = self._generate_configuration_guide()
        guides.append(configuration)
        
        # Pipeline Development Guide
        pipeline_dev = self._generate_pipeline_development_guide()
        guides.append(pipeline_dev)
        
        # CLI Reference Guide
        cli_reference = self._generate_cli_reference_guide()
        guides.append(cli_reference)
        
        # API Usage Guide
        api_usage = self._generate_api_usage_guide()
        guides.append(api_usage)
        
        # Troubleshooting Guide
        troubleshooting = self._generate_troubleshooting_guide()
        guides.append(troubleshooting)
        
        return guides
    
    def _generate_getting_started_guide(self) -> UserGuide:
        """Generate getting started guide"""
        content = """# Getting Started with WriteIt

WriteIt is an LLM-powered writing pipeline tool that helps you create structured content through multi-step AI workflows. This guide will help you get up and running quickly.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.12+** installed
- **uv** package manager (recommended) or pip
- **API keys** for LLM providers (OpenAI, Anthropic, etc.)

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install WriteIt globally
uv tool install writeit[openai,anthropic]
```

### Option 2: Using pip

```bash
# Install WriteIt with pip
pip install writeit[openai,anthropic]
```

## Initial Setup

### 1. Configure LLM Providers

Set up your API keys for the LLM providers you want to use:

```bash
# Set OpenAI API key
llm keys set openai

# Set Anthropic API key  
llm keys set anthropic
```

### 2. Initialize WriteIt

Create the WriteIt directory structure:

```bash
# Initialize WriteIt
writeit init
```

This creates a `~/.writeit` directory with the following structure:

```
~/.writeit/
├── config.yaml          # Global configuration
├── templates/           # Pipeline templates
├── styles/             # Style primers
├── workspaces/         # Your workspaces
└── cache/              # LLM response cache
```

### 3. Create Your First Workspace

Workspaces help you organize your writing projects:

```bash
# Create a workspace for your blog
writeit workspace create my-blog

# Switch to your new workspace
writeit workspace use my-blog
```

## Your First Pipeline

Let's create a simple article pipeline:

### 1. Create a Pipeline File

Create a file named `article.yaml`:

```yaml
metadata:
  name: "Simple Article Generator"
  description: "Generate a basic article outline and content"
  version: "1.0.0"

inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
    placeholder: "Enter your article topic..."

steps:
  outline:
    name: "Create Outline"
    description: "Generate article outline"
    type: llm_generate
    prompt_template: |
      Create a detailed outline for an article about {{ inputs.topic }}.
      
      Include:
      1. Introduction
      2. 3-5 main sections
      3. Conclusion
      
      Format as a structured outline.
    model_preference: ["gpt-4o-mini"]
    
  content:
    name: "Write Article"
    description: "Generate full article content"
    type: llm_generate
    prompt_template: |
      Based on this outline:
      {{ steps.outline }}
      
      Write a complete article about {{ inputs.topic }}.
    model_preference: ["gpt-4o-mini"]
    depends_on: ["outline"]
```

### 2. Run Your Pipeline

Execute your pipeline:

```bash
# Run the pipeline
writeit run article.yaml
```

WriteIt will guide you through the pipeline step by step:

1. **Input Collection**: Enter your article topic
2. **Outline Generation**: Review and select from generated outlines
3. **Content Generation**: Generate the full article
4. **Review**: Finalize your article

### 3. Review Results

After the pipeline completes, you'll have:

- A structured article outline
- Complete article content
- Execution history and token usage

## Next Steps

Now that you've created your first pipeline, you can:

- **Explore Templates**: Try pre-built templates with `writeit list-pipelines`
- **Customize Styles**: Create custom writing styles with `writeit validate --type style`
- **Use the API**: Integrate WriteIt into your applications
- **Share Work**: Export and share your pipelines with others

## Common Commands

```bash
# List available workspaces
writeit workspace list

# Switch workspaces
writeit workspace use my-blog

# List available pipelines
writeit list-pipelines

# Validate a pipeline
writeit validate my-pipeline

# Get help
writeit --help
writeit run --help
```

## Tips for Success

1. **Start Small**: Begin with simple pipelines and gradually add complexity
2. **Use Templates**: Leverage existing templates as starting points
3. **Iterate**: Review and refine your pipelines based on results
4. **Monitor Usage**: Keep an eye on token usage and costs
5. **Experiment**: Try different models and prompts for better results

## Getting Help

If you run into issues:

- Use `writeit --help` for command help
- Check the troubleshooting guide
- Review existing templates for examples
- Monitor token usage with cache statistics
"""
        
        return UserGuide(
            title="Getting Started with WriteIt",
            description="A comprehensive guide to installing, setting up, and running your first WriteIt pipeline",
            content=content,
            audience="new_users",
            difficulty="beginner",
            estimated_time="15 minutes",
            prerequisites=["Python 3.12+", "uv package manager", "LLM API keys"],
            related_guides=["Configuration Guide", "Pipeline Development Guide"]
        )
    
    def _generate_configuration_guide(self) -> UserGuide:
        """Generate configuration guide"""
        return UserGuide(
            title="Configuration Guide",
            description="Learn how to configure WriteIt for your specific needs",
            content="# Configuration Guide\n\n*Detailed configuration content...*",
            audience="users",
            difficulty="intermediate",
            estimated_time="20 minutes",
            prerequisites=["Basic WriteIt setup"],
            related_guides=["Getting Started", "Pipeline Development"]
        )
    
    def _generate_pipeline_development_guide(self) -> UserGuide:
        """Generate pipeline development guide"""
        return UserGuide(
            title="Pipeline Development Guide",
            description="Learn to create and customize WriteIt pipelines",
            content="# Pipeline Development\n\n*Pipeline development content...*",
            audience="developers",
            difficulty="intermediate",
            estimated_time="30 minutes",
            prerequisites=["Basic WriteIt usage", "YAML knowledge"],
            related_guides=["Getting Started", "Configuration Guide"]
        )
    
    def _generate_cli_reference_guide(self) -> UserGuide:
        """Generate CLI reference guide"""
        return UserGuide(
            title="CLI Reference Guide",
            description="Complete reference for WriteIt CLI commands",
            content="# CLI Reference\n\n*CLI reference content...*",
            audience="users",
            difficulty="beginner",
            estimated_time="10 minutes",
            prerequisites=["WriteIt installation"],
            related_guides=["Getting Started"]
        )
    
    def _generate_api_usage_guide(self) -> UserGuide:
        """Generate API usage guide"""
        return UserGuide(
            title="API Usage Guide",
            description="Learn to use WriteIt's REST API and WebSocket interface",
            content="# API Usage\n\n*API usage content...*",
            audience="developers",
            difficulty="advanced",
            estimated_time="25 minutes",
            prerequisites=["Basic WriteIt setup", "HTTP API knowledge"],
            related_guides=["Pipeline Development", "Configuration Guide"]
        )
    
    def _generate_troubleshooting_guide(self) -> UserGuide:
        """Generate troubleshooting guide"""
        return UserGuide(
            title="Troubleshooting Guide",
            description="Solve common issues and problems with WriteIt",
            content="# Troubleshooting\n\n*Troubleshooting content...*",
            audience="all",
            difficulty="intermediate",
            estimated_time="15 minutes",
            prerequisites=["Basic WriteIt usage"],
            related_guides=["Getting Started", "Configuration Guide"]
        )