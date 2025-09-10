# ABOUTME: Template management commands for WriteIt CLI
# ABOUTME: Handle creation, listing, and copying of pipeline templates

import typer
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.workspace.template_manager import TemplateManager, TemplateType, TemplateScope
from writeit.workspace.config import get_active_workspace
from writeit.cli.output import (
    console, print_success, print_error, print_warning,
    create_pipeline_table
)
from writeit.cli.completion import complete_template_name, complete_workspace_name
from writeit.cli.app import get_workspace_override


app = typer.Typer(
    name="template", 
    help="Manage pipeline templates",
    rich_markup_mode="rich"
)


def get_workspace_manager() -> Workspace:
    """Get workspace manager and ensure WriteIt is initialized."""
    workspace_manager = Workspace()
    
    if not workspace_manager.home_dir.exists():
        print_error(
            "WriteIt not initialized. Run 'writeit init' first.",
            "Initialization Required"
        )
        raise typer.Exit(1)
    
    return workspace_manager


def get_template_manager() -> TemplateManager:
    """Get template manager with workspace."""
    workspace_manager = get_workspace_manager()
    return TemplateManager(workspace_manager)


@app.command()
def create(
    name: str = typer.Argument(
        ...,
        help="Template name (without .yaml extension)"
    ),
    workspace_scope: bool = typer.Option(
        True,
        "--workspace/--global",
        help="Create in workspace scope (default) or global scope"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace-name",
        "-w",
        autocompletion=complete_workspace_name,
        help="Target workspace (defaults to active workspace)"
    ),
    from_template: Optional[str] = typer.Option(
        None,
        "--from",
        "-f",
        autocompletion=complete_template_name,
        help="Copy from existing template"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--non-interactive",
        help="Use interactive template creation"
    )
):
    """
    Create a new pipeline template.
    
    Creates a template in workspace scope by default. Use --global to create
    a global template available across all workspaces.
    
    [bold cyan]Examples:[/bold cyan]
    
    Create workspace template:
      [dim]$ writeit template create my-article[/dim]
    
    Create global template:
      [dim]$ writeit template create my-article --global[/dim]
    
    Copy from existing template:
      [dim]$ writeit template create new-article --from tech-article[/dim]
    
    Create in specific workspace:
      [dim]$ writeit template create client-template --workspace-name client-x[/dim]
    """
    try:
        template_manager = get_template_manager()
        
        # Determine scope and workspace
        scope = TemplateScope.WORKSPACE if workspace_scope else TemplateScope.GLOBAL
        workspace_override = get_workspace_override()
        target_workspace = workspace or workspace_override
        
        if scope == TemplateScope.WORKSPACE and target_workspace is None:
            target_workspace = get_active_workspace()
        
        # Handle copying from existing template
        if from_template:
            try:
                location = template_manager.copy_template(
                    source_name=from_template,
                    dest_name=name,
                    template_type=TemplateType.PIPELINE,
                    dest_workspace=target_workspace,
                    dest_scope=scope
                )
                
                print_success(f"Template '{name}' created successfully!")
                console.print(f"[primary]Path:[/primary] [path]{location.path}[/path]")
                console.print(f"[primary]Scope:[/primary] {location.scope.value}")
                if location.workspace_name:
                    console.print(f"[primary]Workspace:[/primary] {location.workspace_name}")
                
                return
                
            except ValueError as e:
                print_error(f"Failed to copy template: {e}")
                raise typer.Exit(1)
        
        # Create new template
        if interactive:
            # Interactive template creation
            console.print(f"[primary]Creating new pipeline template: {name}[/primary]")
            console.print()
            
            # Gather template metadata
            description = typer.prompt("Description", default="")
            author = typer.prompt("Author", default="WriteIt User")
            tags = typer.prompt("Tags (comma-separated)", default="").split(",")
            tags = [tag.strip() for tag in tags if tag.strip()]
            
            # Create basic template content
            content = f'''# WriteIt Pipeline Template: {name.title()}
# 
# {description}

metadata:
  name: "{name.title()}"
  description: "{description}"
  version: "1.0.0"
  author: "{author}"
  created: "{typer.datetime.now().strftime('%Y-%m-%d')}"
  tags: {tags}
  estimated_time: "5-10 minutes"
  word_count_target: "800-1200 words"

# Default configuration values
defaults:
  models:
    primary: "gpt-4o-2024-08-06"
    secondary: "claude-3-5-sonnet-20241022"
    polish: "gpt-4o-mini-2024-07-18"
  word_count: "800-1200 words"

# Input fields that users will fill before starting
inputs:
  topic:
    type: "text"
    description: "The main topic or subject for the article"
    required: true
    placeholder: "Enter the article topic..."
  
  target_audience:
    type: "select"
    description: "Target audience for the content"
    options:
      - "General audience"
      - "Technical professionals"
      - "Business leaders"
      - "Students"
    default: "General audience"

# Pipeline execution steps
steps:
  - name: "outline"
    description: "Create article outline"
    model_preference: "primary"
    prompt_template: |
      Create a detailed outline for an article about {{{{ topic }}}}.
      
      Target audience: {{{{ target_audience }}}}
      Target length: {{{{ word_count }}}}
      
      Include:
      - Compelling introduction hook
      - 3-5 main sections with subsections
      - Key points for each section
      - Conclusion that ties everything together
      
      Make the outline engaging and well-structured.
    
    response_format: "markdown"
    user_feedback: true
    
  - name: "draft"
    description: "Write first draft"
    model_preference: "primary"
    prompt_template: |
      Based on the approved outline below, write a complete article about {{{{ topic }}}}.
      
      OUTLINE:
      {{{{ previous_responses.outline.selected }}}}
      
      Requirements:
      - Target audience: {{{{ target_audience }}}}
      - Target length: {{{{ word_count }}}}
      - Engaging and informative tone
      - Include specific examples where relevant
      - Strong introduction and conclusion
      
      Write the complete article in markdown format.
    
    response_format: "markdown"
    user_feedback: true
    
  - name: "polish"
    description: "Polish and refine"
    model_preference: "polish"
    prompt_template: |
      Polish and refine this article for publication. Focus on:
      
      - Grammar and style improvements
      - Flow and readability
      - Clarity and precision
      - Engaging language
      - Proper formatting
      
      ARTICLE TO POLISH:
      {{{{ previous_responses.draft.selected }}}}
      
      Return the polished version ready for publication.
    
    response_format: "markdown"
    user_feedback: false
'''
        else:
            # Non-interactive: create minimal template
            content = f'''# WriteIt Pipeline Template: {name.title()}

metadata:
  name: "{name.title()}"
  description: "Basic pipeline template"
  version: "1.0.0"

inputs:
  topic:
    type: "text"
    description: "Article topic"
    required: true

steps:
  - name: "generate"
    description: "Generate content"
    prompt_template: |
      Write about {{{{ topic }}}}.
    response_format: "markdown"
'''
        
        # Create the template
        try:
            location = template_manager.create_template(
                name=name,
                template_type=TemplateType.PIPELINE,
                content=content,
                workspace_name=target_workspace,
                scope=scope
            )
            
            print_success(f"Template '{name}' created successfully!")
            console.print(f"[primary]Path:[/primary] [path]{location.path}[/path]")
            console.print(f"[primary]Scope:[/primary] {location.scope.value}")
            if location.workspace_name:
                console.print(f"[primary]Workspace:[/primary] {location.workspace_name}")
                
        except ValueError as e:
            print_error(f"Failed to create template: {e}")
            raise typer.Exit(1)
            
    except Exception as e:
        print_error(f"Error creating template: {e}")
        raise typer.Exit(1)


