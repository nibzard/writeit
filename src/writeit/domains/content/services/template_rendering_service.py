"""Template rendering service.

Domain service responsible for template variable substitution, context-aware
template processing, and template compilation with validation.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, Pattern

from ..entities.template import Template
from ..value_objects.template_name import TemplateName
from ..value_objects.content_type import ContentType
from ....shared.repository import RepositoryError


class RenderingMode(Enum):
    """Template rendering modes."""
    STRICT = "strict"  # Fail on missing variables
    PERMISSIVE = "permissive"  # Allow missing variables with defaults
    PREVIEW = "preview"  # Replace missing with placeholder text


class VariableType(Enum):
    """Types of template variables."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


@dataclass
class VariableDefinition:
    """Definition of a template variable."""
    name: str
    type: VariableType
    required: bool = True
    default: Optional[Any] = None
    description: Optional[str] = None
    validation_pattern: Optional[str] = None
    
    def validate_value(self, value: Any) -> bool:
        """Validate that a value matches this variable's requirements."""
        if value is None:
            return not self.required
        
        # Type validation
        if self.type == VariableType.STRING and not isinstance(value, str):
            return False
        elif self.type == VariableType.INTEGER and not isinstance(value, int):
            return False
        elif self.type == VariableType.FLOAT and not isinstance(value, (int, float)):
            return False
        elif self.type == VariableType.BOOLEAN and not isinstance(value, bool):
            return False
        elif self.type == VariableType.LIST and not isinstance(value, list):
            return False
        elif self.type == VariableType.DICT and not isinstance(value, dict):
            return False
        
        # Pattern validation for strings
        if (self.type == VariableType.STRING and 
            self.validation_pattern and 
            isinstance(value, str)):
            pattern = re.compile(self.validation_pattern)
            return bool(pattern.match(value))
        
        return True


