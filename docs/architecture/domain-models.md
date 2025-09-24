# WriteIt Domain Model Diagrams

This document provides detailed domain model diagrams for WriteIt's Domain-Driven Design architecture.

## Domain Boundaries Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WriteIt System                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │     Pipeline Domain     │  │    Workspace Domain     │                  │
│  │                         │  │                         │                  │
│  │  • PipelineTemplate     │  │  • Workspace            │                  │
│  │  • PipelineRun          │  │  • WorkspaceConfig      │                  │
│  │  • PipelineStep         │  │  • TemplateManager      │                  │
│  │  • StepExecution        │  │                         │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │     Content Domain      │  │    Execution Domain     │                  │
│  │                         │  │                         │                  │
│  │  • Template             │  │  • LLMProvider          │                  │
│  │  • StylePrimer          │  │  • ExecutionContext     │                  │
│  │  • GeneratedContent     │  │  • TokenUsage          │                  │
│  │  • ValidationResult     │  │  • CacheEntry          │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Storage Domain                                   │ │
│  │                                                                         │ │
│  │  • StorageManager    • DatabaseConnection   • TransactionContext      │ │
│  │  • WorkspaceAwareStorage   • CacheStorage   • FileStorage              │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Domain Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Pipeline Domain                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      PipelineTemplate                                    │ │
│  │                                                                         │ │
│  │  • id: PipelineId                                                        │ │
│  │  • name: string                                                         │ │
│  │  • description: string                                                  │ │
│  │  • version: string                                                      │ │
│  │  • metadata: PipelineMetadata                                          │ │
│  │  • inputs: List[PipelineInput]                                         │ │
│  │  • steps: List[PipelineStepTemplate]                                    │ │
│  │  • defaults: Dict[str, Any]                                             │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • validate()                                                           │ │
│  │  • get_step_dependencies()                                              │ │
│  │  • render_step_template()                                               │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         PipelineRun                                       │ │
│  │                                                                         │ │
│  │  • id: string                                                           │ │
│  │  • pipeline_id: PipelineId                                              │ │
│  │  • status: ExecutionStatus                                             │ │
│  │  • inputs: Dict[str, Any]                                               │ │
│  │  • outputs: Dict[str, Any]                                              │ │
│  │  • created_at: datetime                                                │ │
│  │  • started_at: datetime?                                               │ │
│  │  • completed_at: datetime?                                              │ │
│  │  • error: string?                                                      │ │
│  │  • steps: List[StepExecution]                                          │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • start()                                                              │ │
│  │  • complete()                                                           │ │
│  │  • fail()                                                               │ │
│  │  • add_step_result()                                                    │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        PipelineStep                                      │ │
│  │                                                                         │ │
│  │  • key: StepId                                                          │ │
│  │  • name: string                                                         │ │
│  │  • description: string                                                  │ │
│  │  • type: StepType                                                       │ │
│  │  • model_preference: ModelPreference                                   │ │
│  │  • prompt_template: PromptTemplate                                     │ │
│  │  • depends_on: List[StepId]                                             │ │
│  │  • validation: Dict[str, Any]                                           │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       StepExecution                                     │ │
│  │                                                                         │ │
│  │  • step_key: StepId                                                     │ │
│  │  • status: ExecutionStatus                                             │ │
│  │  • started_at: datetime?                                               │ │
│  │  • completed_at: datetime?                                              │ │
│  │  • responses: List[str]                                                 │ │
│  │  • selected_response: string?                                          │ │
│  │  • user_feedback: string?                                              │ │
│  │  • tokens_used: TokenUsage                                             │ │
│  │  • execution_time: float                                               │ │
│  │  • error: string?                                                      │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • start()                                                              │ │
│  │  • add_response()                                                       │ │
│  │  • select_response()                                                    │ │
│  │  • complete()                                                           │ │
│  │  • retry()                                                              │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Value Objects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Pipeline Value Objects                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │      PipelineId         │  │         StepId           │                  │
│  │                         │  │                         │                  │
│  │  • value: string        │  │  • value: string        │                  │
│  │                         │  │                         │                  │
│  │  Validation:            │  │  Validation:            │                  │
│  │  • Format: pipeline_123  │  │  • Format: step_key     │                  │
│  │  • Length: 1-100 chars  │  │  • Length: 1-50 chars   │                  │
│  │  • Characters: a-z0-9_   │  │  • Characters: a-z0-9_  │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │     PromptTemplate      │  │    ModelPreference      │                  │
│  │                         │  │                         │                  │
│  │  • template: string     │  │  • models: List[str]    │                  │
│  │  • variables: Set[str]  │  │  • fallback: str?       │                  │
│  │                         │  │                         │                  │
│  │  Methods:               │  │  Methods:               │                  │
│  │  • render(context)      │  │  • get_model()          │                  │
│  │  • validate()           │  │  • validate()           │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    ExecutionStatus                                       │ │
│  │                                                                         │ │
│  │  Values:                                                                │ │
│  │  • CREATED → RUNNING → COMPLETED                                         │ │
│  │  • CREATED → RUNNING → FAILED                                           │ │
│  │  • CREATED → RUNNING → PAUSED → RESUMED → COMPLETED/FAILED              │ │
│  │  • CREATED → CANCELLED                                                  │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • can_transition_to(target_status)                                     │ │
│  │  • get_valid_transitions()                                              │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Workspace Domain Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Workspace Domain                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                          Workspace                                       │ │
│  │                                                                         │ │
│  │  • name: WorkspaceName                                                  │ │
│  │  • path: WorkspacePath                                                  │ │
│  │  • config: WorkspaceConfig                                              │ │
│  │  • created_at: datetime                                                 │ │
│  │  • updated_at: datetime                                                 │ │
│  │  • is_active: boolean                                                   │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • activate()                                                           │ │
│  │  • deactivate()                                                         │ │
│  │  • update_config()                                                      │ │
│  │  • validate_structure()                                                 │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    WorkspaceConfig                                       │ │
│  │                                                                         │ │
│  │  • global_config: GlobalConfig                                          │ │
│  │  • workspace_settings: Dict[str, ConfigurationValue]                   │ │
│  │  • template_paths: List[WorkspacePath]                                 │ │
│  │  • storage_config: StorageConfig                                       │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • get_setting(key)                                                     │ │
│  │  • set_setting(key, value)                                              │ │
│  │  • inherit_from_global()                                                │ │
│  │  • validate()                                                           │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Value Objects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Workspace Value Objects                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │     WorkspaceName       │  │      WorkspacePath       │                  │
│  │                         │  │                         │                  │
│  │  • value: string        │  │  • path: Path           │                  │
│  │                         │  │                         │                  │
│  │  Validation:            │  │  Validation:            │                  │
│  │  • Length: 1-50 chars   │  │  • Absolute path        │                  │
│  │  • Characters: a-z0-9_- │  │  • Writable directory   │                  │
│  │  • No spaces/special    │  │  • No symlink targets   │                  │
│  │  • Reserved names      │  │                         │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                  ConfigurationValue                                      │ │
│  │                                                                         │ │
│  │  • key: string                                                          │ │
│  │  • value: Any                                                           │ │
│  │  • type: Type                                                            │ │
│  │  • is_required: boolean                                                 │ │
│  │  • default_value: Any?                                                  │ │
│  │  • validation_rules: List[ValidationRule]                              │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • validate(value)                                                      │ │
│  │  • coerce_type(value)                                                   │ │
│  │  • get_default()                                                        │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Content Domain Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Content Domain                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                          Template                                        │ │
│  │                                                                         │ │
│  │  • id: TemplateId                                                       │ │
│  │  • name: TemplateName                                                   │ │
│  │  • type: ContentType                                                    │ │
│  │  • content: string                                                      │ │
│  │  • metadata: Dict[str, Any]                                            │ │
│  │  • version: string                                                      │ │
│  │  • created_at: datetime                                                 │ │
│  │  • updated_at: datetime                                                 │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • validate()                                                           │ │
│  │  • render(context)                                                      │ │
│  │  • get_variables()                                                      │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        StylePrimer                                       │ │
│  │                                                                         │ │
│  │  • id: StyleId                                                           │ │
│  │  • name: StyleName                                                      │ │
│  │  • guidelines: string                                                   │ │
│  │  • tone: string                                                         │ │
│  │  • format: ContentFormat                                                │ │
│  │  • restrictions: List[str]                                              │ │
│  │  • examples: List[Dict[str, str]]                                       │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • validate_content(content)                                            │ │
│  │  • apply_guidelines(content)                                            │ │
│  │  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    GeneratedContent                                       │ │
│  │                                                                         │ │
│  │  • id: ContentId                                                        │ │
│  │  • template_id: TemplateId                                              │ │
│  │  • style_id: StyleId?                                                   │ │
│  │  • content: string                                                      │ │
│  │  • metadata: Dict[str, Any]                                            │ │
│  │  • validation_result: ValidationResult?                                │ │
│  │  • created_at: datetime                                                 │ │
│  │  • generated_by: string                                                 │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • validate()                                                           │ │
│  │  • apply_style(primer)                                                  │ │
│  │  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Value Objects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Content Value Objects                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │      TemplateId          │  │        ContentId         │                  │
│  │                         │  │                         │                  │
│  │  • value: string        │  │  • value: string        │                  │
│  │                         │  │                         │                  │
│  │  Validation:            │  │  Validation:            │                  │
│  │  • UUID format          │  │  • UUID format          │                  │
│  │  • Version support      │  │  • Version support      │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │      ContentType        │  │      ContentFormat       │                  │
│  │                         │  │                         │                  │
│  │  Values:                │  │  Values:                │                  │
│  │  • PIPELINE             │  │  • MARKDOWN             │                  │
│  │  • STYLE_PRIMER         │  │  • HTML                 │                  │
│  │  • PROMPT_TEMPLATE      │  │  • PLAIN_TEXT           │                  │
│  │  • DOCUMENT             │  │  • JSON                 │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                   ValidationResult                                       │ │
│  │                                                                         │ │
│  │  • is_valid: boolean                                                     │ │
│  │  • errors: List[ValidationError]                                        │ │
│  │  • warnings: List[ValidationWarning]                                    │ │
│  │  • score: float                                                         │ │
│  │  • details: Dict[str, Any]                                             │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • add_error(message)                                                   │ │
│  │  • add_warning(message)                                                 │ │
│  │  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Execution Domain Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Execution Domain                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      ExecutionContext                                     │ │
│  │                                                                         │ │
│  │  • context_id: string                                                    │ │
│  │  • pipeline_id: PipelineId                                               │ │
│  │  • run_id: string                                                       │ │
│  │  • workspace_name: WorkspaceName                                        │ │
│  │  • model_name: ModelName                                                │ │
│  │  • inputs: Dict[str, Any]                                              │ │
│  │  • step_outputs: Dict[str, Any]                                         │ │
│  │  • metadata: Dict[str, Any]                                            │ │
│  │  • token_tracker: TokenUsage                                           │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • get_step_output(step_key)                                            │ │
│  │  • set_step_output(step_key, value)                                     │ │
│  │  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        LLMProvider                                       │ │
│  │                                                                         │ │
│  │  • name: string                                                          │ │
│  │  • api_key: string?                                                      │
│  │  • base_url: string?                                                     │
│  │  • models: List[ModelName]                                              │ │
│  │  • rate_limits: RateLimits                                              │ │
│  │  • is_active: boolean                                                   │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • call_model(prompt, model)                                            │ │
│  │  • health_check()                                                       │ │
│  │  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │                                      │
│                                      ▼                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         CacheEntry                                       │ │
│  │                                                                         │ │
│  │  • cache_key: string                                                     │ │
│  │  • prompt: string                                                        │ │
│  │  • model_name: ModelName                                                │ │
│  │  • response: string                                                     │ │
│  │  • tokens_used: TokenUsage                                              │ │
│  │  • created_at: datetime                                                 │ │
│  │  • accessed_at: datetime                                                 │ │
│  │  • access_count: int                                                   │ │
│  │  • metadata: Dict[str, Any]                                            │ │
│  │                                                                         │ │
│  │  Methods:                                                               │ │
│  │  • is_expired()                                                          │ │
│  │  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Value Objects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Execution Value Objects                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │        ModelName         │  │        TokenCount        │                  │
│  │                         │  │                         │                  │
│  │  • value: string        │  │  • prompt_tokens: int   │                  │
│  │                         │  │  • completion_tokens: int│                  │
│  │  Validation:            │  │  • total_tokens: int    │                  │
│  │  • Known models         │  │                         │                  │
│  │  • Provider support     │  │  Methods:               │                  │
│  │                         │  │  • add_tokens()         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │        CacheKey          │  │       ExecutionMode       │                  │
│  │                         │  │                         │                  │
│  │  • value: string        │  │  Values:                │                  │
│  │                         │  │  • CLI                  │                  │
│  │  Generation:            │  │  • TUI                  │                  │
│  │  • SHA256 hash          │  │  • SERVER               │                  │
│  │  • prompt + model       │  │  • BATCH                │                  │
│  │  • context + workspace  │  │                         │                  │
│  │                         │  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Domain Relationships

