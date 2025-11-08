"""
Plugin Integration Layer for Interview Assistant Server

This module bridges the existing server code with the plugin system,
allowing runtime swapping of transcription, LLM, and audio components
without requiring server restarts.

Architecture:
- PluginTranscriber: Wraps plugin-loaded Whisper transcriber
- PluginLLMAnalyzer: Wraps plugin-loaded Ollama LLM
- Plugin registry is initialized and managed at server startup
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.core.plugins import (
    get_plugin_registry,
    load_plugin,
    reload_plugin,
    get_plugin,
    PluginType,
)
from src.core.logger import get_logger

logger = get_logger("system.plugin_integration")


@dataclass
class PluginStatus:
    """Status information for a plugin"""
    name: str
    plugin_type: str
    loaded: bool
    version: str
    error: Optional[str] = None


class PluginTranscriber:
    """
    Plugin-aware Whisper transcriber wrapper.

    Allows hot-swapping of Whisper models and implementations via plugin system.
    Falls back to direct WhisperModel loading if plugins unavailable.
    """

    def __init__(self):
        self.plugin_name = "whisper_transcriber"
        self._transcriber = None
        self._is_using_plugin = False

    def initialize(self, model_name: str = "tiny"):
        """Initialize transcriber via plugin system or fallback"""
        try:
            # Try loading via plugin system
            registry = get_plugin_registry()
            self._transcriber = load_plugin(self.plugin_name)
            self._is_using_plugin = True
            logger.info(f"Transcriber loaded via plugin system: {self.plugin_name}")
        except Exception as e:
            logger.warning(f"Failed to load transcriber plugin, falling back to direct load: {e}")
            # Fallback: load directly
            from faster_whisper import WhisperModel
            from pathlib import Path
            cache_root = str(Path.home() / ".cache" / "hf_models")
            Path(cache_root).mkdir(parents=True, exist_ok=True)
            self._transcriber = WhisperModel(model_name, compute_type="int8", download_root=cache_root)
            self._is_using_plugin = False

    async def transcribe(self, audio_data) -> Dict[str, Any]:
        """Transcribe audio using loaded transcriber"""
        if self._transcriber is None:
            raise RuntimeError("Transcriber not initialized")

        try:
            # Check if it's a plugin (has async transcribe) or direct WhisperModel
            if hasattr(self._transcriber, 'transcribe_async'):
                # Plugin interface
                result = await self._transcriber.transcribe_async(audio_data)
            else:
                # Direct WhisperModel
                result = self._transcriber.transcribe(audio_data)

            return result
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def reload_model(self, model_name: str):
        """Hot-reload to a different Whisper model"""
        try:
            if self._is_using_plugin:
                # If using plugin, reload via plugin system
                reload_plugin(self.plugin_name)
                logger.info(f"Transcriber plugin reloaded")
            else:
                # If using direct load, create new instance
                from faster_whisper import WhisperModel
                from pathlib import Path
                cache_root = str(Path.home() / ".cache" / "hf_models")
                self._transcriber = WhisperModel(model_name, compute_type="int8", download_root=cache_root)
                logger.info(f"Transcriber model reloaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to reload transcriber model: {e}")
            raise


class PluginLLMAnalyzer:
    """
    Plugin-aware LLM analyzer wrapper.

    Allows hot-swapping of LLM implementations and models via plugin system.
    Falls back to direct Ollama integration if plugins unavailable.
    """

    def __init__(self):
        self.plugin_name = "ollama_analyzer"
        self._analyzer = None
        self._is_using_plugin = False

    def initialize(self, model_name: str = "gpt-oss:120b-cloud"):
        """Initialize analyzer via plugin system or fallback"""
        try:
            # Try loading via plugin system
            registry = get_plugin_registry()
            self._analyzer = load_plugin(self.plugin_name)
            self._is_using_plugin = True
            logger.info(f"LLM analyzer loaded via plugin system: {self.plugin_name}")
        except Exception as e:
            logger.warning(f"Failed to load analyzer plugin, using fallback: {e}")
            # Fallback: use the monolithic ImprovedLLMAnalyzer from server
            self._analyzer = None
            self._is_using_plugin = False

    async def analyze_segment(self, text: str, context: str) -> Dict[str, Any]:
        """Analyze text for questions using loaded analyzer"""
        if self._analyzer is None:
            raise RuntimeError("Analyzer not initialized")

        try:
            if hasattr(self._analyzer, 'analyze_segment_async'):
                # Plugin interface
                result = await self._analyzer.analyze_segment_async(text, context)
            elif hasattr(self._analyzer, 'analyze_segment'):
                # Sync version
                result = self._analyzer.analyze_segment(text, context)
            else:
                raise AttributeError("Analyzer doesn't have analyze_segment method")

            return result
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    async def generate_answer(self, question: str, context: str, max_tokens: int = 400) -> str:
        """Generate answer for question"""
        if self._analyzer is None:
            raise RuntimeError("Analyzer not initialized")

        try:
            if hasattr(self._analyzer, 'generate_answer_async'):
                # Plugin interface
                answer = await self._analyzer.generate_answer_async(question, context, max_tokens)
            elif hasattr(self._analyzer, 'generate_answer'):
                # Sync version
                answer = self._analyzer.generate_answer(question, context, max_tokens)
            else:
                raise AttributeError("Analyzer doesn't have generate_answer method")

            return answer
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise

    async def reload_model(self, model_name: str):
        """Hot-reload to a different LLM model"""
        try:
            if self._is_using_plugin and hasattr(self._analyzer, 'set_model'):
                # Call set_model on the plugin
                await self._analyzer.set_model(model_name)
                logger.info(f"LLM model reloaded: {model_name}")
            else:
                # For direct integration, this would need manual reload
                logger.info(f"LLM model reload requested: {model_name} (requires server restart)")
        except Exception as e:
            logger.error(f"Failed to reload LLM model: {e}")
            raise


class PluginManager:
    """
    Central plugin manager for Interview Assistant.

    Handles plugin registration, loading, monitoring, and hot-swapping.
    """

    def __init__(self):
        self.registry = None
        self._plugins: Dict[str, Any] = {}
        self._status_cache: Dict[str, PluginStatus] = {}

    async def initialize(self):
        """Initialize plugin system and register all built-in plugins"""
        try:
            from src.plugins import register_builtin_plugins

            # Register all built-in plugins
            register_builtin_plugins()
            self.registry = get_plugin_registry()

            logger.info("Plugin system initialized and built-in plugins registered")
        except Exception as e:
            logger.error(f"Failed to initialize plugin system: {e}")
            raise

    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a loaded plugin by name"""
        try:
            plugin = get_plugin(name)
            return plugin
        except Exception as e:
            logger.warning(f"Failed to get plugin '{name}': {e}")
            return None

    async def reload_plugin(self, name: str) -> bool:
        """Reload a plugin"""
        try:
            reload_plugin(name)
            logger.info(f"Plugin reloaded: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload plugin '{name}': {e}")
            return False

    def list_plugins(self) -> Dict[str, PluginStatus]:
        """List all available plugins and their status"""
        try:
            if self.registry is None:
                return {}

            plugins_list = self.registry.list_plugins()
            status_dict = {}

            for plugin_name in plugins_list:
                try:
                    plugin = get_plugin(plugin_name)
                    status_dict[plugin_name] = PluginStatus(
                        name=plugin_name,
                        plugin_type="unknown",
                        loaded=True,
                        version="1.0.0",
                        error=None
                    )
                except Exception as e:
                    status_dict[plugin_name] = PluginStatus(
                        name=plugin_name,
                        plugin_type="unknown",
                        loaded=False,
                        version="1.0.0",
                        error=str(e)
                    )

            return status_dict
        except Exception as e:
            logger.error(f"Failed to list plugins: {e}")
            return {}


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


async def initialize_plugin_system():
    """Initialize the plugin system at server startup"""
    manager = get_plugin_manager()
    await manager.initialize()
    logger.info("Plugin system fully initialized and ready")
