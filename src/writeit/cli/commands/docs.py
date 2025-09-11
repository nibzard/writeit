"""
CLI commands for documentation generation
"""

from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from writeit.docs import DocumentationGenerator, DocumentationValidator
from writeit.docs.deployment import DocumentationDeployment
from writeit.docs.models import DocumentationMetrics

app = typer.Typer(help="Documentation generation and management commands")
console = Console()


@app.command("generate")
def generate_docs(
    output: Path = typer.Option(Path("docs/generated"), "--output", "-o", help="Output directory for generated documentation"),
    format: List[str] = typer.Option(["markdown"], "--format", "-f", help="Output format(s)"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate documentation after generation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Generate documentation from code"""
    console.print(Panel("📚 Generating Documentation", style="bold blue"))
    
    try:
        # Initialize generator
        generator = DocumentationGenerator(config_path=config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Generate documentation
            task = progress.add_task("Generating documentation...", total=None)
            docs = generator.generate_all()
            progress.update(task, completed=True)
        
        # Display generation results
        _display_generation_results(docs, generator.get_metrics(), verbose)
        
        # Validate if requested
        if validate:
            validator = DocumentationValidator()
            console.print("\n")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Validating documentation...", total=None)
                results = validator.validate_all(docs)
                progress.update(task, completed=True)
            
            _display_validation_results(results)
        
        # Deploy documentation
        deployment = DocumentationDeployment()
        deployment.deploy(docs, output, format)
        
        console.print(f"\n✅ Documentation generated successfully in {output}")
        
    except Exception as e:
        console.print(f"❌ Error generating documentation: {e}", style="red")
        raise typer.Exit(1)


@app.command("validate")
def validate_docs(
    docs_path: Path = typer.Option(Path("docs/generated"), "--docs-path", "-d", help="Path to generated documentation"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results"),
    fix_issues: bool = typer.Option(False, "--fix", help="Attempt to fix common issues automatically")
):
    """Validate existing documentation"""
    console.print(Panel("🔍 Validating Documentation", style="bold yellow"))
    
    try:
        validator = DocumentationValidator()
        
        # Load existing documentation or generate it
        if docs_path.exists():
            console.print("Loading existing documentation...")
            # For now, regenerate documentation to validate current state
            generator = DocumentationGenerator(config_path=config)
            docs = generator.generate_all()
        else:
            console.print("No existing documentation found, generating...")
            generator = DocumentationGenerator(config_path=config)
            docs = generator.generate_all()
        
        # Validate documentation
        results = validator.validate_all(docs)
        
        # Display results
        _display_validation_results(results, detailed)
        
        # Fix issues if requested
        if fix_issues and not results.is_valid:
            console.print("\n🔧 Attempting to fix issues...")
            fixed_count = validator.fix_common_issues(results)
            console.print(f"Fixed {fixed_count} issues")
        
        # Exit with appropriate code
        if not results.is_valid:
            console.print("\n❌ Documentation validation failed", style="red")
            raise typer.Exit(1)
        else:
            console.print("\n✅ Documentation validation passed", style="green")
            
    except Exception as e:
        console.print(f"❌ Error validating documentation: {e}", style="red")
        raise typer.Exit(1)


@app.command("preview")
def preview_docs(
    docs_path: Path = typer.Option(Path("docs/site"), "--docs-path", "-d", help="Path to documentation site"),
    port: int = typer.Option(8000, "--port", "-p", help="Port for preview server"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host for preview server")
):
    """Preview documentation locally"""
    console.print(Panel("👀 Starting Documentation Preview", style="bold green"))
    
    try:
        deployment = DocumentationDeployment()
        deployment.serve_local_preview(docs_path, host, port)
        
    except Exception as e:
        console.print(f"❌ Error starting preview server: {e}", style="red")
        raise typer.Exit(1)


@app.command("metrics")
def show_metrics(
    docs_path: Path = typer.Option(Path("docs/generated"), "--docs-path", "-d", help="Path to generated documentation"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Show documentation metrics and statistics"""
    console.print(Panel("📊 Documentation Metrics", style="bold magenta"))
    
    try:
        # Generate documentation to get fresh metrics
        generator = DocumentationGenerator(config_path=config)
        generator.generate_all()
        metrics = generator.get_metrics()
        
        # Display metrics table
        table = Table(title="Documentation Coverage")
        table.add_column("Metric", style="cyan")
        table.add_column("Documented", style="green")
        table.add_column("Total", style="blue")
        table.add_column("Coverage", style="yellow")
        
        table.add_row("Modules", str(metrics.documented_modules), str(metrics.total_modules), f"{metrics.module_coverage:.1f}%")
        table.add_row("Classes", str(metrics.documented_classes), str(metrics.total_classes), f"{metrics.class_coverage:.1f}%")
        table.add_row("Functions", str(metrics.documented_functions), str(metrics.total_functions), f"{metrics.function_coverage:.1f}%")
        table.add_row("API Endpoints", str(metrics.documented_api_endpoints), str(metrics.total_api_endpoints), f"{metrics.api_coverage:.1f}%")
        
        console.print(table)
        
        # Display additional metrics
        console.print("\n[dim]Additional Metrics:[/dim]")
        console.print(f"• Generation Time: {metrics.generation_time:.2f} seconds")
        console.print(f"• Example Validity: {metrics.example_validity:.1f}%")
        console.print(f"• Broken Links: {metrics.broken_links}")
        console.print(f"• Overall Coverage: {metrics.overall_coverage:.1f}%")
        
        # Display quality assessment
        console.print("\n[dim]Quality Assessment:[/dim]")
        if metrics.overall_coverage >= 90:
            console.print("• ✅ Excellent documentation coverage")
        elif metrics.overall_coverage >= 70:
            console.print("• ✅ Good documentation coverage")
        elif metrics.overall_coverage >= 50:
            console.print("• ⚠️  Moderate documentation coverage")
        else:
            console.print("• ❌ Poor documentation coverage")
        
    except Exception as e:
        console.print(f"❌ Error showing metrics: {e}", style="red")
        raise typer.Exit(1)


@app.command("config")
def config_docs(
    init: bool = typer.Option(False, "--init", help="Initialize documentation configuration"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    config_path: Path = typer.Option(Path("docs/config.yaml"), "--config-path", help="Configuration file path")
):
    """Manage documentation configuration"""
    if init:
        _init_config(config_path)
    elif show:
        _show_config(config_path)
    else:
        console.print("Use --init to create config or --show to view current config")


def _display_generation_results(docs, metrics: DocumentationMetrics, verbose: bool):
    """Display documentation generation results"""
    console.print("\n[dim]Generated Documentation:[/dim]")
    
    if docs.api_docs:
        console.print(f"• API Documentation: {len(docs.api_docs.endpoints)} endpoints, {len(docs.api_docs.models)} models")
    
    if docs.module_docs:
        console.print(f"• Module Documentation: {len(docs.module_docs)} modules")
        if verbose:
            for module in docs.module_docs:
                console.print(f"  - {module.name}: {len(module.classes)} classes, {len(module.functions)} functions")
    
    if docs.cli_docs:
        console.print(f"• CLI Documentation: {len(docs.cli_docs.commands)} commands")
    
    if docs.template_docs:
        console.print(f"• Template Documentation: {len(docs.template_docs.templates)} templates")
    
    if docs.user_guides:
        console.print(f"• User Guides: {len(docs.user_guides)} guides")
    
    console.print(f"\n[dim]Generated at: {docs.generated_at}[/dim]")


def _display_validation_results(results, detailed: bool = False):
    """Display validation results"""
    console.print("\n[dim]Validation Results:[/dim]")
    
    # Summary
    if results.is_valid:
        console.print("• ✅ Validation passed", style="green")
    else:
        console.print(f"• ❌ Validation failed ({len(results.errors)} errors)", style="red")
    
    if results.has_warnings:
        console.print(f"• ⚠️  {len(results.warnings)} warnings", style="yellow")
    
    console.print(f"• 📊 Coverage: {results.coverage_percentage:.1f}%")
    
    # Detailed results
    if detailed:
        if results.errors:
            console.print("\n[red]Errors:[/red]")
            for error in results.errors:
                console.print(f"• {error.type}: {error.message}")
                if error.suggestion:
                    console.print(f"  💡 {error.suggestion}")
        
        if results.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in results.warnings:
                console.print(f"• {warning.type}: {warning.message}")
                if warning.suggestion:
                    console.print(f"  💡 {warning.suggestion}")


def _init_config(config_path: Path):
    """Initialize documentation configuration"""
    config_content = """documentation:
  sources:
    modules:
      path: src/writeit
      patterns: ["**/*.py"]
      exclude: ["**/__pycache__/**", "**/tests/**"]
      
    api:
      spec_path: openapi.json
      include_examples: true
      
    cli:
      app_module: writeit.cli.main:app
      
    templates:
      path: templates
      formats: ["yaml"]
      
    tests:
      path: tests
      extract_examples: true
      
  outputs:
    markdown:
      output_dir: docs/generated/markdown
      
    html:
      output_dir: docs/site
      theme: material
      
    pdf:
      output_file: docs/writeit-documentation.pdf
      
  validation:
    check_links: true
    validate_examples: true
    check_completeness: true
    
  deployment:
    github_pages: true
    auto_deploy: true
"""
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(config_content)
        console.print(f"✅ Configuration initialized at {config_path}")
    except Exception as e:
        console.print(f"❌ Error initializing configuration: {e}", style="red")
        raise typer.Exit(1)


def _show_config(config_path: Path):
    """Show current configuration"""
    if config_path.exists():
        console.print(f"Configuration file: {config_path}")
        with open(config_path, 'r') as f:
            console.print(f.read())
    else:
        console.print("No configuration file found. Use --init to create one.")


if __name__ == "__main__":
    app()