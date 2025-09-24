"""Mock implementation of ContentValidationService for testing."""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock

from writeit.domains.content.services.content_validation_service import (
    ContentValidationService,
    ValidationResult,
    ValidationRule,
    ValidationIssue
)
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.value_objects.content_type import ContentType


class MockContentValidationService(ContentValidationService):
    """Mock implementation of ContentValidationService.
    
    Provides configurable content validation behavior for testing
    content validation scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock validation service."""
        self._mock = Mock()
        self._validation_results: Dict[str, ValidationResult] = {}
        self._validation_rules: List[ValidationRule] = []
        self._validation_metrics: Dict[str, Dict[str, Any]] = {}
        self._should_fail = False
        
    def configure_validation_result(
        self, 
        content_id: str, 
        result: ValidationResult
    ) -> None:
        """Configure validation result for specific content."""
        self._validation_results[content_id] = result
        
    def configure_validation_rules(self, rules: List[ValidationRule]) -> None:
        """Configure validation rules to apply."""
        self._validation_rules = rules
        
    def configure_validation_metrics(
        self, 
        content_id: str, 
        metrics: Dict[str, Any]
    ) -> None:
        """Configure validation metrics for content."""
        self._validation_metrics[content_id] = metrics
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if validation should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._validation_results.clear()
        self._validation_rules.clear()
        self._validation_metrics.clear()
        self._should_fail = False
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def validate_content(
        self,
        content: GeneratedContent,
        style_primer: Optional[StylePrimer] = None
    ) -> ValidationResult:
        """Validate generated content."""
        self._mock.validate_content(content, style_primer)
        
        content_id = str(content.id.value)
        
        # Return configured result if available
        if content_id in self._validation_results:
            return self._validation_results[content_id]
            
        # Create mock validation result
        if self._should_fail:
            return ValidationResult(
                is_valid=False,
                score=0.3,
                issues=[
                    {
                        "type": "quality",
                        "severity": "error",
                        "message": "Mock validation error",
                        "location": "content"
                    }
                ],
                metrics={
                    "readability_score": 0.3,
                    "grammar_score": 0.4,
                    "style_compliance": 0.2,
                    "content_length": len(content.content or ""),
                    "word_count": len((content.content or "").split())
                }
            )
        else:
            return ValidationResult(
                is_valid=True,
                score=0.95,
                issues=[],
                metrics={
                    "readability_score": 0.95,
                    "grammar_score": 0.98,
                    "style_compliance": 0.92,
                    "content_length": len(content.content or ""),
                    "word_count": len((content.content or "").split())
                }
            )
            
    async def validate_against_style(
        self,
        content: GeneratedContent,
        style_primer: StylePrimer
    ) -> List[Dict[str, Any]]:
        """Validate content against style primer."""
        self._mock.validate_against_style(content, style_primer)
        
        if self._should_fail:
            return [
                {
                    "rule": "tone",
                    "severity": "warning",
                    "message": "Content tone doesn't match style primer",
                    "suggestion": "Use more formal language"
                }
            ]
            
        return []  # No style violations
        
    async def check_grammar_and_spelling(
        self,
        content: GeneratedContent
    ) -> List[Dict[str, Any]]:
        """Check grammar and spelling."""
        self._mock.check_grammar_and_spelling(content)
        
        if self._should_fail:
            return [
                {
                    "type": "spelling",
                    "word": "teh",
                    "suggestion": "the",
                    "position": {"line": 1, "column": 5}
                }
            ]
            
        return []  # No grammar or spelling errors
        
    async def analyze_readability(
        self,
        content: GeneratedContent
    ) -> Dict[str, Any]:
        """Analyze content readability."""
        self._mock.analyze_readability(content)
        
        content_id = str(content.id.value)
        
        # Return configured metrics if available
        if content_id in self._validation_metrics:
            return self._validation_metrics[content_id]
            
        # Create mock metrics
        content_text = content.content or ""
        return {
            "readability_score": 0.85,
            "grammar_score": 0.92,
            "style_compliance": 0.88,
            "content_length": len(content_text),
            "word_count": len(content_text.split())
        }
        
    async def validate_content_structure(
        self,
        content: GeneratedContent,
        expected_structure: Dict[str, Any]
    ) -> List[str]:
        """Validate content structure."""
        self._mock.validate_content_structure(content, expected_structure)
        
        if self._should_fail:
            return ["Missing required section: Introduction"]
            
        return []  # No structure violations
        
    async def check_content_completeness(
        self,
        content: GeneratedContent,
        requirements: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Check if content meets completeness requirements."""
        self._mock.check_content_completeness(content, requirements)
        
        # Return mock completeness check
        return {
            "has_introduction": True,
            "has_conclusion": True,
            "meets_length_requirement": not self._should_fail,
            "has_required_sections": True
        }
        
    async def validate_content_type_compliance(
        self,
        content: GeneratedContent,
        content_type: ContentType
    ) -> List[str]:
        """Validate content complies with type requirements."""
        self._mock.validate_content_type_compliance(content, content_type)
        
        if self._should_fail:
            return [f"Content doesn't comply with {content_type.value} requirements"]
            
        return []  # No compliance violations
        
    async def get_improvement_suggestions(
        self,
        content: GeneratedContent,
        validation_result: ValidationResult
    ) -> List[Dict[str, Any]]:
        """Get improvement suggestions for content."""
        self._mock.get_improvement_suggestions(content, validation_result)
        
        if not validation_result.is_valid:
            return [
                {
                    "category": "readability",
                    "suggestion": "Break up long sentences",
                    "priority": "medium"
                },
                {
                    "category": "style",
                    "suggestion": "Use more active voice",
                    "priority": "low"
                }
            ]
            
        return []  # No suggestions needed
        
    async def create_validation_report(
        self,
        content: GeneratedContent,
        validation_result: ValidationResult
    ) -> Dict[str, Any]:
        """Create comprehensive validation report."""
        self._mock.create_validation_report(content, validation_result)
        
        return {
            "content_id": str(content.id.value),
            "validation_timestamp": "2025-01-15T10:00:00Z",
            "overall_score": validation_result.score,
            "is_valid": validation_result.is_valid,
            "issues_count": len(validation_result.issues),
            "metrics": {
                "readability": validation_result.metrics.readability_score,
                "grammar": validation_result.metrics.grammar_score,
                "style_compliance": validation_result.metrics.style_compliance
            },
            "recommendations": await self.get_improvement_suggestions(content, validation_result)
        }
        
    async def batch_validate_content(
        self,
        content_list: List[GeneratedContent],
        style_primer: Optional[StylePrimer] = None
    ) -> Dict[str, ValidationResult]:
        """Validate multiple content items."""
        self._mock.batch_validate_content(content_list, style_primer)
        
        results = {}
        for content in content_list:
            results[str(content.id.value)] = await self.validate_content(content, style_primer)
            
        return results
