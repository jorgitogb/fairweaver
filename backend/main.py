import json
import logging
import os
from pathlib import Path

import yaml
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mapping_engine import MappingEngine
from oai_pmh import harvest, list_sets
from plugins.loader import load_plugins
from sickle.oaiexceptions import CannotDisseminateFormat, NoRecordsMatch

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())

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
plugins = load_plugins()
engine = MappingEngine(PIVOT_REGISTRY_PATH, plugins)

# SAIA API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://chat-ai.academiccloud.de/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "meta-llama-3.1-8b-instruct")


# ── Pivots ────────────────────────────────────────────────────────────────────


@app.get("/pivots", summary="List all registered pivot profiles")
def list_pivots():
    return {"pivots": engine.list_pivots()}


@app.post("/pivots/recommend", summary="AI-recommend best pivot for an input document")
async def recommend_pivot(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or ""
    
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=422, detail="File must be valid JSON")
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="File must be a JSON object, not an array")

    # Detect format from content
    source_format = detect_format(filename, content)

    # Parse using plugin to get flat field structure (for proper matching)
    if source_format in plugins:
        try:
            parsed = plugins[source_format].load(content)
            data = parsed
        except Exception:
            pass

    recommendations = engine.recommend_pivot(data, source_format=source_format)
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

    result = engine.convert_nested(parsed, source_format, pivot_id)
    output = result.get("json_ld", result)
    return {
        "pivot_id": pivot_id,
        "source_format": source_format,
        "output": output,
        "field_rules": result.get("field_rules", []),
        "missing_fields": result.get("missing_fields", []),
        "confidence": result.get("confidence", None),
        "mapping_source": result.get("mapping_source"),
        "model": result.get("model"),
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


# ── OAI-PMH Harvesting ───────────────────────────────────────────────────────


class HarvestRequest(BaseModel):
    base_url: str
    metadata_prefix: str
    set: str | None = None
    from_date: str | None = None
    until_date: str | None = None
    max_records: int = 10000


@app.post("/harvest", summary="Harvest metadata from OAI-PMH endpoint")
async def harvest_oai_pmh(req: HarvestRequest):
    try:
        result = harvest(
            base_url=req.base_url,
            metadata_prefix=req.metadata_prefix,
            set=req.set,
            from_date=req.from_date,
            until_date=req.until_date,
            max_records=req.max_records,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except CannotDisseminateFormat as e:
        raise HTTPException(
            status_code=400,
            detail=f"Metadata prefix '{req.metadata_prefix}' not supported by this repository: {e}",
        )
    except NoRecordsMatch:
        return {"records": [], "total": 0, "metadata_format": req.metadata_prefix}
    return result


class ListSetsRequest(BaseModel):
    base_url: str


@app.post("/list-sets", summary="List available sets from OAI-PMH endpoint")
async def list_oai_sets(req: ListSetsRequest):
    try:
        sets = list_sets(base_url=req.base_url)
        return {"sets": sets}
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Helpers ───────────────────────────────────────────────────────────────────


def detect_format(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    mapping = {
        ".json": "isa_json",
        ".xml": "datacite_xml",
        ".csv": "darwin_core_csv",
        ".xlsx": "miappe_xlsx",
    }
    if ext == ".json":
        try:
            data = json.loads(content)
            ctx = data.get("@context")
            if isinstance(ctx, str) and "schema.org" in ctx:
                return "schema_org"
            if isinstance(ctx, list):
                ctx_str = " ".join(str(c) for c in ctx)
                if "ro-crate" in ctx_str.lower() or "ro/crate" in ctx_str.lower():
                    return "ro_crate"
            if "@graph" in data:
                return "ro_crate"
        except Exception:
            pass
    return mapping.get(ext, "isa_json")


# ── Serve React build in production ──────────────────────────────────────────

FRONTEND_BUILD = Path("../frontend/dist")
if FRONTEND_BUILD.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD), html=True), name="static")
