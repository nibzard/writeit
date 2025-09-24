"""Mock implementation of LLMOrchestrationService for testing."""

from typing import Dict, List, Any, Optional, AsyncGenerator
from unittest.mock import AsyncMock
from datetime import datetime

from writeit.domains.execution.services.llm_orchestration_service import (
    LLMOrchestrationService,
    ProviderSelectionStrategy,
    RequestContext,
    LLMResponse,
    ProviderStatus
)
from writeit.domains.execution.entities.llm_provider import LLMProvider
from writeit.domains.execution.value_objects.model_name import ModelName


class MockLLMOrchestrationService(LLMOrchestrationService):
    """Mock implementation of LLMOrchestrationService.
    
    Provides configurable LLM orchestration behavior for testing
    LLM orchestration scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock orchestration service."""
        self._mock = AsyncMock()
        self._llm_responses: Dict[str, LLMResponse] = {}
        self._provider_health: Dict[str, ProviderStatus] = {}
        self._available_providers: List[LLMProvider] = []
        self._should_fail = False
        self._response_delay = 0.0
        
    def configure_llm_response(self, model: str, response: LLMResponse) -> None:
        """Configure LLM response for specific model."""
        self._llm_responses[model] = response
        
    def configure_provider_health(
        self, 
        provider_name: str, 
        status: ProviderStatus
    ) -> None:
        """Configure provider health status."""
        self._provider_health[provider_name] = status
        
    def configure_available_providers(self, providers: List[LLMProvider]) -> None:
        """Configure available providers."""
        self._available_providers = providers
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if orchestration should fail."""
        self._should_fail = should_fail
        
    def configure_response_delay(self, delay_seconds: float) -> None:
        """Configure response delay for testing timing."""
        self._response_delay = delay_seconds
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._llm_responses.clear()
        self._provider_health.clear()
        self._available_providers.clear()
        self._should_fail = False
        self._response_delay = 0.0
        self._mock.reset_mock()
        
    @property
    def mock(self) -> AsyncMock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def execute_llm_request(
        self,
        request: RequestContext,
        strategy: Optional[ProviderSelectionStrategy] = None
    ) -> LLMResponse:
        """Execute LLM request with provider selection."""
        await self._mock.execute_llm_request(request, strategy)
        
        # Simulate response delay
        if self._response_delay > 0:
            import asyncio
            await asyncio.sleep(self._response_delay)
            
        if self._should_fail:
            raise Exception("Mock LLM orchestration error")
            
        # Return configured response if available
        if request.model in self._llm_responses:
            return self._llm_responses[request.model]
            
        # Create mock response
        return LLMResponse(
            content=f"Mock response for: {request.prompt}",
            model=request.model,
            tokens_used=50,
            provider="mock-provider",
            request_id="mock-request-123",
            timestamp=datetime.now()
        )
        
    async def stream_llm_request(
        self,
        request: RequestContext,
        strategy: Optional[ProviderSelectionStrategy] = None
    ) -> AsyncGenerator[str, None]:
        """Stream LLM request response."""
        await self._mock.stream_llm_request(request, strategy)
        
        if self._should_fail:
            raise Exception("Mock LLM streaming error")
            
        # Mock streaming response
        response_text = f"Mock streaming response for: {request.prompt}"
        for word in response_text.split():
            if self._response_delay > 0:
                import asyncio
                await asyncio.sleep(self._response_delay / 10)  # Smaller delay per chunk
            yield word + " "
            
    async def select_optimal_provider(
        self,
        model: ModelName,
        strategy: ProviderSelectionStrategy
    ) -> Optional[LLMProvider]:
        """Select optimal provider for model."""
        await self._mock.select_optimal_provider(model, strategy)
        
        if self._should_fail or not self._available_providers:
            return None
            
        # Return first available provider that supports the model
        for provider in self._available_providers:
            if str(model.value) in provider.supported_models:
                return provider
                
        return None
        
    async def check_provider_health(self, provider_name: str) -> ProviderStatus:
        """Check provider health status."""
        await self._mock.check_provider_health(provider_name)
        
        # Return configured health status if available
        if provider_name in self._provider_health:
            return self._provider_health[provider_name]
            
        # Return mock healthy status
        return ProviderStatus.ACTIVE if not self._should_fail else ProviderStatus.ERROR
        
    async def get_available_models(self, provider_name: Optional[str] = None) -> List[str]:
        """Get available models from providers."""
        await self._mock.get_available_models(provider_name)
        
        if provider_name:
            # Get models for specific provider
            for provider in self._available_providers:
                if provider.name == provider_name:
                    return provider.supported_models
            return []
        else:
            # Get all available models
            all_models = set()
            for provider in self._available_providers:
                all_models.update(provider.supported_models)
            return list(all_models)
            
    async def estimate_request_cost(
        self,
        request: RequestContext,
        provider_name: Optional[str] = None
    ) -> float:
        """Estimate cost for LLM request."""
        await self._mock.estimate_request_cost(request, provider_name)
        
        # Mock cost calculation
        base_cost = 0.001  # $0.001 per token
        estimated_tokens = len(request.prompt.split()) + (request.max_tokens or 100)
        return base_cost * estimated_tokens
        
    async def get_provider_metrics(
        self,
        provider_name: str,
        time_period: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get provider performance metrics."""
        await self._mock.get_provider_metrics(provider_name, time_period)
        
        return {
            "provider_name": provider_name,
            "requests_count": 100,
            "average_response_time": 150.0,
            "error_rate": 0.02 if not self._should_fail else 0.25,
            "total_tokens": 50000,
            "total_cost": 50.0
        }
        
    async def configure_fallback_strategy(
        self,
        primary_provider: str,
        fallback_providers: List[str]
    ) -> None:
        """Configure fallback strategy for provider failures."""
        await self._mock.configure_fallback_strategy(primary_provider, fallback_providers)
        
        # Mock configuration - just track the call
        pass
        
    async def execute_with_retry(
        self,
        request: RequestContext,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> LLMResponse:
        """Execute request with retry logic."""
        await self._mock.execute_with_retry(request, max_retries, retry_delay)
        
        # For mock, just delegate to regular execute_llm_request
        return await self.execute_llm_request(request)
        
    async def batch_execute_requests(
        self,
        requests: List[RequestContext],
        strategy: Optional[ProviderSelectionStrategy] = None
    ) -> List[LLMResponse]:
        """Execute multiple requests in batch."""
        await self._mock.batch_execute_requests(requests, strategy)
        
        responses = []
        for request in requests:
            response = await self.execute_llm_request(request, strategy)
            responses.append(response)
            
        return responses
