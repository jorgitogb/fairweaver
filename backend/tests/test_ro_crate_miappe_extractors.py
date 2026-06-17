"""Unit tests for RO-Crate MIAPPE extraction helpers.

Tests the standalone _extract_* functions and graph helpers in ro_crate_plugin.py.
These functions are called by load() but tested independently for precision.
"""

from __future__ import annotations

from formats.ro_crate_plugin import (
    _cv_value_by_name,
    _cv_value_by_property_id,
    _extract_event_id_crops,
    _extract_geolocation,
    _extract_investigation_meta,
    _extract_origin_country,
    _extract_parameter_values,
    _extract_taxonomy,
    _extract_germplasm,
    _find_sources,
    _resolve_license,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_source(
    source_id: str,
    additional_property: list | None = None,
) -> dict:
    """Build a minimal Source entity."""
    src: dict = {"@id": source_id, "@type": "Source"}
    if additional_property is not None:
        src["additionalProperty"] = additional_property
    return src


def _make_cv(
    property_id: str | None = None,
    name: str | None = None,
    value: str = "",
    cv_id: str | None = None,
) -> dict:
    """Build a CharacteristicValue entity (PropertyValue with additionalType)."""
    cv: dict = {
        "@type": ["PropertyValue"],
        "additionalType": "CharacteristicValue",
        "value": value,
    }
    if cv_id:
        cv["@id"] = cv_id
    if property_id:
        cv["propertyID"] = property_id
    if name:
        cv["name"] = name
    return cv


def _make_lab_process(
    process_id: str,
    parameter_value_refs: list | None = None,
    object_refs: list | None = None,
) -> dict:
    """Build a LabProcess entity."""
    lp: dict = {"@id": process_id, "@type": "LabProcess"}
    if parameter_value_refs is not None:
        lp["parameterValue"] = parameter_value_refs
    if object_refs is not None:
        lp["object"] = object_refs
    return lp


def _build_entities_and_sources(
    source_configs: list[dict],
) -> tuple[dict, list[dict]]:
    """Helper: build (entities, sources) from simplified source configs.

    Each config is a dict with:
      - source_id: str
      - additionalProperty: list of dicts (raw CV structures)
    """
    entities: dict = {}
    sources: list = []
    for cfg in source_configs:
        src = _make_source(cfg["source_id"], cfg.get("additionalProperty"))
        sources.append(src)
        entities[src["@id"]] = src
    return entities, sources


# ── _find_sources ─────────────────────────────────────────────────────────────


class TestFindSources:
    def test_finds_direct_source_entities(self):
        src1 = _make_source("#S1")
        src2 = _make_source("#S2")
        graph = [src1, src2]
        entities = {"#S1": src1, "#S2": src2}
        result = _find_sources(graph, entities)
        assert len(result) == 2
        assert result[0]["@id"] == "#S1"
        assert result[1]["@id"] == "#S2"

    def test_finds_sources_via_lab_process_object(self):
        src = _make_source("#S1")
        lp = _make_lab_process("#LP1", object_refs=[{"@id": "#S1"}])
        graph = [lp]
        entities = {"#S1": src}
        result = _find_sources(graph, entities)
        assert len(result) == 1
        assert result[0]["@id"] == "#S1"

    def test_deduplicates_source_from_direct_and_lab_process(self):
        src = _make_source("#S1")
        lp = _make_lab_process("#LP1", object_refs=[{"@id": "#S1"}])
        graph = [src, lp]
        entities = {"#S1": src}
        result = _find_sources(graph, entities)
        assert len(result) == 1

    def test_skips_non_source_entities(self):
        lp = _make_lab_process("#LP1")
        other = {"@id": "#Other", "@type": "Dataset"}
        graph = [lp, other]
        entities = {}
        result = _find_sources(graph, entities)
        assert len(result) == 0


# ── _cv_value_by_property_id ─────────────────────────────────────────────────


class TestCvValueByPropertyId:
    def test_returns_value_when_match(self):
        cv = _make_cv(property_id="MIAPPE_0042", value="Triticum")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _cv_value_by_property_id(sources, entities, "MIAPPE_0042")
        assert result == "Triticum"

    def test_returns_none_when_no_match(self):
        cv = _make_cv(property_id="MIAPPE_0042", value="Triticum")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _cv_value_by_property_id(sources, entities, "MIAPPE_0099")
        assert result is None

    def test_returns_none_for_empty_value(self):
        cv = _make_cv(property_id="MIAPPE_0042", value="")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _cv_value_by_property_id(sources, entities, "MIAPPE_0042")
        assert result is None

    def test_returns_first_match_across_sources(self):
        cv1 = _make_cv(property_id="MIAPPE_0042", value="Triticum")
        cv2 = _make_cv(property_id="MIAPPE_0042", value="Hordeum")
        entities, sources = _build_entities_and_sources(
            [
                {"source_id": "#S1", "additionalProperty": [cv1]},
                {"source_id": "#S2", "additionalProperty": [cv2]},
            ]
        )
        result = _cv_value_by_property_id(sources, entities, "MIAPPE_0042")
        assert result == "Triticum"


# ── _cv_value_by_name ────────────────────────────────────────────────────────


class TestCvValueByName:
    def test_returns_value_when_name_matches(self):
        cv = _make_cv(name="Origin Country", value="Germany")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _cv_value_by_name(sources, entities, "Origin Country")
        assert result == "Germany"

    def test_returns_none_when_no_match(self):
        cv = _make_cv(name="Origin Country", value="Germany")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _cv_value_by_name(sources, entities, "Organism")
        assert result is None


# ── _extract_taxonomy ────────────────────────────────────────────────────────


class TestExtractTaxonomy:
    def test_extracts_all_three_fields(self):
        genus_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/MIAPPE_0042", value="Triticum"
        )
        species_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/MIAPPE_0043", value="aestivum"
        )
        infra_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0044", value="L.")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [genus_cv, species_cv, infra_cv]}]
        )
        result = _extract_taxonomy(entities, sources)
        assert result == {
            "taxon_genus": "Triticum",
            "taxon_species": "aestivum",
            "taxon_infraspecific_name": "L.",
        }

    def test_returns_none_when_no_cv(self):
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": []}]
        )
        result = _extract_taxonomy(entities, sources)
        assert result == {
            "taxon_genus": None,
            "taxon_species": None,
            "taxon_infraspecific_name": None,
        }

    def test_partial_extraction(self):
        genus_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0042", value="Beta")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [genus_cv]}]
        )
        result = _extract_taxonomy(entities, sources)
        assert result["taxon_genus"] == "Beta"
        assert result["taxon_species"] is None
        assert result["taxon_infraspecific_name"] is None


