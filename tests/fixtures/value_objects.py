"""Value object fixtures for testing.

Provides comprehensive test fixtures for all value objects across the five
bounded contexts in WriteIt's domain-driven architecture.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any

# Pipeline domain value objects
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.step_name import StepName
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus

# Workspace domain value objects
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue

# Content domain value objects
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.style_name import StyleName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.content_length import ContentLength
from writeit.domains.content.value_objects.validation_rule import ValidationRule

# Execution domain value objects
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount
from writeit.domains.execution.value_objects.cache_key import CacheKey
from writeit.domains.execution.value_objects.execution_mode import ExecutionMode


# ============================================================================
# Pipeline Domain Value Object Fixtures
# ============================================================================

@pytest.fixture
def pipeline_id():
    """Valid pipeline ID fixture."""
    return PipelineId.from_name("test-pipeline")

@pytest.fixture
def invalid_pipeline_id():
    """Invalid pipeline ID for negative testing."""
    return "ab"  # Too short

@pytest.fixture
def pipeline_name():
    """Valid pipeline name fixture."""
    return PipelineName.from_user_input("Test Pipeline")

@pytest.fixture
def step_id():
    """Valid step ID fixture."""
    return StepId.from_name("test-step")

@pytest.fixture
def step_name():
    """Valid step name fixture."""
    return StepName.from_user_input("Test Step")

@pytest.fixture
def prompt_template():
    """Valid prompt template fixture."""
    return PromptTemplate.create("Generate content about {{ topic }}")

@pytest.fixture
def empty_prompt_template():
    """Empty prompt template for edge case testing."""
    return PromptTemplate.create("")

@pytest.fixture
def model_preference():
    """Valid model preference fixture."""
    return ModelPreference.create(["gpt-4o-mini", "gpt-3.5-turbo"])

@pytest.fixture
def execution_status():
    """Valid execution status fixture."""
    return ExecutionStatus.created()

@pytest.fixture
def execution_status_variants():
    """All execution status variants."""
    return {
        "created": ExecutionStatus.created(),
        "running": ExecutionStatus.running(),
        "completed": ExecutionStatus.completed(),
        "failed": ExecutionStatus.failed("Test error"),
        "cancelled": ExecutionStatus.cancelled()
    }


# ============================================================================
# Workspace Domain Value Object Fixtures
# ============================================================================

@pytest.fixture
def workspace_name():
    """Valid workspace name fixture."""
    return WorkspaceName.from_user_input("test-workspace")

@pytest.fixture
def invalid_workspace_name():
    """Invalid workspace name for negative testing."""
    return "ab"  # Too short

@pytest.fixture
def workspace_path(tmp_path):
    """Valid workspace path fixture using temp directory."""
    return WorkspacePath.from_string(str(tmp_path / "test-workspace"))

@pytest.fixture
def configuration_value():
    """Valid configuration value fixture."""
    return ConfigurationValue.create("auto_save", True, "boolean")

@pytest.fixture
def configuration_value_variants():
    """Different configuration value types."""
    return {
        "string": ConfigurationValue.create("default_model", "gpt-4o-mini", "string"),
        "boolean": ConfigurationValue.create("auto_save", True, "boolean"),
        "integer": ConfigurationValue.create("max_retries", 3, "integer"),
        "float": ConfigurationValue.create("timeout", 30.0, "float"),
        "list": ConfigurationValue.create("tags", ["test", "development"], "list")
    }


# ============================================================================
# Content Domain Value Object Fixtures
# ============================================================================

@pytest.fixture
def content_id():
    """Valid content ID fixture."""
    return ContentId.generate()

@pytest.fixture
def template_name():
    """Valid template name fixture."""
    return TemplateName.from_user_input("test-template")

@pytest.fixture
def style_name():
    """Valid style name fixture."""
    return StyleName.from_user_input("professional")

@pytest.fixture
def content_type():
    """Valid content type fixture."""
    return ContentType.article()

@pytest.fixture
def content_type_variants():
    """Different content type variants."""
    return {
        "article": ContentType.article(),
        "blog_post": ContentType.blog_post(),
        "email": ContentType.email(),
        "social_media": ContentType.social_media(),
        "documentation": ContentType.documentation()
    }

@pytest.fixture
def content_format():
    """Valid content format fixture."""
    return ContentFormat.markdown()

@pytest.fixture
def content_format_variants():
    """Different content format variants."""
    return {
        "markdown": ContentFormat.markdown(),
        "html": ContentFormat.html(),
        "plain_text": ContentFormat.plain_text(),
        "json": ContentFormat.json()
    }

@pytest.fixture
def content_length():
    """Valid content length fixture."""
    return ContentLength.create(min_words=100, max_words=1000, target_words=500)

@pytest.fixture
def validation_rule():
    """Valid validation rule fixture."""
    return ValidationRule.word_count_range(100, 1000)

@pytest.fixture
def validation_rule_variants():
    """Different validation rule types."""
    return {
        "word_count": ValidationRule.word_count_range(100, 1000),
        "character_count": ValidationRule.character_count_range(500, 5000),
        "readability": ValidationRule.readability_score(8.0),
        "sentiment": ValidationRule.sentiment_range(-0.1, 0.1),
        "keyword_density": ValidationRule.keyword_density("AI", 0.02, 0.05)
    }


# ============================================================================
# Execution Domain Value Object Fixtures
# ============================================================================

@pytest.fixture
def model_name():
    """Valid model name fixture."""
    return ModelName.from_string("gpt-4o-mini")

@pytest.fixture
def model_name_variants():
    """Different model name variants."""
    return {
        "gpt_4o_mini": ModelName.from_string("gpt-4o-mini"),
        "gpt_4o": ModelName.from_string("gpt-4o"),
        "claude_3_haiku": ModelName.from_string("claude-3-haiku"),
        "claude_3_sonnet": ModelName.from_string("claude-3-sonnet")
    }

@pytest.fixture
def token_count():
    """Valid token count fixture."""
    return TokenCount.create(input_tokens=100, output_tokens=50)

@pytest.fixture
def cache_key():
    """Valid cache key fixture."""
    return CacheKey.generate()

@pytest.fixture
def execution_mode():
    """Valid execution mode fixture."""
    return ExecutionMode.cli()

@pytest.fixture
def execution_mode_variants():
    """Different execution mode variants."""
    return {
        "cli": ExecutionMode.cli(),
        "tui": ExecutionMode.tui(),
        "api": ExecutionMode.api(),
        "batch": ExecutionMode.batch()
    }


# ============================================================================
# Edge Case and Invalid Fixtures
# ============================================================================

@pytest.fixture
def edge_case_values():
    """Edge case values for boundary testing."""
    return {
        "empty_string": "",
        "whitespace_only": "   ",
        "very_long_string": "x" * 1000,
        "unicode_string": "🚀 Test with émojis and spëcial chars 中文",
        "null_values": [None, "", 0, [], {}],
        "boundary_numbers": [-1, 0, 1, 999, 1000, 1001]
    }

@pytest.fixture
def invalid_value_objects():
    """Invalid value objects for negative testing."""
    return {
        "pipeline_id": {
            "too_short": "ab",
            "too_long": "x" * 100,
            "invalid_chars": "test-pipeline!",
            "starts_with_special": "-test-pipeline",
            "ends_with_special": "test-pipeline-"
        },
        "workspace_name": {
            "too_short": "ab", 
            "too_long": "x" * 100,
            "invalid_chars": "test workspace!",
            "starts_with_number": "1test"
        },
        "content_length": {
            "negative_min": {"min_words": -1, "max_words": 100},
            "negative_max": {"min_words": 100, "max_words": -1},
            "min_greater_than_max": {"min_words": 1000, "max_words": 100}
        },
        "token_count": {
            "negative_input": {"input_tokens": -1, "output_tokens": 50},
            "negative_output": {"input_tokens": 100, "output_tokens": -1}
        }
    }


# ============================================================================
# Complex Composite Fixtures
# ============================================================================

@pytest.fixture
def all_value_object_fixtures():
    """Composite fixture with all valid value objects."""
    return {
        # Pipeline domain
        "pipeline_id": PipelineId.from_name("test-pipeline"),
        "pipeline_name": PipelineName.from_user_input("Test Pipeline"),
        "step_id": StepId.from_name("test-step"),
        "step_name": StepName.from_user_input("Test Step"),
        "prompt_template": PromptTemplate.create("Generate {{ topic }}"),
        "model_preference": ModelPreference.create(["gpt-4o-mini"]),
        "execution_status": ExecutionStatus.created(),
        
        # Workspace domain
        "workspace_name": WorkspaceName.from_user_input("test-workspace"),
        "configuration_value": ConfigurationValue.create("auto_save", True, "boolean"),
        
        # Content domain
        "content_id": ContentId.generate(),
        "template_name": TemplateName.from_user_input("test-template"),
        "style_name": StyleName.from_user_input("professional"),
        "content_type": ContentType.article(),
        "content_format": ContentFormat.markdown(),
        "content_length": ContentLength.create(100, 1000, 500),
        "validation_rule": ValidationRule.word_count_range(100, 1000),
        
        # Execution domain
        "model_name": ModelName.from_string("gpt-4o-mini"),
        "token_count": TokenCount.create(100, 50),
        "cache_key": CacheKey.generate(),
        "execution_mode": ExecutionMode.cli()
    }

@pytest.fixture
def value_object_factory():
    """Factory for creating value objects with custom parameters."""
    class ValueObjectFactory:
        @staticmethod
        def pipeline_id(name: str = None) -> PipelineId:
            return PipelineId.from_name(name or f"pipeline-{uuid4().hex[:8]}")
        
        @staticmethod
        def content_id() -> ContentId:
            return ContentId.generate()
        
        @staticmethod
        def workspace_name(name: str = None) -> WorkspaceName:
            return WorkspaceName.from_user_input(name or f"workspace-{uuid4().hex[:8]}")
        
        @staticmethod
        def prompt_template(template: str = None) -> PromptTemplate:
            return PromptTemplate.create(template or "Generate content about {{ topic }}")
        
        @staticmethod
        def model_preference(models: List[str] = None) -> ModelPreference:
            return ModelPreference.create(models or ["gpt-4o-mini"])
        
        @staticmethod
        def content_length(min_w: int = 100, max_w: int = 1000, target_w: int = 500) -> ContentLength:
            return ContentLength.create(min_w, max_w, target_w)
        
        @staticmethod
        def validation_rule(rule_type: str = "word_count", **kwargs) -> ValidationRule:
            if rule_type == "word_count":
                return ValidationRule.word_count_range(
                    kwargs.get("min_words", 100),
                    kwargs.get("max_words", 1000)
                )
            elif rule_type == "character_count":
                return ValidationRule.character_count_range(
                    kwargs.get("min_chars", 500),
                    kwargs.get("max_chars", 5000)
                )
            else:
                return ValidationRule.word_count_range(100, 1000)
    
    return ValueObjectFactory()