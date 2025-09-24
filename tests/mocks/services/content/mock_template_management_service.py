"""Mock template management service for testing."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from writeit.domains.content.entities.template import Template
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.validation_rule import ValidationRule
from writeit.domains.content.services.template_management_service import (
    TemplateManagementService,
    TemplateCreationOptions,
    TemplateValidationResult,
    TemplateDependencyGraph,
    TemplateInheritanceChain,
    TemplatePerformanceMetrics,
    TemplateVersionComparison,
    TemplateValidationError,
    TemplateDependencyError,
    TemplateOptimizationError
)
from writeit.shared.repository import EntityAlreadyExistsError, EntityNotFoundError


class MockTemplateManagementService(TemplateManagementService):
    """Mock implementation of TemplateManagementService for testing."""
    
    def __init__(self):
        """Initialize mock service with test data."""
        # Don't call super().__init__ to avoid dependency injection
        self._templates: Dict[TemplateName, Template] = {}
        self._validation_results: Dict[TemplateName, TemplateValidationResult] = {}
        self._dependency_graphs: Dict[TemplateName, TemplateDependencyGraph] = {}
        self._performance_metrics: Dict[TemplateName, TemplatePerformanceMetrics] = {}
        
        # Mock state for testing
        self._should_fail_creation = False
        self._should_fail_validation = False
        self._should_fail_optimization = False
        self._should_fail_dependency_analysis = False
        self._custom_validation_result: Optional[TemplateValidationResult] = None
        
        # Setup default test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Setup default test data."""
        # Create sample templates
        blog_post_template = Template.create(
            name=TemplateName.from_user_input("blog-post"),
            content_type=ContentType.blog_post(),
            yaml_content="""metadata:
  name: "Blog Post"
  description: "Generate engaging blog posts"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"

inputs:
  topic:
    type: text
    label: "Blog Topic"
    required: true

steps:
  title:
    name: "Generate Title"
    type: llm_generate
    prompt_template: "Create an engaging title for: {{ inputs.topic }}"
    
  content:
    name: "Write Content"
    type: llm_generate
    prompt_template: "Write a blog post about {{ inputs.topic }} with title: {{ steps.title }}"
""",
            tags=["blog", "content", "writing"],
            output_format=ContentFormat.markdown(),
            validation_rules=[
                ValidationRule.word_count_range(500, 2000),
                ValidationRule.readability_score(60)
            ]
        )
        
        documentation_template = Template.create(
            name=TemplateName.from_user_input("documentation"),
            content_type=ContentType.documentation(),
            yaml_content="""metadata:
  name: "Documentation"
  description: "Generate technical documentation"
  version: "1.0.0"

inputs:
  feature:
    type: text
    label: "Feature Name"
    required: true

steps:
  overview:
    name: "Feature Overview"
    type: llm_generate
    prompt_template: "Write an overview of {{ inputs.feature }}"
    
  usage:
    name: "Usage Instructions"
    type: llm_generate
    prompt_template: "Write usage instructions for {{ inputs.feature }}"
""",
            tags=["documentation", "technical"],
            output_format=ContentFormat.markdown(),
            validation_rules=[
                ValidationRule.heading_structure(),
                ValidationRule.code_block_syntax()
            ]
        )
        
        self._templates[blog_post_template.name] = blog_post_template
        self._templates[documentation_template.name] = documentation_template
        
        # Create sample validation results
        blog_validation = TemplateValidationResult(
            is_valid=True,
            syntax_errors=[],
            semantic_errors=[],
            warnings=[],
            suggestions=["Consider adding examples section"],
            missing_variables=[],
            unused_variables=[],
            performance_issues=[]
        )
        
        doc_validation = TemplateValidationResult(
            is_valid=True,
            syntax_errors=[],
            semantic_errors=[],
            warnings=["Consider adding API reference"],
            suggestions=["Add code examples", "Include troubleshooting section"],
            missing_variables=[],
            unused_variables=[],
            performance_issues=[]
        )
        
        self._validation_results[blog_post_template.name] = blog_validation
        self._validation_results[documentation_template.name] = doc_validation
        
        # Create sample dependency graph
        blog_dependency_graph = TemplateDependencyGraph(
            template=blog_post_template,
            direct_dependencies=[],
            indirect_dependencies=[],
            dependents=[],
            circular_dependencies=[],
            missing_dependencies=[],
            depth=0,
            is_leaf=True,
            is_root=True
        )
        
        self._dependency_graphs[blog_post_template.name] = blog_dependency_graph
        
        # Create sample performance metrics
        blog_performance = TemplatePerformanceMetrics(
            template=blog_post_template,
            average_generation_time=25.5,
            average_token_usage={"input": 150, "output": 800},
            success_rate=0.95,
            error_rate=0.05,
            cache_hit_rate=0.72,
            quality_score=0.88,
            efficiency_score=0.82,
            complexity_score=0.45,
            optimization_suggestions=["Reduce prompt complexity", "Add caching"]
        )
        
        self._performance_metrics[blog_post_template.name] = blog_performance
    
    # Mock control methods for testing
    
    def set_should_fail_creation(self, should_fail: bool):
        """Control whether template creation should fail."""
        self._should_fail_creation = should_fail
    
    def set_should_fail_validation(self, should_fail: bool):
        """Control whether validation should fail."""
        self._should_fail_validation = should_fail
    
    def set_should_fail_optimization(self, should_fail: bool):
        """Control whether optimization should fail."""
        self._should_fail_optimization = should_fail
    
    def set_should_fail_dependency_analysis(self, should_fail: bool):
        """Control whether dependency analysis should fail."""
        self._should_fail_dependency_analysis = should_fail
    
    def set_custom_validation_result(self, result: Optional[TemplateValidationResult]):
        """Set custom validation result for testing."""
        self._custom_validation_result = result
    
    def add_template(self, template: Template):
        """Add template for testing."""
        self._templates[template.name] = template
    
    def get_template(self, name: TemplateName) -> Optional[Template]:
        """Get template by name for testing."""
        return self._templates.get(name)
    
    def list_templates(self) -> List[Template]:
        """List all templates for testing."""
        return list(self._templates.values())
    
    def set_validation_result(self, name: TemplateName, result: TemplateValidationResult):
        """Set validation result for testing."""
        self._validation_results[name] = result
    
    # Implementation of TemplateManagementService interface
    
    async def create_template(
        self,
        name: TemplateName,
        yaml_content: str,
        options: Optional[TemplateCreationOptions] = None,
        workspace_name: Optional[str] = None
    ) -> Template:
        """Create a new template with comprehensive initialization."""
        if self._should_fail_creation:
            raise TemplateValidationError("Forced creation failure for testing")
        
        if name in self._templates:
            raise EntityAlreadyExistsError(f"Template '{name}' already exists")
        
        if options is None:
            options = TemplateCreationOptions()
        
        # Auto-detect content type
        content_type = ContentType.generic()
        if options.auto_detect_content_type:
            if "blog" in yaml_content.lower():
                content_type = ContentType.blog_post()
            elif "doc" in yaml_content.lower():
                content_type = ContentType.documentation()
            elif "email" in yaml_content.lower():
                content_type = ContentType.email()
        
        # Auto-generate tags
        tags = []
        if options.auto_generate_tags:
            if content_type.value == "blog_post":
                tags = ["blog", "content", "writing"]
            elif content_type.value == "documentation":
                tags = ["documentation", "technical"]
            elif content_type.value == "email":
                tags = ["email", "communication"]
        
        # Set default format
        output_format = None
        if options.set_default_format:
            if content_type.value in ["blog_post", "documentation"]:
                output_format = ContentFormat.markdown()
            elif content_type.value == "email":
                output_format = ContentFormat.html()
            else:
                output_format = ContentFormat.text()
        
        # Inherit validation rules
        validation_rules = []
        if options.inherit_validation_rules:
            if content_type.value == "blog_post":
                validation_rules = [
                    ValidationRule.word_count_range(500, 2000),
                    ValidationRule.readability_score(60)
                ]
            elif content_type.value == "documentation":
                validation_rules = [
                    ValidationRule.heading_structure(),
                    ValidationRule.code_block_syntax()
                ]
        
        # Create template
        template = Template.create(
            name=name,
            content_type=content_type,
            yaml_content=yaml_content,
            tags=tags,
            output_format=output_format,
            validation_rules=validation_rules
        )
        
        # Set metadata if provided
        if options.metadata:
            for key, value in options.metadata.items():
                template = template.set_metadata(key, value)
        
        # Store template
        self._templates[name] = template
        
        return template
    
    async def validate_template_comprehensive(
        self,
        template: Template,
        workspace_name: Optional[str] = None
    ) -> TemplateValidationResult:
        """Perform comprehensive template validation."""
        if self._should_fail_validation:
            raise TemplateValidationError("Forced validation failure for testing")
        
        # Return custom result if set
        if self._custom_validation_result:
            return self._custom_validation_result
        
        # Return existing result if available
        if template.name in self._validation_results:
            return self._validation_results[template.name]
        
        # Create basic validation result for new templates
        result = TemplateValidationResult(
            is_valid=True,
            syntax_errors=[],
            semantic_errors=[],
            warnings=[],
            suggestions=[],
            missing_variables=[],
            unused_variables=[],
            performance_issues=[]
        )
        
        # Basic YAML syntax check
        try:
            import yaml
            yaml.safe_load(template.yaml_content)
        except yaml.YAMLError as e:
            result.syntax_errors.append(f"YAML syntax error: {e}")
            result.is_valid = False
        
        # Check for required sections
        if "metadata" not in template.yaml_content:
            result.semantic_errors.append("Missing required 'metadata' section")
            result.is_valid = False
        
        if "steps" not in template.yaml_content:
            result.semantic_errors.append("Missing required 'steps' section")
            result.is_valid = False
        
        # Store result
        self._validation_results[template.name] = result
        
        return result
    
    async def analyze_template_dependencies(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        max_depth: int = 10
    ) -> TemplateDependencyGraph:
        """Analyze template dependency graph."""
        if self._should_fail_dependency_analysis:
            raise TemplateDependencyError("Forced dependency analysis failure for testing")
        
        # Return existing graph if available
        if template.name in self._dependency_graphs:
            return self._dependency_graphs[template.name]
        
        # Create basic dependency graph
        graph = TemplateDependencyGraph(
            template=template,
            direct_dependencies=[],
            indirect_dependencies=[],
            dependents=[],
            circular_dependencies=[],
            missing_dependencies=[],
            depth=0,
            is_leaf=True,
            is_root=True
        )
        
        # Simple dependency analysis
        try:
            import yaml
            parsed = yaml.safe_load(template.yaml_content)
            
            # Check for extends/includes
            if "extends" in parsed:
                extends_name = TemplateName.from_user_input(parsed["extends"])
                graph.direct_dependencies.append(extends_name)
                
                # Check if dependency exists
                if extends_name not in self._templates:
                    graph.missing_dependencies.append(extends_name)
                
                graph.is_leaf = False
            
            if "includes" in parsed:
                includes = parsed["includes"]
                if isinstance(includes, list):
                    for inc in includes:
                        inc_name = TemplateName.from_user_input(inc)
                        graph.direct_dependencies.append(inc_name)
                        if inc_name not in self._templates:
                            graph.missing_dependencies.append(inc_name)
                elif isinstance(includes, str):
                    inc_name = TemplateName.from_user_input(includes)
                    graph.direct_dependencies.append(inc_name)
                    if inc_name not in self._templates:
                        graph.missing_dependencies.append(inc_name)
                
                graph.is_leaf = len(graph.direct_dependencies) == 0
        
        except Exception:
            pass
        
        self._dependency_graphs[template.name] = graph
        return graph
    
    async def analyze_template_inheritance(
        self,
        template: Template,
        workspace_name: Optional[str] = None
    ) -> TemplateInheritanceChain:
        """Analyze template inheritance chain."""
        return TemplateInheritanceChain(
            template=template,
            parent_templates=[],
            child_templates=[],
            inheritance_depth=0,
            conflicts=[],
            merged_variables=set(),
            overridden_prompts=[]
        )
    
    async def optimize_template_performance(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        optimization_level: str = "standard"
    ) -> Template:
        """Optimize template for better performance."""
        if self._should_fail_optimization:
            raise TemplateOptimizationError("Forced optimization failure for testing")
        
        # Create optimized version with metadata
        optimized_template = template.set_metadata(
            "optimization_level", optimization_level
        )
        optimized_template = optimized_template.set_metadata(
            "optimized_at", datetime.now().isoformat()
        )
        
        # Update stored template
        self._templates[template.name] = optimized_template
        
        return optimized_template
    
    async def compare_template_versions(
        self,
        old_template: Template,
        new_template: Template
    ) -> TemplateVersionComparison:
        """Compare two template versions."""
        return TemplateVersionComparison(
            old_version=old_template,
            new_version=new_template,
            syntax_changes=["Updated YAML structure"],
            variable_changes=["Added new input field"],
            prompt_changes=["Modified step prompts"],
            compatibility_issues=[],
            breaking_changes=[],
            improvement_suggestions=["Consider adding validation"]
        )
    
    async def get_template_performance_metrics(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> TemplatePerformanceMetrics:
        """Get comprehensive template performance metrics."""
        # Return existing metrics if available
        if template.name in self._performance_metrics:
            return self._performance_metrics[template.name]
        
        # Create default metrics
        metrics = TemplatePerformanceMetrics(
            template=template,
            average_generation_time=20.0,
            average_token_usage={"input": 100, "output": 500},
            success_rate=0.90,
            error_rate=0.10,
            cache_hit_rate=0.60,
            quality_score=0.80,
            efficiency_score=0.75,
            complexity_score=0.50,
            optimization_suggestions=["Consider prompt optimization"]
        )
        
        self._performance_metrics[template.name] = metrics
        return metrics
    
    async def resolve_template_dependencies(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        auto_create_missing: bool = False
    ) -> List[Template]:
        """Resolve all template dependencies."""
        dependency_graph = await self.analyze_template_dependencies(template, workspace_name)
        
        if dependency_graph.missing_dependencies:
            if not auto_create_missing:
                raise TemplateDependencyError(
                    f"Missing dependencies: {dependency_graph.missing_dependencies}"
                )
            
            # Auto-create missing dependencies (simplified)
            for dep_name in dependency_graph.missing_dependencies:
                if dep_name not in self._templates:
                    # Create minimal template
                    dep_template = Template.create(
                        name=dep_name,
                        content_type=ContentType.generic(),
                        yaml_content=f"""metadata:
  name: "{dep_name}"
  description: "Auto-generated template"
  version: "1.0.0"

steps:
  content:
    name: "Generate Content"
    type: llm_generate
    prompt_template: "Generate content"
""",
                        tags=["auto-generated"],
                        output_format=ContentFormat.text(),
                        validation_rules=[]
                    )
                    self._templates[dep_name] = dep_template
        
        if dependency_graph.circular_dependencies:
            raise TemplateDependencyError(
                f"Circular dependencies detected: {dependency_graph.circular_dependencies}"
            )
        
        # Load all dependency templates
        resolved_templates = []
        all_deps = dependency_graph.direct_dependencies + dependency_graph.indirect_dependencies
        
        for dep_name in all_deps:
            if dep_name in self._templates:
                resolved_templates.append(self._templates[dep_name])
        
        return resolved_templates
    
    # Additional helper methods for testing
    
    def clear_all_templates(self):
        """Clear all templates for testing."""
        self._templates.clear()
        self._validation_results.clear()
        self._dependency_graphs.clear()
        self._performance_metrics.clear()
    
    def get_validation_result(self, name: TemplateName) -> Optional[TemplateValidationResult]:
        """Get validation result for testing."""
        return self._validation_results.get(name)
    
    def get_dependency_graph(self, name: TemplateName) -> Optional[TemplateDependencyGraph]:
        """Get dependency graph for testing."""
        return self._dependency_graphs.get(name)
    
    def get_performance_metrics(self, name: TemplateName) -> Optional[TemplatePerformanceMetrics]:
        """Get performance metrics for testing."""
        return self._performance_metrics.get(name)
    
    def reset_mock_state(self):
        """Reset mock state for testing."""
        self._should_fail_creation = False
        self._should_fail_validation = False
        self._should_fail_optimization = False
        self._should_fail_dependency_analysis = False
        self._custom_validation_result = None
        self.clear_all_templates()
        self._setup_test_data()