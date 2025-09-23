"""Anthropic LLM Provider implementation.

Integrates with Anthropic's API for text generation using Claude models.
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


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Anthropic provider.
        
        Args:
            config: Configuration including api_key, base_url, etc.
        """
        super().__init__(ProviderType.ANTHROPIC, config)
        
        self.api_key = config.get("api_key") if config else None
        self.base_url = config.get("base_url", "https://api.anthropic.com") if config else "https://api.anthropic.com"
        
        self._client = None
        
        # Model definitions with current pricing (as of 2024)
        self._models = {
            "claude-3-5-sonnet-20241022": ModelInfo(
                name="claude-3-5-sonnet-20241022",
                provider=ProviderType.ANTHROPIC,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.VISION],
                context_length=200000,
                max_output_tokens=8192,
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                supports_streaming=True,
                supports_vision=True,
                description="Most intelligent Claude model"
            ),
            "claude-3-5-haiku-20241022": ModelInfo(
                name="claude-3-5-haiku-20241022",
                provider=ProviderType.ANTHROPIC,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING],
                context_length=200000,
                max_output_tokens=8192,
                input_cost_per_1k=0.0008,
                output_cost_per_1k=0.004,
                supports_streaming=True,
                description="Fast and affordable Claude model"
            ),
            "claude-3-opus-20240229": ModelInfo(
                name="claude-3-opus-20240229",
                provider=ProviderType.ANTHROPIC,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.VISION],
                context_length=200000,
                max_output_tokens=4096,
                input_cost_per_1k=0.015,
                output_cost_per_1k=0.075,
                supports_streaming=True,
                supports_vision=True,
                description="Most powerful Claude 3 model"
            ),
            "claude-3-sonnet-20240229": ModelInfo(
                name="claude-3-sonnet-20240229",
                provider=ProviderType.ANTHROPIC,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.VISION],
                context_length=200000,
                max_output_tokens=4096,
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                supports_streaming=True,
                supports_vision=True,
                description="Balanced Claude 3 model"
            ),
            "claude-3-haiku-20240307": ModelInfo(
                name="claude-3-haiku-20240307",
                provider=ProviderType.ANTHROPIC,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.VISION],
                context_length=200000,
                max_output_tokens=4096,
                input_cost_per_1k=0.00025,
                output_cost_per_1k=0.00125,
                supports_streaming=True,
                supports_vision=True,
                description="Fast and affordable Claude 3 model"
            )
        }
    
    async def initialize(self) -> None:
        """Initialize the Anthropic provider."""
        if not self.api_key:
            raise AuthenticationError("Anthropic API key is required", "anthropic")
        
        try:
            # Try to import Anthropic client
            import anthropic
            
            # Initialize client
            self._client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            self._initialized = True
            logger.info("Anthropic provider initialized successfully")
            
        except ImportError:
            raise ProviderError(
                "Anthropic package not installed. Install with: pip install anthropic",
                "missing_dependency",
                "anthropic"
            )
        except Exception as e:
            raise ProviderError(f"Failed to initialize Anthropic provider: {e}", "initialization_error", "anthropic")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Anthropic API."""
        if not self._initialized:
            await self.initialize()
        
        await self.validate_request(request)
        
        try:
            start_time = time.time()
            
            # Prepare API request
            api_request = self._prepare_api_request(request)
            
            # Make API call
            response = await self._client.messages.create(**api_request)
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Extract response data
            content = ""
            if response.content:
                # Anthropic returns a list of content blocks
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Extract token usage
            token_usage = None
            if response.usage:
                token_usage = TokenUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
                )
            
            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=response.stop_reason,
                token_usage=token_usage,
                response_time_ms=response_time_ms,
                provider_response_id=response.id,
                provider_metadata={
                    "stop_sequence": response.stop_sequence,
                    "type": response.type
                }
            )
            
        except Exception as e:
            return await self._handle_api_error(e)
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate streaming text using Anthropic API."""
        if not self._initialized:
            await self.initialize()
        
        await self.validate_request(request)
        
        try:
            # Prepare API request with streaming
            api_request = self._prepare_api_request(request)
            api_request["stream"] = True
            
            # Make streaming API call
            stream = await self._client.messages.create(**api_request)
            
            chunk_index = 0
            start_time = time.time()
            first_token_time = None
            
            async for chunk in stream:
                current_time = time.time()
                
                if chunk.type == "content_block_delta":
                    delta = chunk.delta
                    content = getattr(delta, "text", "") or ""
                    
                    if content and first_token_time is None:
                        first_token_time = current_time
                    
                    # Calculate delta time
                    delta_time_ms = None
                    if chunk_index > 0:
                        delta_time_ms = int((current_time - start_time) * 1000 / chunk_index)
                    
                    yield StreamingChunk(
                        content=content,
                        chunk_index=chunk_index,
                        timestamp=datetime.now(),
                        delta_time_ms=delta_time_ms
                    )
                    
                    chunk_index += 1
                
                elif chunk.type == "message_stop":
                    # Final chunk indicating completion
                    yield StreamingChunk(
                        content="",
                        chunk_index=chunk_index,
                        finish_reason="stop",
                        timestamp=datetime.now()
                    )
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
        """Get list of available Anthropic models."""
        return list(self._models.values())
    
    async def health_check(self) -> bool:
        """Check Anthropic API health."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Make a minimal API call to check connectivity
            # Anthropic doesn't have a dedicated health endpoint, so we make a small request
            response = await self._client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return response is not None
            
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about an Anthropic model."""
        return self._models.get(model_name)
    
    def get_default_model(self) -> Optional[str]:
        """Get default Anthropic model."""
        return "claude-3-5-sonnet-20241022"
    
    def _prepare_api_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepare API request parameters."""
        api_request = {
            "model": request.model,
            "max_tokens": request.max_tokens or 4096
        }
        
        # Handle messages vs prompt
        if request.messages:
            # Filter out system messages and handle separately
            messages = []
            system_content = ""
            
            for msg in request.messages:
                if msg.get("role") == "system":
                    system_content += msg.get("content", "")
                else:
                    messages.append(msg)
            
            api_request["messages"] = messages
            if system_content:
                api_request["system"] = system_content
        else:
            messages = [{"role": "user", "content": request.prompt}]
            api_request["messages"] = messages
            
            if request.system_prompt:
                api_request["system"] = request.system_prompt
        
        # Optional parameters
        if request.temperature is not None:
            api_request["temperature"] = request.temperature
        
        if request.top_p is not None:
            api_request["top_p"] = request.top_p
        
        if request.stop_sequences:
            api_request["stop_sequences"] = request.stop_sequences
        
        # Provider-specific parameters
        if request.provider_params:
            api_request.update(request.provider_params)
        
        return api_request
    
    async def _handle_api_error(self, error: Exception) -> LLMResponse:
        """Handle Anthropic API errors and convert to appropriate exceptions."""
        try:
            import anthropic
            
            if isinstance(error, anthropic.AuthenticationError):
                raise AuthenticationError(str(error), "anthropic")
            
            elif isinstance(error, anthropic.RateLimitError):
                retry_after = getattr(error.response.headers, "retry-after", None) if hasattr(error, 'response') else None
                raise RateLimitError(str(error), retry_after, "anthropic")
            
            elif isinstance(error, anthropic.NotFoundError):
                raise ModelNotFoundError("unknown", "anthropic")
            
            elif isinstance(error, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
                raise ProviderUnavailableError(str(error), "anthropic")
            
            else:
                raise ProviderError(f"Anthropic API error: {error}", "api_error", "anthropic")
                
        except ImportError:
            # Fallback if anthropic package is not available
            raise ProviderError(f"API error: {error}", "api_error", "anthropic")
    
    def supports_streaming(self) -> bool:
        """Anthropic supports streaming."""
        return True
    
    def supports_functions(self) -> bool:
        """Anthropic does not support function calling yet."""
        return False