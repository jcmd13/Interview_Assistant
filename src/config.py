"""
Configuration Management System

This module provides type-safe configuration management using Pydantic schemas
with support for .env files, environment variables, and runtime overrides.

Configuration Priority (lowest to highest):
1. Hardcoded defaults (defined in Pydantic models)
2. .env file values
3. Environment variables
4. Runtime overrides (via ConfigManager.update())

Key Features:
- Type validation with Pydantic v2
- Automatic .env file loading
- Environment variable override support
- Nested configuration structure
- Singleton ConfigManager for global access
- Hot-reload support for runtime updates
"""

import os
from typing import Optional, Literal
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


# ============================================================================
# Configuration Schemas
# ============================================================================

class ServerConfig(BaseModel):
    """WebSocket server configuration."""

    host: str = Field(
        default="127.0.0.1",
        description="Server host address"
    )
    port: int = Field(
        default=8123,
        ge=1024,
        le=65535,
        description="Server port number"
    )


class AudioConfig(BaseModel):
    """Audio processing configuration."""

    sample_rate: int = Field(
        default=16000,
        ge=8000,
        le=48000,
        description="Audio sample rate in Hz"
    )
    window_seconds: float = Field(
        default=6.0,
        gt=0.0,
        le=30.0,
        description="Audio processing window duration"
    )
    hop_seconds: float = Field(
        default=0.8,
        gt=0.0,
        le=10.0,
        description="Hop duration between audio windows"
    )
    energy_gate: float = Field(
        default=1e-4,
        ge=0.0,
        description="Minimum energy threshold for processing"
    )

    @field_validator("hop_seconds")
    @classmethod
    def validate_hop(cls, v: float, info) -> float:
        """Ensure hop_seconds is less than window_seconds."""
        # Note: Can't access window_seconds here in Pydantic v2
        # This validation will be done in the main config
        return v


class WhisperConfig(BaseModel):
    """Whisper speech recognition configuration."""

    model_name: Literal["tiny", "base", "small", "medium", "large"] = Field(
        default="tiny",
        description="Whisper model size"
    )
    compute_type: Literal["int8", "float16", "float32"] = Field(
        default="int8",
        description="Computation precision type"
    )
    force_lang: Optional[str] = Field(
        default=None,
        description="Force specific language (e.g., 'en')"
    )
    initial_prompt: str = Field(
        default="Software engineering, data structures, algorithms, system design, "
                "cloud computing, AWS, Azure, GCP, microservices, API, CI/CD, DevOps, "
                "machine learning, data science, Python, Java, JavaScript, SQL, NoSQL, "
                "product management, agile, scrum, cloud security, SOC operations, "
                "incident response, SIEM, EDR, IAM, RBAC, zero trust.",
        description="Initial prompt for better transcription of technical jargon"
    )


class OllamaConfig(BaseModel):
    """Ollama LLM service configuration."""

    base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL"
    )
    model: str = Field(
        default="gpt-oss:120b-cloud",
        description="Primary Ollama model name"
    )
    model_cloud: str = Field(
        default="gpt-oss:120b-cloud",
        description="Cloud Ollama model name"
    )

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL has proper format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")


class LLMBehaviorConfig(BaseModel):
    """LLM behavior and context configuration."""

    enabled: bool = Field(
        default=True,
        description="Enable/disable LLM features"
    )
    include_full_transcript: bool = Field(
        default=True,
        description="Include full transcript in LLM context"
    )
    tech_interview_mode: bool = Field(
        default=True,
        description="Optimize for technical interview questions"
    )
    context_mode: Literal["full", "window", "headtail"] = Field(
        default="full",
        description="Context mode for LLM prompts"
    )
    window_lines: int = Field(
        default=200,
        ge=10,
        le=1000,
        description="Number of lines for window context mode"
    )
    head_lines: int = Field(
        default=80,
        ge=10,
        le=500,
        description="Number of head lines for headtail mode"
    )
    tail_lines: int = Field(
        default=400,
        ge=10,
        le=1000,
        description="Number of tail lines for headtail mode"
    )
    max_context_chars: int = Field(
        default=400000,
        ge=1000,
        le=1000000,
        description="Maximum context characters for LLM"
    )
    max_output_tokens: int = Field(
        default=400,
        ge=50,
        le=4096,
        description="Maximum output tokens for LLM responses"
    )
    persona: Literal["candidate", "assistant", "neutral"] = Field(
        default="candidate",
        description="Response persona mode"
    )


class RateLimitConfig(BaseModel):
    """LLM rate limiting configuration."""

    min_gap_sec: float = Field(
        default=0.5,
        ge=0.0,
        le=60.0,
        description="Minimum gap between LLM responses in seconds"
    )
    answers_per_min: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Maximum answers per minute"
    )
    seen_ttl_sec: float = Field(
        default=120.0,
        ge=10.0,
        le=3600.0,
        description="Time-to-live for seen questions cache"
    )
    max_concurrent_llm: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum concurrent LLM requests"
    )


class DebugConfig(BaseModel):
    """Debug and logging configuration."""

    debug: bool = Field(
        default=True,
        description="Enable debug output"
    )
    verbose_buffer: bool = Field(
        default=False,
        description="Enable verbose buffer logging"
    )


class FeatureFlags(BaseModel):
    """Feature flags for gradual rollout."""

    use_structured_logging: bool = Field(
        default=True,
        description="Use structured JSON logging vs print statements"
    )


# ============================================================================
# Main Configuration
# ============================================================================

