"""Content domain services.

Provides comprehensive content management services including template lifecycle,
style primer management, and generated content operations following DDD patterns.
"""

from .template_management_service import (
    TemplateManagementService,
    TemplateValidationError,
    TemplateDependencyError,
    TemplateOptimizationError,
    TemplateCreationOptions,
    TemplateDependencyGraph,
    TemplateValidationResult,
    TemplateInheritanceChain,
    TemplatePerformanceMetrics,
    TemplateVersionComparison,
)

from .style_management_service import (
    StyleManagementService,
    StyleValidationError,
    StyleInheritanceError,
    StyleCompositionError,
    StyleCompatibilityLevel,
    StyleOptimizationLevel,
    StyleCreationOptions,
    StyleInheritanceChain,
    StyleCompatibilityMatrix,
    StyleValidationResult,
    StyleCompositionPlan,
    StylePerformanceMetrics,
    StyleRecommendation,
    StyleComparison,
)

from .content_generation_service import (
    ContentGenerationService,
    ContentValidationError,
    ContentOptimizationError,
    ContentAnalysisError,
    QualityAssessmentLevel,
    ContentOptimizationLevel,
    ContentStatus,
    ContentCreationOptions,
    ContentValidationResult,
    ContentQualityAssessment,
    ContentVersionComparison,
    ContentOptimizationPlan,
    ContentAnalytics,
    ContentEnhancementSuggestion,
    ContentInsights,
)

from .template_rendering_service import (
    TemplateRenderingService,
    RenderingMode,
    VariableType,
    VariableDefinition,
    RenderingContext,
    RenderingResult,
    TemplateRenderingError,
    VariableValidationError,
    MissingVariableError,
    TemplateCompilationError,
)

from .content_validation_service import (
    ContentValidationService,
    ValidationSeverity,
    ValidationCategory,
    ValidationIssue,
    ValidationResult,
    ValidationContext,
    ContentValidationError,
    ValidationConfigurationError,
    FormatValidationError,
)

__all__ = [
    # Template Management Service
    "TemplateManagementService",
    "TemplateValidationError",
    "TemplateDependencyError",
    "TemplateOptimizationError",
    "TemplateCreationOptions",
    "TemplateDependencyGraph",
    "TemplateValidationResult",
    "TemplateInheritanceChain",
    "TemplatePerformanceMetrics",
    "TemplateVersionComparison",
    
    # Style Management Service
    "StyleManagementService",
    "StyleValidationError",
    "StyleInheritanceError",
    "StyleCompositionError",
    "StyleCompatibilityLevel",
    "StyleOptimizationLevel",
    "StyleCreationOptions",
    "StyleInheritanceChain",
    "StyleCompatibilityMatrix",
    "StyleValidationResult",
    "StyleCompositionPlan",
    "StylePerformanceMetrics",
    "StyleRecommendation",
    "StyleComparison",
    
    # Content Generation Service
    "ContentGenerationService",
    "ContentValidationError",
    "ContentOptimizationError",
    "ContentAnalysisError",
    "QualityAssessmentLevel",
    "ContentOptimizationLevel",
    "ContentStatus",
    "ContentCreationOptions",
    "ContentValidationResult",
    "ContentQualityAssessment",
    "ContentVersionComparison",
    "ContentOptimizationPlan",
    "ContentAnalytics",
    "ContentEnhancementSuggestion",
    "ContentInsights",
    
    # Template Rendering Service
    "TemplateRenderingService",
    "RenderingMode",
    "VariableType",
    "VariableDefinition",
    "RenderingContext",
    "RenderingResult",
    "TemplateRenderingError",
    "VariableValidationError",
    "MissingVariableError",
    "TemplateCompilationError",
    
    # Content Validation Service
    "ContentValidationService",
    "ValidationSeverity",
    "ValidationCategory",
    "ValidationIssue",
    "ValidationResult",
    "ValidationContext",
    "ContentValidationError",
    "ValidationConfigurationError",
    "FormatValidationError",
]