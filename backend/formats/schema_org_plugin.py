import json

FORMAT_ID = "schema_org"
LABEL = "Schema.org JSON-LD"
EXTENSIONS = [".json"]


def load(content: bytes) -> dict:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Schema.org JSON-LD must be a JSON object, not an array")

    return {
        "identifier": data.get("@id", data.get("identifier", "")),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "creator": data.get("creator", ""),
        "keywords": data.get("keywords", ""),
        "license": data.get("license", ""),
        "datePublished": data.get("datePublished", ""),
        "publisher": data.get("publisher", ""),
        "url": data.get("url", ""),
        "inLanguage": data.get("inLanguage", ""),
        "version": data.get("version", ""),
    }


def write(json_ld: dict) -> dict:
    out = {"@context": "https://schema.org", "@type": "Dataset"}
    target_keys = {
        "name",
        "description",
        "identifier",
        "creator",
        "keywords",
        "license",
        "datePublished",
        "publisher",
        "url",
        "inLanguage",
        "version",
    }
    for k in target_keys:
        if k in json_ld and json_ld[k]:
            out[k] = json_ld[k]
    return out
