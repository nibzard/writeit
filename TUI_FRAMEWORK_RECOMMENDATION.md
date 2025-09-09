# TUI Framework Recommendation for WriteIt

## Decision: **Textual**

## Rationale:
- **Native async architecture**: Built on asyncio from the ground up, perfect for real-time streaming
- **Real-time streaming optimized**: Reactive attributes, live widgets, and non-blocking updates
- **Modern developer experience**: CSS-like styling, React-inspired components, declarative layouts
- **Production-ready**: Cross-platform compatibility, comprehensive error handling, memory efficient
- **WriteIt-perfect features**: Multi-panel layouts, streaming logs, progress tracking, keyboard shortcuts

## Alternatives Considered:

### Rich
- **Strengths**: Beautiful formatting, Live display, lightweight, excellent performance
- **Limitations**: Output-focused, limited interactivity, no event system, requires custom code for complex UIs
- **Verdict**: Excellent as a component within other frameworks, but insufficient alone for WriteIt's interactive needs

### prompt_toolkit  
- **Strengths**: Mature, native asyncio, excellent for CLI prompts, fine-grained control
- **Limitations**: Complex layout system, verbose boilerplate, limited widgets, prompt-focused design
- **Verdict**: Better suited for CLI interfaces than full TUI applications

### urwid
- **Strengths**: Battle-tested, multiple event loops, comprehensive widgets, stable
- **Limitations**: Older API design, verbose syntax, performance issues on constrained systems, limited modern styling
- **Verdict**: Solid but outdated compared to modern alternatives

## Integration Patterns:

### FastAPI/WebSocket Backend Architecture:
```python
# FastAPI Backend
@app.websocket("/ws")  
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Token-by-token streaming
    for token in llm_stream:
        await websocket.send_json({
            "type": "stream_token",
            "content": token,
            "step": current_step
        })
```

### Textual Frontend Integration:
```python
class WriteItTUI(App):
    streaming_content = reactive("")
    
    async def websocket_handler(self):
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            async for message in ws:
                data = json.loads(message)
                if data["type"] == "stream_token":
                    self.streaming_content += data["content"]
    
    def watch_streaming_content(self, content: str):
        log = self.query_one("#ai-output", Log)
        log.write_line(content)
```

### Key Async Patterns:
1. **Background WebSocket handling**: `asyncio.create_task(self.websocket_handler())`
2. **Reactive UI updates**: `reactive` attributes with `watch_*` methods
3. **Non-blocking operations**: `@work` decorator for heavy processing
4. **Event-driven architecture**: Message queues between widgets

## Implementation Examples:

Complete working examples created in `/Users/nikola/dev/writeit/research_examples/`:

1. **textual_websocket_example.py** - Full Textual TUI with multi-panel layout, real-time streaming, and WebSocket integration
2. **fastapi_websocket_backend.py** - FastAPI backend with token-by-token streaming simulation
3. **rich_console_example.py** - Rich alternative showing Live display capabilities  
4. **prompt_toolkit_example.py** - prompt_toolkit async implementation
5. **requirements.txt** - All framework dependencies

## Performance Assessment:
- **Real-time streaming**: Textual excels with built-in reactive updates
- **Memory efficiency**: Smart caching and widget optimization
- **Cross-platform**: Works on Windows, macOS, Linux terminals
- **Development speed**: Modern API reduces boilerplate significantly

**Recommendation**: Proceed with **Textual** for WriteIt's TUI implementation. The framework's async-first design, real-time streaming capabilities, and modern development experience make it the optimal choice for this LLM pipeline application.