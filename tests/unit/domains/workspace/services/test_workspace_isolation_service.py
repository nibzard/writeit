"""Unit tests for WorkspaceIsolationService.

Tests the workspace isolation domain service for enforcing workspace boundaries
and preventing cross-workspace data leakage.
"""

import pytest
from pathlib import Path
from typing import List, Optional
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.repositories.workspace_repository import WorkspaceRepository
from writeit.domains.workspace.services.workspace_isolation_service import (
    WorkspaceIsolationService,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    WorkspaceContext,
    WorkspaceAccessError,
    WorkspaceIsolationError,
    IsolatedWorkspaceOperations
)
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.shared.repository import RepositoryError


class MockWorkspaceRepository:
    """Mock workspace repository for testing."""
    
    def __init__(self):
        self.workspaces = {}
        self.integrity_errors = {}
    
    async def find_by_name(self, name: WorkspaceName) -> Optional[Workspace]:
        return self.workspaces.get(name.value)
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        return self.integrity_errors.get(workspace.name.value, [])
    
    async def update_last_accessed(self, workspace: Workspace) -> None:
        pass
    
    def add_workspace(self, workspace: Workspace):
        self.workspaces[workspace.name.value] = workspace
    
    def set_integrity_errors(self, workspace_name: str, errors: List[str]):
        self.integrity_errors[workspace_name] = errors


@pytest.fixture
def mock_workspace_repository():
    """Create mock workspace repository."""
    return MockWorkspaceRepository()


@pytest.fixture
def isolation_service(mock_workspace_repository):
    """Create workspace isolation service with mock repository."""
    return WorkspaceIsolationService(mock_workspace_repository)


@pytest.fixture
def test_workspace():
    """Create test workspace."""
    name = WorkspaceName("my-workspace")
    path = WorkspacePath.from_string("/tmp/my-workspace")
    config = WorkspaceConfiguration.default()
    
    # Create workspace without directory verification for testing
    workspace = Workspace(
        name=name,
        root_path=path,
        configuration=config,
        is_active=False
    )
    
    # Mock the is_initialized method to return True for testing
    workspace.is_initialized = Mock(return_value=True)
    
    return workspace


@pytest.fixture
def workspace_context(test_workspace):
    """Create workspace context for testing."""
    return WorkspaceContext(
        workspace=test_workspace,
        resource_scope="test",
        operation_id=uuid4(),
        metadata={"test": "data"}
    )


