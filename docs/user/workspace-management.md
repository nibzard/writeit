# Workspace Management Guide

Complete guide to organizing your writing projects with WriteIt's centralized workspace system.

## 🏗️ Overview

WriteIt uses a centralized `~/.writeit` directory that organizes all your content, making it accessible from anywhere while keeping projects isolated and organized.

```bash
~/.writeit/                         # Your WriteIt home
├── config.yaml                    # Global settings & active workspace
├── templates/                      # Global pipeline templates
├── styles/                         # Global style primers
├── workspaces/                     # Your organized projects
│   ├── default/                   # Default workspace
│   ├── blog/                      # Blog articles workspace
│   ├── technical/                 # Technical documentation
│   └── personal/                  # Personal writing
└── cache/                          # Shared LLM response cache
```

## 🚀 Getting Started

### Initial Setup

```bash
# Initialize WriteIt (creates ~/.writeit)
writeit init

# Optional: Auto-migrate existing local workspaces
writeit init --migrate

# Check status
writeit workspace list
# Output: * default
```

### Create Your First Workspace

```bash
# Create workspace for your project
writeit workspace create my-blog

# Switch to it
writeit workspace use my-blog

# Verify active workspace
writeit workspace info
# Output:
# Workspace: my-blog
# Path: ~/.writeit/workspaces/my-blog
# Created: 2025-01-15T10:30:00Z
# Default pipeline: None
# Stored entries: 0
```

## 📁 Workspace Commands

### Create Workspaces

```bash
# Create new workspace
writeit workspace create <name>

# Examples
writeit workspace create blog-articles
writeit workspace create technical-docs
writeit workspace create client-work
writeit workspace create personal-writing
```

**Naming Guidelines:**
- Use lowercase with hyphens or underscores
- Be descriptive: `tech-blog` not `blog1`
- Avoid spaces and special characters
- Maximum 50 characters

### List and Navigate

```bash
# List all workspaces
writeit workspace list
# Output:
#   default
# * my-blog        # * indicates active workspace
#   technical-docs
#   personal-writing

# Switch to different workspace
writeit workspace use technical-docs

# Get detailed information
writeit workspace info [workspace-name]
# If no name provided, shows active workspace
```

### Remove Workspaces

```bash
# Remove workspace (cannot remove active workspace)
writeit workspace remove old-project

# Switch first, then remove
writeit workspace use default
writeit workspace remove old-project
```

⚠️ **Warning**: Removing a workspace permanently deletes all its content, including articles, pipelines, and history. Always backup important work first.

## 🔄 Working with Workspaces

### The "Run from Anywhere" Feature

Once you've set an active workspace, all WriteIt commands work from any directory:

```bash
# Switch to your blog workspace
writeit workspace use my-blog

# Now run pipelines from anywhere
cd ~/Desktop
writeit run tech-article.yaml    # Uses my-blog workspace

cd ~/Documents/projects
writeit list-pipelines           # Shows my-blog pipelines

cd /tmp
writeit workspace info           # Shows my-blog info
```

### Override Active Workspace

```bash
# Use specific workspace for one command
writeit --workspace technical-docs run api-documentation.yaml

# List pipelines from different workspace
writeit --workspace personal-writing list-pipelines
```

### Environment Variable Override

```bash
# Set in your shell profile
export WRITEIT_WORKSPACE=my-blog

# Now all commands use my-blog workspace by default
writeit run article.yaml        # Uses my-blog
```

## 📊 Workspace Organization Patterns

### 1. Project-Based Organization

```bash
# Organize by distinct projects
writeit workspace create company-blog
writeit workspace create personal-blog  
writeit workspace create newsletter
writeit workspace create documentation
```

**Use when:**
- Working on separate, distinct projects
- Different clients or organizations
- Completely different content types

### 2. Content-Type Organization

```bash
# Organize by content type
writeit workspace create articles
writeit workspace create tutorials
writeit workspace create case-studies
writeit workspace create social-media
```

**Use when:**
- Similar audience across content
- Consistent brand/voice
- Shared pipelines and styles

### 3. Client-Based Organization

```bash
# Organize by client
writeit workspace create client-acme
writeit workspace create client-widgets-inc
writeit workspace create internal-content
```

**Use when:**
- Freelance or agency work
- Different style guides per client
- Separate billing/tracking needs

### 4. Hybrid Organization

```bash
# Combine approaches
writeit workspace create acme-blog          # Client + content type
writeit workspace create acme-docs          # Client + content type
writeit workspace create personal-tech      # Personal + topic
writeit workspace create personal-travel    # Personal + topic
```

## 🛠️ Workspace Configuration

### Workspace-Specific Settings

Each workspace has its own configuration file:

```bash
# View workspace config
cat ~/.writeit/workspaces/my-blog/workspace.yaml
```

```yaml
# Example workspace.yaml
name: my-blog
created_at: '2025-01-15T10:30:00'
default_pipeline: blog-post.yaml
llm_providers:
  openai: configured
  anthropic: configured
style_guide: conversational.yaml
```

### Global vs Workspace Configuration

WriteIt uses hierarchical configuration:

1. **Global** (`~/.writeit/config.yaml`) - Shared settings
2. **Workspace** (`~/.writeit/workspaces/{name}/workspace.yaml`) - Workspace overrides  
3. **Local** (`.writeit/config.yaml` in current directory) - Project overrides
4. **Environment** (`WRITEIT_*` variables) - Runtime overrides

### Customize Workspace Settings

