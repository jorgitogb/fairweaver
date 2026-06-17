"""
FAIRweaver format plugin: RO-Crate (ARC metadata format)
Parses ARC RO-Crate JSON-LD into a flat dict for the mapping engine.
Implements the ARC-to-FAIRagro entity traversal logic described in the
FAIRagro Search Hub specification.
"""

import json
from typing import Any
import logging

logger = logging.getLogger(__name__)


FORMAT_ID = "ro_crate"
LABEL = "RO-Crate"
EXTENSIONS = [".json"]  # ro-crate-metadata.json


def load(content: bytes, validate_fairagro: bool = True) -> dict:
    """Parse ARC RO-Crate and extract fields for FAIRagro mapping.

    Traverses the @graph to find Investigation, Study, and Assay entities,
    following the FAIRagro Search Hub specification paths.

    Uses selective entity collection: only entities needed for extraction
    are kept in memory, reducing peak usage for large files.

    Args:
        content: ARC RO-Crate JSON content
        validate_fairagro: Whether to validate against FAIRagro template (default: True)

    Returns:
        dict: Extracted fields with optional validation info
    """
    data = json.loads(content)
    raw_graph = data.get("@graph", [])
    if not raw_graph:
        return {}

    # ── Streaming entity collection ────────────────────────────────────────
    # Single pass: collect only entity types needed for extraction.
    entities: dict[str, dict] = {}
    graph: list[dict] = []
    investigation = None
    studies: list[dict] = []
    assays: list[dict] = []

    for e in raw_graph:
        eid = e.get("@id")
        etype = _entity_type_name(e)

        if etype in _NDJSON_NEEDED_TYPES:
            if eid:
                entities[eid] = e
            graph.append(e)

            if etype == "Investigation" and not investigation:
                investigation = e
            elif etype == "Study":
                studies.append(e)
            elif etype == "Assay":
                assays.append(e)

    # Allow raw_graph to be garbage collected
    del raw_graph

    # ── Shared extraction logic ────────────────────────────────────────────
    return _extract_fields(
        graph=graph,
        entities=entities,
        investigation=investigation,
        studies=studies,
        assays=assays,
        validate_fairagro=validate_fairagro,
    )


# ── Streaming / large-file support ───────────────────────────────────────────


# Entity types needed for MIAPPE extraction (used by both load() and load_ndjson())
_NDJSON_NEEDED_TYPES = frozenset(
    {
        "Investigation",
        "Study",
        "Assay",
        "Source",
        "LabProcess",
        "Sample",
        "Dataset",
        "PropertyValue",
        "CharacteristicValue",
        "ParameterValue",
        "Person",
        "Organization",
        "DefinedTerm",
        "LabProtocol",
        "ScholarlyArticle",
        "CreativeWork",
    }
)


def convert_to_ndjson(content: bytes) -> bytes:
    """Convert a standard RO-Crate JSON to newline-delimited JSON (ndjson).

    Each line is one entity from the @graph array. The first line contains
    the RO-Crate header (@context + metadata). This format enables streaming
    parsing without loading the entire graph into memory.

    Args:
        content: Standard RO-Crate JSON bytes

    Returns:
        bytes: ndjson content (header line + one entity per line)
    """
    data = json.loads(content)
    graph = data.get("@graph", [])

    lines: list[str] = []
    # Header line: RO-Crate context + metadata (everything except @graph)
    header = {k: v for k, v in data.items() if k != "@graph"}
    lines.append(json.dumps(header, ensure_ascii=False))

    # One entity per line
    for entity in graph:
        lines.append(json.dumps(entity, ensure_ascii=False))

    return "\n".join(lines).encode("utf-8")


def load_ndjson(content: bytes, validate_fairagro: bool = True) -> dict:
    """Parse RO-Crate ndjson content with streaming entity collection.

    Each line is parsed independently, keeping only entities needed for
    extraction. Memory usage is proportional to the number of needed entities,
    not the total graph size.

    For a 250 MB file with 500K entities, this uses ~150 MB vs ~1.2 GB
    for the standard JSON loader.

    Args:
        content: ndjson bytes (header line + one entity per line)
        validate_fairagro: Whether to validate against FAIRagro template

    Returns:
        dict: Extracted fields
    """
    text = content.decode("utf-8", errors="replace")
    lines = text.split("\n")

    # First line is the header
    if not lines:
        return {}

    # Stream entities: collect only needed types
    entities: dict[str, dict] = {}
    graph: list[dict] = []
    investigation = None
    studies: list[dict] = []
    assays: list[dict] = []

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue

        eid = e.get("@id")
        etype = _entity_type_name(e)

        if etype in _NDJSON_NEEDED_TYPES:
            if eid:
                entities[eid] = e
            graph.append(e)

            if etype == "Investigation" and not investigation:
                investigation = e
            elif etype == "Study":
                studies.append(e)
            elif etype == "Assay":
                assays.append(e)

    if not graph:
        return {}

    # Delegate to the shared extraction logic
    return _extract_fields(
        graph=graph,
        entities=entities,
        investigation=investigation,
        studies=studies,
        assays=assays,
        validate_fairagro=validate_fairagro,
    )


