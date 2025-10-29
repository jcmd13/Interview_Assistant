"""
Tests for Configuration Management System

This test module verifies that the configuration system works correctly
with proper validation, environment variable support, and .env file loading.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from pydantic import ValidationError

from src.core.config import (
    InterviewAssistantConfig,
    ServerConfig,
    AudioConfig,
    WhisperConfig,
    OllamaConfig,
    LLMBehaviorConfig,
    RateLimitConfig,
    DebugConfig,
    FeatureFlags,
    ConfigManager,
    get_config,
    reload_config,
)


# ============================================================================
# Fixtures
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
def reset_config_manager():
    """Reset ConfigManager singleton between tests."""
    ConfigManager._instance = None
    ConfigManager._config = None
    yield
    ConfigManager._instance = None
    ConfigManager._config = None


# ============================================================================
# Test Default Values
# ============================================================================

class TestDefaultConfiguration:
    """Test that default configuration values are correct."""

    def test_server_defaults(self, clean_env):
        """Test ServerConfig default values."""
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8123

    def test_audio_defaults(self, clean_env):
        """Test AudioConfig default values."""
        config = AudioConfig()
        assert config.sample_rate == 16000
        assert config.window_seconds == 6.0
        assert config.hop_seconds == 0.8
        assert config.energy_gate == 1e-4

    def test_whisper_defaults(self, clean_env):
        """Test WhisperConfig default values."""
        config = WhisperConfig()
        assert config.model_name == "tiny"
        assert config.compute_type == "int8"
        assert config.force_lang is None
        assert "Software engineering" in config.initial_prompt

    def test_ollama_defaults(self, clean_env):
        """Test OllamaConfig default values."""
        config = OllamaConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.model == "gpt-oss:120b-cloud"
        assert config.model_cloud == "gpt-oss:120b-cloud"

    def test_llm_behavior_defaults(self, clean_env):
        """Test LLMBehaviorConfig default values."""
        config = LLMBehaviorConfig()
        assert config.enabled is True
        assert config.include_full_transcript is True
        assert config.tech_interview_mode is True
        assert config.context_mode == "full"
        assert config.max_output_tokens == 400
        assert config.persona == "candidate"

    def test_rate_limit_defaults(self, clean_env):
        """Test RateLimitConfig default values."""
        config = RateLimitConfig()
        assert config.min_gap_sec == 0.5
        assert config.answers_per_min == 15
        assert config.seen_ttl_sec == 120.0
        assert config.max_concurrent_llm == 3

    def test_debug_defaults(self, clean_env):
        """Test DebugConfig default values."""
        config = DebugConfig()
        assert config.debug is True
        assert config.verbose_buffer is False

    def test_feature_flags_defaults(self, clean_env):
        """Test FeatureFlags default values."""
        config = FeatureFlags()
        assert config.use_structured_logging is True


# ============================================================================
# Test Validation
# ============================================================================

class TestConfigValidation:
    """Test configuration validation rules."""

    def test_server_port_validation(self, clean_env):
        """Test that port must be in valid range."""
        # Valid port
        config = ServerConfig(port=8080)
        assert config.port == 8080

        # Invalid port (too low)
        with pytest.raises(ValidationError):
            ServerConfig(port=1023)

        # Invalid port (too high)
        with pytest.raises(ValidationError):
            ServerConfig(port=70000)

    def test_audio_hop_window_validation(self, clean_env):
        """Test that hop_seconds must be less than window_seconds."""
        # Valid configuration
        config = InterviewAssistantConfig(
            audio=AudioConfig(window_seconds=6.0, hop_seconds=0.8)
        )
        assert config.audio.hop_seconds < config.audio.window_seconds

        # Invalid configuration (hop >= window)
        with pytest.raises(ValidationError):
            InterviewAssistantConfig(
                audio=AudioConfig(window_seconds=1.0, hop_seconds=2.0)
            )

    def test_whisper_model_validation(self, clean_env):
        """Test that model_name must be valid."""
        # Valid model
        config = WhisperConfig(model_name="base")
        assert config.model_name == "base"

        # Invalid model
        with pytest.raises(ValidationError):
            WhisperConfig(model_name="invalid_model")

    def test_ollama_url_validation(self, clean_env):
        """Test that Ollama URL must have proper format."""
        # Valid URLs
        config1 = OllamaConfig(base_url="http://localhost:11434")
        assert config1.base_url == "http://localhost:11434"

        config2 = OllamaConfig(base_url="https://api.ollama.com")
        assert config2.base_url == "https://api.ollama.com"

        # URL with trailing slash (should be stripped)
        config3 = OllamaConfig(base_url="http://localhost:11434/")
        assert config3.base_url == "http://localhost:11434"

        # Invalid URL (no protocol)
        with pytest.raises(ValidationError):
            OllamaConfig(base_url="localhost:11434")

    def test_context_mode_validation(self, clean_env):
        """Test that context_mode must be valid."""
        # Valid modes
        for mode in ["full", "window", "headtail"]:
            config = LLMBehaviorConfig(context_mode=mode)
            assert config.context_mode == mode

        # Invalid mode
        with pytest.raises(ValidationError):
            LLMBehaviorConfig(context_mode="invalid")

    def test_persona_validation(self, clean_env):
        """Test that persona must be valid."""
        # Valid personas
        for persona in ["candidate", "assistant", "neutral"]:
            config = LLMBehaviorConfig(persona=persona)
            assert config.persona == persona

        # Invalid persona
        with pytest.raises(ValidationError):
            LLMBehaviorConfig(persona="invalid")


# ============================================================================
# Test Environment Variable Loading
# ============================================================================

class TestEnvironmentVariables:
    """Test loading configuration from environment variables."""

    def test_load_from_env_vars(self, clean_env, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("SERVER__HOST", "0.0.0.0")
        monkeypatch.setenv("SERVER__PORT", "9000")
        monkeypatch.setenv("WHISPER__MODEL_NAME", "base")
        monkeypatch.setenv("DEBUG__DEBUG", "false")

        # Load configuration
        config = InterviewAssistantConfig()

        # Verify values
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 9000
        assert config.whisper.model_name == "base"
        assert config.debug.debug is False

    def test_env_var_case_insensitive(self, clean_env, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("server__host", "192.168.1.1")
        monkeypatch.setenv("SERVER__PORT", "8080")

        config = InterviewAssistantConfig()
        assert config.server.host == "192.168.1.1"
        assert config.server.port == 8080


# ============================================================================
# Test .env File Loading
# ============================================================================

class TestEnvFileLoading:
    """Test loading configuration from .env file."""

    def test_load_from_env_file(self, clean_env, temp_env_file, monkeypatch):
        """Test loading configuration from .env file."""
        # Write test .env file
        temp_env_file.write_text(
            "SERVER__HOST=10.0.0.1\n"
            "SERVER__PORT=7000\n"
            "WHISPER__MODEL_NAME=medium\n"
            "OLLAMA__MODEL=llama3.2:1b\n"
        )

        # Change to temp directory and load config
        monkeypatch.setenv("DOTENV_PATH", str(temp_env_file))
        monkeypatch.chdir(temp_env_file.parent)

        # Note: pydantic-settings looks for .env in current directory
        # So we need to rename our temp file to .env
        env_file = temp_env_file.parent / ".env"
        temp_env_file.rename(env_file)

        try:
            config = InterviewAssistantConfig()

            # Verify values loaded from .env
            assert config.server.host == "10.0.0.1"
            assert config.server.port == 7000
            assert config.whisper.model_name == "medium"
            assert config.ollama.model == "llama3.2:1b"
        finally:
            env_file.unlink(missing_ok=True)


# ============================================================================
# Test Legacy Dictionary Conversion
# ============================================================================

class TestLegacyDictConversion:
    """Test conversion to legacy flat dictionary format."""

    def test_to_legacy_dict(self, clean_env):
        """Test that to_legacy_dict() produces correct format."""
        config = InterviewAssistantConfig()
        legacy = config.to_legacy_dict()

        # Check that all expected keys exist
        expected_keys = [
            "HOST", "PORT", "SAMPLE_RATE", "WINDOW_SECONDS", "HOP_SECONDS",
            "ENERGY_GATE", "MODEL_NAME", "COMPUTE_TYPE", "FORCE_LANG",
            "INITIAL_PROMPT", "OLLAMA_BASE_URL", "OLLAMA_MODEL",
            "OLLAMA_MODEL_CLOUD", "LLM_ENABLED", "LLM_INCLUDE_FULL_TRANSCRIPT",
            "TECH_INTERVIEW_MODE", "LLM_CONTEXT_MODE", "LLM_WINDOW_LINES",
            "LLM_HEAD_LINES", "LLM_TAIL_LINES", "LLM_MAX_CONTEXT_CHARS",
            "MAX_OUTTOK", "PERSONA", "LLM_MIN_GAP_SEC", "ANSWERS_PER_MIN",
            "SEEN_TTL_SEC", "MAX_CONCURRENT_LLM", "DEBUG", "VERBOSE_BUFFER",
            "USE_STRUCTURED_LOGGING"
        ]

        for key in expected_keys:
            assert key in legacy, f"Missing key: {key}"

        # Check some values
        assert legacy["HOST"] == "127.0.0.1"
        assert legacy["PORT"] == 8123
        assert legacy["MODEL_NAME"] == "tiny"
        assert legacy["DEBUG"] is True


# ============================================================================
# Test ConfigManager Singleton
# ============================================================================

class TestConfigManager:
    """Test ConfigManager singleton pattern."""

    def test_singleton_pattern(self, clean_env, reset_config_manager):
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager.get_instance()
        manager2 = ConfigManager.get_instance()

        assert manager1 is manager2

    def test_get_config_function(self, clean_env, reset_config_manager):
        """Test get_config() convenience function."""
        config1 = get_config()
        config2 = get_config()

        # Should return same config object
        assert config1 is config2

    def test_reload_config(self, clean_env, reset_config_manager, monkeypatch):
        """Test configuration reload."""
        # Get initial config
        config1 = get_config()
        initial_port = config1.server.port

        # Change environment
        monkeypatch.setenv("SERVER__PORT", "9999")

        # Reload should pick up new value
        reload_config()
        config2 = get_config()

        assert config2.server.port == 9999
        assert config2.server.port != initial_port

    def test_runtime_update(self, clean_env, reset_config_manager):
        """Test runtime configuration updates."""
        manager = ConfigManager.get_instance()
        config = manager.config

        # Initial value
        assert config.server.port == 8123

        # Update at runtime
        manager.update(server__port=7777)

        # Verify update
        assert config.server.port == 7777


# ============================================================================
# Test Complete Configuration
# ============================================================================

class TestCompleteConfiguration:
    """Test complete configuration scenarios."""

    def test_full_config_structure(self, clean_env):
        """Test that full configuration has all sections."""
        config = InterviewAssistantConfig()

        # Verify all sections exist
        assert hasattr(config, "server")
        assert hasattr(config, "audio")
        assert hasattr(config, "whisper")
        assert hasattr(config, "ollama")
        assert hasattr(config, "llm")
        assert hasattr(config, "rate_limit")
        assert hasattr(config, "debug")
        assert hasattr(config, "features")

    def test_nested_access(self, clean_env):
        """Test nested configuration access."""
        config = InterviewAssistantConfig()

        # Nested access should work
        assert config.server.host == "127.0.0.1"
        assert config.audio.sample_rate == 16000
        assert config.whisper.model_name == "tiny"
        assert config.llm.persona == "candidate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
