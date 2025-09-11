"""
Tests for documentation deployment
"""

import pytest
from pathlib import Path
import shutil
from writeit.docs.deployment import DocumentationDeployment
from writeit.docs.models import (
    DocumentationSet,
    APIDocumentation,
    ModuleDocumentation,
    CLIDocumentation,
    CommandDocumentation,
    ParameterDocumentation,
    APIEndpointDocumentation
)


class TestDocumentationDeployment:
    """Test documentation deployment functionality"""
    
    def test_deployment_initialization(self):
        """Test deployment initializes correctly"""
        deployment = DocumentationDeployment()
        assert deployment is not None
    
    def test_deployment_with_custom_templates(self, tmp_path):
        """Test deployment with custom templates directory"""
        templates_dir = tmp_path / "custom_templates"
        deployment = DocumentationDeployment(templates_dir=templates_dir)
        
        assert deployment.templates_dir == templates_dir
        assert deployment.template_system is not None
    
    def test_deploy_markdown_basic(self, tmp_path):
        """Test basic markdown deployment"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        # Create minimal documentation
        docs = DocumentationSet(version="1.0.0")
        
        deployment.deploy(docs, output_path, ["markdown"])
        
        # Check that files were created
        markdown_dir = output_path / "markdown"
        assert markdown_dir.exists()
        assert (markdown_dir / "README.md").exists()
    
    def test_deploy_api_documentation(self, tmp_path):
        """Test deploying API documentation"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        # Create API documentation
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
                    status_codes={200: "Success"}
                ),
                APIEndpointDocumentation(
                    path="/users/{id}",
                    method="GET",
                    summary="Get user by ID",
                    description="Retrieve a specific user",
                    parameters=[],
                    status_codes={200: "Success", 404: "Not found"}
                )
            ],
            models=[]
        )
        
        docs = DocumentationSet(api_docs=api_docs, version="1.0.0")
        
        deployment.deploy(docs, output_path, ["markdown"])
        
        # Check API documentation files
        api_dir = output_path / "markdown" / "api"
        assert api_dir.exists()
        assert (api_dir / "README.md").exists()
        
        endpoints_dir = api_dir / "endpoints"
        assert endpoints_dir.exists()
        
        # Check endpoint files were created
        endpoint_files = list(endpoints_dir.glob("*.md"))
        assert len(endpoint_files) >= 2  # Should have files for both endpoints
    
    def test_deploy_module_documentation(self, tmp_path):
        """Test deploying module documentation"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        from writeit.docs.models import ClassDocumentation, FunctionDocumentation
        
        # Create module documentation
        module_docs = [
            ModuleDocumentation(
                name="test.module",
                description="Test module description",
                purpose="Test module purpose",
                classes=[
                    ClassDocumentation(
                        name="TestClass",
                        description="Test class description",
                        purpose="Test class purpose",
                        methods=[]
                    )
                ],
                functions=[
                    FunctionDocumentation(
                        name="test_function",
                        signature="test_function() -> str",
                        description="Test function description",
                        parameters=[],
                        return_type="str",
                        return_description="Returns test string"
                    )
                ]
            )
        ]
        
        docs = DocumentationSet(module_docs=module_docs, version="1.0.0")
        
        deployment.deploy(docs, output_path, ["markdown"])
        
        # Check module documentation files
        modules_dir = output_path / "markdown" / "modules"
        assert modules_dir.exists()
        assert (modules_dir / "README.md").exists()
        
        # Check individual module file
        module_file = modules_dir / "test" / "module.md"
        assert module_file.exists()
        
        # Check content
        content = module_file.read_text()
        assert "test.module" in content
        assert "TestClass" in content
        assert "test_function" in content
    
    def test_deploy_cli_documentation(self, tmp_path):
        """Test deploying CLI documentation"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        # Create CLI documentation
        cli_docs = CLIDocumentation(
            app_name="test-cli",
            description="Test CLI application",
            commands=[
                CommandDocumentation(
                    name="test-command",
                    description="Test command description",
                    usage="test-cli test-command [options]",
                    arguments=[
                        ParameterDocumentation(
                            name="input",
                            type_annotation="str",
                            description="Input file",
                            required=True
                        )
                    ],
                    options=[
                        ParameterDocumentation(
                            name="verbose",
                            type_annotation="bool",
                            description="Enable verbose output",
                            required=False,
                            default_value="False"
                        )
                    ],
                    examples=["test-cli test-command input.txt --verbose"]
                )
            ]
        )
        
        docs = DocumentationSet(cli_docs=cli_docs, version="1.0.0")
        
        deployment.deploy(docs, output_path, ["markdown"])
        
        # Check CLI documentation files
        cli_dir = output_path / "markdown" / "cli"
        assert cli_dir.exists()
        assert (cli_dir / "README.md").exists()
        
        # Check content
        content = (cli_dir / "README.md").read_text()
        assert "test-command" in content
        assert "Input file" in content
        assert "Enable verbose output" in content
    
    def test_deploy_multiple_formats(self, tmp_path):
        """Test deploying to multiple formats"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        docs = DocumentationSet(version="1.0.0")
        
        # Deploy to both markdown and HTML
        deployment.deploy(docs, output_path, ["markdown", "html"])
        
        # Check that both formats were created
        assert (output_path / "markdown").exists()
        assert (output_path / "site").exists()
    
    def test_html_deployment_fallback(self, tmp_path):
        """Test HTML deployment when MkDocs is not available"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        docs = DocumentationSet(version="1.0.0")
        
        # This should work even without MkDocs installed
        deployment.deploy(docs, output_path, ["html"])
        
        # Should create the site directory and configuration
        site_dir = output_path / "site"
        assert site_dir.exists()
        assert (site_dir / "mkdocs.yml").exists()
    
    def test_sanitize_filenames(self, tmp_path):
        """Test filename sanitization for special characters"""
        output_path = tmp_path / "output"
        deployment = DocumentationDeployment()
        
        # Create API with special characters in path
        api_docs = APIDocumentation(
            title="Test API",
            description="Test",
            version="1.0.0",
            base_url="http://localhost",
            endpoints=[
                APIEndpointDocumentation(
                    path="/users/{user_id}/items/{item_id}",
                    method="GET",
                    summary="Get user item",
                    description="Get specific item for user",
                    parameters=[],
                    status_codes={200: "Success"}
                )
            ],
            models=[]
        )
        
        docs = DocumentationSet(api_docs=api_docs, version="1.0.0")
        
        deployment.deploy(docs, output_path, ["markdown"])
        
        # Check that files were created with sanitized names
        endpoints_dir = output_path / "markdown" / "api" / "endpoints"
        endpoint_files = list(endpoints_dir.glob("*.md"))
        assert len(endpoint_files) > 0
        
        # Filenames should not contain invalid characters
        for file in endpoint_files:
            assert "{" not in file.name
            assert "}" not in file.name
            assert "/" not in file.name
    
    def test_generate_sitemap(self, tmp_path):
        """Test sitemap generation"""
        deployment = DocumentationDeployment()
        
        from writeit.docs.models import ClassDocumentation
        
        docs = DocumentationSet(
            module_docs=[
                ModuleDocumentation(
                    name="test.module",
                    description="Test",
                    purpose="Test",
                    classes=[],
                    functions=[]
                )
            ],
            version="1.0.0"
        )
        
        sitemap = deployment.generate_sitemap(docs, "https://example.com/docs")
        
        assert "<?xml version=" in sitemap
        assert "<urlset" in sitemap
        assert "https://example.com/docs/" in sitemap
        assert "test/module.html" in sitemap
    
    def test_serve_local_preview_setup(self):
        """Test local preview server setup (without actually starting server)"""
        deployment = DocumentationDeployment()
        
        # This test just checks the method exists and is callable
        assert hasattr(deployment, 'serve_local_preview')
        assert callable(deployment.serve_local_preview)