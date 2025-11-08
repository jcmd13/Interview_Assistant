"""
Whisper Model Manager
Handles hot-swapping of Whisper models without server restart
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from faster_whisper import WhisperModel
from datetime import datetime


class WhisperModelManager:
    """Manages Whisper model hot-swapping"""

    def __init__(self):
        """Initialize model manager"""
        self.current_model_name: str = "base"
        self.current_model: Optional[WhisperModel] = None
        self.models: Dict[str, WhisperModel] = {}  # Cache of loaded models
        self.is_loading: bool = False
        self.load_start_time: Optional[float] = None

    async def load_model(self, model_name: str, device: str = "cpu", compute_type: str = "int8") -> bool:
        """
        Load a Whisper model asynchronously
        Returns True if successful, False otherwise
        """
        if self.is_loading:
            print(f"Model is already loading...")
            return False

        if model_name == self.current_model_name and self.current_model is not None:
            print(f"Model {model_name} is already loaded")
            return True

        try:
            self.is_loading = True
            self.load_start_time = datetime.now()

            loop = asyncio.get_event_loop()

            # Check if already cached
            if model_name in self.models:
                self.current_model = self.models[model_name]
                self.current_model_name = model_name
                print(f"Loaded {model_name} from cache")
                return True

            # Load new model in executor to avoid blocking
            def _load():
                return WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                    local_files_only=False
                )

            model = await loop.run_in_executor(None, _load)
            self.models[model_name] = model
            self.current_model = model
            self.current_model_name = model_name

            load_time = (datetime.now() - self.load_start_time).total_seconds()
            print(f"✓ Loaded Whisper model '{model_name}' in {load_time:.2f}s")
            return True

        except Exception as e:
            print(f"✗ Failed to load model {model_name}: {e}")
            return False

        finally:
            self.is_loading = False
            self.load_start_time = None

    async def transcribe(self, audio: Any, language: Optional[str] = None, initial_prompt: Optional[str] = None) -> Any:
        """
        Transcribe audio with current model
        Returns transcription segments
        """
        if self.current_model is None:
            raise RuntimeError("No model loaded")

        if self.is_loading:
            # Wait for model to load before transcribing
            while self.is_loading:
                await asyncio.sleep(0.1)

        loop = asyncio.get_event_loop()

        def _transcribe():
            return self.current_model.transcribe(
                audio,
                language=language,
                vad_filter=True,
                initial_prompt=initial_prompt
            )

        segments, info = await loop.run_in_executor(None, _transcribe)
        return segments, info

    def get_status(self) -> Dict[str, Any]:
        """Get current status of model manager"""
        return {
            "current_model": self.current_model_name,
            "is_loading": self.is_loading,
            "cached_models": list(self.models.keys()),
            "loaded": self.current_model is not None,
        }

    async def unload_model(self, model_name: Optional[str] = None):
        """Unload a specific model or all non-current models"""
        if model_name:
            if model_name in self.models and model_name != self.current_model_name:
                del self.models[model_name]
                print(f"Unloaded model {model_name}")
        else:
            # Keep only current model in memory
            models_to_remove = [k for k in self.models.keys() if k != self.current_model_name]
            for m in models_to_remove:
                del self.models[m]
            print(f"Unloaded {len(models_to_remove)} unused models")


# Global model manager instance
_model_manager: Optional[WhisperModelManager] = None


def get_model_manager() -> WhisperModelManager:
    """Get or create global model manager"""
    global _model_manager
    if _model_manager is None:
        _model_manager = WhisperModelManager()
    return _model_manager
