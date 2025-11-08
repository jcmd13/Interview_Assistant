"""
Transcription Package

This package contains speech-to-text transcription and analysis components.

Components:
- whisper: Whisper-based transcription (current implementation)
- model_manager: Hot-swapping Whisper models without restart
- question_classifier: Smart question classification (greeting/technical/career)
- Future: Other transcription plugins
"""

from .model_manager import WhisperModelManager, get_model_manager
from .question_classifier import QuestionClassifier, QuestionType, get_classifier

__all__ = [
    "WhisperModelManager",
    "get_model_manager",
    "QuestionClassifier",
    "QuestionType",
    "get_classifier",
]
