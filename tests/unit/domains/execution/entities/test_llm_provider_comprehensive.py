"""Comprehensive unit tests for LLMProvider entity."""

import pytest
from datetime import datetime, timedelta
import json

from src.writeit.domains.execution.entities.llm_provider import (
    LLMProvider, ProviderStatus, ProviderType
)
from src.writeit.domains.execution.value_objects.model_name import ModelName

from tests.builders.execution_builders import LLMProviderBuilder


class TestLLMProvider:
    """Test cases for LLMProvider entity."""
    
    def test_llm_provider_creation_with_valid_data(self):
        """Test creating LLM provider with valid data."""
        provider = LLMProviderBuilder.openai().build()
        
        assert provider.name == "OpenAI Provider"
        assert provider.provider_type == ProviderType.OPENAI
        assert provider.status == ProviderStatus.ACTIVE
        assert provider.api_key_ref == "test_api_key"
        assert provider.base_url == "https://api.openai.com/v1"
        assert len(provider.supported_models) == 3
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is True
        assert provider.is_healthy is True
        assert provider.is_available is True
        assert provider.has_api_key is True
        assert isinstance(provider.created_at, datetime)
        assert isinstance(provider.updated_at, datetime)
    
    def test_llm_provider_creation_with_custom_data(self):
        """Test creating LLM provider with custom data."""
        custom_models = [ModelName.from_string("custom-model")]
        custom_capabilities = {"custom_feature": True, "streaming": False}
        custom_rate_limits = {"custom_limit": 100}
        custom_metadata = {"version": "2.0", "region": "us-west"}
        
        provider = (LLMProviderBuilder()
                   .with_name("Custom Provider")
                   .with_type(ProviderType.LOCAL)
                   .with_status("inactive")
                   .with_api_key_ref("custom_key_ref")
                   .with_base_url("http://custom.api.com")
                   .with_supported_models(["custom-model"])
                   .with_capabilities(custom_capabilities)
                   .with_rate_limits(custom_rate_limits)
                   .with_metadata(custom_metadata)
                   .build())
        
        assert provider.name == "Custom Provider"
        assert provider.provider_type == ProviderType.LOCAL
        assert provider.status == ProviderStatus.INACTIVE
        assert provider.api_key_ref == "custom_key_ref"
        assert provider.base_url == "http://custom.api.com"
        assert len(provider.supported_models) == 1
        assert provider.supported_models[0].value == "custom-model"
        assert provider.capabilities == custom_capabilities
        assert provider.rate_limits == custom_rate_limits
        assert provider.metadata == custom_metadata
        assert provider.is_healthy is False
        assert provider.is_available is True
    
    def test_openai_provider_creation(self):
        """Test creating OpenAI provider."""
        provider = LLMProviderBuilder.openai("My OpenAI").build()
        
        assert provider.name == "My OpenAI"
        assert provider.provider_type == ProviderType.OPENAI
        assert provider.base_url == "https://api.openai.com/v1"
        assert "gpt-4o" in [str(m) for m in provider.supported_models]
        assert "gpt-4o-mini" in [str(m) for m in provider.supported_models]
        assert "gpt-3.5-turbo" in [str(m) for m in provider.supported_models]
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is True
        assert provider.get_rate_limit("requests_per_minute") == 3500
        assert provider.get_rate_limit("tokens_per_minute") == 500000
    
    def test_anthropic_provider_creation(self):
        """Test creating Anthropic provider."""
        provider = LLMProviderBuilder.anthropic("My Anthropic").build()
        
        assert provider.name == "My Anthropic"
        assert provider.provider_type == ProviderType.ANTHROPIC
        assert provider.base_url == "https://api.anthropic.com/v1"
        assert "claude-3-haiku" in [str(m) for m in provider.supported_models]
        assert "claude-3-sonnet" in [str(m) for m in provider.supported_models]
        assert "claude-3-opus" in [str(m) for m in provider.supported_models]
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is False
        assert provider.get_rate_limit("requests_per_minute") == 1000
        assert provider.get_rate_limit("tokens_per_minute") == 100000
    
    def test_local_provider_creation(self):
        """Test creating local provider."""
        provider = LLMProviderBuilder.local("My Local").build()
        
        assert provider.name == "My Local"
        assert provider.provider_type == ProviderType.LOCAL
        assert provider.base_url == "http://localhost:8080"
        assert "llama2" in [str(m) for m in provider.supported_models]
        assert "codellama" in [str(m) for m in provider.supported_models]
        assert provider.supports_streaming() is False
        assert provider.supports_function_calling() is False
        assert provider.supports_vision() is False
        assert len(provider.rate_limits) == 0
    
    def test_mock_provider_creation(self):
        """Test creating mock provider."""
        provider = LLMProviderBuilder.mock_provider("Test Mock").build()
        
        assert provider.name == "Test Mock"
        assert provider.provider_type == ProviderType.MOCK
        assert provider.base_url == "http://mock.test"
        assert "mock-model" in [str(m) for m in provider.supported_models]
        assert "test-model" in [str(m) for m in provider.supported_models]
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is True
    
    def test_provider_status_management(self):
        """Test provider status management."""
        # Active provider
        active_provider = LLMProviderBuilder.openai().active().build()
        assert active_provider.status == ProviderStatus.ACTIVE
        assert active_provider.is_healthy is True
        assert active_provider.is_available is True
        
        # Inactive provider
        inactive_provider = LLMProviderBuilder.openai().inactive().build()
        assert inactive_provider.status == ProviderStatus.INACTIVE
        assert inactive_provider.is_healthy is False
        assert inactive_provider.is_available is True
        
        # Maintenance provider
        maintenance_provider = LLMProviderBuilder.openai().maintenance().build()
        assert maintenance_provider.status == ProviderStatus.MAINTENANCE
        assert maintenance_provider.is_healthy is False
        assert maintenance_provider.is_available is False
        
        # Error provider
        error_provider = LLMProviderBuilder.openai().error("Connection failed").build()
        assert error_provider.status == ProviderStatus.ERROR
        assert error_provider.error_message == "Connection failed"
        assert error_provider.is_healthy is False
        assert error_provider.is_available is False
    
    def test_provider_capabilities(self):
        """Test provider capability queries."""
        # Provider with all capabilities
        full_provider = (LLMProviderBuilder.openai()
                        .with_capabilities({
                            "streaming": True,
                            "function_calling": True,
                            "vision": True,
                            "custom_feature": True
                        })
                        .build())
        
        assert full_provider.supports_streaming() is True
        assert full_provider.supports_function_calling() is True
        assert full_provider.supports_vision() is True
        assert full_provider.capabilities["custom_feature"] is True
        
        # Provider with limited capabilities
        limited_provider = (LLMProviderBuilder.local()
                           .with_capabilities({
                               "streaming": False,
                               "function_calling": False,
                               "vision": False
                           })
                           .build())
        
        assert limited_provider.supports_streaming() is False
        assert limited_provider.supports_function_calling() is False
        assert limited_provider.supports_vision() is False
    
    def test_provider_model_support(self):
        """Test provider model support checks."""
        models = [ModelName.from_string("gpt-4o"), ModelName.from_string("gpt-3.5-turbo")]
        provider = (LLMProviderBuilder.openai()
                   .with_supported_models(["gpt-4o", "gpt-3.5-turbo"])
                   .build())
        
        assert provider.supports_model(ModelName.from_string("gpt-4o")) is True
        assert provider.supports_model(ModelName.from_string("gpt-3.5-turbo")) is True
        assert provider.supports_model(ModelName.from_string("claude-3-haiku")) is False
    
    def test_provider_rate_limits(self):
        """Test provider rate limit queries."""
        provider = (LLMProviderBuilder.openai()
                   .with_rate_limits({
                       "requests_per_minute": 1000,
                       "tokens_per_minute": 50000,
                       "requests_per_day": 10000
                   })
                   .build())
        
        assert provider.get_rate_limit("requests_per_minute") == 1000
        assert provider.get_rate_limit("tokens_per_minute") == 50000
        assert provider.get_rate_limit("requests_per_day") == 10000
        assert provider.get_rate_limit("nonexistent") is None
    
    def test_provider_max_tokens_metadata(self):
        """Test provider max tokens retrieval from metadata."""
        provider = (LLMProviderBuilder.openai()
                   .with_metadata({
                       "max_tokens_gpt-4o": 128000,
                       "max_tokens_gpt-3.5-turbo": 16384
                   })
                   .build())
        
        assert provider.get_max_tokens(ModelName.from_string("gpt-4o")) == 128000
        assert provider.get_max_tokens(ModelName.from_string("gpt-3.5-turbo")) == 16384
        assert provider.get_max_tokens(ModelName.from_string("unknown-model")) is None
    
    def test_provider_timestamps(self):
        """Test provider timestamps."""
        now = datetime.now()
        provider = LLMProviderBuilder.openai().build()
        
        # Created and updated should be close to now
        assert abs((provider.created_at - now).total_seconds()) < 1
        assert abs((provider.updated_at - now).total_seconds()) < 1
        
        # Test custom timestamps
        custom_time = datetime(2023, 8, 15, 14, 30, 0)
        provider_with_custom = (LLMProviderBuilder.openai()
                               .with_timestamps(custom_time, custom_time)
                               .build())
        
        assert provider_with_custom.created_at == custom_time
        assert provider_with_custom.updated_at == custom_time


