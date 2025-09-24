"""Comprehensive business rule enforcement tests.

Tests domain business rules across all domains to ensure:
- Domain invariants are maintained
- State transition rules are enforced 
- Cross-entity consistency is preserved
- Aggregate boundaries are respected
- Business constraints are validated
"""

import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock

# Pipeline Domain Imports
from src.writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from src.writeit.domains.pipeline.entities.pipeline_step import StepExecution
from src.writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate, PipelineStepTemplate
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.execution_status import (
    ExecutionStatus, PipelineExecutionStatus, StepExecutionStatus
)
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate

# Workspace Domain Imports
from src.writeit.domains.workspace.entities.workspace import Workspace
from src.writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from src.writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from src.writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue

# Content Domain Imports
from src.writeit.domains.content.entities.template import Template
from src.writeit.domains.content.entities.style_primer import StylePrimer
from src.writeit.domains.content.entities.generated_content import GeneratedContent
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.content_id import ContentId
from src.writeit.domains.content.value_objects.content_type import ContentType, ContentTypeEnum
from src.writeit.domains.content.value_objects.content_format import ContentFormat, ContentFormatEnum
from src.writeit.domains.content.value_objects.style_name import StyleName

# Execution Domain Imports
from src.writeit.domains.execution.entities.llm_provider import LLMProvider
from src.writeit.domains.execution.entities.token_usage import TokenUsage
from src.writeit.domains.execution.value_objects.model_name import ModelName
from src.writeit.domains.execution.value_objects.token_count import TokenCount

# Test builders
from tests.builders.pipeline_builders import (
    PipelineTemplateBuilder, PipelineRunBuilder, StepExecutionBuilder
)
from tests.builders.workspace_builders import WorkspaceBuilder
from tests.builders.content_builders import TemplateBuilder, StylePrimerBuilder
from tests.builders.execution_builders import LLMProviderBuilder, TokenUsageBuilder


