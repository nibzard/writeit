# CLI Examples & Screenshots

This page showcases WriteIt's beautiful Rich-formatted CLI interface with real examples and expected outputs.

## 🎨 Rich-Formatted Help System

### Main Help Screen
```bash
$ writeit --help
```

**Output:**
```
 Usage: writeit [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 WriteIt - LLM-powered writing pipeline tool with terminal UI                   
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --version    -v            Show version and exit                             │
│ --workspace  -w      TEXT  Use specific workspace (overrides active          │
│                            workspace)                                        │
│ --verbose                  Enable verbose output                             │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ completion       Manage shell completion for WriteIt CLI.                    │
│ list-pipelines   List available pipeline templates.                          │
│ run              Run pipeline execution (TUI or CLI mode).                   │
│ init             Initialize WriteIt home directory                           │
│ workspace        Manage WriteIt workspaces                                   │
│ pipeline         Pipeline operations                                         │
│ validate         Validate pipeline templates and style primers               │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Command-Specific Help
```bash
$ writeit workspace --help
```

**Output:**
```
 Usage: writeit workspace [OPTIONS] COMMAND [ARGS]...                           
                                                                                
 Manage WriteIt workspaces                                                      
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ create   Create a new workspace.                                             │
│ list     List all available workspaces.                                      │
│ use      Switch to a different workspace.                                    │
│ remove   Remove a workspace.                                                 │
│ info     Show detailed information about a workspace.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## 🚀 Initialization with Progress Display

### Basic Initialization
```bash
$ writeit init
```

**Output:**
```
Initializing WriteIt home directory: /Users/niko/.writeit

⠋ Initializing WriteIt...

✓ Created ~/.writeit directory structure
✓ Created default workspace
✓ Created global configuration

WriteIt initialized successfully!
Use 'writeit workspace list' to see available workspaces.
```

### Initialization with Migration
```bash
$ writeit init --migrate
```

**Output:**
```
Initializing WriteIt home directory: /Users/niko/.writeit

⠋ Initializing WriteIt...

✓ Created ~/.writeit directory structure
✓ Created default workspace
✓ Created global configuration

Searching for local workspaces to migrate...

⠋ Scanning for workspaces...

✓ Migrated 2 workspaces
  ✓ /Users/niko/projects/blog
  ✓ /Users/niko/work/docs

WriteIt initialized successfully!
Use 'writeit workspace list' to see available workspaces.
```

## 🏠 Workspace Management with Rich Tables

### Listing Workspaces
```bash
$ writeit workspace list
```

**Output:**
```
        Available Workspaces        
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name          ┃ Status            ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ default       │ ✓ Active          │
│ my-blog       │                   │
│ technical     │                   │
│ personal      │                   │
└───────────────┴───────────────────┘

Active workspace: default
Total workspaces: 4
```

### Creating a Workspace
```bash
$ writeit workspace create my-project
```

**Output:**
```
✓ Created workspace 'my-project'
```

### Creating with Auto-Activation
```bash
$ writeit workspace create my-project --set-active
```

**Output:**
```
✓ Created workspace 'my-project'
✓ Set 'my-project' as active workspace
```

### Workspace Information
```bash
$ writeit workspace info my-blog
```

**Output:**
```
      Workspace: my-blog       
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value                                                                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Created             │ 2025-01-15 10:30:45                                                     │
│ Default Pipeline    │ tech-article                                                             │
│ Stored Entries      │ 15                                                                       │
└─────────────────────┴──────────────────────────────────────────────────────────────────────┘

Path: /Users/niko/.writeit/workspaces/my-blog
```

### Workspace Info with Directory Tree
```bash
$ writeit workspace info my-blog --tree
```

**Output:**
```
      Workspace: my-blog       
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value                                                                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Created             │ 2025-01-15 10:30:45                                                     │
│ Default Pipeline    │ tech-article                                                             │
│ Stored Entries      │ 15                                                                       │
└─────────────────────┴──────────────────────────────────────────────────────────────────────┘

Path: /Users/niko/.writeit/workspaces/my-blog

Workspace: my-blog
├── 📁 articles
│   ├── 📄 webassembly-performance.yaml
│   ├── 📄 rust-async-patterns.yaml
│   └── 📄 python-performance-tips.yaml
├── 📁 pipelines
│   └── 📄 blog-post.yaml
├── 📁 styles
│   └── 📄 casual-technical.yaml
├── 📁 cache
└── 📄 workspace.yaml
```

## ⚡ Pipeline Operations

