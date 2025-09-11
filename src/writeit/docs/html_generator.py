"""
Enhanced HTML documentation generator with MkDocs
"""

import shutil
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import DocumentationSet


class HTMLDocumentationGenerator:
    """Generate enhanced HTML documentation with MkDocs"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path("docs/templates")
    
    def deploy_html(self, docs: DocumentationSet, output_path: Path, markdown_path: Path):
        """Deploy documentation as enhanced HTML using MkDocs"""
        try:
            # Create enhanced MkDocs configuration
            mkdocs_config = self._create_mkdocs_config(docs)
            
            # Setup MkDocs project structure
            self._setup_mkdocs_project(docs, output_path, markdown_path, mkdocs_config)
            
        except Exception as e:
            print(f"❌ Error deploying HTML documentation: {e}")
    
    def _create_mkdocs_config(self, docs: DocumentationSet) -> Dict[str, Any]:
        """Create comprehensive MkDocs configuration"""
        config = {
            "site_name": docs.api_docs.title if docs.api_docs else "WriteIt Documentation",
            "site_description": "Auto-generated documentation for WriteIt",
            "site_author": "WriteIt Team",
            "repo_url": "https://github.com/nibzard/writeit",
            "edit_uri": "edit/main/docs/",
            "copyright": "Copyright © 2025 WriteIt Team",
            "nav": [{"Home": "index.md"}],
            "theme": {
                "name": "material",
                "palette": [
                    {
                        "scheme": "default",
                        "primary": "blue",
                        "accent": "light-blue",
                        "toggle": {
                            "icon": "material/brightness-7",
                            "name": "Switch to dark mode"
                        }
                    },
                    {
                        "scheme": "slate",
                        "primary": "blue",
                        "accent": "light-blue",
                        "toggle": {
                            "icon": "material/brightness-4",
                            "name": "Switch to light mode"
                        }
                    }
                ],
                "features": [
                    "navigation.tabs",
                    "navigation.sections",
                    "navigation.expand",
                    "navigation.path",
                    "navigation.top",
                    "search.suggest",
                    "search.highlight",
                    "search.share",
                    "content.code.copy",
                    "content.code.select",
                    "content.tabs.link"
                ],
                "icon": {
                    "repo": "fontawesome/brands/github"
                }
            },
            "markdown_extensions": [
                "abbr",
                "admonition",
                "attr_list",
                "def_list",
                "footnotes",
                "md_in_html",
                "toc",
                "tables",
                "pymdownx.arithmatex",
                "pymdownx.betterem",
                "pymdownx.caret",
                "pymdownx.details",
                "pymdownx.emoji",
                "pymdownx.highlight",
                "pymdownx.inlinehilite",
                "pymdownx.keys",
                "pymdownx.mark",
                "pymdownx.smartsymbols",
                "pymdownx.superfences",
                "pymdownx.tabbed",
                "pymdownx.tasklist",
                "pymdownx.tilde"
            ],
            "plugins": [
                "search"
            ],
            "extra": {
                "social": [
                    {
                        "icon": "fontawesome/brands/github",
                        "link": "https://github.com/nibzard/writeit"
                    }
                ],
                "generator": False
            },
            "extra_css": ["stylesheets/extra.css"],
            "watch": ["docs/"]
        }
        
        # Build navigation based on available content
        self._build_navigation(config, docs)
        
        return config
    
    def _build_navigation(self, config: Dict[str, Any], docs: DocumentationSet):
        """Build navigation structure based on available documentation"""
        nav = config["nav"]
        
        if docs.api_docs:
            nav.append({"API Reference": "api/README.md"})
        
        if docs.module_docs:
            nav.append({"Modules": "modules/README.md"})
        
        if docs.cli_docs:
            nav.append({"CLI Reference": "cli/README.md"})
        
        if docs.template_docs and docs.template_docs.templates:
            nav.append({"Templates": "templates/README.md"})
        
        if docs.user_guides:
            nav.append({"User Guides": "guides/README.md"})
    
    def _setup_mkdocs_project(self, docs: DocumentationSet, output_path: Path, markdown_path: Path, config: Dict[str, Any]):
        """Setup complete MkDocs project structure"""
        # Create docs directory
        docs_dir = output_path / "docs"
        if markdown_path.exists():
            if docs_dir.exists():
                shutil.rmtree(docs_dir)
            shutil.copytree(markdown_path, docs_dir)
        
        # Create index.md from README.md
        readme_file = docs_dir / "README.md"
        index_file = docs_dir / "index.md"
        if readme_file.exists() and not index_file.exists():
            shutil.copy2(readme_file, index_file)
        
        # Create custom CSS
        self._create_custom_css(docs_dir)
        
        # Create additional assets
        self._create_additional_assets(docs_dir, docs)
        
        # Write MkDocs configuration
        import yaml
        mkdocs_file = output_path / "mkdocs.yml"
        with open(mkdocs_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Try to build with MkDocs
        self._build_with_mkdocs(output_path)
    
    def _create_custom_css(self, docs_dir: Path):
        """Create custom CSS for enhanced styling"""
        stylesheets_dir = docs_dir / "stylesheets"
        stylesheets_dir.mkdir(exist_ok=True)
        
        css_content = """/* Custom WriteIt Documentation Styles */

