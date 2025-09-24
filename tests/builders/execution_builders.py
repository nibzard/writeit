"""Test data builders for Execution domain entities."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Self

from src.writeit.domains.execution.entities.llm_provider import LLMProvider, ProviderType
from src.writeit.domains.execution.entities.execution_context import ExecutionContext
from src.writeit.domains.execution.entities.token_usage import TokenUsage
from src.writeit.domains.execution.value_objects.model_name import ModelName
from src.writeit.domains.execution.value_objects.token_count import TokenCount
from src.writeit.domains.execution.value_objects.cache_key import CacheKey
from src.writeit.domains.execution.value_objects.execution_mode import ExecutionMode


class LLMProviderBuilder:
    """Builder for LLMProvider test data."""
    
    def __init__(self) -> None:
        self._provider_name = "test_provider"
        self._provider_type = ProviderType.OPENAI
        self._api_key = "test_api_key"
        self._api_base_url = "https://api.openai.com/v1"
        self._supported_models = [ModelName("gpt-4o-mini"), ModelName("gpt-4o")]
        self._default_model = ModelName("gpt-4o-mini")
        self._rate_limits = {}
        self._configuration = {}
        self._is_active = True
        self._health_status = "healthy"
        self._metadata = {}
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._last_used = None
    
    def with_name(self, name: str) -> Self:
        """Set the provider name."""
        self._provider_name = name
        return self
    
    def with_type(self, provider_type: str | ProviderType) -> Self:
        """Set the provider type."""
        if isinstance(provider_type, str):
            # Convert string to ProviderType enum (enum values are lowercase)
            provider_type = ProviderType(provider_type.lower())
        self._provider_type = provider_type
        return self
    
    def with_api_key(self, api_key: str) -> Self:
        """Set the API key."""
        self._api_key = api_key
        return self
    
    def with_api_base_url(self, base_url: str) -> Self:
        """Set the API base URL."""
        self._api_base_url = base_url
        return self
    
    def with_supported_models(self, models: List[str | ModelName]) -> Self:
        """Set the supported models."""
        model_names = []
        for model in models:
            if isinstance(model, str):
                model = ModelName(model)
            model_names.append(model)
        self._supported_models = model_names
        return self
    
    def with_default_model(self, model: str | ModelName) -> Self:
        """Set the default model."""
        if isinstance(model, str):
            model = ModelName(model)
        self._default_model = model
        return self
    
    def with_rate_limits(self, limits: Dict[str, Any]) -> Self:
        """Set the rate limits."""
        self._rate_limits = limits
        return self
    
    def with_configuration(self, config: Dict[str, Any]) -> Self:
        """Set the configuration."""
        self._configuration = config
        return self
    
    def active(self) -> Self:
        """Mark the provider as active."""
        self._is_active = True
        return self
    
    def inactive(self) -> Self:
        """Mark the provider as inactive."""
        self._is_active = False
        return self
    
    def with_health_status(self, status: str) -> Self:
        """Set the health status."""
        self._health_status = status
        return self
    
    def healthy(self) -> Self:
        """Mark the provider as healthy."""
        self._health_status = "healthy"
        return self
    
    def unhealthy(self, reason: str = "connection_error") -> Self:
        """Mark the provider as unhealthy."""
        self._health_status = f"unhealthy: {reason}"
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata
        return self
    
    def recently_used(self) -> Self:
        """Mark the provider as recently used."""
        self._last_used = datetime.now()
        return self
    
    def build(self) -> LLMProvider:
        """Build the LLMProvider."""
        from src.writeit.domains.execution.entities.llm_provider import ProviderStatus
        
        # Map internal fields to entity constructor
        return LLMProvider(
            name=self._provider_name,
            provider_type=self._provider_type,
            status=ProviderStatus.ACTIVE if self._is_active else ProviderStatus.INACTIVE,
            api_key_ref=self._api_key,
            base_url=self._api_base_url,
            supported_models=self._supported_models,
            rate_limits=self._rate_limits,
            created_at=self._created_at,
            updated_at=self._updated_at,
            metadata=self._metadata
        )
    
    @classmethod
    def openai(cls, name: str = "openai_test") -> Self:
        """Create an OpenAI provider builder."""
        return (cls()
                .with_name(name)
                .with_type("openai")
                .with_api_base_url("https://api.openai.com/v1")
                .with_supported_models(["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
                .with_default_model("gpt-4o-mini")
                .with_rate_limits({
                    "requests_per_minute": 3000,
                    "tokens_per_minute": 250000
                }))
    
    @classmethod
    def anthropic(cls, name: str = "anthropic_test") -> Self:
        """Create an Anthropic provider builder."""
        return (cls()
                .with_name(name)
                .with_type("anthropic")
                .with_api_base_url("https://api.anthropic.com/v1")
                .with_supported_models(["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"])
                .with_default_model("claude-3-haiku")
                .with_rate_limits({
                    "requests_per_minute": 1000,
                    "tokens_per_minute": 100000
                }))
    
    @classmethod
    def local(cls, name: str = "local_test") -> Self:
        """Create a local provider builder."""
        return (cls()
                .with_name(name)
                .with_type("local")
                .with_api_base_url("http://localhost:8080")
                .with_supported_models(["llama2", "codellama"])
                .with_default_model("llama2")
                .with_rate_limits({}))
    
    @classmethod
    def mock_provider(cls, name: str = "mock_test") -> Self:
        """Create a mock provider builder."""
        return (cls()
                .with_name(name)
                .with_type("mock")
                .with_api_base_url("http://mock.test")
                .with_supported_models(["mock-model"])
                .with_default_model("mock-model")
                .with_rate_limits({}))


class ExecutionContextBuilder:
    """Builder for ExecutionContext test data."""
    
    def __init__(self) -> None:
        self._context_id = "test_context"
        self._execution_mode = ExecutionMode.cli()
        self._workspace_name = "test_workspace"
        self._pipeline_run_id = "test_run"
        self._step_id = None
        self._user_inputs = {}
        self._step_outputs = {}
        self._environment_variables = {}
        self._session_data = {}
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_context_id(self, context_id: str) -> Self:
        """Set the context ID."""
        self._context_id = context_id
        return self
    
    def with_execution_mode(self, mode: ExecutionMode) -> Self:
        """Set the execution mode."""
        self._execution_mode = mode
        return self
    
    def cli_mode(self) -> Self:
        """Set CLI execution mode."""
        self._execution_mode = ExecutionMode.cli()
        return self
    
    def tui_mode(self) -> Self:
        """Set TUI execution mode."""
        self._execution_mode = ExecutionMode.tui()
        return self
    
    def server_mode(self) -> Self:
        """Set server execution mode."""
        self._execution_mode = ExecutionMode.server()
        return self
    
    def with_workspace(self, workspace_name: str) -> Self:
        """Set the workspace name."""
        self._workspace_name = workspace_name
        return self
    
    def with_pipeline_run_id(self, run_id: str) -> Self:
        """Set the pipeline run ID."""
        self._pipeline_run_id = run_id
        return self
    
    def with_step_id(self, step_id: str) -> Self:
        """Set the current step ID."""
        self._step_id = step_id
        return self
    
    def with_user_inputs(self, inputs: Dict[str, Any]) -> Self:
        """Set the user inputs."""
        self._user_inputs = inputs
        return self
    
    def with_step_outputs(self, outputs: Dict[str, Any]) -> Self:
        """Set the step outputs."""
        self._step_outputs = outputs
        return self
    
    def with_environment_variables(self, env_vars: Dict[str, str]) -> Self:
        """Set the environment variables."""
        self._environment_variables = env_vars
        return self
    
    def with_session_data(self, session_data: Dict[str, Any]) -> Self:
        """Set the session data."""
        self._session_data = session_data
        return self
    
    def build(self) -> ExecutionContext:
        """Build the ExecutionContext."""
        return ExecutionContext(
            id=self._context_id,
            workspace_name=self._workspace_name,
            pipeline_id=self._pipeline_run_id or "test-pipeline",
            execution_mode=self._execution_mode
        )
    
    @classmethod
    def cli_context(cls, context_id: str = "cli_context") -> Self:
        """Create a CLI execution context."""
        return (cls()
                .with_context_id(context_id)
                .cli_mode()
                .with_environment_variables({
                    "WRITEIT_MODE": "cli",
                    "TERM": "xterm-256color"
                }))
    
    @classmethod
    def tui_context(cls, context_id: str = "tui_context") -> Self:
        """Create a TUI execution context."""
        return (cls()
                .with_context_id(context_id)
                .tui_mode()
                .with_session_data({
                    "terminal_size": {"width": 120, "height": 40},
                    "theme": "dark"
                }))
    
    @classmethod
    def server_context(cls, context_id: str = "server_context") -> Self:
        """Create a server execution context."""
        return (cls()
                .with_context_id(context_id)
                .server_mode()
                .with_session_data({
                    "client_ip": "127.0.0.1",
                    "user_agent": "WriteIt-Client/1.0"
                }))
    
    @classmethod
    def with_pipeline_execution(cls, run_id: str, step_id: str = "current_step") -> Self:
        """Create a context for pipeline execution."""
        return (cls()
                .with_pipeline_run_id(run_id)
                .with_step_id(step_id)
                .with_user_inputs({"topic": "test topic"})
                .with_step_outputs({"previous": "previous output"}))


class TokenUsageBuilder:
    """Builder for TokenUsage test data."""
    
    def __init__(self) -> None:
        self._provider_name = "test_provider"
        self._model_name = "test_model"
        self._prompt_tokens = 100
        self._completion_tokens = 50
        self._total_tokens = 150
        self._cost_estimate = 0.001
        self._request_id = "test_request"
        self._context_id = "test_context"
        self._workspace_name = "test_workspace"
        self._pipeline_run_id = None
        self._step_id = None
        self._metadata = {}
        self._timestamp = datetime.now()
    
    def with_provider_name(self, provider_name: str) -> Self:
        """Set the provider name."""
        self._provider_name = provider_name
        return self
    
    def with_model_name(self, model_name: str | ModelName) -> Self:
        """Set the model name."""
        if isinstance(model_name, ModelName):
            self._model_name = str(model_name)
        else:
            self._model_name = model_name
        return self
    
    def with_token_counts(self, prompt: int, completion: int) -> Self:
        """Set the token counts."""
        self._prompt_tokens = prompt
        self._completion_tokens = completion
        self._total_tokens = prompt + completion
        return self
    
    def with_cost_estimate(self, cost: float) -> Self:
        """Set the cost estimate."""
        self._cost_estimate = cost
        return self
    
    def with_request_id(self, request_id: str) -> Self:
        """Set the request ID."""
        self._request_id = request_id
        return self
    
    def with_context_id(self, context_id: str) -> Self:
        """Set the context ID."""
        self._context_id = context_id
        return self
    
    def with_workspace(self, workspace_name: str) -> Self:
        """Set the workspace name."""
        self._workspace_name = workspace_name
        return self
    
    def with_pipeline_execution(self, run_id: str, step_id: str) -> Self:
        """Set pipeline execution info."""
        self._pipeline_run_id = run_id
        self._step_id = step_id
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata
        return self
    
    def with_timestamp(self, timestamp: datetime) -> Self:
        """Set the timestamp."""
        self._timestamp = timestamp
        return self
    
    def build(self) -> TokenUsage:
        """Build the TokenUsage."""
        import uuid
        from src.writeit.domains.execution.entities.token_usage import (
            TokenMetrics, CostBreakdown, UsageType, UsageCategory
        )
        from src.writeit.domains.execution.value_objects.model_name import ModelName
        
        # Create TokenMetrics from individual token counts
        token_metrics = TokenMetrics(
            input_tokens=self._prompt_tokens,
            output_tokens=self._completion_tokens, 
            total_tokens=self._total_tokens
        )
        
        # Create CostBreakdown  
        from decimal import Decimal
        cost_breakdown = CostBreakdown(total_cost=Decimal(str(self._cost_estimate)))
        
        return TokenUsage(
            id=str(uuid.uuid4()),
            session_id=self._context_id or str(uuid.uuid4()),
            model_name=ModelName.from_string(self._model_name),
            workspace_name=self._workspace_name,
            pipeline_id=self._pipeline_run_id,
            step_id=self._step_id,
            usage_type=UsageType.TOTAL,
            usage_category=UsageCategory.PIPELINE_EXECUTION,
            token_metrics=token_metrics,
            cost_breakdown=cost_breakdown,
            timestamp=self._timestamp,
            request_id=self._request_id,
            metadata=self._metadata
        )
    
    @classmethod
    def small_request(cls, provider: str = "openai", model: str = "gpt-4o-mini") -> Self:
        """Create a small token usage record."""
        if not model or not model.strip():
            model = "gpt-4o-mini"
        return (cls()
                .with_provider_name(provider)
                .with_model_name(model)
                .with_token_counts(50, 25)
                .with_cost_estimate(0.0001))
    
    @classmethod
    def medium_request(cls, provider: str = "openai", model: str = "gpt-4o") -> Self:
        """Create a medium token usage record."""
        return (cls()
                .with_provider_name(provider)
                .with_model_name(model)
                .with_token_counts(500, 250)
                .with_cost_estimate(0.001))
    
    @classmethod
    def large_request(cls, provider: str = "anthropic", model: str = "claude-3-opus") -> Self:
        """Create a large token usage record."""
        return (cls()
                .with_provider_name(provider)
                .with_model_name(model)
                .with_token_counts(2000, 1000)
                .with_cost_estimate(0.01))
    
    @classmethod
    def pipeline_step_usage(cls, run_id: str, step_id: str) -> Self:
        """Create usage for a pipeline step."""
        return (cls()
                .with_provider_name("openai")
                .with_model_name("gpt-4o-mini")
                .with_token_counts(200, 100)
                .with_cost_estimate(0.0005)
                .with_pipeline_execution(run_id, step_id)
                .with_metadata({
                    "step_type": "llm_generate",
                    "execution_time_ms": 1500
                }))
    
    @classmethod
    def batch_usage(cls, count: int = 5) -> List[Self]:
        """Create a batch of token usage records."""
        return [
            cls.small_request().with_request_id(f"req_{i}")
            for i in range(count)
        ]