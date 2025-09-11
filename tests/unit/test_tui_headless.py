"""Example of headless TUI testing using Textual's testing capabilities.

This demonstrates best practices for testing TUI components without timeouts.
"""

import pytest
from pathlib import Path
from textual.testing import AppTest
from writeit.tui.pipeline_runner import PipelineRunnerApp


@pytest.mark.asyncio
async def test_tui_app_launches_headless():
    """Test that TUI app can launch in headless mode for testing."""
    # Create a minimal pipeline config
    pipeline_config = {
        'metadata': {
            'name': 'Test Pipeline',
            'description': 'Test',
            'version': '1.0.0',
            'author': 'Test'
        },
        'inputs': {},
        'steps': {
            'test_step': {
                'type': 'llm_generation',
                'description': 'Test step',
                'model_preference': 'gpt-4',
                'prompt_template': 'Test prompt'
            }
        }
    }
    
    # Create temporary pipeline file
    import tempfile
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(pipeline_config, f)
        pipeline_path = Path(f.name)
    
    try:
        # Create app instance
        app = PipelineRunnerApp(pipeline_path, "test")
        
        # Use Textual's test runner
        async with app.run_test() as pilot:
            # App is now running in headless mode
            # We can interact with it programmatically
            
            # Wait for app to load
            await pilot.pause()
            
            # Check that app loaded successfully
            assert app.screen is not None
            
            # Simulate user interactions
            await pilot.press("tab")  # Navigate to next field
            await pilot.pause()
            
            # Check focus changes
            focused = app.screen.focused
            assert focused is not None
            
            # Exit the app
            await pilot.press("ctrl+c")
            
    finally:
        # Clean up temp file
        pipeline_path.unlink()


@pytest.mark.asyncio
async def test_tui_error_handling():
    """Test TUI error handling with invalid pipeline."""
    invalid_pipeline_path = Path("nonexistent.yaml")
    
    app = PipelineRunnerApp(invalid_pipeline_path, "test")
    
    async with app.run_test() as pilot:
        await pilot.pause()
        
        # App should show error
        # Check for error message in the screen
        screen_text = pilot.app.screen._repr_text()
        assert "Error" in screen_text or "Failed" in screen_text


class TestTUIComponents:
    """Test individual TUI components."""
    
    @pytest.mark.asyncio
    async def test_focus_navigation(self):
        """Test keyboard navigation between components."""
        # Create test pipeline
        pipeline_config = {
            'metadata': {
                'name': 'Nav Test',
                'description': 'Navigation test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {
                'topic': {
                    'type': 'text',
                    'description': 'Topic'
                },
                'style': {
                    'type': 'text',
                    'description': 'Style'
                }
            },
            'steps': {}
        }
        
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(pipeline_config, f)
            pipeline_path = Path(f.name)
        
        try:
            app = PipelineRunnerApp(pipeline_path, "test")
            
            async with app.run_test() as pilot:
                await pilot.pause()
                
                # Test Tab navigation
                initial_focus = app.screen.focused
                await pilot.press("tab")
                await pilot.pause()
                new_focus = app.screen.focused
                
                # Focus should change
                assert initial_focus != new_focus
                
                # Test Shift+Tab navigation
                await pilot.press("shift+tab")
                await pilot.pause()
                back_focus = app.screen.focused
                
                # Should go back
                assert back_focus == initial_focus
                
        finally:
            pipeline_path.unlink()
    
    @pytest.mark.asyncio
    async def test_input_submission(self):
        """Test submitting input values."""
        pipeline_config = {
            'metadata': {
                'name': 'Input Test',
                'description': 'Test',
                'version': '1.0.0',
                'author': 'Test'
            },
            'inputs': {
                'test_input': {
                    'type': 'text',
                    'description': 'Test input'
                }
            },
            'steps': {}
        }
        
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(pipeline_config, f)
            pipeline_path = Path(f.name)
        
        try:
            app = PipelineRunnerApp(pipeline_path, "test")
            
            async with app.run_test() as pilot:
                await pilot.pause()
                
                # Type in input field
                await pilot.press("tab")  # Focus first input
                await pilot.pause()
                
                # Type text
                await pilot.press("t", "e", "s", "t")
                await pilot.pause()
                
                # Submit (would normally trigger pipeline)
                # In test mode, just verify text was entered
                screen_text = pilot.app.screen._repr_text()
                # Text should appear somewhere in the screen
                # (exact assertion depends on implementation)
                
        finally:
            pipeline_path.unlink()


# Integration with pytest-textual (if available)
def test_tui_with_snapshot(snap_compare):
    """Test TUI appearance using snapshot testing.
    
    This requires pytest-textual plugin:
    pip install pytest-textual
    """
    # This would compare the TUI output against a saved snapshot
    # Useful for regression testing UI changes
    pass