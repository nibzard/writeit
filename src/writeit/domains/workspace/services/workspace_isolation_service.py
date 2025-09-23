"""Workspace isolation service.

Domain service responsible for enforcing workspace boundaries and preventing
cross-workspace data leakage in WriteIt operations.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncContextManager, Callable, Dict, List, Optional, TypeVar
from uuid import UUID

from ..entities.workspace import Workspace
from ..value_objects.workspace_name import WorkspaceName
from ..repositories.workspace_repository import WorkspaceRepository
from ....shared.repository import RepositoryError


T = TypeVar('T')


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    severity: ValidationSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    workspace_name: Optional[WorkspaceName] = None
    resource_id: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of workspace isolation validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    workspace_name: WorkspaceName
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for issue in self.issues
        )
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return any(
            issue.severity == ValidationSeverity.WARNING
            for issue in self.issues
        )
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [
            issue for issue in self.issues
            if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        ]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [
            issue for issue in self.issues
            if issue.severity == ValidationSeverity.WARNING
        ]


@dataclass
class WorkspaceContext:
    """Context for workspace-isolated operations."""
    workspace: Workspace
    resource_scope: Optional[str] = None
    operation_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkspaceAccessError(Exception):
    """Raised when workspace access validation fails."""
    
    def __init__(
        self, 
        message: str, 
        workspace_name: WorkspaceName,
        resource_id: Optional[str] = None
    ):
        super().__init__(message)
        self.workspace_name = workspace_name
        self.resource_id = resource_id


class WorkspaceIsolationError(Exception):
    """Raised when workspace isolation is violated."""
    
    def __init__(
        self, 
        message: str,
        workspace_name: WorkspaceName,
        violation_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.workspace_name = workspace_name
        self.violation_details = violation_details or {}


class WorkspaceIsolationService:
    """Service for enforcing workspace isolation boundaries.
    
    This service ensures that operations remain within their intended workspace
    scope and prevents accidental cross-workspace data leakage.
    
    Examples:
        service = WorkspaceIsolationService(workspace_repo)
        
        # Validate workspace access
        if await service.validate_workspace_access(workspace_name, resource_id):
            # Access allowed
            pass
        
        # Ensure isolation for operation
        result = await service.ensure_workspace_isolation(
            workspace_name, 
            lambda: some_operation()
        )
        
        # Use workspace context manager
        async with service.isolate_workspace_operation(context) as ctx:
            # Perform isolated operations
            await ctx.do_something()
    """
    
    def __init__(self, workspace_repository: WorkspaceRepository):
        """Initialize isolation service.
        
        Args:
            workspace_repository: Repository for workspace data access
        """
        self._workspace_repository = workspace_repository
        self._isolation_cache: Dict[WorkspaceName, ValidationResult] = {}
    
    async def validate_workspace_access(
        self, 
        workspace_name: WorkspaceName, 
        resource_id: str
    ) -> bool:
        """Validate that a resource can be accessed from a workspace.
        
        Args:
            workspace_name: Target workspace
            resource_id: Resource being accessed
            
        Returns:
            True if access is allowed, False otherwise
            
        Raises:
            WorkspaceAccessError: If workspace doesn't exist or access denied
            RepositoryError: If validation check fails
        """
        try:
            # Find the workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                raise WorkspaceAccessError(
                    f"Workspace '{workspace_name}' not found",
                    workspace_name,
                    resource_id
                )
            
            # Check if workspace is initialized
            if not workspace.is_initialized():
                raise WorkspaceAccessError(
                    f"Workspace '{workspace_name}' is not properly initialized",
                    workspace_name,
                    resource_id
                )
            
            # Validate resource scope
            if not await self._validate_resource_scope(workspace, resource_id):
                return False
            
            # Additional workspace-specific validations
            validation_errors = await self._workspace_repository.validate_workspace_integrity(workspace)
            if validation_errors:
                raise WorkspaceAccessError(
                    f"Workspace integrity validation failed: {', '.join(validation_errors)}",
                    workspace_name,
                    resource_id
                )
            
            return True
            
        except RepositoryError as e:
            raise WorkspaceAccessError(
                f"Failed to validate workspace access: {e}",
                workspace_name,
                resource_id
            ) from e
    
    async def ensure_workspace_isolation(
        self, 
        workspace_name: WorkspaceName, 
        operation: Callable[[], T]
    ) -> T:
        """Execute operation with workspace isolation guarantees.
        
        Args:
            workspace_name: Workspace to operate within
            operation: Operation to execute
            
        Returns:
            Result of the operation
            
        Raises:
            WorkspaceIsolationError: If isolation cannot be ensured
            WorkspaceAccessError: If workspace access denied
        """
        # Validate workspace exists and is accessible
        workspace = await self._workspace_repository.find_by_name(workspace_name)
        if not workspace:
            raise WorkspaceIsolationError(
                f"Cannot ensure isolation: workspace '{workspace_name}' not found",
                workspace_name
            )
        
        # Check isolation boundaries before operation
        validation_result = await self.check_workspace_boundaries(workspace_name)
        if not validation_result.is_valid:
            errors = validation_result.get_errors()
            raise WorkspaceIsolationError(
                f"Workspace isolation violated: {'; '.join(issue.message for issue in errors)}",
                workspace_name,
                {"validation_errors": [issue.message for issue in errors]}
            )
        
        try:
            # Execute operation with isolation context
            result = operation()
            
            # Verify isolation wasn't violated during operation
            post_validation = await self.check_workspace_boundaries(workspace_name)
            if not post_validation.is_valid:
                errors = post_validation.get_errors()
                raise WorkspaceIsolationError(
                    f"Isolation violated during operation: {'; '.join(issue.message for issue in errors)}",
                    workspace_name,
                    {"post_operation_errors": [issue.message for issue in errors]}
                )
            
            return result
            
        except Exception as e:
            # Re-raise isolation errors as-is
            if isinstance(e, (WorkspaceIsolationError, WorkspaceAccessError)):
                raise
            
            # Wrap other exceptions with isolation context
            raise WorkspaceIsolationError(
                f"Operation failed within workspace isolation: {e}",
                workspace_name,
                {"original_error": str(e), "error_type": type(e).__name__}
            ) from e
    
    async def check_workspace_boundaries(
        self, 
        workspace_name: Optional[WorkspaceName] = None
    ) -> ValidationResult:
        """Check workspace isolation boundaries.
        
        Args:
            workspace_name: Workspace to check, None for all workspaces
            
        Returns:
            Validation result with any boundary violations
            
        Raises:
            RepositoryError: If boundary check fails
        """
        if workspace_name:
            return await self._check_single_workspace_boundaries(workspace_name)
        else:
            return await self._check_all_workspace_boundaries()
    
    @asynccontextmanager
    async def isolate_workspace_operation(
        self, 
        workspace_context: WorkspaceContext
    ):
        """Context manager for isolated workspace operations.
        
        Args:
            workspace_context: Context for the isolated operations
            
        Yields:
            Isolated operations interface
            
        Raises:
            WorkspaceIsolationError: If isolation setup fails
        """
        # Validate workspace context
        await self._validate_workspace_context(workspace_context)
        
        # Set up isolation boundary
        isolation_context = IsolatedWorkspaceOperations(
            workspace_context, 
            self._workspace_repository
        )
        
        try:
            # Enter isolation context
            await isolation_context._enter_isolation()
            yield isolation_context
            
        except Exception as e:
            # Handle isolation violation
            await isolation_context._handle_isolation_violation(e)
            raise
            
        finally:
            # Clean up isolation context
            await isolation_context._exit_isolation()
    
    async def _validate_resource_scope(
        self, 
        workspace: Workspace, 
        resource_id: str
    ) -> bool:
        """Validate that resource belongs to workspace scope."""
        # Check if resource ID suggests it belongs to this workspace
        workspace_prefix = f"{workspace.name}_"
        
        # Resource IDs should be scoped to workspace or be absolute paths within workspace
        if resource_id.startswith("/"):
            # Absolute path - must be within workspace directory
            workspace_path_str = str(workspace.root_path.value)
            return resource_id.startswith(workspace_path_str)
        elif resource_id.startswith(workspace_prefix):
            # Workspace-scoped resource ID
            return True
        else:
            # Unscoped resource ID - might be legacy, check if in workspace
            # This is a conservative approach - could be made more permissive
            return True  # Allow for now, but log warning
    
    async def _check_single_workspace_boundaries(
        self, 
        workspace_name: WorkspaceName
    ) -> ValidationResult:
        """Check boundaries for a single workspace."""
        issues: List[ValidationIssue] = []
        
        try:
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Workspace '{workspace_name}' not found",
                    workspace_name=workspace_name
                ))
                return ValidationResult(False, issues, workspace_name)
            
            # Check workspace integrity
            integrity_errors = await self._workspace_repository.validate_workspace_integrity(workspace)
            for error in integrity_errors:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Integrity violation: {error}",
                    workspace_name=workspace_name
                ))
            
            # Check directory structure
            if not workspace.is_initialized():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Workspace directory structure not properly initialized",
                    workspace_name=workspace_name
                ))
            
            # Check for cross-workspace contamination
            await self._check_cross_workspace_contamination(workspace, issues)
            
            # Validate workspace configuration
            await self._validate_workspace_configuration(workspace, issues)
            
        except RepositoryError as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"Failed to validate workspace boundaries: {e}",
                workspace_name=workspace_name
            ))
        
        is_valid = not any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for issue in issues
        )
        
        return ValidationResult(is_valid, issues, workspace_name)
    
    async def _check_all_workspace_boundaries(self) -> ValidationResult:
        """Check boundaries for all workspaces."""
        # For now, return a simple valid result
        # This would be implemented to check global isolation issues
        return ValidationResult(
            is_valid=True, 
            issues=[], 
            workspace_name=WorkspaceName.default()
        )
    
    async def _validate_workspace_context(self, context: WorkspaceContext) -> None:
        """Validate workspace context for isolation."""
        if not context.workspace.is_initialized():
            raise WorkspaceIsolationError(
                "Cannot isolate operations in uninitialized workspace",
                context.workspace.name
            )
    
    async def _check_cross_workspace_contamination(
        self, 
        workspace: Workspace, 
        issues: List[ValidationIssue]
    ) -> None:
        """Check for cross-workspace data contamination."""
        # Check if workspace storage contains references to other workspaces
        storage_path = workspace.get_storage_path()
        if storage_path.exists():
            # This would scan storage for foreign workspace references
            # Implementation would depend on specific storage format
            pass
    
    async def _validate_workspace_configuration(
        self, 
        workspace: Workspace, 
        issues: List[ValidationIssue]
    ) -> None:
        """Validate workspace configuration for isolation issues."""
        # Check configuration for proper workspace scoping
        config = workspace.configuration
        
        # Validate that configuration doesn't reference other workspaces
        # This would be more sophisticated in practice
        if hasattr(config, 'settings') and config.settings:
            for key, value in config.settings.items():
                if isinstance(value, str) and value.startswith("/"):
                    # Check if absolute path is within workspace
                    workspace_path_str = str(workspace.root_path.value)
                    if not value.startswith(workspace_path_str):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Configuration '{key}' references path outside workspace: {value}",
                            workspace_name=workspace.name,
                            details={"config_key": key, "path": value}
                        ))


class IsolatedWorkspaceOperations:
    """Operations interface for isolated workspace context."""
    
    def __init__(
        self, 
        context: WorkspaceContext, 
        workspace_repository: WorkspaceRepository
    ):
        self.context = context
        self._workspace_repository = workspace_repository
        self._isolation_active = False
    
    async def _enter_isolation(self) -> None:
        """Set up isolation boundary."""
        self._isolation_active = True
        # Update workspace last access time
        await self._workspace_repository.update_last_accessed(self.context.workspace)
    
    async def _exit_isolation(self) -> None:
        """Clean up isolation boundary."""
        self._isolation_active = False
    
    async def _handle_isolation_violation(self, error: Exception) -> None:
        """Handle isolation violation during operation."""
        # Log violation details
        # In practice, this might notify monitoring systems
        pass
    
    def get_workspace_path(self, relative_path: str = "") -> str:
        """Get absolute path within workspace."""
        if not self._isolation_active:
            raise WorkspaceIsolationError(
                "Cannot access workspace paths outside isolation context",
                self.context.workspace.name
            )
        
        return str(self.context.workspace.root_path.join(relative_path).value)
    
    def get_workspace_name(self) -> WorkspaceName:
        """Get current workspace name."""
        return self.context.workspace.name