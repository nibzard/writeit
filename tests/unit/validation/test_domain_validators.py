"""Tests for domain-specific validators."""

import tempfile
from pathlib import Path

import pytest

from writeit.shared.validation import ValidationContext
from writeit.shared.validation.domain_validators import (
    ConfigurationValueValidator,
    FilePathValidator,
    PipelineTemplateValidator,
    WorkspaceValidator,
    YAMLContentValidator,
)


class TestPipelineTemplateValidator:
    """Test PipelineTemplateValidator."""
    
    def test_valid_pipeline_template(self):
        validator = PipelineTemplateValidator()
        valid_template = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "1.0.0"
            },
            "steps": {
                "step1": {
                    "name": "First Step",
                    "type": "llm_generate",
                    "prompt_template": "Generate content about {{topic}}"
                }
            }
        }
        
        result = validator.validate(valid_template, ValidationContext())
        assert result.is_valid
    
    def test_missing_required_fields(self):
        validator = PipelineTemplateValidator()
        invalid_template = {
            "metadata": {
                "name": "Test Pipeline"
                # Missing description and version
            }
            # Missing steps
        }
        
        result = validator.validate(invalid_template, ValidationContext())
        assert not result.is_valid
        assert any("Missing required fields" in error for error in result.errors)
    
    def test_invalid_version_format(self):
        validator = PipelineTemplateValidator()
        invalid_template = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "invalid-version"
            },
            "steps": {}
        }
        
        result = validator.validate(invalid_template, ValidationContext())
        assert not result.is_valid
        assert any("semantic versioning" in error for error in result.errors)
    
    def test_invalid_step_type(self):
        validator = PipelineTemplateValidator()
        invalid_template = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline", 
                "version": "1.0.0"
            },
            "steps": {
                "step1": {
                    "name": "Invalid Step",
                    "type": "invalid_type"
                }
            }
        }
        
        result = validator.validate(invalid_template, ValidationContext())
        assert not result.is_valid
        assert any("invalid type" in error for error in result.errors)
    
    def test_missing_step_dependency(self):
        validator = PipelineTemplateValidator()
        invalid_template = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "1.0.0"
            },
            "steps": {
                "step1": {
                    "name": "First Step",
                    "type": "llm_generate",
                    "depends_on": ["missing_step"]
                }
            }
        }
        
        result = validator.validate(invalid_template, ValidationContext())
        assert not result.is_valid
        assert any("depends on unknown step" in error for error in result.errors)
    
    def test_invalid_input_configuration(self):
        validator = PipelineTemplateValidator()
        invalid_template = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "1.0.0"
            },
            "steps": {},
            "inputs": {
                "invalid_input": {
                    "type": "invalid_type"
                }
            }
        }
        
        result = validator.validate(invalid_template, ValidationContext())
        assert not result.is_valid
        assert any("invalid type" in error for error in result.errors)
    
    def test_choice_input_without_options(self):
        validator = PipelineTemplateValidator()
        invalid_template = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "1.0.0"
            },
            "steps": {},
            "inputs": {
                "choice_input": {
                    "type": "choice"
                    # Missing options
                }
            }
        }
        
        result = validator.validate(invalid_template, ValidationContext())
        assert not result.is_valid
        assert any("must have 'options'" in error for error in result.errors)
    
    def test_empty_steps_warning(self):
        validator = PipelineTemplateValidator()
        template_with_empty_steps = {
            "metadata": {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "1.0.0"
            },
            "steps": {}
        }
        
        result = validator.validate(template_with_empty_steps, ValidationContext())
        assert result.is_valid
        assert any("no steps defined" in warning for warning in result.warnings)


class TestWorkspaceValidator:
    """Test WorkspaceValidator."""
    
    def test_valid_workspace_name(self):
        validator = WorkspaceValidator()
        result = validator.validate("valid_workspace", ValidationContext())
        assert result.is_valid
    
    def test_workspace_name_with_hyphens(self):
        validator = WorkspaceValidator()
        result = validator.validate("valid-workspace-name", ValidationContext())
        assert result.is_valid
    
    def test_workspace_name_with_numbers(self):
        validator = WorkspaceValidator()
        result = validator.validate("workspace123", ValidationContext())
        assert result.is_valid
    
    def test_invalid_workspace_name_starts_with_number(self):
        validator = WorkspaceValidator()
        result = validator.validate("123workspace", ValidationContext())
        assert not result.is_valid
        assert any("must start with a letter" in error for error in result.errors)
    
    def test_invalid_workspace_name_special_chars(self):
        validator = WorkspaceValidator()
        result = validator.validate("workspace@name", ValidationContext())
        assert not result.is_valid
        assert any("only letters, numbers, underscores, and hyphens" in error for error in result.errors)
    
    def test_empty_workspace_name(self):
        validator = WorkspaceValidator()
        result = validator.validate("", ValidationContext())
        assert not result.is_valid
        assert any("at least 1 characters" in error for error in result.errors)
    
    def test_workspace_name_too_long(self):
        validator = WorkspaceValidator()
        long_name = "a" * 51  # Exceeds 50 character limit
        result = validator.validate(long_name, ValidationContext())
        assert not result.is_valid
        assert any("at most 50 characters" in error for error in result.errors)


