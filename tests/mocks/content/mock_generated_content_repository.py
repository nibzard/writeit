"""Mock implementation of GeneratedContentRepository for testing."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from writeit.domains.content.repositories.generated_content_repository import GeneratedContentRepository
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockGeneratedContentRepository(BaseMockRepository[GeneratedContent], GeneratedContentRepository):
    """Mock implementation of GeneratedContentRepository.
    
    Provides in-memory storage for generated content with content management
    and analytics support.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        super().__init__(str(workspace_name.value))
        self._workspace_name_obj = workspace_name
        
    def _get_entity_id(self, entity: GeneratedContent) -> Any:
        """Extract entity ID from generated content."""
        return str(entity.id)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "GeneratedContent"
        
    # Repository interface implementation
    
    async def save(self, entity: GeneratedContent) -> None:
        """Save or update generated content."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id)
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: UUID) -> Optional[GeneratedContent]:
        """Find generated content by ID."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        content = self._get_entity(str(entity_id))
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id), found=content is not None)
        return content
        
    async def find_all(self) -> List[GeneratedContent]:
        """Find all generated content in current workspace."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        contents = self._get_all_entities()
        self._log_event("find_all", self._get_entity_type_name(), count=len(contents))
        return contents
        
    async def find_by_specification(self, spec: Specification[GeneratedContent]) -> List[GeneratedContent]:
        """Find generated content matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        contents = self._find_entities_by_specification(spec)
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(contents))
        return contents
        
    async def exists(self, entity_id: UUID) -> bool:
        """Check if generated content exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id))
        self._log_event("exists", self._get_entity_type_name(), str(entity_id), exists=exists)
        return exists
        
    async def delete(self, entity: GeneratedContent) -> None:
        """Delete generated content."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete generated content by ID."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id))
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total generated content."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities()
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[GeneratedContent]:
        """Implementation-specific workspace query."""
        return self._get_all_entities(str(workspace.value))
        
    # GeneratedContentRepository-specific methods
    
    async def find_by_pipeline_run(self, run_id: UUID) -> List[GeneratedContent]:
        """Find content generated by a specific pipeline run."""
        await self._check_error_condition("find_by_pipeline_run")
        self._increment_call_count("find_by_pipeline_run")
        await self._apply_call_delay("find_by_pipeline_run")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents if c.pipeline_run_id == run_id]
        
        # Sort by creation time desc
        matching_contents.sort(key=lambda c: c.created_at, reverse=True)
        
        self._log_event("find_by_pipeline_run", self._get_entity_type_name(), 
                       count=len(matching_contents), run_id=str(run_id))
        return matching_contents
        
    async def find_by_content_type(self, content_type: ContentType) -> List[GeneratedContent]:
        """Find content by content type."""
        await self._check_error_condition("find_by_content_type")
        self._increment_call_count("find_by_content_type")
        await self._apply_call_delay("find_by_content_type")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents if c.content_type == content_type]
        
        self._log_event("find_by_content_type", self._get_entity_type_name(), 
                       count=len(matching_contents), content_type=str(content_type))
        return matching_contents
        
    async def find_by_format(self, format: ContentFormat) -> List[GeneratedContent]:
        """Find content by output format."""
        await self._check_error_condition("find_by_format")
        self._increment_call_count("find_by_format")
        await self._apply_call_delay("find_by_format")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents if c.format == format]
        
        self._log_event("find_by_format", self._get_entity_type_name(), 
                       count=len(matching_contents), format=str(format))
        return matching_contents
        
    async def find_by_template_name(self, template_name: str) -> List[GeneratedContent]:
        """Find content generated from a specific template."""
        await self._check_error_condition("find_by_template_name")
        self._increment_call_count("find_by_template_name")
        await self._apply_call_delay("find_by_template_name")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents 
                           if hasattr(c, 'template_name') and c.template_name == template_name]
        
        self._log_event("find_by_template_name", self._get_entity_type_name(), 
                       count=len(matching_contents), template_name=template_name)
        return matching_contents
        
    async def find_recent_content(
        self, 
        limit: int = 10,
        since: Optional[datetime] = None
    ) -> List[GeneratedContent]:
        """Find recently generated content."""
        await self._check_error_condition("find_recent_content")
        self._increment_call_count("find_recent_content")
        await self._apply_call_delay("find_recent_content")
        
        contents = self._get_all_entities()
        
        if since:
            contents = [c for c in contents if c.created_at >= since]
            
        # Sort by creation time desc
        contents.sort(key=lambda c: c.created_at, reverse=True)
        recent_contents = contents[:limit]
        
        self._log_event("find_recent_content", self._get_entity_type_name(), 
                       count=len(recent_contents), limit=limit, since=since)
        return recent_contents
        
    async def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[GeneratedContent]:
        """Find content generated within a date range."""
        await self._check_error_condition("find_by_date_range")
        self._increment_call_count("find_by_date_range")
        await self._apply_call_delay("find_by_date_range")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents 
                           if start_date <= c.created_at <= end_date]
        
        self._log_event("find_by_date_range", self._get_entity_type_name(), 
                       count=len(matching_contents), start_date=start_date, end_date=end_date)
        return matching_contents
        
    async def search_by_title(self, query: str) -> List[GeneratedContent]:
        """Search content by title."""
        await self._check_error_condition("search_by_title")
        self._increment_call_count("search_by_title")
        await self._apply_call_delay("search_by_title")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents 
                           if hasattr(c, 'title') and query.lower() in c.title.lower()]
        
        self._log_event("search_by_title", self._get_entity_type_name(), 
                       count=len(matching_contents), query=query)
        return matching_contents
        
    async def search_by_content(self, query: str) -> List[GeneratedContent]:
        """Search content by body text."""
        await self._check_error_condition("search_by_content")
        self._increment_call_count("search_by_content")
        await self._apply_call_delay("search_by_content")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents 
                           if query.lower() in c.content.lower()]
        
        self._log_event("search_by_content", self._get_entity_type_name(), 
                       count=len(matching_contents), query=query)
        return matching_contents
        
    async def find_by_tag(self, tag: str) -> List[GeneratedContent]:
        """Find content by tag."""
        await self._check_error_condition("find_by_tag")
        self._increment_call_count("find_by_tag")
        await self._apply_call_delay("find_by_tag")
        
        contents = self._get_all_entities()
        matching_contents = [c for c in contents 
                           if hasattr(c, 'tags') and tag in c.tags]
        
        self._log_event("find_by_tag", self._get_entity_type_name(), 
                       count=len(matching_contents), tag=tag)
        return matching_contents
        
    async def get_content_stats(self) -> Dict[str, Any]:
        """Get content generation statistics."""
        await self._check_error_condition("get_content_stats")
        self._increment_call_count("get_content_stats")
        await self._apply_call_delay("get_content_stats")
        
        contents = self._get_all_entities()
        
        total_content = len(contents)
        total_size = sum(len(c.content) for c in contents)
        
        # Group by content type
        type_counts = {}
        for content in contents:
            content_type = str(content.content_type)
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            
        # Group by format
        format_counts = {}
        for content in contents:
            format_type = str(content.format)
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
            
        # Recent activity
        recent_cutoff = datetime.now() - datetime.timedelta(days=7)
        recent_content = [c for c in contents if c.created_at >= recent_cutoff]
        
        stats = {
            "total_content": total_content,
            "total_size_bytes": total_size,
            "average_size_bytes": total_size / total_content if total_content > 0 else 0,
            "content_by_type": type_counts,
            "content_by_format": format_counts,
            "recent_content_count": len(recent_content),
            "oldest_content": min(c.created_at for c in contents) if contents else None,
            "newest_content": max(c.created_at for c in contents) if contents else None
        }
        
        self._log_event("get_content_stats", self._get_entity_type_name(), **stats)
        return stats
        
    async def get_generation_analytics(
        self, 
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get content generation analytics."""
        await self._check_error_condition("get_generation_analytics")
        self._increment_call_count("get_generation_analytics")
        await self._apply_call_delay("get_generation_analytics")
        
        contents = self._get_all_entities()
        if since:
            contents = [c for c in contents if c.created_at >= since]
            
        # Mock analytics data
        analytics = {
            "total_generations": len(contents),
            "success_rate": 95.5,
            "average_generation_time": 2.3,
            "popular_content_types": ["article", "blog_post", "email"],
            "popular_formats": ["markdown", "html", "plain_text"],
            "peak_generation_hours": [9, 14, 16],
            "quality_scores": {
                "average": 4.2,
                "distribution": {"5": 45, "4": 35, "3": 15, "2": 4, "1": 1}
            }
        }
        
        self._log_event("get_generation_analytics", self._get_entity_type_name(), 
                       since=since, **analytics)
        return analytics
        
    async def cleanup_old_content(
        self, 
        older_than: datetime,
        keep_recent_count: int = 100
    ) -> int:
        """Clean up old generated content."""
        await self._check_error_condition("cleanup_old_content")
        self._increment_call_count("cleanup_old_content")
        await self._apply_call_delay("cleanup_old_content")
        
        contents = self._get_all_entities()
        
        # Sort by creation time desc
        contents.sort(key=lambda c: c.created_at, reverse=True)
        
        # Keep the most recent content
        contents_to_keep = contents[:keep_recent_count]
        contents_to_check = contents[keep_recent_count:]
        
        deleted_count = 0
        for content in contents_to_check:
            if content.created_at < older_than:
                self._delete_entity(self._get_entity_id(content))
                deleted_count += 1
                
        self._log_event("cleanup_old_content", self._get_entity_type_name(), 
                       deleted_count=deleted_count, older_than=older_than, 
                       keep_recent_count=keep_recent_count)
        return deleted_count
        
    async def export_content(
        self, 
        content_id: UUID, 
        export_format: str = "json"
    ) -> bytes:
        """Export content in specified format."""
        await self._check_error_condition("export_content")
        self._increment_call_count("export_content")
        await self._apply_call_delay("export_content")
        
        content = await self.find_by_id(content_id)
        if not content:
            raise MockEntityNotFoundError(self._get_entity_type_name(), str(content_id))
            
        # Mock export - return configured data or simple JSON
        if export_format == "json":
            import json
            export_data = {
                "id": str(content.id),
                "title": getattr(content, 'title', 'Generated Content'),
                "content": content.content,
                "content_type": str(content.content_type),
                "format": str(content.format),
                "created_at": content.created_at.isoformat(),
                "exported_at": datetime.now().isoformat()
            }
            result = json.dumps(export_data, indent=2).encode('utf-8')
        else:
            # For other formats, return the content as-is
            result = content.content.encode('utf-8')
            
        self._log_event("export_content", self._get_entity_type_name(), 
                       str(content_id), export_format=export_format, size=len(result))
        return result
        
    async def archive_content(
        self, 
        content_ids: List[UUID],
        archive_location: str
    ) -> bool:
        """Archive content to specified location."""
        await self._check_error_condition("archive_content")
        self._increment_call_count("archive_content")
        await self._apply_call_delay("archive_content")
        
        # Mock archival operation
        success = self._behavior.return_values.get("archive_content", True)
        
        self._log_event("archive_content", self._get_entity_type_name(), 
                       content_count=len(content_ids), archive_location=archive_location, 
                       success=success)
        return success