"""Safe serialization infrastructure replacing pickle with JSON and MessagePack.

This module provides secure serialization mechanisms that avoid the security
risks of pickle while maintaining performance and functionality.
"""

import json
import sys
from typing import Type, TypeVar, Any, Dict, Optional, Union, List
from datetime import datetime
from uuid import UUID
from dataclasses import is_dataclass, fields, asdict
from abc import ABC, abstractmethod
from enum import Enum
import importlib

# Optional MessagePack support
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False
    msgpack = None

from ...shared.repository import RepositoryError
from .schema_validation import SerializationSchema, create_entity_schema, ValidationError as SchemaValidationError
from .version_compatibility import VersionMigrationManager, VersionInfo, MigrationStrategy, VersionCompatibilityError

T = TypeVar('T')


class SerializationError(RepositoryError):
    """Error during entity serialization/deserialization."""
    pass


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    MSGPACK = "msgpack"
    BINARY_JSON = "binary_json"  # JSON with binary wrapper


class SafeEntitySerializer(ABC):
    """Abstract base for safe entity serializers."""
    
    @abstractmethod
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity to bytes."""
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize bytes to entity."""
        pass
    
    @property
    @abstractmethod
    def format(self) -> SerializationFormat:
        """Get the serialization format."""
        pass


