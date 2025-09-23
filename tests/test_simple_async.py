"""Simple test to verify async configuration works."""

import asyncio
import pytest


@pytest.mark.asyncio
async def test_explicit_async_marker():
    """Test with explicit async marker."""
    await asyncio.sleep(0.001)
    assert True


async def test_auto_async_detection():
    """Test without explicit marker (should be auto-detected)."""
    await asyncio.sleep(0.001) 
    assert True


def test_sync_test():
    """Regular sync test."""
    assert True


class TestAsyncInClass:
    """Test async methods in a class."""
    
    @pytest.mark.asyncio
    async def test_explicit_class_async(self):
        """Explicit async test in class."""
        await asyncio.sleep(0.001)
        assert True
    
    async def test_auto_class_async(self):
        """Auto-detected async test in class."""
        await asyncio.sleep(0.001)
        assert True
    
    def test_sync_in_class(self):
        """Sync test in class."""
        assert True