# ABOUTME: Shell completion helpers for WriteIt CLI
# ABOUTME: Provides dynamic completion functions for workspace names, pipelines, etc.

import typer
from typing import List

from writeit.workspace.workspace import Workspace
from writeit.workspace.template_manager import TemplateManager, TemplateType, TemplateScope


def complete_workspace_name(incomplete: str) -> List[str]:
    """Provide workspace name completions."""
    try:
        workspace_manager = Workspace()
        if not workspace_manager.home_dir.exists():
            return []
        
        workspaces = workspace_manager.list_workspaces()
        return [ws for ws in workspaces if ws.startswith(incomplete)]
    except Exception:
        return []


def complete_pipeline_name(incomplete: str) -> List[str]:
    """Provide pipeline template name completions."""
    try:
        workspace_manager = Workspace()
        if not workspace_manager.home_dir.exists():
            return []
        
        template_manager = TemplateManager(workspace_manager)
        
        # Get active workspace
        try:
            workspace_name = workspace_manager.get_active_workspace()
        except Exception:
            workspace_name = "default"
        
        # Get all pipeline templates
        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE,
            workspace_name=workspace_name,
            scope=TemplateScope.AUTO
        )
        
        # Filter by incomplete string
        return [t.name for t in templates if t.name.startswith(incomplete)]
    except Exception:
        return []


def complete_template_name(incomplete: str) -> List[str]:
    """Provide template/style name completions for validation."""
    try:
        workspace_manager = Workspace()
        if not workspace_manager.home_dir.exists():
            return []
        
        template_manager = TemplateManager(workspace_manager)
        
        # Get active workspace
        try:
            workspace_name = workspace_manager.get_active_workspace()
        except Exception:
            workspace_name = "default"
        
        templates = []
        
        # Get pipeline templates
        pipeline_templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE,
            workspace_name=workspace_name,
            scope=TemplateScope.AUTO
        )
        templates.extend([t.name for t in pipeline_templates])
        
        # Get style templates
        style_templates = template_manager.list_templates(
            template_type=TemplateType.STYLE,
            workspace_name=workspace_name,
            scope=TemplateScope.AUTO
        )
        templates.extend([t.name for t in style_templates])
        
        # Remove duplicates and filter by incomplete string
        unique_templates = list(set(templates))
        return [t for t in unique_templates if t.startswith(incomplete)]
    except Exception:
        return []


def install_completion(shell: str = None):
    """Install shell completion for WriteIt CLI."""
    try:
        from writeit.cli.output import console, print_success, print_error
        
        # Use typer's built-in completion installation
        import os
        shell_name = shell or os.environ.get('SHELL', '').split('/')[-1] or 'bash'
        
        # Show instructions instead of auto-installing
        print_success("Shell completion installation instructions:")
        console.print(f"Add this to your [primary]{shell_name}[/primary] configuration file:")
        console.print()
        
        if shell_name == 'bash':
            console.print("[secondary]# Add to ~/.bashrc or ~/.bash_profile:[/secondary]")
            console.print("eval \"$(writeit completion --show --shell bash)\"")
        elif shell_name == 'zsh':
            console.print("[secondary]# Add to ~/.zshrc:[/secondary]")
            console.print("eval \"$(writeit completion --show --shell zsh)\"")
        elif shell_name == 'fish':
            console.print("[secondary]# Add to ~/.config/fish/config.fish:[/secondary]")
            console.print("writeit completion --show --shell fish | source")
        else:
            console.print(f"[secondary]# For {shell_name}:[/secondary]")
            console.print(f"eval \"$(writeit completion --show --shell {shell_name})\"")
            
    except Exception as e:
        from writeit.cli.output import print_error
        print_error(f"Error showing completion instructions: {e}")
        raise typer.Exit(1)


