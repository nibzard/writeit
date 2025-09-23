# Execution Domain Services

This directory contains the comprehensive execution management services for the WriteIt application, following Domain-Driven Design (DDD) patterns. These services provide sophisticated LLM orchestration, cache management, and token analytics capabilities.

## Services Overview

### 1. LLMOrchestrationService

**Purpose**: Multi-provider LLM integration and orchestration with intelligent fallback management.

**Key Features**:
- **Multi-Provider Management**: Support for OpenAI, Anthropic, local, and mock providers
- **Intelligent Load Balancing**: Multiple strategies (Round Robin, Least Loaded, Performance-Based, Cost-Optimized, Latency-Optimized)
- **Automatic Fallback**: Seamless provider switching on errors, timeouts, or rate limits
- **Rate Limiting**: Built-in rate limit management and monitoring
- **Performance Monitoring**: Real-time provider metrics and health checks
- **Request Prioritization**: Support for different priority levels (Low, Normal, High, Critical)
- **Streaming Support**: Full streaming response support with fallback

**Usage Example**:
```python
service = LLMOrchestrationService()

# Register providers
await service.register_provider(openai_provider)
await service.register_provider(anthropic_provider)

# Execute request with automatic provider selection
response = await service.execute_request(
    context=execution_context,
    prompt="Generate article outline",
    model_preference=[ModelName.from_string("gpt-4o-mini")]
)

# Get provider analytics
metrics = service.get_provider_metrics()
performance = service.analyze_provider_performance()
```

### 2. CacheManagementService

**Purpose**: Comprehensive LLM response cache management with optimization and analytics.

**Key Features**:
- **Multiple Cache Strategies**: LRU, LFU, TTL, Adaptive, Cost-Aware, Quality-Aware
- **Intelligent Eviction**: Smart cache cleanup based on cost, quality, and usage patterns
- **Cache Warming**: Proactive cache population for common queries
- **Performance Analytics**: Detailed cache hit rates, cost savings, and efficiency metrics
- **Storage Optimization**: Compression and size management
- **Policy Management**: Configurable cache policies with automatic optimization
- **Background Tasks**: Automated cleanup, warming, and optimization

**Usage Example**:
```python
service = CacheManagementService(cache_repository)

# Configure cache policy
policy = CachePolicy(
    strategy=CacheStrategy.ADAPTIVE,
    max_entries=10000,
    max_size_bytes=100_000_000
)
await service.configure_policy(policy)

# Check cache and manage entries
cached_response = await service.get_cached_response(cache_key)
await service.cache_response(cache_key, response, context)

# Optimize cache performance
plan = await service.generate_optimization_plan()
await service.implement_optimization_plan(plan)
```

### 3. TokenAnalyticsService

**Purpose**: Comprehensive token usage analytics with cost analysis and optimization recommendations.

**Key Features**:
- **Usage Tracking**: Detailed token consumption monitoring across workspaces and pipelines
- **Cost Analysis**: Real-time cost tracking with breakdown by model, pipeline, and workspace
- **Predictive Analytics**: Future usage and cost predictions with confidence levels
- **Optimization Recommendations**: Automated suggestions for cost reduction and efficiency improvement
- **Anomaly Detection**: Automatic detection of unusual usage patterns
- **Benchmark Comparisons**: Performance comparisons against industry standards
- **Budget Alerts**: Configurable budget thresholds with real-time alerts
- **Efficiency Scoring**: Comprehensive efficiency metrics combining cost, cache usage, and performance

**Usage Example**:
```python
service = TokenAnalyticsService(token_repository)

# Record token usage
await service.record_usage(
    workspace="my-project",
    pipeline_run_id="run-123",
    model=ModelName.from_string("gpt-4o-mini"),
    usage=token_count,
    cost=0.002,
    was_cached=False
)

# Analyze workspace usage
analysis = await service.analyze_workspace_usage(
    workspace="my-project",
    period=AnalyticsPeriod.WEEK
)

# Generate optimization plan
plan = await service.generate_optimization_plan(
    workspace="my-project",
    optimization_level=CostOptimizationLevel.MODERATE
)
```

## Architecture Patterns

### Domain-Driven Design Compliance

All services follow DDD principles:
- **Pure Domain Logic**: No infrastructure concerns in service layer
- **Entity Integration**: Proper use of domain entities (ExecutionContext, LLMProvider)
- **Value Object Usage**: Leveraging value objects (ModelName, TokenCount, CacheKey)
- **Repository Abstraction**: Working with repository interfaces, not implementations
- **Rich Error Handling**: Domain-specific exceptions with meaningful error messages

### Async/Await Support

All services are fully asynchronous:
- Non-blocking operations for LLM requests
- Concurrent provider health checks
- Background task management
- Streaming response support

### Workspace Awareness

All services support multi-workspace operations:
- Isolated analytics per workspace
- Workspace-specific caching policies
- Per-workspace budget and alert management
- Cross-workspace comparison capabilities

## Error Handling

Each service provides comprehensive error handling:

