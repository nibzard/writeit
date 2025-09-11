# WriteIt API Documentation

## Overview

WriteIt provides a comprehensive REST API and WebSocket interface for pipeline execution, workspace management, and real-time communication. The API is built with FastAPI and supports both synchronous and asynchronous operations.

**Base URL**: `http://localhost:8000`  
**WebSocket URL**: `ws://localhost:8000`

## Authentication

Currently, WriteIt operates without authentication in development mode. All endpoints are publicly accessible when running locally.

## Data Models

### Pipeline

A pipeline defines a multi-step workflow for content generation.

```json
{
  "id": "string",
  "name": "string", 
  "description": "string",
  "version": "string",
  "metadata": {},
  "defaults": {},
  "inputs": {
    "input_key": {
      "type": "text|choice|number|boolean",
      "label": "string",
      "required": boolean,
      "default": "any",
      "placeholder": "string",
      "help": "string",
      "options": [{"label": "string", "value": "string"}]
    }
  },
  "steps": [
    {
      "key": "string",
      "name": "string", 
      "description": "string",
      "type": "llm_generate|user_input|transform",
      "model_preference": ["string"],
      "validation": {},
      "ui": {}
    }
  ]
}
```

### Pipeline Run

A pipeline run represents a single execution of a pipeline with specific inputs.

```json
{
  "id": "string",
  "pipeline_id": "string",
  "status": "created|running|paused|completed|failed|cancelled",
  "inputs": {},
  "outputs": {},
  "created_at": "2025-01-15T10:30:00Z",
  "started_at": "2025-01-15T10:30:05Z",
  "completed_at": "2025-01-15T10:32:15Z",
  "error": "string|null",
  "steps": [
    {
      "step_key": "string",
      "status": "pending|running|waiting_input|completed|failed|skipped",
      "started_at": "2025-01-15T10:30:05Z",
      "completed_at": "2025-01-15T10:31:20Z", 
      "responses": ["string"],
      "selected_response": "string|null",
      "user_feedback": "string",
      "tokens_used": {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
      },
      "execution_time": 0.0,
      "error": "string|null"
    }
  ]
}
```

## REST API Endpoints

### Health Check

#### GET /health
Check API server health status.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

### Pipeline Management

#### POST /api/pipelines
Create a new pipeline from a YAML configuration file.

**Request Body**
```json
{
  "pipeline_path": "/path/to/pipeline.yaml",
  "workspace_name": "default"
}
```

**Response** 
```json
{
  "id": "pipeline_123",
  "name": "Article Generator",
  "description": "Generates structured articles",
  "version": "1.0.0",
  "metadata": {},
  "defaults": {},
  "inputs": {},
  "steps": []
}
```

**Error Responses**
- `400 Bad Request`: Invalid pipeline file or configuration
- `404 Not Found`: Pipeline file not found
- `500 Internal Server Error`: Server error during pipeline creation

#### GET /api/pipelines/{pipeline_id}
Retrieve pipeline configuration by ID.

**Path Parameters**
- `pipeline_id` (string): Unique pipeline identifier

**Response**
```json
{
  "id": "pipeline_123",
  "name": "Article Generator",
  "description": "Generates structured articles",
  // ... full pipeline configuration
}
```

**Error Responses**
- `404 Not Found`: Pipeline not found

---

### Pipeline Execution

#### POST /api/runs  
Create a new pipeline run.

**Request Body**
```json
{
  "pipeline_id": "pipeline_123",
  "inputs": {
    "topic": "Artificial Intelligence", 
    "style": "formal"
  },
  "workspace_name": "default"
}
```

**Response**
```json
{
  "id": "run_456",
  "pipeline_id": "pipeline_123",
  "status": "created",
  "inputs": {
    "topic": "Artificial Intelligence",
    "style": "formal"
  },
  "outputs": {},
  "created_at": "2025-01-15T10:30:00Z",
  // ... full run configuration
}
```

**Error Responses**
- `400 Bad Request`: Invalid inputs or missing required fields
- `404 Not Found`: Pipeline not found
- `500 Internal Server Error`: Server error during run creation

#### POST /api/runs/{run_id}/execute
Execute a pipeline run.

**Path Parameters**
- `run_id` (string): Unique run identifier

**Query Parameters**
- `workspace_name` (string, optional): Workspace name (default: "default")

**Response**
```json
{
  "id": "run_456",
  "pipeline_id": "pipeline_123", 
  "status": "completed",
  "inputs": {},
  "outputs": {
    "outline": "I. Introduction\nII. Main Points\nIII. Conclusion",
    "content": "# Artificial Intelligence\n\nAI is transforming..."
  },
  "completed_at": "2025-01-15T10:32:15Z",
  "steps": [
    {
      "step_key": "outline",
      "status": "completed",
      "responses": ["I. Introduction\nII. Main Points\nIII. Conclusion"],
      "selected_response": "I. Introduction\nII. Main Points\nIII. Conclusion",
      "tokens_used": {
        "prompt_tokens": 45,
        "completion_tokens": 120,
        "total_tokens": 165
      },
      "execution_time": 3.2
    }
    // ... additional steps
  ]
}
```

**Error Responses**
- `404 Not Found`: Run or pipeline not found
- `500 Internal Server Error`: Execution error

#### GET /api/runs/{run_id}
Get pipeline run status and results.

**Path Parameters**
- `run_id` (string): Unique run identifier

**Query Parameters**
- `workspace_name` (string, optional): Workspace name (default: "default")

