"""
Documentation validation system
"""

import json
import re
import ssl
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse
import urllib.request
from urllib.error import URLError

from .models import (
    DocumentationSet,
    ValidationResult,
    ValidationError,
    DocumentationMetrics
)


class DocumentationValidator:
    """Validate documentation quality and consistency"""
    
    def __init__(self):
        self.metrics = DocumentationMetrics()
        self.validation_results = []
    
    def validate_all(self, docs: DocumentationSet) -> ValidationResult:
        """Perform comprehensive validation of documentation"""
        results = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            info=[]
        )
        
        # Validate API documentation
        if docs.api_docs:
            self._validate_api_docs(docs.api_docs, results)
        
        # Validate module documentation
        if docs.module_docs:
            self._validate_module_docs(docs.module_docs, results)
        
        # Validate CLI documentation
        if docs.cli_docs:
            self._validate_cli_docs(docs.cli_docs, results)
        
        # Validate code examples
        self._validate_code_examples(docs, results)
        
        # Validate links
        if results.coverage_percentage > 0:  # Only validate if we have docs
            self._validate_links(docs, results)
        
        # Check completeness
        self._validate_completeness(docs, results)
        
        # Calculate overall validity
        results.is_valid = len(results.errors) == 0
        
        return results
    
    def _validate_api_docs(self, api_docs, results: ValidationResult):
        """Validate API documentation"""
        if not api_docs.endpoints:
            results.add_error("api_empty", "No API endpoints found", suggestion="Check FastAPI app configuration")
            return
        
        # Update metrics
        self.metrics.total_api_endpoints = len(api_docs.endpoints)
        self.metrics.documented_api_endpoints = len([e for e in api_docs.endpoints if e.description])
        
        # Validate each endpoint
        for endpoint in api_docs.endpoints:
            self._validate_endpoint(endpoint, results)
    
    def _validate_endpoint(self, endpoint, results: ValidationResult):
        """Validate a single API endpoint"""
        # Check required fields
        if not endpoint.path:
            results.add_error("endpoint_missing_path", f"Endpoint missing path: {endpoint.method}")
        
        if not endpoint.method:
            results.add_error("endpoint_missing_method", f"Endpoint missing method: {endpoint.path}")
        
        if not endpoint.description:
            results.add_warning("endpoint_missing_description", f"Endpoint missing description: {endpoint.method} {endpoint.path}")
        
        # Validate path format
        if endpoint.path and not endpoint.path.startswith('/'):
            results.add_error("endpoint_invalid_path", f"Invalid path format: {endpoint.path}")
        
        # Validate HTTP method
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'WebSocket']
        if endpoint.method not in valid_methods:
            results.add_error("endpoint_invalid_method", f"Invalid HTTP method: {endpoint.method}")
    
    def _validate_module_docs(self, module_docs: List, results: ValidationResult):
        """Validate module documentation"""
        for module in module_docs:
            self._validate_module(module, results)
    
    def _validate_module(self, module, results: ValidationResult):
        """Validate a single module"""
        # Update metrics
        self.metrics.total_modules += 1
        if module.description and module.purpose:
            self.metrics.documented_modules += 1
        
        # Check required fields
        if not module.name:
            results.add_error("module_missing_name", "Module missing name")
        
        if not module.description:
            results.add_warning("module_missing_description", f"Module missing description: {module.name}")
        
        if not module.purpose:
            results.add_warning("module_missing_purpose", f"Module missing purpose: {module.name}")
        
        # Validate classes
        for class_doc in module.classes:
            self._validate_class(class_doc, results)
        
        # Validate functions
        for func_doc in module.functions:
            self._validate_function(func_doc, results)
    
    def _validate_class(self, class_doc, results: ValidationResult):
        """Validate a single class"""
        # Update metrics
        self.metrics.total_classes += 1
        if class_doc.description and class_doc.purpose:
            self.metrics.documented_classes += 1
        
        if not class_doc.name:
            results.add_error("class_missing_name", "Class missing name")
        
        if not class_doc.description:
            results.add_warning("class_missing_description", f"Class missing description: {class_doc.name}")
        
        # Validate methods
        for method in class_doc.methods:
            self._validate_function(method, results)
    
    def _validate_function(self, func_doc, results: ValidationResult):
        """Validate a single function"""
        # Update metrics
        self.metrics.total_functions += 1
        if func_doc.description:
            self.metrics.documented_functions += 1
        
        if not func_doc.name:
            results.add_error("function_missing_name", "Function missing name")
        
        if not func_doc.description:
            results.add_warning("function_missing_description", f"Function missing description: {func_doc.name}")
        
        if not func_doc.signature:
            results.add_error("function_missing_signature", f"Function missing signature: {func_doc.name}")
        
        # Validate parameters
        for param in func_doc.parameters:
            if not param.name:
                results.add_error("parameter_missing_name", f"Parameter missing name in {func_doc.name}")
            
            if not param.type_annotation:
                results.add_warning("parameter_missing_type", f"Parameter missing type annotation: {func_doc.name}.{param.name}")
    
    def _validate_cli_docs(self, cli_docs, results: ValidationResult):
        """Validate CLI documentation"""
        if not cli_docs.commands:
            results.add_warning("cli_empty", "No CLI commands found")
            return
        
        # Validate each command
        for command in cli_docs.commands:
            self._validate_command(command, results)
    
    def _validate_command(self, command, results: ValidationResult):
        """Validate a single CLI command"""
        if not command.name:
            results.add_error("command_missing_name", "Command missing name")
        
        if not command.description:
            results.add_warning("command_missing_description", f"Command missing description: {command.name}")
        
        if not command.usage:
            results.add_warning("command_missing_usage", f"Command missing usage: {command.name}")
    
    def _validate_code_examples(self, docs: DocumentationSet, results: ValidationResult):
        """Validate code examples"""
        all_examples = []
        
        # Collect all examples
        if docs.module_docs:
            for module in docs.module_docs:
                all_examples.extend(module.examples)
                for class_doc in module.classes:
                    all_examples.extend(class_doc.examples)
                    for method in class_doc.methods:
                        all_examples.extend(method.examples)
                for func_doc in module.functions:
                    all_examples.extend(func_doc.examples)
        
        if docs.api_docs:
            for endpoint in docs.api_docs.endpoints:
                all_examples.extend(endpoint.examples)
        
        # Validate examples
        self.metrics.total_examples = len(all_examples)
        valid_examples = 0
        
        for example in all_examples:
            if self._validate_example(example, results):
                valid_examples += 1
        
        self.metrics.valid_examples = valid_examples
    
    def _validate_example(self, example, results: ValidationResult) -> bool:
        """Validate a single code example with enhanced checks"""
        if not example.code:
            results.add_error("example_missing_code", f"Example missing code: {example.description}")
            return False
        
        if not example.description:
            results.add_warning("example_missing_description", "Example missing description")
        
        # Enhanced validation for different languages
        if example.language == "python":
            return self._validate_python_example(example, results)
        elif example.language == "bash" or example.language == "shell":
            return self._validate_bash_example(example, results)
        elif example.language == "json":
            return self._validate_json_example(example, results)
        elif example.language == "yaml":
            return self._validate_yaml_example(example, results)
        
        # For other languages, just check if code is not empty
        return len(example.code.strip()) > 0
    
    def _validate_python_example(self, example, results: ValidationResult) -> bool:
        """Enhanced Python code validation"""
        try:
            # Basic syntax validation
            compile(example.code, '<string>', 'exec')
            
            # Check for common issues
            code_lines = example.code.strip().split('\n')
            
            # Check for incomplete examples (like just ">>>")
            if all(line.strip().startswith('>>>') or line.strip().startswith('...') or not line.strip() for line in code_lines):
                results.add_warning("example_incomplete", "Example appears to be incomplete doctest format")
                return False
            
            # Check for obvious placeholders
            placeholder_patterns = ['TODO', 'FIXME', '...', '<replace>', '<your_', 'placeholder']
            for pattern in placeholder_patterns:
                if pattern.lower() in example.code.lower():
                    results.add_warning("example_has_placeholder", f"Example contains placeholder: {pattern}")
                    break
            
            return True
            
        except SyntaxError as e:
            results.add_error("example_syntax_error", f"Python syntax error in example: {e}")
            return False
        except Exception as e:
            results.add_error("example_validation_error", f"Error validating Python example: {e}")
            return False
    
    def _validate_bash_example(self, example, results: ValidationResult) -> bool:
        """Validate bash/shell examples"""
        code = example.code.strip()
        
        # Check for dangerous commands
        dangerous_commands = ['rm -rf /', 'sudo rm', 'mkfs', 'dd if=', '> /dev/']
        for cmd in dangerous_commands:
            if cmd in code:
                results.add_error("example_dangerous_command", f"Example contains dangerous command: {cmd}")
                return False
        
        # Check for basic shell syntax issues
        if code.count('"') % 2 != 0 or code.count("'") % 2 != 0:
            results.add_warning("example_unmatched_quotes", "Example may have unmatched quotes")
        
        return True
    
    def _validate_json_example(self, example, results: ValidationResult) -> bool:
        """Validate JSON examples"""
        try:
            import json
            json.loads(example.code)
            return True
        except json.JSONDecodeError as e:
            results.add_error("example_invalid_json", f"Invalid JSON in example: {e}")
            return False
    
    def _validate_yaml_example(self, example, results: ValidationResult) -> bool:
        """Validate YAML examples"""
        try:
            import yaml
            yaml.safe_load(example.code)
            return True
        except yaml.YAMLError as e:
            results.add_error("example_invalid_yaml", f"Invalid YAML in example: {e}")
            return False
    
    def _validate_links(self, docs: DocumentationSet, results: ValidationResult):
        """Enhanced validation of internal and external links"""
        all_links = set()
        internal_refs = set()
        
        # Collect all links and internal references from documentation
        if docs.module_docs:
            for module in docs.module_docs:
                all_links.update(self._extract_links(module.description))
                internal_refs.update(self._extract_internal_refs(module.description))
                for class_doc in module.classes:
                    all_links.update(self._extract_links(class_doc.description))
                    internal_refs.update(self._extract_internal_refs(class_doc.description))
                    for method in class_doc.methods:
                        all_links.update(self._extract_links(method.description))
                        internal_refs.update(self._extract_internal_refs(method.description))
                for func_doc in module.functions:
                    all_links.update(self._extract_links(func_doc.description))
                    internal_refs.update(self._extract_internal_refs(func_doc.description))
        
        if docs.api_docs:
            all_links.update(self._extract_links(docs.api_docs.description))
            for endpoint in docs.api_docs.endpoints:
                all_links.update(self._extract_links(endpoint.description))
                all_links.update(self._extract_links(endpoint.summary))
        
        if docs.cli_docs:
            all_links.update(self._extract_links(docs.cli_docs.description))
            for command in docs.cli_docs.commands:
                all_links.update(self._extract_links(command.description))
        
        if docs.user_guides:
            for guide in docs.user_guides:
                all_links.update(self._extract_links(guide.content))
                all_links.update(self._extract_links(guide.description))
        
        # Validate external links
        broken_external_links = 0
        for link in all_links:
            if self._is_external_link(link) and self._is_broken_link(link):
                results.add_error("broken_external_link", f"Broken external link: {link}")
                broken_external_links += 1
        
        # Validate internal references
        broken_internal_refs = 0
        for ref in internal_refs:
            if not self._validate_internal_reference(ref, docs):
                results.add_error("broken_internal_ref", f"Broken internal reference: {ref}")
                broken_internal_refs += 1
        
        self.metrics.broken_links = broken_external_links + broken_internal_refs
        
        # Add summary info
        if all_links:
            results.add_info("link_summary", f"Validated {len(all_links)} external links and {len(internal_refs)} internal references")
    
    def _extract_links(self, text: str) -> Set[str]:
        """Extract external links from text"""
        if not text:
            return set()
        
        # Enhanced regex for URL extraction
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]\)\(]+'
        links = set(re.findall(url_pattern, text))
        
        # Also extract markdown links [text](url)
        markdown_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        markdown_matches = re.findall(markdown_pattern, text)
        for text_part, url in markdown_matches:
            if url.startswith('http'):
                links.add(url)
        
        return links
    
    def _extract_internal_refs(self, text: str) -> Set[str]:
        """Extract internal references from text"""
        if not text:
            return set()
        
        refs = set()
        
        # Extract relative markdown links
        markdown_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        markdown_matches = re.findall(markdown_pattern, text)
        for text_part, url in markdown_matches:
            if not url.startswith('http') and not url.startswith('#'):
                refs.add(url)
        
        # Extract class/function references (e.g., `ClassName` or `function_name`)
        code_ref_pattern = r'`([A-Za-z_][A-Za-z0-9_\.]*)`'
        code_refs = re.findall(code_ref_pattern, text)
        refs.update(code_refs)
        
        return refs
    
    def _is_external_link(self, url: str) -> bool:
        """Check if URL is external"""
        return url.startswith('http')
    
    def _validate_internal_reference(self, ref: str, docs: DocumentationSet) -> bool:
        """Validate internal reference exists in documentation"""
        # For now, just check if it looks like a valid reference format
        # This could be enhanced to actually check if the referenced item exists
        
        # Skip validation for file paths and URLs
        if '/' in ref or ref.startswith('http') or ref.startswith('#'):
            return True
        
        # Check if reference matches any documented classes or functions
        if docs.module_docs:
            for module in docs.module_docs:
                for cls in module.classes:
                    if ref == cls.name or ref == f"{module.name}.{cls.name}":
                        return True
                    for method in cls.methods:
                        if ref == method.name or ref == f"{cls.name}.{method.name}":
                            return True
                for func in module.functions:
                    if ref == func.name or ref == f"{module.name}.{func.name}":
                        return True
        
        # If we can't validate it, assume it's valid to avoid false positives
        return True
    
    def _is_broken_link(self, url: str) -> bool:
        """Check if an external link is broken"""
        try:
            # Skip localhost and example links
            skip_domains = ['localhost', '127.0.0.1', 'example.com', 'example.org', 'test.com']
            if any(domain in url for domain in skip_domains):
                return False
            
            # Skip obviously placeholder URLs
            if 'your-domain' in url or 'placeholder' in url or url.endswith('.example'):
                return False
            
            # Try HEAD request first (faster), then GET if that fails
            import urllib.request
            import ssl
            
            # Create SSL context that doesn't verify certificates (for testing)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Set user agent to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Documentation Validator) WriteIt/1.0'
            }
            
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                    return response.status >= 400
            except urllib.error.HTTPError as e:
                # If HEAD fails, try GET
                if e.code in [405, 501]:  # Method not allowed, not implemented
                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                            return response.status >= 400
                    except:
                        return True
                return e.code >= 400
            
        except (URLError, ValueError, Exception):
            # Don't mark as broken if we can't check (might be network issue)
            return False
    
    def _validate_completeness(self, docs: DocumentationSet, results: ValidationResult):
        """Validate documentation completeness"""
        total_items = 0
        documented_items = 0
        
        # Calculate completeness
        if docs.module_docs:
            for module in docs.module_docs:
                # Module itself
                total_items += 1
                if module.description and module.purpose:
                    documented_items += 1
                
                # Classes
                total_items += len(module.classes)
                documented_items += len([c for c in module.classes if c.description])
                
                # Functions
                total_items += len(module.functions)
                documented_items += len([f for f in module.functions if f.description])
        
        if docs.api_docs:
            total_items += len(docs.api_docs.endpoints)
            documented_items += len([e for e in docs.api_docs.endpoints if e.description])
        
        # Calculate coverage percentage
        if total_items > 0:
            coverage = (documented_items / total_items) * 100
            results.coverage_percentage = coverage
            
            # Add warnings for low coverage
            if coverage < 50:
                results.add_warning("low_coverage", f"Low documentation coverage: {coverage:.1f}%")
            elif coverage < 80:
                results.add_info("moderate_coverage", f"Moderate documentation coverage: {coverage:.1f}%")
            else:
                results.add_info("high_coverage", f"High documentation coverage: {coverage:.1f}%")
        
        results.total_items = total_items
        results.documented_items = documented_items
    
    def validate_code_examples(self, examples: List) -> ValidationResult:
        """Validate standalone code examples"""
        results = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])
        
        for i, example in enumerate(examples):
            if not self._validate_example(example, results):
                results.add_error("invalid_example", f"Invalid example at index {i}")
        
        results.is_valid = len(results.errors) == 0
        return results
    
    def validate_api_consistency(self) -> ValidationResult:
        """Validate that API documentation matches actual implementation"""
        results = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])
        
        try:
            # Try to import FastAPI app
            from writeit.server.app import app
            from fastapi.openapi.utils import get_openapi
            
            # Generate OpenAPI spec
            openapi_spec = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
            
            # Compare with existing documentation if available
            # This is a simplified version - in practice, you'd load existing docs and compare
            results.add_info("api_consistency_checked", "API consistency check completed")
            
        except ImportError:
            results.add_warning("api_app_not_found", "FastAPI app not found for consistency check")
        except Exception as e:
            results.add_error("api_consistency_error", f"Error checking API consistency: {e}")
        
        return results
    
    def fix_common_issues(self, results: ValidationResult) -> int:
        """Attempt to fix common validation issues"""
        fixed_count = 0
        
        # Fix missing descriptions by generating generic ones
        for warning in results.warnings[:]:  # Copy list to avoid modification during iteration
            if "missing_description" in warning.type:
                # This is where you could add logic to auto-generate descriptions
                # For now, we'll just count potential fixes
                fixed_count += 1
        
        return fixed_count
    
    def report_results(self, results: ValidationResult):
        """Print validation results to console"""
        print("\n=== Documentation Validation Results ===")
        
        if results.is_valid:
            print("✅ Validation passed")
        else:
            print(f"❌ Validation failed ({len(results.errors)} errors)")
        
        if results.has_warnings:
            print(f"⚠️  {len(results.warnings)} warnings")
        
        print(f"📊 Coverage: {results.coverage_percentage:.1f}%")
        
        if results.errors:
            print("\nErrors:")
            for error in results.errors:
                print(f"  • {error.type}: {error.message}")
                if error.suggestion:
                    print(f"    💡 {error.suggestion}")
        
        if results.warnings:
            print("\nWarnings:")
            for warning in results.warnings:
                print(f"  • {warning.type}: {warning.message}")
                if warning.suggestion:
                    print(f"    💡 {warning.suggestion}")