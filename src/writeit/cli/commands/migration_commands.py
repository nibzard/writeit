"""Migration commands for WriteIt CLI.

Provides user-facing commands for data migration operations, including
detection, analysis, execution, and validation of migrations.
"""

import typer
from pathlib import Path
from typing import Optional, List
from enum import Enum

from writeit.cli.output import console, print_success, print_error, print_warning
from writeit.cli.app import app

from ...application.commands.migration_commands import (
    MigrationType,
    MigrationPriority,
    DetectLegacyWorkspacesCommand,
    AnalyzeMigrationRequirementsCommand,
    StartMigrationCommand,
    BulkMigrationCommand,
    ValidateMigrationCommand,
    RollbackMigrationCommand,
    CleanupMigrationArtifactsCommand,
    GenerateMigrationReportCommand,
    CheckMigrationHealthCommand,
)

from ...application.queries.migration_queries import (
    GetMigrationStatusQuery,
    GetMigrationDetailsQuery,
    GetMigrationHistoryQuery,
    GetMigrationStatsQuery,
    GetLegacyWorkspacesQuery,
    GetMigrationRequirementsQuery,
    GetMigrationBackupsQuery,
    GetMigrationHealthQuery,
    MigrationFilter,
    MigrationSort,
)

from ...application.services.migration_application_service import DefaultMigrationApplicationService
from ...application.di_config import get_container


migration_app = typer.Typer(name="migration", help="Data migration commands")
app.add_typer(migration_app)


class MigrationFormat(str, Enum):
    """Output formats for migration commands."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    TABLE = "table"


@migration_app.command("detect")
def detect_legacy(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Path to search for legacy workspaces"
    ),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", help="Search recursively"
    ),
    format: MigrationFormat = typer.Option(
        MigrationFormat.TABLE, "--format", "-f", help="Output format"
    ),
):
    """Detect legacy workspaces and data formats that need migration."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = DetectLegacyWorkspacesCommand(
            search_paths=[path] if path else None,
            auto_analyze=True,
        )
        
        console.print("[primary]Detecting legacy workspaces...[/primary]")
        
        with console.status("[bold green]Searching for legacy data...[/bold green]"):
            legacy_workspaces = migration_service.detect_legacy_workspaces(command)
        
        if not legacy_workspaces:
            console.print("[secondary]No legacy workspaces found.[/secondary]")
            return
        
        # Display results based on format
        if format == MigrationFormat.TABLE:
            _display_legacy_workspaces_table(legacy_workspaces)
        elif format == MigrationFormat.JSON:
            import json
            console.print(json.dumps(legacy_workspaces, indent=2, default=str))
        elif format == MigrationFormat.YAML:
            import yaml
            console.print(yaml.dump(legacy_workspaces, default_flow_style=False))
        else:
            _display_legacy_workspaces_text(legacy_workspaces)
        
        print_success(f"Found {len(legacy_workspaces)} legacy workspaces")
        
    except Exception as e:
        print_error(f"Error detecting legacy workspaces: {e}")
        raise typer.Exit(1)


