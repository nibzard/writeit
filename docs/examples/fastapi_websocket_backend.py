# ABOUTME: FastAPI backend with WebSocket support for WriteIt TUI application
# ABOUTME: Handles real-time streaming of LLM responses and pipeline coordination

import asyncio
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


class WriteItPipeline:
    """Simulates the WriteIt article generation pipeline."""
    
    STEPS = ["angles", "outline", "draft", "polish"]
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.current_step = 0
        self.pipeline_data = {}
    
    async def simulate_llm_streaming(self, websocket: WebSocket, step: str):
        """Simulate streaming LLM response token by token."""
        sample_responses = {
            "angles": [
                "Article Angle 1: The Rise of AI-Powered Writing Tools",
                "Focusing on productivity gains and creative enhancement...",
                "\n\nArticle Angle 2: Human-AI Collaboration in Content Creation",
                "Exploring the symbiotic relationship between writers and AI...",
                "\n\nArticle Angle 3: The Future of Publishing with AI Assistance",
                "How AI tools are reshaping the publishing industry..."
            ],
            "outline": [
                "# Detailed Article Outline\n\n",
                "## Introduction\n",
                "- Hook: Statistics on AI adoption in writing\n",
                "- Context: Current state of writing tools\n\n",
                "## Main Sections\n",
                "### 1. The Evolution of Writing Tools\n",
                "- From typewriters to AI assistants\n",
                "- Key technological milestones\n\n",
                "### 2. Benefits and Challenges\n",
                "- Productivity improvements\n",
                "- Quality considerations\n",
                "- Ethical implications\n\n",
                "## Conclusion\n",
                "- Future outlook\n",
                "- Call to action for writers"
            ],
            "draft": [
                "# The Rise of AI-Powered Writing Tools\n\n",
                "In the rapidly evolving landscape of digital content creation, ",
                "artificial intelligence has emerged as a transformative force that's ",
                "reshaping how we approach writing and storytelling. ",
                "\n\nFrom simple grammar checkers to sophisticated language models, ",
                "AI-powered writing tools have evolved dramatically over the past decade. ",
                "These innovations promise to enhance creativity, boost productivity, ",
                "and democratize high-quality content creation across industries."
            ],
            "polish": [
                "# The Rise of AI-Powered Writing Tools\n\n",
                "In today's rapidly evolving digital landscape, artificial intelligence ",
                "has emerged as a transformative catalyst, fundamentally reshaping our ",
                "approach to writing and storytelling.\n\n",
                "The evolution from basic grammar checkers to sophisticated language models ",
                "represents a quantum leap in writing assistance technology. These cutting-edge ",
                "innovations promise to amplify human creativity, dramatically boost productivity, ",
                "and democratize access to high-quality content creation across all industries."
            ]
        }
        
        content_tokens = sample_responses.get(step, ["No content available for this step."])
        
        # Simulate token-by-token streaming
        for i, token in enumerate(content_tokens):
            await asyncio.sleep(0.1)  # Simulate LLM response delay
            
            await self.connection_manager.send_personal_message({
                "type": "stream_token",
                "content": token,
                "step": step,
                "token_index": i,
                "total_tokens": len(content_tokens)
            }, websocket)
        
        # Signal step completion
        progress = ((self.current_step + 1) / len(self.STEPS)) * 100
        await self.connection_manager.send_personal_message({
            "type": "step_complete",
            "step": step,
            "progress": int(progress),
            "message": f"Step '{step}' completed successfully"
        }, websocket)
    
    async def process_user_feedback(self, feedback: str, step: str, websocket: WebSocket):
        """Process user feedback and adjust pipeline accordingly."""
        await self.connection_manager.send_personal_message({
            "type": "feedback_received",
            "content": f"Processing feedback for {step}: {feedback}",
            "step": step
        }, websocket)
        
        # Simulate feedback processing
        await asyncio.sleep(1)
        
        await self.connection_manager.send_personal_message({
            "type": "feedback_processed",
            "content": "Feedback integrated. Ready for next step.",
            "step": step
        }, websocket)
    
    async def move_to_next_step(self, websocket: WebSocket):
        """Advance to the next pipeline step."""
        if self.current_step < len(self.STEPS) - 1:
            self.current_step += 1
            next_step = self.STEPS[self.current_step]
            
            await self.connection_manager.send_personal_message({
                "type": "step_started",
                "step": next_step,
                "message": f"Starting step: {next_step}"
            }, websocket)
            
            # Start processing the new step
            await self.simulate_llm_streaming(websocket, next_step)
        else:
            await self.connection_manager.send_personal_message({
                "type": "pipeline_complete",
                "message": "Article pipeline completed successfully!",
                "final_step": self.STEPS[self.current_step]
            }, websocket)
    
    async def regenerate_current_step(self, websocket: WebSocket):
        """Regenerate the current pipeline step."""
        current_step_name = self.STEPS[self.current_step]
        
        await self.connection_manager.send_personal_message({
            "type": "step_regenerating",
            "step": current_step_name,
            "message": f"Regenerating {current_step_name}..."
        }, websocket)
        
        # Simulate regeneration with slight delay
        await asyncio.sleep(0.5)
        await self.simulate_llm_streaming(websocket, current_step_name)


app = FastAPI(title="WriteIt Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for TUI communication."""
    pipeline = WriteItPipeline(manager)
    
    await manager.connect(websocket)
    
    try:
        # Send initial welcome message
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to WriteIt backend",
            "available_steps": pipeline.STEPS
        }, websocket)
        
        # Start with first step
        await pipeline.simulate_llm_streaming(websocket, pipeline.STEPS[0])
        
        # Listen for client messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "user_feedback":
                feedback = message.get("content", "")
                step = message.get("step", "")
                await pipeline.process_user_feedback(feedback, step, websocket)
                
            elif message_type == "next_step":
                await pipeline.move_to_next_step(websocket)
                
            elif message_type == "regenerate":
                await pipeline.regenerate_current_step(websocket)
                
            elif message_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "message": "Connection alive"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "WriteIt Backend"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "WriteIt Backend API",
        "version": "1.0.0",
        "websocket_endpoint": "/ws",
        "features": ["real-time streaming", "multi-step pipeline", "user feedback"]
    }


if __name__ == "__main__":
    uvicorn.run(
        "fastapi_websocket_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )