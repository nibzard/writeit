"""Mock style management service for testing."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from unittest.mock import AsyncMock

from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.value_objects.style_name import StyleName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.services.style_management_service import (
    StyleManagementService,
    StyleCreationOptions,
    StyleInheritanceChain,
    StyleCompatibilityMatrix,
    StyleValidationResult,
    StyleCompatibilityLevel,
    StyleOptimizationLevel,
    StyleValidationError,
    StyleInheritanceError,
    StyleCompositionError
)
from writeit.shared.repository import EntityAlreadyExistsError, EntityNotFoundError


class MockStyleManagementService:
    """Mock implementation of StyleManagementService for testing."""
    
    def __init__(self):
        """Initialize mock service with test data."""
        self._styles: Dict[StyleName, StylePrimer] = {}
        self._validation_results: Dict[StyleName, StyleValidationResult] = {}
        self._inheritance_chains: Dict[StyleName, StyleInheritanceChain] = {}
        self._compatibility_matrices: Dict[str, StyleCompatibilityMatrix] = {}
        
        # Mock state for testing
        self._should_fail_creation = False
        self._should_fail_validation = False
        self._should_fail_inheritance_analysis = False
        self._should_fail_compatibility_analysis = False
        self._custom_validation_result: Optional[StyleValidationResult] = None
        
        # Setup default test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Setup default test data."""
        # Create sample style primers
        formal_style = StylePrimer.create(
            name=StyleName.from_user_input("formal"),
            guidelines="""
# Formal Writing Style

## Tone
- Professional and objective
- Avoid contractions and colloquialisms
- Use third person perspective

## Structure  
- Clear topic sentences
- Logical paragraph flow
- Formal conclusions

## Language
- Precise technical vocabulary
- Complete sentences
- Proper grammar and punctuation
            """.strip(),
            content_types={ContentType.documentation(), ContentType.report()},
            examples=[
                "The analysis demonstrates a significant correlation between...",
                "These findings suggest that further investigation is warranted."
            ]
        )
        
        casual_style = StylePrimer.create(
            name=StyleName.from_user_input("casual"),
            guidelines="""
# Casual Writing Style

## Tone
- Conversational and friendly
- Use contractions naturally
- Second person is fine

## Structure
- Short paragraphs
- Bullet points okay
- Conversational flow

## Language
- Simple, clear words
- Shorter sentences
- Active voice preferred
            """.strip(),
            content_types={ContentType.blog_post(), ContentType.email()},
            examples=[
                "You'll want to check this out because...",
                "Here's what we found when we looked into it:"
            ]
        )
        
        technical_style = StylePrimer.create(
            name=StyleName.from_user_input("technical"),
            guidelines="""
# Technical Writing Style

## Tone
- Clear and precise
- Factual and objective
- Instructional when appropriate

## Structure
- Step-by-step instructions
- Code examples with explanations
- Clear headings and subheadings

## Language
- Domain-specific terminology
- Consistent naming conventions
- Actionable language
            """.strip(),
            content_types={ContentType.documentation()},
            examples=[
                "Execute the following command to install dependencies:",
                "The function returns a Promise that resolves to..."
            ]
        )
        
        self._styles[formal_style.name] = formal_style
        self._styles[casual_style.name] = casual_style
        self._styles[technical_style.name] = technical_style
        
        # Create sample validation results
        formal_validation = StyleValidationResult(
            is_valid=True,
            guideline_errors=[],
            format_errors=[],
            consistency_errors=[],
            warnings=[],
            suggestions=["Consider adding more examples"],
            missing_elements=[],
            redundant_elements=[],
            performance_issues=[]
        )
        
        casual_validation = StyleValidationResult(
            is_valid=True,
            guideline_errors=[],
            format_errors=[],
            consistency_errors=[],
            warnings=["Guidelines could be more specific"],
            suggestions=["Add voice and tone examples", "Include formatting preferences"],
            missing_elements=["formatting_preferences"],
            redundant_elements=[],
            performance_issues=[]
        )
        
        self._validation_results[formal_style.name] = formal_validation
        self._validation_results[casual_style.name] = casual_validation
        
        # Create sample inheritance chain
        formal_inheritance = StyleInheritanceChain(
            style=formal_style,
            parent_styles=[],
            child_styles=[technical_style],
            inheritance_depth=0,
            conflicts=[],
            merged_guidelines=set(),
            overridden_rules=[],
            resolution_order=[formal_style.name]
        )
        
        self._inheritance_chains[formal_style.name] = formal_inheritance
        
        # Create sample compatibility matrix
        formal_casual_matrix = StyleCompatibilityMatrix(
            primary_style=formal_style,
            compared_styles=[casual_style],
            compatibility_scores={"casual": 0.3},
            compatibility_levels={"casual": StyleCompatibilityLevel.PARTIALLY_COMPATIBLE},
            conflicts={"casual": ["tone_mismatch", "formality_level"]},
            recommendations={"casual": ["Consider hybrid approach", "Define context-specific rules"]},
            merge_possibilities={"casual": False}
        )
        
        self._compatibility_matrices["formal-casual"] = formal_casual_matrix
    
    # Mock control methods for testing
    
    def set_should_fail_creation(self, should_fail: bool):
        """Control whether style creation should fail."""
        self._should_fail_creation = should_fail
    
    def set_should_fail_validation(self, should_fail: bool):
        """Control whether validation should fail."""
        self._should_fail_validation = should_fail
    
    def set_should_fail_inheritance_analysis(self, should_fail: bool):
        """Control whether inheritance analysis should fail."""
        self._should_fail_inheritance_analysis = should_fail
    
    def set_should_fail_compatibility_analysis(self, should_fail: bool):
        """Control whether compatibility analysis should fail."""
        self._should_fail_compatibility_analysis = should_fail
    
    def set_custom_validation_result(self, result: Optional[StyleValidationResult]):
        """Set custom validation result for testing."""
        self._custom_validation_result = result
    
    def add_style(self, style: StylePrimer):
        """Add style for testing."""
        self._styles[style.name] = style
    
    def get_style(self, name: StyleName) -> Optional[StylePrimer]:
        """Get style by name for testing."""
        return self._styles.get(name)
    
    def list_styles(self) -> List[StylePrimer]:
        """List all styles for testing."""
        return list(self._styles.values())
    
    # Mock implementation of StyleManagementService interface
    
    async def create_style_primer(
        self,
        name: StyleName,
        guidelines: str,
        content_types: Set[ContentType],
        options: Optional[StyleCreationOptions] = None,
        workspace_name: Optional[str] = None
    ) -> StylePrimer:
        """Create a new style primer with comprehensive initialization."""
        if self._should_fail_creation:
            raise StyleValidationError("Forced creation failure for testing")
        
        if name in self._styles:
            raise EntityAlreadyExistsError(f"Style '{name}' already exists")
        
        if options is None:
            options = StyleCreationOptions()
        
        # Generate examples if requested
        examples = []
        if options.generate_examples:
            if any("formal" in str(ct.value) for ct in content_types):
                examples = [
                    "The analysis demonstrates significant findings...",
                    "These results warrant further investigation."
                ]
            elif any("casual" in str(ct.value) for ct in content_types):
                examples = [
                    "You'll love this new feature!",
                    "Here's what we discovered:"
                ]
        
        # Create style primer
        style = StylePrimer.create(
            name=name,
            guidelines=guidelines,
            content_types=content_types,
            examples=examples
        )
        
        # Set metadata if provided
        if options.metadata:
            for key, value in options.metadata.items():
                style = style.set_metadata(key, value)
        
        # Store style
        self._styles[name] = style
        
        return style
    
    async def validate_style_primer(
        self,
        style: StylePrimer,
        workspace_name: Optional[str] = None,
        strict: bool = False
    ) -> StyleValidationResult:
        """Validate style primer comprehensively."""
        if self._should_fail_validation:
            raise StyleValidationError("Forced validation failure for testing")
        
        # Return custom result if set
        if self._custom_validation_result:
            return self._custom_validation_result
        
        # Return existing result if available
        if style.name in self._validation_results:
            return self._validation_results[style.name]
        
        # Create basic validation result for new styles
        result = StyleValidationResult(
            is_valid=True,
            guideline_errors=[],
            format_errors=[],
            consistency_errors=[],
            warnings=[],
            suggestions=[],
            missing_elements=[],
            redundant_elements=[],
            performance_issues=[]
        )
        
        # Basic validation checks
        if not style.guidelines.strip():
            result.guideline_errors.append("Guidelines cannot be empty")
            result.is_valid = False
        
        if len(style.guidelines) < 50:
            result.warnings.append("Guidelines are very brief")
        
        if not style.content_types:
            result.missing_elements.append("content_types")
            result.suggestions.append("Specify compatible content types")
        
        if not style.examples:
            result.missing_elements.append("examples")
            result.suggestions.append("Add usage examples")
        
        # Check for common guideline elements
        guidelines_lower = style.guidelines.lower()
        if "tone" not in guidelines_lower:
            result.missing_elements.append("tone_guidelines")
        
        if "structure" not in guidelines_lower:
            result.missing_elements.append("structure_guidelines")
        
        if "language" not in guidelines_lower:
            result.missing_elements.append("language_guidelines")
        
        # Store result
        self._validation_results[style.name] = result
        
        return result
    
    async def analyze_style_inheritance(
        self,
        style: StylePrimer,
        workspace_name: Optional[str] = None
    ) -> StyleInheritanceChain:
        """Analyze style inheritance chain."""
        if self._should_fail_inheritance_analysis:
            raise StyleInheritanceError("Forced inheritance analysis failure for testing")
        
        # Return existing chain if available
        if style.name in self._inheritance_chains:
            return self._inheritance_chains[style.name]
        
        # Create basic inheritance chain
        chain = StyleInheritanceChain(
            style=style,
            parent_styles=[],
            child_styles=[],
            inheritance_depth=0,
            conflicts=[],
            merged_guidelines=set(),
            overridden_rules=[],
            resolution_order=[style.name]
        )
        
        # Simple inheritance detection based on name patterns
        style_name_str = str(style.name).lower()
        
        # Find potential parents
        for other_style in self._styles.values():
            other_name_str = str(other_style.name).lower()
            
            # Simple heuristic: if current style contains other style name, it might inherit
            if other_name_str in style_name_str and other_style.name != style.name:
                chain.parent_styles.append(other_style)
                chain.inheritance_depth += 1
        
        # Find potential children
        for other_style in self._styles.values():
            other_name_str = str(other_style.name).lower()
            
            # Simple heuristic: if other style contains current style name, it might inherit
            if style_name_str in other_name_str and other_style.name != style.name:
                chain.child_styles.append(other_style)
        
        self._inheritance_chains[style.name] = chain
        return chain
    
    async def analyze_style_compatibility(
        self,
        primary_style: StylePrimer,
        compared_styles: List[StylePrimer],
        workspace_name: Optional[str] = None
    ) -> StyleCompatibilityMatrix:
        """Analyze compatibility between styles."""
        if self._should_fail_compatibility_analysis:
            raise StyleValidationError("Forced compatibility analysis failure for testing")
        
        # Create compatibility matrix key
        style_names = [str(primary_style.name)] + [str(s.name) for s in compared_styles]
        matrix_key = "-".join(sorted(style_names))
        
        # Return existing matrix if available
        if matrix_key in self._compatibility_matrices:
            return self._compatibility_matrices[matrix_key]
        
        # Calculate compatibility scores and levels
        compatibility_scores = {}
        compatibility_levels = {}
        conflicts = {}
        recommendations = {}
        merge_possibilities = {}
        
        for compared_style in compared_styles:
            style_name = str(compared_style.name)
            
            # Simple compatibility scoring based on content types overlap
            primary_types = primary_style.content_types
            compared_types = compared_style.content_types
            
            if primary_types and compared_types:
                overlap = len(primary_types & compared_types)
                total = len(primary_types | compared_types)
                score = overlap / total if total > 0 else 0.0
            else:
                score = 0.5  # Neutral if no content types specified
            
            compatibility_scores[style_name] = score
            
            # Determine compatibility level
            if score >= 0.8:
                compatibility_levels[style_name] = StyleCompatibilityLevel.FULLY_COMPATIBLE
                conflicts[style_name] = []
                recommendations[style_name] = ["Styles are highly compatible"]
                merge_possibilities[style_name] = True
            elif score >= 0.6:
                compatibility_levels[style_name] = StyleCompatibilityLevel.MOSTLY_COMPATIBLE
                conflicts[style_name] = ["Minor formatting differences"]
                recommendations[style_name] = ["Consider minor adjustments"]
                merge_possibilities[style_name] = True
            elif score >= 0.3:
                compatibility_levels[style_name] = StyleCompatibilityLevel.PARTIALLY_COMPATIBLE
                conflicts[style_name] = ["Tone differences", "Structure conflicts"]
                recommendations[style_name] = ["Define context-specific rules", "Create hybrid approach"]
                merge_possibilities[style_name] = False
            else:
                compatibility_levels[style_name] = StyleCompatibilityLevel.INCOMPATIBLE
                conflicts[style_name] = ["Fundamental approach differences", "Conflicting guidelines"]
                recommendations[style_name] = ["Use styles for different contexts", "Consider complete redesign"]
                merge_possibilities[style_name] = False
        
        matrix = StyleCompatibilityMatrix(
            primary_style=primary_style,
            compared_styles=compared_styles,
            compatibility_scores=compatibility_scores,
            compatibility_levels=compatibility_levels,
            conflicts=conflicts,
            recommendations=recommendations,
            merge_possibilities=merge_possibilities
        )
        
        self._compatibility_matrices[matrix_key] = matrix
        return matrix
    
    async def merge_style_primers(
        self,
        styles: List[StylePrimer],
        merge_strategy: str = "weighted",
        workspace_name: Optional[str] = None
    ) -> StylePrimer:
        """Merge multiple style primers into one."""
        if not styles:
            raise StyleValidationError("No styles provided for merging")
        
        if len(styles) == 1:
            return styles[0]
        
        # Create merged name
        style_names = [str(s.name) for s in styles]
        merged_name = StyleName.from_user_input(f"merged-{'-'.join(style_names[:2])}")
        
        # Merge guidelines
        merged_guidelines = f"# Merged Style: {merged_name}\n\n"
        for i, style in enumerate(styles):
            merged_guidelines += f"## From {style.name}\n{style.guidelines}\n\n"
        
        # Merge content types
        merged_content_types = set()
        for style in styles:
            merged_content_types.update(style.content_types)
        
        # Merge examples
        merged_examples = []
        for style in styles:
            merged_examples.extend(style.examples[:2])  # Limit examples per style
        
        merged_style = StylePrimer.create(
            name=merged_name,
            guidelines=merged_guidelines,
            content_types=merged_content_types,
            examples=merged_examples
        )
        
        # Set merge metadata
        merged_style = merged_style.set_metadata("merged_from", style_names)
        merged_style = merged_style.set_metadata("merge_strategy", merge_strategy)
        merged_style = merged_style.set_metadata("merged_at", datetime.now().isoformat())
        
        return merged_style
    
    async def optimize_style_primer(
        self,
        style: StylePrimer,
        optimization_level: StyleOptimizationLevel = StyleOptimizationLevel.STANDARD,
        workspace_name: Optional[str] = None
    ) -> StylePrimer:
        """Optimize style primer for better performance and clarity."""
        # Create optimized version
        optimized_style = style
        
        # Apply optimizations based on level
        if optimization_level in [StyleOptimizationLevel.STANDARD, StyleOptimizationLevel.AGGRESSIVE]:
            # Optimize guidelines formatting
            guidelines = optimized_style.guidelines
            
            # Ensure consistent markdown formatting
            lines = guidelines.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip().startswith('#'):
                    # Ensure space after hash
                    formatted_lines.append(line.strip())
                else:
                    formatted_lines.append(line)
            
            optimized_guidelines = '\n'.join(formatted_lines)
            optimized_style = optimized_style.update_guidelines(optimized_guidelines)
        
        if optimization_level == StyleOptimizationLevel.AGGRESSIVE:
            # Remove redundant examples
            unique_examples = list(set(optimized_style.examples))
            optimized_style = StylePrimer.create(
                name=optimized_style.name,
                guidelines=optimized_style.guidelines,
                content_types=optimized_style.content_types,
                examples=unique_examples[:5]  # Limit to 5 examples
            )
        
        # Set optimization metadata
        optimized_style = optimized_style.set_metadata(
            "optimization_level", optimization_level.value
        )
        optimized_style = optimized_style.set_metadata(
            "optimized_at", datetime.now().isoformat()
        )
        
        return optimized_style
    
    async def get_style_usage_statistics(
        self,
        style: StylePrimer,
        workspace_name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for a style primer."""
        # Return mock statistics
        return {
            "total_uses": 45,
            "unique_templates": 8,
            "success_rate": 0.92,
            "average_quality_score": 0.85,
            "most_common_content_types": ["blog_post", "documentation"],
            "performance_metrics": {
                "average_generation_time": 18.5,
                "cache_hit_rate": 0.73
            },
            "user_feedback": {
                "average_rating": 4.3,
                "common_feedback": ["Clear guidelines", "Good examples"]
            }
        }
    
    # Additional helper methods for testing
    
    def clear_all_styles(self):
        """Clear all styles for testing."""
        self._styles.clear()
        self._validation_results.clear()
        self._inheritance_chains.clear()
        self._compatibility_matrices.clear()
    
    def get_validation_result(self, name: StyleName) -> Optional[StyleValidationResult]:
        """Get validation result for testing."""
        return self._validation_results.get(name)
    
    def get_inheritance_chain(self, name: StyleName) -> Optional[StyleInheritanceChain]:
        """Get inheritance chain for testing."""
        return self._inheritance_chains.get(name)
    
    def get_compatibility_matrix(self, matrix_key: str) -> Optional[StyleCompatibilityMatrix]:
        """Get compatibility matrix for testing."""
        return self._compatibility_matrices.get(matrix_key)
    
    def reset_mock_state(self):
        """Reset mock state for testing."""
        self._should_fail_creation = False
        self._should_fail_validation = False
        self._should_fail_inheritance_analysis = False
        self._should_fail_compatibility_analysis = False
        self._custom_validation_result = None
        self.clear_all_styles()
        self._setup_test_data()