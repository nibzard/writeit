"""Modern pipeline commands using CQRS architecture.

Updated pipeline commands that use the new BaseCommand infrastructure
and PipelineApplicationService for domain-driven design.
"""

import typer
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from ..base_command import BaseCommand, CommandContext, ValidationCommandError
from ..error_handler import handle_cli_error
from ..output_formatter import OutputFormat
from ....application.services import (
    PipelineApplicationService,
    PipelineExecutionRequest,
    PipelineCreationRequest,
    PipelineListingOptions,
    PipelineExecutionMode,
    PipelineSource,
)


# Create Typer app for pipeline commands
app = typer.Typer(
    name="pipeline", 
    help="Manage and execute WriteIt pipelines with domain-driven architecture",
    rich_markup_mode="rich"
)


class ListPipelinesCommand(BaseCommand):
    """Command to list available pipelines."""
    
    def __init__(self, context: CommandContext, include_global: bool = True, 
                 filter_pattern: Optional[str] = None):
        super().__init__(context)
        self.include_global = include_global
        self.filter_pattern = filter_pattern
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        # No validation needed for list command
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline listing."""
        pipeline_service = self.get_pipeline_service()
        
        # Create listing options
        options = PipelineListingOptions(
            workspace_name=self.context.workspace_name,
            include_global=self.include_global,
            include_local=True,
            filter_pattern=self.filter_pattern
        )
        
        # Get pipelines
        pipelines = await pipeline_service.list_pipelines(options)
        
        return {
            "pipelines": pipelines,
            "total_count": len(pipelines)
        }


class RunPipelineCommand(BaseCommand):
    """Command to execute a pipeline."""
    
    def __init__(self, context: CommandContext, pipeline_name: str, 
                 template_path: Optional[Path] = None, inputs: Optional[Dict[str, Any]] = None,
                 mode: PipelineExecutionMode = PipelineExecutionMode.CLI):
        super().__init__(context)
        self.pipeline_name = pipeline_name
        self.template_path = template_path
        self.inputs = inputs or {}
        self.mode = mode
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.pipeline_name or not self.pipeline_name.strip():
            raise ValidationCommandError("Pipeline name cannot be empty")
        
        if self.template_path and not self.template_path.exists():
            raise ValidationCommandError(f"Template file not found: {self.template_path}")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline with streaming results."""
        pipeline_service = self.get_pipeline_service()
        
        # Determine source based on template path
        source = PipelineSource.LOCAL if self.template_path else PipelineSource.WORKSPACE
        
        # Create execution request
        request = PipelineExecutionRequest(
            pipeline_name=self.pipeline_name,
            workspace_name=self.context.workspace_name,
            source=source,
            mode=self.mode,
            inputs=self.inputs,
            template_path=self.template_path
        )
        
        # Execute pipeline with progress tracking
        results = []
        final_result = None
        
        # Create progress bar
        with self.console.status(f"[bold green]Executing pipeline '{self.pipeline_name}'...") as status:
            async for result in pipeline_service.execute_pipeline(request):
                results.append(result)
                final_result = result
                
                # Update status based on execution progress
                if hasattr(result, 'pipeline_run') and hasattr(result.pipeline_run, 'status'):
                    status.update(f"[bold green]Pipeline status: {result.pipeline_run.status.value}")
        
        return {
            "pipeline_name": self.pipeline_name,
            "execution_results": results,
            "final_result": final_result,
            "total_steps": len(results)
        }


