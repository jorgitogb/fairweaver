"""Unit tests for RO-Crate MIAPPE extraction helpers.

Tests the standalone _extract_* functions and graph helpers in ro_crate_plugin.py.
These functions are called by load() but tested independently for precision.
"""

from __future__ import annotations

from formats.ro_crate_plugin import (
    _cv_value_by_name,
    _cv_value_by_property_id,
    _extract_crop_characteristics,
    _extract_drone_location_params,
    _extract_event_id_crops,
    _extract_geographic_coverage,
    _extract_geolocation,
    _extract_investigation_meta,
    _extract_origin_country,
    _extract_parameter_values,
    _extract_process_types,
    _extract_soil_depths,
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


# ── _extract_geographic_coverage ───────────────────────────────────────────


class TestExtractGeographicCoverage:
    def test_extracts_country_state_county(self):
        country_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/bco_country",
            name="Country",
            value="Germany",
        )
        state_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/bco_stateProvince",
            name="State Province",
            value="Land Brandenburg",
        )
        county_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/bco_county",
            name="County",
            value="Landkreis Markisch-Oderland",
        )
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [country_cv, state_cv, county_cv]}]
        )
        result = _extract_geographic_coverage(entities, sources)
        assert result == {
            "geo_country": "Germany",
            "geo_state": "Land Brandenburg",
            "geo_county": "Landkreis Markisch-Oderland",
        }

    def test_returns_none_when_no_cv(self):
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": []}]
        )
        result = _extract_geographic_coverage(entities, sources)
        assert result == {"geo_country": None, "geo_state": None, "geo_county": None}

    def test_partial_extraction(self):
        country_cv = _make_cv(
            property_id="http://purl.obolibrary.org/obo/bco_country",
            name="Country",
            value="Germany",
        )
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [country_cv]}]
        )
        result = _extract_geographic_coverage(entities, sources)
        assert result["geo_country"] == "Germany"
        assert result["geo_state"] is None
        assert result["geo_county"] is None


# ── _extract_drone_location_params ──────────────────────────────────────────


class TestExtractDroneLocationParams:
    def test_extracts_longitude_latitude_datetime(self):
        lp = _make_lab_process(
            "#LP1",
            parameter_value_refs=[
                {"@id": "#PV_Lng"},
                {"@id": "#PV_Lat"},
                {"@id": "#PV_DT"},
            ],
        )
        entities = {
            "#LP1": lp,
            "#PV_Lng": _make_cv(name="Longitude", value="14.121", cv_id="#PV_Lng"),
            "#PV_Lat": _make_cv(name="Latitude", value="52.516", cv_id="#PV_Lat"),
            "#PV_DT": _make_cv(name="Date and Time", value="2025-03-15T10:30:00", cv_id="#PV_DT"),
        }
        result = _extract_drone_location_params(entities, [lp])
        assert result == {
            "drone_longitude": "14.121",
            "drone_latitude": "52.516",
            "drone_datetime": "2025-03-15T10:30:00",
        }

    def test_returns_none_when_no_params(self):
        lp = _make_lab_process("#LP1")
        entities = {"#LP1": lp}
        result = _extract_drone_location_params(entities, [lp])
        assert result == {"drone_longitude": None, "drone_latitude": None, "drone_datetime": None}

    def test_partial_extraction(self):
        lp = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV_Lng"}])
        entities = {
            "#LP1": lp,
            "#PV_Lng": _make_cv(name="Longitude", value="14.121", cv_id="#PV_Lng"),
        }
        result = _extract_drone_location_params(entities, [lp])
        assert result["drone_longitude"] == "14.121"
        assert result["drone_latitude"] is None
        assert result["drone_datetime"] is None

    def test_skips_empty_values(self):
        lp = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV_Empty"}])
        entities = {
            "#LP1": lp,
            "#PV_Empty": _make_cv(name="Longitude", value="", cv_id="#PV_Empty"),
        }
        result = _extract_drone_location_params(entities, [lp])
        assert result["drone_longitude"] is None

    def test_first_match_wins(self):
        lp1 = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV1"}])
        lp2 = _make_lab_process("#LP2", parameter_value_refs=[{"@id": "#PV2"}])
        entities = {
            "#LP1": lp1,
            "#LP2": lp2,
            "#PV1": _make_cv(name="Longitude", value="14.1", cv_id="#PV1"),
            "#PV2": _make_cv(name="Longitude", value="14.2", cv_id="#PV2"),
        }
        result = _extract_drone_location_params(entities, [lp1, lp2])
        assert result["drone_longitude"] == "14.1"


# ── Material type support ──────────────────────────────────────────────────


