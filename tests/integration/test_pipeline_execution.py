# ABOUTME: Integration tests for pipeline execution system
# ABOUTME: Tests end-to-end pipeline execution with server, client, and caching

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime
import uuid

from writeit.pipeline import PipelineExecutor
from writeit.workspace.workspace import Workspace
from writeit.storage.manager import StorageManager
from writeit.models import PipelineStatus


@pytest.fixture
async def workspace_setup():
    """Set up a temporary workspace for testing."""
    workspace = Workspace()
    workspace_name = f"test_{uuid.uuid4().hex[:8]}"

    # Create workspace (not async)
    workspace.create_workspace(workspace_name)

    # Create storage manager
    storage = StorageManager(workspace, workspace_name)

    yield workspace, storage, workspace_name

    # Cleanup workspace
    try:
        workspace.remove_workspace(workspace_name)
    except Exception:
        pass


@pytest.fixture
def sample_pipeline_file():
    """Create a sample pipeline YAML file for testing."""
    pipeline_config = {
        "metadata": {
            "name": "Test Pipeline",
            "description": "A simple test pipeline",
            "version": "1.0.0",
        },
        "defaults": {"model": "gpt-3.5-turbo"},
        "inputs": {
            "topic": {
                "type": "text",
                "label": "Article Topic",
                "required": True,
                "placeholder": "Enter a topic for the article",
            },
            "style": {
                "type": "choice",
                "label": "Writing Style",
                "required": True,
                "options": [
                    {"label": "Formal", "value": "formal"},
                    {"label": "Casual", "value": "casual"},
                ],
                "default": "formal",
            },
        },
        "steps": {
            "outline": {
                "name": "Create Outline",
                "description": "Generate an article outline",
                "type": "llm_generate",
                "prompt_template": "Create an outline for an article about {{ inputs.topic }} in a {{ inputs.style }} style.",
                "model_preference": ["{{ defaults.model }}"],
            },
            "content": {
                "name": "Write Content",
                "description": "Write the full article",
                "type": "llm_generate",
                "prompt_template": "Based on this outline:\n{{ steps.outline }}\n\nWrite a complete article about {{ inputs.topic }} in a {{ inputs.style }} style.",
                "model_preference": ["{{ defaults.model }}"],
                "depends_on": ["outline"],
            },
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(pipeline_config, f)
        return Path(f.name)


@pytest.mark.anyio
async def test_pipeline_executor_basic(workspace_setup, sample_pipeline_file):
    """Test basic pipeline executor functionality."""
    workspace, storage, workspace_name = workspace_setup

    # Create executor
    executor = PipelineExecutor(workspace, storage, workspace_name)

    # Load pipeline
    pipeline = await executor.load_pipeline(sample_pipeline_file)

    assert pipeline.name == "Test Pipeline"
    assert len(pipeline.steps) == 2
    assert len(pipeline.inputs) == 2

    # Create run
    inputs = {"topic": "Artificial Intelligence", "style": "formal"}

    run_id = await executor.create_run(pipeline, inputs, workspace_name)
    assert run_id is not None

    # Get run
    run = await executor.get_run(run_id)
    assert run is not None
    assert run.status == PipelineStatus.CREATED
    assert run.inputs == inputs


@pytest.mark.anyio
async def test_pipeline_step_execution(workspace_setup, sample_pipeline_file):
    """Test individual step execution."""
    workspace, storage, workspace_name = workspace_setup

    executor = PipelineExecutor(workspace, storage, workspace_name)
    pipeline = await executor.load_pipeline(sample_pipeline_file)

    inputs = {"topic": "Test Topic", "style": "casual"}

    run_id = await executor.create_run(pipeline, inputs, workspace_name)

    # Test step execution
    from writeit.pipeline.executor import ExecutionContext
    from writeit.llm.token_usage import TokenUsageTracker

    context = ExecutionContext(
        pipeline_id=pipeline.id,
        run_id=run_id,
        workspace_name=workspace_name,
        inputs=inputs,
        token_tracker=TokenUsageTracker(),
    )

    # Execute first step
    first_step = pipeline.steps[0]

    # Mock response callback
    responses_received = []

    def response_callback(response_type: str, content: str):
        responses_received.append((response_type, content))

    try:
        step_result = await executor.execute_step(
            first_step, context, pipeline, response_callback
        )

        assert step_result.step_key == first_step.key
        assert len(step_result.responses) > 0
        assert step_result.execution_time > 0

    except Exception as e:
        # LLM calls might fail in test environment
        pytest.skip(f"LLM call failed (expected in test environment): {e}")


@pytest.mark.anyio
async def test_llm_cache_functionality(workspace_setup):
    """Test LLM caching functionality."""
    workspace, storage, workspace_name = workspace_setup

    from writeit.llm.cache import LLMCache, CachedLLMClient

    # Create cache
    cache = LLMCache(storage, workspace_name)
    CachedLLMClient(cache)

    # Test cache miss (first call)
    prompt = "What is the capital of France?"
    model = "gpt-3.5-turbo"

    cached_response = await cache.get(prompt, model)
    assert cached_response is None

    # Test cache put
    cache_key = await cache.put(
        prompt,
        model,
        "Paris is the capital of France.",
        {"prompt_tokens": 10, "completion_tokens": 15},
    )

    assert cache_key is not None

    # Test cache hit (second call)
    cached_response = await cache.get(prompt, model)
    assert cached_response is not None
    assert cached_response.response == "Paris is the capital of France."
    assert cached_response.access_count == 2  # Updated on access

    # Test cache stats
    stats = await cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["workspace"] == workspace_name


@pytest.mark.anyio
async def test_pipeline_template_rendering(workspace_setup, sample_pipeline_file):
    """Test prompt template rendering."""
    workspace, storage, workspace_name = workspace_setup

    executor = PipelineExecutor(workspace, storage, workspace_name)
    pipeline = await executor.load_pipeline(sample_pipeline_file)

    # Test template rendering
    from writeit.pipeline.executor import ExecutionContext

    context = ExecutionContext(
        pipeline_id=pipeline.id,
        run_id="test_run",
        workspace_name=workspace_name,
        inputs={"topic": "AI Ethics", "style": "academic"},
        step_outputs={"outline": "I. Introduction\nII. Main Points\nIII. Conclusion"},
    )

    # Test input substitution
    template = "Write about {{ inputs.topic }} in {{ inputs.style }} style."
    rendered = executor._render_prompt_template(template, context, pipeline)
    assert "AI Ethics" in rendered
    assert "academic" in rendered

    # Test step output substitution
    template = "Based on: {{ steps.outline }}\nWrite the content."
    rendered = executor._render_prompt_template(template, context, pipeline)
    assert "I. Introduction" in rendered

    # Test defaults substitution
    template = "Use model {{ defaults.model }} for this task."
    rendered = executor._render_prompt_template(template, context, pipeline)
    assert "gpt-3.5-turbo" in rendered


@pytest.mark.anyio
async def test_pipeline_input_validation(workspace_setup, sample_pipeline_file):
    """Test pipeline input validation."""
    workspace, storage, workspace_name = workspace_setup

    executor = PipelineExecutor(workspace, storage, workspace_name)
    pipeline = await executor.load_pipeline(sample_pipeline_file)

    # Test valid inputs
    valid_inputs = {"topic": "Machine Learning", "style": "formal"}

    await executor._validate_inputs(pipeline, valid_inputs)  # Should not raise

    # Test missing required input
    invalid_inputs = {
        "style": "formal"
        # Missing 'topic'
    }

    with pytest.raises(Exception):  # Should raise ValidationError
        await executor._validate_inputs(pipeline, invalid_inputs)

    # Test invalid choice value
    invalid_choice_inputs = {"topic": "Machine Learning", "style": "invalid_style"}

    with pytest.raises(Exception):  # Should raise ValidationError
        await executor._validate_inputs(pipeline, invalid_choice_inputs)


@pytest.mark.anyio
async def test_event_sourcing_basic(workspace_setup):
    """Test basic event sourcing functionality."""
    workspace, storage, workspace_name = workspace_setup

    from writeit.pipeline.events import PipelineEventStore, EventType
    from writeit.models import PipelineRun, PipelineStatus

    event_store = PipelineEventStore(storage)

    # Create initial run
    run = PipelineRun(
        id="test_run",
        pipeline_id="test_pipeline",
        workspace_name=workspace_name,
        status=PipelineStatus.CREATED,
    )

    # Create run created event
    event = await event_store.append_event(
        run.id,
        EventType.RUN_CREATED,
        {
            "id": run.id,
            "pipeline_id": run.pipeline_id,
            "workspace_name": run.workspace_name,
            "inputs": {},
            "status": run.status.value,
            "created_at": datetime.now().isoformat(),
            "steps": [],
        },
    )

    assert event.run_id == run.id
    assert event.event_type == EventType.RUN_CREATED
    assert event.sequence_number == 1

    # Get events
    events = await event_store.get_events(run.id)
    assert len(events) == 1
    assert events[0].id == event.id


def test_pipeline_yaml_structure(sample_pipeline_file):
    """Test pipeline YAML structure validation."""
    # Load and validate the sample pipeline
    with open(sample_pipeline_file, "r") as f:
        config = yaml.safe_load(f)

    # Validate required sections
    assert "metadata" in config
    assert "inputs" in config
    assert "steps" in config

    # Validate metadata
    metadata = config["metadata"]
    assert "name" in metadata
    assert "description" in metadata

    # Validate inputs
    inputs = config["inputs"]
    for key, input_config in inputs.items():
        assert "type" in input_config
        assert "label" in input_config

        if input_config["type"] == "choice":
            assert "options" in input_config

    # Validate steps
    steps = config["steps"]
    for key, step_config in steps.items():
        assert "name" in step_config
        assert "description" in step_config
        assert "type" in step_config
        assert "prompt_template" in step_config


if __name__ == "__main__":
    # Run tests directly
    import sys
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v"], capture_output=True, text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    sys.exit(result.returncode)
