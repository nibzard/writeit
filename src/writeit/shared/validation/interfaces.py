"""Core validation interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')


@dataclass(frozen=True)
class ValidationResult:
    """Result of a validation operation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def success(cls, warnings: Optional[List[str]] = None, 
                metadata: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            metadata=metadata or {}
        )
    
    @classmethod
    def failure(cls, errors: List[str], warnings: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            metadata=metadata or {}
        )
    
    def combine(self, other: 'ValidationResult') -> 'ValidationResult':
        """Combine two validation results."""
        combined_metadata = {**self.metadata, **other.metadata}
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata=combined_metadata
        )


@dataclass
class ValidationContext:
    """Context for validation operations."""
    
    workspace_name: Optional[str] = None
    user_id: Optional[str] = None
    environment: str = "production"
    strict_mode: bool = False
    custom_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.custom_data is None:
            self.custom_data = {}
    
    def with_workspace(self, workspace_name: str) -> 'ValidationContext':
        """Create a new context with workspace set."""
        return ValidationContext(
            workspace_name=workspace_name,
            user_id=self.user_id,
            environment=self.environment,
            strict_mode=self.strict_mode,
            custom_data=self.custom_data.copy() if self.custom_data is not None else {}
        )
    
    def with_strict_mode(self, strict: bool = True) -> 'ValidationContext':
        """Create a new context with strict mode enabled/disabled."""
        return ValidationContext(
            workspace_name=self.workspace_name,
            user_id=self.user_id,
            environment=self.environment,
            strict_mode=strict,
            custom_data=self.custom_data.copy() if self.custom_data is not None else {}
        )


class ValidationRule(ABC, Generic[T]):
    """Abstract base class for validation rules."""
    
    @abstractmethod
    def validate(self, value: T, context: ValidationContext) -> ValidationResult:
        """Validate a value against this rule."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule validates."""
        pass
    
    @property
    def rule_name(self) -> str:
        """Name of this validation rule."""
        return self.__class__.__name__
    
    def __and__(self, other: 'ValidationRule[T]') -> 'ValidationRule[T]':
        """Combine validation rules with AND logic."""
        from .framework import CompositeValidationRule
        return CompositeValidationRule([self, other], operator="AND")
    
    def __or__(self, other: 'ValidationRule[T]') -> 'ValidationRule[T]':
        """Combine validation rules with OR logic."""
        from .framework import CompositeValidationRule
        return CompositeValidationRule([self, other], operator="OR")