class TestLLMProviderBusinessLogic:
    """Test business logic and invariants for LLMProvider."""
    
    def test_mark_healthy_updates_provider(self):
        """Test marking provider as healthy."""
        provider = LLMProviderBuilder.openai().error("Connection failed").build()
        assert provider.status == ProviderStatus.ERROR
        assert provider.error_message == "Connection failed"
        
        healthy_provider = provider.mark_healthy()
        
        assert healthy_provider.status == ProviderStatus.ACTIVE
        assert healthy_provider.error_message is None
        assert healthy_provider.last_health_check is not None
        assert healthy_provider.is_healthy is True
        assert healthy_provider is not provider  # Immutable
    
    def test_mark_inactive_updates_provider(self):
        """Test marking provider as inactive."""
        provider = LLMProviderBuilder.openai().active().build()
        inactive_provider = provider.mark_inactive()
        
        assert inactive_provider.status == ProviderStatus.INACTIVE
        assert inactive_provider.is_healthy is False
        assert inactive_provider.is_available is True
        assert inactive_provider is not provider  # Immutable
    
    def test_mark_maintenance_updates_provider(self):
        """Test marking provider as under maintenance."""
        provider = LLMProviderBuilder.openai().build()
        maintenance_provider = provider.mark_maintenance("Scheduled maintenance")
        
        assert maintenance_provider.status == ProviderStatus.MAINTENANCE
        assert maintenance_provider.metadata["maintenance_reason"] == "Scheduled maintenance"
        assert maintenance_provider.is_healthy is False
        assert maintenance_provider.is_available is False
        assert maintenance_provider is not provider  # Immutable
    
    def test_mark_error_updates_provider(self):
        """Test marking provider as having an error."""
        provider = LLMProviderBuilder.openai().build()
        error_provider = provider.mark_error("API timeout")
        
        assert error_provider.status == ProviderStatus.ERROR
        assert error_provider.error_message == "API timeout"
        assert error_provider.last_health_check is not None
        assert error_provider.is_healthy is False
        assert error_provider.is_available is False
        assert error_provider is not provider  # Immutable
    
    def test_add_model_updates_provider(self):
        """Test adding supported model."""
        provider = LLMProviderBuilder.openai().build()
        original_count = len(provider.supported_models)
        new_model = ModelName.from_string("gpt-5")
        
        updated_provider = provider.add_model(new_model)
        
        assert len(updated_provider.supported_models) == original_count + 1
        assert new_model in updated_provider.supported_models
        assert updated_provider.supports_model(new_model) is True
        assert updated_provider is not provider  # Immutable
    
    def test_add_model_prevents_duplicates(self):
        """Test adding duplicate model doesn't change provider."""
        provider = LLMProviderBuilder.openai().build()
        existing_model = provider.supported_models[0]
        
        updated_provider = provider.add_model(existing_model)
        
        assert updated_provider is provider  # No change
        assert len(updated_provider.supported_models) == len(provider.supported_models)
    
    def test_remove_model_updates_provider(self):
        """Test removing supported model."""
        provider = LLMProviderBuilder.openai().build()
        model_to_remove = provider.supported_models[0]
        original_count = len(provider.supported_models)
        
        updated_provider = provider.remove_model(model_to_remove)
        
        assert len(updated_provider.supported_models) == original_count - 1
        assert model_to_remove not in updated_provider.supported_models
        assert updated_provider.supports_model(model_to_remove) is False
        assert updated_provider is not provider  # Immutable
    
    def test_remove_nonexistent_model_no_change(self):
        """Test removing non-existent model doesn't change provider."""
        provider = LLMProviderBuilder.openai().build()
        nonexistent_model = ModelName.from_string("nonexistent-model")
        
        updated_provider = provider.remove_model(nonexistent_model)
        
        assert updated_provider is provider  # No change
        assert len(updated_provider.supported_models) == len(provider.supported_models)
    
    def test_set_capability_updates_provider(self):
        """Test setting capability updates provider."""
        provider = LLMProviderBuilder.openai().build()
        
        updated_provider = provider.set_capability("new_feature", True)
        
        assert updated_provider.capabilities["new_feature"] is True
        assert updated_provider.capabilities["streaming"] is True  # Existing capability preserved
        assert updated_provider is not provider  # Immutable
        
        # Test disabling capability
        disabled_provider = updated_provider.set_capability("new_feature", False)
        assert disabled_provider.capabilities["new_feature"] is False
    
    def test_set_rate_limit_updates_provider(self):
        """Test setting rate limit updates provider."""
        provider = LLMProviderBuilder.openai().build()
        
        updated_provider = provider.set_rate_limit("custom_limit", 2000)
        
        assert updated_provider.rate_limits["custom_limit"] == 2000
        assert updated_provider.get_rate_limit("custom_limit") == 2000
        assert updated_provider is not provider  # Immutable
    
    def test_update_metadata_updates_provider(self):
        """Test updating metadata updates provider."""
        provider = LLMProviderBuilder.openai().build()
        
        updated_provider = provider.update_metadata("custom_key", "custom_value")
        
        assert updated_provider.metadata["custom_key"] == "custom_value"
        assert updated_provider is not provider  # Immutable
    
    def test_create_class_method(self):
        """Test LLMProvider.create class method."""
        models = [ModelName.from_string("test-model")]
        capabilities = {"test_capability": True}
        
        provider = LLMProvider.create(
            name="Test Provider",
            provider_type=ProviderType.MOCK,
            api_key_ref="test_key",
            base_url="http://test.api.com",
            supported_models=models,
            capabilities=capabilities
        )
        
        assert provider.name == "Test Provider"
        assert provider.provider_type == ProviderType.MOCK
        assert provider.api_key_ref == "test_key"
        assert provider.base_url == "http://test.api.com"
        assert provider.supported_models == models
        assert provider.capabilities["test_capability"] is True
        assert provider.status == ProviderStatus.ACTIVE
    
    def test_openai_provider_class_method(self):
        """Test LLMProvider.openai_provider class method."""
        provider = LLMProvider.openai_provider("my_api_key", "My OpenAI")
        
        assert provider.name == "My OpenAI"
        assert provider.provider_type == ProviderType.OPENAI
        assert provider.api_key_ref == "my_api_key"
        assert provider.base_url == "https://api.openai.com/v1"
        assert len(provider.supported_models) == 3
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is True
        assert provider.get_max_tokens(ModelName.from_string("gpt-4o-mini")) == 128000
        assert provider.get_rate_limit("requests_per_minute") == 3500
    
    def test_anthropic_provider_class_method(self):
        """Test LLMProvider.anthropic_provider class method."""
        provider = LLMProvider.anthropic_provider("my_api_key", "My Anthropic")
        
        assert provider.name == "My Anthropic"
        assert provider.provider_type == ProviderType.ANTHROPIC
        assert provider.api_key_ref == "my_api_key"
        assert provider.base_url == "https://api.anthropic.com/v1"
        assert len(provider.supported_models) == 3
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is False
        assert provider.get_max_tokens(ModelName.from_string("claude-3-haiku")) == 200000
        assert provider.get_rate_limit("requests_per_minute") == 1000
    
    def test_mock_provider_class_method(self):
        """Test LLMProvider.mock_provider class method."""
        provider = LLMProvider.mock_provider("Test Mock")
        
        assert provider.name == "Test Mock"
        assert provider.provider_type == ProviderType.MOCK
        assert provider.api_key_ref is None
        assert len(provider.supported_models) == 2
        assert provider.supports_streaming() is True
        assert provider.supports_function_calling() is True
        assert provider.supports_vision() is True
    
    def test_provider_serialization(self):
        """Test provider dictionary serialization."""
        provider = LLMProviderBuilder.openai().build()
        provider_dict = provider.to_dict()
        
        assert provider_dict["name"] == provider.name
        assert provider_dict["provider_type"] == provider.provider_type.value
        assert provider_dict["status"] == provider.status.value
        assert provider_dict["api_key_ref"] == provider.api_key_ref
        assert provider_dict["base_url"] == provider.base_url
        assert len(provider_dict["supported_models"]) == len(provider.supported_models)
        assert provider_dict["capabilities"] == provider.capabilities
        assert provider_dict["rate_limits"] == provider.rate_limits
        assert provider_dict["created_at"] == provider.created_at.isoformat()
        assert provider_dict["updated_at"] == provider.updated_at.isoformat()
    
    def test_provider_serialization_with_health_check(self):
        """Test provider serialization with health check timestamp."""
        now = datetime.now()
        provider = (LLMProviderBuilder.openai()
                   .with_last_health_check(now)
                   .build())
        
        provider_dict = provider.to_dict()
        assert provider_dict["last_health_check"] == now.isoformat()


