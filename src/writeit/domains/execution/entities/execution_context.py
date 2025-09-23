"""Execution Context entity.

Domain entity representing the runtime execution state and context for LLM operations.
"""

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, List, Optional, Self
from enum import Enum

from ..value_objects.model_name import ModelName
from ..value_objects.execution_mode import ExecutionMode
from ..value_objects.cache_key import CacheKey


class ExecutionStatus(str, Enum):
    """Status of execution context."""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionPriority(str, Enum):
    """Priority level for execution."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExecutionContext:
    """Domain entity representing runtime execution state.
    
    Manages the context and state for LLM operations, including:
    - Execution tracking and status
    - Provider selection and failover
    - Cache management
    - Performance monitoring
    - Error handling and recovery
    
    Examples:
        context = ExecutionContext.create(
            workspace_name="my-project",
            pipeline_id="article-generator",
            execution_mode=ExecutionMode.TUI
        )
        
        # Set preferred models
        context = context.set_model_preference([
            ModelName.from_string("gpt-4o-mini"),
            ModelName.from_string("claude-3-haiku")
        ])
        
        # Track execution
        context = context.start_execution()
        context = context.complete_execution()
    """
    
    id: str
    workspace_name: str
    pipeline_id: str
    execution_mode: ExecutionMode
    status: ExecutionStatus = ExecutionStatus.CREATED
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    model_preferences: List[ModelName] = field(default_factory=list)
    provider_preferences: List[str] = field(default_factory=list)
    cache_enabled: bool = True
    streaming_enabled: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 3
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate execution context."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Execution context id must be a non-empty string")
            
        if not self.workspace_name or not isinstance(self.workspace_name, str):
            raise ValueError("Workspace name must be a non-empty string")
            
        if not self.pipeline_id or not isinstance(self.pipeline_id, str):
            raise ValueError("Pipeline id must be a non-empty string")
            
        if not isinstance(self.execution_mode, ExecutionMode):
            raise TypeError("Execution mode must be an ExecutionMode")
            
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("Status must be an ExecutionStatus")
            
        if not isinstance(self.priority, ExecutionPriority):
            raise TypeError("Priority must be an ExecutionPriority")
            
        # Validate model preferences
        for model in self.model_preferences:
            if not isinstance(model, ModelName):
                raise TypeError("Model preferences must be ModelName instances")
                
        # Validate numeric constraints
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
            
        if self.temperature is not None and not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
            
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
            
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")
            
        # Validate state consistency
        if self.status == ExecutionStatus.EXECUTING and self.started_at is None:
            raise ValueError("Executing context must have started_at set")
            
        if self.status in {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED}:
            if self.completed_at is None:
                raise ValueError("Terminal status requires completed_at to be set")
                
        if self.status == ExecutionStatus.FAILED and not self.error_message:
            raise ValueError("Failed status requires error message")
    
    @property
    def is_active(self) -> bool:
        """Check if execution is currently active."""
        return self.status in {
            ExecutionStatus.INITIALIZING,
            ExecutionStatus.READY,
            ExecutionStatus.EXECUTING
        }
    
    @property
    def is_terminal(self) -> bool:
        """Check if execution is in terminal state."""
        return self.status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED
        }
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == ExecutionStatus.FAILED
    
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def set_model_preference(self, models: List[ModelName]) -> Self:
        """Set model preferences in priority order.
        
        Args:
            models: List of models in preference order
            
        Returns:
            Updated execution context
        """
        return replace(self, model_preferences=models.copy())
    
    def add_model_preference(self, model: ModelName) -> Self:
        """Add model to preferences.
        
        Args:
            model: Model to add
            
        Returns:
            Updated execution context
        """
        if model in self.model_preferences:
            return self
            
        new_preferences = self.model_preferences + [model]
        return replace(self, model_preferences=new_preferences)
    
    def set_provider_preference(self, providers: List[str]) -> Self:
        """Set provider preferences in priority order.
        
        Args:
            providers: List of provider names in preference order
            
        Returns:
            Updated execution context
        """
        return replace(self, provider_preferences=providers.copy())
    
    def enable_caching(self, enabled: bool = True) -> Self:
        """Enable or disable caching.
        
        Args:
            enabled: Whether to enable caching
            
        Returns:
            Updated execution context
        """
        return replace(self, cache_enabled=enabled)
    
    def enable_streaming(self, enabled: bool = True) -> Self:
        """Enable or disable streaming.
        
        Args:
            enabled: Whether to enable streaming
            
        Returns:
            Updated execution context
        """
        return replace(self, streaming_enabled=enabled)
    
    def set_parameters(
        self,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_seconds: Optional[int] = None
    ) -> Self:
        """Set execution parameters.
        
        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_seconds: Request timeout
            
        Returns:
            Updated execution context
        """
        updates = {}
        if max_tokens is not None:
            updates["max_tokens"] = max_tokens
        if temperature is not None:
            updates["temperature"] = temperature
        if timeout_seconds is not None:
            updates["timeout_seconds"] = timeout_seconds
            
        return replace(self, **updates)
    
    def set_variable(self, key: str, value: Any) -> Self:
        """Set context variable.
        
        Args:
            key: Variable key
            value: Variable value
            
        Returns:
            Updated execution context
        """
        new_variables = self.variables.copy()
        new_variables[key] = value
        return replace(self, variables=new_variables)
    
    def set_variables(self, variables: Dict[str, Any]) -> Self:
        """Set multiple context variables.
        
        Args:
            variables: Variables to set
            
        Returns:
            Updated execution context
        """
        new_variables = {**self.variables, **variables}
        return replace(self, variables=new_variables)
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get context variable.
        
        Args:
            key: Variable key
            default: Default value
            
        Returns:
            Variable value or default
        """
        return self.variables.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> Self:
        """Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Updated execution context
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        return replace(self, metadata=new_metadata)
    
    def initialize(self) -> Self:
        """Initialize execution context.
        
        Returns:
            Updated context with initializing status
        """
        return replace(
            self,
            status=ExecutionStatus.INITIALIZING,
            created_at=datetime.now()
        )
    
    def mark_ready(self) -> Self:
        """Mark context as ready for execution.
        
        Returns:
            Updated context with ready status
        """
        return replace(self, status=ExecutionStatus.READY)
    
    def start_execution(self) -> Self:
        """Start execution.
        
        Returns:
            Updated context with executing status
            
        Raises:
            ValueError: If context is not ready
        """
        if self.status not in {ExecutionStatus.READY, ExecutionStatus.CREATED}:
            raise ValueError(f"Cannot start execution from status: {self.status}")
            
        return replace(
            self,
            status=ExecutionStatus.EXECUTING,
            started_at=datetime.now()
        )
    
    def complete_execution(self) -> Self:
        """Complete execution successfully.
        
        Returns:
            Updated context with completed status
            
        Raises:
            ValueError: If execution is not active
        """
        if not self.is_active:
            raise ValueError(f"Cannot complete execution from status: {self.status}")
            
        return replace(
            self,
            status=ExecutionStatus.COMPLETED,
            completed_at=datetime.now()
        )
    
    def fail_execution(self, error_message: str) -> Self:
        """Fail execution with error.
        
        Args:
            error_message: Error description
            
        Returns:
            Updated context with failed status
        """
        return replace(
            self,
            status=ExecutionStatus.FAILED,
            error_message=error_message,
            completed_at=datetime.now()
        )
    
    def cancel_execution(self) -> Self:
        """Cancel execution.
        
        Returns:
            Updated context with cancelled status
        """
        return replace(
            self,
            status=ExecutionStatus.CANCELLED,
            completed_at=datetime.now()
        )
    
    def record_performance_metric(self, key: str, value: Any) -> Self:
        """Record performance metric.
        
        Args:
            key: Metric key
            value: Metric value
            
        Returns:
            Updated context with metric
        """
        new_metrics = self.performance_metrics.copy()
        new_metrics[key] = value
        return replace(self, performance_metrics=new_metrics)
    
    def get_cache_key(self, operation: str, inputs: Dict[str, Any]) -> CacheKey:
        """Generate cache key for operation.
        
        Args:
            operation: Operation name
            inputs: Operation inputs
            
        Returns:
            Cache key
        """
        return CacheKey.from_context(
            workspace=self.workspace_name,
            pipeline_id=self.pipeline_id,
            operation=operation,
            inputs=inputs,
            model=self.model_preferences[0] if self.model_preferences else None
        )
    
    def should_use_cache(self) -> bool:
        """Check if caching should be used."""
        return self.cache_enabled
    
    def should_use_streaming(self) -> bool:
        """Check if streaming should be used."""
        return self.streaming_enabled and self.execution_mode.supports_streaming
    
    def get_preferred_model(self) -> Optional[ModelName]:
        """Get most preferred model.
        
        Returns:
            Preferred model or None if no preferences
        """
        return self.model_preferences[0] if self.model_preferences else None
    
    def get_execution_timeout(self) -> Optional[int]:
        """Get execution timeout in seconds.
        
        Returns:
            Timeout or None for no timeout
        """
        if self.timeout_seconds is not None:
            return self.timeout_seconds
            
        # Default timeouts based on execution mode
        if self.execution_mode == ExecutionMode.CLI:
            return 300  # 5 minutes for CLI
        elif self.execution_mode == ExecutionMode.TUI:
            return 600  # 10 minutes for TUI
        elif self.execution_mode == ExecutionMode.SERVER:
            return 120  # 2 minutes for server
        else:
            return None
    
    def can_retry(self, current_attempt: int) -> bool:
        """Check if operation can be retried.
        
        Args:
            current_attempt: Current attempt number (0-based)
            
        Returns:
            True if retry is allowed
        """
        return current_attempt < self.retry_attempts
    
    @classmethod
    def create(
        cls,
        workspace_name: str,
        pipeline_id: str,
        execution_mode: ExecutionMode,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        context_id: Optional[str] = None
    ) -> Self:
        """Create new execution context.
        
        Args:
            workspace_name: Workspace name
            pipeline_id: Pipeline identifier
            execution_mode: Execution mode
            priority: Execution priority
            context_id: Custom context ID
            
        Returns:
            New execution context
        """
        if context_id is None:
            context_id = f"ctx-{uuid.uuid4().hex[:8]}"
            
        return cls(
            id=context_id,
            workspace_name=workspace_name,
            pipeline_id=pipeline_id,
            execution_mode=execution_mode,
            priority=priority,
            created_at=datetime.now()
        )
    
    @classmethod
    def for_cli(
        cls,
        workspace_name: str,
        pipeline_id: str,
        **kwargs
    ) -> Self:
        """Create context for CLI execution.
        
        Args:
            workspace_name: Workspace name
            pipeline_id: Pipeline identifier
            **kwargs: Additional parameters
            
        Returns:
            CLI execution context
        """
        context = cls.create(
            workspace_name=workspace_name,
            pipeline_id=pipeline_id,
            execution_mode=ExecutionMode.CLI,
            **kwargs
        )
        
        # CLI defaults
        context = context.enable_caching(True)
        context = context.enable_streaming(False)
        
        return context
    
    @classmethod
    def for_tui(
        cls,
        workspace_name: str,
        pipeline_id: str,
        **kwargs
    ) -> Self:
        """Create context for TUI execution.
        
        Args:
            workspace_name: Workspace name
            pipeline_id: Pipeline identifier
            **kwargs: Additional parameters
            
        Returns:
            TUI execution context
        """
        context = cls.create(
            workspace_name=workspace_name,
            pipeline_id=pipeline_id,
            execution_mode=ExecutionMode.TUI,
            **kwargs
        )
        
        # TUI defaults
        context = context.enable_caching(True)
        context = context.enable_streaming(True)
        
        return context
    
    @classmethod
    def for_server(
        cls,
        workspace_name: str,
        pipeline_id: str,
        **kwargs
    ) -> Self:
        """Create context for server execution.
        
        Args:
            workspace_name: Workspace name
            pipeline_id: Pipeline identifier
            **kwargs: Additional parameters
            
        Returns:
            Server execution context
        """
        context = cls.create(
            workspace_name=workspace_name,
            pipeline_id=pipeline_id,
            execution_mode=ExecutionMode.SERVER,
            **kwargs
        )
        
        # Server defaults
        context = context.enable_caching(True)
        context = context.enable_streaming(True)
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "workspace_name": self.workspace_name,
            "pipeline_id": self.pipeline_id,
            "execution_mode": str(self.execution_mode),
            "status": self.status.value,
            "priority": self.priority.value,
            "model_preferences": [str(model) for model in self.model_preferences],
            "provider_preferences": self.provider_preferences,
            "cache_enabled": self.cache_enabled,
            "streaming_enabled": self.streaming_enabled,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "performance_metrics": self.performance_metrics
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"ExecutionContext({self.id} - {self.status.value})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"ExecutionContext(id='{self.id}', pipeline='{self.pipeline_id}', "
                f"mode={self.execution_mode}, status={self.status.value})")