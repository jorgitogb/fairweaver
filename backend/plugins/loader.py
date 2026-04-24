"""
FAIRweaver plugin loader.
Discovers all *_plugin.py files in plugins/formats/ automatically.
"""

import importlib.util
import sys
from pathlib import Path


def load_plugins() -> dict:
    plugins = {}
    plugins_dir = Path(__file__).parent.parent / "formats"

    for plugin_file in plugins_dir.glob("*_plugin.py"):
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_file.stem] = module
        spec.loader.exec_module(module)

        if hasattr(module, "FORMAT_ID"):
            plugins[module.FORMAT_ID] = module

    return plugins