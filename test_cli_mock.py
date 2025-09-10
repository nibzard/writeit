#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, 'src')

from writeit.cli.pipeline_runner import CLIPipelineRunner

class MockLLMResponse:
    def __init__(self, text="Mock LLM response"):
        self.text = text
        self.usage = MagicMock()
        self.usage.prompt_tokens = 100
        self.usage.completion_tokens = 50

async def test_cli_runner():
    """Test CLI runner with mocked LLM."""
    
    # Create mock pipeline runner
    runner = CLIPipelineRunner(Path("test_cli_simple.yaml"), "default")
    
    # Mock the LLM model
    mock_model = MagicMock()
    mock_model.prompt = MagicMock(return_value=MockLLMResponse("This is a test plan for your topic."))
    
    # Mock the _get_llm_model method
    runner._get_llm_model = MagicMock(return_value=mock_model)
    
    # Mock user inputs by pre-setting pipeline values
    runner.pipeline_values = {
        "topic": "Python programming",
        "audience": "general"
    }
    
    try:
        # Load pipeline
        runner.load_pipeline()
        print("✓ Pipeline loaded successfully")
        
        # Show what inputs would be collected
        print(f"Pipeline: {runner.pipeline_config.metadata['name']}")
        print(f"Inputs: {len(runner.pipeline_config.inputs)}")
        for inp in runner.pipeline_config.inputs:
            print(f"  - {inp.label} ({inp.type}): {runner.pipeline_values.get(inp.key, 'Not set')}")
        
        # Show steps
        print(f"Steps: {len(runner.pipeline_config.steps)}")
        for step in runner.pipeline_config.steps:
            print(f"  - {step.name}: {step.type}")
        
        # Test pipeline execution (but skip actual execution for now)
        print("✓ Mock test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(test_cli_runner()))
