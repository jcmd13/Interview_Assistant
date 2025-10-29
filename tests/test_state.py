"""
Tests for Application State Management

Verifies that the ApplicationState class properly encapsulates global state
with thread-safe access, observers, and serialization.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.server.state import (
    ApplicationState,
    StateObserver,
    DetectedQuestion,
    AnsweredQuestion,
    AudioBuffer,
    get_state,
    reset_global_state,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def state():
    """Provide a fresh ApplicationState instance for each test."""
    app_state = ApplicationState()
    yield app_state


@pytest.fixture
def reset_singleton():
    """Reset the singleton before and after test."""
    reset_global_state()
    yield
    reset_global_state()


class MockObserver(StateObserver):
    """Mock observer for testing notifications."""

    def __init__(self):
        self.transcript_updates = []
        self.question_detections = []
        self.answers_generated = []
        self.state_resets = []

    async def on_transcript_updated(self, line: str, line_number: int) -> None:
        self.transcript_updates.append((line, line_number))

    async def on_question_detected(self, question: dict) -> None:
        self.question_detections.append(question)

    async def on_answer_generated(self, answer: dict) -> None:
        self.answers_generated.append(answer)

    async def on_state_reset(self) -> None:
        self.state_resets.append(True)


# ============================================================================
# Transcript Management Tests
# ============================================================================

class TestTranscriptManagement:
    """Test transcript-related functionality."""

    @pytest.mark.asyncio
    async def test_add_transcript_line(self, state):
        """Test adding a line to the transcript."""
        line_num = await state.add_transcript_line("Hello, world!")
        assert line_num == 1
        assert state.get_transcript_length() == 1
        assert state.get_transcript()[0] == "Hello, world!"

    @pytest.mark.asyncio
    async def test_add_multiple_lines(self, state):
        """Test adding multiple lines."""
        for i in range(5):
            line_num = await state.add_transcript_line(f"Line {i}")
            assert line_num == i + 1

        assert state.get_transcript_length() == 5
        transcript = state.get_transcript()
        assert transcript[0] == "Line 0"
        assert transcript[4] == "Line 4"

    @pytest.mark.asyncio
    async def test_get_last_n_lines(self, state):
        """Test retrieving the last N lines."""
        for i in range(10):
            await state.add_transcript_line(f"Line {i}")

        last_5 = state.get_last_n_lines(5)
        assert len(last_5) == 5
        assert "5. Line 5" in last_5[0]  # First of last 5
        assert "10. Line 9" in last_5[4]  # Last of last 5

    @pytest.mark.asyncio
    async def test_get_head_tail_lines(self, state):
        """Test retrieving head and tail lines."""
        for i in range(10):
            await state.add_transcript_line(f"Line {i}")

        head_tail = state.get_head_tail_lines(head=2, tail=2)
        assert "1. Line 0" in head_tail
        assert "2. Line 1" in head_tail
        assert "..." in head_tail
        assert "9. Line 8" in head_tail
        assert "10. Line 9" in head_tail

    @pytest.mark.asyncio
    async def test_transcript_trimming(self, state):
        """Test that transcript is trimmed when exceeding max lines."""
        # Create state with small max
        small_state = ApplicationState(max_transcript_lines=10)

        # Add more than max lines
        for i in range(20):
            await small_state.add_transcript_line(f"Line {i}")

        # Should be trimmed to approximately max size
        length = small_state.get_transcript_length()
        assert length <= 10

    def test_get_transcript_copy(self, state):
        """Test that get_transcript returns a copy, not the original."""
        asyncio.run(state.add_transcript_line("Original"))
        transcript1 = state.get_transcript()
        transcript2 = state.get_transcript()

        assert transcript1 == transcript2
        assert transcript1 is not transcript2  # Different objects


# ============================================================================
# Question Detection Tests
# ============================================================================

class TestQuestionDetection:
    """Test question detection functionality."""

    @pytest.mark.asyncio
    async def test_add_detected_question(self, state):
        """Test adding a detected question."""
        question = DetectedQuestion(
            question="What is Python?",
            timestamp=1000.0,
            context="Technical interview",
            confidence=0.9,
        )

        await state.add_detected_question(question)
        questions = state.get_detected_questions()

        assert len(questions) == 1
        assert questions[0]["question"] == "What is Python?"
        assert questions[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_add_multiple_questions(self, state):
        """Test adding multiple questions."""
        for i in range(5):
            question = DetectedQuestion(
                question=f"Question {i}?",
                timestamp=float(i),
            )
            await state.add_detected_question(question)

        assert state.get_detected_questions_count() == 5

    @pytest.mark.asyncio
    async def test_clear_detected_questions(self, state):
        """Test clearing detected questions."""
        question = DetectedQuestion(question="Test?", timestamp=0.0)
        await state.add_detected_question(question)
        assert state.get_detected_questions_count() == 1

        await state.clear_detected_questions()
        assert state.get_detected_questions_count() == 0

    def test_detected_question_serialization(self):
        """Test DetectedQuestion serialization."""
        question = DetectedQuestion(
            question="What?",
            timestamp=1000.0,
            context="Context",
            confidence=0.8,
            urgency="high",
            topic_area="technical",
        )

        q_dict = question.to_dict()
        assert q_dict["question"] == "What?"
        assert q_dict["confidence"] == 0.8
        assert q_dict["urgency"] == "high"


# ============================================================================
# Answer Management Tests
# ============================================================================

class TestAnswerManagement:
    """Test answer-related functionality."""

    @pytest.mark.asyncio
    async def test_add_answered_question(self, state):
        """Test adding an answered question."""
        answer = AnsweredQuestion(
            question="What is Python?",
            answer="Python is a programming language.",
            timestamp=1000.0,
            generation_time_ms=500.0,
            model="gpt-oss:120b",
        )

        await state.add_answered_question(answer)
        answers = state.get_answered_questions()

        assert len(answers) == 1
        assert answers[0]["answer"] == "Python is a programming language."
        assert answers[0]["generation_time_ms"] == 500.0

    @pytest.mark.asyncio
    async def test_add_multiple_answers(self, state):
        """Test adding multiple answers."""
        for i in range(5):
            answer = AnsweredQuestion(
                question=f"Q{i}?",
                answer=f"Answer {i}",
                timestamp=float(i),
            )
            await state.add_answered_question(answer)

        assert state.get_answered_questions_count() == 5

    @pytest.mark.asyncio
    async def test_clear_answered_questions(self, state):
        """Test clearing answered questions."""
        answer = AnsweredQuestion(
            question="Q?",
            answer="A",
            timestamp=0.0,
        )
        await state.add_answered_question(answer)
        assert state.get_answered_questions_count() == 1

        await state.clear_answered_questions()
        assert state.get_answered_questions_count() == 0


# ============================================================================
# Text Buffering Tests
# ============================================================================

class TestTextBuffering:
    """Test text buffer functionality."""

    @pytest.mark.asyncio
    async def test_update_text_buffer(self, state):
        """Test updating text buffers."""
        await state.update_text_buffer(
            latest="Hello",
            sentence="Hello world"
        )

        assert state.get_latest_text() == "Hello"
        assert state.get_sentence_buffer() == "Hello world"

    @pytest.mark.asyncio
    async def test_multiple_text_updates(self, state):
        """Test multiple text updates."""
        for i in range(5):
            await state.update_text_buffer(
                latest=f"Text {i}",
                sentence=f"Sentence {i}"
            )

        assert state.get_latest_text() == "Text 4"
        assert state.get_sentence_buffer() == "Sentence 4"


# ============================================================================
# Audio Buffer Tests
# ============================================================================

class TestAudioBuffer:
    """Test audio buffer functionality."""

    def test_audio_buffer_property(self, state):
        """Test accessing the audio buffer."""
        audio_buf = state.audio_buffer
        assert isinstance(audio_buf, AudioBuffer)
        assert len(audio_buf.data) == 0
        assert audio_buf.bytes_since_last == 0

    @pytest.mark.asyncio
    async def test_update_audio_buffer(self, state):
        """Test updating audio buffer."""
        data = bytearray(b"test audio data")
        await state.update_audio_buffer(data, 1024)

        audio_buf = state.audio_buffer
        assert audio_buf.data == data
        assert audio_buf.bytes_since_last == 1024

    @pytest.mark.asyncio
    async def test_clear_audio_buffer(self, state):
        """Test clearing audio buffer."""
        data = bytearray(b"test audio data")
        await state.update_audio_buffer(data, 1024)
        assert len(state.audio_buffer.data) > 0

        await state.clear_audio_buffer()
        assert len(state.audio_buffer.data) == 0
        assert state.audio_buffer.bytes_since_last == 0


# ============================================================================
# WebSocket Client Management Tests
# ============================================================================

class TestWebSocketManagement:
    """Test WebSocket client management."""

    @pytest.mark.asyncio
    async def test_add_ws_client(self, state):
        """Test adding a WebSocket client."""
        client = MagicMock()
        await state.add_ws_client(client)

        clients = state.get_ws_clients()
        assert client in clients
        assert state.get_ws_clients_count() == 1

    @pytest.mark.asyncio
    async def test_add_multiple_clients(self, state):
        """Test adding multiple clients."""
        clients = [MagicMock() for _ in range(5)]
        for client in clients:
            await state.add_ws_client(client)

        assert state.get_ws_clients_count() == 5

    @pytest.mark.asyncio
    async def test_remove_ws_client(self, state):
        """Test removing a WebSocket client."""
        client1 = MagicMock()
        client2 = MagicMock()

        await state.add_ws_client(client1)
        await state.add_ws_client(client2)
        assert state.get_ws_clients_count() == 2

        await state.remove_ws_client(client1)
        assert state.get_ws_clients_count() == 1
        assert client2 in state.get_ws_clients()

    @pytest.mark.asyncio
    async def test_clear_ws_clients(self, state):
        """Test clearing all clients."""
        for _ in range(5):
            await state.add_ws_client(MagicMock())

        assert state.get_ws_clients_count() == 5
        await state.clear_ws_clients()
        assert state.get_ws_clients_count() == 0


# ============================================================================
# Lifecycle Management Tests
# ============================================================================

class TestLifecycleManagement:
    """Test server lifecycle functionality."""

    @pytest.mark.asyncio
    async def test_shutdown_event(self, state):
        """Test shutdown event signaling."""
        event = state.get_shutdown_event()
        assert not state.is_shutdown_signaled()

        await state.signal_shutdown()
        assert state.is_shutdown_signaled()
        assert event.is_set()

    def test_transcriber_task_management(self, state):
        """Test transcriber task reference."""
        assert state.get_transcriber_task() is None

        task = MagicMock()
        state.set_transcriber_task(task)
        assert state.get_transcriber_task() == task

        state.set_transcriber_task(None)
        assert state.get_transcriber_task() is None


# ============================================================================
# Observer Pattern Tests
# ============================================================================

class TestObserverPattern:
    """Test state observers."""

    @pytest.mark.asyncio
    async def test_subscribe_observer(self, state):
        """Test subscribing to state changes."""
        observer = MockObserver()
        await state.subscribe(observer)

        await state.add_transcript_line("Test line")
        assert len(observer.transcript_updates) == 1
        assert observer.transcript_updates[0] == ("Test line", 1)

    @pytest.mark.asyncio
    async def test_observer_question_notification(self, state):
        """Test observer notification for questions."""
        observer = MockObserver()
        await state.subscribe(observer)

        question = DetectedQuestion(question="Test?", timestamp=0.0)
        await state.add_detected_question(question)

        assert len(observer.question_detections) == 1
        assert observer.question_detections[0]["question"] == "Test?"

    @pytest.mark.asyncio
    async def test_observer_answer_notification(self, state):
        """Test observer notification for answers."""
        observer = MockObserver()
        await state.subscribe(observer)

        answer = AnsweredQuestion(
            question="Q?",
            answer="A",
            timestamp=0.0,
        )
        await state.add_answered_question(answer)

        assert len(observer.answers_generated) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_observer(self, state):
        """Test unsubscribing from state changes."""
        observer = MockObserver()
        await state.subscribe(observer)
        await state.unsubscribe(observer)

        await state.add_transcript_line("Test")
        assert len(observer.transcript_updates) == 0

    @pytest.mark.asyncio
    async def test_reset_observer_notification(self, state):
        """Test observer notification on state reset."""
        observer = MockObserver()
        await state.subscribe(observer)

        await state.add_transcript_line("Test")
        await state.reset()

        assert len(observer.state_resets) == 1
        assert state.get_transcript_length() == 0


# ============================================================================
# Serialization Tests
# ============================================================================

class TestSerialization:
    """Test state serialization and deserialization."""

    @pytest.mark.asyncio
    async def test_to_snapshot(self, state):
        """Test creating a state snapshot."""
        await state.add_transcript_line("Line 1")
        await state.add_transcript_line("Line 2")

        question = DetectedQuestion(question="Q?", timestamp=0.0)
        await state.add_detected_question(question)

        snapshot = state.to_snapshot()

        assert snapshot["transcript"] == ["Line 1", "Line 2"]
        assert snapshot["transcript_length"] == 2
        assert len(snapshot["detected_questions"]) == 1
        assert "metadata" in snapshot

    @pytest.mark.asyncio
    async def test_to_json(self, state):
        """Test JSON serialization."""
        await state.add_transcript_line("Test line")

        json_str = state.to_json()
        data = json.loads(json_str)

        assert "transcript" in data
        assert data["transcript"][0] == "Test line"

    @pytest.mark.asyncio
    async def test_from_snapshot(self, state):
        """Test restoring state from snapshot."""
        # Create snapshot
        await state.add_transcript_line("Line 1")
        question = DetectedQuestion(question="Q?", timestamp=0.0)
        await state.add_detected_question(question)
        snapshot = state.to_snapshot()

        # Create new state and restore
        new_state = ApplicationState()
        await new_state.from_snapshot(snapshot)

        assert new_state.get_transcript() == ["Line 1"]
        assert len(new_state.get_detected_questions()) == 1

    @pytest.mark.asyncio
    async def test_to_legacy_dict(self, state):
        """Test legacy dictionary format."""
        await state.add_transcript_line("Test line")
        question = DetectedQuestion(question="Q?", timestamp=0.0)
        await state.add_detected_question(question)

        legacy = state.to_legacy_dict()

        assert "transcript_lines" in legacy
        assert "detected" in legacy
        assert "qa_log" in legacy
        assert legacy["transcript_lines"][0] == "Test line"


# ============================================================================
# State Reset Tests
# ============================================================================

class TestStateReset:
    """Test state reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_clears_all_state(self, state):
        """Test that reset clears all conversation data."""
        await state.add_transcript_line("Line 1")
        await state.update_text_buffer("text", "buffer")

        question = DetectedQuestion(question="Q?", timestamp=0.0)
        await state.add_detected_question(question)

        answer = AnsweredQuestion(question="Q", answer="A", timestamp=0.0)
        await state.add_answered_question(answer)

        # Reset
        await state.reset()

        assert state.get_transcript_length() == 0
        assert state.get_detected_questions_count() == 0
        assert state.get_answered_questions_count() == 0
        assert state.get_latest_text() == ""
        assert state.get_sentence_buffer() == ""


# ============================================================================
# Singleton Tests
# ============================================================================

class TestSingleton:
    """Test singleton pattern."""

    def test_get_state_singleton(self, reset_singleton):
        """Test that get_state returns singleton."""
        state1 = get_state()
        state2 = get_state()

        assert state1 is state2

    @pytest.mark.asyncio
    async def test_singleton_persists_state(self, reset_singleton):
        """Test that singleton persists state across calls."""
        state = get_state()
        await state.add_transcript_line("Test")

        state2 = get_state()
        assert state2.get_transcript_length() == 1


# ============================================================================
# Statistics Tests
# ============================================================================

class TestStatistics:
    """Test statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_stats(self, state):
        """Test getting state statistics."""
        await state.add_transcript_line("Line 1")
        await state.add_transcript_line("Line 2")

        await state.add_ws_client(MagicMock())
        await state.add_ws_client(MagicMock())

        stats = state.get_stats()

        assert stats["transcript_lines"] == 2
        assert stats["ws_clients"] == 2
        assert "created_at" in stats
        assert "last_modified" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
