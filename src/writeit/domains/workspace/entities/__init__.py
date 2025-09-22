"""Workspace domain entities.

Entities represent the core business objects in the workspace domain
with identity and mutable state.
"""

from .workspace import Workspace
from .workspace_configuration import WorkspaceConfiguration

__all__ = [
    'Workspace',
    'WorkspaceConfiguration'
]