def load_ndjson_file(filepath: str, validate_fairagro: bool = True) -> dict:
    """Stream-parse an ndjson RO-Crate file without loading it all into memory.

    Reads the file line by line, parsing each entity independently.
    Peak memory is proportional to needed entities, not file size.

    Use convert_to_ndjson() first to convert a standard JSON file to ndjson,
    then call this function for memory-efficient loading.

    Args:
        filepath: Path to ndjson file
        validate_fairagro: Whether to validate against FAIRagro template

    Returns:
        dict: Extracted fields
    """
    entities: dict[str, dict] = {}
    graph: list[dict] = []
    investigation = None
    studies: list[dict] = []
    assays: list[dict] = []

    with open(filepath, "r", encoding="utf-8") as f:
        # First line is the header
        header_line = f.readline()
        if not header_line.strip():
            return {}

        # Stream entities line by line
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue

            eid = e.get("@id")
            etype = _entity_type_name(e)

            if etype in _NDJSON_NEEDED_TYPES:
                if eid:
                    entities[eid] = e
                graph.append(e)

                if etype == "Investigation" and not investigation:
                    investigation = e
                elif etype == "Study":
                    studies.append(e)
                elif etype == "Assay":
                    assays.append(e)

    if not graph:
        return {}

    return _extract_fields(
        graph=graph,
        entities=entities,
        investigation=investigation,
        studies=studies,
        assays=assays,
        validate_fairagro=validate_fairagro,
    )


def _extract_fields(
    graph: list[dict],
    entities: dict[str, dict],
    investigation: dict | None,
    studies: list[dict],
    assays: list[dict],
    validate_fairagro: bool = True,
) -> dict:
    """Shared extraction logic used by both load() and load_ndjson().

    Separates field extraction from graph parsing so the same logic
    works for both standard JSON (full graph) and ndjson (streamed graph).
    """
    result: dict[str, Any] = {}

    # ── Citation block: from Investigation ────────────────────────────────
    if investigation:
        result["name"] = investigation.get("name", "")
        result["description"] = investigation.get("description", "")
        result["creator"] = _resolve_ref(investigation.get("creator"), entities)
        result["identifier"] = investigation.get("identifier", "")
        result["@id"] = investigation.get("@id", "")
        result["license"] = investigation.get("license", "")
        result["datePublished"] = investigation.get("datePublished", "")
        result["keywords"] = investigation.get("keywords", [])

    # ── Alternative titles: from Study and Assay names ───────────────────
    alt_titles: list[str] = []
    seen_titles: set[str] = set()
    for s in studies:
        name = s.get("name")
        if name and name not in seen_titles:
            alt_titles.append(name)
            seen_titles.add(name)
    for a in assays:
        name = a.get("name")
        if name and name not in seen_titles:
            alt_titles.append(name)
            seen_titles.add(name)
    if alt_titles:
        result["alternative_titles"] = alt_titles

    # ── Crop block: Study → about → LabProcess → Sample → Organism ──────
    crop_species = []
    crop_species_uris = []
    crop_pests = []
    crop_pest_uris = []
    crop_infection_labels = []

    for study in studies:
        about_list = _as_list(study.get("about"))
        for lab_process in about_list:
            if not _has_type(lab_process, "LabProcess"):
                lab_process = _resolve_ref(lab_process, entities)
            if not _has_type(lab_process, "LabProcess"):
                continue

            for sample in _as_list(lab_process.get("object")):
                sample = _resolve_ref(sample, entities)
                if not _has_type(sample, "Sample") and not _has_type(sample, "Material"):
                    continue

                for prop in _as_list(sample.get("additionalProperty")):
                    prop = _resolve_ref(prop, entities)
                    name_val = _string_value(prop.get("name"))

                    if name_val == "Organism":
                        org = _string_value(prop.get("value"))
                        if org:
                            crop_species.append(org)
                            uri = _string_value(prop.get("valueRef"))
                            if uri:
                                crop_species_uris.append(uri)

                    elif name_val == "Infection Taxon":
                        pest = _string_value(prop.get("value"))
                        if pest:
                            crop_pests.append(pest)
                            uri = _string_value(prop.get("valueRef"))
                            if uri:
                                crop_pest_uris.append(uri)

                    elif name_val == "Infection Label":
                        label = _string_value(prop.get("value"))
                        if label:
                            crop_infection_labels.append(label)

    # Fallback: extract crop/sensor directly from Study entities
    if not crop_species:
        for study in studies:
            cs = _string_value(study.get("crop_species"))
            if cs:
                crop_species.append(cs)
            cs_uri = _string_value(study.get("crop_species_uri"))
            if cs_uri:
                crop_species_uris.append(cs_uri)
            cp = _string_value(study.get("crop_pest"))
            if cp:
                crop_pests.append(cp)
            cp_uri = _string_value(study.get("crop_pest_uri"))
            if cp_uri:
                crop_pest_uris.append(cp_uri)

    if crop_species:
        result["crop_species"] = crop_species[0]
    if crop_species_uris:
        result["crop_species_uri"] = crop_species_uris[0]
    if crop_pests:
        result["crop_pest"] = crop_pests[0]
    if crop_pest_uris:
        result["crop_pest_uri"] = crop_pest_uris[0]
    if crop_infection_labels:
        result["crop_infection_label"] = crop_infection_labels[0]

    # ── Sensor block: Assay → LabProcess → object + measurementMethod ────
    sensor_types = []
    sensor_platform_types = []
    drone_manufacturers = []
    drone_models = []
    drone_lps: list[dict] = []

    for assay in assays:
        technique = _resolve_ref(assay.get("measurementTechnique"), entities)
        if technique:
            sensor_types.append(_string_value(technique) or "")

        method = _resolve_ref(assay.get("measurementMethod"), entities)
        if method:
            sensor_platform_types.append(_string_value(method) or "")

        for lab_process in _as_list(assay.get("about")):
            lab_process = _resolve_ref(lab_process, entities)
            if not _has_type(lab_process, "LabProcess"):
                continue

            drone_lps.append(lab_process)

            for prop in _as_list(lab_process.get("additionalProperty")):
                prop = _resolve_ref(prop, entities)
                prop_name = _string_value(prop.get("name"))
                prop_val = _string_value(prop.get("value"))

                if prop_name == "Drone Manufacturer" and prop_val:
                    drone_manufacturers.append(prop_val)
                elif prop_name == "Drone Model" and prop_val:
                    drone_models.append(prop_val)

    if sensor_types:
        result["measurementTechnique"] = sensor_types[0]
    if sensor_platform_types:
        result["measurementMethod"] = sensor_platform_types[0]
    if drone_manufacturers:
        result["drone_manufacturer"] = drone_manufacturers[0]
    if drone_models:
        result["drone_model"] = drone_models[0]

    # Drone location params (Longitude/Latitude/Date and Time)
    try:
        drone_loc = _extract_drone_location_params(entities, drone_lps)
        result.setdefault("drone_longitude", drone_loc.get("drone_longitude"))
        result.setdefault("drone_latitude", drone_loc.get("drone_latitude"))
        result.setdefault("drone_datetime", drone_loc.get("drone_datetime"))
    except Exception:
        logger.debug("Drone location extraction failed")

    # ── MIAPPE extraction (new blocks, never overwrite existing) ──────────
    try:
        sources = _find_sources(graph, entities)
    except Exception:
        sources = []
        logger.debug("_find_sources failed, skipping MIAPPE extraction")

    # Taxonomy
    try:
        tax = _extract_taxonomy(entities, sources)
        result.setdefault("taxon_genus", tax.get("taxon_genus"))
        result.setdefault("taxon_species", tax.get("taxon_species"))
        result.setdefault("taxon_infraspecific_name", tax.get("taxon_infraspecific_name"))
    except Exception:
        logger.debug("Taxonomy extraction failed")

    # Crop characteristics (grain weight, ICC code, variety)
    try:
        crop_chars = _extract_crop_characteristics(entities, sources)
        result.setdefault("crop_grain_weight", crop_chars.get("crop_grain_weight"))
        result.setdefault("crop_icc_code", crop_chars.get("crop_icc_code"))
        result.setdefault("crop_variety", crop_chars.get("crop_variety"))
    except Exception:
        logger.debug("Crop characteristics extraction failed")

    # Geolocation
    try:
        geo = _extract_geolocation(entities, sources)
        result.setdefault("geo_latitude", geo.get("geo_latitude"))
        result.setdefault("geo_longitude", geo.get("geo_longitude"))
        result.setdefault("geo_altitude", geo.get("geo_altitude"))
    except Exception:
        logger.debug("Geolocation extraction failed")

    # Germplasm
    try:
        germ = _extract_germplasm(entities, sources)
        result.setdefault("germplasm_source_id", germ.get("germplasm_source_id"))
        result.setdefault("germplasm_source_doi", germ.get("germplasm_source_doi"))
    except Exception:
        logger.debug("Germplasm extraction failed")

    # Origin Country
    try:
        result.setdefault("origin_country", _extract_origin_country(entities, sources))
    except Exception:
        logger.debug("Origin Country extraction failed")

    # Geographic coverage (country/state/county)
    try:
        geo_cov = _extract_geographic_coverage(entities, sources)
        result.setdefault("geo_country", geo_cov.get("geo_country"))
        result.setdefault("geo_state", geo_cov.get("geo_state"))
        result.setdefault("geo_county", geo_cov.get("geo_county"))
    except Exception:
        logger.debug("Geographic coverage extraction failed")

    # Parameter values
    try:
        pv = _extract_parameter_values(entities, graph)
        if pv:
            result["parameter_values"] = pv
    except Exception:
        logger.debug("Parameter value extraction failed")

    # Soil depths (distinct top/bottom pairs from SoilSampling processes)
    try:
        soil = _extract_soil_depths(entities, graph)
        if soil:
            result["soil_depths"] = soil
    except Exception:
        logger.debug("Soil depth extraction failed")

    # Agricultural process types (distinct protocol names)
    try:
        proc_types = _extract_process_types(entities, graph)
        if proc_types:
            result["agricultural_processes"] = proc_types
    except Exception:
        logger.debug("Process type extraction failed")

    # License ref resolution (only if current is a dict ref)
    try:
        if isinstance(result.get("license"), dict):
            resolved = _resolve_license(investigation, entities)
            if resolved:
                result["license"] = resolved
    except Exception:
        logger.debug("License resolution failed")

    # Investigation contacts/publications/citation
    try:
        meta = _extract_investigation_meta(investigation, entities)
        for k, v in meta.items():
            result.setdefault(k, v)
    except Exception:
        logger.debug("Investigation meta extraction failed")

    # Default subject for FAIRagro Search Hub
    result.setdefault("subject", "Agricultural Sciences")

    # Event ID crop fallback (only if no crop found yet)
    try:
        if not result.get("crop_species"):
            fallback = _extract_event_id_crops(entities, graph, result.get("crop_species"))
            fallback_crop = fallback.get("crop_species")
            if fallback_crop:
                result.setdefault("crop_species", fallback_crop)
    except Exception:
        logger.debug("Event ID crop fallback failed")

    # FAIRagro template validation
    if validate_fairagro:
        try:
            from fairagro_validator import validate_arc_fairagro

            validation = validate_arc_fairagro(result)
            result["fairagro_valid"] = validation.get("valid", False)
            result["fairagro_errors"] = validation.get("errors", [])
            result["fairagro_warnings"] = validation.get("warnings", [])
        except ImportError:
            logger.debug("FAIRagro validator not available, skipping validation")
        except Exception as e:
            logger.error(f"FAIRagro validation error: {e}")

    return result


