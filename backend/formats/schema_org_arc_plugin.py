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

    if isinstance(data, list):
        data = data[0] if data else {}

    extracted = {}

    extracted["@context"] = data.get("@context", "")
    extracted["@id"] = data.get("@id", "")
    extracted["@type"] = data.get("@type", "")

    extracted["name"] = data.get("name", "")
    extracted["description"] = data.get("description", "")
    extracted["keywords"] = data.get("keywords", [])
    extracted["datePublished"] = data.get("datePublished", "")
    extracted["inLanguage"] = data.get("inLanguage", "")
    extracted["license"] = data.get("license", "")

    authors = data.get("author", [])
    creators = data.get("creator", [])
    contributors = data.get("contributor", [])

    all_persons = []
    for person_list in [authors, creators, contributors]:
        if isinstance(person_list, list):
            all_persons.extend(person_list)
        elif isinstance(person_list, dict):
            all_persons.append(person_list)

    extracted["persons"] = all_persons

    publisher = data.get("publisher", {})
    if isinstance(publisher, dict):
        extracted["publisher_name"] = publisher.get("name", "")
        extracted["publisher_type"] = publisher.get("@type", "")

    if data.get("funder"):
        extracted["funder"] = data["funder"]
    if data.get("citation"):
        extracted["citation"] = data["citation"]
    if data.get("url"):
        extracted["url"] = data["url"]
    if data.get("version"):
        extracted["version"] = data["version"]
    if data.get("alternateName"):
        extracted["alternateName"] = data["alternateName"]

    if data.get("measurementTechnique"):
        extracted["measurementTechnique"] = data["measurementTechnique"]
    if data.get("measurementMethod"):
        extracted["measurementMethod"] = data["measurementMethod"]
    if data.get("technologyType"):
        extracted["technologyType"] = data["technologyType"]
    if data.get("technologyPlatform"):
        extracted["technologyPlatform"] = data["technologyPlatform"]
    if data.get("instrument"):
        extracted["instrument"] = data["instrument"]

    if data.get("about"):
        extracted["about"] = data["about"]
    if data.get("crop_species"):
        extracted["crop_species"] = data["crop_species"]
    if data.get("crop_pest"):
        extracted["crop_pest"] = data["crop_pest"]

    if data.get("location"):
        extracted["location"] = data["location"]
    if data.get("country"):
        extracted["country"] = data["country"]
    if data.get("state"):
        extracted["state"] = data["state"]
    if data.get("county"):
        extracted["county"] = data["county"]

    extracted["conformsTo"] = data.get("http://purl.org/dc/terms/conformsTo", {})

    return extracted


def write(json_ld: dict[str, Any]) -> str:
    """Convert Schema.org Dataset to ARC RO-Crate JSON using ARCtrl.

    Handles both the extracted format (from load()) and raw Schema.org
    format (from the arc-export endpoint). Enriches the ARCtrl output
    with additional entities and fields.

    Args:
        json_ld: Schema.org Dataset dict (extracted or raw).

    Returns:
        RO-Crate JSON string.
    """
    try:
        persons = _extract_persons(json_ld)
        contacts = _build_persons(persons)

        arc_inv = ARC.create(
            identifier=json_ld.get("@id") or json_ld.get("identifier", "unknown"),
            title=json_ld.get("name", ""),
            description=json_ld.get("description", ""),
            public_release_date=json_ld.get("datePublished", ""),
            contacts=contacts,
        )
        arc = ARC.from_arc_investigation(arc_inv)
        raw = arc.to_rocrate_json_string()(arc)
    except Exception as e:
        logger.warning("ARCtrl conversion failed, using fallback: %s", e)
        raw = json.dumps(_fallback_convert(json_ld))

    result = json.loads(raw)
    _enrich_output(result, json_ld)
    return json.dumps(result, indent=2)


def _extract_persons(data: dict) -> list[dict]:
    """Extract persons from either extracted format (persons key)
    or raw Schema.org format (creator/author keys)."""
    persons = data.get("persons", [])
    if persons:
        return persons if isinstance(persons, list) else [persons]

    result = []
    for key in ("creator", "author", "contributor"):
        val = data.get(key)
        if isinstance(val, list):
            result.extend(val)
        elif isinstance(val, dict):
            result.append(val)
    return result


