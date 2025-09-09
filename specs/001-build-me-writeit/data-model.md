# Data Model: WriteIt LLM Article Pipeline

**Phase 1 Design Artifact** | **Date**: 2025-09-08

## Core Entities

### PipelineConfiguration
**Purpose**: Defines the template for article generation workflows
- `name`: str - Human-readable identifier ("tech-article-pipeline")
- `description`: str - Purpose and scope description  
- `created`: datetime - Template creation timestamp
- `defaults`: Dict[str, Any] - Default parameters (temperature, max_tokens, style_primer)
- `inputs`: List[InputSpec] - Required user inputs with validation
- `steps`: List[StepSpec] - Ordered pipeline steps with templates and models

**Validation Rules**:
- Name must be unique within user's pipeline collection
- At least one input must be marked as required
- Steps must form valid sequential workflow
- All template variables must be defined in inputs or previous steps

**State Transitions**: Static configuration, no state changes after creation

### PipelineRun
**Purpose**: Represents a specific execution instance of a pipeline configuration
- `pipeline_run_id`: UUID - Unique identifier for this execution
- `configuration_id`: str - Reference to PipelineConfiguration
- `parent_pipeline_run_id`: Optional[UUID] - For branched runs
- `branch_point`: Optional[StepName] - Step where this branch diverged
- `created_at`: datetime - Execution start time
- `current_step`: StepName - Active step (angles, outline, draft, polish)
- `status`: PipelineStatus - INITIALIZING, RUNNING, PAUSED, COMPLETED, ERROR
- `user_inputs`: Dict[str, str] - Initial inputs (source_material, target_audience)
- `steps`: Dict[StepName, StepState] - Current state of each step

**Validation Rules**:
- Pipeline run ID must be unique across all users
- Parent pipeline run must exist if specified
- Branch point must be valid step name if specified
- Current step must not exceed completed steps
- Status transitions follow valid state machine

**State Transitions**: 
- INITIALIZING → RUNNING (on first step execution)
- RUNNING → PAUSED (on user interrupt)
- RUNNING → COMPLETED (on final step completion)  
- Any state → ERROR (on system failure)

### StepState
**Purpose**: Tracks execution state and results for a single pipeline step
- `step_name`: StepName - Step identifier (angles, outline, draft, polish)
- `status`: StepStatus - PENDING, RUNNING, COMPLETED, SKIPPED
- `started_at`: Optional[datetime] - Step execution start time
- `completed_at`: Optional[datetime] - Step completion time
- `ai_responses`: List[AIResponse] - All model responses for this step
- `user_selection`: Optional[int] - Index of selected response
- `user_feedback`: Optional[str] - User comments for next step
- `merged_content`: Optional[str] - Result of combining multiple responses
- `retry_count`: int - Number of regeneration attempts

**Validation Rules**:
- Step name must be valid pipeline step
- Started/completed timestamps must be sequential
- User selection must be valid index into ai_responses
- AI responses list cannot be empty for COMPLETED status
- Retry count cannot exceed system maximum (3)

**State Transitions**:
- PENDING → RUNNING (on step start)
- RUNNING → COMPLETED (on user selection)
- COMPLETED → RUNNING (on regenerate request)

### AIResponse  
**Purpose**: Individual LLM model response within a pipeline step
- `response_id`: UUID - Unique identifier for this response
- `model_name`: str - AI model used ("gpt-4o", "claude-sonnet-4")
- `provider`: str - AI provider ("openai", "anthropic", "local")
- `prompt_used`: str - Exact prompt sent to model
- `raw_output`: str - Complete model response
- `processed_content`: str - Cleaned/formatted response
- `created_at`: datetime - Response generation timestamp
- `usage_stats`: TokenUsage - Token consumption and costs
- `processing_time`: float - Generation time in seconds
- `quality_score`: Optional[float] - Optional response quality metric

**Validation Rules**:
- Response ID must be globally unique
- Model name and provider must be supported combinations
- Prompt cannot be empty
- Raw output must contain actual response content
- Processing time must be positive
- Quality score must be between 0.0 and 1.0 if specified

**State Transitions**: Immutable once created

### StylePrimer
**Purpose**: Reusable writing style guidelines and voice definitions  
- `primer_id`: str - Unique identifier ("tech-journalist", "academic")
- `name`: str - Human-readable name
- `description`: str - Style description and use cases
- `content`: str - Full style guide content
- `voice_attributes`: Dict[str, str] - Voice characteristics
- `example_openings`: List[str] - Sample article openings
- `guidelines`: Dict[str, List[str]] - Dos and don'ts by category
- `created_at`: datetime - Primer creation time
- `last_used`: datetime - Most recent usage timestamp

