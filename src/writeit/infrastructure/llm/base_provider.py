"""Base LLM Provider interface and abstract implementation.

Defines the contract for all LLM providers in the WriteIt system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from enum import Enum
import asyncio
from datetime import datetime


class ProviderType(str, Enum):
    """Types of LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"


class ModelCapability(str, Enum):
    """Model capabilities."""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    COMPLETION = "completion"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE_GENERATION = "code_generation"


@dataclass
class LLMRequest:
    """Request structure for LLM operations."""
    
    prompt: str
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    
    # Additional parameters
    system_prompt: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    functions: Optional[List[Dict[str, Any]]] = None
    
    # Metadata
    request_id: Optional[str] = None
    workspace_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    step_id: Optional[str] = None
    
    # Provider-specific parameters
    provider_params: Optional[Dict[str, Any]] = None


@dataclass
class TokenUsage:
    """Token usage information."""
    
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @property
    def input_tokens(self) -> int:
        """Alias for prompt_tokens."""
        return self.prompt_tokens
    
    @property
    def output_tokens(self) -> int:
        """Alias for completion_tokens."""
        return self.completion_tokens


@dataclass
class LLMResponse:
    """Response structure for LLM operations."""
    
    content: str
    model: str
    finish_reason: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    
    # Timing information
    response_time_ms: Optional[int] = None
    first_token_time_ms: Optional[int] = None
    
    # Provider-specific data
    provider_response_id: Optional[str] = None
    provider_metadata: Optional[Dict[str, Any]] = None
    
    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Additional data
    function_call: Optional[Dict[str, Any]] = None
    choices: Optional[List[Dict[str, Any]]] = None


@dataclass
class StreamingChunk:
    """Chunk of streaming response."""
    
    content: str
    chunk_index: int
    timestamp: datetime
    finish_reason: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    delta_time_ms: Optional[int] = None


@dataclass
class ModelInfo:
    """Information about a model."""
    
    name: str
    provider: ProviderType
    capabilities: List[ModelCapability]
    context_length: int
    max_output_tokens: Optional[int] = None
    
    # Pricing (per 1K tokens)
    input_cost_per_1k: Optional[float] = None
    output_cost_per_1k: Optional[float] = None
    
    # Model characteristics
    supports_streaming: bool = False
    supports_functions: bool = False
    supports_vision: bool = False
    
    # Additional metadata
    description: Optional[str] = None
    version: Optional[str] = None
    deprecated: bool = False


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, provider: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code
        self.provider = provider


class RateLimitError(ProviderError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, provider: Optional[str] = None):
        super().__init__(message, "rate_limit", provider)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Authentication error."""
    
    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message, "authentication", provider)


class ModelNotFoundError(ProviderError):
    """Model not found error."""
    
    def __init__(self, model: str, provider: Optional[str] = None):
        super().__init__(f"Model '{model}' not found", "model_not_found", provider)
        self.model = model


class ProviderUnavailableError(ProviderError):
    """Provider service unavailable error."""
    
    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message, "service_unavailable", provider)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, provider_type: ProviderType, config: Optional[Dict[str, Any]] = None):
        """Initialize the provider.
        
        Args:
            provider_type: Type of this provider
            config: Provider-specific configuration
        """
        self.provider_type = provider_type
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (async setup, authentication, etc.)."""
        pass
    
    @abstractmethod
    async def generate(
        self, 
        request: LLMRequest
    ) -> LLMResponse:
        """Generate text using the LLM.
        
        Args:
            request: LLM request parameters
            
        Returns:
            LLM response
            
        Raises:
            ProviderError: If generation fails
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self, 
        request: LLMRequest
    ) -> AsyncGenerator[StreamingChunk, None]:
        """Generate text with streaming response.
        
        Args:
            request: LLM request parameters (with stream=True)
            
        Yields:
            Streaming chunks
            
        Raises:
            ProviderError: If streaming fails
        """
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models.
        
        Returns:
            List of model information
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information if available, None otherwise
        """
        pass
    
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming."""
        return True
    
    def supports_functions(self) -> bool:
        """Check if provider supports function calling."""
        return False
    
    def get_default_model(self) -> Optional[str]:
        """Get the default model for this provider."""
        return None
    
    def estimate_cost(
        self, 
        request: LLMRequest, 
        response: Optional[LLMResponse] = None
    ) -> Optional[float]:
        """Estimate the cost of a request.
        
        Args:
            request: LLM request
            response: LLM response (if available)
            
        Returns:
            Estimated cost in USD, None if cannot estimate
        """
        model_info = self.get_model_info(request.model)
        if not model_info or not model_info.input_cost_per_1k:
            return None
        
        if response and response.token_usage:
            input_cost = (response.token_usage.prompt_tokens / 1000) * model_info.input_cost_per_1k
            output_cost = 0
            if model_info.output_cost_per_1k:
                output_cost = (response.token_usage.completion_tokens / 1000) * model_info.output_cost_per_1k
            return input_cost + output_cost
        
        # Rough estimate based on prompt length
        estimated_tokens = len(request.prompt) // 4  # Rough approximation
        return (estimated_tokens / 1000) * model_info.input_cost_per_1k
    
    async def validate_request(self, request: LLMRequest) -> None:
        """Validate an LLM request.
        
        Args:
            request: Request to validate
            
        Raises:
            ProviderError: If request is invalid
        """
        if not request.prompt and not request.messages:
            raise ProviderError("Either prompt or messages must be provided")
        
        if not request.model:
            raise ProviderError("Model must be specified")
        
        model_info = self.get_model_info(request.model)
        if not model_info:
            raise ModelNotFoundError(request.model, str(self.provider_type))
        
        # Check context length
        prompt_length = len(request.prompt or "")
        if request.messages:
            prompt_length += sum(len(str(msg)) for msg in request.messages)
        
        estimated_tokens = prompt_length // 4  # Rough approximation
        if estimated_tokens > model_info.context_length:
            raise ProviderError(
                f"Request too long: {estimated_tokens} tokens exceeds context length {model_info.context_length}"
            )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.provider_type.value})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"{self.__class__.__name__}(provider_type={self.provider_type}, config_keys={list(self.config.keys())})"