def write(json_ld: dict) -> bytes:
    """Convert FAIRagro JSON back to ARC RO-Crate JSON-LD format.

    Args:
        json_ld: FAIRagro JSON data (can be flat or nested structure)

    Returns:
        bytes: ARC RO-Crate JSON-LD content
    """

    # Create basic RO-Crate structure
    ro_crate = {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": []}

    # Add RO-Crate metadata descriptor
    ro_crate["@graph"].append(
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "ro-crate-metadata.json"},
        }
    )

    # Handle both flat and nested structures
    if "@context" in json_ld:
        # Already in JSON-LD format, add ARC entity metadata
        investigation = {k: v for k, v in json_ld.items() if k != "@context"}
        if "@id" not in investigation:
            investigation["@id"] = "#investigation"
        if "additionalType" not in investigation:
            investigation["additionalType"] = "Investigation"
    else:
        # Create Investigation entity from flat structure
        investigation = {
            "@id": "#investigation",
            "@type": "Dataset",
            "additionalType": "Investigation",
            "name": json_ld.get("name", "Untitled Investigation"),
            "description": json_ld.get("description", ""),
            "identifier": json_ld.get("identifier", ""),
            "license": json_ld.get("license", ""),
            "datePublished": json_ld.get("datePublished", ""),
        }

    # Add creator if present
    if "creator" in json_ld:
        investigation["creator"] = json_ld["creator"]

    # Add keywords if present
    if "keywords" in json_ld:
        investigation["keywords"] = json_ld["keywords"]

    ro_crate["@graph"].append(investigation)

    # Create Study entity if study data present
    if "alternative_titles" in json_ld:
        study = {
            "@id": "#study",
            "@type": "Dataset",
            "additionalType": "Study",
            "name": json_ld["alternative_titles"][0]
            if isinstance(json_ld["alternative_titles"], list)
            else json_ld["alternative_titles"],
            "description": json_ld.get("description", ""),
        }
        ro_crate["@graph"].append(study)

    # Create Assay entity if assay data present
    if "measurementTechnique" in json_ld or "measurementMethod" in json_ld:
        assay = {
            "@id": "#assay",
            "@type": "Dataset",
            "additionalType": "Assay",
            "name": "Assay 1",
            "description": "Automated assay from Schema.org conversion",
        }

        if "measurementTechnique" in json_ld:
            assay["measurementTechnique"] = json_ld["measurementTechnique"]

        if "measurementMethod" in json_ld:
            assay["measurementMethod"] = json_ld["measurementMethod"]

        ro_crate["@graph"].append(assay)

    # Add crop/sensor data as additional properties if present
    if "crop_species" in json_ld:
        if "about" not in investigation:
            investigation["about"] = []
        investigation["about"].append(
            {
                "@id": "#crop_data",
                "@type": "PropertyValue",
                "name": "Organism",
                "value": json_ld["crop_species"],
            }
        )

    if "measurementTechnique" in json_ld:
        if "about" not in investigation:
            investigation["about"] = []
        investigation["about"].append(
            {
                "@id": "#sensor_data",
                "@type": "PropertyValue",
                "name": "Measurement Technique",
                "value": json_ld["measurementTechnique"],
            }
        )

    return json.dumps(ro_crate, indent=2).encode("utf-8")


# ── Graph helpers ──────────────────────────────────────────────────────────────


def _has_type(entity: Any, type_name: str) -> bool:
    if not isinstance(entity, dict):
        return False
    atype = entity.get("@type", [])
    if isinstance(atype, str):
        atype = [atype]
    if type_name in atype:
        return True
    # Also check additionalType (ARC uses @type=Dataset + additionalType=Investigation)
    atype2 = entity.get("additionalType", [])
    if isinstance(atype2, str):
        atype2 = [atype2]
    return type_name in atype2


def _entity_type_name(entity: dict) -> str | None:
    """Extract the primary type name from an entity's @type or additionalType.

    Returns additionalType if @type is a generic container (e.g. 'Dataset')
    that has a more specific additionalType. This matches _has_type() behavior.
    """
    if not isinstance(entity, dict):
        return None

    atype = entity.get("@type", [])
    if isinstance(atype, str):
        atype = [atype]

    atype2 = entity.get("additionalType", [])
    if isinstance(atype2, str):
        atype2 = [atype2]

    # Prefer additionalType when @type is generic (Dataset, CreativeWork, etc.)
    if atype2:
        return atype2[0] if isinstance(atype2[0], str) else None
    if atype:
        return atype[0] if isinstance(atype[0], str) else None
    return None


def _find_entity_by_type(graph: list, type_name: str) -> dict | None:
    for e in graph:
        if _has_type(e, type_name):
            return e
    return None


def _find_all_by_type(graph: list, type_name: str) -> list:
    return [e for e in graph if _has_type(e, type_name)]


