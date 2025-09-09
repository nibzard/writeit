# ABOUTME: Example Textual TUI app that connects to WebSocket for real-time streaming
# ABOUTME: Demonstrates how to integrate Textual with FastAPI WebSocket backend for WriteIt

import asyncio
import json
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Log, Static, ProgressBar
from textual.reactive import reactive
import websockets


class WriteItTUI(App):
    """Main TUI application for WriteIt pipeline."""
    
    CSS_PATH = "writeIt.css"
    
    # Reactive attributes for real-time updates
    current_step = reactive("angles")
    progress_value = reactive(0)
    streaming_content = reactive("")
    
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        with Container(id="main"):
            with Horizontal(id="header"):
                yield Static("WriteIt - LLM Article Pipeline", id="title")
                yield ProgressBar(total=100, show_percentage=True, id="progress")
            
            with Horizontal(id="content"):
                with Vertical(id="left-panel"):
                    yield Static("Step Progress", classes="panel-title")
                    yield Static("1. Angles", id="step-1", classes="step active")
                    yield Static("2. Outline", id="step-2", classes="step")
                    yield Static("3. Draft", id="step-3", classes="step")
                    yield Static("4. Polish", id="step-4", classes="step")
                
                with Vertical(id="center-panel"):
                    yield Static("Real-time AI Response", classes="panel-title")
                    yield Log(id="ai-output", auto_scroll=True)
                    
                with Vertical(id="right-panel"):
                    yield Static("Controls", classes="panel-title")
                    yield Input(placeholder="Enter your feedback...", id="user-input")
                    yield Button("Next Step", id="next-btn")
                    yield Button("Regenerate", id="regen-btn")
    
    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        self.start_websocket_connection()
    
    def start_websocket_connection(self) -> None:
        """Start WebSocket connection to FastAPI backend."""
        asyncio.create_task(self.websocket_handler())
    
    async def websocket_handler(self):
        """Handle WebSocket communication with FastAPI backend."""
        uri = "ws://localhost:8000/ws"
        try:
            async with websockets.connect(uri) as websocket:
                # Listen for streaming responses
                async for message in websocket:
                    data = json.loads(message)
                    await self.handle_websocket_message(data)
        except Exception as e:
            log = self.query_one("#ai-output", Log)
            log.write_line(f"WebSocket error: {e}")
    
    async def handle_websocket_message(self, data: dict):
        """Process incoming WebSocket messages."""
        message_type = data.get("type")
        content = data.get("content", "")
        
        log = self.query_one("#ai-output", Log)
        
        if message_type == "stream_token":
            # Real-time streaming token
            self.streaming_content += content
            log.write_line(content, end="")
        elif message_type == "step_complete":
            # Step completion
            self.progress_value = data.get("progress", 0)
            self.current_step = data.get("step", "")
            log.write_line(f"\n✓ {data.get('step')} completed")
            self.update_step_display()
        elif message_type == "error":
            log.write_line(f"❌ Error: {content}")
    
    def update_step_display(self):
        """Update the step progress display."""
        steps = ["angles", "outline", "draft", "polish"]
        current_index = steps.index(self.current_step) if self.current_step in steps else 0
        
        for i, step in enumerate(steps, 1):
            step_widget = self.query_one(f"#step-{i}", Static)
            if i <= current_index + 1:
                step_widget.add_class("active")
            else:
                step_widget.remove_class("active")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "next-btn":
            await self.send_next_step()
        elif event.button.id == "regen-btn":
            await self.send_regenerate()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value
        event.input.value = ""  # Clear input
        
        # Send feedback via WebSocket
        await self.send_user_feedback(user_input)
    
    async def send_user_feedback(self, feedback: str):
        """Send user feedback to backend."""
        message = {
            "type": "user_feedback",
            "content": feedback,
            "step": self.current_step
        }
        # In real implementation, send via WebSocket
        log = self.query_one("#ai-output", Log)
        log.write_line(f"👤 Feedback: {feedback}")
    
    async def send_next_step(self):
        """Request next pipeline step."""
        message = {
            "type": "next_step",
            "current_step": self.current_step
        }
        # In real implementation, send via WebSocket
        log = self.query_one("#ai-output", Log)
        log.write_line("➡️ Moving to next step...")
    
    async def send_regenerate(self):
        """Request regeneration of current step."""
        message = {
            "type": "regenerate",
            "step": self.current_step
        }
        # In real implementation, send via WebSocket
        log = self.query_one("#ai-output", Log)
        log.write_line("🔄 Regenerating current step...")

    def watch_progress_value(self, progress: int) -> None:
        """React to progress changes."""
        progress_bar = self.query_one("#progress", ProgressBar)
        progress_bar.progress = progress


if __name__ == "__main__":
    app = WriteItTUI()
    app.run()