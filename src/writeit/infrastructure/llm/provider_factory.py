"""LLM Provider Factory and Registry.

Manages creation, registration, and selection of LLM providers.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .base_provider import BaseLLMProvider, ProviderType, ProviderError
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for LLM providers."""
    
    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[ProviderType, Type[BaseLLMProvider]] = {}
        self._instances: Dict[str, BaseLLMProvider] = {}
        self._default_configs: Dict[ProviderType, Dict[str, Any]] = {}
        
        # Register built-in providers
        self._register_builtin_providers()
    
    def _register_builtin_providers(self):
        """Register built-in provider implementations."""
        self.register_provider(ProviderType.MOCK, MockLLMProvider)
        self.register_provider(ProviderType.OPENAI, OpenAIProvider)
        self.register_provider(ProviderType.ANTHROPIC, AnthropicProvider)
        
        # Set default configurations
        self._default_configs[ProviderType.MOCK] = {
            "latency_ms": 100,
            "failure_rate": 0.0
        }
    
    def register_provider(
        self, 
        provider_type: ProviderType, 
        provider_class: Type[BaseLLMProvider]
    ) -> None:
        """Register a provider implementation.
        
        Args:
            provider_type: Type of provider
            provider_class: Provider implementation class
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(f"Provider class must inherit from BaseLLMProvider")
        
        self._providers[provider_type] = provider_class
        logger.info(f"Registered provider: {provider_type.value} -> {provider_class.__name__}")
    
    def create_provider(
        self, 
        provider_type: ProviderType, 
        config: Optional[Dict[str, Any]] = None,
        instance_id: Optional[str] = None
    ) -> BaseLLMProvider:
        """Create a provider instance.
        
        Args:
            provider_type: Type of provider to create
            config: Provider-specific configuration
            instance_id: Optional instance identifier for caching
            
        Returns:
            Provider instance
            
        Raises:
            ProviderError: If provider type is not registered
        """
        if provider_type not in self._providers:
            raise ProviderError(f"Provider type '{provider_type.value}' is not registered")
        
        # Check for cached instance
        cache_key = instance_id or f"{provider_type.value}_default"
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        # Merge with default config
        merged_config = self._default_configs.get(provider_type, {}).copy()
        if config:
            merged_config.update(config)
        
        # Create new instance
        provider_class = self._providers[provider_type]
        instance = provider_class(merged_config)
        
        # Cache instance if ID provided
        if instance_id:
            self._instances[cache_key] = instance
        
        logger.info(f"Created provider instance: {provider_type.value}")
        return instance
    
    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available provider types."""
        return list(self._providers.keys())
    
    def set_default_config(
        self, 
        provider_type: ProviderType, 
        config: Dict[str, Any]
    ) -> None:
        """Set default configuration for a provider type."""
        self._default_configs[provider_type] = config
    
    def clear_instances(self) -> None:
        """Clear all cached provider instances."""
        self._instances.clear()


