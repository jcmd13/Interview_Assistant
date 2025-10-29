"""
Application State Management

This module encapsulates all global state for the Interview Assistant server,
replacing scattered global variables with a centralized, thread-safe state manager.

State includes:
- Conversation transcript
- Detected questions
- Answered questions
- Audio buffer
- WebSocket clients
- Server lifecycle events
"""

import asyncio
import json
import time
from typing import List, Dict, Set, Optional, Callable, Any, Deque
from collections import deque
from dataclasses import dataclass, asdict, field
from datetime import datetime


# ============================================================================
# State Observer Pattern
# ============================================================================

class StateObserver:
    """Base class for state change observers."""

    async def on_transcript_updated(self, line: str, line_number: int) -> None:
        """Called when a new line is added to the transcript."""
        pass

    async def on_question_detected(self, question: Dict[str, Any]) -> None:
        """Called when a question is detected."""
        pass

    async def on_answer_generated(self, answer: Dict[str, Any]) -> None:
        """Called when an answer is generated."""
        pass

    async def on_state_reset(self) -> None:
        """Called when the entire state is reset."""
        pass


# ============================================================================
# State Data Classes
# ============================================================================

@dataclass
class DetectedQuestion:
    """Represents a detected question with metadata."""
    question: str
    timestamp: float
    context: str = ""
    confidence: float = 0.7
    urgency: str = "medium"
    topic_area: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnsweredQuestion:
    """Represents a question that has been answered."""
    question: str
    answer: str
    timestamp: float
    generation_time_ms: float = 0.0
    model: str = "unknown"
    context_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AudioBuffer:
    """Encapsulates audio buffer state."""
    data: bytearray = field(default_factory=bytearray)
    bytes_since_last: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def clear(self) -> None:
        """Clear the audio buffer."""
        self.data.clear()
        self.bytes_since_last = 0


# ============================================================================
# Application State Manager
# ============================================================================

