"""Modern template commands using CQRS architecture.

Updated template commands that use the new BaseCommand infrastructure
and ContentApplicationService for domain-driven design.
"""

import typer
from typing import Optional, Dict, Any, List
from pathlib import Path
from rich.console import Console

from ..base_command import BaseCommand, CommandContext, ValidationCommandError
from ..error_handler import handle_cli_error
from ..output_formatter import OutputFormat
from ....application.services import (
    ContentApplicationService,
    TemplateCreationRequest,
    TemplateUpdateRequest,
    TemplateListingOptions,
    TemplateValidationRequest,
)
from ....domains.content.value_objects import TemplateName, ContentType


# Create Typer app for template commands
app = typer.Typer(
    name="template", 
    help="Manage WriteIt content templates with domain-driven architecture",
    rich_markup_mode="rich"
)


class ListTemplatesCommand(BaseCommand):
    """Command to list available templates."""
    
    def __init__(self, context: CommandContext, include_global: bool = True, 
                 content_type: Optional[str] = None, search_pattern: Optional[str] = None):
        super().__init__(context)
        self.include_global = include_global
        self.content_type = ContentType(content_type) if content_type else None
        self.search_pattern = search_pattern
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        # No specific validation needed for list command
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """Execute template listing."""
        content_service = self.get_content_service()
        
        try:
            listing_options = TemplateListingOptions(
                workspace_name=self.context.get_workspace_name(),
                include_global=self.include_global,
                content_type=self.content_type,
                search_pattern=self.search_pattern
            )
            
            result = await content_service.list_templates(listing_options)
            
            if result.success:
                templates_data = [
                    {
                        "name": template.name.value,
                        "type": template.content_type.value,
                        "description": template.description or "No description",
                        "scope": template.scope,
                        "created": template.created_at.strftime("%Y-%m-%d %H:%M:%S") if template.created_at else "Unknown"
                    }
                    for template in result.templates
                ]
                
                if not templates_data:
                    self.print_info("No templates found matching the criteria")
                    return {"status": "success", "templates": [], "count": 0}
                
                self.format_output(templates_data, f"Found {len(templates_data)} templates")
                
                return {
                    "status": "success",
                    "templates": templates_data,
                    "count": len(templates_data),
                    "criteria": {
                        "include_global": self.include_global,
                        "content_type": self.content_type.value if self.content_type else None,
                        "search_pattern": self.search_pattern
                    }
                }
            else:
                self.print_warning(f"Failed to list templates: {result.error_message}")
                return {"status": "error", "message": result.error_message}
                
        except Exception as e:
            self.print_error(f"Error listing templates: {str(e)}")
            return {"status": "error", "message": str(e)}


class CreateTemplateCommand(BaseCommand):
    """Command to create a new template."""
    
    def __init__(self, context: CommandContext, name: str, content_type: str,
                 description: Optional[str] = None, template_file: Optional[Path] = None):
        super().__init__(context)
        self.name = name
        self.content_type = content_type
        self.description = description
        self.template_file = template_file
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Template name cannot be empty")
        
        try:
            TemplateName(self.name)
        except ValueError as e:
            raise ValidationCommandError(f"Invalid template name: {str(e)}")
        
        try:
            ContentType(self.content_type)
        except ValueError:
            valid_types = [t.value for t in ContentType]
            raise ValidationCommandError(f"Invalid content type '{self.content_type}'. Valid types: {', '.join(valid_types)}")
        
        if self.template_file and not self.template_file.exists():
            raise ValidationCommandError(f"Template file not found: {self.template_file}")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute template creation."""
        content_service = self.get_content_service()
        
        try:
            # Read template content if file provided
            template_content = ""
            if self.template_file:
                template_content = self.template_file.read_text(encoding='utf-8')
            
            creation_request = TemplateCreationRequest(
                name=TemplateName(self.name),
                content_type=ContentType(self.content_type),
                description=self.description,
                content=template_content,
                workspace_name=self.context.get_workspace_name()
            )
            
            result = await content_service.create_template(creation_request)
            
            if result.success:
                self.print_success(f"Template '{self.name}' created successfully")
                
                template_info = {
                    "name": result.template.name.value,
                    "type": result.template.content_type.value,
                    "description": result.template.description,
                    "content_length": len(result.template.content),
                    "workspace": result.template.workspace_name.value if result.template.workspace_name else "global"
                }
                
                if self.context.output_format != "table":
                    self.format_output(template_info, "Template Created")
                
                return {"status": "success", "template": template_info}
            else:
                self.print_error(f"Failed to create template: {result.error_message}")
                return {"status": "error", "message": result.error_message}
                
        except Exception as e:
            self.print_error(f"Error creating template: {str(e)}")
            return {"status": "error", "message": str(e)}


class ValidateTemplateCommand(BaseCommand):
    """Command to validate a template."""
    
    def __init__(self, context: CommandContext, name: str, detailed: bool = False):
        super().__init__(context)
        self.name = name
        self.detailed = detailed
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Template name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute template validation."""
        content_service = self.get_content_service()
        
        try:
            validation_request = TemplateValidationRequest(
                name=TemplateName(self.name),
                workspace_name=self.context.get_workspace_name(),
                detailed=self.detailed
            )
            
            result = await content_service.validate_template(validation_request)
            
            if result.success:
                if result.is_valid:
                    self.print_success(f"Template '{self.name}' is valid")
                else:
                    self.print_warning(f"Template '{self.name}' has validation issues")
                
                validation_info = {
                    "template_name": self.name,
                    "is_valid": result.is_valid,
                    "error_count": len(result.errors),
                    "warning_count": len(result.warnings),
                }
                
                if self.detailed:
                    validation_info.update({
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "suggestions": result.suggestions
                    })
                
                if result.errors:
                    self.console.print("\n[red]Errors:[/red]")
                    for error in result.errors:
                        self.console.print(f"  ❌ {error}")
                
                if result.warnings:
                    self.console.print("\n[yellow]Warnings:[/yellow]")
                    for warning in result.warnings:
                        self.console.print(f"  ⚠️ {warning}")
                
                if result.suggestions and self.detailed:
                    self.console.print("\n[cyan]Suggestions:[/cyan]")
                    for suggestion in result.suggestions:
                        self.console.print(f"  💡 {suggestion}")
                
                return {"status": "success", "validation": validation_info}
            else:
                self.print_error(f"Failed to validate template: {result.error_message}")
                return {"status": "error", "message": result.error_message}
                
        except Exception as e:
            self.print_error(f"Error validating template: {str(e)}")
            return {"status": "error", "message": str(e)}


