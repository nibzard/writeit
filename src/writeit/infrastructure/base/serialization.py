"""Domain entity serialization and deserialization.

Handles conversion between domain entities and storage formats,
including JSON serialization with support for value objects.
"""

import json
import pickle
from typing import Type, TypeVar, Any, Dict, Optional
from datetime import datetime
from uuid import UUID
from dataclasses import is_dataclass, fields, asdict
from abc import ABC, abstractmethod

from ...shared.repository import RepositoryError

T = TypeVar('T')


class SerializationError(RepositoryError):
    """Error during entity serialization/deserialization."""
    pass


class EntitySerializer(ABC):
    """Abstract base for entity serializers."""
    
    @abstractmethod
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity to bytes."""
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize bytes to entity."""
        pass


class JSONEntitySerializer(EntitySerializer):
    """JSON-based entity serializer with value object support."""
    
    def __init__(self):
        self._type_registry: Dict[str, Type] = {}
        self._value_object_types = set()
    
    def register_type(self, name: str, type_class: Type) -> None:
        """Register a type for deserialization.
        
        Args:
            name: Type name for lookup
            type_class: Class to register
        """
        self._type_registry[name] = type_class
    
    def register_value_object(self, type_class: Type) -> None:
        """Register a value object type.
        
        Args:
            type_class: Value object class
        """
        self._value_object_types.add(type_class)
        self.register_type(type_class.__name__, type_class)
    
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity to JSON bytes.
        
        Args:
            entity: Entity to serialize
            
        Returns:
            JSON bytes representation
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Convert entity to dict
            data = self._entity_to_dict(entity)
            
            # Add type information
            data['__type__'] = entity.__class__.__name__
            
            # Serialize to JSON
            json_str = json.dumps(data, default=self._json_default, ensure_ascii=False)
            return json_str.encode('utf-8')
            
        except Exception as e:
            raise SerializationError(f"Failed to serialize {type(entity).__name__}: {e}") from e
    
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize JSON bytes to entity.
        
        Args:
            data: JSON bytes to deserialize
            entity_type: Expected entity type
            
        Returns:
            Deserialized entity
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            # Parse JSON
            json_str = data.decode('utf-8')
            json_data = json.loads(json_str)
            
            # Verify type
            stored_type = json_data.get('__type__')
            if stored_type and stored_type != entity_type.__name__:
                raise SerializationError(
                    f"Type mismatch: expected {entity_type.__name__}, got {stored_type}"
                )
            
            # Remove type metadata
            if '__type__' in json_data:
                del json_data['__type__']
            
            # Convert dict back to entity
            return self._dict_to_entity(json_data, entity_type)
            
        except Exception as e:
            raise SerializationError(f"Failed to deserialize {entity_type.__name__}: {e}") from e
    
    def _entity_to_dict(self, entity: Any) -> Dict[str, Any]:
        """Convert entity to dictionary.
        
        Args:
            entity: Entity to convert
            
        Returns:
            Dictionary representation
        """
        if is_dataclass(entity):
            result = {}
            for field in fields(entity):
                value = getattr(entity, field.name)
                result[field.name] = self._serialize_value(value)
            return result
        else:
            # For non-dataclass entities, try to get public attributes
            result = {}
            for attr in dir(entity):
                if not attr.startswith('_') and not callable(getattr(entity, attr)):
                    value = getattr(entity, attr)
                    result[attr] = self._serialize_value(value)
            return result
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value
        """
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, UUID):
            return {'__uuid__': str(value)}
        elif isinstance(value, datetime):
            return {'__datetime__': value.isoformat()}
        elif hasattr(value, 'value') and type(value) in self._value_object_types:
            # Value object
            return {
                '__value_object__': type(value).__name__,
                'value': self._serialize_value(value.value)
            }
        elif is_dataclass(value):
            return {
                '__dataclass__': type(value).__name__,
                'data': self._entity_to_dict(value)
            }
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            # Fallback to string representation
            return str(value)
    
    def _dict_to_entity(self, data: Dict[str, Any], entity_type: Type[T]) -> T:
        """Convert dictionary to entity.
        
        Args:
            data: Dictionary data
            entity_type: Target entity type
            
        Returns:
            Reconstructed entity
        """
        if not is_dataclass(entity_type):
            raise SerializationError(f"Cannot deserialize non-dataclass type: {entity_type}")
        
        # Deserialize field values
        kwargs = {}
        for field in fields(entity_type):
            if field.name in data:
                value = data[field.name]
                kwargs[field.name] = self._deserialize_value(value, field.type)
            elif field.default != field.default_factory:
                # Has default value
                pass
            else:
                raise SerializationError(f"Missing required field: {field.name}")
        
        return entity_type(**kwargs)
    
    def _deserialize_value(self, value: Any, expected_type: Type = None) -> Any:
        """Deserialize a single value.
        
        Args:
            value: Value to deserialize
            expected_type: Expected type hint
            
        Returns:
            Deserialized value
        """
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
                    inner_value = self._deserialize_value(value['value'])
                    return vo_type(inner_value)
                else:
                    raise SerializationError(f"Unknown value object type: {vo_type_name}")
            elif '__dataclass__' in value:
                # Nested dataclass
                dc_type_name = value['__dataclass__']
                if dc_type_name in self._type_registry:
                    dc_type = self._type_registry[dc_type_name]
                    return self._dict_to_entity(value['data'], dc_type)
                else:
                    raise SerializationError(f"Unknown dataclass type: {dc_type_name}")
            else:
                # Regular dict
                return {k: self._deserialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize_value(item) for item in value]
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
            return str(obj)


class PickleEntitySerializer(EntitySerializer):
    """Pickle-based entity serializer for complex objects."""
    
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity using pickle.
        
        Args:
            entity: Entity to serialize
            
        Returns:
            Pickled bytes
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            return pickle.dumps(entity)
        except Exception as e:
            raise SerializationError(f"Failed to pickle {type(entity).__name__}: {e}") from e
    
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize pickle bytes to entity.
        
        Args:
            data: Pickled bytes
            entity_type: Expected entity type
            
        Returns:
            Deserialized entity
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            entity = pickle.loads(data)
            if not isinstance(entity, entity_type):
                raise SerializationError(
                    f"Type mismatch: expected {entity_type.__name__}, got {type(entity).__name__}"
                )
            return entity
        except Exception as e:
            raise SerializationError(f"Failed to unpickle {entity_type.__name__}: {e}") from e


class DomainEntitySerializer:
    """Main serializer for domain entities with fallback strategies."""
    
    def __init__(self, prefer_json: bool = True):
        """Initialize with serializer preference.
        
        Args:
            prefer_json: If True, use JSON when possible, otherwise use pickle
        """
        self.json_serializer = JSONEntitySerializer()
        self.pickle_serializer = PickleEntitySerializer()
        self.prefer_json = prefer_json
    
    def register_type(self, name: str, type_class: Type) -> None:
        """Register a type for JSON serialization.
        
        Args:
            name: Type name
            type_class: Class to register
        """
        self.json_serializer.register_type(name, type_class)
    
    def register_value_object(self, type_class: Type) -> None:
        """Register a value object type.
        
        Args:
            type_class: Value object class
        """
        self.json_serializer.register_value_object(type_class)
    
    def serialize(self, entity: Any) -> bytes:
        """Serialize entity with best available method.
        
        Args:
            entity: Entity to serialize
            
        Returns:
            Serialized bytes with format prefix
        """
        if self.prefer_json and is_dataclass(entity):
            try:
                data = self.json_serializer.serialize(entity)
                return b'JSON:' + data
            except SerializationError:
                # Fall back to pickle
                data = self.pickle_serializer.serialize(entity)
                return b'PICKLE:' + data
        else:
            data = self.pickle_serializer.serialize(entity)
            return b'PICKLE:' + data
    
    def deserialize(self, data: bytes, entity_type: Type[T]) -> T:
        """Deserialize bytes to entity.
        
        Args:
            data: Serialized bytes with format prefix
            entity_type: Expected entity type
            
        Returns:
            Deserialized entity
        """
        if data.startswith(b'JSON:'):
            return self.json_serializer.deserialize(data[5:], entity_type)
        elif data.startswith(b'PICKLE:'):
            return self.pickle_serializer.deserialize(data[7:], entity_type)
        else:
            # Legacy format - try pickle first, then JSON
            try:
                return self.pickle_serializer.deserialize(data, entity_type)
            except SerializationError:
                return self.json_serializer.deserialize(data, entity_type)