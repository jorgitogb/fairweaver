"""
FAIRweaver format plugin: DataCite XML
https://schema.datacite.org/
"""

import xml.etree.ElementTree as ET

FORMAT_ID = "datacite_xml"
LABEL = "DataCite XML"
EXTENSIONS = [".xml"]

NS = {"dc": "http://datacite.org/schema/kernel-4"}


def load(content: bytes) -> dict:
    """Parse DataCite XML bytes into a flat dict for the mapping engine."""
    root = ET.fromstring(content)

    def find(tag: str) -> str:
        el = root.find(f"dc:{tag}", NS) or root.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    flat = {
        "identifier": find("identifier"),
        "title": _find_title(root),
        "description": _find_description(root),
        "publicationYear": find("publicationYear"),
        "resourceType": _find_resource_type(root),
        "creator": _find_creator(root),
        "publisher": find("publisher"),
        "language": find("language"),
    }
    return {k: v for k, v in flat.items() if v}


def write(json_ld: dict) -> dict:
    """Convert pivot JSON-LD to a DataCite-like dict (full XML serialisation: post-hackathon)."""
    return {
        "identifier": json_ld.get("identifier", ""),
        "title": json_ld.get("name", json_ld.get("title", "")),
        "description": json_ld.get("description", ""),
        "publicationYear": json_ld.get("datePublished", "")[:4] if json_ld.get("datePublished") else "",
        "publisher": json_ld.get("publisher", {}).get("name", "") if isinstance(json_ld.get("publisher"), dict) else json_ld.get("publisher", ""),
    }


def _find_title(root) -> str:
    titles = root.find("dc:titles", NS) or root.find("titles")
    if titles is not None:
        t = titles.find("dc:title", NS) or titles.find("title")
        if t is not None and t.text:
            return t.text.strip()
    return ""


def _find_description(root) -> str:
    descs = root.find("dc:descriptions", NS) or root.find("descriptions")
    if descs is not None:
        d = descs.find("dc:description", NS) or descs.find("description")
        if d is not None and d.text:
            return d.text.strip()
    return ""


def _find_resource_type(root) -> str:
    rt = root.find("dc:resourceType", NS) or root.find("resourceType")
    if rt is not None:
        return rt.get("resourceTypeGeneral", rt.text or "")
    return ""


def _find_creator(root) -> str:
    creators = root.find("dc:creators", NS) or root.find("creators")
    if creators is not None:
        c = creators.find("dc:creator", NS) or creators.find("creator")
        if c is not None:
            name = c.find("dc:creatorName", NS) or c.find("creatorName")
            if name is not None and name.text:
                return name.text.strip()
    return ""