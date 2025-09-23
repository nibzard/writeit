"""Infrastructure factory for creating configured repository instances.

Provides a centralized way to create and configure all infrastructure
components with proper dependencies and workspace isolation.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from ..domains.workspace.value_objects.workspace_name import WorkspaceName
from .base.storage_manager import LMDBStorageManager
from .base.serialization import DomainEntitySerializer
from .base.unit_of_work import LMDBUnitOfWork, UnitOfWorkManager

# Pipeline repositories
from .pipeline.pipeline_template_repository_impl import LMDBPipelineTemplateRepository
from .pipeline.pipeline_run_repository_impl import LMDBPipelineRunRepository
from .pipeline.step_execution_repository_impl import LMDBStepExecutionRepository

# Workspace repositories
from .workspace.workspace_repository_impl import LMDBWorkspaceRepository
from .workspace.workspace_config_repository_impl import LMDBWorkspaceConfigRepository

# Content repositories
from .content.content_template_repository_impl import LMDBContentTemplateRepository
from .content.style_primer_repository_impl import LMDBStylePrimerRepository
from .content.generated_content_repository_impl import LMDBGeneratedContentRepository

# Execution repositories
from .execution.llm_cache_repository_impl import LMDBLLMCacheRepository
from .execution.token_usage_repository_impl import LMDBTokenUsageRepository


class InfrastructureFactory:
    """Factory for creating configured infrastructure components.
    
    Manages the creation and configuration of all infrastructure layer
    components including repositories, storage managers, and serializers.
    """
    
    def __init__(
        self,
        workspace_manager=None,
        storage_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize factory with configuration.
        
        Args:
            workspace_manager: Workspace manager instance
            storage_config: Storage configuration options
        """
        self._workspace_manager = workspace_manager
        self._storage_config = storage_config or {}
        self._storage_managers: Dict[str, LMDBStorageManager] = {}
        self._serializers: Dict[str, DomainEntitySerializer] = {}
        self._uow_managers: Dict[str, UnitOfWorkManager] = {}
    
    def create_storage_manager(
        self, 
        workspace_name: Optional[str] = None,
        **kwargs
    ) -> LMDBStorageManager:
        """Create or get cached storage manager for workspace.
        
        Args:
            workspace_name: Workspace name (uses active if None)
            **kwargs: Additional storage configuration
            
        Returns:
            Configured storage manager
        """
        cache_key = workspace_name or "default"
        
        if cache_key not in self._storage_managers:
            config = {**self._storage_config, **kwargs}
            
            storage_manager = LMDBStorageManager(
                workspace_manager=self._workspace_manager,
                workspace_name=workspace_name,
                map_size_mb=config.get("map_size_mb", 500),
                max_dbs=config.get("max_dbs", 20)
            )
            
            # Configure serializer
            serializer = self.create_serializer()
            storage_manager.set_serializer(serializer)
            
            self._storage_managers[cache_key] = storage_manager
        
        return self._storage_managers[cache_key]
    
    def create_serializer(self) -> DomainEntitySerializer:
        """Create configured domain entity serializer.
        
        Returns:
            Configured serializer with all domain types registered
        """
        serializer = DomainEntitySerializer(prefer_json=True)
        
        # Register all domain value objects and entities
        self._register_domain_types(serializer)
        
        return serializer
    
    def create_unit_of_work_manager(
        self, 
        workspace_name: Optional[str] = None
    ) -> UnitOfWorkManager:
        """Create or get cached unit of work manager.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            Unit of work manager
        """
        cache_key = workspace_name or "default"
        
        if cache_key not in self._uow_managers:
            storage_manager = self.create_storage_manager(workspace_name)
            self._uow_managers[cache_key] = UnitOfWorkManager(storage_manager)
        
        return self._uow_managers[cache_key]
    
    def _register_domain_types(self, serializer: DomainEntitySerializer) -> None:
        """Register all domain types with the serializer.
        
        Args:
            serializer: Serializer to configure
        """
        # Import all domain types here to register them
        # This is centralized registration for consistency
        
        # Pipeline domain
        from ..domains.pipeline.value_objects.pipeline_id import PipelineId
        from ..domains.pipeline.value_objects.pipeline_name import PipelineName
        from ..domains.pipeline.value_objects.step_id import StepId
        from ..domains.pipeline.value_objects.prompt_template import PromptTemplate
        from ..domains.pipeline.value_objects.model_preference import ModelPreference
        from ..domains.pipeline.value_objects.execution_status import ExecutionStatus
        
        serializer.register_value_object(PipelineId)
        serializer.register_value_object(PipelineName)
        serializer.register_value_object(StepId)
        serializer.register_value_object(PromptTemplate)
        serializer.register_value_object(ModelPreference)
        serializer.register_value_object(ExecutionStatus)
        
        # Workspace domain
        from ..domains.workspace.value_objects.workspace_name import WorkspaceName
        from ..domains.workspace.value_objects.workspace_path import WorkspacePath
        from ..domains.workspace.value_objects.configuration_value import ConfigurationValue
        
        serializer.register_value_object(WorkspaceName)
        serializer.register_value_object(WorkspacePath)
        serializer.register_value_object(ConfigurationValue)
        
        # Content domain
        from ..domains.content.value_objects.content_id import ContentId
        from ..domains.content.value_objects.template_name import TemplateName
        from ..domains.content.value_objects.style_name import StyleName
        from ..domains.content.value_objects.content_type import ContentType
        from ..domains.content.value_objects.content_format import ContentFormat
        from ..domains.content.value_objects.validation_rule import ValidationRule
        from ..domains.content.value_objects.content_length import ContentLength
        
        serializer.register_value_object(ContentId)
        serializer.register_value_object(TemplateName)
        serializer.register_value_object(StyleName)
        serializer.register_value_object(ContentType)
        serializer.register_value_object(ContentFormat)
        serializer.register_value_object(ValidationRule)
        serializer.register_value_object(ContentLength)
        
        # Execution domain
        from ..domains.execution.value_objects.model_name import ModelName
        from ..domains.execution.value_objects.token_count import TokenCount
        from ..domains.execution.value_objects.cache_key import CacheKey
        from ..domains.execution.value_objects.execution_mode import ExecutionMode
        
        serializer.register_value_object(ModelName)
        serializer.register_value_object(TokenCount)
        serializer.register_value_object(CacheKey)
        serializer.register_value_object(ExecutionMode)
    
    # Pipeline repository factories
    
    def create_pipeline_template_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBPipelineTemplateRepository:
        """Create pipeline template repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBPipelineTemplateRepository(storage_manager, workspace_name)
    
    def create_pipeline_run_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBPipelineRunRepository:
        """Create pipeline run repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBPipelineRunRepository(storage_manager, workspace_name)
    
    def create_step_execution_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBStepExecutionRepository:
        """Create step execution repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBStepExecutionRepository(storage_manager, workspace_name)
    
    # Workspace repository factories
    
    def create_workspace_repository(self) -> LMDBWorkspaceRepository:
        """Create workspace repository (global)."""
        storage_manager = self.create_storage_manager()  # Global storage
        return LMDBWorkspaceRepository(storage_manager)
    
    def create_workspace_config_repository(self) -> LMDBWorkspaceConfigRepository:
        """Create workspace configuration repository (global)."""
        storage_manager = self.create_storage_manager()  # Global storage
        return LMDBWorkspaceConfigRepository(storage_manager)
    
    # Content repository factories
    
    def create_content_template_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBContentTemplateRepository:
        """Create content template repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBContentTemplateRepository(storage_manager, workspace_name)
    
    def create_style_primer_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBStylePrimerRepository:
        """Create style primer repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBStylePrimerRepository(storage_manager, workspace_name)
    
    def create_generated_content_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBGeneratedContentRepository:
        """Create generated content repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBGeneratedContentRepository(storage_manager, workspace_name)
    
    # Execution repository factories
    
    def create_llm_cache_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBLLMCacheRepository:
        """Create LLM cache repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBLLMCacheRepository(storage_manager, workspace_name)
    
    def create_token_usage_repository(
        self, 
        workspace_name: WorkspaceName
    ) -> LMDBTokenUsageRepository:
        """Create token usage repository."""
        storage_manager = self.create_storage_manager(workspace_name.value)
        return LMDBTokenUsageRepository(storage_manager, workspace_name)
    
    def cleanup(self) -> None:
        """Clean up all cached resources."""
        for storage_manager in self._storage_managers.values():
            storage_manager.close()
        
        self._storage_managers.clear()
        self._serializers.clear()
        self._uow_managers.clear()
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics for all storage managers.
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {}
        for workspace, storage_manager in self._storage_managers.items():
            try:
                workspace_stats = storage_manager.get_stats()
                stats[workspace] = workspace_stats
            except Exception as e:
                stats[workspace] = {"error": str(e)}
        
        return stats


# Global factory instance
_factory: Optional[InfrastructureFactory] = None


def get_infrastructure_factory(
    workspace_manager=None,
    storage_config: Optional[Dict[str, Any]] = None
) -> InfrastructureFactory:
    """Get or create global infrastructure factory.
    
    Args:
        workspace_manager: Workspace manager instance
        storage_config: Storage configuration options
        
    Returns:
        Infrastructure factory instance
    """
    global _factory
    
    if _factory is None:
        _factory = InfrastructureFactory(workspace_manager, storage_config)
    
    return _factory


def reset_infrastructure_factory() -> None:
    """Reset global infrastructure factory (useful for testing)."""
    global _factory
    
    if _factory is not None:
        _factory.cleanup()
        _factory = None