# ── _extract_geolocation ─────────────────────────────────────────────────────


class TestExtractGeolocation:
    def test_uses_field_geo_when_available(self):
        lat_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/AGRO_00000574", value="52.5")
        lng_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/AGRO_00000575", value="14.1")
        alt_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/AGRO_00000612", value="62.0")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [lat_cv, lng_cv, alt_cv]}]
        )
        result = _extract_geolocation(entities, sources)
        assert result == {"geo_latitude": "52.5", "geo_longitude": "14.1", "geo_altitude": "62.0"}

    def test_falls_back_to_bio_material_geo(self):
        lat_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0045", value="45.2")
        lng_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0046", value="9.4")
        alt_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0047", value="52.3")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [lat_cv, lng_cv, alt_cv]}]
        )
        result = _extract_geolocation(entities, sources)
        assert result == {"geo_latitude": "45.2", "geo_longitude": "9.4", "geo_altitude": "52.3"}

    def test_falls_back_to_material_source_geo(self):
        lat_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0052", value="40.0")
        lng_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0053", value="-3.0")
        alt_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0054", value="650.0")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [lat_cv, lng_cv, alt_cv]}]
        )
        result = _extract_geolocation(entities, sources)
        assert result == {"geo_latitude": "40.0", "geo_longitude": "-3.0", "geo_altitude": "650.0"}

    def test_returns_none_when_no_geo(self):
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": []}]
        )
        result = _extract_geolocation(entities, sources)
        assert result == {"geo_latitude": None, "geo_longitude": None, "geo_altitude": None}


# ── _extract_germplasm ───────────────────────────────────────────────────────


class TestExtractGermplasm:
    def test_extracts_source_id_and_doi(self):
        id_cv = _make_cv(property_id="http://purl.obolibrary.org/obo/MIAPPE_0050", value="ITA383")
        doi_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/MIAPPE_0051", value="10.18730/YSFT8"
        )
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [id_cv, doi_cv]}]
        )
        result = _extract_germplasm(entities, sources)
        assert result == {"germplasm_source_id": "ITA383", "germplasm_source_doi": "10.18730/YSFT8"}

    def test_returns_none_when_no_germplasm(self):
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": []}]
        )
        result = _extract_germplasm(entities, sources)
        assert result == {"germplasm_source_id": None, "germplasm_source_doi": None}


# ── _extract_origin_country ──────────────────────────────────────────────────


class TestExtractOriginCountry:
    def test_returns_country_when_present(self):
        cv = _make_cv(name="Origin Country", value="United States")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _extract_origin_country(entities, sources)
        assert result == "United States"

    def test_returns_none_when_not_present(self):
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": []}]
        )
        result = _extract_origin_country(entities, sources)
        assert result is None


# ── _extract_parameter_values ────────────────────────────────────────────────