### Listing Pipelines
```bash
$ writeit list-pipelines
```

**Output:**
```
    Available Pipeline Templates    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                         ┃ Type                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ quick-article                │ Global                       │
│ tech-article                 │ Global                       │
│ research-summary             │ Global                       │
│ blog-post                    │ Workspace (my-blog)         │
│ tutorial-guide               │ Workspace (my-blog)         │
└──────────────────────────────┴──────────────────────────────┘

Use 'writeit run <pipeline-name>' to execute a pipeline.
```

### Running a Pipeline (TUI Mode - Default)
```bash
$ writeit run tech-article
```

**Output:**
```
Pipeline: tech-article
Path: /Users/niko/.writeit/templates/tech-article.yaml
Scope: Global
Workspace: my-blog

Launching pipeline TUI...
```

### Running a Pipeline (CLI Mode)
```bash
$ writeit run tech-article --cli
```

**Output:**
```
Pipeline: tech-article
Path: /Users/niko/.writeit/templates/tech-article.yaml
Scope: Global
Workspace: my-blog

Starting CLI pipeline execution...

Pipeline Input Collection
Pipeline: Technical Article Pipeline
Description: 4-step pipeline for technical articles

Enter your topic for the technical article
Article Topic: Python Performance Optimization

What's your target audience?
Target Audience:
  1. beginners - New to programming
  2. intermediate - Some programming experience  
  3. advanced - Experienced developers
Select option (number): 2

What type of technical article?
Article Type:
  1. tutorial - Step-by-step guide
  2. reference - Documentation/API reference
  3. comparison - Tool/library comparison
  4. analysis - Deep-dive analysis
Select option (number): 1

Executing Pipeline: Technical Article Pipeline

Step 1/4: Generate Angles
Generate different article approaches
Execute step: Generate Angles? [y/n] (y): y

⠋ Processing with LLM...

✅ Response:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Here are 5 compelling angles for your Python performance optimization      ┃
┃ tutorial:                                                                  ┃
┃                                                                            ┃
┃ 1. **The Bottleneck Hunter**: A systematic approach to finding and fixing  ┃
┃    performance issues using profiling tools                               ┃
┃                                                                            ┃
┃ 2. **Memory Matters**: Focus on memory-efficient Python patterns and      ┃
┃    data structures                                                         ┃
┃                                                                            ┃
┃ 3. **Speed vs Readability**: When and how to optimize without sacrificing ┃
┃    code maintainability                                                    ┃
┃                                                                            ┃
┃ 4. **Modern Python Performance**: Leveraging Python 3.12+ features for    ┃
┃    better performance                                                      ┃
┃                                                                            ┃
┃ 5. **Real-World Optimizations**: Case studies from production systems     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Accept this response? [y/n] (y): y

Step 2/4: Create Outline
Create detailed article outline
Execute step: Create Outline? [y/n] (y): y

⠋ Processing with LLM...

✅ Response:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # Python Performance Optimization: The Bottleneck Hunter's Guide           ┃
┃                                                                            ┃
┃ ## I. Introduction                                                         ┃
┃ - Why performance matters for intermediate developers                       ┃
┃ - Common performance pitfalls                                              ┃
┃                                                                            ┃
┃ ## II. The Profiling Toolkit                                               ┃
┃ - cProfile and profile modules                                             ┃
┃ - line_profiler for line-by-line analysis                                  ┃
┃ - memory_profiler for memory usage                                         ┃
┃                                                                            ┃
┃ ## III. Identifying Bottlenecks                                            ┃
┃ - Reading profiler output                                                  ┃
┃ - Finding the critical path                                                ┃
┃ - Measuring before optimizing                                              ┃
┃                                                                            ┃
┃ ## IV. Common Optimization Techniques                                       ┃
┃ - Data structure choices                                                   ┃
┃ - Algorithm improvements                                                   ┃
┃ - Built-in function usage                                                  ┃
┃                                                                            ┃
┃ ## V. Hands-on Example                                                     ┃
┃ - Before: Slow data processing script                                      ┃
┃ - Profiling: Finding the problems                                          ┃
┃ - After: Optimized implementation                                          ┃
┃                                                                            ┃
┃ ## VI. Conclusion                                                          ┃
┃ - Performance mindset for intermediate developers                          ┃
┃ - Next steps and advanced topics                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Accept this response? [y/n] (y): y

Step 3/4: Write Article
Generate full article content
Execute step: Write Article? [y/n] (y): y

⠋ Processing with LLM...

✅ Response:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # Python Performance Optimization: The Bottleneck Hunter's Guide           ┃
┃                                                                            ┃
┃ As an intermediate Python developer, you've mastered the basics and        ┃
┃ built working applications. Now it's time to make them faster. This        ┃
┃ tutorial teaches you systematic performance optimization through profiling  ┃
┃ and targeted improvements.                                                 ┃
┃                                                                            ┃
┃ ## Why Performance Matters for Intermediate Developers                     ┃
┃                                                                            ┃
┃ Performance isn't just about raw speed—it's about user experience,         ┃
┃ resource efficiency, and scalability. As your applications grow...         ┃
┃                                                                            ┃
┃ [Article content continues...]                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Accept this response? [y/n] (y): y

Step 4/4: Polish Content
Final editing and refinement
Execute step: Polish Content? [y/n] (y): y

⠋ Processing with LLM...

✅ Pipeline Completed!

Token Usage Summary:
  Total Input Tokens: 1,247
  Total Output Tokens: 2,891
  Total Steps: 4

Executed 4 steps:
  angles: ✅ Completed
  outline: ✅ Completed  
  write: ✅ Completed
  polish: ✅ Completed
```

