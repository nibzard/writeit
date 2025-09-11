# ABOUTME: Core data models for WriteIt pipelines
# ABOUTME: Defines Pipeline, PipelineRun, StepExecution and related structures

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class PipelineStatus(str, Enum):
    """Status enumeration for pipeline runs."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Status enumeration for step execution."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineInput:
    """Configuration for a pipeline input field."""
    key: str
    type: str  # 'text', 'choice', 'number', 'boolean'
    label: str
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help: str = ""
    options: List[Dict[str, str]] = field(default_factory=list)
    max_length: Optional[int] = None
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStep:
    """Configuration for a pipeline step."""
    key: str
    name: str
    description: str
    type: str  # 'llm_generate', 'user_input', 'transform', 'validate'
    prompt_template: str
    selection_prompt: str = ""
    model_preference: List[str] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    ui: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    parallel: bool = False
    retry_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pipeline:
    """Complete pipeline configuration."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    steps: List[PipelineStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class StepExecution:
    """Record of a single step execution."""
    step_key: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    responses: List[str] = field(default_factory=list)
    selected_response: Optional[str] = None
    user_feedback: str = ""
    tokens_used: Dict[str, int] = field(default_factory=dict)
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


@dataclass
class PipelineRun:
    """Record of a complete pipeline execution."""
    id: str
    pipeline_id: str
    workspace_name: str
    status: PipelineStatus = PipelineStatus.CREATED
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    steps: List[StepExecution] = field(default_factory=list)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_tokens_used: Dict[str, int] = field(default_factory=dict)
    total_execution_time: float = 0.0


@dataclass
class PipelineTemplate:
    """Template for creating new pipelines."""
    name: str
    description: str
    category: str
    template_path: str
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    version: str = "1.0.0"


@dataclass
class PipelineArtifact:
    """Output artifact from pipeline execution."""
    id: str
    pipeline_run_id: str
    step_key: str
    name: str
    type: str  # 'text', 'file', 'image', 'json'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    size_bytes: int = 0