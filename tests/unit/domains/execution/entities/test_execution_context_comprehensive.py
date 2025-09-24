"""Comprehensive unit tests for ExecutionContext entity."""

import pytest
from datetime import datetime
from src.writeit.domains.execution.entities.execution_context import (
    ExecutionContext, ExecutionStatus, ExecutionPriority
)
from src.writeit.domains.execution.value_objects.execution_mode import ExecutionMode
from tests.builders.execution_builders import ExecutionContextBuilder


class TestExecutionContext:
    """Test cases for ExecutionContext entity."""
    
    def test_execution_context_creation(self):
        """Test creating execution context with valid data."""
        context = ExecutionContextBuilder.cli_context().build()
        
        assert context.id == "cli_context"
        assert context.workspace_name == "test_workspace"
        assert context.execution_mode == ExecutionMode.cli()
        assert context.status == ExecutionStatus.CREATED
        assert context.priority == ExecutionPriority.NORMAL
        assert context.cache_enabled is True
        assert context.streaming_enabled is False
        assert isinstance(context.created_at, datetime)

    def test_tui_context_creation(self):
        """Test creating TUI execution context."""
        context = ExecutionContextBuilder.tui_context().build()
        
        assert context.execution_mode == ExecutionMode.tui()

    def test_server_context_creation(self):
        """Test creating server execution context."""
        context = ExecutionContextBuilder.server_context().build()
        
        assert context.execution_mode == ExecutionMode.server()


class TestExecutionContextEdgeCases:
    """Test edge cases for ExecutionContext."""
    
    def test_execution_context_validation(self):
        """Test ExecutionContext validation."""
        with pytest.raises(ValueError, match="Execution context id must be a non-empty string"):
            ExecutionContext(
                id="",
                workspace_name="test",
                pipeline_id="test",
                execution_mode=ExecutionMode.cli()
            )
        
        with pytest.raises(ValueError, match="Workspace name must be a non-empty string"):
            ExecutionContext(
                id="test",
                workspace_name="",
                pipeline_id="test",
                execution_mode=ExecutionMode.cli()
            )
        
        with pytest.raises(TypeError, match="Execution mode must be an ExecutionMode"):
            ExecutionContext(
                id="test",
                workspace_name="test",
                pipeline_id="test",
                execution_mode="invalid"  # type: ignore
            )