class SafeJSONEntitySerializer(SafeEntitySerializer):
    """JSON-based entity serializer with enhanced security and type safety."""
    
    def __init__(self, schema_version: str = "1.0", enable_schema_validation: bool = True,
                 migration_strategy: MigrationStrategy = MigrationStrategy.BACKWARD):
        self._type_registry: Dict[str, Type] = {}
        self._value_object_types = set()
        self._schema_version = schema_version
        self._max_depth = 100  # Prevent infinite recursion
        self._max_string_length = 1_000_000  # 1MB string limit
        self._max_list_length = 10_000  # Prevent memory exhaustion
        self._enable_schema_validation = enable_schema_validation
        self._entity_schemas: Dict[Type, SerializationSchema] = {}
        
        # Version migration support
        self._migration_manager = VersionMigrationManager(
            VersionInfo.from_string(schema_version),
            migration_strategy
        )
    
    @property
    def format(self) -> SerializationFormat:
        return SerializationFormat.JSON
    
    def register_type(self, name: str, type_class: Type) -> None:
        """Register a type for deserialization.
        
        Args:
            name: Type name for lookup
            type_class: Class to register
        """
        if not name or not isinstance(name, str):
            raise ValueError("Type name must be a non-empty string")
        if not isinstance(type_class, type):
            raise ValueError("type_class must be a class")
        
        self._type_registry[name] = type_class
    
    def register_value_object(self, type_class: Type) -> None:
        """Register a value object type.
        
        Args:
            type_class: Value object class
        """
        if not isinstance(type_class, type):
            raise ValueError("type_class must be a class")
        
        self._value_object_types.add(type_class)
        self.register_type(type_class.__name__, type_class)
    
    def _get_entity_schema(self, entity_type: Type) -> Optional[SerializationSchema]:
        """Get or create schema for an entity type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Serialization schema or None if schema validation disabled
        """
        if not self._enable_schema_validation:
            return None
        
        if entity_type not in self._entity_schemas:
            try:
                schema = create_entity_schema(
                    entity_type, 
                    value_object_types=list(self._value_object_types)
                )
                self._entity_schemas[entity_type] = schema
            except Exception:
                # If schema creation fails, disable validation for this type
                self._entity_schemas[entity_type] = None
        
        return self._entity_schemas[entity_type]
    
    def register_migration(self, migration) -> None:
        \"\"\"Register a data migration.
        
        Args:
            migration: Data migration to register
        \"\"\"
        self._migration_manager.add_migration(migration)
    
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity to JSON bytes with security measures.
        
        Args:
            entity: Entity to serialize
            
        Returns:
            JSON bytes representation with metadata
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Create secure wrapper with metadata
            wrapper = {
                "__schema_version__": self._schema_version,
                "__format__": self.format.value,
                "__type__": entity.__class__.__name__,
                "__module__": entity.__class__.__module__,
                "data": self._entity_to_dict(entity, depth=0)
            }
            
            # Validate against schema if available
            schema = self._get_entity_schema(entity.__class__)
            if schema:
                try:
                    schema.validate(wrapper)
                except SchemaValidationError as e:
                    raise SerializationError(f"Schema validation failed for {type(entity).__name__}: {e}") from e
            
            # Serialize to JSON with security settings
            json_str = json.dumps(
                wrapper, 
                default=self._json_default, 
                ensure_ascii=True,  # Security: prevent encoding issues
                check_circular=True,  # Prevent circular references
                separators=(',', ':')  # Compact format
            )
            
            # Check size limits
            if len(json_str) > self._max_string_length:
                raise SerializationError(f"Serialized data too large: {len(json_str)} bytes")
            
            return json_str.encode('utf-8')
            
        except json.JSONEncodeError as e:
            raise SerializationError(f"JSON encoding failed for {type(entity).__name__}: {e}") from e
        except Exception as e:
            raise SerializationError(f"Failed to serialize {type(entity).__name__}: {e}") from e
    
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize JSON bytes to entity with security validation.
        
        Args:
            data: JSON bytes to deserialize
            entity_type: Expected entity type
            
        Returns:
            Deserialized entity
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            # Size check
            if len(data) > self._max_string_length:
                raise SerializationError(f"Data too large: {len(data)} bytes")
            
            # Parse JSON
            json_str = data.decode('utf-8')
            json_data = json.loads(json_str)
            
            # Security: Ensure we have a dict
            if not isinstance(json_data, dict):
                raise SerializationError("Invalid data structure: expected object")
            
            # Handle schema version migration
            schema_version = json_data.get('__schema_version__')
            if schema_version != self._schema_version:
                try:
                    # Attempt migration to current version
                    json_data = self._migration_manager.migrate_data(json_data)
                except VersionCompatibilityError as e:
                    raise SerializationError(f"Version migration failed: {e}") from e
            
            # Validate format
            format_value = json_data.get('__format__')
            if format_value != self.format.value:
                raise SerializationError(f"Format mismatch: expected {self.format.value}, got {format_value}")
            
            # Verify type
            stored_type = json_data.get('__type__')
            stored_module = json_data.get('__module__')
            
            if stored_type and stored_type != entity_type.__name__:
                raise SerializationError(
                    f"Type mismatch: expected {entity_type.__name__}, got {stored_type}"
                )
            
            # Security: Validate module
            if stored_module and stored_module != entity_type.__module__:
                # Allow certain safe module migrations
                if not self._is_safe_module_migration(stored_module, entity_type.__module__):
                    raise SerializationError(
                        f"Module mismatch: expected {entity_type.__module__}, got {stored_module}"
                    )
            
            # Validate against schema if available
            schema = self._get_entity_schema(entity_type)
            if schema:
                try:
                    schema.validate(json_data)
                except SchemaValidationError as e:
                    raise SerializationError(f"Schema validation failed for {entity_type.__name__}: {e}") from e
            
            # Extract and convert data
            entity_data = json_data.get('data', {})
            if not isinstance(entity_data, dict):
                raise SerializationError("Invalid entity data: expected object")
            
            return self._dict_to_entity(entity_data, entity_type, depth=0)
            
        except json.JSONDecodeError as e:
            raise SerializationError(f"JSON decoding failed: {e}") from e
        except Exception as e:
            raise SerializationError(f"Failed to deserialize {entity_type.__name__}: {e}") from e
    
    def _is_safe_module_migration(self, old_module: str, new_module: str) -> bool:
        """Check if module migration is safe.
        
        Args:
            old_module: Original module name
            new_module: New module name
            
        Returns:
            True if migration is safe
        """
        # Allow migrations within the same project
        safe_prefixes = ['writeit.', 'src.writeit.']
        
        old_safe = any(old_module.startswith(prefix) for prefix in safe_prefixes)
        new_safe = any(new_module.startswith(prefix) for prefix in safe_prefixes)
        
        return old_safe and new_safe
    
    def _entity_to_dict(self, entity: Any, depth: int = 0) -> Dict[str, Any]:
        """Convert entity to dictionary with depth protection.
        
        Args:
            entity: Entity to convert
            depth: Current recursion depth
            
        Returns:
            Dictionary representation
        """
        if depth > self._max_depth:
            raise SerializationError(f"Maximum recursion depth ({self._max_depth}) exceeded")
        
        if is_dataclass(entity):
            result = {}
            for field in fields(entity):
                value = getattr(entity, field.name)
                result[field.name] = self._serialize_value(value, depth + 1)
            return result
        else:
            # For non-dataclass entities, serialize public attributes
            result = {}
            for attr in dir(entity):
                if not attr.startswith('_') and not callable(getattr(entity, attr, None)):
                    try:
                        value = getattr(entity, attr)
                        result[attr] = self._serialize_value(value, depth + 1)
                    except (AttributeError, TypeError):
                        # Skip attributes that can't be accessed or serialized
                        continue
            return result
    
    def _serialize_value(self, value: Any, depth: int) -> Any:
        """Serialize a single value with security checks.
        
        Args:
            value: Value to serialize
            depth: Current recursion depth
            
        Returns:
            Serialized value
        """
        if depth > self._max_depth:
            raise SerializationError(f"Maximum recursion depth ({self._max_depth}) exceeded")
        
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            # Security: Check string length
            if isinstance(value, str) and len(value) > self._max_string_length:
                raise SerializationError(f"String too long: {len(value)} characters")
            return value
        elif isinstance(value, UUID):
            return {'__uuid__': str(value)}
        elif isinstance(value, datetime):
            return {'__datetime__': value.isoformat()}
        elif hasattr(value, 'value') and type(value) in self._value_object_types:
            # Value object
            return {
                '__value_object__': type(value).__name__,
                'value': self._serialize_value(value.value, depth + 1)
            }
        elif is_dataclass(value):
            return {
                '__dataclass__': type(value).__name__,
                '__module__': type(value).__module__,
                'data': self._entity_to_dict(value, depth + 1)
            }
        elif isinstance(value, list):
            # Security: Check list length
            if len(value) > self._max_list_length:
                raise SerializationError(f"List too long: {len(value)} items")
            return [self._serialize_value(item, depth + 1) for item in value]
        elif isinstance(value, dict):
            # Security: Check dict size
            if len(value) > self._max_list_length:
                raise SerializationError(f"Dict too large: {len(value)} items")
            return {k: self._serialize_value(v, depth + 1) for k, v in value.items()}
        elif isinstance(value, (set, frozenset)):
            return {
                '__set__': [self._serialize_value(item, depth + 1) for item in value]
            }
        elif isinstance(value, tuple):
            return {
                '__tuple__': [self._serialize_value(item, depth + 1) for item in value]
            }
        else:
            # Fallback to string representation for safety
            str_repr = str(value)
            if len(str_repr) > self._max_string_length:
                str_repr = str_repr[:self._max_string_length] + "...[truncated]"
            return {'__str__': str_repr, '__type__': type(value).__name__}
    
    def _dict_to_entity(self, data: Dict[str, Any], entity_type: Type[T], depth: int = 0) -> T:
        """Convert dictionary to entity with depth protection.
        
        Args:
            data: Dictionary data
            entity_type: Target entity type
            depth: Current recursion depth
            
        Returns:
            Reconstructed entity
        """
        if depth > self._max_depth:
            raise SerializationError(f"Maximum recursion depth ({self._max_depth}) exceeded")
        
        if not is_dataclass(entity_type):
            raise SerializationError(f"Cannot deserialize non-dataclass type: {entity_type}")
        
        # Deserialize field values
        kwargs = {}
        entity_fields = {f.name: f for f in fields(entity_type)}
        
        for field_name, field_info in entity_fields.items():
            if field_name in data:
                value = data[field_name]
                kwargs[field_name] = self._deserialize_value(value, field_info.type, depth + 1)
            elif field_info.default != field_info.default_factory:
                # Has default value
                pass
            else:
                raise SerializationError(f"Missing required field: {field_name}")
        
        return entity_type(**kwargs)
    
    def _deserialize_value(self, value: Any, expected_type: Type = None, depth: int = 0) -> Any:
        """Deserialize a single value with security checks.
        
        Args:
            value: Value to deserialize
            expected_type: Expected type hint
            depth: Current recursion depth
            
        Returns:
            Deserialized value
        """
        if depth > self._max_depth:
            raise SerializationError(f"Maximum recursion depth ({self._max_depth}) exceeded")
        
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, dict):
            if '__uuid__' in value:
                return UUID(value['__uuid__'])
            elif '__datetime__' in value:
                return datetime.fromisoformat(value['__datetime__'])
            elif '__value_object__' in value:
                # Value object
                vo_type_name = value['__value_object__']
                if vo_type_name in self._type_registry:
                    vo_type = self._type_registry[vo_type_name]
                    inner_value = self._deserialize_value(value['value'], None, depth + 1)
                    return vo_type(inner_value)
                else:
                    raise SerializationError(f"Unknown value object type: {vo_type_name}")
            elif '__dataclass__' in value:
                # Nested dataclass
                dc_type_name = value['__dataclass__']
                dc_module = value.get('__module__')
                
                if dc_type_name in self._type_registry:
                    dc_type = self._type_registry[dc_type_name]
                    return self._dict_to_entity(value['data'], dc_type, depth + 1)
                else:
                    raise SerializationError(f"Unknown dataclass type: {dc_type_name}")
            elif '__set__' in value:
                return set(self._deserialize_value(item, None, depth + 1) for item in value['__set__'])
            elif '__tuple__' in value:
                return tuple(self._deserialize_value(item, None, depth + 1) for item in value['__tuple__'])
            elif '__str__' in value:
                # String representation fallback
                return value['__str__']
            else:
                # Regular dict
                return {k: self._deserialize_value(v, None, depth + 1) for k, v in value.items()}
        elif isinstance(value, list):
            # Security: Check list length
            if len(value) > self._max_list_length:
                raise SerializationError(f"List too long: {len(value)} items")
            return [self._deserialize_value(item, None, depth + 1) for item in value]
        else:
            return value
    
    def _json_default(self, obj: Any) -> Any:
        """JSON serialization fallback for non-serializable objects.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serializable representation
        """
        if isinstance(obj, UUID):
            return {'__uuid__': str(obj)}
        elif isinstance(obj, datetime):
            return {'__datetime__': obj.isoformat()}
        else:
            # Safe fallback
            return {'__str__': str(obj), '__type__': type(obj).__name__}


