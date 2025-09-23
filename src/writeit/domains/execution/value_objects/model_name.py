"""ModelName value object.

Value object representing a validated LLM model identifier.
"""

import re
from dataclasses import dataclass
from typing import Self, Optional


@dataclass(frozen=True, eq=True)
class ModelName:
    """Value object representing a validated model name.
    
    Ensures model names are properly formatted and normalized.
    
    Examples:
        model = ModelName.from_string("gpt-4o-mini")
        model = ModelName.from_string("claude-3-sonnet")
        
        # Validation
        assert model.is_openai_model()
        assert model.get_provider() == "openai"
        
        # Normalization
        normalized = ModelName.from_string(" GPT-4O-MINI ")
        assert str(normalized) == "gpt-4o-mini"
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate model name."""
        if not self.value:
            raise ValueError("Model name cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError("Model name must be a string")
            
        # Validate format (alphanumeric, hyphens, dots, underscores)
        if not re.match(r'^[a-zA-Z0-9._-]+$', self.value):
            raise ValueError(
                f"Invalid model name format: '{self.value}'. "
                "Must contain only alphanumeric characters, hyphens, dots, and underscores."
            )
            
        # Check length constraints
        if len(self.value) > 100:
            raise ValueError(f"Model name too long: {len(self.value)} characters (max 100)")
            
        if len(self.value) < 2:
            raise ValueError(f"Model name too short: {len(self.value)} characters (min 2)")
    
    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create model name from string with normalization.
        
        Args:
            value: Model name string
            
        Returns:
            Normalized model name
            
        Raises:
            ValueError: If model name is invalid
        """
        if not value or not isinstance(value, str):
            raise ValueError("Model name must be a non-empty string")
            
        # Normalize: strip whitespace and convert to lowercase
        normalized = value.strip().lower()
        
        return cls(normalized)
    
    def get_provider(self) -> Optional[str]:
        """Get the provider name from model name.
        
        Returns:
            Provider name or None if unknown
        """
        model_lower = self.value.lower()
        
        if model_lower.startswith(('gpt-', 'text-', 'davinci', 'curie', 'babbage', 'ada')):
            return "openai"
        elif model_lower.startswith(('claude-', 'anthropic')):
            return "anthropic"
        elif model_lower.startswith(('llama', 'mistral', 'vicuna', 'alpaca')):
            return "local"
        elif model_lower.startswith(('mock', 'test')):
            return "mock"
        else:
            return None
    
    def is_openai_model(self) -> bool:
        """Check if this is an OpenAI model."""
        return self.get_provider() == "openai"
    
    def is_anthropic_model(self) -> bool:
        """Check if this is an Anthropic model."""
        return self.get_provider() == "anthropic"
    
    def is_local_model(self) -> bool:
        """Check if this is a local model."""
        return self.get_provider() == "local"
    
    def is_mock_model(self) -> bool:
        """Check if this is a mock/test model."""
        return self.get_provider() == "mock"
    
    def get_model_family(self) -> Optional[str]:
        """Get the model family (e.g., 'gpt-4', 'claude-3').
        
        Returns:
            Model family or None if unknown
        """
        model_lower = self.value.lower()
        
        # OpenAI families
        if model_lower.startswith('gpt-4'):
            return "gpt-4"
        elif model_lower.startswith('gpt-3.5'):
            return "gpt-3.5"
        elif model_lower.startswith('gpt-3'):
            return "gpt-3"
        
        # Anthropic families
        elif model_lower.startswith('claude-3'):
            return "claude-3"
        elif model_lower.startswith('claude-2'):
            return "claude-2"
        elif model_lower.startswith('claude-1'):
            return "claude-1"
        
        # Local model families
        elif 'llama' in model_lower:
            return "llama"
        elif 'mistral' in model_lower:
            return "mistral"
        
        return None
    
    def get_estimated_context_length(self) -> Optional[int]:
        """Get estimated context length for this model.
        
        Returns:
            Estimated context length or None if unknown
        """
        model_lower = self.value.lower()
        
        # OpenAI models
        if model_lower in ('gpt-4o', 'gpt-4o-mini'):
            return 128000
        elif model_lower.startswith('gpt-4'):
            return 8192
        elif model_lower.startswith('gpt-3.5'):
            return 16384
        
        # Anthropic models
        elif model_lower.startswith('claude-3'):
            return 200000
        elif model_lower.startswith('claude-2'):
            return 100000
        
        return None
    
    def supports_function_calling(self) -> bool:
        """Check if model supports function calling."""
        model_lower = self.value.lower()
        
        # OpenAI models with function calling
        if model_lower in (
            'gpt-4o', 'gpt-4o-mini', 'gpt-4', 'gpt-4-turbo', 
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'
        ):
            return True
        
        # Anthropic models with function calling
        if model_lower.startswith('claude-3'):
            return True
        
        return False
    
    def supports_vision(self) -> bool:
        """Check if model supports vision/image inputs."""
        model_lower = self.value.lower()
        
        # OpenAI vision models
        if model_lower in ('gpt-4o', 'gpt-4-vision-preview', 'gpt-4-turbo'):
            return True
        
        return False
    
    def to_api_format(self) -> str:
        """Convert to API-compatible format.
        
        Returns:
            Model name in API format
        """
        # Most APIs use the normalized lowercase format
        return self.value
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"ModelName('{self.value}')"
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)