### Aggregate Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Domain Relationships                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Pipeline Aggregate Root: PipelineTemplate                                  │
│  ├─ PipelineRun (Entity)                                                    │
│  │  ├─ PipelineStep (Entity)                                               │
│  │  │  └─ StepExecution (Entity)                                           │
│  │  └─ ExecutionContext (Value Object)                                     │
│  └─ PipelineMetadata (Value Object)                                        │
│                                                                             │
│  Workspace Aggregate Root: Workspace                                       │
│  ├─ WorkspaceConfig (Entity)                                               │
│  └─ TemplateManager (Entity)                                               │
│                                                                             │
│  Content Aggregate Root: Template                                          │
│  ├─ GeneratedContent (Entity)                                              │
│  └─ ValidationResult (Value Object)                                        │
│                                                                             │
│  Execution Aggregate Root: ExecutionContext                                │
│  ├─ LLMProvider (Entity)                                                    │
│  ├─ CacheEntry (Entity)                                                    │
│  └─ TokenUsage (Value Object)                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cross-Domain Communication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Cross-Domain Communication                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Pipeline Domain → Execution Domain:                                        │
│  • LLM requests during step execution                                       │
│  • Context creation and management                                          │
│  • Token usage tracking                                                    │
│                                                                             │
│  Pipeline Domain → Storage Domain:                                         │
│  • Pipeline run state persistence                                          │
│  • Event stream storage                                                    │
│  • Template storage                                                        │
│                                                                             │
│  Workspace Domain → Storage Domain:                                       │
│  • Workspace-isolated data access                                          │
│  • Configuration persistence                                               │
│  • Template resolution                                                     │
│                                                                             │
│  Content Domain → Storage Domain:                                          │
│  • Template and style storage                                              │
│  • Generated content persistence                                           │
│  • Validation result storage                                               │
│                                                                             │
│  Execution Domain → Storage Domain:                                        │
│  • Cache storage and retrieval                                             │
│  • Token usage analytics                                                   │
│  • Provider health metrics                                                 │
│                                                                             │
│  Event Bus Integration:                                                    │
│  • Domain events published by all domains                                  │
│  • Cross-domain event handlers                                              │
│  • Event sourcing for audit trail                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Domain Events

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Domain Events                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Pipeline Events:                                                          │
│  • PipelineExecutionStarted                                               │
│  • StepExecutionCompleted                                                 │
│  • PipelineExecutionCompleted                                             │
│  • PipelineExecutionFailed                                                 │
│                                                                             │
│  Workspace Events:                                                         │
│  • WorkspaceCreated                                                        │
│  • WorkspaceActivated                                                      │
│  • WorkspaceDeleted                                                        │
│                                                                             │
│  Content Events:                                                           │
│  • TemplateCreated                                                         │
│  • ContentGenerated                                                        │
│  • TemplateValidated                                                       │
│                                                                             │
│  Execution Events:                                                         │
│  • LLMRequestStarted                                                      │
│  • LLMResponseReceived                                                    │
│  • CacheHit                                                                │
│  • TokensConsumed                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

This domain model diagram provides a comprehensive view of WriteIt's domain-driven design architecture, showing entities, value objects, relationships, and cross-domain communication patterns.