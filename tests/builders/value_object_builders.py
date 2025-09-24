"""Test data builders for Value Objects across all domains."""

from typing import Self, List
from datetime import datetime

# Pipeline domain value objects
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from src.writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from src.writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus

# Workspace domain value objects
from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from src.writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from src.writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue

# Content domain value objects
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.content_format import ContentFormat
from src.writeit.domains.content.value_objects.content_id import ContentId
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.domains.content.value_objects.validation_rule import ValidationRule

# Execution domain value objects
from src.writeit.domains.execution.value_objects.model_name import ModelName
from src.writeit.domains.execution.value_objects.token_count import TokenCount
from src.writeit.domains.execution.value_objects.cache_key import CacheKey
from src.writeit.domains.execution.value_objects.execution_mode import ExecutionMode


class PipelineIdBuilder:
    """Builder for PipelineId test data."""
    
    def __init__(self) -> None:
        self._name = "test_pipeline"
    
    def with_name(self, name: str) -> Self:
        """Set the pipeline name."""
        self._name = name
        return self
    
    def build(self) -> PipelineId:
        """Build the PipelineId."""
        return PipelineId.from_name(self._name)
    
    @classmethod
    def simple(cls) -> Self:
        """Create a simple pipeline ID."""
        return cls().with_name("simple_pipeline")
    
    @classmethod
    def complex(cls) -> Self:
        """Create a complex pipeline ID."""
        return cls().with_name("complex_multi_step_pipeline")
    
    @classmethod
    def with_special_chars(cls) -> Self:
        """Create a pipeline ID with special characters."""
        return cls().with_name("pipeline-with_special.chars")


class StepIdBuilder:
    """Builder for StepId test data."""
    
    def __init__(self) -> None:
        self._value = "test_step"
    
    def with_value(self, value: str) -> Self:
        """Set the step ID value."""
        self._value = value
        return self
    
    def build(self) -> StepId:
        """Build the StepId."""
        return StepId(self._value)
    
    @classmethod
    def simple(cls) -> Self:
        """Create a simple step ID."""
        return cls().with_value("step")
    
    @classmethod
    def numbered(cls, number: int = 1) -> Self:
        """Create a numbered step ID."""
        return cls().with_value(f"step_{number}")
    
    @classmethod
    def named(cls, name: str = "generate") -> Self:
        """Create a named step ID."""
        return cls().with_value(name)


class PromptTemplateBuilder:
    """Builder for PromptTemplate test data."""
    
    def __init__(self) -> None:
        self._template = "Generate content about {{topic}}"
    
    def with_template(self, template: str) -> Self:
        """Set the template string."""
        self._template = template
        return self
    
    def build(self) -> PromptTemplate:
        """Build the PromptTemplate."""
        return PromptTemplate(self._template)
    
    @classmethod
    def simple(cls) -> Self:
        """Create a simple prompt template."""
        return cls().with_template("Write about {{topic}}")
    
    @classmethod
    def complex(cls) -> Self:
        """Create a complex prompt template."""
        return cls().with_template("""
Write a {{style}} article about {{topic}}.

Requirements:
- Length: {{length}} words
- Audience: {{audience}}
- Include: {{sections}}

Previous context: {{context}}
""".strip())
    
    @classmethod
    def with_multiple_vars(cls) -> Self:
        """Create a template with multiple variables."""
        return cls().with_template("{{greeting}} {{name}}, please {{action}} the {{object}}.")


