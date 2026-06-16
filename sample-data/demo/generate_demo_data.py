#!/usr/bin/env python3
"""Generate demo data: 6 Schema.org + 6 ARC files (2 themes x 3 levels x 2 formats).

Schema.org files use proper Schema.org vocabulary throughout.
ARC RO-Crate files match what the ARC export should produce per compliance level.

Usage:  uv run python sample-data/demo/generate_demo_data.py
"""

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent

# ── Persons ─────────────────────────────────────────────────────────────────

TIMO = {
    "@type": "Person",
    "givenName": "Timo",
    "familyName": "Mühlhaus",
    "name": "Timo Mühlhaus",
    "email": "timo.muehlhaus@rptu.de",
    "affiliation": {"@type": "Organization", "name": "RPTU University of Kaiserslautern"},
    "identifier": {"@type": "PropertyValue", "propertyID": "orcid", "value": "0000-0003-3925-6778"},
}
OLIVER = {
    "@type": "Person",
    "givenName": "Oliver",
    "familyName": "Maus",
    "name": "Oliver Maus",
    "email": "maus@nfdi4plants.org",
    "affiliation": {"@type": "Organization", "name": "RPTU University of Kaiserslautern"},
    "identifier": {"@type": "PropertyValue", "propertyID": "orcid", "value": "0000-0002-8241-5300"},
}
UWE = {
    "@type": "Person",
    "givenName": "Uwe",
    "familyName": "Scholz",
    "name": "Uwe Scholz",
    "email": "scholz@ipk-gatersleben.de",
    "affiliation": {"@type": "Organization", "name": "IPK Gatersleben"},
    "identifier": {"@type": "PropertyValue", "propertyID": "orcid", "value": "0000-0001-6113-3518"},
}
THOMAS = {
    "@type": "Person",
    "givenName": "Thomas",
    "familyName": "Schmutzer",
    "name": "Thomas Schmutzer",
    "email": "schmutzer@ipk-gatersleben.de",
    "affiliation": {"@type": "Organization", "name": "IPK Gatersleben"},
    "identifier": {"@type": "PropertyValue", "propertyID": "orcid", "value": "0000-0003-1073-6719"},
}
CHRISTIAN = {
    "@type": "Person",
    "givenName": "Christian",
    "familyName": "Colmsee",
    "name": "Christian Colmsee",
    "email": "colmsee@ipk-gatersleben.de",
    "affiliation": {"@type": "Organization", "name": "IPK Gatersleben"},
    "identifier": {"@type": "PropertyValue", "propertyID": "orcid", "value": "0000-0003-4387-4923"},
}

# ── Theme Data ──────────────────────────────────────────────────────────────

