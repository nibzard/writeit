"""API Response Mapper for domain to DTO conversion.

Provides mapping between domain entities/value objects and API DTOs
while maintaining proper abstraction boundaries and data transformation.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TypeVar, Generic, Type, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from ...domains.workspace.entities import Workspace, WorkspaceConfiguration
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.pipeline.entities import PipelineTemplate, PipelineRun, StepExecution
from ...domains.pipeline.value_objects import PipelineId, StepId, PipelineName, PipelineVersion
from ...domains.content.entities import Content, Template, Style
from ...domains.content.value_objects import ContentId, TemplateId, StyleId
from ...domains.execution.entities import ExecutionContext, ExecutionResult
from ...domains.execution.value_objects import ExecutionId, ExecutionStatus

T = TypeVar('T')
D = TypeVar('D', bound=BaseModel)


# API DTO Models

class WorkspaceDTO(BaseModel):
    """Workspace data transfer object."""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    is_active: bool = True
    configuration: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None


class WorkspaceConfigurationDTO(BaseModel):
    """Workspace configuration data transfer object."""
    workspace_name: str
    settings: Dict[str, Any] = field(default_factory=dict)
    llm_settings: Dict[str, Any] = field(default_factory=dict)
    storage_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PipelineTemplateDTO(BaseModel):
    """Pipeline template data transfer object."""
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    workspace_name: Optional[str] = None


class PipelineRunDTO(BaseModel):
    """Pipeline run data transfer object."""
    id: str
    pipeline_id: str
    pipeline_name: str
    status: str
    workspace_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class StepExecutionDTO(BaseModel):
    """Step execution data transfer object."""
    id: str
    step_id: str
    run_id: str
    name: str
    status: str
    step_type: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    responses: List[str] = field(default_factory=list)
    selected_response: Optional[str] = None
    user_feedback: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentDTO(BaseModel):
    """Content data transfer object."""
    id: str
    name: str
    content_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    workspace_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TemplateDTO(BaseModel):
    """Template data transfer object."""
    id: str
    name: str
    description: Optional[str] = None
    template_type: str
    content: str
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    workspace_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StyleDTO(BaseModel):
    """Style data transfer object."""
    id: str
    name: str
    description: Optional[str] = None
    style_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    workspace_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExecutionContextDTO(BaseModel):
    """Execution context data transfer object."""
    id: str
    workspace_name: str
    execution_mode: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


class ExecutionResultDTO(BaseModel):
    """Execution result data transfer object."""
    id: str
    execution_id: str
    status: str
    results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Generic Mapper Interface

class DomainMapper(ABC, Generic[T, D]):
    """Abstract base class for domain to DTO mapping."""
    
    @abstractmethod
    def to_dto(self, domain_object: T) -> D:
        """Convert domain object to DTO."""
        pass
    
    @abstractmethod
    def from_dto(self, dto: D) -> T:
        """Convert DTO to domain object."""
        pass


# Specific Mappers

class WorkspaceMapper(DomainMapper[Workspace, WorkspaceDTO]):
    """Mapper for Workspace domain objects."""
    
    def to_dto(self, workspace: Workspace) -> WorkspaceDTO:
        """Convert Workspace to WorkspaceDTO."""
        return WorkspaceDTO(
            name=workspace.name.value,
            display_name=workspace.display_name,
            description=workspace.description,
            created_at=workspace.created_at,
            last_accessed=workspace.last_accessed,
            is_active=workspace.is_active,
            configuration=workspace.configuration.to_dict() if workspace.configuration else None,
            stats=workspace.get_stats() if hasattr(workspace, 'get_stats') else None
        )
    
    def from_dto(self, dto: WorkspaceDTO) -> Workspace:
        """Convert WorkspaceDTO to Workspace."""
        # This would typically involve more complex reconstruction
        # For now, basic implementation
        workspace_name = WorkspaceName(dto.name)
        return Workspace(
            name=workspace_name,
            display_name=dto.display_name,
            description=dto.description,
            created_at=dto.created_at,
            last_accessed=dto.last_accessed,
            is_active=dto.is_active
        )


class WorkspaceConfigurationMapper(DomainMapper[WorkspaceConfiguration, WorkspaceConfigurationDTO]):
    """Mapper for WorkspaceConfiguration domain objects."""
    
    def to_dto(self, config: WorkspaceConfiguration) -> WorkspaceConfigurationDTO:
        """Convert WorkspaceConfiguration to WorkspaceConfigurationDTO."""
        return WorkspaceConfigurationDTO(
            workspace_name=config.workspace_name.value,
            settings=config.settings,
            llm_settings=config.llm_settings,
            storage_settings=config.storage_settings,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    
    def from_dto(self, dto: WorkspaceConfigurationDTO) -> WorkspaceConfiguration:
        """Convert WorkspaceConfigurationDTO to WorkspaceConfiguration."""
        workspace_name = WorkspaceName(dto.workspace_name)
        return WorkspaceConfiguration(
            workspace_name=workspace_name,
            settings=dto.settings,
            llm_settings=dto.llm_settings,
            storage_settings=dto.storage_settings,
            created_at=dto.created_at,
            updated_at=dto.updated_at
        )


class PipelineTemplateMapper(DomainMapper[PipelineTemplate, PipelineTemplateDTO]):
    """Mapper for PipelineTemplate domain objects."""
    
    def to_dto(self, template: PipelineTemplate) -> PipelineTemplateDTO:
        """Convert PipelineTemplate to PipelineTemplateDTO."""
        return PipelineTemplateDTO(
            id=template.id.value,
            name=template.name.value,
            description=template.description,
            version=template.version.value,
            author=template.author,
            tags=template.tags,
            metadata=template.metadata,
            inputs=template.inputs,
            steps=[self._step_to_dict(step) for step in template.steps],
            defaults=template.defaults,
            created_at=template.created_at,
            updated_at=template.updated_at,
            workspace_name=template.workspace_name.value if template.workspace_name else None
        )
    
    def from_dto(self, dto: PipelineTemplateDTO) -> PipelineTemplate:
        """Convert PipelineTemplateDTO to PipelineTemplate."""
        pipeline_id = PipelineId(dto.id)
        pipeline_name = PipelineName(dto.name)
        pipeline_version = PipelineVersion(dto.version)
        workspace_name = WorkspaceName(dto.workspace_name) if dto.workspace_name else None
        
        return PipelineTemplate(
            id=pipeline_id,
            name=pipeline_name,
            description=dto.description,
            version=pipeline_version,
            author=dto.author,
            tags=dto.tags,
            metadata=dto.metadata,
            inputs=dto.inputs,
            steps=dto.steps,  # Would need proper step object conversion
            defaults=dto.defaults,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            workspace_name=workspace_name
        )
    
    def _step_to_dict(self, step: Any) -> Dict[str, Any]:
        """Convert step object to dictionary."""
        # This would depend on the actual step structure
        return {
            "id": getattr(step, 'id', None),
            "name": getattr(step, 'name', ''),
            "description": getattr(step, 'description', ''),
            "type": getattr(step, 'type', ''),
            "configuration": getattr(step, 'configuration', {})
        }


class PipelineRunMapper(DomainMapper[PipelineRun, PipelineRunDTO]):
    """Mapper for PipelineRun domain objects."""
    
    def to_dto(self, run: PipelineRun) -> PipelineRunDTO:
        """Convert PipelineRun to PipelineRunDTO."""
        return PipelineRunDTO(
            id=run.id,
            pipeline_id=run.pipeline_id.value,
            pipeline_name=run.pipeline_name.value,
            status=run.status.value,
            workspace_name=run.workspace_name.value,
            inputs=run.inputs,
            outputs=run.outputs,
            execution_context=run.execution_context.to_dict() if run.execution_context else {},
            steps=[self._step_execution_to_dict(step) for step in run.steps],
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error=run.error,
            metrics=run.get_metrics() if hasattr(run, 'get_metrics') else {}
        )
    
    def from_dto(self, dto: PipelineRunDTO) -> PipelineRun:
        """Convert PipelineRunDTO to PipelineRun."""
        # Complex reconstruction - simplified implementation
        pipeline_id = PipelineId(dto.pipeline_id)
        pipeline_name = PipelineName(dto.pipeline_name)
        workspace_name = WorkspaceName(dto.workspace_name)
        
        return PipelineRun(
            id=dto.id,
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            workspace_name=workspace_name,
            status=ExecutionStatus(dto.status),
            inputs=dto.inputs,
            outputs=dto.outputs,
            created_at=dto.created_at,
            started_at=dto.started_at,
            completed_at=dto.completed_at,
            error=dto.error
        )
    
    def _step_execution_to_dict(self, step: StepExecution) -> Dict[str, Any]:
        """Convert step execution to dictionary."""
        return {
            "id": step.id,
            "step_id": step.step_id.value,
            "name": step.name,
            "status": step.status.value,
            "step_type": step.step_type,
            "inputs": step.inputs,
            "outputs": step.outputs,
            "responses": step.responses,
            "selected_response": step.selected_response,
            "user_feedback": step.user_feedback,
            "started_at": step.started_at,
            "completed_at": step.completed_at,
            "execution_time": step.execution_time,
            "tokens_used": step.tokens_used,
            "error": step.error,
            "metadata": step.metadata
        }


class ContentMapper(DomainMapper[Content, ContentDTO]):
    """Mapper for Content domain objects."""
    
    def to_dto(self, content: Content) -> ContentDTO:
        """Convert Content to ContentDTO."""
        return ContentDTO(
            id=content.id.value,
            name=content.name,
            content_type=content.content_type,
            content=content.content,
            metadata=content.metadata,
            workspace_name=content.workspace_name.value if content.workspace_name else None,
            created_at=content.created_at,
            updated_at=content.updated_at
        )
    
    def from_dto(self, dto: ContentDTO) -> Content:
        """Convert ContentDTO to Content."""
        content_id = ContentId(dto.id)
        workspace_name = WorkspaceName(dto.workspace_name) if dto.workspace_name else None
        
        return Content(
            id=content_id,
            name=dto.name,
            content_type=dto.content_type,
            content=dto.content,
            metadata=dto.metadata,
            workspace_name=workspace_name,
            created_at=dto.created_at,
            updated_at=dto.updated_at
        )


class TemplateMapper(DomainMapper[Template, TemplateDTO]):
    """Mapper for Template domain objects."""
    
    def to_dto(self, template: Template) -> TemplateDTO:
        """Convert Template to TemplateDTO."""
        return TemplateDTO(
            id=template.id.value,
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            content=template.content,
            variables=template.variables,
            metadata=template.metadata,
            workspace_name=template.workspace_name.value if template.workspace_name else None,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    def from_dto(self, dto: TemplateDTO) -> Template:
        """Convert TemplateDTO to Template."""
        template_id = TemplateId(dto.id)
        workspace_name = WorkspaceName(dto.workspace_name) if dto.workspace_name else None
        
        return Template(
            id=template_id,
            name=dto.name,
            description=dto.description,
            template_type=dto.template_type,
            content=dto.content,
            variables=dto.variables,
            metadata=dto.metadata,
            workspace_name=workspace_name,
            created_at=dto.created_at,
            updated_at=dto.updated_at
        )


# Response Mapper Registry

class APIResponseMapper:
    """Central registry for domain to DTO mapping."""
    
    def __init__(self):
        self._mappers: Dict[Type, DomainMapper] = {}
        self._setup_default_mappers()
    
    def _setup_default_mappers(self) -> None:
        """Set up default mappers."""
        self.register_mapper(Workspace, WorkspaceMapper())
        self.register_mapper(WorkspaceConfiguration, WorkspaceConfigurationMapper())
        self.register_mapper(PipelineTemplate, PipelineTemplateMapper())
        self.register_mapper(PipelineRun, PipelineRunMapper())
        self.register_mapper(Content, ContentMapper())
        self.register_mapper(Template, TemplateMapper())
    
    def register_mapper(self, domain_type: Type[T], mapper: DomainMapper[T, D]) -> None:
        """Register a mapper for a domain type."""
        self._mappers[domain_type] = mapper
    
    def to_dto(self, domain_object: T) -> BaseModel:
        """Convert domain object to DTO."""
        domain_type = type(domain_object)
        mapper = self._mappers.get(domain_type)
        
        if not mapper:
            raise ValueError(f"No mapper registered for type {domain_type.__name__}")
        
        return mapper.to_dto(domain_object)
    
    def from_dto(self, dto: BaseModel, domain_type: Type[T]) -> T:
        """Convert DTO to domain object."""
        mapper = self._mappers.get(domain_type)
        
        if not mapper:
            raise ValueError(f"No mapper registered for type {domain_type.__name__}")
        
        return mapper.from_dto(dto)
    
    def to_dto_list(self, domain_objects: List[T]) -> List[BaseModel]:
        """Convert list of domain objects to DTOs."""
        return [self.to_dto(obj) for obj in domain_objects]
    
    def create_pagination_response(
        self,
        items: List[BaseModel],
        total: int,
        page: int = 1,
        page_size: int = 50,
        **metadata: Any
    ) -> Dict[str, Any]:
        """Create paginated response."""
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "metadata": metadata
        }
    
    def create_success_response(
        self,
        data: Union[BaseModel, List[BaseModel], Dict[str, Any]],
        message: Optional[str] = None,
        **metadata: Any
    ) -> Dict[str, Any]:
        """Create standardized success response."""
        response = {
            "success": True,
            "data": data
        }
        
        if message:
            response["message"] = message
        
        if metadata:
            response["metadata"] = metadata
        
        return response


# Global response mapper instance
response_mapper = APIResponseMapper()