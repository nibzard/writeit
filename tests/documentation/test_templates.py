"""
Tests for documentation template system
"""

import pytest
from pathlib import Path
from writeit.docs.templates import DocumentationTemplateSystem, TemplateConfig, TemplateManager
from writeit.docs.models import (
    DocumentationSet,
    APIDocumentation,
    ModuleDocumentation,
    CLIDocumentation,
    UserGuide
)


class TestDocumentationTemplateSystem:
    """Test template system functionality"""
    
    def test_template_system_initialization(self, tmp_path):
        """Test template system initializes correctly"""
        templates_dir = tmp_path / "templates"
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        assert system is not None
        assert system.config == config
        assert system.env is not None
    
    def test_create_default_templates(self, tmp_path):
        """Test creating default templates"""
        templates_dir = tmp_path / "templates"
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        system.create_default_templates()
        
        # Check that template files were created
        assert (templates_dir / "main.md.j2").exists()
        assert (templates_dir / "api.md.j2").exists()
        assert (templates_dir / "modules.md.j2").exists()
        assert (templates_dir / "cli.md.j2").exists()
    
    def test_custom_filters(self, tmp_path):
        """Test custom template filters"""
        templates_dir = tmp_path / "templates"
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        # Test code block filter
        result = system._code_block_filter("print('hello')", "python")
        assert "```python" in result
        assert "print('hello')" in result
        assert "```" in result
        
        # Test sanitize filename filter
        result = system._sanitize_filename_filter("bad/file:name<>")
        assert "/" not in result
        assert ":" not in result
        assert "<" not in result
        assert ">" not in result
        
        # Test slugify filter
        result = system._slugify_filter("My Great Title!")
        assert result == "my-great-title"
    
    def test_render_with_template(self, tmp_path):
        """Test rendering with custom template"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create simple test template
        test_template = templates_dir / "test.md.j2"
        test_template.write_text("""# {{ docs.version }} Documentation

Generated at: {{ generated_at.strftime("%Y-%m-%d") }}

{% if docs.api_docs %}
API has {{ docs.api_docs.endpoints|length }} endpoints.
{% endif %}

{% if docs.module_docs %}
Modules: {{ docs.module_docs|length }}
{% endif %}""")
        
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        # Create test documentation
        from writeit.docs.models import APIEndpointDocumentation
        docs = DocumentationSet(
            version="1.0.0",
            api_docs=APIDocumentation(
                title="Test API",
                description="Test",
                version="1.0.0",
                base_url="http://localhost",
                endpoints=[
                    APIEndpointDocumentation(
                        path="/test",
                        method="GET",
                        summary="Test",
                        description="Test",
                        parameters=[],
                        status_codes={}
                    )
                ],
                models=[]
            ),
            module_docs=[
                ModuleDocumentation(
                    name="test",
                    description="Test",
                    purpose="Test",
                    classes=[],
                    functions=[]
                )
            ]
        )
        
        result = system.render_documentation(docs, "test.md.j2")
        
        assert "1.0.0 Documentation" in result
        assert "API has 1 endpoints" in result
        assert "Modules: 1" in result
    
    def test_fallback_rendering(self, tmp_path):
        """Test fallback rendering when template is missing"""
        templates_dir = tmp_path / "templates"
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        # Create minimal docs
        docs = DocumentationSet(version="1.0.0")
        
        # This should use fallback template
        result = system.render_documentation(docs, "nonexistent.md.j2")
        
        assert result is not None
        assert len(result) > 0
        assert "WriteIt" in result or "Documentation" in result
    
    def test_render_api_documentation(self, tmp_path):
        """Test rendering API documentation"""
        templates_dir = tmp_path / "templates"
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        from writeit.docs.models import APIEndpointDocumentation
        api_docs = APIDocumentation(
            title="Test API",
            description="Test API Description",
            version="1.0.0",
            base_url="http://localhost:8000",
            endpoints=[
                APIEndpointDocumentation(
                    path="/users",
                    method="GET",
                    summary="Get users",
                    description="Retrieve all users",
                    parameters=[],
                    status_codes={200: "Success", 404: "Not found"}
                )
            ],
            models=[]
        )
        
        result = system.render_api_documentation(api_docs)
        
        assert "Test API" in result
        assert "/users" in result
        assert "GET" in result
        assert "Retrieve all users" in result
    
    def test_render_user_guide(self, tmp_path):
        """Test rendering user guide"""
        templates_dir = tmp_path / "templates"
        config = TemplateConfig(templates_dir=templates_dir)
        system = DocumentationTemplateSystem(config)
        
        guide = UserGuide(
            title="Getting Started",
            description="A guide to getting started",
            content="This is the guide content...",
            audience="beginners",
            difficulty="easy",
            estimated_time="10 minutes",
            prerequisites=["Python installed"],
            related_guides=["Advanced Usage"]
        )
        
        result = system.render_user_guide(guide)
        
        assert "Getting Started" in result
        assert "beginners" in result
        assert "10 minutes" in result
        assert "Python installed" in result
        assert "This is the guide content" in result


class TestTemplateManager:
    """Test template manager functionality"""
    
    def test_template_manager_initialization(self, tmp_path):
        """Test template manager initializes"""
        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)
        
        assert manager.templates_dir == templates_dir
        assert templates_dir.exists()
    
    def test_create_template_structure(self, tmp_path):
        """Test creating template directory structure"""
        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)
        
        manager.create_template_structure()
        
        # Check subdirectories
        assert (templates_dir / "api").exists()
        assert (templates_dir / "modules").exists()
        assert (templates_dir / "cli").exists()
        assert (templates_dir / "templates").exists()
        assert (templates_dir / "guides").exists()
        
        # Check template files
        assert (templates_dir / "main.md.j2").exists()
        assert (templates_dir / "api.md.j2").exists()
    
    def test_list_templates(self, tmp_path):
        """Test listing templates"""
        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)
        
        # Create some test templates
        (templates_dir / "test1.j2").write_text("Test template 1")
        subdir = templates_dir / "subdir"
        subdir.mkdir()
        (subdir / "test2.j2").write_text("Test template 2")
        
        templates = manager.list_templates()
        
        assert len(templates) >= 2
        template_names = [t.name for t in templates]
        assert "test1.j2" in template_names
        assert "test2.j2" in template_names
    
    def test_validate_template(self, tmp_path):
        """Test template validation"""
        templates_dir = tmp_path / "templates"
        manager = TemplateManager(templates_dir)
        
        # Create valid template
        valid_template = templates_dir / "valid.j2"
        valid_template.write_text("# {{ title }}\n\n{{ content }}")
        
        # Create invalid template
        invalid_template = templates_dir / "invalid.j2"
        invalid_template.write_text("# {{ title }\n\n{{ unclosed")
        
        assert manager.validate_template(valid_template) is True
        assert manager.validate_template(invalid_template) is False