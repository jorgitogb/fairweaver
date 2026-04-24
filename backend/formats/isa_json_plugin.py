"""
FAIRweaver format plugin: ISA-JSON
https://isa-specs.readthedocs.io/en/latest/isajson.html
"""

import json

FORMAT_ID = "isa_json"
LABEL = "ISA-JSON"
EXTENSIONS = [".json"]


def load(content: bytes) -> dict:
    """Parse ISA-JSON bytes into a flat dict for the mapping engine."""
    data = json.loads(content)

    # ISA-JSON top level: investigation object
    flat = {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "identifier": data.get("identifier", ""),
        "submissionDate": data.get("submissionDate", ""),
        "publicReleaseDate": data.get("publicReleaseDate", ""),
    }

    # Pull first study if present
    studies = data.get("studies", [])
    if studies:
        study = studies[0]
        flat.update({
            "study.title": study.get("title", ""),
            "study.description": study.get("description", ""),
            "study.identifier": study.get("identifier", ""),
            "study.filename": study.get("filename", ""),
        })
        # Contacts
        contacts = study.get("people", [])
        if contacts:
            p = contacts[0]
            flat["study.contact.firstName"] = p.get("firstName", "")
            flat["study.contact.lastName"] = p.get("lastName", "")
            flat["study.contact.email"] = p.get("email", "")

    return flat


def write(json_ld: dict) -> dict:
    """Convert pivot JSON-LD back to a minimal ISA-JSON structure."""
    return {
        "title": json_ld.get("name", json_ld.get("title", "")),
        "description": json_ld.get("description", ""),
        "identifier": json_ld.get("identifier", ""),
        "studies": [],
    }