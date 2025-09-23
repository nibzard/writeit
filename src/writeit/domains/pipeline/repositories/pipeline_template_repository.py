"""Pipeline template repository interface.

Provides data access operations for pipeline templates including
CRUD operations, workspace-aware queries, and template validation.
"""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from ....shared.repository import WorkspaceAwareRepository, Specification
from ....domains.workspace.value_objects.workspace_name import WorkspaceName
from ..entities.pipeline_template import PipelineTemplate
from ..value_objects.pipeline_id import PipelineId
from ..value_objects.pipeline_name import PipelineName


class PipelineTemplateRepository(WorkspaceAwareRepository[PipelineTemplate]):
    """Repository for pipeline template persistence and retrieval.
    
    Handles CRUD operations for pipeline templates with workspace isolation,
    template validation, and advanced querying capabilities.
    """
    
    @abstractmethod
    async def find_by_name(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find template by name within current workspace.
        
        Args:
            name: Template name to search for
            
        Returns:
            Template if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def find_global_templates(self) -> List[PipelineTemplate]:
        """Find all global (system-wide) templates.
        
        Returns:
            List of global templates, empty if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def find_latest_version(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find the latest version of a template.
        
        Args:
            name: Template name
            
        Returns:
            Latest template version if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_all_versions(self, name: PipelineName) -> List[PipelineTemplate]:
        """Find all versions of a template.
        
        Args:
            name: Template name
            
        Returns:
            List of all template versions, ordered by version
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def search_by_tag(self, tag: str) -> List[PipelineTemplate]:
        """Search templates by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of templates with the tag
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def search_by_description(self, query: str) -> List[PipelineTemplate]:
        """Search templates by description text.
        
        Args:
            query: Text to search for in descriptions
            
        Returns:
            List of templates matching the query
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def is_name_available(self, name: PipelineName) -> bool:
        """Check if template name is available in current workspace.
        
        Args:
            name: Template name to check
            
        Returns:
            True if name is available, False if taken
            
        Raises:
            RepositoryError: If check operation fails
        """
        pass
    
    @abstractmethod
    async def validate_template(self, template: PipelineTemplate) -> List[str]:
        """Validate template structure and content.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        pass


# Specifications for pipeline template queries

class ByWorkspaceSpecification(Specification[PipelineTemplate]):
    """Specification for filtering templates by workspace."""
    
    def __init__(self, workspace: WorkspaceName):
        self.workspace = workspace
    
    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
        return template.workspace == self.workspace


class ByNameSpecification(Specification[PipelineTemplate]):
    """Specification for filtering templates by name."""
    
    def __init__(self, name: PipelineName):
        self.name = name
    
    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
        return template.name == self.name


class ByTagSpecification(Specification[PipelineTemplate]):
    """Specification for filtering templates by tag."""
    
    def __init__(self, tag: str):
        self.tag = tag
    
    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
        return self.tag in template.metadata.tags


class GlobalTemplateSpecification(Specification[PipelineTemplate]):
    """Specification for filtering global templates."""
    
    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
        return template.is_global


class ByVersionSpecification(Specification[PipelineTemplate]):
    """Specification for filtering templates by version."""
    
    def __init__(self, version: str):
        self.version = version
    
    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
        return template.metadata.version == self.version