### CLI Mode Help
```bash
$ writeit run --help
```

**Output:**
```
 Usage: writeit run [OPTIONS] PIPELINE

 Run pipeline execution (TUI or CLI mode).

 Searches for the pipeline in workspace-specific directories first,
 then falls back to global templates.

 Examples:

 Run a pipeline (TUI):
   $ writeit run article-template

 Run in CLI mode:
   $ writeit run article-template --cli

 Run global pipeline only:
   $ writeit run article-template --global

 Run in specific workspace:
   $ writeit run article-template --workspace myproject

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    pipeline      TEXT  Pipeline configuration file (with or without .yaml  │
│                          extension)                                          │
│                          [required]                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --global     -g            Use global pipeline template only                 │
│ --workspace  -w      TEXT  Use specific workspace (overrides active          │
│                            workspace and global option)                      │
│ --cli                      Run in CLI mode with simple prompts (no TUI)      │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## 🤖 Automation & Scripting with CLI Mode

### Batch Article Generation
```bash
#!/bin/bash
# generate-articles.sh - Batch generate multiple articles

articles=(
  "Python Best Practices"
  "Docker Fundamentals"
  "API Design Patterns"
  "Database Optimization"
  "Testing Strategies"
)

workspace="tech-blog"

for topic in "${articles[@]}"; do
  echo "Generating article: $topic"
  echo -e "${topic}\n2\n1\ny\ny\ny\ny" | \
    writeit run tech-article --cli --workspace "$workspace"
  echo "✅ Completed: $topic"
  echo
done

echo "🎉 Generated ${#articles[@]} articles in workspace: $workspace"
```

**Output:**
```
Generating article: Python Best Practices
Pipeline: tech-article
Path: /Users/niko/.writeit/templates/tech-article.yaml
Scope: Global
Workspace: tech-blog

Starting CLI pipeline execution...

Pipeline Input Collection
Pipeline: Technical Article Pipeline
Description: 4-step pipeline for technical articles

Article Topic: What's your target audience?
Target Audience:
  1. beginners - New to programming
  2. intermediate - Some programming experience  
  3. advanced - Experienced developers
Select option (number): What type of technical article?
Article Type:
  1. tutorial - Step-by-step guide
  2. reference - Documentation/API reference
Select option (number): 
Executing Pipeline: Technical Article Pipeline

Step 1/4: Generate Angles
Execute step: Generate Angles? [y/n] (y): Step 2/4: Create Outline
Execute step: Create Outline? [y/n] (y): Step 3/4: Write Article
Execute step: Write Article? [y/n] (y): Step 4/4: Polish Content
Execute step: Polish Content? [y/n] (y): 
✅ Pipeline Completed!

Token Usage Summary:
  Total Input Tokens: 987
  Total Output Tokens: 2,456
  Total Steps: 4

✅ Completed: Python Best Practices

[Process repeats for each article...]

🎉 Generated 5 articles in workspace: tech-blog
```

### CI/CD Integration Examples

#### GitHub Actions
```yaml
# .github/workflows/generate-docs.yml
name: Generate Documentation

