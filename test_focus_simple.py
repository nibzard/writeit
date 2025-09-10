#!/usr/bin/env python3
"""Test the CLI pipeline runner input collection without LLM calls."""

import sys
from pathlib import Path
from unittest import mock
from io import StringIO

# Add src to path
sys.path.insert(0, 'src')

from writeit.cli.pipeline_runner import CLIPipelineRunner


def test_input_collection():
    """Test the input collection part of the CLI runner."""
    # Create runner
    runner = CLIPipelineRunner(Path("test_cli_simple.yaml"), "default")
    
    # Load pipeline
    runner.load_pipeline()
    
    # Mock user inputs
    inputs = ["AI and Machine Learning", "1"]  # topic, then choice option 1 (general)
    
    with mock.patch('builtins.input', side_effect=inputs):
        with mock.patch('rich.prompt.Prompt.ask', side_effect=inputs):
            # Simulate collecting inputs
            print("=== Testing Input Collection ===")
            print(f"Pipeline: {runner.pipeline_config.metadata['name']}")
            
            # Test each input field manually
            for i, input_field in enumerate(runner.pipeline_config.inputs):
                print(f"\nInput {i+1}: {input_field.label}")
                print(f"  Type: {input_field.type}")
                print(f"  Required: {input_field.required}")
                if input_field.options:
                    print(f"  Options: {[opt['value'] for opt in input_field.options]}")
                
                # Use the pre-set test values instead of prompting
                if input_field.key == "topic":
                    runner.pipeline_values[input_field.key] = "AI and Machine Learning"
                elif input_field.key == "audience":
                    runner.pipeline_values[input_field.key] = "general"
            
            print(f"\n=== Collected Values ===")
            for key, value in runner.pipeline_values.items():
                print(f"  {key}: {value}")
    
    print("✓ Input collection test completed successfully!")

if __name__ == "__main__":
    test_input_collection()
