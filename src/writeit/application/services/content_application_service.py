"""Content Application Service.

Handles content creation and management workflows, coordinating template
management, style application, and content generation across domains.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Union, AsyncGenerator
from enum import Enum
from datetime import datetime
from pathlib import Path

from ...domains.content.services import (
    TemplateManagementService,
    StyleManagementService,
    ContentGenerationService,
    TemplateCreationOptions,
    StyleCreationOptions,
    ContentCreationOptions,
    TemplateValidationResult,
    StyleValidationResult,
    ContentValidationResult,
    ContentQualityAssessment,
    QualityAssessmentLevel,
    ContentOptimizationLevel,
    StyleCompatibilityLevel,
    StyleOptimizationLevel,
)
from ...domains.content.entities import Template, StylePrimer, GeneratedContent
from ...domains.content.value_objects import (
    TemplateName,
    StyleName,
    ContentId,
    ContentType,
    ContentFormat,
    ContentLength,
    ValidationRule,
)
from ...domains.workspace.services import (
    WorkspaceManagementService,
    WorkspaceAnalyticsService,
)
from ...domains.workspace.entities import Workspace
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
)


class ContentCreationMode(str, Enum):
    """Content creation modes."""
    INTERACTIVE = "interactive"    # Interactive creation with prompts
    BATCH = "batch"               # Batch creation from specifications
    TEMPLATE_BASED = "template_based"  # Generate from existing templates
    STYLE_GUIDED = "style_guided"  # Style-first content creation


class ContentValidationLevel(str, Enum):
    """Content validation levels."""
    BASIC = "basic"       # Basic syntax and structure
    STANDARD = "standard" # Standard quality checks
    STRICT = "strict"     # Comprehensive validation
    CUSTOM = "custom"     # Custom validation rules


class ContentOptimizationGoal(str, Enum):
    """Content optimization goals."""
    QUALITY = "quality"       # Optimize for content quality
    PERFORMANCE = "performance"  # Optimize for generation speed
    COST = "cost"            # Optimize for cost efficiency
    CONSISTENCY = "consistency"  # Optimize for style consistency


class ContentListingScope(str, Enum):
    """Content listing scopes."""
    WORKSPACE = "workspace"   # Workspace-specific content
    GLOBAL = "global"        # Global templates and styles
    ALL = "all"             # All available content
    USER_CREATED = "user_created"  # User-created content only


@dataclass
class TemplateCreationRequest:
    """Request for template creation."""
    name: str
    description: str
    content: str
    workspace_name: Optional[str] = None
    validation_level: ContentValidationLevel = ContentValidationLevel.STANDARD
    creation_options: Optional[TemplateCreationOptions] = None
    inherit_from: Optional[str] = None


@dataclass
class StyleCreationRequest:
    """Request for style primer creation."""
    name: str
    description: str
    style_content: str
    workspace_name: Optional[str] = None
    validation_level: ContentValidationLevel = ContentValidationLevel.STANDARD
    creation_options: Optional[StyleCreationOptions] = None
    base_style: Optional[str] = None


@dataclass
class ContentGenerationRequest:
    """Request for content generation."""
    template_name: str
    style_name: Optional[str] = None
    workspace_name: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    creation_mode: ContentCreationMode = ContentCreationMode.TEMPLATE_BASED
    quality_level: QualityAssessmentLevel = QualityAssessmentLevel.STANDARD
    optimization_goal: ContentOptimizationGoal = ContentOptimizationGoal.QUALITY


@dataclass
class ContentListingRequest:
    """Request for content listing."""
    scope: ContentListingScope = ContentListingScope.WORKSPACE
    workspace_name: Optional[str] = None
    content_type: Optional[str] = None  # "template", "style", "generated"
    filter_pattern: Optional[str] = None
    include_metadata: bool = True
    include_analytics: bool = False


@dataclass
class ContentValidationRequest:
    """Request for content validation."""
    content_identifier: str  # Template name, style name, or content ID
    content_type: str        # "template", "style", "generated"
    workspace_name: Optional[str] = None
    validation_level: ContentValidationLevel = ContentValidationLevel.STANDARD
    custom_rules: Optional[List[str]] = None


@dataclass
class ContentOptimizationRequest:
    """Request for content optimization."""
    content_identifier: str
    content_type: str
    workspace_name: Optional[str] = None
    optimization_goal: ContentOptimizationGoal = ContentOptimizationGoal.QUALITY
    optimization_level: ContentOptimizationLevel = ContentOptimizationLevel.STANDARD


@dataclass
class ContentAnalysisRequest:
    """Request for content analysis."""
    workspace_name: Optional[str] = None
    content_types: Optional[List[str]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    include_usage_patterns: bool = True
    include_performance_metrics: bool = True


class ContentApplicationError(Exception):
    """Base exception for content application service errors."""
    pass


class ContentCreationError(ContentApplicationError):
    """Content creation failed."""
    pass


class ContentValidationError(ContentApplicationError):
    """Content validation failed."""
    pass


class ContentNotFoundError(ContentApplicationError):
    """Content not found."""
    pass


class ContentOptimizationError(ContentApplicationError):
    """Content optimization failed."""
    pass


class ContentApplicationService:
    """
    Application service for content operations.
    
    Orchestrates template management, style application, content generation,
    and quality assessment across domains. Provides high-level use cases
    for content creation and management workflows.
    """
    
    def __init__(
        self,
        # Content domain services
        template_management_service: TemplateManagementService,
        style_management_service: StyleManagementService,
        content_generation_service: ContentGenerationService,
        
        # Cross-domain services
        workspace_management_service: WorkspaceManagementService,
        workspace_analytics_service: WorkspaceAnalyticsService,
        llm_orchestration_service: LLMOrchestrationService,
        cache_management_service: CacheManagementService,
    ):
        """Initialize the content application service."""
        # Content domain services
        self._template_management = template_management_service
        self._style_management = style_management_service
        self._content_generation = content_generation_service
        
        # Cross-domain services
        self._workspace_management = workspace_management_service
        self._workspace_analytics = workspace_analytics_service
        self._llm_orchestration = llm_orchestration_service
        self._cache_management = cache_management_service

    async def create_template(
        self, 
        request: TemplateCreationRequest
    ) -> Template:
        """
        Create a new template with comprehensive validation.
        
        Args:
            request: Template creation request
            
        Returns:
            Created template
            
        Raises:
            ContentCreationError: If template creation fails
        """
        try:
            # Resolve workspace
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Check for existing template
            existing = await self._template_management.get_template(
                TemplateName(request.name), workspace
            )
            if existing:
                raise ContentCreationError(f"Template '{request.name}' already exists")
            
            # Validate template content
            validation_result = await self._template_management.validate_template_content(
                request.content,
                workspace=workspace,
                validation_level=request.validation_level.value
            )
            
            if not validation_result.is_valid:
                raise ContentValidationError(
                    f"Template validation failed: {validation_result.errors}"
                )
            
            # Handle inheritance if specified
            creation_options = request.creation_options or TemplateCreationOptions()
            if request.inherit_from:
                parent_template = await self._template_management.get_template(
                    TemplateName(request.inherit_from), workspace
                )
                if parent_template:
                    creation_options.inherit_from = parent_template
            
            # Create template
            template = await self._template_management.create_template(
                name=TemplateName(request.name),
                description=request.description,
                content=request.content,
                workspace=workspace,
                options=creation_options
            )
            
            # Record creation in analytics
            await self._workspace_analytics.record_template_creation(
                workspace.name, template.name
            )
            
            return template
            
        except Exception as e:
            raise ContentCreationError(f"Failed to create template: {e}") from e

    async def create_style(
        self, 
        request: StyleCreationRequest
    ) -> StylePrimer:
        """
        Create a new style primer with validation.
        
        Args:
            request: Style creation request
            
        Returns:
            Created style primer
            
        Raises:
            ContentCreationError: If style creation fails
        """
        try:
            # Resolve workspace
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Check for existing style
            existing = await self._style_management.get_style(
                StyleName(request.name), workspace
            )
            if existing:
                raise ContentCreationError(f"Style '{request.name}' already exists")
            
            # Validate style content
            validation_result = await self._style_management.validate_style_content(
                request.style_content,
                workspace=workspace,
                validation_level=request.validation_level.value
            )
            
            if not validation_result.is_valid:
                raise ContentValidationError(
                    f"Style validation failed: {validation_result.errors}"
                )
            
            # Handle base style if specified
            creation_options = request.creation_options or StyleCreationOptions()
            if request.base_style:
                base_style_obj = await self._style_management.get_style(
                    StyleName(request.base_style), workspace
                )
                if base_style_obj:
                    creation_options.base_style = base_style_obj
            
            # Create style
            style = await self._style_management.create_style(
                name=StyleName(request.name),
                description=request.description,
                style_content=request.style_content,
                workspace=workspace,
                options=creation_options
            )
            
            # Record creation in analytics
            await self._workspace_analytics.record_style_creation(
                workspace.name, style.name
            )
            
            return style
            
        except Exception as e:
            raise ContentCreationError(f"Failed to create style: {e}") from e

    async def generate_content(
        self, 
        request: ContentGenerationRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate content with streaming results.
        
        Args:
            request: Content generation request
            
        Yields:
            Content generation progress and results
            
        Raises:
            ContentCreationError: If content generation fails
        """
        try:
            # Resolve workspace
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Load template
            template = await self._template_management.get_template(
                TemplateName(request.template_name), workspace
            )
            if not template:
                raise ContentNotFoundError(f"Template '{request.template_name}' not found")
            
            # Load style if specified
            style = None
            if request.style_name:
                style = await self._style_management.get_style(
                    StyleName(request.style_name), workspace
                )
                if not style:
                    raise ContentNotFoundError(f"Style '{request.style_name}' not found")
            
            # Validate template-style compatibility
            if style:
                compatibility = await self._style_management.check_template_compatibility(
                    template, style
                )
                if compatibility.compatibility_level == StyleCompatibilityLevel.INCOMPATIBLE:
                    raise ContentCreationError(
                        f"Template and style are incompatible: {compatibility.issues}"
                    )
            
            # Configure generation options
            generation_options = ContentCreationOptions(
                quality_level=request.quality_level,
                optimization_goal=request.optimization_goal.value,
                enable_caching=True,
                enable_streaming=True
            )
            
            # Generate content with streaming
            async for generation_state in self._content_generation.generate_content_stream(
                template=template,
                style=style,
                inputs=request.inputs or {},
                workspace=workspace,
                options=generation_options
            ):
                # Yield progress updates
                yield {
                    "status": generation_state.status.value,
                    "progress": generation_state.progress,
                    "current_step": generation_state.current_step,
                    "partial_content": generation_state.partial_content,
                    "quality_metrics": generation_state.quality_metrics,
                    "warnings": generation_state.warnings,
                    "errors": generation_state.errors
                }
                
                # Record generation progress
                await self._workspace_analytics.record_content_generation_progress(
                    workspace.name, template.name, generation_state
                )
            
            # Final result
            yield {
                "status": "completed",
                "progress": 100,
                "content": generation_state.final_content,
                "quality_assessment": generation_state.quality_assessment,
                "generation_metrics": generation_state.generation_metrics,
                "optimization_suggestions": generation_state.optimization_suggestions
            }
            
        except Exception as e:
            raise ContentCreationError(f"Content generation failed: {e}") from e

    async def list_content(
        self, 
        request: ContentListingRequest
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        List available content across types.
        
        Args:
            request: Content listing request
            
        Returns:
            Dictionary of content lists by type
        """
        try:
            # Resolve workspace if needed
            workspace = None
            if request.scope in [ContentListingScope.WORKSPACE, ContentListingScope.ALL]:
                workspace = await self._resolve_workspace(request.workspace_name)
            
            result = {}
            
            # List templates
            if not request.content_type or request.content_type == "template":
                templates = await self._list_templates(request, workspace)
                result["templates"] = templates
            
            # List styles
            if not request.content_type or request.content_type == "style":
                styles = await self._list_styles(request, workspace)
                result["styles"] = styles
            
            # List generated content
            if not request.content_type or request.content_type == "generated":
                generated_content = await self._list_generated_content(request, workspace)
                result["generated_content"] = generated_content
            
            return result
            
        except Exception as e:
            raise ContentApplicationError(f"Failed to list content: {e}") from e

    async def validate_content(
        self, 
        request: ContentValidationRequest
    ) -> Dict[str, Any]:
        """
        Validate content with comprehensive checks.
        
        Args:
            request: Content validation request
            
        Returns:
            Validation result with errors and suggestions
        """
        try:
            workspace = await self._resolve_workspace(request.workspace_name)
            
            validation_result = None
            
            if request.content_type == "template":
                template = await self._template_management.get_template(
                    TemplateName(request.content_identifier), workspace
                )
                if not template:
                    raise ContentNotFoundError(f"Template '{request.content_identifier}' not found")
                
                validation_result = await self._template_management.validate_template_comprehensive(
                    template,
                    workspace=workspace,
                    validation_level=request.validation_level.value,
                    custom_rules=request.custom_rules
                )
                
            elif request.content_type == "style":
                style = await self._style_management.get_style(
                    StyleName(request.content_identifier), workspace
                )
                if not style:
                    raise ContentNotFoundError(f"Style '{request.content_identifier}' not found")
                
                validation_result = await self._style_management.validate_style_comprehensive(
                    style,
                    workspace=workspace,
                    validation_level=request.validation_level.value,
                    custom_rules=request.custom_rules
                )
                
            elif request.content_type == "generated":
                content = await self._content_generation.get_generated_content(
                    ContentId(request.content_identifier), workspace
                )
                if not content:
                    raise ContentNotFoundError(f"Generated content '{request.content_identifier}' not found")
                
                validation_result = await self._content_generation.validate_generated_content(
                    content,
                    validation_level=request.validation_level.value,
                    custom_rules=request.custom_rules
                )
            
            else:
                raise ContentValidationError(f"Unknown content type: {request.content_type}")
            
            return {
                "content_identifier": request.content_identifier,
                "content_type": request.content_type,
                "validation_result": validation_result.to_dict(),
                "recommendations": await self._generate_content_recommendations(
                    validation_result, request.content_type
                )
            }
            
        except Exception as e:
            raise ContentValidationError(f"Content validation failed: {e}") from e

    async def optimize_content(
        self, 
        request: ContentOptimizationRequest
    ) -> Dict[str, Any]:
        """
        Optimize content for specific goals.
        
        Args:
            request: Content optimization request
            
        Returns:
            Optimization results and suggestions
        """
        try:
            workspace = await self._resolve_workspace(request.workspace_name)
            
            optimization_result = None
            
            if request.content_type == "template":
                template = await self._template_management.get_template(
                    TemplateName(request.content_identifier), workspace
                )
                if not template:
                    raise ContentNotFoundError(f"Template '{request.content_identifier}' not found")
                
                optimization_result = await self._template_management.optimize_template(
                    template,
                    optimization_goal=request.optimization_goal.value,
                    optimization_level=request.optimization_level
                )
                
            elif request.content_type == "style":
                style = await self._style_management.get_style(
                    StyleName(request.content_identifier), workspace
                )
                if not style:
                    raise ContentNotFoundError(f"Style '{request.content_identifier}' not found")
                
                optimization_result = await self._style_management.optimize_style(
                    style,
                    optimization_goal=request.optimization_goal.value,
                    optimization_level=request.optimization_level
                )
                
            elif request.content_type == "generated":
                content = await self._content_generation.get_generated_content(
                    ContentId(request.content_identifier), workspace
                )
                if not content:
                    raise ContentNotFoundError(f"Generated content '{request.content_identifier}' not found")
                
                optimization_result = await self._content_generation.optimize_generated_content(
                    content,
                    optimization_goal=request.optimization_goal.value,
                    optimization_level=request.optimization_level
                )
            
            else:
                raise ContentOptimizationError(f"Unknown content type: {request.content_type}")
            
            return {
                "content_identifier": request.content_identifier,
                "content_type": request.content_type,
                "optimization_goal": request.optimization_goal.value,
                "optimization_result": optimization_result.to_dict(),
                "performance_impact": await self._assess_optimization_impact(
                    optimization_result, workspace
                )
            }
            
        except Exception as e:
            raise ContentOptimizationError(f"Content optimization failed: {e}") from e

    async def analyze_content_usage(
        self, 
        request: ContentAnalysisRequest
    ) -> Dict[str, Any]:
        """
        Analyze content usage patterns and performance.
        
        Args:
            request: Content analysis request
            
        Returns:
            Comprehensive content analysis report
        """
        try:
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Get workspace analytics
            workspace_analytics = await self._workspace_analytics.get_content_analytics(
                workspace.name,
                period_start=request.period_start,
                period_end=request.period_end
            )
            
            analysis = {
                "workspace": workspace.name.value,
                "analysis_period": {
                    "start": request.period_start,
                    "end": request.period_end
                },
                "overview": {
                    "total_templates": workspace_analytics.total_templates,
                    "total_styles": workspace_analytics.total_styles,
                    "total_generated_content": workspace_analytics.total_generated_content,
                    "active_templates": workspace_analytics.active_templates,
                    "active_styles": workspace_analytics.active_styles,
                }
            }
            
            # Add usage patterns if requested
            if request.include_usage_patterns:
                analysis["usage_patterns"] = {
                    "most_used_templates": workspace_analytics.most_used_templates,
                    "most_used_styles": workspace_analytics.most_used_styles,
                    "template_style_combinations": workspace_analytics.popular_combinations,
                    "usage_trends": workspace_analytics.usage_trends,
                }
            
            # Add performance metrics if requested
            if request.include_performance_metrics:
                performance_data = await self._get_content_performance_metrics(
                    workspace, request.period_start, request.period_end
                )
                analysis["performance_metrics"] = performance_data
            
            # Add optimization recommendations
            analysis["recommendations"] = await self._generate_content_analysis_recommendations(
                workspace_analytics, workspace
            )
            
            return analysis
            
        except Exception as e:
            raise ContentApplicationError(f"Content analysis failed: {e}") from e

    # Private helper methods
    
    async def _resolve_workspace(self, workspace_name: Optional[str]) -> Workspace:
        """Resolve workspace, using active workspace if none specified."""
        if workspace_name:
            workspace = await self._workspace_management.get_workspace(
                WorkspaceName(workspace_name)
            )
        else:
            workspace = await self._workspace_management.get_active_workspace()
        
        if not workspace:
            raise ContentApplicationError("No workspace available")
        
        return workspace

    async def _list_templates(
        self, 
        request: ContentListingRequest, 
        workspace: Optional[Workspace]
    ) -> List[Dict[str, Any]]:
        """List templates based on request scope."""
        templates = []
        
        if request.scope in [ContentListingScope.WORKSPACE, ContentListingScope.ALL] and workspace:
            workspace_templates = await self._template_management.list_templates(
                workspace, filter_pattern=request.filter_pattern
            )
            for template in workspace_templates:
                template_info = {
                    "name": template.name.value,
                    "description": template.description,
                    "source": "workspace",
                    "workspace": workspace.name.value,
                }
                
                if request.include_metadata:
                    template_info["metadata"] = await self._get_template_metadata(template, workspace)
                
                if request.include_analytics:
                    template_info["analytics"] = await self._get_template_analytics(template, workspace)
                
                templates.append(template_info)
        
        if request.scope in [ContentListingScope.GLOBAL, ContentListingScope.ALL]:
            global_templates = await self._template_management.list_global_templates(
                filter_pattern=request.filter_pattern
            )
            for template in global_templates:
                template_info = {
                    "name": template.name.value,
                    "description": template.description,
                    "source": "global",
                    "workspace": None,
                }
                
                if request.include_metadata:
                    template_info["metadata"] = await self._get_template_metadata(template, None)
                
                templates.append(template_info)
        
        return templates

    async def _list_styles(
        self, 
        request: ContentListingRequest, 
        workspace: Optional[Workspace]
    ) -> List[Dict[str, Any]]:
        """List styles based on request scope."""
        styles = []
        
        if request.scope in [ContentListingScope.WORKSPACE, ContentListingScope.ALL] and workspace:
            workspace_styles = await self._style_management.list_styles(
                workspace, filter_pattern=request.filter_pattern
            )
            for style in workspace_styles:
                style_info = {
                    "name": style.name.value,
                    "description": style.description,
                    "source": "workspace",
                    "workspace": workspace.name.value,
                }
                
                if request.include_metadata:
                    style_info["metadata"] = await self._get_style_metadata(style, workspace)
                
                if request.include_analytics:
                    style_info["analytics"] = await self._get_style_analytics(style, workspace)
                
                styles.append(style_info)
        
        if request.scope in [ContentListingScope.GLOBAL, ContentListingScope.ALL]:
            global_styles = await self._style_management.list_global_styles(
                filter_pattern=request.filter_pattern
            )
            for style in global_styles:
                style_info = {
                    "name": style.name.value,
                    "description": style.description,
                    "source": "global",
                    "workspace": None,
                }
                
                if request.include_metadata:
                    style_info["metadata"] = await self._get_style_metadata(style, None)
                
                styles.append(style_info)
        
        return styles

    async def _list_generated_content(
        self, 
        request: ContentListingRequest, 
        workspace: Optional[Workspace]
    ) -> List[Dict[str, Any]]:
        """List generated content."""
        if not workspace:
            return []
        
        generated_content = await self._content_generation.list_generated_content(
            workspace, filter_pattern=request.filter_pattern
        )
        
        content_list = []
        for content in generated_content:
            content_info = {
                "id": content.id.value,
                "template_name": content.template_name.value if content.template_name else None,
                "style_name": content.style_name.value if content.style_name else None,
                "status": content.status.value,
                "created_at": content.created_at,
                "content_type": content.content_type.value,
                "content_format": content.content_format.value,
            }
            
            if request.include_metadata:
                content_info["metadata"] = {
                    "length": content.content_length.value if content.content_length else None,
                    "quality_score": content.quality_score,
                    "generation_time": content.generation_time,
                }
            
            if request.include_analytics:
                content_info["analytics"] = await self._get_content_analytics(content, workspace)
            
            content_list.append(content_info)
        
        return content_list

    async def _get_template_metadata(
        self, 
        template: Template, 
        workspace: Optional[Workspace]
    ) -> Dict[str, Any]:
        """Get template metadata."""
        return {
            "steps_count": len(template.steps) if hasattr(template, 'steps') else 0,
            "has_dependencies": bool(template.dependencies) if hasattr(template, 'dependencies') else False,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "version": template.version if hasattr(template, 'version') else "1.0",
        }

    async def _get_style_metadata(
        self, 
        style: StylePrimer, 
        workspace: Optional[Workspace]
    ) -> Dict[str, Any]:
        """Get style metadata."""
        return {
            "style_type": style.style_type if hasattr(style, 'style_type') else "general",
            "compatibility_tags": style.compatibility_tags if hasattr(style, 'compatibility_tags') else [],
            "created_at": style.created_at,
            "updated_at": style.updated_at,
        }

    async def _get_template_analytics(
        self, 
        template: Template, 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Get template analytics."""
        analytics = await self._workspace_analytics.get_template_analytics(
            workspace.name, template.name
        )
        return {
            "usage_count": analytics.usage_count,
            "last_used": analytics.last_used,
            "average_generation_time": analytics.average_generation_time,
            "success_rate": analytics.success_rate,
        }

    async def _get_style_analytics(
        self, 
        style: StylePrimer, 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Get style analytics."""
        analytics = await self._workspace_analytics.get_style_analytics(
            workspace.name, style.name
        )
        return {
            "usage_count": analytics.usage_count,
            "last_used": analytics.last_used,
            "popular_combinations": analytics.popular_template_combinations,
        }

    async def _get_content_analytics(
        self, 
        content: GeneratedContent, 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Get generated content analytics."""
        return {
            "views": 0,  # Could be tracked if needed
            "shares": 0,  # Could be tracked if needed
            "feedback_score": content.quality_score,
        }

    async def _get_content_performance_metrics(
        self, 
        workspace: Workspace,
        period_start: Optional[datetime],
        period_end: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get content performance metrics."""
        # Get cache performance for content generation
        cache_stats = await self._cache_management.get_content_cache_stats(
            workspace.name, period_start, period_end
        )
        
        return {
            "generation_performance": {
                "cache_hit_rate": cache_stats.hit_rate,
                "average_generation_time": cache_stats.average_generation_time,
                "cache_savings": cache_stats.cache_savings_percentage,
            },
            "quality_metrics": {
                "average_quality_score": cache_stats.average_quality_score,
                "quality_improvement_rate": cache_stats.quality_trend,
            }
        }

    async def _generate_content_recommendations(
        self, 
        validation_result: Union[TemplateValidationResult, StyleValidationResult, ContentValidationResult],
        content_type: str
    ) -> List[str]:
        """Generate content improvement recommendations."""
        recommendations = []
        
        if not validation_result.is_valid:
            recommendations.append("Address validation errors to improve content quality")
        
        if hasattr(validation_result, 'warnings') and validation_result.warnings:
            recommendations.append("Review and address validation warnings")
        
        if content_type == "template":
            recommendations.append("Consider adding input validation for better user experience")
            recommendations.append("Test template with various input combinations")
        elif content_type == "style":
            recommendations.append("Ensure style is compatible with common template patterns")
            recommendations.append("Test style with different content types")
        
        return recommendations

    async def _assess_optimization_impact(
        self, 
        optimization_result: Any, 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Assess the impact of content optimization."""
        return {
            "estimated_performance_improvement": optimization_result.performance_improvement if hasattr(optimization_result, 'performance_improvement') else 0,
            "estimated_cost_savings": optimization_result.cost_savings if hasattr(optimization_result, 'cost_savings') else 0,
            "quality_impact": optimization_result.quality_impact if hasattr(optimization_result, 'quality_impact') else "neutral",
            "compatibility_impact": optimization_result.compatibility_impact if hasattr(optimization_result, 'compatibility_impact') else "minimal",
        }

    async def _generate_content_analysis_recommendations(
        self, 
        analytics: Any, 
        workspace: Workspace
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on content analysis."""
        recommendations = []
        
        # Template recommendations
        if analytics.unused_templates_count > 5:
            recommendations.append({
                "type": "cleanup",
                "priority": "low",
                "title": "Unused Templates",
                "description": f"You have {analytics.unused_templates_count} unused templates. Consider archiving or removing them.",
                "action": "Review and clean up unused templates"
            })
        
        # Style recommendations
        if analytics.style_usage_diversity < 0.3:  # Low style diversity
            recommendations.append({
                "type": "content_diversity",
                "priority": "medium",
                "title": "Limited Style Usage",
                "description": "You're using a limited set of styles. Consider exploring more style options.",
                "action": "Create or import additional style primers"
            })
        
        # Performance recommendations
        if analytics.average_generation_time > 30:  # Slow generation
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "title": "Slow Content Generation",
                "description": "Content generation is taking longer than optimal. Consider optimization.",
                "action": "Review and optimize templates and styles for better performance"
            })
        
        return recommendations