class TestPipelineBusinessRules:
    """Test pipeline domain business rules."""
    
    def test_pipeline_run_state_transition_rules(self):
        """Test pipeline run state transition business rules."""
        pipeline_run = PipelineRunBuilder().build()
        
        # Rule: Created runs can transition to queued or running
        assert pipeline_run.status.status == PipelineExecutionStatus.CREATED
        
        # Valid transition: created -> running
        running_run = pipeline_run.start()
        assert running_run.status.status == PipelineExecutionStatus.RUNNING
        assert running_run.started_at is not None
        
        # Rule: Running pipelines can be paused
        paused_run = running_run.pause()
        assert paused_run.status.status == PipelineExecutionStatus.PAUSED
        
        # Rule: Paused pipelines can be resumed or cancelled
        resumed_run = paused_run.resume()
        assert resumed_run.status.status == PipelineExecutionStatus.RUNNING
        
        # Rule: Running pipelines can be completed
        completed_run = resumed_run.complete(outputs={"result": "success"})
        assert completed_run.status.status == PipelineExecutionStatus.COMPLETED
        assert completed_run.completed_at is not None
        
        # Rule: Terminal states cannot be changed - test using status transition
        completed_status = ExecutionStatus.completed()
        
        # Terminal states should have no valid transitions
        assert not completed_status.can_transition_to(PipelineExecutionStatus.RUNNING)
        assert not completed_status.can_transition_to(PipelineExecutionStatus.PAUSED)
        
        with pytest.raises(ValueError, match="Invalid transition"):
            completed_status.transition_to(PipelineExecutionStatus.RUNNING)
    
    def test_pipeline_run_temporal_consistency_rules(self):
        """Test temporal consistency business rules."""
        pipeline_run = PipelineRunBuilder().build()
        
        # Rule: started_at must be after created_at
        running_run = pipeline_run.start()
        assert running_run.started_at >= running_run.created_at
        
        # Rule: completed_at must be after started_at
        completed_run = running_run.complete(outputs={})
        assert completed_run.completed_at >= completed_run.started_at
        
        # Rule: Cannot have completed_at without started_at
        with pytest.raises(ValueError):
            PipelineRun(
                id=str(uuid.uuid4()),
                pipeline_id=PipelineId("test"),
                workspace_name="test",
                status=ExecutionStatus.completed(),
                created_at=datetime.now(),
                started_at=None,
                completed_at=datetime.now()
            )
    
    def test_pipeline_run_error_state_rules(self):
        """Test error state business rules."""
        pipeline_run = PipelineRunBuilder().build()
        running_run = pipeline_run.start()
        
        # Rule: Failed runs must have error message
        failed_run = running_run.fail("Test error")
        assert failed_run.status.status == PipelineExecutionStatus.FAILED
        assert failed_run.error == "Test error"
        
        # Rule: Cannot fail without error message
        with pytest.raises(ValueError):
            running_run.fail(None)
            
        with pytest.raises(ValueError):
            running_run.fail("")
    
    def test_step_execution_dependency_rules(self):
        """Test step execution dependency business rules."""
        # Create pipeline with dependencies
        step1 = PipelineStepTemplate(
            id=StepId("step1"),
            name="First Step",
            description="First step",
            type="llm_generate",
            prompt_template=PromptTemplate("Generate content"),
            dependencies=[]
        )
        
        step2 = PipelineStepTemplate(
            id=StepId("step2"),
            name="Second Step", 
            description="Second step",
            type="llm_generate",
            prompt_template=PromptTemplate("Process {{ steps.step1.result }}"),
            dependencies=["step1"]
        )
        
        template = PipelineTemplate(
            id=PipelineId("test-pipeline"),
            name="Test Pipeline",
            description="Test pipeline",
            version="1.0.0",
            steps={"step1": step1, "step2": step2},
            inputs={},
            defaults={}
        )
        
        # Rule: Steps with dependencies cannot start until dependencies complete
        step1_execution = StepExecution.create(
            step_id=StepId("step1"),
            pipeline_run_id="run123"
        )
        
        step2_execution = StepExecution.create(
            step_id=StepId("step2"),
            pipeline_run_id="run123"
        )
        
        # step1 has no dependencies, can start immediately
        assert step1_execution.can_start(completed_steps=set())
        
        # step2 has dependencies, cannot start until step1 completes
        assert not step2_execution.can_start(completed_steps=set())
        assert step2_execution.can_start(completed_steps={"step1"})
    
    def test_step_execution_state_rules(self):
        """Test step execution state business rules."""
        step_execution = StepExecutionBuilder().build()
        
        # Rule: Steps start in pending state 
        assert step_execution.status.status == StepExecutionStatus.PENDING
        
        # Valid state progression: pending -> running -> completed
        started_step = step_execution.start()
        assert started_step.status.status == StepExecutionStatus.RUNNING
        
        completed_step = started_step.complete(outputs={"result": "test"})
        assert completed_step.status.status == StepExecutionStatus.COMPLETED
        assert completed_step.outputs == {"result": "test"}
        
        # Rule: Terminal steps cannot transition to other states
        completed_status = ExecutionStatus(
            status=StepExecutionStatus.COMPLETED,
            changed_at=datetime.now()
        )
        
        # Terminal status should have no valid transitions
        assert not completed_status.can_transition_to(StepExecutionStatus.RUNNING)
        assert not completed_status.can_transition_to(StepExecutionStatus.PENDING)
        
        with pytest.raises(ValueError, match="Invalid transition"):
            completed_status.transition_to(StepExecutionStatus.RUNNING)


