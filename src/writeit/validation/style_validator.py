# ABOUTME: Style primer validator for WriteIt YAML style files
# ABOUTME: Validates style primer structure, voice, language patterns, and formatting rules
import yaml
import re
from pathlib import Path
from typing import Dict, Any
from .validation_result import ValidationResult


class StyleValidator:
    """Validates WriteIt style primer files."""

    # Required top-level keys for style primers
    REQUIRED_KEYS = {"metadata", "voice", "language", "structure"}

    # Required metadata fields
    REQUIRED_METADATA = {
        "name",
        "description",
        "version",
        "author",
        "category",
        "difficulty",
    }

    # Valid categories
    VALID_CATEGORIES = {
        "professional",
        "informal",
        "academic",
        "creative",
        "marketing",
        "technical",
    }

    # Valid difficulty levels
    VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}

    # Common style primer sections
    COMMON_SECTIONS = {
        "voice",
        "language",
        "structure",
        "formatting",
        "audience",
        "examples",
        "anti_patterns",
        "integration",
    }

    def __init__(self):
        """Initialize the style validator."""
        self.variable_pattern = re.compile(r"\{\{\s*([^}]+)\s*\}\}")

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a style primer file."""
        result = ValidationResult(
            file_path=file_path,
            is_valid=True,
            issues=[],
            metadata={},
            file_type="style",
        )

        try:
            # Check file exists and is readable
            if not file_path.exists():
                result.add_error(f"Style file not found: {file_path}")
                return result

            if not file_path.is_file():
                result.add_error(f"Path is not a file: {file_path}")
                return result

            # Load and parse YAML
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    style = yaml.safe_load(content)
            except yaml.YAMLError as e:
                result.add_error(f"Invalid YAML syntax: {str(e)}")
                return result
            except Exception as e:
                result.add_error(f"Failed to read file: {str(e)}")
                return result

            if not isinstance(style, dict):
                result.add_error("Style primer must be a YAML object/dictionary")
                return result

            # Store parsed style for metadata
            result.metadata["parsed_style"] = style

            # Validate structure
            self._validate_top_level_structure(style, result)
            self._validate_metadata(style.get("metadata", {}), result)
            self._validate_voice(style.get("voice", {}), result)
            self._validate_language(style.get("language", {}), result)
            self._validate_structure_section(style.get("structure", {}), result)

            # Optional sections validation
            if "formatting" in style:
                self._validate_formatting(style["formatting"], result)
            if "audience" in style:
                self._validate_audience(style["audience"], result)
            if "examples" in style:
                self._validate_examples(style["examples"], result)

            # Add statistics to metadata
            result.metadata.update(
                {
                    "has_voice_section": "voice" in style,
                    "has_examples": "examples" in style,
                    "has_anti_patterns": "anti_patterns" in style,
                    "section_count": len(
                        [k for k in style.keys() if k in self.COMMON_SECTIONS]
                    ),
                }
            )

        except Exception as e:
            result.add_error(f"Unexpected validation error: {str(e)}")

        return result

    def _validate_top_level_structure(
        self, style: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate top-level style primer structure."""
        # Check required keys
        missing_keys = self.REQUIRED_KEYS - set(style.keys())
        if missing_keys:
            for key in sorted(missing_keys):
                result.add_error(
                    f"Missing required top-level key: '{key}'",
                    suggestion=f"Add '{key}:' section to style primer",
                )

        # Check for recommended sections
        recommended_keys = {"formatting", "audience", "examples"}
        missing_recommended = recommended_keys - set(style.keys())
        if missing_recommended:
            for key in sorted(missing_recommended):
                result.add_info(
                    f"Consider adding recommended section: '{key}'",
                    suggestion=f"Adding '{key}' section improves style primer completeness",
                )

    def _validate_metadata(
        self, metadata: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate metadata section."""
        if not metadata:
            result.add_error(
                "Empty metadata section",
                suggestion="Add style name, description, version, and author",
            )
            return

        # Check required metadata fields
        missing_fields = self.REQUIRED_METADATA - set(metadata.keys())
        if missing_fields:
            for field in sorted(missing_fields):
                result.add_error(
                    f"Missing required metadata field: '{field}'", location="metadata"
                )

        # Validate specific fields
        if "category" in metadata:
            category = metadata["category"]
            if category not in self.VALID_CATEGORIES:
                result.add_warning(
                    f"Unknown category '{category}'",
                    location="metadata.category",
                    suggestion=f"Valid categories: {', '.join(sorted(self.VALID_CATEGORIES))}",
                )

        if "difficulty" in metadata:
            difficulty = metadata["difficulty"]
            if difficulty not in self.VALID_DIFFICULTIES:
                result.add_warning(
                    f"Unknown difficulty '{difficulty}'",
                    location="metadata.difficulty",
                    suggestion=f"Valid difficulties: {', '.join(sorted(self.VALID_DIFFICULTIES))}",
                )

        if "version" in metadata:
            version = metadata["version"]
            if not isinstance(version, str) or not re.match(
                r"^\d+\.\d+\.\d+", str(version)
            ):
                result.add_warning(
                    "Version should follow semantic versioning (e.g., '1.0.0')",
                    location="metadata.version",
                )

        # Check use_cases if present
        if "use_cases" in metadata:
            use_cases = metadata["use_cases"]
            if not isinstance(use_cases, list):
                result.add_warning(
                    "Use cases should be a list of strings",
                    location="metadata.use_cases",
                )
            elif len(use_cases) == 0:
                result.add_info(
                    "Consider adding use cases to help users understand when to use this style",
                    location="metadata.use_cases",
                )

    def _validate_voice(self, voice: Dict[str, Any], result: ValidationResult) -> None:
        """Validate voice section."""
        if not voice:
            result.add_error(
                "Empty voice section",
                suggestion="Define personality, tone, and perspective",
            )
            return

        # Recommended voice fields
        recommended_fields = {"personality", "tone", "perspective", "characteristics"}
        missing_recommended = recommended_fields - set(voice.keys())

        for field in missing_recommended:
            result.add_info(
                f"Consider adding voice field: '{field}'",
                location="voice",
                suggestion=f"Adding '{field}' helps define the writing voice more clearly",
            )

        # Validate characteristics if present
        if "characteristics" in voice:
            characteristics = voice["characteristics"]
            if not isinstance(characteristics, list):
                result.add_warning(
                    "Voice characteristics should be a list",
                    location="voice.characteristics",
                )
            elif len(characteristics) == 0:
                result.add_warning(
                    "Empty characteristics list",
                    location="voice.characteristics",
                    suggestion="Add specific voice characteristics",
                )

    def _validate_language(
        self, language: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate language section."""
        if not language:
            result.add_error(
                "Empty language section", suggestion="Define formality and word choices"
            )
            return

        # Check for important language elements
        important_elements = {"formality", "preferred_words", "avoid"}
        missing_elements = important_elements - set(language.keys())

        for element in missing_elements:
            result.add_info(
                f"Consider adding language element: '{element}'",
                location="language",
                suggestion=f"Adding '{element}' provides clearer language guidance",
            )

        # Validate word lists
        for list_field in ["preferred_words", "avoid", "technical_language"]:
            if list_field in language:
                self._validate_word_list(
                    language[list_field], f"language.{list_field}", result
                )

    def _validate_word_list(
        self, word_data: Any, location: str, result: ValidationResult
    ) -> None:
        """Validate word lists in language section."""
        if isinstance(word_data, dict):
            # Check if it has any content
            if not word_data:
                result.add_info(
                    "Empty word guidance section",
                    location=location,
                    suggestion="Add word preferences or examples",
                )
        elif isinstance(word_data, list):
            if len(word_data) == 0:
                result.add_info(
                    "Empty word list", location=location, suggestion="Add word examples"
                )
        else:
            result.add_warning(
                "Word guidance should be a dictionary or list", location=location
            )

    def _validate_structure_section(
        self, structure: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate structure section."""
        if not structure:
            result.add_error(
                "Empty structure section",
                suggestion="Define opening, body, and conclusion patterns",
            )
            return

        # Recommended structure elements
        recommended_elements = {"opening", "body_sections", "conclusion"}
        missing_elements = recommended_elements - set(structure.keys())

        for element in missing_elements:
            result.add_info(
                f"Consider adding structure element: '{element}'",
                location="structure",
                suggestion=f"Adding '{element}' provides clearer content organization guidance",
            )

        # Validate specific structure elements
        if "opening" in structure:
            opening = structure["opening"]
            if isinstance(opening, dict):
                if "pattern" not in opening:
                    result.add_info(
                        "Consider adding 'pattern' to opening structure",
                        location="structure.opening",
                    )
            else:
                result.add_warning(
                    "Opening structure should be an object with pattern and elements",
                    location="structure.opening",
                )

    def _validate_formatting(
        self, formatting: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate formatting section."""
        if not formatting:
            result.add_info("Empty formatting section", location="formatting")
            return

        # Check for common formatting elements
        common_elements = {"headings", "lists", "emphasis", "code_blocks"}
        present_elements = set(formatting.keys()) & common_elements

        if not present_elements:
            result.add_info(
                "Consider adding formatting guidelines",
                location="formatting",
                suggestion=f"Common elements: {', '.join(sorted(common_elements))}",
            )

    def _validate_audience(
        self, audience: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate audience section."""
        if not audience:
            result.add_info("Empty audience section", location="audience")
            return

        # Check for important audience elements
        important_elements = {"assumptions", "explanation_depth", "terminology"}
        missing_elements = important_elements - set(audience.keys())

        for element in missing_elements:
            result.add_info(
                f"Consider adding audience element: '{element}'", location="audience"
            )

    def _validate_examples(
        self, examples: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate examples section."""
        if not examples:
            result.add_info("Empty examples section", location="examples")
            return

        # Count different types of examples
        example_types = [
            "excellent_opening",
            "good_explanation",
            "effective_code_example",
            "strong_conclusion",
            "clear_transition",
        ]

        present_examples = [ex for ex in example_types if ex in examples]

        if not present_examples:
            result.add_info(
                "Consider adding concrete writing examples",
                location="examples",
                suggestion="Examples help demonstrate the style in practice",
            )

        # Validate example content
        for example_name, example_content in examples.items():
            if isinstance(example_content, str):
                if not example_content.strip():
                    result.add_warning(
                        f"Empty example: '{example_name}'",
                        location=f"examples.{example_name}",
                    )
                elif len(example_content) < 50:
                    result.add_info(
                        f"Example '{example_name}' is quite short",
                        location=f"examples.{example_name}",
                        suggestion="Longer examples better demonstrate the style",
                    )

    def validate_style_consistency(
        self, style: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate internal consistency of style primer."""
        # Check if voice characteristics align with language preferences
        voice = style.get("voice", {})
        language = style.get("language", {})

        # If voice mentions formal but language says casual, flag inconsistency
        voice_text = str(voice).lower()
        language_text = str(language).lower()

        formal_indicators = ["formal", "professional", "authoritative"]
        casual_indicators = ["casual", "conversational", "informal", "friendly"]

        voice_formal = any(indicator in voice_text for indicator in formal_indicators)
        voice_casual = any(indicator in voice_text for indicator in casual_indicators)
        language_formal = any(
            indicator in language_text for indicator in formal_indicators
        )
        language_casual = any(
            indicator in language_text for indicator in casual_indicators
        )

        if voice_formal and language_casual:
            result.add_warning(
                "Potential inconsistency: voice suggests formal tone but language suggests casual approach",
                suggestion="Ensure voice and language sections align",
            )
        elif voice_casual and language_formal:
            result.add_warning(
                "Potential inconsistency: voice suggests casual tone but language suggests formal approach",
                suggestion="Ensure voice and language sections align",
            )
