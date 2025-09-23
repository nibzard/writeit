"""CLI Infrastructure for WriteIt.

Provides base command functionality, error handling, and output formatting
for the WriteIt command-line interface with integration to the CQRS architecture.
"""

from .base_command import (
    BaseCommand,
    CommandContext,
    CommandExecutionError,
    ValidationCommandError,
    ServiceCommandError,
)

from .error_handler import (
    CLIErrorHandler,
    ErrorContext,
    ErrorSeverity,
    ErrorSuggestion,
    handle_cli_error,
)

from .output_formatter import (
    CLIOutputFormatter,
    OutputFormat,
    create_formatter,
)

__all__ = [
    # Base command infrastructure
    "BaseCommand",
    "CommandContext", 
    "CommandExecutionError",
    "ValidationCommandError",
    "ServiceCommandError",
    
    # Error handling
    "CLIErrorHandler",
    "ErrorContext",
    "ErrorSeverity", 
    "ErrorSuggestion",
    "handle_cli_error",
    
    # Output formatting
    "CLIOutputFormatter",
    "OutputFormat",
    "create_formatter",
]