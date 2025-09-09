# REST API Reference

WriteIt's REST API provides programmatic access to pipeline management, step execution, and artifact retrieval. All endpoints follow OpenAPI 3.0 specification.

## 🔗 Base Information

- **Base URL**: `http://localhost:8000` (embedded server)
- **API Version**: `0.1.0`
- **Content Type**: `application/json`
- **Authentication**: None (local embedded server)
- **OpenAPI Spec**: `http://localhost:8000/docs` (when server running)

## 📋 Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/pipeline/start` | Start new pipeline execution |
| GET | `/pipeline/{run_id}/status` | Get pipeline status |
| POST | `/step/{run_id}/execute` | Execute pipeline step |
| POST | `/step/{run_id}/select` | Select response and advance |
| POST | `/step/{run_id}/rewind` | Rewind to previous step |
| POST | `/step/{run_id}/fork` | Create pipeline branch |
| POST | `/pipeline/{run_id}/save` | Export pipeline to YAML |
| GET | `/artifacts/{run_id}` | Get pipeline artifacts |

## 🚀 Pipeline Management

### Start Pipeline
Start a new article generation pipeline from configuration.

```http
POST /pipeline/start
Content-Type: application/json

{
  "pipeline_path": "pipelines/tech-article.yaml",
  "user_inputs": {
    "source_material": "Recent advances in WebAssembly (WASM) are enabling...",
    "target_audience": "technical professionals"
  }
}
```

**Response (201 Created)**:
```json
{
  "pipeline_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_step": {
    "step_name": "angles",
    "description": "Generate multiple article angles",
    "models": ["gpt-4o", "claude-sonnet-4"],
    "template": "Based on this source material: {source_material}..."
  }
}
```

**Error Responses**:
```json
// 400 Bad Request - Invalid input
{
  "error": "validation_error",
  "message": "source_material is required",
  "details": {
    "field": "user_inputs.source_material",
    "constraint": "required"
  }
}

// 404 Not Found - Configuration not found
{
  "error": "config_not_found",
  "message": "Pipeline configuration not found: invalid-pipeline.yaml",
  "details": {
    "pipeline_path": "invalid-pipeline.yaml"
  }
}
```

### Get Pipeline Status
Retrieve current pipeline execution status and progress.

```http
GET /pipeline/550e8400-e29b-41d4-a716-446655440000/status
```

**Response (200 OK)**:
```json
{
  "current_step": "outline",
  "completed_steps": ["angles"],
  "status": "RUNNING",
  "progress_percent": 50,
  "created_at": "2025-09-08T15:30:00Z",
  "last_activity": "2025-09-08T15:32:45Z"
}
```

**Pipeline Status Values**:
- `INITIALIZING` - Pipeline setup in progress
- `RUNNING` - Active step execution
- `PAUSED` - User interrupted, can resume
- `COMPLETED` - All steps finished
- `ERROR` - Failed execution, may be recoverable

## 🔄 Step Execution

### Execute Step
Execute a pipeline step with optional user feedback. Returns WebSocket URL for real-time streaming.

```http
POST /step/550e8400-e29b-41d4-a716-446655440000/execute
Content-Type: application/json

{
  "step_name": "angles",
  "user_feedback": "Focus on performance benefits",
  "regenerate": false
}
```

**Response (202 Accepted)**:
```json
{
  "websocket_url": "ws://localhost:8000/step/550e8400-e29b-41d4-a716-446655440000/stream",
  "models": ["gpt-4o", "claude-sonnet-4"],
  "estimated_time_seconds": 45
}
```

**WebSocket Messages** (see [WebSocket API](websocket-api.md) for details):
```json
// Real-time streaming tokens
{
  "type": "stream_token",
  "model": "gpt-4o",
  "content": "# Three Article Angles for WebAssembly",
  "response_index": 0,
  "timestamp": "2025-09-08T15:33:12Z"
}

// Step completion
{
  "type": "stream_complete",
  "step_name": "angles",
  "total_responses": 2,
  "total_time_seconds": 42.3
}
```

**Error Responses**:
```json
// 409 Conflict - Step already in progress
{
  "error": "step_in_progress",
  "message": "Step 'angles' is already being executed",
  "details": {
    "current_step": "angles",
    "step_status": "RUNNING"
  }
}
```

