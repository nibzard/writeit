"""
WriteIt Domain Layer - Domain-Driven Design Implementation

This package contains the core business domains of WriteIt, each representing
a bounded context with clear responsibilities and minimal coupling.

## Domain Overview

### Pipeline Domain (writeit.domains.pipeline)
- **Responsibility**: Pipeline lifecycle from templates to execution results
- **Key Entities**: Pipeline, PipelineRun, PipelineStep, StepExecution
- **Boundaries**: Owns pipeline configuration, execution orchestration, state management

### Workspace Domain (writeit.domains.workspace)  
- **Responsibility**: Multi-tenant workspace isolation and configuration
- **Key Entities**: Workspace, WorkspaceConfig, TemplateManager
- **Boundaries**: Owns workspace lifecycle and multi-tenancy concerns

### Content Domain (writeit.domains.content)
- **Responsibility**: Template management, validation, and content generation
- **Key Entities**: ContentTemplate, StylePrimer, GeneratedContent
- **Boundaries**: Owns all content creation, validation, and template management

### Execution Domain (writeit.domains.execution)
- **Responsibility**: LLM integration, caching, and performance optimization
- **Key Entities**: LLMProvider, ExecutionContext, TokenUsage
- **Boundaries**: Owns all external LLM integration and performance optimization

### Storage Domain (writeit.domains.storage)
- **Responsibility**: Data persistence and workspace-aware storage operations
- **Key Entities**: StorageManager, DatabaseConnection, TransactionContext
- **Boundaries**: Owns all persistent storage operations and data access patterns

## Communication Patterns

Domains communicate through:
1. **Domain Events**: Asynchronous, decoupled communication
2. **Well-defined Interfaces**: Clear contracts at domain boundaries
3. **Shared Value Objects**: Common data structures in shared kernel

## Design Principles

1. **Bounded Contexts**: Each domain has clear boundaries and responsibilities
2. **Ubiquitous Language**: Consistent terminology across code and documentation
3. **Rich Domain Models**: Behavior-rich entities, not anemic data structures
4. **Event-Driven Architecture**: Loose coupling through domain events
5. **Dependency Inversion**: Depend on abstractions, not implementations
"""