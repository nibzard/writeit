"""
Workspace Domain - Multi-tenant Workspace Management

This domain handles workspace isolation, configuration, and multi-tenancy
concerns across the WriteIt system.

## Responsibilities

- Workspace creation, activation, and deletion
- Multi-tenant isolation and security
- Global and workspace-specific configuration management
- Template resolution across workspace scopes
- Workspace metadata and settings persistence

## Key Entities

- **Workspace**: Workspace aggregate root with lifecycle management
- **WorkspaceConfiguration**: Settings and preferences per workspace
- **TemplateManager**: Workspace-aware template resolution

## Key Value Objects

- **WorkspaceName**: Validated workspace name with constraints
- **WorkspacePath**: Filesystem path handling and validation
- **ConfigurationValue**: Type-safe configuration values

## Domain Services

- **WorkspaceIsolationService**: Ensure workspace isolation
- **WorkspaceTemplateService**: Template resolution across scopes
- **WorkspaceConfigurationService**: Configuration management

## Domain Events

- **WorkspaceCreated**: New workspace established
- **WorkspaceActivated**: Workspace switched
- **WorkspaceDeleted**: Workspace removed
- **WorkspaceConfigUpdated**: Configuration changed

## Boundaries

This domain owns:
- Workspace lifecycle and metadata
- Multi-tenant isolation enforcement
- Configuration management (global and workspace-specific)
- Template scope resolution

This domain does NOT own:
- File system storage implementation (Storage Domain)
- Pipeline execution within workspaces (Pipeline Domain)
- LLM caching per workspace (Execution Domain)
"""