def _resolve_ref(value: Any, entities: dict) -> Any:
    if isinstance(value, list):
        return [_resolve_ref(item, entities) for item in value]
    if isinstance(value, dict) and "@id" in value:
        ref_id = value["@id"]
        resolved = entities.get(ref_id)
        if resolved:
            merged = dict(resolved)
            merged.update((k, v) for k, v in value.items() if k != "@id")
            return merged
    return value


def _as_list(value: Any) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("name", value.get("@id", ""))
    if isinstance(value, list):
        for v in value:
            s = _string_value(v)
            if s:
                return s
        return ""
    return str(value) if value else ""


# ── MIAPPE extraction helpers ──────────────────────────────────────────────────

# MIAPPE propertyIDs for taxonomy
_MIAPPE_GENUS = "http://purl.obolibrary.org/obo/MIAPPE_0042"
_MIAPPE_SPECIES = "http://purl.obolibrary.org/obo/MIAPPE_0043"
_MIAPPE_INFRASPECIFIC = "http://purl.obolibrary.org/obo/MIAPPE_0044"

# MIAPPE propertyIDs for biological material geo
_MIAPPE_BIO_LAT = "http://purl.obolibrary.org/obo/MIAPPE_0045"
_MIAPPE_BIO_LNG = "http://purl.obolibrary.org/obo/MIAPPE_0046"
_MIAPPE_BIO_ALT = "http://purl.obolibrary.org/obo/MIAPPE_0047"

# MIAPPE propertyIDs for material source geo
_MIAPPE_SRC_LAT = "http://purl.obolibrary.org/obo/MIAPPE_0052"
_MIAPPE_SRC_LNG = "http://purl.obolibrary.org/obo/MIAPPE_0053"
_MIAPPE_SRC_ALT = "http://purl.obolibrary.org/obo/MIAPPE_0054"

# MIAPPE propertyIDs for germplasm
_MIAPPE_SRC_ID = "http://purl.obolibrary.org/obo/MIAPPE_0050"
_MIAPPE_SRC_DOI = "http://purl.obolibrary.org/obo/MIAPPE_0051"

# AGRO propertyIDs for field geo
_AGRO_FIELD_LAT = "http://purl.obolibrary.org/obo/AGRO_00000574"
_AGRO_FIELD_LNG = "http://purl.obolibrary.org/obo/AGRO_00000575"
_AGRO_FIELD_ALT = "http://purl.obolibrary.org/obo/AGRO_00000612"

# Name-based lookups
_NAME_ORIGIN_COUNTRY = "Origin Country"
_NAME_ORGANISM = "Organism"


def _find_sources(graph: list, entities: dict) -> list[dict]:
    """Find all Source entities via direct scan or from LabProcess.object."""
    sources = []
    seen: set[str] = set()

    for e in graph:
        if _has_type(e, "Source") and e.get("@id"):
            sources.append(e)
            seen.add(e["@id"])

    # Also collect from LabProcess.object
    for e in graph:
        if not _has_type(e, "LabProcess"):
            continue
        for obj in _as_list(e.get("object")):
            if isinstance(obj, dict) and obj.get("@id"):
                resolved = entities.get(obj["@id"])
                if resolved and _has_type(resolved, "Source") and obj["@id"] not in seen:
                    sources.append(resolved)
                    seen.add(obj["@id"])

    return sources


def _cv_value_by_property_id(sources: list[dict], entities: dict, property_id: str) -> str | None:
    """Get the first non-empty value from CharacteristicValue matching propertyID."""
    for source in sources:
        for prop in _as_list(source.get("additionalProperty")):
            prop = _resolve_ref(prop, entities)
            if not isinstance(prop, dict):
                continue
            pid = prop.get("propertyID", "")
            if pid == property_id:
                val = _string_value(prop.get("value"))
                if val:
                    return val
    return None


def _cv_value_by_name(sources: list[dict], entities: dict, name: str) -> str | None:
    """Get the first non-empty value from CharacteristicValue matching name."""
    for source in sources:
        for prop in _as_list(source.get("additionalProperty")):
            prop = _resolve_ref(prop, entities)
            if not isinstance(prop, dict):
                continue
            if prop.get("name") == name:
                val = _string_value(prop.get("value"))
                if val:
                    return val
    return None


def _extract_taxonomy(entities: dict, sources: list[dict]) -> dict[str, str | None]:
    """Extract Genus, Species, Infraspecific name from Source CharacteristicValues."""
    return {
        "taxon_genus": _cv_value_by_property_id(sources, entities, _MIAPPE_GENUS),
        "taxon_species": _cv_value_by_property_id(sources, entities, _MIAPPE_SPECIES),
        "taxon_infraspecific_name": _cv_value_by_property_id(
            sources, entities, _MIAPPE_INFRASPECIFIC
        ),
    }


def _extract_geolocation(entities: dict, sources: list[dict]) -> dict[str, str | None]:
    """Extract geolocation from Source CharacteristicValues.

    Priority: field geo (AGRO) first, fallback to biological material geo (MIAPPE).
    """
    lat = _cv_value_by_property_id(sources, entities, _AGRO_FIELD_LAT)
    lng = _cv_value_by_property_id(sources, entities, _AGRO_FIELD_LNG)
    alt = _cv_value_by_property_id(sources, entities, _AGRO_FIELD_ALT)

    if not lat:
        lat = _cv_value_by_property_id(sources, entities, _MIAPPE_BIO_LAT)
    if not lng:
        lng = _cv_value_by_property_id(sources, entities, _MIAPPE_BIO_LNG)
    if not alt:
        alt = _cv_value_by_property_id(sources, entities, _MIAPPE_BIO_ALT)

    # Fallback to material source geo
    if not lat:
        lat = _cv_value_by_property_id(sources, entities, _MIAPPE_SRC_LAT)
    if not lng:
        lng = _cv_value_by_property_id(sources, entities, _MIAPPE_SRC_LNG)
    if not alt:
        alt = _cv_value_by_property_id(sources, entities, _MIAPPE_SRC_ALT)

    return {"geo_latitude": lat, "geo_longitude": lng, "geo_altitude": alt}


