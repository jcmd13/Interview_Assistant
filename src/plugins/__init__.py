"""
Plugins Package

This package will contain the plugin system architecture (Phase 2).

The plugin system will allow hot-swapping of components:
- Transcription providers (Whisper, Deepgram, AssemblyAI, etc.)
- LLM providers (Ollama, OpenAI, Anthropic, etc.)
- CRM integrations (Salesforce, Dynamics 365, etc.)
- Audio processors

Plugin Architecture (Phase 2):
- Abstract base classes for each plugin type
- Plugin registry and discovery
- Dynamic loading and unloading
- Dependency management
"""

__all__ = []
