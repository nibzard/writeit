"""ExecutionMode value object.

Value object representing different execution modes for WriteIt operations.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Self, Dict, Any, Optional


class ExecutionModeType(str, Enum):
    """Execution mode types."""
    CLI = "cli"
    TUI = "tui"
    SERVER = "server"
    BATCH = "batch"
    TEST = "test"


@dataclass(frozen=True, eq=True)
class ExecutionMode:
    """Value object representing execution mode.
    
    Encapsulates execution context information including mode type,
    output preferences, and interaction capabilities.
    
    Examples:
        # Create specific modes
        cli_mode = ExecutionMode.cli()
        tui_mode = ExecutionMode.tui()
        server_mode = ExecutionMode.server()
        
        # Create with options
        cli_mode = ExecutionMode.cli(
            output_format="json",
            verbose=True
        )
        
        # Check capabilities
        assert cli_mode.supports_interaction()
        assert tui_mode.supports_real_time_updates()
        assert server_mode.supports_websockets()
    """
    
    mode_type: ExecutionModeType
    output_format: str = "rich"
    supports_interaction: bool = True
    supports_streaming: bool = False
    supports_websockets: bool = False
    supports_real_time_updates: bool = False
    batch_size: Optional[int] = None
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Validate execution mode."""
        if not isinstance(self.mode_type, ExecutionModeType):
            raise TypeError("Mode type must be an ExecutionModeType")
            
        if not self.output_format or not isinstance(self.output_format, str):
            raise ValueError("Output format must be a non-empty string")
            
        valid_formats = {"rich", "plain", "json", "yaml", "markdown"}
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {self.output_format}. Must be one of {valid_formats}")
            
        if self.batch_size is not None:
            if not isinstance(self.batch_size, int) or self.batch_size <= 0:
                raise ValueError("Batch size must be a positive integer")
                
        if self.timeout_seconds is not None:
            if not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
                raise ValueError("Timeout must be a positive integer")
        
        # Initialize metadata if None
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
    
    @classmethod
    def cli(
        cls,
        output_format: str = "rich",
        verbose: bool = False,
        timeout_seconds: Optional[int] = None
    ) -> Self:
        """Create CLI execution mode.
        
        Args:
            output_format: Output format preference
            verbose: Enable verbose output
            timeout_seconds: Execution timeout
            
        Returns:
            CLI execution mode
        """
        metadata = {"verbose": verbose}
        
        return cls(
            mode_type=ExecutionModeType.CLI,
            output_format=output_format,
            supports_interaction=True,
            supports_streaming=False,
            supports_websockets=False,
            supports_real_time_updates=False,
            timeout_seconds=timeout_seconds,
            metadata=metadata
        )
    
    @classmethod
    def tui(
        cls,
        output_format: str = "rich",
        enable_mouse: bool = True,
        refresh_rate: int = 10
    ) -> Self:
        """Create TUI execution mode.
        
        Args:
            output_format: Output format preference
            enable_mouse: Enable mouse interaction
            refresh_rate: Screen refresh rate (Hz)
            
        Returns:
            TUI execution mode
        """
        metadata = {
            "enable_mouse": enable_mouse,
            "refresh_rate": refresh_rate
        }
        
        return cls(
            mode_type=ExecutionModeType.TUI,
            output_format=output_format,
            supports_interaction=True,
            supports_streaming=True,
            supports_websockets=False,
            supports_real_time_updates=True,
            metadata=metadata
        )
    
    @classmethod
    def server(
        cls,
        output_format: str = "json",
        enable_websockets: bool = True,
        timeout_seconds: Optional[int] = 300
    ) -> Self:
        """Create server execution mode.
        
        Args:
            output_format: Output format preference
            enable_websockets: Enable WebSocket support
            timeout_seconds: Request timeout
            
        Returns:
            Server execution mode
        """
        metadata = {"enable_websockets": enable_websockets}
        
        return cls(
            mode_type=ExecutionModeType.SERVER,
            output_format=output_format,
            supports_interaction=False,
            supports_streaming=True,
            supports_websockets=enable_websockets,
            supports_real_time_updates=True,
            timeout_seconds=timeout_seconds,
            metadata=metadata
        )
    
    @classmethod
    def batch(
        cls,
        batch_size: int = 10,
        output_format: str = "json",
        timeout_seconds: Optional[int] = 3600
    ) -> Self:
        """Create batch execution mode.
        
        Args:
            batch_size: Number of items to process in batch
            output_format: Output format preference
            timeout_seconds: Batch timeout
            
        Returns:
            Batch execution mode
        """
        metadata = {"parallel_execution": True}
        
        return cls(
            mode_type=ExecutionModeType.BATCH,
            output_format=output_format,
            supports_interaction=False,
            supports_streaming=False,
            supports_websockets=False,
            supports_real_time_updates=False,
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
            metadata=metadata
        )
    
    @classmethod
    def test(
        cls,
        output_format: str = "plain",
        fast_mode: bool = True
    ) -> Self:
        """Create test execution mode.
        
        Args:
            output_format: Output format preference
            fast_mode: Enable fast execution for testing
            
        Returns:
            Test execution mode
        """
        metadata = {
            "fast_mode": fast_mode,
            "disable_cache": True,
            "mock_llm": True
        }
        
        return cls(
            mode_type=ExecutionModeType.TEST,
            output_format=output_format,
            supports_interaction=False,
            supports_streaming=False,
            supports_websockets=False,
            supports_real_time_updates=False,
            timeout_seconds=30,  # Short timeout for tests
            metadata=metadata
        )
    
    def is_cli(self) -> bool:
        """Check if this is CLI mode."""
        return self.mode_type == ExecutionModeType.CLI
    
    def is_tui(self) -> bool:
        """Check if this is TUI mode."""
        return self.mode_type == ExecutionModeType.TUI
    
    def is_server(self) -> bool:
        """Check if this is server mode."""
        return self.mode_type == ExecutionModeType.SERVER
    
    def is_batch(self) -> bool:
        """Check if this is batch mode."""
        return self.mode_type == ExecutionModeType.BATCH
    
    def is_test(self) -> bool:
        """Check if this is test mode."""
        return self.mode_type == ExecutionModeType.TEST
    
    def is_interactive(self) -> bool:
        """Check if mode supports user interaction."""
        return self.supports_interaction
    
    def can_stream(self) -> bool:
        """Check if mode supports streaming output."""
        return self.supports_streaming
    
    def can_use_websockets(self) -> bool:
        """Check if mode supports WebSocket communication."""
        return self.supports_websockets
    
    def can_update_real_time(self) -> bool:
        """Check if mode supports real-time updates."""
        return self.supports_real_time_updates
    
    def requires_batch_processing(self) -> bool:
        """Check if mode requires batch processing."""
        return self.batch_size is not None
    
    def get_effective_batch_size(self) -> int:
        """Get effective batch size (1 if not batched)."""
        return self.batch_size or 1
    
    def get_effective_timeout(self) -> int:
        """Get effective timeout in seconds (default 300)."""
        return self.timeout_seconds or 300
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def with_output_format(self, output_format: str) -> Self:
        """Create new mode with different output format.
        
        Args:
            output_format: New output format
            
        Returns:
            New execution mode with updated format
        """
        return ExecutionMode(
            mode_type=self.mode_type,
            output_format=output_format,
            supports_interaction=self.supports_interaction,
            supports_streaming=self.supports_streaming,
            supports_websockets=self.supports_websockets,
            supports_real_time_updates=self.supports_real_time_updates,
            batch_size=self.batch_size,
            timeout_seconds=self.timeout_seconds,
            metadata=self.metadata.copy() if self.metadata else {}
        )
    
    def with_timeout(self, timeout_seconds: int) -> Self:
        """Create new mode with different timeout.
        
        Args:
            timeout_seconds: New timeout in seconds
            
        Returns:
            New execution mode with updated timeout
        """
        return ExecutionMode(
            mode_type=self.mode_type,
            output_format=self.output_format,
            supports_interaction=self.supports_interaction,
            supports_streaming=self.supports_streaming,
            supports_websockets=self.supports_websockets,
            supports_real_time_updates=self.supports_real_time_updates,
            batch_size=self.batch_size,
            timeout_seconds=timeout_seconds,
            metadata=self.metadata.copy() if self.metadata else {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode_type": self.mode_type.value,
            "output_format": self.output_format,
            "supports_interaction": self.supports_interaction,
            "supports_streaming": self.supports_streaming,
            "supports_websockets": self.supports_websockets,
            "supports_real_time_updates": self.supports_real_time_updates,
            "batch_size": self.batch_size,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Execution mode instance
        """
        mode_type = ExecutionModeType(data["mode_type"])
        
        return cls(
            mode_type=mode_type,
            output_format=data.get("output_format", "rich"),
            supports_interaction=data.get("supports_interaction", True),
            supports_streaming=data.get("supports_streaming", False),
            supports_websockets=data.get("supports_websockets", False),
            supports_real_time_updates=data.get("supports_real_time_updates", False),
            batch_size=data.get("batch_size"),
            timeout_seconds=data.get("timeout_seconds"),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation."""
        parts = [self.mode_type.value]
        if self.output_format != "rich":
            parts.append(f"format={self.output_format}")
        if self.batch_size:
            parts.append(f"batch={self.batch_size}")
        return f"ExecutionMode({', '.join(parts)})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"ExecutionMode(type={self.mode_type.value}, "
                f"format={self.output_format}, interactive={self.supports_interaction})")
    
    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash((
            self.mode_type,
            self.output_format,
            self.supports_interaction,
            self.supports_streaming,
            self.supports_websockets,
            self.supports_real_time_updates,
            self.batch_size,
            self.timeout_seconds
        ))
