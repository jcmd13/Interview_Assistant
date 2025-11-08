"""
Desktop App State Management
Tracks the state of the Interview Assistant desktop application
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any
import json
from pathlib import Path


class AppStatus(Enum):
    """Application status states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ProcessStatus(Enum):
    """Individual process status"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    ERROR = "error"


@dataclass
class ProcessInfo:
    """Information about a running process"""
    name: str
    status: ProcessStatus
    pid: Optional[int] = None
    start_time: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "pid": self.pid,
            "start_time": self.start_time,
            "error_message": self.error_message,
        }


@dataclass
class AppState:
    """Complete application state"""
    overall_status: AppStatus
    ollama: ProcessInfo
    server: ProcessInfo
    audio_client: ProcessInfo
    ui_url: str = "file:///Users/john/Personal-Projects/Interview_Assistant/index.html"
    websocket_url: str = "ws://127.0.0.1:8123/"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_status": self.overall_status.value,
            "ollama": self.ollama.to_dict(),
            "server": self.server.to_dict(),
            "audio_client": self.audio_client.to_dict(),
            "ui_url": self.ui_url,
            "websocket_url": self.websocket_url,
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def initial() -> "AppState":
        """Create initial state (all stopped)"""
        return AppState(
            overall_status=AppStatus.STOPPED,
            ollama=ProcessInfo("Ollama", ProcessStatus.NOT_STARTED),
            server=ProcessInfo("Server", ProcessStatus.NOT_STARTED),
            audio_client=ProcessInfo("Audio Client", ProcessStatus.NOT_STARTED),
        )


class AppStateManager:
    """Manages and persists application state"""

    def __init__(self, state_file: Optional[Path] = None):
        """Initialize state manager"""
        self.state_file = state_file or Path.home() / ".interview-assistant" / "app_state.json"
        self.state: AppState = AppState.initial()
        self._ensure_state_dir()
        self.load()

    def _ensure_state_dir(self):
        """Ensure state directory exists"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def update_process(self, process_name: str, status: ProcessStatus, pid: Optional[int] = None, error: Optional[str] = None):
        """Update status of a process"""
        if process_name.lower() == "ollama":
            self.state.ollama.status = status
            self.state.ollama.pid = pid
            self.state.ollama.error_message = error
        elif process_name.lower() == "server":
            self.state.server.status = status
            self.state.server.pid = pid
            self.state.server.error_message = error
        elif process_name.lower() == "audio_client":
            self.state.audio_client.status = status
            self.state.audio_client.pid = pid
            self.state.audio_client.error_message = error

        # Update overall status
        self._update_overall_status()
        self.save()

    def _update_overall_status(self):
        """Update overall status based on process states"""
        if any(p.status == ProcessStatus.ERROR for p in [self.state.ollama, self.state.server, self.state.audio_client]):
            self.state.overall_status = AppStatus.ERROR
        elif all(p.status == ProcessStatus.STOPPED for p in [self.state.ollama, self.state.server, self.state.audio_client]):
            self.state.overall_status = AppStatus.STOPPED
        elif any(p.status == ProcessStatus.RUNNING for p in [self.state.ollama, self.state.server]):
            self.state.overall_status = AppStatus.RUNNING
        else:
            self.state.overall_status = AppStatus.STARTING

    def save(self):
        """Save state to file"""
        try:
            with open(self.state_file, "w") as f:
                f.write(self.state.to_json())
        except Exception as e:
            print(f"Error saving state: {e}")

    def load(self):
        """Load state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    # Reconstruct state from JSON
                    # (simplified for now, can be enhanced)
            else:
                self.state = AppState.initial()
        except Exception as e:
            print(f"Error loading state: {e}")
            self.state = AppState.initial()

    def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        parts = []
        parts.append(f"Overall: {self.state.overall_status.value}")
        parts.append(f"Ollama: {self.state.ollama.status.value}")
        parts.append(f"Server: {self.state.server.status.value}")
        parts.append(f"Audio Client: {self.state.audio_client.status.value}")
        return " | ".join(parts)
