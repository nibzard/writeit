# ABOUTME: Legacy models compatibility module
# ABOUTME: Provides backward compatibility for old model imports
# DEPRECATED: This module is deprecated. Use writeit.domains.pipeline entities instead.

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

# Import from DDD entities
from writeit.domains.pipeline.entities import PipelineRun as DomainPipelineRun
from writeit.domains.pipeline.value_objects import ExecutionStatus


class PipelineStatus(str, Enum):
    """Pipeline execution status enum (legacy compatibility)."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step execution status enum (legacy compatibility)."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """Legacy pipeline step model for backward compatibility."""
    key: str
    name: str
    type: str
    prompt_template: Optional[str] = None
    model_preference: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pipeline:
    """Legacy pipeline model for backward compatibility."""
    id: str
    name: str
    description: str
    steps: Dict[str, PipelineStep]
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepExecution:
    """Legacy step execution model for backward compatibility."""
    id: str
    pipeline_run_id: str
    step_key: str
    status: StepStatus
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tokens_used: Dict[str, int] = field(default_factory=dict)


@dataclass
class PipelineRun:
    """Legacy pipeline run model for backward compatibility."""
    id: str
    pipeline_id: str
    workspace_name: str
    status: PipelineStatus
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


__all__ = [
    "Pipeline",
    "PipelineStep", 
    "PipelineRun",
    "StepExecution",
    "PipelineStatus",
    "StepStatus",
]