**Validation Rules**:
- Primer ID must be unique and follow naming conventions
- Content cannot be empty
- Voice attributes must include required keys (tone, structure, language)
- Example openings must be non-empty if provided
- Guidelines must include 'avoid' and 'prefer' categories

**State Transitions**: 
- last_used updated on pipeline execution
- Content can be modified but maintains version history

### UserSession
**Purpose**: Manages active application state and user preferences
- `session_id`: UUID - Unique session identifier
- `user_id`: str - User identifier (for future multi-user support)
- `active_pipeline_run_id`: Optional[UUID] - Currently active pipeline
- `workspace_path`: Path - User's WriteIt workspace directory
- `preferences`: UserPreferences - Application settings
- `created_at`: datetime - Session start time
- `last_activity`: datetime - Most recent user interaction
- `websocket_connection_id`: Optional[str] - Active WebSocket connection

**Validation Rules**:
- Session ID must be unique across active sessions
- Workspace path must exist and be writable
- Active pipeline run must exist if specified
- Last activity cannot be in future
- WebSocket connection must be valid if specified

**State Transitions**:
- last_activity updated on every user interaction
- active_pipeline_run_id changes on pipeline switching
- websocket_connection_id updated on connection changes

### UserPreferences
**Purpose**: Persistent user configuration and settings
- `default_models`: Dict[StepName, str] - Preferred models per step
- `style_primer`: str - Default style primer ID
- `auto_save_enabled`: bool - Automatic progress saving
- `streaming_buffer_size`: int - Token batching preference
- `keyboard_shortcuts`: Dict[str, str] - Custom key bindings
- `theme`: str - TUI color scheme
- `max_concurrent_pipelines`: int - Concurrent execution limit
- `export_format`: str - Default output format (yaml, json, markdown)

**Validation Rules**:
- Default models must reference valid model identifiers
- Style primer must exist if specified
- Buffer size must be positive integer
- Keyboard shortcuts cannot conflict with system bindings
- Max concurrent pipelines between 1 and 10
- Export format must be supported

**State Transitions**: Updated through user preference modifications

## Entity Relationships

### Pipeline Configuration → Pipeline Run (1:N)
- One configuration can generate multiple execution runs
- Each run references its template configuration
- Configurations are immutable; runs track actual execution

### Pipeline Run → Step State (1:4) 
- Each run contains exactly 4 step states (angles, outline, draft, polish)
- Step states are created when run is initialized
- Order is enforced: angles → outline → draft → polish

### Step State → AI Response (1:N)
- Each step can have multiple AI responses from different models
- User selects one response to proceed to next step
- All responses are preserved for audit and comparison

### Pipeline Run → Pipeline Run (1:N) - Branching
- Parent-child relationship for branched executions
- Child runs share history up to branch point
- Enables exploring alternative paths

### Style Primer → Pipeline Configuration (1:N)
- Multiple configurations can reference same style primer
- Primer content is included in configuration for consistency
- Style evolution tracked through primer versioning

### User Session → Pipeline Run (1:1)
- One active pipeline run per session
- Session persists user context and preferences
- Multiple sessions can exist for concurrent pipelines

## LMDB Storage Schema

### Key Patterns
```
# Pipeline configurations
config:{config_id} → PipelineConfiguration

# Pipeline runs  
run:{pipeline_run_id} → PipelineRun
run_by_config:{config_id}:{timestamp} → pipeline_run_id

# Step states and responses
step:{pipeline_run_id}:{step_name} → StepState
response:{response_id} → AIResponse
step_responses:{pipeline_run_id}:{step_name} → List[response_id]

# Branching relationships
branch_parent:{child_id} → parent_pipeline_run_id
branch_children:{parent_id} → List[child_pipeline_run_id]

# Style primers
primer:{primer_id} → StylePrimer
primer_usage:{primer_id}:{timestamp} → pipeline_run_id

# User sessions
session:{session_id} → UserSession
active_sessions:{user_id} → List[session_id]

# Indices for efficient queries
recent_runs:{user_id} → List[{pipeline_run_id, timestamp}]
completed_runs:{user_id} → List[{pipeline_run_id, timestamp}]
```

### Data Serialization
- All entities serialized as JSON with Pydantic validation
- Binary data (if any) stored separately with reference keys
- Timestamps stored as ISO 8601 strings
- UUIDs stored as string representations
- Enums stored as string values

This data model provides WriteIt with a complete foundation for pipeline execution, artifact versioning, branching operations, and user session management while supporting the event sourcing patterns identified in the research phase.