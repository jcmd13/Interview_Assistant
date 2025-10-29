"""
Server Infrastructure Package

This package contains the WebSocket server, request handlers,
and application state management.

Components:
- state: Centralized application state management
- handlers: WebSocket request handlers (Phase 2)
"""

__all__ = [
    "ApplicationState",
    "StateObserver",
    "DetectedQuestion",
    "AnsweredQuestion",
    "get_state",
    "reset_global_state",
]


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name in ["ApplicationState", "StateObserver", "DetectedQuestion", "AnsweredQuestion"]:
        from .state import ApplicationState, StateObserver, DetectedQuestion, AnsweredQuestion
        return {
            "ApplicationState": ApplicationState,
            "StateObserver": StateObserver,
            "DetectedQuestion": DetectedQuestion,
            "AnsweredQuestion": AnsweredQuestion,
        }[name]
    elif name in ["get_state", "reset_global_state"]:
        from .state import get_state, reset_global_state
        return get_state if name == "get_state" else reset_global_state
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
