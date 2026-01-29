# =============================================================================
# Agent Twitter - Plugin System
# =============================================================================
#
# A modular plugin system for extending Agent Twitter with custom functionality.
#
# Plugins can:
# - Add custom agent types
# - Register new tools/services
# - Hook into the post processing pipeline
# - Add custom API endpoints
#
# =============================================================================

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# Plugin Types
# =============================================================================


class PluginHook(str, Enum):
    """Available plugin hooks"""

    ON_POST_CREATE = "on_post_create"  # After a post is created
    ON_AGENT_RESPONSE = "on_agent_response"  # After an agent responds
    ON_THREAD_COMPLETE = "on_thread_complete"  # When a thread is fully processed
    ON_AGENT_LOAD = "on_agent_load"  # When agents are loaded
    ON_API_REQUEST = "on_api_request"  # Before API request is processed


# =============================================================================
# Plugin Metadata
# =============================================================================


@dataclass
class PluginMetadata:
    """Metadata about a plugin"""

    name: str
    version: str
    description: str
    author: str
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    python_version: str = "3.12+"


# =============================================================================
# Plugin Base Class
# =============================================================================


class Plugin:
    """Base class for all plugins"""

    # Override these in your plugin
    metadata: PluginMetadata = None  # type: ignore
    hooks: Dict[PluginHook, Callable] = None  # type: ignore

    def __init__(self):
        self._hooks: Dict[PluginHook, Callable] = {}
        self._register_hooks()

    def _register_hooks(self):
        """Register plugin hooks. Override in subclass."""
        # Find all methods decorated with @hook
        for name, method in inspect.getmembers(self, predicate=inspect.method):
            if hasattr(method, "_hook_type"):
                self._hooks[method._hook_type] = method

    def get_hooks(self) -> Dict[PluginHook, Callable]:
        """Get all registered hooks"""
        return self._hooks

    def on_enable(self):
        """Called when plugin is enabled"""
        pass

    def on_disable(self):
        """Called when plugin is disabled"""
        pass


# =============================================================================
# Hook Decorator
# =============================================================================


def hook(hook_type: PluginHook):
    """Decorator to register a method as a hook"""

    def decorator(func: Callable) -> Callable:
        func._hook_type = hook_type  # type: ignore
        return func

    return decorator


# =============================================================================
# Plugin Manager
# =============================================================================