/* Code blocks */
.highlight {
    border-radius: 4px;
    margin: 1em 0;
}

.highlight pre {
    padding: 1em;
    overflow-x: auto;
}

/* API endpoints */
.api-endpoint {
    border: 1px solid var(--md-default-fg-color--lighter);
    border-radius: 4px;
    margin: 1em 0;
    padding: 1em;
}

.api-method {
    display: inline-block;
    padding: 0.2em 0.5em;
    border-radius: 3px;
    font-weight: bold;
    font-size: 0.8em;
    margin-right: 0.5em;
}

.api-method.get { background-color: #61affe; color: white; }
.api-method.post { background-color: #49cc90; color: white; }
.api-method.put { background-color: #fca130; color: white; }
.api-method.delete { background-color: #f93e3e; color: white; }
.api-method.patch { background-color: #50e3c2; color: white; }

/* Documentation badges */
.doc-badge {
    display: inline-block;
    padding: 0.2em 0.6em;
    font-size: 0.75em;
    font-weight: bold;
    border-radius: 10px;
    margin: 0.2em;
}

.doc-badge.required { background-color: #f93e3e; color: white; }
.doc-badge.optional { background-color: #61affe; color: white; }
.doc-badge.deprecated { background-color: #fca130; color: white; }

/* Function signatures */
.function-signature {
    background-color: var(--md-code-bg-color);
    padding: 0.5em;
    border-radius: 4px;
    font-family: var(--md-code-font);
    overflow-x: auto;
}

/* Generated timestamp */
.generated-info {
    font-size: 0.8em;
    color: var(--md-default-fg-color--light);
    text-align: center;
    margin-top: 2em;
    padding-top: 1em;
    border-top: 1px solid var(--md-default-fg-color--lightest);
}

/* Responsive improvements */
@media screen and (max-width: 768px) {
    .function-signature {
        font-size: 0.8em;
    }
    
    .api-endpoint {
        padding: 0.5em;
    }
}
"""
        
        with open(stylesheets_dir / "extra.css", 'w') as f:
            f.write(css_content)
    
    def _create_additional_assets(self, docs_dir: Path, docs: DocumentationSet):
        """Create additional assets and pages"""
        # Create 404 page
        not_found_file = docs_dir / "404.md"
        if not not_found_file.exists():
            content = """# Page Not Found

Sorry, the page you are looking for doesn't exist.

## Quick Links

- [Home](index.md)
- [API Documentation](api/README.md)
- [CLI Reference](cli/README.md)
- [User Guides](guides/README.md)

## Search

Use the search functionality above to find what you're looking for.
"""
            
            with open(not_found_file, 'w') as f:
                f.write(content)
    
    def _build_with_mkdocs(self, output_path: Path):
        """Build documentation with MkDocs"""
        try:
            result = subprocess.run(
                ["mkdocs", "build", "--site-dir", "site", "--clean"], 
                cwd=output_path, 
                check=True, 
                capture_output=True,
                text=True
            )
            print(f"✅ HTML documentation built with MkDocs at {output_path}/site")
            
            # Create additional enhancements
            self._enhance_built_site(output_path / "site")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  MkDocs build failed: {e.stderr}")
            print(f"   Markdown files available at {output_path}/docs")
        except FileNotFoundError:
            print(f"⚠️  MkDocs not available, markdown files deployed to {output_path}/docs")
            print("   Install with: pip install mkdocs mkdocs-material")
    
    def _enhance_built_site(self, site_path: Path):
        """Enhance the built MkDocs site"""
        if not site_path.exists():
            return
        
        # Add robots.txt
        robots_file = site_path / "robots.txt"
        with open(robots_file, 'w') as f:
            f.write("User-agent: *\nAllow: /\n")
        
        # Add manifest for PWA support
        manifest_file = site_path / "manifest.json"
        manifest_content = {
            "name": "WriteIt Documentation",
            "short_name": "WriteIt Docs",
            "description": "Auto-generated documentation for WriteIt",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#2196f3",
            "icons": []
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest_content, f, indent=2)