@app.command(name="list")
def list_templates(
    scope: Optional[str] = typer.Option(
        "all",
        "--scope",
        "-s",
        help="Scope to list: 'workspace', 'global', or 'all'"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        autocompletion=complete_workspace_name,
        help="Target workspace (defaults to active workspace)"
    )
):
    """
    List available pipeline templates.
    
    Shows templates from workspace and global scopes with clear labeling.
    
    [bold cyan]Examples:[/bold cyan]
    
    List all templates:
      [dim]$ writeit template list[/dim]
    
    List workspace templates only:
      [dim]$ writeit template list --scope workspace[/dim]
    
    List global templates only:
      [dim]$ writeit template list --scope global[/dim]
    
    List templates for specific workspace:
      [dim]$ writeit template list --workspace client-x[/dim]
    """
    try:
        template_manager = get_template_manager()
        
        # Parse scope
        scope_map = {
            "workspace": TemplateScope.WORKSPACE,
            "global": TemplateScope.GLOBAL,
            "all": TemplateScope.AUTO
        }
        
        if scope not in scope_map:
            print_error(f"Invalid scope '{scope}'. Use 'workspace', 'global', or 'all'")
            raise typer.Exit(1)
        
        template_scope = scope_map[scope]
        
        # Determine workspace
        workspace_override = get_workspace_override()
        target_workspace = workspace or workspace_override
        
        if target_workspace is None and template_scope in (TemplateScope.WORKSPACE, TemplateScope.AUTO):
            target_workspace = get_active_workspace()
        
        # List templates
        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE,
            workspace_name=target_workspace,
            scope=template_scope
        )
        
        if not templates:
            print_warning("No pipeline templates found")
            return
        
        # Create table data
        table_data = []
        for template in templates:
            scope_label = "Global" if template.scope == TemplateScope.GLOBAL else f"Workspace ({template.workspace_name})"
            table_data.append((template.name, scope_label))
        
        # Display table
        table = create_pipeline_table(table_data, "Available Pipeline Templates")
        console.print(table)
        
        # Show usage hint
        console.print("\n[secondary]Use [primary]'writeit run <template-name>'[/primary] to execute a template.[/secondary]")
        
    except Exception as e:
        print_error(f"Error listing templates: {e}")
        raise typer.Exit(1)