def _extract_germplasm(entities: dict, sources: list[dict]) -> dict[str, str | None]:
    """Extract Material source ID and DOI from Source CharacteristicValues."""
    return {
        "germplasm_source_id": _cv_value_by_property_id(sources, entities, _MIAPPE_SRC_ID),
        "germplasm_source_doi": _cv_value_by_property_id(sources, entities, _MIAPPE_SRC_DOI),
    }


def _extract_origin_country(entities: dict, sources: list[dict]) -> str | None:
    """Extract Origin Country from Source CharacteristicValues."""
    return _cv_value_by_name(sources, entities, _NAME_ORIGIN_COUNTRY)


# AGRO/BCO propertyIDs for geographic coverage
_BCO_COUNTRY = "http://purl.obolibrary.org/obo/bco_country"
_BCO_STATE = "http://purl.obolibrary.org/obo/bco_stateProvince"
_BCO_COUNTY = "http://purl.obolibrary.org/obo/bco_county"


def _extract_geographic_coverage(entities: dict, sources: list[dict]) -> dict[str, str | None]:
    """Extract country, state, county from Source CharacteristicValues."""
    return {
        "geo_country": _cv_value_by_property_id(sources, entities, _BCO_COUNTRY),
        "geo_state": _cv_value_by_property_id(sources, entities, _BCO_STATE),
        "geo_county": _cv_value_by_property_id(sources, entities, _BCO_COUNTY),
    }


def _extract_parameter_values(entities: dict, graph: list) -> dict[str, list[str]]:
    """Extract ParameterValue entries from LabProcess entities."""
    params: dict[str, list[str]] = {}
    for e in graph:
        if not _has_type(e, "LabProcess"):
            continue
        for pv_ref in _as_list(e.get("parameterValue")):
            pv = _resolve_ref(pv_ref, entities)
            if not isinstance(pv, dict):
                continue
            name = _string_value(pv.get("name"))
            val = _string_value(pv.get("value"))
            if name and val:
                params.setdefault(name, []).append(val)
    return params


# Name-based lookups for drone location params
_NAME_DRONE_LONGITUDE = "Longitude"
_NAME_DRONE_LATITUDE = "Latitude"
_NAME_DRONE_DATETIME = "Date and Time"


def _extract_drone_location_params(
    entities: dict, lab_processes: list[dict]
) -> dict[str, str | None]:
    """Extract Longitude, Latitude, Date and Time from LabProcess parameterValues."""
    lng: str | None = None
    lat: str | None = None
    dt: str | None = None

    for lp in lab_processes:
        for pv_ref in _as_list(lp.get("parameterValue")):
            pv = _resolve_ref(pv_ref, entities)
            if not isinstance(pv, dict):
                continue
            name = _string_value(pv.get("name"))
            val = _string_value(pv.get("value"))
            if not val:
                continue

            if name == _NAME_DRONE_LONGITUDE and lng is None:
                lng = val
            elif name == _NAME_DRONE_LATITUDE and lat is None:
                lat = val
            elif name == _NAME_DRONE_DATETIME and dt is None:
                dt = val

    return {"drone_longitude": lng, "drone_latitude": lat, "drone_datetime": dt}


# Soil depth propertyIDs
_ENVO_SOIL_TOP_DEPTH = "https://bioregistry.io/ENVO:06105225"
_ENVO_SOIL_BOTTOM_DEPTH = "https://bioregistry.io/ENVO:06105226"
_SOIL_SAMPLING_PROTOCOL = "#Protocol_Events-SoilSampling"


def _extract_soil_depths(entities: dict, graph: list) -> list[dict[str, str]]:
    """Extract distinct soil top/bottom depth pairs from soil sampling LabProcesses.

    Scans LabProcess entities executing the SoilSampling protocol and collects
    distinct (top, bottom) depth combinations from their parameterValues.
    """
    pairs: set[tuple[str, str]] = set()

    for e in graph:
        if not _has_type(e, "LabProcess"):
            continue

        protocol = e.get("executesLabProtocol")
        if isinstance(protocol, dict):
            protocol_id = protocol.get("@id", "")
        elif isinstance(protocol, str):
            protocol_id = protocol
        else:
            continue

        if protocol_id != _SOIL_SAMPLING_PROTOCOL:
            continue

        top: str | None = None
        bottom: str | None = None

        for pv_ref in _as_list(e.get("parameterValue")):
            pv = _resolve_ref(pv_ref, entities)
            if not isinstance(pv, dict):
                continue
            pid = pv.get("propertyID", "")
            val = _string_value(pv.get("value"))
            if not val:
                continue

            if pid == _ENVO_SOIL_TOP_DEPTH:
                top = val
            elif pid == _ENVO_SOIL_BOTTOM_DEPTH:
                bottom = val

        if top is not None and bottom is not None:
            pairs.add((top, bottom))

    return [{"top": t, "bottom": b} for t, b in sorted(pairs)]


