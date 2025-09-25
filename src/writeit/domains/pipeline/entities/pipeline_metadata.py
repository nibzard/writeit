"""Pipeline metadata entity.

Domain entity for managing pipeline metadata, versioning, and categorization."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, List, Optional, Self, cast
from enum import Enum

from ..value_objects.pipeline_id import PipelineId
from ..value_objects.pipeline_name import PipelineName


class PipelineCategory(str, Enum):
    """Standard pipeline categories."""
    CONTENT_GENERATION = "content_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    CREATIVE = "creative"
    BUSINESS = "business"
    EDUCATION = "education"
    UTILITY = "utility"
    CUSTOM = "custom"


class PipelineComplexity(str, Enum):
    """Pipeline complexity levels."""
    SIMPLE = "simple"      # 1-3 steps, basic logic
    MODERATE = "moderate"  # 4-7 steps, some dependencies
    COMPLEX = "complex"    # 8+ steps, complex dependencies
    ADVANCED = "advanced"  # Advanced patterns, parallel execution


class PipelineStatus(str, Enum):
    """Pipeline template status."""
    DRAFT = "draft"              # Under development
    ACTIVE = "active"            # Ready for use
    DEPRECATED = "deprecated"    # Outdated, use newer version
    ARCHIVED = "archived"        # No longer maintained
    EXPERIMENTAL = "experimental" # Testing new features


@dataclass
class PipelineUsageStats:
    """Pipeline usage statistics."""
    
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    average_execution_time: float = 0.0
    total_tokens_used: int = 0
    last_run_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        if self.total_runs == 0:
            return 0.0
        return 100.0 - self.success_rate
    
    def add_run(self, success: bool, execution_time: float, tokens: int) -> Self:
        """Add a new run to statistics.
        
        Args:
            success: Whether run was successful
            execution_time: Execution time in seconds
            tokens: Tokens used
            
        Returns:
            Updated usage stats
        """
        new_total = self.total_runs + 1
        new_successful = self.successful_runs + (1 if success else 0)
        new_failed = self.failed_runs + (0 if success else 1)
        
        # Calculate new average execution time
        if self.total_runs == 0:
            new_avg_time = execution_time
        else:
            total_time = self.average_execution_time * self.total_runs
            new_avg_time = (total_time + execution_time) / new_total
        
        return replace(
            self,
            total_runs=new_total,
            successful_runs=new_successful,
            failed_runs=new_failed,
            average_execution_time=new_avg_time,
            total_tokens_used=self.total_tokens_used + tokens,
            last_run_at=datetime.now()
        )


@dataclass
class PipelineMetadata:
    """Domain entity for pipeline metadata and categorization.
    
    Manages pipeline metadata, versioning, categorization, and usage statistics.
    Provides rich domain behavior for pipeline discovery and management.
    
    Examples:
        metadata = PipelineMetadata.create(
            pipeline_id=pipeline_id,
            name=PipelineName("Article Generator"),
            category=PipelineCategory.CONTENT_GENERATION,
            complexity=PipelineComplexity.MODERATE
        )
        
        # Update metadata
        metadata = metadata.update_version("2.0.0", "Added new features")
        
        # Add tags
        metadata = metadata.add_tags(["article", "blog", "content"])
        
        # Record usage
        metadata = metadata.record_usage(success=True, execution_time=45.2, tokens=1500)
    """
    
    pipeline_id: PipelineId
    name: PipelineName
    version: str
    category: PipelineCategory
    complexity: PipelineComplexity
    status: PipelineStatus = PipelineStatus.ACTIVE
    description: str = ""
    short_description: str = ""
    author: Optional[str] = None
    organization: Optional[str] = None
    license: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    usage_stats: PipelineUsageStats = field(default_factory=PipelineUsageStats)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate metadata."""
        if not isinstance(self.pipeline_id, PipelineId):
            raise TypeError("Pipeline id must be a PipelineId")
            
        if not isinstance(self.name, PipelineName):
            raise TypeError("Name must be a PipelineName")
            
        if not self.version or not isinstance(self.version, str):
            raise ValueError("Version must be a non-empty string")
            
        if not isinstance(self.category, PipelineCategory):
            raise TypeError("Category must be a PipelineCategory")
            
        if not isinstance(self.complexity, PipelineComplexity):
            raise TypeError("Complexity must be a PipelineComplexity")
            
        if not isinstance(self.status, PipelineStatus):
            raise TypeError("Status must be a PipelineStatus")
            
        if not isinstance(self.tags, list):
            raise TypeError("Tags must be a list")
            
        if not isinstance(self.keywords, list):
            raise TypeError("Keywords must be a list")
            
        if not isinstance(self.requirements, list):
            raise TypeError("Requirements must be a list")
            
        if not isinstance(self.usage_stats, PipelineUsageStats):
            raise TypeError("Usage stats must be a PipelineUsageStats")
            
        # Validate URLs if provided
        if self.repository_url and not self._is_valid_url(self.repository_url):
            raise ValueError("Repository URL must be a valid URL")
            
        if self.documentation_url and not self._is_valid_url(self.documentation_url):
            raise ValueError("Documentation URL must be a valid URL")
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        return url.startswith(('http://', 'https://')) and '.' in url
    
    @property
    def is_published(self) -> bool:
        """Check if pipeline is published."""
        return self.published_at is not None
    
    @property
    def is_deprecated(self) -> bool:
        """Check if pipeline is deprecated."""
        return self.status == PipelineStatus.DEPRECATED
    
    @property
    def is_active(self) -> bool:
        """Check if pipeline is active."""
        return self.status == PipelineStatus.ACTIVE
    
    @property
    def is_experimental(self) -> bool:
        """Check if pipeline is experimental."""
        return self.status == PipelineStatus.EXPERIMENTAL
    
    @property
    def age_days(self) -> int:
        """Get pipeline age in days."""
        return (datetime.now() - self.created_at).days
    
    @property
    def days_since_update(self) -> int:
        """Get days since last update."""
        return (datetime.now() - self.updated_at).days
    
    @property
    def popularity_score(self) -> float:
        """Calculate popularity score based on usage stats."""
        # Simple popularity algorithm
        base_score = min(self.usage_stats.total_runs, 100)  # Cap at 100
        success_bonus = self.usage_stats.success_rate / 10   # 0-10 bonus
        recency_bonus = max(0, 30 - self.days_since_update) / 3  # 0-10 bonus
        
        return base_score + success_bonus + recency_bonus
    
    def has_tag(self, tag: str) -> bool:
        """Check if pipeline has specific tag."""
        return tag.lower() in [t.lower() for t in self.tags]
    
    def has_keyword(self, keyword: str) -> bool:
        """Check if pipeline has specific keyword."""
        return keyword.lower() in [k.lower() for k in self.keywords]
    
    def matches_category(self, category: PipelineCategory) -> bool:
        """Check if pipeline matches category."""
        return self.category == category
    
    def matches_complexity(self, complexity: PipelineComplexity) -> bool:
        """Check if pipeline matches complexity."""
        return self.complexity == complexity
    
    def search_relevance(self, query: str) -> float:
        """Calculate search relevance score for query.
        
        Args:
            query: Search query
            
        Returns:
            Relevance score (0.0 - 1.0)
        """
        query_lower = query.lower()
        score = 0.0
        
        # Name match (highest weight)
        if query_lower in str(self.name).lower():
            score += 0.4
        
        # Description match
        if query_lower in self.description.lower():
            score += 0.2
        
        # Tag match
        if any(query_lower in tag.lower() for tag in self.tags):
            score += 0.2
        
        # Keyword match
        if any(query_lower in keyword.lower() for keyword in self.keywords):
            score += 0.15
        
        # Category match
        if query_lower in self.category.value.lower():
            score += 0.05
        
        return min(score, 1.0)
    
    def update_version(
        self,
        new_version: str,
        change_description: Optional[str] = None
    ) -> Self:
        """Update pipeline version.
        
        Args:
            new_version: New version string
            change_description: Description of changes
            
        Returns:
            Updated metadata
        """
        updates = {
            "version": new_version,
            "updated_at": datetime.now()
        }
        
        if change_description:
            updates["custom_metadata"] = {
                **self.custom_metadata,
                "last_change_description": change_description
            }
        
        return cast(Self, replace(self, **updates))
    
    def update_status(self, status: PipelineStatus) -> Self:
        """Update pipeline status.
        
        Args:
            status: New status
            
        Returns:
            Updated metadata
        """
        updates = {
            "status": status,
            "updated_at": datetime.now()
        }
        
        if status == PipelineStatus.DEPRECATED:
            updates["deprecated_at"] = datetime.now()
        
        return cast(Self, replace(self, **updates))
    
    def publish(self) -> Self:
        """Mark pipeline as published.
        
        Returns:
            Updated metadata with published status
        """
        if self.is_published:
            return self
        
        return replace(
            self,
            status=PipelineStatus.ACTIVE,
            published_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def deprecate(self, reason: Optional[str] = None) -> Self:
        """Deprecate pipeline.
        
        Args:
            reason: Optional deprecation reason
            
        Returns:
            Updated metadata with deprecated status
        """
        updates = {
            "status": PipelineStatus.DEPRECATED,
            "deprecated_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        if reason:
            updates["custom_metadata"] = {
                **self.custom_metadata,
                "deprecation_reason": reason
            }
        
        return cast(Self, replace(self, **updates))
    
    def add_tags(self, new_tags: List[str]) -> Self:
        """Add tags to pipeline.
        
        Args:
            new_tags: Tags to add
            
        Returns:
            Updated metadata with new tags
        """
        # Normalize and deduplicate tags
        normalized_tags = [tag.strip().lower() for tag in new_tags if tag.strip()]
        existing_tags = [tag.lower() for tag in self.tags]
        
        unique_new_tags = []
        for tag in normalized_tags:
            if tag not in existing_tags and tag not in unique_new_tags:
                unique_new_tags.append(tag)
        
        if not unique_new_tags:
            return self
        
        updated_tags = self.tags + unique_new_tags
        
        return replace(
            self,
            tags=updated_tags,
            updated_at=datetime.now()
        )
    
    def remove_tags(self, tags_to_remove: List[str]) -> Self:
        """Remove tags from pipeline.
        
        Args:
            tags_to_remove: Tags to remove
            
        Returns:
            Updated metadata without specified tags
        """
        tags_lower = [tag.lower() for tag in tags_to_remove]
        updated_tags = [tag for tag in self.tags if tag.lower() not in tags_lower]
        
        if len(updated_tags) == len(self.tags):
            return self  # No tags were removed
        
        return replace(
            self,
            tags=updated_tags,
            updated_at=datetime.now()
        )
    
    def add_keywords(self, new_keywords: List[str]) -> Self:
        """Add keywords to pipeline.
        
        Args:
            new_keywords: Keywords to add
            
        Returns:
            Updated metadata with new keywords
        """
        # Normalize and deduplicate keywords
        normalized_keywords = [kw.strip().lower() for kw in new_keywords if kw.strip()]
        existing_keywords = [kw.lower() for kw in self.keywords]
        
        unique_new_keywords = []
        for kw in normalized_keywords:
            if kw not in existing_keywords and kw not in unique_new_keywords:
                unique_new_keywords.append(kw)
        
        if not unique_new_keywords:
            return self
        
        updated_keywords = self.keywords + unique_new_keywords
        
        return replace(
            self,
            keywords=updated_keywords,
            updated_at=datetime.now()
        )
    
    def record_usage(
        self,
        success: bool,
        execution_time: float,
        tokens: int
    ) -> Self:
        """Record pipeline usage.
        
        Args:
            success: Whether execution was successful
            execution_time: Execution time in seconds
            tokens: Tokens used
            
        Returns:
            Updated metadata with new usage stats
        """
        updated_stats = self.usage_stats.add_run(success, execution_time, tokens)
        
        return replace(
            self,
            usage_stats=updated_stats,
            updated_at=datetime.now()
        )
    
    def update_custom_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Update custom metadata.
        
        Args:
            metadata: Metadata to merge
            
        Returns:
            Updated metadata
        """
        updated_custom = {**self.custom_metadata, **metadata}
        
        return replace(
            self,
            custom_metadata=updated_custom,
            updated_at=datetime.now()
        )
    
    @classmethod
    def create(
        cls,
        pipeline_id: PipelineId,
        name: PipelineName,
        version: str,
        category: PipelineCategory,
        complexity: PipelineComplexity,
        description: str = "",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Self:
        """Create new pipeline metadata.
        
        Args:
            pipeline_id: Pipeline identifier
            name: Pipeline name
            version: Version string
            category: Pipeline category
            complexity: Pipeline complexity
            description: Description
            author: Author name
            tags: Initial tags
            **kwargs: Additional metadata fields
            
        Returns:
            New pipeline metadata
        """
        # Generate short description from full description
        short_desc = description[:100] + "..." if len(description) > 100 else description
        
        return cls(
            pipeline_id=pipeline_id,
            name=name,
            version=version,
            category=category,
            complexity=complexity,
            description=description,
            short_description=short_desc,
            author=author,
            tags=tags or [],
            **kwargs
        )
    
    @classmethod
    def for_content_generation(
        cls,
        pipeline_id: PipelineId,
        name: PipelineName,
        version: str = "1.0.0",
        complexity: PipelineComplexity = PipelineComplexity.MODERATE,
        **kwargs
    ) -> Self:
        """Create metadata for content generation pipeline."""
        return cls.create(
            pipeline_id=pipeline_id,
            name=name,
            version=version,
            category=PipelineCategory.CONTENT_GENERATION,
            complexity=complexity,
            tags=["content", "generation", "writing"],
            **kwargs
        )
    
    @classmethod
    def for_code_generation(
        cls,
        pipeline_id: PipelineId,
        name: PipelineName,
        version: str = "1.0.0",
        complexity: PipelineComplexity = PipelineComplexity.COMPLEX,
        **kwargs
    ) -> Self:
        """Create metadata for code generation pipeline."""
        return cls.create(
            pipeline_id=pipeline_id,
            name=name,
            version=version,
            category=PipelineCategory.CODE_GENERATION,
            complexity=complexity,
            tags=["code", "generation", "programming"],
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'pipeline_id': str(self.pipeline_id),
            'name': str(self.name),
            'version': self.version,
            'category': self.category.value,
            'complexity': self.complexity.value,
            'status': self.status.value,
            'description': self.description,
            'short_description': self.short_description,
            'author': self.author,
            'organization': self.organization,
            'license': self.license,
            'repository_url': self.repository_url,
            'documentation_url': self.documentation_url,
            'tags': self.tags,
            'keywords': self.keywords,
            'requirements': self.requirements,
            'usage_stats': {
                'total_runs': self.usage_stats.total_runs,
                'successful_runs': self.usage_stats.successful_runs,
                'failed_runs': self.usage_stats.failed_runs,
                'success_rate': self.usage_stats.success_rate,
                'average_execution_time': self.usage_stats.average_execution_time,
                'total_tokens_used': self.usage_stats.total_tokens_used,
                'last_run_at': self.usage_stats.last_run_at.isoformat() if self.usage_stats.last_run_at else None
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'deprecated_at': self.deprecated_at.isoformat() if self.deprecated_at else None,
            'custom_metadata': self.custom_metadata,
            'popularity_score': self.popularity_score
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"PipelineMetadata({self.name} v{self.version})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"PipelineMetadata(id={self.pipeline_id}, name='{self.name}', "
                f"version='{self.version}', category={self.category})")
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.pipeline_id, self.version))