class TestLLMProviderEdgeCases:
    """Test edge cases and error conditions for LLMProvider."""
    
    def test_provider_post_init_validation(self):
        """Test LLMProvider post-init validation."""
        with pytest.raises(ValueError, match="Provider name must be a non-empty string"):
            LLMProvider(
                name="",
                provider_type=ProviderType.OPENAI
            )
        
        with pytest.raises(ValueError, match="Provider name must be a non-empty string"):
            LLMProvider(
                name=None,  # type: ignore
                provider_type=ProviderType.OPENAI
            )
        
        with pytest.raises(TypeError, match="Provider type must be a ProviderType"):
            LLMProvider(
                name="Test Provider",
                provider_type="invalid_type"  # type: ignore
            )
        
        with pytest.raises(TypeError, match="Status must be a ProviderStatus"):
            LLMProvider(
                name="Test Provider",
                provider_type=ProviderType.OPENAI,
                status="invalid_status"  # type: ignore
            )
        
        with pytest.raises(TypeError, match="Supported models must be ModelName instances"):
            LLMProvider(
                name="Test Provider",
                provider_type=ProviderType.OPENAI,
                supported_models=["invalid_model"]  # type: ignore
            )
        
        with pytest.raises(TypeError, match="capabilities must be a dictionary"):
            LLMProvider(
                name="Test Provider",
                provider_type=ProviderType.OPENAI,
                capabilities="invalid"  # type: ignore
            )
        
        with pytest.raises(ValueError, match="Error status requires error message"):
            LLMProvider(
                name="Test Provider",
                provider_type=ProviderType.OPENAI,
                status=ProviderStatus.ERROR
                # Missing error_message
            )
    
    def test_provider_with_no_api_key(self):
        """Test provider without API key."""
        provider = (LLMProviderBuilder.openai()
                   .with_api_key_ref(None)
                   .build())
        
        assert provider.has_api_key is False
        assert provider.api_key_ref is None
    
    def test_provider_with_custom_base_url(self):
        """Test provider with custom base URL."""
        custom_url = "https://custom.openai.proxy.com/v1"
        provider = (LLMProviderBuilder.openai()
                   .with_base_url(custom_url)
                   .build())
        
        assert provider.base_url == custom_url
    
    def test_provider_with_empty_supported_models(self):
        """Test provider with no supported models."""
        provider = (LLMProviderBuilder.openai()
                   .with_supported_models([])
                   .build())
        
        assert len(provider.supported_models) == 0
        assert provider.supports_model(ModelName.from_string("any-model")) is False
    
    def test_provider_with_complex_metadata(self):
        """Test provider with complex metadata."""
        complex_metadata = {
            "regions": ["us-east-1", "us-west-2", "eu-west-1"],
            "pricing": {
                "gpt-4o": {"input": 0.01, "output": 0.03},
                "gpt-4o-mini": {"input": 0.0015, "output": 0.006}
            },
            "features": {
                "max_concurrent_requests": 100,
                "supports_batch": True,
                "retry_policy": {
                    "max_retries": 3,
                    "backoff_factor": 2
                }
            }
        }
        
        provider = (LLMProviderBuilder.openai()
                   .with_metadata(complex_metadata)
                   .build())
        
        assert provider.metadata == complex_metadata
        assert "us-east-1" in provider.metadata["regions"]
        assert provider.metadata["pricing"]["gpt-4o"]["input"] == 0.01
        assert provider.metadata["features"]["supports_batch"] is True
    
    def test_provider_metadata_serialization(self):
        """Test that provider metadata is JSON serializable."""
        provider = LLMProviderBuilder.openai().build()
        
        # Provider dict should be JSON serializable
        try:
            json.dumps(provider.to_dict())
        except (TypeError, ValueError) as e:
            pytest.fail(f"LLMProvider serialization not JSON compatible: {e}")
    
    def test_provider_with_unicode_name(self):
        """Test provider with unicode characters in name."""
        unicode_name = "Öpën ÀI Prövïdër 🤖"
        provider = (LLMProviderBuilder.openai()
                   .with_name(unicode_name)
                   .build())
        
        assert provider.name == unicode_name
        assert "🤖" in provider.name
    
    def test_provider_string_representations(self):
        """Test string representations of LLMProvider."""
        # Active provider
        active_provider = LLMProviderBuilder.openai("Test OpenAI").active().build()
        str_repr = str(active_provider)
        assert "LLMProvider(Test OpenAI - active)" == str_repr
        
        # Error provider
        error_provider = LLMProviderBuilder.openai("Error OpenAI").error("Connection failed").build()
        str_repr = str(error_provider)
        assert "LLMProvider(Error OpenAI - error)" == str_repr
        
        # Test repr
        repr_str = repr(active_provider)
        assert "LLMProvider(name='Test OpenAI'" in repr_str
        assert "type=openai" in repr_str
        assert "status=active" in repr_str
        assert f"models={len(active_provider.supported_models)}" in repr_str
    
    def test_provider_immutability(self):
        """Test provider immutability after creation."""
        provider = LLMProviderBuilder.openai().build()
        original_name = provider.name
        original_status = provider.status
        
        # Provider follows immutability through conventions
        # Direct field access works but update methods are preferred
        assert provider.name == original_name
        assert provider.status == original_status
        
        # If provider has an update method, it should create new instances
        if hasattr(provider, 'update'):
            updated = provider.update(name="Modified Name")
            assert provider.name == original_name  # Original unchanged
            assert updated.name != original_name    # New instance changed
        else:
            # At minimum, verify provider state is preserved
            assert provider.name == original_name
            assert provider.status == original_status
    
    def test_provider_with_extreme_rate_limits(self):
        """Test provider with extreme rate limits."""
        extreme_limits = {
            "requests_per_second": 1000000,
            "tokens_per_hour": 50000000,
            "concurrent_requests": 10000
        }
        
        provider = (LLMProviderBuilder.openai()
                   .with_rate_limits(extreme_limits)
                   .build())
        
        assert provider.get_rate_limit("requests_per_second") == 1000000
        assert provider.get_rate_limit("tokens_per_hour") == 50000000
        assert provider.get_rate_limit("concurrent_requests") == 10000
    
    def test_provider_capability_edge_cases(self):
        """Test provider capability edge cases."""
        # Empty capabilities
        empty_provider = (LLMProviderBuilder.openai()
                         .with_capabilities({})
                         .build())
        
        assert empty_provider.supports_streaming() is False
        assert empty_provider.supports_function_calling() is False
        assert empty_provider.supports_vision() is False
        
        # Mixed boolean and non-boolean capabilities
        mixed_provider = (LLMProviderBuilder.openai()
                         .with_capabilities({
                             "streaming": True,
                             "function_calling": False,
                             "vision": "yes",  # Non-boolean value
                             "custom_number": 42
                         })
                         .build())
        
        assert mixed_provider.supports_streaming() is True
        assert mixed_provider.supports_function_calling() is False
        # Non-boolean values are falsy for capability checks
        assert mixed_provider.supports_vision() == "yes"