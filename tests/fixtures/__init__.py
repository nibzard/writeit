"""Test fixtures for WriteIt domain testing.

This module provides comprehensive test fixtures for all domain entities,
value objects, and aggregates used in WriteIt's domain-driven architecture.

The fixtures are organized by domain and provide both simple and complex
test scenarios to support comprehensive unit testing.
"""

from .pipeline import *
from .workspace import *
from .content import *
from .execution import *
from .value_objects import *

__all__ = [
    # Pipeline fixtures
    "pipeline_id_fixture",
    "step_id_fixture", 
    "pipeline_template_fixture",
    "pipeline_run_fixture",
    "step_execution_fixture",
    "valid_pipeline_template",
    "invalid_pipeline_template",
    "multi_step_pipeline",
    
    # Workspace fixtures
    "workspace_fixture",
    "workspace_configuration_fixture",
    "valid_workspace",
    "invalid_workspace",
    
    # Content fixtures
    "template_fixture",
    "style_primer_fixture",
    "generated_content_fixture",
    "valid_template",
    "invalid_template",
    
    # Execution fixtures
    "llm_provider_fixture",
    "execution_context_fixture", 
    "token_usage_fixture",
    "valid_llm_provider",
    "invalid_llm_provider",
    
    # Value object fixtures
    "all_value_object_fixtures"
]