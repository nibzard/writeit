"""Unit tests for PipelineId value object.

Tests value object behavior, validation, and immutability.
"""

import pytest
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId


class TestPipelineId:
    """Test PipelineId value object behavior and validation."""
    
    def test_create_valid_pipeline_id(self):
        """Test creating a valid pipeline ID."""
        pipeline_id = PipelineId("test-pipeline-123")
        assert pipeline_id.value == "test-pipeline-123"
        assert str(pipeline_id) == "test-pipeline-123"
    
    def test_create_with_underscores(self):
        """Test creating pipeline ID with underscores."""
        pipeline_id = PipelineId("user_content_generator")
        assert pipeline_id.value == "user_content_generator"
    
    def test_create_with_numbers(self):
        """Test creating pipeline ID with numbers."""
        pipeline_id = PipelineId("pipeline123")
        assert pipeline_id.value == "pipeline123"
    
    def test_create_mixed_format(self):
        """Test creating pipeline ID with mixed format."""
        pipeline_id = PipelineId("quick-article-v2_final")
        assert pipeline_id.value == "quick-article-v2_final"
    
    def test_empty_value_raises_error(self):
        """Test that empty value raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline ID cannot be empty"):
            PipelineId("")
    
    def test_none_value_raises_error(self):
        """Test that None value raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline ID cannot be empty"):
            PipelineId(None)
    
    def test_non_string_type_raises_error(self):
        """Test that non-string type raises TypeError."""
        with pytest.raises(TypeError, match="Pipeline ID must be string"):
            PipelineId(123)
    
    def test_too_short_raises_error(self):
        """Test that too short ID raises ValueError."""
        with pytest.raises(ValueError, match="Pipeline ID must be at least 3 characters long"):
            PipelineId("ab")
    
    def test_too_long_raises_error(self):
        """Test that too long ID raises ValueError."""
        long_id = "a" * 65  # 65 characters
        with pytest.raises(ValueError, match="Pipeline ID must be at most 64 characters long"):
            PipelineId(long_id)
    
    def test_invalid_characters_raises_error(self):
        """Test that invalid characters raise ValueError."""
        invalid_ids = [
            "test@pipeline",  # @ symbol
            "test pipeline",  # space
            "test.pipeline",  # dot
            "test/pipeline",  # slash
            "test\\pipeline",  # backslash
            "test$pipeline",  # dollar sign
            "test%pipeline",  # percent
            "test+pipeline",  # plus
            "test=pipeline",  # equals
        ]
        
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
                PipelineId(invalid_id)
    
    def test_starts_with_hyphen_raises_error(self):
        """Test that starting with hyphen raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            PipelineId("-test-pipeline")
    
    def test_ends_with_hyphen_raises_error(self):
        """Test that ending with hyphen raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            PipelineId("test-pipeline-")
    
    def test_starts_with_underscore_raises_error(self):
        """Test that starting with underscore raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            PipelineId("_test_pipeline")
    
    def test_ends_with_underscore_raises_error(self):
        """Test that ending with underscore raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            PipelineId("test_pipeline_")
    
    def test_only_special_characters_raises_error(self):
        """Test that only special characters raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            PipelineId("---")
    
    def test_generate_creates_valid_id(self):
        """Test that generate() creates a valid pipeline ID."""
        pipeline_id = PipelineId.generate()
        
        # Should be valid
        assert isinstance(pipeline_id, PipelineId)
        assert pipeline_id.value.startswith("pipeline-")
        assert len(pipeline_id.value) > 10  # "pipeline-" + 8 hex chars
        
        # Should be unique
        another_id = PipelineId.generate()
        assert pipeline_id.value != another_id.value
    
    def test_from_name_simple(self):
        """Test creating ID from simple name."""
        pipeline_id = PipelineId.from_name("Article Generator")
        assert pipeline_id.value == "article-generator"
    
    def test_from_name_complex(self):
        """Test creating ID from complex name."""
        pipeline_id = PipelineId.from_name("   Quick  Article  Writer  v2.0   ")
        assert pipeline_id.value == "quick-article-writer-v2-0"
    
    def test_from_name_special_characters(self):
        """Test creating ID from name with special characters."""
        pipeline_id = PipelineId.from_name("User's Content Generator!")
        assert pipeline_id.value == "user-s-content-generator"
    
    def test_from_name_short_name_gets_prefix(self):
        """Test that short names get pipeline prefix."""
        pipeline_id = PipelineId.from_name("AI")
        assert pipeline_id.value == "pipeline-ai"
    
    def test_from_name_long_name_gets_truncated(self):
        """Test that long names get truncated."""
        long_name = "This is a very long pipeline name that exceeds the maximum allowed length"
        pipeline_id = PipelineId.from_name(long_name)
        
        assert len(pipeline_id.value) <= 64
        assert not pipeline_id.value.endswith("-")  # Should not end with hyphen
    
    def test_from_name_empty_gets_prefix(self):
        """Test that empty name gets pipeline prefix."""
        pipeline_id = PipelineId.from_name("")
        assert pipeline_id.value == "pipeline-"
    
    def test_from_name_whitespace_only_gets_prefix(self):
        """Test that whitespace-only name gets pipeline prefix."""
        pipeline_id = PipelineId.from_name("   ")
        assert pipeline_id.value == "pipeline-"
    
    def test_equality(self):
        """Test pipeline ID equality."""
        id1 = PipelineId("test-pipeline")
        id2 = PipelineId("test-pipeline")
        id3 = PipelineId("other-pipeline")
        
        assert id1 == id2
        assert id1 != id3
        assert id2 != id3
    
    def test_hash_consistency(self):
        """Test that equal pipeline IDs have equal hashes."""
        id1 = PipelineId("test-pipeline")
        id2 = PipelineId("test-pipeline")
        id3 = PipelineId("other-pipeline")
        
        assert hash(id1) == hash(id2)
        assert hash(id1) != hash(id3)
    
    def test_use_in_set(self):
        """Test using pipeline IDs in sets."""
        id1 = PipelineId("test-pipeline")
        id2 = PipelineId("test-pipeline")  # Same value
        id3 = PipelineId("other-pipeline")
        
        pipeline_set = {id1, id2, id3}
        
        # Should only have 2 unique IDs
        assert len(pipeline_set) == 2
        assert id1 in pipeline_set
        assert id3 in pipeline_set
    
    def test_use_in_dict(self):
        """Test using pipeline IDs as dictionary keys."""
        id1 = PipelineId("test-pipeline")
        id2 = PipelineId("test-pipeline")  # Same value
        id3 = PipelineId("other-pipeline")
        
        pipeline_dict = {
            id1: "first",
            id2: "second",  # Should overwrite first
            id3: "third"
        }
        
        # Should only have 2 entries
        assert len(pipeline_dict) == 2
        assert pipeline_dict[id1] == "second"  # Overwritten
        assert pipeline_dict[id3] == "third"
    
    def test_immutability(self):
        """Test that pipeline ID is immutable."""
        pipeline_id = PipelineId("test-pipeline")
        
        # Should not be able to modify value
        with pytest.raises(AttributeError):
            pipeline_id.value = "modified"
    
    def test_dataclass_frozen(self):
        """Test that dataclass is frozen."""
        pipeline_id = PipelineId("test-pipeline")
        
        # Should not be able to add new attributes
        with pytest.raises(AttributeError):
            pipeline_id.new_attribute = "value"
    
    def test_repr_includes_value(self):
        """Test that repr includes the value."""
        pipeline_id = PipelineId("test-pipeline")
        repr_str = repr(pipeline_id)
        
        assert "test-pipeline" in repr_str
        assert "PipelineId" in repr_str
    
    def test_boundary_conditions(self):
        """Test boundary conditions for length validation."""
        # Minimum valid length (3 characters)
        min_valid = PipelineId("abc")
        assert min_valid.value == "abc"
        
        # Maximum valid length (64 characters)
        max_valid = "a" * 62 + "bc"  # 64 chars total, starts and ends with letters
        max_pipeline_id = PipelineId(max_valid)
        assert max_pipeline_id.value == max_valid
        assert len(max_pipeline_id.value) == 64
    
    def test_single_character_prefix_suffix(self):
        """Test IDs with single characters around special characters."""
        # Valid: single char + special + single char
        valid_id = PipelineId("a-b")
        assert valid_id.value == "a-b"
        
        valid_id2 = PipelineId("x_y")
        assert valid_id2.value == "x_y"
        
        # Valid: longer combinations
        valid_id3 = PipelineId("a-b-c")
        assert valid_id3.value == "a-b-c"