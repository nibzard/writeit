# WriteIt Quickstart Guide

**Phase 1 Design Artifact** | **Date**: 2025-09-08

## Overview

This quickstart guide demonstrates WriteIt's complete article generation pipeline from initial setup through final export. It serves as both user documentation and integration test specification.

## Prerequisites

### System Requirements
- Python 3.11+
- Terminal with 256 color support
- Internet connection for AI model access
- ~500MB disk space for dependencies and artifacts

### AI Provider Setup
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install WriteIt with LLM providers
uv tool install writeit[openai,anthropic]

# Configure API keys
llm keys set openai
llm keys set anthropic

# Verify provider access
llm models list
```

### Initial Configuration
```bash
# Initialize WriteIt (creates ~/.writeit centralized storage)
writeit init

# Verify installation
writeit --version
# Expected: WriteIt 0.1.0

# Create a workspace for your articles
writeit workspace create my-articles

# Switch to your new workspace
writeit workspace use my-articles

# Check available pipelines (works from any directory now!)
writeit list-pipelines
# Expected: tech-article.yaml, blog-post.yaml, research-summary.yaml
```

## Basic Pipeline Execution

### Step 1: Start New Article Pipeline

```bash
# Launch WriteIt TUI (runs from any directory - uses active workspace)
writeit run tech-article.yaml

# Alternative: Use specific workspace
writeit --workspace my-articles run tech-article.yaml

# Alternative: Use global template
writeit run --global tech-article.yaml
```

**Expected TUI State**:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 1/4: angles (outline → draft → polish remaining)      │
├────────────────────────────────────────────────────────────┤
│ Initial Inputs:                                            │
│ ┌─ Source Material ─────────────────────────────────────────┐ │
│ │ [Empty text input field - cursor here]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌─ Target Audience ─────────────────────────────────────────┐ │
│ │ technical professionals                                 │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [Tab] Next Field [Enter] Start Pipeline [Ctrl+Q] Quit     │
└────────────────────────────────────────────────────────────┘
```

### Step 2: Provide Initial Inputs

**Input Source Material**:
```
Recent advances in WebAssembly (WASM) are enabling new possibilities for 
running complex applications in browsers. Major companies like Google, 
Mozilla, and Microsoft are investing heavily in WASM toolchains. 
Performance benchmarks show 90%+ native speed in many cases.
```

**Input Target Audience**: `technical professionals` (default)

Press `[Enter]` to start pipeline execution.

### Step 3: Angles Generation

**Expected TUI State During Generation**:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 1/4: angles (outline → draft → polish remaining)      │
├────────────────────────────────────────────────────────────┤
│ Input from user:                                           │
│ ┌─ Source Material ──────────────────────────────────────┐ │
│ │ Recent advances in WebAssembly (WASM) are enabling... │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o, claude-sonnet-4              [⚡ Streaming] │
│ ┌─ Response 1: gpt-4o ───────────────────────────────────────┐ │
│ │ # Three Article Angles for WebAssembly Advances        │ │
│ │                                                         │ │
│ │ ## 1. The Performance Revolution                        │ │
│ │ Focus on the 90%+ native speed benchmarks and what...  │ │
│ │ [content continues to stream in real-time...]          │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌─ Response 2: claude-sonnet-4 ──────────────────────────────┐ │
│ │ [Waiting for response...]                               │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [Streaming responses from AI models...]                   │
└────────────────────────────────────────────────────────────┘
```

**After Both Responses Complete**:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 1/4: angles (outline → draft → polish remaining)      │
├────────────────────────────────────────────────────────────┤
│ ┌─ Response 1: gpt-4o ───────────────────────────────────────┐ │
│ │ # Three Article Angles for WebAssembly Advances        │ │
│ │ ## 1. The Performance Revolution                        │ │
│ │ ## 2. Enterprise Adoption Patterns                     │ │
│ │ ## 3. Developer Experience Transformation              │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌─ Response 2: claude-sonnet-4 ──────────────────────────────┐ │
│ │ # WebAssembly Article Angles                            │ │
│ │ ## A. Breaking Browser Performance Barriers            │ │
│ │ ## B. The New Server-Side Runtime                      │ │
│ │ ## C. Security and Sandboxing Revolution               │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Your feedback for next step:                              │ │
│ ┌─ Comments ──────────────────────────────────────────────┐ │
│ │ Focus on angle 1 - performance story is most compelling│ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [1] Select Response 1 [2] Select Response 2 [M] Merge     │
│ [R]egenerate [F]ork [S]ave [Q]uit                         │
└────────────────────────────────────────────────────────────┘
```

Press `[1]` to select Response 1, then `[Enter]` to proceed.

### Step 4: Outline Generation

**Expected TUI State**:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 2/4: outline (draft → polish remaining)               │
├────────────────────────────────────────────────────────────┤
│ Input from previous step:                                  │
│ ┌─ Selected Angle ────────────────────────────────────────┐ │
│ │ ## 1. The Performance Revolution                        │ │
│ │ Focus on the 90%+ native speed benchmarks and what...  │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o                              [⚡ Streaming] │
│ ┌─ Response 1 ─────────────────────────────────────────────┐ │
│ │ # Outline: The WebAssembly Performance Revolution      │ │
│ │                                                         │ │
│ │ ## Hook                                                 │ │
│ │ Recent benchmark showing 95% native performance...     │ │
│ │ [streaming content appears here in real-time]          │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Your feedback for next step:                              │ │
│ ┌─ Comments ──────────────────────────────────────────────┐ │
│ │ Include specific code examples and benchmarks          │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [A]ccept [C]omment [R]egenerate [F]ork [B]ack [S]ave      │
└────────────────────────────────────────────────────────────┘
```

Press `[A]` to accept outline and proceed to draft.

### Step 5: Draft Generation

**Expected TUI State**:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 3/4: draft (polish remaining)                         │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o, claude-sonnet-4              [⚡ Streaming] │
│ ┌─ Response 1: gpt-4o ───────────────────────────────────────┐ │
│ │ # The WebAssembly Performance Revolution                │ │
│ │                                                         │ │
│ │ When Mozilla engineers first demonstrated WebAssembly  │ │
│ │ running a AAA game at 60fps in Firefox, the web dev... │ │
│ │ [full article draft streaming in real-time]            │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌─ Response 2: claude-sonnet-4 ──────────────────────────────┐ │
│ │ [Streaming second draft...]                             │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [Generating article drafts...]                            │
└────────────────────────────────────────────────────────────┘
```

