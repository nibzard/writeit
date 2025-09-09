# ABOUTME: Prompt_toolkit example for WriteIt showing async prompt and real-time updates
# ABOUTME: Demonstrates prompt_toolkit's async capabilities with custom layouts

import asyncio
from typing import Optional, Callable
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Frame, Label, Box
from prompt_toolkit.formatted_text import HTML
import threading
import time


class WriteItPromptApp:
    """WriteIt application using prompt_toolkit for async TUI."""
    
    def __init__(self):
        self.current_step = 0
        self.steps = ["Angles", "Outline", "Draft", "Polish"]
        self.streaming_content = ""
        self.user_feedback = ""
        self.is_streaming = False
        
        # Create buffers
        self.output_buffer = Buffer(multiline=True, read_only=True)
        self.input_buffer = Buffer(multiline=True)
        
        # Setup key bindings
        self.kb = KeyBindings()
        self.setup_key_bindings()
        
        # Create layout
        self.layout = self.create_layout()
        
        # Create application
        self.app = Application(
            layout=Layout(self.layout),
            key_bindings=self.kb,
            style=self.create_style(),
            full_screen=True
        )
        
        # Start background streaming task
        asyncio.create_task(self.background_streaming_task())
    
    def create_style(self) -> Style:
        """Create application style."""
        return Style.from_dict({
            'title': 'bg:#3f51b5 #ffffff bold',
            'step-active': '#ffc107 bold',
            'step-complete': '#4caf50 bold', 
            'step-pending': '#9e9e9e',
            'output-area': 'bg:#f5f5f5 #000000',
            'input-area': 'bg:#ffffff #000000',
            'controls': '#607d8b bold',
            'progress': '#2196f3 bold',
        })
    
    def create_layout(self) -> HSplit:
        """Create the application layout."""
        # Header with title and progress
        header = Frame(
            Label(text=self.get_header_text, style="class:title"),
            title="WriteIt Pipeline"
        )
        
        # Main content area split into columns
        body = VSplit([
            # Left panel - Step progress
            Frame(
                Window(
                    FormattedTextControl(text=self.get_step_progress),
                    wrap_lines=True
                ),
                title="Progress",
                width=20
            ),
            
            # Center panel - Streaming output
            Frame(
                Window(
                    BufferControl(buffer=self.output_buffer),
                    wrap_lines=True,
                    scrollbar=True
                ),
                title="AI Output"
            ),
            
            # Right panel - Controls and input
            HSplit([
                Frame(
                    Window(
                        FormattedTextControl(text=self.get_controls_text),
                        wrap_lines=True
                    ),
                    title="Controls",
                    height=8
                ),
                Frame(
                    Window(BufferControl(buffer=self.input_buffer)),
                    title="Feedback",
                )
            ], width=25)
        ])
        
        return HSplit([header, body])
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts."""
        @self.kb.add('c-q')
        def quit_app(event):
            """Quit application."""
            event.app.exit()
        
        @self.kb.add('c-n')
        def next_step(event):
            """Move to next step."""
            if self.current_step < len(self.steps) - 1 and not self.is_streaming:
                self.current_step += 1
                self.start_step_processing()
        
        @self.kb.add('c-r')
        def regenerate(event):
            """Regenerate current step."""
            if not self.is_streaming:
                self.start_step_processing(regenerate=True)
        
        @self.kb.add('enter')
        def submit_feedback(event):
            """Submit user feedback."""
            if self.input_buffer.text.strip():
                self.user_feedback = self.input_buffer.text.strip()
                self.input_buffer.document = Document()  # Clear input
                self.add_to_output(f"\n👤 Feedback: {self.user_feedback}\n")
    
    def get_header_text(self) -> HTML:
        """Generate header text with progress."""
        progress = int((self.current_step / len(self.steps)) * 100)
        current_step_name = self.steps[self.current_step] if self.current_step < len(self.steps) else "Complete"
        return HTML(f'<class:title>WriteIt Pipeline - {current_step_name} ({progress}%)</class>')
    
    def get_step_progress(self) -> HTML:
        """Generate step progress display."""
        html_parts = []
        
        for i, step in enumerate(self.steps):
            if i < self.current_step:
                html_parts.append(f'<class:step-complete>✓ {step}</class>\n')
            elif i == self.current_step:
                if self.is_streaming:
                    html_parts.append(f'<class:step-active>⟳ {step}</class>\n')
                else:
                    html_parts.append(f'<class:step-active>➤ {step}</class>\n')
            else:
                html_parts.append(f'<class:step-pending>○ {step}</class>\n')
        
        return HTML(''.join(html_parts))
    
    def get_controls_text(self) -> HTML:
        """Generate controls help text."""
        return HTML('''
<class:controls>Ctrl+N</class> - Next Step
<class:controls>Ctrl+R</class> - Regenerate
<class:controls>Enter</class> - Submit Feedback
<class:controls>Ctrl+Q</class> - Quit

<class:progress>Status:</class> ''' + ('Streaming' if self.is_streaming else 'Ready'))
    
    def add_to_output(self, text: str):
        """Add text to output buffer."""
        current_text = self.output_buffer.text
        new_text = current_text + text
        self.output_buffer.document = Document(text=new_text, cursor_position=len(new_text))
    
    def clear_output(self):
        """Clear output buffer."""
        self.output_buffer.document = Document()
    
    def start_step_processing(self, regenerate: bool = False):
        """Start processing current step."""
        if self.is_streaming:
            return
        
        current_step_name = self.steps[self.current_step]
        action = "Regenerating" if regenerate else "Starting"
        
        self.add_to_output(f"\n🔄 {action} {current_step_name}...\n")
        
        # Start streaming simulation
        asyncio.create_task(self.simulate_streaming_response(current_step_name))
    
    async def simulate_streaming_response(self, step: str):
        """Simulate streaming AI response."""
        self.is_streaming = True
        
        # Sample responses for each step
        responses = {
            "Angles": [
                "\n🎯 Analyzing your requirements...\n\n",
                "Article Angle 1: Technical Deep-dive\n",
                "- Focus on implementation details\n",
                "- Target: Developer audience\n\n",
                "Article Angle 2: Business Impact\n", 
                "- Focus on ROI and productivity gains\n",
                "- Target: Decision makers\n\n",
                "Article Angle 3: User Experience\n",
                "- Focus on practical applications\n",
                "- Target: End users\n\n",
                "💡 Recommendation: Angle 2 aligns best with your goals.\n"
            ],
            "Outline": [
                "\n📋 Creating detailed outline...\n\n",
                "# Article Structure\n\n",
                "## Introduction (300 words)\n",
                "- Problem statement\n", 
                "- Solution overview\n\n",
                "## Main Content (1200 words)\n",
                "### Benefits Analysis\n",
                "- Quantifiable improvements\n",
                "- Case studies\n\n",
                "### Implementation Strategy\n",
                "- Step-by-step approach\n",
                "- Best practices\n\n",
                "## Conclusion (200 words)\n",
                "- Key takeaways\n",
                "- Next steps\n\n",
                "📊 Total: ~1,700 words, 7-minute read\n"
            ],
            "Draft": [
                "\n✍️ Writing first draft...\n\n",
                "# Revolutionizing Content Creation with AI-Powered Writing Tools\n\n",
                "The landscape of content creation is experiencing unprecedented transformation. ",
                "Organizations across industries are discovering that artificial intelligence doesn't ",
                "replace human creativity—it amplifies it.\n\n",
                "## The Business Case for AI Writing Tools\n\n",
                "Recent studies reveal compelling statistics: companies implementing AI writing ",
                "assistants report 40% faster content production while maintaining quality standards. ",
                "This efficiency gain translates directly to bottom-line impact...\n\n",
                "[Content continues with detailed analysis and examples]\n"
            ],
            "Polish": [
                "\n✨ Applying final polish...\n\n",
                "# Revolutionizing Content Creation with AI-Powered Writing Tools\n\n",
                "Today's content creation landscape is undergoing unprecedented transformation. ",
                "Forward-thinking organizations across industries are discovering a fundamental truth: ",
                "artificial intelligence doesn't replace human creativity—it amplifies it exponentially.\n\n",
                "## The Compelling Business Case for AI Writing Tools\n\n",
                "Industry research reveals striking metrics: companies implementing AI writing ",
                "assistants consistently report 40% faster content production while exceeding ",
                "quality benchmarks. This efficiency breakthrough translates directly to measurable ",
                "ROI across multiple organizational levels...\n\n",
                "🎯 Polish complete - Enhanced clarity and flow\n",
                "📈 Readability improved\n",
                "✅ Brand voice maintained\n"
            ]
        }
        
        content_chunks = responses.get(step, ["Processing..."])
        
        for chunk in content_chunks:
            if not self.is_streaming:  # Check if streaming was cancelled
                break
                
            self.add_to_output(chunk)
            await asyncio.sleep(0.2)  # Simulate streaming delay
        
        self.is_streaming = False
        self.add_to_output(f"\n✅ {step} completed!\n")
    
    async def background_streaming_task(self):
        """Background task for handling real-time updates."""
        # Start with first step automatically
        await asyncio.sleep(1)  # Give UI time to initialize
        self.start_step_processing()
    
    async def run_async(self):
        """Run the application asynchronously."""
        try:
            await self.app.run_async()
        except KeyboardInterrupt:
            pass


async def main():
    """Main application entry point."""
    app = WriteItPromptApp()
    await app.run_async()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"Error: {e}")