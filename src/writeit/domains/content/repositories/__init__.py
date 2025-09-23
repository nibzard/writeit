"""Content domain repositories.

Repository interfaces for content domain entities providing
data access operations for templates, styles, and generated content.
"""

from .content_template_repository import (
    ContentTemplateRepository,
    ByContentTypeSpecification,
    ByFormatSpecification,
    ByTagSpecification,
    GlobalTemplateSpecification,
    UsesVariableSpecification,
)

from .style_primer_repository import (
    StylePrimerRepository,
    ByCategorySpecification,
    ByToneSpecification,
    GlobalStyleSpecification,
    InheritsFromSpecification,
)

from .generated_content_repository import (
    GeneratedContentRepository,
    ByPipelineRunSpecification,
    ByTemplateSpecification,
    ByStyleSpecification,
    DateRangeSpecification,
    RecentContentSpecification,
)

__all__ = [
    # Repository interfaces
    "ContentTemplateRepository",
    "StylePrimerRepository", 
    "GeneratedContentRepository",
    
    # Template specifications
    "ByContentTypeSpecification",
    "ByFormatSpecification",
    "ByTagSpecification",
    "GlobalTemplateSpecification",
    "UsesVariableSpecification",
    
    # Style specifications
    "ByCategorySpecification",
    "ByToneSpecification", 
    "GlobalStyleSpecification",
    "InheritsFromSpecification",
    
    # Content specifications
    "ByPipelineRunSpecification",
    "ByTemplateSpecification",
    "ByStyleSpecification",
    "DateRangeSpecification",
    "RecentContentSpecification",
]