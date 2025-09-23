"""Pipeline domain entity fixtures for testing.

Provides comprehensive test fixtures for pipeline domain entities including
templates, runs, steps, and step executions with various configurations.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional

from writeit.domains.pipeline.entities.pipeline_template import (
    PipelineTemplate, PipelineStepTemplate, PipelineInput
)
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.entities.pipeline_step import PipelineStep, StepExecution
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.step_id import StepId
from writeit.domains.pipeline.value_objects.step_name import StepName
from writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus


# ============================================================================
# Basic Entity Fixtures
# ============================================================================

@pytest.fixture
def pipeline_id_fixture():
    """Valid pipeline ID for testing."""
    return PipelineId.from_name("test-pipeline")

@pytest.fixture
def step_id_fixture():
    """Valid step ID for testing."""
    return StepId.from_name("test-step")

@pytest.fixture
def pipeline_input_fixture():
    """Valid pipeline input configuration."""
    return PipelineInput(
        key="topic",
        type="text",
        label="Topic",
        required=True,
        placeholder="Enter the topic...",
        help="The main topic for content generation",
        max_length=100,
        validation={"min_length": 3}
    )

@pytest.fixture
def pipeline_step_template_fixture():
    """Valid pipeline step template."""
    return PipelineStepTemplate(
        id=StepId.from_name("generate-content"),
        name="Generate Content",
        description="Generate content based on the topic",
        type="llm_generate",
        prompt_template=PromptTemplate.create("Write an article about {{ inputs.topic }}"),
        model_preference=ModelPreference.create(["gpt-4o-mini", "gpt-3.5-turbo"]),
        selection_prompt="Choose the best response:",
        validation={"min_length": 100},
        ui={"show_progress": True},
        depends_on=[],
        parallel=False,
        retry_config={"max_retries": 3, "delay_seconds": 1.0}
    )

@pytest.fixture
def pipeline_template_fixture():
    """Valid pipeline template with single step."""
    pipeline_id = PipelineId.from_name("test-pipeline")
    inputs = [
        PipelineInput(
            key="topic",
            type="text", 
            label="Topic",
            required=True,
            placeholder="Enter topic..."
        )
    ]
    steps = [
        PipelineStepTemplate(
            id=StepId.from_name("content"),
            name="Generate Content",
            description="Generate content about the topic",
            type="llm_generate",
            prompt_template=PromptTemplate.create("Write about {{ inputs.topic }}"),
            model_preference=ModelPreference.create(["gpt-4o-mini"])
        )
    ]
    
    return PipelineTemplate.create(
        name="Test Pipeline",
        description="A test pipeline for content generation",
        inputs=inputs,
        steps=steps,
        version="1.0.0",
        author="Test Author"
    )

@pytest.fixture 
def pipeline_run_fixture(pipeline_id_fixture):
    """Valid pipeline run."""
    return PipelineRun.create(
        id=f"run-{uuid4().hex[:8]}",
        pipeline_id=pipeline_id_fixture,
        pipeline_name="Test Pipeline",
        workspace_name="test-workspace",
        inputs={"topic": "Artificial Intelligence"},
        metadata={"created_by": "test_user"}
    )

@pytest.fixture
def step_execution_fixture():
    """Valid step execution."""
    return StepExecution.create(
        step_id=StepId.from_name("test-step"),
        step_name=StepName.from_user_input("Test Step"),
        max_retries=3,
        metadata={"step_type": "llm_generate"}
    )

@pytest.fixture
def pipeline_step_fixture():
    """Valid pipeline step configuration."""
    return PipelineStep.create(
        step_id=StepId.from_name("content-step"),
        name=StepName.from_user_input("Content Generation"),
        description="Generate content based on user input",
        step_type="llm_generate",
        prompt_template=PromptTemplate.create("Write about {{ topic }}"),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        timeout_seconds=120,
        retry_config={"max_retries": 3, "delay_seconds": 1.0},
        validation={"min_length": 100},
        ui_config={"show_tokens": True}
    )


# ============================================================================
# Complex Pipeline Fixtures
# ============================================================================

@pytest.fixture
def multi_step_pipeline():
    """Pipeline with multiple dependent steps."""
    pipeline_id = PipelineId.from_name("multi-step-pipeline")
    
    inputs = [
        PipelineInput(
            key="topic",
            type="text",
            label="Topic", 
            required=True
        ),
        PipelineInput(
            key="style",
            type="choice",
            label="Writing Style",
            required=True,
            options=[
                {"label": "Formal", "value": "formal"},
                {"label": "Casual", "value": "casual"}
            ]
        )
    ]
    
    # Create dependent steps
    outline_step = PipelineStepTemplate(
        id=StepId.from_name("outline"),
        name="Create Outline",
        description="Create article outline",
        type="llm_generate",
        prompt_template=PromptTemplate.create("Create an outline for {{ inputs.topic }}"),
        model_preference=ModelPreference.create(["gpt-4o-mini"])
    )
    
    content_step = PipelineStepTemplate(
        id=StepId.from_name("content"),
        name="Write Content", 
        description="Write full content",
        type="llm_generate",
        prompt_template=PromptTemplate.create(
            "Based on this outline: {{ steps.outline }}, write content about {{ inputs.topic }} in {{ inputs.style }} style"
        ),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        depends_on=[outline_step.id]
    )
    
    review_step = PipelineStepTemplate(
        id=StepId.from_name("review"),
        name="Review Content",
        description="Review and improve content",
        type="llm_generate", 
        prompt_template=PromptTemplate.create("Review and improve: {{ steps.content }}"),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        depends_on=[content_step.id]
    )
    
    steps = [outline_step, content_step, review_step]
    
    return PipelineTemplate.create(
        name="Multi-Step Content Pipeline",
        description="Pipeline with dependent steps for content creation",
        inputs=inputs,
        steps=steps,
        version="2.0.0",
        author="Test Author",
        tags=["content", "multi-step"]
    )

@pytest.fixture
def parallel_step_pipeline():
    """Pipeline with parallel executable steps."""
    pipeline_id = PipelineId.from_name("parallel-pipeline")
    
    inputs = [
        PipelineInput(key="topic", type="text", label="Topic", required=True)
    ]
    
    # Create parallel steps
    summary_step = PipelineStepTemplate(
        id=StepId.from_name("summary"),
        name="Generate Summary",
        description="Generate topic summary",
        type="llm_generate",
        prompt_template=PromptTemplate.create("Write a summary of {{ inputs.topic }}"),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        parallel=True
    )
    
    keywords_step = PipelineStepTemplate(
        id=StepId.from_name("keywords"),
        name="Extract Keywords",
        description="Extract relevant keywords", 
        type="llm_generate",
        prompt_template=PromptTemplate.create("Extract keywords from {{ inputs.topic }}"),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        parallel=True
    )
    
    combine_step = PipelineStepTemplate(
        id=StepId.from_name("combine"),
        name="Combine Results",
        description="Combine summary and keywords",
        type="llm_generate",
        prompt_template=PromptTemplate.create(
            "Combine summary: {{ steps.summary }} with keywords: {{ steps.keywords }}"
        ),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        depends_on=[summary_step.id, keywords_step.id]
    )
    
    steps = [summary_step, keywords_step, combine_step]
    
    return PipelineTemplate.create(
        name="Parallel Processing Pipeline",
        description="Pipeline with parallel steps",
        inputs=inputs,
        steps=steps,
        version="1.0.0",
        tags=["parallel", "performance"]
    )

@pytest.fixture 
def conditional_pipeline():
    """Pipeline with conditional step execution."""
    pipeline_id = PipelineId.from_name("conditional-pipeline")
    
    inputs = [
        PipelineInput(key="content_type", type="choice", label="Content Type", required=True,
                     options=[{"label": "Article", "value": "article"}, 
                             {"label": "Blog Post", "value": "blog"}]),
        PipelineInput(key="topic", type="text", label="Topic", required=True)
    ]
    
    # Conditional steps based on content type
    article_step = PipelineStepTemplate(
        id=StepId.from_name("article"),
        name="Generate Article",
        description="Generate formal article",
        type="conditional",
        prompt_template=PromptTemplate.create(
            "Write a formal article about {{ inputs.topic }}"
        ),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        validation={"condition": "inputs.content_type == 'article'"}
    )
    
    blog_step = PipelineStepTemplate(
        id=StepId.from_name("blog"),
        name="Generate Blog Post",
        description="Generate casual blog post",
        type="conditional",
        prompt_template=PromptTemplate.create(
            "Write a casual blog post about {{ inputs.topic }}"
        ),
        model_preference=ModelPreference.create(["gpt-4o-mini"]),
        validation={"condition": "inputs.content_type == 'blog'"}
    )
    
    steps = [article_step, blog_step]
    
    return PipelineTemplate.create(
        name="Conditional Content Pipeline",
        description="Pipeline with conditional execution",
        inputs=inputs,
        steps=steps,
        version="1.0.0",
        tags=["conditional", "flexible"]
    )


# ============================================================================
# Pipeline Run State Fixtures
# ============================================================================

@pytest.fixture
def running_pipeline_run(pipeline_id_fixture):
    """Pipeline run in running state."""
    run = PipelineRun.create(
        id=f"run-{uuid4().hex[:8]}",
        pipeline_id=pipeline_id_fixture,
        workspace_name="test-workspace",
        inputs={"topic": "Machine Learning"}
    )
    return run.start()

@pytest.fixture
def completed_pipeline_run(pipeline_id_fixture):
    """Pipeline run in completed state."""
    run = PipelineRun.create(
        id=f"run-{uuid4().hex[:8]}",
        pipeline_id=pipeline_id_fixture,
        workspace_name="test-workspace", 
        inputs={"topic": "Deep Learning"}
    )
    run = run.start()
    return run.complete(outputs={"content": "Generated content about Deep Learning"})

@pytest.fixture
def failed_pipeline_run(pipeline_id_fixture):
    """Pipeline run in failed state."""
    run = PipelineRun.create(
        id=f"run-{uuid4().hex[:8]}",
        pipeline_id=pipeline_id_fixture,
        workspace_name="test-workspace",
        inputs={"topic": "Neural Networks"}
    )
    run = run.start()
    return run.fail("Model API unavailable")

@pytest.fixture
def cancelled_pipeline_run(pipeline_id_fixture):
    """Pipeline run in cancelled state."""
    run = PipelineRun.create(
        id=f"run-{uuid4().hex[:8]}",
        pipeline_id=pipeline_id_fixture,
        workspace_name="test-workspace",
        inputs={"topic": "Computer Vision"}
    )
    run = run.start()
    return run.cancel()


# ============================================================================
# Step Execution State Fixtures
# ============================================================================

@pytest.fixture
def running_step_execution():
    """Step execution in running state."""
    execution = StepExecution.create(
        step_id=StepId.from_name("content-step"),
        step_name=StepName.from_user_input("Content Generation")
    )
    return execution.start(inputs={"topic": "Artificial Intelligence"})

@pytest.fixture
def completed_step_execution():
    """Step execution in completed state."""
    execution = StepExecution.create(
        step_id=StepId.from_name("content-step"),
        step_name=StepName.from_user_input("Content Generation")
    )
    execution = execution.start(inputs={"topic": "Robotics"})
    return execution.complete(outputs={"content": "Generated robotics content"})

@pytest.fixture
def failed_step_execution():
    """Step execution in failed state."""
    execution = StepExecution.create(
        step_id=StepId.from_name("content-step"),
        step_name=StepName.from_user_input("Content Generation")
    )
    execution = execution.start(inputs={"topic": "Quantum Computing"})
    return execution.fail("Token limit exceeded")

@pytest.fixture
def waiting_step_execution():
    """Step execution waiting for user input."""
    execution = StepExecution.create(
        step_id=StepId.from_name("review-step"),
        step_name=StepName.from_user_input("Content Review")
    )
    execution = execution.start(inputs={"content": "Draft content"})
    return execution.wait_for_input()


# ============================================================================
# Invalid/Edge Case Fixtures
# ============================================================================

@pytest.fixture
def invalid_pipeline_template():
    """Invalid pipeline template for negative testing."""
    # Missing required fields, circular dependencies, etc.
    invalid_steps = [
        PipelineStepTemplate(
            id=StepId.from_name("step1"),
            name="Step 1", 
            description="First step",
            type="llm_generate",
            prompt_template=PromptTemplate.create("{{ step2_output }}"),
            model_preference=ModelPreference.create(["gpt-4o-mini"]),
            depends_on=[StepId.from_name("step2")]  # Circular dependency
        ),
        PipelineStepTemplate(
            id=StepId.from_name("step2"),
            name="Step 2",
            description="Second step", 
            type="llm_generate",
            prompt_template=PromptTemplate.create("{{ step1_output }}"),
            model_preference=ModelPreference.create(["gpt-4o-mini"]),
            depends_on=[StepId.from_name("step1")]  # Circular dependency
        )
    ]
    
    return {
        "circular_dependency": {
            "name": "Invalid Pipeline",
            "description": "Pipeline with circular dependencies",
            "inputs": [],
            "steps": invalid_steps
        },
        "empty_steps": {
            "name": "Empty Pipeline",
            "description": "Pipeline with no steps",
            "inputs": [],
            "steps": []
        },
        "invalid_step_type": {
            "name": "Invalid Step Type Pipeline",
            "description": "Pipeline with invalid step type",
            "inputs": [],
            "steps": [
                PipelineStepTemplate(
                    id=StepId.from_name("invalid"),
                    name="Invalid Step",
                    description="Step with invalid type",
                    type="invalid_type",  # Invalid step type
                    prompt_template=PromptTemplate.create("Generate content"),
                    model_preference=ModelPreference.create(["gpt-4o-mini"])
                )
            ]
        }
    }

@pytest.fixture
def edge_case_pipeline_inputs():
    """Edge case pipeline inputs for boundary testing."""
    return {
        "empty_topic": {"topic": ""},
        "very_long_topic": {"topic": "x" * 1000},
        "special_chars": {"topic": "Test with special chars: @#$%^&*()"},
        "unicode": {"topic": "Test with unicode: 🚀 émojis 中文"},
        "missing_required": {},  # Missing required topic
        "extra_fields": {"topic": "AI", "unexpected": "value"},
        "null_values": {"topic": None},
        "numeric_topic": {"topic": 12345}
    }


# ============================================================================
# Factory Fixtures
# ============================================================================

@pytest.fixture
def pipeline_factory():
    """Factory for creating pipeline entities with custom parameters."""
    class PipelineFactory:
        @staticmethod
        def create_template(
            name: str = None,
            num_steps: int = 1,
            has_dependencies: bool = False,
            **kwargs
        ) -> PipelineTemplate:
            """Create pipeline template with specified characteristics."""
            pipeline_name = name or f"test-pipeline-{uuid4().hex[:8]}"
            
            inputs = [
                PipelineInput(key="topic", type="text", label="Topic", required=True)
            ]
            
            steps = []
            for i in range(num_steps):
                step_id = StepId.from_name(f"step-{i}")
                depends_on = [StepId.from_name(f"step-{i-1}")] if has_dependencies and i > 0 else []
                
                step = PipelineStepTemplate(
                    id=step_id,
                    name=f"Step {i+1}",
                    description=f"Step {i+1} description",
                    type="llm_generate",
                    prompt_template=PromptTemplate.create(f"Execute step {i+1} for {{{{ inputs.topic }}}}"),
                    model_preference=ModelPreference.create(["gpt-4o-mini"]),
                    depends_on=depends_on
                )
                steps.append(step)
            
            return PipelineTemplate.create(
                name=pipeline_name,
                description=f"Test pipeline with {num_steps} steps",
                inputs=inputs,
                steps=steps,
                **kwargs
            )
        
        @staticmethod
        def create_run(
            pipeline_template: PipelineTemplate = None,
            status: str = "created",
            **kwargs
        ) -> PipelineRun:
            """Create pipeline run with specified state."""
            if pipeline_template is None:
                pipeline_template = PipelineFactory.create_template()
            
            run = PipelineRun.create(
                id=f"run-{uuid4().hex[:8]}",
                pipeline_id=pipeline_template.id,
                pipeline_name=pipeline_template.name,
                workspace_name="test-workspace",
                inputs={"topic": "Test Topic"},
                **kwargs
            )
            
            if status == "running":
                run = run.start()
            elif status == "completed":
                run = run.start().complete(outputs={"result": "Test output"})
            elif status == "failed":
                run = run.start().fail("Test error")
            elif status == "cancelled":
                run = run.start().cancel()
            
            return run
    
    return PipelineFactory()

# ============================================================================
# Valid/Invalid Entity Collections
# ============================================================================

@pytest.fixture
def valid_pipeline_template(pipeline_template_fixture):
    """Valid pipeline template for positive testing."""
    return pipeline_template_fixture

@pytest.fixture
def valid_pipeline_run(pipeline_run_fixture):
    """Valid pipeline run for positive testing."""
    return pipeline_run_fixture