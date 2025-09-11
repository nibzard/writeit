"""
CLI documentation extractor from Typer commands
"""

import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import typer
from typer.models import CommandInfo, OptionInfo, ArgumentInfo

from ..models import (
    CLIDocumentation,
    CommandDocumentation,
    ParameterDocumentation,
    CodeExample
)


class CLIExtractor:
    """Extract CLI documentation from Typer commands"""
    
    def extract_cli_docs(self, app: typer.Typer) -> CLIDocumentation:
        """Extract complete CLI documentation"""
        cli_docs = CLIDocumentation(
            app_name=app.info.name if app.info else "writeit",
            description=app.info.help if app.info else "",
            commands=[],
            global_options=[]
        )
        
        # Extract commands
        cli_docs.commands = self._extract_commands(app)
        
        # Extract global options
        cli_docs.global_options = self._extract_global_options(app)
        
        return cli_docs
    
    def _extract_commands(self, app: typer.Typer) -> List[CommandDocumentation]:
        """Extract all commands from the Typer app"""
        commands = []
        
        if app.registered_commands:
            for cmd_info in app.registered_commands:
                if isinstance(cmd_info, CommandInfo):
                    command_doc = self._extract_command(cmd_info)
                    if command_doc:
                        commands.append(command_doc)
        
        # Extract commands from sub-apps
        if app.registered_groups:
            for group in app.registered_groups:
                if hasattr(group, 'typer_instance') and group.typer_instance:
                    sub_commands = self._extract_commands(group.typer_instance)
                    commands.extend(sub_commands)
        
        return commands
    
    def _extract_command(self, cmd_info: CommandInfo) -> Optional[CommandDocumentation]:
        """Extract documentation for a single command"""
        try:
            callback = cmd_info.callback
            if not callback:
                return None
            
            # Handle case where name might be None
            if not cmd_info.name:
                # Try to get name from callback function
                if hasattr(callback, '__name__'):
                    cmd_info.name = callback.__name__
                else:
                    cmd_info.name = "unknown_command"
            
            # Get command signature
            sig = inspect.signature(callback)
            
            command_doc = CommandDocumentation(
                name=cmd_info.name or "unknown",
                description=cmd_info.help or "",
                usage=self._generate_usage(cmd_info, sig),
                arguments=[],
                options=[],  # Initialize options as empty list
                examples=self._extract_command_examples(cmd_info),
                source_file=self._get_source_file(callback)
            )
            
            # Extract parameters (arguments and options)
            parameters = self._extract_command_parameters(sig, cmd_info)
            # Separate arguments from options based on default values
            for param in parameters:
                if param.required:
                    command_doc.arguments.append(param)
                else:
                    command_doc.options.append(param)
            
            # Extract command tags from decorators or metadata
            command_doc.tags = self._extract_command_tags(cmd_info)
            
            return command_doc
        
        except Exception as e:
            print(f"Error extracting command docs for {cmd_info.name}: {e}")
            return None
    
    def _extract_command_parameters(self, sig, cmd_info: CommandInfo) -> List[ParameterDocumentation]:
        """Extract parameters from command signature"""
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['ctx', 'typer_context']:
                continue
            
            param_doc = ParameterDocumentation(
                name=param_name,
                type_annotation=self._get_param_type_annotation(param),
                description=self._get_param_description(param_name, cmd_info),
                default_value=self._get_param_default_value(param),
                required=param.default is inspect.Parameter.empty
            )
            
            parameters.append(param_doc)
        
        return parameters
    
    def _get_param_type_annotation(self, param) -> str:
        """Get type annotation for parameter"""
        if param.annotation == inspect.Parameter.empty:
            return "str"
        
        try:
            return str(param.annotation).replace("typing.", "").replace("builtins.", "")
        except:
            return "str"
    
    def _get_param_description(self, param_name: str, cmd_info: CommandInfo) -> str:
        """Extract parameter description"""
        # Try to get from Typer parameter info
        if hasattr(cmd_info, 'params'):
            for param_info in cmd_info.params:
                if isinstance(param_info, (OptionInfo, ArgumentInfo)):
                    if param_info.param_decls and param_name in param_info.param_decls:
                        return param_info.help or ""
        
        # Fallback to docstring parsing
        if cmd_info.callback and cmd_info.callback.__doc__:
            docstring = cmd_info.callback.__doc__
            lines = docstring.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith(f':param {param_name}:'):
                    return line.split(f':param {param_name}:', 1)[1].strip()
                elif line.startswith(f':param {param_name} '):
                    return line.split(f':param {param_name} ', 1)[1].strip()
        
        return ""
    
    def _get_param_default_value(self, param) -> Optional[str]:
        """Get default value for parameter"""
        if param.default == inspect.Parameter.empty:
            return None
        
        try:
            return repr(param.default)
        except:
            return str(param.default)
    
    def _generate_usage(self, cmd_info: CommandInfo, sig) -> str:
        """Generate usage string for command"""
        cmd_name = cmd_info.name or "command"
        usage_parts = [f"writeit {cmd_name}"]
        
        for param_name, param in sig.parameters.items():
            if param_name in ['ctx', 'typer_context']:
                continue
            
            if param.default == inspect.Parameter.empty:
                usage_parts.append(f"<{param_name}>")
            else:
                usage_parts.append(f"[--{param_name}]")
        
        return " ".join(usage_parts)
    
    def _extract_command_examples(self, cmd_info: CommandInfo) -> List[str]:
        """Extract usage examples for command"""
        examples = []
        
        # Generate basic usage example
        cmd_name = cmd_info.name or "command"
        basic_example = f"writeit {cmd_name}"
        examples.append(basic_example)
        
        # Generate examples with parameters
        if cmd_info.callback:
            sig = inspect.signature(cmd_info.callback)
            optional_params = [
                name for name, param in sig.parameters.items()
                if name not in ['ctx', 'typer_context'] and param.default != inspect.Parameter.empty
            ]
            
            if optional_params:
                cmd_name = cmd_info.name or "command"
                example = f"writeit {cmd_name} --{optional_params[0]} value"
                examples.append(example)
        
        return examples
    
    def _extract_command_tags(self, cmd_info: CommandInfo) -> List[str]:
        """Extract command tags from metadata"""
        tags = []
        
        # Add common tags based on command name patterns
        if any(keyword in cmd_info.name.lower() for keyword in ['init', 'setup', 'config']):
            tags.append("setup")
        elif any(keyword in cmd_info.name.lower() for keyword in ['run', 'execute', 'start']):
            tags.append("execution")
        elif any(keyword in cmd_info.name.lower() for keyword in ['list', 'show', 'get']):
            tags.append("query")
        elif any(keyword in cmd_info.name.lower() for keyword in ['create', 'add', 'new']):
            tags.append("creation")
        elif any(keyword in cmd_info.name.lower() for keyword in ['delete', 'remove', 'rm']):
            tags.append("deletion")
        elif any(keyword in cmd_info.name.lower() for keyword in ['validate', 'check', 'test']):
            tags.append("validation")
        
        # Add from command info if available
        if hasattr(cmd_info, 'metadata') and isinstance(cmd_info.metadata, dict):
            if 'tags' in cmd_info.metadata:
                tags.extend(cmd_info.metadata['tags'])
        
        return list(set(tags))
    
    def _extract_global_options(self, app: typer.Typer) -> List[ParameterDocumentation]:
        """Extract global options from app"""
        global_options = []
        
        # Common global options in WriteIt
        common_globals = [
            {
                "name": "--help",
                "type_annotation": "bool",
                "description": "Show help message and exit",
                "required": False,
                "default_value": "False"
            },
            {
                "name": "--version",
                "type_annotation": "bool", 
                "description": "Show version and exit",
                "required": False,
                "default_value": "False"
            },
            {
                "name": "--verbose",
                "type_annotation": "bool",
                "description": "Enable verbose output",
                "required": False,
                "default_value": "False"
            },
            {
                "name": "--workspace",
                "type_annotation": "str",
                "description": "Specify workspace to use",
                "required": False,
                "default_value": None
            }
        ]
        
        for option_data in common_globals:
            global_options.append(ParameterDocumentation(**option_data))
        
        return global_options
    
    def _get_source_file(self, callback) -> Optional[Path]:
        """Get source file path for callback function"""
        try:
            return Path(inspect.getfile(callback))
        except:
            return None
    
    def generate_shell_completion_docs(self, app: typer.Typer) -> str:
        """Generate shell completion documentation"""
        completion_docs = f"""# Shell Completion for {app.info.name if app.info else 'WriteIt'}

## Installation

### Bash
```bash
# Install completion
eval "$({app.info.name if app.info else 'writeit'} --show-completion)"

# Add to your ~/.bashrc
echo 'eval "$({app.info.name if app.info else "writeit"} --show-completion)"' >> ~/.bashrc
```

### Zsh
```bash
# Install completion
eval "$({app.info.name if app.info else 'writeit'} --show-completion)"

# Add to your ~/.zshrc
echo 'eval "$({app.info.name if app.info else "writeit"} --show-completion)"' >> ~/.zshrc
```

### Fish
```bash
# Install completion
{app.info.name if app.info else 'writeit'} --show-completion | source

# Add to your ~/.config/fish/completions/{app.info.name if app.info else 'writeit'}.fish
{app.info.name if app.info else 'writeit'} --show-completion > ~/.config/fish/completions/{app.info.name if app.info else 'writeit'}.fish
```

## Usage

Once completion is installed, you can use tab completion:

```bash
# Complete commands
{app.info.name if app.info else 'writeit'} <TAB>

# Complete options
{app.info.name if app.info else 'writeit'} run <TAB>
{app.info.name if app.info else 'writeit'} run --<TAB>
```
"""
        return completion_docs