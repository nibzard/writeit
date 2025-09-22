"""
Execution Domain - LLM Integration and Performance

This domain handles all external LLM integration, response caching,
token tracking, and execution performance optimization.

## Responsibilities

- LLM provider abstraction and integration
- Response caching with workspace isolation
- Token usage tracking and analytics
- Execution context management
- Provider fallback and error handling

## Key Entities

- **LLMProvider**: Provider configuration and capabilities
- **ExecutionContext**: Runtime execution state and metadata
- **TokenUsage**: Token consumption tracking and analytics
- **CacheEntry**: Cached response with TTL and metadata

## Key Value Objects

- **ModelName**: Validated model identifier with provider mapping
- **TokenCount**: Token usage metrics with cost calculation
- **CacheKey**: Cache key generation with context awareness
- **ExecutionMode**: CLI/TUI/Server mode enumeration
- **ProviderCapability**: Provider feature and limit specification

## Domain Services

- **LLMProviderService**: Provider selection and fallback logic
- **CacheService**: Smart caching with invalidation strategies
- **TokenTrackingService**: Usage analytics and cost tracking
- **ExecutionOptimizationService**: Performance optimization

## Domain Events

- **LLMRequestStarted**: API call initiated
- **LLMResponseReceived**: API response received
- **CacheHit**: Cache lookup succeeded
- **CacheMiss**: Cache lookup failed
- **TokensConsumed**: Token usage recorded
- **ProviderFallback**: Fallback to alternative provider

## Boundaries

This domain owns:
- LLM provider integration and abstraction
- Response caching implementation
- Token usage tracking and analytics
- Execution performance optimization
- Provider health monitoring

This domain does NOT own:
- Pipeline orchestration (Pipeline Domain)
- Data persistence (Storage Domain)
- Template rendering (Content Domain)
- Workspace isolation (Workspace Domain)
"""