class TestExtractParameterValues:
    def test_extracts_from_lab_process(self):
        pv = {"@id": "#PV1", "name": "sowing date", "value": "2024-03-15"}
        lp = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV1"}])
        graph = [lp]
        entities = {"#PV1": pv}
        result = _extract_parameter_values(entities, graph)
        assert result == {"sowing date": ["2024-03-15"]}

    def test_groups_multiple_values_same_name(self):
        pv1 = {"@id": "#PV1", "name": "nitrogen", "value": "100"}
        pv2 = {"@id": "#PV2", "name": "nitrogen", "value": "200"}
        lp = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV1"}, {"@id": "#PV2"}])
        graph = [lp]
        entities = {"#PV1": pv1, "#PV2": pv2}
        result = _extract_parameter_values(entities, graph)
        assert result == {"nitrogen": ["100", "200"]}

    def test_returns_empty_when_no_lab_process(self):
        graph = [{"@id": "#Other", "@type": "Dataset"}]
        entities = {}
        result = _extract_parameter_values(entities, graph)
        assert result == {}

    def test_skips_empty_name_or_value(self):
        pv = {"@id": "#PV1", "name": "", "value": "100"}
        lp = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV1"}])
        graph = [lp]
        entities = {"#PV1": pv}
        result = _extract_parameter_values(entities, graph)
        assert result == {}


# ── _extract_event_id_crops ──────────────────────────────────────────────────


class TestExtractEventIdCrops:
    def test_extracts_organism_from_source(self):
        cv = _make_cv(name="Organism", value="Beta vulgaris")
        src = _make_source("#S1", additional_property=[cv])
        graph = [src]
        entities = {"#S1": src}
        result = _extract_event_id_crops(entities, graph, current_crop=None)
        assert result == {"crop_species": "Beta vulgaris"}

    def test_does_not_override_existing_crop(self):
        cv = _make_cv(name="Organism", value="Beta vulgaris")
        src = _make_source("#S1", additional_property=[cv])
        graph = [src]
        entities = {"#S1": src}
        result = _extract_event_id_crops(entities, graph, current_crop="Triticum")
        assert result == {}

    def test_returns_empty_when_no_organism(self):
        src = _make_source("#S1", additional_property=[])
        graph = [src]
        entities = {"#S1": src}
        result = _extract_event_id_crops(entities, graph, current_crop=None)
        assert result == {}


# ── _resolve_license ─────────────────────────────────────────────────────────


class TestResolveLicense:
    def test_resolves_at_id_reference(self):
        investigation = {"license": {"@id": "#LICENSE"}}
        license_work = {"@id": "#LICENSE", "text": "CC-BY-4.0"}
        entities = {"#LICENSE": license_work}
        result = _resolve_license(investigation, entities)
        assert result == "CC-BY-4.0"

    def test_returns_none_when_no_at_id(self):
        investigation = {"license": "CC-BY-4.0"}
        result = _resolve_license(investigation, {})
        assert result is None

    def test_returns_none_when_no_investigation(self):
        result = _resolve_license(None, {})
        assert result is None

    def test_returns_none_when_ref_not_in_entities(self):
        investigation = {"license": {"@id": "#MISSING"}}
        result = _resolve_license(investigation, {})
        assert result is None


# ── _extract_investigation_meta ──────────────────────────────────────────────


class TestExtractInvestigationMeta:
    def test_extracts_contacts(self):
        contact = {
            "@id": "#C1",
            "name": "John Doe",
            "email": "john@example.com",
            "affiliation": {"name": "Uni Berlin"},
        }
        investigation = {"investigationContacts": [{"@id": "#C1"}]}
        entities = {"#C1": contact}
        result = _extract_investigation_meta(investigation, entities)
        assert result["investigation_contacts"] == [
            {"name": "John Doe", "email": "john@example.com", "affiliation": "Uni Berlin"}
        ]

    def test_extracts_publications(self):
        pub = {"@id": "#P1", "headline": "My Paper", "identifier": {"@id": "#DOI1"}}
        doi = {"@id": "#DOI1", "name": "10.1234/example"}
        investigation = {"investigationPublications": [{"@id": "#P1"}]}
        entities = {"#P1": pub, "#DOI1": doi}
        result = _extract_investigation_meta(investigation, entities)
        assert result["investigation_publications"] == [
            {"title": "My Paper", "identifier": "10.1234/example"}
        ]

    def test_extracts_citation(self):
        citation = {"@id": "#CITE1", "headline": "Citation Title", "identifier": {"@id": "#DOI2"}}
        doi = {"@id": "#DOI2", "name": "10.5678/cite"}
        investigation = {"citation": {"@id": "#CITE1"}}
        entities = {"#CITE1": citation, "#DOI2": doi}
        result = _extract_investigation_meta(investigation, entities)
        assert result["citation"] == {"title": "Citation Title", "identifier": "10.5678/cite"}

    def test_returns_empty_when_no_investigation(self):
        result = _extract_investigation_meta(None, {})
        assert result == {}

    def test_returns_empty_when_no_fields(self):
        investigation = {}
        result = _extract_investigation_meta(investigation, {})
        assert result == {}
