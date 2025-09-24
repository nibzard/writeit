"""Mock factories for testing.

Provides factory functions and classes for creating mock objects
for testing WriteIt's domain-driven architecture components.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Callable, Set
from unittest.mock import AsyncMock, Mock, MagicMock
import asyncio
from datetime import datetime
from uuid import uuid4

from writeit.shared.events import DomainEvent, EventHandler, AsyncEventBus, EventPublishResult
from writeit.pipeline import PipelineExecutor
from writeit.domains.workspace.repositories.workspace_repository import WorkspaceRepository
from writeit.domains.workspace.entities.workspace import Workspace

# Repository imports
from writeit.domains.pipeline.repositories.pipeline_template_repository import PipelineTemplateRepository
from writeit.domains.pipeline.repositories.pipeline_run_repository import PipelineRunRepository
from writeit.domains.pipeline.repositories.step_execution_repository import StepExecutionRepository
from writeit.domains.workspace.repositories.workspace_config_repository import WorkspaceConfigRepository
from writeit.domains.content.repositories.content_template_repository import ContentTemplateRepository
from writeit.domains.content.repositories.style_primer_repository import StylePrimerRepository
from writeit.domains.content.repositories.generated_content_repository import GeneratedContentRepository
from writeit.domains.execution.repositories.llm_cache_repository import LLMCacheRepository
from writeit.domains.execution.repositories.token_usage_repository import TokenUsageRepository

# Service imports
from writeit.domains.pipeline.services.pipeline_validation_service import PipelineValidationService, ValidationResult
from writeit.domains.pipeline.services.pipeline_execution_service import PipelineExecutionService
from writeit.domains.pipeline.services.step_dependency_service import StepDependencyService
from writeit.domains.workspace.services.workspace_management_service import WorkspaceManagementService
from writeit.domains.workspace.services.workspace_configuration_service import WorkspaceConfigurationService
from writeit.domains.workspace.services.workspace_analytics_service import WorkspaceAnalyticsService
from writeit.domains.workspace.services.workspace_isolation_service import WorkspaceIsolationService
from writeit.domains.workspace.services.workspace_template_service import WorkspaceTemplateService
from writeit.domains.content.services.template_management_service import TemplateManagementService
from writeit.domains.content.services.style_management_service import StyleManagementService
from writeit.domains.content.services.content_generation_service import ContentGenerationService
from writeit.domains.content.services.template_rendering_service import TemplateRenderingService
from writeit.domains.content.services.content_validation_service import ContentValidationService
from writeit.domains.execution.services.llm_orchestration_service import LLMOrchestrationService
from writeit.domains.execution.services.cache_management_service import CacheManagementService
from writeit.domains.execution.services.token_analytics_service import TokenAnalyticsService

# Entity and Value Object imports for mock data
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.entities.pipeline_step import StepExecution
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.content.entities.template import Template as ContentTemplate
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.llm.cache import CacheEntry as LLMCacheEntry
from writeit.domains.execution.entities.token_usage import TokenUsage as TokenUsageRecord

# Value Object imports
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.execution.value_objects.token_count import TokenCount


class MockLLMProvider:
    """Mock LLM provider for deterministic testing."""
    
    def __init__(self):
        self.responses: Dict[str, str] = {}
        self.default_response = "Mock LLM response"
        self.call_count = 0
        self.last_prompt = ""
        self.streaming_enabled = False
        self.stream_delay = 0.01  # Small delay for realistic streaming
        self.should_fail = False
        self.failure_message = "Mock LLM failure"
    
    def set_response(self, prompt_key: str, response: str) -> None:
        """Set a specific response for a prompt pattern."""
        self.responses[prompt_key] = response
    
    def set_default_response(self, response: str) -> None:
        """Set the default response for unmatched prompts."""
        self.default_response = response
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "mock-model",
        **kwargs
    ) -> str:
        """Generate text response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Check for specific response
        for key, response in self.responses.items():
            if key.lower() in prompt.lower():
                return response
        
        return self.default_response
    
    async def stream_text(
        self, 
        prompt: str, 
        model: str = "mock-model",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream text response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Get response
        response = await self.generate_text(prompt, model, **kwargs)
        
        # Stream the response word by word
        words = response.split()
        for word in words:
            if self.stream_delay > 0:
                await asyncio.sleep(self.stream_delay)
            yield word + " "
    
    def get_model_info(self, model: str = "mock-model") -> Dict[str, Any]:
        """Get model information (mock)."""
        return {
            "name": model,
            "provider": "mock",
            "version": "1.0.0",
            "context_length": 4096,
            "supports_streaming": True,
            "supports_functions": False
        }
    
    def reset(self) -> None:
        """Reset mock state."""
        self.call_count = 0
        self.last_prompt = ""
        self.responses.clear()
        self.should_fail = False


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.published_events: List[DomainEvent] = []
        self.registered_handlers: Dict[type, List[EventHandler]] = {}
        self.publish_results: List[EventPublishResult] = []
        self.should_fail = False
        self.failure_message = "Mock event bus failure"
        self.running = False
    
    async def publish(self, event: DomainEvent) -> EventPublishResult:
        """Publish an event (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.published_events.append(event)
        
        # Create mock result
        result = EventPublishResult(
            event=event,
            handlers_executed=len(self.registered_handlers.get(type(event), [])),
            handlers_failed=0,
            errors=[],
            stored_event=event
        )
        
        self.publish_results.append(result)
        return result
    
    async def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler (mock)."""
        event_type = handler.event_type
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
    
    async def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler (mock)."""
        event_type = handler.event_type
        if event_type in self.registered_handlers:
            self.registered_handlers[event_type].remove(handler)
    
    async def start(self) -> None:
        """Start the event bus (mock)."""
        self.running = True
    
    async def stop(self) -> None:
        """Stop the event bus (mock)."""
        self.running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics (mock)."""
        return {
            "running": self.running,
            "events_published": len(self.published_events),
            "handlers_registered": sum(len(handlers) for handlers in self.registered_handlers.values()),
            "failed_attempts": 0,
            "dead_letter_queue": 0
        }
    
    def get_published_events(self, event_type: Optional[type] = None) -> List[DomainEvent]:
        """Get published events, optionally filtered by type."""
        if event_type is None:
            return self.published_events.copy()
        return [event for event in self.published_events if isinstance(event, event_type)]
    
    def clear_events(self) -> None:
        """Clear all published events."""
        self.published_events.clear()
        self.publish_results.clear()
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.published_events.clear()
        self.registered_handlers.clear()
        self.publish_results.clear()
        self.should_fail = False
        self.running = False


class MockWorkspaceRepository:
    """Mock workspace repository for testing."""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.operation_log: List[tuple[str, str]] = []  # (operation, workspace_name)
        self.should_fail = False
        self.failure_message = "Mock repository failure"
        self.integrity_errors: Dict[str, List[str]] = {}
    
    async def find_by_name(self, name) -> Optional[Workspace]:
        """Find workspace by name (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_name", name.value))
        return self.workspaces.get(name.value)
    
    async def save(self, workspace: Workspace) -> None:
        """Save workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("save", workspace.name.value))
        self.workspaces[workspace.name.value] = workspace
    
    async def delete(self, workspace: Workspace) -> None:
        """Delete workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("delete", workspace.name.value))
        if workspace.name.value in self.workspaces:
            del self.workspaces[workspace.name.value]
    
    async def list_all(self) -> List[Workspace]:
        """List all workspaces (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.workspaces.values())
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("validate_integrity", workspace.name.value))
        return self.integrity_errors.get(workspace.name.value, [])
    
    async def update_last_accessed(self, workspace: Workspace) -> None:
        """Update last accessed timestamp (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("update_last_accessed", workspace.name.value))
    
    # Test helper methods
    def add_workspace(self, workspace: Workspace) -> None:
        """Add a workspace to the mock repository."""
        self.workspaces[workspace.name.value] = workspace
    
    def set_integrity_errors(self, workspace_name: str, errors: List[str]) -> None:
        """Set integrity errors for a workspace."""
        self.integrity_errors[workspace_name] = errors
    
    def get_operation_count(self, operation: str, workspace_name: str = "") -> int:
        """Get count of specific operations."""
        return len([
            log for log in self.operation_log
            if log[0] == operation and (not workspace_name or log[1] == workspace_name)
        ])
    
    def clear_operation_log(self) -> None:
        """Clear operation log."""
        self.operation_log.clear()
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.workspaces.clear()
        self.operation_log.clear()
        self.integrity_errors.clear()
        self.should_fail = False


# =============================================================================
# Repository Mock Implementations
# =============================================================================

class MockPipelineTemplateRepository:
    """Mock pipeline template repository for testing."""
    
    def __init__(self):
        self.templates: Dict[str, PipelineTemplate] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
        self.validation_errors: Dict[str, List[str]] = {}
        self.global_templates: Set[str] = set()
    
    async def find_by_name(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find template by name within current workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_name", name.value))
        return self.templates.get(name.value)
    
    async def find_by_name_and_workspace(self, name: PipelineName, workspace: WorkspaceName) -> Optional[PipelineTemplate]:
        """Find template by name in specific workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        key = f"{workspace.value}:{name.value}"
        self.operation_log.append(("find_by_name_and_workspace", key))
        return self.templates.get(key)
    
    async def find_global_templates(self) -> List[PipelineTemplate]:
        """Find all global templates (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_global_templates", "*"))
        return [template for key, template in self.templates.items() if key in self.global_templates]
    
    async def find_by_version(self, name: PipelineName, version: str) -> Optional[PipelineTemplate]:
        """Find specific version of template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        key = f"{name.value}:{version}"
        self.operation_log.append(("find_by_version", key))
        return self.templates.get(key)
    
    async def find_latest_version(self, name: PipelineName) -> Optional[PipelineTemplate]:
        """Find latest version of template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_latest_version", name.value))
        # Return the first matching template for simplicity
        for template in self.templates.values():
            if hasattr(template, 'name') and template.name == name:
                return template
        return None
    
    async def find_all_versions(self, name: PipelineName) -> List[PipelineTemplate]:
        """Find all versions of template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_all_versions", name.value))
        return [template for template in self.templates.values() 
                if hasattr(template, 'name') and template.name == name]
    
    async def search_by_tag(self, tag: str) -> List[PipelineTemplate]:
        """Search templates by tag (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("search_by_tag", tag))
        return [template for template in self.templates.values() 
                if hasattr(template, 'tags') and tag in template.tags]
    
    async def search_by_description(self, query: str) -> List[PipelineTemplate]:
        """Search templates by description (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("search_by_description", query))
        return [template for template in self.templates.values() 
                if hasattr(template, 'description') and query.lower() in template.description.lower()]
    
    async def is_name_available(self, name: PipelineName) -> bool:
        """Check if template name is available (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("is_name_available", name.value))
        return name.value not in self.templates
    
    async def validate_template(self, template: PipelineTemplate) -> List[str]:
        """Validate template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else "unknown"
        self.operation_log.append(("validate_template", template_key))
        return self.validation_errors.get(template_key, [])
    
    async def save(self, template: PipelineTemplate) -> None:
        """Save template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else str(uuid4())
        self.operation_log.append(("save", template_key))
        self.templates[template_key] = template
    
    async def delete(self, template: PipelineTemplate) -> None:
        """Delete template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else "unknown"
        self.operation_log.append(("delete", template_key))
        if template_key in self.templates:
            del self.templates[template_key]
    
    async def list_all(self) -> List[PipelineTemplate]:
        """List all templates (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.templates.values())
    
    # Test helper methods
    def add_template(self, template: PipelineTemplate, is_global: bool = False) -> None:
        """Add template to mock repository."""
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else str(uuid4())
        self.templates[template_key] = template
        if is_global:
            self.global_templates.add(template_key)
    
    def set_validation_errors(self, template_name: str, errors: List[str]) -> None:
        """Set validation errors for a template."""
        self.validation_errors[template_name] = errors
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.templates.clear()
        self.operation_log.clear()
        self.validation_errors.clear()
        self.global_templates.clear()
        self.should_fail = False


class MockPipelineRunRepository:
    """Mock pipeline run repository for testing."""
    
    def __init__(self):
        self.runs: Dict[str, PipelineRun] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_id(self, run_id: str) -> Optional[PipelineRun]:
        """Find run by ID (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_id", run_id))
        return self.runs.get(run_id)
    
    async def find_by_pipeline_template(self, template_id: PipelineId) -> List[PipelineRun]:
        """Find runs by template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_pipeline_template", template_id.value))
        return [run for run in self.runs.values() 
                if hasattr(run, 'pipeline_id') and run.pipeline_id == template_id]
    
    async def find_recent_runs(self, limit: int = 10) -> List[PipelineRun]:
        """Find recent runs (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_recent_runs", str(limit)))
        runs = list(self.runs.values())
        return runs[:limit]  # Simplified - would normally sort by date
    
    async def save(self, run: PipelineRun) -> None:
        """Save run (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        run_id = getattr(run, 'id', {}).value if hasattr(run, 'id') else str(uuid4())
        self.operation_log.append(("save", run_id))
        self.runs[run_id] = run
    
    async def delete(self, run: PipelineRun) -> None:
        """Delete run (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        run_id = getattr(run, 'id', {}).value if hasattr(run, 'id') else "unknown"
        self.operation_log.append(("delete", run_id))
        if run_id in self.runs:
            del self.runs[run_id]
    
    async def list_all(self) -> List[PipelineRun]:
        """List all runs (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.runs.values())
    
    # Test helper methods
    def add_run(self, run: PipelineRun) -> None:
        """Add run to mock repository."""
        run_id = getattr(run, 'id', {}).value if hasattr(run, 'id') else str(uuid4())
        self.runs[run_id] = run
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.runs.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockStepExecutionRepository:
    """Mock step execution repository for testing."""
    
    def __init__(self):
        self.executions: Dict[str, StepExecution] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_id(self, execution_id: str) -> Optional[StepExecution]:
        """Find execution by ID (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_id", execution_id))
        return self.executions.get(execution_id)
    
    async def find_by_run_id(self, run_id: str) -> List[StepExecution]:
        """Find executions by run ID (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_run_id", run_id))
        return [exec for exec in self.executions.values() 
                if hasattr(exec, 'run_id') and exec.run_id == run_id]
    
    async def save(self, execution: StepExecution) -> None:
        """Save execution (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        exec_id = getattr(execution, 'id', {}).value if hasattr(execution, 'id') else str(uuid4())
        self.operation_log.append(("save", exec_id))
        self.executions[exec_id] = execution
    
    async def delete(self, execution: StepExecution) -> None:
        """Delete execution (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        exec_id = getattr(execution, 'id', {}).value if hasattr(execution, 'id') else "unknown"
        self.operation_log.append(("delete", exec_id))
        if exec_id in self.executions:
            del self.executions[exec_id]
    
    async def list_all(self) -> List[StepExecution]:
        """List all executions (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.executions.values())
    
    # Test helper methods
    def add_execution(self, execution: StepExecution) -> None:
        """Add execution to mock repository."""
        exec_id = getattr(execution, 'id', {}).value if hasattr(execution, 'id') else str(uuid4())
        self.executions[exec_id] = execution
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.executions.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockWorkspaceConfigRepository:
    """Mock workspace config repository for testing."""
    
    def __init__(self):
        self.configs: Dict[str, WorkspaceConfiguration] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_workspace(self, workspace: WorkspaceName) -> Optional[WorkspaceConfiguration]:
        """Find config by workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_workspace", workspace.value))
        return self.configs.get(workspace.value)
    
    async def save(self, config: WorkspaceConfiguration) -> None:
        """Save config (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        workspace_key = getattr(config, 'workspace_name', {}).value if hasattr(config, 'workspace_name') else str(uuid4())
        self.operation_log.append(("save", workspace_key))
        self.configs[workspace_key] = config
    
    async def delete(self, config: WorkspaceConfiguration) -> None:
        """Delete config (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        workspace_key = getattr(config, 'workspace_name', {}).value if hasattr(config, 'workspace_name') else "unknown"
        self.operation_log.append(("delete", workspace_key))
        if workspace_key in self.configs:
            del self.configs[workspace_key]
    
    async def list_all(self) -> List[WorkspaceConfiguration]:
        """List all configs (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.configs.values())
    
    # Test helper methods
    def add_config(self, config: WorkspaceConfiguration) -> None:
        """Add config to mock repository."""
        workspace_key = getattr(config, 'workspace_name', {}).value if hasattr(config, 'workspace_name') else str(uuid4())
        self.configs[workspace_key] = config
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.configs.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockContentTemplateRepository:
    """Mock content template repository for testing."""
    
    def __init__(self):
        self.templates: Dict[str, ContentTemplate] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_name(self, name: TemplateName) -> Optional[ContentTemplate]:
        """Find template by name (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_name", name.value))
        return self.templates.get(name.value)
    
    async def save(self, template: ContentTemplate) -> None:
        """Save template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else str(uuid4())
        self.operation_log.append(("save", template_key))
        self.templates[template_key] = template
    
    async def delete(self, template: ContentTemplate) -> None:
        """Delete template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else "unknown"
        self.operation_log.append(("delete", template_key))
        if template_key in self.templates:
            del self.templates[template_key]
    
    async def list_all(self) -> List[ContentTemplate]:
        """List all templates (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.templates.values())
    
    # Test helper methods
    def add_template(self, template: ContentTemplate) -> None:
        """Add template to mock repository."""
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else str(uuid4())
        self.templates[template_key] = template
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.templates.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockStylePrimerRepository:
    """Mock style primer repository for testing."""
    
    def __init__(self):
        self.primers: Dict[str, StylePrimer] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_name(self, name: str) -> Optional[StylePrimer]:
        """Find primer by name (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_name", name))
        return self.primers.get(name)
    
    async def save(self, primer: StylePrimer) -> None:
        """Save primer (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        primer_key = getattr(primer, 'name', "unknown")
        self.operation_log.append(("save", primer_key))
        self.primers[primer_key] = primer
    
    async def delete(self, primer: StylePrimer) -> None:
        """Delete primer (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        primer_key = getattr(primer, 'name', "unknown")
        self.operation_log.append(("delete", primer_key))
        if primer_key in self.primers:
            del self.primers[primer_key]
    
    async def list_all(self) -> List[StylePrimer]:
        """List all primers (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.primers.values())
    
    # Test helper methods
    def add_primer(self, primer: StylePrimer) -> None:
        """Add primer to mock repository."""
        primer_key = getattr(primer, 'name', str(uuid4()))
        self.primers[primer_key] = primer
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.primers.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockGeneratedContentRepository:
    """Mock generated content repository for testing."""
    
    def __init__(self):
        self.content: Dict[str, GeneratedContent] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_id(self, content_id: str) -> Optional[GeneratedContent]:
        """Find content by ID (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_id", content_id))
        return self.content.get(content_id)
    
    async def save(self, content: GeneratedContent) -> None:
        """Save content (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        content_id = getattr(content, 'id', str(uuid4()))
        self.operation_log.append(("save", content_id))
        self.content[content_id] = content
    
    async def delete(self, content: GeneratedContent) -> None:
        """Delete content (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        content_id = getattr(content, 'id', "unknown")
        self.operation_log.append(("delete", content_id))
        if content_id in self.content:
            del self.content[content_id]
    
    async def list_all(self) -> List[GeneratedContent]:
        """List all content (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.content.values())
    
    # Test helper methods
    def add_content(self, content: GeneratedContent) -> None:
        """Add content to mock repository."""
        content_id = getattr(content, 'id', str(uuid4()))
        self.content[content_id] = content
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.content.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockLLMCacheRepository:
    """Mock LLM cache repository for testing."""
    
    def __init__(self):
        self.cache_entries: Dict[str, LLMCacheEntry] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_key(self, cache_key: str) -> Optional[LLMCacheEntry]:
        """Find cache entry by key (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_key", cache_key))
        return self.cache_entries.get(cache_key)
    
    async def save(self, entry: LLMCacheEntry) -> None:
        """Save cache entry (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        cache_key = getattr(entry, 'key', str(uuid4()))
        self.operation_log.append(("save", cache_key))
        self.cache_entries[cache_key] = entry
    
    async def delete(self, entry: LLMCacheEntry) -> None:
        """Delete cache entry (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        cache_key = getattr(entry, 'key', "unknown")
        self.operation_log.append(("delete", cache_key))
        if cache_key in self.cache_entries:
            del self.cache_entries[cache_key]
    
    async def list_all(self) -> List[LLMCacheEntry]:
        """List all cache entries (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.cache_entries.values())
    
    async def cleanup_expired(self) -> int:
        """Cleanup expired entries (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("cleanup_expired", "*"))
        return 0  # Mock cleanup - no entries expired
    
    # Test helper methods
    def add_cache_entry(self, entry: LLMCacheEntry) -> None:
        """Add cache entry to mock repository."""
        cache_key = getattr(entry, 'key', str(uuid4()))
        self.cache_entries[cache_key] = entry
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.cache_entries.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockTokenUsageRepository:
    """Mock token usage repository for testing."""
    
    def __init__(self):
        self.usage_records: Dict[str, TokenUsageRecord] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock repository failure"
    
    async def find_by_id(self, record_id: str) -> Optional[TokenUsageRecord]:
        """Find usage record by ID (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_id", record_id))
        return self.usage_records.get(record_id)
    
    async def save(self, record: TokenUsageRecord) -> None:
        """Save usage record (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        record_id = getattr(record, 'id', str(uuid4()))
        self.operation_log.append(("save", record_id))
        self.usage_records[record_id] = record
    
    async def delete(self, record: TokenUsageRecord) -> None:
        """Delete usage record (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        record_id = getattr(record, 'id', "unknown")
        self.operation_log.append(("delete", record_id))
        if record_id in self.usage_records:
            del self.usage_records[record_id]
    
    async def list_all(self) -> List[TokenUsageRecord]:
        """List all usage records (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.usage_records.values())
    
    async def get_usage_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get usage statistics (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("get_usage_stats", f"{start_date}-{end_date}"))
        return {
            "total_tokens": 10000,
            "total_cost": 1.50,
            "requests": 50,
            "models": {"gpt-4o-mini": 8000, "gpt-4": 2000}
        }
    
    # Test helper methods
    def add_usage_record(self, record: TokenUsageRecord) -> None:
        """Add usage record to mock repository."""
        record_id = getattr(record, 'id', str(uuid4()))
        self.usage_records[record_id] = record
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.usage_records.clear()
        self.operation_log.clear()
        self.should_fail = False


# =============================================================================
# Service Mock Implementations
# =============================================================================

class MockPipelineValidationService:
    """Mock pipeline validation service for testing."""
    
    def __init__(self):
        self.validation_results: Dict[str, ValidationResult] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock validation service failure"
    
    def validate_template(self, template: PipelineTemplate) -> ValidationResult:
        """Validate pipeline template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = getattr(template, 'name', {}).value if hasattr(template, 'name') else "unknown"
        self.operation_log.append(("validate_template", template_key))
        
        # Return pre-configured result or default valid result
        if template_key in self.validation_results:
            return self.validation_results[template_key]
        
        # Default valid result
        return ValidationResult(
            issues=[],
            is_valid=True,
            summary="Template is valid"
        )
    
    def validate_step(self, step, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate pipeline step (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        step_name = getattr(step, 'name', "unknown")
        self.operation_log.append(("validate_step", step_name))
        
        return ValidationResult(
            issues=[],
            is_valid=True,
            summary=f"Step '{step_name}' is valid"
        )
    
    def validate_inputs(self, inputs, user_values: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate inputs (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("validate_inputs", str(len(inputs))))
        
        return ValidationResult(
            issues=[],
            is_valid=True,
            summary="Inputs are valid"
        )
    
    # Test helper methods
    def set_validation_result(self, template_name: str, result: ValidationResult) -> None:
        """Set validation result for a template."""
        self.validation_results[template_name] = result
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.validation_results.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockPipelineExecutionService:
    """Mock pipeline execution service for testing."""
    
    def __init__(self):
        self.execution_results: Dict[str, Dict[str, Any]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock execution service failure"
    
    async def execute_pipeline(self, pipeline: PipelineTemplate, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        pipeline_key = getattr(pipeline, 'name', {}).value if hasattr(pipeline, 'name') else "unknown"
        self.operation_log.append(("execute_pipeline", pipeline_key))
        
        # Return pre-configured result or default result
        if pipeline_key in self.execution_results:
            return self.execution_results[pipeline_key]
        
        return {
            "run_id": str(uuid4()),
            "status": "completed",
            "results": {"mock": "execution result"},
            "execution_time": 1.23
        }
    
    async def execute_step(self, step, context: Dict[str, Any]) -> Any:
        """Execute step (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        step_name = getattr(step, 'name', "unknown")
        self.operation_log.append(("execute_step", step_name))
        
        return f"Mock result for step: {step_name}"
    
    # Test helper methods
    def set_execution_result(self, pipeline_name: str, result: Dict[str, Any]) -> None:
        """Set execution result for a pipeline."""
        self.execution_results[pipeline_name] = result
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.execution_results.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockStepDependencyService:
    """Mock step dependency service for testing."""
    
    def __init__(self):
        self.dependency_graphs: Dict[str, List[str]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock dependency service failure"
    
    def resolve_execution_order(self, steps: Dict[str, Any]) -> List[str]:
        """Resolve step execution order (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("resolve_execution_order", str(len(steps))))
        
        # Return pre-configured order or simple list of keys
        pipeline_key = "_".join(sorted(steps.keys()))
        if pipeline_key in self.dependency_graphs:
            return self.dependency_graphs[pipeline_key]
        
        return list(steps.keys())
    
    def validate_dependencies(self, steps: Dict[str, Any]) -> List[str]:
        """Validate step dependencies (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("validate_dependencies", str(len(steps))))
        return []  # No errors in mock
    
    # Test helper methods
    def set_execution_order(self, pipeline_key: str, order: List[str]) -> None:
        """Set execution order for a pipeline."""
        self.dependency_graphs[pipeline_key] = order
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.dependency_graphs.clear()
        self.operation_log.clear()
        self.should_fail = False


# =============================================================================
# Additional Service Mock Implementations
# =============================================================================

class MockWorkspaceManagementService:
    """Mock workspace management service for testing."""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock workspace management service failure"
    
    async def create_workspace(self, name: WorkspaceName, path: WorkspacePath) -> Workspace:
        """Create workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("create_workspace", name.value))
        # Create mock workspace
        workspace = Mock(spec=Workspace)
        workspace.name = name
        workspace.path = path
        self.workspaces[name.value] = workspace
        return workspace
    
    async def delete_workspace(self, workspace: Workspace) -> None:
        """Delete workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        workspace_name = getattr(workspace, 'name', {}).value if hasattr(workspace, 'name') else "unknown"
        self.operation_log.append(("delete_workspace", workspace_name))
        if workspace_name in self.workspaces:
            del self.workspaces[workspace_name]
    
    async def list_workspaces(self) -> List[Workspace]:
        """List workspaces (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_workspaces", "*"))
        return list(self.workspaces.values())
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.workspaces.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockWorkspaceConfigurationService:
    """Mock workspace configuration service for testing."""
    
    def __init__(self):
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock workspace configuration service failure"
    
    async def get_config(self, workspace: WorkspaceName, key: str) -> Any:
        """Get config value (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("get_config", f"{workspace.value}:{key}"))
        workspace_config = self.configs.get(workspace.value, {})
        return workspace_config.get(key)
    
    async def set_config(self, workspace: WorkspaceName, key: str, value: Any) -> None:
        """Set config value (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("set_config", f"{workspace.value}:{key}"))
        if workspace.value not in self.configs:
            self.configs[workspace.value] = {}
        self.configs[workspace.value][key] = value
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.configs.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockWorkspaceAnalyticsService:
    """Mock workspace analytics service for testing."""
    
    def __init__(self):
        self.analytics_data: Dict[str, Dict[str, Any]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock workspace analytics service failure"
    
    async def get_usage_stats(self, workspace: WorkspaceName) -> Dict[str, Any]:
        """Get usage statistics (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("get_usage_stats", workspace.value))
        return self.analytics_data.get(workspace.value, {
            "total_pipelines": 0,
            "total_runs": 0,
            "storage_used": 0
        })
    
    async def track_pipeline_run(self, workspace: WorkspaceName, pipeline_id: str) -> None:
        """Track pipeline run (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("track_pipeline_run", f"{workspace.value}:{pipeline_id}"))
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.analytics_data.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockWorkspaceIsolationService:
    """Mock workspace isolation service for testing."""
    
    def __init__(self):
        self.isolation_violations: Dict[str, List[str]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock workspace isolation service failure"
    
    async def validate_isolation(self, workspace: WorkspaceName) -> List[str]:
        """Validate workspace isolation (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("validate_isolation", workspace.value))
        return self.isolation_violations.get(workspace.value, [])
    
    async def enforce_isolation(self, workspace: WorkspaceName) -> None:
        """Enforce workspace isolation (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("enforce_isolation", workspace.value))
    
    def set_isolation_violations(self, workspace: str, violations: List[str]) -> None:
        """Set isolation violations for testing."""
        self.isolation_violations[workspace] = violations
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.isolation_violations.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockWorkspaceTemplateService:
    """Mock workspace template service for testing."""
    
    def __init__(self):
        self.templates: Dict[str, List[str]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock workspace template service failure"
    
    async def get_available_templates(self, workspace: WorkspaceName) -> List[str]:
        """Get available templates (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("get_available_templates", workspace.value))
        return self.templates.get(workspace.value, [])
    
    async def import_template(self, workspace: WorkspaceName, template_name: str) -> None:
        """Import template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("import_template", f"{workspace.value}:{template_name}"))
        if workspace.value not in self.templates:
            self.templates[workspace.value] = []
        if template_name not in self.templates[workspace.value]:
            self.templates[workspace.value].append(template_name)
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.templates.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockTemplateManagementService:
    """Mock template management service for testing."""
    
    def __init__(self):
        self.templates: Dict[str, ContentTemplate] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock template management service failure"
    
    async def create_template(self, name: TemplateName, content: str) -> ContentTemplate:
        """Create template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("create_template", name.value))
        template = Mock(spec=ContentTemplate)
        template.name = name
        template.content = content
        self.templates[name.value] = template
        return template
    
    async def update_template(self, template: ContentTemplate) -> None:
        """Update template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_name = getattr(template, 'name', {}).value if hasattr(template, 'name') else "unknown"
        self.operation_log.append(("update_template", template_name))
        self.templates[template_name] = template
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.templates.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockStyleManagementService:
    """Mock style management service for testing."""
    
    def __init__(self):
        self.styles: Dict[str, StylePrimer] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock style management service failure"
    
    async def create_style(self, name: str, primer: str) -> StylePrimer:
        """Create style (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("create_style", name))
        style = Mock(spec=StylePrimer)
        style.name = name
        style.primer = primer
        self.styles[name] = style
        return style
    
    async def update_style(self, style: StylePrimer) -> None:
        """Update style (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        style_name = getattr(style, 'name', "unknown")
        self.operation_log.append(("update_style", style_name))
        self.styles[style_name] = style
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.styles.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockContentGenerationService:
    """Mock content generation service for testing."""
    
    def __init__(self):
        self.generated_content: Dict[str, str] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock content generation service failure"
    
    async def generate_content(self, template: ContentTemplate, context: Dict[str, Any]) -> str:
        """Generate content (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_name = getattr(template, 'name', {}).value if hasattr(template, 'name') else "unknown"
        self.operation_log.append(("generate_content", template_name))
        
        # Return pre-configured content or default
        key = f"{template_name}:{str(context)}"
        if key in self.generated_content:
            return self.generated_content[key]
        
        return f"Mock generated content for template: {template_name}"
    
    def set_generated_content(self, template_name: str, context: str, content: str) -> None:
        """Set generated content for testing."""
        key = f"{template_name}:{context}"
        self.generated_content[key] = content
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.generated_content.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockTemplateRenderingService:
    """Mock template rendering service for testing."""
    
    def __init__(self):
        self.rendered_templates: Dict[str, str] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock template rendering service failure"
    
    async def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render template (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        template_key = f"{hash(template_content)}:{str(variables)}"
        self.operation_log.append(("render_template", template_key))
        
        # Return pre-configured result or simple substitution
        if template_key in self.rendered_templates:
            return self.rendered_templates[template_key]
        
        return f"Rendered: {template_content} with {variables}"
    
    def set_rendered_result(self, template_content: str, variables: Dict[str, Any], result: str) -> None:
        """Set rendered result for testing."""
        template_key = f"{hash(template_content)}:{str(variables)}"
        self.rendered_templates[template_key] = result
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.rendered_templates.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockContentValidationService:
    """Mock content validation service for testing."""
    
    def __init__(self):
        self.validation_results: Dict[str, List[str]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock content validation service failure"
    
    async def validate_content(self, content: str, rules: List[str]) -> List[str]:
        """Validate content (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        content_key = hash(content)
        self.operation_log.append(("validate_content", str(content_key)))
        
        return self.validation_results.get(str(content_key), [])
    
    def set_validation_result(self, content: str, errors: List[str]) -> None:
        """Set validation result for testing."""
        content_key = str(hash(content))
        self.validation_results[content_key] = errors
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.validation_results.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockLLMOrchestrationService:
    """Mock LLM orchestration service for testing."""
    
    def __init__(self):
        self.llm_responses: Dict[str, str] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock LLM orchestration service failure"
    
    async def generate_response(self, prompt: str, model: str = "mock-model") -> str:
        """Generate LLM response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        prompt_key = f"{model}:{hash(prompt)}"
        self.operation_log.append(("generate_response", prompt_key))
        
        # Return pre-configured response or default
        if prompt_key in self.llm_responses:
            return self.llm_responses[prompt_key]
        
        return f"Mock LLM response for model {model}"
    
    async def stream_response(self, prompt: str, model: str = "mock-model") -> AsyncGenerator[str, None]:
        """Stream LLM response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        response = await self.generate_response(prompt, model)
        words = response.split()
        for word in words:
            await asyncio.sleep(0.01)  # Small delay for realistic streaming
            yield word + " "
    
    def set_response(self, prompt: str, model: str, response: str) -> None:
        """Set LLM response for testing."""
        prompt_key = f"{model}:{hash(prompt)}"
        self.llm_responses[prompt_key] = response
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.llm_responses.clear()
        self.operation_log.clear()
        self.should_fail = False


class MockCacheManagementService:
    """Mock cache management service for testing."""
    
    def __init__(self):
        self.cache_entries: Dict[str, Any] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock cache management service failure"
        self.hit_count = 0
        self.miss_count = 0
    
    async def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("get_cached_response", cache_key))
        
        if cache_key in self.cache_entries:
            self.hit_count += 1
            return self.cache_entries[cache_key]
        else:
            self.miss_count += 1
            return None
    
    async def cache_response(self, cache_key: str, response: Any, ttl: int = 3600) -> None:
        """Cache response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("cache_response", cache_key))
        self.cache_entries[cache_key] = response
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("invalidate_cache", pattern))
        # Simple pattern matching for mock
        removed = 0
        keys_to_remove = [key for key in self.cache_entries.keys() if pattern in key]
        for key in keys_to_remove:
            del self.cache_entries[key]
            removed += 1
        return removed
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (mock)."""
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "entries": len(self.cache_entries),
            "hit_rate": self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0
        }
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.cache_entries.clear()
        self.operation_log.clear()
        self.hit_count = 0
        self.miss_count = 0
        self.should_fail = False


class MockTokenAnalyticsService:
    """Mock token analytics service for testing."""
    
    def __init__(self):
        self.token_usage: Dict[str, Dict[str, Any]] = {}
        self.operation_log: List[tuple[str, str]] = []
        self.should_fail = False
        self.failure_message = "Mock token analytics service failure"
    
    async def track_token_usage(self, model: str, input_tokens: int, output_tokens: int, cost: float) -> None:
        """Track token usage (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("track_token_usage", f"{model}:{input_tokens}:{output_tokens}"))
        
        if model not in self.token_usage:
            self.token_usage[model] = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "request_count": 0
            }
        
        self.token_usage[model]["total_input_tokens"] += input_tokens
        self.token_usage[model]["total_output_tokens"] += output_tokens
        self.token_usage[model]["total_cost"] += cost
        self.token_usage[model]["request_count"] += 1
    
    async def get_usage_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get usage summary (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("get_usage_summary", f"{start_date}-{end_date}"))
        
        # Aggregate all model usage
        total_input = sum(usage["total_input_tokens"] for usage in self.token_usage.values())
        total_output = sum(usage["total_output_tokens"] for usage in self.token_usage.values())
        total_cost = sum(usage["total_cost"] for usage in self.token_usage.values())
        total_requests = sum(usage["request_count"] for usage in self.token_usage.values())
        
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "models": dict(self.token_usage)
        }
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.token_usage.clear()
        self.operation_log.clear()
        self.should_fail = False


# =============================================================================
# Mock Factory Functions
# =============================================================================

def create_complete_mock_repository_set() -> Dict[str, Any]:
    """Create a complete set of mock repositories for testing.
    
    Returns:
        Dictionary of all mock repositories keyed by interface name
    """
    return {
        "PipelineTemplateRepository": MockPipelineTemplateRepository(),
        "PipelineRunRepository": MockPipelineRunRepository(),
        "StepExecutionRepository": MockStepExecutionRepository(),
        "WorkspaceRepository": MockWorkspaceRepository(),
        "WorkspaceConfigRepository": MockWorkspaceConfigRepository(),
        "ContentTemplateRepository": MockContentTemplateRepository(),
        "StylePrimerRepository": MockStylePrimerRepository(),
        "GeneratedContentRepository": MockGeneratedContentRepository(),
        "LLMCacheRepository": MockLLMCacheRepository(),
        "TokenUsageRepository": MockTokenUsageRepository(),
    }


def create_complete_mock_service_set() -> Dict[str, Any]:
    """Create a complete set of mock services for testing.
    
    Returns:
        Dictionary of all mock services keyed by interface name
    """
    return {
        "PipelineValidationService": MockPipelineValidationService(),
        "PipelineExecutionService": MockPipelineExecutionService(),
        "StepDependencyService": MockStepDependencyService(),
        "WorkspaceManagementService": MockWorkspaceManagementService(),
        "WorkspaceConfigurationService": MockWorkspaceConfigurationService(),
        "WorkspaceAnalyticsService": MockWorkspaceAnalyticsService(),
        "WorkspaceIsolationService": MockWorkspaceIsolationService(),
        "WorkspaceTemplateService": MockWorkspaceTemplateService(),
        "TemplateManagementService": MockTemplateManagementService(),
        "StyleManagementService": MockStyleManagementService(),
        "ContentGenerationService": MockContentGenerationService(),
        "TemplateRenderingService": MockTemplateRenderingService(),
        "ContentValidationService": MockContentValidationService(),
        "LLMOrchestrationService": MockLLMOrchestrationService(),
        "CacheManagementService": MockCacheManagementService(),
        "TokenAnalyticsService": MockTokenAnalyticsService(),
    }


def create_full_mock_infrastructure() -> Dict[str, Any]:
    """Create a complete mock infrastructure with all repositories and services.
    
    Returns:
        Dictionary containing 'repositories' and 'services' sub-dictionaries
    """
    return {
        "repositories": create_complete_mock_repository_set(),
        "services": create_complete_mock_service_set(),
        "providers": {
            "LLMProvider": MockLLMProvider(),
            "EventBus": MockEventBus(),
            "DIContainer": MockDIContainer(),
        }
    }


def reset_all_mocks(infrastructure: Dict[str, Any]) -> None:
    """Reset all mocks in the provided infrastructure.
    
    Args:
        infrastructure: Infrastructure dictionary from create_full_mock_infrastructure()
    """
    for category in infrastructure.values():
        if isinstance(category, dict):
            for mock_obj in category.values():
                if hasattr(mock_obj, 'reset'):
                    mock_obj.reset()


def create_mock_pipeline_executor(
    llm_provider: Optional[MockLLMProvider] = None,
    event_bus: Optional[MockEventBus] = None
) -> Mock:
    """Create a mock pipeline executor for testing.
    
    Args:
        llm_provider: Optional mock LLM provider
        event_bus: Optional mock event bus
    
    Returns:
        Mock pipeline executor
    """
    if llm_provider is None:
        llm_provider = MockLLMProvider()
    
    if event_bus is None:
        event_bus = MockEventBus()
    
    executor = Mock(spec=PipelineExecutor)
    
    # Mock execution result
    mock_result = {
        "run_id": str(uuid4()),
        "status": "completed",
        "steps": {
            "outline": {
                "status": "completed",
                "result": "Mock outline result",
                "execution_time": 1.23
            },
            "content": {
                "status": "completed", 
                "result": "Mock content result",
                "execution_time": 2.45
            }
        },
        "total_execution_time": 3.68,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }
    
    # Configure mock methods
    executor.execute_pipeline = AsyncMock(return_value=mock_result)
    executor.execute_step = AsyncMock(return_value="Mock step result")
    executor.get_execution_status = Mock(return_value="completed")
    executor.cancel_execution = AsyncMock()
    
    # Attach mock dependencies
    executor.llm_provider = llm_provider
    executor.event_bus = event_bus
    
    return executor


class MockDIContainer:
    """Mock dependency injection container for testing."""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.singletons: Dict[str, Any] = {}
        self.factories: Dict[str, Callable] = {}
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton service."""
        self.singletons[name] = instance
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function."""
        self.factories[name] = factory
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self.services[name] = service
    
    def get(self, name: str) -> Any:
        """Get a service by name."""
        if name in self.singletons:
            return self.singletons[name]
        elif name in self.services:
            return self.services[name]
        elif name in self.factories:
            return self.factories[name]()
        else:
            raise KeyError(f"Service '{name}' not found")
    
    async def cleanup(self) -> None:
        """Cleanup all services (mock)."""
        pass
    
    def reset(self) -> None:
        """Reset all registered services."""
        self.services.clear()
        self.singletons.clear()
        self.factories.clear()


class TestDataFactory:
    """Factory for creating common test data structures."""
    
    @staticmethod
    def create_pipeline_yaml(name: str = "test-pipeline") -> Dict[str, Any]:
        """Create a test pipeline YAML structure."""
        return {
            "metadata": {
                "name": name,
                "description": f"Test pipeline: {name}",
                "version": "1.0.0"
            },
            "defaults": {
                "model": "mock-model"
            },
            "inputs": {
                "topic": {
                    "type": "text",
                    "label": "Topic",
                    "required": True,
                    "placeholder": "Enter topic..."
                },
                "style": {
                    "type": "choice",
                    "label": "Style",
                    "options": [
                        {"label": "Formal", "value": "formal"},
                        {"label": "Casual", "value": "casual"}
                    ],
                    "default": "formal"
                }
            },
            "steps": {
                "outline": {
                    "name": "Create Outline", 
                    "type": "llm_generate",
                    "prompt_template": "Create an outline for {{ inputs.topic }} in {{ inputs.style }} style.",
                    "model_preference": ["{{ defaults.model }}"]
                },
                "content": {
                    "name": "Write Content",
                    "type": "llm_generate", 
                    "prompt_template": "Based on this outline: {{ steps.outline }}\n\nWrite complete content about {{ inputs.topic }}.",
                    "depends_on": ["outline"],
                    "model_preference": ["{{ defaults.model }}"]
                }
            }
        }
    
    @staticmethod
    def create_pipeline_run_data(run_id: str = None) -> Dict[str, Any]:
        """Create test pipeline run data."""
        if run_id is None:
            run_id = str(uuid4())
        
        return {
            "run_id": run_id,
            "pipeline_id": "test-pipeline",
            "workspace_name": "test-workspace",
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "inputs": {
                "topic": "Test Topic",
                "style": "formal"
            },
            "steps": {
                "outline": {
                    "status": "completed",
                    "result": "1. Introduction\n2. Main Points\n3. Conclusion",
                    "execution_time": 1.5
                },
                "content": {
                    "status": "running",
                    "result": None,
                    "execution_time": None
                }
            },
            "metadata": {
                "version": "1.0.0",
                "model": "mock-model"
            }
        }
    
    @staticmethod
    def create_test_event(
        event_type: str = "TestEvent",
        aggregate_id: str = "test-aggregate",
        **data
    ) -> Dict[str, Any]:
        """Create test event data."""
        return {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": {
                "version": 1,
                "source": "test"
            }
        }


class MockAsyncContextManager:
    """Mock async context manager for testing."""
    
    def __init__(self, return_value: Any = None):
        self.return_value = return_value
        self.entered = False
        self.exited = False
        self.exception_info = None
    
    async def __aenter__(self):
        self.entered = True
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        self.exception_info = (exc_type, exc_val, exc_tb)
        return False  # Don't suppress exceptions
    
    def was_entered(self) -> bool:
        """Check if context was entered."""
        return self.entered
    
    def was_exited(self) -> bool:
        """Check if context was exited."""
        return self.exited
    
    def had_exception(self) -> bool:
        """Check if an exception occurred in the context."""
        return self.exception_info[0] is not None


def create_mock_async_generator(items: List[Any], delay: float = 0.01):
    """Create a mock async generator for testing.
    
    Args:
        items: List of items to yield
        delay: Delay between yields (for realistic async behavior)
    
    Returns:
        Async generator function
    """
    async def mock_generator():
        for item in items:
            if delay > 0:
                await asyncio.sleep(delay)
            yield item
    
    return mock_generator()


class MockWebSocketConnection:
    """Mock WebSocket connection for testing."""
    
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.received_messages: List[Dict[str, Any]] = []
        self.closed = False
        self.close_code = None
    
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON message (mock)."""
        if self.closed:
            raise RuntimeError("WebSocket is closed")
        self.sent_messages.append(data)
    
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON message (mock)."""
        if self.closed:
            raise RuntimeError("WebSocket is closed")
        if not self.received_messages:
            # Simulate waiting for message
            await asyncio.sleep(0.1)
            return {"type": "ping"}  # Default message
        return self.received_messages.pop(0)
    
    async def close(self, code: int = 1000) -> None:
        """Close connection (mock)."""
        self.closed = True
        self.close_code = code
    
    def add_received_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the received queue."""
        self.received_messages.append(message)
    
    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Get all sent messages."""
        return self.sent_messages.copy()
    
    def clear_messages(self) -> None:
        """Clear all message history."""
        self.sent_messages.clear()
        self.received_messages.clear()