class ApplicationState:
    """
    Centralized state manager for the Interview Assistant server.

    Replaces global variables with thread-safe, observable state management.
    Supports state persistence, snapshots, and observers for UI updates.
    """

    def __init__(self, max_transcript_lines: int = 5000):
        """
        Initialize the application state.

        Args:
            max_transcript_lines: Maximum number of transcript lines to keep in memory
        """
        # Transcript management
        self._transcript: List[str] = []
        self._max_transcript_lines = max_transcript_lines
        self._transcript_lock = asyncio.Lock()

        # Question detection
        self._detected_questions: Deque[DetectedQuestion] = deque(maxlen=500)
        self._detected_lock = asyncio.Lock()

        # Question answering
        self._answered_questions: Deque[AnsweredQuestion] = deque(maxlen=200)
        self._answered_lock = asyncio.Lock()

        # Audio processing
        self._audio_buffer = AudioBuffer()

        # Sentence buffering
        self._latest_text = ""
        self._sentence_buf = ""
        self._text_lock = asyncio.Lock()

        # WebSocket clients
        self._ws_clients: Set[Any] = set()
        self._ws_lock = asyncio.Lock()

        # Lifecycle management
        self._server_shutdown = asyncio.Event()
        self._transcriber_task: Optional[asyncio.Task] = None
        self._lifecycle_lock = asyncio.Lock()

        # Observers
        self._observers: List[StateObserver] = []
        self._observer_lock = asyncio.Lock()

        # State metadata
        self._created_at = datetime.utcnow().isoformat()
        self._last_modified = time.time()

    # ========================================================================
    # Transcript Management
    # ========================================================================

    async def add_transcript_line(self, text: str) -> int:
        """
        Add a line to the transcript.

        Args:
            text: The text to add

        Returns:
            The line number (1-indexed)
        """
        async with self._transcript_lock:
            self._transcript.append(text)

            # Trim old lines if necessary
            if len(self._transcript) > self._max_transcript_lines:
                trim_count = self._max_transcript_lines // 10
                self._transcript = self._transcript[trim_count:]

            line_number = len(self._transcript)
            self._last_modified = time.time()

            # Notify observers
            await self._notify_observers(
                lambda obs: obs.on_transcript_updated(text, line_number)
            )

            return line_number

    def get_transcript(self) -> List[str]:
        """Get the full transcript (synchronous read)."""
        return self._transcript.copy()

    def get_transcript_length(self) -> int:
        """Get the number of lines in the transcript."""
        return len(self._transcript)

    def get_last_n_lines(self, n: int) -> List[str]:
        """
        Get the last N lines of the transcript with line numbers.

        Args:
            n: Number of lines to retrieve

        Returns:
            List of numbered lines
        """
        if n <= 0 or not self._transcript:
            return []

        start_idx = max(0, len(self._transcript) - n)
        return [
            f"{i+1}. {self._transcript[i]}"
            for i in range(start_idx, len(self._transcript))
        ]

    def get_head_tail_lines(self, head: int, tail: int) -> List[str]:
        """
        Get head and tail lines of the transcript.

        Args:
            head: Number of lines from the beginning
            tail: Number of lines from the end

        Returns:
            List of numbered lines with ellipsis in between if needed
        """
        total = len(self._transcript)
        if total == 0:
            return []

        head = max(0, min(head, total))
        tail = max(0, min(tail, total - head))

        parts = []
        for i in range(head):
            parts.append(f"{i+1}. {self._transcript[i]}")

        if head + tail < total:
            parts.append("...")

        start_tail = max(head, total - tail)
        for i in range(start_tail, total):
            parts.append(f"{i+1}. {self._transcript[i]}")

        return parts

    # ========================================================================
    # Question Detection
    # ========================================================================

    async def add_detected_question(self, question: DetectedQuestion) -> None:
        """
        Add a detected question to the queue.

        Args:
            question: The detected question
        """
        async with self._detected_lock:
            self._detected_questions.append(question)
            self._last_modified = time.time()

            # Notify observers
            await self._notify_observers(
                lambda obs: obs.on_question_detected(question.to_dict())
            )

    def get_detected_questions(self) -> List[Dict[str, Any]]:
        """Get all detected questions (as dictionaries)."""
        return [q.to_dict() for q in self._detected_questions]

    def get_detected_questions_count(self) -> int:
        """Get the number of detected questions."""
        return len(self._detected_questions)

    async def clear_detected_questions(self) -> None:
        """Clear all detected questions."""
        async with self._detected_lock:
            self._detected_questions.clear()
            self._last_modified = time.time()

    # ========================================================================
    # Answer Management
    # ========================================================================

    async def add_answered_question(self, answer: AnsweredQuestion) -> None:
        """
        Add an answered question to the log.

        Args:
            answer: The answered question
        """
        async with self._answered_lock:
            self._answered_questions.append(answer)
            self._last_modified = time.time()

            # Notify observers
            await self._notify_observers(
                lambda obs: obs.on_answer_generated(answer.to_dict())
            )

    def get_answered_questions(self) -> List[Dict[str, Any]]:
        """Get all answered questions (as dictionaries)."""
        return [a.to_dict() for a in self._answered_questions]

    def get_answered_questions_count(self) -> int:
        """Get the number of answered questions."""
        return len(self._answered_questions)

    async def clear_answered_questions(self) -> None:
        """Clear all answered questions."""
        async with self._answered_lock:
            self._answered_questions.clear()
            self._last_modified = time.time()

    # ========================================================================
    # Text Buffering
    # ========================================================================

    async def update_text_buffer(self, latest: str, sentence: str) -> None:
        """
        Update the text buffers.

        Args:
            latest: The latest text segment
            sentence: The sentence buffer
        """
        async with self._text_lock:
            self._latest_text = latest
            self._sentence_buf = sentence
            self._last_modified = time.time()

    def get_latest_text(self) -> str:
        """Get the latest text segment."""
        return self._latest_text

    def get_sentence_buffer(self) -> str:
        """Get the sentence buffer."""
        return self._sentence_buf

    # ========================================================================
    # Audio Buffer Management
    # ========================================================================

    @property
    def audio_buffer(self) -> AudioBuffer:
        """Get the audio buffer object."""
        return self._audio_buffer

    async def update_audio_buffer(self, data: bytearray, bytes_since_last: int) -> None:
        """Update the audio buffer state."""
        async with self._audio_buffer.lock:
            self._audio_buffer.data = data
            self._audio_buffer.bytes_since_last = bytes_since_last
            self._last_modified = time.time()

    async def clear_audio_buffer(self) -> None:
        """Clear the audio buffer."""
        async with self._audio_buffer.lock:
            self._audio_buffer.clear()
            self._last_modified = time.time()

    # ========================================================================
    # WebSocket Client Management
    # ========================================================================

    async def add_ws_client(self, client: Any) -> None:
        """
        Add a WebSocket client.

        Args:
            client: The WebSocket connection object
        """
        async with self._ws_lock:
            self._ws_clients.add(client)
            self._last_modified = time.time()

    async def remove_ws_client(self, client: Any) -> None:
        """
        Remove a WebSocket client.

        Args:
            client: The WebSocket connection object
        """
        async with self._ws_lock:
            self._ws_clients.discard(client)
            self._last_modified = time.time()

    def get_ws_clients(self) -> Set[Any]:
        """Get all connected WebSocket clients."""
        return self._ws_clients.copy()

    def get_ws_clients_count(self) -> int:
        """Get the number of connected clients."""
        return len(self._ws_clients)

    async def clear_ws_clients(self) -> None:
        """Clear all WebSocket clients."""
        async with self._ws_lock:
            self._ws_clients.clear()
            self._last_modified = time.time()

    # ========================================================================
    # Lifecycle Management
    # ========================================================================

    def get_shutdown_event(self) -> asyncio.Event:
        """Get the server shutdown event."""
        return self._server_shutdown

    async def signal_shutdown(self) -> None:
        """Signal that the server is shutting down."""
        async with self._lifecycle_lock:
            self._server_shutdown.set()
            self._last_modified = time.time()

    def is_shutdown_signaled(self) -> bool:
        """Check if shutdown has been signaled."""
        return self._server_shutdown.is_set()

    def set_transcriber_task(self, task: Optional[asyncio.Task]) -> None:
        """Set the transcriber task reference."""
        self._transcriber_task = task

    def get_transcriber_task(self) -> Optional[asyncio.Task]:
        """Get the transcriber task reference."""
        return self._transcriber_task

    # ========================================================================
    # Observer Management
    # ========================================================================

    async def subscribe(self, observer: StateObserver) -> None:
        """
        Subscribe to state changes.

        Args:
            observer: An observer implementing StateObserver
        """
        async with self._observer_lock:
            self._observers.append(observer)

    async def unsubscribe(self, observer: StateObserver) -> None:
        """
        Unsubscribe from state changes.

        Args:
            observer: An observer to remove
        """
        async with self._observer_lock:
            self._observers.remove(observer)

    async def _notify_observers(self, notification: Callable) -> None:
        """
        Notify all observers of a state change.

        Args:
            notification: A callable that calls observer methods
        """
        async with self._observer_lock:
            for observer in self._observers:
                try:
                    await notification(observer)
                except Exception as e:
                    # Log but don't crash on observer errors
                    print(f"Observer notification error: {e}")

    # ========================================================================
    # State Serialization
    # ========================================================================

    def to_snapshot(self) -> Dict[str, Any]:
        """
        Create a snapshot of the current state.

        Returns:
            Dictionary representation of the state
        """
        return {
            "transcript": self._transcript.copy(),
            "detected_questions": self.get_detected_questions(),
            "answered_questions": self.get_answered_questions(),
            "latest_text": self._latest_text,
            "sentence_buf": self._sentence_buf,
            "ws_clients_count": self.get_ws_clients_count(),
            "transcript_length": self.get_transcript_length(),
            "metadata": {
                "created_at": self._created_at,
                "last_modified": datetime.fromtimestamp(self._last_modified).isoformat(),
                "shutdown_signaled": self.is_shutdown_signaled(),
            }
        }

    def to_json(self) -> str:
        """
        Serialize state to JSON string.

        Returns:
            JSON string representation of the state
        """
        snapshot = self.to_snapshot()
        return json.dumps(snapshot, indent=2)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to legacy flat dictionary format for backward compatibility.

        Returns:
            Dictionary with legacy structure
        """
        return {
            "transcript_lines": self._transcript.copy(),
            "detected": list(self._detected_questions),
            "qa_log": list(self._answered_questions),
            "latest_text": self._latest_text,
            "sentence_buf": self._sentence_buf,
        }

    # ========================================================================
    # State Restoration & Resetting
    # ========================================================================

    async def from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        Restore state from a snapshot.

        Args:
            snapshot: Dictionary created by to_snapshot()
        """
        async with self._transcript_lock, self._detected_lock, self._answered_lock:
            self._transcript = snapshot.get("transcript", [])

            # Restore detected questions
            self._detected_questions.clear()
            for q_dict in snapshot.get("detected_questions", []):
                q = DetectedQuestion(**q_dict)
                self._detected_questions.append(q)

            # Restore answered questions
            self._answered_questions.clear()
            for a_dict in snapshot.get("answered_questions", []):
                a = AnsweredQuestion(**a_dict)
                self._answered_questions.append(a)

            self._latest_text = snapshot.get("latest_text", "")
            self._sentence_buf = snapshot.get("sentence_buf", "")
            self._last_modified = time.time()

    async def reset(self) -> None:
        """
        Reset all state to initial values.

        Clears all conversation data while keeping configuration.
        """
        async with self._transcript_lock, self._detected_lock, self._answered_lock, self._text_lock:
            self._transcript.clear()
            self._detected_questions.clear()
            self._answered_questions.clear()
            self._latest_text = ""
            self._sentence_buf = ""
            self._last_modified = time.time()

            # Notify observers
            await self._notify_observers(
                lambda obs: obs.on_state_reset()
            )

    # ========================================================================
    # Metadata
    # ========================================================================

    def get_created_at(self) -> str:
        """Get the timestamp when this state was created."""
        return self._created_at

    def get_last_modified(self) -> float:
        """Get the timestamp of the last modification."""
        return self._last_modified

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current state."""
        return {
            "transcript_lines": self.get_transcript_length(),
            "detected_questions": self.get_detected_questions_count(),
            "answered_questions": self.get_answered_questions_count(),
            "ws_clients": self.get_ws_clients_count(),
            "created_at": self._created_at,
            "last_modified": datetime.fromtimestamp(self._last_modified).isoformat(),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_global_state: Optional[ApplicationState] = None


def get_state() -> ApplicationState:
    """
    Get the global application state instance (singleton pattern).

    Returns:
        The global ApplicationState instance
    """
    global _global_state
    if _global_state is None:
        _global_state = ApplicationState()
    return _global_state


def reset_global_state() -> None:
    """Reset the global state (mainly for testing)."""
    global _global_state
    _global_state = None
