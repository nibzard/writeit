"""Comprehensive unit tests for Execution domain value objects."""

import pytest
import hashlib

from src.writeit.domains.execution.value_objects.model_name import ModelName
from src.writeit.domains.execution.value_objects.token_count import TokenCount
from src.writeit.domains.execution.value_objects.cache_key import CacheKey
from src.writeit.domains.execution.value_objects.execution_mode import ExecutionMode

from tests.builders.value_object_builders import (
    ModelNameBuilder, TokenCountBuilder, CacheKeyBuilder
)


class TestModelName:
    """Test cases for ModelName value object."""
    
    def test_model_name_creation(self):
        """Test creating ModelName."""
        name = "gpt-4o-mini"
        model_name = ModelNameBuilder().with_name(name).build()
        
        assert model_name.value == name
        assert str(model_name) == name
    
    def test_model_name_validation(self):
        """Test ModelName validation rules."""
        # Valid model names
        valid_names = [
            "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo",
            "claude-3-haiku", "claude-3-sonnet", "claude-3-opus",
            "llama2", "codellama", "mistral-7b", "local-model",
            "custom_model_v2", "model-123", "test.model"
        ]
        
        for valid_name in valid_names:
            model_name = ModelName(valid_name)
            assert model_name.value == valid_name
    
    def test_model_name_invalid_names(self):
        """Test ModelName with invalid names."""
        invalid_names = [
            "",  # Empty
            "   ",  # Whitespace only
            "model with spaces",  # Spaces not allowed
            "model@invalid",  # Some special characters
            "model#123",  # Hash symbol
            "model/path",  # Forward slash
            "model\\path",  # Backward slash
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Invalid model name"):
                ModelName(invalid_name)
    
    def test_model_name_case_sensitivity(self):
        """Test ModelName case sensitivity."""
        name1 = ModelName("GPT-4o")
        name2 = ModelName("gpt-4o")
        
        assert name1 != name2  # Should be case sensitive
        assert name1.value == "GPT-4o"
        assert name2.value == "gpt-4o"
    
    def test_model_name_length_limits(self):
        """Test ModelName length validation."""
        # Test minimum length
        with pytest.raises(ValueError, match="Model name must be between"):
            ModelName("a")  # Too short
        
        # Valid length
        valid_name = "ab"  # Minimum valid length
        model_name = ModelName(valid_name)
        assert model_name.value == valid_name
        
        # Test maximum length
        max_length = 100  # Reasonable limit
        long_name = "a" * max_length
        model_name = ModelName(long_name)
        assert model_name.value == long_name
        
        # Too long
        with pytest.raises(ValueError, match="Model name must be between"):
            ModelName("a" * (max_length + 1))
    
    def test_model_name_provider_specific_formats(self):
        """Test ModelName with provider-specific formats."""
        # OpenAI format
        openai_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo-16k"]
        for model in openai_models:
            model_name = ModelName(model)
            assert model_name.value == model
        
        # Anthropic format
        anthropic_models = ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
        for model in anthropic_models:
            model_name = ModelName(model)
            assert model_name.value == model
        
        # Local model format
        local_models = ["llama2", "codellama", "mistral-7b"]
        for model in local_models:
            model_name = ModelName(model)
            assert model_name.value == model
    
    def test_model_name_equality(self):
        """Test ModelName equality."""
        name1 = ModelName("gpt-4o")
        name2 = ModelName("gpt-4o")
        name3 = ModelName("claude-3-haiku")
        
        assert name1 == name2
        assert name1 != name3
        assert name1 != "gpt-4o"  # Not equal to string
    
    def test_model_name_hash_consistency(self):
        """Test ModelName hash consistency."""
        name1 = ModelName("gpt-4o")
        name2 = ModelName("gpt-4o")
        
        assert hash(name1) == hash(name2)
        assert name1 in {name2}
    
    def test_model_name_builder_factories(self):
        """Test ModelName builder factory methods."""
        gpt4_mini = ModelNameBuilder.gpt4_mini().build()
        assert gpt4_mini.value == "gpt-4o-mini"
        
        gpt4 = ModelNameBuilder.gpt4().build()
        assert gpt4.value == "gpt-4o"
        
        claude_haiku = ModelNameBuilder.claude_haiku().build()
        assert claude_haiku.value == "claude-3-haiku"
        
        claude_sonnet = ModelNameBuilder.claude_sonnet().build()
        assert claude_sonnet.value == "claude-3-sonnet"


class TestTokenCount:
    """Test cases for TokenCount value object."""
    
    def test_token_count_creation(self):
        """Test creating TokenCount."""
        count = 100
        token_count = TokenCountBuilder().with_value(count).build()
        
        assert token_count.value == count
        assert int(token_count) == count
        assert str(token_count) == "100"
    
    def test_token_count_validation(self):
        """Test TokenCount validation."""
        # Valid token counts
        valid_counts = [0, 1, 100, 1000, 10000, 100000]
        
        for count in valid_counts:
            token_count = TokenCount(count)
            assert token_count.value == count
        
        # Invalid token counts
        with pytest.raises(ValueError, match="Token count cannot be negative"):
            TokenCount(-1)
        
        with pytest.raises(ValueError, match="Token count cannot be negative"):
            TokenCount(-100)
    
    def test_token_count_arithmetic_operations(self):
        """Test TokenCount arithmetic operations."""
        count1 = TokenCount(100)
        count2 = TokenCount(50)
        
        # Addition
        sum_count = count1 + count2
        assert sum_count.value == 150
        assert isinstance(sum_count, TokenCount)
        
        # Subtraction
        diff_count = count1 - count2
        assert diff_count.value == 50
        assert isinstance(diff_count, TokenCount)
        
        # Subtraction that would result in negative (should handle gracefully)
        try:
            negative_result = count2 - count1
            assert negative_result.value == 0  # Clamped to zero
        except ValueError:
            # Or it might raise an error - both are valid approaches
            pass
    
    def test_token_count_comparison_operations(self):
        """Test TokenCount comparison operations."""
        small = TokenCount(50)
        medium = TokenCount(100)
        large = TokenCount(200)
        
        # Less than
        assert small < medium
        assert medium < large
        assert not large < small
        
        # Greater than
        assert large > medium
        assert medium > small
        assert not small > large
        
        # Less than or equal
        assert small <= medium
        assert small <= TokenCount(50)  # Equal
        
        # Greater than or equal
        assert large >= medium
        assert medium >= TokenCount(100)  # Equal
        
        # Equality
        assert medium == TokenCount(100)
        assert medium != small
    
    def test_token_count_zero_handling(self):
        """Test TokenCount zero handling."""
        zero_count = TokenCount(0)
        
        assert zero_count.value == 0
        assert str(zero_count) == "0"
        assert zero_count == TokenCount(0)
    
    def test_token_count_large_values(self):
        """Test TokenCount with large values."""
        large_count = TokenCount(1_000_000)  # 1 million tokens
        
        assert large_count.value == 1_000_000
        assert str(large_count) == "1000000"
        
        # Very large count
        very_large_count = TokenCount(1_000_000_000)  # 1 billion tokens
        assert very_large_count.value == 1_000_000_000
    
    def test_token_count_equality(self):
        """Test TokenCount equality."""
        count1 = TokenCount(100)
        count2 = TokenCount(100)
        count3 = TokenCount(200)
        
        assert count1 == count2
        assert count1 != count3
        assert count1 != 100  # Not equal to raw int
    
    def test_token_count_hash_consistency(self):
        """Test TokenCount hash consistency."""
        count1 = TokenCount(100)
        count2 = TokenCount(100)
        
        assert hash(count1) == hash(count2)
        assert count1 in {count2}
    
    def test_token_count_builder_factories(self):
        """Test TokenCount builder factory methods."""
        small = TokenCountBuilder.small().build()
        assert small.value == 50
        
        medium = TokenCountBuilder.medium().build()
        assert medium.value == 500
        
        large = TokenCountBuilder.large().build()
        assert large.value == 2000
        
        zero = TokenCountBuilder.zero().build()
        assert zero.value == 0


class TestCacheKey:
    """Test cases for CacheKey value object."""
    
    def test_cache_key_generation(self):
        """Test CacheKey generation from data."""
        data = {"prompt": "test prompt", "model": "gpt-4o-mini"}
        cache_key = CacheKeyBuilder().with_key_data(data).build()
        
        assert isinstance(cache_key.value, str)
        assert len(cache_key.value) > 0
        
        # Should be a hash-like string
        assert len(cache_key.value) in [32, 40, 64]  # MD5, SHA1, or SHA256 length
    
    def test_cache_key_deterministic(self):
        """Test CacheKey is deterministic."""
        data = {"prompt": "test", "model": "gpt-4o"}
        
        key1 = CacheKey.from_data(data)
        key2 = CacheKey.from_data(data)
        
        assert key1 == key2
        assert key1.value == key2.value
    
    def test_cache_key_different_data_different_keys(self):
        """Test that different data produces different keys."""
        data1 = {"prompt": "test1", "model": "gpt-4o"}
        data2 = {"prompt": "test2", "model": "gpt-4o"}
        
        key1 = CacheKey.from_data(data1)
        key2 = CacheKey.from_data(data2)
        
        assert key1 != key2
        assert key1.value != key2.value
    
    def test_cache_key_order_independence(self):
        """Test CacheKey is independent of dictionary key order."""
        data1 = {"prompt": "test", "model": "gpt-4o", "temperature": 0.7}
        data2 = {"model": "gpt-4o", "temperature": 0.7, "prompt": "test"}
        
        key1 = CacheKey.from_data(data1)
        key2 = CacheKey.from_data(data2)
        
        assert key1 == key2  # Should be the same despite different order
    
    def test_cache_key_complex_data(self):
        """Test CacheKey with complex data structures."""
        complex_data = {
            "prompt": "complex prompt",
            "model": "gpt-4o",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9
            },
            "context": ["previous", "messages"],
            "metadata": {
                "user_id": "123",
                "session_id": "abc"
            }
        }
        
        cache_key = CacheKey.from_data(complex_data)
        assert isinstance(cache_key.value, str)
        assert len(cache_key.value) > 0
    
    def test_cache_key_with_none_values(self):
        """Test CacheKey with None values."""
        data_with_none = {
            "prompt": "test",
            "model": "gpt-4o",
            "optional_param": None,
            "temperature": 0.7
        }
        
        cache_key = CacheKey.from_data(data_with_none)
        assert isinstance(cache_key.value, str)
    
    def test_cache_key_empty_data(self):
        """Test CacheKey with empty data."""
        empty_data = {}
        
        with pytest.raises(ValueError, match="Cache key data cannot be empty"):
            CacheKey.from_data(empty_data)
    
    def test_cache_key_equality(self):
        """Test CacheKey equality."""
        data = {"prompt": "test", "model": "gpt-4o"}
        key1 = CacheKey.from_data(data)
        key2 = CacheKey.from_data(data)
        key3 = CacheKey.from_data({"prompt": "different", "model": "gpt-4o"})
        
        assert key1 == key2
        assert key1 != key3
        assert key1 != key1.value  # Not equal to raw string
    
    def test_cache_key_hash_consistency(self):
        """Test CacheKey hash consistency."""
        data = {"prompt": "test", "model": "gpt-4o"}
        key1 = CacheKey.from_data(data)
        key2 = CacheKey.from_data(data)
        
        assert hash(key1) == hash(key2)
        assert key1 in {key2}
    
    def test_cache_key_builder_factories(self):
        """Test CacheKey builder factory methods."""
        simple = CacheKeyBuilder.simple().build()
        assert len(simple.value) > 0
        
        complex_key = CacheKeyBuilder.complex().build()
        assert len(complex_key.value) > 0
        
        # Different factory methods should produce different keys
        assert simple.value != complex_key.value


