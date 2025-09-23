"""Tests for access control infrastructure."""

import asyncio
import pytest
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from src.writeit.infrastructure.base.access_control import (
    AccessLevel,
    ResourceType,
    AccessRequest,
    AccessResult,
    ResourceLimit,
    WorkspaceAccessController,
    RateLimitController,
    ResourceLimitController,
    CompositeAccessController,
    AccessControlManager,
    WorkspaceAccessDeniedError,
    RateLimitExceededError,
    ResourceLimitExceededError,
    get_access_control_manager,
    enforce_workspace_access,
    check_workspace_access
)


class TestAccessRequest:
    """Test AccessRequest data class."""
    
    def test_access_request_creation(self):
        """Test creating an access request."""
        workspace_name = WorkspaceName("test")
        request = AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name,
            user_id="user123"
        )
        
        assert request.resource_id == "test-resource"
        assert request.resource_type == ResourceType.FILE
        assert request.access_level == AccessLevel.READ
        assert request.workspace_name == workspace_name
        assert request.user_id == "user123"
        assert isinstance(request.timestamp, float)
        assert request.metadata == {}


class TestWorkspaceAccessController:
    """Test WorkspaceAccessController."""
    
    @pytest.fixture
    def workspace_name(self):
        """Test workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.fixture
    def controller(self):
        """Create workspace access controller."""
        return WorkspaceAccessController()
    
    @pytest.fixture
    def access_request(self, workspace_name):
        """Create test access request."""
        return AccessRequest(
            resource_id="/test/file.txt",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
    
    @pytest.mark.asyncio
    async def test_check_access_allowed(self, controller, access_request):
        """Test access is allowed for valid request."""
        result = await controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "Access granted"
        assert result.access_level == AccessLevel.READ
    
    @pytest.mark.asyncio
    async def test_check_access_restricted_workspace(self, workspace_name):
        """Test access denied for restricted workspace."""
        allowed_workspaces = {WorkspaceName("allowed")}
        controller = WorkspaceAccessController(allowed_workspaces=allowed_workspaces)
        
        request = AccessRequest(
            resource_id="test",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
        
        result = await controller.check_access(request)
        
        assert result.allowed is False
        assert "not in allowed list" in result.reason
        assert result.access_level == AccessLevel.NONE
    
    @pytest.mark.asyncio
    async def test_check_access_level_exceeded(self, controller, workspace_name):
        """Test access denied when access level exceeds maximum."""
        controller.set_workspace_restrictions(workspace_name, {
            'max_access_level': AccessLevel.READ
        })
        
        request = AccessRequest(
            resource_id="test",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.WRITE,
            workspace_name=workspace_name
        )
        
        result = await controller.check_access(request)
        
        assert result.allowed is False
        assert "exceeds maximum" in result.reason
    
    @pytest.mark.asyncio
    async def test_enforce_limits_read_only(self, controller, workspace_name):
        """Test enforce limits for read-only workspace."""
        controller.set_workspace_restrictions(workspace_name, {'read_only': True})
        
        request = AccessRequest(
            resource_id="test",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.WRITE,
            workspace_name=workspace_name
        )
        
        with pytest.raises(WorkspaceAccessDeniedError) as exc_info:
            await controller.enforce_limits(request)
        
        assert "read-only mode" in str(exc_info.value)
        assert exc_info.value.workspace_name == workspace_name
    
    def test_set_and_get_workspace_restrictions(self, controller, workspace_name):
        """Test setting and getting workspace restrictions."""
        restrictions = {'read_only': True, 'max_files': 100}
        controller.set_workspace_restrictions(workspace_name, restrictions)
        
        retrieved = controller.get_workspace_restrictions(workspace_name)
        assert retrieved == restrictions
    
    @pytest.mark.asyncio
    async def test_file_access_validation(self, controller, workspace_name):
        """Test file access path validation."""
        # Test path within workspace (should be allowed)
        request = AccessRequest(
            resource_id=f"/home/user/.writeit/workspaces/{workspace_name}/file.txt",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
        
        result = await controller.check_access(request)
        assert result.allowed is True


class TestRateLimitController:
    """Test RateLimitController."""
    
    @pytest.fixture
    def controller(self):
        """Create rate limit controller."""
        return RateLimitController()
    
    @pytest.fixture
    def workspace_name(self):
        """Test workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.fixture
    def access_request(self, workspace_name):
        """Create test access request."""
        return AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
    
    @pytest.mark.asyncio
    async def test_check_access_no_limit(self, controller, access_request):
        """Test access allowed when no rate limit is configured."""
        result = await controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "No rate limit configured"
    
    @pytest.mark.asyncio
    async def test_check_access_within_limit(self, controller, workspace_name, access_request):
        """Test access allowed when within rate limit."""
        controller.set_rate_limit(workspace_name, ResourceType.FILE, 10, 60)
        
        result = await controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "Rate limit OK"
        assert "rate_limit" in result.restrictions
    
    @pytest.mark.asyncio
    async def test_check_access_exceeded_limit(self, controller, workspace_name):
        """Test access denied when rate limit exceeded."""
        controller.set_rate_limit(workspace_name, ResourceType.FILE, 2, 60)
        
        # Make requests up to limit
        for i in range(3):
            request = AccessRequest(
                resource_id=f"resource-{i}",
                resource_type=ResourceType.FILE,
                access_level=AccessLevel.READ,
                workspace_name=workspace_name
            )
            
            if i < 2:
                # First 2 should succeed
                result = await controller.check_access(request)
                assert result.allowed is True
                await controller.track_usage(request, result)
            else:
                # Third should fail
                result = await controller.check_access(request)
                assert result.allowed is False
                assert "Rate limit exceeded" in result.reason
    
    @pytest.mark.asyncio
    async def test_enforce_limits_exceeded(self, controller, workspace_name):
        """Test enforce limits raises exception when exceeded."""
        controller.set_rate_limit(workspace_name, ResourceType.FILE, 1, 60)
        
        # First request should succeed
        request1 = AccessRequest(
            resource_id="resource-1",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
        result1 = await controller.check_access(request1)
        await controller.track_usage(request1, result1)
        
        # Second request should fail
        request2 = AccessRequest(
            resource_id="resource-2",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
        
        with pytest.raises(RateLimitExceededError) as exc_info:
            await controller.enforce_limits(request2)
        
        assert exc_info.value.resource_id == "resource-2"
        assert exc_info.value.limit == 1
        assert exc_info.value.window_seconds == 60
    
    def test_set_rate_limit(self, controller, workspace_name):
        """Test setting rate limit."""
        controller.set_rate_limit(workspace_name, ResourceType.FILE, 100, 3600)
        
        usage = controller.get_current_usage(workspace_name, ResourceType.FILE)
        assert usage == 0
    
    @pytest.mark.asyncio
    async def test_track_usage(self, controller, workspace_name, access_request):
        """Test tracking usage updates count."""
        controller.set_rate_limit(workspace_name, ResourceType.FILE, 10, 60)
        
        result = AccessResult(allowed=True, reason="test", access_level=AccessLevel.READ)
        await controller.track_usage(access_request, result)
        
        usage = controller.get_current_usage(workspace_name, ResourceType.FILE)
        assert usage == 1


class TestResourceLimitController:
    """Test ResourceLimitController."""
    
    @pytest.fixture
    def controller(self):
        """Create resource limit controller."""
        return ResourceLimitController()
    
    @pytest.fixture
    def workspace_name(self):
        """Test workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.fixture
    def access_request(self, workspace_name):
        """Create test access request."""
        return AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.MEMORY,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
    
    @pytest.mark.asyncio
    async def test_check_access_no_limit(self, controller, access_request):
        """Test access allowed when no resource limit is configured."""
        result = await controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "No resource limit configured"
    
    @pytest.mark.asyncio
    async def test_check_access_no_usage(self, controller, workspace_name, access_request):
        """Test access allowed when no current usage is tracked."""
        controller.set_resource_limit(workspace_name, ResourceType.MEMORY, 1000)
        
        result = await controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "No current usage tracked"
    
    @pytest.mark.asyncio
    async def test_check_access_within_limit(self, controller, workspace_name, access_request):
        """Test access allowed when within resource limit."""
        controller.set_resource_limit(workspace_name, ResourceType.MEMORY, 1000)
        controller.update_current_usage(workspace_name, ResourceType.MEMORY, 500)
        
        result = await controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "Resource limit OK"
        assert "resource_limit" in result.restrictions
    
    @pytest.mark.asyncio
    async def test_check_access_exceeded_limit(self, controller, workspace_name, access_request):
        """Test access denied when resource limit exceeded."""
        controller.set_resource_limit(workspace_name, ResourceType.MEMORY, 1000)
        controller.update_current_usage(workspace_name, ResourceType.MEMORY, 1500)
        
        result = await controller.check_access(access_request)
        
        assert result.allowed is False
        assert "Resource limit exceeded" in result.reason
    
    @pytest.mark.asyncio
    async def test_enforce_limits_exceeded(self, controller, workspace_name, access_request):
        """Test enforce limits raises exception when exceeded."""
        controller.set_resource_limit(workspace_name, ResourceType.MEMORY, 1000)
        controller.update_current_usage(workspace_name, ResourceType.MEMORY, 1500)
        
        with pytest.raises(ResourceLimitExceededError) as exc_info:
            await controller.enforce_limits(access_request)
        
        assert exc_info.value.resource_type == ResourceType.MEMORY
        assert exc_info.value.current == 1500
        assert exc_info.value.limit == 1000
    
    def test_set_resource_limit(self, controller, workspace_name):
        """Test setting resource limit."""
        controller.set_resource_limit(workspace_name, ResourceType.MEMORY, 2000)
        
        # Verify limit is set by updating usage and checking
        controller.update_current_usage(workspace_name, ResourceType.MEMORY, 1000)
        # No exception should be raised since usage is within limit
    
    def test_update_current_usage(self, controller, workspace_name):
        """Test updating current resource usage."""
        controller.set_resource_limit(workspace_name, ResourceType.MEMORY, 1000)
        controller.update_current_usage(workspace_name, ResourceType.MEMORY, 750)
        
        # Verify usage is tracked (indirectly through limit checking)
        # This would be more comprehensive with access to internal state


class TestCompositeAccessController:
    """Test CompositeAccessController."""
    
    @pytest.fixture
    def workspace_controller(self):
        """Create workspace access controller."""
        return WorkspaceAccessController()
    
    @pytest.fixture
    def rate_limit_controller(self):
        """Create rate limit controller."""
        return RateLimitController()
    
    @pytest.fixture
    def composite_controller(self, workspace_controller, rate_limit_controller):
        """Create composite access controller."""
        return CompositeAccessController([workspace_controller, rate_limit_controller])
    
    @pytest.fixture
    def workspace_name(self):
        """Test workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.fixture
    def access_request(self, workspace_name):
        """Create test access request."""
        return AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
    
    @pytest.mark.asyncio
    async def test_check_access_all_allow(self, composite_controller, access_request):
        """Test access allowed when all controllers allow."""
        result = await composite_controller.check_access(access_request)
        
        assert result.allowed is True
        assert result.reason == "Access granted by all controllers"
    
    @pytest.mark.asyncio
    async def test_check_access_one_denies(self, workspace_controller, rate_limit_controller, workspace_name):
        """Test access denied when one controller denies."""
        # Set up rate limit that will be exceeded
        rate_limit_controller.set_rate_limit(workspace_name, ResourceType.FILE, 0, 60)
        
        composite_controller = CompositeAccessController([workspace_controller, rate_limit_controller])
        
        request = AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
        
        result = await composite_controller.check_access(request)
        
        assert result.allowed is False
        assert "Rate limit exceeded" in result.reason
    
    @pytest.mark.asyncio
    async def test_enforce_limits_calls_all(self, composite_controller, access_request):
        """Test enforce limits calls all controllers."""
        # Should not raise any exceptions for valid request
        await composite_controller.enforce_limits(access_request)
    
    @pytest.mark.asyncio
    async def test_track_usage_calls_all(self, composite_controller, access_request):
        """Test track usage calls all controllers."""
        result = AccessResult(allowed=True, reason="test", access_level=AccessLevel.READ)
        await composite_controller.track_usage(access_request, result)


class TestAccessControlManager:
    """Test AccessControlManager."""
    
    @pytest.fixture
    def manager(self):
        """Create access control manager."""
        return AccessControlManager()
    
    @pytest.fixture
    def workspace_name(self):
        """Test workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.fixture
    def access_request(self, workspace_name):
        """Create test access request."""
        return AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
    
    @pytest.mark.asyncio
    async def test_check_access_default_controller(self, manager, access_request):
        """Test check access with default controller."""
        result = await manager.check_access(access_request)
        
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_check_access_specific_controller(self, manager, access_request):
        """Test check access with specific controller."""
        result = await manager.check_access(access_request, "workspace")
        
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_check_access_invalid_controller(self, manager, access_request):
        """Test check access with invalid controller ID."""
        with pytest.raises(Exception) as exc_info:
            await manager.check_access(access_request, "invalid")
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_enforce_access_success(self, manager, access_request):
        """Test enforce access succeeds for valid request."""
        # Should not raise any exceptions
        await manager.enforce_access(access_request)
    
    @pytest.mark.asyncio
    async def test_enforce_access_denied(self, manager, workspace_name):
        """Test enforce access raises exception when denied."""
        # Create request that will be denied
        allowed_workspaces = {WorkspaceName("other")}
        workspace_controller = WorkspaceAccessController(allowed_workspaces=allowed_workspaces)
        manager.register_controller("restricted", workspace_controller)
        
        request = AccessRequest(
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ,
            workspace_name=workspace_name
        )
        
        with pytest.raises(WorkspaceAccessDeniedError):
            await manager.enforce_access(request, "restricted")
    
    @pytest.mark.asyncio
    async def test_controlled_access_context_manager(self, manager, access_request):
        """Test controlled access context manager."""
        async with manager.controlled_access(access_request) as result:
            assert result.allowed is True
            assert isinstance(result, AccessResult)
    
    def test_register_controller(self, manager):
        """Test registering custom controller."""
        custom_controller = WorkspaceAccessController()
        manager.register_controller("custom", custom_controller)
        
        retrieved = manager.get_controller("custom")
        assert retrieved is custom_controller
    
    def test_get_controller(self, manager):
        """Test getting registered controller."""
        workspace_controller = manager.get_workspace_controller()
        assert isinstance(workspace_controller, WorkspaceAccessController)
        
        rate_limit_controller = manager.get_rate_limit_controller()
        assert isinstance(rate_limit_controller, RateLimitController)
        
        resource_limit_controller = manager.get_resource_limit_controller()
        assert isinstance(resource_limit_controller, ResourceLimitController)
    
    def test_get_nonexistent_controller(self, manager):
        """Test getting nonexistent controller returns None."""
        result = manager.get_controller("nonexistent")
        assert result is None


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def workspace_name(self):
        """Test workspace name."""
        return WorkspaceName("test-workspace")
    
    @pytest.mark.asyncio
    async def test_enforce_workspace_access(self, workspace_name):
        """Test enforce_workspace_access convenience function."""
        # Should not raise any exceptions for valid access
        await enforce_workspace_access(
            workspace_name=workspace_name,
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ
        )
    
    @pytest.mark.asyncio
    async def test_check_workspace_access(self, workspace_name):
        """Test check_workspace_access convenience function."""
        result = await check_workspace_access(
            workspace_name=workspace_name,
            resource_id="test-resource",
            resource_type=ResourceType.FILE,
            access_level=AccessLevel.READ
        )
        
        assert isinstance(result, AccessResult)
        assert result.allowed is True
    
    def test_get_access_control_manager(self):
        """Test get_access_control_manager returns manager instance."""
        manager = get_access_control_manager()
        assert isinstance(manager, AccessControlManager)
        
        # Should return same instance on subsequent calls
        manager2 = get_access_control_manager()
        assert manager is manager2


if __name__ == "__main__":
    pytest.main([__file__])