class SafeMessagePackSerializer(SafeEntitySerializer):
    """MessagePack-based entity serializer for binary efficiency."""
    
    def __init__(self, schema_version: str = "1.0", enable_schema_validation: bool = True,
                 migration_strategy: MigrationStrategy = MigrationStrategy.BACKWARD):
        if not HAS_MSGPACK:
            raise SerializationError("MessagePack not available. Install with: pip install msgpack")
        
        self._json_serializer = SafeJSONEntitySerializer(schema_version, enable_schema_validation, migration_strategy)
        self._schema_version = schema_version
    
    @property
    def format(self) -> SerializationFormat:
        return SerializationFormat.MSGPACK
    
    def register_type(self, name: str, type_class: Type) -> None:
        """Register a type for deserialization."""
        self._json_serializer.register_type(name, type_class)
    
    def register_value_object(self, type_class: Type) -> None:
        """Register a value object type."""
        self._json_serializer.register_value_object(type_class)
    
    def register_migration(self, migration) -> None:
        """Register a data migration."""
        self._json_serializer.register_migration(migration)
    
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity to MessagePack bytes.
        
        Args:
            entity: Entity to serialize
            
        Returns:
            MessagePack bytes representation
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # First convert to JSON-compatible dict
            json_data = json.loads(self._json_serializer.serialize(entity).decode('utf-8'))
            
            # Then pack with MessagePack
            return msgpack.packb(
                json_data,
                strict_types=True,
                use_bin_type=True,
                timestamp=3  # Use timestamp extension type
            )
            
        except Exception as e:
            raise SerializationError(f"Failed to serialize {type(entity).__name__} with MessagePack: {e}") from e
    
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize MessagePack bytes to entity.
        
        Args:
            data: MessagePack bytes to deserialize
            entity_type: Expected entity type
            
        Returns:
            Deserialized entity
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            # Unpack MessagePack
            json_data = msgpack.unpackb(
                data,
                strict_map_key=False,
                timestamp=3
            )
            
            # Convert back to JSON and deserialize
            json_bytes = json.dumps(json_data).encode('utf-8')
            return self._json_serializer.deserialize(json_bytes, entity_type)
            
        except Exception as e:
            raise SerializationError(f"Failed to deserialize {entity_type.__name__} from MessagePack: {e}") from e


