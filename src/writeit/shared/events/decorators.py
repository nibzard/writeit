"""Event handling decorators.

Provides convenient decorators for event handler registration and discovery."""

import inspect
from functools import wraps
from typing import Type, Callable, Any, Dict, Optional, get_type_hints

from .domain_event import DomainEvent
from .event_handler import EventHandler, BaseEventHandler


# Registry for decorated handlers
_decorated_handlers: Dict[str, Type[EventHandler]] = {}


def event_handler(
    event_type: Optional[Type[DomainEvent]] = None,
    priority: int = 100,
    auto_register: bool = True
):
    """Decorator for creating event handlers.
    
    Args:
        event_type: The event type to handle (inferred from type hints if not provided)
        priority: Handler priority (lower = higher priority)
        auto_register: Whether to auto-register the handler
    
    Example:
        @event_handler(priority=50)
        async def handle_pipeline_started(event: PipelineExecutionStarted) -> None:
            print(f"Pipeline {event.pipeline_id} started")
        
        # Or as a class decorator
        @event_handler(PipelineExecutionStarted, priority=25)
        class PipelineStartedHandler(BaseEventHandler[PipelineExecutionStarted]):
            async def handle(self, event: PipelineExecutionStarted) -> None:
                print(f"Pipeline {event.pipeline_id} started")
    """
    def decorator(func_or_class):
        if inspect.isclass(func_or_class):
            return _class_handler_decorator(func_or_class, event_type, priority, auto_register)
        else:
            return _function_handler_decorator(func_or_class, event_type, priority, auto_register)
    
    return decorator


def _function_handler_decorator(
    func: Callable,
    event_type: Optional[Type[DomainEvent]],
    priority: int,
    auto_register: bool
):
    """Create a handler class from a function."""
    # Infer event type from function signature if not provided
    if event_type is None:
        type_hints = get_type_hints(func)
        if 'event' in type_hints:
            event_type = type_hints['event']
        else:
            # Try to get from first parameter
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            if params and params[0].annotation != inspect.Parameter.empty:
                event_type = params[0].annotation
        
        if event_type is None:
            raise ValueError(f"Could not infer event type for function {func.__name__}. Please specify explicitly.")
    
    # Create handler class
    class FunctionEventHandler(BaseEventHandler[event_type]):
        def __init__(self):
            super().__init__(priority)
            self.func = func
        
        async def handle(self, event: event_type) -> None:
            if inspect.iscoroutinefunction(self.func):
                await self.func(event)
            else:
                self.func(event)
        
        @property
        def event_type(self) -> Type[event_type]:
            return event_type
        
        def __str__(self) -> str:
            return f"FunctionEventHandler({func.__name__}, priority={self.priority})"
    
    # Add metadata to the original function
    func._event_handler_class = FunctionEventHandler
    func._event_type = event_type
    func._priority = priority
    
    # Auto-register if requested
    if auto_register:
        handler_key = f"{func.__module__}.{func.__name__}"
        _decorated_handlers[handler_key] = FunctionEventHandler
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper


def _class_handler_decorator(
    handler_class: Type,
    event_type: Optional[Type[DomainEvent]],
    priority: int,
    auto_register: bool
):
    """Apply decorator to a handler class."""
    # Set priority if class doesn't have custom __init__
    if not hasattr(handler_class, '_custom_init'):
        original_init = handler_class.__init__
        
        def new_init(self, *args, **kwargs):
            if 'priority' not in kwargs and not args:
                kwargs['priority'] = priority
            original_init(self, *args, **kwargs)
        
        handler_class.__init__ = new_init
    
    # Override event_type if specified
    if event_type is not None:
        handler_class._decorator_event_type = event_type
        
        original_event_type = handler_class.event_type
        
        @property
        def new_event_type(self) -> Type[DomainEvent]:
            return event_type
        
        handler_class.event_type = new_event_type
    
    # Auto-register if requested
    if auto_register:
        handler_key = f"{handler_class.__module__}.{handler_class.__name__}"
        _decorated_handlers[handler_key] = handler_class
    
    return handler_class


def get_decorated_handlers() -> Dict[str, Type[EventHandler]]:
    """Get all decorated handlers.
    
    Returns:
        Dictionary mapping handler keys to handler classes
    """
    return _decorated_handlers.copy()


def clear_decorated_handlers() -> None:
    """Clear all decorated handlers.
    
    Useful for testing.
    """
    _decorated_handlers.clear()


def auto_discover_handlers(module_name: str) -> Dict[str, Type[EventHandler]]:
    """Auto-discover handlers in a module.
    
    Args:
        module_name: The module to search for handlers
        
    Returns:
        Dictionary of discovered handlers
        
    Example:
        handlers = auto_discover_handlers('myapp.handlers')
        for handler_class in handlers.values():
            await event_bus.register_handler(handler_class())
    """
    import importlib
    
    try:
        module = importlib.import_module(module_name)
        # Force execution of module code to trigger decorators
        importlib.reload(module)
    except ImportError:
        return {}
    
    # Return handlers discovered during module import
    return {k: v for k, v in _decorated_handlers.items() if k.startswith(module_name)}


class HandlerDiscovery:
    """Utility class for discovering and registering event handlers."""
    
    @staticmethod
    async def discover_and_register(event_bus, module_patterns: list[str]) -> int:
        """Discover handlers in modules and register them.
        
        Args:
            event_bus: The event bus to register handlers with
            module_patterns: List of module patterns to search
            
        Returns:
            Number of handlers registered
        """
        registered_count = 0
        
        for pattern in module_patterns:
            handlers = auto_discover_handlers(pattern)
            for handler_class in handlers.values():
                try:
                    handler = handler_class()
                    await event_bus.register_handler(handler)
                    registered_count += 1
                except Exception as e:
                    # Log error but continue with other handlers
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to register handler {handler_class.__name__}: {e}")
        
        return registered_count
    
    @staticmethod
    def get_handler_info(handler_class: Type[EventHandler]) -> Dict[str, Any]:
        """Get information about a handler class.
        
        Args:
            handler_class: The handler class to inspect
            
        Returns:
            Dictionary with handler information
        """
        info = {
            'name': handler_class.__name__,
            'module': handler_class.__module__,
            'is_decorated': hasattr(handler_class, '_decorator_event_type'),
            'priority': getattr(handler_class, '_priority', None)
        }
        
        # Try to get event type
        try:
            if hasattr(handler_class, '_decorator_event_type'):
                info['event_type'] = handler_class._decorator_event_type.__name__
            else:
                # Create instance to get event type
                instance = handler_class()
                info['event_type'] = instance.event_type.__name__
        except Exception:
            info['event_type'] = 'unknown'
        
        return info
