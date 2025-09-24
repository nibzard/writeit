"""Security integration module for WriteIt.

Provides unified security integration across all WriteIt components,
including access control, file system security, and audit logging.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, Union, TYPE_CHECKING

from ...domains.workspace.value_objects.workspace_name import WorkspaceName
if TYPE_CHECKING:
    from .storage_manager import LMDBStorageManager
from .access_control import (
    AccessLevel, 
    ResourceType, 
    get_access_control_manager,
    AccessRequest,
    WorkspaceAccessDeniedError
)
from .file_access_control import create_file_access_controller, FileAccessController
from ..persistence.secure_storage import create_secure_storage_manager, SecureStorageManager
from .security_audit import (
    SecurityEventType,
    SecurityEventSeverity,
    get_security_monitor,
    log_security_event
)
from ...shared.errors import SecurityError


class WorkspaceSecurityManager:
    """Comprehensive workspace security manager.
    
    Integrates all security components to provide unified security
    management for workspace operations.
    """
    
    def __init__(
        self,
        workspace_name: WorkspaceName,
        workspace_root: Path,
        user_id: Optional[str] = None,
        enforce_strict_isolation: bool = True
    ):
        """Initialize workspace security manager.
        
        Args:
            workspace_name: Name of the workspace
            workspace_root: Root directory of the workspace
            user_id: User identifier for security tracking
            enforce_strict_isolation: Whether to enforce strict workspace isolation
        """
        self.workspace_name = workspace_name
        self.workspace_root = workspace_root
        self.user_id = user_id
        self.enforce_strict_isolation = enforce_strict_isolation
        
        # Initialize security components
        self._access_manager = get_access_control_manager()
        self._security_monitor = get_security_monitor()
        self._file_controller = create_file_access_controller(workspace_name, workspace_root)
        
        # Configure workspace-specific access controls
        self._configure_workspace_access_controls()
    
    def _configure_workspace_access_controls(self) -> None:
        """Configure workspace-specific access controls."""
        workspace_controller = self._access_manager.get_workspace_controller()
        rate_limit_controller = self._access_manager.get_rate_limit_controller()
        resource_limit_controller = self._access_manager.get_resource_limit_controller()
        
        # Set workspace restrictions
        workspace_controller.set_workspace_restrictions(
            self.workspace_name,
            {
                'max_access_level': AccessLevel.FULL,
                'read_only': False,
                'allow_dangerous_operations': False,
                'enforce_file_restrictions': True
            }
        )
        
        # Set rate limits
        rate_limit_controller.set_rate_limit(
            self.workspace_name,
            ResourceType.FILE,
            max_requests=1000,  # 1000 file operations per hour
            window_seconds=3600
        )
        
        rate_limit_controller.set_rate_limit(
            self.workspace_name,
            ResourceType.DATABASE,
            max_requests=10000,  # 10000 DB operations per hour
            window_seconds=3600
        )
        
        # Set resource limits
        resource_limit_controller.set_resource_limit(
            self.workspace_name,
            ResourceType.MEMORY,
            max_value=500 * 1024 * 1024  # 500MB memory limit
        )
        
        resource_limit_controller.set_resource_limit(
            self.workspace_name,
            ResourceType.FILE,
            max_value=100  # 100 concurrent file handles
        )
    
    async def create_secure_storage(
        self,
        workspace_manager=None,
        map_size_mb: int = 100,
        max_dbs: int = 10
    ) -> SecureStorageManager:
        """Create a secure storage manager for this workspace.
        
        Args:
            workspace_manager: Workspace manager instance
            map_size_mb: Initial LMDB map size in megabytes
            max_dbs: Maximum number of named databases
            
        Returns:
            Secure storage manager instance
        """
        # Log storage access
        await log_security_event(
            SecurityEventType.ACCESS_GRANTED,
            f"Secure storage access granted for workspace '{self.workspace_name}'",
            SecurityEventSeverity.LOW,
            workspace_name=self.workspace_name,
            user_id=self.user_id,
            resource_id="storage",
            details={"map_size_mb": map_size_mb, "max_dbs": max_dbs}
        )
        
        # Create secure storage manager using infrastructure layer
        from ..persistence.secure_storage import create_secure_storage_manager
        return await create_secure_storage_manager(
            workspace_name=self.workspace_name,
            workspace_manager=workspace_manager,
            user_id=self.user_id,
            enforce_isolation=self.enforce_strict_isolation,
            map_size_mb=map_size_mb,
            max_dbs=max_dbs
        )
    
    def get_file_controller(self) -> FileAccessController:
        """Get the file access controller for this workspace.
        
        Returns:
            File access controller instance
        """
        return self._file_controller
    
    @asynccontextmanager
    async def secure_file_operation(
        self,
        operation_type: str,
        file_path: Union[str, Path],
        access_level: AccessLevel = AccessLevel.READ
    ) -> AsyncGenerator[FileAccessController, None]:
        """Context manager for secure file operations.
        
        Args:
            operation_type: Type of operation (read, write, create, delete)
            file_path: Path to file
            access_level: Required access level
            
        Yields:
            File access controller
        """
        # Create access request
        request = AccessRequest(
            resource_id=str(file_path),
            resource_type=ResourceType.FILE,
            access_level=access_level,
            workspace_name=self.workspace_name,
            user_id=self.user_id,
            metadata={"operation_type": operation_type}
        )
        
        try:
            # Check and enforce access
            async with self._access_manager.controlled_access(request):
                # Log successful access
                await log_security_event(
                    SecurityEventType.ACCESS_GRANTED,
                    f"File {operation_type} access granted: {file_path}",
                    SecurityEventSeverity.LOW,
                    workspace_name=self.workspace_name,
                    user_id=self.user_id,
                    resource_id=str(file_path),
                    details={"operation": operation_type, "access_level": access_level.value}
                )
                
                yield self._file_controller
                
        except WorkspaceAccessDeniedError as e:
            # Log access denial
            await log_security_event(
                SecurityEventType.ACCESS_DENIED,
                f"File {operation_type} access denied: {file_path} - {e.reason}",
                SecurityEventSeverity.MEDIUM,
                workspace_name=self.workspace_name,
                user_id=self.user_id,
                resource_id=str(file_path),
                details={"operation": operation_type, "reason": e.reason}
            )
            raise
        except Exception as e:
            # Log unexpected errors
            await log_security_event(
                SecurityEventType.SECURITY_POLICY_VIOLATION,
                f"Unexpected error during file {operation_type}: {file_path} - {e}",
                SecurityEventSeverity.HIGH,
                workspace_name=self.workspace_name,
                user_id=self.user_id,
                resource_id=str(file_path),
                details={"operation": operation_type, "error": str(e)}
            )
            raise
    
    async def validate_workspace_security(self) -> Dict[str, Any]:
        """Validate workspace security configuration and health.
        
        Returns:
            Dictionary with security validation results
        """
        results = {
            'workspace_name': str(self.workspace_name),
            'security_status': 'unknown',
            'issues': [],
            'recommendations': [],
            'metrics': {}
        }
        
        try:
            # Check workspace directory security
            if not self.workspace_root.exists():
                results['issues'].append("Workspace directory does not exist")
                results['recommendations'].append("Create workspace directory with secure permissions")
            else:
                # Check permissions
                stat_info = self.workspace_root.stat()
                permissions = oct(stat_info.st_mode)[-3:]
                
                if permissions != '700':  # Should be owner-only access
                    results['issues'].append(f"Workspace directory has insecure permissions: {permissions}")
                    results['recommendations'].append("Set workspace directory permissions to 700 (owner only)")
            
            # Check access control configuration
            workspace_controller = self._access_manager.get_workspace_controller()
            restrictions = workspace_controller.get_workspace_restrictions(self.workspace_name)
            
            if not restrictions:
                results['issues'].append("No access control restrictions configured")
                results['recommendations'].append("Configure workspace access control restrictions")
            
            # Get security health metrics
            health_metrics = await self._security_monitor.check_workspace_security_health(
                self.workspace_name
            )
            results['metrics'] = health_metrics
            
            # Determine overall security status
            if not results['issues']:
                if health_metrics['security_score'] >= 90:
                    results['security_status'] = 'excellent'
                elif health_metrics['security_score'] >= 75:
                    results['security_status'] = 'good'
                else:
                    results['security_status'] = 'fair'
            else:
                results['security_status'] = 'poor'
            
            # Log security validation
            await log_security_event(
                SecurityEventType.ACCESS_GRANTED,
                f"Security validation completed for workspace '{self.workspace_name}'",
                SecurityEventSeverity.LOW,
                workspace_name=self.workspace_name,
                user_id=self.user_id,
                details=results
            )
            
        except Exception as e:
            results['security_status'] = 'error'
            results['issues'].append(f"Security validation failed: {e}")
            
            await log_security_event(
                SecurityEventType.SECURITY_POLICY_VIOLATION,
                f"Security validation error for workspace '{self.workspace_name}': {e}",
                SecurityEventSeverity.HIGH,
                workspace_name=self.workspace_name,
                user_id=self.user_id,
                details={"error": str(e)}
            )
        
        return results
    
    async def configure_rate_limits(
        self,
        file_operations_per_hour: int = 1000,
        database_operations_per_hour: int = 10000
    ) -> None:
        """Configure rate limits for the workspace.
        
        Args:
            file_operations_per_hour: Maximum file operations per hour
            database_operations_per_hour: Maximum database operations per hour
        """
        rate_limit_controller = self._access_manager.get_rate_limit_controller()
        
        rate_limit_controller.set_rate_limit(
            self.workspace_name,
            ResourceType.FILE,
            max_requests=file_operations_per_hour,
            window_seconds=3600
        )
        
        rate_limit_controller.set_rate_limit(
            self.workspace_name,
            ResourceType.DATABASE,
            max_requests=database_operations_per_hour,
            window_seconds=3600
        )
        
        await log_security_event(
            SecurityEventType.ACCESS_GRANTED,
            f"Rate limits configured for workspace '{self.workspace_name}'",
            SecurityEventSeverity.LOW,
            workspace_name=self.workspace_name,
            user_id=self.user_id,
            details={
                "file_operations_per_hour": file_operations_per_hour,
                "database_operations_per_hour": database_operations_per_hour
            }
        )
    
    async def configure_resource_limits(
        self,
        memory_limit_mb: int = 500,
        max_concurrent_files: int = 100
    ) -> None:
        """Configure resource limits for the workspace.
        
        Args:
            memory_limit_mb: Maximum memory usage in megabytes
            max_concurrent_files: Maximum concurrent file handles
        """
        resource_limit_controller = self._access_manager.get_resource_limit_controller()
        
        resource_limit_controller.set_resource_limit(
            self.workspace_name,
            ResourceType.MEMORY,
            max_value=memory_limit_mb * 1024 * 1024
        )
        
        resource_limit_controller.set_resource_limit(
            self.workspace_name,
            ResourceType.FILE,
            max_value=max_concurrent_files
        )
        
        await log_security_event(
            SecurityEventType.ACCESS_GRANTED,
            f"Resource limits configured for workspace '{self.workspace_name}'",
            SecurityEventSeverity.LOW,
            workspace_name=self.workspace_name,
            user_id=self.user_id,
            details={
                "memory_limit_mb": memory_limit_mb,
                "max_concurrent_files": max_concurrent_files
            }
        )
    
    async def get_security_summary(self) -> Dict[str, Any]:
        """Get a summary of workspace security status.
        
        Returns:
            Dictionary with security summary
        """
        validation_results = await self.validate_workspace_security()
        
        return {
            'workspace_name': str(self.workspace_name),
            'security_status': validation_results['security_status'],
            'security_score': validation_results['metrics'].get('security_score', 0),
            'total_security_events': validation_results['metrics'].get('total_events', 0),
            'issues_count': len(validation_results['issues']),
            'recommendations_count': len(validation_results['recommendations']),
            'isolation_enforced': self.enforce_strict_isolation,
            'last_validation': validation_results['metrics'].get('last_update', 0)
        }


async def create_workspace_security_manager(
    workspace_name: Union[WorkspaceName, str],
    workspace_root: Union[str, Path],
    user_id: Optional[str] = None,
    enforce_strict_isolation: bool = True
) -> WorkspaceSecurityManager:
    """Create a workspace security manager.
    
    Args:
        workspace_name: Name of the workspace
        workspace_root: Root directory of the workspace
        user_id: User identifier for security tracking
        enforce_strict_isolation: Whether to enforce strict workspace isolation
        
    Returns:
        Configured workspace security manager
    """
    if isinstance(workspace_name, str):
        workspace_name = WorkspaceName(workspace_name)
    
    if isinstance(workspace_root, str):
        workspace_root = Path(workspace_root)
    
    manager = WorkspaceSecurityManager(
        workspace_name=workspace_name,
        workspace_root=workspace_root,
        user_id=user_id,
        enforce_strict_isolation=enforce_strict_isolation
    )
    
    # Log security manager creation
    await log_security_event(
        SecurityEventType.ACCESS_GRANTED,
        f"Workspace security manager created for '{workspace_name}'",
        SecurityEventSeverity.LOW,
        workspace_name=workspace_name,
        user_id=user_id,
        details={
            "workspace_root": str(workspace_root),
            "strict_isolation": enforce_strict_isolation
        }
    )
    
    return manager


# Convenience functions for common security operations

async def secure_workspace_operation(
    workspace_name: Union[WorkspaceName, str],
    operation_name: str,
    user_id: Optional[str] = None
) -> None:
    """Log a secure workspace operation.
    
    Args:
        workspace_name: Workspace name
        operation_name: Name of the operation
        user_id: User identifier
    """
    if isinstance(workspace_name, str):
        workspace_name = WorkspaceName(workspace_name)
    
    await log_security_event(
        SecurityEventType.ACCESS_GRANTED,
        f"Workspace operation '{operation_name}' completed successfully",
        SecurityEventSeverity.LOW,
        workspace_name=workspace_name,
        user_id=user_id,
        details={"operation": operation_name}
    )


async def report_security_violation(
    workspace_name: Union[WorkspaceName, str],
    violation_type: str,
    description: str,
    user_id: Optional[str] = None,
    severity: SecurityEventSeverity = SecurityEventSeverity.HIGH
) -> None:
    """Report a security violation.
    
    Args:
        workspace_name: Workspace name
        violation_type: Type of violation
        description: Description of the violation
        user_id: User identifier
        severity: Severity of the violation
    """
    if isinstance(workspace_name, str):
        workspace_name = WorkspaceName(workspace_name)
    
    await log_security_event(
        SecurityEventType.SECURITY_POLICY_VIOLATION,
        f"Security violation: {violation_type} - {description}",
        severity,
        workspace_name=workspace_name,
        user_id=user_id,
        details={"violation_type": violation_type, "description": description}
    )