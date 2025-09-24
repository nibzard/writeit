"""Mock implementation of PipelineTemplateRepository for testing."""

from typing import List, Optional, Any
from uuid import UUID

from writeit.domains.pipeline.repositories.pipeline_template_repository import PipelineTemplateRepository
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError, MockEntityAlreadyExistsError


class MockPipelineTemplateRepository(BaseMockRepository[PipelineTemplate], PipelineTemplateRepository):
    """Mock implementation of PipelineTemplateRepository.
    
    Provides in-memory storage for pipeline templates with full workspace isolation
    and configurable behavior for testing various scenarios.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        super().__init__(str(workspace_name.value))
        self._workspace_name_obj = workspace_name
        
    def _get_entity_id(self, entity: PipelineTemplate) -> Any:
        """Extract entity ID from pipeline template."""
        return entity.id.value
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "PipelineTemplate"
        
    # Repository interface implementation
    
    async def save(self, entity: PipelineTemplate) -> None:
        """Save or update a pipeline template."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id)
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: PipelineId) -> Optional[PipelineTemplate]:
        """Find template by ID."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        template = self._get_entity(entity_id.value)
        self._log_event("find_by_id", self._get_entity_type_name(), entity_id.value, found=template is not None)
        return template
        
    async def find_all(self) -> List[PipelineTemplate]:
        """Find all templates in current workspace."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        templates = self._get_all_entities()
        self._log_event("find_all", self._get_entity_type_name(), count=len(templates))
        return templates
        
    async def find_by_specification(self, spec: Specification[PipelineTemplate]) -> List[PipelineTemplate]:
        """Find templates matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        templates = self._find_entities_by_specification(spec)
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(templates))
        return templates
        
    async def exists(self, entity_id: PipelineId) -> bool:
        """Check if template exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(entity_id.value)
        self._log_event("exists", self._get_entity_type_name(), entity_id.value, exists=exists)
        return exists
        
    async def delete(self, entity: PipelineTemplate) -> None:
        """Delete a template."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: PipelineId) -> bool:
        """Delete template by ID."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(entity_id.value)
        self._log_event("delete_by_id", self._get_entity_type_name(), entity_id.value, deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total templates."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities()
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[PipelineTemplate]:
        """Implementation-specific workspace query."""
        return self._get_all_entities(str(workspace.value))
        
    # PipelineTemplateRepository-specific methods
    
    async def find_by_name(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find template by name within current workspace."""
        await self._check_error_condition("find_by_name")
        self._increment_call_count("find_by_name")
        await self._apply_call_delay("find_by_name")
        
        templates = self._get_all_entities()
        for template in templates:
            if template.name == name:
                self._log_event("find_by_name", self._get_entity_type_name(), template.id.value, found=True)
                return template
                
        self._log_event("find_by_name", self._get_entity_type_name(), found=False, name=str(name.value))
        return None
        
    async def find_by_name_and_workspace(
        self, 
        name: PipelineName, 
        workspace: WorkspaceName
    ) -> Optional[PipelineTemplate]:
        """Find template by name in specific workspace."""
        await self._check_error_condition("find_by_name_and_workspace")
        self._increment_call_count("find_by_name_and_workspace")
        await self._apply_call_delay("find_by_name_and_workspace")
        
        templates = self._get_all_entities(str(workspace.value))
        for template in templates:
            if template.name == name:
                self._log_event("find_by_name_and_workspace", self._get_entity_type_name(), 
                              template.id.value, found=True, workspace=str(workspace.value))
                return template
                
        self._log_event("find_by_name_and_workspace", self._get_entity_type_name(), 
                       found=False, name=str(name.value), workspace=str(workspace.value))
        return None
        
    async def find_global_templates(self) -> List[PipelineTemplate]:
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
                    
        self._log_event("find_global_templates", self._get_entity_type_name(), count=len(global_templates))
        return global_templates
        
    async def find_by_version(
        self, 
        name: PipelineName, 
        version: str
    ) -> Optional[PipelineTemplate]:
        """Find specific version of a template."""
        await self._check_error_condition("find_by_version")
        self._increment_call_count("find_by_version")
        await self._apply_call_delay("find_by_version")
        
        templates = self._get_all_entities()
        for template in templates:
            if template.name == name and template.metadata.version == version:
                self._log_event("find_by_version", self._get_entity_type_name(), 
                              template.id.value, found=True, version=version)
                return template
                
        self._log_event("find_by_version", self._get_entity_type_name(), 
                       found=False, name=str(name.value), version=version)
        return None
        
    async def find_latest_version(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find the latest version of a template."""
        await self._check_error_condition("find_latest_version")
        self._increment_call_count("find_latest_version")
        await self._apply_call_delay("find_latest_version")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates if t.name == name]
        
        if not matching_templates:
            self._log_event("find_latest_version", self._get_entity_type_name(), 
                           found=False, name=str(name.value))
            return None
            
        # Sort by version (simple string comparison for mock)
        latest = max(matching_templates, key=lambda t: t.metadata.version)
        self._log_event("find_latest_version", self._get_entity_type_name(), 
                       latest.id.value, found=True, version=latest.metadata.version)
        return latest
        
    async def find_all_versions(self, name: PipelineName) -> List[PipelineTemplate]:
        """Find all versions of a template."""
        await self._check_error_condition("find_all_versions")
        self._increment_call_count("find_all_versions")
        await self._apply_call_delay("find_all_versions")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates if t.name == name]
        
        # Sort by version
        matching_templates.sort(key=lambda t: t.metadata.version)
        self._log_event("find_all_versions", self._get_entity_type_name(), 
                       count=len(matching_templates), name=str(name.value))
        return matching_templates
        
    async def search_by_tag(self, tag: str) -> List[PipelineTemplate]:
        """Search templates by tag."""
        await self._check_error_condition("search_by_tag")
        self._increment_call_count("search_by_tag")
        await self._apply_call_delay("search_by_tag")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates 
                            if hasattr(t.metadata, 'tags') and tag in t.metadata.tags]
        
        self._log_event("search_by_tag", self._get_entity_type_name(), 
                       count=len(matching_templates), tag=tag)
        return matching_templates
        
    async def search_by_description(self, query: str) -> List[PipelineTemplate]:
        """Search templates by description text."""
        await self._check_error_condition("search_by_description")
        self._increment_call_count("search_by_description")
        await self._apply_call_delay("search_by_description")
        
        templates = self._get_all_entities()
        matching_templates = [t for t in templates 
                            if query.lower() in t.metadata.description.lower()]
        
        self._log_event("search_by_description", self._get_entity_type_name(), 
                       count=len(matching_templates), query=query)
        return matching_templates
        
    async def is_name_available(self, name: PipelineName) -> bool:
        """Check if template name is available in current workspace."""
        await self._check_error_condition("is_name_available")
        self._increment_call_count("is_name_available")
        await self._apply_call_delay("is_name_available")
        
        template = await self.find_by_name(name)
        available = template is None
        self._log_event("is_name_available", self._get_entity_type_name(), 
                       available=available, name=str(name.value))
        return available
        
    async def validate_template(self, template: PipelineTemplate) -> List[str]:
        """Validate template structure and content."""
        await self._check_error_condition("validate_template")
        self._increment_call_count("validate_template")
        await self._apply_call_delay("validate_template")
        
        # Simple mock validation - return configured errors or empty list
        errors = self._behavior.return_values.get("validate_template", [])
        self._log_event("validate_template", self._get_entity_type_name(), 
                       template.id.value, error_count=len(errors))
        return errors