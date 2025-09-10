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
│ run              Start TUI pipeline execution.                               │
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

### Running a Pipeline
```bash
$ writeit run tech-article
```

**Output:**
```
Pipeline: tech-article
Path: /Users/niko/.writeit/templates/tech-article.yaml
Workspace: my-blog

⚠️  TUI pipeline execution not yet implemented
This will launch the Textual UI for pipeline execution.
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
- **Progress indicators** for long operations
- **Beautiful tables** for data display
- **Syntax highlighting** for file content
- **Intelligent error messages** with helpful suggestions
- **Tab completion** for faster workflows
- **Consistent theming** throughout all commands

Try it yourself with `writeit --help` and experience the difference! 🚀