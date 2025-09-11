# ABOUTME: Rich console library example for WriteIt with real-time streaming capabilities
# ABOUTME: Demonstrates Rich's Live display features for streaming content updates

import asyncio
import time
from typing import Generator, Optional
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns


class WriteItRichDisplay:
    """Rich-based display system for WriteIt pipeline."""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.current_step = 0
        self.steps = ["Angles", "Outline", "Draft", "Polish"]
        self.streaming_content = ""
        self.setup_layout()
    
    def setup_layout(self):
        """Initialize the layout structure."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="sidebar", ratio=1),
            Layout(name="main", ratio=3),
            Layout(name="controls", ratio=1)
        )
        
        self.update_header()
        self.update_sidebar()
        self.update_controls()
        self.update_main_content()
    
    def update_header(self):
        """Update header with title and progress."""
        progress = Progress(
            TextColumn("[bold blue]WriteIt Pipeline", justify="center"),
            BarColumn(bar_width=40),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        
        progress_percentage = (self.current_step / len(self.steps)) * 100
        task = progress.add_task("Processing", total=100, completed=progress_percentage)
        
        self.layout["header"].update(Panel(Align.center(progress), title="Progress"))
    
    def update_sidebar(self):
        """Update sidebar with step progress."""
        step_table = Table(show_header=False, show_lines=False, box=None)
        step_table.add_column("Step", style="bold")
        
        for i, step in enumerate(self.steps):
            if i < self.current_step:
                step_table.add_row(f"✓ {step}", style="green")
            elif i == self.current_step:
                step_table.add_row(f"➤ {step}", style="yellow bold")
            else:
                step_table.add_row(f"○ {step}", style="dim")
        
        self.layout["sidebar"].update(Panel(step_table, title="Steps"))
    
    def update_controls(self):
        """Update controls panel."""
        controls_text = Text()
        controls_text.append("Controls:\n\n", style="bold")
        controls_text.append("↵ Enter", style="cyan")
        controls_text.append(" - Submit feedback\n")
        controls_text.append("→ Right", style="cyan")
        controls_text.append(" - Next step\n")
        controls_text.append("r", style="cyan")
        controls_text.append(" - Regenerate\n")
        controls_text.append("q", style="cyan")
        controls_text.append(" - Quit")
        
        self.layout["controls"].update(Panel(controls_text, title="Controls"))
    
    def update_main_content(self, content: str = ""):
        """Update main content area."""
        if not content:
            content = self.streaming_content
        
        content_text = Text(content)
        current_step_name = self.steps[self.current_step] if self.current_step < len(self.steps) else "Complete"
        
        self.layout["main"].update(
            Panel(content_text, title=f"AI Output - {current_step_name}", border_style="blue")
        )
    
    async def stream_content(self, content_generator: Generator[str, None, None]):
        """Stream content to the main display area."""
        self.streaming_content = ""
        
        with Live(self.layout, console=self.console, refresh_per_second=10) as live:
            for chunk in content_generator:
                self.streaming_content += chunk
                self.update_main_content()
                await asyncio.sleep(0.05)  # Control streaming speed
    
    def move_to_next_step(self):
        """Advance to next step."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.streaming_content = ""
            self.update_header()
            self.update_sidebar()
            return True
        return False
    
    def show_completion(self):
        """Show completion screen."""
        completion_text = Text()
        completion_text.append("🎉 Article Pipeline Complete!\n\n", style="bold green")
        completion_text.append("Your article has been generated through all steps:\n")
        
        for step in self.steps:
            completion_text.append(f"✓ {step}\n", style="green")
        
        completion_text.append("\nPress 'q' to quit or 'r' to restart.", style="dim")
        
        self.layout["main"].update(
            Panel(Align.center(completion_text), title="Success!", border_style="green")
        )


