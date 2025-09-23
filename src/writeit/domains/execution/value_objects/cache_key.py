"""CacheKey value object.

Value object representing cache keys for LLM responses with deterministic generation.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Self, Dict, Any, Optional


@dataclass(frozen=True, eq=True)
class CacheKey:
    """Value object representing a cache key for LLM responses.
    
    Generates deterministic cache keys based on request parameters,
    ensuring consistent caching behavior across executions.
    
    Examples:
        # Create from components
        key = CacheKey.from_components(
            model="gpt-4o-mini",
            prompt="Write an article about AI",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Create from request data
        request_data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7
        }
        key = CacheKey.from_request_data(request_data)
        
        # Use as cache key
        cache[str(key)] = response_data
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate cache key."""
        if not self.value:
            raise ValueError("Cache key cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError("Cache key must be a string")
            
        # Validate format (should be hex hash)
        if len(self.value) not in (32, 40, 64):  # MD5, SHA1, SHA256
            raise ValueError(f"Invalid cache key format: {self.value}")
            
        # Check if it's a valid hex string
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError(f"Cache key must be a valid hex string: {self.value}")
    
    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create cache key from string.
        
        Args:
            value: Cache key string
            
        Returns:
            Cache key instance
            
        Raises:
            ValueError: If cache key is invalid
        """
        return cls(value)
    
    @classmethod
    def from_components(
        cls,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Self:
        """Create cache key from request components.
        
        Args:
            model: Model name
            prompt: Prompt text
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            **kwargs: Additional parameters
            
        Returns:
            Generated cache key
        """
        # Build normalized request data
        request_data = {
            "model": model.strip().lower(),
            "prompt": prompt.strip(),
        }
        
        # Add optional parameters if provided
        if temperature is not None:
            request_data["temperature"] = temperature
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
            
        # Add any additional parameters
        for key, value in kwargs.items():
            if value is not None:
                request_data[key] = value
        
        return cls._generate_key(request_data)
    
    @classmethod
    def from_request_data(cls, request_data: Dict[str, Any]) -> Self:
        """Create cache key from request data dictionary.
        
        Args:
            request_data: Request parameters
            
        Returns:
            Generated cache key
        """
        # Normalize the request data
        normalized_data = cls._normalize_request_data(request_data)
        return cls._generate_key(normalized_data)
    
    @classmethod
    def from_messages(
        cls,
        model: str,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Self:
        """Create cache key from chat messages format.
        
        Args:
            model: Model name
            messages: Chat messages list
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            **kwargs: Additional parameters
            
        Returns:
            Generated cache key
        """
        request_data = {
            "model": model.strip().lower(),
            "messages": messages,
        }
        
        if temperature is not None:
            request_data["temperature"] = temperature
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
            
        for key, value in kwargs.items():
            if value is not None:
                request_data[key] = value
        
        return cls._generate_key(request_data)
    
    @classmethod
    def _normalize_request_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize request data for consistent hashing.
        
        Args:
            data: Raw request data
            
        Returns:
            Normalized request data
        """
        normalized = {}
        
        for key, value in data.items():
            # Skip None values
            if value is None:
                continue
                
            # Normalize string values
            if isinstance(value, str):
                if key == "model":
                    normalized[key] = value.strip().lower()
                else:
                    normalized[key] = value.strip()
            
            # Round float values to avoid precision issues
            elif isinstance(value, float):
                normalized[key] = round(value, 6)
            
            # Keep other values as-is
            else:
                normalized[key] = value
        
        return normalized
    
    @classmethod
    def _generate_key(cls, data: Dict[str, Any]) -> Self:
        """Generate cache key from normalized data.
        
        Args:
            data: Normalized request data
            
        Returns:
            Generated cache key
        """
        # Sort keys for deterministic ordering
        sorted_data = dict(sorted(data.items()))
        
        # Serialize to JSON with consistent formatting
        json_str = json.dumps(
            sorted_data,
            ensure_ascii=True,
            separators=(',', ':'),  # No spaces for consistency
            sort_keys=True  # Additional sorting for nested objects
        )
        
        # Generate SHA256 hash
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        return cls(hash_hex)
    
    def get_prefix(self, length: int = 8) -> str:
        """Get prefix of cache key for display.
        
        Args:
            length: Prefix length
            
        Returns:
            Cache key prefix
        """
        return self.value[:length]
    
    def get_namespace(self, namespace_length: int = 2) -> str:
        """Get namespace for cache partitioning.
        
        Args:
            namespace_length: Namespace length in characters
            
        Returns:
            Namespace string for partitioning
        """
        return self.value[:namespace_length]
    
    def matches_prefix(self, prefix: str) -> bool:
        """Check if cache key matches prefix.
        
        Args:
            prefix: Prefix to match
            
        Returns:
            True if key starts with prefix
        """
        return self.value.startswith(prefix.lower())
    
    def to_file_safe(self) -> str:
        """Convert to file-safe format.
        
        Returns:
            File-safe cache key (already hex, so same as value)
        """
        return self.value
    
    def to_cache_path(self, base_dir: str = "cache") -> str:
        """Convert to cache file path with partitioning.
        
        Args:
            base_dir: Base cache directory
            
        Returns:
            Cache file path with namespace partitioning
        """
        namespace = self.get_namespace(2)
        return f"{base_dir}/{namespace}/{self.value}.json"
    
    def hash_algorithm(self) -> str:
        """Get hash algorithm used.
        
        Returns:
            Hash algorithm name
        """
        if len(self.value) == 32:
            return "md5"
        elif len(self.value) == 40:
            return "sha1"
        elif len(self.value) == 64:
            return "sha256"
        else:
            return "unknown"
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __repr__(self) -> str:
        """Debug representation."""
        prefix = self.get_prefix()
        return f"CacheKey('{prefix}...')"
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)