# Agricultural process protocol IDs
_PROCESS_PROTOCOLS = frozenset(
    {
        "#Protocol_Events-Tillage",
        "#Protocol_Events-Mulching",
        "#Protocol_Events-CropResidueManagement",
        "#Protocol_Events-Planting",
        "#Protocol_Events-InorganicFertilization",
        "#Protocol_Events-ChemicalApplications",
        "#Protocol_Events-Irrigation",
        "#Protocol_Events-Harvest",
        "#Protocol_Events-OrganicFertilization",
    }
)

_PROTOCOL_PREFIX = "#Protocol_Events-"


def _extract_process_types(entities: dict, graph: list) -> list[str]:
    """Extract distinct agricultural process type names from LabProcess entities.

    Scans LabProcess entities for executesLabProtocol references matching known
    agricultural process protocol IDs, and returns their display names sorted.
    """
    types: set[str] = set()

    for e in graph:
        if not _has_type(e, "LabProcess"):
            continue

        protocol = e.get("executesLabProtocol")
        if isinstance(protocol, dict):
            protocol_id = protocol.get("@id", "")
        elif isinstance(protocol, str):
            protocol_id = protocol
        else:
            continue

        if protocol_id in _PROCESS_PROTOCOLS and protocol_id.startswith(_PROTOCOL_PREFIX):
            name = protocol_id[len(_PROTOCOL_PREFIX) :]
            types.add(name)

    return sorted(types)


# Crop characteristic name-based lookups
_NAME_GRAIN_WEIGHT = "1000-grain dry weight"
_NAME_ICC_CODE = "ICC code"
_NAME_INFRASPECIFIC = "Infraspecific name"


def _extract_crop_characteristics(entities: dict, sources: list[dict]) -> dict[str, str | None]:
    """Extract grain weight, ICC code, and variety from Source CharacteristicValues."""
    return {
        "crop_grain_weight": _cv_value_by_name(sources, entities, _NAME_GRAIN_WEIGHT),
        "crop_icc_code": _cv_value_by_name(sources, entities, _NAME_ICC_CODE),
        "crop_variety": _cv_value_by_name(sources, entities, _NAME_INFRASPECIFIC),
    }


def _extract_event_id_crops(
    entities: dict, graph: list, current_crop: str | None
) -> dict[str, str | None]:
    """Fallback crop extraction when Organism not found on Source.

    Scans all Source entities for Organism/Genus/Species/Infraspecific via name.
    If still nothing, returns current crop (no override).
    """
    for e in graph:
        if not _has_type(e, "Source"):
            continue
        for prop in _as_list(e.get("additionalProperty")):
            prop = _resolve_ref(prop, entities)
            if not isinstance(prop, dict):
                continue
            if prop.get("name") == _NAME_ORGANISM:
                val = _string_value(prop.get("value"))
                if val and not current_crop:
                    return {"crop_species": val}
    return {}


def _resolve_license(investigation: dict | None, entities: dict) -> str | None:
    """Resolve license from @id reference (e.g. #LICENSE) to CreativeWork text."""
    if not investigation:
        return None
    lic = investigation.get("license")
    if isinstance(lic, dict) and "@id" in lic:
        resolved = entities.get(lic["@id"])
        if resolved and isinstance(resolved, dict):
            return _string_value(resolved.get("text")) or _string_value(resolved.get("name"))
    return None


def _extract_investigation_meta(investigation: dict | None, entities: dict) -> dict[str, Any]:
    """Extract investigationContacts and investigationPublications from Investigation."""
    result: dict[str, Any] = {}
    if not investigation:
        return result

    # investigationContacts
    contacts_raw = investigation.get("investigationContacts")
    if contacts_raw:
        contacts = []
        for ref in _as_list(contacts_raw):
            resolved = _resolve_ref(ref, entities)
            if isinstance(resolved, dict):
                name = _string_value(resolved.get("name"))
                email = _string_value(resolved.get("email"))
                aff = resolved.get("affiliation", {})
                aff_name = ""
                if isinstance(aff, dict):
                    aff_name = _string_value(aff.get("name"))
                elif isinstance(aff, str):
                    aff_name = aff
                if name:
                    contacts.append({"name": name, "email": email, "affiliation": aff_name})
        if contacts:
            result["investigation_contacts"] = contacts

    # investigationPublications
    pubs_raw = investigation.get("investigationPublications")
    if pubs_raw:
        pubs = []
        for ref in _as_list(pubs_raw):
            resolved = _resolve_ref(ref, entities)
            if isinstance(resolved, dict):
                title = _string_value(resolved.get("headline")) or _string_value(
                    resolved.get("name")
                )
                identifier = _resolve_ref(resolved.get("identifier"), entities)
                ident_str = (
                    _string_value(identifier)
                    if isinstance(identifier, dict)
                    else _string_value(identifier)
                )
                if title:
                    pubs.append({"title": title, "identifier": ident_str})
        if pubs:
            result["investigation_publications"] = pubs

    # citation (standalone reference)
    citation_raw = investigation.get("citation")
    if citation_raw:
        resolved = _resolve_ref(citation_raw, entities)
        if isinstance(resolved, dict):
            title = _string_value(resolved.get("headline")) or _string_value(resolved.get("name"))
            identifier = _resolve_ref(resolved.get("identifier"), entities)
            ident_str = (
                _string_value(identifier)
                if isinstance(identifier, dict)
                else _string_value(identifier)
            )
            if title:
                result["citation"] = {"title": title, "identifier": ident_str}

    return result


# ── Transforms (used by mapping engine) ────────────────────────────────────────


