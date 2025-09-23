"""File system implementation of ContentTemplateRepository.

Provides template file management using file system operations
with file watching and dependency tracking.
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

from ...domains.content.repositories.content_template_repository import ContentTemplateRepository
from ...domains.content.entities.template import Template
from ...domains.content.value_objects.template_name import TemplateName
from ...domains.content.value_objects.content_type import ContentType
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError
from ..persistence.file_storage import FileSystemStorage
from ..base.exceptions import StorageError, ValidationError


class FileSystemContentTemplateRepository(ContentTemplateRepository):
    """File system-based implementation of ContentTemplateRepository.
    
    Manages content templates as files with metadata tracking,
    dependency resolution, and version management.
    """
    
    def __init__(self, storage: FileSystemStorage, workspace: Optional[WorkspaceName] = None):
        """Initialize repository.
        
        Args:
            storage: File system storage instance
            workspace: Current workspace (if None, uses global scope)
        """
        super().__init__(workspace)
        self.storage = storage
        self._template_extension = ".yaml"
        self._metadata_extension = ".meta.json"
    
    async def save(self, template: Template) -> None:
        """Save a content template.
        
        Args:
            template: Template to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            template_path = self._get_template_path(template.name)
            metadata_path = self._get_metadata_path(template.name)
            
            # Save template content
            await self.storage.write_yaml(template_path, template.content)
            
            # Save template metadata
            metadata = self._template_to_metadata(template)
            await self.storage.write_json(metadata_path, metadata)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to save template {template.name}: {e}") from e
    
    async def find_by_id(self, template_id: str) -> Optional[Template]:
        """Find template by ID.
        
        Args:
            template_id: Template ID to search for
            
        Returns:
            Template if found, None otherwise
        """
        try:
            # For file-based templates, ID is typically the template name
            template_name = TemplateName(template_id)
            return await self.find_by_name(template_name)
        except (StorageError, ValueError) as e:
            raise RepositoryError(f"Failed to find template by ID {template_id}: {e}") from e
    
    async def find_by_name(self, name: TemplateName) -> Optional[Template]:
        """Find template by name.
        
        Args:
            name: Template name to search for
            
        Returns:
            Template if found, None otherwise
        """
        try:
            template_path = self._get_template_path(name)
            metadata_path = self._get_metadata_path(name)
            
            # Check if template file exists
            if not await self.storage.file_exists(template_path):
                return None
            
            # Load template content
            content = await self.storage.read_yaml(template_path)
            
            # Load metadata if available
            metadata = {}
            if await self.storage.file_exists(metadata_path):
                metadata = await self.storage.read_json(metadata_path)
            
            return self._create_template_from_files(name, content, metadata)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find template by name {name}: {e}") from e
    
    async def find_by_type(self, content_type: ContentType) -> List[Template]:
        """Find templates by content type.
        
        Args:
            content_type: Content type to filter by
            
        Returns:
            List of templates with the content type
        """
        try:
            all_templates = await self.find_all()
            
            type_templates = [
                template for template in all_templates
                if template.content_type == content_type
            ]
            
            return type_templates
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find templates by type {content_type}: {e}") from e
    
    async def search_by_tags(self, tags: List[str]) -> List[Template]:
        """Search templates by tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            List of templates containing any of the tags
        """
        try:
            all_templates = await self.find_all()
            
            tagged_templates = []
            for template in all_templates:
                if any(tag in template.metadata.tags for tag in tags):
                    tagged_templates.append(template)
            
            return tagged_templates
            
        except StorageError as e:
            raise RepositoryError(f"Failed to search templates by tags {tags}: {e}") from e
    
    async def find_global_templates(self) -> List[Template]:
        """Find all global (system-wide) templates.
        
        Returns:
            List of global templates
        """
        try:
            # Switch to global scope temporarily
            old_workspace = self.workspace
            self.workspace = None
            
            try:
                return await self.find_all()
            finally:
                self.workspace = old_workspace
                
        except StorageError as e:
            raise RepositoryError(f"Failed to find global templates: {e}") from e
    
    async def find_template_dependencies(self, template: Template) -> List[Template]:
        """Find templates that this template depends on.
        
        Args:
            template: Template to analyze
            
        Returns:
            List of dependency templates
        """
        try:
            dependencies = []
            
            # Extract dependency names from template metadata
            dependency_names = template.metadata.dependencies
            
            for dep_name in dependency_names:
                dep_template = await self.find_by_name(TemplateName(dep_name))
                if dep_template:
                    dependencies.append(dep_template)
            
            return dependencies
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find dependencies for template {template.name}: {e}"
            ) from e
    
    async def find_dependent_templates(self, template: Template) -> List[Template]:
        """Find templates that depend on this template.
        
        Args:
            template: Template to analyze
            
        Returns:
            List of dependent templates
        """
        try:
            all_templates = await self.find_all()
            
            dependents = []
            for other_template in all_templates:
                if template.name.value in other_template.metadata.dependencies:
                    dependents.append(other_template)
            
            return dependents
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find dependents for template {template.name}: {e}"
            ) from e
    
    async def validate_template_content(self, template: Template) -> List[str]:
        """Validate template content and structure.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        try:
            # Basic structure validation
            if not template.name or not template.name.value:
                errors.append("Template name is required")
            
            if not template.content:
                errors.append("Template content is required")
            
            # Content type validation
            if not template.content_type:
                errors.append("Content type is required")
            
            # Metadata validation
            if template.metadata:
                if not template.metadata.description:
                    errors.append("Template description is recommended")
                
                # Validate dependencies exist
                for dep_name in template.metadata.dependencies:
                    dep_template = await self.find_by_name(TemplateName(dep_name))
                    if not dep_template:
                        errors.append(f"Dependency template not found: {dep_name}")
            
            # Content validation (basic YAML structure)
            if template.content:
                try:
                    # Validate that content is proper YAML/dict structure
                    if not isinstance(template.content, dict):
                        errors.append("Template content must be a dictionary structure")
                except Exception as e:
                    errors.append(f"Invalid template content structure: {e}")
            
            return errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return errors
    
    async def is_name_available(self, name: TemplateName) -> bool:
        """Check if template name is available.
        
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
    
    async def find_all(self) -> List[Template]:
        """Find all templates in current workspace.
        
        Returns:
            List of all templates
        """
        try:
            templates = []
            
            # Get template directory
            template_dir = self._get_template_directory()
            
            # List all template files
            pattern = f"*{self._template_extension}"
            template_files = await self.storage.list_files(template_dir, pattern)
            
            for template_file in template_files:
                # Extract template name from filename
                name_str = template_file.stem
                template_name = TemplateName(name_str)
                
                # Load template
                template = await self.find_by_name(template_name)
                if template:
                    templates.append(template)
            
            return templates
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find all templates: {e}") from e
    
    async def delete(self, template_id: str) -> bool:
        """Delete a template.
        
        Args:
            template_id: ID of template to delete
            
        Returns:
            True if template was deleted, False if not found
        """
        try:
            template_name = TemplateName(template_id)
            template_path = self._get_template_path(template_name)
            metadata_path = self._get_metadata_path(template_name)
            
            # Delete template file
            template_deleted = await self.storage.delete_file(template_path)
            
            # Delete metadata file if it exists
            if await self.storage.file_exists(metadata_path):
                await self.storage.delete_file(metadata_path)
            
            return template_deleted
            
        except (StorageError, ValueError) as e:
            raise RepositoryError(f"Failed to delete template {template_id}: {e}") from e
    
    async def count(self) -> int:
        """Count templates in current workspace.
        
        Returns:
            Number of templates
        """
        try:
            templates = await self.find_all()
            return len(templates)
        except StorageError as e:
            raise RepositoryError(f"Failed to count templates: {e}") from e
    
    def _get_template_directory(self) -> Path:
        """Get template directory path.
        
        Returns:
            Path to template directory
        """
        if self.workspace:
            return Path("workspaces") / self.workspace.value / "templates"
        else:
            return Path("global") / "templates"
    
    def _get_template_path(self, name: TemplateName) -> Path:
        """Get full path for template file.
        
        Args:
            name: Template name
            
        Returns:
            Full path to template file
        """
        template_dir = self._get_template_directory()
        return template_dir / f"{name.value}{self._template_extension}"
    
    def _get_metadata_path(self, name: TemplateName) -> Path:
        """Get full path for metadata file.
        
        Args:
            name: Template name
            
        Returns:
            Full path to metadata file
        """
        template_dir = self._get_template_directory()
        return template_dir / f"{name.value}{self._metadata_extension}"
    
    def _template_to_metadata(self, template: Template) -> Dict[str, Any]:
        """Convert template to metadata dictionary.
        
        Args:
            template: Template to convert
            
        Returns:
            Metadata dictionary
        """
        return {
            "id": str(template.id),
            "name": template.name.value,
            "content_type": template.content_type.value,
            "version": template.version,
            "description": template.metadata.description if template.metadata else "",
            "tags": template.metadata.tags if template.metadata else [],
            "dependencies": template.metadata.dependencies if template.metadata else [],
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
    
    def _create_template_from_files(
        self,
        name: TemplateName,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Template:
        """Create template from file content and metadata.
        
        Args:
            name: Template name
            content: Template content
            metadata: Template metadata
            
        Returns:
            Template instance
        """
        from uuid import UUID
        from datetime import datetime
        from ...domains.content.entities.template_metadata import TemplateMetadata
        
        # Parse metadata
        template_id = UUID(metadata.get("id", str(name.value)))
        content_type = ContentType(metadata.get("content_type", "text"))
        version = metadata.get("version", "1.0.0")
        
        created_at = None
        if metadata.get("created_at"):
            created_at = datetime.fromisoformat(metadata["created_at"])
        
        updated_at = None
        if metadata.get("updated_at"):
            updated_at = datetime.fromisoformat(metadata["updated_at"])
        
        template_metadata = TemplateMetadata(
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            dependencies=metadata.get("dependencies", [])
        )
        
        return Template(
            id=template_id,
            name=name,
            content=content,
            content_type=content_type,
            version=version,
            metadata=template_metadata,
            workspace=self.workspace,
            created_at=created_at,
            updated_at=updated_at
        )
