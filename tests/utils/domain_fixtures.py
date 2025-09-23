"""Domain entity fixtures for testing.

Provides comprehensive fixtures for creating domain entities, value objects,
and aggregates for testing WriteIt's domain-driven architecture.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
import pytest
from pathlib import Path

# Domain entity imports
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.entities.pipeline_step import PipelineStep
from writeit.domains.pipeline.entities.pipeline_metadata import PipelineMetadata
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.content.entities.template import Template
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.execution.entities.llm_provider import LLMProvider
from writeit.domains.execution.entities.execution_context import ExecutionContext
from writeit.domains.execution.entities.token_usage import TokenUsage

# Value object imports
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.step_name import StepName
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.style_name import StyleName
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.content_length import ContentLength
from writeit.domains.content.value_objects.validation_rule import ValidationRule
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount
from writeit.domains.execution.value_objects.cache_key import CacheKey
from writeit.domains.execution.value_objects.execution_mode import ExecutionMode


class DomainFixtures:
    """Centralized collection of domain entity and value object fixtures."""
    
    # ============================================================================
    # Pipeline Domain Fixtures
    # ============================================================================
    
    @staticmethod
    def create_pipeline_id(value: str = None) -> PipelineId:
        """Create a test pipeline ID."""
        if value is None:
            value = f"pipeline-{uuid4().hex[:8]}"
        return PipelineId(value)
    
    @staticmethod
    def create_pipeline_name(value: str = "Test Pipeline") -> PipelineName:
        """Create a test pipeline name."""
        return PipelineName(value)
    
    @staticmethod
    def create_step_id(value: str = None) -> StepId:
        """Create a test step ID."""
        if value is None:
            value = f"step-{uuid4().hex[:8]}"
        return StepId(value)
    
    @staticmethod
    def create_step_name(value: str = "Test Step") -> StepName:
        """Create a test step name."""
        return StepName(value)
    
    @staticmethod
    def create_prompt_template(template: str = "Generate content about {{ topic }}") -> PromptTemplate:
        """Create a test prompt template."""
        return PromptTemplate(template)
    
    @staticmethod
    def create_model_preference(models: List[str] = None) -> ModelPreference:
        """Create a test model preference."""
        if models is None:
            models = ["gpt-4o-mini", "gpt-3.5-turbo"]
        return ModelPreference(models)
    
    @staticmethod
    def create_execution_status(status: str = "pending") -> ExecutionStatus:
        """Create a test execution status."""
        return ExecutionStatus(status)
    
    @staticmethod
    def create_pipeline_metadata(
        name: str = "test-pipeline",
        description: str = "Test pipeline description",
        version: str = "1.0.0",
        author: str = "Test Author",
        **kwargs
    ) -> PipelineMetadata:
        """Create test pipeline metadata."""
        return PipelineMetadata(
            name=name,
            description=description,
            version=version,
            author=author,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    @staticmethod
    def create_pipeline_step(
        step_id: StepId = None,
        name: StepName = None,
        step_type: str = "llm_generate",
        prompt_template: PromptTemplate = None,
        model_preference: ModelPreference = None,
        depends_on: List[StepId] = None,
        **kwargs
    ) -> PipelineStep:
        """Create a test pipeline step."""
        if step_id is None:
            step_id = DomainFixtures.create_step_id()
        if name is None:
            name = DomainFixtures.create_step_name()
        if prompt_template is None:
            prompt_template = DomainFixtures.create_prompt_template()
        if model_preference is None:
            model_preference = DomainFixtures.create_model_preference()
        if depends_on is None:
            depends_on = []
        
        return PipelineStep(
            step_id=step_id,
            name=name,
            step_type=step_type,
            prompt_template=prompt_template,
            model_preference=model_preference,
            depends_on=depends_on,
            configuration=kwargs.get("configuration", {}),
            retry_configuration=kwargs.get("retry_configuration", {})
        )
    
    @staticmethod
    def create_pipeline_template(
        pipeline_id: PipelineId = None,
        metadata: PipelineMetadata = None,
        inputs: Dict[str, Any] = None,
        steps: List[PipelineStep] = None,
        defaults: Dict[str, Any] = None,
        **kwargs
    ) -> PipelineTemplate:
        """Create a test pipeline template."""
        if pipeline_id is None:
            pipeline_id = DomainFixtures.create_pipeline_id()
        if metadata is None:
            metadata = DomainFixtures.create_pipeline_metadata()
        if inputs is None:
            inputs = {
                "topic": {
                    "type": "text",
                    "label": "Topic",
                    "required": True,
                    "placeholder": "Enter topic..."
                }
            }
        if steps is None:
            steps = [DomainFixtures.create_pipeline_step()]
        if defaults is None:
            defaults = {"model": "gpt-4o-mini"}
        
        return PipelineTemplate(
            pipeline_id=pipeline_id,
            metadata=metadata,
            inputs=inputs,
            steps=steps,
            defaults=defaults,
            **kwargs
        )
    
    @staticmethod
    def create_pipeline_run(
        run_id: str = None,
        pipeline_template: PipelineTemplate = None,
        workspace_name: WorkspaceName = None,
        user_inputs: Dict[str, Any] = None,
        status: ExecutionStatus = None,
        **kwargs
    ) -> PipelineRun:
        """Create a test pipeline run."""
        if run_id is None:
            run_id = str(uuid4())
        if pipeline_template is None:
            pipeline_template = DomainFixtures.create_pipeline_template()
        if workspace_name is None:
            workspace_name = DomainFixtures.create_workspace_name()
        if user_inputs is None:
            user_inputs = {"topic": "Test Topic"}
        if status is None:
            status = DomainFixtures.create_execution_status("running")
        
        return PipelineRun(
            run_id=run_id,
            pipeline_template=pipeline_template,
            workspace_name=workspace_name,
            user_inputs=user_inputs,
            status=status,
            created_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    # ============================================================================
    # Workspace Domain Fixtures
    # ============================================================================
    
    @staticmethod
    def create_workspace_name(value: str = "test-workspace") -> WorkspaceName:
        """Create a test workspace name."""
        return WorkspaceName(value)
    
    @staticmethod
    def create_workspace_path(path: str = None) -> WorkspacePath:
        """Create a test workspace path."""
        if path is None:
            path = f"/tmp/test-workspace-{uuid4().hex[:8]}"
        return WorkspacePath(Path(path))
    
    @staticmethod
    def create_configuration_value(
        key: str = "test_setting",
        value: Any = "test_value",
        value_type: str = "string"
    ) -> ConfigurationValue:
        """Create a test configuration value."""
        return ConfigurationValue(key, value, value_type)
    
    @staticmethod
    def create_workspace_configuration(
        settings: Dict[str, ConfigurationValue] = None
    ) -> WorkspaceConfiguration:
        """Create a test workspace configuration."""
        if settings is None:
            settings = {
                "auto_save": DomainFixtures.create_configuration_value("auto_save", True, "boolean"),
                "default_model": DomainFixtures.create_configuration_value("default_model", "gpt-4o-mini", "string")
            }
        
        return WorkspaceConfiguration(
            settings=settings,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def create_workspace(
        name: WorkspaceName = None,
        path: WorkspacePath = None,
        configuration: WorkspaceConfiguration = None,
        **kwargs
    ) -> Workspace:
        """Create a test workspace."""
        if name is None:
            name = DomainFixtures.create_workspace_name()
        if path is None:
            path = DomainFixtures.create_workspace_path()
        if configuration is None:
            configuration = DomainFixtures.create_workspace_configuration()
        
        return Workspace(
            name=name,
            path=path,
            configuration=configuration,
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    # ============================================================================
    # Content Domain Fixtures
    # ============================================================================
    
    @staticmethod
    def create_template_name(value: str = "test-template") -> TemplateName:
        """Create a test template name."""
        return TemplateName(value)
    
    @staticmethod
    def create_style_name(value: str = "test-style") -> StyleName:
        """Create a test style name."""
        return StyleName(value)
    
    @staticmethod
    def create_content_id(value: str = None) -> ContentId:
        """Create a test content ID."""
        if value is None:
            value = f"content-{uuid4().hex[:8]}"
        return ContentId(value)
    
    @staticmethod
    def create_content_type(value: str = "article") -> ContentType:
        """Create a test content type."""
        return ContentType(value)
    
    @staticmethod
    def create_content_format(value: str = "markdown") -> ContentFormat:
        """Create a test content format."""
        return ContentFormat(value)
    
    @staticmethod
    def create_content_length(
        min_length: int = 100,
        max_length: int = 5000,
        target_length: int = 1000
    ) -> ContentLength:
        """Create a test content length."""
        return ContentLength(min_length, max_length, target_length)
    
    @staticmethod
    def create_validation_rule(
        rule_type: str = "length",
        parameters: Dict[str, Any] = None
    ) -> ValidationRule:
        """Create a test validation rule."""
        if parameters is None:
            parameters = {"min_length": 100, "max_length": 5000}
        return ValidationRule(rule_type, parameters)
    
    @staticmethod
    def create_template(
        name: TemplateName = None,
        content: str = None,
        content_type: ContentType = None,
        content_format: ContentFormat = None,
        **kwargs
    ) -> Template:
        """Create a test template."""
        if name is None:
            name = DomainFixtures.create_template_name()
        if content is None:
            content = "# {{ title }}\n\nThis is a test template about {{ topic }}."
        if content_type is None:
            content_type = DomainFixtures.create_content_type()
        if content_format is None:
            content_format = DomainFixtures.create_content_format()
        
        return Template(
            name=name,
            content=content,
            content_type=content_type,
            content_format=content_format,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    @staticmethod
    def create_style_primer(
        name: StyleName = None,
        guidelines: str = None,
        examples: Dict[str, str] = None,
        **kwargs
    ) -> StylePrimer:
        """Create a test style primer."""
        if name is None:
            name = DomainFixtures.create_style_name()
        if guidelines is None:
            guidelines = "Write in a formal, professional tone."
        if examples is None:
            examples = {"formal": "Please consider...", "casual": "Hey, think about..."}
        
        return StylePrimer(
            name=name,
            guidelines=guidelines,
            examples=examples,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    @staticmethod
    def create_generated_content(
        content_id: ContentId = None,
        content: str = None,
        content_type: ContentType = None,
        content_format: ContentFormat = None,
        source_template: TemplateName = None,
        **kwargs
    ) -> GeneratedContent:
        """Create test generated content."""
        if content_id is None:
            content_id = DomainFixtures.create_content_id()
        if content is None:
            content = "# Test Article\n\nThis is generated test content."
        if content_type is None:
            content_type = DomainFixtures.create_content_type()
        if content_format is None:
            content_format = DomainFixtures.create_content_format()
        if source_template is None:
            source_template = DomainFixtures.create_template_name()
        
        return GeneratedContent(
            content_id=content_id,
            content=content,
            content_type=content_type,
            content_format=content_format,
            source_template=source_template,
            created_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    # ============================================================================
    # Execution Domain Fixtures
    # ============================================================================
    
    @staticmethod
    def create_model_name(value: str = "gpt-4o-mini") -> ModelName:
        """Create a test model name."""
        return ModelName(value)
    
    @staticmethod
    def create_token_count(
        input_tokens: int = 100,
        output_tokens: int = 200,
        total_tokens: int = 300
    ) -> TokenCount:
        """Create a test token count."""
        return TokenCount(input_tokens, output_tokens, total_tokens)
    
    @staticmethod
    def create_cache_key(value: str = None) -> CacheKey:
        """Create a test cache key."""
        if value is None:
            value = f"cache-{uuid4().hex[:16]}"
        return CacheKey(value)
    
    @staticmethod
    def create_execution_mode(value: str = "cli") -> ExecutionMode:
        """Create a test execution mode."""
        return ExecutionMode(value)
    
    @staticmethod
    def create_llm_provider(
        provider_name: str = "openai",
        model_name: ModelName = None,
        api_key: str = "test-api-key",
        **kwargs
    ) -> LLMProvider:
        """Create a test LLM provider."""
        if model_name is None:
            model_name = DomainFixtures.create_model_name()
        
        return LLMProvider(
            provider_name=provider_name,
            model_name=model_name,
            api_key=api_key,
            configuration=kwargs.get("configuration", {}),
            rate_limits=kwargs.get("rate_limits", {}),
            **kwargs
        )
    
    @staticmethod
    def create_execution_context(
        run_id: str = None,
        workspace_name: WorkspaceName = None,
        execution_mode: ExecutionMode = None,
        **kwargs
    ) -> ExecutionContext:
        """Create a test execution context."""
        if run_id is None:
            run_id = str(uuid4())
        if workspace_name is None:
            workspace_name = DomainFixtures.create_workspace_name()
        if execution_mode is None:
            execution_mode = DomainFixtures.create_execution_mode()
        
        return ExecutionContext(
            run_id=run_id,
            workspace_name=workspace_name,
            execution_mode=execution_mode,
            created_at=datetime.now(timezone.utc),
            **kwargs
        )
    
    @staticmethod
    def create_token_usage(
        provider_name: str = "openai",
        model_name: ModelName = None,
        token_count: TokenCount = None,
        cost_estimate: float = 0.01,
        **kwargs
    ) -> TokenUsage:
        """Create test token usage."""
        if model_name is None:
            model_name = DomainFixtures.create_model_name()
        if token_count is None:
            token_count = DomainFixtures.create_token_count()
        
        return TokenUsage(
            provider_name=provider_name,
            model_name=model_name,
            token_count=token_count,
            cost_estimate=cost_estimate,
            timestamp=datetime.now(timezone.utc),
            **kwargs
        )


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def domain_fixtures():
    """Provide domain fixtures instance."""
    return DomainFixtures()


# Pipeline Domain Fixtures
@pytest.fixture
def pipeline_id():
    """Create a test pipeline ID."""
    return DomainFixtures.create_pipeline_id()


@pytest.fixture
def pipeline_template():
    """Create a test pipeline template."""
    return DomainFixtures.create_pipeline_template()


@pytest.fixture
def pipeline_run():
    """Create a test pipeline run."""
    return DomainFixtures.create_pipeline_run()


@pytest.fixture
def pipeline_step():
    """Create a test pipeline step."""
    return DomainFixtures.create_pipeline_step()


# Workspace Domain Fixtures
@pytest.fixture
def workspace():
    """Create a test workspace."""
    return DomainFixtures.create_workspace()


@pytest.fixture
def workspace_name():
    """Create a test workspace name."""
    return DomainFixtures.create_workspace_name()


@pytest.fixture
def workspace_configuration():
    """Create a test workspace configuration."""
    return DomainFixtures.create_workspace_configuration()


# Content Domain Fixtures
@pytest.fixture
def template():
    """Create a test template."""
    return DomainFixtures.create_template()


@pytest.fixture
def style_primer():
    """Create a test style primer."""
    return DomainFixtures.create_style_primer()


@pytest.fixture
def generated_content():
    """Create test generated content."""
    return DomainFixtures.create_generated_content()


# Execution Domain Fixtures
@pytest.fixture
def llm_provider():
    """Create a test LLM provider."""
    return DomainFixtures.create_llm_provider()


@pytest.fixture
def execution_context():
    """Create a test execution context."""
    return DomainFixtures.create_execution_context()


@pytest.fixture
def token_usage():
    """Create test token usage."""
    return DomainFixtures.create_token_usage()


# ============================================================================
# Composite Fixtures for Complex Scenarios
# ============================================================================

@pytest.fixture
def complete_pipeline_scenario():
    """Create a complete pipeline test scenario with all related entities."""
    workspace = DomainFixtures.create_workspace()
    template = DomainFixtures.create_template()
    pipeline_template = DomainFixtures.create_pipeline_template()
    pipeline_run = DomainFixtures.create_pipeline_run(
        pipeline_template=pipeline_template,
        workspace_name=workspace.name
    )
    execution_context = DomainFixtures.create_execution_context(
        run_id=pipeline_run.run_id,
        workspace_name=workspace.name
    )
    llm_provider = DomainFixtures.create_llm_provider()
    
    return {
        "workspace": workspace,
        "template": template,
        "pipeline_template": pipeline_template,
        "pipeline_run": pipeline_run,
        "execution_context": execution_context,
        "llm_provider": llm_provider
    }


@pytest.fixture
def multi_step_pipeline():
    """Create a pipeline with multiple steps and dependencies."""
    # Create dependent steps
    outline_step = DomainFixtures.create_pipeline_step(
        step_id=DomainFixtures.create_step_id("outline"),
        name=DomainFixtures.create_step_name("Create Outline"),
        prompt_template=DomainFixtures.create_prompt_template("Create an outline for {{ inputs.topic }}"),
    )
    
    content_step = DomainFixtures.create_pipeline_step(
        step_id=DomainFixtures.create_step_id("content"),
        name=DomainFixtures.create_step_name("Write Content"),
        prompt_template=DomainFixtures.create_prompt_template("Based on {{ steps.outline }}, write content about {{ inputs.topic }}"),
        depends_on=[outline_step.step_id]
    )
    
    review_step = DomainFixtures.create_pipeline_step(
        step_id=DomainFixtures.create_step_id("review"),
        name=DomainFixtures.create_step_name("Review Content"),
        prompt_template=DomainFixtures.create_prompt_template("Review and improve: {{ steps.content }}"),
        depends_on=[content_step.step_id]
    )
    
    return DomainFixtures.create_pipeline_template(
        steps=[outline_step, content_step, review_step]
    )


@pytest.fixture
def workspace_with_templates():
    """Create a workspace with multiple templates and content."""
    workspace = DomainFixtures.create_workspace()
    
    templates = [
        DomainFixtures.create_template(
            name=DomainFixtures.create_template_name("article-template"),
            content_type=DomainFixtures.create_content_type("article")
        ),
        DomainFixtures.create_template(
            name=DomainFixtures.create_template_name("blog-template"),
            content_type=DomainFixtures.create_content_type("blog")
        )
    ]
    
    style_primers = [
        DomainFixtures.create_style_primer(
            name=DomainFixtures.create_style_name("formal")
        ),
        DomainFixtures.create_style_primer(
            name=DomainFixtures.create_style_name("casual")
        )
    ]
    
    return {
        "workspace": workspace,
        "templates": templates,
        "style_primers": style_primers
    }