class PluginManager:
    """Manages plugin loading, registration, and execution"""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[PluginHook, List[Callable]] = {h: [] for h in PluginHook}
        self._plugin_dirs: List[Path] = []

    def add_plugin_directory(self, path: Path):
        """Add a directory to search for plugins"""
        if path.is_dir():
            self._plugin_dirs.append(path)

    def discover_plugins(self) -> List[PluginMetadata]:
        """Discover all available plugins in plugin directories"""
        discovered = []
        for plugin_dir in self._plugin_dirs:
            for py_file in plugin_dir.glob("*_plugin.py"):
                try:
                    metadata = self._get_plugin_metadata(py_file)
                    if metadata:
                        discovered.append(metadata)
                except Exception as e:
                    print(f"Error discovering plugin {py_file}: {e}")
        return discovered

    def _get_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Extract metadata from a plugin file"""
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(  # type: ignore
                plugin_path.stem, plugin_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(module)

                # Find Plugin class
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (
                        inspect.isclass(item)
                        and issubclass(item, Plugin)
                        and item is not Plugin
                    ):
                        # Instantiate to get metadata
                        plugin_instance = item()
                        if plugin_instance.metadata:
                            return plugin_instance.metadata
        except Exception:
            pass
        return None

    def load_plugin(self, plugin_path: Path) -> bool:
        """Load a plugin from a file path"""
        try:
            spec = importlib.util.spec_from_file_location(  # type: ignore
                plugin_path.stem, plugin_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(module)

                # Find Plugin class
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (
                        inspect.isclass(item)
                        and issubclass(item, Plugin)
                        and item is not Plugin
                    ):
                        plugin_instance: Plugin = item()
                        metadata = plugin_instance.metadata

                        if not metadata or not metadata.enabled:
                            continue

                        # Register plugin
                        self._plugins[metadata.name] = plugin_instance

                        # Register hooks
                        for hook_type, hook_func in plugin_instance.get_hooks().items():
                            self._hooks[hook_type].append(hook_func)

                        # Call on_enable
                        plugin_instance.on_enable()

                        print(f"✅ Loaded plugin: {metadata.name} v{metadata.version}")
                        return True
        except Exception as e:
            print(f"❌ Error loading plugin {plugin_path}: {e}")
        return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name"""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            plugin.on_disable()

            # Remove hooks
            for hook_type, hook_func in plugin.get_hooks().items():
                if hook_func in self._hooks[hook_type]:
                    self._hooks[hook_type].remove(hook_func)

            del self._plugins[plugin_name]
            print(f"✅ Unloaded plugin: {plugin_name}")
            return True
        return False

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a disabled plugin"""
        # Would need to persist state and reload
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin without unloading"""
        if plugin_name in self._plugins:
            return self.unload_plugin(plugin_name)
        return False

    def execute_hook(self, hook_type: PluginHook, *args, **kwargs) -> List[Any]:
        """Execute all registered hooks for a given hook type"""
        results = []
        for hook_func in self._hooks[hook_type]:
            try:
                result = hook_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"❌ Error executing hook {hook_type}: {e}")
        return results

    def get_loaded_plugins(self) -> List[PluginMetadata]:
        """Get metadata for all loaded plugins"""
        return [p.metadata for p in self._plugins.values() if p.metadata]

    def is_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded"""
        return plugin_name in self._plugins


# =============================================================================
# Global Plugin Manager Instance
# =============================================================================

plugin_manager = PluginManager()

# Add default plugin directories
plugin_manager.add_plugin_directory(Path(__file__).parent / "plugins")


# =============================================================================
# Example Plugins
# =============================================================================


class LoggingPlugin(Plugin):
    """Example plugin that logs agent responses"""

    metadata = PluginMetadata(
        name="logging",
        version="1.0.0",
        description="Logs all agent responses to a file",
        author="Agent Twitter Team",
        enabled=True,
    )

    @hook(PluginHook.ON_AGENT_RESPONSE)
    def log_agent_response(self, agent_name: str, response: str, post_id: str):
        """Log agent responses"""
        log_entry = f"[{agent_name}] Post {post_id}: {response[:100]}..."
        print(f"📝 {log_entry}")
        # Could write to file here
        return log_entry


class AnalyticsPlugin(Plugin):
    """Example plugin that tracks usage analytics"""

    metadata = PluginMetadata(
        name="analytics",
        version="1.0.0",
        description="Tracks agent usage statistics",
        author="Agent Twitter Team",
        enabled=True,
    )

    def __init__(self):
        super().__init__()
        self.agent_calls: Dict[str, int] = {}

    @hook(PluginHook.ON_AGENT_RESPONSE)
    def track_agent_call(self, agent_name: str, response: str, post_id: str):
        """Track how many times each agent is called"""
        self.agent_calls[agent_name] = self.agent_calls.get(agent_name, 0) + 1
        return {"agent": agent_name, "total_calls": self.agent_calls[agent_name]}


# =============================================================================
# Plugin Configuration
# =============================================================================


class PluginConfig:
    """Configuration for the plugin system"""

    # Enable/disable plugin system entirely
    PLUGINS_ENABLED = True

    # Auto-load plugins from directories
    AUTOLOAD_PLUGINS = True

    # Plugin directories (relative to backend)
    PLUGIN_DIRS = ["plugins", "~/.agent-twitter/plugins"]


def initialize_plugins():
    """Initialize the plugin system"""
    if not PluginConfig.PLUGINS_ENABLED:
        return

    # Add configured directories
    for dir_name in PluginConfig.PLUGIN_DIRS:
        plugin_dir = Path(dir_name).expanduser()
        if plugin_dir.exists():
            plugin_manager.add_plugin_directory(plugin_dir)

    # Auto-load plugins if enabled
    if PluginConfig.AUTOLOAD_PLUGINS:
        for plugin_dir in plugin_manager._plugin_dirs:
            for plugin_file in plugin_dir.glob("*_plugin.py"):
                plugin_manager.load_plugin(plugin_file)


# =============================================================================
# Convenience Functions
# =============================================================================


def register_plugin(plugin: Plugin) -> bool:
    """Register a plugin programmatically"""
    if not plugin.metadata or not plugin.metadata.enabled:
        return False

    plugin_manager._plugins[plugin.metadata.name] = plugin

    for hook_type, hook_func in plugin.get_hooks().items():
        plugin_manager._hooks[hook_type].append(hook_func)

    plugin.on_enable()
    return True


def execute_hooks(hook_type: PluginHook, *args, **kwargs) -> List[Any]:
    """Execute hooks for a given type"""
    return plugin_manager.execute_hook(hook_type, *args, **kwargs)