class InterviewAssistantConfig(BaseSettings):
    """
    Main configuration for Interview Assistant.

    Loads configuration from:
    1. Default values (defined above)
    2. .env file (if present)
    3. Environment variables (with prefix)

    Example .env file:
        SERVER_HOST=0.0.0.0
        SERVER_PORT=8080
        WHISPER_MODEL_NAME=base
        OLLAMA_MODEL=gpt-oss:120b-cloud
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    # Nested configuration sections
    server: ServerConfig = Field(default_factory=ServerConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    llm: LLMBehaviorConfig = Field(default_factory=LLMBehaviorConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @field_validator("audio")
    @classmethod
    def validate_audio_config(cls, v: AudioConfig) -> AudioConfig:
        """Ensure hop_seconds < window_seconds."""
        if v.hop_seconds >= v.window_seconds:
            raise ValueError(
                f"hop_seconds ({v.hop_seconds}) must be less than "
                f"window_seconds ({v.window_seconds})"
            )
        return v

    def to_legacy_dict(self) -> dict:
        """
        Convert config to legacy flat dictionary format.

        This helper method provides backward compatibility with the old
        configuration system where all settings were top-level variables.

        Returns:
            Dictionary with flat keys matching old variable names
        """
        return {
            # Server
            "HOST": self.server.host,
            "PORT": self.server.port,

            # Audio
            "SAMPLE_RATE": self.audio.sample_rate,
            "WINDOW_SECONDS": self.audio.window_seconds,
            "HOP_SECONDS": self.audio.hop_seconds,
            "ENERGY_GATE": self.audio.energy_gate,

            # Whisper
            "MODEL_NAME": self.whisper.model_name,
            "COMPUTE_TYPE": self.whisper.compute_type,
            "FORCE_LANG": self.whisper.force_lang,
            "INITIAL_PROMPT": self.whisper.initial_prompt,

            # Ollama
            "OLLAMA_BASE_URL": self.ollama.base_url,
            "OLLAMA_MODEL": self.ollama.model,
            "OLLAMA_MODEL_CLOUD": self.ollama.model_cloud,

            # LLM Behavior
            "LLM_ENABLED": self.llm.enabled,
            "LLM_INCLUDE_FULL_TRANSCRIPT": self.llm.include_full_transcript,
            "TECH_INTERVIEW_MODE": self.llm.tech_interview_mode,
            "LLM_CONTEXT_MODE": self.llm.context_mode,
            "LLM_WINDOW_LINES": self.llm.window_lines,
            "LLM_HEAD_LINES": self.llm.head_lines,
            "LLM_TAIL_LINES": self.llm.tail_lines,
            "LLM_MAX_CONTEXT_CHARS": self.llm.max_context_chars,
            "MAX_OUTTOK": self.llm.max_output_tokens,
            "PERSONA": self.llm.persona,

            # Rate Limiting
            "LLM_MIN_GAP_SEC": self.rate_limit.min_gap_sec,
            "ANSWERS_PER_MIN": self.rate_limit.answers_per_min,
            "SEEN_TTL_SEC": self.rate_limit.seen_ttl_sec,
            "MAX_CONCURRENT_LLM": self.rate_limit.max_concurrent_llm,

            # Debug
            "DEBUG": self.debug.debug,
            "VERBOSE_BUFFER": self.debug.verbose_buffer,

            # Features
            "USE_STRUCTURED_LOGGING": self.features.use_structured_logging,
        }


# ============================================================================
# Configuration Manager (Singleton)
# ============================================================================

class ConfigManager:
    """
    Singleton configuration manager for global access.

    Usage:
        >>> config = ConfigManager.get_instance()
        >>> print(config.server.host)
        >>> config.update(server__port=9000)  # Hot-reload
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[InterviewAssistantConfig] = None

    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        if ConfigManager._instance is not None:
            raise RuntimeError("Use ConfigManager.get_instance() instead")
        self._load_config()

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from environment and .env file."""
        # Ensure .env is loaded
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

        # Load configuration
        self._config = InterviewAssistantConfig()

    @property
    def config(self) -> InterviewAssistantConfig:
        """Access the configuration object."""
        if self._config is None:
            self._load_config()
        return self._config

    def reload(self) -> None:
        """Reload configuration from files and environment."""
        self._load_config()

    def update(self, **kwargs) -> None:
        """
        Update configuration at runtime.

        Args:
            **kwargs: Configuration updates using double-underscore notation
                     for nested fields (e.g., server__port=9000)

        Example:
            >>> config_mgr = ConfigManager.get_instance()
            >>> config_mgr.update(server__port=9000, debug__debug=False)
        """
        if self._config is None:
            self._load_config()

        # Parse nested updates
        updates = {}
        for key, value in kwargs.items():
            parts = key.split("__")
            if len(parts) == 1:
                # Top-level field
                updates[key] = value
            elif len(parts) == 2:
                # Nested field (e.g., server__port)
                section, field = parts
                if section not in updates:
                    updates[section] = {}
                updates[section][field] = value

        # Apply updates to config
        for section, values in updates.items():
            if hasattr(self._config, section):
                section_obj = getattr(self._config, section)
                if isinstance(values, dict):
                    # Update nested fields
                    for field, value in values.items():
                        if hasattr(section_obj, field):
                            setattr(section_obj, field, value)
                else:
                    # Update section directly
                    setattr(self._config, section, values)


# ============================================================================
# Convenience Functions
# ============================================================================

def get_config() -> InterviewAssistantConfig:
    """
    Get the global configuration instance.

    Returns:
        The application configuration

    Example:
        >>> from src.config import get_config
        >>> config = get_config()
        >>> print(config.server.port)
    """
    return ConfigManager.get_instance().config


def reload_config() -> None:
    """
    Reload configuration from files and environment.

    Example:
        >>> from src.config import reload_config
        >>> reload_config()  # Re-reads .env and environment variables
    """
    ConfigManager.get_instance().reload()