### LLMOrchestrationService Exceptions
- `LLMOrchestrationError`: Base exception
- `ProviderUnavailableError`: No providers available
- `ModelNotSupportedError`: Model not supported by any provider
- `RateLimitExceededError`: Rate limits exceeded

### CacheManagementService Exceptions
- `CacheManagementError`: Base exception
- `CacheStorageError`: Storage operation failures
- `CachePolicyError`: Invalid policy configuration

### TokenAnalyticsService Exceptions
- `TokenAnalyticsError`: Base exception
- `InsufficientDataError`: Not enough data for analysis
- `AnalyticsConfigurationError`: Invalid configuration

## Performance Considerations

### LLMOrchestrationService
- Efficient provider selection algorithms
- Connection pooling and reuse
- Intelligent retry mechanisms
- Metrics caching to reduce overhead

### CacheManagementService
- Background cleanup tasks
- Incremental eviction strategies
- Compressed storage options
- Efficient cache key generation

### TokenAnalyticsService
- Data aggregation optimization
- Statistical analysis caching
- Efficient time-series storage
- Predictive model optimization

## Configuration

### Environment Variables
```bash
# LLM Provider Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Cache Configuration
CACHE_MAX_SIZE_MB=100
CACHE_TTL_HOURS=24
CACHE_STRATEGY=adaptive

# Analytics Configuration
ANALYTICS_RETENTION_DAYS=90
ENABLE_PREDICTIVE_ANALYTICS=true
```

### Service Initialization
```python
# Initialize all services
llm_service = LLMOrchestrationService(
    selection_strategy=ProviderSelectionStrategy.PERFORMANCE_BASED,
    default_timeout=30,
    max_retries=3
)

cache_service = CacheManagementService(
    cache_repository=cache_repo,
    default_policy=cache_policy
)

analytics_service = TokenAnalyticsService(
    token_repository=token_repo,
    default_cost_per_1k_tokens=cost_mapping
)
```

## Integration Examples

### Complete Execution Flow
```python
async def execute_pipeline_step(context: ExecutionContext, prompt: str):
    # Check cache first
    cache_key = context.get_cache_key("generation", {"prompt": prompt})
    cached_response = await cache_service.get_cached_response(cache_key)
    
    if cached_response:
        # Record cache hit
        await analytics_service.record_usage(
            workspace_name=context.workspace_name,
            pipeline_run_id=context.pipeline_id,
            model_name=context.get_preferred_model(),
            usage=cached_response.usage,
            cost=0.0,  # No cost for cache hit
            was_cached=True
        )
        return cached_response.content
    
    # Execute LLM request
    response = await llm_service.execute_request(
        context=context,
        prompt=prompt,
        model_preference=context.model_preferences
    )
    
    # Cache the response
    await cache_service.cache_response(
        cache_key=cache_key,
        content=response.content,
        context=context,
        usage=response.usage,
        cost=response.cost,
        quality_score=response.quality_score,
        model_name=response.model_name
    )
    
    # Record usage analytics
    await analytics_service.record_usage(
        workspace_name=context.workspace_name,
        pipeline_run_id=context.pipeline_id,
        model_name=response.model_name,
        usage=response.usage,
        cost=response.cost,
        was_cached=False,
        context=context
    )
    
    return response.content
```

## Monitoring and Observability

All services provide comprehensive monitoring capabilities:

### Metrics Exposed
- Provider health and performance metrics
- Cache hit rates and storage utilization
- Token usage trends and cost analysis
- Error rates and failure patterns

### Alerting Support
- Budget threshold alerts
- Performance degradation alerts
- Cache capacity alerts
- Anomaly detection alerts

### Dashboard Integration
Services provide structured data for dashboard integration:
- Real-time performance metrics
- Historical trend analysis
- Cost optimization recommendations
- Predictive analytics visualizations

## Testing

All services are designed for comprehensive testing:

### Unit Testing
- Mock repository implementations
- Isolated service logic testing
- Edge case handling verification

### Integration Testing
- Real repository integration
- End-to-end workflow testing
- Performance benchmarking

### Example Test
```python
async def test_llm_orchestration_fallback():
    service = LLMOrchestrationService()
    
    # Configure providers with one failing
    await service.register_provider(failing_provider)
    await service.register_provider(working_provider)
    
    # Should fallback to working provider
    response = await service.execute_request(context, prompt, models)
    
    assert response.provider_name == "working_provider"
    assert response.content is not None
```

## Future Enhancements

Potential areas for future development:

### LLMOrchestrationService
- Advanced circuit breaker patterns
- Multi-region provider support
- Custom load balancing algorithms
- Provider cost optimization

### CacheManagementService
- Distributed caching support
- Advanced compression algorithms
- Machine learning-based eviction
- Cross-workspace cache sharing

### TokenAnalyticsService
- Advanced predictive models
- Real-time cost optimization
- Automated budget management
- Integration with billing systems

---

These services provide a robust foundation for LLM execution management in the WriteIt application, with extensive capabilities for optimization, monitoring, and analytics.