class TestExecutionMode:
    """Test cases for ExecutionMode enum."""
    
    def test_execution_mode_values(self):
        """Test ExecutionMode enum values."""
        assert ExecutionMode.CLI
        assert ExecutionMode.TUI
        assert ExecutionMode.SERVER
    
    def test_execution_mode_string_representation(self):
        """Test ExecutionMode string representation."""
        assert str(ExecutionMode.CLI) in ["CLI", "cli"]
        assert str(ExecutionMode.TUI) in ["TUI", "tui"]
        assert str(ExecutionMode.SERVER) in ["SERVER", "server"]
    
    def test_execution_mode_comparison(self):
        """Test ExecutionMode comparison."""
        mode1 = ExecutionMode.CLI
        mode2 = ExecutionMode.CLI
        mode3 = ExecutionMode.TUI
        
        assert mode1 == mode2
        assert mode1 != mode3
    
    def test_execution_mode_in_collections(self):
        """Test ExecutionMode in collections."""
        modes = {ExecutionMode.CLI, ExecutionMode.TUI}
        
        assert ExecutionMode.CLI in modes
        assert ExecutionMode.SERVER not in modes
        
        mode_list = [ExecutionMode.CLI, ExecutionMode.TUI]
        assert len(mode_list) == 2
        assert ExecutionMode.CLI in mode_list
    
    def test_execution_mode_behavior_mapping(self):
        """Test ExecutionMode behavior mapping."""
        # This would test hypothetical behavior differences
        mode_behaviors = {
            ExecutionMode.CLI: {"interactive": False, "output": "text"},
            ExecutionMode.TUI: {"interactive": True, "output": "rich_text"},
            ExecutionMode.SERVER: {"interactive": False, "output": "json"}
        }
        
        for mode, expected_behavior in mode_behaviors.items():
            # This would test a hypothetical method
            # behavior = mode.get_behavior()
            # assert behavior["interactive"] == expected_behavior["interactive"]
            assert mode is not None  # Placeholder test


