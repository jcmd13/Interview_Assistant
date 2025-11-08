"""
Plugin System Initialization

Provides convenient access to plugin registration and loading.
Auto-discovers and registers available plugins.
"""

from src.core.plugins import (
    PluginRegistry,
    PluginInterface,
    PluginType,
    PluginMetadata,
    get_plugin_registry,
    load_plugin,
    get_plugin,
    unload_plugin,
    reload_plugin,
    list_plugins,
)
from src.core.logger import get_logger

logger = get_logger("system.plugins.init")


def register_builtin_plugins():
    """Register all built-in plugins with the system"""
    registry = get_plugin_registry()

    # Register Whisper Transcription Plugin
    registry.register(
        PluginMetadata(
            name="whisper_transcriber",
            version="1.0.0",
            plugin_type=PluginType.TRANSCRIPTION,
            module_path="src.transcription.whisper",
            class_name="WhisperTranscriber",
            dependencies=[],
        )
    )

    # Register Streaming Whisper Plugin
    registry.register(
        PluginMetadata(
            name="streaming_whisper_transcriber",
            version="1.0.0",
            plugin_type=PluginType.TRANSCRIPTION,
            module_path="src.transcription.whisper",
            class_name="StreamingWhisperTranscriber",
            dependencies=[],
        )
    )

    # Register Ollama LLM Plugin
    registry.register(
        PluginMetadata(
            name="ollama_llm",
            version="1.0.0",
            plugin_type=PluginType.LLM,
            module_path="src.llm.ollama",
            class_name="OllamaLLM",
            dependencies=[],
        )
    )

    # Register Ollama Analyzer
    registry.register(
        PluginMetadata(
            name="ollama_analyzer",
            version="1.0.0",
            plugin_type=PluginType.CUSTOM,
            module_path="src.llm.ollama",
            class_name="OllamaAnalyzer",
            dependencies=["ollama_llm"],
        )
    )

    # Register Audio Effects Plugins
    audio_effects = [
        ("noise_gate", "NoiseGate", "Removes silence below threshold"),
        ("high_pass_filter", "HighPassFilter", "Removes low-frequency rumble"),
        ("voice_enhancer", "VoiceEnhancer", "Boosts voice presence"),
        ("dynamic_compressor", "DynamicCompressor", "Balances volume levels"),
        ("spectral_noise_reducer", "SpectralNoiseReducer", "Reduces background noise"),
    ]

    for plugin_id, class_name, description in audio_effects:
        registry.register(
            PluginMetadata(
                name=plugin_id,
                version="1.0.0",
                plugin_type=PluginType.AUDIO,
                module_path="src.audio.effects",
                class_name=class_name,
                dependencies=[],
                config={"description": description},
            )
        )

    logger.info(
        "Plugins registered",
        total_plugins=len(registry.list_plugins()),
        by_type={
            pt.value: len(registry.list_plugins(pt))
            for pt in PluginType
        },
    )


def get_default_plugin_config():
    """Get default plugin configuration for a fresh install"""
    return {
        "transcription": {
            "primary": "whisper_transcriber",
            "config": {
                "model_name": "base",
                "compute_type": "int8",
                "force_lang": None,
            },
        },
        "llm": {
            "primary": "ollama_llm",
            "config": {
                "base_url": "http://localhost:11434",
                "default_model": "gpt-oss:120b-cloud",
            },
        },
        "audio_processing": [
            {
                "name": "high_pass_filter",
                "enabled": True,
                "config": {"cutoff_hz": 80},
            },
            {
                "name": "noise_gate",
                "enabled": True,
                "config": {"threshold_db": -40},
            },
            {
                "name": "spectral_noise_reducer",
                "enabled": False,  # Disabled by default, can be enabled for noisy environments
                "config": {"reduction_factor": 0.5},
            },
            {
                "name": "voice_enhancer",
                "enabled": False,  # Disabled by default, enable for clarity
                "config": {"intensity": 1.5},
            },
            {
                "name": "dynamic_compressor",
                "enabled": False,  # Disabled by default, enable for very dynamic speech
                "config": {"ratio": 4.0, "threshold_db": -20},
            },
        ],
    }


__all__ = [
    # Core functions
    "register_builtin_plugins",
    "get_default_plugin_config",
    # Re-exported from core
    "PluginRegistry",
    "PluginInterface",
    "PluginType",
    "PluginMetadata",
    "get_plugin_registry",
    "load_plugin",
    "get_plugin",
    "unload_plugin",
    "reload_plugin",
    "list_plugins",
]
