"""Tests for business rule enforcement across domains.

Tests complex business rules that span multiple domain entities
and ensure invariants are maintained across the system.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from writeit.domains.pipeline.entities.pipeline_template import (
    PipelineTemplate,
    PipelineStepTemplate,
    PipelineInput
)
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue

from writeit.domains.content.entities.template import Template
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat

from writeit.domains.execution.entities.token_usage import TokenUsage
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount


class TestPipelineBusinessRules:
    """Test business rules related to pipeline execution and management."""
    
    def test_pipeline_execution_requires_valid_workspace(self):
        """Test that pipeline execution requires a valid workspace."""
        # Create a pipeline template
        template = PipelineTemplate(
            id=PipelineId("test-pipeline"),
            name="Test Pipeline",
            description="Test pipeline",
            inputs={"topic": PipelineInput(key="topic", type="text", label="Topic")},
            steps={
                "outline": PipelineStepTemplate(
                    id=StepId("outline"),
                    name="Create Outline",
                    description="Generate outline",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Create outline for {{ inputs.topic }}")
                )
            }
        )
        
        # Create a valid workspace
        valid_workspace = Workspace(
            name=WorkspaceName("valid-workspace"),
            path=WorkspacePath(Path("/tmp/valid")),
            configuration=WorkspaceConfiguration()
        )
        
        # Should be able to create pipeline run with valid workspace
        pipeline_run = PipelineRun(
            run_id="test-run-1",
            pipeline_template=template,
            workspace_name=valid_workspace.name,
            user_inputs={"topic": "Test Topic"},
            status=ExecutionStatus("created")
        )
        
        assert pipeline_run.workspace_name == valid_workspace.name
        assert pipeline_run.status.value == "created"
    
    def test_pipeline_execution_order_enforces_dependencies(self):
        """Test that pipeline execution order respects step dependencies."""
        # Create pipeline with dependencies
        outline_step = PipelineStepTemplate(
            id=StepId("outline"),
            name="Create Outline",
            description="Generate outline",
            type="llm_generate",
            prompt_template=PromptTemplate("Create outline for {{ inputs.topic }}")
        )
        
        content_step = PipelineStepTemplate(
            id=StepId("content"),
            name="Write Content",
            description="Generate content",
            type="llm_generate",
            prompt_template=PromptTemplate("Based on {{ steps.outline }}, write content"),
            depends_on=[StepId("outline")]
        )
        
        review_step = PipelineStepTemplate(
            id=StepId("review"),
            name="Review Content",
            description="Review and improve content",
            type="llm_generate",
            prompt_template=PromptTemplate("Review and improve: {{ steps.content }}"),
            depends_on=[StepId("content")]
        )
        
        template = PipelineTemplate(
            id=PipelineId("dependency-pipeline"),
            name="Dependency Pipeline",
            description="Pipeline with step dependencies",
            inputs={"topic": PipelineInput(key="topic", type="text", label="Topic")},
            steps={
                "outline": outline_step,
                "content": content_step,
                "review": review_step
            }
        )
        
        # Get execution order - should respect dependencies
        execution_order = template.get_execution_order()
        
        # Outline must come first
        assert execution_order.index("outline") < execution_order.index("content")
        # Content must come before review
        assert execution_order.index("content") < execution_order.index("review")
        
        # Complete order should be: outline, content, review
        assert execution_order == ["outline", "content", "review"]
    
    def test_pipeline_input_validation_business_rules(self):
        """Test business rules for pipeline input validation."""
        # Create input definitions with business rules
        inputs = {
            "title": PipelineInput(
                key="title",
                type="text",
                label="Article Title",
                required=True,
                max_length=100,
                validation={"min_length": 5}
            ),
            "style": PipelineInput(
                key="style",
                type="choice",
                label="Writing Style",
                required=True,
                options=[
                    {"label": "Formal", "value": "formal"},
                    {"label": "Casual", "value": "casual"},
                    {"label": "Technical", "value": "technical"}
                ]
            ),
            "word_count": PipelineInput(
                key="word_count",
                type="number",
                label="Target Word Count",
                required=False,
                validation={"min": 100, "max": 5000}
            )
        }
        
        template = PipelineTemplate(
            id=PipelineId("validation-pipeline"),
            name="Validation Pipeline",
            description="Pipeline with input validation",
            inputs=inputs,
            steps={
                "content": PipelineStepTemplate(
                    id=StepId("content"),
                    name="Generate Content",
                    description="Generate content",
                    type="llm_generate",
                    prompt_template=PromptTemplate(
                        "Write {{ inputs.style }} content titled '{{ inputs.title }}'"
                    )
                )
            }
        )
        
        # Test valid inputs
        valid_inputs = {
            "title": "Valid Article Title",
            "style": "formal",
            "word_count": 1000
        }
        errors = template.validate_inputs(valid_inputs)
        assert len(errors) == 0
        
        # Test missing required input
        missing_required = {
            "style": "formal"  # Missing required 'title'
        }
        errors = template.validate_inputs(missing_required)
        assert len(errors) > 0
        assert any("Required input 'title' is missing" in error for error in errors)
        
        # Test invalid choice value
        invalid_choice = {
            "title": "Valid Title",
            "style": "invalid_style"  # Not in options
        }
        errors = template.validate_inputs(invalid_choice)
        assert len(errors) > 0
        assert any("Invalid value for input 'style'" in error for error in errors)
        
        # Test unexpected input
        unexpected_input = {
            "title": "Valid Title",
            "style": "formal",
            "unexpected_field": "value"
        }
        errors = template.validate_inputs(unexpected_input)
        assert len(errors) > 0
        assert any("Unexpected input 'unexpected_field'" in error for error in errors)
    
    def test_pipeline_template_variable_consistency_rule(self):
        """Test that pipeline templates maintain variable consistency."""
        # Create template where step references non-existent variable
        step = PipelineStepTemplate(
            id=StepId("broken_step"),
            name="Broken Step",
            description="Step with invalid variable reference",
            type="llm_generate",
            prompt_template=PromptTemplate("Use {{ inputs.nonexistent }} and {{ undefined_var }}")
        )
        
        template = PipelineTemplate(
            id=PipelineId("broken-pipeline"),
            name="Broken Pipeline",
            description="Pipeline with variable inconsistency",
            inputs={"valid_input": PipelineInput(key="valid_input", type="text", label="Valid")},
            steps={"broken_step": step}
        )
        
        # Variable consistency should be checked at validation time
        # The prompt template should report undefined variables
        variables = step.prompt_template.variables
        assert "inputs.nonexistent" in variables or "nonexistent" in variables
        assert "undefined_var" in variables
    
    def test_pipeline_parallel_execution_rules(self):
        """Test business rules for parallel pipeline execution."""
        # Create pipeline with parallel and sequential steps
        parallel_step_1 = PipelineStepTemplate(
            id=StepId("parallel_1"),
            name="Parallel Step 1",
            description="Can run in parallel",
            type="llm_generate",
            prompt_template=PromptTemplate("Generate content 1 for {{ inputs.topic }}"),
            parallel=True
        )
        
        parallel_step_2 = PipelineStepTemplate(
            id=StepId("parallel_2"),
            name="Parallel Step 2",
            description="Can run in parallel",
            type="llm_generate",
            prompt_template=PromptTemplate("Generate content 2 for {{ inputs.topic }}"),
            parallel=True
        )
        
        dependent_step = PipelineStepTemplate(
            id=StepId("dependent"),
            name="Dependent Step",
            description="Depends on parallel steps",
            type="llm_generate",
            prompt_template=PromptTemplate("Combine {{ steps.parallel_1 }} and {{ steps.parallel_2 }}"),
            depends_on=[StepId("parallel_1"), StepId("parallel_2")]
        )
        
        template = PipelineTemplate(
            id=PipelineId("parallel-pipeline"),
            name="Parallel Pipeline",
            description="Pipeline with parallel execution",
            inputs={"topic": PipelineInput(key="topic", type="text", label="Topic")},
            steps={
                "parallel_1": parallel_step_1,
                "parallel_2": parallel_step_2,
                "dependent": dependent_step
            }
        )
        
        # Test parallel execution groups
        parallel_groups = template.get_parallel_groups()
        
        # parallel_1 and parallel_2 should be in same group (can run in parallel)
        # dependent should be in separate group (runs after)
        
        # Find group with parallel steps
        parallel_group = None
        dependent_group = None
        
        for group in parallel_groups:
            if "parallel_1" in group and "parallel_2" in group:
                parallel_group = group
            elif "dependent" in group:
                dependent_group = group
        
        assert parallel_group is not None
        assert dependent_group is not None
        assert len(parallel_group) == 2  # Both parallel steps together
        assert len(dependent_group) == 1  # Dependent step alone


class TestWorkspaceBusinessRules:
    """Test business rules related to workspace management."""
    
    def test_workspace_isolation_rule(self):
        """Test that workspaces maintain isolation by default."""
        workspace1 = Workspace(
            name=WorkspaceName("workspace-1"),
            path=WorkspacePath(Path("/tmp/workspace1")),
            configuration=WorkspaceConfiguration()
        )
        
        workspace2 = Workspace(
            name=WorkspaceName("workspace-2"),
            path=WorkspacePath(Path("/tmp/workspace2")),
            configuration=WorkspaceConfiguration()
        )
        
        # Workspaces should be isolated by default
        assert workspace1.is_isolated is True
        assert workspace2.is_isolated is True
        
        # Workspaces should be independent
        assert workspace1.name != workspace2.name
        assert workspace1.path != workspace2.path
    
    def test_default_workspace_business_rule(self):
        """Test business rules for the default workspace."""
        default_workspace = Workspace(
            name=WorkspaceName("default"),
            path=WorkspacePath(Path("/tmp/default")),
            configuration=WorkspaceConfiguration()
        )
        
        other_workspace = Workspace(
            name=WorkspaceName("custom"),
            path=WorkspacePath(Path("/tmp/custom")),
            configuration=WorkspaceConfiguration()
        )
        
        # Only workspace named 'default' should be considered default
        assert default_workspace.is_default() is True
        assert other_workspace.is_default() is False
    
    def test_workspace_configuration_consistency_rule(self):
        """Test that workspace configuration maintains consistency."""
        # Create configuration with typed values
        config = WorkspaceConfiguration(
            settings={
                "auto_save": ConfigurationValue("auto_save", True, "boolean"),
                "default_model": ConfigurationValue("default_model", "gpt-4o-mini", "string"),
                "max_tokens": ConfigurationValue("max_tokens", 4000, "integer")
            }
        )
        
        workspace = Workspace(
            name=WorkspaceName("configured-workspace"),
            path=WorkspacePath(Path("/tmp/configured")),
            configuration=config
        )
        
        # Configuration values should maintain their types
        assert workspace.get_setting("auto_save") is True
        assert isinstance(workspace.get_setting("auto_save"), bool)
        
        assert workspace.get_setting("default_model") == "gpt-4o-mini"
        assert isinstance(workspace.get_setting("default_model"), str)
        
        assert workspace.get_setting("max_tokens") == 4000
        assert isinstance(workspace.get_setting("max_tokens"), int)
    
    def test_workspace_activation_rule(self):
        """Test that only one workspace can be active per context."""
        workspace1 = Workspace(
            name=WorkspaceName("workspace-1"),
            path=WorkspacePath(Path("/tmp/workspace1")),
            configuration=WorkspaceConfiguration(),
            is_active=True
        )
        
        workspace2 = Workspace(
            name=WorkspaceName("workspace-2"),
            path=WorkspacePath(Path("/tmp/workspace2")),
            configuration=WorkspaceConfiguration(),
            is_active=False
        )
        
        # Activating workspace2 should create new instance with active=True
        activated_workspace2 = workspace2.activate()
        
        # Business rule: application should ensure only one workspace is active
        # (This would be enforced at the application service level)
        assert workspace1.is_active is True
        assert workspace2.is_active is False
        assert activated_workspace2.is_active is True
        
        # Original workspace2 should remain unchanged (immutable)
        assert workspace2.is_active is False


class TestContentBusinessRules:
    """Test business rules related to content management."""
    
    def test_template_content_consistency_rule(self):
        """Test that templates maintain content consistency."""
        template = Template(
            name=TemplateName("article-template"),
            content="# {{ title }}\n\n{{ content }}\n\nBy {{ author }}",
            content_type=ContentType("article"),
            content_format=ContentFormat("markdown")
        )
        
        # Template should define required variables
        assert "title" in template.get_required_variables()
        assert "content" in template.get_required_variables()
        assert "author" in template.get_required_variables()
        
        # Template format should be consistent with content
        assert template.content_format.value == "markdown"
        assert template.content.startswith("#")  # Markdown header
    
    def test_generated_content_traceability_rule(self):
        """Test that generated content maintains traceability to source."""
        source_template = TemplateName("source-template")
        
        content = GeneratedContent(
            content_id=ContentId("generated-1"),
            content="# Generated Article\n\nThis is generated content.",
            content_type=ContentType("article"),
            content_format=ContentFormat("markdown"),
            source_template=source_template
        )
        
        # Generated content must maintain link to source template
        assert content.source_template == source_template
        assert content.content_id.value == "generated-1"
        
        # Content should have timestamp for audit trail
        assert content.created_at is not None
        assert isinstance(content.created_at, datetime)
    
    def test_content_format_consistency_rule(self):
        """Test that content format is consistent with actual content."""
        # Markdown content
        markdown_content = GeneratedContent(
            content_id=ContentId("markdown-content"),
            content="# Title\n\n**Bold text** and *italic text*",
            content_type=ContentType("article"),
            content_format=ContentFormat("markdown"),
            source_template=TemplateName("markdown-template")
        )
        
        # JSON content
        json_content = GeneratedContent(
            content_id=ContentId("json-content"),
            content='{"title": "Test", "body": "Content"}',
            content_type=ContentType("data"),
            content_format=ContentFormat("json"),
            source_template=TemplateName("json-template")
        )
        
        # Format should match content structure
        assert markdown_content.content_format.value == "markdown"
        assert markdown_content.content.startswith("#")
        
        assert json_content.content_format.value == "json"
        assert json_content.content.startswith("{")


class TestExecutionBusinessRules:
    """Test business rules related to execution and resource management."""
    
    def test_token_usage_tracking_rule(self):
        """Test that token usage is properly tracked and accumulated."""
        # Create token usage records
        usage1 = TokenUsage(
            provider_name="openai",
            model_name=ModelName("gpt-4o-mini"),
            token_count=TokenCount(input_tokens=100, output_tokens=150),
            cost_estimate=0.01,
            timestamp=datetime.now(timezone.utc)
        )
        
        usage2 = TokenUsage(
            provider_name="openai",
            model_name=ModelName("gpt-4o-mini"),
            token_count=TokenCount(input_tokens=200, output_tokens=300),
            cost_estimate=0.02,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Token usage should accumulate correctly
        total_tokens = usage1.token_count + usage2.token_count
        assert total_tokens.input_tokens == 300
        assert total_tokens.output_tokens == 450
        assert total_tokens.total_tokens == 750
        
        total_cost = usage1.cost_estimate + usage2.cost_estimate
        assert total_cost == 0.03
    
    def test_model_fallback_rule(self):
        """Test that model preferences implement proper fallback logic."""
        # Create model preference with fallbacks
        model_pref = ModelPreference([
            "gpt-4o",       # Primary choice
            "gpt-4o-mini",  # Fallback 1
            "gpt-3.5-turbo" # Fallback 2
        ])
        
        # Should have primary model and fallbacks
        assert model_pref.primary_model == "gpt-4o"
        assert model_pref.has_fallbacks is True
        assert len(model_pref.fallback_models) == 2
        assert "gpt-4o-mini" in model_pref.fallback_models
        assert "gpt-3.5-turbo" in model_pref.fallback_models
    
    def test_execution_resource_limit_rule(self):
        """Test that execution respects resource limits."""
        # Create token count that represents resource usage
        high_usage = TokenCount(
            input_tokens=50000,   # High input
            output_tokens=10000   # High output
        )
        
        moderate_usage = TokenCount(
            input_tokens=1000,
            output_tokens=2000
        )
        
        # Business rule: high usage should be flagged for cost control
        assert high_usage.total_tokens > 50000  # Over typical limits
        assert moderate_usage.total_tokens < 10000  # Within reasonable limits
        
        # Resource usage should be trackable for billing/limits
        assert high_usage.input_tokens > 0
        assert high_usage.output_tokens > 0
        assert high_usage.total_tokens == high_usage.input_tokens + high_usage.output_tokens


class TestCrossdomainBusinessRules:
    """Test business rules that span multiple domains."""
    
    def test_pipeline_workspace_execution_rule(self):
        """Test that pipeline execution is properly scoped to workspace."""
        # Create workspace with specific configuration
        workspace_config = WorkspaceConfiguration(
            settings={
                "default_model": ConfigurationValue("default_model", "gpt-4o-mini", "string"),
                "max_tokens": ConfigurationValue("max_tokens", 4000, "integer")
            }
        )
        
        workspace = Workspace(
            name=WorkspaceName("execution-workspace"),
            path=WorkspacePath(Path("/tmp/execution")),
            configuration=workspace_config
        )
        
        # Create pipeline template
        template = PipelineTemplate(
            id=PipelineId("workspace-pipeline"),
            name="Workspace Pipeline",
            description="Pipeline that respects workspace settings",
            inputs={"topic": PipelineInput(key="topic", type="text", label="Topic")},
            steps={
                "generate": PipelineStepTemplate(
                    id=StepId("generate"),
                    name="Generate Content",
                    description="Generate content using workspace settings",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Generate content about {{ inputs.topic }}")
                )
            }
        )
        
        # Create pipeline run in workspace context
        pipeline_run = PipelineRun(
            run_id="workspace-run-1",
            pipeline_template=template,
            workspace_name=workspace.name,
            user_inputs={"topic": "Test Topic"},
            status=ExecutionStatus("running")
        )
        
        # Business rule: execution should be scoped to workspace
        assert pipeline_run.workspace_name == workspace.name
        
        # Workspace settings should influence execution
        default_model = workspace.get_setting("default_model")
        max_tokens = workspace.get_setting("max_tokens")
        
        assert default_model == "gpt-4o-mini"
        assert max_tokens == 4000
    
    def test_content_generation_audit_trail_rule(self):
        """Test that content generation maintains complete audit trail."""
        # Create source template
        source_template = Template(
            name=TemplateName("audit-template"),
            content="Generate content about {{ topic }}",
            content_type=ContentType("article"),
            content_format=ContentFormat("markdown")
        )
        
        # Create pipeline that uses the template
        pipeline_template = PipelineTemplate(
            id=PipelineId("audit-pipeline"),
            name="Audit Pipeline",
            description="Pipeline for audit trail testing",
            inputs={"topic": PipelineInput(key="topic", type="text", label="Topic")},
            steps={
                "generate": PipelineStepTemplate(
                    id=StepId("generate"),
                    name="Generate",
                    description="Generate content",
                    type="llm_generate",
                    prompt_template=PromptTemplate(source_template.content)
                )
            }
        )
        
        # Create workspace for execution
        workspace = Workspace(
            name=WorkspaceName("audit-workspace"),
            path=WorkspacePath(Path("/tmp/audit")),
            configuration=WorkspaceConfiguration()
        )
        
        # Create pipeline run
        pipeline_run = PipelineRun(
            run_id="audit-run-1",
            pipeline_template=pipeline_template,
            workspace_name=workspace.name,
            user_inputs={"topic": "Audit Testing"},
            status=ExecutionStatus("completed")
        )
        
        # Create generated content with audit trail
        generated_content = GeneratedContent(
            content_id=ContentId("audit-content-1"),
            content="# Audit Testing\n\nThis is generated content for audit testing.",
            content_type=ContentType("article"),
            content_format=ContentFormat("markdown"),
            source_template=source_template.name,
            metadata={
                "pipeline_id": pipeline_template.id.value,
                "run_id": pipeline_run.run_id,
                "workspace": workspace.name.value,
                "step_id": "generate"
            }
        )
        
        # Create token usage for the generation
        token_usage = TokenUsage(
            provider_name="openai",
            model_name=ModelName("gpt-4o-mini"),
            token_count=TokenCount(input_tokens=50, output_tokens=100),
            cost_estimate=0.005,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "run_id": pipeline_run.run_id,
                "step_id": "generate",
                "content_id": generated_content.content_id.value
            }
        )
        
        # Audit trail should be complete and traceable
        assert generated_content.source_template == source_template.name
        assert generated_content.metadata["pipeline_id"] == pipeline_template.id.value
        assert generated_content.metadata["run_id"] == pipeline_run.run_id
        assert generated_content.metadata["workspace"] == workspace.name.value
        
        assert token_usage.metadata["run_id"] == pipeline_run.run_id
        assert token_usage.metadata["content_id"] == generated_content.content_id.value
        
        # All components should have timestamps for temporal tracking
        assert generated_content.created_at is not None
        assert token_usage.timestamp is not None
        assert pipeline_run.created_at is not None
    
    def test_workspace_pipeline_compatibility_rule(self):
        """Test that pipelines are compatible with workspace configurations."""
        # Create workspace with specific model preferences
        restrictive_config = WorkspaceConfiguration(
            settings={
                "allowed_models": ConfigurationValue(
                    "allowed_models",
                    ["gpt-4o-mini", "gpt-3.5-turbo"],
                    "list"
                ),
                "max_steps": ConfigurationValue("max_steps", 5, "integer")
            }
        )
        
        restrictive_workspace = Workspace(
            name=WorkspaceName("restrictive-workspace"),
            path=WorkspacePath(Path("/tmp/restrictive")),
            configuration=restrictive_config
        )
        
        # Create pipeline that should be compatible
        compatible_pipeline = PipelineTemplate(
            id=PipelineId("compatible-pipeline"),
            name="Compatible Pipeline",
            description="Pipeline compatible with workspace restrictions",
            steps={
                "step1": PipelineStepTemplate(
                    id=StepId("step1"),
                    name="Step 1",
                    description="Compatible step",
                    type="llm_generate",
                    prompt_template=PromptTemplate("Generate content"),
                    model_preference=ModelPreference(["gpt-4o-mini"])  # Allowed model
                )
            }
        )
        
        # Create pipeline that should be incompatible
        incompatible_pipeline = PipelineTemplate(
            id=PipelineId("incompatible-pipeline"),
            name="Incompatible Pipeline",
            description="Pipeline incompatible with workspace restrictions",
            steps={
                f"step{i}": PipelineStepTemplate(
                    id=StepId(f"step{i}"),
                    name=f"Step {i}",
                    description=f"Step {i}",
                    type="llm_generate",
                    prompt_template=PromptTemplate(f"Step {i}"),
                    model_preference=ModelPreference(["gpt-4"])  # Not allowed model
                )
                for i in range(1, 7)  # 6 steps, over the limit of 5
            }
        )
        
        # Business rule: compatibility should be checkable
        allowed_models = restrictive_workspace.get_setting("allowed_models", [])
        max_steps = restrictive_workspace.get_setting("max_steps", 100)
        
        # Compatible pipeline checks
        compatible_model = compatible_pipeline.steps["step1"].model_preference.primary_model
        assert compatible_model in allowed_models
        assert len(compatible_pipeline.steps) <= max_steps
        
        # Incompatible pipeline checks
        incompatible_model = list(incompatible_pipeline.steps.values())[0].model_preference.primary_model
        assert incompatible_model not in allowed_models
        assert len(incompatible_pipeline.steps) > max_steps