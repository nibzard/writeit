"""
Module documentation extractor from Python source code
"""

import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from ..models import (
    ModuleDocumentation,
    ClassDocumentation,
    FunctionDocumentation,
    ParameterDocumentation,
    CodeExample
)


class ModuleExtractor:
    """Extract module documentation from source code"""
    
    def extract_module(self, module_path: Path) -> Optional[ModuleDocumentation]:
        """Extract complete module documentation"""
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            module_doc = ModuleDocumentation(
                name=self._get_module_name(module_path),
                description=self._extract_module_docstring(tree),
                purpose=self._extract_module_purpose(tree, source_code),
                classes=[],
                functions=[],
                dependencies=self._extract_dependencies(tree),
                source_file=module_path
            )
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_doc = self._extract_class(node, module_path)
                    if class_doc:
                        module_doc.classes.append(class_doc)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Only extract top-level functions
                    if self._is_top_level_function(node, tree):
                        func_doc = self._extract_function(node, module_path)
                        if func_doc:
                            module_doc.functions.append(func_doc)
            
            # Extract examples
            module_doc.examples = self._extract_examples(tree, source_code)
            
            return module_doc
        
        except Exception as e:
            print(f"Error extracting module docs from {module_path}: {e}")
            return None
    
    def extract_class(self, cls: type) -> Optional[ClassDocumentation]:
        """Extract documentation for a specific class"""
        try:
            source_file = Path(inspect.getfile(cls))
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Find the class node
            class_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
                    class_node = node
                    break
            
            if not class_node:
                return None
            
            return self._extract_class(class_node, source_file)
        
        except Exception as e:
            print(f"Error extracting class docs for {cls.__name__}: {e}")
            return None
    
    def _get_module_name(self, module_path: Path) -> str:
        """Get module name from file path"""
        try:
            # Convert path to module name
            relative_path = module_path.relative_to(Path("src/writeit"))
            module_name = str(relative_path.with_suffix("")).replace("/", ".")
            return module_name
        except ValueError:
            return module_path.stem
    
    def _extract_module_docstring(self, tree: ast.AST) -> str:
        """Extract module docstring"""
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            return tree.body[0].value.value
        return ""
    
    def _extract_module_purpose(self, tree: ast.AST, source_code: str) -> str:
        """Extract module purpose from docstring or comments"""
        docstring = self._extract_module_docstring(tree)
        if docstring:
            # Extract the first line or first sentence
            lines = docstring.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line:
                    return first_line
        
        # Look for ABOUTME comments
        for line in source_code.split('\n'):
            if "ABOUTME:" in line:
                return line.split("ABOUTME:")[1].strip()
        
        return ""
    
    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        """Extract module dependencies from import statements"""
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
        
        return list(set(dependencies))
    
    def _extract_class(self, node: ast.ClassDef, source_file: Path) -> Optional[ClassDocumentation]:
        """Extract class documentation"""
        docstring = ast.get_docstring(node)
        if not docstring:
            return None
        
        class_doc = ClassDocumentation(
            name=node.name,
            description=docstring,
            purpose=self._extract_class_purpose(docstring),
            methods=[],
            class_variables={},
            inheritance=self._extract_inheritance(node),
            source_file=source_file,
            line_number=node.lineno
        )
        
        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_doc = self._extract_function(item, source_file)
                if method_doc:
                    class_doc.methods.append(method_doc)
        
        # Extract class variables
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                class_doc.class_variables[item.target.id] = self._get_type_annotation(item.annotation)
        
        return class_doc
    
    def _extract_class_purpose(self, docstring: str) -> str:
        """Extract class purpose from docstring"""
        lines = docstring.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(':'):
                return line
        return ""
    
    def _extract_inheritance(self, node: ast.ClassDef) -> List[str]:
        """Extract class inheritance hierarchy"""
        inheritance = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                inheritance.append(base.id)
            elif isinstance(base, ast.Attribute):
                inheritance.append(self._get_attribute_name(base))
        return inheritance
    
    def _extract_function(self, node: ast.FunctionDef, source_file: Path) -> Optional[FunctionDocumentation]:
        """Extract function documentation"""
        docstring = ast.get_docstring(node)
        if not docstring and not self._is_public_method(node):
            return None
        
        func_doc = FunctionDocumentation(
            name=node.name,
            signature=self._get_function_signature(node),
            description=docstring or "",
            parameters=self._extract_parameters(node),
            return_type=self._get_return_type(node),
            return_description=self._extract_return_description(docstring),
            source_file=source_file,
            line_number=node.lineno
        )
        
        # Extract examples from docstring
        if docstring:
            func_doc.examples = self._extract_function_examples(docstring)
        
        return func_doc
    
    def _is_public_method(self, node: ast.FunctionDef) -> bool:
        """Check if function/method is public"""
        return not node.name.startswith('_')
    
    def _is_top_level_function(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is top-level (not inside a class)"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return False
        return True
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature"""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_type_annotation(arg.annotation)}"
            args.append(arg_str)
        
        signature = f"{node.name}({', '.join(args)})"
        
        if node.returns:
            signature += f" -> {self._get_type_annotation(node.returns)}"
        
        return signature
    
    def _extract_parameters(self, node: ast.FunctionDef) -> List[ParameterDocumentation]:
        """Extract function parameters"""
        parameters = []
        
        for arg in node.args.args:
            param_doc = ParameterDocumentation(
                name=arg.arg,
                type_annotation=self._get_type_annotation(arg.annotation),
                description=self._extract_parameter_description(arg.arg, ast.get_docstring(node)),
                default_value=self._get_default_value(arg.arg, node),
                required=arg.arg not in [a.arg for a in node.args.defaults]
            )
            parameters.append(param_doc)
        
        return parameters
    
    def _get_type_annotation(self, annotation) -> str:
        """Convert AST type annotation to string"""
        if annotation is None:
            return "Any"
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_name(annotation)
        elif isinstance(annotation, ast.Subscript):
            value = self._get_type_annotation(annotation.value)
            slice_val = self._get_type_annotation(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        
        return "Any"
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name (e.g., module.ClassName)"""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
    
    def _get_default_value(self, arg_name: str, node: ast.FunctionDef) -> Optional[str]:
        """Get default value for parameter"""
        try:
            defaults_start = len(node.args.args) - len(node.args.defaults)
            arg_index = None
            
            for i, arg in enumerate(node.args.args):
                if arg.arg == arg_name:
                    arg_index = i
                    break
            
            if arg_index is not None and arg_index >= defaults_start:
                default_index = arg_index - defaults_start
                default_node = node.args.defaults[default_index]
                
                if isinstance(default_node, ast.Constant):
                    return repr(default_node.value)
                elif isinstance(default_node, ast.Name):
                    return default_node.id
                elif isinstance(default_node, ast.List):
                    return "[]"
                elif isinstance(default_node, ast.Dict):
                    return "{}"
                
                return ast.unparse(default_node)
        except (IndexError, AttributeError):
            pass
        
        return None
    
    def _extract_parameter_description(self, param_name: str, docstring: str) -> str:
        """Extract parameter description from docstring"""
        if not docstring:
            return ""
        
        lines = docstring.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(f':param {param_name}:'):
                return line.split(f':param {param_name}:', 1)[1].strip()
            elif line.startswith(f':param {param_name} '):
                return line.split(f':param {param_name} ', 1)[1].strip()
        
        return ""
    
    def _get_return_type(self, node: ast.FunctionDef) -> str:
        """Get return type annotation"""
        if node.returns:
            return self._get_type_annotation(node.returns)
        return "Any"
    
    def _extract_return_description(self, docstring: str) -> str:
        """Extract return description from docstring"""
        if not docstring:
            return ""
        
        lines = docstring.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(':return:') or line.startswith(':returns:'):
                return line.split(':', 2)[2].strip()
        
        return ""
    
    def _extract_function_examples(self, docstring: str) -> List[CodeExample]:
        """Extract code examples from function docstring"""
        examples = []
        
        lines = docstring.split('\n')
        in_example = False
        example_lines = []
        example_description = ""
        
        for line in lines:
            if line.strip().startswith('>>>') or line.strip().startswith('...'):
                if not in_example:
                    in_example = True
                    example_lines = []
                example_lines.append(line)
            elif in_example and line.strip() == '':
                continue
            elif in_example:
                if example_lines:
                    examples.append(CodeExample(
                        code='\n'.join(example_lines),
                        description=example_description,
                        language="python"
                    ))
                in_example = False
                example_lines = []
                example_description = ""
            elif line.strip().startswith('Example:'):
                example_description = line.split('Example:')[1].strip()
        
        # Handle example at end of docstring
        if in_example and example_lines:
            examples.append(CodeExample(
                code='\n'.join(example_lines),
                description=example_description,
                language="python"
            ))
        
        return examples
    
    def _extract_examples(self, tree: ast.AST, source_code: str) -> List[CodeExample]:
        """Extract examples from module"""
        examples = []
        
        # Look for doctest examples
        docstrings = []
        for node in ast.walk(tree):
            if hasattr(node, 'body'):
                for item in node.body:
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant):
                        if isinstance(item.value.value, str):
                            docstrings.append(item.value.value)
        
        for docstring in docstrings:
            examples.extend(self._extract_function_examples(docstring))
        
        return examples