class TestWorkspaceIsolationService:
    """Test suite for WorkspaceIsolationService."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_init(self, mock_workspace_repository):
        """Test service initialization."""
        service = WorkspaceIsolationService(mock_workspace_repository)
        
        assert service._workspace_repository is mock_workspace_repository
        assert service._isolation_cache == {}
    
    @pytest.mark.asyncio
    async def test_validate_workspace_access_success(
        self, 
        isolation_service, 
        mock_workspace_repository,
        test_workspace
    ):
        """Test successful workspace access validation."""
        # Setup
        mock_workspace_repository.add_workspace(test_workspace)
        
        # Execute
        result = await isolation_service.validate_workspace_access(
            test_workspace.name, 
            "test-resource"
        )
        
        # Verify
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_workspace_access_workspace_not_found(
        self, 
        isolation_service
    ):
        """Test workspace access validation when workspace not found."""
        workspace_name = WorkspaceName("nonexistent")
        
        with pytest.raises(WorkspaceAccessError) as exc_info:
            await isolation_service.validate_workspace_access(
                workspace_name, 
                "test-resource"
            )
        
        assert "Workspace 'nonexistent' not found" in str(exc_info.value)
        assert exc_info.value.workspace_name == workspace_name
        assert exc_info.value.resource_id == "test-resource"
    
    @pytest.mark.asyncio
    async def test_validate_workspace_access_integrity_errors(
        self, 
        isolation_service,
        mock_workspace_repository,
        test_workspace
    ):
        """Test workspace access validation with integrity errors."""
        # Setup
        mock_workspace_repository.add_workspace(test_workspace)
        mock_workspace_repository.set_integrity_errors(
            test_workspace.name.value, 
            ["integrity error 1", "integrity error 2"]
        )
        
        # Execute & Verify
        with pytest.raises(WorkspaceAccessError) as exc_info:
            await isolation_service.validate_workspace_access(
                test_workspace.name, 
                "test-resource"
            )
        
        assert "Workspace integrity validation failed" in str(exc_info.value)
        assert "integrity error 1" in str(exc_info.value)
        assert "integrity error 2" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_workspace_access_repository_error(
        self, 
        isolation_service,
        mock_workspace_repository,
        test_workspace
    ):
        """Test workspace access validation with repository error."""
        # Setup repository to raise error
        async def raise_error(name):
            raise RepositoryError("Database connection failed")
        
        mock_workspace_repository.find_by_name = raise_error
        
        # Execute & Verify
        with pytest.raises(WorkspaceAccessError) as exc_info:
            await isolation_service.validate_workspace_access(
                test_workspace.name, 
                "test-resource"
            )
        
        assert "Failed to validate workspace access" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ensure_workspace_isolation_success(
        self,
        isolation_service,
        mock_workspace_repository,
        test_workspace
    ):
        """Test successful workspace isolation enforcement."""
        # Setup
        mock_workspace_repository.add_workspace(test_workspace)
        
        def test_operation():
            return "operation_result"
        
        # Execute
        result = await isolation_service.ensure_workspace_isolation(
            test_workspace.name,
            test_operation
        )
        
        # Verify
        assert result == "operation_result"
    
    @pytest.mark.asyncio
    async def test_ensure_workspace_isolation_workspace_not_found(
        self,
        isolation_service
    ):
        """Test workspace isolation when workspace not found."""
        workspace_name = WorkspaceName("nonexistent")
        
        def test_operation():
            return "result"
        
        with pytest.raises(WorkspaceIsolationError) as exc_info:
            await isolation_service.ensure_workspace_isolation(
                workspace_name,
                test_operation
            )
        
        assert "Cannot ensure isolation: workspace 'nonexistent' not found" in str(exc_info.value)
        assert exc_info.value.workspace_name == workspace_name
    
    @pytest.mark.asyncio
    async def test_ensure_workspace_isolation_operation_error(
        self,
        isolation_service,
        mock_workspace_repository,
        test_workspace
    ):
        """Test workspace isolation when operation raises error."""
        # Setup
        mock_workspace_repository.add_workspace(test_workspace)
        
        def failing_operation():
            raise ValueError("Operation failed")
        
        # Execute & Verify
        with pytest.raises(WorkspaceIsolationError) as exc_info:
            await isolation_service.ensure_workspace_isolation(
                test_workspace.name,
                failing_operation
            )
        
        assert "Operation failed within workspace isolation" in str(exc_info.value)
        assert exc_info.value.violation_details["original_error"] == "Operation failed"
        assert exc_info.value.violation_details["error_type"] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_check_workspace_boundaries_single_workspace(
        self,
        isolation_service,
        mock_workspace_repository,
        test_workspace
    ):
        """Test workspace boundary checking for single workspace."""
        # Setup
        mock_workspace_repository.add_workspace(test_workspace)
        
        # Execute
        result = await isolation_service.check_workspace_boundaries(test_workspace.name)
        
        # Verify
        assert isinstance(result, ValidationResult)
        assert result.workspace_name == test_workspace.name
        assert result.is_valid is True
        assert result.issues == []
    
    @pytest.mark.asyncio
    async def test_check_workspace_boundaries_with_errors(
        self,
        isolation_service,
        mock_workspace_repository,
        test_workspace
    ):
        """Test workspace boundary checking with integrity errors."""
        # Setup
        mock_workspace_repository.add_workspace(test_workspace)
        mock_workspace_repository.set_integrity_errors(
            test_workspace.name.value,
            ["integrity violation"]
        )
        
        # Execute
        result = await isolation_service.check_workspace_boundaries(test_workspace.name)
        
        # Verify
        assert result.is_valid is False
        assert len(result.issues) > 0
        error_messages = [issue.message for issue in result.issues]
        assert any("integrity violation" in msg for msg in error_messages)
    
    @pytest.mark.asyncio
    async def test_check_workspace_boundaries_all_workspaces(
        self,
        isolation_service
    ):
        """Test workspace boundary checking for all workspaces."""
        # Execute
        result = await isolation_service.check_workspace_boundaries()
        
        # Verify - should return valid result for global check
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_isolate_workspace_operation_context_manager(
        self,
        isolation_service,
        mock_workspace_repository,
        workspace_context
    ):
        """Test workspace operation isolation context manager."""
        # Setup
        mock_workspace_repository.add_workspace(workspace_context.workspace)
        
        # Execute
        async with isolation_service.isolate_workspace_operation(workspace_context) as ctx:
            assert isinstance(ctx, IsolatedWorkspaceOperations)
            assert ctx.context == workspace_context
            
            # Test context operations
            workspace_name = ctx.get_workspace_name()
            assert workspace_name == workspace_context.workspace.name
            
            path = ctx.get_workspace_path("subdir")
            assert "my-workspace" in path
            assert "subdir" in path


class TestValidationResult:
    """Test suite for ValidationResult."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        workspace_name = WorkspaceName("my-workspace")
        issues = [
            ValidationIssue(ValidationSeverity.WARNING, "Warning message"),
            ValidationIssue(ValidationSeverity.ERROR, "Error message")
        ]
        
        result = ValidationResult(False, issues, workspace_name)
        
        assert result.is_valid is False
        assert result.issues == issues
        assert result.workspace_name == workspace_name
    
    def test_has_errors_property(self):
        """Test has_errors property."""
        workspace_name = WorkspaceName("my-workspace")
        
        # Test with errors
        issues_with_errors = [
            ValidationIssue(ValidationSeverity.WARNING, "Warning"),
            ValidationIssue(ValidationSeverity.ERROR, "Error"),
            ValidationIssue(ValidationSeverity.CRITICAL, "Critical")
        ]
        result = ValidationResult(False, issues_with_errors, workspace_name)
        assert result.has_errors is True
        
        # Test without errors
        issues_without_errors = [
            ValidationIssue(ValidationSeverity.INFO, "Info"),
            ValidationIssue(ValidationSeverity.WARNING, "Warning")
        ]
        result = ValidationResult(True, issues_without_errors, workspace_name)
        assert result.has_errors is False
    
    def test_has_warnings_property(self):
        """Test has_warnings property."""
        workspace_name = WorkspaceName("my-workspace")
        
        # Test with warnings
        issues_with_warnings = [
            ValidationIssue(ValidationSeverity.INFO, "Info"),
            ValidationIssue(ValidationSeverity.WARNING, "Warning")
        ]
        result = ValidationResult(True, issues_with_warnings, workspace_name)
        assert result.has_warnings is True
        
        # Test without warnings
        issues_without_warnings = [
            ValidationIssue(ValidationSeverity.INFO, "Info"),
            ValidationIssue(ValidationSeverity.ERROR, "Error")
        ]
        result = ValidationResult(False, issues_without_warnings, workspace_name)
        assert result.has_warnings is False
    
    def test_get_errors_method(self):
        """Test get_errors method."""
        workspace_name = WorkspaceName("my-workspace")
        warning = ValidationIssue(ValidationSeverity.WARNING, "Warning")
        error = ValidationIssue(ValidationSeverity.ERROR, "Error")
        critical = ValidationIssue(ValidationSeverity.CRITICAL, "Critical")
        
        result = ValidationResult(False, [warning, error, critical], workspace_name)
        errors = result.get_errors()
        
        assert len(errors) == 2
        assert error in errors
        assert critical in errors
        assert warning not in errors
    
    def test_get_warnings_method(self):
        """Test get_warnings method."""
        workspace_name = WorkspaceName("my-workspace")
        info = ValidationIssue(ValidationSeverity.INFO, "Info")
        warning = ValidationIssue(ValidationSeverity.WARNING, "Warning")
        error = ValidationIssue(ValidationSeverity.ERROR, "Error")
        
        result = ValidationResult(False, [info, warning, error], workspace_name)
        warnings = result.get_warnings()
        
        assert len(warnings) == 1
        assert warning in warnings
        assert info not in warnings
        assert error not in warnings


