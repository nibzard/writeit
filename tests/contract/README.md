# API Contract Tests

This directory contains comprehensive contract tests for WriteIt's external interfaces. Contract tests ensure that all interfaces behave according to their specified contracts, providing consistency and reliability across different interaction modes.

## Overview

Contract tests verify that:
- **REST API endpoints** follow consistent response formats and HTTP status codes
- **WebSocket connections** handle real-time communication properly
- **CLI commands** produce expected outputs and error messages
- **TUI components** follow interaction patterns and display contracts
- **Data formats** are consistent across all interfaces
- **Security patterns** are implemented correctly
- **Performance characteristics** meet defined requirements

## Test Structure

### 1. REST API Contract Tests (`test_rest_api_contract.py`)
Comprehensive tests for REST API endpoints including:
- Workspace management endpoints
- Pipeline template and execution endpoints
- Content management endpoints
- Health check endpoints
- Error handling and response format validation
- Rate limiting and authentication headers
- CORS configuration

**Key Contracts:**
- HTTP status codes follow REST conventions
- Response formats include required metadata fields
- Error responses are structured and informative
- Pagination responses are consistent
- Rate limiting headers are present

### 2. WebSocket Contract Tests (`test_websocket_contract.py`)
Tests for real-time WebSocket communication:
- Connection lifecycle management
- Message format consistency
- Event broadcasting and subscription
- Error handling and recovery
- Performance and throughput requirements
- Connection limits and cleanup

**Key Contracts:**
- Messages include type, timestamp, and data fields
- Connection lifecycle follows established patterns
- Error recovery mechanisms are in place
- Performance meets throughput requirements

### 3. CLI Output Contract Tests (`test_cli_outputs_contract.py`)
Tests for command-line interface behavior:
- Command output formatting
- Error message consistency
- Help text structure
- Exit code conventions
- JSON output format
- Option validation

**Key Contracts:**
- Success/error indicators use consistent symbols
- Help text is structured and informative
- Exit codes follow Unix conventions
- JSON output is properly formatted

### 4. TUI Flow Contract Tests (`test_tui_flows_contract.py`)
Tests for Textual User Interface interactions:
- Screen navigation and transitions
- Input validation and handling
- Progress display patterns
- Error display and recovery
- Keyboard binding behavior
- Performance characteristics

**Key Contracts:**
- Screens follow consistent navigation patterns
- Input validation provides clear feedback
- Progress displays are informative
- Error recovery is user-friendly

### 5. Contract Pattern Tests (`test_contract_patterns.py`)
Simplified tests demonstrating contract patterns:
- Response format consistency
- Data serialization standards
- Security implementation patterns
- Performance requirements
- Integration workflow contracts

## Running Tests

### Run All Contract Tests
```bash
uv run python -m pytest tests/contract/ -v
```

### Run Specific Test Categories
```bash
# REST API tests
uv run python -m pytest tests/contract/test_rest_api_contract.py -v

# WebSocket tests  
uv run python -m pytest tests/contract/test_websocket_contract.py -v

# CLI output tests
uv run python -m pytest tests/contract/test_cli_outputs_contract.py -v

# TUI flow tests
uv run python -m pytest tests/contract/test_tui_flows_contract.py -v

# Contract pattern tests
uv run python -m pytest tests/contract/test_contract_patterns.py -v
```

### Run with Coverage
```bash
uv run python -m pytest tests/contract/ --cov=src/writeit --cov-report=html
```

## Contract Categories

### Response Format Contracts
Ensure consistent response structures across all interfaces:
```python
# Standard success response
{
    "data": {...},
    "metadata": {
        "timestamp": "2025-01-15T10:00:00Z",
        "version": "1.0.0"
    }
}

# Standard error response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Descriptive error message",
        "details": {...}
    },
    "timestamp": "2025-01-15T10:00:00Z",
    "request_id": "req-123"
}
```

### HTTP Status Code Contracts
REST endpoints use appropriate HTTP status codes:
- `200 OK` - Successful read operations
- `201 Created` - Successful creation operations
- `204 No Content` - Successful deletion operations
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server errors

### WebSocket Message Contracts
WebSocket messages follow consistent structure:
```python
{
    "type": "message_type",
    "timestamp": "2025-01-15T10:00:00Z",
    "data": {...}
}
```

### CLI Output Contracts
CLI outputs use consistent formatting:
- Success indicators: `✓ Operation completed`
- Error indicators: `✗ Error: message`
- Info indicators: `ℹ Processing item`
- Structured output with `--json` flag

### Performance Contracts
Define acceptable performance characteristics:
- API responses: < 1 second
- WebSocket messages: < 100ms
- CLI commands: < 2 seconds
- Data size limits: 10MB request, 50MB response

## Security Contracts

### Input Validation
All inputs are validated according to defined rules:
- Workspace names: `^[a-zA-Z0-9_-]{3,50}$`
- API keys: `^[a-zA-Z0-9]{32,64}$`
- File paths: Prevent directory traversal
- Content sanitization: Remove dangerous HTML/JS

### Authentication
- Use JWT tokens with Bearer scheme
- Token validation with reasonable expiration
- API key validation for external integrations

### Rate Limiting
Standard rate limiting headers:
```
x-ratelimit-limit: 1000
x-ratelimit-remaining: 999
x-ratelimit-reset: 1642680000
```

## Integration Contracts

### End-to-End Workflows
Verify complete user workflows:
1. Workspace creation → Pipeline creation → Pipeline execution
2. Template validation → Pipeline execution → Result viewing
3. Error handling → Recovery → Retry mechanisms

### Data Flow Contracts
Ensure data consistency across interfaces:
- Configuration files match API models
- CLI output matches API responses
- WebSocket events match CLI status updates

## Testing Philosophy

### What Contract Tests Verify
- **Interface Stability**: External APIs don't change unexpectedly
- **Response Consistency**: Similar operations return similar structures
- **Error Handling**: Errors are handled gracefully and informatively
- **Performance**: Responses meet defined time requirements
- **Security**: Inputs are validated and sanitized properly

### What Contract Tests Don't Verify
- Internal implementation details
- Business logic correctness (handled by unit/integration tests)
- Database schema changes
- Performance optimization (handled by load tests)

### Maintenance
- Update contracts when interface requirements change
- Add new contract tests for new features
- Maintain backward compatibility when possible
- Document breaking changes in release notes

## Best Practices

1. **Focus on External Contracts**: Test what users see, not internal details
2. **Use Realistic Data**: Test with typical and edge case data
3. **Test Error Paths**: Verify error handling works correctly
4. **Document Contracts**: Include clear documentation of expected behaviors
5. **Version Contracts**: Maintain contract versioning for compatibility

## Troubleshooting

### Common Issues
- **Import Errors**: Ensure all dependencies are properly installed
- **Circular Dependencies**: Check import order and structure
- **Mock Configuration**: Verify mocks are properly set up
- **Environment Variables**: Ensure test environment is configured

### Debug Tips
- Use `pytest --pdb` for interactive debugging
- Increase verbosity with `-v` flag
- Run specific tests with `-k` flag
- Use `--tb=short` for cleaner error output

## Contributing

When adding new contract tests:

1. Identify the interface contract to verify
2. Create test cases for normal and error scenarios
3. Follow existing naming conventions
4. Include comprehensive documentation
5. Verify tests run successfully in CI/CD

## References

- [WriteIt Architecture Documentation](../docs/architecture.md)
- [REST API Design Guidelines](../docs/api-design.md)
- [Testing Strategy](../docs/testing.md)
- [Contract Testing Best Practices](../docs/contract-testing.md)