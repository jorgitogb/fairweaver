#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from mapping_engine import MappingEngine
from plugins.loader import load_plugins
import os

# Set up the mapping engine
registry_path = Path(__file__).parent / "backend" / "pivot_registry.yaml"
plugins = load_plugins()
engine = MappingEngine(registry_path, plugins)

# Load sample ARC RO-Crate
with open("/tmp/sample_arc.json", "rb") as f:
    content = f.read()

# Use the same format detection as in main.py
def detect_format(filename: str, content: bytes) -> str:
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    mapping = {
        ".json": "isa_json",
        ".xml": "datacite_xml",
        ".csv": "darwin_core_csv",
        ".xlsx": "miappe_xlsx",
    }
    # Try to detect RO-Crate from JSON content
    if ext == ".json":
        try:
            data = json.loads(content)
            # RO-Crate: check @context for ro-crate URL
            ctx = data.get("@context", [])
            if isinstance(ctx, list):
                ctx_str = " ".join(str(c) for c in ctx)
                if "ro-crate" in ctx_str.lower():
                    return "ro_crate"
            # Fallback: check for ro-crate in string representation
            if "ro-crate" in str(data).lower():
                return "ro_crate"
        except Exception:
            pass
    return mapping.get(ext, "isa_json")

source_format = detect_format("arc-ro-crate-metadata.json", content)
print(f"Detected format: {source_format}")

# Load the data using the plugin
if source_format in plugins:
    parsed = plugins[source_format].load(content)
    print(f"Parsed data keys: {list(parsed.keys())}")
else:
    print(f"Format {source_format} not in plugins")
    sys.exit(1)

# Convert using the engine (currently flat)
result = engine.convert(parsed, source_format, "fairagro_searchhub")
print("\n=== Flat conversion result ===")
print(json.dumps(result, indent=2))

# Try nested conversion if available
if hasattr(engine, 'convert_nested'):
    nested_result = engine.convert_nested(parsed, source_format, "fairagro_searchhub")
    print("\n=== Nested conversion result ===")
    print(json.dumps(nested_result, indent=2))
else:
    print("\nconvert_nested method not available")