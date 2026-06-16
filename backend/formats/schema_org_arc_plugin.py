import json
import logging
from typing import Any

from arctrl import ARC, Person

logger = logging.getLogger(__name__)

FORMAT_ID = "schema_org_arc"
LABEL = "Schema.org Dataset (ARC)"
EXTENSIONS = [".json"]


def load(content: bytes) -> dict[str, Any]:
    """Parse Schema.org Dataset JSON bytes to flat dict for the mapping engine."""
    data = json.loads(content)

    # Handle array of datasets
    if isinstance(data, list):
        # For batch processing, we'll process the first dataset
        # In practice, this would be handled by batch processing logic
        data = data[0] if data else {}

    # Extract key fields from Schema.org Dataset
    extracted = {}

    # Basic metadata
    extracted["@context"] = data.get("@context", "")
    extracted["@id"] = data.get("@id", "")
    extracted["@type"] = data.get("@type", "")

    # Main properties
    extracted["name"] = data.get("name", "")
    extracted["description"] = data.get("description", "")
    extracted["keywords"] = data.get("keywords", [])
    extracted["datePublished"] = data.get("datePublished", "")
    extracted["inLanguage"] = data.get("inLanguage", "")
    extracted["license"] = data.get("license", "")

    # Authors, creators, contributors
    authors = data.get("author", [])
    creators = data.get("creator", [])
    contributors = data.get("contributor", [])

    # Combine all persons
    all_persons = []
    for person_list in [authors, creators, contributors]:
        if isinstance(person_list, list):
            all_persons.extend(person_list)

    # Extract basic person information
    extracted["persons"] = all_persons

    # Publisher information
    publisher = data.get("publisher", {})
    if isinstance(publisher, dict):
        extracted["publisher_name"] = publisher.get("name", "")
        extracted["publisher_type"] = publisher.get("@type", "")

    # Additional metadata
    extracted["conformsTo"] = data.get("http://purl.org/dc/terms/conformsTo", {})

    return extracted


def write(json_ld: dict[str, Any]) -> str:
    """Convert Schema.org Dataset to ARC RO-Crate JSON using ARCtrl.

    Args:
        json_ld: Schema.org Dataset as flat dict (from load()).

    Returns:
        RO-Crate JSON string.
    """
    try:
        contacts = _build_persons(json_ld.get("persons", []))
        arc_inv = ARC.create(
            identifier=json_ld.get("@id", "unknown"),
            title=json_ld.get("name", ""),
            description=json_ld.get("description", ""),
            public_release_date=json_ld.get("datePublished", ""),
            contacts=contacts,
        )
        arc = ARC.from_arc_investigation(arc_inv)
        return arc.to_rocrate_json_string()(arc)

    except Exception as e:
        logger.warning("ARCtrl conversion failed, using fallback: %s", e)
        return json.dumps(_fallback_convert(json_ld), indent=2)


def _fallback_convert(json_ld: dict[str, Any]) -> dict[str, Any]:
    """Minimal ARC RO-Crate structure when ARCtrl is unavailable."""
    # Create minimal ARC structure
    arc_structure = {
        "@context": {
            "@vocab": "https://w3id.org/ro/crate/1.1/",
            "@base": "./",
        },
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": "https://w3id.org/ro/crate/1.1",
                "about": {"@id": "./"},
                "hasPart": [{"@id": "data/"}],
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": json_ld.get("name", "Unknown Dataset"),
                "description": json_ld.get("description", ""),
                "datePublished": json_ld.get("datePublished", ""),
                "license": json_ld.get("license", ""),
                "keywords": json_ld.get("keywords", []),
            },
        ],
    }

    # Add publisher if available
    publisher = json_ld.get("publisher", {})
    if publisher:
        publisher_entry = {
            "@id": f"publisher_{hash(str(publisher))}",
            "@type": publisher.get("@type", "Organization"),
            "name": publisher.get("name", ""),
        }
        arc_structure["@graph"].append(publisher_entry)
        # Link publisher to dataset
        dataset_entry = next(
            (entry for entry in arc_structure["@graph"] if entry["@id"] == "./"), None
        )
        if dataset_entry:
            dataset_entry["publisher"] = {"@id": publisher_entry["@id"]}

    return arc_structure


def _build_persons(persons: list[dict[str, Any]]) -> list[Person]:
    """Convert raw person dicts to ARCtrl Person objects."""
    result = []
    for p in persons:
        if not isinstance(p, dict):
            continue
        result.append(
            Person(
                first_name=p.get("givenName", p.get("first_name", "")),
                last_name=p.get("familyName", p.get("last_name", "")),
                email=p.get("email", ""),
                orcid=p.get("orcid", ""),
            )
        )
    return result
