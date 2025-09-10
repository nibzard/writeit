# ABOUTME: Style management commands for WriteIt CLI  
# ABOUTME: Handle creation, listing, and copying of style primers

import typer
from typing import List, Optional
from pathlib import Path

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
    name="style", 
    help="Manage style primers",
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
        help="Style primer name (without .yaml extension)"
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
    from_style: Optional[str] = typer.Option(
        None,
        "--from",
        "-f",
        autocompletion=complete_template_name,
        help="Copy from existing style primer"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--non-interactive",
        help="Use interactive style creation"
    )
):
    """
    Create a new style primer.
    
    Creates a style primer in workspace scope by default. Use --global to create
    a global style available across all workspaces.
    
    [bold cyan]Examples:[/bold cyan]
    
    Create workspace style:
      [dim]$ writeit style create client-voice[/dim]
    
    Create global style:
      [dim]$ writeit style create professional-tone --global[/dim]
    
    Copy from existing style:
      [dim]$ writeit style create new-voice --from technical-expert[/dim]
    
    Create in specific workspace:
      [dim]$ writeit style create brand-voice --workspace-name client-x[/dim]
    """
    try:
        template_manager = get_template_manager()
        
        # Determine scope and workspace
        scope = TemplateScope.WORKSPACE if workspace_scope else TemplateScope.GLOBAL
        workspace_override = get_workspace_override()
        target_workspace = workspace or workspace_override
        
        if scope == TemplateScope.WORKSPACE and target_workspace is None:
            target_workspace = get_active_workspace()
        
        # Handle copying from existing style
        if from_style:
            try:
                location = template_manager.copy_template(
                    source_name=from_style,
                    dest_name=name,
                    template_type=TemplateType.STYLE,
                    dest_workspace=target_workspace,
                    dest_scope=scope
                )
                
                print_success(f"Style primer '{name}' created successfully!")
                console.print(f"[primary]Path:[/primary] [path]{location.path}[/path]")
                console.print(f"[primary]Scope:[/primary] {location.scope.value}")
                if location.workspace_name:
                    console.print(f"[primary]Workspace:[/primary] {location.workspace_name}")
                
                return
                
            except ValueError as e:
                print_error(f"Failed to copy style primer: {e}")
                raise typer.Exit(1)
        
        # Create new style primer
        if interactive:
            # Interactive style creation
            console.print(f"[primary]Creating new style primer: {name}[/primary]")
            console.print()
            
            # Gather style metadata
            description = typer.prompt("Description", default="")
            category = typer.prompt("Category", default="professional")
            personality = typer.prompt("Personality traits", default="Professional, clear, engaging")
            tone = typer.prompt("Tone", default="Informative and approachable")
            
            # Create basic style content
            content = f'''# WriteIt Style Primer: {name.title()}
# 
# {description}

metadata:
  name: "{name.title()}"
  description: "{description}"
  version: "1.0.0"
  author: "WriteIt User"
  category: "{category}"
  difficulty: "intermediate"
  created: "{typer.datetime.now().strftime('%Y-%m-%d')}"

# Core voice and personality
voice:
  personality: "{personality}"
  tone: "{tone}"
  perspective: "Expert sharing knowledge with clarity"

# Language characteristics
language:
  formality: "professional_casual"  # formal, professional_casual, casual, conversational
  complexity: "balanced"  # simple, balanced, complex, technical
  sentence_structure: "varied"  # short, varied, complex
  vocabulary: "accessible"  # simple, accessible, sophisticated, technical

# Content style guidelines
style:
  introduction_style: "engaging_hook"  # direct, engaging_hook, question, story
  paragraph_length: "medium"  # short, medium, long, mixed
  use_examples: true
  use_analogies: true
  use_lists: true
  use_subheadings: true

# Engagement techniques
engagement:
  address_reader: "you"  # you, readers, audience, formal
  use_questions: "rhetorical"  # none, rhetorical, direct
  call_to_action: "subtle"  # none, subtle, direct, strong
  humor: "light"  # none, light, moderate, frequent

# Technical considerations
technical:
  jargon_level: "explained"  # none, minimal, explained, assumed
  code_examples: false
  citations: false
  data_visualization: false

# Brand voice (if applicable)
brand:
  values: []
  key_messages: []
  avoid_phrases: []
  preferred_phrases: []

# Writing patterns
patterns:
  opening_phrases:
    - "Let's explore..."
    - "Consider this..."
    - "Here's what you need to know..."
  
  transition_phrases:
    - "Building on this..."
    - "Taking this further..."
    - "What's more..."
  
  closing_phrases:
    - "The key takeaway is..."
    - "Moving forward..."
    - "To sum up..."

# Content guidelines
guidelines:
  - "Use clear, concise language"
  - "Support claims with evidence or examples"
  - "Maintain consistent tone throughout"
  - "Focus on reader value and actionability"
  - "Use active voice when possible"
'''
        else:
            # Non-interactive: create minimal style
            content = f'''# WriteIt Style Primer: {name.title()}

metadata:
  name: "{name.title()}"
  description: "Basic style primer"
  version: "1.0.0"

voice:
  personality: "Professional, clear"
  tone: "Informative"

language:
  formality: "professional_casual"
  complexity: "balanced"
'''
        
        # Create the style primer
        try:
            location = template_manager.create_template(
                name=name,
                template_type=TemplateType.STYLE,
                content=content,
                workspace_name=target_workspace,
                scope=scope
            )
            
            print_success(f"Style primer '{name}' created successfully!")
            console.print(f"[primary]Path:[/primary] [path]{location.path}[/path]")
            console.print(f"[primary]Scope:[/primary] {location.scope.value}")
            if location.workspace_name:
                console.print(f"[primary]Workspace:[/primary] {location.workspace_name}")
                
        except ValueError as e:
            print_error(f"Failed to create style primer: {e}")
            raise typer.Exit(1)
            
    except Exception as e:
        print_error(f"Error creating style primer: {e}")
        raise typer.Exit(1)


