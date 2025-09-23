"""Test the domain fixtures to ensure they create valid entities.

This test file validates that all domain fixtures produce valid entities
with proper relationships and constraints.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from tests.utils.domain_fixtures import DomainFixtures

# Import domain types for validation
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.entities.pipeline_step import PipelineStep
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.content.entities.template import Template
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.execution.entities.llm_provider import LLMProvider
from writeit.domains.execution.entities.execution_context import ExecutionContext
from writeit.domains.execution.entities.token_usage import TokenUsage

# Value object imports for validation
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.execution.value_objects.model_name import ModelName


class TestDomainFixtures:
    """Test all domain fixtures for correctness."""
    
    # =========================================================================
    # Pipeline Domain Fixture Tests
    # =========================================================================
    
    def test_create_pipeline_id(self):
        """Test pipeline ID fixture."""
        pipeline_id = DomainFixtures.create_pipeline_id()
        assert isinstance(pipeline_id, PipelineId)
        assert pipeline_id.value.startswith("pipeline-")
        
        # Test with custom value
        custom_id = DomainFixtures.create_pipeline_id("custom-pipeline")
        assert custom_id.value == "custom-pipeline"
    
    def test_create_pipeline_step(self):
        """Test pipeline step fixture."""
        step = DomainFixtures.create_pipeline_step()
        assert isinstance(step, PipelineStep)
        assert step.step_id is not None
        assert step.name is not None
        assert step.step_type == "llm_generate"
        assert step.prompt_template is not None
        assert step.model_preference is not None
        assert isinstance(step.depends_on, list)
    
    def test_create_pipeline_template(self):
        """Test pipeline template fixture."""
        template = DomainFixtures.create_pipeline_template()
        assert isinstance(template, PipelineTemplate)
        assert template.pipeline_id is not None
        assert template.metadata is not None
        assert isinstance(template.inputs, dict)
        assert isinstance(template.steps, list)
        assert len(template.steps) > 0
        assert isinstance(template.defaults, dict)
    
    def test_create_pipeline_run(self):
        """Test pipeline run fixture."""
        run = DomainFixtures.create_pipeline_run()
        assert isinstance(run, PipelineRun)
        assert run.run_id is not None
        assert run.pipeline_template is not None
        assert run.workspace_name is not None
        assert isinstance(run.user_inputs, dict)
        assert run.status is not None
        assert isinstance(run.created_at, datetime)
    
    def test_create_pipeline_with_dependencies(self):
        """Test creating pipeline with step dependencies."""
        step1 = DomainFixtures.create_pipeline_step(
            step_id=DomainFixtures.create_step_id("step1")
        )
        step2 = DomainFixtures.create_pipeline_step(
            step_id=DomainFixtures.create_step_id("step2"),
            depends_on=[step1.step_id]
        )
        
        template = DomainFixtures.create_pipeline_template(steps=[step1, step2])
        
        assert len(template.steps) == 2
        assert template.steps[1].depends_on == [step1.step_id]
    
    # =========================================================================
    # Workspace Domain Fixture Tests
    # =========================================================================
    
    def test_create_workspace_name(self):
        """Test workspace name fixture."""
        name = DomainFixtures.create_workspace_name()
        assert isinstance(name, WorkspaceName)
        assert name.value == "test-workspace"
        
        # Test with custom value
        custom_name = DomainFixtures.create_workspace_name("my-workspace")
        assert custom_name.value == "my-workspace"
    
    def test_create_workspace(self):
        """Test workspace fixture."""
        workspace = DomainFixtures.create_workspace()
        assert isinstance(workspace, Workspace)
        assert workspace.name is not None
        assert workspace.path is not None
        assert workspace.configuration is not None
        assert isinstance(workspace.created_at, datetime)
        assert isinstance(workspace.last_accessed_at, datetime)
    
    def test_create_workspace_configuration(self):
        """Test workspace configuration fixture."""
        config = DomainFixtures.create_workspace_configuration()
        assert config is not None
        assert hasattr(config, 'settings')
        assert isinstance(config.settings, dict)
        assert len(config.settings) > 0
    
    # =========================================================================
    # Content Domain Fixture Tests
    # =========================================================================
    
    def test_create_template_name(self):
        """Test template name fixture."""
        name = DomainFixtures.create_template_name()
        assert isinstance(name, TemplateName)
        assert name.value == "test-template"
    
    def test_create_template(self):
        """Test template fixture."""
        template = DomainFixtures.create_template()
        assert isinstance(template, Template)
        assert template.name is not None
        assert template.content is not None
        assert "{{ topic }}" in template.content  # Check for template variables
        assert template.content_type is not None
        assert template.content_format is not None
        assert isinstance(template.created_at, datetime)
    
    def test_create_style_primer(self):
        """Test style primer fixture."""
        primer = DomainFixtures.create_style_primer()
        assert isinstance(primer, StylePrimer)
        assert primer.name is not None
        assert primer.guidelines is not None
        assert isinstance(primer.examples, dict)
        assert len(primer.examples) > 0
    
    def test_create_generated_content(self):
        """Test generated content fixture."""
        content = DomainFixtures.create_generated_content()
        assert isinstance(content, GeneratedContent)
        assert content.content_id is not None
        assert content.content is not None
        assert content.content_type is not None
        assert content.content_format is not None
        assert content.source_template is not None
    
    # =========================================================================
    # Execution Domain Fixture Tests
    # =========================================================================
    
    def test_create_model_name(self):
        """Test model name fixture."""
        name = DomainFixtures.create_model_name()
        assert isinstance(name, ModelName)
        assert name.value == "gpt-4o-mini"
    
    def test_create_llm_provider(self):
        """Test LLM provider fixture."""
        provider = DomainFixtures.create_llm_provider()
        assert isinstance(provider, LLMProvider)
        assert provider.provider_name == "openai"
        assert provider.model_name is not None
        assert provider.api_key is not None
    
    def test_create_execution_context(self):
        """Test execution context fixture."""
        context = DomainFixtures.create_execution_context()
        assert isinstance(context, ExecutionContext)
        assert context.run_id is not None
        assert context.workspace_name is not None
        assert context.execution_mode is not None
        assert isinstance(context.created_at, datetime)
    
    def test_create_token_usage(self):
        """Test token usage fixture."""
        usage = DomainFixtures.create_token_usage()
        assert isinstance(usage, TokenUsage)
        assert usage.provider_name == "openai"
        assert usage.model_name is not None
        assert usage.token_count is not None
        assert usage.cost_estimate > 0
        assert isinstance(usage.timestamp, datetime)
    
    # =========================================================================
    # Fixture Integration Tests
    # =========================================================================
    
    def test_complete_pipeline_scenario(self, complete_pipeline_scenario):
        """Test complete pipeline scenario fixture."""
        scenario = complete_pipeline_scenario
        
        # Verify all components are present
        assert "workspace" in scenario
        assert "template" in scenario
        assert "pipeline_template" in scenario
        assert "pipeline_run" in scenario
        assert "execution_context" in scenario
        assert "llm_provider" in scenario
        
        # Verify relationships
        workspace = scenario["workspace"]
        pipeline_run = scenario["pipeline_run"]
        execution_context = scenario["execution_context"]
        
        assert pipeline_run.workspace_name == workspace.name
        assert execution_context.workspace_name == workspace.name
        assert execution_context.run_id == pipeline_run.run_id
    
    def test_multi_step_pipeline(self, multi_step_pipeline):
        """Test multi-step pipeline fixture."""
        pipeline = multi_step_pipeline
        assert isinstance(pipeline, PipelineTemplate)
        assert len(pipeline.steps) == 3
        
        # Verify step dependencies
        outline_step = pipeline.steps[0]
        content_step = pipeline.steps[1]
        review_step = pipeline.steps[2]
        
        # Check dependencies
        assert len(outline_step.depends_on) == 0  # No dependencies
        assert content_step.depends_on == [outline_step.step_id]  # Depends on outline
        assert review_step.depends_on == [content_step.step_id]  # Depends on content
    
    def test_workspace_with_templates(self, workspace_with_templates):
        """Test workspace with templates fixture."""
        scenario = workspace_with_templates
        
        assert "workspace" in scenario
        assert "templates" in scenario
        assert "style_primers" in scenario
        
        workspace = scenario["workspace"]
        templates = scenario["templates"]
        style_primers = scenario["style_primers"]
        
        assert isinstance(workspace, Workspace)
        assert len(templates) == 2
        assert len(style_primers) == 2
        
        # Verify template types
        assert any(t.content_type.value == "article" for t in templates)
        assert any(t.content_type.value == "blog" for t in templates)
        
        # Verify style primers
        assert any(s.name.value == "formal" for s in style_primers)
        assert any(s.name.value == "casual" for s in style_primers)
    
    # =========================================================================
    # Customization and Edge Case Tests
    # =========================================================================
    
    def test_fixture_customization(self):
        """Test that fixtures can be customized with parameters."""
        # Custom pipeline with specific name
        custom_pipeline = DomainFixtures.create_pipeline_template(
            metadata=DomainFixtures.create_pipeline_metadata(
                name="custom-pipeline",
                description="Custom description"
            )
        )
        
        assert custom_pipeline.metadata.name == "custom-pipeline"
        assert custom_pipeline.metadata.description == "Custom description"
        
        # Custom workspace with specific settings
        custom_workspace = DomainFixtures.create_workspace(
            name=DomainFixtures.create_workspace_name("custom-workspace")
        )
        
        assert custom_workspace.name.value == "custom-workspace"
    
    def test_value_object_constraints(self):
        """Test that value objects maintain their constraints."""
        # Test execution status constraints
        valid_status = DomainFixtures.create_execution_status("running")
        assert valid_status.value == "running"
        
        # Test that invalid status would fail (this depends on implementation)
        # This test assumes ExecutionStatus validates input
        
        # Test model preferences
        models = ["gpt-4o-mini", "gpt-3.5-turbo"]
        preference = DomainFixtures.create_model_preference(models)
        assert len(preference.models) == 2
        assert "gpt-4o-mini" in preference.models
    
    def test_datetime_fields(self):
        """Test that datetime fields are properly set."""
        workspace = DomainFixtures.create_workspace()
        template = DomainFixtures.create_template()
        pipeline_run = DomainFixtures.create_pipeline_run()
        
        # All should have recent timestamps
        now = datetime.now(timezone.utc)
        
        # Check that created_at is recent (within last minute)
        assert (now - workspace.created_at).total_seconds() < 60
        assert (now - template.created_at).total_seconds() < 60
        assert (now - pipeline_run.created_at).total_seconds() < 60
    
    def test_unique_identifiers(self):
        """Test that fixtures generate unique identifiers."""
        # Create multiple instances and verify uniqueness
        pipeline_ids = [DomainFixtures.create_pipeline_id() for _ in range(5)]
        content_ids = [DomainFixtures.create_content_id() for _ in range(5)]
        run_ids = [DomainFixtures.create_pipeline_run().run_id for _ in range(5)]
        
        # All should be unique
        assert len(set(p.value for p in pipeline_ids)) == 5
        assert len(set(c.value for c in content_ids)) == 5
        assert len(set(run_ids)) == 5


class TestFixturePytestIntegration:
    """Test pytest fixture integration."""
    
    def test_pipeline_fixtures(self, pipeline_id, pipeline_template, pipeline_run, pipeline_step):
        """Test that pytest fixtures work correctly."""
        assert isinstance(pipeline_id, PipelineId)
        assert isinstance(pipeline_template, PipelineTemplate)
        assert isinstance(pipeline_run, PipelineRun)
        assert isinstance(pipeline_step, PipelineStep)
    
    def test_workspace_fixtures(self, workspace, workspace_name, workspace_configuration):
        """Test workspace pytest fixtures."""
        assert isinstance(workspace, Workspace)
        assert isinstance(workspace_name, WorkspaceName)
        assert workspace_configuration is not None
    
    def test_content_fixtures(self, template, style_primer, generated_content):
        """Test content pytest fixtures."""
        assert isinstance(template, Template)
        assert isinstance(style_primer, StylePrimer)
        assert isinstance(generated_content, GeneratedContent)
    
    def test_execution_fixtures(self, llm_provider, execution_context, token_usage):
        """Test execution pytest fixtures."""
        assert isinstance(llm_provider, LLMProvider)
        assert isinstance(execution_context, ExecutionContext)
        assert isinstance(token_usage, TokenUsage)
    
    def test_domain_fixtures_utility(self, domain_fixtures):
        """Test the domain fixtures utility class."""
        assert domain_fixtures is not None
        
        # Test that we can create entities through the utility
        workspace = domain_fixtures.create_workspace()
        template = domain_fixtures.create_template()
        pipeline = domain_fixtures.create_pipeline_template()
        
        assert isinstance(workspace, Workspace)
        assert isinstance(template, Template)
        assert isinstance(pipeline, PipelineTemplate)
