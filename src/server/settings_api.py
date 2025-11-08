"""
Live Settings Management API
Handles runtime configuration changes without server restart
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
import json


class SettingType(Enum):
    """Types of settings"""
    MIC_ENABLED = "mic_enabled"
    TRANSCRIPTION_ENABLED = "transcription_enabled"
    ANSWERS_ENABLED = "answers_enabled"
    WHISPER_MODEL = "whisper_model"
    OLLAMA_MODEL = "ollama_model"
    AUDIO_DEVICE = "audio_device"
    FILTER_GREETINGS = "filter_greetings"
    USER_TOPICS = "user_topics"


@dataclass
class Setting:
    """Individual setting"""
    key: SettingType
    value: Any
    previous_value: Optional[Any] = None
    changed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key.value,
            "value": self.value,
            "previous_value": self.previous_value,
            "changed": self.changed,
        }


class SettingsManager:
    """Manages application settings with change notifications"""

    def __init__(self):
        """Initialize settings manager"""
        self.settings: Dict[SettingType, Setting] = {
            SettingType.MIC_ENABLED: Setting(SettingType.MIC_ENABLED, True),
            SettingType.TRANSCRIPTION_ENABLED: Setting(SettingType.TRANSCRIPTION_ENABLED, True),
            SettingType.ANSWERS_ENABLED: Setting(SettingType.ANSWERS_ENABLED, True),
            SettingType.WHISPER_MODEL: Setting(SettingType.WHISPER_MODEL, "base"),
            SettingType.OLLAMA_MODEL: Setting(SettingType.OLLAMA_MODEL, "gpt-oss:120b-cloud"),
            SettingType.AUDIO_DEVICE: Setting(SettingType.AUDIO_DEVICE, "0"),
            SettingType.FILTER_GREETINGS: Setting(SettingType.FILTER_GREETINGS, True),
            SettingType.USER_TOPICS: Setting(
                SettingType.USER_TOPICS,
                {
                    "primary": ["DevOps", "IT Security", "Python", "AWS"],
                    "adjacent": ["Cloud Computing", "CI/CD", "Kubernetes"],
                },
            ),
        }

        # Callbacks for setting changes
        self.on_change_callbacks: Dict[SettingType, List[Callable]] = {
            key: [] for key in SettingType
        }

    def get(self, key: SettingType) -> Any:
        """Get a setting value"""
        if key in self.settings:
            return self.settings[key].value
        return None

    def get_all(self) -> Dict[str, Any]:
        """Get all settings as dict"""
        return {key.value: setting.value for key, setting in self.settings.items()}

    def set(self, key: SettingType, value: Any) -> bool:
        """Set a setting and trigger callbacks"""
        if key not in self.settings:
            return False

        setting = self.settings[key]
        old_value = setting.value

        # Validate before setting
        if not self._validate_setting(key, value):
            return False

        setting.previous_value = old_value
        setting.value = value
        setting.changed = True

        # Trigger callbacks
        self._notify_change(key, old_value, value)
        return True

    def _validate_setting(self, key: SettingType, value: Any) -> bool:
        """Validate setting value"""
        if key in [SettingType.MIC_ENABLED, SettingType.TRANSCRIPTION_ENABLED, SettingType.ANSWERS_ENABLED, SettingType.FILTER_GREETINGS]:
            return isinstance(value, bool)

        if key == SettingType.WHISPER_MODEL:
            valid_models = ["tiny", "base", "small", "medium", "large"]
            return isinstance(value, str) and value in valid_models

        if key == SettingType.OLLAMA_MODEL:
            return isinstance(value, str) and len(value) > 0

        if key == SettingType.AUDIO_DEVICE:
            return isinstance(value, str)

        if key == SettingType.USER_TOPICS:
            return isinstance(value, dict) and "primary" in value and "adjacent" in value

        return True

    def on_change(self, key: SettingType, callback: Callable):
        """Register callback for setting changes"""
        if key not in self.on_change_callbacks:
            self.on_change_callbacks[key] = []
        self.on_change_callbacks[key].append(callback)

    def _notify_change(self, key: SettingType, old_value: Any, new_value: Any):
        """Notify all callbacks about a setting change"""
        if key in self.on_change_callbacks:
            for callback in self.on_change_callbacks[key]:
                try:
                    callback(old_value, new_value)
                except Exception as e:
                    print(f"Error in setting change callback: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert all settings to dict"""
        return {key.value: setting.to_dict() for key, setting in self.settings.items()}

    def from_dict(self, data: Dict[str, Any]):
        """Load settings from dict"""
        for key_str, value in data.items():
            try:
                key = SettingType(key_str)
                if isinstance(value, dict) and "value" in value:
                    self.set(key, value["value"])
                else:
                    self.set(key, value)
            except (ValueError, KeyError):
                continue


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get or create global settings manager"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
