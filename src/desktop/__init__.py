"""
Desktop application module
Provides macOS menu bar app and state management
"""

from .app_state import AppState, AppStateManager, AppStatus, ProcessStatus, ProcessInfo

__all__ = [
    "AppState",
    "AppStateManager",
    "AppStatus",
    "ProcessStatus",
    "ProcessInfo",
]