class ModelPreferenceBuilder:
    """Builder for ModelPreference test data."""
    
    def __init__(self) -> None:
        self._preferred_models = ["gpt-4o-mini"]
        self._fallback_strategy = "next_available"
        self._constraints = {}
    
    def with_preferred_models(self, models: List[str]) -> Self:
        """Set the preferred models."""
        self._preferred_models = models
        return self
    
    def with_fallback_strategy(self, strategy: str) -> Self:
        """Set the fallback strategy."""
        self._fallback_strategy = strategy
        return self
    
    def with_constraints(self, constraints: dict) -> Self:
        """Set model constraints."""
        self._constraints = constraints
        return self
    
    def build(self) -> ModelPreference:
        """Build the ModelPreference."""
        return ModelPreference(
            preferred_models=self._preferred_models,
            fallback_strategy=self._fallback_strategy,
            constraints=self._constraints
        )
    
    @classmethod
    def default(cls) -> Self:
        """Create default model preference."""
        return ModelPreference.default()
    
    @classmethod
    def openai_only(cls) -> Self:
        """Create OpenAI-only preference."""
        return cls().with_preferred_models(["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
    
    @classmethod
    def anthropic_only(cls) -> Self:
        """Create Anthropic-only preference."""
        return cls().with_preferred_models(["claude-3-sonnet", "claude-3-haiku"])


class WorkspaceNameBuilder:
    """Builder for WorkspaceName test data."""
    
    def __init__(self) -> None:
        self._name = "test_workspace"
    
    def with_name(self, name: str) -> Self:
        """Set the workspace name."""
        self._name = name
        return self
    
    def build(self) -> WorkspaceName:
        """Build the WorkspaceName."""
        return WorkspaceName(self._name)
    
    @classmethod
    def default(cls) -> Self:
        """Create default workspace name."""
        return cls().with_name("default")
    
    @classmethod
    def project(cls, project_name: str = "project") -> Self:
        """Create project workspace name."""
        return cls().with_name(project_name)
    
    @classmethod
    def temporary(cls) -> Self:
        """Create temporary workspace name."""
        return cls().with_name("temp_workspace")


class WorkspacePathBuilder:
    """Builder for WorkspacePath test data."""
    
    def __init__(self) -> None:
        self._path = "/tmp/test_workspace"
    
    def with_path(self, path: str) -> Self:
        """Set the workspace path."""
        self._path = path
        return self
    
    def build(self) -> WorkspacePath:
        """Build the WorkspacePath."""
        return WorkspacePath(self._path)
    
    @classmethod
    def home(cls, name: str = "test") -> Self:
        """Create home-based workspace path."""
        return cls().with_path(f"~/.writeit/workspaces/{name}")
    
    @classmethod
    def tmp(cls, name: str = "test") -> Self:
        """Create tmp-based workspace path."""
        return cls().with_path(f"/tmp/{name}")
    
    @classmethod
    def project(cls, name: str = "project") -> Self:
        """Create project-based workspace path."""
        return cls().with_path(f"/projects/{name}")


class TemplateNameBuilder:
    """Builder for TemplateName test data."""
    
    def __init__(self) -> None:
        self._name = "test_template"
    
    def with_name(self, name: str) -> Self:
        """Set the template name."""
        self._name = name
        return self
    
    def build(self) -> TemplateName:
        """Build the TemplateName."""
        return TemplateName(self._name)
    
    @classmethod
    def article(cls) -> Self:
        """Create article template name."""
        return cls().with_name("article_template")
    
    @classmethod
    def pipeline(cls) -> Self:
        """Create pipeline template name."""
        return cls().with_name("pipeline_template")
    
    @classmethod
    def style(cls) -> Self:
        """Create style template name."""
        return cls().with_name("style_template")


class ModelNameBuilder:
    """Builder for ModelName test data."""
    
    def __init__(self) -> None:
        self._name = "test_model"
    
    def with_name(self, name: str) -> Self:
        """Set the model name."""
        self._name = name
        return self
    
    def build(self) -> ModelName:
        """Build the ModelName."""
        return ModelName(self._name)
    
    @classmethod
    def gpt4_mini(cls) -> Self:
        """Create GPT-4o-mini model name."""
        return cls().with_name("gpt-4o-mini")
    
    @classmethod
    def gpt4(cls) -> Self:
        """Create GPT-4o model name."""
        return cls().with_name("gpt-4o")
    
    @classmethod
    def claude_haiku(cls) -> Self:
        """Create Claude Haiku model name."""
        return cls().with_name("claude-3-haiku")
    
    @classmethod
    def claude_sonnet(cls) -> Self:
        """Create Claude Sonnet model name."""
        return cls().with_name("claude-3-sonnet")


class TokenCountBuilder:
    """Builder for TokenCount test data."""
    
    def __init__(self) -> None:
        self._value = 100
    
    def with_value(self, value: int) -> Self:
        """Set the token count value."""
        self._value = value
        return self
    
    def build(self) -> TokenCount:
        """Build the TokenCount."""
        return TokenCount(self._value)
    
    @classmethod
    def small(cls) -> Self:
        """Create small token count."""
        return cls().with_value(50)
    
    @classmethod
    def medium(cls) -> Self:
        """Create medium token count."""
        return cls().with_value(500)
    
    @classmethod
    def large(cls) -> Self:
        """Create large token count."""
        return cls().with_value(2000)
    
    @classmethod
    def zero(cls) -> Self:
        """Create zero token count."""
        return cls().with_value(0)


class CacheKeyBuilder:
    """Builder for CacheKey test data."""
    
    def __init__(self) -> None:
        self._key_data = {"prompt": "test prompt", "model": "test_model"}
    
    def with_key_data(self, data: dict) -> Self:
        """Set the cache key data."""
        self._key_data = data
        return self
    
    def with_prompt(self, prompt: str) -> Self:
        """Set the prompt in key data."""
        self._key_data["prompt"] = prompt
        return self
    
    def with_model(self, model: str) -> Self:
        """Set the model in key data."""
        self._key_data["model"] = model
        return self
    
    def build(self) -> CacheKey:
        """Build the CacheKey."""
        return CacheKey.from_data(self._key_data)
    
    @classmethod
    def simple(cls) -> Self:
        """Create simple cache key."""
        return cls().with_key_data({"prompt": "simple", "model": "gpt-4o-mini"})
    
    @classmethod
    def complex(cls) -> Self:
        """Create complex cache key."""
        return cls().with_key_data({
            "prompt": "complex prompt with variables",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1000,
            "context": "additional context"
        })


class ValidationRuleBuilder:
    """Builder for ValidationRule test data."""
    
    def __init__(self) -> None:
        self._rule_type = "length"
        self._parameters = {"min": 10, "max": 1000}
        self._message = "Content must be between 10 and 1000 characters"
    
    def with_rule_type(self, rule_type: str) -> Self:
        """Set the rule type."""
        self._rule_type = rule_type
        return self
    
    def with_parameters(self, parameters: dict) -> Self:
        """Set the rule parameters."""
        self._parameters = parameters
        return self
    
    def with_message(self, message: str) -> Self:
        """Set the validation message."""
        self._message = message
        return self
    
    def build(self) -> ValidationRule:
        """Build the ValidationRule."""
        return ValidationRule(
            rule_type=self._rule_type,
            parameters=self._parameters,
            message=self._message
        )
    
    @classmethod
    def length_rule(cls, min_length: int = 10, max_length: int = 1000) -> Self:
        """Create length validation rule."""
        return (cls()
                .with_rule_type("length")
                .with_parameters({"min": min_length, "max": max_length})
                .with_message(f"Content must be between {min_length} and {max_length} characters"))
    
    @classmethod
    def required_rule(cls) -> Self:
        """Create required field validation rule."""
        return (cls()
                .with_rule_type("required")
                .with_parameters({})
                .with_message("This field is required"))
    
    @classmethod
    def regex_rule(cls, pattern: str = r"^[A-Za-z0-9_-]+$") -> Self:
        """Create regex validation rule."""
        return (cls()
                .with_rule_type("regex")
                .with_parameters({"pattern": pattern})
                .with_message(f"Must match pattern: {pattern}"))