@app.command()
def copy(
    source: str = typer.Argument(
        ...,
        autocompletion=complete_template_name,
        help="Source template name"
    ),
    destination: str = typer.Argument(
        ...,
        help="Destination template name"
    ),
    to_workspace: bool = typer.Option(
        True,
        "--to-workspace/--to-global",
        help="Copy to workspace scope (default) or global scope"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        autocompletion=complete_workspace_name,
        help="Target workspace (defaults to active workspace)"
    ),
    from_workspace: Optional[str] = typer.Option(
        None,
        "--from-workspace",
        autocompletion=complete_workspace_name,
        help="Source workspace (auto-detects if not specified)"
    )
):
    """
    Copy a template from one location to another.
    
    [bold cyan]Examples:[/bold cyan]
    
    Copy global template to workspace:
      [dim]$ writeit template copy tech-article my-article[/dim]
    
    Copy to global scope:
      [dim]$ writeit template copy my-article shared-article --to-global[/dim]
    
    Copy between workspaces:
      [dim]$ writeit template copy client-template --from-workspace client-a --workspace client-b[/dim]
    """
    try:
        template_manager = get_template_manager()
        
        # Determine target scope and workspace
        dest_scope = TemplateScope.WORKSPACE if to_workspace else TemplateScope.GLOBAL
        workspace_override = get_workspace_override()
        target_workspace = workspace or workspace_override
        
        if dest_scope == TemplateScope.WORKSPACE and target_workspace is None:
            target_workspace = get_active_workspace()
        
        # Copy template
        location = template_manager.copy_template(
            source_name=source,
            dest_name=destination,
            template_type=TemplateType.PIPELINE,
            source_workspace=from_workspace,
            dest_workspace=target_workspace,
            dest_scope=dest_scope
        )
        
        print_success("Template copied successfully!")
        console.print(f"[primary]Source:[/primary] {source}")
        console.print(f"[primary]Destination:[/primary] {destination}")
        console.print(f"[primary]Path:[/primary] [path]{location.path}[/path]")
        console.print(f"[primary]Scope:[/primary] {location.scope.value}")
        if location.workspace_name:
            console.print(f"[primary]Workspace:[/primary] {location.workspace_name}")
            
    except ValueError as e:
        print_error(f"Copy failed: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Error copying template: {e}")
        raise typer.Exit(1)