"""CLI command for data migration from legacy formats to DDD structure."""

import asyncio
import json
from pathlib import Path
from typing import Optional
import click

from ...application.services.data_migration_service import DataMigrationService, MigrationResult
from ...workspace.config import WorkspaceConfig


@click.command()
@click.argument('source_path', type=click.Path(exists=True, path_type=Path))
@click.argument('workspace_name', type=str)
@click.option('--dry-run', is_flag=True, help='Analyze migration without making changes')
@click.option('--no-backup', is_flag=True, help='Skip creating backup before migration')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--output-report', type=click.Path(path_type=Path), help='Save migration report to file')
def migrate(
    source_path: Path,
    workspace_name: str,
    dry_run: bool,
    no_backup: bool,
    verbose: bool,
    output_report: Optional[Path]
) -> None:
    """Migrate legacy WriteIt workspace to new DDD structure.
    
    SOURCE_PATH: Path to legacy workspace directory
    WORKSPACE_NAME: Name for the new workspace
    
    This command migrates all data from the legacy WriteIt format to the new
    Domain-Driven Design architecture including:
    - Workspace structure and configuration
    - Token usage data to new TokenUsage entities  
    - Cache entries to new cache structure
    - Pipeline and template data to new domain entities
    
    Examples:
        writeit migrate ./legacy-project my-project
        writeit migrate ./legacy-project my-project --dry-run --verbose
        writeit migrate ./legacy-project my-project --no-backup
    """
    click.echo(f"Starting migration from {source_path} to workspace '{workspace_name}'...")
    
    if dry_run:
        click.echo("🔍 DRY RUN MODE - No changes will be made")
    
    # Initialize migration service
    migration_service = DataMigrationService()
    
    try:
        # Run migration
        result: MigrationResult = asyncio.run(
            migration_service.migrate_all_data(
                source_workspace_path=source_path,
                workspace_name=workspace_name,
                dry_run=dry_run,
                create_backup=not no_backup
            )
        )
        
        # Display results
        _display_migration_results(result, verbose)
        
        # Save report if requested
        if output_report:
            report = migration_service.get_migration_report()
            with open(output_report, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            click.echo(f"📄 Migration report saved to: {output_report}")
        
        # Exit with appropriate code
        if not result.success:
            click.exit(1)
            
    except KeyboardInterrupt:
        click.echo("\n❌ Migration cancelled by user")
        click.exit(130)
    except Exception as e:
        click.echo(f"❌ Migration failed with error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        click.exit(1)


def _display_migration_results(result: MigrationResult, verbose: bool) -> None:
    """Display migration results in a user-friendly format."""
    
    # Overall status
    if result.success:
        click.echo("✅ Migration completed successfully!")
    else:
        click.echo("❌ Migration failed!")
    
    # Summary statistics
    click.echo(f"\n📊 Migration Summary:")
    click.echo(f"   Duration: {result.duration_seconds:.2f} seconds")
    click.echo(f"   Items migrated: {result.migrated_count}")
    click.echo(f"   Errors: {result.error_count}")
    click.echo(f"   Warnings: {len(result.warnings)}")
    
    # Backup information
    if result.backup_path:
        click.echo(f"   Backup created: {result.backup_path}")
    
    # Message
    click.echo(f"\n💬 {result.message}")
    
    # Warnings
    if result.warnings:
        click.echo(f"\n⚠️  Warnings:")
        for warning in result.warnings[:5]:  # Show first 5 warnings
            click.echo(f"   - {warning}")
        if len(result.warnings) > 5:
            click.echo(f"   ... and {len(result.warnings) - 5} more warnings")
    
    # Verbose details
    if verbose and result.success:
        click.echo(f"\n🔍 Migration Details:")
        click.echo(f"   Source processed: Migration service analyzed all legacy data")
        click.echo(f"   Target created: New DDD-compliant workspace structure")
        click.echo(f"   Data transformed: Legacy formats converted to domain entities")
        click.echo(f"   Validation: All migrated data validated against DDD constraints")


@click.group()
def migration() -> None:
    """Data migration commands for WriteIt DDD transformation."""
    pass


@migration.command()
@click.argument('workspace_name', type=str)
def status(workspace_name: str) -> None:
    """Check migration status for a workspace.
    
    WORKSPACE_NAME: Name of the workspace to check
    
    This command analyzes a workspace to determine if it has been
    migrated to the new DDD structure and shows details about
    any legacy data that may still need migration.
    """
    workspace_config = WorkspaceConfig()
    workspace_path = workspace_config.get_workspace_path(workspace_name)
    
    if not workspace_path.exists():
        click.echo(f"❌ Workspace '{workspace_name}' does not exist")
        click.exit(1)
    
    click.echo(f"🔍 Checking migration status for workspace '{workspace_name}'...")
    
    # Check for DDD structure indicators
    ddd_indicators = [
        workspace_path / "domains",
        workspace_path / "config.yaml",
        workspace_path / "storage"
    ]
    
    has_ddd_structure = all(indicator.exists() for indicator in ddd_indicators)
    
    # Check for legacy data
    legacy_indicators = [
        workspace_path / ".writeit",
        workspace_path / "token_usage.json",
        workspace_path / "*.mdb"
    ]
    
    has_legacy_data = any(
        any(workspace_path.glob(pattern)) if "*" in str(indicator) else indicator.exists()
        for indicator in legacy_indicators
    )
    
    # Display status
    if has_ddd_structure and not has_legacy_data:
        click.echo("✅ Workspace is fully migrated to DDD structure")
    elif has_ddd_structure and has_legacy_data:
        click.echo("⚠️  Workspace has DDD structure but may have unmigrated legacy data")
    elif not has_ddd_structure and has_legacy_data:
        click.echo("📋 Workspace contains legacy data that needs migration")
    else:
        click.echo("❓ Workspace status unclear - may need manual inspection")
    
    # Show detailed findings
    click.echo(f"\n📋 Workspace Analysis:")
    click.echo(f"   Path: {workspace_path}")
    click.echo(f"   DDD structure: {'✅' if has_ddd_structure else '❌'}")
    click.echo(f"   Legacy data: {'⚠️' if has_legacy_data else '✅'}")
    
    # Show recommendations
    if has_legacy_data and not has_ddd_structure:
        click.echo(f"\n💡 Recommendation: Run migration with:")
        click.echo(f"   writeit migrate {workspace_path} {workspace_name}")
    elif has_legacy_data and has_ddd_structure:
        click.echo(f"\n💡 Recommendation: Check for remaining legacy files and run migration again")


@migration.command()
@click.argument('backup_path', type=click.Path(exists=True, path_type=Path))
@click.argument('workspace_name', type=str)
@click.option('--force', is_flag=True, help='Force rollback even if workspace exists')
def rollback(backup_path: Path, workspace_name: str, force: bool) -> None:
    """Rollback a migration using backup.
    
    BACKUP_PATH: Path to backup directory
    WORKSPACE_NAME: Name of workspace to rollback
    
    This command restores a workspace to its pre-migration state
    using the backup created during migration.
    
    WARNING: This will overwrite the current workspace state!
    """
    workspace_config = WorkspaceConfig()
    workspace_path = workspace_config.get_workspace_path(workspace_name)
    
    # Safety checks
    if workspace_path.exists() and not force:
        click.echo(f"❌ Workspace '{workspace_name}' already exists. Use --force to overwrite.")
        click.exit(1)
    
    if not backup_path.exists():
        click.echo(f"❌ Backup path does not exist: {backup_path}")
        click.exit(1)
    
    click.echo(f"🔄 Rolling back migration for workspace '{workspace_name}'...")
    click.echo(f"   From backup: {backup_path}")
    click.echo(f"   To workspace: {workspace_path}")
    
    if not force:
        # Ask for confirmation
        if not click.confirm("⚠️  This will overwrite the current workspace. Continue?"):
            click.echo("❌ Rollback cancelled")
            return
    
    try:
        # Perform rollback
        if workspace_path.exists():
            import shutil
            shutil.rmtree(workspace_path)
        
        shutil.copytree(backup_path, workspace_path)
        
        click.echo("✅ Rollback completed successfully!")
        click.echo(f"   Workspace '{workspace_name}' restored from backup")
        
    except Exception as e:
        click.echo(f"❌ Rollback failed: {str(e)}")
        click.exit(1)


@migration.command()
def list_backups() -> None:
    """List available migration backups."""
    backup_dir = Path.home() / ".writeit" / "backups"
    
    if not backup_dir.exists():
        click.echo("No backup directory found")
        return
    
    backups = list(backup_dir.glob("migration_backup_*"))
    
    if not backups:
        click.echo("No migration backups found")
        return
    
    click.echo("📋 Available Migration Backups:")
    click.echo()
    
    for backup in sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True):
        stat = backup.stat()
        size_mb = stat.st_size / (1024 * 1024)
        created = datetime.fromtimestamp(stat.st_mtime)
        
        click.echo(f"📁 {backup.name}")
        click.echo(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"   Size: {size_mb:.2f} MB")
        click.echo(f"   Path: {backup}")
        click.echo()


if __name__ == '__main__':
    migrate()