**Response**
```json
{
  "id": "run_456",
  "pipeline_id": "pipeline_123",
  "status": "running",
  // ... full run details
}
```

#### GET /api/workspaces/{workspace_name}/runs
List pipeline runs for a workspace.

**Path Parameters**
- `workspace_name` (string): Workspace name

**Query Parameters**
- `limit` (integer, optional): Maximum number of runs to return (default: 50)

**Response**
```json
[
  {
    "id": "run_456",
    "pipeline_id": "pipeline_123",
    "status": "completed",
    "created_at": "2025-01-15T10:30:00Z"
    // ... run summary
  }
  // ... additional runs
]
```

---

## WebSocket API

### Real-time Pipeline Execution

#### WS /ws/{run_id}
Establish WebSocket connection for real-time pipeline execution updates.

**Connection**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/run_456');
```

#### Incoming Messages

**Connection Confirmation**
```json
{
  "type": "connected",
  "connection_id": "conn_789",
  "run_id": "run_456", 
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Progress Updates**
```json
{
  "type": "progress",
  "event": "step_start|step_complete",
  "data": {
    "step_index": 0,
    "step_key": "outline",
    "step_name": "Create Outline",
    "total_steps": 2
  },
  "timestamp": "2025-01-15T10:30:05Z"
}
```

**Response Streaming**
```json
{
  "type": "response", 
  "response_type": "response",
  "content": "I. Introduction\nAI is a rapidly evolving field...",
  "timestamp": "2025-01-15T10:30:10Z"
}
```

**Completion Notification**
```json
{
  "type": "completed",
  "run": {
    "id": "run_456",
    "status": "completed",
    // ... complete run results
  },
  "timestamp": "2025-01-15T10:32:15Z"
}
```

**Error Notification**
```json
{
  "type": "error",
  "error": "LLM API rate limit exceeded",
  "timestamp": "2025-01-15T10:30:30Z"
}
```

#### Outgoing Messages

**User Selection**
```json
{
  "type": "user_selection",
  "step_key": "outline",
  "selected_response": "I. Introduction\nII. Core Concepts\nIII. Applications"
}
```

**User Feedback**
```json
{
  "type": "user_feedback", 
  "step_key": "outline",
  "feedback": "Please make the outline more detailed"
}
```

**Run Control**
```json
{
  "type": "pause_run"
}
```

```json
{
  "type": "resume_run"
}
```

---

## Error Handling

### Standard Error Response

All API errors follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "PIPELINE_NOT_FOUND", 
  "suggestion": "Check that the pipeline ID is correct and the pipeline exists"
}
```

### Common Error Codes

- `PIPELINE_NOT_FOUND`: Pipeline ID does not exist
- `RUN_NOT_FOUND`: Run ID does not exist  
- `WORKSPACE_NOT_FOUND`: Workspace does not exist
- `INVALID_INPUT`: Input validation failed
- `EXECUTION_FAILED`: Pipeline execution error
- `LLM_API_ERROR`: LLM service error
- `STORAGE_ERROR`: Database/storage error

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

Currently, WriteIt does not implement rate limiting. In production deployments, consider implementing:

- API key-based rate limiting
- Per-workspace execution limits  
- LLM token usage quotas
- Concurrent execution limits

---

## Caching

WriteIt implements intelligent LLM response caching to optimize performance and reduce costs:

### Cache Behavior

- **Cache Key**: Based on prompt, model, and execution context
- **TTL**: 24 hours by default (configurable)
- **Scope**: Workspace-isolated caching
- **Storage**: Memory + persistent LMDB storage

### Cache Headers

Responses include cache information in headers:

```
X-Cache: HIT|MISS
X-Cache-Key: abc123def456
X-Cache-Age: 3600
```

### Cache Management

Use these endpoints to manage caching:

```bash
# Get cache statistics
GET /api/cache/stats?workspace=default

# Clear cache for workspace
DELETE /api/cache?workspace=default

# Invalidate specific cache entry
DELETE /api/cache/{cache_key}
```

---

## Client Libraries

### Python Client

```python
from writeit.server import PipelineClient

async def run_pipeline():
    client = PipelineClient()
    
    result = await client.run_pipeline(
        pipeline_path=Path("article.yaml"),
        inputs={"topic": "AI Ethics", "style": "academic"},
        progress_callback=lambda event, data: print(f"Progress: {event}"),
        response_callback=lambda type, content: print(f"Response: {content}")
    )
    
    print(f"Pipeline completed: {result['status']}")
```

### JavaScript Client

```javascript
class WriteItClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  async createPipeline(pipelinePath, workspaceName = 'default') {
    const response = await fetch(`${this.baseUrl}/api/pipelines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        pipeline_path: pipelinePath, 
        workspace_name: workspaceName 
      })
    });
    return response.json();
  }
  
  connectWebSocket(runId) {
    const ws = new WebSocket(`ws://localhost:8000/ws/${runId}`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Received:', message);
    };
    
    return ws;
  }
}
```

---

## Development and Testing

### Starting the Server

```bash
# Development mode with auto-reload
uv run uvicorn writeit.server.app:app --reload --port 8000

# Production mode
uv run uvicorn writeit.server.app:app --host 0.0.0.0 --port 8000
```

### Testing the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Create a pipeline
curl -X POST http://localhost:8000/api/pipelines \
  -H "Content-Type: application/json" \
  -d '{"pipeline_path": "examples/article.yaml", "workspace_name": "default"}'

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/run_123
```

### API Documentation

When the server is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json