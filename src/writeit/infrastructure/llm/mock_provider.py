"""Mock LLM Provider for testing and development.

Provides deterministic responses for testing pipeline functionality
without requiring actual LLM API calls.
"""

import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
import uuid
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
    ProviderError
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing and development."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize mock provider."""
        super().__init__(ProviderType.MOCK, config)
        
        # Mock configuration
        self.latency_ms = config.get("latency_ms", 500) if config else 500
        self.failure_rate = config.get("failure_rate", 0.0) if config else 0.0
        self.response_templates = config.get("response_templates", {}) if config else {}
        
        # Default response templates
        self._default_templates = {
            "article": "# {topic}\n\nThis is a comprehensive article about {topic}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "summary": "Summary: {content}\n\nKey points:\n- Point 1\n- Point 2\n- Point 3",
            "analysis": "Analysis of {topic}:\n\n1. Overview\n2. Key findings\n3. Recommendations",
            "default": "Mock response for: {prompt}"
        }
        
        # Available models
        self._models = {
            "mock-fast": ModelInfo(
                name="mock-fast",
                provider=ProviderType.MOCK,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING],
                context_length=4096,
                max_output_tokens=2048,
                input_cost_per_1k=0.001,  # Very cheap for testing
                output_cost_per_1k=0.002,
                supports_streaming=True,
                description="Fast mock model for testing"
            ),
            "mock-quality": ModelInfo(
                name="mock-quality",
                provider=ProviderType.MOCK,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING],
                context_length=8192,
                max_output_tokens=4096,
                input_cost_per_1k=0.005,
                output_cost_per_1k=0.010,
                supports_streaming=True,
                supports_functions=True,
                description="High-quality mock model for testing"
            ),
            "mock-basic": ModelInfo(
                name="mock-basic",
                provider=ProviderType.MOCK,
                capabilities=[ModelCapability.TEXT_GENERATION],
                context_length=2048,
                max_output_tokens=1024,
                input_cost_per_1k=0.0005,
                output_cost_per_1k=0.001,
                supports_streaming=False,
                description="Basic mock model for simple testing"
            )
        }
    
    async def initialize(self) -> None:
        """Initialize the mock provider."""
        self._initialized = True
        # Simulate initialization delay
        await asyncio.sleep(0.1)
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a mock response."""
        await self.validate_request(request)
        
        # Simulate network latency
        await asyncio.sleep(self.latency_ms / 1000)
        
        # Simulate random failures
        if random.random() < self.failure_rate:
            raise ProviderError("Mock failure for testing", "mock_error", "mock")
        
        # Generate mock content
        content = self._generate_mock_content(request)
        
        # Calculate token usage
        prompt_tokens = self._estimate_tokens(request.prompt)
        completion_tokens = self._estimate_tokens(content)
        
        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        
        return LLMResponse(
            content=content,
            model=request.model,
            finish_reason="stop",
            token_usage=token_usage,
            response_time_ms=self.latency_ms,
            provider_response_id=f"mock-{uuid.uuid4().hex[:8]}",
            provider_metadata={
                "mock_provider": True,
                "template_used": self._detect_template_type(request.prompt)
            }
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming mock response."""
        await self.validate_request(request)
        
        # Check if model supports streaming
        model_info = self.get_model_info(request.model)
        if not model_info or not model_info.supports_streaming:
            raise ProviderError(f"Model {request.model} does not support streaming")
        
        # Generate full content first
        content = self._generate_mock_content(request)
        words = content.split()
        
        # Stream words with delays
        chunk_delay = self.latency_ms / (len(words) + 1) / 1000
        
        current_content = ""
        for i, word in enumerate(words):
            await asyncio.sleep(chunk_delay)
            
            current_content += (" " if current_content else "") + word
            
            yield StreamingChunk(
                content=word + (" " if i < len(words) - 1 else ""),
                chunk_index=i,
                timestamp=datetime.now(),
                delta_time_ms=int(chunk_delay * 1000)
            )
        
        # Final chunk with token usage
        prompt_tokens = self._estimate_tokens(request.prompt)
        completion_tokens = self._estimate_tokens(content)
        
        yield StreamingChunk(
            content="",
            chunk_index=len(words),
            finish_reason="stop",
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            timestamp=datetime.now()
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of mock models."""
        return list(self._models.values())
    
    async def health_check(self) -> bool:
        """Mock health check (always healthy unless configured otherwise)."""
        return self.config.get("healthy", True)
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a mock model."""
        return self._models.get(model_name)
    
    def get_default_model(self) -> Optional[str]:
        """Get default mock model."""
        return "mock-fast"
    
    def supports_streaming(self) -> bool:
        """Mock provider supports streaming."""
        return True
    
    def supports_functions(self) -> bool:
        """Some mock models support functions."""
        return True
    
    def _generate_mock_content(self, request: LLMRequest) -> str:
        """Generate mock content based on the request."""
        # Check for custom templates first
        template_type = self._detect_template_type(request.prompt)
        template = self.response_templates.get(template_type)
        
        if not template:
            template = self._default_templates.get(template_type, self._default_templates["default"])
        
        # Extract variables from prompt for template substitution
        variables = self._extract_variables(request.prompt)
        
        try:
            content = template.format(**variables)
        except KeyError:
            # Fallback if template variables don't match
            content = template.replace("{prompt}", request.prompt[:100])
            content = content.replace("{topic}", variables.get("topic", "unknown topic"))
            content = content.replace("{content}", variables.get("content", "content"))
        
        # Adjust length based on max_tokens
        if request.max_tokens:
            # Rough approximation: 1 token ≈ 4 characters
            max_chars = request.max_tokens * 4
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
        
        return content
    
    def _detect_template_type(self, prompt: str) -> str:
        """Detect the type of content being requested."""
        prompt_lower = prompt.lower()
        
        if "article" in prompt_lower or "write about" in prompt_lower:
            return "article"
        elif "summary" in prompt_lower or "summarize" in prompt_lower:
            return "summary" 
        elif "analysis" in prompt_lower or "analyze" in prompt_lower:
            return "analysis"
        else:
            return "default"
    
    def _extract_variables(self, prompt: str) -> Dict[str, str]:
        """Extract variables from the prompt for template substitution."""
        variables = {
            "prompt": prompt,
            "topic": "general topic",
            "content": "sample content"
        }
        
        # Simple extraction patterns
        if "about " in prompt.lower():
            parts = prompt.lower().split("about ")
            if len(parts) > 1:
                topic = parts[1].split()[0:3]  # Take first few words
                variables["topic"] = " ".join(topic)
        
        return variables
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Very rough approximation: 1 token ≈ 4 characters
        return max(1, len(text) // 4)
    
    def set_response_template(self, template_type: str, template: str) -> None:
        """Set a custom response template."""
        self.response_templates[template_type] = template
    
    def set_latency(self, latency_ms: int) -> None:
        """Set mock latency."""
        self.latency_ms = latency_ms
    
    def set_failure_rate(self, rate: float) -> None:
        """Set mock failure rate (0.0 to 1.0)."""
        self.failure_rate = max(0.0, min(1.0, rate))
