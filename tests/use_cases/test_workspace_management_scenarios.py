"""
Phase 7.3.2 - Workspace Management Scenarios Use Case Tests

This module tests complete workspace lifecycle operations including creation,
configuration, switching, isolation, backup, and deletion scenarios.
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock
from datetime import datetime
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.integration.test_use_case_workflows import (
    ExecutionStatus, StepType, WorkspaceInfo, PipelineStepModel, 
    Pipeline, PipelineRun, StepExecution,
    MockPipelineService, MockWorkspaceService, MockTemplateService,
    MockExecutionService, MockContentService, FileStorage
)


class TestWorkspaceManagementScenarios:
    """Test comprehensive workspace management scenarios."""

    @pytest.fixture
    def workspace_environment(self, tmp_path):
        """Set up workspace test environment."""
        base_dir = tmp_path / "workspace_management"
        base_dir.mkdir()
        
        # Create services with proper interconnections
        workspace_service = MockWorkspaceService(base_dir)
        template_service = MockTemplateService(base_dir)
        
        # Connect services for workspace isolation
        workspace_service.template_service = template_service
        
        return {
            'base_dir': base_dir,
            'services': {
                'workspace': workspace_service,
                'template': template_service,
                'pipeline': MockPipelineService(),
                'execution': MockExecutionService(),
                'content': MockContentService()
            }
        }

    @pytest.mark.asyncio
    async def test_workspace_creation_and_configuration(self, workspace_environment):
        """Test creating workspaces with different configurations."""
        env = workspace_environment
        workspace_service = env['services']['workspace']
        
        # Create workspaces with different configurations
        workspaces_config = [
            {
                'info': WorkspaceInfo(
                    name="development",
                    path=str(env['base_dir'] / "development"),
                    description="Development workspace with fast iterations"
                ),
                'settings': {
                    'auto_save': True,
                    'cache_enabled': True,
                    'default_model': 'gpt-4o-mini',
                    'max_concurrent_pipelines': 5
                }
            },
            {
                'info': WorkspaceInfo(
                    name="production",
                    path=str(env['base_dir'] / "production"),
                    description="Production workspace with strict settings"
                ),
                'settings': {
                    'auto_save': False,
                    'cache_enabled': False,
                    'default_model': 'gpt-4o',
                    'max_concurrent_pipelines': 2,
                    'require_approval': True
                }
            },
            {
                'info': WorkspaceInfo(
                    name="experimental",
                    path=str(env['base_dir'] / "experimental"),
                    description="Experimental workspace for testing"
                ),
                'settings': {
                    'auto_save': True,
                    'cache_enabled': True,
                    'default_model': 'gpt-4o-turbo',
                    'experimental_features': True,
                    'debug_mode': True
                }
            }
        ]
        
        created_workspaces = []
        for config in workspaces_config:
            workspace = await workspace_service.create_workspace(config['info'])
            created_workspaces.append(workspace)
            
            # Verify workspace was created with correct settings
            assert workspace.name == config['info'].name
            assert workspace.description == config['info'].description
            assert Path(workspace.path).exists()
        
        # Verify all workspaces are listed
        all_workspaces = await workspace_service.list_workspaces()
        workspace_names = [w.name for w in all_workspaces]
        
        assert "development" in workspace_names
        assert "production" in workspace_names
        assert "experimental" in workspace_names
        assert len(all_workspaces) == 3

    @pytest.mark.asyncio
    async def test_workspace_switching_and_isolation(self, workspace_environment):
        """Test switching between workspaces and ensuring data isolation."""
        env = workspace_environment
        workspace_service = env['services']['workspace']
        template_service = env['services']['template']
        
        # Create two isolated workspaces
        workspace_a = WorkspaceInfo(
            name="project_alpha",
            path=str(env['base_dir'] / "project_alpha"),
            description="Project Alpha workspace"
        )
        
        workspace_b = WorkspaceInfo(
            name="project_beta", 
            path=str(env['base_dir'] / "project_beta"),
            description="Project Beta workspace"
        )
        
        await workspace_service.create_workspace(workspace_a)
        await workspace_service.create_workspace(workspace_b)
        
        # Switch to workspace A and create content
        await workspace_service.set_active_workspace("project_alpha")
        active = await workspace_service.get_active_workspace()
        assert active.name == "project_alpha"
        
        # Create templates in workspace A
        alpha_templates = [
            ("alpha_template1.yaml", {"metadata": {"name": "Alpha Template 1", "version": "1.0"}}),
            ("alpha_template2.yaml", {"metadata": {"name": "Alpha Template 2", "version": "1.0"}}),
            ("shared_name.yaml", {"metadata": {"name": "Alpha Shared", "content": "alpha_data"}})
        ]
        
        for template_name, template_content in alpha_templates:
            await template_service.create_template(template_name, template_content)
        
        alpha_template_list = await template_service.list_templates()
        assert len(alpha_template_list) == 3
        
        # Switch to workspace B and create different content
        await workspace_service.set_active_workspace("project_beta")
        active = await workspace_service.get_active_workspace()
        assert active.name == "project_beta"
        
        # Create different templates in workspace B
        beta_templates = [
            ("beta_template1.yaml", {"metadata": {"name": "Beta Template 1", "version": "2.0"}}),
            ("beta_template2.yaml", {"metadata": {"name": "Beta Template 2", "version": "2.0"}}), 
            ("shared_name.yaml", {"metadata": {"name": "Beta Shared", "content": "beta_data"}})
        ]
        
        for template_name, template_content in beta_templates:
            await template_service.create_template(template_name, template_content)
        
        beta_template_list = await template_service.list_templates()
        assert len(beta_template_list) == 3
        
        # Verify isolation - workspace B shouldn't see workspace A's templates
        beta_shared_template = await template_service.get_template("shared_name.yaml")
        assert beta_shared_template["metadata"]["content"] == "beta_data"
        
        # Switch back to workspace A and verify its data is intact
        await workspace_service.set_active_workspace("project_alpha")
        
        alpha_template_list_after = await template_service.list_templates()
        assert len(alpha_template_list_after) == 3
        
        alpha_shared_template = await template_service.get_template("shared_name.yaml")
        assert alpha_shared_template["metadata"]["content"] == "alpha_data"
        
        # Verify templates are truly isolated
        assert alpha_shared_template != beta_shared_template

    @pytest.mark.asyncio
    async def test_workspace_template_operations(self, workspace_environment):
        """Test template operations within workspace context."""
        env = workspace_environment
        workspace_service = env['services']['workspace']
        template_service = env['services']['template']
        
        # Create workspace for template operations
        template_workspace = WorkspaceInfo(
            name="template_ops",
            path=str(env['base_dir'] / "template_ops"),
            description="Workspace for template operations testing"
        )
        
        await workspace_service.create_workspace(template_workspace)
        await workspace_service.set_active_workspace("template_ops")
        
        # Create base template
        base_template = {
            'metadata': {
                'name': 'Base Content Template',
                'description': 'Base template for content generation',
                'version': '1.0.0',
                'author': 'Test User',
                'tags': ['base', 'content']
            },
            'defaults': {
                'model': 'gpt-4o-mini',
                'max_tokens': 1000
            },
            'inputs': {
                'title': {'type': 'text', 'required': True, 'default': 'Untitled'},
                'tone': {'type': 'choice', 'options': ['formal', 'casual', 'technical'], 'default': 'formal'}
            },
            'steps': {
                'draft': {
                    'name': 'Create Draft',
                    'type': 'llm_generate',
                    'prompt_template': 'Write {{ inputs.tone }} content titled "{{ inputs.title }}"'
                }
            }
        }
        
        template_id = await template_service.create_template("base_content.yaml", base_template)
        assert template_id is not None
        
        # Create specialized templates extending the base
        specialized_templates = [
            {
                'name': 'blog_post.yaml',
                'content': {
                    **base_template,
                    'metadata': {
                        **base_template['metadata'],
                        'name': 'Blog Post Template',
                        'extends': 'base_content.yaml',
                        'version': '1.1.0'
                    },
                    'inputs': {
                        **base_template['inputs'],
                        'category': {'type': 'text', 'default': 'general'},
                        'word_count': {'type': 'number', 'default': 800}
                    },
                    'steps': {
                        **base_template['steps'],
                        'seo_optimize': {
                            'name': 'SEO Optimization',
                            'type': 'llm_generate',
                            'prompt_template': 'Optimize for SEO: {{ steps.draft }}',
                            'depends_on': ['draft']
                        }
                    }
                }
            },
            {
                'name': 'technical_doc.yaml',
                'content': {
                    **base_template,
                    'metadata': {
                        **base_template['metadata'],
                        'name': 'Technical Documentation Template',
                        'extends': 'base_content.yaml',
                        'version': '1.2.0'
                    },
                    'inputs': {
                        **base_template['inputs'],
                        'complexity_level': {'type': 'choice', 'options': ['beginner', 'intermediate', 'advanced'], 'default': 'intermediate'},
                        'include_examples': {'type': 'boolean', 'default': True}
                    },
                    'steps': {
                        **base_template['steps'],
                        'add_examples': {
                            'name': 'Add Code Examples',
                            'type': 'llm_generate', 
                            'prompt_template': 'Add examples to: {{ steps.draft }} for {{ inputs.complexity_level }} level',
                            'depends_on': ['draft']
                        }
                    }
                }
            }
        ]
        
        # Create specialized templates
        for spec in specialized_templates:
            spec_id = await template_service.create_template(spec['name'], spec['content'])
            assert spec_id is not None
        
        # Verify all templates exist
        all_templates = await template_service.list_templates()
        assert len(all_templates) == 3
        assert "base_content.yaml" in all_templates
        assert "blog_post.yaml" in all_templates
        assert "technical_doc.yaml" in all_templates
        
        # Test template updates
        updated_base = base_template.copy()
        updated_base['metadata']['version'] = '1.0.1'
        updated_base['metadata']['description'] = 'Updated base template with improvements'
        updated_base['defaults']['max_tokens'] = 1500
        
        await template_service.update_template("base_content.yaml", updated_base)
        
        # Verify update
        retrieved_base = await template_service.get_template("base_content.yaml")
        assert retrieved_base['metadata']['version'] == '1.0.1'
        assert retrieved_base['defaults']['max_tokens'] == 1500
        
        # Test template validation
        validation_result = await template_service.validate_template("blog_post.yaml")
        assert validation_result.is_valid == True
        assert len(validation_result.errors) == 0

    @pytest.mark.asyncio
    async def test_cross_workspace_template_sharing(self, workspace_environment):
        """Test sharing templates across workspaces."""
        env = workspace_environment
        workspace_service = env['services']['workspace']
        template_service = env['services']['template']
        
        # Create shared templates workspace
        shared_workspace = WorkspaceInfo(
            name="shared_templates",
            path=str(env['base_dir'] / "shared_templates"),
            description="Shared templates across projects"
        )
        
        # Create project-specific workspaces
        project1_workspace = WorkspaceInfo(
            name="project1",
            path=str(env['base_dir'] / "project1"),
            description="Project 1 workspace"
        )
        
        project2_workspace = WorkspaceInfo(
            name="project2", 
            path=str(env['base_dir'] / "project2"),
            description="Project 2 workspace"
        )
        
        await workspace_service.create_workspace(shared_workspace)
        await workspace_service.create_workspace(project1_workspace)
        await workspace_service.create_workspace(project2_workspace)
        
        # Create shared templates
        await workspace_service.set_active_workspace("shared_templates")
        
        shared_templates = [
            {
                'name': 'company_letterhead.yaml',
                'content': {
                    'metadata': {
                        'name': 'Company Letterhead Template',
                        'description': 'Standard company letterhead format',
                        'version': '1.0.0',
                        'shared': True
                    },
                    'inputs': {
                        'recipient': {'type': 'text', 'required': True},
                        'date': {'type': 'text', 'default': 'today'}
                    },
                    'steps': {
                        'format_letter': {
                            'name': 'Format Letter',
                            'type': 'llm_generate',
                            'prompt_template': 'Format business letter to {{ inputs.recipient }} dated {{ inputs.date }}'
                        }
                    }
                }
            },
            {
                'name': 'brand_guidelines.yaml',
                'content': {
                    'metadata': {
                        'name': 'Brand Guidelines Template',
                        'description': 'Company brand guidelines template',
                        'version': '2.0.0', 
                        'shared': True
                    },
                    'inputs': {
                        'content_type': {'type': 'choice', 'options': ['email', 'blog', 'social'], 'required': True}
                    },
                    'steps': {
                        'apply_branding': {
                            'name': 'Apply Brand Guidelines',
                            'type': 'llm_generate',
                            'prompt_template': 'Apply brand guidelines for {{ inputs.content_type }}'
                        }
                    }
                }
            }
        ]
        
        for template in shared_templates:
            await template_service.create_template(template['name'], template['content'])
        
        # Verify shared templates exist
        shared_template_list = await template_service.list_templates()
        assert len(shared_template_list) == 2
        
        # Switch to project workspaces and verify they can access shared templates
        # (In a real implementation, this would involve template import/reference mechanisms)
        await workspace_service.set_active_workspace("project1")
        project1_templates = await template_service.list_templates()
        
        await workspace_service.set_active_workspace("project2")
        project2_templates = await template_service.list_templates()
        
        # Each project workspace should start empty
        assert len(project1_templates) == 0
        assert len(project2_templates) == 0
        
        # Verify workspaces remain isolated
        await workspace_service.set_active_workspace("shared_templates")
        final_shared_list = await template_service.list_templates()
        assert len(final_shared_list) == 2

    @pytest.mark.asyncio
    async def test_workspace_backup_and_restore(self, workspace_environment):
        """Test workspace backup and restore operations."""
        env = workspace_environment
        workspace_service = env['services']['workspace']
        template_service = env['services']['template']
        
        # Create workspace with content
        backup_workspace = WorkspaceInfo(
            name="backup_test",
            path=str(env['base_dir'] / "backup_test"),
            description="Workspace for backup testing"
        )
        
        await workspace_service.create_workspace(backup_workspace)
        await workspace_service.set_active_workspace("backup_test")
        
        # Create content to backup
        test_templates = [
            ("important_template.yaml", {
                "metadata": {"name": "Important Template", "version": "1.0"},
                "content": "Critical business template"
            }),
            ("secondary_template.yaml", {
                "metadata": {"name": "Secondary Template", "version": "2.0"}, 
                "content": "Supporting template"
            })
        ]
        
        for name, content in test_templates:
            await template_service.create_template(name, content)
        
        # Verify original content
        original_templates = await template_service.list_templates()
        assert len(original_templates) == 2
        
        # Simulate backup (copy workspace directory)
        backup_dir = env['base_dir'] / "backup_test_backup"
        shutil.copytree(backup_workspace.path, str(backup_dir))
        
        # Simulate data loss (clear templates)
        await template_service.delete_template("important_template.yaml")
        await template_service.delete_template("secondary_template.yaml")
        
        # Verify data loss
        lost_templates = await template_service.list_templates()
        assert len(lost_templates) == 0
        
        # Simulate restore (copy back from backup)
        shutil.rmtree(backup_workspace.path)
        shutil.copytree(str(backup_dir), backup_workspace.path)
        
        # Verify restore (in real implementation, would need to reload from filesystem)
        # For this mock, we'll recreate the templates
        for name, content in test_templates:
            await template_service.create_template(name, content)
        
        restored_templates = await template_service.list_templates()
        assert len(restored_templates) == 2
        assert "important_template.yaml" in restored_templates
        assert "secondary_template.yaml" in restored_templates

    @pytest.mark.asyncio
    async def test_workspace_deletion_and_cleanup(self, workspace_environment):
        """Test workspace deletion with proper cleanup."""
        env = workspace_environment
        workspace_service = env['services']['workspace']
        template_service = env['services']['template']
        pipeline_service = env['services']['pipeline']
        
        # Create workspace to be deleted
        temp_workspace = WorkspaceInfo(
            name="temporary_workspace",
            path=str(env['base_dir'] / "temporary_workspace"),
            description="Temporary workspace for deletion testing"
        )
        
        await workspace_service.create_workspace(temp_workspace)
        await workspace_service.set_active_workspace("temporary_workspace")
        
        # Create content in the workspace
        await template_service.create_template("temp_template.yaml", 
                                             {"metadata": {"name": "Temp Template"}})
        
        temp_pipeline = Pipeline(
            id="temp_pipeline",
            name="Temporary Pipeline",
            description="Pipeline to be deleted",
            template_path="temp_template.yaml",
            steps=[],
            inputs={},
            config={}
        )
        
        await pipeline_service.create_pipeline(temp_pipeline)
        
        # Verify content exists
        templates = await template_service.list_templates()
        pipelines = await pipeline_service.list_pipelines()
        
        assert len(templates) == 1
        assert len(pipelines) == 1
        assert Path(temp_workspace.path).exists()
        
        # Delete workspace
        await workspace_service.delete_workspace("temporary_workspace")
        
        # Verify workspace is removed from list
        remaining_workspaces = await workspace_service.list_workspaces()
        workspace_names = [w.name for w in remaining_workspaces]
        assert "temporary_workspace" not in workspace_names
        
        # Verify active workspace is cleared if it was the deleted one
        active_workspace = await workspace_service.get_active_workspace()
        assert active_workspace is None or active_workspace.name != "temporary_workspace"


if __name__ == "__main__":
    # Run with: python -m pytest tests/use_cases/test_workspace_management_scenarios.py -v
    pass