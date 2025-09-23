"""Schema validation for safe serialization.

Provides validation for serialized data structures to ensure data integrity
and prevent malicious payloads.
"""

import json
from typing import Any, Dict, List, Union, Optional, Type, TypeVar
from dataclasses import is_dataclass, fields
from abc import ABC, abstractmethod
from enum import Enum
from uuid import UUID
from datetime import datetime

T = TypeVar('T')


class ValidationError(Exception):
    """Schema validation error."""
    pass


class SchemaType(Enum):
    """Supported schema types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    NULL = "null"
    ARRAY = "array"
    OBJECT = "object"
    UUID = "uuid"
    DATETIME = "datetime"
    DATACLASS = "dataclass"
    VALUE_OBJECT = "value_object"


class SchemaConstraint(ABC):
    """Base class for schema constraints."""
    
    @abstractmethod
    def validate(self, value: Any, path: str = "") -> None:
        """Validate a value against this constraint.
        
        Args:
            value: Value to validate
            path: Current path in the data structure
            
        Raises:
            ValidationError: If validation fails
        """
        pass


class LengthConstraint(SchemaConstraint):
    """Length constraint for strings and arrays."""
    
    def __init__(self, min_length: Optional[int] = None, max_length: Optional[int] = None):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any, path: str = "") -> None:
        if not hasattr(value, '__len__'):
            raise ValidationError(f"{path}: Value must have length")
        
        length = len(value)
        
        if self.min_length is not None and length < self.min_length:
            raise ValidationError(f"{path}: Length {length} is less than minimum {self.min_length}")
        
        if self.max_length is not None and length > self.max_length:
            raise ValidationError(f"{path}: Length {length} exceeds maximum {self.max_length}")


class RangeConstraint(SchemaConstraint):
    """Range constraint for numeric values."""
    
    def __init__(self, min_value: Optional[Union[int, float]] = None, 
                 max_value: Optional[Union[int, float]] = None):
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any, path: str = "") -> None:
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{path}: Value must be numeric")
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"{path}: Value {value} is less than minimum {self.min_value}")
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"{path}: Value {value} exceeds maximum {self.max_value}")


class PatternConstraint(SchemaConstraint):
    """Pattern constraint for string values."""
    
    def __init__(self, pattern: str):
        import re
        self.pattern = pattern
        self.regex = re.compile(pattern)
    
    def validate(self, value: Any, path: str = "") -> None:
        if not isinstance(value, str):
            raise ValidationError(f"{path}: Value must be string")
        
        if not self.regex.match(value):
            raise ValidationError(f"{path}: Value '{value}' does not match pattern '{self.pattern}'")


class AllowedValuesConstraint(SchemaConstraint):
    """Constraint for allowed values (enum-like)."""
    
    def __init__(self, allowed_values: List[Any]):
        self.allowed_values = set(allowed_values)
    
    def validate(self, value: Any, path: str = "") -> None:
        if value not in self.allowed_values:
            raise ValidationError(f"{path}: Value '{value}' not in allowed values {list(self.allowed_values)}")


class SchemaField:
    """Schema field definition."""
    
    def __init__(self, 
                 schema_type: SchemaType,
                 required: bool = True,
                 nullable: bool = False,
                 constraints: Optional[List[SchemaConstraint]] = None,
                 items_schema: Optional['SchemaField'] = None,
                 properties_schema: Optional[Dict[str, 'SchemaField']] = None,
                 description: Optional[str] = None):
        """Initialize schema field.
        
        Args:
            schema_type: Type of the field
            required: Whether field is required
            nullable: Whether field can be null
            constraints: List of validation constraints
            items_schema: Schema for array items
            properties_schema: Schema for object properties
            description: Field description
        """
        self.schema_type = schema_type
        self.required = required
        self.nullable = nullable
        self.constraints = constraints or []
        self.items_schema = items_schema
        self.properties_schema = properties_schema or {}
        self.description = description
    
    def validate(self, value: Any, path: str = "") -> None:
        """Validate value against this field schema.
        
        Args:
            value: Value to validate
            path: Current path in data structure
            
        Raises:
            ValidationError: If validation fails
        """
        # Check null values
        if value is None:
            if self.nullable:
                return
            else:
                raise ValidationError(f"{path}: Null value not allowed")
        
        # Validate type
        self._validate_type(value, path)
        
        # Apply constraints
        for constraint in self.constraints:
            constraint.validate(value, path)
        
        # Validate nested structures
        if self.schema_type == SchemaType.ARRAY and self.items_schema:
            self._validate_array_items(value, path)
        elif self.schema_type == SchemaType.OBJECT and self.properties_schema:
            self._validate_object_properties(value, path)
    
    def _validate_type(self, value: Any, path: str) -> None:
        """Validate the basic type of a value."""
        if self.schema_type == SchemaType.STRING:
            if not isinstance(value, str):
                raise ValidationError(f"{path}: Expected string, got {type(value).__name__}")
        elif self.schema_type == SchemaType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(f"{path}: Expected integer, got {type(value).__name__}")
        elif self.schema_type == SchemaType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValidationError(f"{path}: Expected float, got {type(value).__name__}")
        elif self.schema_type == SchemaType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValidationError(f"{path}: Expected boolean, got {type(value).__name__}")
        elif self.schema_type == SchemaType.ARRAY:
            if not isinstance(value, list):
                raise ValidationError(f"{path}: Expected array, got {type(value).__name__}")
        elif self.schema_type == SchemaType.OBJECT:
            if not isinstance(value, dict):
                raise ValidationError(f"{path}: Expected object, got {type(value).__name__}")
        elif self.schema_type == SchemaType.UUID:
            if isinstance(value, dict) and '__uuid__' in value:
                # Validate UUID string format
                try:
                    UUID(value['__uuid__'])
                except ValueError:
                    raise ValidationError(f"{path}: Invalid UUID format")
            else:
                raise ValidationError(f"{path}: Expected UUID object")
        elif self.schema_type == SchemaType.DATETIME:
            if isinstance(value, dict) and '__datetime__' in value:
                # Validate datetime format
                try:
                    datetime.fromisoformat(value['__datetime__'])
                except ValueError:
                    raise ValidationError(f"{path}: Invalid datetime format")
            else:
                raise ValidationError(f"{path}: Expected datetime object")
    
    def _validate_array_items(self, value: List[Any], path: str) -> None:
        """Validate array items."""
        for i, item in enumerate(value):
            item_path = f"{path}[{i}]"
            self.items_schema.validate(item, item_path)
    
    def _validate_object_properties(self, value: Dict[str, Any], path: str) -> None:
        """Validate object properties."""
        # Check required properties
        for prop_name, prop_schema in self.properties_schema.items():
            prop_path = f"{path}.{prop_name}" if path else prop_name
            
            if prop_name in value:
                prop_schema.validate(value[prop_name], prop_path)
            elif prop_schema.required:
                raise ValidationError(f"{prop_path}: Required property missing")
        
        # Check for unexpected properties (strict mode)
        unexpected = set(value.keys()) - set(self.properties_schema.keys())
        if unexpected:
            unexpected_list = list(unexpected)
            raise ValidationError(f"{path}: Unexpected properties: {unexpected_list}")


class SerializationSchema:
    """Schema for validating serialized data."""
    
    def __init__(self, root_schema: SchemaField, version: str = "1.0"):
        """Initialize schema.
        
        Args:
            root_schema: Root schema field
            version: Schema version
        """
        self.root_schema = root_schema
        self.version = version
    
    def validate(self, data: Any) -> None:
        """Validate data against schema.
        
        Args:
            data: Data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        self.root_schema.validate(data, "")


