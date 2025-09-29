"""Template management service.

Provides comprehensive template lifecycle operations including
creation, validation, versioning, dependency analysis, and performance optimization.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import re
import yaml
import asyncio
from collections import defaultdict

from ....shared.repository import EntityAlreadyExistsError, EntityNotFoundError, RepositoryError
from ..entities.template import Template, TemplateScope
from ..value_objects.template_name import TemplateName
from ..value_objects.content_type import ContentType
from ..value_objects.content_format import ContentFormat
from ..value_objects.validation_rule import ValidationRule
from ..value_objects.content_length import ContentLength
from ..repositories.content_template_repository import ContentTemplateRepository

logger = logging.getLogger(__name__)


class TemplateValidationError(Exception):
    """Raised when template validation fails."""
    pass


class TemplateDependencyError(Exception):
    """Raised when template dependency operations fail."""
    pass


class TemplateOptimizationError(Exception):
    """Raised when template optimization fails."""
    pass


@dataclass
class TemplateCreationOptions:
    """Options for template creation."""
    validate_syntax: bool = True
    auto_detect_content_type: bool = True
    auto_generate_tags: bool = True
    inherit_validation_rules: bool = True
    set_default_format: bool = True
    create_dependencies: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TemplateDependencyGraph:
    """Template dependency graph analysis."""
    template: Template
    direct_dependencies: List[TemplateName]
    indirect_dependencies: List[TemplateName]
    dependents: List[TemplateName]
    circular_dependencies: List[List[TemplateName]]
    missing_dependencies: List[TemplateName]
    depth: int
    is_leaf: bool
    is_root: bool


@dataclass
class TemplateValidationResult:
    """Result of template validation."""
    is_valid: bool
    syntax_errors: List[str]
    semantic_errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    missing_variables: List[str]
    unused_variables: List[str]
    performance_issues: List[str]


@dataclass
class TemplateInheritanceChain:
    """Template inheritance chain analysis."""
    template: Template
    parent_templates: List[Template]
    child_templates: List[Template]
    inheritance_depth: int
    conflicts: List[str]
    merged_variables: Set[str]
    overridden_prompts: List[str]


@dataclass
class TemplatePerformanceMetrics:
    """Template performance analysis."""
    template: Template
    average_generation_time: float
    average_token_usage: Dict[str, int]
    success_rate: float
    error_rate: float
    cache_hit_rate: float
    quality_score: float
    efficiency_score: float
    complexity_score: float
    optimization_suggestions: List[str]


@dataclass
class TemplateVersionComparison:
    """Comparison between template versions."""
    old_version: Template
    new_version: Template
    syntax_changes: List[str]
    variable_changes: List[str]
    prompt_changes: List[str]
    compatibility_issues: List[str]
    breaking_changes: List[str]
    improvement_suggestions: List[str]


class TemplateManagementService:
    """Service for comprehensive template lifecycle management.
    
    Provides template creation, validation, versioning, dependency analysis,
    inheritance management, and performance optimization capabilities.
    
    Examples:
        service = TemplateManagementService(template_repo)
        
        # Create new template with auto-detection
        template = await service.create_template(
            name=TemplateName.from_user_input("blog-post"),
            yaml_content=yaml_content,
            options=TemplateCreationOptions(auto_detect_content_type=True)
        )
        
        # Analyze template dependencies
        graph = await service.analyze_template_dependencies(template)
        
        # Validate template comprehensively
        result = await service.validate_template_comprehensive(template)
        
        # Optimize template performance
        optimized = await service.optimize_template_performance(template)
    """
    
    def __init__(
        self,
        template_repository: ContentTemplateRepository
    ) -> None:
        """Initialize template management service.
        
        Args:
            template_repository: Repository for template persistence
        """
        self._template_repo = template_repository
        self._validation_cache = {}
        self._dependency_cache = {}
        self._performance_cache = {}
        self._optimization_rules = []
        self._inheritance_analyzers = []
        
        # Built-in validation patterns
        self._variable_pattern = re.compile(r'\{\{\s*([^}]+)\s*\}\}')
        self._step_dependency_pattern = re.compile(r'steps\.([a-zA-Z_][a-zA-Z0-9_]*)')
        self._yaml_validation_enabled = True
        
        # Default optimization rules
        self._setup_default_optimization_rules()
    
    async def create_template(
        self,
        name: TemplateName,
        yaml_content: str,
        options: Optional[TemplateCreationOptions] = None,
        workspace_name: Optional[str] = None
    ) -> Template:
        """Create a new template with comprehensive initialization.
        
        Args:
            name: Template name
            yaml_content: YAML configuration content
            options: Creation options
            workspace_name: Target workspace
            
        Returns:
            Created template
            
        Raises:
            TemplateValidationError: If template validation fails
            EntityAlreadyExistsError: If template name already exists
            RepositoryError: If creation operation fails
        """
        if options is None:
            options = TemplateCreationOptions()
        
        # Check if template already exists
        existing = await self._template_repo.find_by_name(name)
        if existing:
            raise EntityAlreadyExistsError(f"Template '{name}' already exists")
        
        # Validate YAML syntax if requested
        if options.validate_syntax:
            syntax_errors = await self._validate_yaml_syntax(yaml_content)
            if syntax_errors:
                raise TemplateValidationError(f"YAML syntax errors: {syntax_errors}")
        
        # Auto-detect content type
        content_type = ContentType.generic()
        if options.auto_detect_content_type:
            content_type = await self._auto_detect_content_type(yaml_content)
        
        # Auto-generate tags
        tags = []
        if options.auto_generate_tags:
            tags = await self._auto_generate_tags(yaml_content, content_type)
        
        # Set default format
        output_format = None
        if options.set_default_format:
            output_format = await self._determine_default_format(content_type)
        
        # Inherit validation rules
        validation_rules = []
        if options.inherit_validation_rules:
            validation_rules = await self._inherit_validation_rules(content_type)
        
        # Create template entity
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
        
        # Save template
        template = await self._template_repo.save(template, workspace_name)
        
        # Create dependencies if requested
        if options.create_dependencies:
            await self._create_template_dependencies(template, workspace_name)
        
        return template
    
    async def validate_template_comprehensive(
        self,
        template: Template,
        workspace_name: Optional[str] = None
    ) -> TemplateValidationResult:
        """Perform comprehensive template validation.
        
        Args:
            template: Template to validate
            workspace_name: Workspace context
            
        Returns:
            Comprehensive validation result
            
        Raises:
            RepositoryError: If validation operation fails
        """
        # Check cache first
        cache_key = f"{template.id}:{template.version}:{workspace_name}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
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
        
        # YAML syntax validation
        syntax_errors = await self._validate_yaml_syntax(template.yaml_content)
        result.syntax_errors.extend(syntax_errors)
        
        # Semantic validation
        semantic_errors = await self._validate_template_semantics(template)
        result.semantic_errors.extend(semantic_errors)
        
        # Variable analysis
        missing_vars, unused_vars = await self._analyze_template_variables(template)
        result.missing_variables.extend(missing_vars)
        result.unused_variables.extend(unused_vars)
        
        # Performance analysis
        perf_issues = await self._analyze_template_performance_issues(template)
        result.performance_issues.extend(perf_issues)
        
        # Content type compatibility
        compat_warnings = await self._validate_content_type_compatibility(template)
        result.warnings.extend(compat_warnings)
        
        # Generate suggestions
        suggestions = await self._generate_template_suggestions(template, result)
        result.suggestions.extend(suggestions)
        
        # Determine overall validity
        result.is_valid = (
            len(result.syntax_errors) == 0 and
            len(result.semantic_errors) == 0 and
            len(result.missing_variables) == 0
        )
        
        # Cache result
        self._validation_cache[cache_key] = result
        
        return result
    
    async def analyze_template_dependencies(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        max_depth: int = 10
    ) -> TemplateDependencyGraph:
        """Analyze template dependency graph.
        
        Args:
            template: Template to analyze
            workspace_name: Workspace context
            max_depth: Maximum dependency depth to analyze
            
        Returns:
            Dependency graph analysis
            
        Raises:
            TemplateDependencyError: If dependency analysis fails
        """
        # Check cache first
        cache_key = f"{template.id}:{workspace_name}:{max_depth}"
        if cache_key in self._dependency_cache:
            return self._dependency_cache[cache_key]
        
        try:
            # Extract direct dependencies
            direct_deps = await self._extract_direct_dependencies(template)
            
            # Resolve indirect dependencies
            indirect_deps = await self._resolve_indirect_dependencies(
                template, direct_deps, max_depth, workspace_name
            )
            
            # Find dependents
            dependents = await self._find_template_dependents(template, workspace_name)
            
            # Detect circular dependencies
            circular_deps = await self._detect_circular_dependencies(
                template, direct_deps, workspace_name
            )
            
            # Find missing dependencies
            missing_deps = await self._find_missing_dependencies(
                direct_deps + indirect_deps, workspace_name
            )
            
            # Calculate depth and position
            depth = await self._calculate_dependency_depth(template, workspace_name)
            is_leaf = len(direct_deps) == 0
            is_root = len(dependents) == 0
            
            graph = TemplateDependencyGraph(
                template=template,
                direct_dependencies=direct_deps,
                indirect_dependencies=indirect_deps,
                dependents=dependents,
                circular_dependencies=circular_deps,
                missing_dependencies=missing_deps,
                depth=depth,
                is_leaf=is_leaf,
                is_root=is_root
            )
            
            # Cache result
            self._dependency_cache[cache_key] = graph
            
            return graph
            
        except Exception as e:
            raise TemplateDependencyError(f"Dependency analysis failed: {e}") from e
    
    async def analyze_template_inheritance(
        self,
        template: Template,
        workspace_name: Optional[str] = None
    ) -> TemplateInheritanceChain:
        """Analyze template inheritance chain.
        
        Args:
            template: Template to analyze
            workspace_name: Workspace context
            
        Returns:
            Inheritance chain analysis
            
        Raises:
            RepositoryError: If inheritance analysis fails
        """
        # Find parent templates (templates this extends/includes)
        parent_templates = await self._find_parent_templates(template, workspace_name)
        
        # Find child templates (templates that extend/include this)
        child_templates = await self._find_child_templates(template, workspace_name)
        
        # Calculate inheritance depth
        depth = await self._calculate_inheritance_depth(template, workspace_name)
        
        # Analyze conflicts
        conflicts = await self._analyze_inheritance_conflicts(
            template, parent_templates, workspace_name
        )
        
        # Merge variables from inheritance chain
        merged_variables = await self._merge_inherited_variables(
            template, parent_templates
        )
        
        # Find overridden prompts
        overridden_prompts = await self._find_overridden_prompts(
            template, parent_templates
        )
        
        return TemplateInheritanceChain(
            template=template,
            parent_templates=parent_templates,
            child_templates=child_templates,
            inheritance_depth=depth,
            conflicts=conflicts,
            merged_variables=merged_variables,
            overridden_prompts=overridden_prompts
        )
    
    async def optimize_template_performance(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        optimization_level: str = "standard"
    ) -> Template:
        """Optimize template for better performance.
        
        Args:
            template: Template to optimize
            workspace_name: Workspace context
            optimization_level: Level of optimization (basic, standard, aggressive)
            
        Returns:
            Optimized template
            
        Raises:
            TemplateOptimizationError: If optimization fails
        """
        try:
            optimized_template = template
            
            # Apply optimization rules based on level
            if optimization_level in ["basic", "standard", "aggressive"]:
                optimized_template = await self._apply_prompt_optimizations(
                    optimized_template
                )
            
            if optimization_level in ["standard", "aggressive"]:
                optimized_template = await self._apply_variable_optimizations(
                    optimized_template
                )
                optimized_template = await self._apply_structure_optimizations(
                    optimized_template
                )
            
            if optimization_level == "aggressive":
                optimized_template = await self._apply_advanced_optimizations(
                    optimized_template
                )
            
            # Update optimization metadata
            optimized_template = optimized_template.set_metadata(
                "optimization_level", optimization_level
            )
            optimized_template = optimized_template.set_metadata(
                "optimized_at", datetime.now().isoformat()
            )
            
            return optimized_template
            
        except Exception as e:
            raise TemplateOptimizationError(f"Template optimization failed: {e}") from e
    
    async def compare_template_versions(
        self,
        old_template: Template,
        new_template: Template
    ) -> TemplateVersionComparison:
        """Compare two template versions.
        
        Args:
            old_template: Original template version
            new_template: New template version
            
        Returns:
            Version comparison analysis
            
        Raises:
            RepositoryError: If comparison operation fails
        """
        # Analyze syntax changes
        syntax_changes = await self._analyze_syntax_changes(old_template, new_template)
        
        # Analyze variable changes
        variable_changes = await self._analyze_variable_changes(old_template, new_template)
        
        # Analyze prompt changes
        prompt_changes = await self._analyze_prompt_changes(old_template, new_template)
        
        # Check compatibility issues
        compatibility_issues = await self._check_compatibility_issues(
            old_template, new_template
        )
        
        # Identify breaking changes
        breaking_changes = await self._identify_breaking_changes(
            old_template, new_template
        )
        
        # Generate improvement suggestions
        improvements = await self._generate_improvement_suggestions(
            old_template, new_template
        )
        
        return TemplateVersionComparison(
            old_version=old_template,
            new_version=new_template,
            syntax_changes=syntax_changes,
            variable_changes=variable_changes,
            prompt_changes=prompt_changes,
            compatibility_issues=compatibility_issues,
            breaking_changes=breaking_changes,
            improvement_suggestions=improvements
        )
    
    async def get_template_performance_metrics(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> TemplatePerformanceMetrics:
        """Get comprehensive template performance metrics.
        
        Args:
            template: Template to analyze
            workspace_name: Workspace context
            time_range: Time range for metrics (start, end)
            
        Returns:
            Performance metrics analysis
            
        Raises:
            RepositoryError: If metrics calculation fails
        """
        # Check cache first
        cache_key = f"{template.id}:{workspace_name}:{time_range}"
        if cache_key in self._performance_cache:
            return self._performance_cache[cache_key]
        
        # Get usage statistics
        usage_stats = await self._template_repo.get_template_usage_stats(template)
        
        # Calculate performance metrics
        avg_generation_time = usage_stats.get("average_generation_time", 0.0)
        avg_token_usage = usage_stats.get("average_token_usage", {})
        success_rate = usage_stats.get("success_rate", 0.0)
        error_rate = 1.0 - success_rate
        cache_hit_rate = usage_stats.get("cache_hit_rate", 0.0)
        
        # Calculate quality scores
        quality_score = await self._calculate_quality_score(template)
        efficiency_score = await self._calculate_efficiency_score(template, usage_stats)
        complexity_score = await self._calculate_complexity_score(template)
        
        # Generate optimization suggestions
        optimization_suggestions = await self._generate_optimization_suggestions(
            template, usage_stats
        )
        
        metrics = TemplatePerformanceMetrics(
            template=template,
            average_generation_time=avg_generation_time,
            average_token_usage=avg_token_usage,
            success_rate=success_rate,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate,
            quality_score=quality_score,
            efficiency_score=efficiency_score,
            complexity_score=complexity_score,
            optimization_suggestions=optimization_suggestions
        )
        
        # Cache result
        self._performance_cache[cache_key] = metrics
        
        return metrics
    
    async def resolve_template_dependencies(
        self,
        template: Template,
        workspace_name: Optional[str] = None,
        auto_create_missing: bool = False
    ) -> List[Template]:
        """Resolve all template dependencies.
        
        Args:
            template: Template to resolve dependencies for
            workspace_name: Workspace context
            auto_create_missing: Whether to auto-create missing dependencies
            
        Returns:
            List of resolved dependency templates
            
        Raises:
            TemplateDependencyError: If dependency resolution fails
        """
        dependency_graph = await self.analyze_template_dependencies(template, workspace_name)
        
        if dependency_graph.missing_dependencies:
            if auto_create_missing:
                await self._auto_create_missing_dependencies(
                    dependency_graph.missing_dependencies, workspace_name
                )
            else:
                raise TemplateDependencyError(
                    f"Missing dependencies: {dependency_graph.missing_dependencies}"
                )
        
        if dependency_graph.circular_dependencies:
            raise TemplateDependencyError(
                f"Circular dependencies detected: {dependency_graph.circular_dependencies}"
            )
        
        # Load all dependency templates
        resolved_templates = []
        all_deps = dependency_graph.direct_dependencies + dependency_graph.indirect_dependencies
        
        for dep_name in all_deps:
            dep_template = await self._template_repo.find_by_name(dep_name)
            if dep_template:
                resolved_templates.append(dep_template)
        
        return resolved_templates
    
    # Private helper methods
    
    def _setup_default_optimization_rules(self) -> None:
        """Setup default template optimization rules."""
        self._optimization_rules = [
            ("remove_redundant_whitespace", self._remove_redundant_whitespace),
            ("optimize_variable_usage", self._optimize_variable_usage),
            ("simplify_complex_prompts", self._simplify_complex_prompts),
            ("cache_static_content", self._cache_static_content),
            ("minimize_token_usage", self._minimize_token_usage)
        ]
    
    async def _validate_yaml_syntax(self, yaml_content: str) -> List[str]:
        """Validate YAML syntax."""
        errors = []
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
        return errors
    
    async def _auto_detect_content_type(self, yaml_content: str) -> ContentType:
        """Auto-detect content type from YAML content."""
        try:
            parsed = yaml.safe_load(yaml_content)
            metadata = parsed.get("metadata", {})
            
            # Check explicit content type
            if "content_type" in metadata:
                return ContentType.from_string(metadata["content_type"])
            
            # Infer from name or description
            name = metadata.get("name", "").lower()
            description = metadata.get("description", "").lower()
            
            if any(keyword in name + description for keyword in ["blog", "article", "post"]):
                return ContentType.blog_post()
            elif any(keyword in name + description for keyword in ["doc", "documentation"]):
                return ContentType.documentation()
            elif any(keyword in name + description for keyword in ["email", "message"]):
                return ContentType.email()
            elif any(keyword in name + description for keyword in ["report", "analysis"]):
                return ContentType.report()
            else:
                return ContentType.generic()
                
        except Exception:
            return ContentType.generic()
    
    async def _auto_generate_tags(self, yaml_content: str, content_type: ContentType) -> List[str]:
        """Auto-generate tags from template content."""
        tags = set()
        
        # Add content type as tag
        tags.add(content_type.value)
        
        try:
            parsed = yaml.safe_load(yaml_content)
            
            # Extract from metadata
            metadata = parsed.get("metadata", {})
            name = metadata.get("name", "").lower()
            description = metadata.get("description", "").lower()
            
            # Extract keywords from name and description
            keywords = re.findall(r'\b\w{3,}\b', name + " " + description)
            tags.update(keywords[:5])  # Limit to 5 keywords
            
            # Check for specific patterns
            if "steps" in parsed:
                tags.add("multi-step")
                if len(parsed["steps"]) > 5:
                    tags.add("complex")
            
            if "inputs" in parsed:
                tags.add("interactive")
                if len(parsed["inputs"]) > 3:
                    tags.add("detailed-input")
            
        except Exception:
            pass
        
        return list(tags)[:10]  # Limit total tags
    
    async def _determine_default_format(self, content_type: ContentType) -> Optional[ContentFormat]:
        """Determine default output format for content type."""
        format_mapping = {
            "blog_post": ContentFormat.markdown(),
            "documentation": ContentFormat.markdown(),
            "email": ContentFormat.html(),
            "report": ContentFormat.markdown(),
            "generic": ContentFormat.text()
        }
        return format_mapping.get(content_type.value)
    
    async def _inherit_validation_rules(self, content_type: ContentType) -> List[ValidationRule]:
        """Inherit default validation rules for content type."""
        rules = []
        
        if content_type.value == "blog_post":
            rules.extend([
                ValidationRule.word_count_range(500, 2000),
                ValidationRule.readability_score(60),
                ValidationRule.heading_structure()
            ])
        elif content_type.value == "documentation":
            rules.extend([
                ValidationRule.word_count_range(200, 5000),
                ValidationRule.heading_structure(),
                ValidationRule.code_block_syntax()
            ])
        elif content_type.value == "email":
            rules.extend([
                ValidationRule.word_count_range(50, 500),
                ValidationRule.subject_line_length(50)
            ])
        
        return rules
    
    async def _validate_template_semantics(self, template: Template) -> List[str]:
        """Validate template semantic structure."""
        errors = []
        
        try:
            parsed = yaml.safe_load(template.yaml_content)
            
            # Check required sections
            if "metadata" not in parsed:
                errors.append("Missing required 'metadata' section")
            elif "name" not in parsed["metadata"]:
                errors.append("Missing required 'metadata.name' field")
            
            if "steps" not in parsed:
                errors.append("Missing required 'steps' section")
            elif not parsed["steps"]:
                errors.append("Steps section cannot be empty")
            
            # Validate step structure
            if "steps" in parsed:
                for step_name, step_config in parsed["steps"].items():
                    if not isinstance(step_config, dict):
                        errors.append(f"Step '{step_name}' must be a dictionary")
                        continue
                    
                    if "type" not in step_config:
                        errors.append(f"Step '{step_name}' missing required 'type' field")
                    
                    if "prompt_template" not in step_config:
                        errors.append(f"Step '{step_name}' missing required 'prompt_template' field")
            
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")
        except Exception as e:
            errors.append(f"Semantic validation error: {e}")
        
        return errors
    
    async def _analyze_template_variables(self, template: Template) -> Tuple[List[str], List[str]]:
        """Analyze template variables for missing and unused variables."""
        try:
            parsed = yaml.safe_load(template.yaml_content)
            
            # Extract used variables from prompt templates
            used_variables = set()
            for step_config in parsed.get("steps", {}).values():
                if isinstance(step_config, dict) and "prompt_template" in step_config:
                    prompt = step_config["prompt_template"]
                    matches = self._variable_pattern.findall(prompt)
                    used_variables.update(match.strip() for match in matches)
            
            # Extract defined inputs
            defined_inputs = set()
            if "inputs" in parsed:
                defined_inputs.update(f"inputs.{key}" for key in parsed["inputs"].keys())
            
            # Extract available defaults
            available_defaults = set()
            if "defaults" in parsed:
                available_defaults.update(f"defaults.{key}" for key in parsed["defaults"].keys())
            
            # Find missing and unused variables
            all_available = defined_inputs | available_defaults
            missing_variables = [var for var in used_variables if var not in all_available]
            unused_variables = [var for var in all_available if var not in used_variables]
            
            return missing_variables, unused_variables
            
        except Exception:
            return [], []
    
    async def _analyze_template_performance_issues(self, template: Template) -> List[str]:
        """Analyze potential performance issues."""
        issues = []
        
        try:
            parsed = yaml.safe_load(template.yaml_content)
            
            # Check for overly complex prompts
            for step_name, step_config in parsed.get("steps", {}).items():
                if isinstance(step_config, dict) and "prompt_template" in step_config:
                    prompt = step_config["prompt_template"]
                    if len(prompt) > 2000:
                        issues.append(f"Step '{step_name}' has very long prompt (>{len(prompt)} chars)")
                    
                    # Check for excessive variable usage
                    variable_count = len(self._variable_pattern.findall(prompt))
                    if variable_count > 10:
                        issues.append(f"Step '{step_name}' uses many variables ({variable_count})")
            
            # Check for too many steps
            step_count = len(parsed.get("steps", {}))
            if step_count > 10:
                issues.append(f"Template has many steps ({step_count}), consider splitting")
            
        except Exception:
            pass
        
        return issues
    
    async def _validate_content_type_compatibility(self, template: Template) -> List[str]:
        """Validate content type compatibility."""
        warnings = []
        
        # Check if template structure matches content type expectations
        try:
            parsed = yaml.safe_load(template.yaml_content)
            content_type = template.content_type.value
            
            if content_type == "blog_post":
                # Blog posts should have title and content steps
                steps = parsed.get("steps", {})
                if "title" not in steps and "headline" not in steps:
                    warnings.append("Blog post template should include title/headline step")
                if "content" not in steps and "body" not in steps:
                    warnings.append("Blog post template should include content/body step")
            
            elif content_type == "email":
                # Email templates should have subject and body
                steps = parsed.get("steps", {})
                if "subject" not in steps:
                    warnings.append("Email template should include subject step")
                if "body" not in steps and "content" not in steps:
                    warnings.append("Email template should include body/content step")
            
        except Exception:
            pass
        
        return warnings
    
    async def _generate_template_suggestions(
        self,
        template: Template,
        validation_result: TemplateValidationResult
    ) -> List[str]:
        """Generate improvement suggestions for template."""
        suggestions = []
        
        # Suggestions based on validation results
        if validation_result.unused_variables:
            suggestions.append(
                f"Remove unused variables: {', '.join(validation_result.unused_variables)}"
            )
        
        if validation_result.performance_issues:
            suggestions.append("Consider optimizing for better performance")
        
        # Content-specific suggestions
        try:
            parsed = yaml.safe_load(template.yaml_content)
            
            # Suggest adding validation rules
            if not template.validation_rules:
                suggestions.append("Consider adding validation rules for quality assurance")
            
            # Suggest adding descriptions
            if not template.description:
                suggestions.append("Add a description to help users understand the template")
            
            # Suggest adding examples
            if "examples" not in parsed.get("metadata", {}):
                suggestions.append("Add usage examples to improve usability")
            
        except Exception:
            pass
        
        return suggestions
    
    async def _extract_direct_dependencies(self, template: Template) -> List[TemplateName]:
        """Extract direct template dependencies."""
        dependencies = []
        
        try:
            parsed = yaml.safe_load(template.yaml_content)
            
            # Look for template includes/extends
            if "extends" in parsed:
                dependencies.append(TemplateName.from_user_input(parsed["extends"]))
            
            if "includes" in parsed:
                includes = parsed["includes"]
                if isinstance(includes, list):
                    dependencies.extend(
                        TemplateName.from_user_input(inc) for inc in includes
                    )
                elif isinstance(includes, str):
                    dependencies.append(TemplateName.from_user_input(includes))
            
            # Look for step dependencies on other templates
            for step_config in parsed.get("steps", {}).values():
                if isinstance(step_config, dict):
                    if "template" in step_config:
                        dependencies.append(
                            TemplateName.from_user_input(step_config["template"])
                        )
            
        except Exception:
            pass
        
        return dependencies
    
    async def _resolve_indirect_dependencies(
        self,
        template: Template,
        direct_deps: List[TemplateName],
        max_depth: int,
        workspace_name: Optional[str]
    ) -> List[TemplateName]:
        """Resolve indirect dependencies recursively."""
        indirect_deps = []
        visited = set()
        
        async def _resolve_recursive(deps: List[TemplateName], depth: int):
            if depth >= max_depth:
                return
            
            for dep_name in deps:
                if dep_name in visited:
                    continue
                visited.add(dep_name)
                
                # Load dependency template
                dep_template = await self._template_repo.find_by_name(dep_name)
                if dep_template:
                    # Get its dependencies
                    sub_deps = await self._extract_direct_dependencies(dep_template)
                    indirect_deps.extend(sub_deps)
                    
                    # Recurse
                    await _resolve_recursive(sub_deps, depth + 1)
        
        await _resolve_recursive(direct_deps, 0)
        
        # Remove duplicates and direct dependencies
        return list(set(indirect_deps) - set(direct_deps))
    
    async def _find_template_dependents(
        self,
        template: Template,
        workspace_name: Optional[str]
    ) -> List[TemplateName]:
        """Find templates that depend on this template."""
        dependents = await self._template_repo.get_template_dependents(template)
        return dependents
    
    async def _detect_circular_dependencies(
        self,
        template: Template,
        dependencies: List[TemplateName],
        workspace_name: Optional[str]
    ) -> List[List[TemplateName]]:
        """Detect circular dependencies."""
        circular_deps = []
        
        # Simple cycle detection - could be enhanced with graph algorithms
        for dep_name in dependencies:
            dep_template = await self._template_repo.find_by_name(dep_name)
            if dep_template:
                dep_dependencies = await self._extract_direct_dependencies(dep_template)
                if template.name in dep_dependencies:
                    circular_deps.append([template.name, dep_name])
        
        return circular_deps
    
    async def _find_missing_dependencies(
        self,
        dependencies: List[TemplateName],
        workspace_name: Optional[str]
    ) -> List[TemplateName]:
        """Find missing dependency templates."""
        missing = []
        
        for dep_name in dependencies:
            dep_template = await self._template_repo.find_by_name(dep_name)
            if not dep_template:
                missing.append(dep_name)
        
        return missing
    
    async def _calculate_dependency_depth(
        self,
        template: Template,
        workspace_name: Optional[str]
    ) -> int:
        """Calculate maximum dependency depth."""
        # This would implement a graph traversal to find maximum depth
        # For now, return a simple estimate
        direct_deps = await self._extract_direct_dependencies(template)
        return len(direct_deps)
    
    async def _apply_prompt_optimizations(self, template: Template) -> Template:
        """Apply prompt-level optimizations."""
        # This would implement prompt optimization logic
        return template
    
    async def _apply_variable_optimizations(self, template: Template) -> Template:
        """Apply variable usage optimizations."""
        # This would implement variable optimization logic
        return template
    
    async def _apply_structure_optimizations(self, template: Template) -> Template:
        """Apply structural optimizations."""
        # This would implement structure optimization logic
        return template
    
    async def _apply_advanced_optimizations(self, template: Template) -> Template:
        """Apply advanced optimizations."""
        # This would implement advanced optimization logic
        return template
    
    async def _calculate_quality_score(self, template: Template) -> float:
        """Calculate template quality score."""
        # This would implement quality scoring logic
        return 0.8  # Placeholder
    
    async def _calculate_efficiency_score(self, template: Template, usage_stats: Dict[str, Any]) -> float:
        """Calculate template efficiency score."""
        # This would implement efficiency scoring logic
        return 0.7  # Placeholder
    
    async def _calculate_complexity_score(self, template: Template) -> float:
        """Calculate template complexity score."""
        # This would implement complexity scoring logic
        return 0.5  # Placeholder
    
    async def _generate_optimization_suggestions(
        self,
        template: Template,
        usage_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization suggestions."""
        suggestions = []
        
        # Based on usage statistics
        if usage_stats.get("average_generation_time", 0) > 10:
            suggestions.append("Consider simplifying prompts to reduce generation time")
        
        if usage_stats.get("error_rate", 0) > 0.1:
            suggestions.append("Add validation rules to reduce error rate")
        
        if usage_stats.get("cache_hit_rate", 0) < 0.3:
            suggestions.append("Consider caching strategies for better performance")
        
        return suggestions
    
    # Additional helper methods for version comparison, inheritance analysis, etc.
    # These would be implemented with specific logic for each feature
    
    async def _analyze_syntax_changes(self, old: Template, new: Template) -> List[str]:
        """Analyze syntax changes between versions."""
        return []  # Placeholder
    
    async def _analyze_variable_changes(self, old: Template, new: Template) -> List[str]:
        """Analyze variable changes between versions."""
        return []  # Placeholder
    
    async def _analyze_prompt_changes(self, old: Template, new: Template) -> List[str]:
        """Analyze prompt changes between versions."""
        return []  # Placeholder
    
    async def _check_compatibility_issues(self, old: Template, new: Template) -> List[str]:
        """Check compatibility issues between versions."""
        return []  # Placeholder
    
    async def _identify_breaking_changes(self, old: Template, new: Template) -> List[str]:
        """Identify breaking changes between versions."""
        return []  # Placeholder
    
    async def _generate_improvement_suggestions(self, old: Template, new: Template) -> List[str]:
        """Generate improvement suggestions."""
        return []  # Placeholder
    
    # Optimization rule implementations
    
    async def _remove_redundant_whitespace(self, template: Template) -> Template:
        """Remove redundant whitespace from template."""
        return template  # Placeholder
    
    async def _optimize_variable_usage(self, template: Template) -> Template:
        """Optimize variable usage in template."""
        return template  # Placeholder
    
    async def _simplify_complex_prompts(self, template: Template) -> Template:
        """Simplify overly complex prompts."""
        return template  # Placeholder
    
    async def _cache_static_content(self, template: Template) -> Template:
        """Add caching for static content."""
        return template  # Placeholder
    
    async def _minimize_token_usage(self, template: Template) -> Template:
        """Minimize token usage in prompts."""
        return template  # Placeholder
    
    # Inheritance and dependency helper methods
    
    async def _find_parent_templates(
        self,
        template: Template,
        workspace_name: Optional[str]
    ) -> List[Template]:
        """Find parent templates in inheritance chain."""
        return []  # Placeholder
    
    async def _find_child_templates(
        self,
        template: Template,
        workspace_name: Optional[str]
    ) -> List[Template]:
        """Find child templates in inheritance chain."""
        return []  # Placeholder
    
    async def _calculate_inheritance_depth(
        self,
        template: Template,
        workspace_name: Optional[str]
    ) -> int:
        """Calculate inheritance depth."""
        return 0  # Placeholder
    
    async def _analyze_inheritance_conflicts(
        self,
        template: Template,
        parents: List[Template],
        workspace_name: Optional[str]
    ) -> List[str]:
        """Analyze inheritance conflicts."""
        return []  # Placeholder
    
    async def _merge_inherited_variables(
        self,
        template: Template,
        parents: List[Template]
    ) -> Set[str]:
        """Merge variables from inheritance chain."""
        return set()  # Placeholder
    
    async def _find_overridden_prompts(
        self,
        template: Template,
        parents: List[Template]
    ) -> List[str]:
        """Find overridden prompts in inheritance chain."""
        return []  # Placeholder
    
    async def _create_template_dependencies(
        self,
        template: Template,
        workspace_name: Optional[str]
    ) -> None:
        """Create missing template dependencies."""
        # Extract dependencies from template content
        dependencies = self._extract_template_dependencies(template.content)
        
        if not dependencies:
            return
        
        # Check which dependencies exist
        missing_deps = []
        for dep_name in dependencies:
            try:
                await self._template_repository.get_by_name(dep_name, workspace_name)
            except RepositoryError:
                missing_deps.append(dep_name)
        
        if missing_deps:
            # Log missing dependencies
            logger.warning(
                f"Missing template dependencies: {[str(dep) for dep in missing_deps]} "
                f"for template {template.name} in workspace: {workspace_name or 'global'}"
            )
            
            # Optionally auto-create if enabled
            if hasattr(self, '_auto_create_dependencies') and getattr(self, '_auto_create_dependencies', False):
                await self._auto_create_missing_dependencies(missing_deps, workspace_name)
    
    async def _auto_create_missing_dependencies(
        self,
        missing_deps: List[TemplateName],
        workspace_name: Optional[str]
    ) -> None:
        """Auto-create missing dependency templates."""
        for dep_name in missing_deps:
            try:
                # Create a basic template stub for the missing dependency
                stub_template = Template.create(
                    name=dep_name,
                    content=f"# Auto-generated template stub for {dep_name}\n\n{{{{ content }}}}",
                    description=f"Auto-generated dependency template for {dep_name}",
                    template_type=ContentType.TEMPLATE_STUB,
                    scope=TemplateScope.WORKSPACE if workspace_name else TemplateScope.GLOBAL,
                    workspace_name=workspace_name,
                    author="system",
                    tags=["auto-generated", "dependency-stub"]
                )
                
                await self._template_repository.save(stub_template)
                
                logger.info(f"Auto-created template dependency stub: {dep_name}")
                
            except Exception as e:
                logger.error(f"Failed to auto-create template dependency {dep_name}: {e}")
                # Continue with other dependencies even if one fails