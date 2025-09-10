# ABOUTME: Validate command for WriteIt CLI
# ABOUTME: Validates pipeline templates and style primers with Rich output formatting

import typer
from typing import List, Optional
from pathlib import Path
from enum import Enum

from writeit.workspace.workspace import Workspace
from writeit.workspace.config import get_active_workspace
from writeit.workspace.template_manager import TemplateManager, TemplateType, TemplateScope
from writeit.validation import PipelineValidator, StyleValidator, ValidationSummary
from writeit.cli.output import (
    console, print_success, print_error, print_warning,
    format_validation_results, show_yaml_with_highlighting
)
from writeit.cli.completion import complete_template_name
from writeit.cli.app import get_workspace_override


class FileType(str, Enum):
    pipeline = "pipeline"
    style = "style"
    auto = "auto"


app = typer.Typer(
    name="validate", 
    help="Validate pipeline templates and style primers",
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


def resolve_template_path(
    template_manager: TemplateManager, 
    workspace_name: str, 
    filename: str, 
    use_global: bool = False
) -> Path:
    """Resolve template file path in workspace-aware manner."""
    # Determine scope
    scope = TemplateScope.GLOBAL if use_global else TemplateScope.AUTO
    
    # Try to detect file type first
    detected_type = detect_file_type(Path(filename))
    
    # If we can detect the type, use template manager
    if detected_type:
        template_type = TemplateType.PIPELINE if detected_type == "pipeline" else TemplateType.STYLE
        location = template_manager.resolve_template(filename, template_type, workspace_name, scope)
        if location and location.exists:
            return location.path
    
    # Fall back to trying both types
    for template_type in [TemplateType.PIPELINE, TemplateType.STYLE]:
        location = template_manager.resolve_template(filename, template_type, workspace_name, scope)
        if location and location.exists:
            return location.path
    
    # If not found, return current directory path as fallback
    normalized_filename = filename if filename.endswith(('.yaml', '.yml')) else f"{filename}.yaml"
    return Path.cwd() / normalized_filename


def detect_file_type(file_path: Path) -> Optional[str]:
    """Auto-detect file type based on content and naming patterns."""
    try:
        # Check file name patterns first
        name = file_path.name.lower()
        
        # Style primers often have style-related names
        if any(word in name for word in ['style', 'primer', 'voice', 'tone']):
            return "style"
        
        # Pipeline templates often have pipeline-related names  
        if any(word in name for word in ['pipeline', 'template', 'article', 'blog', 'guide']):
            return "pipeline"
        
        # Check content for distinguishing features
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read first 1KB
                    content_lower = content.lower()
                    
                    # Pipeline indicators
                    pipeline_indicators = ['steps:', 'inputs:', 'model_preference:', 'prompt_template:']
                    pipeline_score = sum(1 for indicator in pipeline_indicators if indicator in content_lower)
                    
                    # Style indicators
                    style_indicators = ['voice:', 'language:', 'tone:', 'personality:', 'characteristics:']
                    style_score = sum(1 for indicator in style_indicators if indicator in content_lower)
                    
                    if pipeline_score > style_score:
                        return "pipeline"
                    elif style_score > pipeline_score:
                        return "style"
            except Exception:
                pass  # If we can't read the file, fall back to None
        
        return None
        
    except Exception:
        return None


@app.command()
def validate(
    files: List[str] = typer.Argument(
        ...,
        help="Template/style names to validate (no .yaml extension needed)"
    ),
    file_type: FileType = typer.Option(
        FileType.auto,
        "--type",
        "-t",
        help="File type to validate (auto-detects if not specified)"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed validation results with suggestions"
    ),
    summary_only: bool = typer.Option(
        False,
        "--summary-only",
        "-s",
        help="Show only summary, not individual issues"
    ),
    use_global: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Only look in global templates/styles directory"
    ),
    local: bool = typer.Option(
        False,
        "--local",
        "-l",
        help="Only look in current directory (skip workspace search)"
    ),
    show_content: bool = typer.Option(
        False,
        "--show-content",
        help="Show file content with syntax highlighting"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Use specific workspace (overrides active workspace and global option)"
    )
):
    """
    Validate pipeline templates and style primers.
    
    Validates YAML files for correctness and WriteIt-specific requirements.
    Searches workspace-specific directories first, then global templates.
    
    [bold cyan]Examples:[/bold cyan]
    
    Basic validation:
      [dim]$ writeit validate article-template[/dim]
    
    Validate with detailed output:
      [dim]$ writeit validate article-template --detailed[/dim]
    
    Validate specific file type:
      [dim]$ writeit validate my-primer --type style[/dim]
    
    Validate multiple files:
      [dim]$ writeit validate template1 template2 style1[/dim]
    
    Global templates only:
      [dim]$ writeit validate article-template --global[/dim]
    
    Show file content:
      [dim]$ writeit validate template --show-content[/dim]
    """
    workspace_manager = get_workspace_manager()
    template_manager = TemplateManager(workspace_manager)
    
    try:
        # Initialize validators
        pipeline_validator = PipelineValidator()
        style_validator = StyleValidator()
        
        results = []
        
        # Determine workspace to use
        workspace_override = get_workspace_override()
        workspace_name = workspace or workspace_override or get_active_workspace()
        
        # Process each file
        for file_arg in files:
            file_path = Path(file_arg)
            
            # Resolve file path in workspace-aware manner
            if not file_path.is_absolute():
                if local:
                    # Only look in current directory - add extension if needed
                    if not file_arg.endswith('.yaml') and not file_arg.endswith('.yml'):
                        file_path = Path.cwd() / (file_arg + '.yaml')
                    else:
                        file_path = Path.cwd() / file_arg
                else:
                    # Use workspace-aware resolution
                    file_path = resolve_template_path(template_manager, workspace_name, file_arg, use_global)
            
            # Check if file exists
            if not file_path.exists():
                print_error(f"File not found: {file_path}")
                continue
            
            # Auto-detect file type if needed
            detected_type = file_type
            if detected_type == FileType.auto:
                detected_type = detect_file_type(file_path)
                if not detected_type:
                    print_warning(f"Could not auto-detect type for {file_path}, skipping")
                    continue
            
            # Show what we're validating
            console.print(f"[primary]Validating:[/primary] [path]{file_path}[/path] [secondary]({detected_type})[/secondary]")
            
            # Show file content if requested
            if show_content:
                console.print()
                show_yaml_with_highlighting(file_path)
                console.print()
            
            # Validate based on type
            try:
                if detected_type == "pipeline" or detected_type == FileType.pipeline:
                    result = pipeline_validator.validate_file(file_path)
                elif detected_type == "style" or detected_type == FileType.style:
                    result = style_validator.validate_file(file_path)
                else:
                    print_error(f"Unknown file type '{detected_type}' for {file_path}")
                    continue
                
                results.append(result)
                
            except Exception as e:
                print_error(f"Error validating {file_path}: {e}")
                continue
        
        # Display results
        if not results:
            print_error("No files were successfully validated")
            raise typer.Exit(1)
        
        # Format and display results
        if summary_only:
            summary = ValidationSummary(results)
            console.print(f"\n[primary]Validation Summary[/primary]")
            console.print(f"Files processed: {len(results)}")
            console.print(f"[success]Valid files: {summary.valid_files}[/success]")
            if summary.failed_files > 0:
                console.print(f"[error]Failed files: {summary.failed_files}[/error]")
        else:
            format_validation_results(results, detailed=detailed, show_suggestions=detailed)
        
        # Return appropriate exit code
        summary = ValidationSummary(results)
        if summary.failed_files > 0:
            console.print(f"\n[error]Validation failed for {summary.failed_files} file(s)[/error]")
            raise typer.Exit(1)
        else:
            console.print(f"\n[success]All {len(results)} file(s) validated successfully! ✓[/success]")
            
    except Exception as e:
        print_error(f"Error during validation: {e}")
        raise typer.Exit(1)