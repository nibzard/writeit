"""Simple migration command for WriteIt CLI.

Provides a straightforward command for migrating legacy workspaces to the new DDD format.
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from writeit.cli.output import print_success, print_error, print_warning
from writeit.migration.data_migrator import MigrationManager, MigrationResult


# Simple migration app
simple_migration_app = typer.Typer(
    name="simple-migrate", 
    help="Simple workspace migration commands for legacy data"
)


@simple_migration_app.command("detect")
def detect_legacy_workspaces(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Path to search for legacy workspaces"
    ),
    detailed: bool = typer.Option(
        False, "--detailed", help="Show detailed analysis"
    ),
) -> None:
    """Detect legacy workspaces that need migration."""
    console = Console()
    
    try:
        migration_manager = MigrationManager()
        
        search_paths = [path] if path else None
        legacy_workspaces = migration_manager.scan_for_migrations(search_paths)
        
        if not legacy_workspaces:
            console.print("[secondary]No legacy workspaces found.[/secondary]")
            return
        
        if detailed:
            _display_detailed_detection(console, legacy_workspaces, migration_manager)
        else:
            _display_simple_detection(console, legacy_workspaces)
        
        print_success(f"Found {len(legacy_workspaces)} legacy workspaces")
        
    except Exception as e:
        print_error(f"Error detecting legacy workspaces: {e}")
        raise typer.Exit(1)


@simple_migration_app.command("migrate")
def migrate_workspace(
    source: Path = typer.Argument(..., help="Path to legacy workspace to migrate"),
    target_name: Optional[str] = typer.Option(
        None, "--target", "-t", help="Target workspace name (auto-generated if not provided)"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before migration"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing workspace"
    ),
    validate: bool = typer.Option(
        True, "--validate/--no-validate", help="Validate migration after completion"
    ),
) -> None:
    """Migrate a legacy workspace to new DDD format."""
    console = Console()
    
    try:
        migration_manager = MigrationManager()
        
        console.print(f"[primary]Starting migration of {source}...[/primary]")
        
        if backup:
            console.print("[yellow]Backup will be created before migration[/yellow]")
        
        with console.status("[bold green]Running migration...[/bold green]"):
            result = migration_manager.migrator.migrate_workspace(
                source,
                target_name=target_name,
                overwrite=overwrite,
                backup=backup
            )
        
        _display_migration_result(console, result)
        
        if result.success:
            if validate and target_name:
                console.print("\n[primary]Validating migration...[/primary]")
                validation_result = migration_manager.validate_migration(target_name)
                _display_validation_result(console, validation_result)
            
            print_success("Migration completed successfully!")
        else:
            print_error("Migration failed!")
            raise typer.Exit(1)
            
    except Exception as e:
        print_error(f"Error during migration: {e}")
        raise typer.Exit(1)


@simple_migration_app.command("migrate-all")
def migrate_all_workspaces(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Path to search for legacy workspaces"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--non-interactive", help="Prompt for each workspace"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before migration"
    ),
) -> None:
    """Migrate all detected legacy workspaces."""
    console = Console()
    
    try:
        migration_manager = MigrationManager()
        
        search_paths = [path] if path else None
        legacy_workspaces = migration_manager.scan_for_migrations(search_paths)
        
        if not legacy_workspaces:
            console.print("[secondary]No legacy workspaces found.[/secondary]")
            return
        
        console.print(f"[primary]Found {len(legacy_workspaces)} legacy workspaces[/primary]")
        
        results = migration_manager.migrate_all(
            search_paths=search_paths,
            interactive=interactive,
            backup=backup
        )
        
        # Display results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        _display_bulk_migration_results(console, results)
        
        if failed == 0:
            print_success(f"All {successful} workspaces migrated successfully!")
        else:
            print_warning(f"Migration completed: {successful} successful, {failed} failed")
            
    except Exception as e:
        print_error(f"Error during bulk migration: {e}")
        raise typer.Exit(1)


@simple_migration_app.command("validate")
def validate_migrated_workspace(
    workspace_name: str = typer.Argument(..., help="Name of workspace to validate")
) -> None:
    """Validate that a migrated workspace is working correctly."""
    console = Console()
    
    try:
        migration_manager = MigrationManager()
        
        console.print(f"[primary]Validating workspace '{workspace_name}'...[/primary]")
        
        with console.status("[bold green]Validating workspace...[/bold green]"):
            result = migration_manager.validate_migration(workspace_name)
        
        _display_validation_result(console, result)
        
        if result.success:
            print_success("Workspace validation passed!")
        else:
            print_error("Workspace validation failed!")
            raise typer.Exit(1)
            
    except Exception as e:
        print_error(f"Error during validation: {e}")
        raise typer.Exit(1)


@simple_migration_app.command("check-pickle")
def check_pickle_data(
    path: Path = typer.Argument(..., help="Path to storage directory to check")
) -> None:
    """Check for legacy pickle data in storage."""
    console = Console()
    
    try:
        from writeit.migration.data_migrator import DataFormatDetector
        
        console.print(f"[primary]Checking for pickle data in {path}...[/primary]")
        
        pickle_keys = DataFormatDetector.detect_legacy_pickle_data(path)
        
        if not pickle_keys:
            console.print("[secondary]No pickle data found.[/secondary]")
            return
        
        console.print(f"[red]Found {len(pickle_keys)} keys with pickle data:[/red]")
        
        # Show first 20 keys
        display_keys = pickle_keys[:20]
        for key in display_keys:
            console.print(f"  • {key}")
        
        if len(pickle_keys) > 20:
            console.print(f"  ... and {len(pickle_keys) - 20} more")
        
        print_warning("Pickle data cannot be migrated for security reasons")
        
    except Exception as e:
        print_error(f"Error checking pickle data: {e}")
        raise typer.Exit(1)


# Display helper functions
def _display_simple_detection(console: Console, workspaces: List[Path]) -> None:
    """Display simple detection results."""
    console.print("\n[bold]Legacy Workspaces Found:[/bold]")
    for i, path in enumerate(workspaces, 1):
        console.print(f"  {i}. {path}")


def _display_detailed_detection(
    console: Console, 
    workspaces: List[Path], 
    migration_manager: MigrationManager
) -> None:
    """Display detailed detection results."""
    from rich.table import Table
    
    table = Table(title="Legacy Workspace Analysis")
    table.add_column("Path", style="cyan")
    table.add_column("Has Config", style="green")
    table.add_column("Pipelines", style="green")
    table.add_column("Articles", style="green")
    table.add_column("Has LMDB", style="yellow")
    table.add_column("Complexity", style="magenta")
    
    for path in workspaces:
        try:
            analysis = migration_manager.detector.analyze_legacy_workspace(path)
            table.add_row(
                str(path),
                "✓" if analysis.has_pipelines or analysis.has_articles else "✗",
                str(analysis.pipeline_count),
                str(analysis.article_count),
                "✓" if analysis.has_lmdb else "✗",
                analysis.migration_complexity,
            )
        except Exception:
            table.add_row(str(path), "✗", "0", "0", "✗", "unknown")
    
    console.print(table)


def _display_migration_result(console: Console, result: MigrationResult) -> None:
    """Display migration result."""
    console.print(f"\n[bold]Migration Result[/bold]")
    console.print(f"Status: {'[green]Success[/green]' if result.success else '[red]Failed[/red]'}")
    console.print(f"Message: {result.message}")
    console.print(f"Items Migrated: {result.migrated_items}")
    console.print(f"Items Skipped: {result.skipped_items}")
    console.print(f"Items Failed: {result.error_items}")
    
    if result.backup_path:
        console.print(f"Backup: {result.backup_path}")
    
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings[:10]:  # Show first 10 warnings
            console.print(f"  • {warning}")
        if len(result.warnings) > 10:
            console.print(f"  ... and {len(result.warnings) - 10} more warnings")
    
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")


def _display_validation_result(console: Console, result: MigrationResult) -> None:
    """Display validation result."""
    console.print(f"\n[bold]Validation Result[/bold]")
    console.print(f"Status: {'[green]Passed[/green]' if result.success else '[red]Failed[/red]'}")
    console.print(f"Message: {result.message}")
    
    if result.warnings:
        console.print("\n[yellow]Validation Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")


def _display_bulk_migration_results(console: Console, results: List[MigrationResult]) -> None:
    """Display bulk migration results."""
    from rich.table import Table
    
    table = Table(title="Bulk Migration Results")
    table.add_column("Source", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Migrated", style="yellow")
    table.add_column("Failed", style="red")
    table.add_column("Message", style="blue")
    
    for result in results:
        status_color = "green" if result.success else "red"
        status_text = "Success" if result.success else "Failed"
        
        # Extract source path from result or message
        if hasattr(result, 'source_path'):
            source = str(result.source_path)
        else:
            source = result.message.split("'")[1] if "'" in result.message else "Unknown"
        
        table.add_row(
            source,
            f"[{status_color}]{status_text}[/{status_color}]",
            str(result.migrated_items),
            str(result.error_items),
            result.message[:50] + "..." if len(result.message) > 50 else result.message,
        )
    
    console.print(table)