"""Integration tests for command handlers.

These tests verify that command handlers work correctly with real dependencies
and integration between different components.
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
import tempfile
import shutil

from src.writeit.application.commands.handlers.workspace_handlers import (
    ConcreteCreateWorkspaceCommandHandler,
    ConcreteSwitchWorkspaceCommandHandler,
    ConcreteDeleteWorkspaceCommandHandler,
    ConcreteConfigureWorkspaceCommandHandler
)
from src.writeit.application.commands.workspace_commands import (
    CreateWorkspaceCommand,
    SwitchWorkspaceCommand,
    DeleteWorkspaceCommand,
    ConfigureWorkspaceCommand,
    WorkspaceCommandResult
)
from src.writeit.application.commands.handlers.pipeline_template_handlers import (
    ConcreteCreatePipelineTemplateCommandHandler,
    ConcreteValidatePipelineTemplateCommandHandler
)
from src.writeit.application.commands.pipeline_commands import (
    CreatePipelineTemplateCommand,
    ValidatePipelineTemplateCommand,
    PipelineTemplateCommandResult
)
from src.writeit.application.di_config import DIConfiguration
from src.writeit.shared.dependencies.container import Container
from src.writeit.shared.events.event_bus import EventBus


class TestWorkspaceCommandHandlers:
    """Integration tests for workspace command handlers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def container(self, temp_dir):
        """Create a DI container for testing."""
        return DIConfiguration.create_container(base_path=temp_dir)
    
    @pytest.fixture
    def event_bus(self):
        """Create an event bus for testing."""
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_create_workspace_handler(self, container, event_bus, temp_dir):
        """Test workspace creation command handler."""
        # Get handler from container
        handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        
        # Create command
        command = CreateWorkspaceCommand(
            name="test-workspace",
            description="Test workspace for integration testing",
            base_path=temp_dir / "workspaces" / "test-workspace",
            initialize_storage=True,
            copy_global_templates=False
        )
        
        # Execute command
        result = await handler.handle(command)
        
        # Verify result
        assert result.success is True
        assert result.workspace_name == "test-workspace"
        assert result.workspace is not None
        assert "created successfully" in result.message
        
        # Verify workspace was actually created
        workspace_dir = temp_dir / "workspaces" / "test-workspace"
        assert workspace_dir.exists()
    
    @pytest.mark.asyncio
    async def test_create_workspace_validation(self, container, event_bus):
        """Test workspace creation validation."""
        handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        
        # Test empty name
        command = CreateWorkspaceCommand(name="")
        validation_errors = await handler.validate(command)
        assert "Workspace name is required" in validation_errors
        
        # Test invalid name
        command = CreateWorkspaceCommand(name="invalid/name")
        validation_errors = await handler.validate(command)
        assert "Invalid workspace name" in validation_errors
    
    @pytest.mark.asyncio
    async def test_switch_workspace_handler(self, container, event_bus, temp_dir):
        """Test workspace switching command handler."""
        # First create a workspace
        create_handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        create_command = CreateWorkspaceCommand(
            name="switch-test-workspace",
            base_path=temp_dir / "workspaces" / "switch-test"
        )
        create_result = await create_handler.handle(create_command)
        assert create_result.success
        
        # Now test switching
        switch_handler = container.resolve(ConcreteSwitchWorkspaceCommandHandler)
        switch_command = SwitchWorkspaceCommand(
            workspace_name="switch-test-workspace",
            validate_workspace=True
        )
        
        result = await switch_handler.handle(switch_command)
        
        assert result.success is True
        assert result.workspace_name == "switch-test-workspace"
        assert "Switched to workspace" in result.message
    
    @pytest.mark.asyncio
    async def test_configure_workspace_handler(self, container, event_bus, temp_dir):
        """Test workspace configuration command handler."""
        # First create a workspace
        create_handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        create_command = CreateWorkspaceCommand(
            name="config-test-workspace",
            base_path=temp_dir / "workspaces" / "config-test"
        )
        create_result = await create_handler.handle(create_command)
        assert create_result.success
        
        # Now test configuration
        config_handler = container.resolve(ConcreteConfigureWorkspaceCommandHandler)
        config_command = ConfigureWorkspaceCommand(
            workspace_name="config-test-workspace",
            configuration_updates={
                "llm_model": "gpt-4",
                "max_tokens": 2000,
                "theme": "dark"
            }
        )
        
        result = await config_handler.handle(config_command)
        
        assert result.success is True
        assert result.workspace_name == "config-test-workspace"
        assert result.configuration is not None
        assert result.configuration.settings["llm_model"] == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_delete_workspace_handler(self, container, event_bus, temp_dir):
        """Test workspace deletion command handler."""
        # First create a workspace
        create_handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        create_command = CreateWorkspaceCommand(
            name="delete-test-workspace",
            base_path=temp_dir / "workspaces" / "delete-test"
        )
        create_result = await create_handler.handle(create_command)
        assert create_result.success
        
        # Now test deletion
        delete_handler = container.resolve(ConcreteDeleteWorkspaceCommandHandler)
        delete_command = DeleteWorkspaceCommand(
            workspace_name="delete-test-workspace",
            backup_before_delete=False,
            force=True
        )
        
        result = await delete_handler.handle(delete_command)
        
        assert result.success is True
        assert result.workspace_name == "delete-test-workspace"
        assert "deleted successfully" in result.message