def show_completion(shell: str = None):
    """Show completion script for manual installation."""
    try:
        from writeit.cli.output import print_error
        import os
        
        # Get shell type
        shell_name = shell or os.environ.get('SHELL', '').split('/')[-1] or 'bash'
        
        if shell_name == 'zsh':
            # Generate simpler Zsh-specific completion
            completion_script = '''
# WriteIt completion script for zsh
_writeit() {
    local context state state_descr line
    typeset -A opt_args

    _arguments -s -S \\
        {-h,--help}'[Show help]' \\
        {-v,--version}'[Show version]' \\
        {-w,--workspace}'[Workspace name]:workspace:_writeit_workspaces' \\
        --verbose'[Enable verbose output]' \\
        '1:command:_writeit_commands' \\
        '*::arguments:_writeit_args'
}

_writeit_args() {
    case $words[1] in
        workspace)
            _arguments \\
                '1:subcommand:(create list use remove info)' \\
                '2:workspace:_writeit_workspaces'
            ;;
        run)
            _arguments '1:pipeline:_writeit_pipelines'
            ;;
        validate)
            _arguments \\
                '--type[validation type]:(pipeline style auto)' \\
                '--detailed[detailed results]' \\
                '--global[global only]' \\
                '--local[local only]' \\
                '1:template:_writeit_templates'
            ;;
        completion)
            _arguments \\
                '--install[install completion]' \\
                '--show[show script]' \\
                '--shell[shell type]:(bash zsh fish)'
            ;;
    esac
}

_writeit_commands() {
    local -a commands
    commands=(
        'init:Initialize WriteIt'
        'workspace:Manage workspaces' 
        'template:Manage templates'
        'style:Manage style primers'
        'run:Execute pipeline'
        'list-pipelines:List pipelines'
        'validate:Validate templates'
        'completion:Shell completion'
    )
    _describe -t commands 'commands' commands
}

_writeit_workspaces() {
    local -a workspaces
    workspaces=(${(f)"$(writeit workspace list 2>/dev/null | grep -v Available | sed 's/^[[:space:]]*\\*\\?[[:space:]]*//')"})
    _describe -t workspaces 'workspaces' workspaces
}

_writeit_pipelines() {
    local -a pipelines  
    pipelines=(${(f)"$(writeit list-pipelines 2>/dev/null | grep -E '^[[:space:]]*[a-zA-Z]' | sed 's/^[[:space:]]*//')"})
    _describe -t pipelines 'pipelines' pipelines
}

_writeit_templates() {
    local -a templates
    templates=(${(f)"$(writeit list-pipelines 2>/dev/null | grep -E '^[[:space:]]*[a-zA-Z]' | sed 's/^[[:space:]]*//')"})
    _describe -t templates 'templates' templates
}

compdef _writeit writeit
'''
        else:
            # Generate Bash-style completion (original code)
            completion_script = f'''
# WriteIt completion script for {shell_name}
_writeit_completion() {{
    local cur prev words cword
    _init_completion || return
    
    case "$prev" in
        workspace)
            COMPREPLY=($(compgen -W "create list use remove info" -- "$cur"))
            return 0
            ;;
        use|remove|info)
            # Complete workspace names
            local workspaces
            workspaces=$(writeit workspace list 2>/dev/null | grep -v "Available workspaces" | sed 's/^[[:space:]]*\\*\\?[[:space:]]*//')
            COMPREPLY=($(compgen -W "$workspaces" -- "$cur"))
            return 0
            ;;
        run)
            # Complete pipeline names  
            local pipelines
            pipelines=$(writeit list-pipelines 2>/dev/null | grep -E "^[[:space:]]*[a-zA-Z]" | sed 's/^[[:space:]]*//')
            COMPREPLY=($(compgen -W "$pipelines" -- "$cur"))
            return 0
            ;;
    esac
    
    COMPREPLY=($(compgen -W "init workspace template style run list-pipelines validate completion --help --version --workspace --verbose" -- "$cur"))
}}

complete -F _writeit_completion writeit
'''
        
        typer.echo(completion_script)
        
    except Exception as e:
        from writeit.cli.output import print_error
        print_error(f"Error generating completion script: {e}")
        raise typer.Exit(1)