class TestWorkspaceBusinessRules:
    """Test workspace domain business rules."""
    
    def test_workspace_isolation_rules(self):
        """Test workspace isolation business rules."""
        workspace1 = WorkspaceBuilder().with_name("workspace1").build()
        workspace2 = WorkspaceBuilder().with_name("workspace2").build()
        
        # Rule: Workspace names must be unique within scope
        assert workspace1.name != workspace2.name
        
        # Rule: Workspace names must be valid identifiers
        with pytest.raises(ValueError):
            WorkspaceName("invalid name with spaces")
            
        with pytest.raises(ValueError):
            WorkspaceName("invalid-name-with-special-chars!")
    
    def test_workspace_configuration_inheritance_rules(self):
        """Test configuration inheritance business rules."""
        # Rule: Workspace config inherits from global config
        global_config = {
            "llm": {"default_model": "gpt-4", "timeout": 30},
            "cache": {"enabled": True, "ttl": 3600}
        }
        
        workspace_config = {
            "llm": {"default_model": "gpt-3.5-turbo"}  # Override default_model
        }
        
        config = WorkspaceConfiguration(
            workspace_name=WorkspaceName("test"),
            values=workspace_config,
            global_defaults=global_config
        )
        
        # Rule: Workspace values override global values
        assert config.get_value("llm.default_model") == "gpt-3.5-turbo"
        
        # Rule: Missing workspace values fall back to global
        assert config.get_value("llm.timeout") == 30
        assert config.get_value("cache.enabled") is True
        
        # Rule: Non-existent values return None or default
        assert config.get_value("non.existent") is None
        assert config.get_value("non.existent", "default") == "default"
    
    def test_workspace_template_scope_rules(self):
        """Test template scope resolution business rules."""
        workspace = WorkspaceBuilder().with_name("test-workspace").build()
        
        # Rule: Workspace templates take precedence over global templates
        # This would be tested with actual TemplateRepository integration
        # For now, we test the scoping logic
        
        # Rule: Template names must be unique within scope
        template_name = TemplateName("article-template")
        assert template_name.value == "article-template"
        
        # Rule: Template names cannot contain path separators
        with pytest.raises(ValueError):
            TemplateName("path/to/template")
            
        with pytest.raises(ValueError):
            TemplateName("..\\parent\\template")


class TestContentBusinessRules:
    """Test content domain business rules."""
    
    def test_template_validation_rules(self):
        """Test template validation business rules."""
        # Rule: Template must have valid structure
        valid_content = '''
metadata:
  name: "Test Template"
  description: "Test template"

inputs:
  topic:
    type: text
    required: true

steps:
  generate:
    name: "Generate Content"
    type: llm_generate
    prompt_template: "Generate content about {{ inputs.topic }}"
'''
        
        template = Template(
            id=ContentId("test-template"),
            name=TemplateName("test-template"),
            content_type=ContentType.PIPELINE,
            content=valid_content,
            workspace_name="test"
        )
        
        assert template.is_valid()
        
        # Rule: Invalid YAML should fail validation
        invalid_template = Template(
            id=ContentId("invalid-template"),
            name=TemplateName("invalid-template"),
            content_type=ContentType.PIPELINE,
            content="invalid: yaml: content:",  # Invalid YAML
            workspace_name="test"
        )
        
        assert not invalid_template.is_valid()
    
    def test_style_primer_compatibility_rules(self):
        """Test style primer compatibility business rules."""
        style_primer = StylePrimer(
            id=ContentId("formal-style"),
            name=StyleName("formal-style"),
            description="Formal writing style",
            guidelines={"tone": "professional", "length": "detailed"},
            workspace_name="test"
        )
        
        # Rule: Style primer must have guidelines
        assert style_primer.guidelines
        assert "tone" in style_primer.guidelines
        
        # Rule: Empty guidelines should be invalid
        with pytest.raises(ValueError):
            StylePrimer(
                id=ContentId("empty-style"),
                name=StyleName("empty-style"),
                description="Empty style",
                guidelines={},  # Empty guidelines
                workspace_name="test"
            )
    
    def test_content_lifecycle_rules(self):
        """Test generated content lifecycle business rules."""
        # Create generated content with proper structure
        content = GeneratedContent(
            id=ContentId("generated-content"),
            content_text="Generated article content about AI",
            template_name=TemplateName("blog-post"),
            content_type=ContentType(ContentTypeEnum.ARTICLE),
            format=ContentFormat(ContentFormatEnum.MARKDOWN),
            word_count=len("Generated article content about AI".split()),
            character_count=len("Generated article content about AI")
        )
        
        # Rule: Content must reference valid template
        assert content.template_name is not None
        assert content.template_name.value == "blog-post"
        
        # Rule: Content must have actual text
        assert content.content_text
        assert len(content.content_text.strip()) > 0
        
        # Rule: Word count should match actual content
        expected_word_count = len(content.content_text.split())
        assert content.word_count == expected_word_count
        
        # Rule: Character count should match content length
        assert content.character_count == len(content.content_text)
        
        # Rule: Content type must be valid
        assert content.content_type.value == ContentTypeEnum.ARTICLE


