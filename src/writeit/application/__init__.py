"""
Application Layer - Use Cases and Application Services

This layer orchestrates domain operations and provides the main
entry points for external systems (CLI, API, TUI).

## Responsibilities

- Implement application use cases
- Coordinate multiple domain operations
- Handle cross-cutting concerns (logging, validation, security)
- Provide command/query separation (CQRS)
- Manage transaction boundaries

## Modules

### Commands (writeit.application.commands)
- Command handlers for write operations
- Pipeline execution commands
- Workspace management commands
- Template management commands

### Queries (writeit.application.queries)
- Query handlers for read operations
- Pipeline status queries
- Template discovery queries
- Workspace information queries

### Use Cases (writeit.application.use_cases)
- Complex business workflows
- Multi-domain operations
- Transaction management
- Error handling and recovery

### Services (writeit.application.services)
- Application-level services
- Cross-domain coordination
- External system integration
- Event handling and propagation

## Design Principles

1. **Use Case Driven**: Each use case represents a user goal
2. **Domain Coordination**: Orchestrate domain services, don't duplicate logic
3. **Transaction Management**: Define clear transaction boundaries
4. **Error Handling**: Convert domain errors to application responses
5. **Event Handling**: Coordinate domain events across boundaries
"""