class SafeDomainEntitySerializer:
    """Main safe serializer for domain entities with format selection."""
    
    def __init__(self, 
                 default_format: SerializationFormat = SerializationFormat.JSON,
                 schema_version: str = "1.0",
                 enable_schema_validation: bool = True,
                 migration_strategy: MigrationStrategy = MigrationStrategy.BACKWARD):
        """Initialize with format preference.
        
        Args:
            default_format: Default serialization format
            schema_version: Schema version for compatibility
            enable_schema_validation: Whether to enable schema validation
            migration_strategy: Version migration strategy
        """
        self._default_format = default_format
        self._schema_version = schema_version
        self._enable_schema_validation = enable_schema_validation
        
        # Initialize serializers
        self._json_serializer = SafeJSONEntitySerializer(schema_version, enable_schema_validation, migration_strategy)
        
        if HAS_MSGPACK:
            self._msgpack_serializer = SafeMessagePackSerializer(schema_version, enable_schema_validation, migration_strategy)
        else:
            self._msgpack_serializer = None
        
        # Format prefixes for identification
        self._format_prefixes = {
            SerializationFormat.JSON: b'SJSON:',  # Safe JSON
            SerializationFormat.MSGPACK: b'SMSGP:',  # Safe MessagePack
        }
    
    @property
    def available_formats(self) -> List[SerializationFormat]:
        """Get list of available serialization formats."""
        formats = [SerializationFormat.JSON]
        if HAS_MSGPACK:
            formats.append(SerializationFormat.MSGPACK)
        return formats
    
    def register_type(self, name: str, type_class: Type) -> None:
        """Register a type for serialization.
        
        Args:
            name: Type name
            type_class: Class to register
        """
        self._json_serializer.register_type(name, type_class)
        if self._msgpack_serializer:
            self._msgpack_serializer.register_type(name, type_class)
    
    def register_value_object(self, type_class: Type) -> None:
        """Register a value object type.
        
        Args:
            type_class: Value object class
        """
        self._json_serializer.register_value_object(type_class)
        if self._msgpack_serializer:
            self._msgpack_serializer.register_value_object(type_class)
    
    def register_migration(self, migration) -> None:
        \"\"\"Register a data migration.
        
        Args:
            migration: Data migration to register
        \"\"\"
        self._json_serializer.register_migration(migration)
        if self._msgpack_serializer:
            self._msgpack_serializer.register_migration(migration)
    
    def serialize(self, entity: Any, format_preference: Optional[SerializationFormat] = None) -> bytes:
        """Serialize entity with specified or default format.
        
        Args:
            entity: Entity to serialize
            format_preference: Preferred format, falls back to default
            
        Returns:
            Serialized bytes with format prefix
        """
        format_to_use = format_preference or self._default_format
        
        # Fallback if preferred format not available
        if format_to_use == SerializationFormat.MSGPACK and not self._msgpack_serializer:
            format_to_use = SerializationFormat.JSON
        
        try:
            if format_to_use == SerializationFormat.JSON:
                data = self._json_serializer.serialize(entity)
                prefix = self._format_prefixes[SerializationFormat.JSON]
            elif format_to_use == SerializationFormat.MSGPACK:
                data = self._msgpack_serializer.serialize(entity)
                prefix = self._format_prefixes[SerializationFormat.MSGPACK]
            else:
                raise SerializationError(f"Unsupported format: {format_to_use}")
            
            return prefix + data
            
        except Exception as e:
            # Fallback to JSON if other format fails
            if format_to_use != SerializationFormat.JSON:
                try:
                    data = self._json_serializer.serialize(entity)
                    prefix = self._format_prefixes[SerializationFormat.JSON]
                    return prefix + data
                except Exception as fallback_error:
                    raise SerializationError(
                        f"Both {format_to_use.value} and JSON serialization failed: {e}, {fallback_error}"
                    ) from e
            raise
    
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize bytes to entity.
        
        Args:
            data: Serialized bytes with format prefix
            entity_type: Expected entity type
            
        Returns:
            Deserialized entity
        """
        # Detect format from prefix
        for format_type, prefix in self._format_prefixes.items():
            if data.startswith(prefix):
                payload = data[len(prefix):]
                
                if format_type == SerializationFormat.JSON:
                    return self._json_serializer.deserialize(payload, entity_type)
                elif format_type == SerializationFormat.MSGPACK and self._msgpack_serializer:
                    return self._msgpack_serializer.deserialize(payload, entity_type)
                else:
                    raise SerializationError(f"Serializer not available for format: {format_type}")
        
        # Legacy detection - try to detect old pickle format and reject it
        if data.startswith(b'\x80\x03') or data.startswith(b'\x80\x04') or data.startswith(b'PICKLE:'):
            raise SerializationError(
                "Pickle format detected and rejected for security reasons. "
                "Please migrate data to safe serialization format."
            )
        
        # Try JSON as fallback for untagged data
        try:
            return self._json_serializer.deserialize(data, entity_type)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize data: {e}") from e


def create_safe_serializer(format_preference: SerializationFormat = SerializationFormat.JSON,
                          enable_schema_validation: bool = True,
                          migration_strategy: MigrationStrategy = MigrationStrategy.BACKWARD) -> SafeDomainEntitySerializer:
    """Create a safe domain entity serializer.
    
    Args:
        format_preference: Preferred serialization format
        enable_schema_validation: Whether to enable schema validation
        migration_strategy: Version migration strategy
        
    Returns:
        Configured safe serializer
    """
    return SafeDomainEntitySerializer(
        default_format=format_preference,
        enable_schema_validation=enable_schema_validation,
        migration_strategy=migration_strategy
    )