class TestWorkspaceContext:
    """Test suite for WorkspaceContext."""
    
    def test_workspace_context_creation(self, test_workspace):
        """Test WorkspaceContext creation."""
        operation_id = uuid4()
        metadata = {"key": "value"}
        
        context = WorkspaceContext(
            workspace=test_workspace,
            resource_scope="test-scope",
            operation_id=operation_id,
            metadata=metadata
        )
        
        assert context.workspace == test_workspace
        assert context.resource_scope == "test-scope"
        assert context.operation_id == operation_id
        assert context.metadata == metadata
    
    def test_workspace_context_minimal_creation(self, test_workspace):
        """Test WorkspaceContext creation with minimal fields."""
        context = WorkspaceContext(workspace=test_workspace)
        
        assert context.workspace == test_workspace
        assert context.resource_scope is None
        assert context.operation_id is None
        assert context.metadata is None


class TestIsolatedWorkspaceOperations:
    """Test suite for IsolatedWorkspaceOperations."""
    
    @pytest.mark.asyncio
    async def test_isolated_operations_initialization(self, workspace_context):
        """Test IsolatedWorkspaceOperations initialization."""
        mock_repo = Mock()
        ops = IsolatedWorkspaceOperations(workspace_context, mock_repo)
        
        assert ops.context == workspace_context
        assert ops._workspace_repository == mock_repo
        assert ops._isolation_active is False
    
    @pytest.mark.asyncio
    async def test_enter_and_exit_isolation(self, workspace_context):
        """Test isolation enter and exit."""
        mock_repo = AsyncMock()
        ops = IsolatedWorkspaceOperations(workspace_context, mock_repo)
        
        # Test enter
        await ops._enter_isolation()
        assert ops._isolation_active is True
        mock_repo.update_last_accessed.assert_called_once_with(workspace_context.workspace)
        
        # Test exit
        await ops._exit_isolation()
        assert ops._isolation_active is False
    
    @pytest.mark.asyncio
    async def test_get_workspace_path_when_active(self, workspace_context):
        """Test getting workspace path when isolation is active."""
        mock_repo = Mock()
        ops = IsolatedWorkspaceOperations(workspace_context, mock_repo)
        
        # Activate isolation
        ops._isolation_active = True
        
        # Test path generation
        path = ops.get_workspace_path("subdir")
        assert "my-workspace" in path
        assert "subdir" in path
    
    @pytest.mark.asyncio
    async def test_get_workspace_path_when_inactive_raises_error(self, workspace_context):
        """Test getting workspace path when isolation is inactive."""
        mock_repo = Mock()
        ops = IsolatedWorkspaceOperations(workspace_context, mock_repo)
        
        # Isolation not active
        with pytest.raises(WorkspaceIsolationError) as exc_info:
            ops.get_workspace_path("subdir")
        
        assert "Cannot access workspace paths outside isolation context" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_workspace_name(self, workspace_context):
        """Test getting workspace name."""
        mock_repo = Mock()
        ops = IsolatedWorkspaceOperations(workspace_context, mock_repo)
        
        name = ops.get_workspace_name()
        assert name == workspace_context.workspace.name


