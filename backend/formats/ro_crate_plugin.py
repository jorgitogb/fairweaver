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
    
    Args:
        content: ARC RO-Crate JSON content
        validate_fairagro: Whether to validate against FAIRagro template (default: True)
    
    Returns:
        dict: Extracted fields with optional validation info
    """
    data = json.loads(content)
    graph = data.get("@graph", [])
    if not graph:
        return {}

    entities = {e.get("@id"): e for e in graph if e.get("@id")}
    result: dict[str, Any] = {}

    # ── Locate root entities by additionalType ────────────────────────────
    investigation = _find_entity_by_type(graph, "Investigation")
    studies = _find_all_by_type(graph, "Study")
    assays = _find_all_by_type(graph, "Assay")

    # ── Citation block: from Investigation ────────────────────────────────
    if investigation:
        result["name"] = investigation.get("name", "")
        result["description"] = investigation.get("description", "")
        result["creator"] = _resolve_ref(investigation.get("creator"), entities)
        result["identifier"] = investigation.get("identifier", "")
        result["@id"] = investigation.get("@id", "")
        result["license"] = investigation.get("license", "")
        result["datePublished"] = investigation.get("datePublished", "")

    # ── Alternative titles: from Study and Assay names ───────────────────
    alt_titles = []
    for s in studies:
        name = s.get("name")
        if name:
            alt_titles.append(name)
    for a in assays:
        name = a.get("name")
        if name:
            alt_titles.append(name)
    if alt_titles:
        result["alternative_titles"] = alt_titles

    # ── Crop block: Study → about → LabProcess → Sample → Organism ──────
    crop_species = []
    crop_species_uris = []
    crop_pests = []
    crop_pest_uris = []

    for study in studies:
        about_list = _as_list(study.get("about"))
        for lab_process in about_list:
            if not _has_type(lab_process, "LabProcess"):
                lab_process = _resolve_ref(lab_process, entities)
            if not _has_type(lab_process, "LabProcess"):
                continue

            for sample in _as_list(lab_process.get("object")):
                sample = _resolve_ref(sample, entities)
                if not _has_type(sample, "Sample"):
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

    if crop_species:
        result["crop_species"] = crop_species[0]  # first crop
    if crop_species_uris:
        result["crop_species_uri"] = crop_species_uris[0]
    if crop_pests:
        result["crop_pest"] = crop_pests[0]
    if crop_pest_uris:
        result["crop_pest_uri"] = crop_pest_uris[0]

    # ── Sensor block: Assay → LabProcess → object + measurementMethod ────
    sensor_types = []
    sensor_platform_types = []
    drone_manufacturers = []
    drone_models = []

    for assay in assays:
        technique = _resolve_ref(assay.get("measurementTechnique"), entities)
        if technique:
            sensor_types.append(_string_value(technique) or "")

        method = _resolve_ref(assay.get("measurementMethod"), entities)
        if method:
            sensor_platform_types.append(_string_value(method) or "")

        # Walk about → LabProcess → additionalProperty for drone info
        for lab_process in _as_list(assay.get("about")):
            lab_process = _resolve_ref(lab_process, entities)
            if not _has_type(lab_process, "LabProcess"):
                continue

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

    # FAIRagro template validation
    if validate_fairagro:
        try:
            from arc_templates.fairagro_validator import FairagroArcValidator
            validator = FairagroArcValidator()
            validation = validator.validate(data)
            if not validation["valid"]:
                logger.warning(f"FAIRagro ARC validation failed: {validation['errors']}")
                # Add validation info to result for frontend feedback
                result["_validation"] = validation
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
    ro_crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": []
    }

    # Add RO-Crate metadata descriptor
    ro_crate["@graph"].append({
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        "about": {"@id": "ro-crate-metadata.json"}
    })

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
            "name": json_ld["alternative_titles"][0] if isinstance(json_ld["alternative_titles"], list) else json_ld["alternative_titles"],
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
        investigation["about"].append({
            "@id": "#crop_data",
            "@type": "PropertyValue",
            "name": "Organism",
            "value": json_ld["crop_species"]
        })

    if "measurementTechnique" in json_ld:
        if "about" not in investigation:
            investigation["about"] = []
        investigation["about"].append({
            "@id": "#sensor_data",
            "@type": "PropertyValue",
            "name": "Measurement Technique",
            "value": json_ld["measurementTechnique"]
        })

    return json.dumps(ro_crate, indent=2).encode('utf-8')


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
                "affiliation": creator_data.get("affiliation", {})
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
                studies.append({
                    "name": item.get("name", ""),
                    "description": item.get("description", "")
                })
        return studies

    return None
