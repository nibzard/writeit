"""TokenCount value object.

Value object representing token usage metrics with validation.
"""

from dataclasses import dataclass
from typing import Self, Optional


@dataclass(frozen=True, eq=True)
class TokenCount:
    """Value object representing token count with validation.
    
    Ensures token counts are non-negative and within reasonable bounds.
    
    Examples:
        tokens = TokenCount.from_int(1500)
        tokens = TokenCount.zero()
        
        # Operations
        total = TokenCount.from_int(1000) + TokenCount.from_int(500)
        remaining = TokenCount.from_int(2000) - TokenCount.from_int(1200)
        
        # Validation
        assert tokens.is_valid()
        assert not tokens.is_zero()
        assert tokens.is_within_limit(2000)
    """
    
    value: int
    
    def __post_init__(self) -> None:
        """Validate token count."""
        if not isinstance(self.value, int):
            raise TypeError("Token count must be an integer")
            
        if self.value < 0:
            raise ValueError(f"Token count cannot be negative: {self.value}")
            
        # Reasonable upper bound (1M tokens)
        if self.value > 1_000_000:
            raise ValueError(f"Token count exceeds maximum: {self.value} (max 1,000,000)")
    
    @classmethod
    def from_int(cls, value: int) -> Self:
        """Create token count from integer.
        
        Args:
            value: Token count value
            
        Returns:
            Token count instance
            
        Raises:
            ValueError: If value is invalid
            TypeError: If value is not an integer
        """
        return cls(value)
    
    @classmethod
    def zero(cls) -> Self:
        """Create zero token count.
        
        Returns:
            Zero token count
        """
        return cls(0)
    
    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create token count from string.
        
        Args:
            value: String representation of token count
            
        Returns:
            Token count instance
            
        Raises:
            ValueError: If string cannot be parsed or value is invalid
        """
        try:
            int_value = int(value.strip())
            return cls.from_int(int_value)
        except ValueError as e:
            raise ValueError(f"Invalid token count string: '{value}'") from e
    
    def is_zero(self) -> bool:
        """Check if token count is zero.
        
        Returns:
            True if count is zero
        """
        return self.value == 0
    
    def is_positive(self) -> bool:
        """Check if token count is positive.
        
        Returns:
            True if count is greater than zero
        """
        return self.value > 0
    
    def is_within_limit(self, limit: int) -> bool:
        """Check if token count is within limit.
        
        Args:
            limit: Maximum allowed tokens
            
        Returns:
            True if count is within limit
        """
        return self.value <= limit
    
    def is_within_percentage(self, total: 'TokenCount', percentage: float) -> bool:
        """Check if token count is within percentage of total.
        
        Args:
            total: Total token count
            percentage: Percentage threshold (0.0 to 1.0)
            
        Returns:
            True if count is within percentage
        """
        if total.is_zero():
            return self.is_zero()
            
        threshold = int(total.value * percentage)
        return self.value <= threshold
    
    def percentage_of(self, total: 'TokenCount') -> float:
        """Calculate percentage of total.
        
        Args:
            total: Total token count
            
        Returns:
            Percentage (0.0 to 1.0)
        """
        if total.is_zero():
            return 0.0 if self.is_zero() else float('inf')
            
        return self.value / total.value
    
    def add(self, other: 'TokenCount') -> Self:
        """Add token counts.
        
        Args:
            other: Token count to add
            
        Returns:
            Sum of token counts
        """
        return TokenCount.from_int(self.value + other.value)
    
    def subtract(self, other: 'TokenCount') -> Self:
        """Subtract token counts.
        
        Args:
            other: Token count to subtract
            
        Returns:
            Difference of token counts
            
        Raises:
            ValueError: If result would be negative
        """
        result = self.value - other.value
        if result < 0:
            raise ValueError(f"Cannot subtract {other.value} from {self.value} (would be negative)")
        return TokenCount.from_int(result)
    
    def multiply(self, factor: float) -> Self:
        """Multiply token count by factor.
        
        Args:
            factor: Multiplication factor
            
        Returns:
            Multiplied token count
        """
        result = int(self.value * factor)
        return TokenCount.from_int(result)
    
    def min(self, other: 'TokenCount') -> Self:
        """Get minimum of two token counts.
        
        Args:
            other: Other token count
            
        Returns:
            Minimum token count
        """
        return TokenCount.from_int(min(self.value, other.value))
    
    def max(self, other: 'TokenCount') -> Self:
        """Get maximum of two token counts.
        
        Args:
            other: Other token count
            
        Returns:
            Maximum token count
        """
        return TokenCount.from_int(max(self.value, other.value))
    
    def to_human_readable(self) -> str:
        """Convert to human-readable format.
        
        Returns:
            Human-readable token count
        """
        if self.value >= 1_000_000:
            return f"{self.value / 1_000_000:.1f}M tokens"
        elif self.value >= 1_000:
            return f"{self.value / 1_000:.1f}K tokens"
        else:
            return f"{self.value} tokens"
    
    def to_cost_estimate(self, cost_per_1k_tokens: float) -> float:
        """Estimate cost based on tokens.
        
        Args:
            cost_per_1k_tokens: Cost per 1000 tokens
            
        Returns:
            Estimated cost in currency units
        """
        return (self.value / 1000) * cost_per_1k_tokens
    
    # Operator overloads for convenience
    def __add__(self, other: 'TokenCount') -> Self:
        """Add operator."""
        return self.add(other)
    
    def __sub__(self, other: 'TokenCount') -> Self:
        """Subtract operator."""
        return self.subtract(other)
    
    def __mul__(self, factor: float) -> Self:
        """Multiply operator."""
        return self.multiply(factor)
    
    def __lt__(self, other: 'TokenCount') -> bool:
        """Less than operator."""
        return self.value < other.value
    
    def __le__(self, other: 'TokenCount') -> bool:
        """Less than or equal operator."""
        return self.value <= other.value
    
    def __gt__(self, other: 'TokenCount') -> bool:
        """Greater than operator."""
        return self.value > other.value
    
    def __ge__(self, other: 'TokenCount') -> bool:
        """Greater than or equal operator."""
        return self.value >= other.value
    
    def __int__(self) -> int:
        """Convert to integer."""
        return self.value
    
    def __str__(self) -> str:
        """String representation."""
        return str(self.value)
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"TokenCount({self.value})"
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)
