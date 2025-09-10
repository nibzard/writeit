# ABOUTME: Token usage tracking for LLM calls in WriteIt pipelines
# ABOUTME: Provides models and utilities for monitoring token consumption and costs

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal


@dataclass
class TokenUsage:
    """Token usage data for a single LLM call."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    details: Optional[Dict[str, Any]] = None
    
    @property
    def cost_estimate(self) -> Optional[Decimal]:
        """Estimate cost based on typical pricing (placeholder for model-specific pricing)."""
        # This would need model-specific pricing data
        return None
    
    @classmethod
    def from_llm_response(cls, response) -> 'TokenUsage':
        """Create TokenUsage from LLM response usage data."""
        try:
            usage = response.usage()
            return cls(
                input_tokens=usage.input,
                output_tokens=usage.output,
                total_tokens=usage.input + usage.output,
                details=usage.details if hasattr(usage, 'details') else None
            )
        except (AttributeError, TypeError):
            # Fallback if usage() not available or returns unexpected format
            return cls(input_tokens=0, output_tokens=0, total_tokens=0)


@dataclass
class StepTokenUsage:
    """Token usage for a single pipeline step."""
    step_key: str
    step_name: str
    model_name: str
    usage: TokenUsage
    timestamp: datetime = field(default_factory=datetime.now)
    regeneration_count: int = 0


@dataclass
class PipelineRunTokens:
    """Aggregated token usage for an entire pipeline run."""
    pipeline_name: str
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[StepTokenUsage] = field(default_factory=list)
    
    @property
    def total_input_tokens(self) -> int:
        """Total input tokens across all steps."""
        return sum(step.usage.input_tokens for step in self.steps)
    
    @property
    def total_output_tokens(self) -> int:
        """Total output tokens across all steps."""
        return sum(step.usage.output_tokens for step in self.steps)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens across all steps."""
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def by_model(self) -> Dict[str, TokenUsage]:
        """Group token usage by model."""
        by_model = {}
        for step in self.steps:
            model = step.model_name
            if model not in by_model:
                by_model[model] = TokenUsage(0, 0, 0)
            
            existing = by_model[model]
            by_model[model] = TokenUsage(
                input_tokens=existing.input_tokens + step.usage.input_tokens,
                output_tokens=existing.output_tokens + step.usage.output_tokens,
                total_tokens=existing.total_tokens + step.usage.total_tokens
            )
        
        return by_model
    
    def add_step_usage(self, step_key: str, step_name: str, model_name: str, 
                      response) -> StepTokenUsage:
        """Add token usage for a pipeline step."""
        usage = TokenUsage.from_llm_response(response)
        step_usage = StepTokenUsage(
            step_key=step_key,
            step_name=step_name,
            model_name=model_name,
            usage=usage
        )
        
        # Check if this step already exists (regeneration)
        existing_step = None
        for i, existing in enumerate(self.steps):
            if existing.step_key == step_key:
                existing_step = existing
                existing.regeneration_count += 1
                self.steps[i] = step_usage
                step_usage.regeneration_count = existing.regeneration_count
                break
        
        if not existing_step:
            self.steps.append(step_usage)
        
        return step_usage
    
    def finish_run(self) -> None:
        """Mark the pipeline run as completed."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'pipeline_name': self.pipeline_name,
            'run_id': self.run_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_tokens,
            'by_model': {
                model: {
                    'input_tokens': usage.input_tokens,
                    'output_tokens': usage.output_tokens,
                    'total_tokens': usage.total_tokens
                }
                for model, usage in self.by_model.items()
            },
            'steps': [
                {
                    'step_key': step.step_key,
                    'step_name': step.step_name,
                    'model_name': step.model_name,
                    'timestamp': step.timestamp.isoformat(),
                    'regeneration_count': step.regeneration_count,
                    'usage': {
                        'input_tokens': step.usage.input_tokens,
                        'output_tokens': step.usage.output_tokens,
                        'total_tokens': step.usage.total_tokens,
                        'details': step.usage.details
                    }
                }
                for step in self.steps
            ]
        }


class TokenUsageTracker:
    """Manages token usage tracking across pipeline runs."""
    
    def __init__(self) -> None:
        self.current_run: Optional[PipelineRunTokens] = None
        self.completed_runs: List[PipelineRunTokens] = []
    
    def start_pipeline_run(self, pipeline_name: str, run_id: str) -> PipelineRunTokens:
        """Start tracking a new pipeline run."""
        self.current_run = PipelineRunTokens(
            pipeline_name=pipeline_name,
            run_id=run_id,
            start_time=datetime.now()
        )
        return self.current_run
    
    def track_step_usage(self, step_key: str, step_name: str, model_name: str, 
                        response) -> Optional[StepTokenUsage]:
        """Track token usage for a pipeline step."""
        if not self.current_run:
            return None
        
        return self.current_run.add_step_usage(step_key, step_name, model_name, response)
    
    def finish_current_run(self) -> Optional[PipelineRunTokens]:
        """Complete the current pipeline run and move to completed runs."""
        if not self.current_run:
            return None
        
        self.current_run.finish_run()
        self.completed_runs.append(self.current_run)
        finished_run = self.current_run
        self.current_run = None
        return finished_run
    
    def get_total_usage(self) -> Dict[str, int]:
        """Get total token usage across all completed runs."""
        total_input = sum(run.total_input_tokens for run in self.completed_runs)
        total_output = sum(run.total_output_tokens for run in self.completed_runs)
        
        return {
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'total_tokens': total_input + total_output,
            'completed_runs': len(self.completed_runs)
        }
