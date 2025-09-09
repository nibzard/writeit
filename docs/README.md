# WriteIt Documentation

Welcome to the WriteIt LLM Article Pipeline documentation. WriteIt transforms raw content into polished articles through an interactive, 4-step AI-powered pipeline with human-in-the-loop feedback.

## 📖 Documentation Structure

### 🏗️ Architecture & Design
- [**System Architecture**](architecture/system-architecture.md) - High-level system design and component interactions
- [**Data Models**](architecture/data-models.md) - Core entities and their relationships
- [**State Management**](architecture/state-management.md) - Event sourcing and pipeline state patterns
- [**Storage Architecture**](architecture/storage-architecture.md) - LMDB design and artifact versioning

### 👨‍💻 Developer Guides
- [**Getting Started**](developer/getting-started.md) - Setup and development environment
- [**Library Architecture**](developer/library-architecture.md) - Library-first design patterns
- [**Testing Strategy**](developer/testing-strategy.md) - TDD approach and test categories
- [**Contributing Guide**](developer/contributing.md) - Code standards and contribution workflow

### 📚 API Documentation
- [**REST API Reference**](api/rest-api.md) - Complete API documentation with examples
- [**WebSocket API**](api/websocket-api.md) - Real-time streaming protocol
- [**SDK Reference**](api/sdk-reference.md) - Python SDK for WriteIt integration
- [**Error Handling**](api/error-handling.md) - Error codes and recovery patterns

### 👤 User Guides
- [**Installation Guide**](user/installation.md) - System requirements and setup
- [**Quick Start Tutorial**](user/quickstart.md) - Your first article pipeline
- [**Pipeline Configuration**](user/pipeline-config.md) - Creating custom workflows
- [**Advanced Features**](user/advanced-features.md) - Branching, rewind, and power user features

### 🚀 Deployment & Operations  
- [**Deployment Guide**](deployment/deployment.md) - Production deployment strategies
- [**Configuration Management**](deployment/configuration.md) - Environment and secrets management
- [**Monitoring & Observability**](deployment/monitoring.md) - Logging, metrics, and alerting
- [**Troubleshooting**](deployment/troubleshooting.md) - Common issues and solutions

### 📋 Examples & Tutorials
- [**Example Pipelines**](examples/pipeline-examples.md) - Pre-built workflows for different content types
- [**Custom LLM Integration**](examples/custom-llm-integration.md) - Adding new AI providers
- [**TUI Customization**](examples/tui-customization.md) - Customizing the terminal interface
- [**Batch Processing**](examples/batch-processing.md) - Automating article generation

## 🎯 Quick Navigation

### New to WriteIt?
1. Start with [Installation Guide](user/installation.md)
2. Follow the [Quick Start Tutorial](user/quickstart.md)
3. Explore [Example Pipelines](examples/pipeline-examples.md)

### Developers?
1. Read [Getting Started](developer/getting-started.md)
2. Understand [System Architecture](architecture/system-architecture.md)
3. Follow [Testing Strategy](developer/testing-strategy.md)

### Integrating WriteIt?
1. Review [REST API Reference](api/rest-api.md)
2. Check [SDK Reference](api/sdk-reference.md)
3. See [Integration Examples](examples/custom-llm-integration.md)

### Deploying to Production?
1. Follow [Deployment Guide](deployment/deployment.md)
2. Set up [Monitoring](deployment/monitoring.md)
3. Review [Configuration Management](deployment/configuration.md)

## 🤝 Community & Support

- **Issues & Bugs**: Report on [GitHub Issues](https://github.com/writeIt/writeIt/issues)
- **Feature Requests**: Use [GitHub Discussions](https://github.com/writeIt/writeIt/discussions)
- **Contributing**: See [Contributing Guide](developer/contributing.md)
- **Questions**: Check [FAQ](user/faq.md) or start a discussion

## 📝 Documentation Standards

This documentation follows these principles:
- **Clear Examples**: Every concept includes working code examples
- **Progressive Disclosure**: Information organized from basic to advanced
- **Up-to-Date**: Documentation updated with every release
- **Searchable**: Comprehensive cross-references and indexing
- **Accessible**: Clear language and multiple learning paths

---

**Version**: 0.1.0 | **Last Updated**: 2025-09-08 | **License**: MIT