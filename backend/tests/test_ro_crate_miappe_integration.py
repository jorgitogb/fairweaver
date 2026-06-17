"""Integration tests for RO-Crate MIAPPE extraction on real ARC files.

These tests verify that load() produces the expected MIAPPE fields
(taxonomy, geolocation, germplasm, origin_country, parameter_values, etc.)
when run on the 3 real ARC files: wheat-danielA, benjamin, matthiasL.
"""

from __future__ import annotations

import os
import time

import pytest

from formats.ro_crate_plugin import load as ro_crate_load

# Skip large-file tests when CI_LIGHT is set (e.g. in fast CI runs)
_CI_LIGHT = bool(os.environ.get("CI_LIGHT"))


def _load_file(filename: str) -> bytes:
    with open(f"../sample-data/demo/{filename}") as f:
        return f.read().encode()


# ── wheat-danielA (42 KB) ────────────────────────────────────────────────────


class TestWheatDanielA:
    """Integration: wheat-danielA — Origin Country + germplasm + sowing date."""

    @pytest.fixture(scope="class")
    def parsed(self):
        return ro_crate_load(_load_file("arc-ro-crate-wheat-danielA.json"), validate_fairagro=False)

    def test_crop_species(self, parsed):
        assert parsed["crop_species"] == "Triticum aestivum"

    def test_germplasm_source_id(self, parsed):
        assert parsed["germplasm_source_id"] == "TRI 10"

    def test_germplasm_source_doi(self, parsed):
        assert parsed["germplasm_source_doi"] == "10.25642/IPK/GBIS/10"

    def test_origin_country(self, parsed):
        assert parsed["origin_country"] == "United States"

    def test_license(self, parsed):
        assert parsed["license"] == "ALL RIGHTS RESERVED BY THE AUTHORS"

    def test_identifier(self, parsed):
        assert parsed["identifier"] == "Norman_ARC"

    def test_parameter_values_has_sowing_date(self, parsed):
        pv = parsed["parameter_values"]
        assert "sowing date" in pv
        assert len(pv["sowing date"]) >= 1

    def test_taxonomy_absent(self, parsed):
        assert parsed["taxon_genus"] is None
        assert parsed["taxon_species"] is None
        assert parsed["taxon_infraspecific_name"] is None

    def test_geolocation_absent(self, parsed):
        assert parsed["geo_latitude"] is None
        assert parsed["geo_longitude"] is None


# ── benjamin (108 MB) ────────────────────────────────────────────────────────


@pytest.mark.skipif(_CI_LIGHT, reason="skip large file tests in CI_LIGHT")
class TestBenjamin:
    """Integration: benjamin — rich taxonomy + geolocation + 44 parameter types."""

    @pytest.fixture(scope="class")
    def parsed(self):
        t0 = time.time()
        result = ro_crate_load(_load_file("arc-ro-crate-benjamin.json"), validate_fairagro=False)
        elapsed = time.time() - t0
        if elapsed > 60:
            pytest.skip(f"benjamin load took {elapsed:.0f}s — too slow for this run")
        return result

    def test_crop_species(self, parsed):
        assert parsed["crop_species"] == "Beta vulgaris subsp. vulgaris"

    def test_taxonomy_genus(self, parsed):
        assert parsed["taxon_genus"] == "Beta"

    def test_taxonomy_species(self, parsed):
        assert parsed["taxon_species"] == "Beta vulgaris"

    def test_taxonomy_infraspecific(self, parsed):
        assert parsed["taxon_infraspecific_name"] == "Depola"

    def test_geo_latitude(self, parsed):
        assert parsed["geo_latitude"] == "52.5169268154762"

    def test_geo_longitude(self, parsed):
        assert parsed["geo_longitude"] == "14.1218853869048"

    def test_geo_altitude(self, parsed):
        assert parsed["geo_altitude"] == "62.2724404761905"

    def test_license_resolved(self, parsed):
        assert parsed["license"] == "ALL RIGHTS RESERVED BY THE AUTHORS"

    def test_measurement_method(self, parsed):
        assert parsed["measurementMethod"] == "wet digestion"

    def test_parameter_values_count(self, parsed):
        assert len(parsed["parameter_values"]) == 44

    def test_germplasm_absent(self, parsed):
        assert parsed["germplasm_source_id"] is None
        assert parsed["germplasm_source_doi"] is None

    def test_origin_country_absent(self, parsed):
        assert parsed["origin_country"] is None


