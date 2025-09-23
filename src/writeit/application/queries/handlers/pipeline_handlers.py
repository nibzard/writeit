"""Pipeline Query Handlers.

Concrete implementations of pipeline-related query handlers.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...queries.pipeline_queries import (
    GetPipelineTemplateQuery,
    ListPipelineTemplatesQuery,
    SearchPipelineTemplatesQuery,
    GetPipelineRunQuery,
    ListPipelineRunsQuery,
    GetPipelineAnalyticsQuery,
    GetPipelineUsageStatsQuery,
    GetPopularPipelinesQuery,
    PipelineTemplateQueryResult,
    PipelineRunQueryResult,
    PipelineAnalyticsQueryResult,
    GetPipelineTemplateQueryHandler,
    ListPipelineTemplatesQueryHandler,
    SearchPipelineTemplatesQueryHandler,
    GetPipelineRunQueryHandler,
    ListPipelineRunsQueryHandler,
    GetPipelineAnalyticsQueryHandler,
)
from ...domains.pipeline.repositories import PipelineTemplateRepository, PipelineRunRepository
from ...domains.workspace.repositories import WorkspaceRepository
from ...domains.pipeline.entities import PipelineTemplate, PipelineRun
from ...domains.pipeline.value_objects import PipelineId, PipelineName
from ...domains.workspace.value_objects import WorkspaceName
from ...shared.errors import RepositoryError, QueryError

logger = logging.getLogger(__name__)


class ConcreteGetPipelineTemplateQueryHandler(GetPipelineTemplateQueryHandler):
    """Handler for getting pipeline template by ID."""
    
    def __init__(
        self,
        pipeline_template_repository: PipelineTemplateRepository,
        workspace_repository: WorkspaceRepository
    ):
        self.pipeline_template_repository = pipeline_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: GetPipelineTemplateQuery) -> PipelineTemplateQueryResult:
        """Handle get pipeline template query."""
        try:
            logger.debug(f"Getting pipeline template: {query.pipeline_id}")
            
            # Get workspace context if specified
            workspace = None
            if query.workspace_name:
                workspace = await self.workspace_repository.find_by_name(
                    WorkspaceName(query.workspace_name)
                )
                if not workspace:
                    return PipelineTemplateQueryResult(
                        success=False,
                        error=f"Workspace '{query.workspace_name}' not found"
                    )
            
            # Get template by ID
            template = await self.pipeline_template_repository.find_by_id(
                PipelineId(query.pipeline_id)
            )
            
            if not template:
                return PipelineTemplateQueryResult(
                    success=False,
                    error=f"Pipeline template '{query.pipeline_id}' not found"
                )
            
            # Filter by workspace if specified
            if workspace and template.workspace_name != workspace.name:
                return PipelineTemplateQueryResult(
                    success=False,
                    error=f"Template not found in workspace '{query.workspace_name}'"
                )
            
            # Filter data based on query parameters
            template_data = template.to_dict()
            if not query.include_steps:
                template_data.pop('steps', None)
            if not query.include_inputs:
                template_data.pop('inputs', None)
            if not query.include_metadata:
                template_data.pop('metadata', None)
                template_data.pop('created_at', None)
                template_data.pop('updated_at', None)
            
            return PipelineTemplateQueryResult(
                success=True,
                template=template,
                data=template_data
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting pipeline template: {e}")
            return PipelineTemplateQueryResult(
                success=False,
                error=f"Failed to retrieve pipeline template: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting pipeline template: {e}")
            return PipelineTemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteListPipelineTemplatesQueryHandler(ListPipelineTemplatesQueryHandler):
    """Handler for listing pipeline templates."""
    
    def __init__(
        self,
        pipeline_template_repository: PipelineTemplateRepository,
        workspace_repository: WorkspaceRepository
    ):
        self.pipeline_template_repository = pipeline_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: ListPipelineTemplatesQuery) -> PipelineTemplateQueryResult:
        """Handle list pipeline templates query."""
        try:
            logger.debug(f"Listing pipeline templates with filters: {query}")
            
            # Get workspace context
            workspace = None
            if query.workspace_name:
                workspace = await self.workspace_repository.find_by_name(
                    WorkspaceName(query.workspace_name)
                )
                if not workspace:
                    return PipelineTemplateQueryResult(
                        success=False,
                        error=f"Workspace '{query.workspace_name}' not found"
                    )
            
            # Build specification for filtering
            specs = []
            
            # Workspace filter
            if workspace:
                from ...shared.repository import Specification
                class WorkspaceSpec(Specification):
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        return template.workspace_name == workspace.name
                specs.append(WorkspaceSpec())
            elif query.scope == "global":
                class GlobalSpec(Specification):
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        return template.workspace_name == WorkspaceName("global")
                specs.append(GlobalSpec())
            
            # Category filter
            if query.category:
                from ...shared.repository import Specification
                class CategorySpec(Specification):
                    def __init__(self, category: str):
                        self.category = category
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        return template.metadata.get('category') == self.category
                specs.append(CategorySpec(query.category))
            
            # Tags filter
            if query.tags:
                from ...shared.repository import Specification
                class TagsSpec(Specification):
                    def __init__(self, tags: List[str]):
                        self.tags = tags
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        template_tags = template.metadata.get('tags', [])
                        return all(tag in template_tags for tag in self.tags)
                specs.append(TagsSpec(query.tags))
            
            # Author filter
            if query.author:
                from ...shared.repository import Specification
                class AuthorSpec(Specification):
                    def __init__(self, author: str):
                        self.author = author
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        return template.metadata.get('author') == self.author
                specs.append(AuthorSpec(query.author))
            
            # Date filters
            if query.created_after:
                from ...shared.repository import Specification
                class CreatedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        return template.created_at >= self.date
                specs.append(CreatedAfterSpec(query.created_after))
            
            if query.created_before:
                from ...shared.repository import Specification
                class CreatedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, template: PipelineTemplate) -> bool:
                        return template.created_at <= self.date
                specs.append(CreatedBeforeSpec(query.created_before))
            
            # Combine specifications
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get templates with pagination
            templates = await self.pipeline_template_repository.find_all(
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
            
            return PipelineTemplateQueryResult(
                success=True,
                templates=templates,
                data=template_data,
                total=len(templates)
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error listing pipeline templates: {e}")
            return PipelineTemplateQueryResult(
                success=False,
                error=f"Failed to list pipeline templates: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing pipeline templates: {e}")
            return PipelineTemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteSearchPipelineTemplatesQueryHandler(SearchPipelineTemplatesQueryHandler):
    """Handler for searching pipeline templates."""
    
    def __init__(
        self,
        pipeline_template_repository: PipelineTemplateRepository,
        workspace_repository: WorkspaceRepository
    ):
        self.pipeline_template_repository = pipeline_template_repository
        self.workspace_repository = workspace_repository
    
    async def handle(self, query: SearchPipelineTemplatesQuery) -> PipelineTemplateQueryResult:
        """Handle search pipeline templates query."""
        try:
            logger.debug(f"Searching pipeline templates: {query.search_query}")
            
            # Get all templates with basic filtering
            list_query = ListPipelineTemplatesQuery(
                workspace_name=query.workspace_name,
                scope=query.scope,
                category=query.category,
                tags=query.tags,
                limit=1000,  # Large limit for searching
                offset=0
            )
            
            list_handler = ConcreteListPipelineTemplatesQueryHandler(
                self.pipeline_template_repository,
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
            
            return PipelineTemplateQueryResult(
                success=True,
                templates=paginated_results,
                data=template_data,
                total=len(search_results)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error searching pipeline templates: {e}")
            return PipelineTemplateQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetPipelineRunQueryHandler(GetPipelineRunQueryHandler):
    """Handler for getting pipeline run by ID."""
    
    def __init__(self, pipeline_run_repository: PipelineRunRepository):
        self.pipeline_run_repository = pipeline_run_repository
    
    async def handle(self, query: GetPipelineRunQuery) -> PipelineRunQueryResult:
        """Handle get pipeline run query."""
        try:
            logger.debug(f"Getting pipeline run: {query.run_id}")
            
            # Get run by ID
            run = await self.pipeline_run_repository.find_by_id(query.run_id)
            
            if not run:
                return PipelineRunQueryResult(
                    success=False,
                    error=f"Pipeline run '{query.run_id}' not found"
                )
            
            # Filter data based on query parameters
            run_data = run.to_dict()
            if not query.include_steps:
                run_data.pop('step_executions', None)
            if not query.include_outputs:
                run_data.pop('outputs', None)
            if not query.include_metrics:
                run_data.pop('metrics', None)
            
            return PipelineRunQueryResult(
                success=True,
                run=run,
                data=run_data
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error getting pipeline run: {e}")
            return PipelineRunQueryResult(
                success=False,
                error=f"Failed to retrieve pipeline run: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting pipeline run: {e}")
            return PipelineRunQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteListPipelineRunsQueryHandler(ListPipelineRunsQueryHandler):
    """Handler for listing pipeline runs."""
    
    def __init__(self, pipeline_run_repository: PipelineRunRepository):
        self.pipeline_run_repository = pipeline_run_repository
    
    async def handle(self, query: ListPipelineRunsQuery) -> PipelineRunQueryResult:
        """Handle list pipeline runs query."""
        try:
            logger.debug(f"Listing pipeline runs with filters: {query}")
            
            # Build specification for filtering
            specs = []
            
            # Status filter
            if query.status:
                from ...shared.repository import Specification
                class StatusSpec(Specification):
                    def __init__(self, status: str):
                        self.status = status
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.status == self.status
                specs.append(StatusSpec(query.status.value))
            
            # Pipeline name filter
            if query.pipeline_name:
                from ...shared.repository import Specification
                class PipelineNameSpec(Specification):
                    def __init__(self, name: str):
                        self.name = name
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.pipeline_name == self.name
                specs.append(PipelineNameSpec(query.pipeline_name))
            
            # User filter
            if query.user_id:
                from ...shared.repository import Specification
                class UserSpec(Specification):
                    def __init__(self, user_id: str):
                        self.user_id = user_id
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.user_id == self.user_id
                specs.append(UserSpec(query.user_id))
            
            # Date filters
            if query.started_after:
                from ...shared.repository import Specification
                class StartedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.started_at >= self.date
                specs.append(StartedAfterSpec(query.started_after))
            
            if query.started_before:
                from ...shared.repository import Specification
                class StartedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.started_at <= self.date
                specs.append(StartedBeforeSpec(query.started_before))
            
            # Combine specifications
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            # Get runs with pagination
            runs = await self.pipeline_run_repository.find_all(
                spec=spec,
                limit=query.limit,
                offset=query.offset
            )
            
            # Apply sorting
            if query.sort_by:
                reverse = query.sort_order == "desc"
                runs.sort(
                    key=lambda r: getattr(r, query.sort_by, r.started_at),
                    reverse=reverse
                )
            
            # Convert to response format
            runs_data = [run.to_dict() for run in runs]
            
            return PipelineRunQueryResult(
                success=True,
                runs=runs,
                data=runs_data,
                total=len(runs)
            )
            
        except RepositoryError as e:
            logger.error(f"Repository error listing pipeline runs: {e}")
            return PipelineRunQueryResult(
                success=False,
                error=f"Failed to list pipeline runs: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing pipeline runs: {e}")
            return PipelineRunQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


class ConcreteGetPipelineAnalyticsQueryHandler(GetPipelineAnalyticsQueryHandler):
    """Handler for getting pipeline analytics."""
    
    def __init__(
        self,
        pipeline_run_repository: PipelineRunRepository,
        pipeline_template_repository: PipelineTemplateRepository
    ):
        self.pipeline_run_repository = pipeline_run_repository
        self.pipeline_template_repository = pipeline_template_repository
    
    async def handle(self, query: GetPipelineAnalyticsQuery) -> PipelineAnalyticsQueryResult:
        """Handle get pipeline analytics query."""
        try:
            logger.debug(f"Getting pipeline analytics: {query}")
            
            # Get all runs in time range
            specs = []
            
            if query.time_range_start:
                from ...shared.repository import Specification
                class StartedAfterSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.started_at >= self.date
                specs.append(StartedAfterSpec(query.time_range_start))
            
            if query.time_range_end:
                from ...shared.repository import Specification
                class StartedBeforeSpec(Specification):
                    def __init__(self, date: datetime):
                        self.date = date
                    def is_satisfied_by(self, run: PipelineRun) -> bool:
                        return run.started_at <= self.date
                specs.append(StartedBeforeSpec(query.time_range_end))
            
            spec = None
            if specs:
                from ...shared.repository import AndSpecification
                spec = AndSpecification(*specs)
            
            runs = await self.pipeline_run_repository.find_all(spec=spec)
            
            # Calculate analytics
            total_runs = len(runs)
            successful_runs = len([r for r in runs if r.status == "completed"])
            failed_runs = len([r for r in runs if r.status == "failed"])
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            # Calculate execution time statistics
            execution_times = []
            for run in runs:
                if run.started_at and run.completed_at:
                    duration = (run.completed_at - run.started_at).total_seconds()
                    execution_times.append(duration)
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Group by time period
            time_series_data = []
            if runs:
                # Group runs by the specified time period
                from collections import defaultdict
                grouped_runs = defaultdict(list)
                
                for run in runs:
                    if query.group_by == "hour":
                        key = run.started_at.strftime("%Y-%m-%d %H:00")
                    elif query.group_by == "day":
                        key = run.started_at.strftime("%Y-%m-%d")
                    elif query.group_by == "week":
                        # Get Monday of the week
                        monday = run.started_at - datetime.timedelta(days=run.started_at.weekday())
                        key = monday.strftime("%Y-%m-%d")
                    else:  # month
                        key = run.started_at.strftime("%Y-%m")
                    
                    grouped_runs[key].append(run)
                
                # Create time series data
                for period, period_runs in grouped_runs.items():
                    period_successful = len([r for r in period_runs if r.status == "completed"])
                    period_total = len(period_runs)
                    period_success_rate = (period_successful / period_total * 100) if period_total > 0 else 0
                    
                    time_series_data.append({
                        "period": period,
                        "total_runs": period_total,
                        "successful_runs": period_successful,
                        "success_rate": period_success_rate
                    })
                
                # Sort by period
                time_series_data.sort(key=lambda x: x["period"])
            
            analytics = {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": round(success_rate, 2),
                "avg_execution_time": round(avg_execution_time, 2),
                "time_range": {
                    "start": query.time_range_start.isoformat() if query.time_range_start else None,
                    "end": query.time_range_end.isoformat() if query.time_range_end else None
                }
            }
            
            return PipelineAnalyticsQueryResult(
                success=True,
                analytics=analytics,
                time_series=time_series_data
            )
            
        except Exception as e:
            logger.error(f"Unexpected error getting pipeline analytics: {e}")
            return PipelineAnalyticsQueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )