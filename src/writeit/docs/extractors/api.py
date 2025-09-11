"""
API documentation extractor from FastAPI/OpenAPI specifications
"""

import json
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from fastapi import FastAPI, openapi
from fastapi.openapi.utils import get_openapi

from ..models import (
    APIDocumentation,
    APIEndpointDocumentation,
    APIModelDocumentation,
    ParameterDocumentation,
    CodeExample
)


class APIExtractor:
    """Extract API documentation from FastAPI/OpenAPI"""
    
    def extract_api_docs(self, app: FastAPI) -> APIDocumentation:
        """Extract complete API documentation from FastAPI app"""
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        return self._extract_from_openapi_schema(openapi_schema)
    
    def extract_from_openapi_file(self, spec_file: Path) -> APIDocumentation:
        """Extract API documentation from OpenAPI JSON file"""
        with open(spec_file, 'r') as f:
            openapi_schema = json.load(f)
        
        return self._extract_from_openapi_schema(openapi_schema)
    
    def _extract_from_openapi_schema(self, schema: Dict[str, Any]) -> APIDocumentation:
        """Extract documentation from OpenAPI schema"""
        api_docs = APIDocumentation(
            title=schema.get("info", {}).get("title", "API Documentation"),
            description=schema.get("info", {}).get("description", ""),
            version=schema.get("info", {}).get("version", "1.0.0"),
            base_url=schema.get("servers", [{}])[0].get("url", ""),
            endpoints=[],
            models=[]
        )
        
        # Extract endpoints
        paths = schema.get("paths", {})
        for path, methods in paths.items():
            for method, endpoint_data in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                    endpoint_doc = self._extract_endpoint(path, method, endpoint_data)
                    if endpoint_doc:
                        api_docs.endpoints.append(endpoint_doc)
        
        # Extract models (schemas)
        schemas = schema.get("components", {}).get("schemas", {})
        for schema_name, schema_data in schemas.items():
            model_doc = self._extract_model(schema_name, schema_data)
            if model_doc:
                api_docs.models.append(model_doc)
        
        return api_docs
    
    def _extract_endpoint(self, path: str, method: str, endpoint_data: Dict[str, Any]) -> APIEndpointDocumentation:
        """Extract documentation for a single endpoint"""
        endpoint_doc = APIEndpointDocumentation(
            path=path,
            method=method.upper(),
            summary=endpoint_data.get("summary", ""),
            description=endpoint_data.get("description", endpoint_data.get("summary", "")),
            parameters=[],
            status_codes={}
        )
        
        # Extract parameters
        parameters = endpoint_data.get("parameters", [])
        for param in parameters:
            param_doc = self._extract_parameter(param)
            if param_doc:
                endpoint_doc.parameters.append(param_doc)
        
        # Extract request body
        request_body = endpoint_data.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            for content_type, content_data in content.items():
                schema_ref = content_data.get("schema", {}).get("$ref", "")
                endpoint_doc.request_body = {
                    "content_type": content_type,
                    "schema": schema_ref.split("/")[-1] if schema_ref else "Unknown"
                }
        
        # Extract responses
        responses = endpoint_data.get("responses", {})
        for status_code, response_data in responses.items():
            try:
                status_int = int(status_code)
                endpoint_doc.status_codes[status_int] = response_data.get("description", "")
            except ValueError:
                endpoint_doc.status_codes[status_code] = response_data.get("description", "")
        
        # Extract tags
        endpoint_doc.tags = endpoint_data.get("tags", [])
        
        return endpoint_doc
    
    def _extract_parameter(self, param_data: Dict[str, Any]) -> Optional[ParameterDocumentation]:
        """Extract documentation for a parameter"""
        try:
            param_type = param_data.get("schema", {}).get("type", "string")
            if param_data.get("in") == "query":
                param_type = "query"
            elif param_data.get("in") == "path":
                param_type = "path"
            elif param_data.get("in") == "header":
                param_type = "header"
            
            return ParameterDocumentation(
                name=param_data.get("name", ""),
                type_annotation=param_type,
                description=param_data.get("description", ""),
                required=param_data.get("required", False),
                default_value=param_data.get("schema", {}).get("default")
            )
        except Exception:
            return None
    
    def _extract_model(self, name: str, schema_data: Dict[str, Any]) -> APIModelDocumentation:
        """Extract documentation for a model (schema)"""
        model_doc = APIModelDocumentation(
            name=name,
            description=schema_data.get("description", f"Model: {name}"),
            fields={}
        )
        
        # Extract properties
        properties = schema_data.get("properties", {})
        for field_name, field_data in properties.items():
            field_type = field_data.get("type", "string")
            field_desc = field_data.get("description", f"Field: {field_name}")
            
            # Handle enum values
            if "enum" in field_data:
                field_desc += f" (Values: {field_data['enum']})"
            
            # Handle array types
            if field_type == "array":
                items_type = field_data.get("items", {}).get("type", "unknown")
                field_type = f"Array[{items_type}]"
            
            model_doc.fields[field_name] = field_desc
        
        # Extract example
        if "example" in schema_data:
            model_doc.examples.append(schema_data["example"])
        
        return model_doc
    
    def extract_websocket_docs(self, app: FastAPI) -> List[APIEndpointDocumentation]:
        """Extract WebSocket endpoint documentation"""
        websocket_endpoints = []
        
        for route in app.routes:
            if hasattr(route, "websocket_endpoint"):
                endpoint_doc = APIEndpointDocumentation(
                    path=route.path,
                    method="WebSocket",
                    summary="WebSocket endpoint",
                    description=f"WebSocket endpoint at {route.path}",
                    parameters=[],
                    status_codes={}
                )
                websocket_endpoints.append(endpoint_doc)
        
        return websocket_endpoints
    
    def generate_examples(self, endpoint: APIEndpointDocumentation) -> List[CodeExample]:
        """Generate usage examples for an endpoint"""
        examples = []
        
        # Generate HTTP request example
        http_example = self._generate_http_example(endpoint)
        if http_example:
            examples.append(http_example)
        
        # Generate Python client example
        python_example = self._generate_python_example(endpoint)
        if python_example:
            examples.append(python_example)
        
        return examples
    
    def _generate_http_example(self, endpoint: APIEndpointDocumentation) -> Optional[CodeExample]:
        """Generate HTTP request example"""
        try:
            method = endpoint.method
            url = f"http://localhost:8000{endpoint.path}"
            
            example_lines = [f"{method} {url} HTTP/1.1"]
            example_lines.append("Host: localhost:8000")
            example_lines.append("Content-Type: application/json")
            example_lines.append("")
            
            if endpoint.request_body:
                example_lines.append(json.dumps({"key": "value"}, indent=2))
            
            return CodeExample(
                code="\n".join(example_lines),
                description=f"HTTP {method} request to {endpoint.path}",
                language="http"
            )
        except Exception:
            return None
    
    def _generate_python_example(self, endpoint: APIEndpointDocumentation) -> Optional[CodeExample]:
        """Generate Python client example"""
        try:
            method = endpoint.method.lower()
            url = f"http://localhost:8000{endpoint.path}"
            
            example_lines = [
                "import requests",
                "",
                f"url = '{url}'"
            ]
            
            if method == "get":
                example_lines.append("response = requests.get(url)")
            elif method == "post":
                example_lines.append("data = {'key': 'value'}")
                example_lines.append("response = requests.post(url, json=data)")
            elif method == "put":
                example_lines.append("data = {'key': 'value'}")
                example_lines.append("response = requests.put(url, json=data)")
            elif method == "delete":
                example_lines.append("response = requests.delete(url)")
            
            example_lines.extend([
                "",
                "if response.status_code == 200:",
                "    print(response.json())"
            ])
            
            return CodeExample(
                code="\n".join(example_lines),
                description=f"Python client example for {endpoint.method} {endpoint.path}",
                language="python"
            )
        except Exception:
            return None