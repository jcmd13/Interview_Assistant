"""
Plugin System Foundation

Provides:
- Plugin interface/protocol definitions
- Plugin registry and discovery
- Plugin loader with dependency management
- Plugin configuration management
- Hot-reload support
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, Type, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import importlib
import inspect
from pathlib import Path

from src.core.logger import get_logger

logger = get_logger("system.plugins")

T = TypeVar('T', bound='PluginInterface')


class PluginType(str, Enum):
    """Plugin type categories"""
    TRANSCRIPTION = "transcription"  # Speech-to-text backends
    LLM = "llm"                      # Language model backends
    AUDIO = "audio"                  # Audio processing
    PERSISTENCE = "persistence"      # Data storage
    MONITORING = "monitoring"        # Performance/health monitoring
    CUSTOM = "custom"                # User-defined plugins


class PluginInterface(ABC):
    """Base interface all plugins must implement"""

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Human-readable plugin name"""
        pass

    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """Plugin version (semver: major.minor.patch)"""
        pass

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Type of plugin"""
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """List of required dependencies (package names)"""
        pass

    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize plugin with optional configuration

        Args:
            config: Plugin-specific configuration dict
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup and shutdown plugin"""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if plugin is ready to use"""
        pass


@dataclass
class PluginMetadata:
    """Plugin metadata"""

    name: str
    version: str
    plugin_type: PluginType
    module_path: str
    class_name: str
    dependencies: List[str]
    config: Optional[Dict[str, Any]] = None
    is_loaded: bool = False
    instance: Optional[PluginInterface] = None

    def __repr__(self) -> str:
        return (
            f"PluginMetadata({self.name}@{self.version}, "
            f"type={self.plugin_type}, loaded={self.is_loaded})"
        )


class PluginRegistry:
    """Central registry for all plugins"""

    def __init__(self):
        self._plugins: Dict[str, PluginMetadata] = {}
        self._instances: Dict[str, PluginInterface] = {}
        self._type_index: Dict[PluginType, List[str]] = {pt: [] for pt in PluginType}
        self._dependency_graph: Dict[str, List[str]] = {}

    def register(self, metadata: PluginMetadata) -> None:
        """
        Register a plugin

        Args:
            metadata: Plugin metadata
        """
        if metadata.name in self._plugins:
            logger.warning(
                "Plugin already registered, overwriting",
                plugin_name=metadata.name,
            )

        self._plugins[metadata.name] = metadata
        self._type_index[metadata.plugin_type].append(metadata.name)
        self._dependency_graph[metadata.name] = metadata.dependencies

        logger.info(
            "Plugin registered",
            plugin_name=metadata.name,
            plugin_type=metadata.plugin_type,
            version=metadata.version,
        )

    def get(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name"""
        return self._plugins.get(name)

    def get_instance(self, name: str) -> Optional[PluginInterface]:
        """Get loaded plugin instance"""
        return self._instances.get(name)

    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[PluginMetadata]:
        """
        List all registered plugins, optionally filtered by type

        Args:
            plugin_type: Optional plugin type filter

        Returns:
            List of plugin metadata
        """
        if plugin_type is None:
            return list(self._plugins.values())
        return [self._plugins[name] for name in self._type_index.get(plugin_type, [])]

    def _check_dependencies(self, plugin_name: str) -> bool:
        """Check if all dependencies are satisfied"""
        deps = self._dependency_graph.get(plugin_name, [])
        for dep in deps:
            if dep not in self._instances:
                logger.error(
                    "Dependency not loaded",
                    plugin_name=plugin_name,
                    missing_dependency=dep,
                )
                return False
        return True

    def load(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load and initialize a plugin

        Args:
            name: Plugin name
            config: Optional runtime configuration

        Returns:
            True if loaded successfully, False otherwise
        """
        metadata = self.get(name)
        if not metadata:
            logger.error("Plugin not found", plugin_name=name)
            return False

        if metadata.is_loaded:
            logger.warning("Plugin already loaded", plugin_name=name)
            return True

        # Check dependencies first
        if not self._check_dependencies(name):
            logger.error(
                "Cannot load plugin, dependencies not satisfied",
                plugin_name=name,
            )
            return False

        try:
            # Load module dynamically
            module = importlib.import_module(metadata.module_path)
            plugin_class = getattr(module, metadata.class_name)

            # Create instance
            instance = plugin_class()

            # Merge configs
            final_config = {**(metadata.config or {}), **(config or {})}

            # Initialize
            instance.initialize(final_config if final_config else None)

            # Store instance
            self._instances[name] = instance
            metadata.instance = instance
            metadata.is_loaded = True

            logger.info(
                "Plugin loaded successfully",
                plugin_name=name,
                version=metadata.version,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to load plugin",
                plugin_name=name,
                error=str(e),
            )
            return False

    def unload(self, name: str) -> bool:
        """
        Unload and shutdown a plugin

        Args:
            name: Plugin name

        Returns:
            True if unloaded successfully
        """
        metadata = self.get(name)
        if not metadata or not metadata.is_loaded:
            return False

        try:
            instance = self._instances.pop(name, None)
            if instance:
                instance.shutdown()

            metadata.is_loaded = False
            metadata.instance = None

            logger.info("Plugin unloaded", plugin_name=name)
            return True

        except Exception as e:
            logger.error("Failed to unload plugin", plugin_name=name, error=str(e))
            return False

    def reload(self, name: str) -> bool:
        """Hot-reload a plugin"""
        metadata = self.get(name)
        if not metadata:
            return False

        config = metadata.config
        if not self.unload(name):
            return False

        return self.load(name, config)

    def get_dependency_order(self) -> List[str]:
        """
        Get plugins in dependency order (topological sort)

        Returns:
            List of plugin names in load order
        """
        # Simple topological sort
        visited = set()
        order = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            for dep in self._dependency_graph.get(name, []):
                if dep in self._plugins:
                    visit(dep)
            order.append(name)

        for name in self._plugins:
            visit(name)

        return order


# Global plugin registry
_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry"""
    return _registry


def register_plugin(metadata: PluginMetadata) -> None:
    """Register a plugin"""
    _registry.register(metadata)


def load_plugin(name: str, config: Optional[Dict[str, Any]] = None) -> bool:
    """Load a plugin"""
    return _registry.load(name, config)


def get_plugin(name: str) -> Optional[PluginInterface]:
    """Get loaded plugin instance"""
    return _registry.get_instance(name)


def unload_plugin(name: str) -> bool:
    """Unload a plugin"""
    return _registry.unload(name)


def reload_plugin(name: str) -> bool:
    """Hot-reload a plugin"""
    return _registry.reload(name)


def list_plugins(plugin_type: Optional[PluginType] = None) -> List[PluginMetadata]:
    """List registered plugins"""
    return _registry.list_plugins(plugin_type)
