"""OpenAI LLM Provider implementation.

Integrates with OpenAI's API for text generation using GPT models.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
import time

from .base_provider import (
    BaseLLMProvider,
    ProviderType,
    ModelCapability,
    LLMRequest,
    LLMResponse,
    StreamingChunk,
    ModelInfo,
    TokenUsage,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    ProviderUnavailableError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI provider.
        
        Args:
            config: Configuration including api_key, organization, etc.
        """
        super().__init__(ProviderType.OPENAI, config)
        
        self.api_key = config.get("api_key") if config else None
        self.organization = config.get("organization") if config else None
        self.base_url = config.get("base_url", "https://api.openai.com/v1") if config else "https://api.openai.com/v1"
        
        self._client = None
        self._async_client = None
        
        # Model definitions with current pricing (as of 2024)
        self._models = {
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                provider=ProviderType.OPENAI,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.VISION],
                context_length=128000,
                max_output_tokens=4096,
                input_cost_per_1k=0.0025,
                output_cost_per_1k=0.010,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                description="Most advanced OpenAI model with vision capabilities"
            ),
            "gpt-4o-mini": ModelInfo(
                name="gpt-4o-mini",
                provider=ProviderType.OPENAI,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING],
                context_length=128000,
                max_output_tokens=16384,
                input_cost_per_1k=0.00015,
                output_cost_per_1k=0.0006,
                supports_streaming=True,
                supports_functions=True,
                description="Affordable and intelligent small model"
            ),
            "gpt-4-turbo": ModelInfo(
                name="gpt-4-turbo",
                provider=ProviderType.OPENAI,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.VISION],
                context_length=128000,
                max_output_tokens=4096,
                input_cost_per_1k=0.01,
                output_cost_per_1k=0.03,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                description="Previous generation GPT-4 Turbo model"
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                provider=ProviderType.OPENAI,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING],
                context_length=16385,
                max_output_tokens=4096,
                input_cost_per_1k=0.0005,
                output_cost_per_1k=0.0015,
                supports_streaming=True,
                supports_functions=True,
                description="Fast and cost-effective model"
            )
        }
    
    async def initialize(self) -> None:
        """Initialize the OpenAI provider."""
        if not self.api_key:
            raise AuthenticationError("OpenAI API key is required", "openai")
        
        try:
            # Try to import OpenAI client
            import openai
            
            # Initialize synchronous client
            self._client = openai.OpenAI(
                api_key=self.api_key,
                organization=self.organization,
                base_url=self.base_url
            )
            
            # Initialize asynchronous client
            self._async_client = openai.AsyncOpenAI(
                api_key=self.api_key,
                organization=self.organization,
                base_url=self.base_url
            )
            
            self._initialized = True
            logger.info("OpenAI provider initialized successfully")
            
        except ImportError:
            raise ProviderError(
                "OpenAI package not installed. Install with: pip install openai",
                "missing_dependency",
                "openai"
            )
        except Exception as e:
            raise ProviderError(f"Failed to initialize OpenAI provider: {e}", "initialization_error", "openai")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using OpenAI API."""
        if not self._initialized:
            await self.initialize()
        
        await self.validate_request(request)
        
        try:
            start_time = time.time()
            
            # Prepare API request
            api_request = self._prepare_api_request(request)
            
            # Make API call
            response = await self._async_client.chat.completions.create(**api_request)
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Extract response data
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # Extract token usage
            token_usage = None
            if response.usage:
                token_usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens
                )
            
            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=choice.finish_reason,
                token_usage=token_usage,
                response_time_ms=response_time_ms,
                provider_response_id=response.id,
                provider_metadata={
                    "system_fingerprint": getattr(response, "system_fingerprint", None),
                    "created": response.created
                },
                function_call=getattr(choice.message, "function_call", None)
            )
            
        except Exception as e:
            return await self._handle_api_error(e)
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate streaming text using OpenAI API."""
        if not self._initialized:
            await self.initialize()
        
        await self.validate_request(request)
        
        try:
            # Prepare API request with streaming
            api_request = self._prepare_api_request(request)
            api_request["stream"] = True
            
            # Make streaming API call
            stream = await self._async_client.chat.completions.create(**api_request)
            
            chunk_index = 0
            start_time = time.time()
            first_token_time = None
            
            async for chunk in stream:
                current_time = time.time()
                
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    content = getattr(delta, "content", "") or ""
                    
                    if content and first_token_time is None:
                        first_token_time = current_time
                    
                    # Calculate delta time
                    delta_time_ms = None
                    if chunk_index > 0:
                        delta_time_ms = int((current_time - start_time) * 1000 / chunk_index)
                    
                    yield StreamingChunk(
                        content=content,
                        chunk_index=chunk_index,
                        finish_reason=choice.finish_reason,
                        timestamp=datetime.now(),
                        delta_time_ms=delta_time_ms
                    )
                    
                    chunk_index += 1
                    
                    # Check for completion
                    if choice.finish_reason:
                        break
            
        except Exception as e:
            error_response = await self._handle_api_error(e)
            # Convert error to streaming format
            yield StreamingChunk(
                content="",
                chunk_index=0,
                finish_reason="error",
                timestamp=datetime.now()
            )
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available OpenAI models."""
        return list(self._models.values())
    
    async def health_check(self) -> bool:
        """Check OpenAI API health."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Make a minimal API call to check connectivity
            response = await self._async_client.models.list()
            return len(response.data) > 0
            
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about an OpenAI model."""
        return self._models.get(model_name)
    
    def get_default_model(self) -> Optional[str]:
        """Get default OpenAI model."""
        return "gpt-4o-mini"
    
    def _prepare_api_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepare API request parameters."""
        api_request = {
            "model": request.model,
            "stream": request.stream
        }
        
        # Handle messages vs prompt
        if request.messages:
            api_request["messages"] = request.messages
        else:
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            api_request["messages"] = messages
        
        # Optional parameters
        if request.max_tokens is not None:
            api_request["max_tokens"] = request.max_tokens
        
        if request.temperature is not None:
            api_request["temperature"] = request.temperature
        
        if request.top_p is not None:
            api_request["top_p"] = request.top_p
        
        if request.stop_sequences:
            api_request["stop"] = request.stop_sequences
        
        if request.functions:
            api_request["functions"] = request.functions
        
        # Provider-specific parameters
        if request.provider_params:
            api_request.update(request.provider_params)
        
        return api_request
    
    async def _handle_api_error(self, error: Exception) -> LLMResponse:
        """Handle OpenAI API errors and convert to appropriate exceptions."""
        try:
            import openai
            
            if isinstance(error, openai.AuthenticationError):
                raise AuthenticationError(str(error), "openai")
            
            elif isinstance(error, openai.RateLimitError):
                retry_after = getattr(error, "retry_after", None)
                raise RateLimitError(str(error), retry_after, "openai")
            
            elif isinstance(error, openai.NotFoundError):
                raise ModelNotFoundError("unknown", "openai")
            
            elif isinstance(error, (openai.APIConnectionError, openai.APITimeoutError)):
                raise ProviderUnavailableError(str(error), "openai")
            
            else:
                raise ProviderError(f"OpenAI API error: {error}", "api_error", "openai")
                
        except ImportError:
            # Fallback if openai package is not available
            raise ProviderError(f"API error: {error}", "api_error", "openai")
    
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True
    
    def supports_functions(self) -> bool:
        """OpenAI supports function calling."""
        return True