### Select Response
Select AI response(s) and advance to next step or complete pipeline.

```http
POST /step/550e8400-e29b-41d4-a716-446655440000/select
Content-Type: application/json

{
  "response_ids": ["resp-001"],
  "user_feedback": "Great angle! Make the outline more technical.",
  "merge_instruction": ""
}
```

**Response (200 OK)**:
```json
{
  "merged_output": "# The Performance Revolution\nWebAssembly is transforming...",
  "next_step": {
    "step_name": "outline",
    "description": "Create detailed outline from selected angle",
    "models": ["gpt-4o"],
    "template": "Selected angle: {angles_output}..."
  }
}
```

**Multiple Response Selection**:
```http
POST /step/550e8400-e29b-41d4-a716-446655440000/select
Content-Type: application/json

{
  "response_ids": ["resp-001", "resp-002"],
  "merge_instruction": "Combine the performance focus from response 1 with the enterprise examples from response 2",
  "user_feedback": "Technical depth with real-world examples"
}
```

## 🌳 Branching & History

### Rewind Pipeline
Rewind pipeline to previous step, invalidating subsequent work.

```http
POST /step/550e8400-e29b-41d4-a716-446655440000/rewind
Content-Type: application/json

{
  "target_step": "outline"
}
```

**Response (200 OK)**:
```json
{
  "new_current_step": "outline",
  "invalidated_steps": ["draft", "polish"],
  "rewind_timestamp": "2025-09-08T15:45:30Z"
}
```

### Fork Pipeline
Create alternative branch from current or previous step.

```http
POST /step/550e8400-e29b-41d4-a716-446655440000/fork
Content-Type: application/json

{
  "from_response_id": "resp-002",
  "branch_name": "alternative-angle"
}
```

**Response (201 Created)**:
```json
{
  "new_pipeline_run_id": "7f3e8400-e29b-41d4-a716-446655440001",
  "branch_point": "angles",
  "parent_pipeline_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "branch_name": "alternative-angle"
}
```

## 💾 Persistence & Export

### Save Pipeline
Export complete pipeline run to YAML with full history.

```http
POST /pipeline/550e8400-e29b-41d4-a716-446655440000/save
Content-Type: application/json

{
  "output_path": "exports/my-article.yaml",
  "include_history": true
}
```

**Response (200 OK)**:
```json
{
  "saved_path": "/home/user/.writeit/exports/my-article.yaml",
  "file_size": 15420,
  "export_format": "yaml",
  "export_timestamp": "2025-09-08T16:00:00Z"
}
```

**Exported YAML Structure**:
```yaml
metadata:
  pipeline_run_id: "550e8400-e29b-41d4-a716-446655440000"
  configuration: "tech-article.yaml"
  created_at: "2025-09-08T15:30:00Z"
  completed_at: "2025-09-08T16:00:00Z"
  total_cost: "$0.24"
  
final_article: |
  # The WebAssembly Performance Revolution
  
  When Mozilla first demonstrated WebAssembly...
  [complete polished article content]

pipeline_history:
  angles:
    models_used: ["gpt-4o", "claude-sonnet-4"]
    user_selection: 0
    user_feedback: "Focus on performance benefits"
    responses: [...]
    
  outline:
    models_used: ["gpt-4o"]
    user_selection: 0
    user_feedback: "Great angle! Make the outline more technical."
    responses: [...]
    
  # ... additional steps
```

### Get Artifacts
Retrieve all artifacts (responses, prompts, metadata) for a pipeline run.

```http
GET /artifacts/550e8400-e29b-41d4-a716-446655440000?step_name=angles&include_responses=true
```

**Query Parameters**:
- `step_name` (optional) - Filter artifacts by specific step
- `include_responses` (optional, default: true) - Include full AI responses
- `limit` (optional, default: 100) - Maximum artifacts to return

