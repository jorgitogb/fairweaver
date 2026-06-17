import xml.etree.ElementTree as ET

FORMAT_ID = "oai_dc"
LABEL = "OAI-PMH Dublin Core"
EXTENSIONS = [".xml"]

DC_NS = "http://purl.org/dc/elements/1.1/"
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"


def load(content: bytes) -> dict:
    root = ET.fromstring(content)
    dc_el = root.find(f".//{{{OAI_DC_NS}}}dc")
    if dc_el is None:
        dc_el = root.find(f".//{{{DC_NS}}}dc")
    if dc_el is None:
        for el in root.iter():
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if tag in {"dc", "metadata"}:
                dc_el = el
                break
    if dc_el is None:
        dc_el = root
    return normalize(_element_to_sickle(dc_el))


def normalize(sickle_metadata: dict) -> dict:
    result = {}
    flatten_as_list = {"creator", "contributor", "subject", "identifier", "rights"}
    for key, values in sickle_metadata.items():
        if not isinstance(values, list):
            values = [values]
        cleaned = [v.strip() for v in values if isinstance(v, str) and v.strip()]
        if not cleaned:
            continue
        if key in flatten_as_list:
            result[key] = cleaned
        else:
            result[key] = cleaned[0] if len(cleaned) == 1 else "; ".join(cleaned)
    return result


def _element_to_sickle(el: ET.Element) -> dict:
    result = {}
    for child in el:
        tag = child.tag.split("}")[-1]
        text = (child.text or "").strip()
        if text:
            result.setdefault(tag, []).append(text)
    return result


def write(json_ld: dict) -> dict:
    out = {"@format": "oai_dc"}
    dc_fields = {
        "title",
        "creator",
        "subject",
        "description",
        "publisher",
        "contributor",
        "date",
        "type",
        "format",
        "identifier",
        "source",
        "language",
        "relation",
        "coverage",
        "rights",
    }
    for k in dc_fields:
        if k in json_ld and json_ld[k]:
            out[k] = json_ld[k]
    return out
