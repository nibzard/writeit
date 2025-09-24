# WriteIt Developer Guide

This guide provides comprehensive information for developers working with WriteIt, including setup, development workflow, contribution guidelines, and best practices.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Architecture Overview](#architecture-overview)
- [Code Structure](#code-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Domain-Driven Design](#domain-driven-design)
- [API Development](#api-development)
- [CLI Development](#cli-development)
- [Best Practices](#best-practices)
- [Contributing](#contributing)

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: uv (Astral's package manager)
- **Text Editor**: VS Code (recommended) or any Python IDE
- **Git**: For version control

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/writeit.git
cd writeit

# 2. Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies and create virtual environment
uv sync

# 4. Initialize WriteIt (for development)
uv run writeit init --migrate

# 5. Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### First Run

```bash
# Test basic functionality
uv run writeit --version
uv run writeit --help

# List available pipelines
uv run writeit list-pipelines

# Run a test pipeline
uv run writeit run tech-article --dry-run

# Start development server
uv run uvicorn writeit.server.app:app --reload --port 8000
```

---

## 🛠️ Development Environment

### IDE Setup (VS Code)

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestPath": "./.venv/bin/pytest",
    "python.analysis.typeCheckingMode": "strict",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### Recommended Extensions

- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **Black Formatter** (Microsoft)
- **isort** (Microsoft)
- **GitLens** (GitKraken)
- **Docker** (Microsoft)

### Development Commands

```bash
# Development shell with uv
uv run python
uv run ipython

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/ tests/

# Formatting
uv run ruff format src/ tests/

# Import sorting
uv run ruff check --select I src/ tests/

# Security scanning
uv run bandit -r src/

# Dependency updates
uv tree
uv outdated
uv update --package package-name
```

---

## 🏗️ Architecture Overview

### Domain-Driven Design

WriteIt follows Domain-Driven Design (DDD) principles with clear bounded contexts:

```
src/writeit/
├── domains/              # Domain layer
│   ├── pipeline/         # Pipeline bounded context
│   ├── workspace/        # Workspace bounded context
│   ├── content/          # Content bounded context
│   ├── execution/        # Execution bounded context
│   └── storage/          # Storage bounded context
├── application/          # Application layer
│   ├── commands/         # CQRS command handlers
│   ├── queries/          # CQRS query handlers
│   └── services/         # Application services
├── infrastructure/       # Infrastructure layer
│   ├── persistence/      # Database adapters
│   ├── llm/             # LLM provider adapters
│   ├── web/             # FastAPI adapters
│   └── cli/             # CLI adapters
└── shared/              # Shared kernel
    ├── events/          # Domain events
    ├── value_objects/   # Shared value objects
    └── errors/          # Error definitions
```

### Key Architectural Patterns

1. **Hexagonal Architecture**: Ports and adapters pattern
2. **CQRS**: Command Query Responsibility Segregation
3. **Event Sourcing**: Immutable event streams
4. **Dependency Injection**: Service container with automatic resolution
5. **Repository Pattern**: Data access abstraction

### Component Interactions

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI/TUI/UI     │    │   FastAPI Server │    │   Client Lib    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┴──────────┬───────────┘
                     │                      │
          ┌─────────────────────────────────────────┐
          │           Application Layer              │
          │  ┌─────────────┐  ┌─────────────┐      │
          │  │ Commands    │  │ Queries      │      │
          │  └─────────────┘  └─────────────┘      │
          └─────────────────────────────────────────┘
                     │                      │
          ┌─────────────────────────────────────────┐
          │             Domain Layer                │
          │  ┌─────────────┐  ┌─────────────┐      │
          │  │ Services    │  │ Events      │      │
          │  └─────────────┘  └─────────────┘      │
          └─────────────────────────────────────────┘
                     │                      │
          ┌─────────────────────────────────────────┐
          │          Infrastructure Layer             │
          │  ┌─────────────┐  ┌─────────────┐      │
          │  │ Repositories│  │ External     │      │
          │  │             │  │ Services     │      │
          │  └─────────────┘  └─────────────┘      │
          └─────────────────────────────────────────┘
```

---

## 📁 Code Structure

### Directory Structure

```
src/writeit/
├── __init__.py                   # Package initialization
├── main.py                       # Main entry point
├── cli/                          # CLI components
│   ├── __init__.py
│   ├── main.py                   # CLI main entry point
│   ├── app.py                    # Typer app configuration
│   ├── commands/                 # CLI command modules
│   │   ├── init.py
│   │   ├── workspace.py
│   │   ├── pipeline.py
│   │   ├── validate.py
│   │   └── ...
│   ├── output.py                 # CLI output formatting
│   └── completion.py             # CLI completion helpers
├── server/                       # Server components
│   ├── __init__.py
│   ├── app.py                    # FastAPI application
│   ├── client.py                 # Server client library
│   └── websocket.py              # WebSocket manager
├── domains/                      # Domain layer
│   ├── pipeline/                 # Pipeline domain
│   │   ├── entities/             # Domain entities
│   │   │   ├── pipeline_template.py
│   │   │   ├── pipeline_run.py
│   │   │   └── ...
│   │   ├── value_objects/        # Value objects
│   │   │   ├── pipeline_id.py
│   │   │   ├── execution_status.py
│   │   │   └── ...
│   │   ├── repositories/         # Domain repository interfaces
│   │   │   ├── pipeline_repository.py
│   │   │   └── ...
│   │   ├── services/             # Domain services
│   │   │   ├── pipeline_validation.py
│   │   │   └── ...
│   │   └── events/               # Domain events
│   │       ├── pipeline_events.py
│   │       └── ...
│   ├── workspace/                # Workspace domain
│   ├── content/                  # Content domain
│   ├── execution/                # Execution domain
│   └── storage/                  # Storage domain
├── application/                  # Application layer
│   ├── commands/                 # CQRS command handlers
│   │   ├── pipeline_commands.py
│   │   ├── workspace_commands.py
│   │   └── ...
│   ├── queries/                  # CQRS query handlers
│   │   ├── pipeline_queries.py
│   │   ├── workspace_queries.py
│   │   └── ...
│   └── services/                 # Application services
│       ├── pipeline_service.py
│       ├── workspace_service.py
│       └── ...
├── infrastructure/               # Infrastructure layer
│   ├── persistence/              # Storage implementations
│   │   ├── lmdb_storage.py
│   │   ├── cache_storage.py
│   │   └── ...
│   ├── repositories/             # Repository implementations
│   │   ├── pipeline_repository_impl.py
│   │   └── ...
│   ├── llm/                      # LLM provider implementations
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── ...
│   ├── web/                      # Web infrastructure
│   │   ├── endpoints/            # API endpoints
│   │   ├── middleware/           # Web middleware
│   │   └── ...
│   └── cli/                      # CLI infrastructure
│       ├── commands/             # CLI command implementations
│       └── ...
├── shared/                       # Shared kernel
│   ├── events/                   # Shared events
│   ├── value_objects/            # Shared value objects
│   ├── errors/                   # Error definitions
│   └── container.py              # Dependency injection container
├── tui/                          # TUI components
│   ├── __init__.py
│   ├── app.py                    # TUI application
│   └── widgets/                  # TUI widgets
├── storage/                      # Legacy storage (being migrated)
├── models/                       # Legacy models (being migrated)
└── utils/                        # Utility functions
```

### Naming Conventions

**Files and Directories:**
- Use `snake_case` for files and directories
- Group related functionality in directories
- Use `__init__.py` to expose public APIs

**Classes:**
- Use `PascalCase` for classes
- Domain entities: `PipelineTemplate`, `Workspace`
- Value objects: `PipelineId`, `ExecutionStatus`
- Services: `PipelineExecutionService`

**Functions and Methods:**
- Use `snake_case` for functions and methods
- Public methods: descriptive names
- Private methods: prefix with `_`
- Domain methods: business-focused language

**Variables:**
- Use `snake_case` for variables
- Constants: `UPPER_SNAKE_CASE`
- Boolean variables: prefix with `is_`, `has_`, `can_`

### Code Organization Principles

1. **Domain First**: Start with domain entities and value objects
2. **Infrastructure Last**: Implement infrastructure after defining domain interfaces
3. **Clear Boundaries**: Each layer depends only on layers below it
4. **Shared Kernel**: Put truly shared components in `shared/`
5. **Explicit Dependencies**: Use dependency injection for all services

---

## 🔄 Development Workflow

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Develop Domain Layer**
   ```bash
   # Create domain entities and value objects
   # Define domain services
   # Create domain events
   ```

3. **Implement Application Layer**
   ```bash
   # Create command/query handlers
   # Implement application services
   # Define use cases
   ```

4. **Implement Infrastructure**
   ```bash
   # Create repository implementations
   # Implement external service adapters
   # Add API endpoints or CLI commands
   ```

5. **Write Tests**
   ```bash
   # Unit tests for domain logic
   # Integration tests for services
   # End-to-end tests for complete workflows
   ```

6. **Validate and Refactor**
   ```bash
   # Run all tests
   uv run pytest tests/
   
   # Check code quality
   uv run ruff check src/ tests/
   uv run mypy src/
   
   # Validate functionality
   uv run writeit validate --all
   ```

### Testing Workflow

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/

# Run specific test file
uv run pytest tests/test_pipeline_execution.py

# Run with verbose output
uv run pytest -v

# Run with debugging
uv run pytest --pdb
```

### Code Quality Workflow

```bash
# Format code
uv run ruff format src/ tests/

# Check and fix imports
uv run ruff check --select I --fix src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/ --strict

# Security scanning
uv run bandit -r src/

# Documentation generation
uv run python -m sphinx -b html docs/ docs/_build/
```

### Git Workflow

```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat: add new pipeline template type"

# Push to remote
git push origin feature/your-feature-name

# Create pull request
# Link to GitHub issue
# Request review from team members
```

### Commit Message Format

Follow conventional commits format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(pipeline): add conditional step execution
fix(workspace): handle workspace creation race condition
docs(api): update OpenAPI specification
refactor(storage): migrate to LMDB storage
test(pipeline): add integration tests for pipeline execution
```

---

## 🧪 Testing

### Testing Strategy

WriteIt uses a comprehensive testing strategy:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Contract Tests**: Test API contracts and interfaces
4. **End-to-End Tests**: Test complete user workflows
5. **Performance Tests**: Test performance characteristics

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                  # Pytest configuration and fixtures
├── unit/                        # Unit tests
│   ├── domains/                 # Domain layer tests
│   │   ├── test_pipeline_entities.py
│   │   ├── test_workspace_services.py
│   │   └── ...
│   ├── application/             # Application layer tests
│   │   ├── test_pipeline_commands.py
│   │   ├── test_workspace_queries.py
│   │   └── ...
│   └── infrastructure/          # Infrastructure tests
│       ├── test_repositories.py
│       ├── test_llm_providers.py
│       └── ...
├── integration/                 # Integration tests
│   ├── test_pipeline_execution.py
│   ├── test_workspace_management.py
│   ├── test_llm_integration.py
│   └── ...
├── contract/                    # Contract tests
│   ├── test_api_contracts.py
│   ├── test_cli_contracts.py
│   └── ...
└── e2e/                         # End-to-end tests
    ├── test_complete_workflow.py
    ├── test_error_scenarios.py
    └── ...
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from writeit.domains.pipeline.entities import PipelineTemplate
from writeit.domains.workspace.entities import Workspace
from writeit.shared.container import Container

@pytest.fixture
def container():
    """Dependency injection container for tests."""
    return Container()

@pytest.fixture
def sample_pipeline():
    """Sample pipeline template for testing."""
    return PipelineTemplate(
        name="test-pipeline",
        description="Test pipeline",
        version="1.0.0",
        inputs={},
        steps=[]
    )

@pytest.fixture
def sample_workspace():
    """Sample workspace for testing."""
    return Workspace(
        name="test-workspace",
        path="/tmp/test-workspace"
    )
```

### Unit Testing Example

```python
# tests/unit/domains/test_pipeline_execution.py
import pytest
from writeit.domains.pipeline.entities import PipelineTemplate, PipelineRun
from writeit.domains.pipeline.services import PipelineExecutionService

def test_pipeline_execution_start(sample_pipeline):
    """Test pipeline execution start."""
    # Arrange
    service = PipelineExecutionService()
    
    # Act
    run = service.start_execution(sample_pipeline, {})
    
    # Assert
    assert run.pipeline_id == sample_pipeline.id
    assert run.status == ExecutionStatus.RUNNING
    assert run.created_at is not None

def test_pipeline_step_dependency_resolution(sample_pipeline):
    """Test step dependency resolution."""
    # Arrange
    # Add steps with dependencies
    sample_pipeline.steps = [
        PipelineStep(key="step1", dependencies=[]),
        PipelineStep(key="step2", dependencies=["step1"]),
        PipelineStep(key="step3", dependencies=["step1", "step2"])
    ]
    
    service = PipelineExecutionService()
    
    # Act
    execution_order = service.resolve_dependencies(sample_pipeline)
    
    # Assert
    assert execution_order[0].key == "step1"
    assert execution_order[1].key in ["step2", "step3"]
    assert execution_order[2].key in ["step2", "step3"]
```

### Integration Testing Example

```python
# tests/integration/test_pipeline_execution.py
import pytest
import asyncio
from writeit.application.services import PipelineApplicationService
from writeit.infrastructure.persistence.lmdb_storage import LMDBStorageManager

@pytest.mark.asyncio
async def test_complete_pipeline_execution(tmp_path):
    """Test complete pipeline execution with real storage."""
    # Arrange
    storage = LMDBStorageManager(tmp_path)
    service = PipelineApplicationService(storage)
    
    pipeline_template = create_test_pipeline()
    inputs = {"topic": "Test topic", "style": "technical"}
    
    # Act
    result = await service.execute_pipeline(pipeline_template, inputs)
    
    # Assert
    assert result.status == "completed"
    assert result.outputs is not None
    assert len(result.steps) > 0
    
    # Verify persistence
    stored_run = await storage.get_pipeline_run(result.id)
    assert stored_run is not None
    assert stored_run.status == "completed"
```

### Contract Testing Example

```python
# tests/contract/test_api_contracts.py
import pytest
from fastapi.testclient import TestClient
from writeit.server.app import app

def test_pipeline_execution_api_contract():
    """Test API contract for pipeline execution."""
    client = TestClient(app)
    
    # Test request schema
    request_data = {
        "pipeline_id": "test-pipeline",
        "inputs": {"topic": "AI Ethics"},
        "workspace_name": "default"
    }
    
    # Test response schema
    response = client.post("/api/runs", json=request_data)
    
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert "pipeline_id" in data
    assert "status" in data
    assert data["status"] in ["created", "running"]
```

### Mocking External Dependencies

```python
# tests/unit/infrastructure/test_llm_providers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from writeit.infrastructure.llm.openai_provider import OpenAIProvider

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    return mock_client

def test_openai_provider_call(mock_openai_client):
    """Test OpenAI provider with mocked client."""
    # Arrange
    provider = OpenAIProvider(api_key="test-key")
    provider.client = mock_openai_client
    
    # Act
    response = asyncio.run(provider.call_model("Test prompt", "gpt-4o-mini"))
    
    # Assert
    assert response == "Test response"
    mock_openai_client.chat.completions.create.assert_called_once()
```

---

## 🏛️ Domain-Driven Design

### Entity Design

```python
# src/writeit/domains/pipeline/entities/pipeline_template.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

from writeit.domains.pipeline.value_objects import (
    PipelineId,
    ExecutionStatus,
    PromptTemplate
)
from writeit.domains.pipeline.events import PipelineTemplateCreated

@dataclass
class PipelineTemplate:
    """Pipeline template aggregate root."""
    
    # Entity identity
    id: PipelineId = field(default_factory=lambda: PipelineId(str(uuid4())))
    
    # Business attributes
    name: str
    description: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Pipeline definition
    inputs: Dict[str, Any] = field(default_factory=dict)
    steps: List[PipelineStepTemplate] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def __post_init__(self):
        """Validate invariant after initialization."""
        self._validate_invariants()
    
    def _validate_invariants(self):
        """Validate business invariants."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Pipeline name cannot be empty")
        
        if len(self.steps) == 0:
            raise ValueError("Pipeline must have at least one step")
        
        # Validate step dependencies
        step_keys = {step.key for step in self.steps}
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_keys:
                    raise ValueError(f"Step '{step.key}' depends on non-existent step '{dep}'")
    
    def update_metadata(self, metadata: Dict[str, Any]) -> List[PipelineTemplateUpdated]:
        """Update pipeline metadata."""
        events = []
        
        # Business logic for metadata update
        if self.metadata != metadata:
            old_metadata = self.metadata.copy()
            self.metadata = metadata.copy()
            self.updated_at = datetime.now()
            
            events.append(PipelineTemplateUpdated(
                pipeline_id=self.id,
                change_type="metadata_updated",
                old_value=old_metadata,
                new_value=metadata
            ))
        
        return events
    
    def add_step(self, step: PipelineStepTemplate) -> List[PipelineStepAdded]:
        """Add a step to the pipeline."""
        events = []
        
        # Business logic for step addition
        if step.key in {s.key for s in self.steps}:
            raise ValueError(f"Step with key '{step.key}' already exists")
        
        # Validate dependencies
        for dep in step.depends_on:
            if dep not in {s.key for s in self.steps}:
                raise ValueError(f"Dependency '{dep}' not found in pipeline")
        
        self.steps.append(step)
        self.updated_at = datetime.now()
        
        events.append(PipelineStepAdded(
            pipeline_id=self.id,
            step_key=step.key,
            step_position=len(self.steps) - 1
        ))
        
        return events
    
    def validate_template(self) -> ValidationResult:
        """Validate the complete template."""
        errors = []
        
        # Validate business rules
        if len(self.steps) > 50:
            errors.append("Pipeline cannot have more than 50 steps")
        
        # Validate step-specific rules
        for step in self.steps:
            if step.type == "llm_generate" and not step.prompt_template:
                errors.append(f"LLM step '{step.key}' must have prompt template")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

### Value Object Design

```python
# src/writeit/domains/pipeline/value_objects/pipeline_id.py
from dataclasses import dataclass
from typing import NewType
import re
import uuid

# Strong typing with NewType
PipelineIdValue = NewType('PipelineIdValue', str)

@dataclass(frozen=True)
class PipelineId:
    """Strongly-typed pipeline identifier."""
    
    value: PipelineIdValue
    
    def __post_init__(self):
        """Validate pipeline ID format."""
        self._validate_format()
    
    def _validate_format(self):
        """Validate that the pipeline ID follows expected format."""
        # Allow UUID format or custom pipeline_ format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        custom_pattern = r'^pipeline_[a-z0-9_]+$'
        
        if not (re.match(uuid_pattern, self.value) or re.match(custom_pattern, self.value)):
            raise ValueError(
                f"Invalid pipeline ID format: {self.value}. "
                f"Must be UUID or follow pattern 'pipeline_name'"
            )
    
    @classmethod
    def generate(cls) -> 'PipelineId':
        """Generate a new pipeline ID."""
        return cls(PipelineIdValue(str(uuid4())))
    
    @classmethod
    def from_string(cls, value: str) -> 'PipelineId':
        """Create pipeline ID from string."""
        return cls(PipelineIdValue(value))
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, PipelineId):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash implementation."""
        return hash(self.value)
```

### Domain Service Design

```python
# src/writeit/domains/pipeline/services/pipeline_validation_service.py
from typing import List, Optional
from writeit.domains.pipeline.entities import PipelineTemplate
from writeit.domains.pipeline.value_objects import ValidationResult

class PipelineValidationService:
    """Domain service for pipeline validation logic."""
    
    def validate_template(self, template: PipelineTemplate) -> ValidationResult:
        """Validate complete pipeline template."""
        errors = []
        warnings = []
        
        # Basic validation
        errors.extend(self._validate_basic_structure(template))
        
        # Step validation
        errors.extend(self._validate_steps(template))
        
        # Dependency validation
        errors.extend(self._validate_dependencies(template))
        
        # Business rule validation
        errors.extend(self._validate_business_rules(template))
        
        # Performance warnings
        warnings.extend(self._check_performance_warnings(template))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=self._calculate_validation_score(errors, warnings)
        )
    
    def _validate_basic_structure(self, template: PipelineTemplate) -> List[str]:
        """Validate basic pipeline structure."""
        errors = []
        
        if not template.name or len(template.name.strip()) == 0:
            errors.append("Pipeline name is required")
        
        if len(template.name) > 100:
            errors.append("Pipeline name cannot exceed 100 characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', template.name):
            errors.append("Pipeline name can only contain letters, numbers, hyphens, and underscores")
        
        if len(template.steps) == 0:
            errors.append("Pipeline must have at least one step")
        
        if len(template.steps) > 50:
            errors.append("Pipeline cannot have more than 50 steps")
        
        return errors
    
    def _validate_steps(self, template: PipelineTemplate) -> List[str]:
        """Validate individual pipeline steps."""
        errors = []
        step_keys = set()
        
        for i, step in enumerate(template.steps):
            # Check for duplicate step keys
            if step.key in step_keys:
                errors.append(f"Duplicate step key: {step.key}")
            step_keys.add(step.key)
            
            # Validate step key format
            if not re.match(r'^[a-z0-9_]+$', step.key):
                errors.append(f"Step key '{step.key}' can only contain lowercase letters, numbers, and underscores")
            
            # Validate step-specific requirements
            if step.type == "llm_generate":
                if not step.prompt_template:
                    errors.append(f"LLM step '{step.key}' must have a prompt template")
                
                if not step.model_preference:
                    errors.append(f"LLM step '{step.key}' must specify model preference")
            
            elif step.type == "user_input":
                if not step.input_schema:
                    errors.append(f"User input step '{step.key}' must have an input schema")
        
        return errors
    
    def _validate_dependencies(self, template: PipelineTemplate) -> List[str]:
        """Validate step dependencies."""
        errors = []
        step_keys = {step.key for step in template.steps}
        
        for step in template.steps:
            for dep in step.depends_on:
                if dep not in step_keys:
                    errors.append(f"Step '{step.key}' depends on non-existent step '{dep}'")
                
                # Check for circular dependencies
                if self._has_circular_dependency(template, step.key, dep):
                    errors.append(f"Circular dependency detected involving step '{step.key}'")
        
        return errors
    
    def _has_circular_dependency(self, template: PipelineTemplate, start_step: str, current_step: str, visited: Optional[set] = None) -> bool:
        """Check for circular dependencies."""
        if visited is None:
            visited = set()
        
        if current_step in visited:
            return current_step == start_step
        
        if current_step == start_step and len(visited) > 0:
            return True
        
        visited.add(current_step)
        
        # Find current step and check its dependencies
        for step in template.steps:
            if step.key == current_step:
                for dep in step.depends_on:
                    if self._has_circular_dependency(template, start_step, dep, visited.copy()):
                        return True
                break
        
        return False
    
    def _validate_business_rules(self, template: PipelineTemplate) -> List[str]:
        """Validate business-specific rules."""
        errors = []
        
        # Rule: Must have at least one LLM step
        llm_steps = [step for step in template.steps if step.type == "llm_generate"]
        if len(llm_steps) == 0:
            errors.append("Pipeline must have at least one LLM generation step")
        
        # Rule: Cannot have more than 5 consecutive LLM steps
        consecutive_llm = 0
        for step in template.steps:
            if step.type == "llm_generate":
                consecutive_llm += 1
                if consecutive_llm > 5:
                    errors.append("Cannot have more than 5 consecutive LLM steps")
                    break
            else:
                consecutive_llm = 0
        
        # Rule: Final step should produce output
        if template.steps and template.steps[-1].type not in ["llm_generate", "transform"]:
            errors.append("Final step should produce output content")
        
        return errors
    
    def _check_performance_warnings(self, template: PipelineTemplate) -> List[str]:
        """Check for performance warnings."""
        warnings = []
        
        # Warning: Many LLM steps may be slow
        llm_steps = [step for step in template.steps if step.type == "llm_generate"]
        if len(llm_steps) > 10:
            warnings.append(f"Pipeline has {len(llm_steps)} LLM steps, which may be slow to execute")
        
        # Warning: Complex dependency chains
        max_chain_length = self._calculate_max_dependency_chain(template)
        if max_chain_length > 5:
            warnings.append(f"Complex dependency chain detected (max length: {max_chain_length})")
        
        return warnings
    
    def _calculate_max_dependency_chain(self, template: PipelineTemplate) -> int:
        """Calculate maximum dependency chain length."""
        step_deps = {step.key: set(step.depends_on) for step in template.steps}
        max_length = 0
        
        for step_key in step_deps:
            length = self._calculate_chain_length(step_key, step_deps, set())
            max_length = max(max_length, length)
        
        return max_length
    
    def _calculate_chain_length(self, step_key: str, step_deps: dict, visited: set) -> int:
        """Calculate dependency chain length for a step."""
        if step_key in visited:
            return 0
        
        visited.add(step_key)
        
        if step_key not in step_deps:
            return 1
        
        max_deps_length = 0
        for dep in step_deps[step_key]:
            deps_length = self._calculate_chain_length(dep, step_deps, visited.copy())
            max_deps_length = max(max_deps_length, deps_length)
        
        return 1 + max_deps_length
    
    def _calculate_validation_score(self, errors: List[str], warnings: List[str]) -> float:
        """Calculate validation score (0.0 to 1.0)."""
        # Simple scoring: start with 1.0, subtract for errors and warnings
        score = 1.0
        score -= len(errors) * 0.5  # Each error reduces score by 0.5
        score -= len(warnings) * 0.1  # Each warning reduces score by 0.1
        
        return max(0.0, score)
```

### Repository Pattern

```python
# src/writeit/domains/pipeline/repositories/pipeline_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from writeit.domains.pipeline.entities import PipelineTemplate, PipelineRun
from writeit.domains.pipeline.value_objects import PipelineId

class PipelineRepository(ABC):
    """Abstract repository for pipeline operations."""
    
    @abstractmethod
    async def save_template(self, template: PipelineTemplate) -> None:
        """Save pipeline template."""
        pass
    
    @abstractmethod
    async def get_template(self, template_id: PipelineId) -> Optional[PipelineTemplate]:
        """Get pipeline template by ID."""
        pass
    
    @abstractmethod
    async def get_template_by_name(self, name: str, workspace_name: str) -> Optional[PipelineTemplate]:
        """Get pipeline template by name and workspace."""
        pass
    
    @abstractmethod
    async def list_templates(self, workspace_name: str) -> List[PipelineTemplate]:
        """List all templates in workspace."""
        pass
    
    @abstractmethod
    async def delete_template(self, template_id: PipelineId) -> None:
        """Delete pipeline template."""
        pass
    
    @abstractmethod
    async def save_run(self, run: PipelineRun) -> None:
        """Save pipeline run."""
        pass
    
    @abstractmethod
    async def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Get pipeline run by ID."""
        pass
    
    @abstractmethod
    async def list_runs(self, workspace_name: str, limit: int = 50) -> List[PipelineRun]:
        """List pipeline runs in workspace."""
        pass

# Implementation
# src/writeit/infrastructure/repositories/pipeline_repository_impl.py
import asyncio
from typing import List, Optional, Dict, Any
from writeit.infrastructure.persistence.lmdb_storage import LMDBStorageManager
from writeit.domains.pipeline.repositories import PipelineRepository
from writeit.domains.pipeline.entities import PipelineTemplate, PipelineRun
from writeit.domains.pipeline.value_objects import PipelineId

class LMDBPipelineRepository(PipelineRepository):
    """LMDB implementation of pipeline repository."""
    
    def __init__(self, storage_manager: LMDBStorageManager):
        self.storage = storage_manager
        self._template_cache = {}
        self._run_cache = {}
    
    async def save_template(self, template: PipelineTemplate) -> None:
        """Save pipeline template to LMDB."""
        # Serialize template
        template_data = self._serialize_template(template)
        
        # Save to storage
        await self.storage.store_json(
            f"pipeline_templates/{template.id.value}",
            template_data,
            db_name="templates"
        )
        
        # Update cache
        self._template_cache[template.id.value] = template
    
    async def get_template(self, template_id: PipelineId) -> Optional[PipelineTemplate]:
        """Get pipeline template from LMDB."""
        # Check cache first
        if template_id.value in self._template_cache:
            return self._template_cache[template_id.value]
        
        # Load from storage
        template_data = await self.storage.load_json(
            f"pipeline_templates/{template_id.value}",
            db_name="templates"
        )
        
        if not template_data:
            return None
        
        # Deserialize
        template = self._deserialize_template(template_data)
        
        # Update cache
        self._template_cache[template_id.value] = template
        
        return template
    
    async def get_template_by_name(self, name: str, workspace_name: str) -> Optional[PipelineTemplate]:
        """Get pipeline template by name and workspace."""
        # This would require an index or scan in real implementation
        # For now, implement simple scan
        templates = await self.list_templates(workspace_name)
        for template in templates:
            if template.name == name:
                return template
        return None
    
    async def list_templates(self, workspace_name: str) -> List[PipelineTemplate]:
        """List all templates in workspace."""
        # In real implementation, this would use proper indexing
        # For now, return cached templates
        return list(self._template_cache.values())
    
    async def delete_template(self, template_id: PipelineId) -> None:
        """Delete pipeline template."""
        # Remove from storage
        await self.storage.delete(
            f"pipeline_templates/{template_id.value}",
            db_name="templates"
        )
        
        # Remove from cache
        self._template_cache.pop(template_id.value, None)
    
    def _serialize_template(self, template: PipelineTemplate) -> Dict[str, Any]:
        """Serialize template for storage."""
        return {
            "id": template.id.value,
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "metadata": template.metadata,
            "inputs": template.inputs,
            "steps": [self._serialize_step(step) for step in template.steps],
            "defaults": template.defaults,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "created_by": template.created_by
        }
    
    def _deserialize_template(self, data: Dict[str, Any]) -> PipelineTemplate:
        """Deserialize template from storage."""
        return PipelineTemplate(
            id=PipelineId(data["id"]),
            name=data["name"],
            description=data["description"],
            version=data["version"],
            metadata=data["metadata"],
            inputs=data["inputs"],
            steps=[self._deserialize_step(step_data) for step_data in data["steps"]],
            defaults=data["defaults"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            created_by=data["created_by"]
        )
    
    def _serialize_step(self, step) -> Dict[str, Any]:
        """Serialize step for storage."""
        return {
            "key": step.key,
            "name": step.name,
            "description": step.description,
            "type": step.type.value,
            "model_preference": step.model_preference,
            "prompt_template": step.prompt_template.value if step.prompt_template else None,
            "depends_on": step.depends_on,
            "validation": step.validation
        }
    
    def _deserialize_step(self, data: Dict[str, Any]):
        """Deserialize step from storage."""
        return PipelineStepTemplate(
            key=data["key"],
            name=data["name"],
            description=data["description"],
            type=StepType(data["type"]),
            model_preference=data["model_preference"],
            prompt_template=PromptTemplate(data["prompt_template"]) if data["prompt_template"] else None,
            depends_on=data["depends_on"],
            validation=data["validation"]
        )
```

---

## 🔌 API Development

### REST API Development

```python
# src/writeit/infrastructure/web/endpoints/pipeline_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from writeit.application.commands.pipeline_commands import (
    CreatePipelineCommand,
    ExecutePipelineCommand,
    GetPipelineQuery
)
from writeit.application.services import PipelineApplicationService
from writeit.shared.container import Container

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

def get_pipeline_service() -> PipelineApplicationService:
    """Dependency injection for pipeline service."""
    container = Container()
    return container.get(PipelineApplicationService)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    request: Dict[str, Any],
    service: PipelineApplicationService = Depends(get_pipeline_service)
):
    """Create a new pipeline from configuration."""
    try:
        command = CreatePipelineCommand(
            pipeline_path=request["pipeline_path"],
            workspace_name=request.get("workspace_name", "default")
        )
        
        pipeline = await service.create_pipeline(command)
        
        return {
            "id": pipeline.id.value,
            "name": pipeline.name,
            "description": pipeline.description,
            "version": pipeline.version,
            "created_at": pipeline.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create pipeline: {str(e)}"
        )

@router.get("/{pipeline_id}", response_model=Dict[str, Any])
async def get_pipeline(
    pipeline_id: str,
    workspace_name: str = "default",
    service: PipelineApplicationService = Depends(get_pipeline_service)
):
    """Get pipeline configuration."""
    try:
        query = GetPipelineQuery(
            pipeline_id=PipelineId(pipeline_id),
            workspace_name=workspace_name
        )
        
        pipeline = await service.get_pipeline(query)
        
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )
        
        return {
            "id": pipeline.id.value,
            "name": pipeline.name,
            "description": pipeline.description,
            "version": pipeline.version,
            "metadata": pipeline.metadata,
            "inputs": pipeline.inputs,
            "steps": [
                {
                    "key": step.key,
                    "name": step.name,
                    "description": step.description,
                    "type": step.type.value,
                    "depends_on": step.depends_on
                }
                for step in pipeline.steps
            ],
            "defaults": pipeline.defaults,
            "created_at": pipeline.created_at.isoformat(),
            "updated_at": pipeline.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline: {str(e)}"
        )

@router.post("/{pipeline_id}/execute", response_model=Dict[str, Any])
async def execute_pipeline(
    pipeline_id: str,
    request: Dict[str, Any],
    service: PipelineApplicationService = Depends(get_pipeline_service)
):
    """Execute pipeline with inputs."""
    try:
        command = ExecutePipelineCommand(
            pipeline_id=PipelineId(pipeline_id),
            inputs=request.get("inputs", {}),
            workspace_name=request.get("workspace_name", "default"),
            execution_mode=request.get("execution_mode", "async")
        )
        
        result = await service.execute_pipeline(command)
        
        return {
            "run_id": result.id,
            "pipeline_id": result.pipeline_id.value,
            "status": result.status.value,
            "created_at": result.created_at.isoformat(),
            "steps": [
                {
                    "step_key": step.step_key,
                    "status": step.status.value,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
                for step in result.steps
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute pipeline: {str(e)}"
        )
```

### WebSocket Development

```python
# src/writeit/infrastructure/web/websocket_manager.py
import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from writeit.shared.events import EventBus, DomainEvent

class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.run_connections: Dict[str, Set[str]] = {}
        
        # Subscribe to relevant events
        self.event_bus.subscribe("PipelineExecutionStarted", self._on_pipeline_started)
        self.event_bus.subscribe("StepExecutionCompleted", self._on_step_completed)
        self.event_bus.subscribe("PipelineExecutionCompleted", self._on_pipeline_completed)
    
    async def connect(self, websocket: WebSocket, run_id: str):
        """Accept WebSocket connection and subscribe to run updates."""
        await websocket.accept()
        
        # Add to connections
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        
        # Track run connections
        if run_id not in self.run_connections:
            self.run_connections[run_id] = set()
        
        connection_id = id(websocket)
        self.run_connections[run_id].add(connection_id)
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connected",
            "connection_id": connection_id,
            "run_id": run_id,
            "timestamp": asyncio.get_event_loop().time()
        }, websocket)
    
    async def disconnect(self, websocket: WebSocket, run_id: str):
        """Handle WebSocket disconnection."""
        if run_id in self.active_connections:
            self.active_connections[run_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        
        connection_id = id(websocket)
        if run_id in self.run_connections:
            self.run_connections[run_id].discard(connection_id)
            
            # Clean up empty sets
            if not self.run_connections[run_id]:
                del self.run_connections[run_id]
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Connection may be closed
            pass
    
    async def broadcast_to_run(self, run_id: str, message: Dict):
        """Broadcast message to all connections subscribed to a run."""
        if run_id in self.active_connections:
            # Create copy of connections list to avoid modification during iteration
            connections = self.active_connections[run_id].copy()
            
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Remove failed connection
                    await self.disconnect(connection, run_id)
    
    async def _on_pipeline_started(self, event: DomainEvent):
        """Handle pipeline started event."""
        await self.broadcast_to_run(event.run_id, {
            "type": "pipeline_started",
            "pipeline_id": event.pipeline_id,
            "run_id": event.run_id,
            "timestamp": event.timestamp.isoformat()
        })
    
    async def _on_step_completed(self, event: DomainEvent):
        """Handle step completed event."""
        await self.broadcast_to_run(event.run_id, {
            "type": "step_completed",
            "step_key": event.step_key,
            "step_name": event.step_name,
            "execution_time": event.execution_time,
            "tokens_used": event.tokens_used.__dict__ if event.tokens_used else None,
            "timestamp": event.timestamp.isoformat()
        })
    
    async def _on_pipeline_completed(self, event: DomainEvent):
        """Handle pipeline completed event."""
        await self.broadcast_to_run(event.run_id, {
            "type": "pipeline_completed",
            "run_id": event.run_id,
            "status": event.status,
            "total_time": event.total_time,
            "total_tokens": event.total_tokens,
            "outputs": event.outputs,
            "timestamp": event.timestamp.isoformat()
        })

# WebSocket endpoint
# src/writeit/infrastructure/web/websocket_endpoints.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from writeit.infrastructure.web.websocket_manager import WebSocketManager
from writeit.shared.container import Container

router = APIRouter()

def get_websocket_manager() -> WebSocketManager:
    """Dependency injection for WebSocket manager."""
    container = Container()
    return container.get(WebSocketManager)

@router.websocket("/ws/{run_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    run_id: str,
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """WebSocket endpoint for real-time pipeline updates."""
    await manager.connect(websocket, run_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client messages
            await handle_client_message(message, websocket, run_id, manager)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, run_id)

async def handle_client_message(
    message: Dict,
    websocket: WebSocket,
    run_id: str,
    manager: WebSocketManager
):
    """Handle incoming WebSocket messages from client."""
    message_type = message.get("type")
    
    if message_type == "user_selection":
        # Handle user response selection
        step_key = message.get("step_key")
        selected_response = message.get("selected_response")
        user_feedback = message.get("user_feedback")
        
        # Process selection through application service
        # This would interact with the pipeline execution service
        
    elif message_type == "pause_run":
        # Handle pipeline pause request
        pass
        
    elif message_type == "resume_run":
        # Handle pipeline resume request
        pass
        
    elif message_type == "cancel_run":
        # Handle pipeline cancellation
        pass
```

### Middleware Development

```python
# src/writeit/infrastructure/web/middleware/cors_middleware.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI application."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response information."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "x_request_id": request.headers.get("x-request-id")
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url} - {response.status_code}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time,
                "x_request_id": request.headers.get("x-request-id")
            }
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Handle errors and return appropriate responses."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled error: {str(e)}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "x_request_id": request.headers.get("x-request-id")
                },
                exc_info=True
            )
            
            # Return user-friendly error response
            from fastapi import HTTPException
            
            if isinstance(e, HTTPException):
                raise e
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error occurred"
                )
```

---

## 💻 CLI Development

### CLI Command Development

```python
# src/writeit/infrastructure/cli/commands/pipeline_commands.py
import typer
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncio

from writeit.application.commands.pipeline_commands import ExecutePipelineCommand
from writeit.application.services import PipelineApplicationService
from writeit.shared.container import Container
from writeit.cli.output import print_success, print_error, print_info

app = typer.Typer(
    name="pipeline",
    help="Pipeline management commands",
    rich_markup_mode="rich"
)

console = Console()

def get_pipeline_service() -> PipelineApplicationService:
    """Get pipeline service with dependency injection."""
    container = Container()
    return container.get(PipelineApplicationService)

@app.command()
def list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
    format: str = typer.Option("table", "--format", help="Output format (table, json)"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace name")
):
    """List available pipeline templates."""
    try:
        service = get_pipeline_service()
        
        # Get pipelines from workspace
        pipelines = asyncio.run(service.list_pipelines(workspace or "default"))
        
        if format == "json":
            import json
            output = [
                {
                    "id": p.id.value,
                    "name": p.name,
                    "description": p.description,
                    "version": p.version,
                    "steps": len(p.steps),
                    "created_at": p.created_at.isoformat()
                }
                for p in pipelines
            ]
            console.print(json.dumps(output, indent=2))
        else:
            # Create rich table
            table = Table(title="Available Pipelines")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="magenta")
            table.add_column("Version", style="green")
            table.add_column("Steps", style="yellow", justify="right")
            
            if verbose:
                table.add_column("Created", style="blue")
                table.add_column("ID", style="dim")
            
            for pipeline in pipelines:
                row = [
                    pipeline.name,
                    pipeline.description,
                    pipeline.version,
                    str(len(pipeline.steps))
                ]
                
                if verbose:
                    row.extend([
                        pipeline.created_at.strftime("%Y-%m-%d %H:%M"),
                        pipeline.id.value[:8] + "..."
                    ])
                
                table.add_row(*row)
            
            console.print(table)
            
    except Exception as e:
        print_error(f"Failed to list pipelines: {str(e)}")
        raise typer.Exit(1)

