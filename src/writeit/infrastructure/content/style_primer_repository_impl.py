"""LMDB implementation of StylePrimerRepository.

Provides concrete LMDB-backed storage for style primers with
workspace isolation and style management capabilities.
"""

from typing import List, Optional, Any
from datetime import datetime, timedelta

from ...domains.content.repositories.style_primer_repository import StylePrimerRepository
from ...domains.content.entities.style_primer import StylePrimer
from ...domains.content.value_objects.content_id import ContentId
from ...domains.content.value_objects.style_name import StyleName
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBStylePrimerRepository(LMDBRepositoryBase[StylePrimer], StylePrimerRepository):
    """LMDB implementation of StylePrimerRepository.
    
    Stores style primers with workspace isolation and provides
    comprehensive style management capabilities.
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
            entity_type=StylePrimer,
            db_name="style_primers",
            db_key="primers"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with style primer-specific types."""
        serializer.register_value_object(ContentId)
        serializer.register_value_object(StyleName)
        serializer.register_value_object(WorkspaceName)
        serializer.register_type("StylePrimer", StylePrimer)
    
    def _get_entity_id(self, entity: StylePrimer) -> Any:
        """Extract entity ID for storage key."""
        return entity.id
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID."""
        workspace_prefix = self._get_workspace_prefix()
        if isinstance(entity_id, ContentId):
            return f"{workspace_prefix}primer:{entity_id.value}"
        else:
            return f"{workspace_prefix}primer:{str(entity_id)}"
    
    async def find_by_name(self, name: StyleName) -> Optional[StylePrimer]:
        """Find style primer by name within current workspace."""
        all_primers = await self.find_by_workspace()
        for primer in all_primers:
            if primer.name == name:
                return primer
        return None
    
    async def find_by_category(self, category: str) -> List[StylePrimer]:
        """Find style primers by category."""
        all_primers = await self.find_by_workspace()
        return [p for p in all_primers if p.category == category]
    
    async def find_active_primers(self) -> List[StylePrimer]:
        """Find all active (non-deprecated) style primers."""
        all_primers = await self.find_by_workspace()
        return [p for p in all_primers if not p.is_deprecated]
    
    async def search_primers(self, query: str) -> List[StylePrimer]:
        """Search style primers by text query."""
        all_primers = await self.find_by_workspace()
        query_lower = query.lower()
        
        return [
            primer for primer in all_primers
            if (query_lower in primer.name.value.lower() or
                (primer.description and query_lower in primer.description.lower()) or
                any(query_lower in tag.lower() for tag in primer.tags))
        ]
    
    async def get_popular_primers(self, limit: int = 10) -> List[StylePrimer]:
        """Find most used style primers."""
        all_primers = await self.find_by_workspace()
        active_primers = [p for p in all_primers if not p.is_deprecated]
        active_primers.sort(key=lambda p: p.usage_count, reverse=True)
        return active_primers[:limit]
    
    async def get_primer_statistics(self) -> dict:
        """Get style primer usage statistics."""
        all_primers = await self.find_by_workspace()
        
        if not all_primers:
            return {
                "total_primers": 0,
                "active_primers": 0,
                "deprecated_primers": 0,
                "categories": {},
                "total_usage": 0
            }
        
        active = [p for p in all_primers if not p.is_deprecated]
        deprecated = [p for p in all_primers if p.is_deprecated]
        
        categories = {}
        for primer in all_primers:
            if primer.category:
                categories[primer.category] = categories.get(primer.category, 0) + 1
        
        return {
            "total_primers": len(all_primers),
            "active_primers": len(active),
            "deprecated_primers": len(deprecated),
            "categories": categories,
            "total_usage": sum(p.usage_count for p in all_primers)
        }