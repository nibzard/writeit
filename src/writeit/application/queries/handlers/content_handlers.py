"""Content Query Handlers.

Concrete implementations of content-related query handlers.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...queries.content_queries import (
    GetTemplatesQuery,
    GetTemplateQuery,
    GetTemplateByNameQuery,
    SearchTemplatesQuery,
    GetGeneratedContentQuery,
    ListGeneratedContentQuery,
    SearchGeneratedContentQuery,
    GetStylePrimersQuery,
    GetStylePrimerQuery,
    GetContentAnalyticsQuery,
    GetPopularTemplatesQuery,
    ValidateTemplateQuery,
    CheckTemplateExistsQuery,
    TemplateQueryResult,
    GeneratedContentQueryResult,
    StylePrimerQueryResult,
    ContentAnalyticsQueryResult,
    GetTemplatesQueryHandler,
    GetTemplateQueryHandler,
    GetTemplateByNameQueryHandler,
    SearchTemplatesQueryHandler,
    GetGeneratedContentQueryHandler,
    ListGeneratedContentQueryHandler,
    SearchGeneratedContentQueryHandler,
    GetStylePrimersQueryHandler,
    GetStylePrimerQueryHandler,
    GetContentAnalyticsQueryHandler,
    GetPopularTemplatesQueryHandler,
    ValidateTemplateQueryHandler,
    CheckTemplateExistsQueryHandler,
)
from ...domains.content.repositories import (
    ContentTemplateRepository,
    StylePrimerRepository,
    GeneratedContentRepository
)
from ...domains.content.entities import ContentTemplate, StylePrimer, GeneratedContent
from ...domains.content.value_objects import TemplateId, ContentId
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.content.services import TemplateRenderingService, ContentValidationService
from ...shared.errors import RepositoryError, QueryError

logger = logging.getLogger(__name__)


class ConcreteGetTemplatesQueryHandler(GetTemplatesQueryHandler):
    """Handler for listing content templates."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        workspace_repository=None  # For workspace resolution
    ):
        self.content_template_repository = content_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetTemplatesQuery) -> TemplateQueryResult:
        """Handle list templates query."""
        try:
            logger.debug(f"Listing templates with filters: {query}")
            
            # Build specification for filtering
            specs = []
            
            # Workspace scope filter
            if query.workspace_name:
                from ...shared.repository import Specification
                class WorkspaceSpec(Specification):
                    def __init__(self, workspace_name: str):
                        self.workspace_name = workspace_name
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return str(template.workspace_name) == self.workspace_name
                specs.append(WorkspaceSpec(query.workspace_name))
            elif query.scope == "global":
                from ...shared.repository import Specification
                class GlobalSpec(Specification):
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.workspace_name == WorkspaceName("global")
                specs.append(GlobalSpec())
            
            # Content type filter
            if query.content_type:
                from ...shared.repository import Specification
                class ContentTypeSpec(Specification):
                    def __init__(self, content_type: str):
                        self.content_type = content_type
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.content_type == self.content_type
                specs.append(ContentTypeSpec(query.content_type))
            
            # Status filter
            if query.status:
                from ...shared.repository import Specification
                class StatusSpec(Specification):
                    def __init__(self, status: str):
                        self.status = status
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.status == self.status
                specs.append(StatusSpec(query.status))
            
            # Category filter
            if query.category:
                from ...shared.repository import Specification
                class CategorySpec(Specification):
                    def __init__(self, category: str):
                        self.category = category
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.metadata.get('category') == self.category
                specs.append(CategorySpec(query.category))
            
            # Tags filter
            if query.tags:
                from ...shared.repository import Specification
                class TagsSpec(Specification):
                    def __init__(self, tags: List[str]):
                        self.tags = tags
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        template_tags = template.metadata.get('tags', [])
                        return all(tag in template_tags for tag in self.tags)
                specs.append(TagsSpec(query.tags))
            
            # Author filter
            if query.author:
                from ...shared.repository import Specification
                class AuthorSpec(Specification):
                    def __init__(self, author: str):
                        self.author = author
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.metadata.get('author') == self.author
                specs.append(AuthorSpec(query.author))
            
            # Date filters
            if query.created_after:
                from ...shared.repository import Specification
                class CreatedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.created_at >= self.date
                specs.append(CreatedAfterSpec(query.created_after))
            
            if query.created_before:
                from ...shared.repository import Specification
                class CreatedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.created_at <= self.date
                specs.append(CreatedBeforeSpec(query.created_before))
            
            if query.updated_after:
                from ...shared.repository import Specification
                class UpdatedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.updated_at >= self.date
                specs.append(UpdatedAfterSpec(query.updated_after))
            
            if query.updated_before:
                from ...shared.repository import Specification
                class UpdatedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.updated_at <= self.date
                specs.append(UpdatedBeforeSpec(query.updated_before))
            
            # Combine specifications
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get templates with pagination
            templates = await self.content_template_repository.find_all(
                spec=spec,
                limit=query.limit,
                offset=query.offset
            )
            
            # Apply sorting
            if query.sort_by:
                reverse = query.sort_order == "desc"
                templates.sort(
                    key=lambda t: getattr(t, query.sort_by, t.created_at),
                    reverse=reverse
                )
            
            # Convert to response format
            template_data = [template.to_dict() for template in templates]
            
            return TemplateQueryResult(
                success=True,
                templates=templates,
                data=template_data,
                total=len(templates)
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error listing templates: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Failed to list templates: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing templates: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetTemplateQueryHandler(GetTemplateQueryHandler):
    """Handler for getting template by ID."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        workspace_repository=None
    ):
        self.content_template_repository = content_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetTemplateQuery) -> TemplateQueryResult:
        """Handle get template query."""
        try:
            logger.debug(f"Getting template: {query.template_id}")
            
            # Get template by ID
            template = await self.content_template_repository.find_by_id(query.template_id)
            
            if not template:
                return TemplateQueryResult(
                    success=False,
                    error=f"Template '{query.template_id}' not found"
                )
            
            # Check workspace access if specified
            if query.workspace_name:
                if str(template.workspace_name) != query.workspace_name:
                    return TemplateQueryResult(
                        success=False,
                        error=f"Template not found in workspace '{query.workspace_name}'"
                    )
            
            # Filter data based on query parameters
            template_data = template.to_dict()
            if not query.include_metadata:
                template_data.pop('metadata', None)
                template_data.pop('created_at', None)
                template_data.pop('updated_at', None)
            
            if not query.include_content:
                template_data.pop('content', None)
            
            return TemplateQueryResult(
                success=True,
                template=template,
                data=template_data
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting template: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Failed to retrieve template: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting template: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetTemplateByNameQueryHandler(GetTemplateByNameQueryHandler):
    """Handler for getting template by name."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        workspace_repository=None
    ):
        self.content_template_repository = content_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetTemplateByNameQuery) -> TemplateQueryResult:
        """Handle get template by name query."""
        try:
            logger.debug(f"Getting template by name: {query.template_name}")
            
            # Build specification for finding template by name
            specs = [
                # Name specification
                type('NameSpec', (object,), {
                    'is_satisfied_by': lambda self, template: template.name == query.template_name
                })()
            ]
            
            # Workspace scope filter
            if query.workspace_name:
                from ...shared.repository import Specification
                class WorkspaceSpec(Specification):
                    def __init__(self, workspace_name: str):
                        self.workspace_name = workspace_name
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return str(template.workspace_name) == self.workspace_name
                specs.append(WorkspaceSpec(query.workspace_name))
            elif query.scope == "global":
                from ...shared.repository import Specification
                class GlobalSpec(Specification):
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.workspace_name == WorkspaceName("global")
                specs.append(GlobalSpec())
            
            # Combine specifications
            from ...shared.repository import AndSpecification
            spec = AndSpecification(*specs)
            
            # Find template
            templates = await self.content_template_repository.find_all(spec=spec)
            
            if not templates:
                return TemplateQueryResult(
                    success=False,
                    error=f"Template '{query.template_name}' not found"
                )
            
            # Get the most recent version (should typically be just one)
            template = templates[0]
            
            # Get versions if requested
            versions = []
            if query.include_versions:
                # This would require finding all templates with the same name
                # For now, return current version
                versions = [{
                    "version": template.version,
                    "created_at": template.created_at.isoformat(),
                    "status": template.status
                }]
            
            template_data = template.to_dict()
            
            return TemplateQueryResult(
                success=True,
                template=template,
                versions=versions,
                data=template_data
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting template by name: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Failed to retrieve template: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting template by name: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteSearchTemplatesQueryHandler(SearchTemplatesQueryHandler):
    """Handler for searching templates."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        workspace_repository=None
    ):
        self.content_template_repository = content_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: SearchTemplatesQuery) -> TemplateQueryResult:
        """Handle search templates query."""
        try:
            logger.debug(f"Searching templates: {query.search_query}")
            
            # Get all templates with basic filtering
            list_query = GetTemplatesQuery(
                workspace_name=query.workspace_name,
                scope=query.scope,
                content_type=query.content_type,
                category=query.category,
                tags=query.tags,
                limit=1000,  # Large limit for searching
                offset=0
            )
            
            list_handler = ConcreteGetTemplatesQueryHandler(
                self.content_template_repository,
                self.workspace_repository
            )
            
            result = await list_handler.handle(list_query)
            if not result.success:
                return result
            
            # Apply text search
            search_results = []
            search_query_lower = query.search_query.lower()
            
            for template in result.templates:
                template_dict = template.to_dict()
                match_found = False
                
                # Search in specified fields
                for field in query.search_fields:
                    if field in template_dict:
                        field_value = str(template_dict[field]).lower()
                        if search_query_lower in field_value:
                            match_found = True
                            break
                
                if match_found:
                    search_results.append(template)
            
            # Apply pagination to search results
            start_idx = query.offset or 0
            end_idx = start_idx + (query.limit or len(search_results))
            paginated_results = search_results[start_idx:end_idx]
            
            # Convert to response format
            template_data = [template.to_dict() for template in paginated_results]
            
            return TemplateQueryResult(
                success=True,
                templates=paginated_results,
                data=template_data,
                total=len(search_results)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error searching templates: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetGeneratedContentQueryHandler(GetGeneratedContentQueryHandler):
    """Handler for getting generated content by ID."""
    
    def __init__(
        self,
        generated_content_repository: GeneratedContentRepository,
        workspace_repository=None
    ):
        self.generated_content_repository = generated_content_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetGeneratedContentQuery) -> GeneratedContentQueryResult:
        """Handle get generated content query."""
        try:
            logger.debug(f"Getting generated content: {query.content_id}")
            
            # Get content by ID
            content = await self.generated_content_repository.find_by_id(query.content_id)
            
            if not content:
                return GeneratedContentQueryResult(
                    success=False,
                    error=f"Generated content '{query.content_id}' not found"
                )
            
            # Check workspace access if specified
            if query.workspace_name:
                if str(content.workspace_name) != query.workspace_name:
                    return GeneratedContentQueryResult(
                        success=False,
                        error=f"Content not found in workspace '{query.workspace_name}'"
                    )
            
            # Filter data based on query parameters
            content_data = content.to_dict()
            if not query.include_metadata:
                content_data.pop('metadata', None)
                content_data.pop('created_at', None)
                content_data.pop('updated_at', None)
            
            if not query.include_source:
                content_data.pop('source_template_id', None)
                content_data.pop('pipeline_run_id', None)
            
            if not query.include_metrics:
                content_data.pop('metrics', None)
            
            return GeneratedContentQueryResult(
                success=True,
                content_item=content,
                data=content_data
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting generated content: {e}")
            return GeneratedContentQueryResult(
                success=False,
                error=f"Failed to retrieve generated content: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting generated content: {e}")
            return GeneratedContentQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteListGeneratedContentQueryHandler(ListGeneratedContentQueryHandler):
    """Handler for listing generated content."""
    
    def __init__(
        self,
        generated_content_repository: GeneratedContentRepository,
        workspace_repository=None
    ):
        self.generated_content_repository = generated_content_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: ListGeneratedContentQuery) -> GeneratedContentQueryResult:
        """Handle list generated content query."""
        try:
            logger.debug(f"Listing generated content with filters: {query}")
            
            # Build specification for filtering
            specs = []
            
            # Workspace filter
            if query.workspace_name:
                from ...shared.repository import Specification
                class WorkspaceSpec(Specification):
                    def __init__(self, workspace_name: str):
                        self.workspace_name = workspace_name
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return str(content.workspace_name) == self.workspace_name
                specs.append(WorkspaceSpec(query.workspace_name))
            
            # Template filter
            if query.template_id:
                from ...shared.repository import Specification
                class TemplateSpec(Specification):
                    def __init__(self, template_id: TemplateId):
                        self.template_id = template_id
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return content.source_template_id == self.template_id
                specs.append(TemplateSpec(query.template_id))
            
            # Pipeline run filter
            if query.pipeline_run_id:
                from ...shared.repository import Specification
                class PipelineRunSpec(Specification):
                    def __init__(self, pipeline_run_id: str):
                        self.pipeline_run_id = pipeline_run_id
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return content.pipeline_run_id == self.pipeline_run_id
                specs.append(PipelineRunSpec(query.pipeline_run_id))
            
            # Content type filter
            if query.content_type:
                from ...shared.repository import Specification
                class ContentTypeSpec(Specification):
                    def __init__(self, content_type: str):
                        self.content_type = content_type
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return content.content_type == self.content_type
                specs.append(ContentTypeSpec(query.content_type))
            
            # Status filter
            if query.status:
                from ...shared.repository import Specification
                class StatusSpec(Specification):
                    def __init__(self, status: str):
                        self.status = status
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return content.status == self.status
                specs.append(StatusSpec(query.status))
            
            # Date filters
            if query.created_after:
                from ...shared.repository import Specification
                class CreatedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return content.created_at >= self.date
                specs.append(CreatedAfterSpec(query.created_after))
            
            if query.created_before:
                from ...shared.repository import Specification
                class CreatedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, content: GeneratedContent) -> bool:
                        return content.created_at <= self.date
                specs.append(CreatedBeforeSpec(query.created_before))
            
            # Combine specifications
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get content with pagination
            content_items = await self.generated_content_repository.find_all(
                spec=spec,
                limit=query.limit,
                offset=query.offset
            )
            
            # Apply sorting
            if query.sort_by:
                reverse = query.sort_order == "desc"
                content_items.sort(
                    key=lambda c: getattr(c, query.sort_by, c.created_at),
                    reverse=reverse
                )
            
            # Convert to response format
            content_data = []
            for item in content_items:
                item_dict = item.to_dict()
                if not query.include_metrics:
                    item_dict.pop('metrics', None)
                content_data.append(item_dict)
            
            return GeneratedContentQueryResult(
                success=True,
                content_items=content_items,
                data=content_data,
                total=len(content_items)
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error listing generated content: {e}")
            return GeneratedContentQueryResult(
                success=False,
                error=f"Failed to list generated content: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing generated content: {e}")
            return GeneratedContentQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetStylePrimersQueryHandler(GetStylePrimersQueryHandler):
    """Handler for listing style primers."""
    
    def __init__(
        self,
        style_primer_repository: StylePrimerRepository,
        workspace_repository=None
    ):
        self.style_primer_repository = style_primer_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetStylePrimersQuery) -> StylePrimerQueryResult:
        """Handle list style primers query."""
        try:
            logger.debug(f"Listing style primers with filters: {query}")
            
            # Build specification for filtering
            specs = []
            
            # Workspace scope filter
            if query.workspace_name:
                from ...shared.repository import Specification
                class WorkspaceSpec(Specification):
                    def __init__(self, workspace_name: str):
                        self.workspace_name = workspace_name
                    def is_satisfied_by(self, primer: StylePrimer) -> bool:
                        return str(primer.workspace_name) == self.workspace_name
                specs.append(WorkspaceSpec(query.workspace_name))
            elif query.scope == "global":
                from ...shared.repository import Specification
                class GlobalSpec(Specification):
                    def is_satisfied_by(self, primer: StylePrimer) -> bool:
                        return primer.workspace_name == WorkspaceName("global")
                specs.append(GlobalSpec())
            
            # Category filter
            if query.category:
                from ...shared.repository import Specification
                class CategorySpec(Specification):
                    def __init__(self, category: str):
                        self.category = category
                    def is_satisfied_by(self, primer: StylePrimer) -> bool:
                        return primer.metadata.get('category') == self.category
                specs.append(CategorySpec(query.category))
            
            # Tags filter
            if query.tags:
                from ...shared.repository import Specification
                class TagsSpec(Specification):
                    def __init__(self, tags: List[str]):
                        self.tags = tags
                    def is_satisfied_by(self, primer: StylePrimer) -> bool:
                        primer_tags = primer.metadata.get('tags', [])
                        return all(tag in primer_tags for tag in self.tags)
                specs.append(TagsSpec(query.tags))
            
            # Author filter
            if query.author:
                from ...shared.repository import Specification
                class AuthorSpec(Specification):
                    def __init__(self, author: str):
                        self.author = author
                    def is_satisfied_by(self, primer: StylePrimer) -> bool:
                        return primer.metadata.get('author') == self.author
                specs.append(AuthorSpec(query.author))
            
            # Combine specifications
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get primers with pagination
            primers = await self.style_primer_repository.find_all(
                spec=spec,
                limit=query.limit,
                offset=query.offset
            )
            
            # Apply sorting
            if query.sort_by:
                reverse = query.sort_order == "desc"
                primers.sort(
                    key=lambda p: getattr(p, query.sort_by, p.created_at),
                    reverse=reverse
                )
            
            # Convert to response format
            primer_data = [primer.to_dict() for primer in primers]
            
            return StylePrimerQueryResult(
                success=True,
                primers=primers,
                data=primer_data,
                total=len(primers)
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error listing style primers: {e}")
            return StylePrimerQueryResult(
                success=False,
                error=f"Failed to list style primers: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing style primers: {e}")
            return StylePrimerQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetStylePrimerQueryHandler(GetStylePrimerQueryHandler):
    """Handler for getting style primer by ID."""
    
    def __init__(
        self,
        style_primer_repository: StylePrimerRepository,
        workspace_repository=None
    ):
        self.style_primer_repository = style_primer_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetStylePrimerQuery) -> StylePrimerQueryResult:
        """Handle get style primer query."""
        try:
            logger.debug(f"Getting style primer: {query.primer_id}")
            
            # Get primer by ID
            primer = await self.style_primer_repository.find_by_id(query.primer_id)
            
            if not primer:
                return StylePrimerQueryResult(
                    success=False,
                    error=f"Style primer '{query.primer_id}' not found"
                )
            
            # Check workspace access if specified
            if query.workspace_name:
                if str(primer.workspace_name) != query.workspace_name:
                    return StylePrimerQueryResult(
                        success=False,
                        error=f"Style primer not found in workspace '{query.workspace_name}'"
                    )
            
            return StylePrimerQueryResult(
                success=True,
                primer=primer,
                data=primer.to_dict()
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting style primer: {e}")
            return StylePrimerQueryResult(
                success=False,
                error=f"Failed to retrieve style primer: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting style primer: {e}")
            return StylePrimerQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetContentAnalyticsQueryHandler(GetContentAnalyticsQueryHandler):
    """Handler for getting content analytics."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        generated_content_repository: GeneratedContentRepository,
        style_primer_repository: StylePrimerRepository
    ):
        self.content_template_repository = content_template_repository
        self.generated_content_repository = generated_content_repository
        self.style_primer_repository = style_primer_repository
    
    async def handle(self, query: GetContentAnalyticsQuery) -> ContentAnalyticsQueryResult:
        """Handle get content analytics query."""
        try:
            logger.debug(f"Getting content analytics: {query}")
            
            # Build base specifications for time range
            specs = []
            
            if query.time_range_start:
                from ...shared.repository import Specification
                class CreatedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, item) -> bool:
                        return item.created_at >= self.date
                specs.append(CreatedAfterSpec(query.time_range_start))
            
            if query.time_range_end:
                from ...shared.repository import Specification
                class CreatedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, item) -> bool:
                        return item.created_at <= self.date
                specs.append(CreatedBeforeSpec(query.time_range_end))
            
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get content counts
            template_count = len(await self.content_template_repository.find_all(spec=spec))
            generated_content_count = len(await self.generated_content_repository.find_all(spec=spec))
            style_primer_count = len(await self.style_primer_repository.find_all(spec=spec))
            
            # Calculate usage patterns over time
            time_series_data = []
            if query.time_range_start and query.time_range_end:
                # Group by the specified time period
                from collections import defaultdict
                grouped_templates = defaultdict(list)
                grouped_content = defaultdict(list)
                grouped_primers = defaultdict(list)
                
                # Get all items in time range
                templates = await self.content_template_repository.find_all(spec=spec)
                content_items = await self.generated_content_repository.find_all(spec=spec)
                primers = await self.style_primer_repository.find_all(spec=spec)
                
                # Group items by time period
                for template in templates:
                    if query.group_by == "hour":
                        key = template.created_at.strftime("%Y-%m-%d %H:00")
                    elif query.group_by == "day":
                        key = template.created_at.strftime("%Y-%m-%d")
                    elif query.group_by == "week":
                        monday = template.created_at - datetime.timedelta(days=template.created_at.weekday())
                        key = monday.strftime("%Y-%m-%d")
                    else:  # month
                        key = template.created_at.strftime("%Y-%m")
                    grouped_templates[key].append(template)
                
                for item in content_items:
                    if query.group_by == "hour":
                        key = item.created_at.strftime("%Y-%m-%d %H:00")
                    elif query.group_by == "day":
                        key = item.created_at.strftime("%Y-%m-%d")
                    elif query.group_by == "week":
                        monday = item.created_at - datetime.timedelta(days=item.created_at.weekday())
                        key = monday.strftime("%Y-%m-%d")
                    else:  # month
                        key = item.created_at.strftime("%Y-%m")
                    grouped_content[key].append(item)
                
                for primer in primers:
                    if query.group_by == "hour":
                        key = primer.created_at.strftime("%Y-%m-%d %H:00")
                    elif query.group_by == "day":
                        key = primer.created_at.strftime("%Y-%m-%d")
                    elif query.group_by == "week":
                        monday = primer.created_at - datetime.timedelta(days=primer.created_at.weekday())
                        key = monday.strftime("%Y-%m-%d")
                    else:  # month
                        key = primer.created_at.strftime("%Y-%m")
                    grouped_primers[key].append(primer)
                
                # Create time series data
                all_periods = set(grouped_templates.keys()) | set(grouped_content.keys()) | set(grouped_primers.keys())
                
                for period in sorted(all_periods):
                    time_series_data.append({
                        "period": period,
                        "templates_created": len(grouped_templates[period]),
                        "content_generated": len(grouped_content[period]),
                        "primers_created": len(grouped_primers[period])
                    })
            
            analytics = {
                "total_templates": template_count,
                "total_generated_content": generated_content_count,
                "total_style_primers": style_primer_count,
                "content_types": {},  # Would be populated with actual data
                "template_categories": {},  # Would be populated with actual data
                "time_range": {
                    "start": query.time_range_start.isoformat() if query.time_range_start else None,
                    "end": query.time_range_end.isoformat() if query.time_range_end else None
                }
            }
            
            return ContentAnalyticsQueryResult(
                success=True,
                analytics=analytics,
                time_series=time_series_data
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting content analytics: {e}")
            return ContentAnalyticsQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetPopularTemplatesQueryHandler(GetPopularTemplatesQueryHandler):
    """Handler for getting popular templates."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        generated_content_repository: GeneratedContentRepository
    ):
        self.content_template_repository = content_template_repository
        self.generated_content_repository = generated_content_repository
    
    async def handle(self, query: GetPopularTemplatesQuery) -> ContentAnalyticsQueryResult:
        """Handle get popular templates query."""
        try:
            logger.debug(f"Getting popular templates: {query}")
            
            # Get all templates
            templates = await self.content_template_repository.find_all()
            
            # Calculate popularity metrics for each template
            template_popularity = []
            
            for template in templates:
                # Get generated content for this template
                content_specs = [
                    type('TemplateSpec', (object,), {
                        'is_satisfied_by': lambda self, content: content.source_template_id == template.id
                    })()
                ]
                
                if query.time_range_start:
                    from ...shared.repository import Specification
                    class CreatedAfterSpec(Specification):
                        def __init__(self, date: datetime):
                            self.date = date
                        def is_satisfied_by(self, content):
                            return content.created_at >= self.date
                    content_specs.append(CreatedAfterSpec(query.time_range_start))
                
                if query.time_range_end:
                    from ...shared.repository import Specification
                    class CreatedBeforeSpec(Specification):
                        def __init__(self, date: datetime):
                            self.date = date
                        def is_satisfied_by(self, content):
                            return content.created_at <= self.date
                    content_specs.append(CreatedBeforeSpec(query.time_range_end))
                
                from ...shared.repository import AndSpecification
                content_spec = AndSpecification(*content_specs)
                
                generated_content = await self.generated_content_repository.find_all(spec=content_spec)
                
                # Calculate metrics
                usage_count = len(generated_content)
                success_count = len([c for c in generated_content if c.status == "completed"])
                success_rate = (success_count / usage_count * 100) if usage_count > 0 else 0
                
                # Calculate average execution time
                execution_times = []
                for content in generated_content:
                    if content.created_at and content.completed_at:
                        duration = (content.completed_at - content.created_at).total_seconds()
                        execution_times.append(duration)
                
                avg_duration = sum(execution_times) / len(execution_times) if execution_times else 0
                
                template_popularity.append({
                    "template": template,
                    "usage_count": usage_count,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration
                })
            
            # Sort by requested metric
            if query.metric == "usage_count":
                template_popularity.sort(key=lambda x: x["usage_count"], reverse=True)
            elif query.metric == "success_rate":
                template_popularity.sort(key=lambda x: x["success_rate"], reverse=True)
            elif query.metric == "avg_duration":
                template_popularity.sort(key=lambda x: x["avg_duration"], reverse=False)
            
            # Apply limit
            popular_templates = template_popularity[:query.limit]
            
            # Convert to response format
            popular_data = []
            for item in popular_templates:
                popular_data.append({
                    "template_id": str(item["template"].id),
                    "template_name": item["template"].name,
                    "category": item["template"].metadata.get("category"),
                    "usage_count": item["usage_count"],
                    "success_rate": round(item["success_rate"], 2),
                    "avg_duration": round(item["avg_duration"], 2)
                })
            
            return ContentAnalyticsQueryResult(
                success=True,
                popular_templates=popular_data,
                data=popular_data
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting popular templates: {e}")
            return ContentAnalyticsQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteValidateTemplateQueryHandler(ValidateTemplateQueryHandler):
    """Handler for validating template."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        content_validation_service: ContentValidationService
    ):
        self.content_template_repository = content_template_repository
        self.content_validation_service = content_validation_service
    
    async def handle(self, query: ValidateTemplateQuery) -> TemplateQueryResult:
        """Handle validate template query."""
        try:
            logger.debug(f"Validating template: {query.template_id}")
            
            validation_errors = []
            
            # Get template if ID provided
            template = None
            if query.template_id:
                template = await self.content_template_repository.find_by_id(query.template_id)
                if not template:
                    validation_errors.append(f"Template '{query.template_id}' not found")
            
            # Validate template content
            template_content = query.template_content
            if template and not template_content:
                template_content = template.content
            
            if not template_content:
                validation_errors.append("No template content provided for validation")
            
            # Perform validation
            if template_content:
                try:
                    validation_result = await self.content_validation_service.validate_template(
                        template_content,
                        validation_level=query.validation_level
                    )
                    
                    if not validation_result.is_valid:
                        validation_errors.extend(validation_result.errors)
                    
                except Exception as e:
                    validation_errors.append(f"Validation service error: {str(e)}")
            
            return TemplateQueryResult(
                success=len(validation_errors) == 0,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Unexpected error validating template: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteCheckTemplateExistsQueryHandler(CheckTemplateExistsQueryHandler):
    """Handler for checking template existence."""
    
    def __init__(
        self,
        content_template_repository: ContentTemplateRepository,
        workspace_repository=None
    ):
        self.content_template_repository = content_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: CheckTemplateExistsQuery) -> TemplateQueryResult:
        """Handle check template exists query."""
        try:
            logger.debug(f"Checking template exists: {query.template_name}")
            
            # Build specification for finding template
            specs = [
                # Name specification
                type('NameSpec', (object,), {
                    'is_satisfied_by': lambda self, template: template.name == query.template_name
                })()
            ]
            
            # Workspace scope filter
            if query.workspace_name:
                from ...shared.repository import Specification
                class WorkspaceSpec(Specification):
                    def __init__(self, workspace_name: str):
                        self.workspace_name = workspace_name
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return str(template.workspace_name) == self.workspace_name
                specs.append(WorkspaceSpec(query.workspace_name))
            elif query.scope == "global":
                from ...shared.repository import Specification
                class GlobalSpec(Specification):
                    def is_satisfied_by(self, template: ContentTemplate) -> bool:
                        return template.workspace_name == WorkspaceName("global")
                specs.append(GlobalSpec())
            
            # Combine specifications
            from ...shared.repository import AndSpecification
            spec = AndSpecification(*specs)
            
            # Check if template exists
            templates = await self.content_template_repository.find_all(spec=spec)
            exists = len(templates) > 0
            
            return TemplateQueryResult(
                success=True,
                exists=exists
            )
            
        except Exception as e:
            logger.error(f"Unexpected error checking template exists: {e}")
            return TemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