class DomainEntitySchemaBuilder:
    """Builder for creating schemas from domain entities."""
    
    def __init__(self):
        self._type_schemas: Dict[Type, SchemaField] = {}
        self._value_object_types: set = set()
    
    def register_value_object(self, value_object_type: Type) -> 'DomainEntitySchemaBuilder':
        """Register a value object type.
        
        Args:
            value_object_type: Value object class
            
        Returns:
            Self for chaining
        """
        self._value_object_types.add(value_object_type)
        return self
    
    def build_schema(self, entity_type: Type[T]) -> SerializationSchema:
        """Build schema for a domain entity.
        
        Args:
            entity_type: Entity type to build schema for
            
        Returns:
            Serialization schema
        """
        if not is_dataclass(entity_type):
            raise ValueError(f"Only dataclass entities are supported: {entity_type}")
        
        # Build wrapper schema matching serialization format
        wrapper_schema = SchemaField(
            schema_type=SchemaType.OBJECT,
            properties_schema={
                "__schema_version__": SchemaField(SchemaType.STRING, required=True),
                "__format__": SchemaField(SchemaType.STRING, required=True),
                "__type__": SchemaField(SchemaType.STRING, required=True),
                "__module__": SchemaField(SchemaType.STRING, required=True),
                "data": self._build_dataclass_schema(entity_type)
            }
        )
        
        return SerializationSchema(wrapper_schema)
    
    def _build_dataclass_schema(self, dataclass_type: Type) -> SchemaField:
        """Build schema for a dataclass."""
        if dataclass_type in self._type_schemas:
            return self._type_schemas[dataclass_type]
        
        properties = {}
        for field in fields(dataclass_type):
            field_schema = self._build_field_schema(field.type)
            field_schema.required = field.default == field.default_factory
            properties[field.name] = field_schema
        
        schema = SchemaField(
            schema_type=SchemaType.OBJECT,
            properties_schema=properties
        )
        
        self._type_schemas[dataclass_type] = schema
        return schema
    
    def _build_field_schema(self, field_type: Type) -> SchemaField:
        """Build schema for a field type."""
        # Handle basic types
        if field_type == str:
            return SchemaField(SchemaType.STRING, constraints=[
                LengthConstraint(max_length=1_000_000)  # 1MB string limit
            ])
        elif field_type == int:
            return SchemaField(SchemaType.INTEGER)
        elif field_type == float:
            return SchemaField(SchemaType.FLOAT)
        elif field_type == bool:
            return SchemaField(SchemaType.BOOLEAN)
        elif field_type == UUID:
            return SchemaField(SchemaType.UUID)
        elif field_type == datetime:
            return SchemaField(SchemaType.DATETIME)
        
        # Handle generic types
        if hasattr(field_type, '__origin__'):
            origin = field_type.__origin__
            args = getattr(field_type, '__args__', ())
            
            if origin == list:
                item_type = args[0] if args else Any
                return SchemaField(
                    schema_type=SchemaType.ARRAY,
                    items_schema=self._build_field_schema(item_type),
                    constraints=[LengthConstraint(max_length=10_000)]  # 10k items max
                )
            elif origin == dict:
                # For simplicity, treat as generic object
                return SchemaField(SchemaType.OBJECT)
            elif origin == Union:
                # Handle Optional types (Union[X, None])
                non_none_types = [arg for arg in args if arg != type(None)]
                if len(non_none_types) == 1:
                    schema = self._build_field_schema(non_none_types[0])
                    schema.nullable = True
                    return schema
        
        # Handle dataclasses
        if is_dataclass(field_type):
            return self._build_dataclass_schema(field_type)
        
        # Handle value objects
        if field_type in self._value_object_types:
            return SchemaField(
                schema_type=SchemaType.VALUE_OBJECT,
                properties_schema={
                    "__value_object__": SchemaField(SchemaType.STRING),
                    "value": SchemaField(SchemaType.STRING)  # Simplified for now
                }
            )
        
        # Fallback to generic object
        return SchemaField(SchemaType.OBJECT)


def create_entity_schema(entity_type: Type[T], 
                        value_object_types: Optional[List[Type]] = None) -> SerializationSchema:
    """Create a serialization schema for a domain entity.
    
    Args:
        entity_type: Entity type to create schema for
        value_object_types: List of value object types
        
    Returns:
        Serialization schema
    """
    builder = DomainEntitySchemaBuilder()
    
    if value_object_types:
        for vo_type in value_object_types:
            builder.register_value_object(vo_type)
    
    return builder.build_schema(entity_type)