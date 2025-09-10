# ABOUTME: Unit tests for PipelineValidator class
# ABOUTME: Tests YAML parsing, structure validation, and variable reference checking
import pytest
import yaml
import tempfile
from pathlib import Path
from writeit.validation import PipelineValidator, ValidationResult, IssueType


class TestPipelineValidator:
    """Test cases for PipelineValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PipelineValidator()
    
    def create_temp_yaml_file(self, content: dict) -> Path:
        """Create temporary YAML file with given content."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(content, temp_file, default_flow_style=False)
        temp_file.close()
        return Path(temp_file.name)
    
    def test_valid_pipeline_passes_validation(self):
        """Test that a valid pipeline passes validation."""
        valid_pipeline = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'A test pipeline',
                'version': '1.0.0',
                'author': 'Test Author'
            },
            'inputs': {
                'topic': {
                    'type': 'string',
                    'description': 'Article topic',
                    'required': True
                }
            },
            'steps': {
                'plan': {
                    'type': 'llm_generation',
                    'description': 'Create article plan',
                    'model_preference': ['gpt-4'],
                    'prompt_template': 'Create a plan for {{ inputs.topic }}',
                    'response_count': 3
                },
                'select_plan': {
                    'type': 'user_selection',
                    'from_step': 'plan',
                    'description': 'Select the best plan'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(valid_pipeline)
        result = self.validator.validate_file(file_path)
        
        assert result.is_valid
        assert len(result.issues) == 0
        assert result.metadata['step_count'] == 2
        assert result.metadata['llm_step_count'] == 1
        
        # Clean up
        file_path.unlink()
    
    def test_missing_required_keys_fails_validation(self):
        """Test that missing required keys cause validation failure."""
        invalid_pipeline = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Missing other fields'
            }
            # Missing 'inputs' and 'steps'
        }
        
        file_path = self.create_temp_yaml_file(invalid_pipeline)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        assert result.has_errors
        
        # Should have errors for missing inputs and steps
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('inputs' in msg for msg in error_messages)
        assert any('steps' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_invalid_yaml_syntax_fails_validation(self):
        """Test that invalid YAML syntax is caught."""
        # Create file with invalid YAML
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_file.write("invalid: yaml: content:\n  - missing\n    indentation")
        temp_file.close()
        
        file_path = Path(temp_file.name)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        assert result.has_errors
        assert any('YAML syntax' in issue.message for issue in result.issues)
        
        # Clean up
        file_path.unlink()
    
    def test_missing_metadata_fields_detected(self):
        """Test that missing metadata fields are detected."""
        pipeline_missing_metadata = {
            'metadata': {
                'name': 'Test Pipeline'
                # Missing description, version, author
            },
            'inputs': {},
            'steps': {
                'test': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Test prompt'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_missing_metadata)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have errors for missing metadata fields
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('description' in msg for msg in error_messages)
        assert any('version' in msg for msg in error_messages)
        assert any('author' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_invalid_step_type_detected(self):
        """Test that invalid step types are detected."""
        pipeline_invalid_step = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {},
            'steps': {
                'invalid_step': {
                    'type': 'invalid_type',  # Invalid step type
                    'description': 'Invalid step'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_step)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have error for invalid step type
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('invalid type' in msg.lower() for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_missing_llm_step_fields_detected(self):
        """Test that missing required fields in LLM steps are detected."""
        pipeline_missing_llm_fields = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {},
            'steps': {
                'incomplete_llm': {
                    'type': 'llm_generation'
                    # Missing description, model_preference, prompt_template
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_missing_llm_fields)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have errors for missing LLM fields
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('description' in msg for msg in error_messages)
        assert any('model_preference' in msg for msg in error_messages)
        assert any('prompt_template' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_invalid_variable_references_detected(self):
        """Test that invalid variable references are detected."""
        pipeline_invalid_vars = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {
                'topic': {'type': 'string'}
            },
            'steps': {
                'step1': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Using {{ inputs.nonexistent }} and {{ steps.future_step.response }}'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_vars)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have errors for invalid variable references
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('nonexistent' in msg for msg in error_messages)
        assert any('future_step' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_selection_step_validation(self):
        """Test validation of user selection steps."""
        pipeline_invalid_selection = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {},
            'steps': {
                'select_step': {
                    'type': 'user_selection'
                    # Missing from_step
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_selection)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have error for missing from_step
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('from_step' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_step_dependency_validation(self):
        """Test validation of step dependency order."""
        pipeline_invalid_deps = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {},
            'steps': {
                'select_step': {
                    'type': 'user_selection',
                    'from_step': 'later_step'  # References step that comes later
                },
                'later_step': {
                    'type': 'llm_generation',
                    'description': 'Later step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Test'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_deps)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have error for forward reference
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('comes after' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_nonexistent_file_validation(self):
        """Test validation of nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.yaml")
        result = self.validator.validate_file(nonexistent_path)
        
        assert not result.is_valid
        assert result.has_errors
        assert any('not found' in issue.message for issue in result.issues)
    
    def test_input_type_validation(self):
        """Test validation of input types."""
        pipeline_invalid_input = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {
                'bad_input': {
                    'type': 'invalid_type'  # Invalid input type
                },
                'choice_input': {
                    'type': 'choice'
                    # Missing options for choice type
                }
            },
            'steps': {
                'test': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Test'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_input)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have warnings/errors for input validation
        issues = [issue.message for issue in result.issues]
        assert any('invalid_type' in msg for msg in issues)
        assert any('options' in msg for msg in issues)
        
        # Clean up
        file_path.unlink()
    
    def test_response_count_validation(self):
        """Test validation of response count in LLM steps."""
        pipeline_invalid_count = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {},
            'steps': {
                'bad_count': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Test',
                    'response_count': -1  # Invalid count
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_count)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have error for invalid response count
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('positive integer' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()
    
    def test_defaults_variables_recognized(self):
        """Test that defaults.* variables are recognized as valid."""
        pipeline_with_defaults = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test with defaults',
                'version': '1.0.0',
                'author': 'Test'
            },
            'defaults': {
                'models': {
                    'primary': 'gpt-4',
                    'secondary': 'claude-3'
                },
                'word_count': '1000 words',
                'nested': {
                    'deep': {
                        'value': 'test'
                    }
                }
            },
            'inputs': {
                'topic': {'type': 'string'}
            },
            'steps': {
                'step1': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': ['{{ defaults.models.primary }}', '{{ defaults.models.secondary }}'],
                    'prompt_template': 'Topic: {{ inputs.topic }}, Length: {{ defaults.word_count }}, Deep: {{ defaults.nested.deep.value }}'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_with_defaults)
        result = self.validator.validate_file(file_path)
        
        # Should be valid - all variable references should be recognized
        if not result.is_valid:
            print(f"Validation errors: {[issue.message for issue in result.issues if issue.is_error]}")
        
        assert result.is_valid
        
        # Clean up
        file_path.unlink()
    
    def test_global_variables_recognized(self):
        """Test that global.* variables are recognized as valid."""
        pipeline_with_global = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test with global variables',
                'version': '1.0.0',
                'author': 'Test'
            },
            'global': {
                'config': {
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                'style': {
                    'tone': 'professional'
                }
            },
            'inputs': {
                'topic': {'type': 'string'}
            },
            'steps': {
                'step1': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Topic: {{ inputs.topic }}, Tone: {{ global.style.tone }}, Temp: {{ global.config.temperature }}'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_with_global)
        result = self.validator.validate_file(file_path)
        
        # Should be valid - all variable references should be recognized
        if not result.is_valid:
            print(f"Validation errors: {[issue.message for issue in result.issues if issue.is_error]}")
        
        assert result.is_valid
        
        # Clean up
        file_path.unlink()
    
    def test_invalid_defaults_variables_detected(self):
        """Test that invalid defaults.* variables are still detected as errors."""
        pipeline_invalid_defaults = {
            'metadata': {
                'name': 'Test Pipeline',
                'description': 'Test with invalid defaults variables',
                'version': '1.0.0',
                'author': 'Test'
            },
            'defaults': {
                'models': {
                    'primary': 'gpt-4'
                }
            },
            'inputs': {
                'topic': {'type': 'string'}
            },
            'steps': {
                'step1': {
                    'type': 'llm_generation',
                    'description': 'Test step',
                    'model_preference': 'gpt-4',
                    'prompt_template': 'Using {{ defaults.models.nonexistent }} and {{ defaults.missing.field }}'
                }
            }
        }
        
        file_path = self.create_temp_yaml_file(pipeline_invalid_defaults)
        result = self.validator.validate_file(file_path)
        
        assert not result.is_valid
        
        # Should have errors for invalid variable references
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any('nonexistent' in msg for msg in error_messages)
        assert any('missing.field' in msg for msg in error_messages)
        
        # Clean up
        file_path.unlink()