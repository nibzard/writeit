"""Model preference value object.

Provides LLM model selection with fallback logic and validation.
"""

from dataclasses import dataclass
from typing import List, Optional, Self, Any, cast
from enum import Enum


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


class ModelCapability(str, Enum):
    """Model capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CONVERSATION = "conversation"
    LONG_CONTEXT = "long_context"


@dataclass(frozen=True)
class ModelPreference:
    """LLM model selection criteria with fallback logic.
    
    Defines preferred models in priority order with validation
    and fallback behavior.
    
    Examples:
        ModelPreference(["gpt-4o-mini", "claude-3-sonnet"])
        ModelPreference(["gpt-4o"], fallback_to_default=True)
    """
    
    models: List[str]
    fallback_to_default: bool = True
    required_capabilities: Optional[List[ModelCapability]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Validate model preference configuration."""
        if not self.models:
            raise ValueError("Model preference must include at least one model")
            
        if not isinstance(self.models, list):
            raise TypeError("Models must be a list")
            
        # Validate model names
        for model in self.models:
            if not isinstance(model, str):
                raise TypeError(f"Model name must be string, got {type(model)}")
            if not model.strip():
                raise ValueError("Model name cannot be empty")
                
        # Validate temperature
        if self.temperature is not None:
            if not 0.0 <= self.temperature <= 2.0:
                raise ValueError("Temperature must be between 0.0 and 2.0")
                
        # Validate max_tokens
        if self.max_tokens is not None:
            if self.max_tokens <= 0:
                raise ValueError("Max tokens must be positive")
            if self.max_tokens > 1000000:
                raise ValueError("Max tokens too large (limit: 1,000,000)")
                
        # Set default capabilities if not provided
        if self.required_capabilities is None:
            object.__setattr__(self, 'required_capabilities', [ModelCapability.TEXT_GENERATION])
    
    @property
    def primary_model(self) -> str:
        """Get the primary (first choice) model."""
        return self.models[0]
    
    @property
    def has_fallbacks(self) -> bool:
        """Check if fallback models are configured."""
        return len(self.models) > 1 or self.fallback_to_default
    
    def get_model_for_provider(self, provider: ModelProvider) -> Optional[str]:
        """Get the preferred model for a specific provider."""
        # Simple provider mapping based on common model names
        provider_patterns = {
            ModelProvider.OPENAI: ["gpt-", "text-", "davinci", "curie", "babbage", "ada"],
            ModelProvider.ANTHROPIC: ["claude-", "anthropic"],
            ModelProvider.LOCAL: ["local-", "ollama-", "llamacpp-"],
            ModelProvider.MOCK: ["mock-", "test-"]
        }
        
        patterns = provider_patterns.get(provider, [])
        
        for model in self.models:
            model_lower = model.lower()
            if any(pattern in model_lower for pattern in patterns):
                return model
                
        return None
    
    def create_with_fallback(self, additional_models: List[str]) -> Self:
        """Create new preference with additional fallback models."""
        combined_models = self.models + additional_models
        return cast(Self, ModelPreference(
            models=combined_models,
            fallback_to_default=self.fallback_to_default,
            required_capabilities=self.required_capabilities,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        ))
    
    @classmethod
    def single(cls, model: str, **kwargs: Any) -> Self:
        """Create preference for a single model."""
        return cls(models=[model], **kwargs)
    
    @classmethod
    def openai_gpt4(cls, **kwargs: Any) -> Self:
        """Create preference for OpenAI GPT-4 models."""
        return cls(
            models=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            **kwargs
        )
    
    @classmethod
    def anthropic_claude(cls, **kwargs: Any) -> Self:
        """Create preference for Anthropic Claude models."""
        return cls(
            models=["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229"],
            **kwargs
        )
    
    @classmethod
    def fast_models(cls, **kwargs: Any) -> Self:
        """Create preference optimized for speed."""
        return cls(
            models=["gpt-4o-mini", "claude-3-haiku-20240307"],
            **kwargs
        )
    
    @classmethod
    def powerful_models(cls, **kwargs: Any) -> Self:
        """Create preference optimized for capability."""
        return cls(
            models=["gpt-4o", "claude-3-5-sonnet-20241022"],
            **kwargs
        )
    
    @classmethod
    def default(cls, **kwargs: Any) -> Self:
        """Create default model preference."""
        return cls(
            models=["gpt-4o-mini"],
            **kwargs
        )
    
    def __str__(self) -> str:
        """String representation."""
        if len(self.models) == 1:
            return self.models[0]
        return f"{self.models[0]} (+{len(self.models)-1} fallbacks)"
    
    def __contains__(self, model: str) -> bool:
        """Check if model is in preference list."""
        return model in self.models