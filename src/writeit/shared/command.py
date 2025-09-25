"""Base CQRS Command infrastructure.

Provides base classes and interfaces for implementing Command Query
Responsibility Segregation (CQRS) pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeVar, Generic, Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class Command(ABC):
    """Base class for all commands.
    
    Commands represent write operations that change system state.
    They should be immutable and contain all data needed for execution.
    """
    
    command_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    workspace_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize command with defaults."""
        # Field default factories handle the initialization now
        pass


@dataclass(frozen=True)
class CommandResult(ABC):
    """Base class for command execution results.
    
    Contains the outcome of command execution including success/failure,
    data returned, and any errors or warnings.
    """
    
    success: bool = True
    message: str = ""
    result_data: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Initialize result with defaults."""
        # Field default factories handle the initialization now
        pass
    
    @property
    def has_errors(self) -> bool:
        """Check if result has errors."""
        return bool(self.errors)
    
    @property
    def has_warnings(self) -> bool:
        """Check if result has warnings."""
        return bool(self.warnings)


TCommand = TypeVar('TCommand', bound=Command)
TResult = TypeVar('TResult', bound=CommandResult)


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """Base interface for command handlers.
    
    Command handlers contain the business logic for executing commands.
    Each command type should have a corresponding handler.
    """
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """Execute the command and return result.
        
        Args:
            command: The command to execute
            
        Returns:
            Result of command execution
            
        Raises:
            CommandExecutionError: If command execution fails
        """
        pass
    
    async def validate(self, command: TCommand) -> List[str]:
        """Validate command before execution.
        
        Args:
            command: The command to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        return []
    
    async def can_handle(self, command: TCommand) -> bool:
        """Check if this handler can execute the command.
        
        Args:
            command: The command to check
            
        Returns:
            True if handler can execute the command
        """
        return True


class CommandBus(ABC, Generic[TCommand, TResult]):
    """Interface for command bus that routes commands to handlers."""
    
    @abstractmethod
    async def send(self, command: TCommand) -> TResult:
        """Send command for execution.
        
        Args:
            command: Command to execute
            
        Returns:
            Command execution result
            
        Raises:
            CommandHandlerNotFoundError: If no handler found for command
            CommandExecutionError: If command execution fails
        """
        pass
    
    @abstractmethod
    def register_handler(
        self, 
        command_type: type[TCommand], 
        handler: CommandHandler[TCommand, TResult]
    ) -> None:
        """Register command handler for command type.
        
        Args:
            command_type: Type of command to handle
            handler: Handler instance
        """
        pass


# Command Exceptions

class CommandError(Exception):
    """Base exception for command-related errors."""
    
    def __init__(self, message: str, command: Optional[Command] = None):
        super().__init__(message)
        self.command = command


class CommandValidationError(CommandError):
    """Exception raised when command validation fails."""
    
    def __init__(
        self, 
        message: str, 
        validation_errors: List[str], 
        command: Optional[Command] = None
    ):
        super().__init__(message, command)
        self.validation_errors = validation_errors


class CommandHandlerNotFoundError(CommandError):
    """Exception raised when no handler found for command."""
    pass


class CommandExecutionError(CommandError):
    """Exception raised when command execution fails."""
    
    def __init__(
        self, 
        message: str, 
        inner_exception: Optional[Exception] = None,
        command: Optional[Command] = None
    ):
        super().__init__(message, command)
        self.inner_exception = inner_exception


# Simple Command Bus Implementation

class SimpleCommandBus(CommandBus[TCommand, TResult]):
    """Simple in-memory command bus implementation."""
    
    def __init__(self) -> None:
        self._handlers: Dict[type[TCommand], CommandHandler[TCommand, TResult]] = {}
    
    async def send(self, command: TCommand) -> TResult:
        """Send command for execution."""
        command_type = type(command)
        
        if command_type not in self._handlers:
            raise CommandHandlerNotFoundError(
                f"No handler registered for command type: {command_type.__name__}",
                command
            )
        
        handler = self._handlers[command_type]
        
        # Validate command
        validation_errors = await handler.validate(command)
        if validation_errors:
            raise CommandValidationError(
                f"Command validation failed: {', '.join(validation_errors)}",
                validation_errors,
                command
            )
        
        # Check if handler can execute
        if not await handler.can_handle(command):
            raise CommandExecutionError(
                f"Handler cannot execute command: {command_type.__name__}",
                inner_exception=None,
                command=command
            )
        
        try:
            # Execute command
            return await handler.handle(command)
        except Exception as e:
            raise CommandExecutionError(
                f"Command execution failed: {str(e)}",
                e,
                command
            )
    
    def register_handler(
        self, 
        command_type: type[TCommand], 
        handler: CommandHandler[TCommand, TResult]
    ) -> None:
        """Register command handler."""
        self._handlers[command_type] = handler
    
    def get_registered_commands(self) -> List[type]:
        """Get list of registered command types."""
        return list(self._handlers.keys())
    
    def has_handler(self, command_type: type) -> bool:
        """Check if handler is registered for command type."""
        return command_type in self._handlers