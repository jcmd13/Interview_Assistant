"""
Settings API WebSocket Endpoints for Interview Assistant

Provides WebSocket message handlers for:
- Getting/updating settings
- Hot-reloading plugins
- Swapping models without restart
- Managing system configuration

Used by admin UI and menu bar app to control server at runtime.
"""

import json
from typing import Dict, Any, Callable, Optional
from dataclasses import asdict

from src.core.logger import get_logger

logger = get_logger("system.settings_api")


class SettingsAPIHandler:
    """
    Handles all settings-related WebSocket commands.

    Maps incoming JSON commands to appropriate handlers.
    """

    def __init__(self, settings_manager, transcriber, llm_analyzer, plugin_manager):
        """
        Initialize handler with references to server components.

        Args:
            settings_manager: SettingsManager instance
            transcriber: PluginTranscriber instance
            llm_analyzer: PluginLLMAnalyzer instance
            plugin_manager: PluginManager instance
        """
        self.settings = settings_manager
        self.transcriber = transcriber
        self.llm = llm_analyzer
        self.plugins = plugin_manager

        # Command dispatch table
        self.handlers: Dict[str, Callable] = {
            # Settings management
            "get_settings": self.get_settings,
            "set_setting": self.set_setting,
            "get_setting": self.get_setting,
            "reset_settings": self.reset_settings,

            # Model swapping (hot-reload)
            "swap_whisper_model": self.swap_whisper_model,
            "swap_llm_model": self.swap_llm_model,
            "get_available_models": self.get_available_models,

            # Plugin management
            "get_plugins": self.get_plugins,
            "reload_plugin": self.reload_plugin,
            "get_plugin_status": self.get_plugin_status,

            # System control
            "get_server_status": self.get_server_status,
        }

    async def handle_command(self, cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle incoming WebSocket command.

        Args:
            cmd: Command dict with "cmd" key and optional args

        Returns:
            Response dict to send back to client, or None for no response
        """
        cmd_type = cmd.get("cmd")

        if cmd_type not in self.handlers:
            logger.warning("unknown_command", cmd=cmd_type)
            return {
                "type": "error",
                "error": f"Unknown command: {cmd_type}",
            }

        try:
            handler = self.handlers[cmd_type]
            result = await handler(cmd)
            return result
        except Exception as e:
            logger.error("command_handler_error", cmd=cmd_type, error=str(e))
            return {
                "type": "error",
                "error": f"Error processing {cmd_type}: {str(e)}",
            }

    # =====================
    # Settings Management
    # =====================

    async def get_settings(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Get all current settings"""
        try:
            all_settings = self.settings.get_all_settings()
            return {
                "type": "settings",
                "settings": all_settings,
            }
        except Exception as e:
            logger.error("get_settings_failed", error=str(e))
            raise

    async def get_setting(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific setting value"""
        key = cmd.get("key")
        if not key:
            return {
                "type": "error",
                "error": "Missing 'key' parameter",
            }

        try:
            value = self.settings.get_setting(key)
            return {
                "type": "setting_value",
                "key": key,
                "value": value,
            }
        except KeyError:
            return {
                "type": "error",
                "error": f"Setting not found: {key}",
            }

    async def set_setting(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Update a setting value"""
        key = cmd.get("key")
        value = cmd.get("value")

        if not key:
            return {
                "type": "error",
                "error": "Missing 'key' parameter",
            }

        try:
            self.settings.set_setting(key, value)
            logger.info("setting_updated", key=key, value=value)

            return {
                "type": "setting_updated",
                "key": key,
                "value": value,
                "requires_restart": self._setting_requires_restart(key),
            }
        except ValueError as e:
            return {
                "type": "error",
                "error": str(e),
            }

    async def reset_settings(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Reset all settings to defaults"""
        try:
            self.settings.reset_to_defaults()
            logger.info("settings_reset_to_defaults")

            return {
                "type": "settings_reset",
                "message": "All settings reset to defaults",
            }
        except Exception as e:
            logger.error("reset_settings_failed", error=str(e))
            raise

    # =====================
    # Model Swapping
    # =====================

    async def swap_whisper_model(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Hot-swap Whisper transcription model"""
        model = cmd.get("model")

        if not model:
            return {
                "type": "error",
                "error": "Missing 'model' parameter",
            }

        try:
            if not self.transcriber:
                return {
                    "type": "error",
                    "error": "Transcriber not initialized",
                }

            await self.transcriber.reload_model(model)
            logger.info("whisper_model_swapped", model=model)

            return {
                "type": "model_swapped",
                "component": "transcriber",
                "model": model,
                "timestamp": self._timestamp(),
            }

        except Exception as e:
            logger.error("whisper_swap_failed", error=str(e), model=model)
            raise

    async def swap_llm_model(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Hot-swap LLM model"""
        model = cmd.get("model")

        if not model:
            return {
                "type": "error",
                "error": "Missing 'model' parameter",
            }

        try:
            if not self.llm:
                return {
                    "type": "error",
                    "error": "LLM analyzer not initialized",
                }

            await self.llm.reload_model(model)
            logger.info("llm_model_swapped", model=model)

            return {
                "type": "model_swapped",
                "component": "llm",
                "model": model,
                "timestamp": self._timestamp(),
            }

        except Exception as e:
            logger.error("llm_swap_failed", error=str(e), model=model)
            raise

    async def get_available_models(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of available models for swapping"""
        return {
            "type": "available_models",
            "transcriber": {
                "current": "tiny",  # TODO: Get from transcriber
                "available": ["tiny", "base", "small", "medium", "large"],
            },
            "llm": {
                "current": "gpt-oss:120b-cloud",  # TODO: Get from LLM
                "available": [
                    "gpt-oss:120b-cloud",
                    "mistral",
                    "neural-chat",
                    "openhermes2.5-mistral",
                ],
            },
        }

    # =====================
    # Plugin Management
    # =====================

    async def get_plugins(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of all plugins and their status"""
        try:
            plugins_status = self.plugins.list_plugins()

            return {
                "type": "plugin_list",
                "plugins": {
                    name: asdict(status)
                    for name, status in plugins_status.items()
                },
            }
        except Exception as e:
            logger.error("get_plugins_failed", error=str(e))
            raise

    async def reload_plugin(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Reload a specific plugin"""
        name = cmd.get("name")

        if not name:
            return {
                "type": "error",
                "error": "Missing 'name' parameter",
            }

        try:
            success = await self.plugins.reload_plugin(name)

            if success:
                logger.info("plugin_reloaded", name=name)
                return {
                    "type": "plugin_reloaded",
                    "name": name,
                    "timestamp": self._timestamp(),
                }
            else:
                return {
                    "type": "error",
                    "error": f"Failed to reload plugin: {name}",
                }

        except Exception as e:
            logger.error("reload_plugin_failed", error=str(e), name=name)
            raise

    async def get_plugin_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific plugin"""
        name = cmd.get("name")

        if not name:
            return {
                "type": "error",
                "error": "Missing 'name' parameter",
            }

        try:
            plugins_status = self.plugins.list_plugins()

            if name not in plugins_status:
                return {
                    "type": "error",
                    "error": f"Plugin not found: {name}",
                }

            status = plugins_status[name]
            return {
                "type": "plugin_status",
                "plugin": asdict(status),
            }

        except Exception as e:
            logger.error("get_plugin_status_failed", error=str(e), name=name)
            raise

    # =====================
    # System Status
    # =====================

    async def get_server_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall server status"""
        return {
            "type": "server_status",
            "status": "running",
            "components": {
                "transcriber": self.transcriber is not None,
                "llm": self.llm is not None,
                "plugins": self.plugins is not None,
                "settings": self.settings is not None,
            },
            "timestamp": self._timestamp(),
        }

    # =====================
    # Helpers
    # =====================

    def _setting_requires_restart(self, key: str) -> bool:
        """Check if setting requires server restart"""
        restart_required = {
            "server_host",
            "server_port",
            "sample_rate",
            "buffer_size",
        }
        return key in restart_required

    def _timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
