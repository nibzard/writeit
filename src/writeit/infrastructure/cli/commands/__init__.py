"""Modern CLI commands using CQRS architecture.

Updated CLI commands that integrate with the domain-driven design
application services for better separation of concerns and maintainability.
"""

from .workspace_commands import app as workspace_app
from .pipeline_commands import app as pipeline_app
from .init_commands import app as init_app
from .template_commands import app as template_app
from .validate_commands import app as validate_app

__all__ = [
    "workspace_app",
    "pipeline_app", 
    "init_app",
    "template_app",
    "validate_app",
]