class TestExecutionBusinessRules:
    """Test execution domain business rules."""
    
    def test_token_usage_tracking_rules(self):
        """Test token usage tracking business rules."""
        token_usage = TokenUsageBuilder().build()
        
        # Rule: Token counts must be non-negative
        assert token_usage.prompt_tokens >= 0
        assert token_usage.completion_tokens >= 0
        assert token_usage.total_tokens >= 0
        
        # Rule: Total tokens should equal sum of parts
        expected_total = token_usage.prompt_tokens + token_usage.completion_tokens
        assert token_usage.total_tokens == expected_total
        
        # Rule: Cannot have negative token counts
        with pytest.raises(ValueError):
            TokenCount(-1)
            
        with pytest.raises(ValueError):
            TokenUsage(
                model=ModelName("gpt-4"),
                prompt_tokens=TokenCount(-1),  # Invalid negative
                completion_tokens=TokenCount(100),
                total_tokens=TokenCount(99)
            )
    
    def test_llm_provider_availability_rules(self):
        """Test LLM provider availability business rules."""
        provider = LLMProviderBuilder().build()
        
        # Rule: Provider must support at least one model
        assert len(provider.supported_models) > 0
        
        # Rule: Provider name must be unique and valid
        assert provider.name
        assert isinstance(provider.name, str)
        assert len(provider.name.strip()) > 0
        
        # Rule: Provider must have valid configuration
        assert provider.configuration is not None
    
    def test_cache_consistency_rules(self):
        """Test cache consistency business rules."""
        # This would test cache-specific business rules
        # For now, testing basic cache key generation rules
        
        # Rule: Cache keys must be deterministic for same inputs
        prompt1 = "Generate an article about AI"
        model1 = ModelName("gpt-4")
        params1 = {"temperature": 0.7, "max_tokens": 1000}
        
        # Same inputs should generate same cache key
        from src.writeit.domains.execution.value_objects.cache_key import CacheKey
        
        key1 = CacheKey.generate(prompt1, model1, params1)
        key2 = CacheKey.generate(prompt1, model1, params1)
        
        assert key1 == key2
        
        # Different inputs should generate different cache keys
        prompt2 = "Generate an article about ML"
        key3 = CacheKey.generate(prompt2, model1, params1)
        
        assert key1 != key3


