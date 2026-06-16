import json
import logging
import os
from pathlib import Path

import yaml
from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mapping_engine import MappingEngine
from formats.oai_dc_plugin import normalize as normalize_oai_dc
from oai_pmh import harvest, list_sets
from plugins.loader import load_plugins
from sickle.oaiexceptions import CannotDisseminateFormat, NoRecordsMatch
from arc_templates.fairagro_validator import FairagroArcValidator
from formats.schema_org_plugin import load as schema_org_load
from formats.ro_crate_plugin import load as ro_crate_load
from formats.schema_org_arc_plugin import load as schema_org_arc_load, write as schema_org_arc_write
import tempfile
import zipfile
import io

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

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

# ── In-memory ARC record store for OAI-PMH serving ──────────────────────────
arc_record_store: dict[str, dict] = {}  # oai_identifier → {arc: dict, raw_schema: dict, set_spec: str}


def _arc_to_fairagro_jsonld(arc_data: dict) -> dict:
    """Extract ARC RO-Crate root entity and reshape to FAIRagro Core Metadata Spec JSON-LD."""
    graph = arc_data.get("@graph", [])
    root = next((e for e in graph if e.get("@id") == "./"), {})

    # Build author array from Person entities referenced by root creator/author
    authors = []
    creator_refs = root.get("creator") or root.get("author") or []
    if isinstance(creator_refs, dict):
        creator_refs = [creator_refs]
    for ref in creator_refs:
        ref_id = ref.get("@id") if isinstance(ref, dict) else None
        if ref_id:
            person = next((e for e in graph if e.get("@id") == ref_id), None)
            if person and person.get("@type") in ("Person", "https://schema.org/Person"):
                entry = {"@type": "Person", "name": person.get("name", "")}
                if person.get("givenName"):
                    entry["givenName"] = person["givenName"]
                if person.get("familyName"):
                    entry["familyName"] = person["familyName"]
                if person.get("email"):
                    entry["email"] = person["email"]
                affil = person.get("affiliation", {})
                if isinstance(affil, dict) and affil.get("@id"):
                    org = next((e for e in graph if e.get("@id") == affil["@id"]), None)
                    if org:
                        entry["affiliation"] = {"@type": "Organization", "name": org.get("name", "")}
                authors.append(entry)

    # Build keywords as DefinedTerm array
    raw_keywords = root.get("keywords", [])
    if isinstance(raw_keywords, str):
        raw_keywords = [raw_keywords]
    keywords = []
    for kw in raw_keywords:
        if isinstance(kw, str):
            keywords.append({"@type": "DefinedTerm", "name": kw})

    # Build identifier
    raw_id = root.get("identifier", "")
    identifiers = []
    if raw_id:
        prop_id = "https://registry.identifiers.org/registry/doi" if raw_id.startswith("10.") or "doi" in raw_id.lower() else "https://schema.org/url"
        identifiers.append({
            "@type": "PropertyValue",
            "value": raw_id,
            "propertyID": prop_id,
        })

    result = {
        "@context": {"@language": "en", "@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "name": root.get("name", "Untitled"),
        "description": [root.get("description", "")] if root.get("description") else [],
        "identifier": identifiers,
        "license": root.get("license", ""),
        "url": root.get("url", ""),
        "keywords": keywords,
        "about": [{
            "@type": "DefinedTerm",
            "name": "agricultural sciences",
            "url": "http://aims.fao.org/aos/agrovoc/c_49876",
            "termCode": "c_49876",
            "inDefinedTermSet": "http://aims.fao.org/aos/agrovoc",
        }],
        "includedInDataCatalog": {
            "@type": "DataCatalog",
            "name": "FAIRweaver Demo",
            "url": "https://github.com/jorgitogb/fairweaver",
        },
    }

    if authors:
        result["author"] = authors
    if root.get("datePublished"):
        result["datePublished"] = root["datePublished"]
    if root.get("version"):
        result["version"] = root["version"]
    if root.get("inLanguage"):
        result["inLanguage"] = [root["inLanguage"]]

    return result


# ── Demo data for OAI-PMH pre-population ─────────────────────────────────────
DEMO_DATASETS = [
    {
        "filename": "wheat_basic.json",
        "set_spec": "wheat",
        "data": {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Wheat Growth Study — Basic",
            "description": "Basic study of wheat growth under standard field conditions at the Müncheberg experimental station.",
            "creator": {
                "@type": "Person",
                "name": "Maria Schmidt",
                "givenName": "Maria",
                "familyName": "Schmidt",
                "email": "maria.schmidt@example.org",
            },
            "identifier": "wheat-study-basic-001",
            "license": "https://spdx.org/licenses/CC-BY-4.0.html",
            "datePublished": "2024-03-15",
        },
    },
    {
        "filename": "wheat_intermediate.json",
        "set_spec": "wheat",
        "data": {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Wheat Phenotyping Trial — Intermediate",
            "description": "Intermediate phenotyping study of wheat varieties under drought stress, including multi-year field observations.",
            "creator": {
                "@type": "Person",
                "name": "Thomas Weber",
                "givenName": "Thomas",
                "familyName": "Weber",
                "email": "thomas.weber@example.org",
            },
            "identifier": "wheat-pheno-int-002",
            "license": "https://spdx.org/licenses/CC-BY-4.0.html",
            "datePublished": "2024-06-01",
            "keywords": ["wheat", "drought tolerance", "phenotyping", "field trial"],
            "publisher": {"@type": "Organization", "name": "Leibniz Institute of Plant Genetics"},
            "url": "https://example.org/datasets/wheat-pheno-int-002",
            "version": "1.0",
            "inLanguage": "en",
        },
    },
    {
        "filename": "wheat_full.json",
        "set_spec": "wheat",
        "data": {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Wheat Multi-Omics Study — Full",
            "description": "Comprehensive multi-omics study of wheat under heat and drought stress, integrating phenomics, transcriptomics, and metabolomics measurements.",
            "creator": {
                "@type": "Person",
                "name": "Anna Fischer",
                "givenName": "Anna",
                "familyName": "Fischer",
                "email": "anna.fischer@example.org",
                "affiliation": {"@type": "Organization", "name": "University of Hohenheim"},
            },
            "identifier": "wheat-omics-full-003",
            "license": "https://spdx.org/licenses/CC-BY-4.0.html",
            "datePublished": "2024-09-20",
            "keywords": ["wheat", "heat stress", "drought", "multi-omics", "transcriptomics", "metabolomics"],
            "measurementTechnique": "mass spectrometry",
            "funder": "DFG",
            "publisher": {"@type": "Organization", "name": "University of Hohenheim"},
            "url": "https://example.org/datasets/wheat-omics-full-003",
            "version": "2.1",
            "inLanguage": "en",
            "alternateName": "WHOMICS-2024",
        },
    },
    {
        "filename": "maize_basic.json",
        "set_spec": "maize",
        "data": {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Maize Yield Trial — Basic",
            "description": "Basic yield trial of maize cultivars under conventional tillage at the Dürnast research farm.",
            "creator": {
                "@type": "Person",
                "name": "Klaus Bauer",
                "givenName": "Klaus",
                "familyName": "Bauer",
                "email": "klaus.bauer@example.org",
            },
            "identifier": "maize-yield-basic-001",
            "license": "https://spdx.org/licenses/CC-BY-4.0.html",
            "datePublished": "2024-02-10",
        },
    },
    {
        "filename": "maize_intermediate.json",
        "set_spec": "maize",
        "data": {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Maize Nitrogen Response — Intermediate",
            "description": "Intermediate study of nitrogen fertilizer response in maize, with yield components and soil N measurements.",
            "creator": {
                "@type": "Person",
                "name": "Sandra Klein",
                "givenName": "Sandra",
                "familyName": "Klein",
                "email": "sandra.klein@example.org",
            },
            "identifier": "maize-nitro-int-002",
            "license": "https://spdx.org/licenses/CC-BY-4.0.html",
            "datePublished": "2024-05-18",
            "keywords": ["maize", "nitrogen", "fertilizer", "yield"],
            "publisher": {"@type": "Organization", "name": "Bavarian State Research Center"},
            "url": "https://example.org/datasets/maize-nitro-int-002",
            "version": "1.2",
            "inLanguage": "en",
        },
    },
    {
        "filename": "maize_full.json",
        "set_spec": "maize",
        "data": {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Maize Sensor-Based Phenotyping — Full",
            "description": "Comprehensive sensor-based phenotyping of maize using UAV multispectral imaging, soil sensors, and automated weather stations.",
            "creator": {
                "@type": "Person",
                "name": "Lena Hoffmann",
                "givenName": "Lena",
                "familyName": "Hoffmann",
                "email": "lena.hoffmann@example.org",
                "affiliation": {"@type": "Organization", "name": "Julius Kühn Institute"},
            },
            "identifier": "maize-sensor-full-003",
            "license": "https://spdx.org/licenses/CC-BY-4.0.html",
            "datePublished": "2024-11-05",
            "keywords": ["maize", "UAV", "multispectral", "sensor", "phenotyping", "precision agriculture"],
            "measurementTechnique": "multispectral imaging",
            "funder": "BMBF",
            "instrument": {"@type": "Thing", "name": "DJI Phantom 4 Multispectral", "description": "UAV-mounted multispectral sensor"},
            "publisher": {"@type": "Organization", "name": "Julius Kühn Institute"},
            "url": "https://example.org/datasets/maize-sensor-full-003",
            "version": "3.0",
            "inLanguage": "en",
            "alternateName": "MAIZE-SENSE-2024",
        },
    },
]


def _prepopulate_arc_store():
    """Convert demo Schema.org datasets to ARC RO-Crate and populate the OAI-PMH store."""
    for ds in DEMO_DATASETS:
        try:
            arc = _fallback_convert_to_arc(ds["data"])
            oai_id = f"oai:fairweaver:{ds['filename'].replace('.json', '')}"
            arc_record_store[oai_id] = {
                "arc": arc,
                "raw_schema": ds["data"],
                "set_spec": ds["set_spec"],
            }
            logger.info("Pre-populated OAI-PMH store: %s (set=%s)", oai_id, ds["set_spec"])
        except Exception as e:
            logger.warning("Failed to pre-populate %s: %s", ds["filename"], e)


def _ensure_store_populated():
    """Lazy init: populate OAI-PMH store on first call."""
    if not arc_record_store:
        _prepopulate_arc_store()


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

    result = engine.convert(parsed, source_format, pivot_id)
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


class HarvestConvertRequest(BaseModel):
    base_url: str
    metadata_prefix: str = "oai_dc"
    set: str | None = None
    from_date: str | None = None
    until_date: str | None = None
    max_records: int = 10
    pivot_id: str = "fairagro_searchhub"


@app.post("/harvest/convert", summary="Harvest and convert OAI-PMH records to pivot JSON-LD")
async def harvest_convert(req: HarvestConvertRequest):
    try:
        harvested = harvest(
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
            detail=f"Metadata prefix '{req.metadata_prefix}' not supported: {e}",
        )
    except NoRecordsMatch:
        return {"records": [], "total": 0}

    pivot_id = req.pivot_id
    source_format = "oai_dc"
    results = []
    for rec in harvested.get("records", []):
        try:
            parsed = normalize_oai_dc(rec["metadata"])
        except Exception as e:
            logger.warning("skip record %s: normalize failed: %s", rec.get("identifier"), e)
            continue
        try:
            conv = engine.convert_nested(parsed, source_format, pivot_id)
        except Exception as e:
            logger.warning("skip record %s: convert failed: %s", rec.get("identifier"), e)
            continue
        results.append(
            {
                "identifier": rec.get("identifier"),
                "datestamp": rec.get("datestamp"),
                "set_spec": rec.get("set_spec", []),
                "pivot_id": pivot_id,
                "source_format": source_format,
                "output": conv.get("json_ld", conv),
                "field_rules": conv.get("field_rules", []),
                "missing_fields": conv.get("missing_fields", []),
                "confidence": conv.get("confidence"),
                "mapping_source": conv.get("mapping_source"),
                "model": conv.get("model"),
            }
        )

    return {"records": results, "total": len(results)}


@app.get("/source-formats/schema-org", summary="Get schema.org field definitions")
def get_schema_org_fields():
    """Get schema.org JSON-LD field definitions with descriptions for mapping."""
    return {
        "source_format": "schema_org",
        "fields": [
            {
                "name": "@id",
                "label": "Identifier",
                "description": "Unique identifier for the dataset or investigation",
                "required": True,
                "examples": ["dataset-123", "https://doi.org/10.1234/example"]
            },
            {
                "name": "name",
                "label": "Name/Title",
                "description": "Primary title or name of the dataset",
                "required": True,
                "examples": ["Climate Change Dataset", "Wheat Phenotyping Trial 2023"]
            },
            {
                "name": "description",
                "label": "Description",
                "description": "Detailed description of the dataset content and purpose",
                "required": True,
                "examples": ["Long-term observations of wheat growth under drought conditions", "Genomic sequence data from Arabidopsis thaliana"]
            },
            {
                "name": "creator",
                "label": "Creator/Author",
                "description": "Person or organization responsible for creating the dataset",
                "required": False,
                "examples": [{"@type": "Person", "name": "Jane Smith"}, {"@type": "Organization", "name": "Research Institute"}]
            },
            {
                "name": "identifier",
                "label": "Identifier",
                "description": "Persistent identifier for the dataset (often same as @id)",
                "required": False,
                "examples": ["dataset-123", "DOI:10.1234/example"]
            },
            {
                "name": "datePublished",
                "label": "Publication Date",
                "description": "Date when the dataset was published or made available",
                "required": False,
                "examples": ["2023-01-15", "2023-02-20T10:30:00Z"]
            },
            {
                "name": "license",
                "label": "License",
                "description": "License governing usage and redistribution of the dataset",
                "required": False,
                "examples": ["CC-BY-4.0", "MIT", "Apache-2.0"]
            },
            {
                "name": "keywords",
                "label": "Keywords",
                "description": "Keywords or tags describing the dataset content",
                "required": False,
                "examples": ["climate", "drought", "agriculture", "genomics"]
            },
            {
                "name": "publisher",
                "label": "Publisher",
                "description": "Publisher or organization that made the dataset available",
                "required": False,
                "examples": ["Data Publishers Inc.", "University of Agricultural Research"]
            },
            {
                "name": "url",
                "label": "URL/Web Page",
                "description": "URL where more information about the dataset can be found",
                "required": False,
                "examples": ["https://example.org/dataset/123", "https://doi.org/10.1234/example"]
            },
            {
                "name": "inLanguage",
                "label": "Language",
                "description": "Language of the dataset content",
                "required": False,
                "examples": ["en", "en-US", "fr"]
            },
            {
                "name": "version",
                "label": "Version",
                "description": "Version identifier of the dataset",
                "required": False,
                "examples": ["1.0", "2.1", "beta-3"]
            }
        ]
    }


@app.get("/template-fields/{template_id}", summary="Get template field structure for ARC conversion")
def get_template_fields(template_id: str):
    """Get template field structure (mandatory vs recommended) for ARC conversion."""
    try:
        # Load the FAIRagro template to extract field structure
        validator = FairagroArcValidator()
        
        # Get the basic template info from existing method
        template_info = validator.get_template_info()
        
        # Return comprehensive field structure for ARC conversion
        return {
            "template_id": template_info["template_id"],
            "version": template_info["version"],
            "name": template_info["name"],
            "description": template_info["description"],
            "specification": template_info["specification"],
            "domains": validator.template.get("domains", []),
            "required_fields": template_info["required_fields"],
            "recommended_fields": validator.template.get("recommended_fields", {}),
            "field_paths": validator.template.get("field_paths", {}),
            "required_entities": template_info["required_entities"],
            "arc_structure": template_info["arc_structure"],
            "required_isa_files": template_info["required_isa_files"],
            "validation_rules": validator.template.get("validation_rules", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load template fields: {str(e)}")


@app.post("/convert/arc-export", summary="Convert to ARC RO-Crate format")
async def convert_to_arc(
    file: UploadFile = File(...),
    source_format: str = "auto",
    pivot_id: str = "fairagro_searchhub",
    batch: bool = False,
    preview: bool = False,
):
    """Convert input file to ARC RO-Crate format with optional batch processing and preview."""
    try:
        # Read file content
        content = await file.read()

        # For batch processing, expect a ZIP file
        if batch:
            return await _process_batch_arc_export(content, pivot_id, preview)

        # Single file processing
        return await _process_single_arc_export(file, content, source_format, pivot_id, preview)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ARC export failed: {str(e)}")


async def _process_single_arc_export(
    file: UploadFile, content: bytes, source_format: str, pivot_id: str, preview: bool
):
    """Process single file ARC export."""
    # Detect format if auto
    if source_format == "auto":
        source_format = detect_format(file.filename, content)

    # Load using appropriate plugin
    if source_format == "schema_org":
        parsed = schema_org_load(content)
    elif source_format == "schema_org_arc":
        parsed = schema_org_arc_load(content)
    elif source_format == "ro_crate":
        parsed = ro_crate_load(content, validate_fairagro=False)
    else:
        # For other formats, try to convert to Schema.org first
        # This handles the case where users upload files that need to be converted
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            parsed = {"error": "Unable to parse content"}

    # Auto-select template based on content
    if pivot_id == "auto":
        pivot_id = _auto_select_template(parsed)

    # Parse raw JSON for richer ARC building (plugins may strip fields)
    try:
        raw_data = json.loads(content)
    except Exception:
        raw_data = parsed

    # Convert Schema.org to ARC using the enhanced fallback (produces
    # Investigation/Study/Assay entities based on available fields).
    # ARCtrl library produces Investigation-only ARCs, so we prefer the fallback.
    if source_format == "schema_org":
        try:
            arc_content = _fallback_convert_to_arc(raw_data)
        except Exception as e:
            logger.warning("Fallback ARC conversion failed, trying arctrl: %s", e)
            arc_content = schema_org_arc_write(raw_data)
    elif source_format == "ro_crate":
        arc_content = raw_data
    else:
        arc_content = _fallback_convert_to_arc(raw_data)

    # Validate the generated ARC
    arc_data = json.loads(arc_content) if isinstance(arc_content, str) else arc_content
    validator = FairagroArcValidator()
    validation = validator.validate(arc_data)

    # Generate FAIRagro-compliant JSON-LD for Search Hub
    fairagro_jsonld = _arc_to_fairagro_jsonld(arc_data)

    # Store in OAI-PMH record store
    oai_id = f"oai:fairweaver:{file.filename.replace('.json', '')}"
    raw_data_for_store = raw_data if isinstance(raw_data, dict) else {}
    arc_record_store[oai_id] = {
        "arc": arc_data,
        "raw_schema": raw_data_for_store,
        "set_spec": "converted",
    }

    if preview:
        # Return preview with validation info, FAIRagro JSON-LD, and OAI-PMH identifier
        return {
            "preview": arc_data,
            "fairagro_jsonld": fairagro_jsonld,
            "validation": validation,
            "filename": file.filename.replace(".json", "") + "_arc-ro-crate.json",
            "oai_identifier": oai_id,
        }

    # Return file download
    return Response(
        content=json.dumps(arc_content, indent=2) if isinstance(arc_content, dict) else arc_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={file.filename.replace('.json', '')}_arc-ro-crate.json"
        },
    )


def _fallback_convert_to_arc(source: dict) -> dict:
    """Convert Schema.org dict to ARC RO-Crate, producing richer entity hierarchy
    when more fields are present. Uses the raw data directly to preserve all keys."""
    graph = []

    # RO-Crate metadata descriptor
    graph.append({
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": "https://w3id.org/ro/crate/1.1",
        "about": {"@id": "./"},
    })

    # Determine available field groups
    has_recommended = any(k in source for k in ("keywords", "publisher", "url", "version", "inLanguage", "alternateName"))
    has_full = any(k in source for k in ("measurementTechnique", "about", "instrument", "funder", "distribution"))

    # Helper: extract person ID
    def _person_id(p):
        if isinstance(p, dict):
            return "#" + p.get("familyName", "Person") + "_" + p.get("givenName", "Unknown").replace(" ", "_")
        return "#Person"

    # ── Root / Investigation ──
    inv = {
        "@id": "./",
        "@type": "Dataset",
        "additionalType": "Investigation",
        "name": source.get("name", "Unknown Dataset"),
        "description": source.get("description", ""),
        "identifier": source.get("@id") or source.get("identifier", ""),
        "datePublished": source.get("datePublished", ""),
        "license": source.get("license", ""),
    }

    # Creator
    creator = source.get("creator")
    if creator and isinstance(creator, dict):
        pid = _person_id(creator)
        inv["creator"] = [{"@id": pid}]
        graph.append({
            "@id": pid,
            "@type": "Person",
            "givenName": creator.get("givenName", ""),
            "familyName": creator.get("familyName", ""),
            "name": creator.get("name", ""),
            "email": creator.get("email", ""),
        })
        if "affiliation" in creator:
            aff = creator["affiliation"]
            if isinstance(aff, dict) and aff.get("name"):
                org_id = "#Organization_" + aff["name"].replace(" ", "_")
                inv["creator"][0]["@id"] = pid
                graph.append({"@id": org_id, "@type": "Organization", "name": aff["name"]})
                graph[-2]["affiliation"] = {"@id": org_id}

    if has_recommended:
        inv["keywords"] = source.get("keywords", [])
        pub = source.get("publisher")
        if isinstance(pub, dict):
            org_id = "#Publisher_" + pub.get("name", "Unknown").replace(" ", "_")
            inv["publisher"] = {"@id": org_id}
            graph.append({"@id": org_id, "@type": "Organization", "name": pub.get("name", "")})
        if source.get("url"):
            inv["url"] = source["url"]
        if source.get("version"):
            inv["version"] = source["version"]
        if source.get("inLanguage"):
            inv["inLanguage"] = source["inLanguage"]
        if source.get("alternateName"):
            inv["alternative_titles"] = [source["alternateName"]]
    if has_full:
        funder_val = source.get("funder")
        inv["funder"] = funder_val if isinstance(funder_val, str) else (funder_val.get("name", "") if isinstance(funder_val, dict) else "")
        if creator and isinstance(creator, dict):
            inv["investigationContacts"] = [{"@id": pid}]
        citation = source.get("citation")
        if isinstance(citation, dict) and citation.get("identifier"):
            pub_id = "#Publication_1"
            inv["investigationPublications"] = [{"@id": pub_id}]
            graph.append({
                "@id": pub_id, "@type": "ScholarlyArticle",
                "name": citation.get("name", ""),
                "identifier": citation.get("identifier", ""),
            })
    graph.append(inv)

    # ── Study ──
    study_id = "#Study_1"
    study = {
        "@id": study_id,
        "@type": "Dataset",
        "additionalType": "Study",
        "name": "Study of " + source.get("name", "Dataset"),
        "description": "Study derived from " + source.get("name", "Dataset"),
        "hasPart": [],
    }
    if source.get("keywords"):
        study["studyDesignDescriptors"] = source["keywords"]
    if has_full:
        crop = source.get("about")
        if isinstance(crop, dict):
            study["crop_species"] = crop.get("name", "")
            study["crop_species_uri"] = crop.get("sameAs", "")
        if source.get("crop_pest"):
            study["crop_pest"] = source["crop_pest"]
        if source.get("crop_pest_uri"):
            study["crop_pest_uri"] = source["crop_pest_uri"]
    graph.append(study)
    inv["hasPart"] = [{"@id": study_id}]

    # ── Assay ──
    assay_id = "#Assay_1"
    assay = {
        "@id": assay_id,
        "@type": "Dataset",
        "additionalType": "Assay",
        "name": "Assay for " + source.get("name", "Dataset"),
        "description": source.get("description", ""),
        "measurementTechnique": source.get("measurementTechnique", ""),
        "about": [{"@id": study_id}],
    }
    instr = source.get("instrument")
    if isinstance(instr, dict) and instr.get("name"):
        instr_id = "#Instrument_1"
        assay["instrument"] = [{"@id": instr_id}]
        graph.append({
            "@id": instr_id,
            "@type": instr.get("additionalType", "Thing"),
            "name": instr["name"],
            "description": instr.get("description", ""),
        })
    graph.append(assay)
    study["hasPart"].append({"@id": assay_id})

    return {
        "@context": ["https://w3id.org/ro/crate/1.1/context", {"@vocab": "https://schema.org/"}],
        "@graph": graph,
    }


async def _process_batch_arc_export(content: bytes, pivot_id: str, preview: bool):
    """Process batch ARC export from ZIP file."""
    results = []

    # Create temporary directory for ZIP extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "upload.zip")
        with open(zip_path, "wb") as f:
            f.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Process each file in the ZIP
            for file_info in zip_ref.infolist():
                if not file_info.is_dir() and file_info.filename.lower().endswith(".json"):
                    # Read file from ZIP
                    with zip_ref.open(file_info) as file:
                        file_content = file.read()

                    # Create mock UploadFile for processing
                    mock_file = type(
                        "MockUploadFile",
                        (),
                        {"filename": file_info.filename, "content_type": "application/json"},
                    )()

                    # Process single file
                    result = await _process_single_arc_export(
                        mock_file, file_content, "auto", pivot_id, preview
                    )

                    if preview:
                        results.append({"filename": file_info.filename, "result": result})
                    else:
                        results.append(
                            {
                                "filename": file_info.filename,
                                "arc_filename": file_info.filename.replace(".json", "")
                                + "_arc-ro-crate.json",
                                "validation": result.headers.get("X-Validation", "{}"),
                            }
                        )

    if preview:
        return {"batch_preview": results}

    # Create ZIP of all ARC files
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for result in results:
            # Re-process to get actual file content (simplified for demo)
            arc_content = json.dumps(result["result"]["preview"], indent=2).encode("utf-8")
            zipf.writestr(result["arc_filename"], arc_content)

    output_zip.seek(0)
    return Response(
        content=output_zip.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=arc_export_batch.zip"},
    )


def _auto_select_template(parsed_data: dict) -> str:
    """Auto-select appropriate ARC template based on content analysis."""
    # Check for agronomy/plant phenotyping indicators
    if any(key in parsed_data for key in ["crop_species", "crop_pest", "organism"]):
        return "fairagro_plant_phenotyping"

    # Check for genomics indicators
    if any(key in parsed_data for key in ["sequencing", "dna", "rna", "genome"]):
        return "fairagro_genomics"

    # Check for sensor/drone indicators
    if any(key in parsed_data for key in ["drone", "sensor", "measurementTechnique"]):
        return "fairagro_sensor"

    # Default to standard FAIRagro template
    return "fairagro_searchhub"


@app.post("/arc/validate/fairagro", summary="Validate ARC against FAIRagro template")
async def validate_arc_fairagro(file: UploadFile = File(...)):
    """Validate ARC file against FAIRagro template."""
    try:
        content = await file.read()
        data = json.loads(content)
        validator = FairagroArcValidator()
        validation = validator.validate(data)
        return validation
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ListSetsRequest(BaseModel):
    base_url: str


@app.post("/list-sets", summary="List available sets from OAI-PMH endpoint")
async def list_oai_sets(req: ListSetsRequest):
    try:
        sets = list_sets(base_url=req.base_url)
        return {"sets": sets}
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── OAI-PMH Serving Endpoint ─────────────────────────────────────────────────


def _oai_xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _oai_response(verb: str, content: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{__import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</responseDate>
  <request verb="{verb}">{_oai_xml_escape(_oai_base_url)}</request>
{content}
</OAI-PMH>"""


_oai_base_url = "http://localhost:8000/oai-pmh"


def _oai_header(identifier: str, datestamp: str, set_specs: list[str]) -> str:
    sets_xml = "".join(f"<setSpec>{s}</setSpec>" for s in set_specs)
    return f"""  <header>
    <identifier>{_oai_xml_escape(identifier)}</identifier>
    <datestamp>{datestamp}</datestamp>
    {sets_xml}
  </header>"""


def _arc_to_oai_metadata(arc: dict) -> str:
    """Serialize ARC JSON-LD as OAI-PMH metadata XML."""
    arc_json = json.dumps(arc, indent=2)
    escaped = _oai_xml_escape(arc_json)
    return f"""  <metadata>
    <fairagroArc xmlns="https://fairagro.net/oai/fairagro_arc" xsi:schemaLocation="https://fairagro.net/oai/fairagro_arc">
      <jsonld>{escaped}</jsonld>
    </fairagroArc>
  </metadata>"""


def _oai_error(code: str, message: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{__import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</responseDate>
  <request>{_oai_xml_escape(_oai_base_url)}</request>
  <error code="{code}">{_oai_xml_escape(message)}</error>
</OAI-PMH>"""


@app.get("/oai-pmh", summary="OAI-PMH server endpoint")
async def oai_pmh_server(
    verb: str | None = Query(None),
    identifier: str | None = Query(None),
    metadataPrefix: str | None = Query(None),
    set_: str | None = Query(None, alias="set"),
    from_: str | None = Query(None, alias="from"),
    until: str | None = Query(None),
    resumptionToken: str | None = Query(None),
):
    """Serve ARC RO-Crate records via OAI-PMH protocol."""
    _ensure_store_populated()
    if not verb:
        return Response(
            content=_oai_error("badVerb", "Missing verb argument"),
            media_type="application/xml",
            status_code=400,
        )

    if verb == "Identify":
        content = f"""  <Identify>
    <repositoryName>FAIRweaver ARC RO-Crate Repository</repositoryName>
    <baseURL>{_oai_xml_escape(_oai_base_url)}</baseURL>
    <protocolVersion>2.0</protocolVersion>
    <adminEmail>admin@example.org</adminEmail>
    <earliestDatestamp>2024-01-01</earliestDatestamp>
    <deletedRecord>no</deletedRecord>
    <granularity>YYYY-MM-DD</granularity>
  </Identify>"""
        return Response(content=_oai_response("Identify", content), media_type="application/xml")

    if verb == "ListMetadataFormats":
        content = """  <ListMetadataFormats>
    <metadataFormat>
      <metadataPrefix>fairagro_arc</metadataPrefix>
      <schema>https://fairagro.net/oai/fairagro_arc</schema>
      <metadataNamespace>https://fairagro.net/oai/fairagro_arc</metadataNamespace>
    </metadataFormat>
  </ListMetadataFormats>"""
        return Response(content=_oai_response("ListMetadataFormats", content), media_type="application/xml")

    if verb == "ListSets":
        sets_seen = set()
        sets_xml = ""
        for rec in arc_record_store.values():
            spec = rec.get("set_spec", "converted")
            if spec not in sets_seen:
                sets_seen.add(spec)
                sets_xml += f"""    <set>
      <setSpec>{spec}</setSpec>
      <setName>{spec.capitalize()} Datasets</setName>
    </set>
"""
        if not sets_xml:
            return Response(
                content=_oai_error("noRecordsMatch", "No sets available"),
                media_type="application/xml",
                status_code=400,
            )
        content = f"  <ListSets>\n{sets_xml}  </ListSets>"
        return Response(content=_oai_response("ListSets", content), media_type="application/xml")

    if verb in ("ListRecords", "ListIdentifiers"):
        if metadataPrefix != "fairagro_arc":
            return Response(
                content=_oai_error("cannotDisseminateFormat", f"Format '{metadataPrefix}' not supported"),
                media_type="application/xml",
                status_code=400,
            )

        records_xml = ""
        for oai_id, rec in arc_record_store.items():
            if set_ and rec.get("set_spec") != set_:
                continue
            header = _oai_header(oai_id, "2024-01-01", [rec.get("set_spec", "converted")])
            if verb == "ListRecords":
                metadata = _arc_to_oai_metadata(rec["arc"])
                records_xml += f"  <record>\n{header}\n{metadata}\n  </record>\n"
            else:
                records_xml += f"  <record>\n{header}\n  </record>\n"

        if not records_xml:
            return Response(
                content=_oai_error("noRecordsMatch", "No matching records"),
                media_type="application/xml",
                status_code=400,
            )

        tag = "ListRecords" if verb == "ListRecords" else "ListIdentifiers"
        content = f"  <{tag}>\n{records_xml}  </{tag}>"
        return Response(content=_oai_response(tag, content), media_type="application/xml")

    if verb == "GetRecord":
        if not identifier:
            return Response(
                content=_oai_error("badArgument", "Missing identifier argument"),
                media_type="application/xml",
                status_code=400,
            )
        if metadataPrefix != "fairagro_arc":
            return Response(
                content=_oai_error("cannotDisseminateFormat", f"Format '{metadataPrefix}' not supported"),
                media_type="application/xml",
                status_code=400,
            )

        rec = arc_record_store.get(identifier)
        if not rec:
            return Response(
                content=_oai_error("idDoesNotExist", f"Record '{identifier}' not found"),
                media_type="application/xml",
                status_code=400,
            )

        header = _oai_header(identifier, "2024-01-01", [rec.get("set_spec", "converted")])
        metadata = _arc_to_oai_metadata(rec["arc"])
        content = f"""  <GetRecord>
    <record>
{header}
{metadata}
    </record>
  </GetRecord>"""
        return Response(content=_oai_response("GetRecord", content), media_type="application/xml")

    return Response(
        content=_oai_error("badVerb", f"Verb '{verb}' not recognized"),
        media_type="application/xml",
        status_code=400,
    )


# ── Compliance Classification ─────────────────────────────────────────────────


def _schema_org_to_fairagro_keys(data: dict) -> set:
    """Extract FAIRagro field keys from Schema.org JSON-LD.

    Maps Schema.org vocabulary paths to FAIRagro-compatible field names
    so compliance scoring works on proper Schema.org files (not flat extensions).
    """
    flat = set(engine._flatten_keys(data))
    keys = set(flat)

    # Schema.org → FAIRagro semantic mappings
    if "about.name" in flat:
        keys.add("crop_species")
    if "about.sameAs" in flat or ("about" in flat and isinstance(data.get("about"), dict) and data["about"].get("@id")):
        keys.add("crop_species_uri")
    if "instrument.name" in flat:
        keys.add("sensorType")
    if "alternateName" in flat:
        keys.add("alternative_titles")
    if "@id" in flat or "identifier" in flat:
        keys.add("investigationIdentifier")
        keys.add("identifier")
    if "citation" in flat:
        keys.add("investigationPublications")

    return keys


@app.post("/compliance/classify", summary="Classify compliance level against FAIRagro template")
async def classify_compliance(file: UploadFile = File(...)):
    """Analyze uploaded file and return FAIRagro compliance level (basic/intermediate/full)."""
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=422, detail="File must be valid JSON")

    filename = file.filename or ""
    source_format = detect_format(filename, content)
    fairagro_keys = _schema_org_to_fairagro_keys(data)

    # FAIRagro template field groups
    basic_fields = {
        "name", "description", "creator", "identifier",
        "license", "datePublished",
    }
    recommended_fields = {
        "keywords", "publisher", "url", "inLanguage", "version",
        "investigationIdentifier", "alternative_titles",
    }
    full_fields = {
        "measurementTechnique",
        "crop_species", "crop_species_uri", "crop_pest", "crop_pest_uri",
        "sensorType", "funder", "distribution",
        "investigationPublications",
    }

    def score_group(fields: set) -> dict:
        present = [f for f in fields if f in fairagro_keys]
        missing = [f for f in fields if f not in fairagro_keys]
        pct = round(len(present) / len(fields) * 100, 1) if fields else 100.0
        return {"present": present, "missing": missing, "score": pct}

    basic = score_group(basic_fields)
    recommended = score_group(recommended_fields)
    full_extra = score_group(full_fields)

    if basic["score"] >= 90 and recommended["score"] >= 70 and full_extra["score"] >= 50:
        level = "full"
    elif basic["score"] >= 80 and recommended["score"] >= 40:
        level = "intermediate"
    else:
        level = "basic"

    return {
        "level": level,
        "source_format": source_format,
        "breakdown": {
            "required": basic,
            "recommended": recommended,
            "full": full_extra,
        },
        "overall_score": round(
            (basic["score"] * 0.5 + recommended["score"] * 0.3 + full_extra["score"] * 0.2),
            1,
        ),
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

    if ext == ".xml":
        snippet = content[:2000].lower()
        if b"oai_dc:dc" in snippet or b"oai_dc" in snippet and b"dc:title" in snippet:
            return "oai_dc"

    if ext == ".json":
        try:
            data = json.loads(content)
            if isinstance(data, list):
                data = data[0] if data else {}
            ctx = data.get("@context")
            if isinstance(ctx, str) and "schema.org" in ctx:
                # Check if it's already an ARC format by looking for RO-Crate context
                if "ro-crate" in ctx.lower():
                    return "ro_crate"
                # For plain Schema.org, we can check for specific fields
                if "@type" in data and data["@type"] == "Dataset":
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
