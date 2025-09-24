"""Comprehensive unit tests for StylePrimer entity."""

import pytest
from datetime import datetime, timedelta
import json

from src.writeit.domains.content.entities.style_primer import StylePrimer
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.content_id import ContentId

from tests.builders.content_builders import StylePrimerBuilder


class TestStylePrimer:
    """Test cases for StylePrimer entity."""
    
    def test_style_primer_creation_with_valid_data(self):
        """Test creating a style primer with valid data."""
        style_primer = StylePrimerBuilder.professional().build()
        
        assert isinstance(style_primer.id, ContentId)
        assert isinstance(style_primer.name, StyleName)
        assert style_primer.tone == "professional"
        assert style_primer.voice == "third_person"
        assert style_primer.writing_style == "formal"
        assert style_primer.target_audience == "business professionals"
        assert len(style_primer.guidelines) > 0
        assert len(style_primer.examples) > 0
        assert "professional" in style_primer.tags
        assert isinstance(style_primer.created_at, datetime)
        assert isinstance(style_primer.updated_at, datetime)
        assert style_primer.language == "en"
        assert style_primer.is_published is False
        assert style_primer.is_deprecated is False
        assert style_primer.usage_count == 0
    
    def test_style_primer_creation_with_custom_data(self):
        """Test creating a style primer with custom data."""
        custom_guidelines = ["Use active voice", "Keep sentences short", "Focus on clarity"]
        custom_examples = ["This approach works well.", "We recommend this solution."]
        custom_metadata = {
            "category": "writing",
            "difficulty": "beginner",
            "updated_by": "editor"
        }
        
        style_primer = (StylePrimerBuilder()
                       .with_name("custom-style")
                       .with_description("Custom style for testing")
                       .with_tone("friendly")
                       .with_voice("first_person")
                       .with_writing_style("conversational")
                       .with_target_audience("new users")
                       .with_guidelines(custom_guidelines)
                       .with_examples(custom_examples)
                       .with_metadata(custom_metadata)
                       .with_author("Test Author")
                       .build())
        
        assert style_primer.name.value == "custom-style"
        assert style_primer.description == "Custom style for testing"
        assert style_primer.tone == "friendly"
        assert style_primer.voice == "first_person"
        assert style_primer.writing_style == "conversational"
        assert style_primer.target_audience == "new users"
        assert style_primer.guidelines == custom_guidelines
        assert style_primer.examples == custom_examples
        assert style_primer.metadata == custom_metadata
        assert style_primer.author == "Test Author"
    
    def test_professional_style_primer_creation(self):
        """Test creating a professional style primer."""
        style_primer = StylePrimerBuilder.professional("business-pro").build()
        
        assert style_primer.tone == "professional"
        assert style_primer.voice == "third_person"
        assert style_primer.writing_style == "formal"
        assert style_primer.target_audience == "business professionals"
        assert "Use formal language throughout" in style_primer.guidelines
        assert "professional" in style_primer.tags
        assert "formal" in style_primer.tags
        assert "business" in style_primer.tags
    
    def test_casual_style_primer_creation(self):
        """Test creating a casual style primer."""
        style_primer = StylePrimerBuilder.casual("friendly-chat").build()
        
        assert style_primer.tone == "casual"
        assert style_primer.voice == "second_person"
        assert style_primer.writing_style == "conversational"
        assert style_primer.target_audience == "general audience"
        assert "Use conversational language" in style_primer.guidelines
        assert "casual" in style_primer.tags
        assert "conversational" in style_primer.tags
        assert "friendly" in style_primer.tags
    
    def test_technical_style_primer_creation(self):
        """Test creating a technical style primer."""
        style_primer = StylePrimerBuilder.technical("dev-docs").build()
        
        assert style_primer.tone == "technical"
        assert style_primer.voice == "third_person"
        assert style_primer.writing_style == "academic"
        assert style_primer.target_audience == "software developers"
        assert "Use precise technical terminology" in style_primer.guidelines
        assert ContentType.documentation() in style_primer.applicable_content_types
        assert ContentType.code() in style_primer.applicable_content_types
        assert "technical" in style_primer.tags
        assert "documentation" in style_primer.tags
        assert "programming" in style_primer.tags
    
    def test_style_primer_with_formatting_preferences(self):
        """Test style primer with formatting preferences."""
        formatting_prefs = {
            "line_length": 80,
            "paragraph_spacing": "double",
            "heading_style": "title_case",
            "list_style": "bullet"
        }
        
        style_primer = (StylePrimerBuilder.professional()
                       .with_formatting_preferences(formatting_prefs)
                       .build())
        
        assert style_primer.formatting_preferences == formatting_prefs
        assert style_primer.formatting_preferences["line_length"] == 80
        assert style_primer.formatting_preferences["heading_style"] == "title_case"
    
    def test_style_primer_with_vocabulary_preferences(self):
        """Test style primer with vocabulary preferences."""
        vocab_prefs = {
            "complexity": "intermediate",
            "jargon": "minimal",
            "contractions": "allowed",
            "technical_terms": "define_first_use"
        }
        
        style_primer = (StylePrimerBuilder.casual()
                       .with_vocabulary_preferences(vocab_prefs)
                       .build())
        
        assert style_primer.vocabulary_preferences == vocab_prefs
        assert style_primer.vocabulary_preferences["complexity"] == "intermediate"
        assert style_primer.vocabulary_preferences["contractions"] == "allowed"
    
    def test_style_primer_with_applicable_content_types(self):
        """Test style primer with specific applicable content types."""
        content_types = [
            ContentType.article(),
            ContentType.documentation(),
            ContentType.blog_post()
        ]
        
        style_primer = (StylePrimerBuilder.professional()
                       .with_applicable_content_types(content_types)
                       .build())
        
        assert style_primer.applicable_content_types == content_types
        assert ContentType.article() in style_primer.applicable_content_types
        assert ContentType.documentation() in style_primer.applicable_content_types
        assert ContentType.blog_post() in style_primer.applicable_content_types
    
    def test_style_primer_with_published_status(self):
        """Test style primer with published status."""
        published_primer = (StylePrimerBuilder.professional()
                           .with_published(True)
                           .build())
        
        assert published_primer.is_published is True
        assert published_primer.published_at is not None
        assert isinstance(published_primer.published_at, datetime)
        
        draft_primer = (StylePrimerBuilder.professional()
                       .with_published(False)
                       .build())
        
        assert draft_primer.is_published is False
        assert draft_primer.published_at is None
    
    def test_style_primer_with_deprecated_status(self):
        """Test style primer with deprecated status."""
        deprecated_primer = (StylePrimerBuilder.professional()
                            .with_deprecated(True)
                            .build())
        
        assert deprecated_primer.is_deprecated is True
        assert deprecated_primer.deprecated_at is not None
        assert isinstance(deprecated_primer.deprecated_at, datetime)
        
        active_primer = (StylePrimerBuilder.professional()
                        .with_deprecated(False)
                        .build())
        
        assert active_primer.is_deprecated is False
        assert active_primer.deprecated_at is None
    
    def test_style_primer_with_usage_count(self):
        """Test style primer with usage count."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_usage_count(42)
                       .build())
        
        assert style_primer.usage_count == 42
    
    def test_style_primer_timestamps(self):
        """Test style primer timestamps."""
        now = datetime.now()
        style_primer = StylePrimerBuilder.professional().build()
        
        # Created and updated should be close to now
        assert abs((style_primer.created_at - now).total_seconds()) < 1
        assert abs((style_primer.updated_at - now).total_seconds()) < 1
        
        # Test custom timestamps
        custom_time = datetime(2023, 8, 15, 14, 30, 0)
        style_primer_with_custom = (StylePrimerBuilder.professional()
                                   .with_timestamps(custom_time, custom_time)
                                   .build())
        
        assert style_primer_with_custom.created_at == custom_time
        assert style_primer_with_custom.updated_at == custom_time
    
    def test_style_primer_versioning(self):
        """Test style primer versioning."""
        v1_primer = (StylePrimerBuilder.professional()
                    .with_version("1.0.0")
                    .build())
        
        v2_primer = (StylePrimerBuilder.professional()
                    .with_version("2.1.0")
                    .build())
        
        assert v1_primer.version == "1.0.0"
        assert v2_primer.version == "2.1.0"
        assert v1_primer.version != v2_primer.version


class TestStylePrimerBusinessLogic:
    """Test business logic and invariants for StylePrimer."""
    
    def test_set_tone_updates_style(self):
        """Test setting tone updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_updated = style_primer.updated_at
        
        # Wait a tiny bit to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        updated_primer = style_primer.set_tone("casual")
        
        assert updated_primer.tone == "casual"
        assert updated_primer.updated_at > original_updated
        assert updated_primer is not style_primer  # Immutable
    
    def test_set_tone_validation(self):
        """Test tone validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Tone cannot be empty"):
            style_primer.set_tone("")
        
        with pytest.raises(ValueError, match="Tone cannot be empty"):
            style_primer.set_tone("   ")
    
    def test_set_voice_updates_style(self):
        """Test setting voice updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        updated_primer = style_primer.set_voice("first_person")
        
        assert updated_primer.voice == "first_person"
        assert updated_primer is not style_primer  # Immutable
    
    def test_set_voice_validation(self):
        """Test voice validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Voice cannot be empty"):
            style_primer.set_voice("")
        
        with pytest.raises(ValueError, match="Invalid voice"):
            style_primer.set_voice("invalid_voice")
        
        # Valid voices should work
        valid_voices = ["first_person", "second_person", "third_person"]
        for voice in valid_voices:
            updated = style_primer.set_voice(voice)
            assert updated.voice == voice
    
    def test_set_writing_style_updates_style(self):
        """Test setting writing style updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        updated_primer = style_primer.set_writing_style("journalistic")
        
        assert updated_primer.writing_style == "journalistic"
        assert updated_primer is not style_primer  # Immutable
    
    def test_set_writing_style_validation(self):
        """Test writing style validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Writing style cannot be empty"):
            style_primer.set_writing_style("")
        
        with pytest.raises(ValueError, match="Writing style cannot be empty"):
            style_primer.set_writing_style("   ")
    
    def test_set_target_audience_updates_style(self):
        """Test setting target audience updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        updated_primer = style_primer.set_target_audience("marketing professionals")
        
        assert updated_primer.target_audience == "marketing professionals"
        assert updated_primer is not style_primer  # Immutable
    
    def test_set_target_audience_validation(self):
        """Test target audience validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Target audience cannot be empty"):
            style_primer.set_target_audience("")
        
        with pytest.raises(ValueError, match="Target audience cannot be empty"):
            style_primer.set_target_audience("   ")
    
    def test_add_guideline_updates_style(self):
        """Test adding guideline updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_count = len(style_primer.guidelines)
        
        updated_primer = style_primer.add_guideline("Use bullet points for lists")
        
        assert len(updated_primer.guidelines) == original_count + 1
        assert "Use bullet points for lists" in updated_primer.guidelines
        assert updated_primer is not style_primer  # Immutable
    
    def test_add_guideline_prevents_duplicates(self):
        """Test adding duplicate guideline doesn't change the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        existing_guideline = style_primer.guidelines[0]
        
        updated_primer = style_primer.add_guideline(existing_guideline)
        
        assert updated_primer is style_primer  # No change
        assert len(updated_primer.guidelines) == len(style_primer.guidelines)
    
    def test_add_guideline_validation(self):
        """Test guideline validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Guideline cannot be empty"):
            style_primer.add_guideline("")
        
        with pytest.raises(ValueError, match="Guideline cannot be empty"):
            style_primer.add_guideline("   ")
    
    def test_remove_guideline_updates_style(self):
        """Test removing guideline updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        guideline_to_remove = style_primer.guidelines[0]
        original_count = len(style_primer.guidelines)
        
        updated_primer = style_primer.remove_guideline(guideline_to_remove)
        
        assert len(updated_primer.guidelines) == original_count - 1
        assert guideline_to_remove not in updated_primer.guidelines
        assert updated_primer is not style_primer  # Immutable
    
    def test_remove_nonexistent_guideline_no_change(self):
        """Test removing non-existent guideline doesn't change the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_count = len(style_primer.guidelines)
        
        updated_primer = style_primer.remove_guideline("Non-existent guideline")
        
        assert updated_primer is style_primer  # No change
        assert len(updated_primer.guidelines) == original_count
    
    def test_set_formatting_preference_updates_style(self):
        """Test setting formatting preference updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        
        updated_primer = style_primer.set_formatting_preference("indent_size", 4)
        
        assert updated_primer.formatting_preferences["indent_size"] == 4
        assert updated_primer is not style_primer  # Immutable
    
    def test_set_vocabulary_preference_updates_style(self):
        """Test setting vocabulary preference updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        
        updated_primer = style_primer.set_vocabulary_preference("reading_level", "college")
        
        assert updated_primer.vocabulary_preferences["reading_level"] == "college"
        assert updated_primer is not style_primer  # Immutable
    
    def test_add_applicable_content_type_updates_style(self):
        """Test adding applicable content type updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_count = len(style_primer.applicable_content_types)
        
        updated_primer = style_primer.add_applicable_content_type(ContentType.blog_post())
        
        assert len(updated_primer.applicable_content_types) == original_count + 1
        assert ContentType.blog_post() in updated_primer.applicable_content_types
        assert updated_primer is not style_primer  # Immutable
    
    def test_add_applicable_content_type_prevents_duplicates(self):
        """Test adding duplicate content type doesn't change the style primer."""
        content_type = ContentType.article()
        style_primer = (StylePrimerBuilder.professional()
                       .with_applicable_content_types([content_type])
                       .build())
        
        updated_primer = style_primer.add_applicable_content_type(content_type)
        
        assert updated_primer is style_primer  # No change
        assert len(updated_primer.applicable_content_types) == 1
    
    def test_add_applicable_content_type_validation(self):
        """Test content type validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(TypeError, match="Content type must be a ContentType"):
            style_primer.add_applicable_content_type("invalid")  # type: ignore
    
    def test_remove_applicable_content_type_updates_style(self):
        """Test removing applicable content type updates the style primer."""
        content_type = ContentType.article()
        style_primer = (StylePrimerBuilder.professional()
                       .with_applicable_content_types([content_type, ContentType.blog_post()])
                       .build())
        
        updated_primer = style_primer.remove_applicable_content_type(content_type)
        
        assert content_type not in updated_primer.applicable_content_types
        assert ContentType.blog_post() in updated_primer.applicable_content_types
        assert updated_primer is not style_primer  # Immutable
    
    def test_remove_nonexistent_content_type_no_change(self):
        """Test removing non-existent content type doesn't change the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_count = len(style_primer.applicable_content_types)
        
        updated_primer = style_primer.remove_applicable_content_type(ContentType.video())
        
        assert updated_primer is style_primer  # No change
        assert len(updated_primer.applicable_content_types) == original_count
    
    def test_add_example_updates_style(self):
        """Test adding example updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_count = len(style_primer.examples)
        
        updated_primer = style_primer.add_example("This is an excellent example of professional writing.")
        
        assert len(updated_primer.examples) == original_count + 1
        assert "This is an excellent example of professional writing." in updated_primer.examples
        assert updated_primer is not style_primer  # Immutable
    
    def test_add_example_prevents_duplicates(self):
        """Test adding duplicate example doesn't change the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        existing_example = style_primer.examples[0]
        
        updated_primer = style_primer.add_example(existing_example)
        
        assert updated_primer is style_primer  # No change
        assert len(updated_primer.examples) == len(style_primer.examples)
    
    def test_add_example_validation(self):
        """Test example validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Example cannot be empty"):
            style_primer.add_example("")
        
        with pytest.raises(ValueError, match="Example cannot be empty"):
            style_primer.add_example("   ")
    
    def test_add_tag_updates_style(self):
        """Test adding tag updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        original_count = len(style_primer.tags)
        
        updated_primer = style_primer.add_tag("Enterprise")
        
        assert len(updated_primer.tags) == original_count + 1
        assert "enterprise" in updated_primer.tags  # Normalized to lowercase
        assert updated_primer is not style_primer  # Immutable
    
    def test_add_tag_prevents_duplicates(self):
        """Test adding duplicate tag doesn't change the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        existing_tag = style_primer.tags[0]
        
        updated_primer = style_primer.add_tag(existing_tag.upper())  # Different case
        
        assert updated_primer is style_primer  # No change
        assert len(updated_primer.tags) == len(style_primer.tags)
    
    def test_add_tag_validation(self):
        """Test tag validation."""
        style_primer = StylePrimerBuilder.professional().build()
        
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            style_primer.add_tag("")
        
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            style_primer.add_tag("   ")
    
    def test_publish_updates_style(self):
        """Test publishing updates the style primer."""
        style_primer = StylePrimerBuilder.professional().build()
        
        published_primer = style_primer.publish("Publisher Name")
        
        assert published_primer.is_published is True
        assert published_primer.published_at is not None
        assert published_primer.author == "Publisher Name"
        assert published_primer is not style_primer  # Immutable
    
    def test_publish_already_published_no_change(self):
        """Test publishing already published style primer doesn't change it."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_published(True)
                       .build())
        
        republished_primer = style_primer.publish("Another Publisher")
        
        assert republished_primer is style_primer  # No change
    
    def test_deprecate_updates_style(self):
        """Test deprecating updates the style primer."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_published(True)
                       .build())
        
        deprecated_primer = style_primer.deprecate("Outdated approach", "Admin User")
        
        assert deprecated_primer.is_deprecated is True
        assert deprecated_primer.is_published is False  # Unpublished when deprecated
        assert deprecated_primer.deprecated_at is not None
        assert deprecated_primer.metadata["deprecation_reason"] == "Outdated approach"
        assert deprecated_primer.metadata["deprecated_by"] == "Admin User"
        assert deprecated_primer is not style_primer  # Immutable
    
    def test_deprecate_already_deprecated_no_change(self):
        """Test deprecating already deprecated style primer doesn't change it."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_deprecated(True)
                       .build())
        
        redeprecated_primer = style_primer.deprecate("Another reason")
        
        assert redeprecated_primer is style_primer  # No change
    
    def test_increment_usage_updates_count(self):
        """Test incrementing usage updates the count."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_usage_count(5)
                       .build())
        
        updated_primer = style_primer.increment_usage()
        
        assert updated_primer.usage_count == 6
        assert updated_primer is not style_primer  # Immutable
    
    def test_is_applicable_to_content_type_with_restrictions(self):
        """Test content type applicability with restrictions."""
        content_types = [ContentType.article(), ContentType.blog_post()]
        style_primer = (StylePrimerBuilder.professional()
                       .with_applicable_content_types(content_types)
                       .build())
        
        assert style_primer.is_applicable_to_content_type(ContentType.article()) is True
        assert style_primer.is_applicable_to_content_type(ContentType.blog_post()) is True
        assert style_primer.is_applicable_to_content_type(ContentType.documentation()) is False
        assert style_primer.is_applicable_to_content_type(ContentType.email()) is False
    
    def test_is_applicable_to_content_type_no_restrictions(self):
        """Test content type applicability without restrictions."""
        style_primer = StylePrimerBuilder.professional().build()  # No content types specified
        
        # Should apply to all content types when none specified
        assert style_primer.is_applicable_to_content_type(ContentType.article()) is True
        assert style_primer.is_applicable_to_content_type(ContentType.blog_post()) is True
        assert style_primer.is_applicable_to_content_type(ContentType.documentation()) is True
        assert style_primer.is_applicable_to_content_type(ContentType.email()) is True
    
    def test_get_style_summary_with_all_attributes(self):
        """Test style summary with all attributes."""
        style_primer = (StylePrimerBuilder()
                       .with_tone("professional")
                       .with_voice("third_person")
                       .with_writing_style("formal")
                       .with_target_audience("business executives")
                       .build())
        
        summary = style_primer.get_style_summary()
        
        assert "Tone: professional" in summary
        assert "Voice: third person" in summary
        assert "Style: formal" in summary
        assert "Audience: business executives" in summary
    
    def test_get_style_summary_partial_attributes(self):
        """Test style summary with partial attributes."""
        style_primer = (StylePrimerBuilder()
                       .with_tone("casual")
                       .with_target_audience("developers")
                       .build())
        
        summary = style_primer.get_style_summary()
        
        assert "Tone: casual" in summary
        assert "Audience: developers" in summary
        assert "Voice:" not in summary
        assert "Style:" not in summary
    
    def test_get_style_summary_no_attributes(self):
        """Test style summary with no style attributes."""
        style_primer = (StylePrimerBuilder()
                       .with_tone(None)
                       .with_voice(None)
                       .with_writing_style(None)
                       .with_target_audience(None)
                       .build())
        
        summary = style_primer.get_style_summary()
        
        assert summary == "No style preferences defined"
    
    def test_create_class_method(self):
        """Test StylePrimer.create class method."""
        name = StyleName.from_user_input("test-style")
        style_primer = StylePrimer.create(
            name=name,
            description="Test style created via class method",
            tone="friendly",
            voice="second_person",
            writing_style="conversational",
            target_audience="general users",
            language="es",
            author="Creator"
        )
        
        assert style_primer.name == name
        assert style_primer.description == "Test style created via class method"
        assert style_primer.tone == "friendly"
        assert style_primer.voice == "second_person"
        assert style_primer.writing_style == "conversational"
        assert style_primer.target_audience == "general users"
        assert style_primer.language == "es"
        assert style_primer.author == "Creator"
        assert isinstance(style_primer.created_at, datetime)
        assert isinstance(style_primer.updated_at, datetime)


class TestStylePrimerEdgeCases:
    """Test edge cases and error conditions for StylePrimer."""
    
    def test_style_primer_with_empty_guidelines(self):
        """Test style primer with empty guidelines."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_guidelines([])
                       .build())
        
        assert style_primer.guidelines == []
        assert len(style_primer.guidelines) == 0
    
    def test_style_primer_with_empty_examples(self):
        """Test style primer with empty examples."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_examples([])
                       .build())
        
        assert style_primer.examples == []
        assert len(style_primer.examples) == 0
    
    def test_style_primer_with_empty_tags(self):
        """Test style primer with empty tags."""
        style_primer = (StylePrimerBuilder.professional()
                       .with_tags([])
                       .build())
        
        assert style_primer.tags == []
        assert len(style_primer.tags) == 0
    
    def test_style_primer_with_unicode_content(self):
        """Test style primer with unicode content."""
        unicode_description = "Çréâtë çöñtëñt ïñ müłtïplë làñgüàgës 🌍"
        unicode_guidelines = [
            "Üsë üñïçödë çhàràçtërs whëñ àpprøprïàtë",
            "Rëspëçt çültüràł ñüàñçës ïñ wrïtïñg 📝"
        ]
        
        style_primer = (StylePrimerBuilder.professional()
                       .with_description(unicode_description)
                       .with_guidelines(unicode_guidelines)
                       .with_target_audience("ïñtërnàtïönàł àüdïëñçë")
                       .build())
        
        assert style_primer.description == unicode_description
        assert style_primer.guidelines == unicode_guidelines
        assert style_primer.target_audience == "ïñtërnàtïönàł àüdïëñçë"
        assert "🌍" in style_primer.description
        assert "📝" in style_primer.guidelines[1]
    
    def test_style_primer_with_special_characters_in_metadata(self):
        """Test style primer with special characters in metadata."""
        special_metadata = {
            "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
            "paths": ["/special/path", "C:\\Windows\\Path"],
            "unicode": "Spëçîál characters 🎉",
            "mixed": {"nested": "value with émojis 😊"}
        }
        
        style_primer = (StylePrimerBuilder.professional()
                       .with_metadata(special_metadata)
                       .build())
        
        assert style_primer.metadata == special_metadata
        assert "!@#$%^&*()" in style_primer.metadata["special_chars"]
        assert "🎉" in style_primer.metadata["unicode"]
        assert "😊" in style_primer.metadata["mixed"]["nested"]
    
    def test_style_primer_metadata_serialization(self):
        """Test that style primer metadata is JSON serializable."""
        style_primer = StylePrimerBuilder.professional().build()
        
        # Basic metadata should be JSON serializable
        try:
            json.dumps(style_primer.metadata)
        except (TypeError, ValueError) as e:
            pytest.fail(f"StylePrimer metadata not serializable: {e}")
    
    def test_style_primer_with_long_content(self):
        """Test style primer with long content."""
        long_description = "Very detailed style description. " * 100  # ~3KB
        long_guidelines = [f"Guideline number {i} with detailed explanation" for i in range(100)]
        
        style_primer = (StylePrimerBuilder.professional()
                       .with_description(long_description)
                       .with_guidelines(long_guidelines)
                       .build())
        
        assert len(style_primer.description) > 2000
        assert len(style_primer.guidelines) == 100
        assert style_primer.guidelines[99] == "Guideline number 99 with detailed explanation"
    
    def test_style_primer_post_init_validation(self):
        """Test StylePrimer post-init validation."""
        with pytest.raises(TypeError, match="Style primer ID must be a ContentId"):
            StylePrimer(
                id="invalid_id",  # type: ignore
                name=StyleName("test"),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="Style primer name must be a StyleName"):
            StylePrimer(
                id=ContentId.generate(),
                name="invalid_name",  # type: ignore
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="Language must be a string"):
            StylePrimer(
                id=ContentId.generate(),
                name=StyleName("test"),
                language=123,  # type: ignore
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="All applicable content types must be ContentType instances"):
            StylePrimer(
                id=ContentId.generate(),
                name=StyleName("test"),
                applicable_content_types=["invalid_type"],  # type: ignore
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_style_primer_string_representations(self):
        """Test string representations of StylePrimer."""
        # Draft style primer
        draft_primer = StylePrimerBuilder.professional("test-style").build()
        str_repr = str(draft_primer)
        assert "StylePrimer(test-style, draft)" == str_repr
        
        # Published style primer
        published_primer = (StylePrimerBuilder.professional("published-style")
                           .with_published(True)
                           .build())
        str_repr = str(published_primer)
        assert "StylePrimer(published-style, published)" == str_repr
        
        # Deprecated style primer
        deprecated_primer = (StylePrimerBuilder.professional("deprecated-style")
                            .with_deprecated(True)
                            .build())
        str_repr = str(deprecated_primer)
        assert "StylePrimer(deprecated-style, deprecated)" == str_repr
        
        # Test repr
        repr_str = repr(draft_primer)
        assert "StylePrimer(id=" in repr_str
        assert "name=test-style" in repr_str
        assert "tone=professional" in repr_str
        assert "published=False" in repr_str
    
    def test_style_primer_immutability(self):
        """Test style primer immutability after creation."""
        style_primer = StylePrimerBuilder.professional().build()
        original_tone = style_primer.tone
        original_guidelines = style_primer.guidelines
        
        # Direct modification should not be possible (frozen dataclass)
        with pytest.raises(AttributeError):
            style_primer.tone = "Modified tone"  # type: ignore
        
        with pytest.raises(AttributeError):
            style_primer.is_published = True  # type: ignore
        
        # Values should remain unchanged
        assert style_primer.tone == original_tone
        assert style_primer.guidelines == original_guidelines