class ProviderFactory:
    """Factory for creating and managing LLM providers."""
    
    def __init__(self, registry: Optional[ProviderRegistry] = None):
        """Initialize the provider factory.
        
        Args:
            registry: Provider registry (creates default if None)
        """
        self.registry = registry or ProviderRegistry()
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
    
    def configure_provider(
        self, 
        provider_name: str, 
        provider_type: ProviderType, 
        config: Dict[str, Any]
    ) -> None:
        """Configure a named provider.
        
        Args:
            provider_name: Name for this provider configuration
            provider_type: Type of provider
            config: Provider configuration
        """
        self._provider_configs[provider_name] = {
            "type": provider_type,
            "config": config
        }
        logger.info(f"Configured provider '{provider_name}' of type {provider_type.value}")
    
    def get_provider(
        self, 
        provider_name: str, 
        auto_initialize: bool = True
    ) -> BaseLLMProvider:
        """Get a configured provider by name.
        
        Args:
            provider_name: Name of the provider configuration
            auto_initialize: Whether to automatically initialize the provider
            
        Returns:
            Provider instance
            
        Raises:
            ProviderError: If provider is not configured
        """
        if provider_name not in self._provider_configs:
            raise ProviderError(f"Provider '{provider_name}' is not configured")
        
        config_data = self._provider_configs[provider_name]
        provider = self.registry.create_provider(
            provider_type=config_data["type"],
            config=config_data["config"],
            instance_id=provider_name
        )
        
        if auto_initialize and not provider._initialized:
            import asyncio
            if asyncio.iscoroutinefunction(provider.initialize):
                # If we're in an async context, this should be awaited by caller
                logger.warning(f"Provider '{provider_name}' requires async initialization")
            else:
                provider.initialize()
        
        return provider
    
    def create_provider_by_type(
        self, 
        provider_type: ProviderType, 
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLLMProvider:
        """Create a provider directly by type.
        
        Args:
            provider_type: Type of provider to create
            config: Provider configuration
            
        Returns:
            Provider instance
        """
        return self.registry.create_provider(provider_type, config)
    
    def get_configured_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return list(self._provider_configs.keys())
    
    def auto_configure_from_env(self) -> None:
        """Auto-configure providers from environment variables."""
        import os
        
        # OpenAI configuration
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.configure_provider(
                "openai_default",
                ProviderType.OPENAI,
                {
                    "api_key": openai_api_key,
                    "organization": os.getenv("OPENAI_ORG_ID")
                }
            )
        
        # Anthropic configuration
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            self.configure_provider(
                "anthropic_default",
                ProviderType.ANTHROPIC,
                {
                    "api_key": anthropic_api_key,
                    "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
                }
            )
        
        # Always configure mock provider for testing
        self.configure_provider(
            "mock_default",
            ProviderType.MOCK,
            {
                "latency_ms": 50,
                "failure_rate": 0.0
            }
        )
        
        logger.info("Auto-configured providers from environment")
    
    def get_fallback_chain(self, primary_provider: str) -> List[str]:
        """Get a fallback chain for a primary provider.
        
        Args:
            primary_provider: Name of primary provider
            
        Returns:
            List of provider names in fallback order
        """
        fallback_chain = [primary_provider]
        
        # Add common fallbacks
        if "openai" in primary_provider.lower():
            # OpenAI fallbacks - try Anthropic as backup, then mock
            if "anthropic_default" in self._provider_configs:
                fallback_chain.append("anthropic_default")
            if "mock_default" in self._provider_configs:
                fallback_chain.append("mock_default")
        
        elif "anthropic" in primary_provider.lower():
            # Anthropic fallbacks - try OpenAI as backup, then mock
            if "openai_default" in self._provider_configs:
                fallback_chain.append("openai_default")
            if "mock_default" in self._provider_configs:
                fallback_chain.append("mock_default")
        
        elif "mock" not in primary_provider.lower():
            # For any non-mock provider, add mock as ultimate fallback
            if "mock_default" in self._provider_configs:
                fallback_chain.append("mock_default")
        
        return fallback_chain


# Global provider factory instance
_global_factory: Optional[ProviderFactory] = None


def get_provider_factory() -> ProviderFactory:
    """Get the global provider factory instance."""
    global _global_factory
    if _global_factory is None:
        _global_factory = ProviderFactory()
        _global_factory.auto_configure_from_env()
    return _global_factory


def configure_global_provider(
    provider_name: str, 
    provider_type: ProviderType, 
    config: Dict[str, Any]
) -> None:
    """Configure a provider in the global factory."""
    factory = get_provider_factory()
    factory.configure_provider(provider_name, provider_type, config)


def get_global_provider(provider_name: str) -> BaseLLMProvider:
    """Get a provider from the global factory."""
    factory = get_provider_factory()
    return factory.get_provider(provider_name)