def _build_themes():
    return {
        "wheat": {
            "doi": "10.5447/fairweaver/2024/wheat-drought-001",
            "name": "Wheat Drought Phenotyping Field Trial 2024",
            "description": "Multi-temporal drone-based NDVI and multispectral imaging of winter wheat (Triticum aestivum cv. Julius) under controlled drought stress. Six field plots with three irrigation regimes: full irrigation (100% ETc), reduced irrigation (50% ETc), and rain-fed control. Imaging conducted bi-weekly from stem elongation to physiological maturity using DJI Matrice 300 RTK equipped with Micasense RedEdge-MX multispectral sensor.",
            "creator": TIMO,
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "datePublished": "2024-09-15",
            "keywords": ["wheat", "drought stress", "NDVI", "phenotyping", "field trial", "Triticum aestivum", "multispectral imaging"],
            "publisher": {"@type": "Organization", "name": "RPTU University of Kaiserslautern, Plant Phenomics Group"},
            "url": "https://fairweaver.example.org/datasets/wheat-drought-2024",
            "inLanguage": "en",
            "version": "1.0",
            "alternateName": "Wheat Drought Field Trial 2024",
            "about_crop": {"@type": "Thing", "name": "Triticum aestivum", "sameAs": "http://purl.obolibrary.org/obo/NCBITaxon_4565"},
            "measurementTechnique": "Multispectral imaging",
            "instrument": {"@type": "Thing", "name": "Micasense RedEdge-MX", "description": "Multispectral sensor on DJI Matrice 300 RTK UAV", "additionalType": "Sensor"},
            "funder": "DFG – German Research Foundation",
            "distribution": {"@type": "DataDownload", "contentUrl": "https://fairweaver.example.org/datasets/wheat-drought-2024/download", "encodingFormat": "application/zip"},
            "citation": {"@type": "ScholarlyArticle", "name": "Multi-temporal UAV-based phenotyping of winter wheat under drought stress", "identifier": "https://doi.org/10.1234/fake-doi/wheat-2024"},
            "crop_pest": "Zymoseptoria tritici",
            "crop_pest_uri": "http://purl.obolibrary.org/obo/NCBITaxon_5284",
            "authors": [TIMO, OLIVER],
        },
        "maize": {
            "doi": "10.5447/fairweaver/2024/maize-heat-001",
            "name": "Maize Heat Stress Transcriptome RNA-Seq Dataset",
            "description": "Transcriptome profiling of maize (Zea mays cv. B73) leaf tissue under heat stress (38 degree C day / 28 degree C night, 14h photoperiod) vs control (28 degree C day / 18 degree C night). Three biological replicates per condition. RNA extracted from 3rd fully expanded leaf at V6 stage. Stranded mRNA-seq libraries sequenced on Illumina NovaSeq 6000, 2x150bp PE, approximately 40M reads per sample. Heat stress responsive transcription factors and heat shock protein expression analyzed.",
            "creator": UWE,
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "datePublished": "2024-07-01",
            "keywords": ["maize", "heat stress", "RNA-Seq", "transcriptomics", "Zea mays", "heat shock proteins", "NovaSeq"],
            "publisher": {"@type": "Organization", "name": "IPK Gatersleben, Genome Diversity Group"},
            "url": "https://fairweaver.example.org/datasets/maize-heat-2024",
            "inLanguage": "en",
            "version": "2.1",
            "alternateName": "Maize Heat Stress Transcriptome 2024",
            "about_crop": {"@type": "Thing", "name": "Zea mays", "sameAs": "http://purl.obolibrary.org/obo/NCBITaxon_4577"},
            "measurementTechnique": "RNA-Seq transcriptomics",
            "instrument": {"@type": "Thing", "name": "Illumina NovaSeq 6000", "description": "High-throughput sequencing platform for mRNA-seq", "additionalType": "SequencingPlatform"},
            "funder": "BMBF – German Ministry of Education and Research",
            "distribution": {"@type": "DataDownload", "contentUrl": "https://fairweaver.example.org/datasets/maize-heat-2024/download", "encodingFormat": "application/zip"},
            "citation": {"@type": "ScholarlyArticle", "name": "Transcriptome analysis of heat-stressed maize reveals novel thermotolerance pathways", "identifier": "https://doi.org/10.1234/fake-doi/maize-2024"},
            "crop_pest": "Spodoptera frugiperda",
            "crop_pest_uri": "http://purl.obolibrary.org/obo/NCBITaxon_7108",
            "authors": [UWE, THOMAS, CHRISTIAN],
        },
    }


# ── Schema.org Builder ──────────────────────────────────────────────────────

def build_schema_org(t: dict, theme_key: str, level: str) -> dict:
    root = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": "https://doi.org/" + t["doi"],
    }

    # Basic fields (FAIRagro required)
    root["name"] = t["name"]
    root["description"] = t["description"]
    root["creator"] = t["creator"]
    root["license"] = t["license"]
    root["datePublished"] = t["datePublished"]

    if level == "basic":
        return root

    # Intermediate fields (FAIRagro recommended)
    root["keywords"] = t["keywords"]
    root["publisher"] = t["publisher"]
    root["url"] = t["url"]
    root["inLanguage"] = t["inLanguage"]
    root["version"] = t["version"]
    root["alternateName"] = t["alternateName"]

    if level == "intermediate":
        return root

    # Full fields (FAIRagro full)
    root["about"] = t["about_crop"]
    root["measurementTechnique"] = t["measurementTechnique"]
    root["instrument"] = t["instrument"]
    root["funder"] = {"@type": "Organization", "name": t["funder"]}
    root["distribution"] = t["distribution"]
    root["citation"] = t["citation"]
    root["crop_pest"] = t["crop_pest"]
    root["crop_pest_uri"] = t["crop_pest_uri"]

    return root


# ── ARC RO-Crate Builder ────────────────────────────────────────────────────

