"""Pipeline domain query handlers.

CQRS Query handler implementations that execute pipeline read operations
using repository interfaces and domain services.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ....shared.query import QueryHandler, QueryExecutionError
from ..repositories import (
    PipelineTemplateRepository,
    PipelineRunRepository,
    StepExecutionRepository,
    ByWorkspaceSpecification,
    ByNameSpecification,
    ByTagSpecification,
    GlobalTemplateSpecification,
    ByTemplateIdSpecification,
    ByStatusSpecification,
    ActiveRunsSpecification,
    CompletedRunsSpecification,
    FailedRunsSpecification,
    DateRangeSpecification,
    ByRunIdSpecification,
    ByStepIdSpecification,
)
from ..services.pipeline_validation_service import PipelineValidationService
from .pipeline_queries import (
    GetPipelineTemplatesQuery,
    GetPipelineTemplatesResult,
    GetPipelineTemplateQuery,
    GetPipelineTemplateResult,
    GetPipelineRunQuery,
    GetPipelineRunResult,
    GetPipelineRunsQuery,
    GetPipelineRunsResult,
    SearchPipelineTemplatesQuery,
    SearchPipelineTemplatesResult,
    GetPipelineHistoryQuery,
    GetPipelineHistoryResult,
    GetPipelineMetricsQuery,
    GetPipelineMetricsResult,
    GetStepExecutionsQuery,
    GetStepExecutionsResult,
    PaginationInfo,
)


class GetPipelineTemplatesHandler(QueryHandler[GetPipelineTemplatesQuery, GetPipelineTemplatesResult]):
    """Handler for listing pipeline templates with filtering and pagination."""
    
    def __init__(
        self,
        template_repository: PipelineTemplateRepository,
        validation_service: Optional[PipelineValidationService] = None
    ):
        self.template_repository = template_repository
        self.validation_service = validation_service
    
    async def handle(self, query: GetPipelineTemplatesQuery) -> GetPipelineTemplatesResult:
        """Execute the templates list query."""
        start_time = time.time()
        
        try:
            # Build specifications for filtering
            specifications = []
            
            # Workspace filtering
            if query.workspace_name:
                specifications.append(ByWorkspaceSpecification(query.workspace_name))
            
            # Include global templates if requested
            if query.include_global:
                specifications.append(GlobalTemplateSpecification())
            
            # Tag filtering
            if query.tags:
                for tag in query.tags:
                    specifications.append(ByTagSpecification(tag))
            
            # Get templates with pagination
            templates = await self.template_repository.find_by_specification(
                specifications,
                page=query.page,
                page_size=query.page_size,
                sort_by=query.sort_by.value,
                sort_direction=query.sort_direction
            )
            
            # Get total counts
            total_count = await self.template_repository.count_by_specification(specifications)
            
            # Calculate workspace vs global breakdown
            workspace_count = 0
            global_count = 0
            
            if query.workspace_name:
                workspace_count = await self.template_repository.count_by_specification([
                    ByWorkspaceSpecification(query.workspace_name)
                ])
            
            if query.include_global:
                global_count = await self.template_repository.count_by_specification([
                    GlobalTemplateSpecification()
                ])
            
            # Build pagination info
            pagination = PaginationInfo(
                page=query.page,
                page_size=query.page_size,
                total_count=total_count,
                total_pages=(total_count + query.page_size - 1) // query.page_size,
                has_next=query.page * query.page_size < total_count,
                has_previous=query.page > 1
            )
            
            # Applied filters summary
            filters_applied = {
                "workspace_name": query.workspace_name,
                "include_global": query.include_global,
                "tags": query.tags,
                "category": query.category,
                "author": query.author,
                "complexity_level": query.complexity_level,
                "sort_by": query.sort_by.value,
                "sort_direction": query.sort_direction
            }
            
            execution_time = time.time() - start_time
            
            return GetPipelineTemplatesResult(
                success=True,
                data=templates,
                templates=templates,
                pagination=pagination,
                filters_applied=filters_applied,
                total_global_templates=global_count,
                total_workspace_templates=workspace_count,
                total_count=total_count,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get pipeline templates: {str(e)}",
                e,
                query
            )
    
    async def validate(self, query: GetPipelineTemplatesQuery) -> List[str]:
        """Validate the templates list query."""
        errors = []
        
        if query.page < 1:
            errors.append("Page must be >= 1")
        
        if query.page_size < 1 or query.page_size > 1000:
            errors.append("Page size must be between 1 and 1000")
        
        if query.sort_direction not in ("asc", "desc"):
            errors.append("Sort direction must be 'asc' or 'desc'")
        
        return errors


class GetPipelineTemplateHandler(QueryHandler[GetPipelineTemplateQuery, GetPipelineTemplateResult]):
    """Handler for getting a specific pipeline template."""
    
    def __init__(
        self,
        template_repository: PipelineTemplateRepository,
        run_repository: Optional[PipelineRunRepository] = None
    ):
        self.template_repository = template_repository
        self.run_repository = run_repository
    
    async def handle(self, query: GetPipelineTemplateQuery) -> GetPipelineTemplateResult:
        """Execute the template get query."""
        start_time = time.time()
        
        try:
            # Get the template
            template = await self.template_repository.get_by_id(query.template_id)
            
            if not template:
                execution_time = time.time() - start_time
                return GetPipelineTemplateResult(
                    success=True,
                    data=None,
                    template=None,
                    execution_time=execution_time
                )
            
            # Check if it's a global template
            is_global = template.metadata.get("workspace") is None
            
            # Get usage stats if requested
            usage_stats = None
            recent_runs = []
            
            if query.include_usage_stats and self.run_repository:
                # Get run count and recent executions
                run_count = await self.run_repository.count_by_specification([
                    ByTemplateIdSpecification(query.template_id)
                ])
                
                # Get recent runs (last 10)
                recent_run_list = await self.run_repository.find_by_specification(
                    [ByTemplateIdSpecification(query.template_id)],
                    page=1,
                    page_size=10,
                    sort_by="created_at",
                    sort_direction="desc"
                )
                
                recent_runs = [run.to_dict() for run in recent_run_list]
                
                usage_stats = {
                    "total_runs": run_count,
                    "recent_runs_count": len(recent_runs),
                    "last_used": recent_runs[0]["created_at"] if recent_runs else None
                }
            
            execution_time = time.time() - start_time
            
            return GetPipelineTemplateResult(
                success=True,
                data=template,
                template=template,
                usage_stats=usage_stats,
                recent_runs=recent_runs,
                is_global=is_global,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get pipeline template: {str(e)}",
                e,
                query
            )
    
    async def validate(self, query: GetPipelineTemplateQuery) -> List[str]:
        """Validate the template get query."""
        errors = []
        
        if not query.template_id:
            errors.append("Template ID is required")
        
        return errors


class GetPipelineRunHandler(QueryHandler[GetPipelineRunQuery, GetPipelineRunResult]):
    """Handler for getting a specific pipeline run."""
    
    def __init__(
        self,
        run_repository: PipelineRunRepository,
        step_repository: Optional[StepExecutionRepository] = None,
        template_repository: Optional[PipelineTemplateRepository] = None
    ):
        self.run_repository = run_repository
        self.step_repository = step_repository
        self.template_repository = template_repository
    
    async def handle(self, query: GetPipelineRunQuery) -> GetPipelineRunResult:
        """Execute the run get query."""
        start_time = time.time()
        
        try:
            # Get the run
            run = await self.run_repository.get_by_id(query.run_id)
            
            if not run:
                execution_time = time.time() - start_time
                return GetPipelineRunResult(
                    success=True,
                    data=None,
                    run=None,
                    execution_time=execution_time
                )
            
            # Filter by workspace if specified
            if query.workspace_name and run.workspace_name != query.workspace_name:
                execution_time = time.time() - start_time
                return GetPipelineRunResult(
                    success=True,
                    data=None,
                    run=None,
                    execution_time=execution_time
                )
            
            step_executions = []
            execution_metrics = None
            template_info = None
            
            # Get step executions if requested
            if query.include_step_executions and self.step_repository:
                step_executions = await self.step_repository.find_by_specification([
                    ByRunIdSpecification(query.run_id)
                ])
            
            # Get execution metrics if requested
            if query.include_metrics:
                execution_metrics = {
                    "total_duration": run.duration,
                    "total_tokens": run.get_total_tokens(),
                    "token_breakdown": run.total_tokens_used,
                    "step_count": len(step_executions),
                    "status_changes": run.metadata.get("status_changes", []),
                    "execution_mode": run.metadata.get("mode", "normal")
                }
            
            # Get template info if available
            if self.template_repository:
                template = await self.template_repository.get_by_id(run.pipeline_id)
                if template:
                    template_info = {
                        "name": template.name,
                        "description": template.description,
                        "version": template.version,
                        "author": template.author,
                        "step_count": len(template.steps)
                    }
            
            execution_time = time.time() - start_time
            
            return GetPipelineRunResult(
                success=True,
                data=run,
                run=run,
                step_executions=step_executions,
                execution_metrics=execution_metrics,
                template_info=template_info,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get pipeline run: {str(e)}",
                e,
                query
            )
    
    async def validate(self, query: GetPipelineRunQuery) -> List[str]:
        """Validate the run get query."""
        errors = []
        
        if not query.run_id:
            errors.append("Run ID is required")
        
        return errors


class GetPipelineRunsHandler(QueryHandler[GetPipelineRunsQuery, GetPipelineRunsResult]):
    """Handler for listing pipeline runs with filtering and pagination."""
    
    def __init__(self, run_repository: PipelineRunRepository):
        self.run_repository = run_repository
    
    async def handle(self, query: GetPipelineRunsQuery) -> GetPipelineRunsResult:
        """Execute the runs list query."""
        start_time = time.time()
        
        try:
            # Build specifications for filtering
            specifications = []
            
            # Workspace filtering
            if query.workspace_name:
                specifications.append(ByWorkspaceSpecification(query.workspace_name))
            
            # Template filtering
            if query.template_id:
                specifications.append(ByTemplateIdSpecification(query.template_id))
            
            # Status filtering
            if query.status_filter:
                for status in query.status_filter:
                    specifications.append(ByStatusSpecification(status))
            
            # Date range filtering
            if query.start_date or query.end_date:
                specifications.append(DateRangeSpecification(
                    start_date=query.start_date,
                    end_date=query.end_date
                ))
            
            # Get runs with pagination
            runs = await self.run_repository.find_by_specification(
                specifications,
                page=query.page,
                page_size=query.page_size,
                sort_by=query.sort_by.value,
                sort_direction=query.sort_direction
            )
            
            # Get total count
            total_count = await self.run_repository.count_by_specification(specifications)
            
            # Build status summary
            status_summary = {}
            all_runs = await self.run_repository.find_by_specification(specifications)
            for run in all_runs:
                status = str(run.status.status)
                status_summary[status] = status_summary.get(status, 0) + 1
            
            # Date range stats
            date_range_stats = {}
            if query.start_date and query.end_date:
                date_range_stats = {
                    "start_date": query.start_date.isoformat(),
                    "end_date": query.end_date.isoformat(),
                    "total_days": (query.end_date - query.start_date).days,
                    "runs_in_range": len(runs)
                }
            
            # Build pagination info
            pagination = PaginationInfo(
                page=query.page,
                page_size=query.page_size,
                total_count=total_count,
                total_pages=(total_count + query.page_size - 1) // query.page_size,
                has_next=query.page * query.page_size < total_count,
                has_previous=query.page > 1
            )
            
            execution_time = time.time() - start_time
            
            return GetPipelineRunsResult(
                success=True,
                data=runs,
                runs=runs,
                pagination=pagination,
                status_summary=status_summary,
                date_range_stats=date_range_stats,
                total_count=total_count,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get pipeline runs: {str(e)}",
                e,
                query
            )


class SearchPipelineTemplatesHandler(QueryHandler[SearchPipelineTemplatesQuery, SearchPipelineTemplatesResult]):
    """Handler for searching pipeline templates by text content."""
    
    def __init__(self, template_repository: PipelineTemplateRepository):
        self.template_repository = template_repository
    
    async def handle(self, query: SearchPipelineTemplatesQuery) -> SearchPipelineTemplatesResult:
        """Execute the template search query."""
        start_time = time.time()
        
        try:
            # For now, implement a simple text search
            # In a real implementation, you'd use a proper search engine
            all_templates = await self.template_repository.find_all()
            
            search_results = []
            search_term_lower = query.search_term.lower()
            
            for template in all_templates:
                relevance_score = 0.0
                matching_fields = []
                
                # Search in name
                if "name" in query.search_fields and search_term_lower in template.name.lower():
                    relevance_score += 1.0
                    matching_fields.append("name")
                
                # Search in description
                if "description" in query.search_fields and search_term_lower in template.description.lower():
                    relevance_score += 0.8
                    matching_fields.append("description")
                
                # Search in tags
                if "tags" in query.search_fields:
                    for tag in template.tags:
                        if search_term_lower in tag.lower():
                            relevance_score += 0.6
                            matching_fields.append("tags")
                            break
                
                # Apply filters
                if query.category_filter and template.metadata.get("category") != query.category_filter:
                    continue
                
                if query.tag_filter:
                    if not any(tag in template.tags for tag in query.tag_filter):
                        continue
                
                # Check minimum relevance
                if relevance_score >= query.min_relevance_score:
                    search_results.append({
                        "template": template,
                        "relevance_score": relevance_score,
                        "matching_fields": matching_fields
                    })
            
            # Sort by relevance score
            search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Apply pagination
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            paginated_results = search_results[start_idx:end_idx]
            
            # Build pagination info
            total_count = len(search_results)
            pagination = PaginationInfo(
                page=query.page,
                page_size=query.page_size,
                total_count=total_count,
                total_pages=(total_count + query.page_size - 1) // query.page_size,
                has_next=end_idx < total_count,
                has_previous=query.page > 1
            )
            
            # Search metadata
            search_metadata = {
                "search_term": query.search_term,
                "fields_searched": query.search_fields,
                "total_matches": total_count,
                "max_relevance_score": max([r["relevance_score"] for r in search_results]) if search_results else 0.0,
                "filters_applied": {
                    "category": query.category_filter,
                    "tags": query.tag_filter,
                    "min_relevance": query.min_relevance_score
                }
            }
            
            execution_time = time.time() - start_time
            
            return SearchPipelineTemplatesResult(
                success=True,
                data=paginated_results,
                templates=paginated_results,
                search_metadata=search_metadata,
                pagination=pagination,
                total_count=total_count,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to search pipeline templates: {str(e)}",
                e,
                query
            )


class GetPipelineHistoryHandler(QueryHandler[GetPipelineHistoryQuery, GetPipelineHistoryResult]):
    """Handler for getting pipeline execution history and analytics."""
    
    def __init__(
        self,
        run_repository: PipelineRunRepository,
        step_repository: Optional[StepExecutionRepository] = None
    ):
        self.run_repository = run_repository
        self.step_repository = step_repository
    
    async def handle(self, query: GetPipelineHistoryQuery) -> GetPipelineHistoryResult:
        """Execute the history query."""
        start_time = time.time()
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=query.date_range_days)
            
            # Build specifications
            specifications = [
                DateRangeSpecification(start_date=start_date, end_date=end_date)
            ]
            
            if query.workspace_name:
                specifications.append(ByWorkspaceSpecification(query.workspace_name))
            
            if query.template_id:
                specifications.append(ByTemplateIdSpecification(query.template_id))
            
            # Get runs in date range
            runs = await self.run_repository.find_by_specification(specifications)
            
            # Build time series data
            time_series_data = self._build_time_series(runs, query.group_by_period, start_date, end_date)
            
            # Calculate summary statistics
            summary_statistics = self._calculate_summary_stats(runs)
            
            # Build success rate trend
            success_rate_trend = self._build_success_rate_trend(runs, query.group_by_period)
            
            # Build token usage trend
            token_usage_trend = []
            if query.include_token_usage:
                token_usage_trend = self._build_token_usage_trend(runs, query.group_by_period)
            
            # Performance metrics
            performance_metrics = {}
            if query.include_performance_metrics:
                performance_metrics = self._calculate_performance_metrics(runs)
            
            # Step performance breakdown
            step_performance = {}
            if query.include_step_breakdown and self.step_repository:
                step_performance = await self._calculate_step_performance(runs)
            
            execution_time = time.time() - start_time
            
            return GetPipelineHistoryResult(
                success=True,
                time_series_data=time_series_data,
                summary_statistics=summary_statistics,
                success_rate_trend=success_rate_trend,
                token_usage_trend=token_usage_trend,
                performance_metrics=performance_metrics,
                step_performance=step_performance,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get pipeline history: {str(e)}",
                e,
                query
            )
    
    def _build_time_series(self, runs, group_by_period, start_date, end_date):
        """Build time series data grouped by period."""
        # Implementation would group runs by time periods
        # This is a simplified version
        return [
            {
                "period": start_date.isoformat(),
                "total_runs": len(runs),
                "successful_runs": len([r for r in runs if r.is_completed]),
                "failed_runs": len([r for r in runs if r.is_failed]),
                "avg_duration": sum([r.duration or 0 for r in runs]) / len(runs) if runs else 0
            }
        ]
    
    def _calculate_summary_stats(self, runs):
        """Calculate summary statistics."""
        total_runs = len(runs)
        successful_runs = len([r for r in runs if r.is_completed])
        failed_runs = len([r for r in runs if r.is_failed])
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
            "avg_duration": sum([r.duration or 0 for r in runs]) / total_runs if total_runs > 0 else 0,
            "total_tokens": sum([r.get_total_tokens() for r in runs])
        }
    
    def _build_success_rate_trend(self, runs, group_by_period):
        """Build success rate trend over time."""
        # Simplified implementation
        return [{"period": "current", "success_rate": 0.85}]
    
    def _build_token_usage_trend(self, runs, group_by_period):
        """Build token usage trend over time."""
        # Simplified implementation
        return [{"period": "current", "total_tokens": sum([r.get_total_tokens() for r in runs])}]
    
    def _calculate_performance_metrics(self, runs):
        """Calculate performance metrics."""
        durations = [r.duration for r in runs if r.duration]
        
        if not durations:
            return {}
        
        return {
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations)
        }
    
    async def _calculate_step_performance(self, runs):
        """Calculate step performance breakdown."""
        # Would get step executions for all runs and analyze
        return {"placeholder": "step_performance_data"}


class GetPipelineMetricsHandler(QueryHandler[GetPipelineMetricsQuery, GetPipelineMetricsResult]):
    """Handler for getting pipeline performance metrics and KPIs."""
    
    def __init__(
        self,
        run_repository: PipelineRunRepository,
        template_repository: Optional[PipelineTemplateRepository] = None
    ):
        self.run_repository = run_repository
        self.template_repository = template_repository
    
    async def handle(self, query: GetPipelineMetricsQuery) -> GetPipelineMetricsResult:
        """Execute the metrics query."""
        start_time = time.time()
        
        try:
            # Calculate date ranges
            end_date = datetime.now()
            start_date = end_date - timedelta(days=query.date_range_days)
            
            # Build specifications
            specifications = [
                DateRangeSpecification(start_date=start_date, end_date=end_date)
            ]
            
            if query.workspace_name:
                specifications.append(ByWorkspaceSpecification(query.workspace_name))
            
            # Get runs
            runs = await self.run_repository.find_by_specification(specifications)
            
            # Filter by template IDs if specified
            if query.template_ids:
                runs = [r for r in runs if r.pipeline_id in query.template_ids]
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(runs)
            
            # Calculate per-template metrics
            template_metrics = {}
            if query.template_ids:
                for template_id in query.template_ids:
                    template_runs = [r for r in runs if r.pipeline_id == template_id]
                    template_metrics[str(template_id)] = self._calculate_overall_metrics(template_runs)
            
            # Cost analysis
            cost_analysis = {}
            if query.include_cost_analysis:
                cost_analysis = self._calculate_cost_analysis(runs)
            
            # Performance benchmarks
            performance_benchmarks = {}
            if query.include_performance_breakdown:
                performance_benchmarks = self._calculate_performance_benchmarks(runs)
            
            # Error analysis
            error_analysis = {}
            if query.include_error_analysis:
                error_analysis = self._calculate_error_analysis(runs)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(overall_metrics, error_analysis)
            
            execution_time = time.time() - start_time
            
            return GetPipelineMetricsResult(
                success=True,
                overall_metrics=overall_metrics,
                template_metrics=template_metrics,
                cost_analysis=cost_analysis,
                performance_benchmarks=performance_benchmarks,
                error_analysis=error_analysis,
                recommendations=recommendations,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get pipeline metrics: {str(e)}",
                e,
                query
            )
    
    def _calculate_overall_metrics(self, runs):
        """Calculate overall metrics for a set of runs."""
        total_runs = len(runs)
        if total_runs == 0:
            return {"total_runs": 0}
        
        successful_runs = len([r for r in runs if r.is_completed])
        failed_runs = len([r for r in runs if r.is_failed])
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": successful_runs / total_runs,
            "failure_rate": failed_runs / total_runs,
            "avg_duration": sum([r.duration or 0 for r in runs]) / total_runs,
            "total_tokens": sum([r.get_total_tokens() for r in runs]),
            "avg_tokens_per_run": sum([r.get_total_tokens() for r in runs]) / total_runs
        }
    
    def _calculate_cost_analysis(self, runs):
        """Calculate cost analysis."""
        # Simplified cost calculation
        total_tokens = sum([r.get_total_tokens() for r in runs])
        estimated_cost = total_tokens * 0.00002  # Example rate
        
        return {
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
            "cost_per_run": estimated_cost / len(runs) if runs else 0,
            "token_efficiency": total_tokens / len([r for r in runs if r.is_completed]) if runs else 0
        }
    
    def _calculate_performance_benchmarks(self, runs):
        """Calculate performance benchmarks."""
        durations = [r.duration for r in runs if r.duration]
        
        if not durations:
            return {}
        
        return {
            "avg_duration": sum(durations) / len(durations),
            "p50_duration": sorted(durations)[len(durations) // 2],
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)],
            "p99_duration": sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 100 else max(durations)
        }
    
    def _calculate_error_analysis(self, runs):
        """Calculate error analysis."""
        failed_runs = [r for r in runs if r.is_failed]
        
        if not failed_runs:
            return {"total_errors": 0}
        
        error_types = {}
        for run in failed_runs:
            error_msg = run.error or "Unknown error"
            error_type = error_msg.split(":")[0] if ":" in error_msg else "Unknown"
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(failed_runs),
            "error_rate": len(failed_runs) / len(runs) if runs else 0,
            "error_types": error_types,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def _generate_recommendations(self, overall_metrics, error_analysis):
        """Generate performance recommendations."""
        recommendations = []
        
        if overall_metrics.get("success_rate", 1.0) < 0.9:
            recommendations.append("Consider improving error handling - success rate below 90%")
        
        if error_analysis.get("error_rate", 0) > 0.1:
            recommendations.append("High error rate detected - review pipeline configurations")
        
        if overall_metrics.get("avg_duration", 0) > 300:  # 5 minutes
            recommendations.append("Average execution time is high - consider optimization")
        
        return recommendations


class GetStepExecutionsHandler(QueryHandler[GetStepExecutionsQuery, GetStepExecutionsResult]):
    """Handler for listing step executions with filtering and pagination."""
    
    def __init__(self, step_repository: StepExecutionRepository):
        self.step_repository = step_repository
    
    async def handle(self, query: GetStepExecutionsQuery) -> GetStepExecutionsResult:
        """Execute the step executions query."""
        start_time = time.time()
        
        try:
            # Build specifications
            specifications = []
            
            if query.run_id:
                specifications.append(ByRunIdSpecification(query.run_id))
            
            if query.step_id:
                specifications.append(ByStepIdSpecification(query.step_id))
            
            # Date range filtering
            if query.date_range_days > 0:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=query.date_range_days)
                specifications.append(DateRangeSpecification(start_date, end_date))
            
            # Get executions with pagination
            executions = await self.step_repository.find_by_specification(
                specifications,
                page=query.page,
                page_size=query.page_size,
                sort_by=query.sort_by.value,
                sort_direction=query.sort_direction
            )
            
            # Get total count
            total_count = await self.step_repository.count_by_specification(specifications)
            
            # Calculate summary and performance stats
            execution_summary = self._calculate_execution_summary(executions)
            performance_stats = self._calculate_performance_stats(executions)
            error_patterns = self._analyze_error_patterns(executions)
            
            # Build pagination info
            pagination = PaginationInfo(
                page=query.page,
                page_size=query.page_size,
                total_count=total_count,
                total_pages=(total_count + query.page_size - 1) // query.page_size,
                has_next=query.page * query.page_size < total_count,
                has_previous=query.page > 1
            )
            
            execution_time = time.time() - start_time
            
            return GetStepExecutionsResult(
                success=True,
                data=executions,
                executions=executions,
                pagination=pagination,
                execution_summary=execution_summary,
                performance_stats=performance_stats,
                error_patterns=error_patterns,
                total_count=total_count,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise QueryExecutionError(
                f"Failed to get step executions: {str(e)}",
                e,
                query
            )
    
    def _calculate_execution_summary(self, executions):
        """Calculate execution summary."""
        total = len(executions)
        if total == 0:
            return {"total_executions": 0}
        
        successful = len([e for e in executions if e.status.is_successful])
        failed = len([e for e in executions if e.status.is_failed])
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / total,
            "failure_rate": failed / total
        }
    
    def _calculate_performance_stats(self, executions):
        """Calculate performance statistics."""
        durations = [e.duration for e in executions if e.duration]
        
        if not durations:
            return {}
        
        return {
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations)
        }
    
    def _analyze_error_patterns(self, executions):
        """Analyze error patterns."""
        failed_executions = [e for e in executions if e.status.is_failed]
        
        if not failed_executions:
            return []
        
        error_patterns = {}
        for execution in failed_executions:
            error_msg = execution.status.error_message or "Unknown error"
            error_type = error_msg.split(":")[0] if ":" in error_msg else "Unknown"
            
            if error_type not in error_patterns:
                error_patterns[error_type] = {
                    "count": 0,
                    "examples": []
                }
            
            error_patterns[error_type]["count"] += 1
            if len(error_patterns[error_type]["examples"]) < 3:
                error_patterns[error_type]["examples"].append(error_msg)
        
        return [
            {
                "error_type": error_type,
                "count": data["count"],
                "examples": data["examples"]
            }
            for error_type, data in sorted(error_patterns.items(), key=lambda x: x[1]["count"], reverse=True)
        ]