def _enrich_output(result: dict, source: dict) -> None:
    """Post-process ARCtrl output to add missing entities and fields."""
    graph = result.setdefault("@graph", [])

    root = next((e for e in graph if e.get("@id") == "./"), None)
    if not root:
        root = {"@id": "./", "@type": "Dataset"}
        graph.append(root)

    # Preserve original license and datePublished (ARCtrl may overwrite)
    if source.get("license"):
        root["license"] = source["license"]
    if source.get("datePublished"):
        root["datePublished"] = source["datePublished"]

    # Add keywords
    keywords = source.get("keywords", [])
    if keywords:
        root["keywords"] = keywords if isinstance(keywords, list) else [keywords]

    # Add url, version, inLanguage
    if source.get("url"):
        root["url"] = source["url"]
    if source.get("version"):
        root["version"] = source["version"]
    if source.get("inLanguage"):
        root["inLanguage"] = source["inLanguage"]

    # Add publisher as Organization entity
    publisher = source.get("publisher", {})
    if isinstance(publisher, dict) and publisher.get("name"):
        org_id = "#Publisher_" + publisher["name"].replace(" ", "_")
        if not any(e.get("@id") == org_id for e in graph):
            graph.append(
                {
                    "@id": org_id,
                    "@type": "Organization",
                    "name": publisher["name"],
                }
            )
        root["publisher"] = {"@id": org_id}

    # Add funder
    funder_val = source.get("funder")
    if funder_val:
        root["funder"] = (
            funder_val
            if isinstance(funder_val, str)
            else (funder_val.get("name", "") if isinstance(funder_val, dict) else "")
        )

    # Add alternateName as alternative_titles
    if source.get("alternateName"):
        root["alternative_titles"] = (
            [source["alternateName"]]
            if isinstance(source["alternateName"], str)
            else source["alternateName"]
        )

    # Add Study entity
    study_id = "studies/Study_1/"
    study = next((e for e in graph if e.get("@id") == study_id), None)
    if not study and source.get("measurementTechnique"):
        study_name = source.get("studyName") or "Study of " + source.get("name", "Dataset")
        study_desc = source.get("studyDescription") or "Study derived from " + source.get(
            "name", "Dataset"
        )
        study = {
            "@id": study_id,
            "@type": "Dataset",
            "additionalType": "Study",
            "name": study_name,
            "description": study_desc,
        }
        study_descriptors = source.get("studyDesignDescriptors") or source.get("keywords")
        if study_descriptors:
            study["studyDesignDescriptors"] = (
                study_descriptors if isinstance(study_descriptors, list) else [study_descriptors]
            )
        if source.get("studyDesignType"):
            study["studyDesignType"] = source["studyDesignType"]
        graph.append(study)
        root.setdefault("hasPart", []).append({"@id": study_id})

    # Add Assay entity
    assay_id = "assays/Assay_1/"
    assay = next((e for e in graph if e.get("@id") == assay_id), None)
    if not assay and source.get("measurementTechnique"):
        assay = {
            "@id": assay_id,
            "@type": "Dataset",
            "additionalType": "Assay",
            "name": source.get("assayName") or "Assay for " + source.get("name", "Dataset"),
            "description": source.get("description", ""),
            "measurementTechnique": source.get("measurementTechnique", ""),
            "measurementMethod": source.get("measurementMethod")
            or source.get("measurementTechnique", ""),
            "technologyType": source.get("technologyType")
            or source.get("measurementTechnique", ""),
            "technologyPlatform": source.get("technologyPlatform") or "",
        }
        if source.get("assayCategory"):
            assay["assayCategory"] = source["assayCategory"]
        if source.get("assayType"):
            assay["assayType"] = source["assayType"]
        about_target = source.get("studyName") and study_id
        if about_target:
            assay["about"] = [{"@id": study_id}]
        graph.append(assay)

    # Link Study → Assay
    study_entity = next((e for e in graph if e.get("additionalType") == "Study"), None)
    assay_entity = next((e for e in graph if e.get("additionalType") == "Assay"), None)
    if study_entity and assay_entity:
        study_entity.setdefault("hasPart", []).append({"@id": assay_id})
        if not assay_entity.get("about"):
            assay_entity["about"] = [{"@id": study_entity["@id"]}]

    # Add isa.investigation.xlsx File entity (DataPLANT compliance)
    if not any(e.get("@id") == "isa.investigation.xlsx" for e in graph):
        graph.append(
            {
                "@id": "isa.investigation.xlsx",
                "@type": "File",
                "name": "ISA Investigation Metadata",
                "description": "Required ISA investigation metadata file for DataPLANT ARC compliance",
            }
        )

    # Add Instrument entity
    instrument = source.get("instrument")
    if isinstance(instrument, dict) and instrument.get("name"):
        instr_id = "#Instrument_1"
        if not any(e.get("@id") == instr_id for e in graph):
            graph.append(
                {
                    "@id": instr_id,
                    "@type": instrument.get("additionalType", "Thing"),
                    "name": instrument["name"],
                    "description": instrument.get("description", ""),
                }
            )

    # Add Location / Place entity
    location = source.get("location")
    if isinstance(location, dict):
        loc_id = "#Location_1"
        if not any(e.get("@id") == loc_id for e in graph):
            loc_entity = {"@id": loc_id, "@type": "Place"}
            if location.get("name"):
                loc_entity["name"] = location["name"]
            geo = location.get("geo")
            if isinstance(geo, dict):
                geo_entity = {"@type": "GeoCoordinates"}
                if geo.get("latitude"):
                    geo_entity["latitude"] = geo["latitude"]
                if geo.get("longitude"):
                    geo_entity["longitude"] = geo["longitude"]
                loc_entity["geo"] = geo_entity
            graph.append(loc_entity)
            root["location"] = {"@id": loc_id}

    # Add DefinedRegion (country/state/county)
    geo_coverage = {}
    if source.get("country"):
        geo_coverage["country"] = source["country"]
    if source.get("state"):
        geo_coverage["state"] = source["state"]
    if source.get("county"):
        geo_coverage["county"] = source["county"]
    if geo_coverage:
        gc_id = "#GeographicCoverage_1"
        if not any(e.get("@id") == gc_id for e in graph):
            graph.append(
                {
                    "@id": gc_id,
                    "@type": "DefinedRegion",
                    **geo_coverage,
                }
            )
            root["geographicCoverage"] = {"@id": gc_id}

    # Add Soil entity
    if source.get("soilType"):
        soil_id = "#Soil_1"
        if not any(e.get("@id") == soil_id for e in graph):
            graph.append(
                {
                    "@id": soil_id,
                    "@type": "Thing",
                    "name": source["soilType"],
                    "additionalType": "SoilType",
                }
            )
            root["soil"] = {"@id": soil_id}

    # Add Process entity
    if source.get("processType"):
        proc_id = "#Process_1"
        if not any(e.get("@id") == proc_id for e in graph):
            graph.append(
                {
                    "@id": proc_id,
                    "@type": "Thing",
                    "name": source["processType"],
                    "additionalType": "Process",
                }
            )
            root["process"] = {"@id": proc_id}

    # Add investigationPublications (supports array of publications)
    pubs = source.get("investigationPublications", [])
    if not pubs and source.get("citation"):
        pubs = [source["citation"]]
    if isinstance(pubs, dict):
        pubs = [pubs]
    pub_refs = []
    for i, pub in enumerate(pubs):
        if isinstance(pub, dict) and pub.get("identifier"):
            pub_id = f"#Publication_{i + 1}"
            if not any(e.get("@id") == pub_id for e in graph):
                graph.append(
                    {
                        "@id": pub_id,
                        "@type": "ScholarlyArticle",
                        "name": pub.get("name", ""),
                        "identifier": pub.get("identifier", ""),
                        "authorList": pub.get("authorList", ""),
                    }
                )
            pub_refs.append({"@id": pub_id})
    if pub_refs:
        root["investigationPublications"] = pub_refs

    # Add investigationContacts from persons
    persons = _extract_persons(source)
    person_refs = []
    for p in persons:
        if isinstance(p, dict):
            pid = (
                p.get("identifier")
                or p.get("@id")
                or "#Person_" + p.get("familyName", "Unknown") + "_" + p.get("givenName", "")
            )
            person_refs.append({"@id": pid})
    if person_refs:
        root["investigationContacts"] = person_refs