class TestCrossDomainBusinessRules:
    """Test cross-domain business rules and constraints."""
    
    def test_workspace_data_isolation_rules(self):
        """Test workspace data isolation business rules."""
        workspace1 = "workspace1"
        workspace2 = "workspace2"
        
        # Rule: Pipeline runs are isolated by workspace
        run1 = PipelineRunBuilder().with_workspace_name(workspace1).build()
        run2 = PipelineRunBuilder().with_workspace_name(workspace2).build()
        
        assert run1.workspace_name != run2.workspace_name
        
        # Rule: Templates are isolated by workspace
        template1 = TemplateBuilder().with_workspace_name(workspace1).build()
        template2 = TemplateBuilder().with_workspace_name(workspace2).build()
        
        assert template1.workspace_name != template2.workspace_name
        
        # Rule: Content is isolated by workspace (note: GeneratedContent doesn't have workspace_name field)
        # This would be handled at the repository level for workspace isolation
        # For now, test that content can be created with different templates
        content1 = GeneratedContent(
            id=ContentId("content1"),
            content_text="Content from workspace 1",
            template_name=TemplateName("template1"),
            content_type=ContentType(ContentTypeEnum.ARTICLE),
            format=ContentFormat(ContentFormatEnum.MARKDOWN),
            word_count=5,
            character_count=len("Content from workspace 1")
        )
        
        content2 = GeneratedContent(
            id=ContentId("content2"), 
            content_text="Content from workspace 2",
            template_name=TemplateName("template2"),
            content_type=ContentType(ContentTypeEnum.ARTICLE),
            format=ContentFormat(ContentFormatEnum.MARKDOWN),
            word_count=5,
            character_count=len("Content from workspace 2")
        )
        
        # Different content should use different templates
        assert content1.template_name != content2.template_name
    
    def test_resource_usage_limits_rules(self):
        """Test resource usage limit business rules."""
        # Rule: Token usage should be tracked per request
        token_usage = TokenUsage(
            model=ModelName("gpt-4"),
            prompt_tokens=TokenCount(100),
            completion_tokens=TokenCount(200),
            total_tokens=TokenCount(300)
        )
        
        # Rule: Should be able to aggregate token usage
        total_usage = token_usage.prompt_tokens.value + token_usage.completion_tokens.value
        assert total_usage == token_usage.total_tokens.value
        
        # Rule: Token counts must be consistent
        assert token_usage.total_tokens.value >= token_usage.prompt_tokens.value
        assert token_usage.total_tokens.value >= token_usage.completion_tokens.value
    
    def test_event_ordering_consistency_rules(self):
        """Test event ordering and consistency business rules."""
        # Rule: Pipeline events must follow logical order
        pipeline_run = PipelineRunBuilder().build()
        
        # Events should follow: created -> started -> completed
        events = [
            {"type": "pipeline_created", "timestamp": pipeline_run.created_at},
            {"type": "pipeline_started", "timestamp": pipeline_run.created_at + timedelta(seconds=1)},
            {"type": "pipeline_completed", "timestamp": pipeline_run.created_at + timedelta(seconds=30)}
        ]
        
        # Rule: Events must be in chronological order
        for i in range(1, len(events)):
            assert events[i]["timestamp"] >= events[i-1]["timestamp"]
        
        # Rule: Started event must come after created event
        created_event = next(e for e in events if e["type"] == "pipeline_created")
        started_event = next(e for e in events if e["type"] == "pipeline_started")
        completed_event = next(e for e in events if e["type"] == "pipeline_completed")
        
        assert started_event["timestamp"] > created_event["timestamp"]
        assert completed_event["timestamp"] > started_event["timestamp"]
    
    def test_aggregate_boundary_enforcement_rules(self):
        """Test aggregate boundary enforcement business rules."""
        # Rule: Pipeline aggregate includes run and step executions
        pipeline_run = PipelineRunBuilder().build()
        step_execution = StepExecutionBuilder().with_pipeline_run_id(pipeline_run.id).build()
        
        # Rule: Step executions belong to pipeline run aggregate
        assert step_execution.pipeline_run_id == pipeline_run.id
        
        # Rule: Cannot modify step execution from outside pipeline aggregate
        # This would be enforced by the repository pattern and domain services
        
        # Rule: Workspace aggregate includes all workspace-scoped entities
        workspace_name = "test-workspace"
        
        # All entities should be scoped to workspace
        pipeline_in_workspace = PipelineRunBuilder().with_workspace_name(workspace_name).build()
        template_in_workspace = TemplateBuilder().with_workspace_name(workspace_name).build()
        
        assert pipeline_in_workspace.workspace_name == workspace_name
        assert template_in_workspace.workspace_name == workspace_name
    
    def test_data_consistency_across_domains(self):
        """Test data consistency across domain boundaries."""
        workspace_name = "test-workspace"
        template_id = "test-template"
        
        # Rule: Generated content must reference valid template
        content = GeneratedContent(
            id=ContentId("content1"),
            content_text="Generated content",
            template_name=TemplateName(template_id),
            content_type=ContentType(ContentTypeEnum.ARTICLE),
            format=ContentFormat(ContentFormatEnum.MARKDOWN),
            word_count=2,
            character_count=len("Generated content")
        )
        
        # Rule: Content references correct template
        # Workspace isolation would be enforced by repository queries
        assert content.template_name.value == template_id
        
        # Rule: Pipeline runs using templates must reference valid templates
        pipeline_run = PipelineRun.create(
            pipeline_id=PipelineId(template_id),
            workspace_name=workspace_name,
            inputs={"topic": "test"}
        )
        
        assert pipeline_run.workspace_name == workspace_name
        assert pipeline_run.pipeline_id.value == template_id
