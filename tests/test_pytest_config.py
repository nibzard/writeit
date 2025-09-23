"""Test to verify pytest async configuration is working correctly."""

import asyncio
import pytest


class TestPytestAsyncConfig:
    """Test pytest async configuration."""
    
    def test_sync_test(self):
        """Test that sync tests work normally."""
        assert True
    
    async def test_async_test_auto_detection(self):
        """Test that async tests are auto-detected and work."""
        await asyncio.sleep(0.001)  # Minimal async operation
        assert True
    
    @pytest.mark.asyncio
    async def test_explicit_async_marker(self):
        """Test that explicitly marked async tests work."""
        await asyncio.sleep(0.001)
        assert True
    
    async def test_async_fixture_usage(self, async_test_context):
        """Test that async fixtures work correctly."""
        assert async_test_context is not None
        await asyncio.sleep(0.001)
        assert True
    
    def test_temp_dir_fixture(self, temp_dir):
        """Test that temp directory fixture works."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        assert "writeit_test_" in temp_dir.name
    
    def test_test_config_fixture(self, test_config):
        """Test that test config fixture works."""
        assert isinstance(test_config, dict)
        assert "workspace" in test_config
        assert "storage" in test_config
        assert "llm" in test_config
        assert "pipeline" in test_config
        assert "testing" in test_config
    
    def test_mock_llm_provider_fixture(self, mock_llm_provider):
        """Test that mock LLM provider fixture works."""
        assert mock_llm_provider is not None
        assert hasattr(mock_llm_provider, 'generate_text')
        assert hasattr(mock_llm_provider, 'stream_text')
        assert hasattr(mock_llm_provider, 'get_model_info')
    
    def test_test_data_factory_fixture(self, test_data_factory):
        """Test that test data factory fixture works."""
        assert test_data_factory is not None
        
        # Test pipeline creation
        pipeline = test_data_factory.create_pipeline_yaml("test")
        assert pipeline["metadata"]["name"] == "test"
        assert "inputs" in pipeline
        assert "steps" in pipeline
        
        # Test workspace config creation
        config = test_data_factory.create_workspace_config(custom_setting=True)
        assert config["name"] == "test-workspace"
        assert config["custom_setting"] is True
    
    async def test_performance_tracker_fixture(self, performance_tracker):
        """Test that performance tracker fixture works."""
        assert performance_tracker is not None
        
        # Test timing operation
        with performance_tracker.time_operation("test_op"):
            await asyncio.sleep(0.01)
        
        metrics = performance_tracker.get_metrics()
        assert "test_op" in metrics
        assert metrics["test_op"]["count"] == 1
        assert metrics["test_op"]["average"] > 0
    
    async def test_wait_for_helper(self, wait_for):
        """Test that wait_for helper works."""
        counter = 0
        
        def increment_counter():
            nonlocal counter
            counter += 1
            return counter >= 3
        
        # This should complete quickly as condition is met on 3rd check
        result = await wait_for(increment_counter, timeout=1.0, poll_interval=0.001)
        assert result is True
        assert counter >= 3
    
    async def test_simple_mock_event_bus_fixture(self, simple_mock_event_bus):
        """Test that simple mock event bus fixture works."""
        assert simple_mock_event_bus is not None
        assert not simple_mock_event_bus.running
        
        # Test start/stop
        await simple_mock_event_bus.start()
        assert simple_mock_event_bus.running
        
        await simple_mock_event_bus.stop()
        assert not simple_mock_event_bus.running
        
        # Test event publishing (basic mock)
        mock_event = {"type": "test", "data": "test_data"}
        result = await simple_mock_event_bus.publish(mock_event)
        
        assert result.event == mock_event
        assert len(simple_mock_event_bus.published_events) == 1
        assert simple_mock_event_bus.published_events[0] == mock_event


class TestPytestMarkers:
    """Test pytest markers configuration."""
    
    @pytest.mark.slow
    async def test_slow_marker(self):
        """Test that slow marker works (can be filtered out)."""
        await asyncio.sleep(0.001)
        assert True
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit marker works."""
        assert True
    
    @pytest.mark.integration
    async def test_integration_marker(self):
        """Test that integration marker works."""
        await asyncio.sleep(0.001)
        assert True
    
    @pytest.mark.workspace
    def test_workspace_marker(self):
        """Test that workspace marker works."""
        assert True
    
    @pytest.mark.storage
    def test_storage_marker(self):
        """Test that storage marker works."""
        assert True
    
    @pytest.mark.event_bus
    async def test_event_bus_marker(self):
        """Test that event_bus marker works."""
        await asyncio.sleep(0.001)
        assert True
    
    @pytest.mark.pipeline
    async def test_pipeline_marker(self):
        """Test that pipeline marker works."""
        await asyncio.sleep(0.001)
        assert True


class TestEnvironmentConfiguration:
    """Test environment configuration."""
    
    def test_environment_variables_set(self):
        """Test that test environment variables are properly set."""
        import os
        
        assert os.environ.get("WRITEIT_TEST_MODE") == "true"
        assert os.environ.get("WRITEIT_LOG_LEVEL") == "WARNING"
        assert os.environ.get("WRITEIT_LLM_PROVIDER") == "mock"
        assert os.environ.get("WRITEIT_DATABASE_TIMEOUT") == "10"


# Test that should be automatically marked as async
async def test_function_level_async():
    """Test function-level async test (should be auto-marked)."""
    await asyncio.sleep(0.001)
    assert True