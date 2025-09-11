# ABOUTME: Unit tests for StyleValidator class
# ABOUTME: Tests YAML parsing, structure validation, and style primer consistency checks
import yaml
import tempfile
from pathlib import Path
from writeit.validation import StyleValidator


class TestStyleValidator:
    """Test cases for StyleValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StyleValidator()

    def create_temp_yaml_file(self, content: dict) -> Path:
        """Create temporary YAML file with given content."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(content, temp_file, default_flow_style=False)
        temp_file.close()
        return Path(temp_file.name)

    def test_valid_style_passes_validation(self):
        """Test that a valid style primer passes validation."""
        valid_style = {
            "metadata": {
                "name": "Test Style",
                "description": "A test style primer",
                "version": "1.0.0",
                "author": "Test Author",
                "category": "professional",
                "difficulty": "intermediate",
                "use_cases": ["Technical documentation", "Blog posts"],
            },
            "voice": {
                "personality": "Professional and approachable",
                "tone": "Confident yet friendly",
                "perspective": "Expert sharing knowledge",
                "characteristics": [
                    "Uses clear, direct language",
                    "Provides concrete examples",
                ],
            },
            "language": {
                "formality": "Professional but accessible",
                "preferred_words": {
                    "implement": "use instead of do",
                    "utilize": "use when appropriate",
                },
                "avoid": ["jargon without explanation", "overly casual terms"],
            },
            "structure": {
                "opening": {
                    "pattern": "Problem → Solution → Outcome",
                    "elements": ["Clear problem statement", "Proposed solution"],
                },
                "body_sections": {
                    "organization": "Logical flow",
                    "section_length": "200-400 words",
                },
                "conclusion": {
                    "pattern": "Summary → Action Items",
                    "elements": ["Key takeaways", "Next steps"],
                },
            },
        }

        file_path = self.create_temp_yaml_file(valid_style)
        result = self.validator.validate_file(file_path)

        assert result.is_valid
        assert len([issue for issue in result.issues if issue.is_error]) == 0
        assert result.metadata["has_voice_section"]
        assert result.metadata["section_count"] >= 3

        # Clean up
        file_path.unlink()

    def test_missing_required_keys_fails_validation(self):
        """Test that missing required keys cause validation failure."""
        invalid_style = {
            "metadata": {"name": "Test Style", "description": "Missing other fields"}
            # Missing 'voice', 'language', 'structure'
        }

        file_path = self.create_temp_yaml_file(invalid_style)
        result = self.validator.validate_file(file_path)

        assert not result.is_valid
        assert result.has_errors

        # Should have errors for missing required sections
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any("voice" in msg for msg in error_messages)
        assert any("language" in msg for msg in error_messages)
        assert any("structure" in msg for msg in error_messages)

        # Clean up
        file_path.unlink()

    def test_invalid_yaml_syntax_fails_validation(self):
        """Test that invalid YAML syntax is caught."""
        # Create file with invalid YAML
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        temp_file.write("invalid: yaml: content:\n  - missing\n    indentation")
        temp_file.close()

        file_path = Path(temp_file.name)
        result = self.validator.validate_file(file_path)

        assert not result.is_valid
        assert result.has_errors
        assert any("YAML syntax" in issue.message for issue in result.issues)

        # Clean up
        file_path.unlink()

    def test_missing_metadata_fields_detected(self):
        """Test that missing metadata fields are detected."""
        style_missing_metadata = {
            "metadata": {
                "name": "Test Style"
                # Missing description, version, author, category, difficulty
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_missing_metadata)
        result = self.validator.validate_file(file_path)

        assert not result.is_valid

        # Should have errors for missing metadata fields
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any("description" in msg for msg in error_messages)
        assert any("version" in msg for msg in error_messages)
        assert any("author" in msg for msg in error_messages)
        assert any("category" in msg for msg in error_messages)
        assert any("difficulty" in msg for msg in error_messages)

        # Clean up
        file_path.unlink()

    def test_invalid_category_detected(self):
        """Test that invalid categories are detected."""
        style_invalid_category = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "invalid_category",  # Invalid category
                "difficulty": "intermediate",
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_invalid_category)
        result = self.validator.validate_file(file_path)

        # Should have warning for invalid category
        warning_messages = [
            issue.message for issue in result.issues if issue.is_warning
        ]
        assert any("invalid_category" in msg for msg in warning_messages)

        # Clean up
        file_path.unlink()

    def test_invalid_difficulty_detected(self):
        """Test that invalid difficulty levels are detected."""
        style_invalid_difficulty = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "expert",  # Invalid difficulty
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_invalid_difficulty)
        result = self.validator.validate_file(file_path)

        # Should have warning for invalid difficulty
        warning_messages = [
            issue.message for issue in result.issues if issue.is_warning
        ]
        assert any("expert" in msg for msg in warning_messages)

        # Clean up
        file_path.unlink()

    def test_empty_voice_section_detected(self):
        """Test that empty voice section is detected."""
        style_empty_voice = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {},  # Empty voice section
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_empty_voice)
        result = self.validator.validate_file(file_path)

        assert not result.is_valid

        # Should have error for empty voice section
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any("empty voice section" in msg.lower() for msg in error_messages)

        # Clean up
        file_path.unlink()

    def test_empty_language_section_detected(self):
        """Test that empty language section is detected."""
        style_empty_language = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {"personality": "test"},
            "language": {},  # Empty language section
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_empty_language)
        result = self.validator.validate_file(file_path)

        assert not result.is_valid

        # Should have error for empty language section
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any("empty language section" in msg.lower() for msg in error_messages)

        # Clean up
        file_path.unlink()

    def test_empty_structure_section_detected(self):
        """Test that empty structure section is detected."""
        style_empty_structure = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {},  # Empty structure section
        }

        file_path = self.create_temp_yaml_file(style_empty_structure)
        result = self.validator.validate_file(file_path)

        assert not result.is_valid

        # Should have error for empty structure section
        error_messages = [issue.message for issue in result.issues if issue.is_error]
        assert any("empty structure section" in msg.lower() for msg in error_messages)

        # Clean up
        file_path.unlink()

    def test_voice_characteristics_validation(self):
        """Test validation of voice characteristics."""
        style_bad_characteristics = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {
                "personality": "test",
                "characteristics": "should be list",  # Should be list, not string
            },
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_bad_characteristics)
        result = self.validator.validate_file(file_path)

        # Should have warning about characteristics format
        warning_messages = [
            issue.message for issue in result.issues if issue.is_warning
        ]
        assert any("should be a list" in msg for msg in warning_messages)

        # Clean up
        file_path.unlink()

    def test_examples_validation(self):
        """Test validation of examples section."""
        style_with_examples = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
            "examples": {
                "empty_example": "",  # Empty example
                "short_example": "too short",  # Very short example
                "good_example": "This is a longer example that demonstrates the writing style properly with enough content to be meaningful and helpful to users.",
            },
        }

        file_path = self.create_temp_yaml_file(style_with_examples)
        result = self.validator.validate_file(file_path)

        # Should have warnings for empty and short examples
        warning_messages = [
            issue.message for issue in result.issues if issue.is_warning
        ]
        assert any("empty example" in msg.lower() for msg in warning_messages)

        info_messages = [issue.message for issue in result.issues if issue.is_info]
        assert any("quite short" in msg for msg in info_messages)

        # Clean up
        file_path.unlink()

    def test_nonexistent_file_validation(self):
        """Test validation of nonexistent file."""
        nonexistent_path = Path("/nonexistent/style.yaml")
        result = self.validator.validate_file(nonexistent_path)

        assert not result.is_valid
        assert result.has_errors
        assert any("not found" in issue.message for issue in result.issues)

    def test_version_format_validation(self):
        """Test validation of version format."""
        style_bad_version = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "not-semver",  # Invalid version format
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_bad_version)
        result = self.validator.validate_file(file_path)

        # Should have warning about version format
        warning_messages = [
            issue.message for issue in result.issues if issue.is_warning
        ]
        assert any("semantic versioning" in msg for msg in warning_messages)

        # Clean up
        file_path.unlink()

    def test_use_cases_validation(self):
        """Test validation of use cases."""
        style_bad_use_cases = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
                "use_cases": "should be list",  # Should be list
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
        }

        file_path = self.create_temp_yaml_file(style_bad_use_cases)
        result = self.validator.validate_file(file_path)

        # Should have warning about use cases format
        warning_messages = [
            issue.message for issue in result.issues if issue.is_warning
        ]
        assert any("should be a list" in msg for msg in warning_messages)

        # Clean up
        file_path.unlink()

    def test_recommended_sections_info(self):
        """Test that missing recommended sections generate info messages."""
        minimal_style = {
            "metadata": {
                "name": "Test Style",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "category": "professional",
                "difficulty": "intermediate",
            },
            "voice": {"personality": "test"},
            "language": {"formality": "test"},
            "structure": {"opening": "test"},
            # Missing recommended sections: formatting, audience, examples
        }

        file_path = self.create_temp_yaml_file(minimal_style)
        result = self.validator.validate_file(file_path)

        # Should pass validation but have info messages about recommended sections
        assert result.is_valid  # Should be valid even without recommended sections

        info_messages = [issue.message for issue in result.issues if issue.is_info]
        assert any("formatting" in msg for msg in info_messages)
        assert any("audience" in msg for msg in info_messages)
        assert any("examples" in msg for msg in info_messages)

        # Clean up
        file_path.unlink()
