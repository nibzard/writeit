"""
Data models for documentation generation system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class CodeExample:
    """Represents a code example with metadata"""
    code: str
    description: str
    language: str = "python"
    source_file: Optional[Path] = None
    line_number: Optional[int] = None
    expected_output: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ParameterDocumentation:
    """Documentation for a function/method parameter"""
    name: str
    type_annotation: str
    description: str
    default_value: Optional[str] = None
    required: bool = True


@dataclass
class FunctionDocumentation:
    """Documentation for a function or method"""
    name: str
    signature: str
    description: str
    parameters: List[ParameterDocumentation]
    return_type: str
    return_description: str
    examples: List[CodeExample] = field(default_factory=list)
    source_file: Optional[Path] = None
    line_number: Optional[int] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ClassDocumentation:
    """Documentation for a class"""
    name: str
    description: str
    purpose: str
    methods: List[FunctionDocumentation]
    class_variables: Dict[str, str] = field(default_factory=dict)
    inheritance: List[str] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)
    source_file: Optional[Path] = None
    line_number: Optional[int] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ModuleDocumentation:
    """Documentation for a Python module"""
    name: str
    description: str
    purpose: str
    classes: List[ClassDocumentation]
    functions: List[FunctionDocumentation]
    dependencies: List[str] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)
    source_file: Optional[Path] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class APIEndpointDocumentation:
    """Documentation for an API endpoint"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[ParameterDocumentation]
    request_body: Optional[Dict[str, Any]] = None
    response_body: Optional[Dict[str, Any]] = None
    status_codes: Dict[int, str] = field(default_factory=dict)
    examples: List[CodeExample] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class APIModelDocumentation:
    """Documentation for an API model (Pydantic model)"""
    name: str
    description: str
    fields: Dict[str, str] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    source_file: Optional[Path] = None


@dataclass
class APIDocumentation:
    """Complete API documentation"""
    title: str
    description: str
    version: str
    base_url: str
    endpoints: List[APIEndpointDocumentation]
    models: List[APIModelDocumentation]
    websocket_endpoints: List[APIEndpointDocumentation] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)


@dataclass
class CommandDocumentation:
    """Documentation for a CLI command"""
    name: str
    description: str
    usage: str
    arguments: List[ParameterDocumentation]
    options: List[ParameterDocumentation]
    examples: List[str] = field(default_factory=list)
    source_file: Optional[Path] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class CLIDocumentation:
    """Complete CLI documentation"""
    app_name: str
    description: str
    commands: List[CommandDocumentation]
    global_options: List[ParameterDocumentation] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)


@dataclass
class TemplateFieldDocumentation:
    """Documentation for a template field"""
    name: str
    type: str
    description: str
    required: bool
    default_value: Optional[str] = None
    options: Optional[List[str]] = None
    validation: Optional[str] = None


@dataclass
class TemplateStepDocumentation:
    """Documentation for a template step"""
    key: str
    name: str
    description: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TemplateDocumentation:
    """Documentation for a pipeline template"""
    name: str
    description: str
    version: str
    inputs: List[TemplateFieldDocumentation]
    steps: List[TemplateStepDocumentation]
    metadata: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    source_file: Optional[Path] = None


@dataclass
class TemplateDocumentationSet:
    """Collection of template documentation"""
    templates: List[TemplateDocumentation]
    style_primers: List[TemplateDocumentation] = field(default_factory=list)


@dataclass
class UserGuide:
    """User guide documentation"""
    title: str
    description: str
    content: str
    audience: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: str
    prerequisites: List[str] = field(default_factory=list)
    related_guides: List[str] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)


@dataclass
class DocumentationSet:
    """Complete documentation set"""
    api_docs: Optional[APIDocumentation] = None
    module_docs: List[ModuleDocumentation] = field(default_factory=list)
    cli_docs: Optional[CLIDocumentation] = None
    template_docs: Optional[TemplateDocumentationSet] = None
    user_guides: List[UserGuide] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"


@dataclass
class ValidationError:
    """Represents a documentation validation error"""
    type: str
    message: str
    severity: str  # error, warning, info
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of documentation validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    coverage_percentage: float = 0.0
    total_items: int = 0
    documented_items: int = 0

    def add_error(self, error_type: str, message: str, **kwargs):
        """Add an error to the validation result"""
        self.errors.append(ValidationError(
            type=error_type,
            message=message,
            severity="error",
            **kwargs
        ))

    def add_warning(self, warning_type: str, message: str, **kwargs):
        """Add a warning to the validation result"""
        self.warnings.append(ValidationError(
            type=warning_type,
            message=message,
            severity="warning",
            **kwargs
        ))

    def add_info(self, info_type: str, message: str, **kwargs):
        """Add an info message to the validation result"""
        self.info.append(ValidationError(
            type=info_type,
            message=message,
            severity="info",
            **kwargs
        ))

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return len(self.warnings) > 0


@dataclass
class DocumentationConfig:
    """Configuration for documentation generation"""
    sources: Dict[str, Any] = field(default_factory=lambda: {
        "modules": {
            "path": "src/writeit",
            "patterns": ["**/*.py"],
            "exclude": ["**/__pycache__/**", "**/tests/**"]
        }
    })
    outputs: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    deployment: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, config_path: Path) -> "DocumentationConfig":
        """Load configuration from YAML file"""
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data.get('documentation', {}))


@dataclass
class DocumentationMetrics:
    """Documentation quality and coverage metrics"""
    total_modules: int = 0
    documented_modules: int = 0
    total_classes: int = 0
    documented_classes: int = 0
    total_functions: int = 0
    documented_functions: int = 0
    total_api_endpoints: int = 0
    documented_api_endpoints: int = 0
    total_examples: int = 0
    valid_examples: int = 0
    broken_links: int = 0
    generation_time: float = 0.0
    
    @property
    def module_coverage(self) -> float:
        """Calculate module documentation coverage"""
        return self.documented_modules / self.total_modules * 100 if self.total_modules > 0 else 0
    
    @property
    def class_coverage(self) -> float:
        """Calculate class documentation coverage"""
        return self.documented_classes / self.total_classes * 100 if self.total_classes > 0 else 0
    
    @property
    def function_coverage(self) -> float:
        """Calculate function documentation coverage"""
        return self.documented_functions / self.total_functions * 100 if self.total_functions > 0 else 0
    
    @property
    def api_coverage(self) -> float:
        """Calculate API documentation coverage"""
        return self.documented_api_endpoints / self.total_api_endpoints * 100 if self.total_api_endpoints > 0 else 0
    
    @property
    def example_validity(self) -> float:
        """Calculate example validity rate"""
        return self.valid_examples / self.total_examples * 100 if self.total_examples > 0 else 0
    
    @property
    def overall_coverage(self) -> float:
        """Calculate overall documentation coverage"""
        total_items = self.total_modules + self.total_classes + self.total_functions + self.total_api_endpoints
        documented_items = self.documented_modules + self.documented_classes + self.documented_functions + self.documented_api_endpoints
        return documented_items / total_items * 100 if total_items > 0 else 0