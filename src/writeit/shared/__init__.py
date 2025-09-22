"""
Shared Kernel - Common Domain Abstractions

This package contains shared abstractions, value objects, and interfaces
that are used across multiple domains.

## Responsibilities

- Define shared value objects used across domains
- Provide common abstractions and interfaces
- Define shared domain events
- Implement common error types and handling

## Modules

### Events (writeit.shared.events)
- Base event interfaces
- Event bus abstraction
- Event handler registration
- Event persistence and replay

### Value Objects (writeit.shared.value_objects)
- Common value objects (IDs, dates, etc.)
- Validation rules and constraints
- Equality and comparison logic
- Serialization support

### Errors (writeit.shared.errors)
- Base exception classes
- Domain-specific error types
- Error code definitions
- Error message templates

### Interfaces (writeit.shared.interfaces)
- Common repository interfaces
- Service abstractions
- Event handler interfaces
- Validation interfaces

## Design Principles

1. **Minimal Dependencies**: Shared kernel should have minimal external dependencies
2. **Stability**: Changes should be rare and well-coordinated
3. **Generic**: Should be useful across multiple domains
4. **Well-Tested**: Comprehensive test coverage for shared components
5. **Documented**: Clear contracts and usage examples

## Usage Guidelines

- Only add to shared kernel when truly needed by multiple domains
- Prefer composition over inheritance for shared behavior
- Use interfaces to define contracts between domains
- Keep shared value objects immutable and side-effect free
"""