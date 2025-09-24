"""Mock content generation service for testing."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from unittest.mock import AsyncMock
import hashlib

from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.entities.template import Template
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.content_length import ContentLength
from writeit.domains.content.value_objects.validation_rule import ValidationRule
from writeit.shared.repository import EntityAlreadyExistsError, EntityNotFoundError


# Mock enums and classes for ContentGenerationService
class QualityAssessmentLevel(str, Enum):
    """Quality assessment levels."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    EXPERT = "expert"


class ContentOptimizationLevel(str, Enum):
    """Content optimization levels."""
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


@dataclass
class ContentQualityMetrics:
    """Content quality assessment metrics."""
    overall_score: float
    readability_score: float
    coherence_score: float
    relevance_score: float
    style_consistency_score: float
    grammar_score: float
    structure_score: float
    engagement_score: float
    technical_accuracy_score: float
    completeness_score: float
    
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class ContentAnalysis:
    """Comprehensive content analysis."""
    content: GeneratedContent
    word_count: int
    sentence_count: int
    paragraph_count: int
    reading_level: str
    key_topics: List[str]
    sentiment_score: float
    structure_analysis: Dict[str, Any]
    style_adherence: float
    template_compliance: float
    validation_results: List[str]


@dataclass
class ContentVersionComparison:
    """Comparison between content versions."""
    original_content: GeneratedContent
    new_content: GeneratedContent
    changes: List[str]
    improvements: List[str]
    quality_delta: float
    recommendation: str


