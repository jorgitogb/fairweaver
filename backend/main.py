from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import yaml
import json
import os
from pathlib import Path

from mapping_engine import MappingEngine
from plugins.loader import load_plugins

app = FastAPI(
    title="FAIRweaver API",
    description="AI-assisted metadata interoperability platform with selectable pivot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load pivot registry and plugins on startup
PIVOT_REGISTRY_PATH = Path(os.getenv("PIVOT_REGISTRY_PATH", "pivot_registry.yaml"))
engine = MappingEngine(PIVOT_REGISTRY_PATH)
plugins = load_plugins()


# ── Pivots ────────────────────────────────────────────────────────────────────

@app.get("/pivots", summary="List all registered pivot profiles")
def list_pivots():
    return {"pivots": engine.list_pivots()}


@app.post("/pivots/recommend", summary="AI-recommend best pivot for an input document")
async def recommend_pivot(file: UploadFile = File(...)):
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=422, detail="File must be valid JSON")
    recommendations = engine.recommend_pivot(data)
    return {"recommendations": recommendations}


# ── Mappings ──────────────────────────────────────────────────────────────────

@app.get("/mappings", summary="List available YAML mappings")
def list_mappings(source_format: str = None, pivot: str = None):
    mappings = engine.list_mappings(source_format=source_format, pivot=pivot)
    return {"mappings": mappings}


@app.post("/mappings/generate", summary="AI-generate a YAML mapping draft")
async def generate_mapping(
    file: UploadFile = File(...),
    pivot_id: str = "bioschemas_dataset",
):
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=422, detail="File must be valid JSON")
    mapping = engine.generate_mapping(data, pivot_id)
    return {"mapping": mapping, "pivot_id": pivot_id}


@app.post("/mappings/validate", summary="Validate a YAML mapping file")
async def validate_mapping(file: UploadFile = File(...)):
    content = await file.read()
    try:
        mapping = yaml.safe_load(content)
    except Exception:
        raise HTTPException(status_code=422, detail="File must be valid YAML")
    result = engine.validate_mapping(mapping)
    return result


# ── Conversion ────────────────────────────────────────────────────────────────

@app.post("/convert", summary="Convert input metadata to pivot JSON-LD")
async def convert(
    file: UploadFile = File(...),
    source_format: str = "auto",
    pivot_id: str = "bioschemas_dataset",
):
    content = await file.read()
    filename = file.filename or ""

    # Auto-detect format from extension
    if source_format == "auto":
        source_format = detect_format(filename, content)

    if source_format not in plugins:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{source_format}'. Supported: {list(plugins.keys())}",
        )

    try:
        parsed = plugins[source_format].load(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")

    result = engine.convert(parsed, source_format, pivot_id)
    return {
        "pivot_id": pivot_id,
        "source_format": source_format,
        "output": result["json_ld"],
        "missing_fields": result.get("missing_fields", []),
        "confidence": result.get("confidence", None),
    }


@app.post("/convert/chain", summary="Bidirectional conversion via pivot")
async def convert_chain(
    file: UploadFile = File(...),
    source_format: str = "auto",
    pivot_id: str = "bioschemas_dataset",
    target_format: str = "datacite",
):
    content = await file.read()
    filename = file.filename or ""

    if source_format == "auto":
        source_format = detect_format(filename, content)

    if source_format not in plugins:
        raise HTTPException(status_code=422, detail=f"Unsupported source format '{source_format}'")
    if target_format not in plugins:
        raise HTTPException(status_code=422, detail=f"Unsupported target format '{target_format}'")

    try:
        parsed = plugins[source_format].load(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")

    pivot_result = engine.convert(parsed, source_format, pivot_id)
    output = plugins[target_format].write(pivot_result["json_ld"])

    return {
        "source_format": source_format,
        "pivot_id": pivot_id,
        "target_format": target_format,
        "output": output,
        "missing_fields": pivot_result.get("missing_fields", []),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def detect_format(filename: str, content: bytes) -> str:
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
            if "@type" in data and "ro-crate" in str(data).lower():
                return "ro_crate"
        except Exception:
            pass
    return mapping.get(ext, "isa_json")


# ── Serve React build in production ──────────────────────────────────────────

FRONTEND_BUILD = Path("../frontend/dist")
if FRONTEND_BUILD.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD), html=True), name="static")