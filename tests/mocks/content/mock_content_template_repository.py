"""Mock implementation of ContentTemplateRepository for testing."""

from typing import List, Optional, Dict, Any
from pathlib import Path

from writeit.domains.content.repositories.content_template_repository import ContentTemplateRepository
from writeit.domains.content.entities.template import Template
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockContentTemplateRepository(BaseMockRepository[Template], ContentTemplateRepository):
    """Mock implementation of ContentTemplateRepository.
    
    Provides in-memory storage for content templates with file management
    simulation and validation support.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        super().__init__(str(workspace_name.value))
        self._workspace_name_obj = workspace_name
        self._template_content: Dict[str, str] = {}  # Store template content
        
    def _get_entity_id(self, entity: Template) -> Any:
        """Extract entity ID from template."""
        return str(entity.name.value)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "ContentTemplate"
        
    # Repository interface implementation
    
    async def save(self, entity: Template) -> None:
        """Save or update a content template."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id)
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: TemplateName) -> Optional[Template]:
        """Find template by name (ID)."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        template = self._get_entity(str(entity_id.value))
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), found=template is not None)
        return template
        
    async def find_all(self) -> List[Template]:
        """Find all templates in current workspace."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        templates = self._get_all_entities()
        self._log_event("find_all", self._get_entity_type_name(), count=len(templates))
        return templates
        
    async def find_by_specification(self, spec: Specification[Template]) -> List[Template]:
        """Find templates matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        templates = self._find_entities_by_specification(spec)
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(templates))
        return templates
        
    async def exists(self, entity_id: TemplateName) -> bool:
        """Check if template exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id.value))
        self._log_event("exists", self._get_entity_type_name(), str(entity_id.value), exists=exists)
        return exists
        
    async def delete(self, entity: Template) -> None:
        """Delete a template."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
            
        # Also remove content
        content_key = f"{self._workspace_name}:{entity_id}"
        self._template_content.pop(content_key, None)
        
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: TemplateName) -> bool:
        """Delete template by name."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id.value))
        
        if deleted:
            # Also remove content
            content_key = f"{self._workspace_name}:{entity_id.value}"
            self._template_content.pop(content_key, None)
        
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total templates."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities()
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[Template]:
        """Implementation-specific workspace query."""
        return self._get_all_entities(str(workspace.value))
        
    # ContentTemplateRepository-specific methods
    
    async def find_by_name(self, name: TemplateName) -> Optional[Template]:
        """Find template by name within current workspace."""
        return await self.find_by_id(name)
        
    async def find_by_name_and_workspace(
        self, 
        name: TemplateName, 
        workspace: WorkspaceName
    ) -> Optional[Template]:
        """Find template by name in specific workspace."""
        await self._check_error_condition("find_by_name_and_workspace")
        self._increment_call_count("find_by_name_and_workspace")
        await self._apply_call_delay("find_by_name_and_workspace")
        
        template = self._get_entity(str(name.value), str(workspace.value))
        self._log_event("find_by_name_and_workspace", self._get_entity_type_name(), 
                       str(name.value), found=template is not None, workspace=str(workspace.value))
        return template
        
    async def find_by_content_type(self, content_type: ContentType) -> List[Template]:
        """Find templates by content type."""
        await self._check_error_condition("find_by_content_type")
        self._increment_call_count("find_by_content_type")
        await self._apply_call_delay("find_by_content_type")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates if t.content_type == content_type]
        
        self._log_event("find_by_content_type", self._get_entity_type_name(), 
                       count=len(matching_templates), content_type=str(content_type))
        return matching_templates
        
    async def find_by_format(self, format: ContentFormat) -> List[Template]:
        """Find templates by output format."""
        await self._check_error_condition("find_by_format")
        self._increment_call_count("find_by_format")
        await self._apply_call_delay("find_by_format")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates if t.format == format]
        
        self._log_event("find_by_format", self._get_entity_type_name(), 
                       count=len(matching_templates), format=str(format))
        return matching_templates
        
    async def find_global_templates(self) -> List[Template]:
        """Find all global (system-wide) templates."""
        await self._check_error_condition("find_global_templates")
        self._increment_call_count("find_global_templates")
        await self._apply_call_delay("find_global_templates")
        
        # Search across all workspaces for global templates
        global_templates = []
        for workspace_storage in self._storage.values():
            for template in workspace_storage.values():
                if hasattr(template, 'is_global') and template.is_global:
                    global_templates.append(template)
                    
        self._log_event("find_global_templates", self._get_entity_type_name(), 
                       count=len(global_templates))
        return global_templates
        
    async def search_by_tag(self, tag: str) -> List[Template]:
        """Search templates by tag."""
        await self._check_error_condition("search_by_tag")
        self._increment_call_count("search_by_tag")
        await self._apply_call_delay("search_by_tag")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates 
                            if hasattr(t, 'tags') and tag in t.tags]
        
        self._log_event("search_by_tag", self._get_entity_type_name(), 
                       count=len(matching_templates), tag=tag)
        return matching_templates
        
    async def search_by_description(self, query: str) -> List[Template]:
        """Search templates by description text."""
        await self._check_error_condition("search_by_description")
        self._increment_call_count("search_by_description")
        await self._apply_call_delay("search_by_description")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates 
                            if query.lower() in t.description.lower()]
        
        self._log_event("search_by_description", self._get_entity_type_name(), 
                       count=len(matching_templates), query=query)
        return matching_templates
        
    async def find_templates_using_variable(self, variable: str) -> List[Template]:
        """Find templates that use a specific variable."""
        await self._check_error_condition("find_templates_using_variable")
        self._increment_call_count("find_templates_using_variable")
        await self._apply_call_delay("find_templates_using_variable")
        
        templates = self._get_all_entities()
        matching_templates = []
        
        for template in templates:
            # Check if variable is in template variables
            if hasattr(template, 'variables') and variable in template.variables:
                matching_templates.append(template)
            else:
                # Also check template content for the variable
                content_key = f"{self._workspace_name}:{template.name.value}"
                content = self._template_content.get(content_key, "")
                if f"{{{{{variable}}}}}" in content or f"{{{{ {variable} }}}}" in content:
                    matching_templates.append(template)
                    
        self._log_event("find_templates_using_variable", self._get_entity_type_name(), 
                       count=len(matching_templates), variable=variable)
        return matching_templates
        
    async def load_template_content(self, template: Template) -> str:
        """Load template content from mock storage."""
        await self._check_error_condition("load_template_content")
        self._increment_call_count("load_template_content")
        await self._apply_call_delay("load_template_content")
        
        content_key = f"{self._workspace_name}:{template.name.value}"
        content = self._template_content.get(content_key)
        
        if content is None:
            raise MockEntityNotFoundError(f"{self._get_entity_type_name()}Content", str(template.name.value))
            
        self._log_event("load_template_content", self._get_entity_type_name(), 
                       str(template.name.value), content_length=len(content))
        return content
        
    async def save_template_content(
        self, 
        template: Template, 
        content: str
    ) -> None:
        """Save template content to mock storage."""
        await self._check_error_condition("save_template_content")
        self._increment_call_count("save_template_content")
        await self._apply_call_delay("save_template_content")
        
        content_key = f"{self._workspace_name}:{template.name.value}"
        self._template_content[content_key] = content
        
        self._log_event("save_template_content", self._get_entity_type_name(), 
                       str(template.name.value), content_length=len(content))
        
    async def validate_template_syntax(self, template: Template) -> List[str]:
        """Validate template syntax and structure."""
        await self._check_error_condition("validate_template_syntax")
        self._increment_call_count("validate_template_syntax")
        await self._apply_call_delay("validate_template_syntax")
        
        # Mock validation - return configured errors or empty list
        errors = self._behavior.return_values.get("validate_template_syntax", [])
        self._log_event("validate_template_syntax", self._get_entity_type_name(), 
                       str(template.name.value), error_count=len(errors))
        return errors
        
    async def get_template_variables(self, template: Template) -> List[str]:
        """Extract variables used in template."""
        await self._check_error_condition("get_template_variables")
        self._increment_call_count("get_template_variables")
        await self._apply_call_delay("get_template_variables")
        
        # Return configured variables or extract from content
        configured_variables = self._behavior.return_values.get("get_template_variables")
        if configured_variables is not None:
            variables = configured_variables
        else:
            # Simple variable extraction from content
            content_key = f"{self._workspace_name}:{template.name.value}"
            content = self._template_content.get(content_key, "")
            
            import re
            # Find Jinja2-style variables {{ variable }}
            variables = list(set(re.findall(r'\{\{\s*(\w+)\s*\}\}', content)))
            
        self._log_event("get_template_variables", self._get_entity_type_name(), 
                       str(template.name.value), variable_count=len(variables))
        return variables
        
    async def get_template_dependencies(self, template: Template) -> List[TemplateName]:
        """Get templates that this template depends on."""
        await self._check_error_condition("get_template_dependencies")
        self._increment_call_count("get_template_dependencies")
        await self._apply_call_delay("get_template_dependencies")
        
        # Mock dependencies - return configured list or empty
        dependencies = self._behavior.return_values.get("get_template_dependencies", [])
        dependency_names = [TemplateName(dep) if isinstance(dep, str) else dep for dep in dependencies]
        
        self._log_event("get_template_dependencies", self._get_entity_type_name(), 
                       str(template.name.value), dependency_count=len(dependency_names))
        return dependency_names
        
    async def get_template_dependents(self, template: Template) -> List[TemplateName]:
        """Get templates that depend on this template."""
        await self._check_error_condition("get_template_dependents")
        self._increment_call_count("get_template_dependents")
        await self._apply_call_delay("get_template_dependents")
        
        # Mock dependents - return configured list or empty
        dependents = self._behavior.return_values.get("get_template_dependents", [])
        dependent_names = [TemplateName(dep) if isinstance(dep, str) else dep for dep in dependents]
        
        self._log_event("get_template_dependents", self._get_entity_type_name(), 
                       str(template.name.value), dependent_count=len(dependent_names))
        return dependent_names
        
    async def copy_template(
        self, 
        source: Template, 
        target_name: TemplateName, 
        target_workspace: Optional[WorkspaceName] = None
    ) -> Template:
        """Copy template to new name/workspace."""
        await self._check_error_condition("copy_template")
        self._increment_call_count("copy_template")
        await self._apply_call_delay("copy_template")
        
        target_ws = target_workspace or self._workspace_name_obj
        
        # Check if target already exists
        existing = await self.find_by_name_and_workspace(target_name, target_ws)
        if existing:
            from ..base_mock_repository import MockEntityAlreadyExistsError
            raise MockEntityAlreadyExistsError(self._get_entity_type_name(), str(target_name.value))
            
        # Create copy of template
        copied_template = source.with_name(target_name)
        
        # Store in target workspace
        target_storage = self._get_workspace_storage(str(target_ws.value))
        target_storage[str(target_name.value)] = copied_template
        
        # Copy content if it exists
        source_content_key = f"{self._workspace_name}:{source.name.value}"
        target_content_key = f"{target_ws.value}:{target_name.value}"
        if source_content_key in self._template_content:
            self._template_content[target_content_key] = self._template_content[source_content_key]
            
        self._log_event("copy_template", self._get_entity_type_name(), 
                       str(target_name.value), source_name=str(source.name.value),
                       target_workspace=str(target_ws.value))
        return copied_template
        
    async def get_template_usage_stats(self, template: Template) -> Dict[str, Any]:
        """Get template usage statistics."""
        await self._check_error_condition("get_template_usage_stats")
        self._increment_call_count("get_template_usage_stats")
        await self._apply_call_delay("get_template_usage_stats")
        
        # Mock usage statistics
        stats = self._behavior.return_values.get("get_template_usage_stats", {
            "total_uses": 10,
            "recent_uses": 3,
            "last_used": "2025-01-15T10:00:00Z",
            "common_variables": ["topic", "style"]
        })
        
        self._log_event("get_template_usage_stats", self._get_entity_type_name(), 
                       str(template.name.value), **stats)
        return stats