class TestMaterialTypeSupport:
    def test_material_with_additional_type_matches_sample(self):
        """Entity with @type=Sample + additionalType=Material should match Sample check."""
        mat = {
            "@id": "#Mat1",
            "@type": "Sample",
            "additionalType": "Material",
            "additionalProperty": [],
        }
        from formats.ro_crate_plugin import _has_type

        assert _has_type(mat, "Sample")

    def test_material_only_additional_type_matches_material(self):
        """Entity with only additionalType=Material should match Material check."""
        mat = {"@id": "#Mat1", "additionalType": "Material", "additionalProperty": []}
        from formats.ro_crate_plugin import _has_type

        assert _has_type(mat, "Material")

    def test_material_only_does_not_match_sample(self):
        """Entity with only additionalType=Material should NOT match Sample check."""
        mat = {"@id": "#Mat1", "additionalType": "Material", "additionalProperty": []}
        from formats.ro_crate_plugin import _has_type

        assert not _has_type(mat, "Sample")


# ── Infection Label extraction (integrated into crop block) ────────────────


class TestInfectionLabelExtraction:
    def test_extract_infection_label_from_material(self):
        """Infection Label CharacteristicValue should be extractable by name."""
        from formats.ro_crate_plugin import _cv_value_by_name

        cv = _make_cv(name="Infection Label", value="PVY_positiv")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [cv]}]
        )
        result = _cv_value_by_name(sources, entities, "Infection Label")
        assert result == "PVY_positiv"


# ── Subject default ────────────────────────────────────────────────────────


class TestSubjectDefault:
    def test_always_has_subject_in_output(self):
        """_extract_fields should always set subject='Agricultural Sciences'."""
        from formats.ro_crate_plugin import _extract_fields

        result = _extract_fields(
            graph=[],
            entities={},
            investigation=None,
            studies=[],
            assays=[],
            validate_fairagro=False,
        )
        assert result.get("subject") == "Agricultural Sciences"


# ── Keywords extraction ────────────────────────────────────────────────────


class TestKeywordsExtraction:
    def test_extracts_keywords_from_investigation(self):
        from formats.ro_crate_plugin import _extract_fields

        investigation = {
            "@id": "./",
            "@type": "Dataset",
            "additionalType": "Investigation",
            "keywords": ["wheat", "drought tolerance", "phenotyping"],
        }
        result = _extract_fields(
            graph=[investigation],
            entities={"./": investigation},
            investigation=investigation,
            studies=[],
            assays=[],
            validate_fairagro=False,
        )
        assert result.get("keywords") == ["wheat", "drought tolerance", "phenotyping"]

    def test_returns_empty_list_when_no_keywords(self):
        from formats.ro_crate_plugin import _extract_fields

        investigation = {"@id": "./", "name": "Test"}
        result = _extract_fields(
            graph=[],
            entities={},
            investigation=investigation,
            studies=[],
            assays=[],
            validate_fairagro=False,
        )
        assert result.get("keywords") == []


# ── _extract_soil_depths ──────────────────────────────────────────────────


class TestExtractSoilDepths:
    def test_extracts_distinct_depth_pairs(self):
        lp1 = _make_lab_process(
            "#LP1",
            parameter_value_refs=[{"@id": "#PV_Top1"}, {"@id": "#PV_Bot1"}],
        )
        lp1["executesLabProtocol"] = {"@id": "#Protocol_Events-SoilSampling"}
        entities = {
            "#LP1": lp1,
            "#PV_Top1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105225", value="0", cv_id="#PV_Top1"
            ),
            "#PV_Bot1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105226", value="30", cv_id="#PV_Bot1"
            ),
        }
        graph = [lp1]
        result = _extract_soil_depths(entities, graph)
        assert result == [{"top": "0", "bottom": "30"}]

    def test_deduplicates_same_pair(self):
        lp1 = _make_lab_process(
            "#LP1", parameter_value_refs=[{"@id": "#PV_Top1"}, {"@id": "#PV_Bot1"}]
        )
        lp1["executesLabProtocol"] = {"@id": "#Protocol_Events-SoilSampling"}
        lp2 = _make_lab_process(
            "#LP2", parameter_value_refs=[{"@id": "#PV_Top2"}, {"@id": "#PV_Bot2"}]
        )
        lp2["executesLabProtocol"] = {"@id": "#Protocol_Events-SoilSampling"}
        entities = {
            "#LP1": lp1,
            "#LP2": lp2,
            "#PV_Top1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105225", value="0", cv_id="#PV_Top1"
            ),
            "#PV_Bot1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105226", value="30", cv_id="#PV_Bot1"
            ),
            "#PV_Top2": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105225", value="0", cv_id="#PV_Top2"
            ),
            "#PV_Bot2": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105226", value="30", cv_id="#PV_Bot2"
            ),
        }
        result = _extract_soil_depths(entities, [lp1, lp2])
        assert len(result) == 1

    def test_collects_multiple_distinct_pairs(self):
        lp1 = _make_lab_process(
            "#LP1", parameter_value_refs=[{"@id": "#PV_Top1"}, {"@id": "#PV_Bot1"}]
        )
        lp1["executesLabProtocol"] = {"@id": "#Protocol_Events-SoilSampling"}
        lp2 = _make_lab_process(
            "#LP2", parameter_value_refs=[{"@id": "#PV_Top2"}, {"@id": "#PV_Bot2"}]
        )
        lp2["executesLabProtocol"] = {"@id": "#Protocol_Events-SoilSampling"}
        entities = {
            "#LP1": lp1,
            "#LP2": lp2,
            "#PV_Top1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105225", value="0", cv_id="#PV_Top1"
            ),
            "#PV_Bot1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105226", value="30", cv_id="#PV_Bot1"
            ),
            "#PV_Top2": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105225", value="30", cv_id="#PV_Top2"
            ),
            "#PV_Bot2": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105226", value="60", cv_id="#PV_Bot2"
            ),
        }
        result = _extract_soil_depths(entities, [lp1, lp2])
        assert len(result) == 2

    def test_skips_non_soil_sampling_processes(self):
        lp = _make_lab_process("#LP1", parameter_value_refs=[{"@id": "#PV1"}])
        lp["executesLabProtocol"] = {"@id": "#Protocol_Events-Tillage"}
        entities = {
            "#LP1": lp,
            "#PV1": _make_cv(
                property_id="https://bioregistry.io/ENVO:06105225", value="0", cv_id="#PV1"
            ),
        }
        result = _extract_soil_depths(entities, [lp])
        assert result == []

    def test_returns_empty_when_no_processes(self):
        result = _extract_soil_depths({}, [])
        assert result == []


