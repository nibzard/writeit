#!/usr/bin/env python3
"""Integration test for CLI pipeline mode."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

# Add src to path  
sys.path.insert(0, 'src')

def create_simple_pipeline_config():
    """Create a simple pipeline config for testing."""
    config = """
metadata:
  name: "Test CLI Pipeline"
  description: "Simple test pipeline for CLI mode"
  version: "1.0.0"
  author: "Test"

inputs:
  topic:
    type: "text"
    label: "What's your topic?"
    required: true
    help: "Enter the main topic for your content"
  
  format:
    type: "choice" 
    label: "Output format"
    default: "article"
    options:
      - value: "article"
        label: "Article"
      - value: "summary"
        label: "Summary"
    required: true

steps:
  outline:
    name: "Create Outline"
    description: "Generate an outline for the content"
    type: "llm_generation"
    prompt_template: "Create an outline for: {{topic}} in {{format}} format"
    model_preference: ["gpt-4"]
"""
    return config.strip()

def test_cli_command_parsing():
    """Test that the CLI command parsing works correctly."""
    print("=== Testing CLI Command Integration ===")
    
    # Create a temporary pipeline file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(create_simple_pipeline_config())
        pipeline_path = f.name
    
    try:
        from writeit.cli.commands.pipeline import run
        
        print("✓ CLI command imports successfully")
        
        # Test that the CLI flag is recognized (we can't actually execute without LLM setup)
        # But we can verify the function signature accepts our new parameter
        import inspect
        sig = inspect.signature(run)
        assert 'cli_mode' in sig.parameters, "cli_mode parameter not found in run function"
        
        print("✓ CLI mode parameter is properly defined")
        print("✓ CLI integration test passed")
        
    finally:
        # Clean up
        os.unlink(pipeline_path)

def test_pipeline_config_loading():
    """Test that pipeline config loading works for CLI."""
    print("\n=== Testing Pipeline Config Loading ===")
    
    from writeit.cli.pipeline_runner import CLIPipelineRunner
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(create_simple_pipeline_config())
        pipeline_path = Path(f.name)
    
    try:
        # Create runner and test loading
        runner = CLIPipelineRunner(pipeline_path, "default")
        runner.load_pipeline()
        
        # Verify loaded config
        config = runner.pipeline_config
        assert config.metadata['name'] == "Test CLI Pipeline"
        assert len(config.inputs) == 2
        assert len(config.steps) == 1
        
        # Check input types
        topic_input = next(inp for inp in config.inputs if inp.key == 'topic')
        assert topic_input.type == 'text'
        assert topic_input.required == True
        
        format_input = next(inp for inp in config.inputs if inp.key == 'format') 
        assert format_input.type == 'choice'
        assert len(format_input.options) == 2
        
        # Check step
        outline_step = config.steps[0]
        assert outline_step.key == 'outline'
        assert outline_step.type == 'llm_generation'
        
        print("✓ Pipeline config loads correctly")
        print("✓ Input types are parsed correctly")
        print("✓ Steps are configured properly")
        
    finally:
        os.unlink(pipeline_path)

def test_prompt_building():
    """Test that prompt template building works."""
    print("\n=== Testing Prompt Template Building ===")
    
    from writeit.cli.pipeline_runner import CLIPipelineRunner
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(create_simple_pipeline_config())
        pipeline_path = Path(f.name)
    
    try:
        runner = CLIPipelineRunner(pipeline_path, "default")
        runner.load_pipeline()
        
        # Set test values
        runner.pipeline_values = {
            'topic': 'Python Programming',
            'format': 'article'
        }
        
        # Test prompt building
        template = "Create an outline for: {{topic}} in {{format}} format"
        built_prompt = runner._build_prompt(template)
        expected = "Create an outline for: Python Programming in article format"
        
        assert built_prompt == expected, f"Expected '{expected}', got '{built_prompt}'"
        
        print("✓ Prompt template substitution works correctly")
        
    finally:
        os.unlink(pipeline_path)

if __name__ == "__main__":
    test_cli_command_parsing()
    test_pipeline_config_loading()  
    test_prompt_building()
    print("\n🎉 All CLI integration tests passed!")
