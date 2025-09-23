"""Modern CLI commands using CQRS architecture.

Updated CLI commands that integrate with the domain-driven design
application services for better separation of concerns and maintainability.
"""

from .workspace_commands import app as workspace_app
from .pipeline_commands import app as pipeline_app

__all__ = [
    "workspace_app",
    "pipeline_app",
]