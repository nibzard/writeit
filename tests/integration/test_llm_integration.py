#!/usr/bin/env python3
"""Test script to verify LLM integration works without the TUI."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import llm
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass 
class PipelineStep:
    key: str
    name: str
    description: str
    type: str
    prompt_template: str
    model_preference: Any = None
    validation: Dict[str, Any] = field(default_factory=dict)

def test_llm_basic():
    """Test basic LLM functionality."""
    print("Testing basic LLM functionality...")
    try:
        model = llm.get_model("gpt-4o-mini")
        response = model.prompt("Say hello in exactly 5 words")
        print(f"✅ LLM Response: {response.text()}")
        return True
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return False

def test_template_rendering():
    """Test prompt template rendering."""
    print("\nTesting template rendering...")
    
    # Create a mock step
    step = PipelineStep(
        key="test",
        name="Test Step",
        description="Test step for template rendering",
        type="llm_generation",
        prompt_template="Write about: {{ inputs.topic }} for {{ inputs.audience }}. Use {{ defaults.word_count }} words.",
        model_preference="gpt-4o-mini"
    )
    
    # Mock user inputs and defaults
    user_inputs = {"topic": "AI", "audience": "beginners"}
    defaults = {"word_count": "500"}
    
    # Render template
    template = step.prompt_template
    for key, value in user_inputs.items():
        template = template.replace(f"{{{{ inputs.{key} }}}}", str(value))
    for key, value in defaults.items():
        template = template.replace(f"{{{{ defaults.{key} }}}}", str(value))
    
    print(f"✅ Rendered template: {template}")
    return template

def test_pipeline_config():
    """Test loading the quick-article pipeline config."""
    print("\nTesting pipeline config loading...")
    try:
        config_path = Path.home() / ".writeit" / "templates" / "quick-article.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            print(f"✅ Loaded pipeline: {config_data['metadata']['name']}")
            print(f"   Steps: {list(config_data['steps'].keys())}")
            return config_data
        else:
            print(f"❌ Config file not found: {config_path}")
            return None
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        return None

async def test_full_step_execution():
    """Test executing a single step with LLM."""
    print("\nTesting full step execution...")
    
    # Load pipeline config
    config_path = Path.home() / ".writeit" / "templates" / "quick-article.yaml"
    if not config_path.exists():
        print("❌ Pipeline config not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        step_config = config["steps"]["plan"]  # First step
        
        # Mock inputs
        user_inputs = {"topic": "Machine Learning", "audience": "general"}
        
        # Render template
        template = step_config["prompt_template"]
        for key, value in user_inputs.items():
            template = template.replace(f"{{{{ inputs.{key} }}}}", str(value))
        for key, value in config["defaults"].items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    template = template.replace(f"{{{{ defaults.{key}.{sub_key} }}}}", str(sub_value))
            else:
                template = template.replace(f"{{{{ defaults.{key} }}}}", str(value))
        
        print(f"Rendered prompt:\n{template[:200]}...")
        
        # Get model and make call
        model_name = step_config.get("model_preference", "gpt-4o-mini")
        if isinstance(model_name, list):
            model_name = model_name[0] 
        if "{{" in str(model_name):
            model_name = "gpt-4o-mini"
        
        print(f"Using model: {model_name}")
        model = llm.get_model(model_name)
        response = model.prompt(template)
        
        print(f"✅ Response received ({len(response.text())} chars)")
        print(f"First 100 chars: {response.text()[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Step execution error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing WriteIt LLM Integration\n")
    
    # Test 1: Basic LLM
    basic_ok = test_llm_basic()
    
    # Test 2: Template rendering
    template = test_template_rendering()
    
    # Test 3: Pipeline config
    config = test_pipeline_config()
    
    # Test 4: Full step execution (async)
    if basic_ok and config:
        print("\n🚀 Testing full step execution...")
        asyncio.run(test_full_step_execution())
    
    print("\n✅ Testing complete!")