def parse_person(creator_data: Any) -> list[dict]:
    """Transform creator to FAIRagro author format."""
    if not creator_data:
        return []

    if isinstance(creator_data, dict):
        creator_data = [creator_data]

    authors = []
    for person in creator_data:
        if not isinstance(person, dict):
            continue

        # Extract name: prefer givenName + familyName, fallback to name
        given = person.get("givenName", "")
        family = person.get("familyName", "")
        name = f"{given} {family}".strip() or person.get("name", "")

        if not name:
            continue

        author = {"authorName": name}

        # Affiliation
        aff = person.get("affiliation", {})
        if isinstance(aff, dict):
            author["authorAffiliation"] = aff.get("name", "Unknown")
        elif isinstance(aff, str):
            author["authorAffiliation"] = aff

        # Identifier (ORCID)
        identifier = person.get("@id", "")
        if identifier and "orcid.org" in identifier:
            author["authorIdentifier"] = identifier
            author["authorIdentifierScheme"] = "ORCID"
        else:
            author["authorIdentifier"] = identifier or "Unknown"
            author["authorIdentifierScheme"] = "Other"

        authors.append(author)

    return authors


def wrap_description(description: Any) -> list[dict]:
    """Wrap description in FAIRagro dsDescription format."""
    if not description:
        return [{"dsDescriptionValue": "No description available"}]

    if isinstance(description, str):
        return [{"dsDescriptionValue": description}]
    if isinstance(description, list):
        return [{"dsDescriptionValue": d} for d in description if d]

    return [{"dsDescriptionValue": str(description)}]


def wrap_other_id(identifier: Any) -> list[dict]:
    """Wrap identifier in FAIRagro otherId format."""
    if not identifier:
        return [{"otherIdValue": "Unknown", "otherIdAgency": "Other"}]

    if isinstance(identifier, str):
        agency = "DOI" if "doi.org" in identifier else "Other"
        return [{"otherIdValue": identifier, "otherIdAgency": agency}]
    if isinstance(identifier, list):
        result = []
        for id_val in identifier:
            if isinstance(id_val, str):
                agency = "DOI" if "doi.org" in id_val else "Other"
                result.append({"otherIdValue": id_val, "otherIdAgency": agency})
        return result

    # Fallback
    return [{"otherIdValue": str(identifier), "otherIdAgency": "Other"}]


def extract_organism(additional_type: Any) -> list[dict]:
    """Extract crop/organism from Sample.additionalType field."""
    if not additional_type:
        return [{"cropSpecies": "Unknown"}]

    if isinstance(additional_type, str):
        return [{"cropSpecies": additional_type}]
    if isinstance(additional_type, list):
        return [{"cropSpecies": t} for t in additional_type if t]

    return [{"cropSpecies": str(additional_type)}]


def wrap_sensor_type(technique: Any) -> list[dict]:
    """Wrap measurement technique in sensor format."""
    if not technique:
        return [{"sensorSensorType": "Unknown"}]

    # Handle dict (e.g., {"name": "Drone"}) - extract the name value
    if isinstance(technique, dict):
        name = technique.get("name") or technique.get("@id") or str(technique)
        return [{"sensorSensorType": name}]

    if isinstance(technique, str):
        return [{"sensorSensorType": technique}]
    if isinstance(technique, list):
        result = []
        for t in technique:
            if isinstance(t, dict):
                result.append({"sensorSensorType": t.get("name") or t.get("@id") or str(t)})
            elif t:
                result.append({"sensorSensorType": t})
        return result

    return [{"sensorSensorType": str(technique)}]


def wrap_platform(method: Any) -> list[dict]:
    """Wrap measurement method as sensor platform."""
    if not method:
        return [{"sensorPlatform": "Unknown"}]

    # Handle dict (e.g., {"name": "digital camera", "termCode": "..."})
    if isinstance(method, dict):
        name = method.get("name") or method.get("@id") or str(method)
        return [{"sensorPlatform": name}]

    if isinstance(method, str):
        return [{"sensorPlatform": method}]
    if isinstance(method, list):
        result = []
        for m in method:
            if isinstance(m, dict):
                result.append({"sensorPlatform": m.get("name") or m.get("@id") or str(m)})
            elif m:
                result.append({"sensorPlatform": m})
        return result

    return [{"sensorPlatform": str(method)}]


# Alias for wrap_sensor
wrap_sensor = wrap_sensor_type


def parse_schema_org_person(creator_data: Any) -> Any:
    """Transform Schema.org creator to ARC format."""
    if not creator_data:
        return None

    if isinstance(creator_data, dict):
        # Handle Schema.org Person format
        if creator_data.get("@type") == "Person":
            return {
                "@type": "Person",
                "name": creator_data.get("name", ""),
                "email": creator_data.get("email", ""),
                "affiliation": creator_data.get("affiliation", {}),
            }
        return creator_data

    if isinstance(creator_data, str):
        return {"name": creator_data}

    if isinstance(creator_data, list):
        return [parse_schema_org_person(item) for item in creator_data]

    return creator_data


def extract_study_entities(has_part_data: Any) -> Any:
    """Extract study entities from Schema.org hasPart."""
    if not has_part_data:
        return None

    if isinstance(has_part_data, list):
        studies = []
        for item in has_part_data:
            if isinstance(item, dict) and item.get("@type") == "Dataset":
                studies.append(
                    {"name": item.get("name", ""), "description": item.get("description", "")}
                )
        return studies

    return None
