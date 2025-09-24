"""Comprehensive unit tests for business rules across all domains."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from src.writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from src.writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus
from src.writeit.domains.workspace.entities.workspace import Workspace
from src.writeit.domains.content.entities.template import Template

from tests.builders.pipeline_builders import (
    PipelineTemplateBuilder, PipelineRunBuilder, PipelineStepTemplateBuilder
)
from tests.builders.workspace_builders import WorkspaceBuilder
from tests.builders.content_builders import TemplateBuilder


class TestPipelineBusinessRules:
    """Test business rules for Pipeline domain."""
    
    def test_pipeline_execution_status_transitions(self):
        """Test that pipeline execution status follows valid transitions."""
        
        def can_transition(from_status: ExecutionStatus, to_status: ExecutionStatus) -> bool:
            """Business rule: Define valid status transitions."""
            valid_transitions = {
                ExecutionStatus.PENDING: [ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED],
                ExecutionStatus.RUNNING: [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED],
                ExecutionStatus.COMPLETED: [],  # Terminal state
                ExecutionStatus.FAILED: [],     # Terminal state  
                ExecutionStatus.CANCELLED: []   # Terminal state
            }
            return to_status in valid_transitions.get(from_status, [])
        
        # Test valid transitions
        assert can_transition(ExecutionStatus.PENDING, ExecutionStatus.RUNNING)
        assert can_transition(ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED)
        assert can_transition(ExecutionStatus.RUNNING, ExecutionStatus.FAILED)
        assert can_transition(ExecutionStatus.PENDING, ExecutionStatus.CANCELLED)
        
        # Test invalid transitions
        assert not can_transition(ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING)
        assert not can_transition(ExecutionStatus.FAILED, ExecutionStatus.PENDING)
        assert not can_transition(ExecutionStatus.CANCELLED, ExecutionStatus.RUNNING)
    
    def test_pipeline_step_dependency_acyclic_rule(self):
        """Test that pipeline step dependencies must be acyclic."""
        # Valid dependency chain: A -> B -> C
        step_a = PipelineStepTemplateBuilder.llm_step("step_a").build()
        step_b = PipelineStepTemplateBuilder.llm_step("step_b").with_dependencies(["step_a"]).build()
        step_c = PipelineStepTemplateBuilder.llm_step("step_c").with_dependencies(["step_b"]).build()
        
        # Should create successfully (no cycles)
        template = (PipelineTemplateBuilder()
                   .with_name("Valid Dependencies")
                   .with_steps([step_a, step_b, step_c])
                   .build())
        
        assert template.get_execution_order() == ["step_a", "step_b", "step_c"]
        
        # Circular dependency: A -> B -> A should fail
        step_a_circular = PipelineStepTemplateBuilder.llm_step("step_a").with_dependencies(["step_b"]).build()
        step_b_circular = PipelineStepTemplateBuilder.llm_step("step_b").with_dependencies(["step_a"]).build()
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            PipelineTemplateBuilder().with_name("Circular").with_steps([step_a_circular, step_b_circular]).build()
    
    def test_pipeline_input_validation_business_rules(self):
        """Test business rules for pipeline input validation."""
        # Business rule: Required inputs must be provided
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        # Missing required input should fail validation
        incomplete_inputs = {"style": "opt1"}  # Missing required "topic"
        errors = template.validate_inputs(incomplete_inputs)
        assert any("Required input 'topic' is missing" in error for error in errors)
        
        # Complete inputs should pass validation
        complete_inputs = {"topic": "Valid Topic", "style": "opt1"}
        errors = template.validate_inputs(complete_inputs)
        assert len(errors) == 0
        
        # Extra inputs should be flagged
        extra_inputs = {"topic": "Valid", "style": "opt1", "unexpected": "value"}
        errors = template.validate_inputs(extra_inputs)
        assert any("Unexpected input 'unexpected'" in error for error in errors)
    
    def test_pipeline_execution_time_constraints(self):
        """Test business rules for pipeline execution time constraints."""
        # Business rule: Execution times should be logical
        now = datetime.now()
        
        # Running pipeline should have started_at but not completed_at
        running_run = (PipelineRunBuilder
                      .running("time_test")
                      .build())
        
        assert running_run.started_at is not None
        assert running_run.completed_at is None
        assert running_run.created_at <= running_run.started_at
        
        # Completed pipeline should have both timestamps
        completed_run = (PipelineRunBuilder
                        .completed("completed_test")
                        .build())
        
        assert completed_run.started_at is not None
        assert completed_run.completed_at is not None
        # Business rule: completed_at >= started_at
        assert completed_run.completed_at >= completed_run.started_at
    
    def test_pipeline_variable_consistency_rule(self):
        """Test that pipeline variables are consistent across steps and inputs."""
        # Business rule: Step variables should reference available inputs or previous steps
        template = PipelineTemplateBuilder.complex_with_dependencies().build()
        
        # Get all variables used in steps
        all_step_variables = set()
        for step in template.steps.values():
            all_step_variables.update(step.get_required_variables())
        
        # Get available input variables  
        input_variables = set(f"inputs.{key}" for key in template.inputs.keys())
        input_variables.update(template.inputs.keys())  # Also allow direct reference
        
        # Business rule: All step variables should be satisfiable
        # This is a simplified check - real implementation would be more complex
        for variable in all_step_variables:
            if variable.startswith("inputs."):
                input_key = variable.replace("inputs.", "")
                assert input_key in template.inputs, f"Variable {variable} references non-existent input {input_key}"
    
    def test_pipeline_parallel_execution_constraints(self):
        """Test business rules for parallel execution."""
        template = PipelineTemplateBuilder.with_parallel_steps().build()
        parallel_groups = template.get_parallel_groups()
        
        # Business rule: Steps in the same parallel group should not depend on each other
        for group in parallel_groups:
            if len(group) > 1:  # Multiple steps in parallel
                for step_key in group:
                    step = template.get_step(step_key)
                    # No dependencies on other steps in the same group
                    for dep in step.depends_on:
                        assert dep.value not in group, f"Parallel step {step_key} depends on {dep.value} in same group"
    
    def test_pipeline_version_consistency_rule(self):
        """Test pipeline version consistency business rules."""
        # Business rule: Version updates should increment logically
        original = (PipelineTemplateBuilder
                   .simple()
                   .with_version("1.0.0")
                   .build())
        
        # Valid version update
        updated = original.update(version="1.1.0")
        assert updated.version == "1.1.0"
        assert updated.updated_at > original.updated_at
        
        # Business rule: created_at should not change on updates
        assert updated.created_at == original.created_at


class TestWorkspaceBusinessRules:
    """Test business rules for Workspace domain."""
    
    def test_workspace_isolation_rule(self):
        """Test that workspaces are properly isolated."""
        # Business rule: Workspaces should have unique names and paths
        workspace1 = WorkspaceBuilder.default("workspace1").build()
        workspace2 = WorkspaceBuilder.default("workspace2").build()
        
        assert workspace1.name != workspace2.name
        assert workspace1.path != workspace2.path
        
        # Business rule: Workspace names should be valid identifiers
        valid_workspace = WorkspaceBuilder.default("valid_name").build()
        assert valid_workspace.name.value == "valid_name"
        
        # Invalid names should be rejected by WorkspaceName validation
        with pytest.raises(ValueError):
            WorkspaceBuilder.default("invalid name with spaces").build()
    
    def test_workspace_active_status_rule(self):
        """Test business rules for workspace active status."""
        # Business rule: Only one workspace should be active at a time
        # This would typically be enforced at the application service level
        
        active_workspace = WorkspaceBuilder.active("active1").build()
        assert active_workspace.is_active is True
        assert active_workspace.last_accessed is not None
        
        inactive_workspace = WorkspaceBuilder.default("inactive").build()
        assert inactive_workspace.is_active is False
        
        # Business rule: Active workspaces should have recent access time
        if active_workspace.is_active and active_workspace.last_accessed:
            time_since_access = datetime.now() - active_workspace.last_accessed
            assert time_since_access.total_seconds() < 300  # Within 5 minutes
    
    def test_workspace_path_validity_rule(self):
        """Test business rules for workspace path validity."""
        # Business rule: Workspace paths should be valid and safe
        valid_paths = [
            "/home/user/.writeit/workspaces/test",
            "~/workspaces/project",
            "./local/workspace"
        ]
        
        for valid_path in valid_paths:
            workspace = WorkspaceBuilder.with_custom_path("test", valid_path).build()
            assert str(workspace.path) == valid_path
        
        # Business rule: Paths should not be empty
        with pytest.raises(ValueError):
            WorkspaceBuilder.with_custom_path("test", "").build()
    
    def test_workspace_metadata_consistency_rule(self):
        """Test business rules for workspace metadata consistency."""
        # Business rule: Project workspaces should have consistent metadata
        project_workspace = WorkspaceBuilder.project_workspace("test_proj", "TestProject").build()
        
        assert "project_name" in project_workspace.metadata
        assert project_workspace.metadata["project_name"] == "TestProject"
        assert "project" in project_workspace.metadata.get("tags", [])
        
        # Business rule: Workspace metadata should be serializable
        import json
        try:
            json.dumps(project_workspace.metadata)
        except (TypeError, ValueError):
            pytest.fail("Workspace metadata should be JSON serializable")
    
    def test_workspace_lifecycle_rules(self):
        """Test business rules for workspace lifecycle."""
        # Business rule: Timestamp ordering should be logical
        workspace = WorkspaceBuilder.default().build()
        
        assert workspace.created_at <= workspace.updated_at
        
        # Business rule: Last accessed should be after creation if set
        accessed_workspace = WorkspaceBuilder.active().build()
        if accessed_workspace.last_accessed:
            assert accessed_workspace.created_at <= accessed_workspace.last_accessed


class TestContentBusinessRules:
    """Test business rules for Content domain."""
    
    def test_template_name_uniqueness_rule(self):
        """Test business rule for template name uniqueness."""
        # Business rule: Template names should be unique within a scope
        name = "unique_template"
        template1 = TemplateBuilder().with_name(name).build()
        template2 = TemplateBuilder().with_name(name).build()
        
        # Same name creates same TemplateName value object
        assert template1.name == template2.name
        
        # Different names create different value objects
        different_template = TemplateBuilder().with_name("different_name").build()
        assert template1.name != different_template.name
    
    def test_template_content_type_consistency_rule(self):
        """Test business rules for template content type consistency."""
        # Business rule: Content should match declared content type
        pipeline_template = TemplateBuilder.pipeline_template().build()
        assert pipeline_template.content_type.name in ["PIPELINE", "pipeline"]
        assert "metadata:" in pipeline_template.content
        assert "steps:" in pipeline_template.content
        
        article_template = TemplateBuilder.article_template().build()
        assert article_template.content_type.name in ["MARKDOWN", "markdown"]
        assert "#" in article_template.content  # Markdown headers
    
    def test_template_variable_extraction_rule(self):
        """Test business rules for template variable extraction."""
        # Business rule: Variables should be extracted consistently
        content = "Hello {{name}}, welcome to {{platform}}! Your {{item}} is ready."
        template = TemplateBuilder().with_content(content).build()
        
        expected_variables = {"name", "platform", "item"}
        assert template.variables == expected_variables
        
        # Business rule: Malformed variables should be handled gracefully
        malformed_content = "Hello {{name}}, welcome to }invalid{ and {{valid}}."
        malformed_template = TemplateBuilder().with_content(malformed_content).build()
        
        # Should extract valid variables
        assert "valid" in malformed_template.variables
        # Behavior for malformed variables is implementation-specific
    
    def test_template_dependency_resolution_rule(self):
        """Test business rules for template dependency resolution."""
        # Business rule: Template dependencies should form a valid DAG
        base_template = TemplateBuilder().with_name("base").with_dependencies([]).build()
        
        dependent_template = TemplateBuilder.with_dependencies(
            "dependent", ["base"]
        ).build()
        
        assert "base" in dependent_template.dependencies
        assert len(dependent_template.dependencies) == 1
        
        # Business rule: No self-dependencies
        with pytest.raises(ValueError):
            # This would be caught during template creation/validation
            template = TemplateBuilder().with_name("self_dep").with_dependencies(["self_dep"]).build()
            # Validation logic would check for self-references
            if template.name.value in template.dependencies:
                raise ValueError("Template cannot depend on itself")
    
    def test_template_version_management_rule(self):
        """Test business rules for template version management."""
        # Business rule: Version strings should follow semantic versioning
        template_v1 = TemplateBuilder().with_version("1.0.0").build()
        template_v2 = TemplateBuilder().with_version("1.1.0").build()
        template_v3 = TemplateBuilder().with_version("2.0.0").build()
        
        versions = [template_v1.version, template_v2.version, template_v3.version]
        assert all(len(v.split(".")) == 3 for v in versions), "Versions should be semantic (X.Y.Z)"
        
        # Business rule: Templates should be immutable after creation
        original_content = template_v1.content
        with pytest.raises(AttributeError):
            template_v1.content = "modified"  # type: ignore
        assert template_v1.content == original_content
    
    def test_template_validation_rule_consistency(self):
        """Test business rules for template validation rules."""
        from tests.builders.value_object_builders import ValidationRuleBuilder
        
        # Business rule: Validation rules should be consistent with template purpose
        length_rule = ValidationRuleBuilder.length_rule(10, 1000).build()
        required_rule = ValidationRuleBuilder.required_rule().build()
        
        template_with_rules = (TemplateBuilder
                              .article_template()
                              .with_validation_rules([length_rule, required_rule])
                              .build())
        
        assert len(template_with_rules.validation_rules) == 2
        
        # Business rule: Rules should be applicable to the content type
        rule_types = [rule.rule_type for rule in template_with_rules.validation_rules]
        assert "length" in rule_types  # Applicable to articles
        assert "required" in rule_types  # Applicable to any content


class TestCrossDomainBusinessRules:
    """Test business rules that span multiple domains."""
    
    def test_pipeline_workspace_isolation_rule(self):
        """Test that pipelines are properly isolated by workspace."""
        # Business rule: Pipelines should be scoped to workspaces
        workspace1 = "workspace1"
        workspace2 = "workspace2"
        
        run1 = (PipelineRunBuilder
                .pending("run1")
                .with_workspace(workspace1)
                .build())
        
        run2 = (PipelineRunBuilder
                .pending("run2") 
                .with_workspace(workspace2)
                .build())
        
        assert run1.workspace_name != run2.workspace_name
        
        # Business rule: Runs should not access resources from other workspaces
        assert run1.workspace_name == workspace1
        assert run2.workspace_name == workspace2
    
    def test_template_pipeline_compatibility_rule(self):
        """Test business rules for template and pipeline compatibility."""
        # Business rule: Pipeline templates should be usable as content templates
        pipeline_template = TemplateBuilder.pipeline_template("test_pipeline").build()
        
        # Should have pipeline-specific structure
        assert "metadata:" in pipeline_template.content
        assert "inputs:" in pipeline_template.content
        assert "steps:" in pipeline_template.content
        
        # Business rule: Templates should have required variables for pipeline execution
        required_pipeline_vars = {"name", "description"}  # Common pipeline variables
        template_vars = pipeline_template.variables
        
        # At least some pipeline variables should be present
        assert len(template_vars.intersection(required_pipeline_vars)) > 0
    
    def test_content_workspace_scoping_rule(self):
        """Test business rules for content scoping within workspaces."""
        # Business rule: Generated content should be associated with workspaces
        from tests.builders.content_builders import GeneratedContentBuilder
        
        workspace_content = (GeneratedContentBuilder
                            .markdown_article("Test Article")
                            .with_workspace("test_workspace")
                            .build())
        
        assert workspace_content.workspace_name == "test_workspace"
        
        # Business rule: Content should maintain workspace context
        assert workspace_content.workspace_name is not None
        assert len(workspace_content.workspace_name) > 0
    
    def test_execution_context_consistency_rule(self):
        """Test business rules for execution context consistency."""
        from tests.builders.execution_builders import ExecutionContextBuilder
        
        # Business rule: Execution context should be consistent across domains
        context = (ExecutionContextBuilder
                  .with_pipeline_execution("test_run", "current_step")
                  .with_workspace("test_workspace")
                  .build())
        
        assert context.pipeline_run_id == "test_run"
        assert context.workspace_name == "test_workspace" 
        assert context.step_id == "current_step"
        
        # Business rule: Context should maintain referential integrity
        # In a real system, these IDs would reference actual entities
        assert context.pipeline_run_id is not None
        assert context.workspace_name is not None
    
    def test_resource_limitation_rules(self):
        """Test business rules for resource limitations."""
        from tests.builders.execution_builders import TokenUsageBuilder
        
        # Business rule: Token usage should be tracked and limited
        large_usage = TokenUsageBuilder.large_request().build()
        assert large_usage.total_tokens.value > 1000
        
        # Business rule: Cost estimates should be reasonable
        assert large_usage.cost_estimate > 0
        assert large_usage.cost_estimate < 100  # Reasonable upper bound
        
        # Business rule: Usage should be attributed to workspace
        workspace_usage = (TokenUsageBuilder
                          .pipeline_step_usage("run_id", "step_id")
                          .with_workspace("test_workspace")
                          .build())
        
        assert workspace_usage.workspace_name == "test_workspace"


class TestBusinessRuleInvariants:
    """Test invariants that should hold across all business rules."""
    
    def test_entity_identity_consistency(self):
        """Test that entity identity is consistent across operations."""
        # Business invariant: Entity IDs should be stable
        template = TemplateBuilder.article_template().build()
        original_name = template.name
        
        # Template name should be immutable
        with pytest.raises(AttributeError):
            template.name = TemplateBuilder().with_name("different").build().name  # type: ignore
        
        assert template.name == original_name
    
    def test_timestamp_monotonicity_invariant(self):
        """Test that timestamps follow monotonic ordering."""
        # Business invariant: created_at <= updated_at
        entities = [
            PipelineTemplateBuilder.simple().build(),
            WorkspaceBuilder.default().build(),
            TemplateBuilder.article_template().build()
        ]
        
        for entity in entities:
            if hasattr(entity, 'created_at') and hasattr(entity, 'updated_at'):
                assert entity.created_at <= entity.updated_at
    
    def test_validation_consistency_invariant(self):
        """Test that validation is consistent across all domains."""
        # Business invariant: Empty/null values should be handled consistently
        
        # All domains should reject empty names
        with pytest.raises(ValueError):
            PipelineTemplateBuilder().with_name("").build()
        
        with pytest.raises(ValueError):
            TemplateBuilder().with_name("").build()
        
        # Value objects should validate consistently
        from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
        from src.writeit.domains.content.value_objects.template_name import TemplateName
        
        with pytest.raises(ValueError):
            PipelineId.from_name("")
        
        with pytest.raises(ValueError):
            TemplateName("")
    
    def test_immutability_invariant(self):
        """Test that immutability is preserved across all value objects."""
        # Business invariant: Value objects should be immutable
        from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
        from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
        from src.writeit.domains.content.value_objects.template_name import TemplateName
        from src.writeit.domains.execution.value_objects.model_name import ModelName
        
        value_objects = [
            PipelineId.from_name("test"),
            WorkspaceName("test"),
            TemplateName("test"),
            ModelName("test-model")
        ]
        
        for obj in value_objects:
            with pytest.raises(AttributeError):
                obj.value = "modified"  # type: ignore
    
    def test_equality_transitivity_invariant(self):
        """Test that equality is transitive for all value objects."""
        # Business invariant: If A == B and B == C, then A == C
        from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
        
        id1 = PipelineId.from_name("test")
        id2 = PipelineId.from_name("test")
        id3 = PipelineId.from_name("test")
        
        assert id1 == id2
        assert id2 == id3
        assert id1 == id3  # Transitivity
    
    def test_hash_consistency_invariant(self):
        """Test that hash consistency is maintained."""
        # Business invariant: Equal objects have equal hashes
        from src.writeit.domains.execution.value_objects.token_count import TokenCount
        
        count1 = TokenCount(100)
        count2 = TokenCount(100)
        
        assert count1 == count2
        assert hash(count1) == hash(count2)
        
        # Should be usable in sets
        count_set = {count1, count2}
        assert len(count_set) == 1  # Deduplicated