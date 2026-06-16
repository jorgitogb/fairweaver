from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestArcToAgrischemasConversion:
    """Test ARC RO-Crate to AgroSchemas pivot conversion."""

    def _load_arc(self, filename: str) -> bytes:
        with open(f"../sample-data/demo/{filename}") as f:
            return f.read().encode()

    def test_fieldtrial_conversion_full(self):
        """ARC full → fieldtrial: all required fields mapped."""
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_fieldtrial",
            files={"file": ("wheat.json", content, "application/json")},
        )
        assert resp.status_code == 200
        data = resp.json()
        output = data["output"]
        assert output["identifier"] == "10.5447/fairweaver/2024/wheat-drought-001"
        assert output["title"] == "Wheat Drought Phenotyping Field Trial 2024"
        assert "Triticum aestivum" in output["description"]
        assert output["startDate"] == "2024-09-15"
        assert output["crop"] == "Triticum aestivum"
        assert output["license"] == "https://creativecommons.org/licenses/by/4.0/"

    def test_fieldtrial_missing_location(self):
        """Fieldtrial: location correctly reported as missing."""
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_fieldtrial",
            files={"file": ("wheat.json", content, "application/json")},
        )
        data = resp.json()
        missing = [f["field"] for f in data["missing_fields"]]
        assert "location" in missing

    def test_fieldtrial_conversion_basic(self):
        """ARC basic → fieldtrial: fewer fields mapped, more missing."""
        content = self._load_arc("arc-ro-crate-wheat-basic.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_fieldtrial",
            files={"file": ("wheat.json", content, "application/json")},
        )
        assert resp.status_code == 200
        data = resp.json()
        output = data["output"]
        assert output.get("title") is not None
        # Basic level has no crop data → crop is missing
        missing = [f["field"] for f in data["missing_fields"]]
        assert "crop" in missing

    def test_cropvariety_conversion(self):
        """ARC full → cropvariety: required fields mapped."""
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_cropvariety",
            files={"file": ("wheat.json", content, "application/json")},
        )
        assert resp.status_code == 200
        data = resp.json()
        output = data["output"]
        assert output["crop"] == "Triticum aestivum"
        assert output["identifier"] == "10.5447/fairweaver/2024/wheat-drought-001"
        assert output["name"] == "Wheat Drought Phenotyping Field Trial 2024"

    def test_cropvariety_missing_optional_fields(self):
        """Cropvariety: optional fields like variety, registrationYear missing."""
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_cropvariety",
            files={"file": ("wheat.json", content, "application/json")},
        )
        data = resp.json()
        missing = [f["field"] for f in data["missing_fields"]]
        assert "variety" in missing
        assert "registrationYear" in missing
        assert "countryOfOrigin" in missing

    def test_maize_theme(self):
        """ARC maize → fieldtrial: different theme data mapped correctly."""
        content = self._load_arc("arc-ro-crate-maize-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_fieldtrial",
            files={"file": ("maize.json", content, "application/json")},
        )
        assert resp.status_code == 200
        data = resp.json()
        output = data["output"]
        assert output["crop"] == "Zea mays"
        assert "Maize Heat Stress" in output["title"]

    def test_confidence_score(self):
        """Confidence score > 0 when fields are mapped."""
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_fieldtrial",
            files={"file": ("wheat.json", content, "application/json")},
        )
        data = resp.json()
        assert data["confidence"] > 0.5

    def test_mapping_source_cached(self):
        """Mapping loaded from cache (YAML file exists)."""
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        resp = client.post(
            "/convert?source_format=ro_crate&pivot_id=agrischemas_fieldtrial",
            files={"file": ("wheat.json", content, "application/json")},
        )
        data = resp.json()
        assert data["mapping_source"] == "cached"

    def test_fallback_extract_crop_from_study(self):
        """Plugin extracts crop_species directly from Study entities."""
        from formats.ro_crate_plugin import load as ro_crate_load
        content = self._load_arc("arc-ro-crate-wheat-full.json")
        parsed = ro_crate_load(content, validate_fairagro=False)
        assert parsed["crop_species"] == "Triticum aestivum"
        assert parsed["crop_pest"] == "Zymoseptoria tritici"
        assert parsed["crop_species_uri"] == "http://purl.obolibrary.org/obo/NCBITaxon_4565"