def build_arc(t: dict, theme_key: str, level: str) -> dict:
    is_intermediate = level in ("intermediate", "full")
    is_full = level == "full"

    graph = []

    # -- RO-Crate metadata
    graph.append({
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": "https://w3id.org/ro/crate/1.1",
        "about": {"@id": "./"},
    })

    # -- Root dataset (ARC RO-Crate root)
    root = {
        "@id": "./",
        "@type": "Dataset",
        "name": t["name"],
        "description": t["description"],
        "datePublished": t["datePublished"],
        "license": t["license"],
        "creator": [{"@id": "#" + _person_id(p)} for p in t["authors"]],
    }
    graph.append(root)

    # -- Person entries
    for p in t["authors"]:
        pid = "#" + _person_id(p)
        entry = {
            "@id": pid,
            "@type": "Person",
            "givenName": p["givenName"],
            "familyName": p["familyName"],
            "name": p["name"],
        }
        if p.get("email"):
            entry["email"] = p["email"]
        if "identifier" in p:
            entry["identifier"] = p["identifier"]
        if "affiliation" in p:
            entry["affiliation"] = p["affiliation"]
        graph.append(entry)

    # -- Organization
    org_name = t["publisher"]["name"]
    org_id = "#Organization_" + org_name.replace(" ", "_").replace(",", "")
    graph.append({"@id": org_id, "@type": "Organization", "name": org_name})

    # -- Investigation
    inv = {
        "@id": "#Investigation_" + theme_key,
        "@type": "Dataset",
        "additionalType": "Investigation",
        "name": t["name"],
        "description": t["description"],
        "identifier": t["doi"],
        "license": t["license"],
        "datePublished": t["datePublished"],
        "creator": [{"@id": "#" + _person_id(p)} for p in t["authors"]],
        "hasPart": [{"@id": "#Study_" + theme_key}],
    }
    if is_intermediate:
        inv["keywords"] = t["keywords"]
        inv["publisher"] = {"@id": org_id}
    if is_full:
        inv["funder"] = t["funder"]
        inv["alternative_titles"] = [t["alternateName"]]
        inv["investigationContacts"] = [{"@id": "#" + _person_id(t["authors"][0])}]
        inv["investigationPublications"] = [{"@id": "#Publication_" + theme_key}]
    graph.append(inv)

    # -- Publication (full only)
    if is_full:
        graph.append({
            "@id": "#Publication_" + theme_key,
            "@type": "ScholarlyArticle",
            "name": t["citation"]["name"],
            "identifier": t["citation"]["identifier"],
            "author": [{"@id": "#" + _person_id(p)} for p in t["authors"]],
        })

    # -- Study
    study = {
        "@id": "#Study_" + theme_key,
        "@type": "Dataset",
        "additionalType": "Study",
        "name": theme_key.title() + " Field Trial",
        "description": "Field study: " + t["name"],
        "hasPart": [{"@id": "#Assay_" + theme_key}],
    }
    if is_intermediate:
        study["studyDesignDescriptors"] = t["keywords"]
        study["studyDesignType"] = "Randomized complete block design" if theme_key == "wheat" else "Completely randomized design"
        study["studyPersonnel"] = [{"@id": "#" + _person_id(t["authors"][0])}]
    if is_full:
        study["crop_species"] = t["about_crop"]["name"]
        study["crop_species_uri"] = t["about_crop"]["sameAs"]
        study["crop_pest"] = t["crop_pest"]
        study["crop_pest_uri"] = t["crop_pest_uri"]
    graph.append(study)

    # -- Assay
    assay = {
        "@id": "#Assay_" + theme_key,
        "@type": "Dataset",
        "additionalType": "Assay",
        "name": theme_key.title() + " " + t["measurementTechnique"],
        "description": t["measurementTechnique"] + " assay for " + t["name"],
        "measurementTechnique": t["measurementTechnique"],
        "about": [{"@id": "#Study_" + theme_key}],
    }
    if is_intermediate:
        assay["assayCategory"] = "measurement"
        assay["assayType"] = "imaging_assay" if "imaging" in t["measurementTechnique"].lower() else "seq_assay"
    if is_full:
        assay["instrument"] = [{"@id": "#Instrument_" + theme_key}]
        graph.append({
            "@id": "#Instrument_" + theme_key,
            "@type": t["instrument"]["additionalType"],
            "name": t["instrument"]["name"],
            "description": t["instrument"]["description"],
        })
    graph.append(assay)

    # -- Data files
    suffix = "tiff" if "imaging" in t["measurementTechnique"].lower() else "fastq"
    for i in range(1, 4):
        graph.append({
            "@id": f"assays/{theme_key}/dataset/sample{i}.{suffix}",
            "@type": "File",
            "name": f"Sample {i} - {theme_key}",
            "encodingFormat": "image/tiff" if suffix == "tiff" else "application/gzip",
        })

    return {
        "@context": ["https://w3id.org/ro/crate/1.1/context", {"@vocab": "https://schema.org/"}],
        "@graph": graph,
    }


def _person_id(p: dict) -> str:
    return p["familyName"] + "_" + p["givenName"].replace(" ", "_")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    themes = _build_themes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for theme_key in ("wheat", "maize"):
        t = themes[theme_key]
        for level in ("basic", "intermediate", "full"):
            so = build_schema_org(t, theme_key, level)
            so_path = OUT_DIR / f"schema-org-{theme_key}-{level}.json"
            with open(so_path, "w") as f:
                json.dump(so, f, indent=2)
            print(f"  Created {so_path.name}")

            arc = build_arc(t, theme_key, level)
            arc_path = OUT_DIR / f"arc-ro-crate-{theme_key}-{level}.json"
            with open(arc_path, "w") as f:
                json.dump(arc, f, indent=2)
            print(f"  Created {arc_path.name}")

    print(f"\nAll 12 files generated in {OUT_DIR}")


if __name__ == "__main__":
    main()
