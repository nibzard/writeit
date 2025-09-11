# ABOUTME: Client library for communicating with WriteIt FastAPI server
# ABOUTME: Provides async interface for TUI to interact with pipeline execution backend

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import websockets
import aiohttp
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Configuration for WriteIt server connection."""

    host: str = "127.0.0.1"
    port: int = 8000
    protocol: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def ws_base_url(self) -> str:
        ws_protocol = "wss" if self.protocol == "https" else "ws"
        return f"{ws_protocol}://{self.host}:{self.port}"


class WriteItClient:
    """Client for communicating with WriteIt FastAPI server."""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure we have an active session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def health_check(self) -> bool:
        """Check if the server is healthy."""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.config.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def create_pipeline(
        self, pipeline_path: Path, workspace_name: str = "default"
    ) -> Dict[str, Any]:
        """Create a pipeline from a file."""
        await self._ensure_session()

        data = {"pipeline_path": str(pipeline_path), "workspace_name": workspace_name}

        async with self.session.post(
            f"{self.config.base_url}/api/pipelines", json=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Get pipeline configuration."""
        await self._ensure_session()

        async with self.session.get(
            f"{self.config.base_url}/api/pipelines/{pipeline_id}"
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def create_run(
        self, pipeline_id: str, inputs: Dict[str, Any], workspace_name: str = "default"
    ) -> Dict[str, Any]:
        """Create a new pipeline run."""
        await self._ensure_session()

        data = {
            "pipeline_id": pipeline_id,
            "inputs": inputs,
            "workspace_name": workspace_name,
        }

        async with self.session.post(
            f"{self.config.base_url}/api/runs", json=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def execute_run(
        self, run_id: str, workspace_name: str = "default"
    ) -> Dict[str, Any]:
        """Execute a pipeline run."""
        await self._ensure_session()

        params = {"workspace_name": workspace_name}

        async with self.session.post(
            f"{self.config.base_url}/api/runs/{run_id}/execute", params=params
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_run(
        self, run_id: str, workspace_name: str = "default"
    ) -> Dict[str, Any]:
        """Get pipeline run status."""
        await self._ensure_session()

        params = {"workspace_name": workspace_name}

        async with self.session.get(
            f"{self.config.base_url}/api/runs/{run_id}", params=params
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def list_runs(
        self, workspace_name: str = "default", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List pipeline runs for a workspace."""
        await self._ensure_session()

        params = {"limit": limit}

        async with self.session.get(
            f"{self.config.base_url}/api/workspaces/{workspace_name}/runs",
            params=params,
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def stream_run_execution(
        self,
        run_id: str,
        message_callback: Callable[[Dict[str, Any]], None],
        user_message_handler: Optional[Callable[[str], Dict[str, Any]]] = None,
    ) -> None:
        """Stream pipeline run execution via WebSocket."""
        ws_url = f"{self.config.ws_base_url}/ws/{run_id}"

        async with websockets.connect(ws_url) as websocket:
            # Handle incoming messages
            async def handle_messages():
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        message_callback(data)
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode WebSocket message: {e}")
                    except Exception as e:
                        print(f"Error handling WebSocket message: {e}")

            # Handle outgoing user messages
            async def handle_user_input():
                while True:
                    if user_message_handler:
                        try:
                            user_message = user_message_handler(run_id)
                            if user_message:
                                await websocket.send(json.dumps(user_message))
                        except Exception as e:
                            print(f"Error sending user message: {e}")
                    await asyncio.sleep(0.1)

            # Run both handlers concurrently
            await asyncio.gather(handle_messages(), handle_user_input())


class PipelineClient:
    """High-level client for pipeline operations."""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.client = WriteItClient(config)
        self.workspace_name = "default"

    async def run_pipeline(
        self,
        pipeline_path: Path,
        inputs: Dict[str, Any],
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        response_callback: Optional[Callable[[str, str], None]] = None,
        workspace_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a complete pipeline with callbacks."""
        workspace = workspace_name or self.workspace_name

        async with self.client:
            # Check server health
            if not await self.client.health_check():
                raise ConnectionError("WriteIt server is not available")

            # Create pipeline
            pipeline_resp = await self.client.create_pipeline(pipeline_path, workspace)
            pipeline_id = pipeline_resp["id"]

            # Create run
            run_resp = await self.client.create_run(pipeline_id, inputs, workspace)
            run_id = run_resp["id"]

            # Set up WebSocket streaming
            execution_complete = asyncio.Event()
            final_result = None

            def handle_ws_message(message: Dict[str, Any]):
                nonlocal final_result

                message_type = message.get("type")

                if message_type == "progress" and progress_callback:
                    event_type = message.get("data", {}).get("event")
                    data = message.get("data", {})
                    progress_callback(event_type, data)

                elif message_type == "response" and response_callback:
                    response_type = message.get("response_type")
                    content = message.get("content", "")
                    response_callback(response_type, content)

                elif message_type == "completed":
                    final_result = message.get("run")
                    execution_complete.set()

                elif message_type == "error":
                    error_msg = message.get("error", "Unknown error")
                    raise RuntimeError(f"Pipeline execution failed: {error_msg}")

            # Start execution and streaming concurrently
            async def start_execution():
                await self.client.execute_run(run_id, workspace)

            async def start_streaming():
                await self.client.stream_run_execution(run_id, handle_ws_message)

            # Run both tasks
            await asyncio.gather(start_execution(), start_streaming())

            # Wait for completion
            await execution_complete.wait()

            return final_result or run_resp

    async def get_pipeline_info(self, pipeline_path: Path) -> Dict[str, Any]:
        """Get pipeline information without running it."""
        async with self.client:
            if not await self.client.health_check():
                raise ConnectionError("WriteIt server is not available")

            pipeline_resp = await self.client.create_pipeline(
                pipeline_path, self.workspace_name
            )
            return pipeline_resp
