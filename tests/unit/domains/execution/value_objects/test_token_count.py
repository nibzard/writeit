"""Unit tests for TokenCount value object.

Tests value object behavior, validation, and calculations.
"""

import pytest
from writeit.domains.execution.value_objects.token_count import TokenCount


class TestTokenCount:
    """Test TokenCount value object behavior and validation."""
    
    def test_create_valid_token_count(self):
        """Test creating a valid token count."""
        token_count = TokenCount(
            input_tokens=100,
            output_tokens=200,
            total_tokens=300
        )
        
        assert token_count.input_tokens == 100
        assert token_count.output_tokens == 200
        assert token_count.total_tokens == 300
    
    def test_create_with_calculated_total(self):
        """Test creating token count with auto-calculated total."""
        token_count = TokenCount(
            input_tokens=150,
            output_tokens=250
        )
        
        assert token_count.input_tokens == 150
        assert token_count.output_tokens == 250
        assert token_count.total_tokens == 400  # Auto-calculated
    
    def test_negative_input_tokens_raises_error(self):
        """Test that negative input tokens raise ValueError."""
        with pytest.raises(ValueError, match="Input tokens cannot be negative"):
            TokenCount(input_tokens=-1, output_tokens=100)
    
    def test_negative_output_tokens_raises_error(self):
        """Test that negative output tokens raise ValueError."""
        with pytest.raises(ValueError, match="Output tokens cannot be negative"):
            TokenCount(input_tokens=100, output_tokens=-1)
    
    def test_negative_total_tokens_raises_error(self):
        """Test that negative total tokens raise ValueError."""
        with pytest.raises(ValueError, match="Total tokens cannot be negative"):
            TokenCount(input_tokens=100, output_tokens=200, total_tokens=-1)
    
    def test_non_integer_input_tokens_raises_error(self):
        """Test that non-integer input tokens raise TypeError."""
        with pytest.raises(TypeError, match="Input tokens must be an integer"):
            TokenCount(input_tokens=100.5, output_tokens=200)
    
    def test_non_integer_output_tokens_raises_error(self):
        """Test that non-integer output tokens raise TypeError."""
        with pytest.raises(TypeError, match="Output tokens must be an integer"):
            TokenCount(input_tokens=100, output_tokens=200.5)
    
    def test_non_integer_total_tokens_raises_error(self):
        """Test that non-integer total tokens raise TypeError."""
        with pytest.raises(TypeError, match="Total tokens must be an integer"):
            TokenCount(input_tokens=100, output_tokens=200, total_tokens=300.5)
    
    def test_inconsistent_total_raises_error(self):
        """Test that inconsistent total raises ValueError."""
        with pytest.raises(ValueError, match="Total tokens.*does not match sum"):
            TokenCount(
                input_tokens=100,
                output_tokens=200,
                total_tokens=250  # Should be 300
            )
    
    def test_zero_tokens_allowed(self):
        """Test that zero tokens are allowed."""
        token_count = TokenCount(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0
        )
        
        assert token_count.input_tokens == 0
        assert token_count.output_tokens == 0
        assert token_count.total_tokens == 0
    
    def test_only_input_tokens(self):
        """Test creating with only input tokens."""
        token_count = TokenCount(input_tokens=100, output_tokens=0)
        
        assert token_count.input_tokens == 100
        assert token_count.output_tokens == 0
        assert token_count.total_tokens == 100
    
    def test_only_output_tokens(self):
        """Test creating with only output tokens."""
        token_count = TokenCount(input_tokens=0, output_tokens=200)
        
        assert token_count.input_tokens == 0
        assert token_count.output_tokens == 200
        assert token_count.total_tokens == 200
    
    def test_add_token_counts(self):
        """Test adding token counts together."""
        count1 = TokenCount(input_tokens=100, output_tokens=150)
        count2 = TokenCount(input_tokens=50, output_tokens=75)
        
        result = count1 + count2
        
        assert result.input_tokens == 150
        assert result.output_tokens == 225
        assert result.total_tokens == 375
    
    def test_subtract_token_counts(self):
        """Test subtracting token counts."""
        count1 = TokenCount(input_tokens=200, output_tokens=300)
        count2 = TokenCount(input_tokens=50, output_tokens=100)
        
        result = count1 - count2
        
        assert result.input_tokens == 150
        assert result.output_tokens == 200
        assert result.total_tokens == 350
    
    def test_subtract_resulting_in_negative_raises_error(self):
        """Test that subtraction resulting in negative raises ValueError."""
        count1 = TokenCount(input_tokens=50, output_tokens=75)
        count2 = TokenCount(input_tokens=100, output_tokens=50)
        
        with pytest.raises(ValueError, match="cannot be negative"):
            count1 - count2
    
    def test_multiply_by_scalar(self):
        """Test multiplying token count by scalar."""
        count = TokenCount(input_tokens=100, output_tokens=150)
        
        result = count * 3
        
        assert result.input_tokens == 300
        assert result.output_tokens == 450
        assert result.total_tokens == 750
    
    def test_multiply_by_zero(self):
        """Test multiplying token count by zero."""
        count = TokenCount(input_tokens=100, output_tokens=150)
        
        result = count * 0
        
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.total_tokens == 0
    
    def test_multiply_by_negative_raises_error(self):
        """Test that multiplying by negative raises ValueError."""
        count = TokenCount(input_tokens=100, output_tokens=150)
        
        with pytest.raises(ValueError, match="Multiplier cannot be negative"):
            count * -1
    
    def test_multiply_by_non_number_raises_error(self):
        """Test that multiplying by non-number raises TypeError."""
        count = TokenCount(input_tokens=100, output_tokens=150)
        
        with pytest.raises(TypeError, match="Multiplier must be a number"):
            count * "invalid"
    
    def test_divide_by_scalar(self):
        """Test dividing token count by scalar."""
        count = TokenCount(input_tokens=300, output_tokens=450)
        
        result = count / 3
        
        assert result.input_tokens == 100
        assert result.output_tokens == 150
        assert result.total_tokens == 250
    
    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ZeroDivisionError."""
        count = TokenCount(input_tokens=100, output_tokens=150)
        
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            count / 0
    
    def test_divide_by_negative_raises_error(self):
        """Test that dividing by negative raises ValueError."""
        count = TokenCount(input_tokens=100, output_tokens=150)
        
        with pytest.raises(ValueError, match="Divisor cannot be negative"):
            count / -1
    
    def test_get_ratio_input_to_output(self):
        """Test getting ratio of input to output tokens."""
        count = TokenCount(input_tokens=100, output_tokens=200)
        
        ratio = count.get_input_output_ratio()
        assert ratio == 0.5
    
    def test_get_ratio_with_zero_output(self):
        """Test getting ratio when output tokens is zero."""
        count = TokenCount(input_tokens=100, output_tokens=0)
        
        ratio = count.get_input_output_ratio()
        assert ratio == float('inf')
    
    def test_get_ratio_with_zero_input(self):
        """Test getting ratio when input tokens is zero."""
        count = TokenCount(input_tokens=0, output_tokens=200)
        
        ratio = count.get_input_output_ratio()
        assert ratio == 0.0
    
    def test_get_ratio_with_both_zero(self):
        """Test getting ratio when both input and output are zero."""
        count = TokenCount(input_tokens=0, output_tokens=0)
        
        ratio = count.get_input_output_ratio()
        assert ratio == 0.0
    
    def test_get_percentage_input(self):
        """Test getting percentage of input tokens."""
        count = TokenCount(input_tokens=100, output_tokens=200)
        
        percentage = count.get_input_percentage()
        assert percentage == pytest.approx(33.33, rel=1e-2)
    
    def test_get_percentage_output(self):
        """Test getting percentage of output tokens."""
        count = TokenCount(input_tokens=100, output_tokens=200)
        
        percentage = count.get_output_percentage()
        assert percentage == pytest.approx(66.67, rel=1e-2)
    
    def test_get_percentage_with_zero_total(self):
        """Test getting percentages when total is zero."""
        count = TokenCount(input_tokens=0, output_tokens=0)
        
        input_percentage = count.get_input_percentage()
        output_percentage = count.get_output_percentage()
        
        assert input_percentage == 0.0
        assert output_percentage == 0.0
    
    def test_is_zero(self):
        """Test checking if token count is zero."""
        zero_count = TokenCount(input_tokens=0, output_tokens=0)
        non_zero_count = TokenCount(input_tokens=1, output_tokens=0)
        
        assert zero_count.is_zero() is True
        assert non_zero_count.is_zero() is False
    
    def test_is_empty_input(self):
        """Test checking if input tokens is empty."""
        count_with_input = TokenCount(input_tokens=100, output_tokens=200)
        count_without_input = TokenCount(input_tokens=0, output_tokens=200)
        
        assert count_with_input.is_empty_input() is False
        assert count_without_input.is_empty_input() is True
    
    def test_is_empty_output(self):
        """Test checking if output tokens is empty."""
        count_with_output = TokenCount(input_tokens=100, output_tokens=200)
        count_without_output = TokenCount(input_tokens=100, output_tokens=0)
        
        assert count_with_output.is_empty_output() is False
        assert count_without_output.is_empty_output() is True
    
    def test_to_dict(self):
        """Test converting token count to dictionary."""
        count = TokenCount(input_tokens=100, output_tokens=200, total_tokens=300)
        
        result = count.to_dict()
        
        expected = {
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300
        }
        assert result == expected
    
    def test_from_dict(self):
        """Test creating token count from dictionary."""
        data = {
            "input_tokens": 150,
            "output_tokens": 250,
            "total_tokens": 400
        }
        
        count = TokenCount.from_dict(data)
        
        assert count.input_tokens == 150
        assert count.output_tokens == 250
        assert count.total_tokens == 400
    
    def test_from_dict_missing_fields_uses_defaults(self):
        """Test creating token count from dictionary with missing fields."""
        data = {
            "input_tokens": 100
        }
        
        count = TokenCount.from_dict(data)
        
        assert count.input_tokens == 100
        assert count.output_tokens == 0
        assert count.total_tokens == 100
    
    def test_from_dict_with_invalid_data_raises_error(self):
        """Test that creating from invalid dictionary raises error."""
        invalid_data = {
            "input_tokens": -1,
            "output_tokens": 100
        }
        
        with pytest.raises(ValueError):
            TokenCount.from_dict(invalid_data)
    
    def test_equality(self):
        """Test token count equality."""
        count1 = TokenCount(input_tokens=100, output_tokens=200)
        count2 = TokenCount(input_tokens=100, output_tokens=200)
        count3 = TokenCount(input_tokens=150, output_tokens=200)
        
        assert count1 == count2
        assert count1 != count3
        assert count2 != count3
    
    def test_hash_consistency(self):
        """Test that equal token counts have equal hashes."""
        count1 = TokenCount(input_tokens=100, output_tokens=200)
        count2 = TokenCount(input_tokens=100, output_tokens=200)
        count3 = TokenCount(input_tokens=150, output_tokens=200)
        
        assert hash(count1) == hash(count2)
        assert hash(count1) != hash(count3)
    
    def test_comparison_operators(self):
        """Test comparison operators for token counts."""
        count1 = TokenCount(input_tokens=100, output_tokens=100)  # total: 200
        count2 = TokenCount(input_tokens=150, output_tokens=150)  # total: 300
        count3 = TokenCount(input_tokens=200, output_tokens=200)  # total: 400
        
        # Test ordering based on total tokens
        assert count1 < count2 < count3
        assert count3 > count2 > count1
        assert count1 <= count2 <= count3
        assert count3 >= count2 >= count1
    
    def test_string_representation(self):
        """Test string representation."""
        count = TokenCount(input_tokens=100, output_tokens=200, total_tokens=300)
        
        str_repr = str(count)
        assert "100" in str_repr
        assert "200" in str_repr
        assert "300" in str_repr
    
    def test_repr_representation(self):
        """Test debug representation."""
        count = TokenCount(input_tokens=100, output_tokens=200, total_tokens=300)
        
        repr_str = repr(count)
        assert "TokenCount" in repr_str
        assert "input_tokens=100" in repr_str
        assert "output_tokens=200" in repr_str
        assert "total_tokens=300" in repr_str
    
    def test_immutability(self):
        """Test that token count is immutable."""
        count = TokenCount(input_tokens=100, output_tokens=200)
        
        # Should not be able to modify values
        with pytest.raises(AttributeError):
            count.input_tokens = 150
        
        with pytest.raises(AttributeError):
            count.output_tokens = 250
        
        with pytest.raises(AttributeError):
            count.total_tokens = 400
    
    def test_dataclass_frozen(self):
        """Test that dataclass is frozen."""
        count = TokenCount(input_tokens=100, output_tokens=200)
        
        # Should not be able to add new attributes
        with pytest.raises(AttributeError):
            count.new_attribute = "value"
    
    def test_large_numbers(self):
        """Test handling of large token counts."""
        large_count = TokenCount(
            input_tokens=1_000_000,
            output_tokens=2_000_000,
            total_tokens=3_000_000
        )
        
        assert large_count.input_tokens == 1_000_000
        assert large_count.output_tokens == 2_000_000
        assert large_count.total_tokens == 3_000_000
    
    def test_operations_preserve_type(self):
        """Test that arithmetic operations preserve TokenCount type."""
        count1 = TokenCount(input_tokens=100, output_tokens=150)
        count2 = TokenCount(input_tokens=50, output_tokens=75)
        
        addition_result = count1 + count2
        subtraction_result = count1 - count2
        multiplication_result = count1 * 2
        division_result = count1 / 2
        
        assert isinstance(addition_result, TokenCount)
        assert isinstance(subtraction_result, TokenCount)
        assert isinstance(multiplication_result, TokenCount)
        assert isinstance(division_result, TokenCount)