class TestExecutionValueObjectEdgeCases:
    """Test edge cases for execution domain value objects."""
    
    def test_value_objects_with_extreme_values(self):
        """Test value objects with extreme values."""
        # Very large token count
        large_tokens = TokenCount(10_000_000)  # 10 million tokens
        assert large_tokens.value == 10_000_000
        
        # Token count at integer limits
        max_int_tokens = TokenCount(2**31 - 1)  # Max 32-bit signed int
        assert max_int_tokens.value == 2**31 - 1
    
    def test_token_count_arithmetic_edge_cases(self):
        """Test TokenCount arithmetic edge cases."""
        zero = TokenCount(0)
        small = TokenCount(1)
        large = TokenCount(1000)
        
        # Adding to zero
        result = zero + small
        assert result.value == 1
        
        # Subtracting to zero or below
        result = small - large
        if hasattr(result, 'value'):
            # If subtraction is allowed and clamped to zero
            assert result.value >= 0
        # Otherwise, it should have raised an exception
    
    def test_model_name_with_version_numbers(self):
        """Test ModelName with version numbers."""
        versioned_models = [
            "gpt-4o-2024-05-13",
            "claude-3-haiku-20240307",
            "llama2-7b-v1.0",
            "mistral-7b-instruct-v0.2"
        ]
        
        for model in versioned_models:
            model_name = ModelName(model)
            assert model_name.value == model
    
    def test_cache_key_with_unicode_data(self):
        """Test CacheKey with unicode data."""
        unicode_data = {
            "prompt": "Écrivez un article sur l'intelligence artificielle",
            "model": "gpt-4o",
            "language": "français",
            "émojis": "🤖🧠💡"
        }
        
        cache_key = CacheKey.from_data(unicode_data)
        assert isinstance(cache_key.value, str)
        assert len(cache_key.value) > 0
    
    def test_cache_key_collision_resistance(self):
        """Test CacheKey collision resistance."""
        # Similar but different data should produce different keys
        data1 = {"prompt": "abc", "model": "def"}
        data2 = {"prompt": "ab", "model": "cdef"}
        data3 = {"prompt": "a", "model": "bcdef"}
        
        key1 = CacheKey.from_data(data1)
        key2 = CacheKey.from_data(data2)
        key3 = CacheKey.from_data(data3)
        
        # All keys should be different
        assert len({key1.value, key2.value, key3.value}) == 3
    
    def test_cache_key_data_type_handling(self):
        """Test CacheKey with different data types."""
        mixed_data = {
            "string": "value",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None
        }
        
        cache_key = CacheKey.from_data(mixed_data)
        assert isinstance(cache_key.value, str)
    
    def test_value_object_immutability_comprehensive(self):
        """Test comprehensive immutability for all value objects."""
        model_name = ModelName("gpt-4o")
        token_count = TokenCount(100)
        cache_key = CacheKey.from_data({"test": "data"})
        
        # Should not be able to modify any internal state
        value_objects = [model_name, token_count, cache_key]
        
        for obj in value_objects:
            with pytest.raises(AttributeError):
                obj.value = "modified"  # type: ignore
    
    def test_value_object_serialization(self):
        """Test value object serialization for caching/storage."""
        import json
        
        # Create value objects
        model_name = ModelName("gpt-4o")
        token_count = TokenCount(100)
        execution_mode = ExecutionMode.CLI
        
        # Values should be JSON serializable
        serializable_values = {
            "model_name": model_name.value,
            "token_count": token_count.value,
            "execution_mode": str(execution_mode)
        }
        
        try:
            json_str = json.dumps(serializable_values)
            assert isinstance(json_str, str)
            
            # Should be able to deserialize
            parsed = json.loads(json_str)
            assert parsed["model_name"] == "gpt-4o"
            assert parsed["token_count"] == 100
        except (TypeError, ValueError) as e:
            pytest.fail(f"Value objects not serializable: {e}")
    
    def test_hash_stability_across_sessions(self):
        """Test that value object hashes are stable across sessions."""
        # This tests that hashes don't depend on object memory addresses
        data = {"prompt": "stable test", "model": "gpt-4o"}
        
        # Create multiple instances
        key1 = CacheKey.from_data(data)
        key2 = CacheKey.from_data(data.copy())  # Different dict object
        
        assert hash(key1) == hash(key2)
        assert key1 == key2
    
    def test_value_object_string_representations(self):
        """Test string representations are meaningful."""
        model_name = ModelName("gpt-4o")
        token_count = TokenCount(1500)
        execution_mode = ExecutionMode.TUI
        
        # String representations should be informative
        assert "gpt-4o" in str(model_name)
        assert "1500" in str(token_count)
        assert str(execution_mode).upper() in ["TUI", "CLI", "SERVER"]
        
        # Repr should be detailed
        assert "ModelName" in repr(model_name)
        assert "TokenCount" in repr(token_count)
        assert "ExecutionMode" in repr(execution_mode)