on:
  push:
    paths: ['specs/**']

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
    - name: Install WriteIt
      run: uv tool install writeit[openai,anthropic]
      
    - name: Generate API Documentation
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        WRITEIT_WORKSPACE: api-docs
      run: |
        echo -e "REST API Documentation\n2\ny\ny\ny" | \
          writeit run api-docs --cli
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
        WRITEIT_WORKSPACE = 'production-docs'
    }
    
    stages {
        stage('Generate Release Notes') {
            steps {
                script {
                    sh '''
                        echo -e "Version 2.1.0 Release\n1\ny\ny\ny" | \\
                          writeit run release-notes --cli
                    '''
                }
            }
        }
    }
}
```

### Environment Variable Configuration
```bash
# Set persistent configuration
export WRITEIT_HOME=/opt/writeit
export WRITEIT_WORKSPACE=production
export OPENAI_API_KEY=sk-your-key-here

# Batch process with environment config
topics=(
  "Security Updates"
  "Performance Improvements"
  "New Features"
)

for topic in "${topics[@]}"; do
  echo -e "${topic}\n3\ny\ny\ny\ny" | writeit run changelog --cli
done
```

### Error Handling in Scripts
```bash
#!/bin/bash
# robust-generation.sh - Generate with error handling

generate_article() {
    local topic="$1"
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "Attempt $((retry_count + 1)) for: $topic"
        
        if echo -e "${topic}\n2\ny\ny\ny\ny" | \
           writeit run tech-article --cli --workspace dev-blog; then
            echo "✅ Success: $topic"
            return 0
        else
            echo "❌ Failed attempt $((retry_count + 1)) for: $topic"
            retry_count=$((retry_count + 1))
            sleep 5  # Wait before retry
        fi
    done
    
    echo "🚫 Failed to generate after $max_retries attempts: $topic"
    return 1
}

# Usage
generate_article "Advanced Python Patterns"
```

### Interactive vs Non-Interactive Modes
```bash
# Interactive (prompt for each input)
writeit run tutorial --cli

# Semi-automated (pre-fill some inputs)
echo -e "Docker Basics\n1" | writeit run tutorial --cli

# Fully automated (all inputs provided)
echo -e "Docker Basics\n1\ny\ny\ny" | writeit run tutorial --cli

# Conditional automation
if [ "$CI" = "true" ]; then
    # In CI: fully automated
    echo -e "Auto-generated docs\n2\ny\ny\ny" | writeit run api-docs --cli
else
    # Local development: interactive
    writeit run api-docs --cli
fi
```

## ✅ Template Validation with Rich Output

### Basic Validation
```bash
$ writeit validate tech-article
```

**Output:**
```
Validating: /Users/niko/.writeit/templates/tech-article.yaml (pipeline)

✅ All 1 file(s) validated successfully! ✓
```

### Detailed Validation
```bash
$ writeit validate tech-article --detailed
```

**Output:**
```
Validating: /Users/niko/.writeit/templates/tech-article.yaml (pipeline)

✓ File is valid (pipeline)
```

### Validation with Syntax Highlighting
```bash
$ writeit validate tech-article --show-content --detailed
```

**Output:**
```
Validating: /Users/niko/.writeit/templates/tech-article.yaml (pipeline)

# Syntax-highlighted YAML content
metadata:
  name: "Technical Article Pipeline"
  description: "4-step pipeline for technical articles"
  version: "1.0.0"
  
steps:
  angles:
    prompt_template: |
      Generate 3-5 different article angles...
    model_preference: ["gpt-4o", "claude-3-5-sonnet"]
    
  outline:
    prompt_template: |
      Create a detailed outline...
    model_preference: ["gpt-4o"]
    
# ... (colorized YAML continues)

✓ File is valid (pipeline)
```

### Multiple File Validation
```bash
$ writeit validate tech-article quick-article blog-post --summary-only
```

**Output:**
```
Validation Summary
Files processed: 3
✅ Valid files: 3
```

### Validation Errors with Rich Formatting
```bash
$ writeit validate broken-template --detailed
```

**Output:**
```
Validating: /Users/niko/templates/broken-template.yaml (pipeline)

❌ File has 3 issues (pipeline)

  ❌ Missing required field 'metadata.name' at metadata (line 2)
    💡 Add a descriptive name for your pipeline template

  ⚠️  Step 'angles' missing model_preference at steps.angles (line 8)
    💡 Specify preferred models like: ["gpt-4o", "claude-3-5-sonnet"]

  ℹ️  Consider adding description field at metadata
    💡 Help users understand what this pipeline does

❌ Validation failed for 1 file(s)
```

## 🎯 Shell Completion Management

### Installing Completion
```bash
$ writeit completion --install
```

**Output:**
```
✓ Shell completion installation instructions:
Add this to your zsh configuration file:

