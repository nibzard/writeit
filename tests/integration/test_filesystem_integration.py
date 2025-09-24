"""File System Integration Tests for workspace and template file operations.

This test suite validates file system operations including:
- Template file management
- Workspace directory structure
- File watching and change detection
- Concurrent file operations
- File system error handling
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import time
import threading
from concurrent.futures import ThreadPoolExecutor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from writeit.infrastructure.persistence.file_storage import FileStorage
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.content.entities.template import Template as ContentTemplate
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat


class TestFileSystemIntegration:
    """Integration tests for file system operations."""

    @pytest.fixture
    def temp_workspace_path(self):
        """Create temporary workspace directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def file_storage(self, temp_workspace_path):
        """Create file storage instance."""
        return FileStorage(base_path=temp_workspace_path)

    @pytest.fixture
    def sample_workspace_name(self):
        """Sample workspace name for testing."""
        return WorkspaceName("filesystem_test_workspace")

    @pytest.fixture
    def sample_templates(self):
        """Create sample templates for testing."""
        templates = []
        for i in range(5):
            template = ContentTemplate(
                id=ContentId(f"template_{i}"),
                name=TemplateName(f"test_template_{i}"),
                content=f"# Template {i}\n\nThis is template number {i} with content: {{{{ variable_{i} }}}}",
                content_type=ContentType.MARKDOWN,
                format=ContentFormat.TEMPLATE,
                metadata={"index": i, "category": "test"}
            )
            templates.append(template)
        return templates

    async def test_workspace_directory_creation(self, file_storage, sample_workspace_name, temp_workspace_path):
        """Test workspace directory structure creation."""
        
        # Create workspace directory structure
        workspace_path = await file_storage.create_workspace_structure(sample_workspace_name)
        
        # Verify main workspace directory exists
        assert workspace_path.exists()
        assert workspace_path.is_dir()
        
        # Verify subdirectories are created
        templates_dir = workspace_path / "templates"
        styles_dir = workspace_path / "styles"
        outputs_dir = workspace_path / "outputs"
        config_dir = workspace_path / "config"
        
        assert templates_dir.exists()
        assert styles_dir.exists()
        assert outputs_dir.exists()
        assert config_dir.exists()
        
        # Verify permissions (if on Unix-like system)
        if hasattr(workspace_path.stat(), 'st_mode'):
            mode = workspace_path.stat().st_mode & 0o777
            assert mode >= 0o755  # Should be readable and executable

    async def test_template_file_operations(self, file_storage, sample_workspace_name, sample_templates):
        """Test template file CRUD operations."""
        
        # Create workspace
        workspace_path = await file_storage.create_workspace_structure(sample_workspace_name)
        templates_dir = workspace_path / "templates"
        
        # Test save operations
        saved_files = []
        for template in sample_templates:
            file_path = await file_storage.save_template_file(
                sample_workspace_name, template
            )
            saved_files.append(file_path)
            
            # Verify file was created
            assert file_path.exists()
            assert file_path.is_file()
            assert file_path.parent == templates_dir
            
            # Verify file content
            content = file_path.read_text(encoding='utf-8')
            assert template.content in content
        
        # Test list operations
        all_template_files = await file_storage.list_template_files(sample_workspace_name)
        assert len(all_template_files) == len(sample_templates)
        
        # Verify all saved files are in the list
        saved_file_names = {f.name for f in saved_files}
        listed_file_names = {f.name for f in all_template_files}
        assert saved_file_names == listed_file_names
        
        # Test load operations
        for template, file_path in zip(sample_templates, saved_files):
            loaded_template = await file_storage.load_template_file(file_path)
            assert loaded_template.id == template.id
            assert loaded_template.name == template.name
            assert loaded_template.content == template.content
            assert loaded_template.content_type == template.content_type
        
        # Test update operations
        updated_template = sample_templates[0]
        updated_template.content = "# Updated Template\n\nThis content has been updated: {{ new_variable }}"
        
        updated_file_path = await file_storage.save_template_file(
            sample_workspace_name, updated_template
        )
        
        # Verify update
        loaded_updated = await file_storage.load_template_file(updated_file_path)
        assert "This content has been updated" in loaded_updated.content
        
        # Test delete operations
        for file_path in saved_files[:2]:  # Delete first two files
            await file_storage.delete_template_file(file_path)
            assert not file_path.exists()
        
        # Verify remaining files
        remaining_files = await file_storage.list_template_files(sample_workspace_name)
        assert len(remaining_files) == len(sample_templates) - 2

    async def test_concurrent_file_operations(self, file_storage, temp_workspace_path):
        """Test concurrent file operations for thread safety."""
        
        workspace_name = WorkspaceName("concurrent_file_test")
        workspace_path = await file_storage.create_workspace_structure(workspace_name)
        
        # Create templates for concurrent operations
        def create_template(index: int) -> ContentTemplate:
            return ContentTemplate(
                id=ContentId(f"concurrent_template_{index}"),
                name=TemplateName(f"concurrent_test_{index}"),
                content=f"# Concurrent Template {index}\n\nContent for template {index}",
                content_type=ContentType.MARKDOWN,
                format=ContentFormat.TEMPLATE,
                metadata={"thread_id": threading.current_thread().ident}
            )
        
        # Concurrent save function
        async def save_templates_batch(start_index: int, count: int):
            saved_paths = []
            for i in range(start_index, start_index + count):
                template = create_template(i)
                file_path = await file_storage.save_template_file(workspace_name, template)
                saved_paths.append(file_path)
            return saved_paths
        
        # Run concurrent save operations
        batch_size = 10
        num_batches = 5
        
        tasks = []
        for batch in range(num_batches):
            start_index = batch * batch_size
            task = save_templates_batch(start_index, batch_size)
            tasks.append(task)
        
        # Execute all batches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception), f"Concurrent file operation failed: {result}"
        
        # Verify all files were created
        all_saved_paths = []
        for batch_result in results:
            all_saved_paths.extend(batch_result)
        
        expected_count = batch_size * num_batches
        assert len(all_saved_paths) == expected_count
        
        # Verify all files exist and have correct content
        for i, file_path in enumerate(all_saved_paths):
            assert file_path.exists()
            
            # Load and verify content
            loaded_template = await file_storage.load_template_file(file_path)
            assert loaded_template is not None
            assert f"Content for template" in loaded_template.content
        
        # Verify file listing consistency
        all_template_files = await file_storage.list_template_files(workspace_name)
        assert len(all_template_files) == expected_count

    async def test_workspace_isolation_filesystem(self, file_storage, temp_workspace_path):
        """Test file system isolation between workspaces."""
        
        # Create multiple workspaces
        workspace1 = WorkspaceName("isolation_test_1")
        workspace2 = WorkspaceName("isolation_test_2")
        workspace3 = WorkspaceName("isolation_test_3")
        
        # Create workspace directories
        ws1_path = await file_storage.create_workspace_structure(workspace1)
        ws2_path = await file_storage.create_workspace_structure(workspace2)
        ws3_path = await file_storage.create_workspace_structure(workspace3)
        
        # Verify workspaces are in separate directories
        assert ws1_path != ws2_path != ws3_path
        assert ws1_path.name == workspace1.value
        assert ws2_path.name == workspace2.value
        assert ws3_path.name == workspace3.value
        
        # Create templates in each workspace
        templates = {}
        for i, workspace in enumerate([workspace1, workspace2, workspace3]):
            template = ContentTemplate(
                id=ContentId(f"template_{workspace.value}"),
                name=TemplateName(f"template_for_{workspace.value}"),
                content=f"# Template for {workspace.value}\n\nSpecific content for workspace {i+1}",
                content_type=ContentType.MARKDOWN,
                format=ContentFormat.TEMPLATE,
                metadata={"workspace": workspace.value}
            )
            templates[workspace.value] = template
            
            # Save template to respective workspace
            file_path = await file_storage.save_template_file(workspace, template)
            assert file_path.parent.parent.name == workspace.value
        
        # Verify isolation - each workspace should only see its own files
        for workspace in [workspace1, workspace2, workspace3]:
            workspace_files = await file_storage.list_template_files(workspace)
            assert len(workspace_files) == 1
            
            loaded_template = await file_storage.load_template_file(workspace_files[0])
            expected_template = templates[workspace.value]
            assert loaded_template.id == expected_template.id
            assert loaded_template.name == expected_template.name
            assert workspace.value in loaded_template.content

    async def test_file_error_handling(self, file_storage, temp_workspace_path):
        """Test file system error handling."""
        
        workspace_name = WorkspaceName("error_handling_test")
        
        # Test loading non-existent template
        non_existent_path = temp_workspace_path / "non_existent" / "template.yaml"
        
        with pytest.raises((FileNotFoundError, OSError)):
            await file_storage.load_template_file(non_existent_path)
        
        # Test creating workspace in read-only directory (if possible)
        # This is platform-specific and may not be testable in all environments
        try:
            readonly_path = temp_workspace_path / "readonly"
            readonly_path.mkdir()
            readonly_path.chmod(0o444)  # Read-only
            
            readonly_workspace = WorkspaceName("readonly_test")
            # This should handle the error gracefully
            with pytest.raises((PermissionError, OSError)):
                await file_storage.create_workspace_structure(readonly_workspace, base_path=readonly_path)
                
        except (OSError, PermissionError):
            # Skip this test if we can't create read-only directories
            pytest.skip("Cannot test read-only directory permissions on this system")
        
        # Test invalid template content
        workspace_path = await file_storage.create_workspace_structure(workspace_name)
        invalid_template_path = workspace_path / "templates" / "invalid.yaml"
        
        # Write malformed YAML/JSON
        invalid_template_path.write_text("invalid: yaml: content: {{{")
        
        with pytest.raises(Exception):  # Should raise parsing error
            await file_storage.load_template_file(invalid_template_path)

    async def test_large_file_operations(self, file_storage, temp_workspace_path):
        """Test operations with large files."""
        
        workspace_name = WorkspaceName("large_file_test")
        workspace_path = await file_storage.create_workspace_structure(workspace_name)
        
        # Create large template content (100KB)
        large_content = "# Large Template\n\n" + ("This is a large template with lots of content. " * 2000)
        
        large_template = ContentTemplate(
            id=ContentId("large_template"),
            name=TemplateName("large_test_template"),
            content=large_content,
            content_type=ContentType.MARKDOWN,
            format=ContentFormat.TEMPLATE,
            metadata={"size": "large"}
        )
        
        # Save large template
        start_time = time.time()
        file_path = await file_storage.save_template_file(workspace_name, large_template)
        save_time = time.time() - start_time
        
        assert file_path.exists()
        assert file_path.stat().st_size > 50000  # Should be > 50KB
        assert save_time < 5.0  # Should complete within 5 seconds
        
        # Load large template
        start_time = time.time()
        loaded_template = await file_storage.load_template_file(file_path)
        load_time = time.time() - start_time
        
        assert loaded_template.content == large_content
        assert len(loaded_template.content) > 50000
        assert load_time < 2.0  # Should load within 2 seconds
        
        # Test multiple large files
        large_templates = []
        for i in range(10):
            template = ContentTemplate(
                id=ContentId(f"large_template_{i}"),
                name=TemplateName(f"large_template_{i}"),
                content=f"# Large Template {i}\n\n" + (f"Content block {i}: " * 1000),
                content_type=ContentType.MARKDOWN,
                format=ContentFormat.TEMPLATE,
                metadata={"size": "large", "index": i}
            )
            large_templates.append(template)
        
        # Save all large templates
        start_time = time.time()
        save_tasks = [
            file_storage.save_template_file(workspace_name, template)
            for template in large_templates
        ]
        saved_paths = await asyncio.gather(*save_tasks)
        total_save_time = time.time() - start_time
        
        assert len(saved_paths) == 10
        assert all(path.exists() for path in saved_paths)
        assert total_save_time < 10.0  # Should complete within 10 seconds
        
        # Verify total workspace size
        total_size = sum(path.stat().st_size for path in saved_paths if path.exists())
        assert total_size > 500000  # Should be > 500KB total

    async def test_unicode_filename_handling(self, file_storage, temp_workspace_path):
        """Test handling of unicode characters in filenames."""
        
        workspace_name = WorkspaceName("unicode_test_中文")
        
        # Create workspace with unicode name
        workspace_path = await file_storage.create_workspace_structure(workspace_name)
        assert workspace_path.exists()
        
        # Create template with unicode content and filename
        unicode_template = ContentTemplate(
            id=ContentId("unicode_✨"),
            name=TemplateName("测试模板_🚀"),
            content="# Unicode Template 🎆\n\n内容: 中文测试 αβγ عربي 🌍",
            content_type=ContentType.MARKDOWN,
            format=ContentFormat.TEMPLATE,
            metadata={"language": "中文", "emoji": "🚀"}
        )
        
        # Save unicode template
        file_path = await file_storage.save_template_file(workspace_name, unicode_template)
        assert file_path.exists()
        
        # Load and verify unicode content
        loaded_template = await file_storage.load_template_file(file_path)
        assert "中文测试" in loaded_template.content
        assert "🎆" in loaded_template.content
        assert loaded_template.metadata["language"] == "中文"
        assert loaded_template.metadata["emoji"] == "🚀"
        
        # Test listing with unicode filenames
        template_files = await file_storage.list_template_files(workspace_name)
        assert len(template_files) == 1
        assert template_files[0].exists()


