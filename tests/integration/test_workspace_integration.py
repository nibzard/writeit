# ABOUTME: Integration tests for WriteIt workspace functionality
# ABOUTME: Tests complete workflow of workspace creation, migration, and CLI integration
import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
import os

from writeit.workspace.workspace import Workspace
from writeit.workspace.migration import WorkspaceMigrator
from writeit.infrastructure.base.storage_manager import LMDBStorageManager


class TestWorkspaceIntegration:
    """Integration tests for complete workspace functionality."""

    @pytest.fixture
    def temp_home(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def workspace_manager(self, temp_home):
        """Create workspace manager with temporary directory."""
        return Workspace(temp_home / ".writeit")

    def test_complete_workspace_lifecycle(self, workspace_manager):
        """Test complete workspace lifecycle from initialization to removal."""
        # 1. Initialize WriteIt
        workspace_manager.initialize()
        assert workspace_manager.home_dir.exists()
        assert workspace_manager.workspace_exists("default")

        # 2. Create new workspace
        workspace_manager.create_workspace("project1")
        assert workspace_manager.workspace_exists("project1")

        # 3. Switch to new workspace
        workspace_manager.set_active_workspace("project1")
        assert workspace_manager.get_active_workspace() == "project1"

        # 4. Create storage in new workspace
        storage = LMDBStorageManager(workspace_manager, "project1")
        storage.store_json("test_data", {"project": "project1", "data": "test"})

        # 5. Create another workspace
        workspace_manager.create_workspace("project2")

        # 6. Verify workspace isolation
        storage2 = LMDBStorageManager(workspace_manager, "project2")
        storage2.store_json("test_data", {"project": "project2", "data": "different"})

        # Data should be isolated
        data1 = storage.load_json("test_data")
        data2 = storage2.load_json("test_data")
        assert data1["project"] == "project1"
        assert data2["project"] == "project2"

        # 7. List workspaces
        workspaces = workspace_manager.list_workspaces()
        assert set(workspaces) == {"default", "project1", "project2"}

        # 8. Switch back to default
        workspace_manager.set_active_workspace("default")
        assert workspace_manager.get_active_workspace() == "default"

        # 9. Remove unused workspace
        workspace_manager.remove_workspace("project2")
        assert not workspace_manager.workspace_exists("project2")

        # 10. Verify project1 still exists and has data
        assert workspace_manager.workspace_exists("project1")
        data1_verify = storage.load_json("test_data")
        assert data1_verify["project"] == "project1"

    def test_workspace_migration_flow(self, workspace_manager, temp_home):
        """Test migrating local workspaces to centralized structure."""
        # Initialize centralized workspace
        workspace_manager.initialize()

        # Create mock local workspace
        local_workspace = temp_home / "local_project"
        local_workspace.mkdir()
        local_writeit = local_workspace / ".writeit"
        local_writeit.mkdir()

        # Create local workspace structure
        (local_writeit / "pipelines").mkdir()
        (local_writeit / "articles").mkdir()

        # Add some content
        pipeline_file = local_writeit / "pipelines" / "test-pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump({"name": "test-pipeline", "steps": ["step1", "step2"]}, f)

        article_file = local_writeit / "articles" / "test-article.md"
        with open(article_file, "w") as f:
            f.write("# Test Article\n\nContent here.")

        config_file = local_writeit / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"local_setting": "value"}, f)

        # Migrate the local workspace
        migrator = WorkspaceMigrator(workspace_manager)
        success, message = migrator.migrate_local_workspace(
            local_workspace, "migrated_project"
        )

        assert success, f"Migration failed: {message}"
        assert workspace_manager.workspace_exists("migrated_project")

        # Verify migrated content
        migrated_path = workspace_manager.get_workspace_path("migrated_project")

        # Check pipeline was migrated
        migrated_pipeline = migrated_path / "pipelines" / "test-pipeline.yaml"
        assert migrated_pipeline.exists()
        with open(migrated_pipeline, "r") as f:
            pipeline_data = yaml.safe_load(f)
        assert pipeline_data["name"] == "test-pipeline"

        # Check article was migrated
        migrated_article = migrated_path / "articles" / "test-article.md"
        assert migrated_article.exists()
        with open(migrated_article, "r") as f:
            content = f.read()
        assert "# Test Article" in content

    def test_hierarchical_config_loading(self, workspace_manager, temp_home):
        """Test hierarchical configuration loading with all levels."""
        # Initialize and create workspace
        workspace_manager.initialize()
        workspace_manager.create_workspace("config_test")

        # Set workspace-specific config
        workspace_path = workspace_manager.get_workspace_path("config_test")
        workspace_config = workspace_path / "workspace.yaml"

        # Load existing config and modify it
        with open(workspace_config, "r") as f:
            config_data = yaml.safe_load(f)
        config_data["workspace_setting"] = "workspace_value"
        config_data["override_test"] = "from_workspace"

        with open(workspace_config, "w") as f:
            yaml.dump(config_data, f)

        # Create local config directory
        local_dir = temp_home / "project"
        local_dir.mkdir()
        local_writeit = local_dir / ".writeit"
        local_writeit.mkdir()

        local_config = local_writeit / "config.yaml"
        with open(local_config, "w") as f:
            yaml.dump(
                {"local_setting": "local_value", "override_test": "from_local"}, f
            )

        # Test config loading
        from writeit.workspace.config import ConfigLoader

        config_loader = ConfigLoader(workspace_manager)

        # Test with environment override
        with os.environ.copy() as env:
            env["WRITEIT_ENV_SETTING"] = "env_value"
            env["WRITEIT_OVERRIDE_TEST"] = "from_env"

            # Temporarily set environment
            old_env = os.environ.copy()
            os.environ.update(env)

            try:
                config = config_loader.load_config(
                    workspace="config_test", local_dir=local_dir
                )

                # Verify hierarchy: env > local > workspace > global
                assert config["env"]["setting"] == "env_value"  # From env
                assert config["override"]["test"] == "from_env"  # Env overrides all
                assert config["local_setting"] == "local_value"  # From local
                assert (
                    config["workspace_setting"] == "workspace_value"
                )  # From workspace
                assert (
                    config["active_workspace"] == "default"
                )  # From global (not overridden by local)

            finally:
                # Restore original environment
                os.environ.clear()
                os.environ.update(old_env)

    def test_storage_across_workspaces(self, workspace_manager):
        """Test storage operations across multiple workspaces."""
        workspace_manager.initialize()

        # Create multiple workspaces
        workspace_manager.create_workspace("storage_test1")
        workspace_manager.create_workspace("storage_test2")

        # Create storage managers for each workspace
        storage1 = LMDBStorageManager(workspace_manager, "storage_test1")
        storage2 = LMDBStorageManager(workspace_manager, "storage_test2")

        # Store data in each workspace
        test_data1 = {
            "workspace": "storage_test1",
            "articles": ["article1", "article2"],
            "metadata": {"created": "2023-01-01", "author": "test"},
        }

        test_data2 = {
            "workspace": "storage_test2",
            "articles": ["article3", "article4", "article5"],
            "metadata": {"created": "2023-01-02", "author": "test2"},
        }

        # Store in different databases within each workspace
        storage1.store_json("workspace_info", test_data1, db_name="metadata")
        storage1.store_json(
            "article_1",
            {"title": "Article 1", "content": "Content 1"},
            db_name="articles",
        )

        storage2.store_json("workspace_info", test_data2, db_name="metadata")
        storage2.store_json(
            "article_3",
            {"title": "Article 3", "content": "Content 3"},
            db_name="articles",
        )

        # Verify data isolation
        info1 = storage1.load_json("workspace_info", db_name="metadata")
        info2 = storage2.load_json("workspace_info", db_name="metadata")

        assert info1["workspace"] == "storage_test1"
        assert info2["workspace"] == "storage_test2"
        assert len(info1["articles"]) == 2
        assert len(info2["articles"]) == 3

        # Verify articles are isolated
        article1 = storage1.load_json("article_1", db_name="articles")
        article3_from_ws1 = storage1.load_json(
            "article_3", db_name="articles", default=None
        )
        article3_from_ws2 = storage2.load_json("article_3", db_name="articles")

        assert article1["title"] == "Article 1"
        assert article3_from_ws1 is None  # Should not exist in workspace1
        assert article3_from_ws2["title"] == "Article 3"

        # Test cross-workspace key listing
        keys1 = storage1.list_keys(db_name="articles")
        keys2 = storage2.list_keys(db_name="articles")

        assert "article_1" in keys1
        assert "article_3" not in keys1
        assert "article_3" in keys2
        assert "article_1" not in keys2

    def test_workspace_with_real_pipeline_structure(self, workspace_manager):
        """Test workspace with realistic pipeline and article structure."""
        workspace_manager.initialize()
        workspace_manager.create_workspace("blog_project")

        workspace_path = workspace_manager.get_workspace_path("blog_project")

        # Create realistic pipeline templates
        pipelines_dir = workspace_path / "pipelines"

        blog_pipeline = {
            "name": "blog-post",
            "description": "Generate blog post from outline",
            "steps": [
                {
                    "name": "angle_generation",
                    "type": "llm_generation",
                    "models": ["gpt-4", "claude-sonnet"],
                    "prompt_template": "Generate 3 different angles for: {topic}",
                },
                {
                    "name": "outline_creation",
                    "type": "llm_generation",
                    "models": ["gpt-4"],
                    "prompt_template": "Create detailed outline for: {selected_angle}",
                },
                {
                    "name": "draft_writing",
                    "type": "llm_generation",
                    "models": ["claude-sonnet", "gpt-4"],
                    "prompt_template": "Write blog post draft from outline: {outline}",
                },
                {
                    "name": "final_polish",
                    "type": "llm_generation",
                    "models": ["claude-sonnet"],
                    "prompt_template": "Polish and refine: {draft}",
                },
            ],
        }

        with open(pipelines_dir / "blog-post.yaml", "w") as f:
            yaml.dump(blog_pipeline, f, default_flow_style=False)

        # Create articles directory with sample outputs
        articles_dir = workspace_path / "articles"

        sample_article = """# How AI is Transforming Content Creation

## Introduction
Artificial Intelligence has revolutionized how we approach content creation...

## The Evolution of AI Writing Tools
From simple grammar checkers to sophisticated language models...

## Impact on Writers and Content Creators  
The relationship between human creativity and AI assistance...

## Conclusion
As AI continues to evolve, the future of content creation looks promising...
"""

        with open(articles_dir / "ai-content-creation.md", "w") as f:
            f.write(sample_article)

        # Store pipeline execution history in storage
        storage = LMDBStorageManager(workspace_manager, "blog_project")

        pipeline_run = {
            "pipeline_id": "blog-post-001",
            "status": "completed",
            "started_at": "2023-01-15T10:00:00Z",
            "completed_at": "2023-01-15T10:45:00Z",
            "steps": [
                {
                    "name": "angle_generation",
                    "status": "completed",
                    "selected_response": 1,
                    "responses": [
                        "Technical deep-dive into AI writing capabilities",
                        "Human perspective on AI content collaboration",
                        "Business impact of AI content tools",
                    ],
                },
                {
                    "name": "outline_creation",
                    "status": "completed",
                    "selected_response": 0,
                    "responses": [
                        "I. Introduction\nII. Evolution of AI Writing\nIII. Impact on Writers\nIV. Conclusion"
                    ],
                },
            ],
            "final_article": "ai-content-creation.md",
        }

        storage.store_json("pipeline_run_001", pipeline_run, db_name="pipeline_runs")

        # Verify complete workspace structure
        assert (pipelines_dir / "blog-post.yaml").exists()
        assert (articles_dir / "ai-content-creation.md").exists()

        # Verify pipeline configuration
        with open(pipelines_dir / "blog-post.yaml", "r") as f:
            loaded_pipeline = yaml.safe_load(f)
        assert loaded_pipeline["name"] == "blog-post"
        assert len(loaded_pipeline["steps"]) == 4

        # Verify storage data
        stored_run = storage.load_json("pipeline_run_001", db_name="pipeline_runs")
        assert stored_run["pipeline_id"] == "blog-post-001"
        assert stored_run["status"] == "completed"
        assert len(stored_run["steps"]) == 2

        # Verify article content
        with open(articles_dir / "ai-content-creation.md", "r") as f:
            content = f.read()
        assert "# How AI is Transforming Content Creation" in content
        assert "## Introduction" in content