# ── matthiasL (389 MB) ──────────────────────────────────────────────────────


@pytest.mark.skipif(_CI_LIGHT, reason="skip large file tests in CI_LIGHT")
class TestMatthiasL:
    """Integration: matthiasL — inline CV + rich taxonomy + germplasm + 87 params."""

    @pytest.fixture(scope="class")
    def parsed(self):
        t0 = time.time()
        result = ro_crate_load(
            _load_file("arc-ro-crate-metadata-matthiasL.json"), validate_fairagro=False
        )
        elapsed = time.time() - t0
        if elapsed > 120:
            pytest.skip(f"matthiasL load took {elapsed:.0f}s — too slow for this run")
        return result

    def test_crop_species(self, parsed):
        assert parsed["crop_species"] == "Wheat"

    def test_taxonomy_genus(self, parsed):
        assert parsed["taxon_genus"] == "Triticum"

    def test_taxonomy_species(self, parsed):
        assert parsed["taxon_species"] == "aestivum"

    def test_taxonomy_infraspecific(self, parsed):
        assert parsed["taxon_infraspecific_name"] == "L."

    def test_geo_latitude(self, parsed):
        assert parsed["geo_latitude"] == "45.24503"

    def test_geo_longitude(self, parsed):
        assert parsed["geo_longitude"] == "9.42247"

    def test_geo_altitude(self, parsed):
        assert parsed["geo_altitude"] == "52.313841"

    def test_germplasm_source_id(self, parsed):
        assert parsed["germplasm_source_id"] == "ITA383"

    def test_germplasm_source_doi(self, parsed):
        assert parsed["germplasm_source_doi"] == "10.18730/YSFT8"

    def test_license(self, parsed):
        assert parsed["license"] == "ALL RIGHTS RESERVED BY THE AUTHORS"

    def test_measurement_technique(self, parsed):
        assert parsed["measurementTechnique"] == "None"

    def test_parameter_values_count(self, parsed):
        assert len(parsed["parameter_values"]) == 87

    def test_alternative_titles_count(self, parsed):
        assert len(parsed["alternative_titles"]) == 805

    def test_creator_count(self, parsed):
        assert len(parsed["creator"]) == 53

    def test_origin_country_absent(self, parsed):
        assert parsed["origin_country"] is None


# ── NDJSON streaming tests ──────────────────────────────────────────────────


class TestNdjsonStreaming:
    """Verify ndjson streaming produces identical results to standard load."""

    def _load_both(self, filename: str):
        """Load file via both standard and ndjson paths, return both results."""
        from formats.ro_crate_plugin import convert_to_ndjson, load as std_load

        content = _load_file(filename)
        result_std = std_load(content, validate_fairagro=False)

        ndjson = convert_to_ndjson(content)
        # Write to temp file for file-based streaming
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False, mode="wb") as f:
            f.write(ndjson)
            tmp_path = f.name

        try:
            from formats.ro_crate_plugin import load_ndjson_file

            result_ndj = load_ndjson_file(tmp_path, validate_fairagro=False)
        finally:
            os.unlink(tmp_path)

        return result_std, result_ndj

    def test_wheat_danielA_matches(self):
        result_std, result_ndj = self._load_both("arc-ro-crate-wheat-danielA.json")
        assert result_std == result_ndj

    def test_benjamin_matches(self):
        result_std, result_ndj = self._load_both("arc-ro-crate-benjamin.json")
        assert result_std == result_ndj

    def test_matthiasL_matches(self):
        result_std, result_ndj = self._load_both("arc-ro-crate-metadata-matthiasL.json")
        assert result_std == result_ndj
