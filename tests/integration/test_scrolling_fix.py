#!/usr/bin/env python3
"""Test script to validate TUI scrolling and focus fixes."""

import asyncio
import sys
import pytest
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from writeit.tui.pipeline_runner import PipelineRunnerApp


@pytest.mark.asyncio
async def test_focus_navigation():
    """Test enhanced focus navigation."""
    print("Testing TUI focus navigation and scrolling fixes...")

    # Use existing template
    pipeline_path = Path("templates/quick-article.yaml")
    if not pipeline_path.exists():
        print(f"Error: Pipeline template not found at {pipeline_path}")
        return

    app = PipelineRunnerApp(pipeline_path, "test")

    async with app.run_test() as pilot:
        # Wait for app to fully load
        await pilot.pause()

        # Test focus cycling through inputs
        print("✓ Testing focus navigation...")
        await pilot.press("tab")  # Should focus next interactive element
        await pilot.pause()

        await pilot.press("shift+tab")  # Should focus previous
        await pilot.pause()

        await pilot.press("ctrl+j")  # Enhanced next focus
        await pilot.pause()

        await pilot.press("ctrl+k")  # Enhanced previous focus
        await pilot.pause()

        # Test scrolling
        print("✓ Testing scroll actions...")
        await pilot.press("ctrl+d")  # Scroll down
        await pilot.pause()

        await pilot.press("ctrl+u")  # Scroll up
        await pilot.pause()

        print("✓ All focus and scroll actions completed successfully!")

        # The app should still be responsive
        focused = app.screen.focused
        if focused:
            print(
                f"✓ Focus is on widget: {focused.__class__.__name__} (id: {getattr(focused, 'id', 'no-id')})"
            )
        else:
            print("⚠ No widget currently focused")


if __name__ == "__main__":
    asyncio.run(test_focus_navigation())