**Response (200 OK)**:
```json
{
  "pipeline_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_count": 8,
  "artifacts": [
    {
      "artifact_id": "art-001",
      "step_name": "angles",
      "model_name": "gpt-4o",
      "response_index": 0,
      "prompt_used": "Based on this source material: Recent advances...",
      "raw_output": "# Three Article Angles for WebAssembly...",
      "selected_for_next": true,
      "user_feedback": "Focus on performance benefits",
      "timestamp": "2025-09-08T15:33:00Z",
      "tokens_used": 1250,
      "processing_time": 18.5,
      "cost_usd": 0.08
    },
    // ... more artifacts
  ]
}
```

## 🛡️ Error Handling

### Standard Error Format
All errors follow consistent JSON structure:

```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {
    "field": "specific_field",
    "value": "invalid_value",
    "constraint": "validation_rule"
  },
  "timestamp": "2025-09-08T15:45:00Z",
  "request_id": "req-12345"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Request validation failed |
| `config_not_found` | 404 | Pipeline configuration missing |
| `pipeline_not_found` | 404 | Pipeline run doesn't exist |
| `step_in_progress` | 409 | Step already executing |
| `invalid_state_transition` | 409 | Invalid pipeline state change |
| `llm_provider_error` | 502 | AI provider unavailable |
| `storage_error` | 500 | Database operation failed |

### Error Recovery Examples

**Provider Fallback**:
```json
// When primary LLM provider fails
{
  "error": "llm_provider_error",
  "message": "OpenAI API unavailable, falling back to Anthropic",
  "details": {
    "primary_provider": "openai",
    "fallback_provider": "anthropic",
    "retry_count": 1
  }
}
```

**Automatic Retry**:
```json
// Transient storage error with retry
{
  "error": "storage_error",
  "message": "Database temporarily unavailable, retrying...",
  "details": {
    "operation": "store_pipeline_run",
    "retry_count": 2,
    "max_retries": 3,
    "retry_after_seconds": 5
  }
}
```

## 📊 Response Headers

### Standard Headers
All responses include standard headers for debugging and monitoring:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: req-12345
X-Pipeline-Run-ID: 550e8400-e29b-41d4-a716-446655440000
X-Processing-Time-Ms: 1250
X-Rate-Limit-Remaining: 95
X-Rate-Limit-Reset: 2025-09-08T16:00:00Z
```

### Caching Headers
```http
# Static configuration data
Cache-Control: public, max-age=3600
ETag: "config-tech-article-v1"

# Dynamic pipeline state  
Cache-Control: no-cache, no-store
X-Pipeline-State-Version: 15
```

## 🔧 Development & Testing

### API Testing Examples
```python
# Using httpx for async testing
import httpx
import pytest

@pytest.mark.asyncio
async def test_complete_pipeline_workflow():
    """Test complete pipeline from start to export"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Start pipeline
        start_response = await client.post("/pipeline/start", json={
            "pipeline_path": "pipelines/tech-article.yaml",
            "user_inputs": {
                "source_material": "Test content",
                "target_audience": "developers"
            }
        })
        assert start_response.status_code == 201
        run_id = start_response.json()["pipeline_run_id"]
        
        # Execute first step
        execute_response = await client.post(f"/step/{run_id}/execute", json={
            "step_name": "angles"
        })
        assert execute_response.status_code == 202
        
        # Select response (mock)
        select_response = await client.post(f"/step/{run_id}/select", json={
            "response_ids": ["resp-001"],
            "user_feedback": "Good direction"
        })
        assert select_response.status_code == 200
        
        # Export final result
        save_response = await client.post(f"/pipeline/{run_id}/save")
        assert save_response.status_code == 200
```

### curl Examples
```bash
# Start pipeline
curl -X POST http://localhost:8000/pipeline/start \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_path": "pipelines/tech-article.yaml",
    "user_inputs": {
      "source_material": "WebAssembly performance improvements...",
      "target_audience": "technical professionals"
    }
  }'

# Check status
curl http://localhost:8000/pipeline/550e8400-e29b-41d4-a716-446655440000/status

# Execute step
curl -X POST http://localhost:8000/step/550e8400-e29b-41d4-a716-446655440000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "step_name": "angles",
    "user_feedback": "Focus on enterprise use cases"
  }'
```

This API provides complete programmatic access to WriteIt's pipeline functionality while maintaining the simplicity and reliability principles of the overall architecture.