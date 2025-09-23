"""Access control infrastructure for WriteIt.

Provides comprehensive access control mechanisms including workspace isolation,
file system restrictions, rate limiting, and resource usage controls.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.errors import DomainError


class AccessLevel(Enum):
    """Access level enumeration."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    FULL = "full"


class ResourceType(Enum):
    """Resource type enumeration."""
    FILE = "file"
    DIRECTORY = "directory"
    DATABASE = "database"
    MEMORY = "memory"
    NETWORK = "network"
    CPU = "cpu"


@dataclass
class AccessRequest:
    """Access request information."""
    resource_id: str
    resource_type: ResourceType
    access_level: AccessLevel
    workspace_name: WorkspaceName
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessResult:
    """Access control result."""
    allowed: bool
    reason: str
    access_level: AccessLevel = AccessLevel.NONE
    restrictions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[float] = None


@dataclass
class ResourceLimit:
    """Resource usage limit definition."""
    resource_type: ResourceType
    max_value: Union[int, float]
    window_seconds: Optional[float] = None
    burst_limit: Optional[Union[int, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    resource_type: ResourceType
    current_value: Union[int, float]
    max_value: Union[int, float]
    usage_percentage: float
    window_start: float
    last_updated: float = field(default_factory=time.time)


class AccessControlError(DomainError):
    """Base exception for access control errors."""
    pass


class WorkspaceAccessDeniedError(AccessControlError):
    """Raised when workspace access is denied."""
    
    def __init__(self, workspace_name: WorkspaceName, resource_id: str, reason: str):
        super().__init__(f"Access denied to workspace '{workspace_name}' resource '{resource_id}': {reason}")
        self.workspace_name = workspace_name
        self.resource_id = resource_id
        self.reason = reason


class ResourceLimitExceededError(AccessControlError):
    """Raised when resource limits are exceeded."""
    
    def __init__(self, resource_type: ResourceType, current: Union[int, float], limit: Union[int, float]):
        super().__init__(f"Resource limit exceeded for {resource_type.value}: {current} > {limit}")
        self.resource_type = resource_type
        self.current = current
        self.limit = limit


class RateLimitExceededError(AccessControlError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, resource_id: str, limit: int, window_seconds: float):
        super().__init__(f"Rate limit exceeded for '{resource_id}': {limit} requests per {window_seconds}s")
        self.resource_id = resource_id
        self.limit = limit
        self.window_seconds = window_seconds


class IAccessController(ABC):
    """Interface for access control implementations."""
    
    @abstractmethod
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """Check if access is allowed for the given request."""
        pass
    
    @abstractmethod
    async def enforce_limits(self, request: AccessRequest) -> None:
        """Enforce resource limits for the request."""
        pass
    
    @abstractmethod
    async def track_usage(self, request: AccessRequest, result: AccessResult) -> None:
        """Track resource usage for the request."""
        pass


class WorkspaceAccessController(IAccessController):
    """Workspace-aware access controller."""
    
    def __init__(
        self,
        allowed_workspaces: Optional[Set[WorkspaceName]] = None,
        default_access_level: AccessLevel = AccessLevel.READ
    ):
        """Initialize workspace access controller.
        
        Args:
            allowed_workspaces: Set of allowed workspace names. None means all workspaces allowed.
            default_access_level: Default access level for allowed workspaces
        """
        self._allowed_workspaces = allowed_workspaces
        self._default_access_level = default_access_level
        self._workspace_restrictions: Dict[WorkspaceName, Dict[str, Any]] = {}
        
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """Check workspace access permissions."""
        # Check if workspace is allowed
        if (self._allowed_workspaces is not None and 
            request.workspace_name not in self._allowed_workspaces):
            return AccessResult(
                allowed=False,
                reason=f"Workspace '{request.workspace_name}' not in allowed list",
                access_level=AccessLevel.NONE
            )
        
        # Check workspace-specific restrictions
        restrictions = self._workspace_restrictions.get(request.workspace_name, {})
        
        # Check access level
        max_allowed_level = restrictions.get('max_access_level', self._default_access_level)
        if request.access_level.value > max_allowed_level.value:
            return AccessResult(
                allowed=False,
                reason=f"Requested access level '{request.access_level.value}' exceeds maximum '{max_allowed_level.value}'",
                access_level=AccessLevel.NONE
            )
        
        # Check resource-specific restrictions
        if request.resource_type == ResourceType.FILE:
            if not await self._check_file_access(request):
                return AccessResult(
                    allowed=False,
                    reason="File access denied by workspace policy",
                    access_level=AccessLevel.NONE
                )
        
        return AccessResult(
            allowed=True,
            reason="Access granted",
            access_level=request.access_level,
            restrictions=restrictions
        )
    
    async def enforce_limits(self, request: AccessRequest) -> None:
        """Enforce workspace-specific limits."""
        restrictions = self._workspace_restrictions.get(request.workspace_name, {})
        
        # Check if workspace is in read-only mode
        if restrictions.get('read_only', False) and request.access_level in (AccessLevel.WRITE, AccessLevel.ADMIN, AccessLevel.FULL):
            raise WorkspaceAccessDeniedError(
                request.workspace_name,
                request.resource_id,
                "Workspace is in read-only mode"
            )
    
    async def track_usage(self, request: AccessRequest, result: AccessResult) -> None:
        """Track workspace access patterns."""
        # Implementation would track access patterns for monitoring
        pass
    
    async def _check_file_access(self, request: AccessRequest) -> bool:
        """Check file access within workspace boundaries."""
        try:
            # Ensure file path is within workspace
            resource_path = Path(request.resource_id)
            workspace_path = Path(f"~/.writeit/workspaces/{request.workspace_name}").expanduser()
            
            # Resolve to absolute paths
            resource_abs = resource_path.resolve()
            workspace_abs = workspace_path.resolve()
            
            # Check if resource is within workspace
            try:
                resource_abs.relative_to(workspace_abs)
                return True
            except ValueError:
                # Path is outside workspace
                return False
                
        except (OSError, ValueError):
            # Invalid path
            return False
    
    def set_workspace_restrictions(
        self, 
        workspace_name: WorkspaceName, 
        restrictions: Dict[str, Any]
    ) -> None:
        """Set restrictions for a specific workspace."""
        self._workspace_restrictions[workspace_name] = restrictions
    
    def get_workspace_restrictions(self, workspace_name: WorkspaceName) -> Dict[str, Any]:
        """Get restrictions for a specific workspace."""
        return self._workspace_restrictions.get(workspace_name, {})


class RateLimitController(IAccessController):
    """Rate limiting access controller."""
    
    def __init__(self):
        """Initialize rate limit controller."""
        self._limits: Dict[str, ResourceLimit] = {}
        self._usage_tracking: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """Check rate limits for the request."""
        limit_key = f"{request.workspace_name}:{request.resource_type.value}"
        
        if limit_key not in self._limits:
            # No rate limit configured
            return AccessResult(
                allowed=True,
                reason="No rate limit configured",
                access_level=request.access_level
            )
        
        limit = self._limits[limit_key]
        current_time = time.time()
        
        async with self._lock:
            # Clean old entries
            if limit_key in self._usage_tracking:
                window_start = current_time - (limit.window_seconds or 3600)
                self._usage_tracking[limit_key] = [
                    t for t in self._usage_tracking[limit_key] if t >= window_start
                ]
            else:
                self._usage_tracking[limit_key] = []
            
            current_usage = len(self._usage_tracking[limit_key])
            
            if current_usage >= limit.max_value:
                return AccessResult(
                    allowed=False,
                    reason=f"Rate limit exceeded: {current_usage}/{limit.max_value} in {limit.window_seconds}s",
                    access_level=AccessLevel.NONE
                )
            
            return AccessResult(
                allowed=True,
                reason="Rate limit OK",
                access_level=request.access_level,
                restrictions={"rate_limit": {"current": current_usage, "max": limit.max_value}}
            )
    
    async def enforce_limits(self, request: AccessRequest) -> None:
        """Enforce rate limits."""
        result = await self.check_access(request)
        if not result.allowed:
            limit_key = f"{request.workspace_name}:{request.resource_type.value}"
            limit = self._limits[limit_key]
            raise RateLimitExceededError(
                request.resource_id,
                int(limit.max_value),
                limit.window_seconds or 3600
            )
    
    async def track_usage(self, request: AccessRequest, result: AccessResult) -> None:
        """Track rate limit usage."""
        if result.allowed:
            limit_key = f"{request.workspace_name}:{request.resource_type.value}"
            current_time = time.time()
            
            async with self._lock:
                if limit_key not in self._usage_tracking:
                    self._usage_tracking[limit_key] = []
                self._usage_tracking[limit_key].append(current_time)
    
    def set_rate_limit(
        self, 
        workspace_name: WorkspaceName, 
        resource_type: ResourceType,
        max_requests: int,
        window_seconds: float = 3600
    ) -> None:
        """Set rate limit for a workspace and resource type."""
        limit_key = f"{workspace_name}:{resource_type.value}"
        self._limits[limit_key] = ResourceLimit(
            resource_type=resource_type,
            max_value=max_requests,
            window_seconds=window_seconds
        )
    
    def get_current_usage(self, workspace_name: WorkspaceName, resource_type: ResourceType) -> int:
        """Get current usage count for a workspace and resource type."""
        limit_key = f"{workspace_name}:{resource_type.value}"
        return len(self._usage_tracking.get(limit_key, []))


class ResourceLimitController(IAccessController):
    """Resource usage limit controller."""
    
    def __init__(self):
        """Initialize resource limit controller."""
        self._limits: Dict[str, ResourceLimit] = {}
        self._current_usage: Dict[str, ResourceUsage] = {}
        self._lock = asyncio.Lock()
    
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """Check resource limits for the request."""
        limit_key = f"{request.workspace_name}:{request.resource_type.value}"
        
        if limit_key not in self._limits:
            return AccessResult(
                allowed=True,
                reason="No resource limit configured",
                access_level=request.access_level
            )
        
        limit = self._limits[limit_key]
        usage = self._current_usage.get(limit_key)
        
        if not usage:
            return AccessResult(
                allowed=True,
                reason="No current usage tracked",
                access_level=request.access_level
            )
        
        if usage.current_value >= limit.max_value:
            return AccessResult(
                allowed=False,
                reason=f"Resource limit exceeded: {usage.current_value}/{limit.max_value}",
                access_level=AccessLevel.NONE
            )
        
        return AccessResult(
            allowed=True,
            reason="Resource limit OK",
            access_level=request.access_level,
            restrictions={"resource_limit": {"current": usage.current_value, "max": limit.max_value}}
        )
    
    async def enforce_limits(self, request: AccessRequest) -> None:
        """Enforce resource limits."""
        result = await self.check_access(request)
        if not result.allowed:
            limit_key = f"{request.workspace_name}:{request.resource_type.value}"
            limit = self._limits[limit_key]
            usage = self._current_usage[limit_key]
            raise ResourceLimitExceededError(
                request.resource_type,
                usage.current_value,
                limit.max_value
            )
    
    async def track_usage(self, request: AccessRequest, result: AccessResult) -> None:
        """Track resource usage."""
        # Implementation would update current usage based on operation
        pass
    
    def set_resource_limit(
        self,
        workspace_name: WorkspaceName,
        resource_type: ResourceType,
        max_value: Union[int, float]
    ) -> None:
        """Set resource limit for a workspace and resource type."""
        limit_key = f"{workspace_name}:{resource_type.value}"
        self._limits[limit_key] = ResourceLimit(
            resource_type=resource_type,
            max_value=max_value
        )
    
    def update_current_usage(
        self,
        workspace_name: WorkspaceName,
        resource_type: ResourceType,
        current_value: Union[int, float]
    ) -> None:
        """Update current resource usage."""
        limit_key = f"{workspace_name}:{resource_type.value}"
        limit = self._limits.get(limit_key)
        
        if limit:
            self._current_usage[limit_key] = ResourceUsage(
                resource_type=resource_type,
                current_value=current_value,
                max_value=limit.max_value,
                usage_percentage=(current_value / limit.max_value) * 100,
                window_start=time.time()
            )


class CompositeAccessController(IAccessController):
    """Composite access controller that combines multiple controllers."""
    
    def __init__(self, controllers: List[IAccessController]):
        """Initialize composite controller.
        
        Args:
            controllers: List of access controllers to combine
        """
        self._controllers = controllers
    
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """Check access using all controllers."""
        for controller in self._controllers:
            result = await controller.check_access(request)
            if not result.allowed:
                return result
        
        return AccessResult(
            allowed=True,
            reason="Access granted by all controllers",
            access_level=request.access_level
        )
    
    async def enforce_limits(self, request: AccessRequest) -> None:
        """Enforce limits using all controllers."""
        for controller in self._controllers:
            await controller.enforce_limits(request)
    
    async def track_usage(self, request: AccessRequest, result: AccessResult) -> None:
        """Track usage using all controllers."""
        for controller in self._controllers:
            await controller.track_usage(request, result)


class AccessControlManager:
    """Central access control manager."""
    
    def __init__(self):
        """Initialize access control manager."""
        self._controllers: Dict[str, IAccessController] = {}
        self._default_controller_id = "default"
        
        # Set up default controllers
        self._setup_default_controllers()
    
    def _setup_default_controllers(self) -> None:
        """Set up default access controllers."""
        workspace_controller = WorkspaceAccessController()
        rate_limit_controller = RateLimitController()
        resource_limit_controller = ResourceLimitController()
        
        # Create composite controller with all default controllers
        composite_controller = CompositeAccessController([
            workspace_controller,
            rate_limit_controller,
            resource_limit_controller
        ])
        
        self._controllers[self._default_controller_id] = composite_controller
        self._controllers["workspace"] = workspace_controller
        self._controllers["rate_limit"] = rate_limit_controller
        self._controllers["resource_limit"] = resource_limit_controller
    
    async def check_access(
        self, 
        request: AccessRequest, 
        controller_id: Optional[str] = None
    ) -> AccessResult:
        """Check access using specified or default controller."""
        controller = self._controllers.get(controller_id or self._default_controller_id)
        if not controller:
            raise AccessControlError(f"Access controller '{controller_id}' not found")
        
        return await controller.check_access(request)
    
    async def enforce_access(
        self, 
        request: AccessRequest, 
        controller_id: Optional[str] = None
    ) -> None:
        """Enforce access control for the request."""
        controller = self._controllers.get(controller_id or self._default_controller_id)
        if not controller:
            raise AccessControlError(f"Access controller '{controller_id}' not found")
        
        # Check access first
        result = await controller.check_access(request)
        if not result.allowed:
            raise WorkspaceAccessDeniedError(
                request.workspace_name,
                request.resource_id,
                result.reason
            )
        
        # Enforce limits
        await controller.enforce_limits(request)
        
        # Track usage
        await controller.track_usage(request, result)
    
    @asynccontextmanager
    async def controlled_access(
        self,
        request: AccessRequest,
        controller_id: Optional[str] = None
    ) -> AsyncGenerator[AccessResult, None]:
        """Context manager for controlled access operations."""
        # Enforce access before entering context
        await self.enforce_access(request, controller_id)
        
        # Get access result for context
        controller = self._controllers.get(controller_id or self._default_controller_id)
        result = await controller.check_access(request)
        
        try:
            yield result
        finally:
            # Track completion
            await controller.track_usage(request, result)
    
    def register_controller(self, controller_id: str, controller: IAccessController) -> None:
        """Register a custom access controller."""
        self._controllers[controller_id] = controller
    
    def get_controller(self, controller_id: str) -> Optional[IAccessController]:
        """Get a registered access controller."""
        return self._controllers.get(controller_id)
    
    def get_workspace_controller(self) -> WorkspaceAccessController:
        """Get the workspace access controller."""
        return self._controllers["workspace"]
    
    def get_rate_limit_controller(self) -> RateLimitController:
        """Get the rate limit controller."""
        return self._controllers["rate_limit"]
    
    def get_resource_limit_controller(self) -> ResourceLimitController:
        """Get the resource limit controller."""
        return self._controllers["resource_limit"]


# Global access control manager instance
_access_control_manager: Optional[AccessControlManager] = None


def get_access_control_manager() -> AccessControlManager:
    """Get or create the global access control manager."""
    global _access_control_manager
    if _access_control_manager is None:
        _access_control_manager = AccessControlManager()
    return _access_control_manager


async def enforce_workspace_access(
    workspace_name: WorkspaceName,
    resource_id: str,
    resource_type: ResourceType,
    access_level: AccessLevel,
    user_id: Optional[str] = None
) -> None:
    """Convenience function to enforce workspace access."""
    request = AccessRequest(
        resource_id=resource_id,
        resource_type=resource_type,
        access_level=access_level,
        workspace_name=workspace_name,
        user_id=user_id
    )
    
    manager = get_access_control_manager()
    await manager.enforce_access(request)


async def check_workspace_access(
    workspace_name: WorkspaceName,
    resource_id: str,
    resource_type: ResourceType,
    access_level: AccessLevel,
    user_id: Optional[str] = None
) -> AccessResult:
    """Convenience function to check workspace access."""
    request = AccessRequest(
        resource_id=resource_id,
        resource_type=resource_type,
        access_level=access_level,
        workspace_name=workspace_name,
        user_id=user_id
    )
    
    manager = get_access_control_manager()
    return await manager.check_access(request)