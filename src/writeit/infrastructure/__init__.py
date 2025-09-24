"""Infrastructure layer for WriteIt.

Provides concrete implementations of domain repositories using LMDB storage.
Includes transaction management, data serialization, and workspace isolation.
"""

# from .base.storage_manager import LMDBStorageManager  # Temporarily disabled due to circular import
from .base.repository_base import LMDBRepositoryBase
from .base.unit_of_work import LMDBUnitOfWork
from .base.serialization import DomainEntitySerializer
from .base.exceptions import (
    InfrastructureError,
    StorageError,
    ConnectionError,
    SerializationError,
    TransactionError,
    ValidationError,
    ConfigurationError,
    CacheError
)
from .factory import InfrastructureFactory, get_infrastructure_factory, reset_infrastructure_factory

# Repository implementations
from .pipeline import (
    LMDBPipelineTemplateRepository,
    LMDBPipelineRunRepository,
    LMDBStepExecutionRepository
)
from .workspace import (
    LMDBWorkspaceRepository,
    LMDBWorkspaceConfigRepository
)
from .content import (
    LMDBContentTemplateRepository,
    LMDBStylePrimerRepository,
    LMDBGeneratedContentRepository
)
from .execution import (
    LMDBLLMCacheRepository,
    LMDBTokenUsageRepository
)

__all__ = [
    # Base infrastructure
    # "LMDBStorageManager",  # Temporarily disabled due to circular import
    "LMDBRepositoryBase", 
    "LMDBUnitOfWork",
    "DomainEntitySerializer",
    
    # Exceptions
    "InfrastructureError",
    "StorageError",
    "ConnectionError",
    "SerializationError",
    "TransactionError",
    "ValidationError",
    "ConfigurationError",
    "CacheError",
    
    # Factory
    "InfrastructureFactory",
    "get_infrastructure_factory",
    "reset_infrastructure_factory",
    
    # Pipeline repositories
    "LMDBPipelineTemplateRepository",
    "LMDBPipelineRunRepository",
    "LMDBStepExecutionRepository",
    
    # Workspace repositories
    "LMDBWorkspaceRepository",
    "LMDBWorkspaceConfigRepository",
    
    # Content repositories
    "LMDBContentTemplateRepository",
    "LMDBStylePrimerRepository",
    "LMDBGeneratedContentRepository",
    
    # Execution repositories
    "LMDBLLMCacheRepository",
    "LMDBTokenUsageRepository",
]