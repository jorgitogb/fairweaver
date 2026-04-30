"""
FAIRweaver format plugin: RO-Crate (ARC metadata format)
Parses ARC RO-Crate JSON-LD to flat dict for mapping engine.
"""

import json
from typing import Any, Dict, List


FORMAT_ID = "ro_crate"
LABEL = "RO-Crate"
EXTENSIONS = [".json"]  # ro-crate-metadata.json


def load(content: bytes) -> dict:
    """Parse RO-Crate JSON-LD into a flat dict with entity references."""
    data = json.loads(content)
    
    # Extract @graph array (RO-Crate structure)
    graph = data.get("@graph", [])
    
    # Build entity index by @id for reference resolution
    entities = {e.get("@id"): e for e in graph if e.get("@id")}
    
    # Find root entity (Investigation or first Dataset)
    root = _find_root(graph)
    
    if not root:
        return {}
    
    # Flatten the root with inline references resolved
    flat = _flatten_entity(root, entities)
    
    return flat


def write(json_ld: dict) -> bytes:
    """Convert FAIRagro JSON back to RO-Crate JSON-LD (stub - Phase 1)."""
    # Reverse conversion not implemented in Phase 1
    raise NotImplementedError("Reverse conversion not yet implemented")


def _find_root(graph: list) -> dict | None:
    """Find the root entity (Investigation > Study > first Dataset)."""
    for e in graph:
        atype = e.get("@type", [])
        if isinstance(atype, str):
            atype = [atype]
        if "Investigation" in atype or "Dataset" in atype:
            return e
    return graph[0] if graph else None


def _flatten_entity(entity: dict, entities: dict) -> dict:
    """Flatten entity with resolved references."""
    result = {}
    
    for key, value in entity.items():
        if key.startswith("@"):
            continue
        
        if isinstance(value, dict):
            # Resolve reference if it has @id
            if "@id" in value:
                ref_id = value["@id"]
                resolved = entities.get(ref_id, value)
                result[key] = _flatten_entity(resolved, entities)
            else:
                result[key] = _flatten_entity(value, entities)
        elif isinstance(value, list):
            result[key] = [_flatten_entity(v, entities) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    
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