# Add to ~/.zshrc:
eval "$(writeit completion --show --shell zsh)"
```

### Showing Completion Script
```bash
$ writeit completion --show --shell bash
```

**Output:**
```
# WriteIt completion script for bash
_writeit_completion() {
    local cur prev words cword
    _init_completion || return
    
    case "$prev" in
        workspace)
            COMPREPLY=($(compgen -W "create list use remove info" -- "$cur"))
            return 0
            ;;
        use|remove|info)
            # Complete workspace names
            local workspaces
            workspaces=$(writeit workspace list 2>/dev/null | grep -v "Available workspaces" | sed 's/^[[:space:]]*\*\?[[:space:]]*//')
            COMPREPLY=($(compgen -W "$workspaces" -- "$cur"))
            return 0
            ;;
        # ... (completion script continues)
    esac
    
    COMPREPLY=($(compgen -W "init workspace run list-pipelines validate completion --help --version --workspace --verbose" -- "$cur"))
}

complete -F _writeit_completion writeit
```

## 🎨 Rich Theme and Styling

### Success Messages
```bash
$ writeit workspace create success-demo
```

**Output:**
```
✓ Created workspace 'success-demo'
```

### Error Messages
```bash
$ writeit workspace use nonexistent
```

**Output:**
```
┌─ Error ──────────────────────────────────────────────────────────────────────┐
│ Workspace 'nonexistent' not found                                           │
│                                                                              │
│ Available workspaces:                                                        │
│   • default                                                                  │
│   • my-blog                                                                  │
│   • technical                                                                │
│   • personal                                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Warning Messages
```bash
$ writeit workspace remove my-blog
```

**Output:**
```
⚠️  You are about to remove workspace 'my-blog'
Path: /Users/niko/.writeit/workspaces/my-blog
❌ This will permanently delete all data in this workspace.

Are you sure you want to continue? (y/N): n
Cancelled.
```

### Info Messages
```bash
$ writeit --verbose workspace list
```

**Output:**
```
ℹ️  Verbose mode enabled

        Available Workspaces        
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name          ┃ Status            ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ default       │ ✓ Active          │
│ my-blog       │                   │
└───────────────┴───────────────────┘

Active workspace: default
Total workspaces: 2
```

## 🔧 Development Mode Examples

### Development Commands with uv run
```bash
$ uv run writeit --help
```

**Output:** *(Same as above, but runs in development mode)*

### Development Validation
```bash
$ uv run writeit validate tech-article --detailed
```

**Output:**
```
Validating: /Users/niko/dev/writeit/templates/tech-article.yaml (pipeline)

✓ File is valid (pipeline)
```

## 💡 Pro Tips for Better CLI Experience

### Tab Completion in Action
After setting up completion, tab-completion works like this:

```bash
$ writeit work<TAB>
workspace

$ writeit workspace <TAB>
create  info    list    remove  use

$ writeit workspace use <TAB>
my-blog     technical   personal

$ writeit run <TAB>
tech-article    quick-article   blog-post   research-summary

$ writeit run tech-article --<TAB>
--cli    --global    --workspace    --help

$ writeit validate <TAB>
tech-article         quick-article        technical-expert
blog-post           research-summary     casual-tone
```

### Combining Commands
```bash
# Create workspace and immediately switch to it
$ writeit workspace create my-new-project --set-active
✓ Created workspace 'my-new-project'
✓ Set 'my-new-project' as active workspace

# Check pipelines in the new workspace
$ writeit list-pipelines
    Available Pipeline Templates    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                         ┃ Type                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ quick-article                │ Global                       │
│ tech-article                 │ Global                       │
└──────────────────────────────┴──────────────────────────────┘

# Run validation on multiple files
$ writeit validate tech-article quick-article --summary-only
Validation Summary
Files processed: 2
✅ Valid files: 2
```

---

These examples showcase WriteIt's beautiful, functional CLI interface built with Typer and Rich. The combination provides:

- **Rich-formatted help** with clear sections and colors
- **Dual execution modes**: Interactive TUI and automation-friendly CLI
- **Progress indicators** for long operations  
- **Beautiful tables** for data display
- **Syntax highlighting** for file content
- **Intelligent error messages** with helpful suggestions
- **Tab completion** for faster workflows
- **Consistent theming** throughout all commands
- **Automation support** with scriptable CLI mode
- **CI/CD integration** examples and patterns
- **Error handling** and retry mechanisms for production use

Try both modes:
- `writeit run tech-article` for the interactive TUI experience
- `writeit run tech-article --cli` for automation-friendly CLI mode

Experience the difference! 🚀