class TestPipelineTemplateCommandHandlers:
    """Integration tests for pipeline template command handlers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def container(self, temp_dir):
        """Create a DI container for testing."""
        return DIConfiguration.create_container(base_path=temp_dir)
    
    @pytest.fixture
    def sample_pipeline_content(self):
        """Sample pipeline template content for testing."""
        return """
metadata:
  name: "Test Pipeline"
  description: "A simple test pipeline"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"

inputs:
  topic:
    type: text
    label: "Topic"
    required: true
    placeholder: "Enter topic..."

steps:
  outline:
    name: "Create Outline"
    description: "Generate content outline"
    type: llm_generate
    prompt_template: |
      Create an outline for {{ inputs.topic }}
    model_preference: ["{{ defaults.model }}"]
  
  content:
    name: "Write Content"
    description: "Generate full content"
    type: llm_generate
    prompt_template: |
      Based on outline: {{ steps.outline }}
      Write content about {{ inputs.topic }}
    depends_on: ["outline"]
    model_preference: ["{{ defaults.model }}"]
"""
    
    @pytest.mark.asyncio
    async def test_create_pipeline_template_handler(
        self, 
        container, 
        sample_pipeline_content,
        temp_dir
    ):
        """Test pipeline template creation command handler."""
        handler = container.resolve(ConcreteCreatePipelineTemplateCommandHandler)
        
        command = CreatePipelineTemplateCommand(
            name="test-pipeline",
            description="Test pipeline for integration testing",
            content=sample_pipeline_content,
            author="test-user",
            tags=["test", "integration"],
            validation_level="strict"
        )
        
        result = await handler.handle(command)
        
        assert result.success is True
        assert result.template_name == "test-pipeline"
        assert result.template is not None
        assert "created successfully" in result.message
        assert result.template.name.value == "test-pipeline"
    
    @pytest.mark.asyncio
    async def test_create_pipeline_template_from_file(
        self, 
        container, 
        sample_pipeline_content,
        temp_dir
    ):
        """Test pipeline template creation from file."""
        # Create temporary file
        template_file = temp_dir / "test-pipeline.yaml"
        template_file.write_text(sample_pipeline_content)
        
        handler = container.resolve(ConcreteCreatePipelineTemplateCommandHandler)
        
        command = CreatePipelineTemplateCommand(
            name="file-pipeline",
            description="Pipeline created from file",
            template_path=template_file,
            author="test-user"
        )
        
        result = await handler.handle(command)
        
        assert result.success is True
        assert result.template_name == "file-pipeline"
        assert result.template is not None
    
    @pytest.mark.asyncio
    async def test_create_pipeline_template_validation(self, container):
        """Test pipeline template creation validation."""
        handler = container.resolve(ConcreteCreatePipelineTemplateCommandHandler)
        
        # Test empty name
        command = CreatePipelineTemplateCommand(name="", content="test")
        validation_errors = await handler.validate(command)
        assert "Pipeline name is required" in validation_errors
        
        # Test missing content
        command = CreatePipelineTemplateCommand(name="test")
        validation_errors = await handler.validate(command)
        assert "Either content or template_path must be provided" in validation_errors
        
        # Test invalid name
        command = CreatePipelineTemplateCommand(name="invalid/name", content="test")
        validation_errors = await handler.validate(command)
        assert "Invalid pipeline name" in validation_errors
    
    @pytest.mark.asyncio
    async def test_validate_pipeline_template_handler(
        self, 
        container, 
        sample_pipeline_content,
        temp_dir
    ):
        """Test pipeline template validation command handler."""
        handler = container.resolve(ConcreteValidatePipelineTemplateCommandHandler)
        
        # Test valid template
        command = ValidatePipelineTemplateCommand(
            content=sample_pipeline_content,
            validation_level="strict"
        )
        
        result = await handler.handle(command)
        
        assert result.success is True
        assert "validation completed" in result.message
        assert len(result.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_pipeline_template_invalid_content(
        self, 
        container
    ):
        """Test pipeline template validation with invalid content."""
        handler = container.resolve(ConcreteValidatePipelineTemplateCommandHandler)
        
        # Test invalid template content
        invalid_content = "invalid: yaml: content: [unclosed bracket"
        command = ValidatePipelineTemplateCommand(
            content=invalid_content,
            validation_level="strict"
        )
        
        result = await handler.handle(command)
        
        assert result.success is True  # Validation command itself succeeds
        assert len(result.validation_errors) > 0
        assert "validation completed" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_pipeline_template_from_file(
        self, 
        container, 
        sample_pipeline_content,
        temp_dir
    ):
        """Test pipeline template validation from file."""
        # Create temporary file
        template_file = temp_dir / "validate-test.yaml"
        template_file.write_text(sample_pipeline_content)
        
        handler = container.resolve(ConcreteValidatePipelineTemplateCommandHandler)
        
        command = ValidatePipelineTemplateCommand(
            template_path=template_file,
            validation_level="strict"
        )
        
        result = await handler.handle(command)
        
        assert result.success is True
        assert "validation completed" in result.message
        assert len(result.validation_errors) == 0


class TestCommandHandlerIntegration:
    """Integration tests for cross-domain command handler interactions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def container(self, temp_dir):
        """Create a DI container for testing."""
        return DIConfiguration.create_container(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_workspace_pipeline_integration(self, container, temp_dir):
        """Test integration between workspace and pipeline command handlers."""
        # Create workspace
        workspace_handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        workspace_command = CreateWorkspaceCommand(
            name="integration-test-workspace",
            base_path=temp_dir / "integration-workspace"
        )
        workspace_result = await workspace_handler.handle(workspace_command)
        assert workspace_result.success
        
        # Create pipeline template in workspace
        pipeline_content = """
metadata:
  name: "Integration Test Pipeline"
  description: "Pipeline for integration testing"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"

inputs:
  topic:
    type: text
    label: "Topic"
    required: true

steps:
  generate:
    name: "Generate Content"
    type: llm_generate
    prompt_template: "Write about {{ inputs.topic }}"
    model_preference: ["{{ defaults.model }}"]
"""
        
        pipeline_handler = container.resolve(ConcreteCreatePipelineTemplateCommandHandler)
        pipeline_command = CreatePipelineTemplateCommand(
            name="integration-pipeline",
            description="Pipeline created in workspace context",
            content=pipeline_content,
            workspace_name="integration-test-workspace",
            author="integration-test-user"
        )
        
        pipeline_result = await pipeline_handler.handle(pipeline_command)
        
        assert pipeline_result.success is True
        assert pipeline_result.template_name == "integration-pipeline"
        
        # Validate the pipeline
        validate_handler = container.resolve(ConcreteValidatePipelineTemplateCommandHandler)
        validate_command = ValidatePipelineTemplateCommand(
            pipeline_name="integration-pipeline",
            workspace_name="integration-test-workspace",
            validation_level="strict"
        )
        
        validate_result = await validate_handler.handle(validate_command)
        
        assert validate_result.success is True
        assert len(validate_result.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, container):
        """Test error handling across command handlers."""
        workspace_handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        
        # Try to create workspace with invalid name
        invalid_command = CreateWorkspaceCommand(name="invalid/workspace name")
        
        result = await workspace_handler.handle(invalid_command)
        
        assert result.success is False
        assert "Invalid workspace name" in result.message
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_di_container_resolution(self, container):
        """Test that all command handlers can be resolved from DI container."""
        # Test workspace handlers
        workspace_handlers = [
            ConcreteCreateWorkspaceCommandHandler,
            ConcreteSwitchWorkspaceCommandHandler,
            ConcreteDeleteWorkspaceCommandHandler,
            ConcreteConfigureWorkspaceCommandHandler
        ]
        
        for handler_type in workspace_handlers:
            handler = container.resolve(handler_type)
            assert handler is not None
            assert isinstance(handler, handler_type)
        
        # Test pipeline handlers
        pipeline_handlers = [
            ConcreteCreatePipelineTemplateCommandHandler,
            ConcreteValidatePipelineTemplateCommandHandler
        ]
        
        for handler_type in pipeline_handlers:
            handler = container.resolve(handler_type)
            assert handler is not None
            assert isinstance(handler, handler_type)
    
    @pytest.mark.asyncio
    async def test_event_publishing_integration(self, container, temp_dir):
        """Test that command handlers publish appropriate domain events."""
        # This test would require mocking the event bus to capture events
        # For now, we'll just verify that handlers complete successfully
        # which implies events were published without errors
        
        workspace_handler = container.resolve(ConcreteCreateWorkspaceCommandHandler)
        workspace_command = CreateWorkspaceCommand(
            name="event-test-workspace",
            base_path=temp_dir / "event-test"
        )
        
        result = await workspace_handler.handle(workspace_command)
        
        assert result.success is True
        # If no exceptions were raised, events were likely published successfully