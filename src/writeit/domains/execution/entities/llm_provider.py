"""LLM Provider entity.

Domain entity representing an LLM provider configuration and capabilities.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, List, Optional, Self
from enum import Enum

from ..value_objects.model_name import ModelName
from ..value_objects.token_count import TokenCount


class ProviderStatus(str, Enum):
    """Status of an LLM provider."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class ProviderType(str, Enum):
    """Type of LLM provider."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class LLMProvider:
    """Domain entity representing an LLM provider.
    
    Manages provider configuration, capabilities, and health status.
    
    Examples:
        provider = LLMProvider.create(
            name="OpenAI GPT-4",
            provider_type=ProviderType.OPENAI,
            api_key_ref="openai_api_key",
            supported_models=[
                ModelName.from_string("gpt-4o-mini"),
                ModelName.from_string("gpt-4o")
            ]
        )
        
        # Check capabilities
        supports_streaming = provider.supports_streaming()
        max_tokens = provider.get_max_tokens(ModelName.from_string("gpt-4o-mini"))
        
        # Update status
        provider = provider.mark_healthy()
        provider = provider.mark_error("API key invalid")
    """
    
    name: str
    provider_type: ProviderType
    status: ProviderStatus = ProviderStatus.ACTIVE
    api_key_ref: Optional[str] = None
    base_url: Optional[str] = None
    supported_models: List[ModelName] = field(default_factory=list)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None
    last_health_check: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate LLM provider."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Provider name must be a non-empty string")
            
        if not isinstance(self.provider_type, ProviderType):
            raise TypeError("Provider type must be a ProviderType")
            
        if not isinstance(self.status, ProviderStatus):
            raise TypeError("Status must be a ProviderStatus")
            
        # Validate supported models
        for model in self.supported_models:
            if not isinstance(model, ModelName):
                raise TypeError("Supported models must be ModelName instances")
                
        # Validate dictionaries
        for field_name, field_value in [
            ("capabilities", self.capabilities),
            ("rate_limits", self.rate_limits),
            ("metadata", self.metadata)
        ]:
            if not isinstance(field_value, dict):
                raise TypeError(f"{field_name} must be a dictionary")
                
        # Validate status consistency
        if self.status == ProviderStatus.ERROR and not self.error_message:
            raise ValueError("Error status requires error message")
    
    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy and available."""
        return self.status == ProviderStatus.ACTIVE
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available for requests."""
        return self.status in {ProviderStatus.ACTIVE, ProviderStatus.INACTIVE}
    
    @property
    def has_api_key(self) -> bool:
        """Check if provider has API key configured."""
        return self.api_key_ref is not None
    
    def supports_model(self, model: ModelName) -> bool:
        """Check if provider supports a specific model.
        
        Args:
            model: Model name to check
            
        Returns:
            True if model is supported
        """
        return model in self.supported_models
    
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return self.capabilities.get("streaming", False)
    
    def supports_function_calling(self) -> bool:
        """Check if provider supports function calling."""
        return self.capabilities.get("function_calling", False)
    
    def supports_vision(self) -> bool:
        """Check if provider supports vision/image inputs."""
        return self.capabilities.get("vision", False)
    
    def get_max_tokens(self, model: ModelName) -> Optional[int]:
        """Get maximum tokens for a model.
        
        Args:
            model: Model name
            
        Returns:
            Maximum tokens or None if unknown
        """
        model_key = f"max_tokens_{str(model)}"
        return self.metadata.get(model_key)
    
    def get_rate_limit(self, limit_type: str = "requests_per_minute") -> Optional[int]:
        """Get rate limit for this provider.
        
        Args:
            limit_type: Type of rate limit
            
        Returns:
            Rate limit or None if not set
        """
        return self.rate_limits.get(limit_type)
    
    def mark_healthy(self) -> Self:
        """Mark provider as healthy.
        
        Returns:
            Updated provider with healthy status
        """
        return replace(
            self,
            status=ProviderStatus.ACTIVE,
            error_message=None,
            last_health_check=datetime.now(),
            updated_at=datetime.now()
        )
    
    def mark_inactive(self) -> Self:
        """Mark provider as inactive.
        
        Returns:
            Updated provider with inactive status
        """
        return replace(
            self,
            status=ProviderStatus.INACTIVE,
            updated_at=datetime.now()
        )
    
    def mark_maintenance(self, reason: str = "") -> Self:
        """Mark provider as under maintenance.
        
        Args:
            reason: Maintenance reason
            
        Returns:
            Updated provider with maintenance status
        """
        metadata = self.metadata.copy()
        if reason:
            metadata["maintenance_reason"] = reason
            
        return replace(
            self,
            status=ProviderStatus.MAINTENANCE,
            metadata=metadata,
            updated_at=datetime.now()
        )
    
    def mark_error(self, error_message: str) -> Self:
        """Mark provider as having an error.
        
        Args:
            error_message: Error description
            
        Returns:
            Updated provider with error status
        """
        return replace(
            self,
            status=ProviderStatus.ERROR,
            error_message=error_message,
            last_health_check=datetime.now(),
            updated_at=datetime.now()
        )
    
    def add_model(self, model: ModelName) -> Self:
        """Add supported model.
        
        Args:
            model: Model to add
            
        Returns:
            Updated provider with new model
        """
        if model in self.supported_models:
            return self
            
        new_models = self.supported_models + [model]
        return replace(
            self,
            supported_models=new_models,
            updated_at=datetime.now()
        )
    
    def remove_model(self, model: ModelName) -> Self:
        """Remove supported model.
        
        Args:
            model: Model to remove
            
        Returns:
            Updated provider without model
        """
        if model not in self.supported_models:
            return self
            
        new_models = [m for m in self.supported_models if m != model]
        return replace(
            self,
            supported_models=new_models,
            updated_at=datetime.now()
        )
    
    def set_capability(self, capability: str, enabled: bool) -> Self:
        """Set provider capability.
        
        Args:
            capability: Capability name
            enabled: Whether capability is enabled
            
        Returns:
            Updated provider with capability
        """
        new_capabilities = self.capabilities.copy()
        new_capabilities[capability] = enabled
        
        return replace(
            self,
            capabilities=new_capabilities,
            updated_at=datetime.now()
        )
    
    def set_rate_limit(self, limit_type: str, limit_value: int) -> Self:
        """Set rate limit.
        
        Args:
            limit_type: Type of rate limit
            limit_value: Limit value
            
        Returns:
            Updated provider with rate limit
        """
        new_rate_limits = self.rate_limits.copy()
        new_rate_limits[limit_type] = limit_value
        
        return replace(
            self,
            rate_limits=new_rate_limits,
            updated_at=datetime.now()
        )
    
    def update_metadata(self, key: str, value: Any) -> Self:
        """Update metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Updated provider with metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        
        return replace(
            self,
            metadata=new_metadata,
            updated_at=datetime.now()
        )
    
    @classmethod
    def create(
        cls,
        name: str,
        provider_type: ProviderType,
        api_key_ref: Optional[str] = None,
        base_url: Optional[str] = None,
        supported_models: Optional[List[ModelName]] = None,
        capabilities: Optional[Dict[str, bool]] = None
    ) -> Self:
        """Create a new LLM provider.
        
        Args:
            name: Provider name
            provider_type: Provider type
            api_key_ref: API key reference
            base_url: Base URL for API
            supported_models: List of supported models
            capabilities: Provider capabilities
            
        Returns:
            New LLM provider
        """
        # Set default capabilities based on provider type
        default_capabilities = {}
        if provider_type == ProviderType.OPENAI:
            default_capabilities = {
                "streaming": True,
                "function_calling": True,
                "vision": True
            }
        elif provider_type == ProviderType.ANTHROPIC:
            default_capabilities = {
                "streaming": True,
                "function_calling": True,
                "vision": False
            }
        elif provider_type == ProviderType.LOCAL:
            default_capabilities = {
                "streaming": False,
                "function_calling": False,
                "vision": False
            }
        elif provider_type == ProviderType.MOCK:
            default_capabilities = {
                "streaming": True,
                "function_calling": True,
                "vision": True
            }
        
        # Merge with provided capabilities
        final_capabilities = {**default_capabilities, **(capabilities or {})}
        
        return cls(
            name=name,
            provider_type=provider_type,
            api_key_ref=api_key_ref,
            base_url=base_url,
            supported_models=supported_models or [],
            capabilities=final_capabilities,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @classmethod
    def openai_provider(
        cls,
        api_key_ref: str,
        name: str = "OpenAI",
        base_url: Optional[str] = None
    ) -> Self:
        """Create OpenAI provider with default models.
        
        Args:
            api_key_ref: API key reference
            name: Provider name
            base_url: Custom base URL
            
        Returns:
            OpenAI provider
        """
        models = [
            ModelName.from_string("gpt-4o-mini"),
            ModelName.from_string("gpt-4o"),
            ModelName.from_string("gpt-3.5-turbo")
        ]
        
        provider = cls.create(
            name=name,
            provider_type=ProviderType.OPENAI,
            api_key_ref=api_key_ref,
            base_url=base_url or "https://api.openai.com/v1",
            supported_models=models
        )
        
        # Set OpenAI-specific metadata
        provider = provider.update_metadata("max_tokens_gpt-4o-mini", 128000)
        provider = provider.update_metadata("max_tokens_gpt-4o", 128000)
        provider = provider.update_metadata("max_tokens_gpt-3.5-turbo", 16384)
        
        # Set rate limits
        provider = provider.set_rate_limit("requests_per_minute", 3500)
        provider = provider.set_rate_limit("tokens_per_minute", 500000)
        
        return provider
    
    @classmethod
    def anthropic_provider(
        cls,
        api_key_ref: str,
        name: str = "Anthropic",
        base_url: Optional[str] = None
    ) -> Self:
        """Create Anthropic provider with default models.
        
        Args:
            api_key_ref: API key reference
            name: Provider name
            base_url: Custom base URL
            
        Returns:
            Anthropic provider
        """
        models = [
            ModelName.from_string("claude-3-haiku"),
            ModelName.from_string("claude-3-sonnet"),
            ModelName.from_string("claude-3-opus")
        ]
        
        provider = cls.create(
            name=name,
            provider_type=ProviderType.ANTHROPIC,
            api_key_ref=api_key_ref,
            base_url=base_url or "https://api.anthropic.com/v1",
            supported_models=models
        )
        
        # Set Anthropic-specific metadata
        provider = provider.update_metadata("max_tokens_claude-3-haiku", 200000)
        provider = provider.update_metadata("max_tokens_claude-3-sonnet", 200000)
        provider = provider.update_metadata("max_tokens_claude-3-opus", 200000)
        
        # Set rate limits
        provider = provider.set_rate_limit("requests_per_minute", 1000)
        provider = provider.set_rate_limit("tokens_per_minute", 100000)
        
        return provider
    
    @classmethod
    def mock_provider(cls, name: str = "Mock") -> Self:
        """Create mock provider for testing.
        
        Args:
            name: Provider name
            
        Returns:
            Mock provider
        """
        models = [
            ModelName.from_string("mock-model"),
            ModelName.from_string("test-model")
        ]
        
        return cls.create(
            name=name,
            provider_type=ProviderType.MOCK,
            supported_models=models
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "provider_type": self.provider_type.value,
            "status": self.status.value,
            "api_key_ref": self.api_key_ref,
            "base_url": self.base_url,
            "supported_models": [str(model) for model in self.supported_models],
            "capabilities": self.capabilities,
            "rate_limits": self.rate_limits,
            "error_message": self.error_message,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"LLMProvider({self.name} - {self.status.value})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"LLMProvider(name='{self.name}', type={self.provider_type.value}, "
                f"status={self.status.value}, models={len(self.supported_models)})")