class TestFilePathValidator:
    """Test FilePathValidator."""
    
    def test_valid_file_path(self):
        validator = FilePathValidator()
        result = validator.validate("valid/file/path.txt", ValidationContext())
        assert result.is_valid
    
    def test_path_traversal_attack(self):
        validator = FilePathValidator()
        result = validator.validate("../../../etc/passwd", ValidationContext())
        assert not result.is_valid
        assert any("path traversal" in error for error in result.errors)
    
    def test_absolute_path_not_allowed(self):
        validator = FilePathValidator()
        result = validator.validate("/absolute/path", ValidationContext())
        assert not result.is_valid
        assert any("path traversal" in error for error in result.errors)
    
    def test_base_path_restriction(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = FilePathValidator(base_path=temp_dir)
            
            # Valid path within base
            valid_path = Path(temp_dir) / "subdir" / "file.txt"
            valid_path.parent.mkdir(parents=True, exist_ok=True)
            valid_path.touch()
            
            result = validator.validate(str(valid_path), ValidationContext())
            assert result.is_valid
    
    def test_file_extension_validation(self):
        validator = FilePathValidator(allowed_extensions=[".txt", ".yaml"])
        
        # Valid extension
        result = validator.validate("file.txt", ValidationContext())
        assert result.is_valid
        
        # Invalid extension
        result = validator.validate("file.exe", ValidationContext())
        assert not result.is_valid
        assert any("not allowed" in error for error in result.errors)
    
    def test_must_exist_validation(self):
        validator = FilePathValidator(must_exist=True)
        
        # Non-existent file
        result = validator.validate("nonexistent/file.txt", ValidationContext())
        assert not result.is_valid
        assert any("does not exist" in error for error in result.errors)
        
        # Existing file
        with tempfile.NamedTemporaryFile() as temp_file:
            result = validator.validate(temp_file.name, ValidationContext())
            assert result.is_valid


class TestConfigurationValueValidator:
    """Test ConfigurationValueValidator."""
    
    def test_valid_type_string(self):
        validator = ConfigurationValueValidator(str)
        result = validator.validate("test_string", ValidationContext())
        assert result.is_valid
    
    def test_invalid_type(self):
        validator = ConfigurationValueValidator(str)
        result = validator.validate(123, ValidationContext())
        assert not result.is_valid
        assert any("must be of type str" in error for error in result.errors)
    
    def test_allowed_values(self):
        validator = ConfigurationValueValidator(str, allowed_values=["option1", "option2"])
        
        # Valid value
        result = validator.validate("option1", ValidationContext())
        assert result.is_valid
        
        # Invalid value
        result = validator.validate("option3", ValidationContext())
        assert not result.is_valid
        assert any("must be one of" in error for error in result.errors)
    
    def test_numeric_range_validation(self):
        validator = ConfigurationValueValidator(int, min_value=0, max_value=100)
        
        # Valid value
        result = validator.validate(50, ValidationContext())
        assert result.is_valid
        
        # Too low
        result = validator.validate(-1, ValidationContext())
        assert not result.is_valid
        assert any("must be at least 0" in error for error in result.errors)
        
        # Too high
        result = validator.validate(101, ValidationContext())
        assert not result.is_valid
        assert any("must be at most 100" in error for error in result.errors)
    
    def test_boolean_validation(self):
        validator = ConfigurationValueValidator(bool)
        
        result = validator.validate(True, ValidationContext())
        assert result.is_valid
        
        result = validator.validate(False, ValidationContext())
        assert result.is_valid
        
        result = validator.validate("true", ValidationContext())
        assert not result.is_valid
        assert any("must be of type bool" in error for error in result.errors)


class TestYAMLContentValidator:
    """Test YAMLContentValidator."""
    
    def test_valid_yaml(self):
        validator = YAMLContentValidator()
        valid_yaml = """
        name: test
        version: 1.0.0
        items:
          - item1
          - item2
        """
        
        result = validator.validate(valid_yaml, ValidationContext())
        assert result.is_valid
    
    def test_invalid_yaml_syntax(self):
        validator = YAMLContentValidator()
        invalid_yaml = """
        name: test
        version: 1.0.0
        items:
          - item1
          - item2
            invalid_indentation
        """
        
        result = validator.validate(invalid_yaml, ValidationContext())
        assert not result.is_valid
        assert any("Invalid YAML syntax" in error for error in result.errors)
    
    def test_empty_yaml(self):
        validator = YAMLContentValidator()
        result = validator.validate("", ValidationContext())
        
        assert result.is_valid
        assert any("empty" in warning for warning in result.warnings)
    
    def test_non_string_input(self):
        validator = YAMLContentValidator()
        result = validator.validate(123, ValidationContext())
        
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)
    
    def test_minimal_valid_yaml(self):
        validator = YAMLContentValidator()
        result = validator.validate("key: value", ValidationContext())
        assert result.is_valid