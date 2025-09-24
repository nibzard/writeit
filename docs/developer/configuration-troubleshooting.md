# WriteIt Configuration and Troubleshooting Guide

This guide provides comprehensive information about configuring WriteIt and troubleshooting common issues.

## 📋 Table of Contents

- [Configuration](#configuration)
- [Environment Setup](#environment-setup)
- [LLM Provider Configuration](#llm-provider-configuration)
- [Storage Configuration](#storage-configuration)
- [Workspace Configuration](#workspace-configuration)
- [Common Issues](#common-issues)
- [Performance Optimization](#performance-optimization)
- [Debugging](#debugging)
- [Migration Guide](#migration-guide)

---

## ⚙️ Configuration

### Configuration File Structure

WriteIt uses a hierarchical configuration system:

```
~/.writeit/                    # Global WriteIt directory
├── config.yaml                # Global configuration
├── workspaces/                # Workspace directory
│   ├── default/              # Default workspace
│   │   └── config.yaml       # Workspace-specific config
│   └── project1/             # Project workspace
│       └── config.yaml       # Workspace-specific config
├── templates/                 # Global templates
├── styles/                    # Global style primers
└── cache/                     # LLM response cache
```

### Global Configuration (`~/.writeit/config.yaml`)

```yaml
# WriteIt Global Configuration
version: "1.0.0"

# Workspace Settings
workspace:
  default_workspace: "default"
  auto_create_workspace: true
  workspace_paths:
    - "~/.writeit/workspaces"
    - "~/projects/writeit-workspaces"

# LLM Provider Configuration
llm:
  default_model: "gpt-4o-mini"
  fallback_models:
    - "claude-3-sonnet-20240229"
    - "gpt-3.5-turbo"
  
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      base_url: "https://api.openai.com/v1"
      timeout: 30
      max_retries: 3
      models:
        - "gpt-4o"
        - "gpt-4o-mini"
        - "gpt-3.5-turbo"
    
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      base_url: "https://api.anthropic.com"
      timeout: 30
      max_retries: 3
      models:
        - "claude-3-5-sonnet-20241022"
        - "claude-3-haiku-20240307"
        - "claude-3-sonnet-20240229"
    
    local:
      base_url: "http://localhost:8000/v1"
      api_key: "not-needed"
      timeout: 60
      max_retries: 1
      models:
        - "local-model"

# Storage Configuration
storage:
  type: "lmdb"
  base_path: "~/.writeit/storage"
  
  # LMDB Settings
  lmdb:
    map_size: 104857600        # 100MB
    max_dbs: 10
    max_readers: 126
    sync: true
    
  # Cache Settings
  cache:
    memory_cache_size: 1000
    persistent_cache: true
    cache_ttl: 86400          # 24 hours
    compression: true
    
  # Backup Settings
  backup:
    enabled: true
    interval: 86400          # Daily
    retention: 7              # Keep 7 days
    compression: true

# UI Configuration
ui:
  default_interface: "cli"    # cli, tui
  color_theme: "auto"        # auto, light, dark
  progress_style: "rich"     # rich, simple, none
  table_max_width: 80
  
  # TUI Settings
  tui:
    theme: "dark"
    animation: true
    mouse_support: true
    refresh_rate: 0.5

# Logging Configuration
logging:
  level: "INFO"              # DEBUG, INFO, WARNING, ERROR
  format: "rich"             # rich, json, text
  file: "~/.writeit/logs/writeit.log"
  max_size: 10485760          # 10MB
  backup_count: 5

# Security Settings
security:
  validate_inputs: true
  sanitize_prompts: true
  max_prompt_length: 100000
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10

# Performance Settings
performance:
  max_concurrent_executions: 5
  timeout: 300                # 5 minutes
  memory_limit: 536870912     # 512MB
  enable_caching: true
  cache_preload: true
```

### Workspace Configuration (`~/.writeit/workspaces/{name}/config.yaml`)

```yaml
# Workspace-specific Configuration
workspace:
  name: "my-project"
  description: "Blog content generation workspace"
  created_at: "2025-01-15T10:30:00Z"
  updated_at: "2025-01-15T10:30:00Z"
  
  # Template Paths
  template_paths:
    - "./templates"
    - "../shared/templates"
    - "~/.writeit/templates"
  
  # Style Primer Paths
  style_paths:
    - "./styles"
    - "../shared/styles"
    - "~/.writeit/styles"
  
  # Inherit global settings
  inherit_global: true
  
  # Workspace-specific settings
  settings:
    default_model: "gpt-4o"
    output_directory: "./output"
    auto_backup: true

# Override global LLM settings for this workspace
llm:
  default_model: "gpt-4o"      # Override global default
  custom_settings:
    temperature: 0.7
    max_tokens: 2000

# Workspace-specific storage
storage:
  # Separate cache for workspace
  cache:
    workspace_isolated: true
    custom_ttl: 43200          # 12 hours
  
  # Custom backup settings
  backup:
    enabled: true
    location: "./backups"
    interval: 3600            # Hourly

# Workspace-specific logging
logging:
  level: "DEBUG"
  file: "./writeit.log"
```

---

## 🌍 Environment Setup

### Required Environment Variables

```bash
# WriteIt Configuration
export WRITEIT_HOME="${HOME}/.writeit"
export WRITEIT_DEFAULT_WORKSPACE="default"
export WRITEIT_LOG_LEVEL="INFO"

# LLM Provider API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Local model configuration
export LOCAL_LLM_BASE_URL="http://localhost:8000"
export LOCAL_LLM_MODEL="my-local-model"

# Storage configuration
export WRITEIT_STORAGE_PATH="${HOME}/.writeit/storage"
export WRITEIT_CACHE_SIZE="1000"
export WRITEIT_CACHE_TTL="86400"

# Security and limits
export WRITEIT_MAX_CONCURRENT="5"
export WRITEIT_TIMEOUT="300"
export WRITEIT_RATE_LIMIT="60"
```

### Optional Environment Variables

```bash
# Development and debugging
export WRITEIT_DEBUG="true"
export WRITEIT_PROFILE="true"
export WRITEIT_TEST_MODE="false"

# UI preferences
export WRITEIT_COLOR_THEME="dark"
export WRITEIT_DEFAULT_INTERFACE="tui"

# Performance tuning
export WRITEIT_MEMORY_LIMIT="536870912"    # 512MB
export WRITEIT_MAX_RETRIES="3"
export WRITEIT_REQUEST_TIMEOUT="30"

# Storage settings
export WRITEIT_LMDB_MAP_SIZE="104857600"   # 100MB
export WRITEIT_ENABLE_COMPRESSION="true"
export WRITEIT_BACKUP_ENABLED="true"
```

### Setup Script

Create a setup script for new environments:

```bash
#!/bin/bash
# setup-writeit.sh - WriteIt environment setup

# WriteIt configuration
export WRITEIT_HOME="${HOME}/.writeit"
export WRITEIT_LOG_LEVEL="INFO"

# Create WriteIt directory structure
mkdir -p "${WRITEIT_HOME}"/{workspaces,templates,styles,cache,logs}

# Copy default configuration if it doesn't exist
if [ ! -f "${WRITEIT_HOME}/config.yaml" ]; then
    cp "config/default-config.yaml" "${WRITEIT_HOME}/config.yaml"
fi

# Initialize WriteIt
writeit init

echo "WriteIt environment setup complete!"
echo "Configuration location: ${WRITEIT_HOME}/config.yaml"
echo "Don't forget to set your LLM API keys!"
```

---

## 🤖 LLM Provider Configuration

### OpenAI Configuration

```yaml
llm:
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      base_url: "https://api.openai.com/v1"
      timeout: 30
      max_retries: 3
      models:
        - "gpt-4o"
        - "gpt-4o-mini"
        - "gpt-3.5-turbo"
      
      # Model-specific settings
      model_settings:
        gpt-4o:
          max_tokens: 4096
          temperature: 0.7
          top_p: 0.9
          
        gpt-4o-mini:
          max_tokens: 8192
          temperature: 0.7
          top_p: 0.9
```

### Anthropic Configuration

```yaml
llm:
  providers:
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      base_url: "https://api.anthropic.com"
      timeout: 30
      max_retries: 3
      models:
        - "claude-3-5-sonnet-20241022"
        - "claude-3-haiku-20240307"
        - "claude-3-sonnet-20240229"
      
      # Model-specific settings
      model_settings:
        claude-3-5-sonnet-20241022:
          max_tokens: 4096
          temperature: 0.7
          top_k: 40
          
        claude-3-haiku-20240307:
          max_tokens: 8192
          temperature: 0.7
          top_k: 40
```

### Local Model Configuration

```yaml
llm:
  providers:
    local:
      base_url: "http://localhost:8000/v1"
      api_key: "not-needed"
      timeout: 60
      max_retries: 1
      models:
        - "llama2-7b-chat"
        - "mistral-7b-instruct"
        - "codellama-7b-instruct"
      
      # Model-specific settings
      model_settings:
        llama2-7b-chat:
          max_tokens: 2048
          temperature: 0.8
          
        mistral-7b-instruct:
          max_tokens: 2048
          temperature: 0.7
```

### Provider Fallback Strategy

```yaml
llm:
  default_model: "gpt-4o-mini"
  fallback_models:
    - "claude-3-sonnet-20240229"
    - "gpt-3.5-turbo"
    - "claude-3-haiku-20240307"
  
  # Fallback configuration
  fallback:
    enabled: true
    max_attempts: 3
    retry_delay: 1.0
    exponential_backoff: true
    
  # Provider health checks
  health_checks:
    enabled: true
    interval: 300          # 5 minutes
    timeout: 10
    
  # Cost management
  cost_management:
    enabled: true
    monthly_budget: 100.0
    warn_threshold: 0.8    # 80% of budget
    block_threshold: 1.0   # 100% of budget
```

---

## 💾 Storage Configuration

### LMDB Configuration

```yaml
storage:
  type: "lmdb"
  base_path: "~/.writeit/storage"
  
  # LMDB-specific settings
  lmdb:
    map_size: 104857600        # 100MB
    max_dbs: 10
    max_readers: 126
    sync: true
    lock: true
    
    # Environment flags
    flags:
      no_subdir: false
      readonly: false
      metasync: true
      sync: true
      map_async: false
    
    # Database configuration
    databases:
      pipeline_runs:
        key_size: 32
        value_size: 4096
        dupsort: false
        
      pipeline_events:
        key_size: 32
        value_size: 1024
        dupsort: true
        
      llm_cache:
        key_size: 64
        value_size: 8192
        dupsort: false
```

### Cache Configuration

```yaml
storage:
  cache:
    # Two-tier cache strategy
    memory_cache_size: 1000    # Max entries in memory
    persistent_cache: true     # Use persistent cache
    
    # Cache key configuration
    key_components:
      - "prompt"
      - "model"
      - "context"
      - "workspace"
    
    # Cache policies
    eviction_policy: "lru"     # lru, lfu, fifo
    ttl: 86400                 # 24 hours
    compression: true          # Compress cached values
    
    # Cache statistics
    track_stats: true
    log_hits: true
    log_misses: false
    
    # Cache invalidation
    invalidate_on:
      - "model_update"
      - "workspace_change"
      - "template_update"
```

### Backup Configuration

```yaml
storage:
  backup:
    enabled: true
    interval: 86400          # Daily backups
    retention: 7              # Keep 7 days
    compression: true
    
    # Backup location
    location: "~/.writeit/backups"
    
    # What to backup
    include:
      - "workspaces"
      - "templates"
      - "styles"
      - "config"
    
    exclude:
      - "cache"
      - "logs"
      - "*.tmp"
    
    # Backup format
    format: "tar.gz"
    encryption: false        # Enable with GPG key
    
    # Verification
    verify_integrity: true
    test_restore: false      # Periodic restore tests
```

---

## 📁 Workspace Configuration

### Workspace Templates

```yaml
# Workspace template configuration
workspace_templates:
  blog:
    description: "Blog content generation workspace"
    template_path: "templates/blog"
    style_path: "styles/blog"
    config:
      llm:
        default_model: "gpt-4o"
      storage:
        cache:
          ttl: 43200    # 12 hours for blog content
  
  technical:
    description: "Technical documentation workspace"
    template_path: "templates/technical"
    style_path: "styles/technical"
    config:
      llm:
        default_model: "gpt-4o"
      storage:
        cache:
          ttl: 86400    # 24 hours for technical docs
```

### Workspace Inheritance

```yaml
# Global settings that workspaces can inherit
global_inheritance:
  llm:
    providers: true
    fallback_models: true
    health_checks: true
  
  storage:
    base_path: true
    backup: true
    compression: true
  
  ui:
    color_theme: true
    progress_style: true
  
  security:
    validate_inputs: true
    rate_limiting: true

# Workspace-specific overrides
workspace_overrides:
  my-project:
    llm:
      default_model: "gpt-4o"    # Override global default
    
    storage:
      cache:
        ttl: 43200              # Override global TTL
```

### Workspace Migration

```yaml
# Migration configuration
migration:
  enabled: true
  source_format: "legacy"
  target_format: "current"
  
  # Migration rules
  rules:
    workspace_config:
      rename_keys:
        "workspace_dir": "workspace_path"
        "template_dir": "template_paths"
      remove_keys:
        - "deprecated_setting"
        - "old_config"
    
    pipeline_config:
      rename_keys:
        "steps": "pipeline_steps"
        "inputs": "pipeline_inputs"
      transform_values:
        "model": "model_mapping"
```

---

## 🚨 Common Issues

### Installation Issues

#### Issue: WriteIt not found after installation
```bash
# Symptoms
bash: writeit: command not found

# Solutions
# 1. Check installation
pip list | grep writeit

# 2. Ensure installation location is in PATH
which python
echo $PATH

# 3. Reinstall with explicit path
pip install --user writeit
export PATH="$HOME/.local/bin:$PATH"

# 4. Check virtual environment
source venv/bin/activate  # If using venv
which writeit
```

#### Issue: Missing dependencies
```bash
# Symptoms
ImportError: No module named 'typer'
ModuleNotFoundError: No module named 'rich'

# Solutions
# 1. Reinstall dependencies
pip install -e .

# 2. Install specific dependencies
pip install typer rich pydantic

# 3. Check requirements.txt
pip install -r requirements.txt

# 4. Upgrade pip
pip install --upgrade pip
```

### Configuration Issues

#### Issue: Configuration file not found
```bash
# Symptoms
WriteIt not initialized. Run 'writeit init' first.
Configuration file not found: ~/.writeit/config.yaml

# Solutions
# 1. Initialize WriteIt
writeit init

# 2. Create config manually
mkdir -p ~/.writeit
cat > ~/.writeit/config.yaml << EOF
version: "1.0.0"
workspace:
  default_workspace: "default"
EOF

# 3. Check file permissions
ls -la ~/.writeit/
chmod 755 ~/.writeit
chmod 644 ~/.writeit/config.yaml
```

#### Issue: Invalid configuration format
```bash
# Symptoms
Error parsing configuration file
Invalid YAML syntax
Configuration validation failed

# Solutions
# 1. Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.writeit/config.yaml'))"

# 2. Check configuration schema
writeit validate-config

# 3. Use configuration template
cp ~/.writeit/config.yaml ~/.writeit/config.yaml.backup
cp config/default-config.yaml ~/.writeit/config.yaml

# 4. Check for common YAML issues
# - No tabs (use spaces)
# - Proper indentation
# - Quoted strings with special characters
# - No trailing commas
```

### LLM Provider Issues

#### Issue: API key not configured
```bash
# Symptoms
API key not configured for provider
Authentication failed
Invalid API key

# Solutions
# 1. Set environment variable
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Add to configuration file
# ~/.writeit/config.yaml
llm:
  providers:
    openai:
      api_key: "sk-..."
    anthropic:
      api_key: "sk-ant-..."

# 3. Test API key
curl -H "Authorization: Bearer sk-..." https://api.openai.com/v1/models

# 4. Check environment variable
echo $OPENAI_API_KEY
```

#### Issue: Rate limiting or quota exceeded
```bash
# Symptoms
Rate limit exceeded
Quota exceeded
Too many requests

# Solutions
# 1. Check current usage
# OpenAI Dashboard: https://platform.openai.com/usage
# Anthropic Console: https://console.anthropic.com

# 2. Configure fallback models
# ~/.writeit/config.yaml
llm:
  fallback_models:
    - "gpt-3.5-turbo"
    - "claude-3-haiku-20240307"

# 3. Implement caching
storage:
  cache:
    enabled: true
    ttl: 86400

# 4. Add rate limiting
security:
  rate_limiting:
    enabled: true
    requests_per_minute: 60
```

#### Issue: Model not available
```bash
# Symptoms
Model not found: 'gpt-5'
Invalid model name
Model not supported by provider

# Solutions
# 1. Check available models
writeit llm list-models

# 2. Update configuration with valid models
# ~/.writeit/config.yaml
llm:
  providers:
    openai:
      models:
        - "gpt-4o"
        - "gpt-4o-mini"
        - "gpt-3.5-turbo"

# 3. Test model availability
python -c "
import openai
client = openai.OpenAI()
models = client.models.list()
print([m.id for m in models.data])
"
```

### Storage Issues

#### Issue: LMDB map size exceeded
```bash
# Symptoms
LMDB map size exceeded
MDB_MAP_FULL: Environment mapsize limit reached
Database full

# Solutions
# 1. Increase map size
# ~/.writeit/config.yaml
storage:
  lmdb:
    map_size: 1048576000  # 1GB

# 2. Clean up old data
writeit cleanup --old-data --days 30

# 3. Enable compression
storage:
  compression: true

# 4. Backup and recreate
writeit backup --output backup.tar.gz
writeit reset --storage
writeit restore --input backup.tar.gz
```

#### Issue: Permission denied
```bash
# Symptoms
Permission denied: ~/.writeit
Cannot create directory: Permission denied
Cannot open database: Permission denied

# Solutions
# 1. Check permissions
ls -la ~/.writeit/
ls -la ~/.writeit/workspaces/

# 2. Fix permissions
chmod 755 ~/.writeit
chmod 755 ~/.writeit/workspaces
chmod -R 644 ~/.writeit/*.yaml

# 3. Check ownership
ls -ld ~/.writeit/
# If owned by root: sudo chown -R $USER:$USER ~/.writeit

# 4. Check disk space
df -h ~/.writeit/
```

### Workspace Issues

#### Issue: Workspace not found
```bash
# Symptoms
Workspace not found: 'my-project'
Cannot switch to workspace
Invalid workspace name

# Solutions
# 1. List available workspaces
writeit workspace list

# 2. Create workspace
writeit workspace create my-project

# 3. Check workspace directory
ls -la ~/.writeit/workspaces/

# 4. Validate workspace name
# Valid: a-z, 0-9, hyphens, underscores
# Invalid: spaces, special characters
```

#### Issue: Workspace corruption
```bash
# Symptoms
Workspace configuration corrupted
Cannot load workspace: invalid data
Workspace validation failed

# Solutions
# 1. Validate workspace
writeit workspace validate my-project

# 2. Check workspace config
cat ~/.writeit/workspaces/my-project/config.yaml
python -c "import yaml; yaml.safe_load(open('~/.writeit/workspaces/my-project/config.yaml'))"

# 3. Restore from backup
writeit backup --workspace my-project --output my-project-backup.tar.gz
writeit workspace remove my-project --force
writeit workspace create my-project
writeit restore --workspace my-project --input my-project-backup.tar.gz

# 4. Manual recovery
cp ~/.writeit/workspaces/my-project/config.yaml ~/.writeit/workspaces/my-project/config.yaml.backup
# Edit config manually to fix issues
```

### Pipeline Issues

#### Issue: Template not found
```bash
# Symptoms
Template not found: 'my-template'
Cannot load template
Invalid template path

# Solutions
# 1. List available templates
writeit template list

# 2. Check template paths
writeit workspace info --include-paths

# 3. Validate template location
ls -la ~/.writeit/templates/
ls -la ~/.writeit/workspaces/current/templates/

# 4. Create template
writeit template create my-template --type pipeline
```

#### Issue: Pipeline execution failed
```bash
# Symptoms
Pipeline execution failed
Step execution timeout
Invalid pipeline configuration

# Solutions
# 1. Check pipeline status
writeit list-runs --status failed

# 2. Validate pipeline template
writeit validate --detailed my-template

# 3. Check execution logs
writeit logs --run-id <run-id> --level DEBUG

# 4. Run with debug mode
writeit run my-template --debug --inputs topic="test"

# 5. Check LLM provider health
writeit llm health-check
```

---

## ⚡ Performance Optimization

### Caching Optimization

```yaml
# Optimize cache settings
storage:
  cache:
    # Increase memory cache for frequently used responses
    memory_cache_size: 2000
    
    # Optimize TTL based on use case
    ttl: 172800    # 48 hours for content that doesn't change often
    
    # Enable compression for larger responses
    compression: true
    compression_level: 6
    
    # Use efficient eviction policy
    eviction_policy: "lru"
    
    # Enable cache warming for common prompts
    preload_common: true
    
    # Cache statistics for monitoring
    track_stats: true
    log_stats_interval: 3600  # Log every hour
```

### Storage Optimization

```yaml
# Optimize LMDB settings
storage:
  lmdb:
    # Increase map size for larger datasets
    map_size: 1073741824  # 1GB
    
    # Optimize for concurrent access
    max_readers: 256
    max_dbs: 20
    
    # Enable synchronous writes for data integrity
    sync: true
    
    # Use environment flags for performance
    flags:
      nosync: false      # Keep sync for safety
      readonly: false
      metasync: true
    
  # Enable compression for large values
  compression: true
  compression_level: 6
  
  # Optimize database configuration
  databases:
    pipeline_events:
      dupsort: true      # Allow duplicate keys for event streams
      integerkey: true   # Use integer keys for performance
```

### Concurrency Optimization

```yaml
# Optimize concurrent execution
performance:
  # Increase concurrent pipeline executions
  max_concurrent_executions: 10
  
  # Optimize timeouts
  timeout: 600          # 10 minutes
  
  # Memory management
  memory_limit: 1073741824  # 1GB
  gc_interval: 300     # Garbage collection every 5 minutes
  
  # Connection pooling
  connection_pool:
    max_size: 20
    min_size: 5
    idle_timeout: 300

# LLM optimization
llm:
  # Configure request batching
  batch_requests: true
  batch_size: 5
  batch_timeout: 1.0
  
  # Optimize retry strategy
  retry:
    max_attempts: 3
    base_delay: 1.0
    max_delay: 30.0
    exponential_backoff: true
```

### Memory Optimization

```yaml
# Memory optimization settings
performance:
  # Memory limits
  memory_limit: 1073741824  # 1GB
  stack_size: 8388608      # 8MB
  
  # Garbage collection
  gc:
    enabled: true
    threshold: 0.8        # Trigger at 80% memory usage
    interval: 300         # Check every 5 minutes
  
  # Memory monitoring
  monitor:
    enabled: true
    interval: 60          # Check every minute
    alert_threshold: 0.9  # Alert at 90% usage

# Cache memory optimization
storage:
  cache:
    memory_cache_size: 1000
    memory_limit: 52428800  # 50MB for cache
    
    # Cache entry size limits
    max_entry_size: 1048576  # 1MB per entry
    
    # Memory pressure handling
    on_memory_pressure:
      action: "evict"      # evict, compress, reject
      threshold: 0.8       # 80% memory usage
```

---

## 🔍 Debugging

### Enable Debug Mode

```bash
# Enable debug logging
export WRITEIT_LOG_LEVEL="DEBUG"
export WRITEIT_DEBUG="true"

# Run with debug output
writeit run my-template --debug

# Enable verbose output
writeit --verbose run my-template

# Enable debug for specific modules
export WRITEIT_DEBUG_MODULES="storage,llm,pipeline"
```

### Debug Configuration Files

```bash
# Validate configuration syntax
writeit validate-config

# Show effective configuration
writeit config --show-effective

# Check configuration paths
writeit config --show-paths

# Test workspace configuration
writeit workspace validate my-workspace
```

### Debug Storage Issues

```bash
# Check storage health
writeit storage health-check

# Show storage statistics
writeit storage stats

# Check database integrity
writeit storage check-integrity

# Show cache statistics
writeit cache stats

# Clear cache (debug only)
writeit cache clear --force
```

### Debug LLM Issues

```bash
# Test LLM provider connectivity
writeit llm test-provider openai

# Check available models
writeit llm list-models

# Test model response
writeit llm test-model gpt-4o-mini --prompt "Hello, world!"

# Show provider statistics
writeit llm stats

# Check rate limits
writeit llm rate-limits
```

### Debug Pipeline Execution

```bash
# Run pipeline with dry-run
writeit run my-template --dry-run --verbose

# Show pipeline execution plan
writeit run my-template --show-plan

# Validate pipeline template
writeit validate --detailed my-template

# Show execution logs
writeit logs --run-id <run-id> --level DEBUG

# Debug step execution
writeit run my-template --debug-step outline
```

### Debug Scripts

Create debug scripts for common issues:

```bash
#!/bin/bash
# debug-writeit.sh - WriteIt debugging script

echo "=== WriteIt Debug Information ==="
echo "Date: $(date)"
echo

# Basic information
echo "=== Basic Info ==="
echo "WriteIt Version: $(writeit --version)"
echo "Python Version: $(python --version)"
echo "Operating System: $(uname -a)"
echo

# Environment
echo "=== Environment ==="
echo "WRITEIT_HOME: ${WRITEIT_HOME:-Not set}"
echo "WRITEIT_LOG_LEVEL: ${WRITEIT_LOG_LEVEL:-Not set}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+Set}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+Set}"
echo

# WriteIt status
echo "=== WriteIt Status ==="
writeit status
echo

# Workspace information
echo "=== Workspaces ==="
writeit workspace list --verbose
echo

# Storage health
echo "=== Storage Health ==="
writeit storage health-check 2>/dev/null || echo "Storage health check failed"
echo

# LLM providers
echo "=== LLM Providers ==="
writeit llm test-provider openai 2>/dev/null || echo "OpenAI test failed"
writeit llm test-provider anthropic 2>/dev/null || echo "Anthropic test failed"
echo

echo "=== End Debug Information ==="
```

---

## 🔄 Migration Guide

### From Legacy WriteIt

If you're upgrading from a pre-DDD version of WriteIt:

```bash
# 1. Backup existing data
cp -r ~/.writeit ~/.writeit.backup.$(date +%Y%m%d)

# 2. Initialize with migration
writeit init --migrate

# 3. Validate migration
writeit workspace validate default
writeit validate --global tech-article

# 4. Test functionality
writeit run tech-article --dry-run
```

### Configuration Migration

```yaml
# Legacy configuration format (example)
legacy_config:
  workspace_dir: "~/.writeit/workspaces"
  api_key: "sk-..."
  default_model: "gpt-4"
  cache_size: 1000

# Migration to new format
migrated_config:
  workspace:
    workspace_paths: ["~/.writeit/workspaces"]
  llm:
    providers:
      openai:
        api_key: "sk-..."
    default_model: "gpt-4"
  storage:
    cache:
      memory_cache_size: 1000
```

### Data Migration

```bash
# Migrate workspace data
writeit migrate --type workspace --source ~/.writeit.backup/workspaces

# Migrate templates
writeit migrate --type templates --source ~/.writeit.backup/templates

# Migrate cache (optional)
writeit migrate --type cache --source ~/.writeit.backup/cache

# Validate migration
writeit validate-all
```

### Common Migration Issues

#### Issue: Migration fails with data format error
```bash
# Solution: Use force migration
writeit migrate --type workspace --force

# Solution: Migrate individual workspaces
writeit migrate --type workspace --source ~/.writeit.backup/workspaces/my-project
```

#### Issue: Missing configuration after migration
```bash
# Solution: Manual configuration update
cp ~/.writeit.backup/config.yaml ~/.writeit/config.yaml
# Update format manually
```

#### Issue: Performance degradation after migration
```bash
# Solution: Optimize new configuration
writeit optimize-config
writeit storage optimize
```

---

This comprehensive configuration and troubleshooting guide should help you configure WriteIt effectively and resolve common issues. For additional help, check the logs at `~/.writeit/logs/` or use the debug commands provided.