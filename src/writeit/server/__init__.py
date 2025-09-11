# ABOUTME: WriteIt FastAPI server module
# ABOUTME: REST API and WebSocket endpoints for TUI backend communication

from .app import app, WebSocketManager, get_executor
from .client import WriteItClient, PipelineClient, ServerConfig

__all__ = [
    'app', 
    'WebSocketManager', 
    'get_executor',
    'WriteItClient',
    'PipelineClient', 
    'ServerConfig'
]