@migration_app.command("analyze")
def analyze_requirements(
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Workspace to analyze (default: active workspace)"
    ),
    all_workspaces: bool = typer.Option(
        False, "--all", help="Analyze all workspaces"
    ),
    check_data: bool = typer.Option(
        True, "--check-data/--no-check-data", help="Check data formats"
    ),
    check_config: bool = typer.Option(
        True, "--check-config/--no-check-config", help="Check configuration formats"
    ),
    check_cache: bool = typer.Option(
        True, "--check-cache/--no-check-cache", help="Check cache formats"
    ),
):
    """Analyze migration requirements for workspaces."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = AnalyzeMigrationRequirementsCommand(
            workspace_name=workspace,
            include_all_workspaces=all_workspaces,
            check_data_formats=check_data,
            check_configurations=check_config,
            check_cache=check_cache,
        )
        
        console.print("[primary]Analyzing migration requirements...[/primary]")
        
        with console.status("[bold green]Analyzing requirements...[/bold green]"):
            required_migrations = migration_service.analyze_migration_requirements(command)
        
        if not required_migrations:
            console.print("[secondary]No migrations required.[/secondary]")
            return
        
        # Display required migrations
        console.print("\n[bold]Required Migrations:[/bold]")
        for migration_type in required_migrations:
            console.print(f"  • {migration_type.value}")
        
        print_success(f"Found {len(required_migrations)} required migrations")
        
    except Exception as e:
        print_error(f"Error analyzing migration requirements: {e}")
        raise typer.Exit(1)


@migration_app.command("migrate")
def start_migration(
    migration_type: MigrationType = typer.Argument(..., help="Type of migration to perform"),
    source: Optional[Path] = typer.Option(
        None, "--source", "-s", help="Source path for migration"
    ),
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Target workspace name"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before migration"
    ),
    rollback: bool = typer.Option(
        True, "--rollback/--no-rollback", help="Rollback on failure"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be migrated without actually doing it"
    ),
    force: bool = typer.Option(
        False, "--force", help="Force migration even if warnings exist"
    ),
):
    """Start a migration operation."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = StartMigrationCommand(
            migration_type=migration_type,
            source_path=source,
            target_workspace=workspace,
            backup_before=backup,
            rollback_on_failure=rollback,
            dry_run=dry_run,
            force=force,
        )
        
        console.print(f"[primary]Starting {migration_type.value} migration...[/primary]")
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No actual changes will be made[/yellow]")
        
        with console.status("[bold green]Running migration...[/bold green]"):
            result = migration_service.start_migration(command)
        
        # Display results
        _display_migration_result(result)
        
        if result.status.value == "completed":
            print_success("Migration completed successfully")
        elif result.status.value == "failed":
            print_error("Migration failed")
            raise typer.Exit(1)
        elif result.status.value == "rolled_back":
            print_warning("Migration was rolled back due to failure")
            raise typer.Exit(1)
        
    except Exception as e:
        print_error(f"Error running migration: {e}")
        raise typer.Exit(1)


@migration_app.command("status")
def migration_status(
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Filter by workspace"
    ),
    migration_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by migration type"
    ),
    status_filter: MigrationFilter = typer.Option(
        MigrationFilter.ALL, "--status", "-s", help="Filter by status"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Limit number of results"
    ),
    format: MigrationFormat = typer.Option(
        MigrationFormat.TABLE, "--format", "-f", help="Output format"
    ),
):
    """Show migration status."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        query = GetMigrationStatusQuery(
            workspace_name=workspace,
            migration_type=migration_type,
            status_filter=status_filter,
            limit=limit,
        )
        
        migrations = migration_service.get_migration_status(query)
        
        if not migrations:
            console.print("[secondary]No migrations found.[/secondary]")
            return
        
        # Display results based on format
        if format == MigrationFormat.TABLE:
            _display_migrations_table(migrations)
        elif format == MigrationFormat.JSON:
            import json
            console.print(json.dumps(migrations, indent=2, default=str))
        elif format == MigrationFormat.YAML:
            import yaml
            console.print(yaml.dump(migrations, default_flow_style=False))
        else:
            _display_migrations_text(migrations)
        
    except Exception as e:
        print_error(f"Error getting migration status: {e}")
        raise typer.Exit(1)


@migration_app.command("history")
def migration_history(
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Filter by workspace"
    ),
    limit: int = typer.Option(
        20, "--limit", "-l", help="Limit number of results"
    ),
    include_failed: bool = typer.Option(
        True, "--include-failed/--no-failed", help="Include failed migrations"
    ),
    format: MigrationFormat = typer.Option(
        MigrationFormat.TABLE, "--format", "-f", help="Output format"
    ),
):
    """Show migration history."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        query = GetMigrationHistoryQuery(
            workspace_name=workspace,
            limit=limit,
            include_failed=include_failed,
        )
        
        migrations = migration_service.get_migration_history(query)
        
        if not migrations:
            console.print("[secondary]No migration history found.[/secondary]")
            return
        
        # Display results based on format
        if format == MigrationFormat.TABLE:
            _display_migrations_table(migrations)
        elif format == MigrationFormat.JSON:
            import json
            console.print(json.dumps(migrations, indent=2, default=str))
        elif format == MigrationFormat.YAML:
            import yaml
            console.print(yaml.dump(migrations, default_flow_style=False))
        else:
            _display_migrations_text(migrations)
        
    except Exception as e:
        print_error(f"Error getting migration history: {e}")
        raise typer.Exit(1)


