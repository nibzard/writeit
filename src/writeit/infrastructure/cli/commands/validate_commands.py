"""Modern validation commands using CQRS architecture.

Updated validation commands that use the new BaseCommand infrastructure
and application services for domain-driven design validation.
"""

import typer
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..base_command import BaseCommand, CommandContext, ValidationCommandError
from ..error_handler import handle_cli_error
from ..output_formatter import OutputFormat
from ....application.services import (
    ContentApplicationService,
    PipelineApplicationService,
    TemplateValidationRequest,
    PipelineValidationRequest,
    ValidationScope,
)
from ....domains.content.value_objects import TemplateName, ContentType
from ....domains.pipeline.value_objects import PipelineId


# Create Typer app for validation commands
app = typer.Typer(
    name="validate", 
    help="Validate WriteIt templates, pipelines, and configurations",
    rich_markup_mode="rich"
)


class ValidateTemplatesCommand(BaseCommand):
    """Command to validate templates."""
    
    def __init__(self, context: CommandContext, template_name: Optional[str] = None,
                 scope: str = "workspace", detailed: bool = False, 
                 content_type: Optional[str] = None):
        super().__init__(context)
        self.template_name = template_name
        self.scope = ValidationScope(scope)
        self.detailed = detailed
        self.content_type = ContentType(content_type) if content_type else None
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if self.template_name and not self.template_name.strip():
            raise ValidationCommandError("Template name cannot be empty")
        
        if self.content_type:
            try:
                ContentType(self.content_type.value)
            except ValueError:
                valid_types = [t.value for t in ContentType]
                raise ValidationCommandError(f"Invalid content type. Valid types: {', '.join(valid_types)}")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute template validation."""
        content_service = self.get_content_service()
        
        try:
            validation_results = []
            
            if self.template_name:
                # Validate specific template
                validation_request = TemplateValidationRequest(
                    name=TemplateName(self.template_name),
                    workspace_name=self.context.get_workspace_name(),
                    detailed=self.detailed
                )
                
                result = await content_service.validate_template(validation_request)
                validation_results.append(result)
                
            else:
                # Validate all templates in scope
                listing_options = {
                    "workspace_name": self.context.get_workspace_name(),
                    "include_global": self.scope == ValidationScope.GLOBAL,
                    "content_type": self.content_type
                }
                
                templates_result = await content_service.list_templates(listing_options)
                
                if templates_result.success:
                    for template in templates_result.templates:
                        validation_request = TemplateValidationRequest(
                            name=template.name,
                            workspace_name=self.context.get_workspace_name(),
                            detailed=self.detailed
                        )
                        
                        result = await content_service.validate_template(validation_request)
                        validation_results.append(result)
                else:
                    self.print_error(f"Failed to list templates: {templates_result.error_message}")
                    return {"status": "error", "message": templates_result.error_message}
            
            # Process results
            valid_count = sum(1 for r in validation_results if r.success and r.is_valid)
            invalid_count = len(validation_results) - valid_count
            
            summary = {
                "status": "success",
                "total_templates": len(validation_results),
                "valid_templates": valid_count,
                "invalid_templates": invalid_count,
                "validation_results": []
            }
            
            # Display results
            if self.context.output_format == "table":
                self._display_validation_table(validation_results)
            
            # Collect detailed results
            for result in validation_results:
                template_result = {
                    "template_name": result.template_name if hasattr(result, 'template_name') else "Unknown",
                    "is_valid": result.is_valid if result.success else False,
                    "error_count": len(result.errors) if result.success else 1,
                    "warning_count": len(result.warnings) if result.success else 0,
                }
                
                if self.detailed and result.success:
                    template_result.update({
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "suggestions": result.suggestions
                    })
                
                summary["validation_results"].append(template_result)
            
            # Print summary
            if invalid_count == 0:
                self.print_success(f"All {valid_count} templates are valid")
            else:
                self.print_warning(f"{invalid_count} templates have validation issues")
            
            return summary
            
        except Exception as e:
            self.print_error(f"Error validating templates: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _display_validation_table(self, results: List[Any]) -> None:
        """Display validation results in table format."""
        table = Table(title="Template Validation Results")
        table.add_column("Template", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Errors", style="red")
        table.add_column("Warnings", style="yellow")
        
        for result in results:
            if result.success:
                status = "✅ Valid" if result.is_valid else "❌ Invalid"
                error_count = str(len(result.errors))
                warning_count = str(len(result.warnings))
                template_name = getattr(result, 'template_name', 'Unknown')
            else:
                status = "❌ Error"
                error_count = "1"
                warning_count = "0"
                template_name = "Unknown"
            
            table.add_row(template_name, status, error_count, warning_count)
        
        self.console.print(table)


class ValidatePipelinesCommand(BaseCommand):
    """Command to validate pipelines."""
    
    def __init__(self, context: CommandContext, pipeline_name: Optional[str] = None,
                 scope: str = "workspace", detailed: bool = False):
        super().__init__(context)
        self.pipeline_name = pipeline_name
        self.scope = ValidationScope(scope)
        self.detailed = detailed
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if self.pipeline_name and not self.pipeline_name.strip():
            raise ValidationCommandError("Pipeline name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute pipeline validation."""
        pipeline_service = self.get_pipeline_service()
        
        try:
            validation_results = []
            
            if self.pipeline_name:
                # Validate specific pipeline
                validation_request = PipelineValidationRequest(
                    pipeline_id=PipelineId(self.pipeline_name),
                    workspace_name=self.context.get_workspace_name(),
                    detailed=self.detailed
                )
                
                result = await pipeline_service.validate_pipeline(validation_request)
                validation_results.append(result)
                
            else:
                # Validate all pipelines in scope
                listing_options = {
                    "workspace_name": self.context.get_workspace_name(),
                    "include_global": self.scope == ValidationScope.GLOBAL
                }
                
                pipelines_result = await pipeline_service.list_pipelines(listing_options)
                
                if pipelines_result.success:
                    for pipeline in pipelines_result.pipelines:
                        validation_request = PipelineValidationRequest(
                            pipeline_id=pipeline.id,
                            workspace_name=self.context.get_workspace_name(),
                            detailed=self.detailed
                        )
                        
                        result = await pipeline_service.validate_pipeline(validation_request)
                        validation_results.append(result)
                else:
                    self.print_error(f"Failed to list pipelines: {pipelines_result.error_message}")
                    return {"status": "error", "message": pipelines_result.error_message}
            
            # Process results similar to template validation
            valid_count = sum(1 for r in validation_results if r.success and r.is_valid)
            invalid_count = len(validation_results) - valid_count
            
            summary = {
                "status": "success",
                "total_pipelines": len(validation_results),
                "valid_pipelines": valid_count,
                "invalid_pipelines": invalid_count,
                "validation_results": []
            }
            
            # Display results
            if self.context.output_format == "table":
                self._display_pipeline_validation_table(validation_results)
            
            # Collect detailed results
            for result in validation_results:
                pipeline_result = {
                    "pipeline_name": result.pipeline_name if hasattr(result, 'pipeline_name') else "Unknown",
                    "is_valid": result.is_valid if result.success else False,
                    "error_count": len(result.errors) if result.success else 1,
                    "warning_count": len(result.warnings) if result.success else 0,
                }
                
                if self.detailed and result.success:
                    pipeline_result.update({
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "suggestions": result.suggestions
                    })
                
                summary["validation_results"].append(pipeline_result)
            
            # Print summary
            if invalid_count == 0:
                self.print_success(f"All {valid_count} pipelines are valid")
            else:
                self.print_warning(f"{invalid_count} pipelines have validation issues")
            
            return summary
            
        except Exception as e:
            self.print_error(f"Error validating pipelines: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _display_pipeline_validation_table(self, results: List[Any]) -> None:
        """Display pipeline validation results in table format."""
        table = Table(title="Pipeline Validation Results")
        table.add_column("Pipeline", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Errors", style="red")
        table.add_column("Warnings", style="yellow")
        
        for result in results:
            if result.success:
                status = "✅ Valid" if result.is_valid else "❌ Invalid"
                error_count = str(len(result.errors))
                warning_count = str(len(result.warnings))
                pipeline_name = getattr(result, 'pipeline_name', 'Unknown')
            else:
                status = "❌ Error"
                error_count = "1"
                warning_count = "0"
                pipeline_name = "Unknown"
            
            table.add_row(pipeline_name, status, error_count, warning_count)
        
        self.console.print(table)


class ValidateAllCommand(BaseCommand):
    """Command to validate all resources in workspace."""
    
    def __init__(self, context: CommandContext, scope: str = "workspace", detailed: bool = False):
        super().__init__(context)
        self.scope = ValidationScope(scope)
        self.detailed = detailed
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        # No specific validation needed
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """Execute comprehensive validation."""
        try:
            # Validate templates
            template_command = ValidateTemplatesCommand(
                context=self.context,
                scope=self.scope.value,
                detailed=self.detailed
            )
            template_results = await template_command.execute()
            
            # Validate pipelines
            pipeline_command = ValidatePipelinesCommand(
                context=self.context,
                scope=self.scope.value,
                detailed=self.detailed
            )
            pipeline_results = await pipeline_command.execute()
            
            # Combine results
            total_errors = 0
            total_warnings = 0
            
            if template_results.get("status") == "success":
                total_errors += template_results.get("invalid_templates", 0)
                for result in template_results.get("validation_results", []):
                    total_warnings += result.get("warning_count", 0)
            
            if pipeline_results.get("status") == "success":
                total_errors += pipeline_results.get("invalid_pipelines", 0)
                for result in pipeline_results.get("validation_results", []):
                    total_warnings += result.get("warning_count", 0)
            
            summary = {
                "status": "success",
                "scope": self.scope.value,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "template_validation": template_results,
                "pipeline_validation": pipeline_results
            }
            
            # Print overall summary
            if total_errors == 0:
                self.print_success("All resources are valid!")
            else:
                self.print_warning(f"Found {total_errors} validation errors and {total_warnings} warnings")
            
            return summary
            
        except Exception as e:
            self.print_error(f"Error during comprehensive validation: {str(e)}")
            return {"status": "error", "message": str(e)}


# Command wrapper functions for Typer
@app.command("templates")
def validate_templates(
    template_name: Optional[str] = typer.Argument(None, help="Specific template name to validate"),
    scope: str = typer.Option("workspace", "--scope", help="Validation scope (workspace, global, all)"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results"),
    content_type: Optional[str] = typer.Option(None, "--type", help="Filter by content type"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Validate templates."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ValidateTemplatesCommand(
        context=context,
        template_name=template_name,
        scope=scope,
        detailed=detailed,
        content_type=content_type
    )
    
    with handle_cli_error(console, verbose):
        command.run()


@app.command("pipelines")
def validate_pipelines(
    pipeline_name: Optional[str] = typer.Argument(None, help="Specific pipeline name to validate"),
    scope: str = typer.Option("workspace", "--scope", help="Validation scope (workspace, global, all)"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Validate pipelines."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ValidatePipelinesCommand(
        context=context,
        pipeline_name=pipeline_name,
        scope=scope,
        detailed=detailed
    )
    
    with handle_cli_error(console, verbose):
        command.run()


@app.command("all")
def validate_all(
    scope: str = typer.Option("workspace", "--scope", help="Validation scope (workspace, global, all)"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Validate all resources in workspace."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ValidateAllCommand(
        context=context,
        scope=scope,
        detailed=detailed
    )
    
    with handle_cli_error(console, verbose):
        command.run()


# Default command (validate all)
@app.callback(invoke_without_command=True)
def validate_default(
    ctx: typer.Context,
    scope: str = typer.Option("workspace", "--scope", help="Validation scope (workspace, global, all)"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Validate all resources (default command)."""
    if ctx.invoked_subcommand is None:
        validate_all(scope, detailed, workspace_name, verbose, output_format)