class DeleteTemplateCommand(BaseCommand):
    """Command to delete a template."""
    
    def __init__(self, context: CommandContext, name: str, force: bool = False):
        super().__init__(context)
        self.name = name
        self.force = force
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Template name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute template deletion."""
        content_service = self.get_content_service()
        
        try:
            # Confirm deletion unless forced
            if not self.force and not self.confirm_action(f"Delete template '{self.name}'?"):
                return {"status": "cancelled", "message": "Deletion cancelled by user"}
            
            result = await content_service.delete_template(
                TemplateName(self.name),
                workspace_name=self.context.get_workspace_name()
            )
            
            if result.success:
                self.print_success(f"Template '{self.name}' deleted successfully")
                return {"status": "success", "template_name": self.name}
            else:
                self.print_error(f"Failed to delete template: {result.error_message}")
                return {"status": "error", "message": result.error_message}
                
        except Exception as e:
            self.print_error(f"Error deleting template: {str(e)}")
            return {"status": "error", "message": str(e)}


# Command wrapper functions for Typer
@app.command("list")
def list_templates(
    include_global: bool = typer.Option(True, "--global/--local", help="Include global templates"),
    content_type: Optional[str] = typer.Option(None, "--type", help="Filter by content type"),
    search: Optional[str] = typer.Option(None, "--search", help="Search pattern"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """List available templates."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ListTemplatesCommand(
        context=context,
        include_global=include_global,
        content_type=content_type,
        search_pattern=search
    )
    
    with handle_cli_error(console, verbose):
        command.run()


@app.command("create")
def create_template(
    name: str = typer.Argument(..., help="Template name"),
    content_type: str = typer.Argument(..., help="Content type (pipeline, style, etc.)"),
    description: Optional[str] = typer.Option(None, "--description", help="Template description"),
    template_file: Optional[Path] = typer.Option(None, "--file", help="Template file to import"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Create a new template."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = CreateTemplateCommand(
        context=context,
        name=name,
        content_type=content_type,
        description=description,
        template_file=template_file
    )
    
    with handle_cli_error(console, verbose):
        command.run()


@app.command("validate")
def validate_template(
    name: str = typer.Argument(..., help="Template name to validate"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Validate a template."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ValidateTemplateCommand(
        context=context,
        name=name,
        detailed=detailed
    )
    
    with handle_cli_error(console, verbose):
        command.run()


@app.command("delete")
def delete_template(
    name: str = typer.Argument(..., help="Template name to delete"),
    force: bool = typer.Option(False, "--force", help="Force deletion without confirmation"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """Delete a template."""
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        force=force,
        output_format=output_format,
        console=console
    )
    
    command = DeleteTemplateCommand(
        context=context,
        name=name,
        force=force
    )
    
    with handle_cli_error(console, verbose):
        command.run()