```bash
# Set default pipeline for workspace
writeit config set --workspace my-blog default-pipeline blog-post.yaml

# Set workspace-specific LLM preferences
writeit config set --workspace technical-docs preferred-models gpt-4,claude-sonnet

# View effective configuration
writeit config show --workspace my-blog
```

## 📁 Workspace Directory Structure

Each workspace contains:

```bash
~/.writeit/workspaces/my-blog/
├── workspace.yaml              # Workspace configuration
├── pipelines/                  # Workspace-specific pipelines
│   ├── blog-post.yaml         # Custom blog pipeline
│   └── newsletter.yaml        # Newsletter pipeline
├── articles/                   # Generated articles
│   ├── 2025-01-15_ai-trends.md
│   └── 2025-01-16_python-tips.md
├── main.lmdb/                  # Main artifact storage
├── pipelines.lmdb/             # Pipeline run history
└── cache.lmdb/                 # Workspace-specific cache
```

### Storage Isolation

Each workspace has completely isolated storage:

- **Articles**: Separate directories
- **LMDB data**: Separate database files
- **Pipeline history**: Independent tracking
- **Configuration**: Workspace-specific overrides

## 🔄 Migration and Backup

### Migrating Existing Projects

```bash
# Auto-detect and migrate local .writeit directories
writeit init --migrate

# Manual migration
writeit migrate-workspace ~/old-project my-new-workspace
```

### Backup Workspaces

```bash
# Backup entire WriteIt installation
cp -r ~/.writeit ~/.writeit-backup-$(date +%Y%m%d)

# Backup specific workspace
cp -r ~/.writeit/workspaces/my-blog ~/backups/my-blog-backup

# Export workspace content
writeit export --workspace my-blog --output ~/exports/my-blog.tar.gz
```

### Restore Workspaces

```bash
# Restore from backup
cp -r ~/backups/my-blog-backup ~/.writeit/workspaces/my-blog

# Import exported workspace
writeit import ~/exports/my-blog.tar.gz
```

## ⚡ Advanced Workspace Features

### Workspace Templates

```bash
# Create workspace from template
writeit workspace create --template blog-starter my-new-blog

# Save current workspace as template
writeit workspace save-template my-blog blog-template
```

### Cross-Workspace Operations

```bash
# Copy pipeline between workspaces
writeit pipeline copy --from technical-docs --to my-blog api-doc.yaml

# Share style guide globally
writeit style promote --workspace my-blog conversational.yaml

# Search across all workspaces
writeit search "artificial intelligence" --all-workspaces
```

### Workspace Statistics

```bash
# Show workspace usage
writeit workspace stats
# Output:
# Workspace Statistics:
# 
# my-blog:           15 articles, 45 pipeline runs, 120MB storage
# technical-docs:     8 articles, 23 pipeline runs, 65MB storage  
# personal-writing:   3 articles,  7 pipeline runs, 12MB storage
# 
# Total:             26 articles, 75 pipeline runs, 197MB storage

# Detailed workspace analysis
writeit workspace analyze my-blog
# Output:
# Workspace: my-blog
# Created: 2025-01-10
# Most used pipeline: blog-post.yaml (12 runs)
# Average article length: 1,847 words
# Most productive day: 2025-01-15 (3 articles)
# Storage breakdown:
#   - Articles: 45MB
#   - Pipeline history: 67MB
#   - Cache: 8MB
```

## 🔍 Troubleshooting

### Common Issues

#### Workspace Not Found
```bash
# Check if workspace exists
writeit workspace list

# Create if missing
writeit workspace create missing-workspace
```

#### Permission Denied
```bash
# Fix permissions
chmod 755 ~/.writeit
chmod -R 644 ~/.writeit/workspaces/
```

#### Corrupted Workspace
```bash
# Repair workspace
writeit workspace repair my-blog

# Or recreate from backup
writeit workspace remove my-blog
cp -r ~/backups/my-blog-backup ~/.writeit/workspaces/my-blog
```

#### Can't Switch Workspaces
```bash
# Check current workspace lock
writeit workspace unlock

# Force switch
writeit workspace use --force different-workspace
```

### Maintenance

```bash
# Clean up old artifacts (keeps last 50 runs per workspace)
writeit cleanup --keep 50

# Compact database files
writeit workspace compact my-blog

# Verify workspace integrity
writeit workspace verify my-blog
```

## 🌟 Best Practices

### 1. Naming Conventions
- Use consistent naming: `project-type` or `client-project`
- Avoid changing workspace names frequently
- Use descriptive names: `tech-blog` not `blog1`

### 2. Organization Strategy
- Start with simple organization, evolve as needed
- Group related content in same workspace
- Use separate workspaces for different audiences

### 3. Backup Strategy
- Backup before major changes
- Regular automated backups of `~/.writeit`
- Export important workspaces before system changes

### 4. Performance Optimization
- Keep workspaces focused (avoid too many articles in one)
- Regular cleanup of old artifacts
- Use workspace-specific caching

### 5. Collaboration
- Use consistent workspace names across team
- Share workspace templates
- Document workspace organization in team wiki

---

## 📚 See Also

- [Installation Guide](installation.md) - Initial WriteIt setup
- [Quick Start Tutorial](quickstart.md) - Your first article
- [Pipeline Configuration](../developer/pipelines.md) - Custom pipeline creation
- [Configuration Reference](../developer/configuration.md) - All configuration options

**Ready to organize your writing?** Start with `writeit workspace create my-first-project` and begin writing! ✍️