@dataclass
class RenderingContext:
    """Context for template rendering operations."""
    variables: Dict[str, Any]
    mode: RenderingMode = RenderingMode.STRICT
    template_name: Optional[TemplateName] = None
    content_type: Optional[ContentType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get variable value with optional default."""
        return self.variables.get(name, default)
    
    def has_variable(self, name: str) -> bool:
        """Check if variable exists in context."""
        return name in self.variables
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value in context."""
        self.variables[name] = value
    
    def merge_variables(self, additional_vars: Dict[str, Any]) -> None:
        """Merge additional variables into context."""
        self.variables.update(additional_vars)


@dataclass
class RenderingResult:
    """Result of template rendering operation."""
    rendered_content: str
    used_variables: Set[str]
    missing_variables: Set[str]
    validation_errors: List[str]
    success: bool
    
    @property
    def has_errors(self) -> bool:
        """Check if rendering had validation errors."""
        return len(self.validation_errors) > 0
    
    @property
    def has_missing_variables(self) -> bool:
        """Check if any required variables were missing."""
        return len(self.missing_variables) > 0


class TemplateRenderingError(Exception):
    """Base exception for template rendering operations."""
    
    def __init__(
        self, 
        message: str, 
        template_name: Optional[TemplateName] = None,
        context_info: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.template_name = template_name
        self.context_info = context_info or {}


class VariableValidationError(TemplateRenderingError):
    """Raised when variable validation fails."""
    
    def __init__(
        self, 
        message: str, 
        variable_name: str,
        expected_type: VariableType,
        actual_value: Any,
        template_name: Optional[TemplateName] = None
    ):
        super().__init__(message, template_name, {
            "variable_name": variable_name,
            "expected_type": expected_type.value,
            "actual_value": actual_value,
            "actual_type": type(actual_value).__name__
        })
        self.variable_name = variable_name
        self.expected_type = expected_type
        self.actual_value = actual_value


class MissingVariableError(TemplateRenderingError):
    """Raised when required variables are missing."""
    
    def __init__(
        self, 
        missing_variables: Set[str],
        template_name: Optional[TemplateName] = None
    ):
        missing_list = ", ".join(sorted(missing_variables))
        message = f"Missing required variables: {missing_list}"
        super().__init__(message, template_name, {
            "missing_variables": list(missing_variables)
        })
        self.missing_variables = missing_variables


class TemplateCompilationError(TemplateRenderingError):
    """Raised when template compilation fails."""
    pass


class TemplateRenderingService:
    """Service for rendering templates with variable substitution.
    
    This service handles template processing including:
    - Variable extraction and validation
    - Context-aware rendering with different modes
    - Template compilation and caching
    - Variable type checking and coercion
    
    Examples:
        service = TemplateRenderingService()
        
        # Define variables for template
        variables = {
            "topic": "Machine Learning",
            "audience": "developers",
            "length": "medium"
        }
        
        context = RenderingContext(
            variables=variables,
            mode=RenderingMode.STRICT
        )
        
        # Render template
        result = await service.render_template(template, context)
        
        if result.success:
            print(result.rendered_content)
        else:
            print(f"Errors: {result.validation_errors}")
    """
    
    # Regex pattern for finding template variables like {{ variable_name }}
    VARIABLE_PATTERN = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}')
    
    # Regex pattern for finding variable definitions in template metadata
    VARIABLE_DEF_PATTERN = re.compile(
        r'variables:\s*\n((?:\s*-?\s*\w+:.*\n?)*)', 
        re.MULTILINE
    )
    
    def __init__(self):
        """Initialize template rendering service."""
        self._variable_cache: Dict[str, Set[str]] = {}
        self._compiled_templates: Dict[str, Pattern] = {}
    
    async def render_template(
        self, 
        template: Template, 
        context: RenderingContext
    ) -> RenderingResult:
        """Render template with variable substitution.
        
        Args:
            template: Template to render
            context: Rendering context with variables
            
        Returns:
            Rendering result with processed content
            
        Raises:
            TemplateRenderingError: If rendering fails
            VariableValidationError: If variable validation fails
            MissingVariableError: If required variables missing in strict mode
        """
        try:
            # Extract variable definitions from template
            variable_definitions = await self._extract_variable_definitions(template)
            
            # Validate provided variables
            validation_errors = await self._validate_variables(
                context.variables, 
                variable_definitions,
                context.mode
            )
            
            # Find all variables used in template
            template_variables = await self._extract_template_variables(template)
            
            # Determine missing variables
            missing_variables = set()
            for var_name in template_variables:
                if var_name not in context.variables:
                    var_def = variable_definitions.get(var_name)
                    # If variable has a definition, check if it's required
                    # If no definition exists, assume it's required for strict validation
                    if var_def is None or var_def.required:
                        missing_variables.add(var_name)
            
            # Handle missing variables based on rendering mode
            if missing_variables and context.mode == RenderingMode.STRICT:
                raise MissingVariableError(missing_variables, template.name)
            
            # Perform variable substitution
            rendered_content = await self._substitute_variables(
                template.yaml_content,
                context,
                variable_definitions,
                template_variables
            )
            
            # Track which variables were actually used
            used_variables = template_variables.intersection(context.variables.keys())
            
            success = len(validation_errors) == 0 and (
                context.mode != RenderingMode.STRICT or len(missing_variables) == 0
            )
            
            return RenderingResult(
                rendered_content=rendered_content,
                used_variables=used_variables,
                missing_variables=missing_variables,
                validation_errors=validation_errors,
                success=success
            )
            
        except (MissingVariableError, VariableValidationError):
            # Re-raise these as they are expected
            raise
        except Exception as e:
            raise TemplateRenderingError(
                f"Failed to render template: {e}",
                template.name,
                {"original_error": str(e)}
            ) from e
    
    async def extract_variable_definitions(
        self, 
        template: Template
    ) -> Dict[str, VariableDefinition]:
        """Extract variable definitions from template metadata.
        
        Args:
            template: Template to analyze
            
        Returns:
            Dictionary of variable definitions
        """
        return await self._extract_variable_definitions(template)
    
    async def extract_template_variables(
        self, 
        template: Template
    ) -> Set[str]:
        """Extract all variable names used in template.
        
        Args:
            template: Template to analyze
            
        Returns:
            Set of variable names found in template
        """
        return await self._extract_template_variables(template)
    
    async def validate_rendering_context(
        self,
        template: Template,
        context: RenderingContext
    ) -> List[str]:
        """Validate that rendering context is sufficient for template.
        
        Args:
            template: Template to validate against
            context: Rendering context to validate
            
        Returns:
            List of validation error messages
        """
        try:
            variable_definitions = await self._extract_variable_definitions(template)
            return await self._validate_variables(context.variables, variable_definitions, context.mode)
        except Exception as e:
            return [f"Context validation failed: {e}"]
    
    async def create_rendering_context(
        self,
        variables: Dict[str, Any],
        mode: RenderingMode = RenderingMode.STRICT,
        template: Optional[Template] = None
    ) -> RenderingContext:
        """Create rendering context with optional template metadata.
        
        Args:
            variables: Variables for rendering
            mode: Rendering mode
            template: Optional template for metadata
            
        Returns:
            Configured rendering context
        """
        context = RenderingContext(
            variables=variables,
            mode=mode
        )
        
        if template:
            context.template_name = template.name
            context.content_type = template.content_type
            context.metadata = {
                "template_version": template.version,
                "template_id": str(template.id),
                "template_tags": template.tags
            }
        
        return context
    
    async def _extract_variable_definitions(
        self, 
        template: Template
    ) -> Dict[str, VariableDefinition]:
        """Extract variable definitions from template YAML metadata."""
        variable_definitions = {}
        
        # Parse YAML content to find variable definitions
        lines = template.yaml_content.split('\n')
        in_variables_section = False
        in_inputs_section = False
        current_indent = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            
            # Check for top-level sections
            if indent == 0 and stripped.endswith(':'):
                section_name = stripped[:-1].strip()
                in_variables_section = (section_name == 'variables')
                in_inputs_section = (section_name == 'inputs')
                current_indent = 0
                continue
            
            # Check for section end (new top-level section or lower indent)
            if indent <= current_indent and stripped.endswith(':') and indent == 0:
                in_variables_section = False
                in_inputs_section = False
                continue
            
            # Parse variable definitions in variables or inputs sections
            if (in_variables_section or in_inputs_section) and ':' in stripped:
                # Set the section indent level if not already set
                if current_indent == 0:
                    current_indent = indent
                
                # Only process direct children of the section (variables/inputs)
                # Skip nested properties (which have higher indentation)
                if indent == current_indent:
                    # Handle both list format (- name:) and direct format (name:)
                    if stripped.startswith('- '):
                        var_line = stripped[2:].strip()
                    else:
                        var_line = stripped
                    
                    if ':' in var_line:
                        name = var_line.split(':')[0].strip()
                        if name and not name.startswith('#'):
                            var_def = VariableDefinition(
                                name=name,
                                type=VariableType.ANY,  # Default type
                                required=True
                            )
                            variable_definitions[name] = var_def
        
        return variable_definitions
    
    async def _extract_template_variables(self, template: Template) -> Set[str]:
        """Extract all variable names from template content."""
        # Use caching for performance
        cache_key = f"{template.id}:{template.version}"
        if cache_key in self._variable_cache:
            return self._variable_cache[cache_key]
        
        # Find all {{ variable_name }} patterns
        variables = set()
        matches = self.VARIABLE_PATTERN.findall(template.yaml_content)
        
        for match in matches:
            # Handle nested variable names like inputs.topic
            var_name = match.split('.')[0]  # Take root variable name
            variables.add(var_name)
        
        # Cache the result
        self._variable_cache[cache_key] = variables
        return variables
    
    async def _validate_variables(
        self,
        variables: Dict[str, Any],
        definitions: Dict[str, VariableDefinition],
        mode: RenderingMode = RenderingMode.STRICT
    ) -> List[str]:
        """Validate variables against their definitions."""
        errors = []
        
        for var_name, var_def in definitions.items():
            if var_name in variables:
                value = variables[var_name]
                if not var_def.validate_value(value):
                    errors.append(
                        f"Variable '{var_name}' validation failed: "
                        f"expected {var_def.type.value}, got {type(value).__name__}"
                    )
            elif var_def.required and mode == RenderingMode.STRICT:
                errors.append(f"Required variable '{var_name}' is missing")
        
        return errors
    
    async def _substitute_variables(
        self,
        content: str,
        context: RenderingContext,
        definitions: Dict[str, VariableDefinition],
        template_variables: Set[str]
    ) -> str:
        """Substitute variables in template content."""
        
        def replace_variable(match):
            var_name = match.group(1).strip()
            root_var = var_name.split('.')[0]
            
            # Get value from context
            if root_var in context.variables:
                value = context.variables[root_var]
                
                # Handle nested access like inputs.topic
                if '.' in var_name:
                    parts = var_name.split('.')[1:]
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                
                if value is not None:
                    return str(value)
            
            # Handle missing variables based on mode
            if context.mode == RenderingMode.PERMISSIVE:
                var_def = definitions.get(root_var)
                if var_def and var_def.default is not None:
                    return str(var_def.default)
                return ""  # Empty string for missing variables
            elif context.mode == RenderingMode.PREVIEW:
                return f"{{{{ {var_name} }}}}"  # Keep placeholder
            else:
                # STRICT mode - this should have been caught earlier
                return f"{{{{ {var_name} }}}}"
        
        # Substitute all variables
        result = self.VARIABLE_PATTERN.sub(replace_variable, content)
        return result
    
    def clear_cache(self) -> None:
        """Clear internal caches."""
        self._variable_cache.clear()
        self._compiled_templates.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "variable_cache_size": len(self._variable_cache),
            "compiled_templates_size": len(self._compiled_templates)
        }