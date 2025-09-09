# Developer Getting Started Guide

This guide will get you up and running with WriteIt development in under 15 minutes. WriteIt follows **Test-Driven Development (TDD)** and **library-first architecture** principles.

## 🚀 Quick Setup

### Prerequisites
- **Python 3.11+** (3.12 recommended)
- **Git** for version control
- **Terminal** with good color support
- **Text Editor** with Python LSP support (VS Code, PyCharm, Vim/Neovim)

### 1. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/writeIt/writeIt.git
cd writeIt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .[dev,test]

# Verify installation
writeit --version
```

### 2. Configure Development Environment
```bash
# Set up pre-commit hooks
pre-commit install

# Configure LLM providers (for testing)
llm keys set openai
llm keys set anthropic

# Initialize workspace
writeit init ~/dev-writeIt-workspace

# Run development tests
pytest tests/ -v
```

### 3. Verify Setup
```bash
# Run linting
ruff check src/ tests/
ruff format --check src/ tests/

# Run type checking
mypy src/

# Run full test suite
pytest tests/ --cov=src --cov-report=html

# Start development TUI
writeit run pipelines/tech-article.yaml
```

Expected output:
```
✅ All dependencies installed
✅ Pre-commit hooks configured
✅ Tests passing (X/X)
✅ Linting clean
✅ Type checking passed
✅ TUI starts without errors
```

## 🏗️ Project Structure

```
writeIt/
├── src/                    # Library-first architecture
│   ├── models/             # Data models (Pydantic)
│   ├── storage/            # LMDB storage layer
│   ├── llm/               # LLM integration
│   ├── pipeline/          # Pipeline engine
│   ├── server/            # FastAPI server
│   ├── tui/               # Textual interface
│   └── cli/               # Command-line entry
├── tests/                  # TDD test suite
│   ├── contract/          # API contract tests
│   ├── integration/       # End-to-end tests
│   └── unit/              # Library unit tests
├── docs/                   # Documentation
├── pipelines/             # Example configurations
├── styles/                # Writing style guides
├── pyproject.toml         # Project configuration
└── CLAUDE.md              # Development context
```

## 🧪 Test-Driven Development Workflow

WriteIt follows **strict TDD**: tests must be written first and must fail before implementation.

### TDD Cycle
```
1. 🔴 RED: Write failing test
2. 🟢 GREEN: Make test pass (minimal code)
3. 🔵 REFACTOR: Improve code while keeping tests green
4. 🔄 REPEAT: Next feature/requirement
```

### Example TDD Implementation
```bash
# 1. Start with failing contract test
cat > tests/contract/test_pipeline_start.py << 'EOF'
import pytest
from httpx import AsyncClient
from src.server.app import app

class TestPipelineStart:
    async def test_start_pipeline_success(self):
        """Test POST /pipeline/start returns 201 with run_id"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/pipeline/start", json={
                "pipeline_path": "pipelines/tech-article.yaml",
                "user_inputs": {
                    "source_material": "Test content",
                    "target_audience": "developers"
                }
            })
            
            # This MUST fail initially
            assert response.status_code == 201
            data = response.json()
            assert "pipeline_run_id" in data
            assert "first_step" in data
EOF

# 2. Run test - it should FAIL
pytest tests/contract/test_pipeline_start.py -v
# Expected: ImportError or 404 - endpoint doesn't exist yet

# 3. Implement minimal code to make test pass
mkdir -p src/server
cat > src/server/app.py << 'EOF'
from fastapi import FastAPI

app = FastAPI(title="WriteIt API")

@app.post("/pipeline/start")
async def start_pipeline(request: dict):
    return {
        "pipeline_run_id": "test-uuid",
        "first_step": {"step_name": "angles"}
    }
EOF

# 4. Run test - it should PASS now
pytest tests/contract/test_pipeline_start.py -v

# 5. Refactor with proper implementation
# ... implement real logic while keeping tests green
```

## 📚 Library-First Architecture

Every feature is implemented as a **standalone library** with CLI interface:

### Library Structure Template
```python
# src/storage/lmdb_store.py
"""
ABOUTME: LMDB storage interface for WriteIt pipeline data
ABOUTME: Provides CRUD operations with event sourcing support
"""

class LMDBStore:
    """Standalone LMDB storage library"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Implementation...
    
    async def store_pipeline_run(self, run: PipelineRun) -> None:
        """Store pipeline run with indexing"""
        # Implementation...

# CLI interface for library
def main():
    """CLI entry point for storage operations"""
    import argparse
    parser = argparse.ArgumentParser(description="WriteIt LMDB Storage")
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument("--format", choices=["json", "yaml"], default="json")
    # CLI implementation...

if __name__ == "__main__":
    main()
```

### Library Testing Template  
```python
# tests/unit/test_lmdb_store.py
"""Unit tests for LMDB storage library"""

class TestLMDBStore:
    @pytest.fixture
    def temp_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test.lmdb"
    
    async def test_store_pipeline_run(self, temp_db):
        """Test pipeline run storage and retrieval"""
        store = LMDBStore(temp_db)
        run = PipelineRun(pipeline_run_id=uuid4(), ...)
        
        await store.store_pipeline_run(run)
        retrieved = await store.get_pipeline_run(run.pipeline_run_id)
        
        assert retrieved == run