@app.command(name="list")
def list_styles(
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
    List available style primers.
    
    Shows style primers from workspace and global scopes with clear labeling.
    
    [bold cyan]Examples:[/bold cyan]
    
    List all style primers:
      [dim]$ writeit style list[/dim]
    
    List workspace styles only:
      [dim]$ writeit style list --scope workspace[/dim]
    
    List global styles only:
      [dim]$ writeit style list --scope global[/dim]
    
    List styles for specific workspace:
      [dim]$ writeit style list --workspace client-x[/dim]
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
        
        # List style primers
        styles = template_manager.list_templates(
            template_type=TemplateType.STYLE,
            workspace_name=target_workspace,
            scope=template_scope
        )
        
        if not styles:
            print_warning("No style primers found")
            return
        
        # Create table data
        table_data = []
        for style in styles:
            scope_label = "Global" if style.scope == TemplateScope.GLOBAL else f"Workspace ({style.workspace_name})"
            table_data.append((style.name, scope_label))
        
        # Display table
        table = create_pipeline_table(table_data, "Available Style Primers")
        console.print(table)
        
        # Show usage hint
        console.print(f"\n[secondary]Style primers are used within pipeline templates to define writing voice and style.[/secondary]")
        
    except Exception as e:
        print_error(f"Error listing style primers: {e}")
        raise typer.Exit(1)


@app.command()
def copy(
    source: str = typer.Argument(
        ...,
        autocompletion=complete_template_name,
        help="Source style primer name"
    ),
    destination: str = typer.Argument(
        ...,
        help="Destination style primer name"
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
    Copy a style primer from one location to another.
    
    [bold cyan]Examples:[/bold cyan]
    
    Copy global style to workspace:
      [dim]$ writeit style copy technical-expert my-voice[/dim]
    
    Copy to global scope:
      [dim]$ writeit style copy my-voice shared-voice --to-global[/dim]
    
    Copy between workspaces:
      [dim]$ writeit style copy client-voice --from-workspace client-a --workspace client-b[/dim]
    """
    try:
        template_manager = get_template_manager()
        
        # Determine target scope and workspace
        dest_scope = TemplateScope.WORKSPACE if to_workspace else TemplateScope.GLOBAL
        workspace_override = get_workspace_override()
        target_workspace = workspace or workspace_override
        
        if dest_scope == TemplateScope.WORKSPACE and target_workspace is None:
            target_workspace = get_active_workspace()
        
        # Copy style primer
        location = template_manager.copy_template(
            source_name=source,
            dest_name=destination,
            template_type=TemplateType.STYLE,
            source_workspace=from_workspace,
            dest_workspace=target_workspace,
            dest_scope=dest_scope
        )
        
        print_success(f"Style primer copied successfully!")
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
        print_error(f"Error copying style primer: {e}")
        raise typer.Exit(1)