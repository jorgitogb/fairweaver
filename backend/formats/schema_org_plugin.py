import json

FORMAT_ID = "schema_org"
LABEL = "Schema.org JSON-LD"
EXTENSIONS = [".json"]


def load(content: bytes) -> dict:
    data = json.loads(content)
    if isinstance(data, list):
        data = data[0] if data else {}

    result = {
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

    # ── Persons (combined from author/creator/contributor) ──
    authors = data.get("author", [])
    creators = data.get("creator", [])
    contributors = data.get("contributor", [])
    all_persons = []
    for person_list in [authors, creators, contributors]:
        if isinstance(person_list, list):
            all_persons.extend(person_list)
        elif isinstance(person_list, dict):
            all_persons.append(person_list)
    result["persons"] = all_persons

    # ── Investigation-level ──
    if data.get("alternateName"):
        result["alternateName"] = data["alternateName"]
    if data.get("funder"):
        result["funder"] = data["funder"]
    if data.get("citation"):
        result["citation"] = data["citation"]
    if data.get("investigationContacts"):
        result["investigationContacts"] = data["investigationContacts"]
    if data.get("investigationPublications"):
        result["investigationPublications"] = data["investigationPublications"]
    if data.get("distribution"):
        result["distribution"] = data["distribution"]

    # ── Study-level ──
    if data.get("studyDesignDescriptors"):
        result["studyDesignDescriptors"] = data["studyDesignDescriptors"]
    if data.get("studyDesignType"):
        result["studyDesignType"] = data["studyDesignType"]
    if data.get("studyPersonnel"):
        result["studyPersonnel"] = data["studyPersonnel"]
    if data.get("studyName"):
        result["studyName"] = data["studyName"]
    if data.get("studyDescription"):
        result["studyDescription"] = data["studyDescription"]
    if data.get("crop_species"):
        result["crop_species"] = data["crop_species"]
    if data.get("crop_species_uri"):
        result["crop_species_uri"] = data["crop_species_uri"]
    if data.get("crop_pest"):
        result["crop_pest"] = data["crop_pest"]
    if data.get("crop_pest_uri"):
        result["crop_pest_uri"] = data["crop_pest_uri"]

    # ── Assay-level ──
    if data.get("measurementTechnique"):
        result["measurementTechnique"] = data["measurementTechnique"]
    if data.get("measurementMethod"):
        result["measurementMethod"] = data["measurementMethod"]
    if data.get("technologyType"):
        result["technologyType"] = data["technologyType"]
    if data.get("technologyPlatform"):
        result["technologyPlatform"] = data["technologyPlatform"]
    if data.get("assayCategory"):
        result["assayCategory"] = data["assayCategory"]
    if data.get("assayType"):
        result["assayType"] = data["assayType"]
    if data.get("assayName"):
        result["assayName"] = data["assayName"]
    if data.get("instrument"):
        result["instrument"] = data["instrument"]
    if data.get("sensorType"):
        result["sensorType"] = data["sensorType"]
    if data.get("sensorPlatformType"):
        result["sensorPlatformType"] = data["sensorPlatformType"]

    # ── Crop / About ──
    if data.get("about"):
        result["about"] = data["about"]

    # ── Geographic / Location ──
    if data.get("location"):
        result["location"] = data["location"]
    if data.get("country"):
        result["geo_country"] = data["country"]
    if data.get("state"):
        result["geo_state"] = data["state"]
    if data.get("county"):
        result["geo_county"] = data["county"]

    # Extract lat/lng from location or drone fields
    location = data.get("location", {})
    if isinstance(location, dict):
        geo = location.get("geo", {})
        if isinstance(geo, dict):
            lat = geo.get("latitude")
            lng = geo.get("longitude")
            alt = geo.get("altitude")
            if lat:
                result["geo_latitude"] = lat
            if lng:
                result["geo_longitude"] = lng
            if alt:
                result["geo_altitude"] = alt
    if data.get("drone_latitude"):
        result["drone_latitude"] = data["drone_latitude"]
    if data.get("drone_longitude"):
        result["drone_longitude"] = data["drone_longitude"]

    # ── Soil ──
    if data.get("soilType"):
        result["soilType"] = data["soilType"]

    # ── Process ──
    if data.get("processType"):
        result["processType"] = data["processType"]

    return result


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