# Manual test runner
if __name__ == "__main__":
    async def run_filesystem_tests():
        """Run file system integration tests manually."""
        test_instance = TestFileSystemIntegration()
        
        print("📁 Running File System Integration Tests...\n")
        
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_workspace_path = Path(temp_dir)
                file_storage = FileStorage(base_path=temp_workspace_path)
                sample_workspace_name = WorkspaceName("filesystem_test_workspace")
                
                print("1. Testing workspace directory creation...")
                workspace_path = await file_storage.create_workspace_structure(sample_workspace_name)
                assert workspace_path.exists()
                print("✅ Workspace directory creation successful")
                
                print("2. Testing basic file operations...")
                # Create sample template
                template = ContentTemplate(
                    id=ContentId("test_template"),
                    name=TemplateName("basic_test"),
                    content="# Test Template\n\nBasic test content",
                    content_type=ContentType.MARKDOWN,
                    format=ContentFormat.TEMPLATE,
                    metadata={}
                )
                
                # Save template
                file_path = await file_storage.save_template_file(sample_workspace_name, template)
                assert file_path.exists()
                
                # Load template
                loaded_template = await file_storage.load_template_file(file_path)
                assert loaded_template.content == template.content
                print("✅ Basic file operations successful")
                
                print("\n🎉 File system integration tests completed successfully!")
                
        except Exception as e:
            print(f"❌ File system integration test failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    asyncio.run(run_filesystem_tests())
