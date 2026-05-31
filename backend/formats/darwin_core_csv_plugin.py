import csv
import io

FORMAT_ID = "darwin_core_csv"
LABEL = "Darwin Core CSV"
EXTENSIONS = [".csv"]

DARWIN_CORE_FIELDS = [
    "scientificName",
    "basisOfRecord",
    "eventDate",
    "institutionCode",
    "collectionCode",
    "catalogNumber",
    "decimalLatitude",
    "decimalLongitude",
    "country",
    "stateProvince",
    "locality",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "specificEpithet",
    "recordedBy",
    "identifiedBy",
]

WRITE_MAP = {
    "name": "scientificName",
    "catalogNumber": "catalogNumber",
    "eventDate": "eventDate",
    "recordedBy": "recordedBy",
}


def load(content: bytes) -> dict:
    if not content:
        raise ValueError("empty")
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("no header row")
    for row in reader:
        return {k: row.get(k, "") for k in DARWIN_CORE_FIELDS}
    return {k: "" for k in DARWIN_CORE_FIELDS}


def write(json_ld: dict) -> dict:
    result = {
        "scientificName": json_ld.get("name", ""),
        "description": json_ld.get("description", ""),
        "catalogNumber": json_ld.get("identifier", ""),
        "eventDate": json_ld.get("datePublished", ""),
        "recordedBy": json_ld.get("creator", ""),
        "license": json_ld.get("license", ""),
        "url": json_ld.get("url", ""),
    }
    return result