```

## 🔧 Development Tools

### Code Quality Tools
```bash
# Linting with Ruff
ruff check src/ tests/            # Check for issues
ruff check --fix src/ tests/      # Auto-fix issues
ruff format src/ tests/           # Format code

# Type checking with MyPy
mypy src/                         # Check types
mypy --strict src/                # Strict checking

# Testing with Pytest
pytest tests/                     # Run all tests
pytest tests/unit/                # Run unit tests only
pytest -k "test_pipeline"         # Run specific tests
pytest --cov=src --cov-report=html  # Coverage report
```

### Pre-commit Hooks
WriteIt uses pre-commit hooks to ensure code quality:

```yaml
# .pre-commit-config.yaml
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.6
  hooks:
  - id: ruff
    args: [--fix, --exit-non-zero-on-fix]
  - id: ruff-format

- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.7.1
  hooks:
  - id: mypy
    additional_dependencies: [types-PyYAML]

- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.5.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
```

### Development Scripts
```bash
# scripts/dev-setup.sh - Complete development setup
#!/bin/bash
set -e

echo "🚀 Setting up WriteIt development environment..."

# Install dependencies
pip install -e .[dev,test]

# Install pre-commit hooks
pre-commit install

# Initialize test workspace
mkdir -p ~/dev-writeIt-workspace
writeit init ~/dev-writeIt-workspace

# Run verification
echo "✅ Running verification tests..."
pytest tests/contract/ -v
ruff check src/ tests/
mypy src/

echo "🎉 Development environment ready!"
```

## 📖 Common Development Tasks

### Adding a New API Endpoint
```bash
# 1. Write contract test first
cat > tests/contract/test_new_endpoint.py << 'EOF'
async def test_new_endpoint():
    # Test that MUST fail initially
    response = await client.post("/new-endpoint")
    assert response.status_code == 200
EOF

# 2. Run test to confirm failure
pytest tests/contract/test_new_endpoint.py

# 3. Implement endpoint in src/server/
# 4. Run test to confirm success
# 5. Add integration test
# 6. Commit changes
```

### Adding a New Data Model
```bash
# 1. Write model test first
cat > tests/unit/test_new_model.py << 'EOF'
def test_new_model_validation():
    # Test that MUST fail initially
    model = NewModel(field="value")
    assert model.field == "value"
EOF

# 2. Implement model in src/models/
# 3. Add to __init__.py exports
# 4. Update related services
```

### Adding a New TUI Component
```bash
# 1. Write component test
cat > tests/integration/test_new_widget.py << 'EOF'
def test_new_widget_behavior():
    # Test widget behavior
    widget = NewWidget()
    # Assert behavior
EOF

# 2. Implement in src/tui/
# 3. Add to main app
# 4. Test interactively
```

## 🐛 Debugging

### Debug Configuration
```python
# Debug configuration for WriteIt
import logging
import asyncio

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Enable asyncio debug mode
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
loop = asyncio.new_event_loop()
loop.set_debug(True)
asyncio.set_event_loop(loop)
```

### Common Debug Commands
```bash
# Debug TUI with logging
TEXTUAL_LOG=debug writeit run pipelines/tech-article.yaml

# Debug API server
uvicorn src.server.app:app --reload --log-level debug

# Debug specific test with pdb
pytest tests/integration/test_pipeline.py -s --pdb

# Debug LMDB database
python -c "
import lmdb
env = lmdb.open('~/.writeit/data/events.lmdb')
with env.begin() as txn:
    for key, value in txn.cursor():
        print(f'{key}: {value}')
"
```

## 📈 Performance Profiling

### Memory Profiling
```bash
# Install profiling tools
pip install memory-profiler line-profiler

# Profile memory usage
python -m memory_profiler scripts/profile_memory.py

# Profile line by line
kernprof -l -v scripts/profile_performance.py
```

### TUI Performance
```bash
# Profile TUI performance
TEXTUAL_LOG=debug TEXTUAL_PROFILE=profile.html writeit run pipelines/tech-article.yaml

# View profiling results
open profile.html
```

## 🤝 Contributing Workflow

### 1. Feature Development
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Follow TDD workflow
# Write tests → Implement → Refactor → Commit

# Push feature branch
git push origin feature/your-feature-name
```

### 2. Code Review Process
```bash
# Before submitting PR:
pytest tests/ --cov=src             # All tests pass
ruff check src/ tests/              # Linting clean
mypy src/                          # Type checking passes
pre-commit run --all-files         # Pre-commit hooks pass

# Create pull request
gh pr create --title "Feature: Your feature description" --body "Detailed description"
```

### 3. Code Standards
- **Tests first**: Never implement without failing tests
- **Library-first**: Each feature as standalone library
- **No mocks**: Use real dependencies in tests
- **Documentation**: Update docs with code changes
- **Type hints**: All functions must have type annotations
- **Error handling**: Explicit error handling, no silent failures

## 🆘 Getting Help

### Internal Resources
- **Architecture docs**: `docs/architecture/`
- **API reference**: `docs/api/`
- **Example code**: `examples/`
- **Test patterns**: `tests/`

### External Resources
- **Textual docs**: https://textual.textualize.io/
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **LMDB docs**: https://lmdb.readthedocs.io/
- **pytest docs**: https://docs.pytest.org/

### Community
- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas  
- **Discord**: Real-time developer chat (link in README)

---

**Happy coding!** Remember: Tests first, libraries always, real dependencies only. 🚀