"""LMDB implementation of PipelineTemplateRepository.

Provides persistent storage for pipeline templates using LMDB
with workspace isolation, versioning, and advanced querying.
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ...domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
    ByWorkspaceSpecification,
    ByNameSpecification,
    ByTagSpecification,
    GlobalTemplateSpecification,
    ByVersionSpecification
)
from ...domains.pipeline.entities.pipeline_template import PipelineTemplate
from ...domains.pipeline.value_objects.pipeline_id import PipelineId
from ...domains.pipeline.value_objects.pipeline_name import PipelineName
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError
from ..persistence.lmdb_storage import LMDBStorage
from ..base.exceptions import StorageError, ValidationError


class LMDBPipelineTemplateRepository(PipelineTemplateRepository):
    """LMDB-based implementation of PipelineTemplateRepository.
    
    Stores pipeline templates in LMDB with workspace isolation,
    version management, and efficient querying capabilities.
    """
    
    def __init__(self, storage: LMDBStorage, workspace: Optional[WorkspaceName] = None):
        """Initialize repository.
        
        Args:
            storage: LMDB storage instance
            workspace: Current workspace (if None, uses global scope)
        """
        super().__init__(workspace)
        self.storage = storage
        self._db_name = "pipeline_templates"
        
    async def save(self, template: PipelineTemplate) -> None:
        """Save a pipeline template.
        
        Args:
            template: Template to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            # Generate storage key
            key = self._make_key(template.id, template.workspace)
            
            # Store template
            await self.storage.store_entity(
                template,
                key,
                self._db_name
            )
            
            # Update search indices
            await self._update_indices(template)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to save pipeline template {template.id}: {e}") from e
    
    async def find_by_id(self, template_id: PipelineId) -> Optional[PipelineTemplate]:
        """Find template by ID.
        
        Args:
            template_id: Template ID to search for
            
        Returns:
            Template if found, None otherwise
        """
        try:
            key = self._make_key(template_id, self.workspace)
            return await self.storage.load_entity(
                key,
                PipelineTemplate,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to find pipeline template {template_id}: {e}") from e
    
    async def find_by_name(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find template by name within current workspace.
        
        Args:
            name: Template name to search for
            
        Returns:
            Template if found, None otherwise
        """
        try:
            # Search by name in current workspace
            templates = await self._find_by_specification(
                ByNameSpecification(name)
            )
            
            # Return latest version if multiple versions exist
            if templates:
                return max(templates, key=lambda t: t.metadata.version)
            return None
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find pipeline template by name {name}: {e}") from e
    
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
        """
        try:
            # Search in specified workspace
            old_workspace = self.workspace
            self.workspace = workspace
            
            try:
                result = await self.find_by_name(name)
            finally:
                self.workspace = old_workspace
            
            return result
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find pipeline template {name} in workspace {workspace}: {e}"
            ) from e
    
    async def find_global_templates(self) -> List[PipelineTemplate]:
        """Find all global (system-wide) templates.
        
        Returns:
            List of global templates, empty if none found
        """
        try:
            return await self._find_by_specification(
                GlobalTemplateSpecification()
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to find global templates: {e}") from e
    
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
        """
        try:
            # Combine name and version specifications
            name_spec = ByNameSpecification(name)
            version_spec = ByVersionSpecification(version)
            
            templates = await self._find_by_specification(name_spec)
            
            # Filter by version
            for template in templates:
                if version_spec.is_satisfied_by(template):
                    return template
            
            return None
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find pipeline template {name} version {version}: {e}"
            ) from e
    
    async def find_latest_version(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find the latest version of a template.
        
        Args:
            name: Template name
            
        Returns:
            Latest template version if found, None otherwise
        """
        try:
            return await self.find_by_name(name)  # find_by_name already returns latest
        except StorageError as e:
            raise RepositoryError(f"Failed to find latest version of {name}: {e}") from e
    
    async def find_all_versions(self, name: PipelineName) -> List[PipelineTemplate]:
        """Find all versions of a template.
        
        Args:
            name: Template name
            
        Returns:
            List of all template versions, ordered by version
        """
        try:
            templates = await self._find_by_specification(
                ByNameSpecification(name)
            )
            
            # Sort by version (assuming semantic versioning)
            return sorted(templates, key=lambda t: t.metadata.version)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find all versions of {name}: {e}") from e
    
    async def search_by_tag(self, tag: str) -> List[PipelineTemplate]:
        """Search templates by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of templates with the tag
        """
        try:
            return await self._find_by_specification(
                ByTagSpecification(tag)
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to search templates by tag {tag}: {e}") from e
    
    async def search_by_description(self, query: str) -> List[PipelineTemplate]:
        """Search templates by description text.
        
        Args:
            query: Text to search for in descriptions
            
        Returns:
            List of templates matching the query
        """
        try:
            # Get all templates in workspace
            all_templates = await self.find_all()
            
            # Filter by description text
            query_lower = query.lower()
            matching_templates = [
                template for template in all_templates
                if query_lower in template.metadata.description.lower()
            ]
            
            return matching_templates
            
        except StorageError as e:
            raise RepositoryError(f"Failed to search templates by description: {e}") from e
    
    async def is_name_available(self, name: PipelineName) -> bool:
        """Check if template name is available in current workspace.
        
        Args:
            name: Template name to check
            
        Returns:
            True if name is available, False if taken
        """
        try:
            existing = await self.find_by_name(name)
            return existing is None
        except StorageError as e:
            raise RepositoryError(f"Failed to check name availability for {name}: {e}") from e
    
    async def validate_template(self, template: PipelineTemplate) -> List[str]:
        """Validate template structure and content.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        try:
            # Basic structure validation
            if not template.id:
                errors.append("Template ID is required")
            
            if not template.name or not template.name.value:
                errors.append("Template name is required")
            
            if not template.metadata:
                errors.append("Template metadata is required")
            else:
                if not template.metadata.description:
                    errors.append("Template description is required")
                if not template.metadata.version:
                    errors.append("Template version is required")
            
            if not template.steps:
                errors.append("Template must have at least one step")
            
            # Step validation
            for i, step in enumerate(template.steps):
                if not step.name:
                    errors.append(f"Step {i+1} must have a name")
                if not step.type:
                    errors.append(f"Step {i+1} must have a type")
                if not step.prompt_template or not step.prompt_template.template:
                    errors.append(f"Step {i+1} must have a prompt template")
            
            # Dependency validation
            step_names = {step.name.value for step in template.steps}
            for step in template.steps:
                for dep in step.dependencies:
                    if dep.value not in step_names:
                        errors.append(
                            f"Step '{step.name.value}' depends on unknown step '{dep.value}'"
                        )
            
            return errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return errors
    
    async def find_all(self) -> List[PipelineTemplate]:
        """Find all templates in current workspace.
        
        Returns:
            List of all templates in workspace
        """
        try:
            if self.workspace:
                return await self._find_by_specification(
                    ByWorkspaceSpecification(self.workspace)
                )
            else:
                # Global scope - find all templates
                prefix = "template:"
                return await self.storage.find_entities_by_prefix(
                    prefix,
                    PipelineTemplate,
                    self._db_name
                )
        except StorageError as e:
            raise RepositoryError(f"Failed to find all templates: {e}") from e
    
    async def delete(self, template_id: PipelineId) -> bool:
        """Delete a template.
        
        Args:
            template_id: ID of template to delete
            
        Returns:
            True if template was deleted, False if not found
        """
        try:
            key = self._make_key(template_id, self.workspace)
            
            # Remove from main storage
            deleted = await self.storage.delete_entity(key, self._db_name)
            
            # Clean up indices
            if deleted:
                await self._remove_from_indices(template_id)
            
            return deleted
            
        except StorageError as e:
            raise RepositoryError(f"Failed to delete template {template_id}: {e}") from e
    
    async def count(self) -> int:
        """Count templates in current workspace.
        
        Returns:
            Number of templates
        """
        try:
            if self.workspace:
                prefix = f"template:{self.workspace.value}:"
            else:
                prefix = "template:"
            
            return await self.storage.count_entities(prefix, self._db_name)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to count templates: {e}") from e
    
    def _make_key(self, template_id: PipelineId, workspace: Optional[WorkspaceName]) -> str:
        """Create storage key for template.
        
        Args:
            template_id: Template ID
            workspace: Workspace (None for global)
            
        Returns:
            Storage key
        """
        if workspace:
            return f"template:{workspace.value}:{template_id.value}"
        else:
            return f"template:global:{template_id.value}"
    
    async def _find_by_specification(self, spec) -> List[PipelineTemplate]:
        """Find templates matching specification.
        
        Args:
            spec: Specification to match
            
        Returns:
            List of matching templates
        """
        # For now, we'll use a simple approach of loading all and filtering
        # In production, this could be optimized with proper indexing
        
        if self.workspace:
            prefix = f"template:{self.workspace.value}:"
        else:
            prefix = "template:"
        
        all_templates = await self.storage.find_entities_by_prefix(
            prefix,
            PipelineTemplate,
            self._db_name
        )
        
        return [template for template in all_templates if spec.is_satisfied_by(template)]
    
    async def _update_indices(self, template: PipelineTemplate) -> None:
        """Update search indices for template.
        
        Args:
            template: Template to index
        """
        # For now, we'll skip complex indexing
        # This could be enhanced with dedicated index tables
        pass
    
    async def _remove_from_indices(self, template_id: PipelineId) -> None:
        """Remove template from search indices.
        
        Args:
            template_id: Template ID to remove
        """
        # For now, we'll skip complex indexing
        # This could be enhanced with dedicated index tables
        pass
