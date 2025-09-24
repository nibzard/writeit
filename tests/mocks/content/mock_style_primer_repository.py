"""Mock implementation of StylePrimerRepository for testing."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from writeit.domains.content.repositories.style_primer_repository import StylePrimerRepository
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.value_objects.style_name import StyleName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError, MockEntityAlreadyExistsError


class MockStylePrimerRepository(BaseMockRepository[StylePrimer], StylePrimerRepository):
    """Mock implementation of StylePrimerRepository.
    
    Provides in-memory storage for style primers with style management
    and validation support.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        super().__init__(str(workspace_name.value))
        self._workspace_name_obj = workspace_name
        
    def _get_entity_id(self, entity: StylePrimer) -> Any:
        """Extract entity ID from style primer."""
        return str(entity.id)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "StylePrimer"
        
    # Repository interface implementation
    
    async def save(self, entity: StylePrimer) -> None:
        """Save or update a style primer."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id)
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: UUID) -> Optional[StylePrimer]:
        """Find style primer by ID."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        primer = self._get_entity(str(entity_id))
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id), found=primer is not None)
        return primer
        
    async def find_all(self) -> List[StylePrimer]:
        """Find all style primers in current workspace."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        primers = self._get_all_entities()
        self._log_event("find_all", self._get_entity_type_name(), count=len(primers))
        return primers
        
    async def find_by_specification(self, spec: Specification[StylePrimer]) -> List[StylePrimer]:
        """Find style primers matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        primers = self._find_entities_by_specification(spec)
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(primers))
        return primers
        
    async def exists(self, entity_id: UUID) -> bool:
        """Check if style primer exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id))
        self._log_event("exists", self._get_entity_type_name(), str(entity_id), exists=exists)
        return exists
        
    async def delete(self, entity: StylePrimer) -> None:
        """Delete a style primer."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete style primer by ID."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id))
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total style primers."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities()
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[StylePrimer]:
        """Implementation-specific workspace query."""
        return self._get_all_entities(str(workspace.value))
        
    # StylePrimerRepository-specific methods
    
    async def find_by_name(self, name: StyleName) -> Optional[StylePrimer]:
        """Find style primer by name within current workspace."""
        await self._check_error_condition("find_by_name")
        self._increment_call_count("find_by_name")
        await self._apply_call_delay("find_by_name")
        
        primers = self._get_all_entities()
        for primer in primers:
            if primer.name == name:
                self._log_event("find_by_name", self._get_entity_type_name(), 
                              str(primer.id), found=True, name=str(name.value))
                return primer
                
        self._log_event("find_by_name", self._get_entity_type_name(), 
                       found=False, name=str(name.value))
        return None
        
    async def find_by_name_and_workspace(
        self, 
        name: StyleName, 
        workspace: WorkspaceName
    ) -> Optional[StylePrimer]:
        """Find style primer by name in specific workspace."""
        await self._check_error_condition("find_by_name_and_workspace")
        self._increment_call_count("find_by_name_and_workspace")
        await self._apply_call_delay("find_by_name_and_workspace")
        
        primers = self._get_all_entities(str(workspace.value))
        for primer in primers:
            if primer.name == name:
                self._log_event("find_by_name_and_workspace", self._get_entity_type_name(), 
                              str(primer.id), found=True, name=str(name.value), workspace=str(workspace.value))
                return primer
                
        self._log_event("find_by_name_and_workspace", self._get_entity_type_name(), 
                       found=False, name=str(name.value), workspace=str(workspace.value))
        return None
        
    async def find_by_content_type(self, content_type: ContentType) -> List[StylePrimer]:
        """Find style primers for specific content type."""
        await self._check_error_condition("find_by_content_type")
        self._increment_call_count("find_by_content_type")
        await self._apply_call_delay("find_by_content_type")
        
        primers = self._get_all_entities()
        matching_primers = [p for p in primers 
                          if hasattr(p, 'content_types') and content_type in p.content_types]
        
        self._log_event("find_by_content_type", self._get_entity_type_name(), 
                       count=len(matching_primers), content_type=str(content_type))
        return matching_primers
        
    async def find_global_primers(self) -> List[StylePrimer]:
        """Find all global (system-wide) style primers."""
        await self._check_error_condition("find_global_primers")
        self._increment_call_count("find_global_primers")
        await self._apply_call_delay("find_global_primers")
        
        # Search across all workspaces for global primers
        global_primers = []
        for workspace_storage in self._storage.values():
            for primer in workspace_storage.values():
                if hasattr(primer, 'is_global') and primer.is_global:
                    global_primers.append(primer)
                    
        self._log_event("find_global_primers", self._get_entity_type_name(), 
                       count=len(global_primers))
        return global_primers
        
    async def search_by_tag(self, tag: str) -> List[StylePrimer]:
        """Search style primers by tag."""
        await self._check_error_condition("search_by_tag")
        self._increment_call_count("search_by_tag")
        await self._apply_call_delay("search_by_tag")
        
        primers = self._get_all_entities()
        matching_primers = [p for p in primers 
                          if hasattr(p, 'tags') and tag in p.tags]
        
        self._log_event("search_by_tag", self._get_entity_type_name(), 
                       count=len(matching_primers), tag=tag)
        return matching_primers
        
    async def search_by_description(self, query: str) -> List[StylePrimer]:
        """Search style primers by description text."""
        await self._check_error_condition("search_by_description")
        self._increment_call_count("search_by_description")
        await self._apply_call_delay("search_by_description")
        
        primers = self._get_all_entities()
        matching_primers = [p for p in primers 
                          if query.lower() in p.description.lower()]
        
        self._log_event("search_by_description", self._get_entity_type_name(), 
                       count=len(matching_primers), query=query)
        return matching_primers
        
    async def find_by_style_properties(self, properties: Dict[str, str]) -> List[StylePrimer]:
        """Find style primers with specific style properties."""
        await self._check_error_condition("find_by_style_properties")
        self._increment_call_count("find_by_style_properties")
        await self._apply_call_delay("find_by_style_properties")
        
        primers = self._get_all_entities()
        matching_primers = []
        
        for primer in primers:
            if hasattr(primer, 'style_properties'):
                # Check if all requested properties match
                if all(primer.style_properties.get(key) == value 
                      for key, value in properties.items()):
                    matching_primers.append(primer)
                    
        self._log_event("find_by_style_properties", self._get_entity_type_name(), 
                       count=len(matching_primers), properties=properties)
        return matching_primers
        
    async def validate_style_syntax(self, primer: StylePrimer) -> List[str]:
        """Validate style primer syntax and structure."""
        await self._check_error_condition("validate_style_syntax")
        self._increment_call_count("validate_style_syntax")
        await self._apply_call_delay("validate_style_syntax")
        
        # Mock validation - return configured errors or empty list
        errors = self._behavior.return_values.get("validate_style_syntax", [])
        self._log_event("validate_style_syntax", self._get_entity_type_name(), 
                       str(primer.id), error_count=len(errors))
        return errors
        
    async def get_style_examples(self, primer: StylePrimer) -> List[str]:
        """Get style examples for a primer."""
        await self._check_error_condition("get_style_examples")
        self._increment_call_count("get_style_examples")
        await self._apply_call_delay("get_style_examples")
        
        # Return configured examples or default
        examples = self._behavior.return_values.get("get_style_examples", [
            "Example 1: Formal business writing",
            "Example 2: Casual conversational tone",
            "Example 3: Technical documentation style"
        ])
        
        self._log_event("get_style_examples", self._get_entity_type_name(), 
                       str(primer.id), example_count=len(examples))
        return examples
        
    async def copy_primer(
        self, 
        source: StylePrimer, 
        target_name: StyleName, 
        target_workspace: Optional[WorkspaceName] = None
    ) -> StylePrimer:
        """Copy style primer to new name/workspace."""
        await self._check_error_condition("copy_primer")
        self._increment_call_count("copy_primer")
        await self._apply_call_delay("copy_primer")
        
        target_ws = target_workspace or self._workspace_name_obj
        
        # Check if target already exists
        existing = await self.find_by_name_and_workspace(target_name, target_ws)
        if existing:
            raise MockEntityAlreadyExistsError(self._get_entity_type_name(), str(target_name.value))
            
        # Create copy of primer
        copied_primer = source.with_name(target_name)
        
        # Store in target workspace
        target_storage = self._get_workspace_storage(str(target_ws.value))
        target_storage[str(copied_primer.id)] = copied_primer
        
        self._log_event("copy_primer", self._get_entity_type_name(), 
                       str(copied_primer.id), source_name=str(source.name.value),
                       target_workspace=str(target_ws.value))
        return copied_primer
        
    async def get_primer_usage_stats(self, primer: StylePrimer) -> Dict[str, Any]:
        """Get style primer usage statistics."""
        await self._check_error_condition("get_primer_usage_stats")
        self._increment_call_count("get_primer_usage_stats")
        await self._apply_call_delay("get_primer_usage_stats")
        
        # Mock usage statistics
        stats = self._behavior.return_values.get("get_primer_usage_stats", {
            "total_uses": 25,
            "recent_uses": 8,
            "last_used": "2025-01-15T14:30:00Z",
            "popular_content_types": ["article", "blog_post"],
            "average_rating": 4.5
        })
        
        self._log_event("get_primer_usage_stats", self._get_entity_type_name(), 
                       str(primer.id), **stats)
        return stats
        
    async def is_name_available(self, name: StyleName) -> bool:
        """Check if style primer name is available in current workspace."""
        await self._check_error_condition("is_name_available")
        self._increment_call_count("is_name_available")
        await self._apply_call_delay("is_name_available")
        
        primer = await self.find_by_name(name)
        available = primer is None
        self._log_event("is_name_available", self._get_entity_type_name(), 
                       available=available, name=str(name.value))
        return available
        
    async def export_primer(self, primer: StylePrimer) -> Dict[str, Any]:
        """Export style primer for backup or sharing."""
        await self._check_error_condition("export_primer")
        self._increment_call_count("export_primer")
        await self._apply_call_delay("export_primer")
        
        export_data = {
            "id": str(primer.id),
            "name": str(primer.name.value),
            "description": primer.description,
            "style_properties": getattr(primer, 'style_properties', {}),
            "content_types": [str(ct) for ct in getattr(primer, 'content_types', [])],
            "tags": getattr(primer, 'tags', []),
            "exported_at": "2025-01-15T10:00:00Z",
            "version": "1.0.0"
        }
        
        self._log_event("export_primer", self._get_entity_type_name(), str(primer.id))
        return export_data
        
    async def import_primer(
        self, 
        import_data: Dict[str, Any], 
        target_workspace: Optional[WorkspaceName] = None
    ) -> StylePrimer:
        """Import style primer from exported data."""
        await self._check_error_condition("import_primer")
        self._increment_call_count("import_primer")
        await self._apply_call_delay("import_primer")
        
        target_ws = target_workspace or self._workspace_name_obj
        
        # Create primer from import data (simplified mock implementation)
        from writeit.domains.content.entities.style_primer import StylePrimer
        from writeit.domains.content.value_objects.style_name import StyleName
        
        primer = StylePrimer(
            name=StyleName(import_data["name"]),
            description=import_data["description"],
            workspace=target_ws
        )
        
        # Store in target workspace
        target_storage = self._get_workspace_storage(str(target_ws.value))
        target_storage[str(primer.id)] = primer
        
        self._log_event("import_primer", self._get_entity_type_name(), 
                       str(primer.id), target_workspace=str(target_ws.value))
        return primer