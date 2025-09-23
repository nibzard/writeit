"""Content template repository interface.

Provides data access operations for content templates including
file management, validation, and template resolution.
"""

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ....shared.repository import WorkspaceAwareRepository, Specification
from ....domains.workspace.value_objects.workspace_name import WorkspaceName
from ..entities.template import Template
from ..value_objects.template_name import TemplateName
from ..value_objects.content_type import ContentType
from ..value_objects.content_format import ContentFormat


class ContentTemplateRepository(WorkspaceAwareRepository[Template]):
    """Repository for content template persistence and retrieval.
    
    Handles CRUD operations for content templates with file management,
    validation, and workspace-aware template resolution.
    """
    
    @abstractmethod
    async def find_by_name(self, name: TemplateName) -> Optional[Template]:
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
        name: TemplateName, 
        workspace: WorkspaceName
    ) -> Optional[Template]:
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
    async def find_by_content_type(self, content_type: ContentType) -> List[Template]:
        """Find templates by content type.
        
        Args:
            content_type: Content type to filter by
            
        Returns:
            List of templates with the content type
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_format(self, format: ContentFormat) -> List[Template]:
        """Find templates by output format.
        
        Args:
            format: Content format to filter by
            
        Returns:
            List of templates with the format
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_global_templates(self) -> List[Template]:
        """Find all global (system-wide) templates.
        
        Returns:
            List of global templates, empty if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def search_by_tag(self, tag: str) -> List[Template]:
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
    async def search_by_description(self, query: str) -> List[Template]:
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
    async def find_templates_using_variable(self, variable: str) -> List[Template]:
        """Find templates that use a specific variable.
        
        Args:
            variable: Variable name to search for
            
        Returns:
            List of templates using the variable
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def load_template_content(self, template: Template) -> str:
        """Load template content from file system.
        
        Args:
            template: Template to load content for
            
        Returns:
            Template content as string
            
        Raises:
            EntityNotFoundError: If template file not found
            RepositoryError: If content loading fails
        """
        pass
    
    @abstractmethod
    async def save_template_content(
        self, 
        template: Template, 
        content: str
    ) -> None:
        """Save template content to file system.
        
        Args:
            template: Template to save content for
            content: Template content to save
            
        Raises:
            RepositoryError: If content saving fails
        """
        pass
    
    @abstractmethod
    async def validate_template_syntax(self, template: Template) -> List[str]:
        """Validate template syntax and structure.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        pass
    
    @abstractmethod
    async def get_template_variables(self, template: Template) -> List[str]:
        """Extract variables used in template.
        
        Args:
            template: Template to analyze
            
        Returns:
            List of variable names used in template
            
        Raises:
            RepositoryError: If analysis operation fails
        """
        pass
    
    @abstractmethod
    async def get_template_dependencies(self, template: Template) -> List[TemplateName]:
        """Get templates that this template depends on.
        
        Args:
            template: Template to analyze dependencies for
            
        Returns:
            List of template names this template depends on
            
        Raises:
            RepositoryError: If dependency analysis fails
        """
        pass
    
    @abstractmethod
    async def get_template_dependents(self, template: Template) -> List[TemplateName]:
        """Get templates that depend on this template.
        
        Args:
            template: Template to analyze dependents for
            
        Returns:
            List of template names that depend on this template
            
        Raises:
            RepositoryError: If dependent analysis fails
        """
        pass
    
    @abstractmethod
    async def copy_template(
        self, 
        source: Template, 
        target_name: TemplateName, 
        target_workspace: Optional[WorkspaceName] = None
    ) -> Template:
        """Copy template to new name/workspace.
        
        Args:
            source: Source template to copy
            target_name: New template name
            target_workspace: Target workspace, defaults to current
            
        Returns:
            New template copy
            
        Raises:
            EntityAlreadyExistsError: If target already exists
            RepositoryError: If copy operation fails
        """
        pass
    
    @abstractmethod
    async def get_template_usage_stats(self, template: Template) -> Dict[str, Any]:
        """Get template usage statistics.
        
        Args:
            template: Template to get stats for
            
        Returns:
            Dictionary with usage statistics:
            - total_uses: Total number of times used
            - recent_uses: Uses in last 30 days
            - last_used: Last usage timestamp
            - common_variables: Most commonly used variables
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass


# Specifications for content template queries

class ByContentTypeSpecification(Specification[Template]):
    """Specification for filtering templates by content type."""
    
    def __init__(self, content_type: ContentType):
        self.content_type = content_type
    
    def is_satisfied_by(self, template: Template) -> bool:
        return template.content_type == self.content_type


class ByFormatSpecification(Specification[Template]):
    """Specification for filtering templates by format."""
    
    def __init__(self, format: ContentFormat):
        self.format = format
    
    def is_satisfied_by(self, template: Template) -> bool:
        return template.format == self.format


class ByTagSpecification(Specification[Template]):
    """Specification for filtering templates by tag."""
    
    def __init__(self, tag: str):
        self.tag = tag
    
    def is_satisfied_by(self, template: Template) -> bool:
        return self.tag in template.tags


class GlobalTemplateSpecification(Specification[Template]):
    """Specification for filtering global templates."""
    
    def is_satisfied_by(self, template: Template) -> bool:
        return template.is_global


class UsesVariableSpecification(Specification[Template]):
    """Specification for filtering templates that use a variable."""
    
    def __init__(self, variable: str):
        self.variable = variable
    
    def is_satisfied_by(self, template: Template) -> bool:
        # This would need access to template content analysis
        # Implementation would check if variable is used in template
        return self.variable in template.variables


class PublishedTemplatesSpecification(Specification[Template]):
    """Specification for filtering published templates."""
    
    def __init__(self):
        pass
    
    def is_satisfied_by(self, template: Template) -> bool:
        return template.is_published