@app.command()
def run(
    pipeline_path: str = typer.Argument(..., help="Path to pipeline YAML file"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace name"),
    inputs: Optional[str] = typer.Option(None, "--inputs", "-i", help="Pipeline inputs (JSON or key=value pairs)"),
    tui: bool = typer.Option(False, "--tui", help="Use TUI interface"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Execute a pipeline template."""
    try:
        service = get_pipeline_service()
        
        # Parse inputs
        pipeline_inputs = {}
        if inputs:
            try:
                # Try to parse as JSON first
                import json
                pipeline_inputs = json.loads(inputs)
            except json.JSONDecodeError:
                # Parse as key=value pairs
                for pair in inputs.split(','):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        pipeline_inputs[key.strip()] = value.strip()
        
        # Create command
        command = ExecutePipelineCommand(
            pipeline_path=Path(pipeline_path),
            inputs=pipeline_inputs,
            workspace_name=workspace or "default",
            execution_mode="tui" if tui else "cli",
            dry_run=dry_run
        )
        
        if dry_run:
            # Show execution plan
            print_info("Dry run execution plan:")
            pipeline = asyncio.run(service.validate_pipeline(command))
            
            table = Table(title="Execution Plan")
            table.add_column("Step", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Dependencies", style="yellow")
            table.add_column("Model", style="green")
            
            for step in pipeline.steps:
                table.add_row(
                    step.key,
                    step.type.value,
                    ", ".join(step.depends_on) if step.depends_on else "None",
                    step.model_preference[0] if step.model_preference else "Default"
                )
            
            console.print(table)
            return
        
        if tui:
            # Launch TUI interface
            from writeit.tui.app import run_pipeline_tui
            asyncio.run(run_pipeline_tui(command, service))
        else:
            # Execute with CLI interface
            result = asyncio.run(execute_pipeline_cli(command, service, verbose))
            
            print_success(f"Pipeline execution completed: {result.status}")
            
            if result.outputs:
                console.print(Panel.fit(
                    f"[bold green]Outputs:[/bold green]\n{result.outputs}",
                    title="Pipeline Results"
                ))
                
    except Exception as e:
        print_error(f"Pipeline execution failed: {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)

async def execute_pipeline_cli(
    command: ExecutePipelineCommand,
    service: PipelineApplicationService,
    verbose: bool
):
    """Execute pipeline with CLI interface and progress reporting."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        
        # Show initial progress
        task = progress.add_task("Starting pipeline execution...", total=None)
        
        # Execute pipeline
        result = await service.execute_pipeline(command)
        
        # Update progress
        progress.update(task, description=f"Pipeline {result.status.value}")
        
        # Show step progress
        if verbose:
            for step in result.steps:
                status_icon = "✓" if step.status.value == "completed" else "✗"
                console.print(f"  {status_icon} {step.key}: {step.status.value}")
                
                if step.execution_time:
                    console.print(f"    Time: {step.execution_time:.2f}s")
                
                if step.tokens_used:
                    console.print(f"    Tokens: {step.tokens_used.total_tokens}")
        
        return result

@app.command()
def validate(
    template_name: str = typer.Argument(..., help="Template name to validate"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace name"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed validation results")
):
    """Validate a pipeline template."""
    try:
        service = get_pipeline_service()
        
        result = asyncio.run(service.validate_template(
            template_name,
            workspace or "default"
        ))
        
        if result.is_valid:
            print_success(f"Template '{template_name}' is valid")
            
            if detailed:
                console.print(Panel.fit(
                    f"Validation Score: {result.score:.2f}\n"
                    f"Warnings: {len(result.warnings)}",
                    title="Validation Details"
                ))
                
                if result.warnings:
                    console.print("\n[yellow]Warnings:[/yellow]")
                    for warning in result.warnings:
                        console.print(f"  • {warning}")
        else:
            print_error(f"Template '{template_name}' has validation errors")
            
            console.print("\n[red]Errors:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            
            if detailed and result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")
            
            raise typer.Exit(1)
            
    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        raise typer.Exit(1)
```

### CLI Output Management

```python
# src/writeit/infrastructure/cli/output.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.tree import Tree
from typing import Any, Dict, List, Optional
import sys

# Global console instance
console = Console()

def print_success(message: str, title: Optional[str] = None):
    """Print success message."""
    if title:
        console.print(Panel.fit(
            f"[green]✓[/green] {message}",
            title=title,
            border_style="green"
        ))
    else:
        console.print(f"[green]✓[/green] {message}")

def print_error(message: str, title: Optional[str] = None):
    """Print error message."""
    if title:
        console.print(Panel.fit(
            f"[red]✗[/red] {message}",
            title=title,
            border_style="red"
        ))
    else:
        console.print(f"[red]✗[/red] {message}")

def print_warning(message: str, title: Optional[str] = None):
    """Print warning message."""
    if title:
        console.print(Panel.fit(
            f"[yellow]⚠[/yellow] {message}",
            title=title,
            border_style="yellow"
        ))
    else:
        console.print(f"[yellow]⚠[/yellow] {message}")

def print_info(message: str, title: Optional[str] = None):
    """Print info message."""
    if title:
        console.print(Panel.fit(
            f"[blue]ℹ[/blue] {message}",
            title=title,
            border_style="blue"
        ))
    else:
        console.print(f"[blue]ℹ[/blue] {message}")

def create_workspace_table(workspaces: List[Dict[str, Any]]) -> Table:
    """Create a rich table for workspace listing."""
    table = Table(title="Workspaces")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta")
    table.add_column("Active", style="green")
    table.add_column("Created", style="blue")
    table.add_column("Size", style="yellow", justify="right")
    
    for workspace in workspaces:
        active_indicator = "✓" if workspace.get("is_active") else ""
        
        table.add_row(
            workspace["name"],
            workspace["path"],
            active_indicator,
            workspace.get("created_at", "Unknown"),
            format_size(workspace.get("size", 0))
        )
    
    return table

def create_pipeline_table(pipelines: List[Dict[str, Any]], verbose: bool = False) -> Table:
    """Create a rich table for pipeline listing."""
    table = Table(title="Pipelines")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Steps", style="yellow", justify="right")
    
    if verbose:
        table.add_column("Created", style="blue")
        table.add_column("ID", style="dim")
    
    for pipeline in pipelines:
        row = [
            pipeline["name"],
            pipeline["description"],
            pipeline["version"],
            str(pipeline.get("steps", 0))
        ]
        
        if verbose:
            row.extend([
                pipeline.get("created_at", "Unknown"),
                pipeline.get("id", "")[:8] + "..." if len(pipeline.get("id", "")) > 8 else pipeline.get("id", "")
            ])
        
        table.add_row(*row)
    
    return table

def create_progress_bar(description: str, total: Optional[int] = None) -> Progress:
    """Create a progress bar with spinner."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True
    )

def create_directory_tree(path: str, max_depth: int = 3) -> Tree:
    """Create a directory tree visualization."""
    tree = Tree(f"📁 {path}")
    
    try:
        import os
        from pathlib import Path
        
        def add_directory(current_tree: Tree, current_path: Path, depth: int = 0):
            if depth >= max_depth:
                return
            
            try:
                for item in sorted(current_path.iterdir()):
                    if item.is_dir():
                        if not item.name.startswith('.'):
                            subtree = current_tree.add(f"📁 {item.name}/")
                            add_directory(subtree, item, depth + 1)
                    else:
                        current_tree.add(f"📄 {item.name}")
            except PermissionError:
                current_tree.add("[dim]🔒 Permission denied[/dim]")
        
        add_directory(tree, Path(path))
        
    except Exception as e:
        tree.add(f"[red]Error: {str(e)}[/red]")
    
    return tree

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def confirm_with_style(
    message: str,
    default: bool = False,
    abort: bool = True
) -> bool:
    """Show styled confirmation prompt."""
    from rich.prompt import Confirm
    
    result = Confirm.ask(message, default=default)
    
    if not result and abort:
        print_error("Operation cancelled")
        sys.exit(1)
    
    return result

def create_workspace_info_table(workspace_info: Dict[str, Any]) -> Table:
    """Create a detailed workspace information table."""
    table = Table(title=f"Workspace: {workspace_info['name']}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")
    
    # Basic info
    table.add_row("Name", workspace_info["name"])
    table.add_row("Path", workspace_info["path"])
    table.add_row("Active", "✓" if workspace_info.get("is_active") else "✗")
    
    if "created_at" in workspace_info:
        table.add_row("Created", workspace_info["created_at"])
    
    if "updated_at" in workspace_info:
        table.add_row("Updated", workspace_info["updated_at"])
    
    # Storage info
    if "storage" in workspace_info:
        storage = workspace_info["storage"]
        table.add_row("Storage Size", format_size(storage.get("size", 0)))
        table.add_row("Pipeline Runs", str(storage.get("pipeline_runs", 0)))
        table.add_row("Cache Entries", str(storage.get("cache_entries", 0)))
    
    # Configuration
    if "config" in workspace_info:
        config = workspace_info["config"]
        if "description" in config:
            table.add_row("Description", config["description"])
        
        if "template_paths" in config:
            paths = "\n".join(config["template_paths"])
            table.add_row("Template Paths", paths)
    
    return table

def print_json_output(data: Any, pretty: bool = True):
    """Print JSON output with optional pretty formatting."""
    import json
    
    if pretty:
        console.print_json(data=data)
    else:
        console.print(json.dumps(data))

def print_yaml_output(data: Any):
    """Print YAML output."""
    try:
        import yaml
        console.print(yaml.dump(data, default_flow_style=False))
    except ImportError:
        print_error("PyYAML not installed. Cannot output YAML.")
        print_json_output(data)
```

---

## 📋 Best Practices

### Code Quality

**Type Hints:**
```python
# Always use type hints
from typing import List, Dict, Optional, AsyncGenerator

def process_items(items: List[str]) -> Dict[str, int]:
    """Process list of items and return counts."""
    return {item: items.count(item) for item in set(items)}
```

**Documentation:**
```python
def validate_pipeline(
    template: PipelineTemplate,
    strict: bool = False
) -> ValidationResult:
    """
    Validate pipeline template against business rules.
    
    Args:
        template: The pipeline template to validate
        strict: Whether to use strict validation rules
        
    Returns:
        ValidationResult with validation status and errors
        
    Raises:
        ValueError: If template is None or invalid
        ValidationError: If validation fails catastrophically
        
    Example:
        >>> result = validate_pipeline(template, strict=True)
        >>> if result.is_valid:
        ...     print("Template is valid")
    """
```

**Error Handling:**
```python
# Use specific exception types
class PipelineValidationError(Exception):
    """Raised when pipeline validation fails."""
    pass

# Handle exceptions appropriately
try:
    result = await service.execute_pipeline(command)
except PipelineValidationError as e:
    print_error(f"Validation error: {e}")
    return None
except Exception as e:
    print_error(f"Unexpected error: {e}")
    logger.error("Pipeline execution failed", exc_info=True)
    return None
```

### Performance

**Async/Await Best Practices:**
```python
# Use async for I/O operations
async def fetch_data(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()

# Avoid blocking operations in async code
async def process_file(file_path: str) -> List[str]:
    # Bad: Blocking file read
    # data = open(file_path).read()
    
    # Good: Async file read
    async with aiofiles.open(file_path, 'r') as f:
        data = await f.read()
    
    return data.splitlines()
```

**Memory Management:**
```python
# Use generators for large datasets
def process_large_file(file_path: str) -> AsyncGenerator[str, None]:
    """Process large file line by line."""
    async with aiofiles.open(file_path, 'r') as f:
        async for line in f:
            yield line.strip()

# Use context managers for resource cleanup
async def with_database_connection():
    async with DatabaseConnection() as conn:
        yield conn
```

**Caching:**
```python
# Implement caching for expensive operations
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=1000)
def get_pipeline_template(template_id: str) -> Optional[PipelineTemplate]:
    """Get pipeline template with caching."""
    return database.get_template(template_id)

# Time-based cache invalidation
def cached_with_ttl(ttl: timedelta):
    """Decorator for time-based caching."""
    def decorator(func):
        cache = {}
        
        def wrapper(*args):
            key = (args, tuple(kwargs.items()))
            
            if key in cache:
                result, timestamp = cache[key]
                if datetime.now() - timestamp < ttl:
                    return result
            
            result = func(*args)
            cache[key] = (result, datetime.now())
            return result
        
        return wrapper
    return decorator
```

### Security

**Input Validation:**
```python
# Always validate user inputs
def validate_workspace_name(name: str) -> str:
    """Validate and normalize workspace name."""
    if not name or len(name.strip()) == 0:
        raise ValueError("Workspace name cannot be empty")
    
    if len(name) > 50:
        raise ValueError("Workspace name too long")
    
    # Sanitize input
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    if not sanitized:
        raise ValueError("Invalid workspace name")
    
    return sanitized.lower()
```

**Path Security:**
```python
# Prevent path traversal attacks
import os
from pathlib import Path

def safe_join(base_path: Path, user_path: str) -> Path:
    """Safely join paths preventing traversal."""
    try:
        # Resolve to absolute path
        full_path = (base_path / user_path).resolve()
        
        # Ensure result is within base path
        if not str(full_path).startswith(str(base_path.resolve())):
            raise ValueError("Path traversal detected")
        
        return full_path
    except (ValueError, OSError):
        raise ValueError("Invalid path")
```

**API Key Management:**
```python
# Use environment variables for sensitive data
import os
from typing import Optional

def get_api_key(provider: str) -> Optional[str]:
    """Get API key from environment variables."""
    key_name = f"{provider.upper()}_API_KEY"
    return os.getenv(key_name)

# Never log sensitive data
import logging

def log_api_call(endpoint: str, response_time: float):
    """Log API call without sensitive data."""
    logger.info(
        f"API call to {endpoint} completed in {response_time:.2f}s"
        # Never log request/response bodies with sensitive data
    )
```

### Testing

**Test Organization:**
```python
# Group related tests in classes
class TestPipelineExecution:
    """Test suite for pipeline execution functionality."""
    
    def setup_method(self):
        """Setup test data before each test."""
        self.template = create_test_pipeline()
        self.service = create_test_service()
    
    def test_successful_execution(self):
        """Test successful pipeline execution."""
        result = self.service.execute_pipeline(self.template, {})
        
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.steps) > 0
    
    def test_step_failure_handling(self):
        """Test handling of step failures."""
        # Setup failing step
        self.template.steps[0].should_fail = True
        
        result = self.service.execute_pipeline(self.template, {})
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None
```

**Mock Usage:**
```python
# Use mocks for external dependencies
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.mark.asyncio
async def test_llm_provider_call():
    """Test LLM provider with mocked client."""
    # Create mock
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    
    # Inject mock
    provider = OpenAIProvider(api_key="test")
    provider.client = mock_client
    
    # Test
    result = await provider.call_model("Test prompt", "gpt-4o-mini")
    
    assert result == "Test response"
    mock_client.chat.completions.create.assert_called_once()
```

**Fixtures:**
```python
# Use fixtures for reusable test data
@pytest.fixture
def sample_workspace():
    """Create sample workspace for testing."""
    return Workspace(
        name="test-workspace",
        path="/tmp/test-workspace"
    )

@pytest.fixture
def sample_pipeline(sample_workspace):
    """Create sample pipeline in workspace."""
    return PipelineTemplate(
        name="test-pipeline",
        workspace_id=sample_workspace.id,
        steps=[create_test_step()]
    )

@pytest.fixture
def mock_storage():
    """Mock storage for testing."""
    storage = MagicMock()
    storage.save_pipeline.return_value = None
    storage.load_pipeline.return_value = None
    return storage
```

---

## 🤝 Contributing

### Contribution Guidelines

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/writeit.git
   cd writeit
   ```

2. **Setup Development Environment**
   ```bash
   uv sync
   uv run writeit init
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation
   - Follow commit message format

5. **Test Changes**
   ```bash
   uv run pytest tests/
   uv run ruff check src/ tests/
   uv run mypy src/
   ```

6. **Submit Pull Request**
   - Clear description of changes
   - Link to relevant issues
   - Ensure CI checks pass
   - Request review from maintainers

### Code Style

**Python Style Guidelines:**
- Follow PEP 8
- Use Black for code formatting
- Use isort for import sorting
- Use mypy for type checking
- Maximum line length: 88 characters

**Imports:**
```python
# Standard library imports first
import os
import sys
from typing import List, Dict

# Third-party imports second
import pytest
from fastapi import FastAPI
from rich.console import Console

# Local imports third
from writeit.domains.pipeline.entities import PipelineTemplate
from writeit.application.services import PipelineApplicationService
```

**Docstrings:**
```python
def process_pipeline(
    pipeline: PipelineTemplate,
    inputs: Dict[str, Any],
    workspace: str = "default"
) -> PipelineResult:
    """
    Process a pipeline template with given inputs.
    
    Args:
        pipeline: The pipeline template to process
        inputs: Input values for the pipeline
        workspace: Target workspace name
        
    Returns:
        PipelineResult containing execution results
        
    Raises:
        PipelineValidationError: If pipeline validation fails
        ExecutionError: If pipeline execution fails
        
    Example:
        >>> result = process_pipeline(template, {"topic": "AI"})
        >>> print(result.status)
    """
```

### Pull Request Process

1. **Title Format**
   ```
   feat: add new pipeline execution mode
   fix: resolve workspace creation race condition
   docs: update API documentation
   ```

2. **Description**
   - What changes were made and why
   - How to test the changes
   - Any breaking changes
   - Related issues

3. **Checklist**
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] All tests pass
   - [ ] Type checking passes
   - [ ] No security vulnerabilities

### Issue Reporting

**Bug Reports:**
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment information
- Relevant logs/error messages

**Feature Requests:**
- Problem statement
- Proposed solution
- Use cases
- Alternative approaches considered

**Documentation Issues:**
- What documentation is unclear
- Suggested improvements
- Missing information

### Community Guidelines

- **Be respectful** in all interactions
- **Be constructive** in feedback
- **Be helpful** to newcomers
- **Be patient** with different skill levels
- **Be inclusive** of all contributors

---

This developer guide provides comprehensive information for working with WriteIt. Follow these guidelines to ensure high-quality contributions and maintainable code. For additional questions, refer to the existing codebase or reach out to the maintainers.