def _fallback_convert(json_ld: dict[str, Any]) -> dict[str, Any]:
    """Minimal ARC RO-Crate structure when ARCtrl is unavailable."""
    graph = [
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
    ]

    publisher = json_ld.get("publisher", {})
    if isinstance(publisher, dict) and publisher.get("name"):
        pub_id = "#Publisher_" + publisher["name"].replace(" ", "_")
        graph.append(
            {
                "@id": pub_id,
                "@type": publisher.get("@type", "Organization"),
                "name": publisher["name"],
            }
        )
        graph[1]["publisher"] = {"@id": pub_id}

    return {
        "@context": {
            "@vocab": "https://w3id.org/ro/crate/1.1/",
            "@base": "./",
        },
        "@graph": graph,
    }


def _build_persons(persons: list[dict[str, Any]]) -> list[Person]:
    """Convert raw person dicts to ARCtrl Person objects."""
    result = []
    for p in persons:
        if not isinstance(p, dict):
            continue
        orcid_val = ""
        if p.get("identifier"):
            ident = p["identifier"]
            if isinstance(ident, dict):
                orcid_val = ident.get("value", "")
            elif isinstance(ident, str):
                orcid_val = ident.replace("http://orcid.org/", "")

        result.append(
            Person(
                first_name=p.get("givenName", p.get("first_name", "")),
                last_name=p.get("familyName", p.get("last_name", "")),
                email=p.get("email", ""),
                orcid=orcid_val,
            )
        )
    return result
