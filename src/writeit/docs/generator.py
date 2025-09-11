"""
Main documentation generator orchestrator
"""

import importlib
import inspect
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .models import (
    DocumentationSet, 
    ModuleDocumentation,
    APIDocumentation,
    CLIDocumentation, 
    TemplateDocumentationSet,
    UserGuide,
    DocumentationConfig,
    DocumentationMetrics,
    ClassDocumentation
)
from .extractors import (
    ModuleExtractor,
    APIExtractor,
    CLIExtractor,
    TemplateExtractor,
    ExampleExtractor
)
from .generators import UserGuideGenerator


@dataclass
class ExtractorRegistry:
    """Registry for documentation extractors"""
    module_extractor: ModuleExtractor
    api_extractor: APIExtractor
    cli_extractor: CLIExtractor
    template_extractor: TemplateExtractor
    example_extractor: ExampleExtractor


class DocumentationGenerator:
    """Main documentation generator orchestrator"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.extractors = self._init_extractors()
        self.metrics = DocumentationMetrics()
        self.generation_start_time = None
        
    def _load_config(self, config_path: Optional[Path]) -> DocumentationConfig:
        """Load documentation configuration"""
        if config_path and config_path.exists():
            return DocumentationConfig.from_file(config_path)
        return DocumentationConfig()
    
    def _init_extractors(self) -> ExtractorRegistry:
        """Initialize all documentation extractors"""
        return ExtractorRegistry(
            module_extractor=ModuleExtractor(),
            api_extractor=APIExtractor(),
            cli_extractor=CLIExtractor(),
            template_extractor=TemplateExtractor(),
            example_extractor=ExampleExtractor()
        )
    
    def generate_all(self) -> DocumentationSet:
        """Generate complete documentation set"""
        import time
        self.generation_start_time = time.time()
        
        docs = DocumentationSet()
        
        # Generate API documentation
        if self._should_generate_api_docs():
            docs.api_docs = self._generate_api_docs()
        
        # Generate module documentation
        if self._should_generate_module_docs():
            docs.module_docs = self._generate_module_docs()
        
        # Generate CLI documentation
        if self._should_generate_cli_docs():
            docs.cli_docs = self._generate_cli_docs()
        
        # Generate template documentation
        if self._should_generate_template_docs():
            docs.template_docs = self._generate_template_docs()
        
        # Generate user guides
        if self._should_generate_user_guides():
            docs.user_guides = self._generate_user_guides()
        
        # Calculate generation time
        if self.generation_start_time:
            self.metrics.generation_time = time.time() - self.generation_start_time
        
        return docs
    
    def _should_generate_api_docs(self) -> bool:
        """Check if API documentation should be generated"""
        return "api" in self.config.sources
    
    def _should_generate_module_docs(self) -> bool:
        """Check if module documentation should be generated"""
        return "modules" in self.config.sources
    
    def _should_generate_cli_docs(self) -> bool:
        """Check if CLI documentation should be generated"""
        return "cli" in self.config.sources
    
    def _should_generate_template_docs(self) -> bool:
        """Check if template documentation should be generated"""
        return "templates" in self.config.sources
    
    def _should_generate_user_guides(self) -> bool:
        """Check if user guides should be generated"""
        return "user_guides" in self.config.sources
    
    def _generate_api_docs(self) -> Optional[APIDocumentation]:
        """Generate API documentation"""
        try:
            # Try to import FastAPI app
            from writeit.server.app import app
            return self.extractors.api_extractor.extract_api_docs(app)
        except ImportError:
            # Try to generate from OpenAPI spec file
            api_config = self.config.sources.get("api", {})
            spec_path = api_config.get("spec_path", "openapi.json")
            if Path(spec_path).exists():
                return self.extractors.api_extractor.extract_from_openapi_file(Path(spec_path))
        except Exception as e:
            print(f"Warning: Could not generate API documentation: {e}")
        return None
    
    def _generate_module_docs(self) -> List[ModuleDocumentation]:
        """Generate module documentation from source code"""
        modules_config = self.config.sources.get("modules", {})
        base_path = Path(modules_config.get("path", "src/writeit"))
        patterns = modules_config.get("patterns", ["**/*.py"])
        exclude = modules_config.get("exclude", ["**/__pycache__/**", "**/tests/**"])
        
        module_docs = []
        
        for pattern in patterns:
            for py_file in base_path.rglob(pattern):
                if any(py_file.match(excl) for excl in exclude):
                    continue
                
                try:
                    module_doc = self.extractors.module_extractor.extract_module(py_file)
                    if module_doc:
                        module_docs.append(module_doc)
                        self._update_module_metrics(module_doc)
                except Exception as e:
                    print(f"Warning: Could not extract docs from {py_file}: {e}")
        
        return module_docs
    
    def _generate_cli_docs(self) -> Optional[CLIDocumentation]:
        """Generate CLI documentation"""
        try:
            # Try to import Typer app
            from writeit.cli.main import app
            return self.extractors.cli_extractor.extract_cli_docs(app)
        except ImportError:
            print("Warning: Could not import CLI app for documentation generation")
        except Exception as e:
            print(f"Warning: Could not generate CLI documentation: {e}")
        return None
    
    def _generate_template_docs(self) -> Optional[TemplateDocumentationSet]:
        """Generate template documentation"""
        templates_config = self.config.sources.get("templates", {})
        template_path = Path(templates_config.get("path", "templates"))
        
        if not template_path.exists():
            return None
        
        try:
            return self.extractors.template_extractor.extract_templates(template_path)
        except Exception as e:
            print(f"Warning: Could not generate template documentation: {e}")
        return None
    
    def _generate_user_guides(self) -> List[UserGuide]:
        """Generate user guides"""
        generator = UserGuideGenerator()
        return generator.generate_guides()
    
    def _update_module_metrics(self, module_doc: ModuleDocumentation):
        """Update metrics based on module documentation"""
        self.metrics.total_modules += 1
        if module_doc.description and module_doc.purpose:
            self.metrics.documented_modules += 1
        
        self.metrics.total_classes += len(module_doc.classes)
        documented_classes = sum(1 for cls in module_doc.classes if cls.description and cls.purpose)
        self.metrics.documented_classes += documented_classes
        
        self.metrics.total_functions += len(module_doc.functions)
        documented_functions = sum(1 for func in module_doc.functions if func.description)
        self.metrics.documented_functions += documented_functions
    
    def get_metrics(self) -> DocumentationMetrics:
        """Get documentation generation metrics"""
        return self.metrics
    
    def generate_for_module(self, module_name: str) -> Optional[ModuleDocumentation]:
        """Generate documentation for a specific module"""
        try:
            module = importlib.import_module(module_name)
            module_file = Path(inspect.getfile(module))
            return self.extractors.module_extractor.extract_module(module_file)
        except Exception as e:
            print(f"Error generating docs for module {module_name}: {e}")
        return None
    
    def generate_for_class(self, class_path: str) -> Optional[ClassDocumentation]:
        """Generate documentation for a specific class"""
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return self.extractors.module_extractor.extract_class(cls)
        except Exception as e:
            print(f"Error generating docs for class {class_path}: {e}")
        return None
    
    def validate_generation(self) -> bool:
        """Validate that documentation generation was successful"""
        metrics = self.get_metrics()
        
        # Check basic metrics
        if metrics.overall_coverage < 50:
            print(f"Warning: Low documentation coverage ({metrics.overall_coverage:.1f}%)")
        
        if metrics.generation_time > 60:
            print(f"Warning: Documentation generation took {metrics.generation_time:.1f} seconds")
        
        return True