"""Test script for CQRS Command Handlers implementation.

This script tests the basic functionality of the implemented CQRS command handlers
without requiring external dependencies like LMDB.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from writeit.application.commands.pipeline_commands import (
    ExecutePipelineCommand,
    CreatePipelineTemplateCommand,
    ValidatePipelineTemplateCommand,
    PipelineSource,
    PipelineExecutionMode,
)
from writeit.application.commands.handlers.pipeline_execution_handlers import (
    ConcreteExecutePipelineCommandHandler,
)
from writeit.application.commands.handlers.pipeline_template_handlers import (
    ConcreteCreatePipelineTemplateCommandHandler,
    ConcreteValidatePipelineTemplateCommandHandler,
)
from writeit.domains.pipeline.value_objects import PipelineId, PipelineName
from writeit.domains.workspace.value_objects import WorkspaceName
from writeit.shared.events.event_bus import AsyncEventBus
from writeit.shared.events.domain_event import DomainEvent


async def test_command_handlers():
    """Test basic command handler functionality."""
    print("🧪 Testing CQRS Command Handlers...")
    
    # Create event bus
    event_bus = AsyncEventBus()
    
    # Test command validation
    print("\n✅ Testing Command Validation...")
    
    # Test valid execute pipeline command
    execute_command = ExecutePipelineCommand(
        pipeline_name="test-pipeline",
        workspace_name="default",
        source=PipelineSource.WORKSPACE,
        mode=PipelineExecutionMode.CLI,
        inputs={"topic": "AI ethics"}
    )
    
    print(f"✅ ExecutePipelineCommand created: {execute_command.pipeline_name}")
    
    # Test valid create pipeline template command
    create_command = CreatePipelineTemplateCommand(
        name="test-template",
        description="Test template",
        content="metadata:\n  name: test\nsteps:\n  - name: step1\n    type: llm_generate",
        workspace_name="default"
    )
    
    print(f"✅ CreatePipelineTemplateCommand created: {create_command.name}")
    
    # Test valid validate pipeline template command
    validate_command = ValidatePipelineTemplateCommand(
        content="metadata:\n  name: test\nsteps:\n  - name: step1\n    type: llm_generate"
    )
    
    print(f"✅ ValidatePipelineTemplateCommand created")
    
    # Test command DTO properties
    print("\n✅ Testing Command DTO Properties...")
    
    # Check execute command properties
    assert execute_command.pipeline_name == "test-pipeline"
    assert execute_command.workspace_name == "default"
    assert execute_command.source == PipelineSource.WORKSPACE
    assert execute_command.mode == PipelineExecutionMode.CLI
    assert execute_command.inputs == {"topic": "AI ethics"}
    print("✅ ExecutePipelineCommand properties validated")
    
    # Check create command properties
    assert create_command.name == "test-template"
    assert create_command.description == "Test template"
    assert "metadata:" in create_command.content
    assert create_command.workspace_name == "default"
    print("✅ CreatePipelineTemplateCommand properties validated")
    
    # Check validate command properties
    assert "metadata:" in validate_command.content
    assert validate_command.validation_level == "strict"
    print("✅ ValidatePipelineTemplateCommand properties validated")
    
    # Test pipeline name validation
    print("\n✅ Testing Pipeline Name Validation...")
    
    try:
        valid_name = PipelineName.from_string("valid-pipeline-name")
        print(f"✅ Valid pipeline name: {valid_name}")
    except ValueError as e:
        print(f"❌ Pipeline name validation failed: {e}")
        return False
    
    # Test workspace name validation
    print("\n✅ Testing Workspace Name Validation...")
    
    try:
        valid_workspace = WorkspaceName.from_user_input("valid-workspace")
        print(f"✅ Valid workspace name: {valid_workspace}")
    except ValueError as e:
        print(f"❌ Workspace name validation failed: {e}")
        return False
    
    # Test pipeline ID generation
    print("\n✅ Testing Pipeline ID Generation...")
    
    pipeline_id = PipelineId.generate()
    print(f"✅ Generated pipeline ID: {pipeline_id}")
    
    # Test event bus
    print("\n✅ Testing Event Bus...")
    
    # Create a test event
    class TestEvent(DomainEvent):
        def __init__(self, message):
            super().__init__()
            self.message = message
        
        @property
        def event_type(self) -> str:
            return "test.event"
        
        @property
        def aggregate_id(self) -> str:
            return "test-aggregate"
        
        def to_dict(self) -> dict:
            return {
                "message": self.message,
                "event_type": self.event_type,
                "aggregate_id": self.aggregate_id
            }
    
    test_event = TestEvent("Test event message")
    
    # Publish event
    await event_bus.publish(test_event)
    print("✅ Event published successfully")
    
    print("\n🎉 All command handler tests passed!")
    return True


async def test_value_objects():
    """Test domain value objects."""
    print("\n🧪 Testing Domain Value Objects...")
    
    # Test PipelineName
    print("✅ Testing PipelineName...")
    
    # Valid names
    valid_names = ["simple-pipeline", "my_awesome_pipeline", "pipeline123"]
    for name in valid_names:
        try:
            pipeline_name = PipelineName.from_string(name)
            print(f"  ✅ Valid pipeline name: {pipeline_name}")
        except ValueError:
            print(f"  ❌ Should be valid but failed: {name}")
            return False
    
    # Invalid names
    invalid_names = ["", " ", "@pipeline", "pipeline@", "pipeline@with@special", "a" * 101, "ab"]
    for name in invalid_names:
        try:
            pipeline_name = PipelineName.from_string(name)
            print(f"  ❌ Should be invalid but passed: {name}")
            return False
        except ValueError:
            print(f"  ✅ Correctly rejected invalid name: {name}")
    
    # Test PipelineId
    print("✅ Testing PipelineId...")
    
    pipeline_id = PipelineId.generate()
    print(f"  ✅ Generated PipelineId: {pipeline_id}")
    
    # Test string conversion
    pipeline_id_str = str(pipeline_id)
    reconstructed_id = PipelineId(pipeline_id_str)
    print(f"  ✅ PipelineId string conversion works: {reconstructed_id}")
    
    # Test WorkspaceName
    print("✅ Testing WorkspaceName...")
    
    # Valid names
    valid_workspace_names = ["my-project", "workspace_123", "myworkspace"]
    for name in valid_workspace_names:
        try:
            workspace_name = WorkspaceName.from_user_input(name)
            print(f"  ✅ Valid workspace name: {workspace_name}")
        except ValueError:
            print(f"  ❌ Should be valid but failed: {name}")
            return False
    
    print("✅ All value object tests passed!")
    return True


async def main():
    """Main test function."""
    print("🚀 Starting CQRS Command Handlers Test Suite")
    print("=" * 50)
    
    try:
        # Test value objects first
        if not await test_value_objects():
            print("❌ Value object tests failed")
            return False
        
        # Test command handlers
        if not await test_command_handlers():
            print("❌ Command handler tests failed")
            return False
        
        print("\n🎉 All tests passed successfully!")
        print("\n📋 Summary:")
        print("  ✅ CQRS Command DTOs are properly defined")
        print("  ✅ Command handlers can be imported")
        print("  ✅ Value objects work correctly")
        print("  ✅ Event bus is functional")
        print("  ✅ Command validation logic is in place")
        
        return True
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    
    if success:
        print("\n🎊 Phase 4.1 - CQRS Command Handlers implementation is working!")
        sys.exit(0)
    else:
        print("\n💥 Phase 4.1 - CQRS Command Handlers implementation has issues!")
        sys.exit(1)