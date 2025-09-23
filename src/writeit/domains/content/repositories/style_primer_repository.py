"""Style primer repository interface.

Provides data access operations for style primers including
style management, validation, and primer resolution.
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any

from ....shared.repository import WorkspaceAwareRepository, Specification
from ....domains.workspace.value_objects.workspace_name import WorkspaceName
from ..entities.style_primer import StylePrimer
from ..value_objects.style_name import StyleName
from ..value_objects.content_type import ContentType


class StylePrimerRepository(WorkspaceAwareRepository[StylePrimer]):
    """Repository for style primer persistence and retrieval.
    
    Handles CRUD operations for style primers with validation,
    inheritance, and workspace-aware style resolution.
    """
    
    @abstractmethod
    async def find_by_name(self, name: StyleName) -> Optional[StylePrimer]:
        """Find style primer by name within current workspace.
        
        Args:
            name: Style name to search for
            
        Returns:
            Style primer if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_name_and_workspace(
        self, 
        name: StyleName, 
        workspace: WorkspaceName
    ) -> Optional[StylePrimer]:
        """Find style primer by name in specific workspace.
        
        Args:
            name: Style name to search for
            workspace: Workspace to search in
            
        Returns:
            Style primer if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_content_type(self, content_type: ContentType) -> List[StylePrimer]:
        """Find style primers applicable to content type.
        
        Args:
            content_type: Content type to filter by
            
        Returns:
            List of style primers for the content type
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_global_styles(self) -> List[StylePrimer]:
        """Find all global (system-wide) style primers.
        
        Returns:
            List of global style primers, empty if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_category(self, category: str) -> List[StylePrimer]:
        """Find style primers by category.
        
        Args:
            category: Style category to filter by
            
        Returns:
            List of style primers in the category
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def search_by_tag(self, tag: str) -> List[StylePrimer]:
        """Search style primers by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of style primers with the tag
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def search_by_description(self, query: str) -> List[StylePrimer]:
        """Search style primers by description text.
        
        Args:
            query: Text to search for in descriptions
            
        Returns:
            List of style primers matching the query
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_compatible_styles(
        self, 
        content_type: ContentType, 
        tone: Optional[str] = None
    ) -> List[StylePrimer]:
        """Find style primers compatible with content type and tone.
        
        Args:
            content_type: Content type to match
            tone: Optional tone to filter by
            
        Returns:
            List of compatible style primers
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_style_inheritance_chain(
        self, 
        style: StylePrimer
    ) -> List[StylePrimer]:
        """Get style inheritance chain (parent styles).
        
        Args:
            style: Style to get inheritance chain for
            
        Returns:
            List of parent styles in inheritance order
            
        Raises:
            RepositoryError: If chain resolution fails
        """
        pass
    
    @abstractmethod
    async def get_derived_styles(
        self, 
        style: StylePrimer
    ) -> List[StylePrimer]:
        """Get styles that inherit from this style.
        
        Args:
            style: Style to get derived styles for
            
        Returns:
            List of styles that inherit from this style
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def validate_style_consistency(
        self, 
        style: StylePrimer
    ) -> List[str]:
        """Validate style primer consistency and guidelines.
        
        Args:
            style: Style primer to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        pass
    
    @abstractmethod
    async def merge_style_guidelines(
        self, 
        base_style: StylePrimer, 
        override_style: StylePrimer
    ) -> Dict[str, Any]:
        """Merge style guidelines from two styles.
        
        Args:
            base_style: Base style primer
            override_style: Override style primer
            
        Returns:
            Merged style guidelines
            
        Raises:
            RepositoryError: If merge operation fails
        """
        pass
    
    @abstractmethod
    async def apply_style_to_content(
        self, 
        style: StylePrimer, 
        content: str, 
        content_type: ContentType
    ) -> str:
        """Apply style primer guidelines to content.
        
        Args:
            style: Style primer to apply
            content: Content to style
            content_type: Type of content
            
        Returns:
            Styled content
            
        Raises:
            RepositoryError: If styling operation fails
        """
        pass
    
    @abstractmethod
    async def copy_style(
        self, 
        source: StylePrimer, 
        target_name: StyleName, 
        target_workspace: Optional[WorkspaceName] = None
    ) -> StylePrimer:
        """Copy style primer to new name/workspace.
        
        Args:
            source: Source style to copy
            target_name: New style name
            target_workspace: Target workspace, defaults to current
            
        Returns:
            New style copy
            
        Raises:
            EntityAlreadyExistsError: If target already exists
            RepositoryError: If copy operation fails
        """
        pass
    
    @abstractmethod
    async def get_style_usage_stats(self, style: StylePrimer) -> Dict[str, Any]:
        """Get style primer usage statistics.
        
        Args:
            style: Style primer to get stats for
            
        Returns:
            Dictionary with usage statistics:
            - total_uses: Total number of times used
            - recent_uses: Uses in last 30 days
            - last_used: Last usage timestamp
            - popular_content_types: Most common content types used with
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass


# Specifications for style primer queries

class ByContentTypeSpecification(Specification[StylePrimer]):
    """Specification for filtering style primers by content type."""
    
    def __init__(self, content_type: ContentType):
        self.content_type = content_type
    
    def is_satisfied_by(self, style: StylePrimer) -> bool:
        return self.content_type in style.applicable_content_types


class ByCategorySpecification(Specification[StylePrimer]):
    """Specification for filtering style primers by category."""
    
    def __init__(self, category: str):
        self.category = category
    
    def is_satisfied_by(self, style: StylePrimer) -> bool:
        return style.category == self.category


class ByTagSpecification(Specification[StylePrimer]):
    """Specification for filtering style primers by tag."""
    
    def __init__(self, tag: str):
        self.tag = tag
    
    def is_satisfied_by(self, style: StylePrimer) -> bool:
        return self.tag in style.tags


class GlobalStyleSpecification(Specification[StylePrimer]):
    """Specification for filtering global style primers."""
    
    def is_satisfied_by(self, style: StylePrimer) -> bool:
        return style.is_global


class ByToneSpecification(Specification[StylePrimer]):
    """Specification for filtering style primers by tone."""
    
    def __init__(self, tone: str):
        self.tone = tone
    
    def is_satisfied_by(self, style: StylePrimer) -> bool:
        return style.tone == self.tone


class InheritsFromSpecification(Specification[StylePrimer]):
    """Specification for filtering style primers that inherit from another style."""
    
    def __init__(self, parent_style: StylePrimer):
        self.parent_style = parent_style
    
    def is_satisfied_by(self, style: StylePrimer) -> bool:
        return style.parent_style == self.parent_style