# Additional handlers for completeness (simplified implementations)

class ConcreteSearchGeneratedContentQueryHandler(SearchGeneratedContentQueryHandler):
    """Handler for searching generated content."""
    
    def __init__(self, generated_content_repository: GeneratedContentRepository):
        self.generated_content_repository = generated_content_repository
    
    async def handle(self, query: SearchGeneratedContentQuery) -> GeneratedContentQueryResult:
        """Handle search generated content query."""
        try:
            logger.debug(f"Searching generated content: {query.search_query}")
            
            # Get all content with basic filtering
            list_query = ListGeneratedContentQuery(
                workspace_name=query.workspace_name,
                template_id=query.template_id,
                pipeline_run_id=query.pipeline_run_id,
                limit=1000,
                offset=0
            )
            
            list_handler = ConcreteListGeneratedContentQueryHandler(
                self.generated_content_repository
            )
            
            result = await list_handler.handle(list_query)
            if not result.success:
                return result
            
            # Apply text search
            search_results = []
            search_query_lower = query.search_query.lower()
            
            for content in result.content_items:
                content_dict = content.to_dict()
                match_found = False
                
                # Search in specified fields
                for field in query.search_fields:
                    if field in content_dict:
                        field_value = str(content_dict[field]).lower()
                        if search_query_lower in field_value:
                            match_found = True
                            break
                
                if match_found:
                    search_results.append(content)
            
            # Apply pagination to search results
            start_idx = query.offset or 0
            end_idx = start_idx + (query.limit or len(search_results))
            paginated_results = search_results[start_idx:end_idx]
            
            # Convert to response format
            content_data = [content.to_dict() for content in paginated_results]
            
            return GeneratedContentQueryResult(
                success=True,
                content_items=paginated_results,
                data=content_data,
                total=len(search_results)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error searching generated content: {e}")
            return GeneratedContentQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )