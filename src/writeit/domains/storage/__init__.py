"""
Storage Domain - Data Persistence and Access

This domain handles all data persistence operations, database abstraction,
and workspace-aware storage management.

## Responsibilities

- Data persistence abstraction (LMDB, file system)
- Transaction management and connection pooling
- Workspace-isolated data access
- Database schema versioning and migrations
- Storage performance monitoring and optimization

## Key Entities

- **StorageManager**: Main storage abstraction with workspace awareness
- **DatabaseConnection**: Connection management and lifecycle
- **TransactionContext**: Transaction boundary and rollback management
- **StorageSchema**: Database schema definition and versioning

## Key Value Objects

- **StorageKey**: Strongly-typed storage key with workspace context
- **DatabaseName**: Validated database name with workspace isolation
- **TransactionId**: Transaction identifier for debugging and monitoring
- **StorageMetrics**: Performance and usage metrics

## Domain Services

- **StorageIsolationService**: Workspace data isolation enforcement
- **TransactionManagementService**: Transaction lifecycle management
- **StorageMigrationService**: Schema versioning and migration
- **StorageOptimizationService**: Performance tuning and cleanup

## Domain Events

- **DataStored**: Data successfully persisted
- **DataRetrieved**: Data successfully loaded
- **TransactionCommitted**: Transaction successfully committed
- **TransactionRolledBack**: Transaction rolled back due to error
- **StorageError**: Storage operation failed
- **MigrationCompleted**: Schema migration completed

## Boundaries

This domain owns:
- All data persistence operations
- Database connection management
- Transaction boundaries and consistency
- Storage performance optimization
- Workspace data isolation

This domain does NOT own:
- Business logic (handled by other domains)
- Cache implementation details (Execution Domain)
- File content validation (Content Domain)
- Workspace business rules (Workspace Domain)
"""