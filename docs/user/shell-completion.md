# Shell Completion Guide

WriteIt provides intelligent shell completion for all commands, options, workspaces, and pipeline names. Set it up once and enjoy faster, more efficient CLI usage.

## 🚀 Quick Setup

### Automatic Installation
```bash
# Auto-detect your shell and show installation instructions
writeit completion --install

# For specific shells
writeit completion --install --shell bash
writeit completion --install --shell zsh
writeit completion --install --shell fish
```

### Manual Installation
```bash
# Generate completion script for your shell
writeit completion --show --shell bash

# Add to your shell configuration
echo 'eval "$(writeit completion --show --shell bash)"' >> ~/.bashrc
```

## 🐚 Shell-Specific Instructions

### Bash
```bash
# Add to ~/.bashrc or ~/.bash_profile
eval "$(writeit completion --show --shell bash)"

# Or create a completion file
writeit completion --show --shell bash > ~/.bash_completion.d/writeit
```

### Zsh
```bash
# Add to ~/.zshrc
eval "$(writeit completion --show --shell zsh)"

# Or use completion directory
mkdir -p ~/.zsh/completions
writeit completion --show --shell zsh > ~/.zsh/completions/_writeit
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc
```

### Fish
```bash
# Add to ~/.config/fish/config.fish
writeit completion --show --shell fish | source

# Or create completion file
mkdir -p ~/.config/fish/completions
writeit completion --show --shell fish > ~/.config/fish/completions/writeit.fish
```

### PowerShell
```powershell
# Add to your PowerShell profile
writeit completion --show --shell powershell | Out-String | Invoke-Expression

# Or save to profile
writeit completion --show --shell powershell >> $PROFILE
```

## ✨ What Gets Completed

### Commands and Subcommands
```bash
writeit <TAB>
# Completes: init, workspace, run, list-pipelines, validate, completion

writeit workspace <TAB>
# Completes: create, list, use, remove, info

writeit validate <TAB>
# Completes: --type, --detailed, --show-content, --global, --local
```

### Workspace Names
```bash
writeit workspace use <TAB>
# Completes with actual workspace names: my-blog, technical-docs, personal

writeit workspace remove <TAB>
# Completes with existing workspaces (excluding active workspace)

writeit --workspace <TAB>
# Global workspace option completion
```

### Pipeline Names
```bash
writeit run <TAB>
# Completes with available pipeline templates:
# tech-article, quick-article, blog-post, research-summary

writeit validate <TAB>
# Completes with pipeline templates and style primers
```

### File Paths and Options
```bash
writeit validate --type <TAB>
# Completes: pipeline, style, auto

writeit completion --shell <TAB>
# Completes: bash, zsh, fish, powershell

writeit validate my-template --<TAB>
# Completes: --detailed, --show-content, --global, --local, --type
```

## 🔧 Advanced Completion Features

### Context-Aware Suggestions
Completion is intelligent and context-aware:

```bash
# Only shows removable workspaces (not the active one)
writeit workspace remove <TAB>

# Shows both pipeline templates and style primers
writeit validate <TAB>

# Pipeline names from both global and workspace-specific locations
writeit run <TAB>
```

### Dynamic Updates
Completion data is fetched dynamically, so it stays up-to-date:
- New workspaces appear immediately in completion
- Pipeline templates from global and workspace directories
- Only valid options for each command context

### Performance
Completion functions are optimized for speed:
- Cached results where appropriate
- Fast directory scanning
- Graceful fallback if WriteIt isn't initialized

## 🛠️ Troubleshooting

### Completion Not Working

**Check if completion is loaded:**
```bash
# Test basic completion
writeit <TAB>

# Check if function exists (bash/zsh)
type _writeit_completion
```

**Reload shell configuration:**
```bash
# Bash
source ~/.bashrc

# Zsh
source ~/.zshrc

# Fish
source ~/.config/fish/config.fish
```

### Slow Completion

**For large numbers of workspaces/pipelines:**
```bash
# Completion caches results briefly
# If it's still slow, check for filesystem issues
ls -la ~/.writeit/workspaces/
```

### Missing Workspaces/Pipelines

**Ensure WriteIt is initialized:**
```bash
writeit workspace list
# If this fails, run: writeit init
```

**Check workspace access:**
```bash
ls -la ~/.writeit/
ls -la ~/.writeit/workspaces/
```

### Completion Updates

**Force refresh completion cache:**
```bash
# Simply run a WriteIt command to refresh
writeit workspace list > /dev/null
```

## 📝 Customizing Completion

### Adding Custom Completions
If you're extending WriteIt, you can customize the completion script:

```bash
# Generate the base script
writeit completion --show --shell bash > my_writeit_completion.sh

# Edit to add your custom logic
# Then source it instead of the default
```

### Integration with Other Tools
```bash
# Combine with other CLI tools
alias wr="writeit"
complete -F _writeit_completion wr  # bash
compdef wr=writeit                  # zsh
```

## 🎯 Best Practices

### Daily Workflow
1. **Set up completion once** - Add to your shell config
2. **Use tab liberally** - It's faster than typing full names
3. **Discover commands** - Tab to see what's available
4. **Learn shortcuts** - `writeit w<TAB>` → `writeit workspace`

### Efficiency Tips
```bash
# Quick workspace switching
writeit workspace use <TAB>

# Fast pipeline discovery
writeit run <TAB>

# Rapid validation
writeit validate <TAB> --detailed

# Option discovery
writeit validate --<TAB>
```

### Teaching Your Team
```bash
# Share setup commands
echo "# WriteIt completion setup"
echo 'eval "$(writeit completion --show)"' >> ~/.bashrc

# Document common patterns
echo "# Tab to complete workspace names:"
echo "writeit workspace use <TAB>"
```

## 🔄 Updates and Maintenance

### Keeping Completion Current
Completion updates automatically with WriteIt updates. No maintenance required.

### Version Compatibility
Shell completion works with WriteIt 0.1.0+. Older versions used different completion systems.

### Shell Support
- ✅ **Bash 4.0+** - Full support
- ✅ **Zsh 5.0+** - Full support  
- ✅ **Fish 3.0+** - Full support
- ✅ **PowerShell 5.0+** - Full support
- ⚠️ **Other shells** - Basic completion may work

## 📚 Additional Resources

- **[Quick Start Tutorial](quickstart.md)** - Get started with WriteIt
- **[Workspace Management](workspace-management.md)** - Organize your projects
- **[CLI Reference](../api/cli-reference.md)** - Complete command documentation

---

**Pro Tip**: Once you set up completion, WriteIt becomes much more discoverable. Use `<TAB>` liberally to explore commands and options! 🚀