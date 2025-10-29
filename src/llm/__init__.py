"""
LLM Package

This package contains LLM-related components for question detection and answer generation.

Components:
- analyzer: Question detection and answer generation logic
- ollama: Ollama LLM implementation (current implementation)
- Future: Other LLM provider plugins (OpenAI, Anthropic, etc.)
"""

__all__ = ["ImprovedLLMAnalyzer"]

def __getattr__(name):
    if name == "ImprovedLLMAnalyzer":
        from .analyzer import ImprovedLLMAnalyzer
        return ImprovedLLMAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