class TestWorkspaceAccessError:
    """Test suite for WorkspaceAccessError."""
    
    def test_workspace_access_error_creation(self):
        """Test WorkspaceAccessError creation."""
        workspace_name = WorkspaceName("my-workspace")
        error = WorkspaceAccessError(
            "Access denied",
            workspace_name,
            "resource-123"
        )
        
        assert str(error) == "Access denied"
        assert error.workspace_name == workspace_name
        assert error.resource_id == "resource-123"
    
    def test_workspace_access_error_without_resource_id(self):
        """Test WorkspaceAccessError creation without resource ID."""
        workspace_name = WorkspaceName("my-workspace")
        error = WorkspaceAccessError("Access denied", workspace_name)
        
        assert str(error) == "Access denied"
        assert error.workspace_name == workspace_name
        assert error.resource_id is None


class TestWorkspaceIsolationError:
    """Test suite for WorkspaceIsolationError."""
    
    def test_workspace_isolation_error_creation(self):
        """Test WorkspaceIsolationError creation."""
        workspace_name = WorkspaceName("my-workspace")
        details = {"violation": "boundary crossed"}
        
        error = WorkspaceIsolationError(
            "Isolation violated",
            workspace_name,
            details
        )
        
        assert str(error) == "Isolation violated"
        assert error.workspace_name == workspace_name
        assert error.violation_details == details
    
    def test_workspace_isolation_error_without_details(self):
        """Test WorkspaceIsolationError creation without details."""
        workspace_name = WorkspaceName("my-workspace")
        error = WorkspaceIsolationError("Isolation violated", workspace_name)
        
        assert str(error) == "Isolation violated"
        assert error.workspace_name == workspace_name
        assert error.violation_details == {}