class ValidatePipelineCommand(BaseCommand):
    """Command to validate a pipeline template."""
    
    def __init__(self, context: CommandContext, pipeline_name: str, detailed: bool = False):
        super().__init__(context)
        self.pipeline_name = pipeline_name
        self.detailed = detailed
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.pipeline_name or not self.pipeline_name.strip():
            raise ValidationCommandError("Pipeline name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline validation."""
        pipeline_service = self.get_pipeline_service()
        
        # Validate pipeline
        validation_result = await pipeline_service.validate_pipeline(
            self.pipeline_name,
            workspace_name=self.context.workspace_name,
            detailed=self.detailed
        )
        
        return {
            "pipeline_name": self.pipeline_name,
            "validation_result": validation_result,
            "is_valid": validation_result["is_valid"]
        }


class CreatePipelineCommand(BaseCommand):
    """Command to create a new pipeline template."""
    
    def __init__(self, context: CommandContext, name: str, description: str,
                 template_path: Optional[Path] = None, content: Optional[str] = None):
        super().__init__(context)
        self.name = name
        self.description = description
        self.template_path = template_path
        self.content = content
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Pipeline name cannot be empty")
        
        if not self.description or not self.description.strip():
            raise ValidationCommandError("Pipeline description cannot be empty")
        
        if not self.content and not self.template_path:
            raise ValidationCommandError("Either content or template_path must be provided")
        
        if self.template_path and not self.template_path.exists():
            raise ValidationCommandError(f"Template file not found: {self.template_path}")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline creation."""
        pipeline_service = self.get_pipeline_service()
        
        # Create pipeline request
        request = PipelineCreationRequest(
            name=self.name,
            description=self.description,
            workspace_name=self.context.workspace_name,
            template_content=self.content,
            template_path=self.template_path
        )
        
        # Create pipeline
        template = await pipeline_service.create_pipeline(request)
        
        return {
            "pipeline_name": template.name,
            "description": template.description,
            "created_at": template.created_at,
            "status": "created"
        }


class PipelineAnalyticsCommand(BaseCommand):
    """Command to get pipeline analytics."""
    
    def __init__(self, context: CommandContext, pipeline_name: str):
        super().__init__(context)
        self.pipeline_name = pipeline_name
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.pipeline_name or not self.pipeline_name.strip():
            raise ValidationCommandError("Pipeline name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline analytics retrieval."""
        pipeline_service = self.get_pipeline_service()
        
        # Get pipeline analytics
        analytics = await pipeline_service.get_pipeline_analytics(
            self.pipeline_name,
            workspace_name=self.context.workspace_name
        )
        
        return {
            "pipeline_name": self.pipeline_name,
            "analytics": analytics
        }


# Typer command functions that use the new command classes

@app.command(name="list")
def list_pipelines(
    include_global: bool = typer.Option(True, "--global", "-g", help="Include global pipelines"),
    filter_pattern: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter pipelines by pattern"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    List available pipeline templates.

    [bold cyan]Examples:[/bold cyan]

    List all pipelines:
      [dim]$ writeit pipeline list[/dim]

    List workspace-only pipelines:
      [dim]$ writeit pipeline list --no-global[/dim]

    Filter pipelines:
      [dim]$ writeit pipeline list --filter "article*"[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ListPipelinesCommand(context, include_global, filter_pattern)
    
    try:
        result = command.run()
        
        if not result["pipelines"]:
            command.print_info("No pipelines found. Create one with: writeit pipeline create <name>")
            return
        
        # Display results
        if output_format == "table":
            command.format_output(result["pipelines"], "Available Pipelines")
            console.print(f"\nTotal pipelines: {result['total_count']}")
        else:
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "pipeline list", console, workspace_name=workspace)
        raise typer.Exit(exit_code)


@app.command()
def run(
    pipeline_name: str = typer.Argument(..., help="Name of the pipeline to execute"),
    template_path: Optional[Path] = typer.Option(None, "--template", "-t", help="Path to pipeline template file"),
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="JSON file with input values"),
    mode: str = typer.Option("cli", "--mode", "-m", help="Execution mode: cli, tui, api"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Execute a pipeline.

    [bold cyan]Examples:[/bold cyan]

    Run a pipeline:
      [dim]$ writeit pipeline run article-generator[/dim]

    Run with template file:
      [dim]$ writeit pipeline run article-generator --template ./my-template.yaml[/dim]

    Run with input file:
      [dim]$ writeit pipeline run article-generator --input ./inputs.json[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    # Load inputs from file if provided
    inputs = {}
    if input_file:
        try:
            import json
            inputs = json.loads(input_file.read_text())
        except Exception as e:
            console.print(f"[red]Error reading input file: {e}[/red]")
            raise typer.Exit(1)
    
    # Convert mode string to enum
    try:
        execution_mode = PipelineExecutionMode(mode)
    except ValueError:
        console.print(f"[red]Invalid execution mode: {mode}[/red]")
        console.print("Valid modes: cli, tui, api, background")
        raise typer.Exit(1)
    
    command = RunPipelineCommand(context, pipeline_name, template_path, inputs, execution_mode)
    
    try:
        result = command.run()
        
        # Display execution results
        from ..output_formatter import CLIOutputFormatter
        formatter = CLIOutputFormatter(console, OutputFormat(output_format))
        
        if result["final_result"] and output_format == "table":
            formatter.print_pipeline_execution_result(result["final_result"])
        else:
            command.format_output(result)
        
        command.print_success(f"Pipeline '{pipeline_name}' executed successfully")
    
    except Exception as e:
        exit_code = handle_cli_error(e, "pipeline run", console, 
                                  workspace_name=workspace, pipeline_name=pipeline_name)
        raise typer.Exit(exit_code)


@app.command()
def validate(
    pipeline_name: str = typer.Argument(..., help="Name of the pipeline to validate"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed validation information"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Validate a pipeline template.

    [bold cyan]Examples:[/bold cyan]

    Validate a pipeline:
      [dim]$ writeit pipeline validate article-generator[/dim]

    Detailed validation:
      [dim]$ writeit pipeline validate article-generator --detailed[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ValidatePipelineCommand(context, pipeline_name, detailed)
    
    try:
        result = command.run()
        
        # Display validation results
        if result["is_valid"]:
            command.print_success(f"Pipeline '{pipeline_name}' is valid")
        else:
            command.print_warning(f"Pipeline '{pipeline_name}' has validation issues")
        
        if output_format == "table" and detailed:
            validation_result = result["validation_result"]
            
            # Display template validation
            if "template_validation" in validation_result:
                command.format_output(validation_result["template_validation"], "Template Validation")
            
            # Display dependency validation
            if "dependency_validation" in validation_result:
                command.format_output(validation_result["dependency_validation"], "Dependency Validation")
            
            # Display recommendations
            if "recommendations" in validation_result and validation_result["recommendations"]:
                command.format_output(validation_result["recommendations"], "Recommendations")
        else:
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "pipeline validate", console,
                                  workspace_name=workspace, pipeline_name=pipeline_name)
        raise typer.Exit(exit_code)


@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the pipeline to create"),
    description: str = typer.Argument(..., help="Description of the pipeline"),
    template_path: Optional[Path] = typer.Option(None, "--template", "-t", help="Path to pipeline template file"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Pipeline content as string"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Create a new pipeline template.

    [bold cyan]Examples:[/bold cyan]

    Create from template file:
      [dim]$ writeit pipeline create my-pipeline "My pipeline description" --template ./template.yaml[/dim]

    Create with inline content:
      [dim]$ writeit pipeline create my-pipeline "My pipeline description" --content "..."[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = CreatePipelineCommand(context, name, description, template_path, content)
    
    try:
        result = command.run()
        
        command.print_success(f"Pipeline '{name}' created successfully")
        
        if output_format != "table":
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "pipeline create", console,
                                  workspace_name=workspace, pipeline_name=name)
        raise typer.Exit(exit_code)


@app.command()
def analytics(
    pipeline_name: str = typer.Argument(..., help="Name of the pipeline"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Show pipeline analytics and performance metrics.

    [bold cyan]Examples:[/bold cyan]

    Show pipeline analytics:
      [dim]$ writeit pipeline analytics article-generator[/dim]

    Show as JSON:
      [dim]$ writeit pipeline analytics article-generator --format json[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = PipelineAnalyticsCommand(context, pipeline_name)
    
    try:
        result = command.run()
        
        # Display analytics
        if output_format == "table":
            analytics = result["analytics"]
            
            # Display execution history
            if "execution_history" in analytics:
                command.format_output(analytics["execution_history"], "Execution History")
            
            # Display performance metrics
            if "performance_metrics" in analytics:
                command.format_output(analytics["performance_metrics"], "Performance Metrics")
            
            # Display recommendations
            if "recommendations" in analytics and analytics["recommendations"]:
                command.format_output(analytics["recommendations"], "Recommendations")
        else:
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "pipeline analytics", console,
                                  workspace_name=workspace, pipeline_name=pipeline_name)
        raise typer.Exit(exit_code)