@migration_app.command("validate")
def validate_migration(
    migration_id: str = typer.Argument(..., help="Migration ID to validate"),
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Workspace name"
    ),
    deep_validation: bool = typer.Option(
        False, "--deep", help="Perform deep validation"
    ),
    compare_with_source: bool = typer.Option(
        True, "--compare/--no-compare", help="Compare with source data"
    ),
):
    """Validate migration results."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = ValidateMigrationCommand(
            migration_id=migration_id,
            workspace_name=workspace,
            deep_validation=deep_validation,
            compare_with_source=compare_with_source,
        )
        
        console.print(f"[primary]Validating migration {migration_id}...[/primary]")
        
        with console.status("[bold green]Validating migration...[/bold green]"):
            validation_results = migration_service.validate_migration(command)
        
        # Display validation results
        _display_validation_results(validation_results)
        
        if validation_results["is_valid"]:
            print_success("Migration validation passed")
        else:
            print_error("Migration validation failed")
            raise typer.Exit(1)
        
    except Exception as e:
        print_error(f"Error validating migration: {e}")
        raise typer.Exit(1)


@migration_app.command("rollback")
def rollback_migration(
    migration_id: str = typer.Argument(..., help="Migration ID to rollback"),
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Workspace name"
    ),
    backup_path: Optional[Path] = typer.Option(
        None, "--backup-path", "-b", help="Specific backup path to restore"
    ),
    force: bool = typer.Option(
        False, "--force", help="Force rollback even if warnings exist"
    ),
):
    """Rollback a migration."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = RollbackMigrationCommand(
            migration_id=migration_id,
            workspace_name=workspace,
            backup_path=backup_path,
            force=force,
        )
        
        console.print(f"[primary]Rolling back migration {migration_id}...[/primary]")
        
        with console.status("[bold green]Rolling back migration...[/bold green]"):
            result = migration_service.rollback_migration(command)
        
        # Display results
        _display_migration_result(result)
        
        if result.status.value == "completed":
            print_success("Rollback completed successfully")
        else:
            print_error("Rollback failed")
            raise typer.Exit(1)
        
    except Exception as e:
        print_error(f"Error rolling back migration: {e}")
        raise typer.Exit(1)


@migration_app.command("cleanup")
def cleanup_migration(
    migration_id: str = typer.Argument(..., help="Migration ID to cleanup"),
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Workspace name"
    ),
    remove_backups: bool = typer.Option(
        False, "--remove-backups", help="Remove migration backups"
    ),
    remove_legacy_data: bool = typer.Option(
        False, "--remove-legacy", help="Remove legacy data"
    ),
):
    """Clean up migration artifacts."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = CleanupMigrationArtifactsCommand(
            migration_id=migration_id,
            workspace_name=workspace,
            remove_backups=remove_backups,
            remove_legacy_data=remove_legacy_data,
        )
        
        console.print(f"[primary]Cleaning up migration {migration_id}...[/primary]")
        
        with console.status("[bold green]Cleaning up...[/bold green]"):
            success = migration_service.cleanup_migration_artifacts(command)
        
        if success:
            print_success("Cleanup completed successfully")
        else:
            print_error("Cleanup failed")
            raise typer.Exit(1)
        
    except Exception as e:
        print_error(f"Error cleaning up migration: {e}")
        raise typer.Exit(1)


@migration_app.command("health")
def check_migration_health(
    check_disk: bool = typer.Option(
        True, "--disk/--no-disk", help="Check disk space"
    ),
    check_permissions: bool = typer.Option(
        True, "--permissions/--no-permissions", help="Check permissions"
    ),
    check_dependencies: bool = typer.Option(
        True, "--dependencies/--no-dependencies", help="Check dependencies"
    ),
    check_backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Check backup system"
    ),
):
    """Check migration system health."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = CheckMigrationHealthCommand(
            check_disk_space=check_disk,
            check_permissions=check_permissions,
            check_dependencies=check_dependencies,
            validate_backup_system=check_backup,
        )
        
        console.print("[primary]Checking migration system health...[/primary]")
        
        with console.status("[bold green]Checking health...[/bold green]"):
            health = migration_service.check_migration_health(command)
        
        # Display health results
        _display_health_results(health)
        
        if health.is_healthy:
            print_success("Migration system is healthy")
        else:
            print_error("Migration system has issues")
            raise typer.Exit(1)
        
    except Exception as e:
        print_error(f"Error checking migration health: {e}")
        raise typer.Exit(1)


