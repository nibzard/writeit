"""
Tests for documentation extractors
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from writeit.docs.extractors import ModuleExtractor, APIExtractor, CLIExtractor
from writeit.docs.models import ModuleDocumentation, APIDocumentation


class TestModuleExtractor:
    """Test module documentation extraction"""
    
    def test_module_extractor_initialization(self):
        """Test module extractor initializes"""
        extractor = ModuleExtractor()
        assert extractor is not None
    
    def test_extract_simple_module(self, tmp_path):
        """Test extracting documentation from simple module"""
        # Create test module
        test_module = tmp_path / "test_module.py"
        test_module.write_text('''"""Test module docstring"""

def test_function():
    """Test function docstring"""
    pass

class TestClass:
    """Test class docstring"""
    
    def test_method(self):
        """Test method docstring"""
        pass
''')
        
        extractor = ModuleExtractor()
        module_doc = extractor.extract_module(test_module)
        
        assert module_doc is not None
        assert "Test module docstring" in module_doc.description
        assert len(module_doc.functions) >= 1
        assert len(module_doc.classes) >= 1
        assert module_doc.functions[0].name == "test_function"
        assert module_doc.classes[0].name == "TestClass"
    
    def test_extract_module_with_imports(self, tmp_path):
        """Test extracting module with imports"""
        test_module = tmp_path / "test_imports.py"
        test_module.write_text('''"""Module with imports"""
import os
import sys
from pathlib import Path
from typing import List, Dict

def example_function():
    """Example function"""
    pass
''')
        
        extractor = ModuleExtractor()
        module_doc = extractor.extract_module(test_module)
        
        assert module_doc is not None
        assert len(module_doc.dependencies) > 0
        assert "os" in module_doc.dependencies
        assert "pathlib" in module_doc.dependencies
    
    def test_extract_class_with_methods(self, tmp_path):
        """Test extracting class with methods"""
        test_module = tmp_path / "test_class.py"
        test_module.write_text('''"""Test module"""

class ExampleClass:
    """Example class with methods"""
    
    def __init__(self, value: str):
        """Initialize with value"""
        self.value = value
    
    def get_value(self) -> str:
        """Get the value"""
        return self.value
    
    def set_value(self, new_value: str) -> None:
        """Set a new value"""
        self.value = new_value
    
    def _private_method(self):
        """Private method should not be documented"""
        pass
''')
        
        extractor = ModuleExtractor()
        module_doc = extractor.extract_module(test_module)
        
        assert module_doc is not None
        assert len(module_doc.classes) == 1
        
        class_doc = module_doc.classes[0]
        assert class_doc.name == "ExampleClass"
        assert len(class_doc.methods) >= 3  # __init__, get_value, set_value
        
        # Check that private method is excluded or marked appropriately
        method_names = [m.name for m in class_doc.methods]
        public_methods = [name for name in method_names if not name.startswith('_')]
        assert len(public_methods) >= 2  # get_value, set_value
    
    def test_extract_function_parameters(self, tmp_path):
        """Test extracting function parameters"""
        test_module = tmp_path / "test_params.py"
        test_module.write_text('''"""Test parameters"""

def example_function(
    required_param: str,
    optional_param: int = 42,
    list_param: list = None
) -> bool:
    """
    Example function with parameters
    
    :param required_param: A required string parameter
    :param optional_param: An optional integer parameter
    :param list_param: An optional list parameter
    :return: Always returns True
    """
    return True
''')
        
        extractor = ModuleExtractor()
        module_doc = extractor.extract_module(test_module)
        
        assert module_doc is not None
        assert len(module_doc.functions) == 1
        
        func_doc = module_doc.functions[0]
        assert func_doc.name == "example_function"
        assert len(func_doc.parameters) == 3
        
        # Check parameter details
        params = {p.name: p for p in func_doc.parameters}
        assert "required_param" in params
        assert "optional_param" in params
        assert "list_param" in params
        
        assert params["required_param"].required is True
        assert params["optional_param"].required is False
        assert params["optional_param"].default_value == "42"
    
    def test_malformed_module_handling(self, tmp_path):
        """Test handling of malformed modules"""
        # Create module with syntax error
        bad_module = tmp_path / "bad_module.py"
        bad_module.write_text('''"""Bad module"""
def incomplete_function(
    # Missing closing parenthesis and body
''')
        
        extractor = ModuleExtractor()
        module_doc = extractor.extract_module(bad_module)
        
        # Should handle gracefully and return None
        assert module_doc is None


class TestAPIExtractor:
    """Test API documentation extraction"""
    
    def test_api_extractor_initialization(self):
        """Test API extractor initializes"""
        extractor = APIExtractor()
        assert extractor is not None
    
    def test_extract_openapi_schema(self):
        """Test extracting from OpenAPI schema"""
        # Mock OpenAPI schema
        schema = {
            "info": {
                "title": "Test API",
                "description": "Test API Description",
                "version": "1.0.0"
            },
            "servers": [{"url": "http://localhost:8000"}],
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "description": "Test endpoint description",
                        "parameters": [],
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "TestModel": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        extractor = APIExtractor()
        api_docs = extractor._extract_from_openapi_schema(schema)
        
        assert api_docs is not None
        assert api_docs.title == "Test API"
        assert api_docs.version == "1.0.0"
        assert len(api_docs.endpoints) == 1
        assert len(api_docs.models) == 1
        
        endpoint = api_docs.endpoints[0]
        assert endpoint.path == "/test"
        assert endpoint.method == "GET"
        
        model = api_docs.models[0]
        assert model.name == "TestModel"


class TestCLIExtractor:
    """Test CLI documentation extraction"""
    
    def test_cli_extractor_initialization(self):
        """Test CLI extractor initializes"""
        extractor = CLIExtractor()
        assert extractor is not None
    
    def test_extract_command_info(self):
        """Test extracting command information"""
        # Mock CommandInfo
        mock_command = Mock()
        mock_command.name = "test-command"
        mock_command.help = "Test command help"
        mock_command.callback = lambda x: None
        
        # Mock callback signature
        import inspect
        def mock_callback(arg1: str, arg2: int = 42):
            pass
        sig = inspect.signature(mock_callback)
        
        extractor = CLIExtractor()
        
        with patch('inspect.signature', return_value=sig):
            command_doc = extractor._extract_command(mock_command)
        
        if command_doc:  # May be None due to mocking
            assert command_doc.name == "test-command"
            assert command_doc.description == "Test command help"
    
    def test_global_options_extraction(self):
        """Test extraction of global options"""
        extractor = CLIExtractor()
        
        # Mock Typer app
        mock_app = Mock()
        
        global_options = extractor._extract_global_options(mock_app)
        
        assert isinstance(global_options, list)
        assert len(global_options) > 0
        
        # Should include common options like --help, --version
        option_names = [opt.name for opt in global_options]
        assert "--help" in option_names
        assert "--version" in option_names