# ── _extract_process_types ─────────────────────────────────────────────────


class TestExtractProcessTypes:
    def test_extracts_distinct_process_names(self):
        lp1 = {
            "@id": "#LP1",
            "@type": "LabProcess",
            "executesLabProtocol": {"@id": "#Protocol_Events-Tillage"},
        }
        lp2 = {
            "@id": "#LP2",
            "@type": "LabProcess",
            "executesLabProtocol": {"@id": "#Protocol_Events-Planting"},
        }
        lp3 = {
            "@id": "#LP3",
            "@type": "LabProcess",
            "executesLabProtocol": {"@id": "#Protocol_Events-Harvest"},
        }
        result = _extract_process_types({}, [lp1, lp2, lp3])
        assert sorted(result) == ["Harvest", "Planting", "Tillage"]

    def test_deduplicates_same_process(self):
        lp1 = {
            "@id": "#LP1",
            "@type": "LabProcess",
            "executesLabProtocol": {"@id": "#Protocol_Events-Tillage"},
        }
        lp2 = {
            "@id": "#LP2",
            "@type": "LabProcess",
            "executesLabProtocol": {"@id": "#Protocol_Events-Tillage"},
        }
        result = _extract_process_types({}, [lp1, lp2])
        assert result == ["Tillage"]

    def test_skips_unknown_protocols(self):
        lp = {
            "@id": "#LP1",
            "@type": "LabProcess",
            "executesLabProtocol": {"@id": "#Protocol_Materials-BiologicalMaterial"},
        }
        result = _extract_process_types({}, [lp])
        assert result == []

    def test_skips_non_lab_process_entities(self):
        src = {"@id": "#S1", "@type": "Source"}
        result = _extract_process_types({}, [src])
        assert result == []

    def test_returns_empty_when_no_graph(self):
        result = _extract_process_types({}, [])
        assert result == []

    def test_handles_string_protocol_id(self):
        lp = {
            "@id": "#LP1",
            "@type": "LabProcess",
            "executesLabProtocol": "#Protocol_Events-Irrigation",
        }
        result = _extract_process_types({}, [lp])
        assert result == ["Irrigation"]


# ── _extract_crop_characteristics ──────────────────────────────────────────


class TestExtractCropCharacteristics:
    def test_extracts_grain_weight_icc_code_variety(self):
        grain_cv = _make_cv(name="1000-grain dry weight", value="45.2")
        icc_cv = _make_cv(name="ICC code", value="12345")
        variety_cv = _make_cv(name="Infraspecific name", value="Absolut")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [grain_cv, icc_cv, variety_cv]}]
        )
        result = _extract_crop_characteristics(entities, sources)
        assert result == {
            "crop_grain_weight": "45.2",
            "crop_icc_code": "12345",
            "crop_variety": "Absolut",
        }

    def test_returns_none_when_no_cv(self):
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": []}]
        )
        result = _extract_crop_characteristics(entities, sources)
        assert result == {
            "crop_grain_weight": None,
            "crop_icc_code": None,
            "crop_variety": None,
        }

    def test_partial_extraction(self):
        grain_cv = _make_cv(name="1000-grain dry weight", value="45.2")
        entities, sources = _build_entities_and_sources(
            [{"source_id": "#S1", "additionalProperty": [grain_cv]}]
        )
        result = _extract_crop_characteristics(entities, sources)
        assert result["crop_grain_weight"] == "45.2"
        assert result["crop_icc_code"] is None
        assert result["crop_variety"] is None