@migration_app.command("report")
def generate_report(
    migration_id: Optional[str] = typer.Option(
        None, "--migration-id", "-m", help="Migration ID (generates summary if not provided)"
    ),
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Workspace name"
    ),
    detailed: bool = typer.Option(
        True, "--detailed/--simple", help="Include detailed information"
    ),
    format: MigrationFormat = typer.Option(
        MigrationFormat.TEXT, "--format", "-f", help="Output format"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Generate migration report."""
    try:
        container = get_container()
        migration_service = container.get(DefaultMigrationApplicationService)
        
        command = GenerateMigrationReportCommand(
            migration_id=migration_id,
            workspace_name=workspace,
            include_details=detailed,
            format=format.value,
        )
        
        console.print("[primary]Generating migration report...[/primary]")
        
        with console.status("[bold green]Generating report...[/bold green]"):
            report = migration_service.generate_migration_report(command)
        
        # Display or save report
        report_content = _format_report(report, format)
        
        if output:
            with open(output, 'w') as f:
                f.write(report_content)
            print_success(f"Report saved to {output}")
        else:
            console.print(report_content)
        
    except Exception as e:
        print_error(f"Error generating migration report: {e}")
        raise typer.Exit(1)


# Display helper functions
def _display_legacy_workspaces_table(workspaces: List[Dict[str, Any]]) -> None:
    """Display legacy workspaces in table format."""
    from rich.table import Table
    
    table = Table(title="Legacy Workspaces")
    table.add_column("Path", style="cyan")
    table.add_column("Has Config", style="green")
    table.add_column("Has Pipelines", style="green")
    table.add_column("Has Articles", style="green")
    table.add_column("Has LMDB", style="yellow")
    table.add_column("Complexity", style="magenta")
    table.add_column("Recommended Name", style="blue")
    
    for ws in workspaces:
        table.add_row(
            str(ws.get("path", "")),
            "✓" if ws.get("has_config") else "✗",
            "✓" if ws.get("has_pipelines") else "✗",
            "✓" if ws.get("has_articles") else "✗",
            "✓" if ws.get("has_lmdb") else "✗",
            ws.get("migration_complexity", "unknown"),
            ws.get("recommended_workspace_name", "unknown"),
        )
    
    console.print(table)


def _display_legacy_workspaces_text(workspaces: List[Dict[str, Any]]) -> None:
    """Display legacy workspaces in text format."""
    for i, ws in enumerate(workspaces, 1):
        console.print(f"\n[bold]{i}. {ws.get('path', 'Unknown')}[/bold]")
        console.print(f"   Config: {'✓' if ws.get('has_config') else '✗'}")
        console.print(f"   Pipelines: {'✓' if ws.get('has_pipelines') else '✗'}")
        console.print(f"   Articles: {'✓' if ws.get('has_articles') else '✗'}")
        console.print(f"   LMDB: {'✓' if ws.get('has_lmdb') else '✗'}")
        console.print(f"   Complexity: {ws.get('migration_complexity', 'unknown')}")
        console.print(f"   Recommended Name: {ws.get('recommended_workspace_name', 'unknown')}")


def _display_migrations_table(migrations: List[Dict[str, Any]]) -> None:
    """Display migrations in table format."""
    from rich.table import Table
    
    table = Table(title="Migrations")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Workspace", style="blue")
    table.add_column("Items Migrated", style="yellow")
    table.add_column("Items Failed", style="red")
    table.add_column("Duration (s)", style="magenta")
    
    for migration in migrations:
        status_color = "green" if migration.get("status") == "completed" else "red"
        table.add_row(
            migration.get("migration_id", ""),
            f"[{status_color}]{migration.get('status', 'unknown')}[/{status_color}]",
            migration.get("workspace_name", ""),
            str(migration.get("items_migrated", 0)),
            str(migration.get("items_failed", 0)),
            f"{migration.get('execution_time', 0):.1f}",
        )
    
    console.print(table)


def _display_migrations_text(migrations: List[Dict[str, Any]]) -> None:
    """Display migrations in text format."""
    for i, migration in enumerate(migrations, 1):
        console.print(f"\n[bold]{i}. {migration.get('migration_id', 'Unknown')}[/bold]")
        console.print(f"   Status: {migration.get('status', 'unknown')}")
        console.print(f"   Workspace: {migration.get('workspace_name', 'N/A')}")
        console.print(f"   Items Migrated: {migration.get('items_migrated', 0)}")
        console.print(f"   Items Failed: {migration.get('items_failed', 0)}")
        console.print(f"   Duration: {migration.get('execution_time', 0):.1f}s")
        if migration.get("error_details"):
            console.print(f"   Error: {migration.get('error_details')}")


def _display_migration_result(result) -> None:
    """Display migration result."""
    console.print(f"\n[bold]Migration: {result.migration_id}[/bold]")
    console.print(f"Status: {result.status.value}")
    console.print(f"Message: {result.message}")
    console.print(f"Items Migrated: {result.items_migrated}")
    console.print(f"Items Failed: {result.items_failed}")
    console.print(f"Execution Time: {result.execution_time.total_seconds():.1f}s")
    
    if result.backup_path:
        console.print(f"Backup: {result.backup_path}")
    
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")
    
    if result.error_details:
        console.print(f"\n[red]Error Details:[/red] {result.error_details}")


def _display_validation_results(results: Dict[str, Any]) -> None:
    """Display validation results."""
    console.print(f"\n[bold]Validation Results: {results.get('migration_id', 'Unknown')}[/bold]")
    
    status_color = "green" if results.get("is_valid") else "red"
    console.print(f"Status: [{status_color}]{results.get('is_valid', False)}[/{status_color}]")
    
    if results.get("issues"):
        console.print("\n[red]Issues:[/red]")
        for issue in results.get("issues", []):
            console.print(f"  • {issue}")
    
    if results.get("warnings"):
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in results.get("warnings", []):
            console.print(f"  • {warning}")


def _display_health_results(health) -> None:
    """Display health results."""
    console.print(f"\n[bold]Migration System Health[/bold]")
    
    status_color = "green" if health.is_healthy else "red"
    console.print(f"Overall Status: [{status_color}]{health.is_healthy}[/{status_color}]")
    
    console.print(f"Disk Space: {'✓' if health.permissions_ok else '✗'}")
    console.print(f"Permissions: {'✓' if health.permissions_ok else '✗'}")
    console.print(f"Dependencies: {'✓' if health.dependencies_ok else '✗'}")
    console.print(f"Backup System: {'✓' if health.backup_system_ok else '✗'}")
    
    if health.issues:
        console.print("\n[red]Issues:[/red]")
        for issue in health.issues:
            console.print(f"  • {issue}")


def _format_report(report, format: MigrationFormat) -> str:
    """Format report according to specified format."""
    if format == MigrationFormat.JSON:
        import json
        return json.dumps({
            "migration_id": report.migration_id,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "summary": report.summary,
            "details": report.details,
            "validation_results": report.validation_results,
            "recommendations": report.recommendations,
        }, indent=2)
    
    elif format == MigrationFormat.YAML:
        import yaml
        return yaml.dump({
            "migration_id": report.migration_id,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "summary": report.summary,
            "details": report.details,
            "validation_results": report.validation_results,
            "recommendations": report.recommendations,
        }, default_flow_style=False)
    
    else:  # TEXT format
        lines = [
            f"# {report.title}",
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Migration ID: {report.migration_id}",
            "",
            "## Summary",
        ]
        
        for key, value in report.summary.items():
            lines.append(f"{key}: {value}")
        
        if report.validation_results:
            lines.extend(["", "## Validation Results"])
            for key, value in report.validation_results.items():
                lines.append(f"{key}: {value}")
        
        if report.recommendations:
            lines.extend(["", "## Recommendations"])
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)