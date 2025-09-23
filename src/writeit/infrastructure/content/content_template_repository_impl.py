"""LMDB implementation of ContentTemplateRepository.

Provides concrete LMDB-backed storage for content templates with
workspace isolation, versioning, and template management capabilities.
"""

from typing import List, Optional, Any
from datetime import datetime

from ...domains.content.repositories.content_template_repository import (
    ContentTemplateRepository,
    ByContentTypeSpecification,
    ByTagSpecification,
    PublishedTemplatesSpecification,
    ByAuthorSpecification,
    ByFormatSpecification,
    RecentTemplatesSpecification
)
from ...domains.content.entities.template import Template
from ...domains.content.value_objects.content_id import ContentId
from ...domains.content.value_objects.template_name import TemplateName
from ...domains.content.value_objects.content_type import ContentType
from ...domains.content.value_objects.content_format import ContentFormat
from ...domains.content.value_objects.validation_rule import ValidationRule
from ...domains.content.value_objects.content_length import ContentLength
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBContentTemplateRepository(LMDBRepositoryBase[Template], ContentTemplateRepository):
    """LMDB implementation of ContentTemplateRepository.
    
    Stores content templates with workspace isolation and provides
    comprehensive template management with versioning and tagging.
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
            entity_type=Template,
            db_name="content_templates",
            db_key="templates"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with template-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        # Register value objects
        serializer.register_value_object(ContentId)
        serializer.register_value_object(TemplateName)
        serializer.register_value_object(ContentType)
        serializer.register_value_object(ContentFormat)
        serializer.register_value_object(ValidationRule)
        serializer.register_value_object(ContentLength)
        serializer.register_value_object(WorkspaceName)
        
        # Register entity types
        serializer.register_type("Template", Template)
    
    def _get_entity_id(self, entity: Template) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Template entity
            
        Returns:
            Entity identifier
        """
        return entity.id
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier (ContentId)
            
        Returns:
            Storage key string
        """
        workspace_prefix = self._get_workspace_prefix()
        if isinstance(entity_id, ContentId):
            return f"{workspace_prefix}template:{entity_id.value}"
        else:
            return f"{workspace_prefix}template:{str(entity_id)}"
    
    async def find_by_name(self, name: TemplateName) -> Optional[Template]:
        """Find template by name within current workspace.
        
        Args:
            name: Template name to search for
            
        Returns:
            Template if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_templates = await self.find_by_workspace()
        for template in all_templates:
            if template.name == name:
                return template
        return None
    
    async def find_by_content_type(self, content_type: ContentType) -> List[Template]:
        """Find templates by content type.
        
        Args:
            content_type: Content type to filter by
            
        Returns:
            List of templates for the content type
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByContentTypeSpecification(content_type)
        return await self.find_by_specification(spec)
    
    async def find_by_tag(self, tag: str) -> List[Template]:
        """Find templates by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of templates with the tag
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByTagSpecification(tag)
        return await self.find_by_specification(spec)
    
    async def find_published_templates(self) -> List[Template]:
        """Find all published templates in current workspace.
        
        Returns:
            List of published templates
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = PublishedTemplatesSpecification()
        return await self.find_by_specification(spec)
    
    async def find_by_author(self, author: str) -> List[Template]:
        """Find templates by author.
        
        Args:
            author: Author to search for
            
        Returns:
            List of templates by the author
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByAuthorSpecification(author)
        return await self.find_by_specification(spec)
    
    async def find_by_output_format(self, format_type: ContentFormat) -> List[Template]:
        """Find templates by output format.
        
        Args:
            format_type: Output format to filter by
            
        Returns:
            List of templates with the output format
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByFormatSpecification(format_type)
        return await self.find_by_specification(spec)
    
    async def find_recent_templates(self, days: int = 7) -> List[Template]:
        """Find recently created or updated templates.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent templates, ordered by update time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        since = datetime.now() - timedelta(days=days)
        spec = RecentTemplatesSpecification(since)
        templates = await self.find_by_specification(spec)
        
        # Sort by updated_at (newest first)
        templates.sort(key=lambda t: t.updated_at, reverse=True)
        return templates
    
    async def find_popular_templates(self, limit: int = 10) -> List[Template]:
        """Find most used templates.
        
        Args:
            limit: Maximum number of templates to return
            
        Returns:
            List of templates ordered by usage count desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_templates = await self.find_by_workspace()
        
        # Filter published templates and sort by usage
        published_templates = [t for t in all_templates if t.is_published]
        published_templates.sort(key=lambda t: t.usage_count, reverse=True)
        
        return published_templates[:limit]
    
    async def search_templates(
        self, 
        query: str, 
        search_fields: Optional[List[str]] = None
    ) -> List[Template]:
        """Search templates by text query.
        
        Args:
            query: Search query string
            search_fields: Fields to search in (default: name, description, tags)
            
        Returns:
            List of matching templates
            
        Raises:
            RepositoryError: If search operation fails
        """
        if search_fields is None:
            search_fields = ["name", "description", "tags"]
        
        all_templates = await self.find_by_workspace()
        matching_templates = []
        query_lower = query.lower()
        
        for template in all_templates:
            matches = False
            
            # Search in name
            if "name" in search_fields and query_lower in template.name.value.lower():
                matches = True
            
            # Search in description
            if "description" in search_fields and template.description:
                if query_lower in template.description.lower():
                    matches = True
            
            # Search in tags
            if "tags" in search_fields:
                for tag in template.tags:
                    if query_lower in tag.lower():
                        matches = True
                        break
            
            # Search in YAML content
            if "content" in search_fields and query_lower in template.yaml_content.lower():
                matches = True
            
            if matches:
                matching_templates.append(template)
        
        return matching_templates
    
    async def get_template_versions(self, name: TemplateName) -> List[Template]:
        """Get all versions of a template.
        
        Args:
            name: Template name
            
        Returns:
            List of template versions, ordered by version
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_templates = await self.find_by_workspace()
        versions = [t for t in all_templates if t.name == name]
        
        # Sort by version (simple string comparison for now)
        versions.sort(key=lambda t: t.version)
        return versions
    
    async def get_latest_version(self, name: TemplateName) -> Optional[Template]:
        """Get the latest version of a template.
        
        Args:
            name: Template name
            
        Returns:
            Latest template version if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        versions = await self.get_template_versions(name)
        return versions[-1] if versions else None
    
    async def is_name_available(self, name: TemplateName) -> bool:
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
    
    async def validate_template_yaml(self, yaml_content: str) -> List[str]:
        """Validate template YAML structure and content.
        
        Args:
            yaml_content: YAML content to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        errors = []
        
        try:
            import yaml
            
            # Basic YAML parsing
            try:
                parsed = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {e}")
                return errors
            
            if not isinstance(parsed, dict):
                errors.append("YAML must be a dictionary/object")
                return errors
            
            # Check required sections
            required_sections = ["metadata", "steps"]
            for section in required_sections:
                if section not in parsed:
                    errors.append(f"Missing required section: {section}")
            
            # Validate metadata
            if "metadata" in parsed:
                metadata = parsed["metadata"]
                if not isinstance(metadata, dict):
                    errors.append("Metadata must be a dictionary")
                else:
                    required_metadata = ["name", "description"]
                    for field in required_metadata:
                        if field not in metadata:
                            errors.append(f"Missing required metadata field: {field}")
            
            # Validate steps
            if "steps" in parsed:
                steps = parsed["steps"]
                if not isinstance(steps, dict):
                    errors.append("Steps must be a dictionary")
                elif not steps:
                    errors.append("Template must have at least one step")
                else:
                    for step_name, step_config in steps.items():
                        if not isinstance(step_config, dict):
                            errors.append(f"Step '{step_name}' must be a dictionary")
                            continue
                        
                        # Check required step fields
                        required_step_fields = ["name", "type"]
                        for field in required_step_fields:
                            if field not in step_config:
                                errors.append(f"Step '{step_name}' missing required field: {field}")
        
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    async def get_template_statistics(self) -> dict:
        """Get template usage statistics for current workspace.
        
        Returns:
            Dictionary with template statistics
            
        Raises:
            RepositoryError: If statistics calculation fails
        """
        all_templates = await self.find_by_workspace()
        
        if not all_templates:
            return {
                "total_templates": 0,
                "published_templates": 0,
                "draft_templates": 0,
                "deprecated_templates": 0,
                "total_usage": 0,
                "most_popular": None,
                "content_types": {},
                "authors": {},
                "tags": {}
            }
        
        # Calculate statistics
        published = [t for t in all_templates if t.is_published]
        deprecated = [t for t in all_templates if t.is_deprecated]
        draft = [t for t in all_templates if not t.is_published and not t.is_deprecated]
        
        total_usage = sum(t.usage_count for t in all_templates)
        most_popular = max(all_templates, key=lambda t: t.usage_count) if all_templates else None
        
        # Count by content type
        content_types = {}
        for template in all_templates:
            content_type = str(template.content_type)
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Count by author
        authors = {}
        for template in all_templates:
            if template.author:
                authors[template.author] = authors.get(template.author, 0) + 1
        
        # Count tags
        tags = {}
        for template in all_templates:
            for tag in template.tags:
                tags[tag] = tags.get(tag, 0) + 1
        
        return {
            "total_templates": len(all_templates),
            "published_templates": len(published),
            "draft_templates": len(draft),
            "deprecated_templates": len(deprecated),
            "total_usage": total_usage,
            "most_popular": str(most_popular.name) if most_popular else None,
            "content_types": content_types,
            "authors": authors,
            "tags": dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10])  # Top 10 tags
        }
    
    async def cleanup_deprecated_templates(self, older_than_days: int = 30) -> int:
        """Clean up old deprecated templates.
        
        Args:
            older_than_days: Delete templates deprecated more than this many days ago
            
        Returns:
            Number of templates deleted
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        all_templates = await self.find_by_workspace()
        
        old_deprecated = [
            template for template in all_templates
            if template.is_deprecated and 
               template.deprecated_at and 
               template.deprecated_at < cutoff_date
        ]
        
        deleted_count = 0
        for template in old_deprecated:
            if await self.delete_by_id(template.id):
                deleted_count += 1
        
        return deleted_count
    
    async def duplicate_template(
        self, 
        template: Template, 
        new_name: TemplateName, 
        author: Optional[str] = None
    ) -> Template:
        """Create a duplicate of an existing template.
        
        Args:
            template: Template to duplicate
            new_name: Name for the new template
            author: Author of the duplicate
            
        Returns:
            New template instance
            
        Raises:
            EntityAlreadyExistsError: If new name already exists
            RepositoryError: If duplication fails
        """
        from ...shared.repository import EntityAlreadyExistsError
        
        if not await self.is_name_available(new_name):
            raise EntityAlreadyExistsError("Template", new_name)
        
        duplicate = Template.create(
            name=new_name,
            content_type=template.content_type,
            yaml_content=template.yaml_content,
            author=author or template.author,
            description=f"Copy of {template.name}",
            tags=template.tags.copy(),
            output_format=template.output_format,
            content_length=template.content_length,
            validation_rules=template.validation_rules.copy()
        )
        
        await self.save(duplicate)
        return duplicate
    
    async def export_template(self, template: Template) -> dict:
        """Export template for backup or sharing.
        
        Args:
            template: Template to export
            
        Returns:
            Exportable template data
        """
        return {
            "name": template.name.value,
            "content_type": str(template.content_type),
            "yaml_content": template.yaml_content,
            "version": template.version,
            "author": template.author,
            "description": template.description,
            "tags": template.tags,
            "output_format": str(template.output_format) if template.output_format else None,
            "content_length": {
                "min_words": template.content_length.min_words,
                "max_words": template.content_length.max_words,
                "min_chars": template.content_length.min_chars,
                "max_chars": template.content_length.max_chars
            } if template.content_length else None,
            "validation_rules": [
                {
                    "rule_type": rule.rule_type,
                    "parameters": rule.parameters
                } for rule in template.validation_rules
            ],
            "metadata": template.metadata,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }