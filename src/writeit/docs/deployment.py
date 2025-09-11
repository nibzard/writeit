"""
Documentation deployment system
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from .models import DocumentationSet
from .templates import DocumentationTemplateSystem, TemplateConfig
from .html_generator import HTMLDocumentationGenerator
from .pdf_generator import PDFDocumentationGenerator


class DocumentationDeployment:
    """Deploy documentation to multiple formats and platforms"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize deployment with optional custom templates"""
        self.templates_dir = templates_dir or Path("docs/templates")
        self.template_system = None
        self._initialize_template_system()
    
    def _initialize_template_system(self):
        """Initialize template system"""
        if self.templates_dir.exists():
            config = TemplateConfig(templates_dir=self.templates_dir)
            self.template_system = DocumentationTemplateSystem(config)
        else:
            # Create default templates
            config = TemplateConfig(templates_dir=self.templates_dir)
            self.template_system = DocumentationTemplateSystem(config)
            self.template_system.create_default_templates()
    
    def deploy(self, docs: DocumentationSet, output_path: Path, formats: List[str]):
        """Deploy documentation to specified formats"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        for format_type in formats:
            if format_type == "markdown":
                self._deploy_markdown_with_templates(docs, output_path / "markdown")
            elif format_type == "html":
                self._deploy_html_enhanced(docs, output_path / "site")
            elif format_type == "pdf":
                self._deploy_pdf_enhanced(docs, output_path / "writeit-documentation.pdf", output_path)
            else:
                print(f"Unknown format: {format_type}")
    
    def _deploy_markdown_with_templates(self, docs: DocumentationSet, output_path: Path):
        """Deploy documentation as Markdown files using templates"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.template_system:
            # Use template system for enhanced output
            self._deploy_with_template_system(docs, output_path)
        else:
            # Fallback to original deployment
            self._deploy_markdown_fallback(docs, output_path)
        
        print(f"✅ Markdown documentation deployed to {output_path}")
    
    def _deploy_with_template_system(self, docs: DocumentationSet, output_path: Path):
        """Deploy using Jinja2 template system"""
        # Main documentation file
        try:
            main_content = self.template_system.render_documentation(docs)
            with open(output_path / "README.md", 'w') as f:
                f.write(main_content)
        except Exception as e:
            print(f"Warning: Could not render main template: {e}")
            self._write_index_markdown(docs, output_path)
        
        # API documentation
        if docs.api_docs:
            try:
                api_content = self.template_system.render_api_documentation(docs.api_docs)
                api_dir = output_path / "api"
                api_dir.mkdir(exist_ok=True)
                with open(api_dir / "README.md", 'w') as f:
                    f.write(api_content)
                
                # Individual endpoint files
                self._write_api_markdown(docs.api_docs, output_path)
            except Exception as e:
                print(f"Warning: Could not render API template: {e}")
                self._write_api_markdown(docs.api_docs, output_path)
        
        # Module documentation
        if docs.module_docs:
            try:
                modules_content = self.template_system.render_module_documentation(docs.module_docs)
                modules_dir = output_path / "modules"
                modules_dir.mkdir(exist_ok=True)
                with open(modules_dir / "README.md", 'w') as f:
                    f.write(modules_content)
                
                # Individual module files
                self._write_module_markdown(docs.module_docs, output_path)
            except Exception as e:
                print(f"Warning: Could not render modules template: {e}")
                self._write_module_markdown(docs.module_docs, output_path)
        
        # CLI documentation
        if docs.cli_docs:
            try:
                cli_content = self.template_system.render_cli_documentation(docs.cli_docs)
                cli_dir = output_path / "cli"
                cli_dir.mkdir(exist_ok=True)
                with open(cli_dir / "README.md", 'w') as f:
                    f.write(cli_content)
            except Exception as e:
                print(f"Warning: Could not render CLI template: {e}")
                self._write_cli_markdown(docs.cli_docs, output_path)
        
        # Template documentation
        if docs.template_docs:
            self._write_template_markdown(docs.template_docs, output_path)
        
        # User guides
        if docs.user_guides:
            guides_dir = output_path / "guides"
            guides_dir.mkdir(exist_ok=True)
            
            # Index file
            guides_index = "# User Guides\n\n"
            for guide in docs.user_guides:
                guides_index += f"- [{guide.title}]({guide.title.replace(' ', '-').lower()}.md)\n"
            
            with open(guides_dir / "README.md", 'w') as f:
                f.write(guides_index)
            
            # Individual guide files
            for guide in docs.user_guides:
                try:
                    guide_content = self.template_system.render_user_guide(guide)
                    filename = guide.title.replace(' ', '-').lower() + ".md"
                    with open(guides_dir / filename, 'w') as f:
                        f.write(guide_content)
                except Exception as e:
                    print(f"Warning: Could not render guide template: {e}")
    
    def _deploy_markdown_fallback(self, docs: DocumentationSet, output_path: Path):
        """Fallback markdown deployment without templates"""
        # API documentation
        if docs.api_docs:
            self._write_api_markdown(docs.api_docs, output_path)
        
        # Module documentation
        if docs.module_docs:
            self._write_module_markdown(docs.module_docs, output_path)
        
        # CLI documentation
        if docs.cli_docs:
            self._write_cli_markdown(docs.cli_docs, output_path)
        
        # Template documentation
        if docs.template_docs:
            self._write_template_markdown(docs.template_docs, output_path)
        
        # User guides
        if docs.user_guides:
            self._write_guides_markdown(docs.user_guides, output_path)
        
        # Index file
        self._write_index_markdown(docs, output_path)
    
    def _write_api_markdown(self, api_docs, output_path: Path):
        """Write API documentation as Markdown"""
        api_dir = output_path / "api"
        api_dir.mkdir(exist_ok=True)
        
        # API overview
        overview_content = f"""# API Documentation

{api_docs.description}

## Base URL
{api_docs.base_url}

## Version
{api_docs.version}

## Endpoints

"""
        
        for endpoint in api_docs.endpoints:
            filename = f"{endpoint.method.lower()}{endpoint.path.replace('/', '_').replace('{', '_').replace('}', '_')}.md"
            overview_content += f"- [{endpoint.method} {endpoint.path}](endpoints/{filename})\n"
        
        with open(api_dir / "README.md", 'w') as f:
            f.write(overview_content)
        
        # Individual endpoint files
        endpoints_dir = api_dir / "endpoints"
        endpoints_dir.mkdir(exist_ok=True)
        
        for endpoint in api_docs.endpoints:
            filename = f"{endpoint.method.lower()}{endpoint.path.replace('/', '_').replace('{', '_').replace('}', '_')}.md"
            content = self._generate_endpoint_markdown(endpoint)
            
            with open(endpoints_dir / filename, 'w') as f:
                f.write(content)
    
    def _generate_endpoint_markdown(self, endpoint) -> str:
        """Generate Markdown for a single endpoint"""
        content = f"""# {endpoint.method} {endpoint.path}

{endpoint.description}

## Parameters
"""
        
        if endpoint.parameters:
            for param in endpoint.parameters:
                required = "Required" if param.required else "Optional"
                content += f"- **{param.name}** ({param.type_annotation}): {param.description} [{required}]\n"
        else:
            content += "No parameters\n"
        
        if endpoint.request_body:
            content += f"\n## Request Body\n{endpoint.request_body}\n"
        
        if endpoint.status_codes:
            content += "\n## Status Codes\n"
            for code, description in endpoint.status_codes.items():
                content += f"- **{code}**: {description}\n"
        
        if endpoint.examples:
            content += "\n## Examples\n"
            for example in endpoint.examples:
                content += f"### {example.description}\n\n```{example.language}\n{example.code}\n```\n\n"
        
        return content
    
    def _write_module_markdown(self, module_docs: List, output_path: Path):
        """Write module documentation as Markdown"""
        modules_dir = output_path / "modules"
        modules_dir.mkdir(exist_ok=True)
        
        # Modules overview
        overview_content = "# Module Documentation\n\n"
        for module in module_docs:
            overview_content += f"- [{module.name}]({module.name.replace('.', '/')}.md)\n"
        
        with open(modules_dir / "README.md", 'w') as f:
            f.write(overview_content)
        
        # Individual module files
        for module in module_docs:
            module_path = modules_dir / (module.name.replace('.', '/') + ".md")
            module_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = self._generate_module_markdown(module)
            with open(module_path, 'w') as f:
                f.write(content)
    
    def _generate_module_markdown(self, module) -> str:
        """Generate Markdown for a single module"""
        content = f"""# {module.name}

{module.description}

## Purpose
{module.purpose}

"""
        
        if module.dependencies:
            content += "## Dependencies\n"
            for dep in module.dependencies:
                content += f"- {dep}\n"
            content += "\n"
        
        if module.classes:
            content += "## Classes\n"
            for class_doc in module.classes:
                content += f"### {class_doc.name}\n\n{class_doc.description}\n\n"
                
                if class_doc.methods:
                    content += "#### Methods\n"
                    for method in class_doc.methods:
                        content += f"- **{method.name}**{method.signature}\n  {method.description}\n"
                content += "\n"
        
        if module.functions:
            content += "## Functions\n"
            for func_doc in module.functions:
                content += f"### {func_doc.name}\n\n{func_doc.signature}\n\n{func_doc.description}\n\n"
        
        return content
    
    def _write_cli_markdown(self, cli_docs, output_path: Path):
        """Write CLI documentation as Markdown"""
        cli_dir = output_path / "cli"
        cli_dir.mkdir(exist_ok=True)
        
        content = f"""# CLI Documentation

{cli_docs.description}

## Commands

"""
        
        for command in cli_docs.commands:
            content += f"### {command.name}\n\n"
            content += f"**Description**: {command.description}\n\n"
            content += f"**Usage**: `{command.usage}`\n\n"
            
            if command.arguments:
                content += "**Arguments**:\n"
                for arg in command.arguments:
                    required = "Required" if arg.required else "Optional"
                    content += f"- `{arg.name}` ({arg.type_annotation}): {arg.description} [{required}]\n"
                content += "\n"
            
            if command.examples:
                content += "**Examples**:\n"
                for example in command.examples:
                    content += f"```bash\n{example}\n```\n"
                content += "\n"
        
        with open(cli_dir / "README.md", 'w') as f:
            f.write(content)
    
    def _write_template_markdown(self, template_docs, output_path: Path):
        """Write template documentation as Markdown"""
        templates_dir = output_path / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        content = "# Pipeline Templates\n\n"
        
        if template_docs.templates:
            content += "## Pipeline Templates\n\n"
            for template in template_docs.templates:
                content += f"### {template.name}\n\n"
                content += f"{template.description}\n\n"
                
                if template.inputs:
                    content += "**Inputs**:\n"
                    for input_field in template.inputs:
                        required = "Required" if input_field.required else "Optional"
                        content += f"- **{input_field.name}** ({input_field.type}): {input_field.description} [{required}]\n"
                    content += "\n"
                
                if template.steps:
                    content += "**Steps**:\n"
                    for step in template.steps:
                        content += f"- **{step.name}** ({step.type}): {step.description}\n"
                    content += "\n"
        
        if template_docs.style_primers:
            content += "## Style Primers\n\n"
            for style in template_docs.style_primers:
                content += f"### {style.name}\n\n"
                content += f"{style.description}\n\n"
        
        with open(templates_dir / "README.md", 'w') as f:
            f.write(content)
    
    def _write_guides_markdown(self, user_guides: List, output_path: Path):
        """Write user guides as Markdown"""
        guides_dir = output_path / "guides"
        guides_dir.mkdir(exist_ok=True)
        
        # Guides overview
        overview_content = "# User Guides\n\n"
        for guide in user_guides:
            overview_content += f"- [{guide.title}]({guide.title.replace(' ', '-').lower()}.md) - {guide.description}\n"
        
        with open(guides_dir / "README.md", 'w') as f:
            f.write(overview_content)
        
        # Individual guide files
        for guide in user_guides:
            filename = guide.title.replace(' ', '-').lower() + ".md"
            content = f"""# {guide.title}

{guide.description}

**Audience**: {guide.audience}  
**Difficulty**: {guide.difficulty}  
**Estimated Time**: {guide.estimated_time}

## Prerequisites
"""
            
            if guide.prerequisites:
                for prereq in guide.prerequisites:
                    content += f"- {prereq}\n"
            else:
                content += "None\n"
            
            content += "\n" + guide.content + "\n"
            
            if guide.related_guides:
                content += "\n## Related Guides\n"
                for related in guide.related_guides:
                    content += f"- {related}\n"
            
            with open(guides_dir / filename, 'w') as f:
                f.write(content)
    
    def _write_index_markdown(self, docs: DocumentationSet, output_path: Path):
        """Write main index file"""
        content = f"""# WriteIt Documentation

Welcome to WriteIt's auto-generated documentation. This documentation is generated directly from the source code to ensure it stays up-to-date.

## Quick Links

- [API Documentation](api/README.md)
- [Module Documentation](modules/README.md)
- [CLI Documentation](cli/README.md)
- [Pipeline Templates](templates/README.md)
- [User Guides](guides/README.md)

## Generated Information

This documentation was automatically generated on {docs.generated_at} from WriteIt version {docs.version}.

## Documentation Coverage

- **API Endpoints**: {len(docs.api_docs.endpoints) if docs.api_docs else 0} documented
- **Modules**: {len(docs.module_docs)} documented
- **CLI Commands**: {len(docs.cli_docs.commands) if docs.cli_docs else 0} documented
- **User Guides**: {len(docs.user_guides)} available

## Getting Help

If you need help with WriteIt:

1. Check the [User Guides](guides/README.md) for comprehensive tutorials
2. Use the CLI help: `writeit --help`
3. Validate your setup: `writeit docs validate`
4. Generate this documentation: `writeit docs generate`

---

*This documentation is automatically generated. Please report any issues or inconsistencies.*
"""
        
        with open(output_path / "README.md", 'w') as f:
            f.write(content)
    
    def _deploy_html_enhanced(self, docs: DocumentationSet, output_path: Path):
        """Deploy documentation as enhanced HTML using new generator"""
        try:
            # First deploy markdown with templates
            markdown_path = output_path.parent / "markdown"
            self._deploy_markdown_with_templates(docs, markdown_path)
            
            # Use enhanced HTML generator
            html_generator = HTMLDocumentationGenerator(self.templates_dir)
            html_generator.deploy_html(docs, output_path, markdown_path)
            
        except Exception as e:
            print(f"❌ Error deploying enhanced HTML documentation: {e}")
            # Fallback to original method
            self._deploy_html_fallback(docs, output_path)
    
    def _deploy_html_fallback(self, docs: DocumentationSet, output_path: Path):
        """Fallback HTML deployment using MkDocs"""
        try:
            # First deploy markdown
            markdown_path = output_path.parent / "markdown"
            self._deploy_markdown(docs, markdown_path)
            
            # Create MkDocs configuration
            mkdocs_config = {
                "site_name": "WriteIt Documentation",
                "site_description": "Auto-generated documentation for WriteIt",
                "site_author": "WriteIt Team",
                "repo_url": "https://github.com/nibzard/writeit",
                "nav": [
                    {"Home": "index.md"},
                    {"API Documentation": "api/README.md"},
                    {"Module Documentation": "modules/README.md"},
                    {"CLI Documentation": "cli/README.md"},
                    {"Pipeline Templates": "templates/README.md"},
                    {"User Guides": "guides/README.md"}
                ],
                "theme": {
                    "name": "material",
                    "features": ["navigation.tabs", "navigation.sections", "search.suggest"]
                },
                "markdown_extensions": [
                    "codehilite",
                    "fenced_code",
                    "tables"
                ]
            }
            
            # Write MkDocs config
            import yaml
            mkdocs_file = output_path / "mkdocs.yml"
            with open(mkdocs_file, 'w') as f:
                yaml.dump(mkdocs_config, f, default_flow_style=False)
            
            # Copy markdown files to docs directory
            docs_dir = output_path / "docs"
            if markdown_path.exists():
                if docs_dir.exists():
                    shutil.rmtree(docs_dir)
                shutil.copytree(markdown_path, docs_dir)
            
            # Update MkDocs navigation based on actual content
            if docs.api_docs:
                mkdocs_config["nav"].append({"API Reference": "api/README.md"})
            if docs.module_docs:
                mkdocs_config["nav"].append({"Modules": "modules/README.md"})
            if docs.cli_docs:
                mkdocs_config["nav"].append({"CLI": "cli/README.md"})
            if docs.template_docs:
                mkdocs_config["nav"].append({"Templates": "templates/README.md"})
            if docs.user_guides:
                mkdocs_config["nav"].append({"Guides": "guides/README.md"})
            
            # Create index.md from README.md
            index_file = docs_dir / "index.md" if 'docs_dir' in locals() else output_path / "index.md"
            readme_file = docs_dir / "README.md" if 'docs_dir' in locals() else output_path / "README.md"
            if readme_file.exists() and not index_file.exists():
                shutil.copy2(readme_file, index_file)
            
            # Try to build with MkDocs if available
            try:
                result = subprocess.run(
                    ["mkdocs", "build", "--site-dir", "site"], 
                    cwd=output_path, 
                    check=True, 
                    capture_output=True,
                    text=True
                )
                print(f"✅ HTML documentation built with MkDocs at {output_path}/site")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  MkDocs build failed: {e.stderr}")
                print(f"   Markdown files available at {docs_dir}")
            except FileNotFoundError:
                print(f"⚠️  MkDocs not available, markdown files deployed to {docs_dir}")
                print("   Install with: pip install mkdocs mkdocs-material")
        
        except Exception as e:
            print(f"❌ Error deploying HTML documentation: {e}")
    
    def _deploy_pdf_enhanced(self, docs: DocumentationSet, output_path: Path, base_output_path: Path):
        """Deploy documentation as PDF using enhanced generator"""
        try:
            pdf_generator = PDFDocumentationGenerator()
            
            # Try to use existing HTML if available
            html_path = base_output_path / "site"
            if not html_path.exists():
                html_path = base_output_path / "html" / "site"
            
            success = pdf_generator.generate_pdf(docs, output_path, html_path if html_path.exists() else None)
            
            if success:
                print(f"✅ PDF documentation generated: {output_path}")
            else:
                print("⚠️  PDF generation failed, trying fallback methods...")
                self._deploy_pdf_fallback(docs, output_path)
            
        except Exception as e:
            print(f"❌ Error deploying PDF documentation: {e}")
            self._deploy_pdf_fallback(docs, output_path)
    
    def _deploy_pdf_fallback(self, docs: DocumentationSet, output_path: Path):
        """Fallback PDF deployment"""
        try:
            # Create simple text-based PDF
            content = f"""WriteIt Documentation

Generated: {docs.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
Version: {docs.version}

API Endpoints: {len(docs.api_docs.endpoints) if docs.api_docs else 0}
Modules: {len(docs.module_docs)}
CLI Commands: {len(docs.cli_docs.commands) if docs.cli_docs else 0}
User Guides: {len(docs.user_guides)}

This is a simplified PDF version. For full documentation, please use the HTML version.
"""
            
            # Write as text file if PDF generation completely fails
            text_output = output_path.with_suffix('.txt')
            with open(text_output, 'w') as f:
                f.write(content)
            
            print(f"⚠️  Created simplified text documentation: {text_output}")
            print("   For PDF support, install: pip install weasyprint reportlab")
            
        except Exception as e:
            print(f"❌ Complete PDF deployment failure: {e}")
    
    def deploy_to_github_pages(self, site_path: Path):
        """Deploy documentation to GitHub Pages"""
        try:
            # Check if git repository
            if not (site_path.parent / ".git").exists():
                print("⚠️  Not a git repository, cannot deploy to GitHub Pages")
                return
            
            # Try to use gh-pages CLI if available
            try:
                subprocess.run([
                    "gh-pages", 
                    "--dist", str(site_path),
                    "--dotfiles"
                ], check=True, capture_output=True)
                print("✅ Deployed to GitHub Pages using gh-pages")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  gh-pages CLI not available")
                print("   Install with: npm install -g gh-pages")
        
        except Exception as e:
            print(f"❌ Error deploying to GitHub Pages: {e}")
    
    def serve_local_preview(self, docs_path: Path, host: str = "127.0.0.1", port: int = 8000):
        """Start local preview server"""
        try:
            # Try Python's built-in HTTP server
            import http.server
            import socketserver
            
            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=str(docs_path), **kwargs)
            
            with socketserver.TCPServer((host, port), Handler) as httpd:
                print(f"🚀 Preview server started at http://{host}:{port}")
                print("Press Ctrl+C to stop the server")
                httpd.serve_forever()
        
        except KeyboardInterrupt:
            print("\n🛑 Preview server stopped")
        except Exception as e:
            print(f"❌ Error starting preview server: {e}")
    
    def _deploy_pdf(self, docs: DocumentationSet, output_path: Path):
        """Legacy PDF deployment method"""
        return self._deploy_pdf_fallback(docs, output_path)
    
    def generate_sitemap(self, docs: DocumentationSet, base_url: str) -> str:
        """Generate sitemap for documentation"""
        urls = []
        
        # Add main pages
        urls.append(f"{base_url}/")
        urls.append(f"{base_url}/api/")
        urls.append(f"{base_url}/modules/")
        urls.append(f"{base_url}/cli/")
        urls.append(f"{base_url}/templates/")
        urls.append(f"{base_url}/guides/")
        
        # Add specific pages
        if docs.module_docs:
            for module in docs.module_docs:
                urls.append(f"{base_url}/modules/{module.name.replace('.', '/')}.html")
        
        # Generate sitemap XML
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for url in urls:
            sitemap += f'  <url>\n    <loc>{url}</loc>\n    <priority>0.8</priority>\n  </url>\n'
        
        sitemap += '</urlset>\n'
        return sitemap