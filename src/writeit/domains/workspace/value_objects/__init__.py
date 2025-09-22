"""Workspace domain value objects.

Value objects provide immutable, validated data structures that represent
concepts in the workspace domain.
"""

from .workspace_name import WorkspaceName
from .workspace_path import WorkspacePath
from .configuration_value import (
    ConfigurationValue,
    StringConfigValue,
    IntConfigValue,
    BoolConfigValue,
    ListConfigValue,
    DictConfigValue,
    string_config,
    int_config,
    bool_config,
    list_config,
    dict_config
)

__all__ = [
    # Core value objects
    'WorkspaceName',
    'WorkspacePath',
    
    # Configuration value objects
    'ConfigurationValue',
    'StringConfigValue',
    'IntConfigValue', 
    'BoolConfigValue',
    'ListConfigValue',
    'DictConfigValue',
    
    # Configuration factories
    'string_config',
    'int_config',
    'bool_config',
    'list_config',
    'dict_config'
]
