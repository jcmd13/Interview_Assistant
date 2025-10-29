"""
Shared Fixtures and Configuration for Tests

This module provides common fixtures, setup/teardown logic, and test utilities
for the test suite.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from unittest.mock import MagicMock, AsyncMock


# ============================================================================
# Session-Level Setup
# ============================================================================

def pytest_configure(config):
    """Configure pytest session."""
    # Add src directory to path for imports
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


# ============================================================================
# Async Test Support
# ============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    """Provide an async client fixture for testing async functions."""
    # This is a template - extend based on actual client needs
    client = AsyncMock()
    yield client


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def clean_env(monkeypatch) -> Generator:
    """Clean environment variables before each test."""
    # Store original env
    original_env = dict(os.environ)

    # Clear relevant env vars
    env_keys = [k for k in os.environ if any(
        k.startswith(prefix) for prefix in [
            "SERVER_", "AUDIO_", "WHISPER_", "OLLAMA_",
            "LLM_", "RATE_", "DEBUG_", "FEATURE_"
        ]
    )]
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)

    yield

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_env_file() -> Generator:
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        env_path = Path(f.name)
        yield env_path
    env_path.unlink(missing_ok=True)


@pytest.fixture
def temp_dir() -> Generator:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def reset_config_manager():
    """Reset ConfigManager singleton between tests."""
    try:
        from src.core.config import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = None
    except ImportError:
        pass

    yield

    try:
        from src.core.config import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = None
    except ImportError:
        pass


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def reset_logging():
    """Reset logging configuration between tests."""
    try:
        from src.core.logger import _logger_state
        _logger_state.clear()
    except (ImportError, AttributeError):
        pass

    yield

    try:
        from src.core.logger import _logger_state
        _logger_state.clear()
    except (ImportError, AttributeError):
        pass


@pytest.fixture
def capture_logs():
    """Capture log output for assertion."""
    import io
    from contextlib import redirect_stdout, redirect_stderr

    class LogCapture:
        def __init__(self):
            self.stdout = io.StringIO()
            self.stderr = io.StringIO()
            self._stdout_redirect = None
            self._stderr_redirect = None

        def __enter__(self):
            self._stdout_redirect = redirect_stdout(self.stdout)
            self._stderr_redirect = redirect_stderr(self.stderr)
            self._stdout_redirect.__enter__()
            self._stderr_redirect.__enter__()
            return self

        def __exit__(self, *args):
            self._stdout_redirect.__exit__(*args)
            self._stderr_redirect.__exit__(*args)

        def get_output(self):
            return self.stdout.getvalue()

        def get_error(self):
            return self.stderr.getvalue()

    return LogCapture()


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_ollama():
    """Mock Ollama API client."""
    mock = AsyncMock()
    mock.chat = AsyncMock(return_value={
        "message": {
            "content": "This is a test response"
        }
    })
    return mock


@pytest.fixture
def mock_whisper():
    """Mock Whisper transcription engine."""
    mock = MagicMock()
    mock.transcribe = MagicMock(return_value={
        "text": "Test transcription",
        "segments": [
            {"id": 0, "start": 0, "end": 1, "text": "Test"}
        ]
    })
    return mock


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    mock = AsyncMock()
    mock.send = AsyncMock()
    mock.recv = AsyncMock()
    mock.close = AsyncMock()
    return mock


# ============================================================================
# Audio Fixtures
# ============================================================================

@pytest.fixture
def sample_audio_data():
    """Provide sample audio data (PCM, 16-bit, 16kHz)."""
    import array
    # Generate 1 second of silence
    sample_rate = 16000
    duration_sec = 1
    samples = array.array('h', [0] * (sample_rate * duration_sec))
    return samples.tobytes()


@pytest.fixture
def sample_audio_with_tone():
    """Provide sample audio data with a test tone (440Hz)."""
    import math
    import array

    sample_rate = 16000
    duration_sec = 1
    frequency = 440  # Hz

    samples = []
    for i in range(int(sample_rate * duration_sec)):
        # Generate sine wave
        sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(sample)

    audio_array = array.array('h', samples)
    return audio_array.tobytes()


# ============================================================================
# Marker Registration (for custom markers)
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on module location."""
    for item in items:
        # Add 'unit' marker to all tests in tests/ by default
        if "test_" in str(item.fspath):
            if "integration" not in item.keywords:
                item.add_marker(pytest.mark.unit)
