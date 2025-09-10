#!/usr/bin/env python3
"""Demo script showing CLI mode capabilities."""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def create_demo_pipeline():
    """Create a demo pipeline for testing."""
    return """
metadata:
  name: "Demo CLI Pipeline"
  description: "Demonstrates CLI mode execution"
  version: "1.0.0"
  author: "WriteIt Team"

inputs:
  topic:
    type: "text"
    label: "Article Topic"
    required: true
    help: "What would you like to write about?"
  
  audience:
    type: "choice"
    label: "Target Audience"
    default: "general"
    options:
      - value: "general"
        label: "General readers"
      - value: "technical"
        label: "Technical audience"
    required: true

  urgency:
    type: "choice"
    label: "Urgency Level"
    default: "normal"
    options:
      - value: "low"
        label: "Low priority"
      - value: "normal" 
        label: "Normal priority"
      - value: "high"
        label: "High priority"
    required: false

steps:
  outline:
    name: "Create Outline"
    description: "Generate a structured outline"
    type: "llm_generation"
    prompt_template: |
      Create an outline for: {{topic}}
      Target audience: {{audience}}
      Priority: {{urgency}}
    model_preference: ["gpt-4"]
""".strip()

def demo_cli_vs_tui():
    """Demonstrate the difference between CLI and TUI modes."""
    print("🚀 WriteIt CLI Mode Demo")
    print("=" * 50)
    
    # Create a temporary pipeline
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(create_demo_pipeline())
        pipeline_path = f.name
    
    # Copy to WriteIt templates directory
    writeit_templates = Path.home() / ".writeit" / "templates"
    demo_pipeline_path = writeit_templates / "demo-cli.yaml"
    
    try:
        if writeit_templates.exists():
            with open(demo_pipeline_path, 'w') as f:
                f.write(create_demo_pipeline())
        
        print("\n📋 Available Execution Modes:")
        print("1. TUI Mode (default): Interactive, visual interface")
        print("   Command: uv run writeit run demo-cli")
        print()
        print("2. CLI Mode: Simple prompts, automation-friendly")  
        print("   Command: uv run writeit run demo-cli --cli")
        print()
        
        print("🔍 Pipeline Details:")
        print(f"- Pipeline: Demo CLI Pipeline")
        print(f"- Inputs: 3 (topic, audience, urgency)")
        print(f"- Steps: 1 (outline generation)")
        print(f"- Location: {demo_pipeline_path}")
        print()
        
        print("💡 CLI Mode Features:")
        print("✓ Simple text prompts")
        print("✓ Numbered option selection")
        print("✓ Yes/no confirmations")
        print("✓ Progress indicators")
        print("✓ Token usage tracking")
        print("✓ Step-by-step execution")
        print("✓ Error handling with continue/abort options")
        print()
        
        print("🚀 Try it yourself:")
        print("uv run writeit run demo-cli --cli")
        print()
        print("Example input sequence:")
        print('1. Topic: "Python Best Practices"')
        print('2. Audience: 2 (technical)')
        print('3. Urgency: 1 (low)')
        print('4. Execute step: y')
        print()
        
    finally:
        # Cleanup
        if os.path.exists(pipeline_path):
            os.unlink(pipeline_path)
        if demo_pipeline_path.exists():
            demo_pipeline_path.unlink()

if __name__ == "__main__":
    demo_cli_vs_tui()