class MockContentGenerationService:
    """Mock implementation of ContentGenerationService for testing."""
    
    def __init__(self):
        """Initialize mock service with test data."""
        self._generated_content: Dict[ContentId, GeneratedContent] = {}
        self._quality_metrics: Dict[ContentId, ContentQualityMetrics] = {}
        self._content_analysis: Dict[ContentId, ContentAnalysis] = {}
        self._usage_statistics: Dict[str, Dict[str, Any]] = {}
        
        # Mock state for testing
        self._should_fail_creation = False
        self._should_fail_validation = False
        self._should_fail_quality_assessment = False
        self._should_fail_optimization = False
        self._custom_quality_score = None
        self._custom_validation_result = None
        
        # Setup default test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Setup default test data."""
        # Create sample generated content
        blog_content = GeneratedContent.create(
            content_type=ContentType.blog_post(),
            content_format=ContentFormat.markdown(),
            raw_content="""# The Future of AI in Content Creation

Artificial intelligence is revolutionizing how we create and consume content. From automated writing to personalized recommendations, AI is transforming the landscape.

## Key Benefits

- **Efficiency**: AI can generate content at scale
- **Consistency**: Maintains brand voice across all content
- **Personalization**: Tailors content to individual audiences

## Challenges

While AI offers many benefits, we must also consider:

1. Quality control and fact-checking
2. Maintaining human creativity and insight
3. Ethical considerations in automated content

## Conclusion

The future of content creation lies in the collaboration between human creativity and AI efficiency. By leveraging the strengths of both, we can create more engaging and valuable content for our audiences.
""",
            metadata={
                "template_name": "blog-post",
                "word_count": 145,
                "generation_time": 25.3,
                "model_used": "gpt-4o-mini"
            }
        )
        
        doc_content = GeneratedContent.create(
            content_type=ContentType.documentation(),
            content_format=ContentFormat.markdown(),
            raw_content="""# API Authentication Guide

This guide covers authentication methods for the API.

## Overview

The API supports multiple authentication methods to ensure secure access to resources.

## Methods

### API Keys

```python
headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}
```

### OAuth 2.0

1. Obtain client credentials
2. Request access token
3. Include token in requests

## Best Practices

- Store keys securely
- Rotate keys regularly
- Use HTTPS only
- Monitor access logs

## Troubleshooting

Common issues and solutions:

- **401 Unauthorized**: Check API key format
- **403 Forbidden**: Verify permissions
- **429 Rate Limited**: Implement backoff
""",
            metadata={
                "template_name": "documentation",
                "word_count": 89,
                "generation_time": 18.7,
                "model_used": "gpt-4o-mini"
            }
        )
        
        self._generated_content[blog_content.id] = blog_content
        self._generated_content[doc_content.id] = doc_content
        
        # Create sample quality metrics
        blog_quality = ContentQualityMetrics(
            overall_score=0.85,
            readability_score=0.88,
            coherence_score=0.82,
            relevance_score=0.90,
            style_consistency_score=0.87,
            grammar_score=0.95,
            structure_score=0.80,
            engagement_score=0.78,
            technical_accuracy_score=0.85,
            completeness_score=0.83,
            issues=["Could use more specific examples"],
            suggestions=["Add more data to support claims", "Include call-to-action"],
            strengths=["Clear structure", "Good use of headings", "Engaging introduction"]
        )
        
        doc_quality = ContentQualityMetrics(
            overall_score=0.92,
            readability_score=0.90,
            coherence_score=0.95,
            relevance_score=0.95,
            style_consistency_score=0.88,
            grammar_score=0.98,
            structure_score=0.93,
            engagement_score=0.75,
            technical_accuracy_score=0.95,
            completeness_score=0.90,
            issues=[],
            suggestions=["Add more troubleshooting examples"],
            strengths=["Excellent technical accuracy", "Clear code examples", "Well-organized"]
        )
        
        self._quality_metrics[blog_content.id] = blog_quality
        self._quality_metrics[doc_content.id] = doc_quality
        
        # Create sample content analysis
        blog_analysis = ContentAnalysis(
            content=blog_content,
            word_count=145,
            sentence_count=12,
            paragraph_count=6,
            reading_level="Grade 8",
            key_topics=["AI", "content creation", "automation", "benefits", "challenges"],
            sentiment_score=0.72,
            structure_analysis={
                "has_introduction": True,
                "has_conclusion": True,
                "heading_levels": [1, 2],
                "list_count": 2,
                "code_blocks": 0
            },
            style_adherence=0.87,
            template_compliance=0.95,
            validation_results=["Word count within range", "Proper heading structure"]
        )
        
        self._content_analysis[blog_content.id] = blog_analysis
    
    # Mock control methods for testing
    
    def set_should_fail_creation(self, should_fail: bool):
        """Control whether content creation should fail."""
        self._should_fail_creation = should_fail
    
    def set_should_fail_validation(self, should_fail: bool):
        """Control whether validation should fail."""
        self._should_fail_validation = should_fail
    
    def set_should_fail_quality_assessment(self, should_fail: bool):
        """Control whether quality assessment should fail."""
        self._should_fail_quality_assessment = should_fail
    
    def set_should_fail_optimization(self, should_fail: bool):
        """Control whether optimization should fail."""
        self._should_fail_optimization = should_fail
    
    def set_custom_quality_score(self, score: Optional[float]):
        """Set custom quality score for testing."""
        self._custom_quality_score = score
    
    def set_custom_validation_result(self, result: Optional[List[str]]):
        """Set custom validation result for testing."""
        self._custom_validation_result = result
    
    def add_generated_content(self, content: GeneratedContent):
        """Add generated content for testing."""
        self._generated_content[content.id] = content
    
    def get_generated_content(self, content_id: ContentId) -> Optional[GeneratedContent]:
        """Get generated content by ID for testing."""
        return self._generated_content.get(content_id)
    
    def list_generated_content(self) -> List[GeneratedContent]:
        """List all generated content for testing."""
        return list(self._generated_content.values())
    
    # Mock implementation of ContentGenerationService interface
    
    async def create_generated_content(
        self,
        content_type: ContentType,
        content_format: ContentFormat,
        raw_content: str,
        template: Optional[Template] = None,
        style_primer: Optional[StylePrimer] = None,
        metadata: Optional[Dict[str, Any]] = None,
        workspace_name: Optional[str] = None
    ) -> GeneratedContent:
        """Create new generated content with validation and processing."""
        if self._should_fail_creation:
            raise Exception("Forced creation failure for testing")
        
        # Create generated content
        generated_content = GeneratedContent.create(
            content_type=content_type,
            content_format=content_format,
            raw_content=raw_content,
            metadata=metadata or {}
        )
        
        # Add template and style information to metadata
        if template:
            generated_content = generated_content.set_metadata("template_name", str(template.name))
            generated_content = generated_content.set_metadata("template_version", template.version)
        
        if style_primer:
            generated_content = generated_content.set_metadata("style_name", str(style_primer.name))
        
        # Add generation metadata
        generated_content = generated_content.set_metadata("generated_at", datetime.now().isoformat())
        generated_content = generated_content.set_metadata("word_count", len(raw_content.split()))
        
        # Store content
        self._generated_content[generated_content.id] = generated_content
        
        return generated_content
    
    async def validate_generated_content(
        self,
        content: GeneratedContent,
        validation_rules: List[ValidationRule],
        workspace_name: Optional[str] = None
    ) -> List[str]:
        """Validate generated content against rules."""
        if self._should_fail_validation:
            raise Exception("Forced validation failure for testing")
        
        # Return custom result if set
        if self._custom_validation_result is not None:
            return self._custom_validation_result
        
        validation_results = []
        
        # Basic validations
        word_count = len(content.raw_content.split())
        
        # Check word count rules
        for rule in validation_rules:
            if hasattr(rule, 'min_words') and hasattr(rule, 'max_words'):
                if word_count < rule.min_words:
                    validation_results.append(f"Content too short: {word_count} words (min: {rule.min_words})")
                elif word_count > rule.max_words:
                    validation_results.append(f"Content too long: {word_count} words (max: {rule.max_words})")
            
            # Check readability rules
            if hasattr(rule, 'min_score') and 'readability' in str(rule).lower():
                # Mock readability check
                if len(content.raw_content.split('.')) < 5:
                    validation_results.append("Content may not meet readability requirements")
        
        # Check format-specific rules
        if content.content_format == ContentFormat.markdown():
            if not content.raw_content.startswith('#'):
                validation_results.append("Markdown content should start with a heading")
        
        # If no issues found, add success message
        if not validation_results:
            validation_results = ["Content passes all validation rules"]
        
        return validation_results
    
    async def assess_content_quality(
        self,
        content: GeneratedContent,
        assessment_level: QualityAssessmentLevel = QualityAssessmentLevel.STANDARD,
        workspace_name: Optional[str] = None
    ) -> ContentQualityMetrics:
        """Assess the quality of generated content."""
        if self._should_fail_quality_assessment:
            raise Exception("Forced quality assessment failure for testing")
        
        # Return existing metrics if available
        if content.id in self._quality_metrics:
            metrics = self._quality_metrics[content.id]
            
            # Apply custom quality score if set
            if self._custom_quality_score is not None:
                metrics.overall_score = self._custom_quality_score
            
            return metrics
        
        # Create new quality metrics
        word_count = len(content.raw_content.split())
        sentence_count = len(content.raw_content.split('.'))
        
        # Base scores with some variation
        base_score = 0.75
        if word_count > 100:
            base_score += 0.1
        if sentence_count > 5:
            base_score += 0.05
        if content.content_format == ContentFormat.markdown() and '#' in content.raw_content:
            base_score += 0.05
        
        # Apply custom score if set
        overall_score = self._custom_quality_score or min(base_score, 1.0)
        
        metrics = ContentQualityMetrics(
            overall_score=overall_score,
            readability_score=min(base_score + 0.1, 1.0),
            coherence_score=min(base_score + 0.05, 1.0),
            relevance_score=min(base_score + 0.15, 1.0),
            style_consistency_score=base_score,
            grammar_score=min(base_score + 0.2, 1.0),
            structure_score=min(base_score + 0.05, 1.0),
            engagement_score=max(base_score - 0.1, 0.0),
            technical_accuracy_score=base_score,
            completeness_score=min(base_score + 0.08, 1.0),
            issues=[],
            suggestions=[],
            strengths=[]
        )
        
        # Add assessment-level specific analysis
        if assessment_level in [QualityAssessmentLevel.STANDARD, QualityAssessmentLevel.COMPREHENSIVE, QualityAssessmentLevel.EXPERT]:
            if word_count < 50:
                metrics.issues.append("Content is very brief")
                metrics.suggestions.append("Consider expanding the content")
            
            if overall_score > 0.8:
                metrics.strengths.append("High overall quality")
            
            if sentence_count < 3:
                metrics.issues.append("Very few sentences")
                metrics.suggestions.append("Add more detailed explanations")
        
        if assessment_level in [QualityAssessmentLevel.COMPREHENSIVE, QualityAssessmentLevel.EXPERT]:
            # More detailed analysis
            if content.content_type == ContentType.blog_post():
                if "conclusion" not in content.raw_content.lower():
                    metrics.suggestions.append("Consider adding a conclusion section")
            
            elif content.content_type == ContentType.documentation():
                if "example" not in content.raw_content.lower():
                    metrics.suggestions.append("Add practical examples")
        
        if assessment_level == QualityAssessmentLevel.EXPERT:
            # Expert-level analysis
            metrics.suggestions.append("Consider A/B testing different versions")
            metrics.strengths.append("Content structure follows best practices")
        
        # Store metrics
        self._quality_metrics[content.id] = metrics
        
        return metrics
    
    async def optimize_generated_content(
        self,
        content: GeneratedContent,
        optimization_level: ContentOptimizationLevel = ContentOptimizationLevel.STANDARD,
        target_metrics: Optional[Dict[str, float]] = None,
        workspace_name: Optional[str] = None
    ) -> GeneratedContent:
        """Optimize generated content for better quality and performance."""
        if self._should_fail_optimization:
            raise Exception("Forced optimization failure for testing")
        
        optimized_content = content.raw_content
        
        # Apply optimizations based on level
        if optimization_level in [ContentOptimizationLevel.STANDARD, ContentOptimizationLevel.AGGRESSIVE]:
            # Basic optimizations
            
            # Remove extra whitespace
            lines = optimized_content.split('\n')
            cleaned_lines = []
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line or (cleaned_lines and cleaned_lines[-1]):  # Preserve single empty lines
                    cleaned_lines.append(cleaned_line)
            
            optimized_content = '\n'.join(cleaned_lines)
            
            # Ensure proper heading hierarchy for markdown
            if content.content_format == ContentFormat.markdown():
                if not optimized_content.startswith('#'):
                    # Add main heading if missing
                    first_line = optimized_content.split('\n')[0]
                    if len(first_line) > 0:
                        optimized_content = f"# {first_line}\n\n" + '\n'.join(optimized_content.split('\n')[1:])
        
        if optimization_level == ContentOptimizationLevel.AGGRESSIVE:
            # More aggressive optimizations
            
            # Ensure minimum word count
            word_count = len(optimized_content.split())
            if word_count < 100:
                optimized_content += "\n\nThis content has been automatically expanded to meet minimum length requirements."
        
        # Create optimized version
        optimized = GeneratedContent.create(
            content_type=content.content_type,
            content_format=content.content_format,
            raw_content=optimized_content,
            metadata=content.metadata.copy()
        )
        
        # Add optimization metadata
        optimized = optimized.set_metadata("optimization_level", optimization_level.value)
        optimized = optimized.set_metadata("optimized_at", datetime.now().isoformat())
        optimized = optimized.set_metadata("original_content_id", str(content.id))
        
        # Store optimized content
        self._generated_content[optimized.id] = optimized
        
        return optimized
    
    async def analyze_content_comprehensive(
        self,
        content: GeneratedContent,
        workspace_name: Optional[str] = None
    ) -> ContentAnalysis:
        """Perform comprehensive content analysis."""
        # Return existing analysis if available
        if content.id in self._content_analysis:
            return self._content_analysis[content.id]
        
        # Create comprehensive analysis
        raw_content = content.raw_content
        words = raw_content.split()
        sentences = raw_content.split('.')
        paragraphs = [p.strip() for p in raw_content.split('\n\n') if p.strip()]
        
        # Extract key topics (simple keyword extraction)
        key_topics = []
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        word_freq = {}
        for word in words:
            cleaned_word = re.sub(r'[^\w]', '', word.lower())
            if cleaned_word and cleaned_word not in common_words and len(cleaned_word) > 3:
                word_freq[cleaned_word] = word_freq.get(cleaned_word, 0) + 1
        
        # Get top keywords as key topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        key_topics = [word for word, freq in sorted_words[:5]]
        
        # Analyze structure
        structure_analysis = {
            "has_introduction": len(paragraphs) > 0,
            "has_conclusion": "conclusion" in raw_content.lower() or len(paragraphs) > 2,
            "heading_levels": [],
            "list_count": raw_content.count('-') + raw_content.count('*') + raw_content.count('1.'),
            "code_blocks": raw_content.count('```')
        }
        
        # Find heading levels for markdown
        if content.content_format == ContentFormat.markdown():
            for line in raw_content.split('\n'):
                if line.strip().startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    if level not in structure_analysis["heading_levels"]:
                        structure_analysis["heading_levels"].append(level)
        
        # Mock sentiment analysis (0 = negative, 0.5 = neutral, 1 = positive)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'perfect', 'outstanding']
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'horrible', 'disappointing', 'poor']
        
        positive_count = sum(1 for word in words if word.lower() in positive_words)
        negative_count = sum(1 for word in words if word.lower() in negative_words)
        total_emotional_words = positive_count + negative_count
        
        if total_emotional_words > 0:
            sentiment_score = positive_count / total_emotional_words
        else:
            sentiment_score = 0.5  # Neutral
        
        # Determine reading level (simplified)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        if avg_sentence_length < 10:
            reading_level = "Grade 6-8"
        elif avg_sentence_length < 15:
            reading_level = "Grade 9-12"
        else:
            reading_level = "College"
        
        analysis = ContentAnalysis(
            content=content,
            word_count=len(words),
            sentence_count=len(sentences),
            paragraph_count=len(paragraphs),
            reading_level=reading_level,
            key_topics=key_topics,
            sentiment_score=sentiment_score,
            structure_analysis=structure_analysis,
            style_adherence=0.8,  # Mock score
            template_compliance=0.85,  # Mock score
            validation_results=["Basic structure analysis complete"]
        )
        
        # Store analysis
        self._content_analysis[content.id] = analysis
        
        return analysis
    
    async def compare_content_versions(
        self,
        original_content: GeneratedContent,
        new_content: GeneratedContent
    ) -> ContentVersionComparison:
        """Compare two versions of content."""
        changes = []
        improvements = []
        
        # Compare basic metrics
        original_words = len(original_content.raw_content.split())
        new_words = len(new_content.raw_content.split())
        
        if new_words != original_words:
            changes.append(f"Word count changed from {original_words} to {new_words}")
            
            if new_words > original_words:
                improvements.append("Content expanded with additional detail")
            elif new_words < original_words:
                improvements.append("Content made more concise")
        
        # Compare content structure
        original_lines = original_content.raw_content.split('\n')
        new_lines = new_content.raw_content.split('\n')
        
        if len(new_lines) != len(original_lines):
            changes.append(f"Structure changed: {len(original_lines)} → {len(new_lines)} lines")
        
        # Get quality metrics for comparison
        try:
            original_quality = await self.assess_content_quality(original_content)
            new_quality = await self.assess_content_quality(new_content)
            quality_delta = new_quality.overall_score - original_quality.overall_score
        except:
            quality_delta = 0.0
        
        # Determine recommendation
        if quality_delta > 0.1:
            recommendation = "Significant improvement - recommend using new version"
        elif quality_delta > 0.02:
            recommendation = "Minor improvement - new version is slightly better"
        elif quality_delta < -0.1:
            recommendation = "Quality decreased - consider keeping original version"
        elif quality_delta < -0.02:
            recommendation = "Slight quality decrease - review changes carefully"
        else:
            recommendation = "Similar quality - choose based on specific requirements"
        
        if quality_delta > 0:
            improvements.append(f"Overall quality improved by {quality_delta:.2f}")
        
        return ContentVersionComparison(
            original_content=original_content,
            new_content=new_content,
            changes=changes or ["No significant changes detected"],
            improvements=improvements or ["No clear improvements identified"],
            quality_delta=quality_delta,
            recommendation=recommendation
        )
    
    async def get_content_usage_statistics(
        self,
        workspace_name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        content_type: Optional[ContentType] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for generated content."""
        # Return mock statistics
        stats = {
            "total_content_generated": len(self._generated_content),
            "content_by_type": {
                "blog_post": 15,
                "documentation": 8,
                "email": 5,
                "report": 3
            },
            "content_by_format": {
                "markdown": 20,
                "html": 8,
                "text": 3
            },
            "average_quality_score": 0.83,
            "average_word_count": 156,
            "most_common_topics": ["AI", "content", "documentation", "automation"],
            "quality_distribution": {
                "excellent": 12,
                "good": 15,
                "fair": 4,
                "poor": 0
            },
            "optimization_requests": 8,
            "validation_failures": 2,
            "generation_time_stats": {
                "average_seconds": 22.5,
                "median_seconds": 18.7,
                "fastest_seconds": 12.1,
                "slowest_seconds": 45.3
            }
        }
        
        # Filter by content type if specified
        if content_type:
            content_type_str = content_type.value
            stats["filtered_by_type"] = content_type_str
            stats["type_specific_count"] = stats["content_by_type"].get(content_type_str, 0)
        
        return stats
    
    # Additional helper methods for testing
    
    def clear_all_content(self):
        """Clear all generated content for testing."""
        self._generated_content.clear()
        self._quality_metrics.clear()
        self._content_analysis.clear()
        self._usage_statistics.clear()
    
    def get_quality_metrics(self, content_id: ContentId) -> Optional[ContentQualityMetrics]:
        """Get quality metrics for testing."""
        return self._quality_metrics.get(content_id)
    
    def get_content_analysis(self, content_id: ContentId) -> Optional[ContentAnalysis]:
        """Get content analysis for testing."""
        return self._content_analysis.get(content_id)
    
    def set_usage_statistics(self, stats: Dict[str, Any]):
        """Set usage statistics for testing."""
        self._usage_statistics = stats.copy()
    
    def reset_mock_state(self):
        """Reset mock state for testing."""
        self._should_fail_creation = False
        self._should_fail_validation = False
        self._should_fail_quality_assessment = False
        self._should_fail_optimization = False
        self._custom_quality_score = None
        self._custom_validation_result = None
        self.clear_all_content()
        self._setup_test_data()