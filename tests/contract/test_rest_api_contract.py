"""
Contract tests for REST API endpoints.

Ensures that all REST API endpoints behave according to their contracts,
including proper HTTP status codes, response formats, and error handling.
"""

import pytest
import json
import asyncio
from httpx import AsyncClient, ASGITransport
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import shutil

from writeit.infrastructure.web.app import create_app
from writeit.shared.dependencies.container import Container
from writeit.shared.events.bus import EventBus
from writeit.workspace.workspace import Workspace


@pytest.fixture
def temp_home() -> Path:
    """Create temporary home directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
async def test_app(temp_home: Path):
    """Create test FastAPI application with temporary workspace."""
    # Initialize workspace
    workspace = Workspace(temp_home / ".writeit")
    workspace.initialize()
    
    # Create app with test container
    container = Container()
    event_bus = EventBus()
    app = create_app(container=container, event_bus=event_bus, debug=True)
    
    # Set workspace for testing
    app.state.workspace = temp_home / ".writeit"
    
    yield app


@pytest.fixture
async def client(test_app):
    """Create test HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), 
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def test_workspace(test_app, temp_home: Path):
    """Create test workspace."""
    workspace_data = {
        "name": "test-workspace",
        "display_name": "Test Workspace",
        "description": "Workspace for API contract testing",
        "configuration": {
            "default_model": "gpt-4o-mini",
            "max_tokens": 1000
        }
    }
    
    async with AsyncClient(
        transport=ASGITransport(app=test_app), 
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/workspaces", json=workspace_data)
        assert response.status_code == 201
        
    return workspace_data


@pytest.fixture
async def test_pipeline_template(test_app, test_workspace):
    """Create test pipeline template."""
    template_data = {
        "metadata": {
            "name": "test-pipeline",
            "description": "Test pipeline for contract testing",
            "version": "1.0.0"
        },
        "defaults": {
            "model": "gpt-4o-mini"
        },
        "inputs": {
            "topic": {
                "type": "text",
                "label": "Topic",
                "required": True
            }
        },
        "steps": {
            "outline": {
                "name": "Create Outline",
                "type": "llm_generate",
                "prompt_template": "Create an outline for {{ inputs.topic }}",
                "model_preference": ["gpt-4o-mini"]
            }
        }
    }
    
    async with AsyncClient(
        transport=ASGITransport(app=test_app), 
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/pipelines/templates", json=template_data)
        assert response.status_code == 201
        
    return template_data


class TestWorkspaceEndpointsContract:
    """Contract tests for workspace endpoints."""

    async def test_create_workspace_contract(self, client):
        """Test workspace creation contract."""
        workspace_data = {
            "name": "contract-test-workspace",
            "display_name": "Contract Test Workspace",
            "description": "Testing workspace contract",
            "configuration": {
                "default_model": "gpt-4o-mini",
                "max_tokens": 1000
            }
        }
        
        response = await client.post("/api/v1/workspaces", json=workspace_data)
        
        # Contract: 201 Created
        assert response.status_code == 201
        
        # Contract: Response structure
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "display_name" in data
        assert "description" in data
        assert "configuration" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Contract: Data integrity
        assert data["name"] == workspace_data["name"]
        assert data["display_name"] == workspace_data["display_name"]
        assert data["description"] == workspace_data["description"]
        assert data["configuration"] == workspace_data["configuration"]

    async def test_list_workspaces_contract(self, client, test_workspace):
        """Test workspace listing contract."""
        response = await client.get("/api/v1/workspaces")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "workspaces" in data
        assert "pagination" in data
        assert "total_count" in data
        
        # Contract: Pagination structure
        pagination = data["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_previous" in pagination

    async def test_get_workspace_contract(self, client, test_workspace):
        """Test get workspace details contract."""
        response = await client.get(f"/api/v1/workspaces/{test_workspace['name']}")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "display_name" in data
        assert "description" in data
        assert "configuration" in data
        assert "statistics" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_update_workspace_contract(self, client, test_workspace):
        """Test workspace update contract."""
        update_data = {
            "display_name": "Updated Contract Workspace",
            "description": "Updated description",
            "configuration": {
                "default_model": "gpt-4o",
                "max_tokens": 2000
            }
        }
        
        response = await client.put(
            f"/api/v1/workspaces/{test_workspace['name']}", 
            json=update_data
        )
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert data["display_name"] == update_data["display_name"]
        assert data["description"] == update_data["description"]
        assert data["configuration"] == update_data["configuration"]

    async def test_delete_workspace_contract(self, client):
        """Test workspace deletion contract."""
        # Create workspace to delete
        workspace_data = {
            "name": "delete-test-workspace",
            "display_name": "Delete Test Workspace",
            "description": "Workspace for deletion test"
        }
        
        create_response = await client.post("/api/v1/workspaces", json=workspace_data)
        assert create_response.status_code == 201
        
        # Delete workspace
        delete_response = await client.delete(f"/api/v1/workspaces/{workspace_data['name']}")
        
        # Contract: 204 No Content
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(f"/api/v1/workspaces/{workspace_data['name']}")
        assert get_response.status_code == 404

    async def test_workspace_error_handling_contract(self, client):
        """Test workspace error handling contract."""
        # Test 404 for nonexistent workspace
        response = await client.get("/api/v1/workspaces/nonexistent")
        assert response.status_code == 404
        
        # Test 400 for invalid workspace data
        invalid_data = {"name": "", "display_name": "Invalid"}  # Empty name
        response = await client.post("/api/v1/workspaces", json=invalid_data)
        assert response.status_code == 422  # FastAPI validation error


class TestPipelineEndpointsContract:
    """Contract tests for pipeline endpoints."""

    async def test_create_pipeline_template_contract(self, client, test_workspace):
        """Test pipeline template creation contract."""
        template_data = {
            "metadata": {
                "name": "contract-test-pipeline",
                "description": "Contract test pipeline",
                "version": "1.0.0"
            },
            "defaults": {
                "model": "gpt-4o-mini"
            },
            "inputs": {
                "topic": {
                    "type": "text",
                    "label": "Topic",
                    "required": True
                }
            },
            "steps": {
                "outline": {
                    "name": "Create Outline",
                    "type": "llm_generate",
                    "prompt_template": "Create an outline for {{ inputs.topic }}",
                    "model_preference": ["gpt-4o-mini"]
                }
            }
        }
        
        response = await client.post("/api/v1/pipelines/templates", json=template_data)
        
        # Contract: 201 Created
        assert response.status_code == 201
        
        # Contract: Response structure
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "version" in data
        assert "workspace_name" in data
        assert "metadata" in data
        assert "defaults" in data
        assert "inputs" in data
        assert "steps" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_list_pipeline_templates_contract(self, client, test_pipeline_template):
        """Test pipeline template listing contract."""
        response = await client.get("/api/v1/pipelines/templates")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "templates" in data
        assert "pagination" in data
        assert "total_count" in data
        
        # Contract: Template structure
        templates = data["templates"]
        if templates:  # If there are templates
            template = templates[0]
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "version" in template
            assert "workspace_name" in template

    async def test_execute_pipeline_contract(self, client, test_pipeline_template):
        """Test pipeline execution contract."""
        execution_data = {
            "template_id": "contract-test-pipeline",
            "workspace_name": "test-workspace",
            "inputs": {
                "topic": "Artificial Intelligence"
            },
            "execution_mode": "sync"
        }
        
        response = await client.post("/api/v1/pipelines/execute", json=execution_data)
        
        # Contract: 202 Accepted (async execution)
        assert response.status_code == 202
        
        # Contract: Response structure
        data = response.json()
        assert "run_id" in data
        assert "status" in data
        assert "pipeline_id" in data
        assert "workspace_name" in data
        assert "inputs" in data
        assert "created_at" in data

    async def test_list_pipeline_runs_contract(self, client, test_pipeline_template):
        """Test pipeline run listing contract."""
        response = await client.get("/api/v1/pipelines/runs")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "runs" in data
        assert "pagination" in data
        assert "total_count" in data

    async def test_get_pipeline_run_contract(self, client, test_pipeline_template):
        """Test get pipeline run details contract."""
        # First execute a pipeline to get a run
        execution_data = {
            "template_id": "contract-test-pipeline",
            "workspace_name": "test-workspace",
            "inputs": {"topic": "Test Topic"},
            "execution_mode": "sync"
        }
        
        execute_response = await client.post("/api/v1/pipelines/execute", json=execution_data)
        assert execute_response.status_code == 202
        
        run_data = execute_response.json()
        run_id = run_data["run_id"]
        
        # Get run details
        response = await client.get(f"/api/v1/pipelines/runs/{run_id}")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "id" in data
        assert "pipeline_id" in data
        assert "status" in data
        assert "workspace_name" in data
        assert "inputs" in data
        assert "outputs" in data
        assert "created_at" in data
        assert "steps" in data

    async def test_pipeline_error_handling_contract(self, client):
        """Test pipeline error handling contract."""
        # Test 404 for nonexistent pipeline
        response = await client.get("/api/v1/pipelines/templates/nonexistent")
        assert response.status_code == 404
        
        # Test 422 for invalid pipeline data
        invalid_template = {"metadata": {"name": ""}}  # Missing required fields
        response = await client.post("/api/v1/pipelines/templates", json=invalid_template)
        assert response.status_code == 422

    async def test_pipeline_execution_with_invalid_inputs_contract(self, client, test_pipeline_template):
        """Test pipeline execution with invalid inputs contract."""
        execution_data = {
            "template_id": "contract-test-pipeline",
            "workspace_name": "test-workspace",
            "inputs": {},  # Missing required 'topic' input
            "execution_mode": "sync"
        }
        
        response = await client.post("/api/v1/pipelines/execute", json=execution_data)
        
        # Contract: 400 Bad Request for missing required inputs
        assert response.status_code == 400


class TestContentEndpointsContract:
    """Contract tests for content endpoints."""

    async def test_create_content_contract(self, client, test_workspace):
        """Test content creation contract."""
        content_data = {
            "workspace_name": "test-workspace",
            "content_type": "template",
            "name": "contract-test-template",
            "content": "# Test Template\nThis is a test template.",
            "metadata": {
                "description": "Contract test template",
                "tags": ["test", "contract"]
            }
        }
        
        response = await client.post("/api/v1/content", json=content_data)
        
        # Contract: 201 Created
        assert response.status_code == 201
        
        # Contract: Response structure
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "content_type" in data
        assert "workspace_name" in data
        assert "content" in data
        assert "metadata" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_list_content_contract(self, client, test_workspace):
        """Test content listing contract."""
        response = await client.get("/api/v1/content")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "content_items" in data
        assert "pagination" in data
        assert "total_count" in data

    async def test_content_error_handling_contract(self, client):
        """Test content error handling contract."""
        # Test 422 for invalid content data
        invalid_content = {"workspace_name": "", "content_type": "invalid"}
        response = await client.post("/api/v1/content", json=invalid_content)
        assert response.status_code == 422


class TestHealthEndpointsContract:
    """Contract tests for health endpoints."""

    async def test_health_check_contract(self, client):
        """Test basic health check contract."""
        response = await client.get("/api/v1/health")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        
        # Contract: Status values
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    async def test_detailed_health_check_contract(self, client):
        """Test detailed health check contract."""
        response = await client.get("/api/v1/health/detailed")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Response structure
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "dependencies" in data
        assert "metrics" in data
        
        # Contract: Dependencies structure
        dependencies = data["dependencies"]
        assert isinstance(dependencies, dict)
        
        # Contract: Metrics structure
        metrics = data["metrics"]
        assert isinstance(metrics, dict)


class TestAPIResponseFormatsContract:
    """Contract tests for API response formats."""

    async def test_error_response_format_contract(self, client):
        """Test error response format contract."""
        # Trigger 404 error
        response = await client.get("/api/v1/workspaces/nonexistent")
        
        # Contract: 404 status
        assert response.status_code == 404
        
        # Contract: Error response structure
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
        
        error = data["error"]
        assert "code" in error
        assert "type" in error

    async def test_validation_error_format_contract(self, client):
        """Test validation error format contract."""
        # Trigger validation error
        invalid_data = {"name": ""}  # Invalid workspace name
        response = await client.post("/api/v1/workspaces", json=invalid_data)
        
        # Contract: 422 status
        assert response.status_code == 422
        
        # Contract: Validation error structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    async def test_pagination_format_contract(self, client, test_workspace):
        """Test pagination response format contract."""
        response = await client.get("/api/v1/workspaces?page=1&page_size=10")
        
        # Contract: 200 OK
        assert response.status_code == 200
        
        # Contract: Pagination structure
        data = response.json()
        pagination = data["pagination"]
        
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total_pages" in pagination
        assert "total_count" in pagination
        assert "has_next" in pagination
        assert "has_previous" in pagination
        
        # Contract: Pagination values
        assert pagination["page"] == 1
        assert pagination["page_size"] == 10
        assert isinstance(pagination["has_next"], bool)
        assert isinstance(pagination["has_previous"], bool)

    async def test_api_version_header_contract(self, client):
        """Test API version header contract."""
        response = await client.get("/api/v1/health")
        
        # Contract: API version header
        assert "api-version" in response.headers
        assert response.headers["api-version"] == "1.0.0"

    async def test_cors_headers_contract(self, client):
        """Test CORS headers contract."""
        # Simple preflight request simulation
        response = await client.options("/api/v1/health")
        
        # Contract: CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


class TestRateLimitingContract:
    """Contract tests for rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_rate_limiting_headers_contract(self, client):
        """Test rate limiting headers contract."""
        response = await client.get("/api/v1/health")
        
        # Contract: Rate limiting headers should be present
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers
        
        # Contract: Header values should be valid
        limit = int(response.headers["x-ratelimit-limit"])
        remaining = int(response.headers["x-ratelimit-remaining"])
        reset = int(response.headers["x-ratelimit-reset"])
        
        assert limit > 0
        assert remaining >= 0
        assert reset > 0


class TestAPIAuthenticationContract:
    """Contract tests for API authentication (when implemented)."""

    @pytest.mark.asyncio
    async def test_unauthorized_access_contract(self, client):
        """Test unauthorized access contract."""
        # This test assumes authentication might be added in future
        # For now, endpoints should be public
        
        response = await client.get("/api/v1/health")
        
        # Contract: Currently public endpoints return 200
        assert response.status_code == 200

    @pytest.mark.asyncio  
    async def test_authentication_headers_contract(self, client):
        """Test authentication headers contract."""
        # Test with invalid auth header (if auth is implemented)
        headers = {"Authorization": "Bearer invalid-token"}
        
        response = await client.get("/api/v1/health", headers=headers)
        
        # Contract: Currently auth is not enforced, so should return 200
        # This test will need updating when auth is implemented
        assert response.status_code == 200