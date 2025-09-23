"""LMDB implementation of PipelineTemplateRepository.

Provides concrete LMDB-backed storage for pipeline templates with
workspace isolation, versioning, and advanced querying capabilities.
"""

from typing import List, Optional, Any
from datetime import datetime

from ...domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
    ByWorkspaceSpecification,
    ByNameSpecification,
    ByTagSpecification,
    GlobalTemplateSpecification,
    ByVersionSpecification
)
from ...domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineInput, PipelineStepTemplate
from ...domains.pipeline.value_objects.pipeline_id import PipelineId
from ...domains.pipeline.value_objects.pipeline_name import PipelineName
from ...domains.pipeline.value_objects.step_id import StepId
from ...domains.pipeline.value_objects.prompt_template import PromptTemplate
from ...domains.pipeline.value_objects.model_preference import ModelPreference
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBPipelineTemplateRepository(LMDBRepositoryBase[PipelineTemplate], PipelineTemplateRepository):
    """LMDB implementation of PipelineTemplateRepository.
    
    Stores pipeline templates with workspace isolation and provides
    advanced querying capabilities including version management.
    """
    
    def __init__(
        self, 
        storage_manager: LMDBStorageManager,
        workspace_name: WorkspaceName
    ):
        """Initialize repository.
        
        Args:
            storage_manager: LMDB storage manager
            workspace_name: Workspace for data isolation
        """
        super().__init__(
            storage_manager=storage_manager,
            workspace_name=workspace_name,
            entity_type=PipelineTemplate,
            db_name="pipeline_templates",
            db_key="templates"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with pipeline-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        # Register value objects
        serializer.register_value_object(PipelineId)
        serializer.register_value_object(PipelineName)
        serializer.register_value_object(StepId)
        serializer.register_value_object(PromptTemplate)
        serializer.register_value_object(ModelPreference)
        serializer.register_value_object(WorkspaceName)
        
        # Register entity types
        serializer.register_type("PipelineTemplate", PipelineTemplate)
        serializer.register_type("PipelineInput", PipelineInput)
        serializer.register_type("PipelineStepTemplate", PipelineStepTemplate)
    
    def _get_entity_id(self, entity: PipelineTemplate) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Pipeline template entity
            
        Returns:
            Entity identifier
        """
        return entity.id
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier (PipelineId)
            
        Returns:
            Storage key string
        """
        workspace_prefix = self._get_workspace_prefix()
        if isinstance(entity_id, PipelineId):
            return f"{workspace_prefix}template:{entity_id.value}"
        else:
            return f"{workspace_prefix}template:{str(entity_id)}"
    
    async def find_by_name(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find template by name within current workspace.
        
        Args:
            name: Template name to search for
            
        Returns:
            Template if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ByNameSpecification(name)
        results = await self.find_by_specification(spec)
        return results[0] if results else None
    
    async def find_by_name_and_workspace(
        self, 
        name: PipelineName, 
        workspace: WorkspaceName
    ) -> Optional[PipelineTemplate]:
        """Find template by name in specific workspace.
        
        Args:
            name: Template name to search for
            workspace: Workspace to search in
            
        Returns:
            Template if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(workspace) & ByNameSpecification(name)
        results = await self.find_by_specification(spec)
        return results[0] if results else None
    
    async def find_global_templates(self) -> List[PipelineTemplate]:
        """Find all global (system-wide) templates.
        
        Returns:
            List of global templates, empty if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = GlobalTemplateSpecification()
        return await self.find_by_specification(spec)
    
    async def find_by_version(
        self, 
        name: PipelineName, 
        version: str
    ) -> Optional[PipelineTemplate]:
        """Find specific version of a template.
        
        Args:
            name: Template name
            version: Version identifier
            
        Returns:
            Template version if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = (ByWorkspaceSpecification(self.workspace_name) & 
                ByNameSpecification(name) & 
                ByVersionSpecification(version))
        results = await self.find_by_specification(spec)
        return results[0] if results else None
    
    async def find_latest_version(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find the latest version of a template.
        
        Args:
            name: Template name
            
        Returns:
            Latest template version if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ByNameSpecification(name)
        results = await self.find_by_specification(spec)
        
        if not results:
            return None
        
        # Sort by version and return latest
        # Simple version comparison - for complex versioning, use packaging.version
        return max(results, key=lambda t: self._parse_version(t.version))
    
    async def find_all_versions(self, name: PipelineName) -> List[PipelineTemplate]:
        """Find all versions of a template.
        
        Args:
            name: Template name
            
        Returns:
            List of all template versions, ordered by version
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ByNameSpecification(name)
        results = await self.find_by_specification(spec)
        
        # Sort by version
        return sorted(results, key=lambda t: self._parse_version(t.version))
    
    async def search_by_tag(self, tag: str) -> List[PipelineTemplate]:
        """Search templates by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of templates with the tag
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ByTagSpecification(tag)
        return await self.find_by_specification(spec)
    
    async def search_by_description(self, query: str) -> List[PipelineTemplate]:
        """Search templates by description text.
        
        Args:
            query: Text to search for in descriptions
            
        Returns:
            List of templates matching the query
            
        Raises:
            RepositoryError: If query operation fails
        """
        # Load all templates in workspace and filter by description
        all_templates = await self.find_by_workspace()
        query_lower = query.lower()
        
        return [
            template for template in all_templates
            if query_lower in template.description.lower()
        ]
    
    async def is_name_available(self, name: PipelineName) -> bool:
        """Check if template name is available in current workspace.
        
        Args:
            name: Template name to check
            
        Returns:
            True if name is available, False if taken
            
        Raises:
            RepositoryError: If check operation fails
        """
        existing = await self.find_by_name(name)
        return existing is None
    
    async def validate_template(self, template: PipelineTemplate) -> List[str]:
        """Validate template structure and content.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        errors = []
        
        try:
            # Basic validation
            if not template.name:
                errors.append("Template name is required")
            
            if not template.description:
                errors.append("Template description is required")
            
            if not template.steps:
                errors.append("Template must have at least one step")
            
            # Validate inputs
            for key, input_def in template.inputs.items():
                if not isinstance(input_def, PipelineInput):
                    errors.append(f"Invalid input definition for '{key}'")
                    continue
                
                # Validate input configuration
                try:
                    input_def.__post_init__()  # Re-run validation
                except ValueError as e:
                    errors.append(f"Input '{key}': {e}")
            
            # Validate steps
            step_ids = set()
            for key, step in template.steps.items():
                if not isinstance(step, PipelineStepTemplate):
                    errors.append(f"Invalid step definition for '{key}'")
                    continue
                
                # Check for duplicate step IDs
                if step.id in step_ids:
                    errors.append(f"Duplicate step ID: {step.id}")
                step_ids.add(step.id)
                
                # Validate step configuration
                try:
                    step.__post_init__()  # Re-run validation
                except ValueError as e:
                    errors.append(f"Step '{key}': {e}")
                
                # Validate dependencies exist
                for dep in step.depends_on:
                    if dep not in step_ids and dep.value not in template.steps:
                        errors.append(f"Step '{key}' depends on non-existent step '{dep}'")
            
            # Validate template metadata
            try:
                template.__post_init__()  # Re-run validation
            except ValueError as e:
                errors.append(f"Template validation: {e}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    def _parse_version(self, version: str) -> tuple:
        """Parse version string for comparison.
        
        Args:
            version: Version string
            
        Returns:
            Tuple for version comparison
        """
        try:
            # Simple semantic version parsing (major.minor.patch)
            parts = version.split('.')
            return tuple(int(p) for p in parts[:3])
        except (ValueError, AttributeError):
            # Fallback to string comparison
            return (version,)
    
    async def find_templates_by_author(self, author: str) -> List[PipelineTemplate]:
        """Find templates by author.
        
        Args:
            author: Author name to search for
            
        Returns:
            List of templates by the author
        """
        all_templates = await self.find_by_workspace()
        return [
            template for template in all_templates
            if template.author and template.author == author
        ]
    
    async def find_templates_updated_since(self, since: datetime) -> List[PipelineTemplate]:
        """Find templates updated since given date.
        
        Args:
            since: Datetime to compare against
            
        Returns:
            List of recently updated templates
        """
        all_templates = await self.find_by_workspace()
        return [
            template for template in all_templates
            if template.updated_at >= since
        ]
    
    async def get_template_statistics(self) -> dict:
        """Get statistics about templates in current workspace.
        
        Returns:
            Dictionary with template statistics
        """
        all_templates = await self.find_by_workspace()
        
        if not all_templates:
            return {
                "total_count": 0,
                "avg_steps": 0,
                "avg_inputs": 0,
                "common_tags": [],
                "authors": []
            }
        
        # Calculate statistics
        total_steps = sum(len(t.steps) for t in all_templates)
        total_inputs = sum(len(t.inputs) for t in all_templates)
        
        # Count tags
        tag_counts = {}
        for template in all_templates:
            for tag in template.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get authors
        authors = set(t.author for t in all_templates if t.author)
        
        return {
            "total_count": len(all_templates),
            "avg_steps": total_steps / len(all_templates),
            "avg_inputs": total_inputs / len(all_templates),
            "common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "authors": sorted(authors)
        }