def simulate_llm_response(step: str) -> Generator[str, None, None]:
    """Simulate streaming LLM response for different pipeline steps."""
    responses = {
        "Angles": [
            "Analyzing your source material...\n\n",
            "🎯 Article Angle 1: The Human-AI Writing Partnership\n",
            "Focus: How AI enhances rather than replaces human creativity\n",
            "Key points: Productivity gains, creative inspiration, skill development\n\n",
            "🎯 Article Angle 2: The Evolution of Digital Writing Tools\n",
            "Focus: Historical perspective on writing technology advancement\n",
            "Key points: From typewriters to AI, technological milestones\n\n",
            "🎯 Article Angle 3: Ethical Considerations in AI-Assisted Writing\n",
            "Focus: Balancing efficiency with authenticity\n",
            "Key points: Attribution, originality, human oversight\n\n",
            "✨ Recommendation: Angle 1 offers the most engaging narrative for your audience."
        ],
        "Outline": [
            "Creating detailed outline based on selected angle...\n\n",
            "# The Human-AI Writing Partnership\n\n",
            "## Introduction (500 words)\n",
            "- Hook: Statistics on AI adoption in content creation\n",
            "- Context: Current state of writing industry\n",
            "- Thesis: AI as creative partner, not replacement\n\n",
            "## Historical Context (800 words)\n",
            "### From Quills to Algorithms\n",
            "- Evolution of writing tools\n",
            "- Previous technological disruptions\n\n",
            "## The Partnership Model (1200 words)\n",
            "### Benefits of AI Collaboration\n",
            "- Research acceleration\n",
            "- Ideation support\n",
            "- Editing assistance\n\n",
            "### Maintaining Human Voice\n",
            "- Creative control\n",
            "- Personal expression\n",
            "- Editorial judgment\n\n",
            "## Practical Applications (800 words)\n",
            "- Case studies\n",
            "- Industry examples\n",
            "- Success metrics\n\n",
            "## Future Outlook (400 words)\n",
            "- Emerging trends\n",
            "- Predictions\n",
            "- Call to action\n\n",
            "📊 Total word count: ~3,700 words\n",
            "📖 Reading time: ~15 minutes"
        ],
        "Draft": [
            "Writing full draft based on approved outline...\n\n",
            "# The Human-AI Writing Partnership: Redefining Creativity in the Digital Age\n\n",
            "In the bustling newsrooms and quiet home offices where tomorrow's stories take shape, ",
            "a quiet revolution is unfolding. Writers are discovering that their newest collaborator ",
            "doesn't occupy the desk next to them—it exists in the cloud, processes language at ",
            "lightning speed, and never needs a coffee break.\n\n",
            "The rise of AI-powered writing tools represents more than just another technological ",
            "advancement; it signals a fundamental shift in how we approach the creative process. ",
            "Recent surveys indicate that over 60% of professional writers have experimented with ",
            "AI assistance, yet many remain uncertain about how this technology will reshape their craft.\n\n",
            "## A New Chapter in Writing's Evolution\n\n",
            "To understand where we're headed, it's worth reflecting on where we've been. The history ",
            "of writing is inseparable from the history of writing tools. From the invention of the ",
            "printing press to the adoption of word processors, each technological leap has fundamentally ",
            "altered not just how we write, but what we write and who gets to participate in the ",
            "conversation.\n\n",
            "[Content continues streaming...]"
        ],
        "Polish": [
            "Applying final polish and refinements...\n\n",
            "# The Human-AI Writing Partnership: Redefining Creativity in the Digital Age\n\n",
            "In bustling newsrooms and quiet home offices where tomorrow's stories take shape, ",
            "a profound revolution is quietly unfolding. Writers worldwide are discovering that their ",
            "most valuable collaborator doesn't occupy the adjacent desk—it exists in the cloud, ",
            "processes language with unprecedented speed, and maintains unwavering availability.\n\n",
            "The emergence of AI-powered writing tools transcends mere technological advancement, ",
            "signaling a fundamental transformation in our approach to creative expression. ",
            "Industry research reveals that over 60% of professional writers have experimented with ",
            "AI assistance, yet many remain thoughtfully uncertain about how this technology will ",
            "reshape their craft's future landscape.\n\n",
            "## A New Chapter in Writing's Evolutionary Journey\n\n",
            "Understanding our destination requires acknowledging our origins. Writing's history ",
            "remains inseparable from the evolution of its tools. From Gutenberg's revolutionary ",
            "printing press to the widespread adoption of digital word processors, each technological ",
            "breakthrough has fundamentally transformed not merely our writing methods, but the very ",
            "nature of our content and the democratization of literary participation.\n\n",
            "✨ Polish complete - Enhanced clarity, flow, and engagement\n",
            "📈 Readability score improved by 15%\n",
            "🎯 Voice consistency maintained throughout"
        ]
    }
    
    content = responses.get(step, ["Processing..."])
    for chunk in content:
        yield chunk
        time.sleep(0.1)  # Simulate processing time


async def main():
    """Main application loop."""
    display = WriteItRichDisplay()
    
    with Live(display.layout, console=display.console, refresh_per_second=4):
        for step in display.steps:
            display.console.print(f"\n[bold cyan]Starting {step} generation...[/bold cyan]")
            
            # Simulate streaming content
            content_gen = simulate_llm_response(step)
            await display.stream_content(content_gen)
            
            # Update display
            display.update_header()
            display.update_sidebar()
            
            # Simulate user interaction delay
            await asyncio.sleep(2)
            
            if not display.move_to_next_step():
                break
        
        # Show completion
        display.show_completion()
        
        # Keep display active for a moment
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[bold red]Application interrupted by user[/bold red]")
    except Exception as e:
        print(f"[bold red]Error: {e}[/bold red]")