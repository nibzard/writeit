"""Mock implementations for all domain service interfaces.

This module provides mock implementations of domain services for testing purposes.
All mocks support configurable behavior and state verification.

Mock Features:
- Configurable return values and error conditions
- Call tracking and behavior verification
- Realistic domain logic simulation
- Support for testing complex domain scenarios
"""

from .pipeline import (
    MockPipelineValidationService,
    MockPipelineExecutionService,
    MockStepDependencyService
)

from .workspace import (
    MockWorkspaceIsolationService,
    MockWorkspaceTemplateService
)

from .content import (
    MockTemplateRenderingService,
    MockContentValidationService
)

from .execution import (
    MockLLMOrchestrationService,
    MockCacheManagementService,
    MockTokenAnalyticsService
)

__all__ = [
    "MockPipelineValidationService",
    "MockPipelineExecutionService", 
    "MockStepDependencyService",
    "MockWorkspaceIsolationService",
    "MockWorkspaceTemplateService",
    "MockTemplateRenderingService",
    "MockContentValidationService",
    "MockLLMOrchestrationService",
    "MockCacheManagementService",
    "MockTokenAnalyticsService",
]
