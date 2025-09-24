"""Mock implementation of TemplateRenderingService for testing."""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock

from writeit.domains.content.services.template_rendering_service import (
    TemplateRenderingService,
    RenderingContext,
    RenderingResult,
    TemplateError
)
from writeit.domains.content.entities.template import Template
from writeit.domains.content.value_objects.template_name import TemplateName


class MockTemplateRenderingService(TemplateRenderingService):
    """Mock implementation of TemplateRenderingService.
    
    Provides configurable template rendering behavior for testing
    template rendering scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock rendering service."""
        self._mock = Mock()
        self._rendering_results: Dict[str, RenderingResult] = {}
        self._rendered_content: Dict[str, str] = {}
        self._template_errors: List[TemplateError] = []
        self._should_fail = False
        
    def configure_rendering_result(
        self, 
        template_name: str, 
        result: RenderingResult
    ) -> None:
        """Configure rendering result for specific template."""
        self._rendering_results[template_name] = result
        
    def configure_rendered_content(self, template_name: str, content: str) -> None:
        """Configure rendered content for template."""
        self._rendered_content[template_name] = content
        
    def configure_template_errors(self, errors: List[TemplateError]) -> None:
        """Configure template errors to return."""
        self._template_errors = errors
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if rendering should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._rendering_results.clear()
        self._rendered_content.clear()
        self._template_errors.clear()
        self._should_fail = False
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def render_template(
        self,
        template: Template,
        context: RenderingContext
    ) -> RenderingResult:
        """Render template with given context."""
        self._mock.render_template(template, context)
        
        template_key = str(template.name.value)
        
        # Return configured result if available
        if template_key in self._rendering_results:
            return self._rendering_results[template_key]
            
        # Create mock rendering result
        if self._should_fail:
            return RenderingResult(
                success=False,
                content="",
                errors=self._template_errors or [
                    TemplateError(
                        message="Mock rendering error",
                        line_number=1,
                        column_number=1,
                        error_type="rendering"
                    )
                ],
                warnings=[],
                metadata={}
            )
        else:
            content = self._rendered_content.get(
                template_key, 
                f"Mock rendered content for {template_key}"
            )
            return RenderingResult(
                success=True,
                content=content,
                errors=[],
                warnings=[],
                metadata={"template": template_key}
            )
            
    async def render_string(
        self,
        template_string: str,
        context: RenderingContext
    ) -> str:
        """Render template string with context."""
        self._mock.render_string(template_string, context)
        
        if self._should_fail:
            raise TemplateError("Mock string rendering error")
            
        # Simple mock rendering - replace variables
        rendered = template_string
        for key, value in context.variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
            
        return rendered
        
    async def validate_template_syntax(
        self,
        template: Template
    ) -> List[TemplateError]:
        """Validate template syntax."""
        self._mock.validate_template_syntax(template)
        
        if self._should_fail:
            return self._template_errors or [
                TemplateError(
                    message="Mock syntax error",
                    line_number=1,
                    column_number=1,
                    error_type="syntax"
                )
            ]
            
        return self._template_errors
        
    async def extract_template_variables(
        self,
        template: Template
    ) -> List[str]:
        """Extract variables from template."""
        self._mock.extract_template_variables(template)
        
        # Return mock variables
        return ["variable1", "variable2", "topic", "style"]
        
    async def validate_context_completeness(
        self,
        template: Template,
        context: RenderingContext
    ) -> List[str]:
        """Validate that context has all required variables."""
        self._mock.validate_context_completeness(template, context)
        
        if self._should_fail:
            return ["Missing variable: mock_required_var"]
            
        return []  # No missing variables
        
    async def create_rendering_context(
        self,
        variables: Dict[str, Any],
        functions: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RenderingContext:
        """Create rendering context."""
        self._mock.create_rendering_context(variables, functions, filters)
        
        return RenderingContext(
            variables=variables,
            functions=functions or {},
            filters=filters or {},
            template_path="/mock/template/path",
            include_paths=["/mock/includes"]
        )
        
    async def render_partial(
        self,
        template: Template,
        partial_name: str,
        context: RenderingContext
    ) -> str:
        """Render template partial."""
        self._mock.render_partial(template, partial_name, context)
        
        if self._should_fail:
            raise TemplateError(f"Mock partial rendering error: {partial_name}")
            
        return f"Mock rendered partial: {partial_name}"
        
    async def get_template_dependencies(
        self,
        template: Template
    ) -> List[str]:
        """Get template dependencies (includes, extends, etc.)."""
        self._mock.get_template_dependencies(template)
        
        # Return mock dependencies
        return ["base.yaml", "header.yaml", "footer.yaml"]
        
    async def precompile_template(
        self,
        template: Template
    ) -> Dict[str, Any]:
        """Precompile template for faster rendering."""
        self._mock.precompile_template(template)
        
        return {
            "compiled": True,
            "template_id": str(template.id.value),
            "variables": ["var1", "var2"],
            "metadata": {"compilation_time": "2025-01-15T10:00:00Z"}
        }
        
    async def render_with_cache(
        self,
        template: Template,
        context: RenderingContext,
        cache_key: Optional[str] = None
    ) -> RenderingResult:
        """Render template with caching."""
        self._mock.render_with_cache(template, context, cache_key)
        
        # Delegate to regular render_template for mock
        return await self.render_template(template, context)
