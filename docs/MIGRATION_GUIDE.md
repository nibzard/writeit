# WriteIt Data Migration Guide

This guide explains how to migrate your existing WriteIt workspaces from the legacy format to the new Domain-Driven Design (DDD) architecture.

## Overview

The migration system safely converts:
- Legacy workspace structures (`.writeit` directories)
- Configuration files
- Pipeline definitions  
- Template files
- LMDB storage data
- Cache entries

## Prerequisites

Before starting migration:
1. **Backup your data**: The migration system creates automatic backups, but having a separate backup is recommended
2. **Check for pickle data**: Some legacy data formats use unsafe pickle serialization that cannot be migrated
3. **Ensure disk space**: Migration requires temporary space for backups

## Migration Commands

### 1. Detect Legacy Workspaces

First, scan your system for legacy workspaces that need migration:

```bash
# Simple detection
writeit migrate detect

# Detailed analysis with complexity assessment
writeit migrate detect --detailed

# Search specific paths
writeit migrate detect --path /path/to/search
```

### 2. Check for Unsafe Data

Legacy installations may have used pickle serialization, which is unsafe and cannot be migrated:

```bash
writeit migrate check-pickle ~/.writeit
```

If pickle data is found, those specific entries will be skipped during migration.

### 3. Migrate Single Workspace

Migrate a specific legacy workspace:

```bash
# Basic migration with auto-generated workspace name
writeit migrate migrate /path/to/legacy/workspace

# Specify target workspace name
writeit migrate migrate /path/to/legacy/workspace --target my-project

# Skip backup creation (not recommended)
writeit migrate migrate /path/to/legacy/workspace --no-backup

# Overwrite existing workspace
writeit migrate migrate /path/to/legacy/workspace --overwrite
```

### 4. Migrate All Workspaces

Migrate all detected legacy workspaces:

```bash
# Interactive mode (prompts for each workspace)
writeit migrate migrate-all

# Non-interactive mode
writeit migrate migrate-all --non-interactive

# Search specific paths
writeit migrate migrate-all --path /path/to/search
```

### 5. Validate Migration

After migration, validate that the workspace was successfully converted:

```bash
writeit migrate validate workspace-name
```

## Migration Process

### What Gets Migrated

1. **Workspace Structure**
   - `.writeit` directories → centralized `~/.writeit/workspaces/`
   - Configuration files
   - Directory structure

2. **Configuration Data**
   - LLM provider settings
   - Default preferences
   - Workspace-specific settings

3. **Pipelines & Templates**
   - YAML pipeline definitions
   - Template files
   - Associated metadata

4. **Storage Data**
   - LMDB database files
   - Pipeline execution history
   - Generated content (safe formats only)

5. **Cache Data**
   - LLM response cache (safe formats only)
   - Template rendering cache

### What Gets Skipped

- **Pickle-serialized data**: Unsafe and cannot be migrated
- **Corrupted files**: Files that cannot be read
- **Unknown formats**: Data in unrecognized formats

### Backup and Rollback

The migration system automatically creates backups before making changes:

```bash
# List available backups
writeit migration rollback list-backups

# Restore from backup (advanced)
writeit migration rollback restore backup-id
```

Backups are stored in `~/.writeit/migration_backups/` with timestamps.

## Common Scenarios

### Scenario 1: Single Project Migration

You have a single project with a `.writeit` directory:

```bash
# 1. Detect the workspace
writeit migrate detect --path ~/my-project

# 2. Check for unsafe data
writeit migrate check-pickle ~/my-project/.writeit

# 3. Migrate the workspace
writeit migrate migrate ~/my-project --target my-project

# 4. Validate the migration
writeit migrate validate my-project
```

### Scenario 2: Multiple Workspaces

You have multiple projects across your system:

```bash
# 1. Detect all workspaces
writeit migrate detect --detailed

# 2. Migrate all workspaces interactively
writeit migrate migrate-all

# 3. Validate all migrations
writeit workspace list
```

### Scenario 3: Migration with Issues

If migration encounters problems:

```bash
# 1. Run with detailed output
writeit migrate migrate /path/to/workspace --verbose

# 2. Check the migration report
# Reports are saved to ~/.writeit/migration_reports/

# 3. Restore from backup if needed
writeit migration rollback restore backup-id
```

## Troubleshooting

### Common Issues

**Migration fails with "NameError: self is not defined"**
- This is a known issue with complex workspace configurations
- Try migrating with `--no-backup` flag
- Report the issue with your workspace structure

**"No legacy workspaces found"**
- Ensure you're searching the correct paths
- Check that `.writeit` directories exist
- Use `--path` to specify exact locations

**"Permission denied" errors**
- Ensure you have read/write access to source and target directories
- Run with appropriate permissions
- Check disk space in `~/.writeit/`

**"Configuration migration failed"**
- Legacy configurations may have incompatible settings
- The system will create default configurations
- Manual configuration may be required after migration

### Getting Help

```bash
# Get help with migration commands
writeit migrate --help
writeit migrate migrate --help

# Check migration status
writeit migration status
```

## Post-Migration Steps

### 1. Verify Workspace Functionality

```bash
# Test basic workspace operations
writeit workspace list
writeit workspace use migrated-workspace
writeit list-pipelines

# Try running a simple pipeline
writeit run simple-pipeline --tui
```

### 2. Update Configuration

Some legacy configuration settings may need manual updates:

```bash
# Edit workspace configuration
writeit workspace config edit migrated-workspace

# Check LLM provider settings
writeit config show
```

### 3. Clean Up (Optional)

After successful migration and verification:

```bash
# Remove original .writeit directories (backups exist)
rm -rf /path/to/original/.writeit

# Clean up old migration backups
writeit migration cleanup --older-than 30days
```

## Advanced Usage

### Custom Migration Paths

```bash
# Migrate to a custom location
writeit migrate migrate /source --target custom-name --workspace-path /custom/path
```

### Dry Run Mode

Test migration without making changes:

```bash
# Preview what would be migrated
writeit migrate migrate /source --dry-run
```

### Selective Migration

Migrate specific components only:

```bash
# Migrate only configuration
writeit migrate migrate /source --components config

# Migrate only pipelines
writeit migrate migrate /source --components pipelines
```

## Data Safety

The migration system is designed with safety in mind:

1. **Automatic Backups**: Every migration creates a timestamped backup
2. **Validation**: Post-migration validation ensures data integrity
3. **Rollback**: Restore from backup if issues occur
4. **Safe Serialization**: Only uses safe, well-defined serialization formats
5. **Error Handling**: Graceful handling of corrupted or incompatible data

## Reporting Issues

If you encounter migration issues:

1. Enable verbose logging: `writeit --verbose migrate ...`
2. Check migration reports in `~/.writeit/migration_reports/`
3. Provide the legacy workspace structure (without sensitive data)
4. Include error messages and system information

## Conclusion

The WriteIt migration system provides a safe, reliable way to transition from legacy workspace formats to the new DDD architecture. By following this guide and using the provided tools, you can ensure your data is migrated successfully while maintaining full rollback capability.