Select preferred draft and proceed to final polish step.

### Step 6: Polish & Completion

**Final Polish Step**:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 4/4: polish (final step)                              │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o-mini                         [⚡ Streaming] │
│ ┌─ Response 1 ─────────────────────────────────────────────┐ │
│ │ # The WebAssembly Performance Revolution (FINAL)       │ │
│ │                                                         │ │
│ │ When Mozilla first demonstrated WebAssembly running... │ │
│ │ [polished article with improved flow and clarity]      │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Pipeline Complete! 🎉                                     │ │
│ [S]ave Article [E]xport [N]ew Pipeline [Q]uit             │
└────────────────────────────────────────────────────────────┘
```

### Step 7: Export Final Article

Press `[S]` to save article:

**Expected Export Dialog**:
```
┌─ Save Article ─────────────────────────────────────────────┐
│ Output Format: [YAML] [JSON] [Markdown]                   │
│ Include History: [✓] Complete pipeline history            │
│ File Path: ~/articles/runs/2025-09-08_webasm_final.yaml   │
│                                                            │
│ [Enter] Save [Esc] Cancel                                  │
└────────────────────────────────────────────────────────────┘
```

Press `[Enter]` to save article with complete pipeline history.

**Expected Output File**: `~/articles/runs/2025-09-08_webasm_final.yaml`
```yaml
metadata:
  pipeline_run_id: "550e8400-e29b-41d4-a716-446655440000"
  configuration: "tech-article.yaml"
  created_at: "2025-09-08T15:30:00Z"
  completed_at: "2025-09-08T15:45:30Z"
  total_cost: "$0.24"

final_article: |
  # The WebAssembly Performance Revolution
  
  When Mozilla first demonstrated WebAssembly running...
  [complete polished article content]

pipeline_history:
  angles:
    models_used: ["gpt-4o", "claude-sonnet-4"]
    user_selection: 0  # First response
    user_feedback: "Focus on angle 1 - performance story is most compelling"
    
  outline:
    models_used: ["gpt-4o"]
    user_selection: 0
    user_feedback: "Include specific code examples and benchmarks"
    
  draft:
    models_used: ["gpt-4o", "claude-sonnet-4"] 
    user_selection: 1  # Claude response
    user_feedback: ""
    
  polish:
    models_used: ["gpt-4o-mini"]
    user_selection: 0
    user_feedback: ""

execution_stats:
  total_tokens: 12450
  total_time_seconds: 930
  steps_completed: 4
  regenerations: 0
  branches_created: 0
```

## Advanced Features Testing

### Rewind Functionality

1. During any step, press `[B]` to go back to previous step
2. Expected: Previous step state restored with all original responses
3. Make different selection and proceed
4. Expected: New branch created automatically

### Branching/Forking

1. At any completed step, press `[F]` to fork pipeline
2. Expected: New pipeline branch created from current point
3. Switch between branches using TUI navigation
4. Expected: Independent execution paths maintained

### Multi-Pipeline Management

1. Start second pipeline while first is running: `writeit run blog-post.yaml`
2. Expected: New TUI session with separate pipeline state
3. Switch between sessions using session management
4. Expected: Isolated pipeline executions

## Error Recovery Testing

### Network Failure Simulation
```bash
# Disconnect network during streaming
sudo ifconfig en0 down
```
**Expected Behavior**: 
- TUI shows "Connection Lost" message
- Option to retry or switch to local model
- Pipeline state preserved for recovery

### Invalid Input Testing
```bash
# Start pipeline with missing configuration
writeit run nonexistent.yaml
```
**Expected Behavior**:
- Clear error message: "Pipeline configuration not found"
- Suggestion to run `writeit list-pipelines`
- Graceful return to command prompt

### Model Provider Failure
```bash
# Invalid API key simulation
llm keys set openai invalid_key
writeit run tech-article.yaml
```
**Expected Behavior**:
- Authentication error displayed
- Automatic fallback to available providers
- User prompted to fix credentials

## Performance Validation

### Streaming Response Time
- **Target**: First token < 2 seconds
- **Test**: Measure time from step start to first content display
- **Expected**: Sub-second response for all supported models

### Memory Usage
- **Target**: < 100MB steady state
- **Test**: Monitor RSS during complete pipeline execution
- **Expected**: Efficient memory management with streaming

### Storage Efficiency  
- **Target**: < 1MB per complete pipeline run
- **Test**: Check LMDB database size after multiple runs
- **Expected**: Efficient artifact storage with compression

## Integration Verification

This quickstart serves as the comprehensive integration test for WriteIt's core functionality:

✅ **Pipeline Configuration Loading**
✅ **Multi-Model LLM Integration** 
✅ **Real-Time Streaming Display**
✅ **User Selection & Feedback**
✅ **State Management & Persistence**
✅ **Rewind & Branching Operations**
✅ **YAML Export with History**
✅ **Error Handling & Recovery**
✅ **Cross-Platform TUI Compatibility**

**Success Criteria**: All steps complete without errors, final article exported with complete history, performance targets met.