"""Prompt template value object.

Provides template string validation and variable substitution capabilities.
"""

import re
from dataclasses import dataclass
from typing import Dict, Any, Set, Self
from string import Template


@dataclass(frozen=True)
class PromptTemplate:
    """Template string with validation and variable substitution.
    
    Supports Jinja2-style variable substitution with {{ variable }} syntax.
    Validates template syntax and extracts variable requirements.
    
    Examples:
        "Write an article about {{ topic }} in {{ style }} style."
        "Based on {{ steps.outline }}, create content about {{ inputs.topic }}."
    """
    
    template: str
    
    def __post_init__(self) -> None:
        """Validate template format and syntax."""
        if not isinstance(self.template, str):
            raise TypeError(f"Template must be string, got {type(self.template)}")
            
        if not self.template.strip():
            raise ValueError("Template cannot be empty or whitespace only")
            
        if len(self.template) > 10000:
            raise ValueError("Template too long (max 10,000 characters)")
            
        # Validate Jinja2-style syntax
        self._validate_syntax()
    
    def _validate_syntax(self) -> None:
        """Validate template syntax for common errors."""
        # Check for balanced braces
        open_braces = self.template.count('{{')
        close_braces = self.template.count('}}')
        
        if open_braces != close_braces:
            raise ValueError(
                f"Unbalanced template braces: {open_braces} opening, {close_braces} closing"
            )
        
        # Check for malformed variables (single braces, empty variables)
        single_brace_pattern = r'(?<!\{)\{(?!\{)|(?<!\})\}(?!\})'
        if re.search(single_brace_pattern, self.template):
            raise ValueError(
                "Template contains single braces. Use {{ variable }} for variables"
            )
            
        # Check for empty variables
        empty_var_pattern = r'\{\{\s*\}\}'
        if re.search(empty_var_pattern, self.template):
            raise ValueError("Template contains empty variables {{ }}")
    
    @property
    def variables(self) -> Set[str]:
        """Extract all variables referenced in the template."""
        # Find all {{ variable }} patterns
        pattern = r'\{\{\s*([^{}]+?)\s*\}\}'
        matches = re.findall(pattern, self.template)
        
        variables = set()
        for match in matches:
            # Handle complex expressions like steps.outline, inputs.topic
            # Extract the root variable name
            var_name = match.split('.')[0].split('|')[0].strip()
            if var_name:
                variables.add(var_name)
                
        return variables
    
    @property
    def nested_variables(self) -> Set[str]:
        """Extract all variable references including nested paths."""
        pattern = r'\{\{\s*([^{}|]+?)(?:\s*\|[^{}]*)?\s*\}\}'
        matches = re.findall(pattern, self.template)
        
        variables = set()
        for match in matches:
            var_path = match.strip()
            if var_path:
                variables.add(var_path)
                
        return variables
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render template with provided context.
        
        Args:
            context: Dictionary of variables to substitute
            
        Returns:
            Rendered template string
            
        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing required variables
        required_vars = self.variables
        missing_vars = required_vars - set(context.keys())
        
        if missing_vars:
            raise ValueError(
                f"Missing required template variables: {', '.join(sorted(missing_vars))}"
            )
        
        # Simple template substitution
        result = self.template
        
        # Handle nested variable access (e.g., steps.outline, inputs.topic)
        for var_path in self.nested_variables:
            placeholder = f"{{{ var_path }}}"
            
            # Navigate nested context
            value = context
            try:
                for part in var_path.split('.'):
                    if isinstance(value, dict):
                        value = value[part]
                    else:
                        value = getattr(value, part)
                        
                # Convert to string
                str_value = str(value) if value is not None else ""
                result = result.replace(placeholder, str_value)
                
            except (KeyError, AttributeError, TypeError):
                # Variable path not found, leave as is or replace with empty
                result = result.replace(placeholder, "")
        
        return result
    
    @classmethod
    def simple(cls, text: str) -> Self:
        """Create a simple template without variables."""
        return cls(text)
    
    @classmethod
    def from_string(cls, template_string: str) -> Self:
        """Create template from string (alias for constructor)."""
        return cls(template_string)
    
    def is_simple(self) -> bool:
        """Check if template has no variables."""
        return len(self.variables) == 0
    
    def __str__(self) -> str:
        """String representation."""
        return self.template
    
    def __len__(self) -> int:
        """Template length."""
        return len(self.template)