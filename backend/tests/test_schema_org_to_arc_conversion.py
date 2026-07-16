from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)


class TestSchemaOrgToARCConversion:
    """Test schema.org to ARC conversion functionality."""

    def test_schema_org_to_arc_conversion_basic(self):
        """Test basic schema.org JSON-LD to ARC conversion."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Test Dataset",
                "description": "A test dataset for FAIRagro-MI",
                "creator": [{"@type": "Person", "name": "John Doe"}],
                "identifier": "test-123",
                "datePublished": "2023-01-01",
                "license": "CC-BY-4.0",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test_dataset.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        assert "@context" in arc_data
        assert "@graph" in arc_data

        graph = arc_data["@graph"]
        entities = {e.get("@id"): e for e in graph if e.get("@id")}

        investigation = entities.get("./")
        assert investigation is not None
        assert investigation.get("name") is not None

    def test_schema_org_to_arc_conversion_with_field_mapping(self):
        """Test schema.org to ARC conversion with field mapping."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Genomics Dataset",
                "description": "A genomics research dataset",
                "creator": [{"@type": "Person", "name": "Jane Smith"}],
                "identifier": "genomics-456",
                "datePublished": "2023-02-15",
                "license": "MIT",
                "sequencing": "Illumina NovaSeq",
                "dna": ["hg38"],
                "genome": "Homo sapiens",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("genomics_dataset.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])

        investigation_entities = [e for e in graph if e.get("name") == "Genomics Dataset"]
        assert len(investigation_entities) > 0

    def test_schema_org_to_arc_conversion_plant_phenotyping(self):
        """Test schema.org to ARC conversion for plant phenotyping data."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Wheat Phenotyping Dataset",
                "description": "High-throughput wheat phenotyping data",
                "creator": [{"@type": "Organization", "name": "AgriTech Lab"}],
                "identifier": "wheat-pheno-789",
                "datePublished": "2023-03-20",
                "license": "CC-BY-SA-4.0",
                "crop_species": "Triticum aestivum",
                "crop_pest": "Fusarium graminearum",
                "organism": "Triticum aestivum",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("wheat_pheno.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])

        investigation_entities = [e for e in graph if e.get("name") == "Wheat Phenotyping Dataset"]
        assert len(investigation_entities) > 0

    def test_schema_org_to_arc_conversion_sensor_data(self):
        """Test schema.org to ARC conversion for sensor data."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Field Sensor Dataset",
                "description": "Environmental sensor measurements from field trials",
                "creator": [{"@type": "Person", "name": "Alex Chen"}],
                "identifier": "sensor-data-999",
                "datePublished": "2023-04-10",
                "license": "Apache-2.0",
                "measurementMethod": "NDVI analysis",
                "measurementTechnique": "UAV-based remote sensing",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("sensor_data.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])

        investigation_entities = [e for e in graph if e.get("name") == "Field Sensor Dataset"]
        assert len(investigation_entities) > 0

    def test_schema_org_to_arc_conversion_manual_template_selection(self):
        """Test schema.org to ARC conversion with manual template selection."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Manual Template Test",
                "description": "Testing manual template selection",
                "creator": [{"@type": "Person", "name": "Test User"}],
                "identifier": "manual-test-001",
                "datePublished": "2023-05-01",
                "license": "CC-BY-4.0",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("manual_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        assert "@context" in arc_data
        assert "@graph" in arc_data

    def test_schema_org_to_arc_conversion_with_preview(self):
        """Test schema.org to ARC conversion with preview mode."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Preview Test Dataset",
                "description": "Testing preview functionality",
                "creator": [{"@type": "Organization", "name": "Test Organization"}],
                "identifier": "preview-test-001",
                "datePublished": "2023-06-01",
                "license": "MIT",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("preview_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data
        assert "validation" in data

        validation = data["validation"]
        assert "valid" in validation or "errors" in validation

    def test_schema_org_to_arc_conversion_with_batch(self):
        """Test schema.org to ARC conversion with batch processing."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Batch Test Dataset",
                "description": "Testing batch processing",
                "creator": [{"@type": "Person", "name": "User"}],
                "identifier": "batch-test-1",
                "datePublished": "2023-07-01",
                "license": "CC-BY-4.0",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("batch_test1.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

    def test_schema_org_to_arc_conversion_field_extraction(self):
        """Test that schema.org fields are properly extracted during ARC conversion."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Field Extraction Test",
                "description": "Testing field extraction during conversion",
                "creator": [{"@type": "Person", "name": "Field Extraction User"}],
                "identifier": "field-extract-test-001",
                "datePublished": "2023-08-01",
                "license": "CC-BY-4.0",
                "keywords": ["test", "field", "extraction"],
                "url": "https://example.org/dataset",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("field_extract.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])

        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Field Extraction Test":
                investigation_found = True
                break

        assert investigation_found, "Dataset name should be preserved in ARC conversion"

    def test_schema_org_to_arc_conversion_missing_required_fields(self):
        """Test schema.org to ARC conversion with minimal data."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Minimal Dataset",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("minimal_dataset.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data
        assert "validation" in data

    def test_schema_org_to_arc_conversion_error_handling(self):
        """Test error handling in schema.org to ARC conversion."""
        # Invalid JSON returns 400 (format detection fails to detect schema.org)
        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("invalid.json", b"not json", "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_schema_org_to_arc_conversion_template_specific_mappings(self):
        """Test conversion with template-specific field mapping."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Template Specific Test",
                "description": "Testing template-specific field mapping",
                "creator": [{"@type": "Organization", "name": "Test Org"}],
                "identifier": "template-test-001",
                "datePublished": "2023-09-01",
                "license": "CC-BY-SA-4.0",
                "keywords": ["mapping", "test"],
                "publisher": "Test Publisher",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("template_mapping.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

        arc_data = data["preview"]
        assert "@graph" in arc_data

    def test_schema_org_to_arc_conversion_validation_completeness(self):
        """Test that ARC conversion validation is complete and accurate."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Validation Completeness Test",
                "description": "Testing validation completeness",
                "creator": [{"@type": "Person", "name": "Validation User"}],
                "identifier": "validation-complete-001",
                "datePublished": "2023-10-01",
                "license": "Apache-2.0",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("validation_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data
        assert "validation" in data

        validation = data["validation"]
        assert isinstance(validation, dict)

    def test_schema_org_to_arc_conversion_rich_input_validation_passes(self):
        """Test rich Schema.org input (maize-full) produces Assay with all required ARC fields."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "@id": "https://doi.org/10.5447/fairweaver/2024/maize-heat-001",
                "name": "Maize Heat Stress Transcriptome RNA-Seq Dataset",
                "description": "Transcriptome profiling of maize leaf tissue under heat stress",
                "creator": {
                    "@type": "Person",
                    "givenName": "Uwe",
                    "familyName": "Scholz",
                    "name": "Uwe Scholz",
                    "email": "scholz@ipk-gatersleben.de",
                    "affiliation": {"@type": "Organization", "name": "IPK Gatersleben"},
                },
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "datePublished": "2024-07-01",
                "measurementTechnique": "RNA-Seq transcriptomics",
                "instrument": {
                    "@type": "Thing",
                    "name": "Illumina NovaSeq 6000",
                    "additionalType": "SequencingPlatform",
                },
                "citation": {
                    "@type": "ScholarlyArticle",
                    "name": "Transcriptome analysis of heat-stressed maize",
                    "identifier": "https://doi.org/10.1234/fake-doi/maize-2024",
                },
                "funder": "BMBF",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("maize-full.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data
        assert "validation" in data

        # — Assay must have the 3 previously-missing fields —
        graph = data["preview"]["@graph"]
        assay = next((e for e in graph if e.get("additionalType") == "Assay"), {})
        assert assay.get("measurementMethod") == "RNA-Seq transcriptomics"
        assert assay.get("technologyType") == "SequencingPlatform"
        assert assay.get("technologyPlatform") == "Illumina NovaSeq 6000"

        # — Graph must include isa.investigation.xlsx entity —
        has_investigation_file = any(e.get("@id") == "isa.investigation.xlsx" for e in graph)
        assert has_investigation_file, "Graph must contain isa.investigation.xlsx entity"

        # — Validation must NOT mention these 4 specific errors —
        validation_errors = " ".join(data["validation"].get("errors", []))
        assert "measurementMethod" not in validation_errors
        assert "technologyType" not in validation_errors
        assert "technologyPlatform" not in validation_errors
        assert "isa.investigation.xlsx" not in validation_errors

    def test_measurementMethod_preserved_distinct_from_measurementTechnique(self):
        """Test that measurementMethod is preserved as a distinct value from measurementTechnique."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Measurement Test",
                "description": "Testing distinct measurementMethod",
                "creator": {"@type": "Person", "name": "Test User"},
                "identifier": "measure-test-001",
                "datePublished": "2023-01-01",
                "license": "CC-BY-4.0",
                "measurementTechnique": "Multispectral imaging",
                "measurementMethod": "NDVI calculation from red and near-infrared reflectance bands",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("measure_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        graph = data["preview"]["@graph"]
        assay = next((e for e in graph if e.get("additionalType") == "Assay"), {})

        assert (
            assay.get("measurementMethod")
            == "NDVI calculation from red and near-infrared reflectance bands"
        )
        assert assay.get("measurementTechnique") == "Multispectral imaging"
        assert assay["measurementMethod"] != assay["measurementTechnique"]

    def test_full_wheat_input_preserves_all_fields(self):
        """Test that full wheat input preserves crop, sensor, geo, soil, process fields."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Wheat Drought Phenotyping Field Trial 2024",
                "description": "Multi-temporal drone-based NDVI and multispectral imaging of winter wheat",
                "creator": {
                    "@type": "Person",
                    "givenName": "Timo",
                    "familyName": "Mühlhaus",
                    "name": "Timo Mühlhaus",
                    "email": "timo.muehlhaus@rptu.de",
                    "identifier": {
                        "@type": "PropertyValue",
                        "propertyID": "orcid",
                        "value": "0000-0003-3925-6778",
                    },
                    "affiliation": {
                        "@type": "Organization",
                        "name": "RPTU University of Kaiserslautern",
                    },
                },
                "identifier": "wheat-drought-001",
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "datePublished": "2024-09-15",
                "keywords": ["wheat", "drought stress", "NDVI", "phenotyping", "field trial"],
                "measurementTechnique": "Multispectral imaging",
                "measurementMethod": "NDVI calculation from red and near-infrared reflectance bands",
                "instrument": {
                    "@type": "Sensor",
                    "name": "Micasense RedEdge-MX",
                    "description": "Multispectral sensor on DJI Matrice 300 RTK UAV",
                },
                "about": {
                    "@type": "Thing",
                    "name": "Triticum aestivum",
                    "sameAs": "http://purl.obolibrary.org/obo/NCBITaxon_4565",
                },
                "crop_pest": "Zymoseptoria tritici",
                "crop_pest_uri": "http://purl.obolibrary.org/obo/NCBITaxon_5284",
                "funder": "DFG – German Research Foundation",
                "citation": {
                    "@type": "ScholarlyArticle",
                    "name": "Multi-temporal UAV-based phenotyping of winter wheat under drought stress",
                    "identifier": "https://doi.org/10.1234/fake-doi/wheat-2024",
                },
                "location": {
                    "@type": "Place",
                    "name": "RPTU Field Station Kaiserslautern",
                    "geo": {"@type": "GeoCoordinates", "latitude": 49.4401, "longitude": 7.7491},
                },
                "country": "Germany",
                "state": "Rhineland-Palatinate",
                "county": "Kaiserslautern",
                "soilType": "Luvisol",
                "processType": "UAV-based remote sensing",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("full_wheat.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        graph = data["preview"]["@graph"]
        entities_by_id = {e.get("@id"): e for e in graph if e.get("@id")}
        root = entities_by_id.get("./", {})

        # Investigation-level fields
        assert root.get("license") == "https://creativecommons.org/licenses/by/4.0/"
        assert root.get("datePublished") == "2024-09-15"
        assert "wheat" in root.get("keywords", [])
        assert "DFG" in root.get("funder", "")
        assert root.get("investigationContacts") is not None
        assert root.get("investigationPublications") is not None

        # Location/geo entities
        assert any(e.get("additionalType") == "SoilType" for e in graph)
        assert any(e.get("additionalType") == "Process" for e in graph)
        assert any(e.get("@type") == "Place" for e in graph)
        assert any(e.get("@type") == "DefinedRegion" for e in graph)

        # Study-level fields
        study = next((e for e in graph if e.get("additionalType") == "Study"), {})
        assert "wheat" in study.get("studyDesignDescriptors", [])
        assert study.get("crop_species") == "Triticum aestivum"

        # Assay-level fields
        assay = next((e for e in graph if e.get("additionalType") == "Assay"), {})
        assert (
            assay.get("measurementMethod")
            == "NDVI calculation from red and near-infrared reflectance bands"
        )
        assert assay.get("measurementTechnique") == "Multispectral imaging"

        # Hierarchy links
        assert any(p.get("@id") == study.get("@id") for p in root.get("hasPart", []))
        assert any(p.get("@id") == assay.get("@id") for p in study.get("hasPart", []))

    def test_license_and_datePublished_preserved(self):
        """Test that license URL and datePublished are preserved (not corrupted)."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "License Test",
                "description": "Testing license and date preservation",
                "creator": {"@type": "Person", "name": "Test User"},
                "identifier": "license-test-001",
                "datePublished": "2024-09-15",
                "license": "https://creativecommons.org/licenses/by/4.0/",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("license_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        graph = data["preview"]["@graph"]
        root = next((e for e in graph if e.get("@id") == "./"), {})

        assert root.get("license") == "https://creativecommons.org/licenses/by/4.0/"
        assert root.get("datePublished") == "2024-09-15"

    def test_schema_org_plugin_loader_extracts_all_fields(self):
        """Test that schema_org_plugin.load() extracts expanded field set."""
        from formats.schema_org_plugin import load

        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Full Test",
                "description": "Test all loader fields",
                "creator": [{"@type": "Person", "name": "User"}],
                "identifier": "full-test-001",
                "datePublished": "2024-01-01",
                "license": "CC-BY-4.0",
                "keywords": ["test", "data"],
                "alternateName": "ALT-001",
                "funder": "DFG",
                "citation": {"name": "Paper", "identifier": "doi:10.1234/test"},
                "measurementTechnique": "UAV imaging",
                "measurementMethod": "NDVI",
                "technologyType": "Multispectral sensor",
                "technologyPlatform": "DJI Matrice 300",
                "instrument": {"name": "RedEdge-MX"},
                "crop_species": "Triticum aestivum",
                "crop_pest": "Fusarium",
                "location": {"geo": {"latitude": 49.44, "longitude": 7.75}},
                "country": "Germany",
                "state": "RP",
                "county": "KL",
                "soilType": "Luvisol",
                "processType": "UAV sensing",
                "about": {"name": "Wheat"},
            }
        )

        result = load(content)

        # Core fields
        assert result["name"] == "Full Test"
        assert result["identifier"] == "full-test-001"

        # Investigation-level
        assert result["alternateName"] == "ALT-001"
        assert result["funder"] == "DFG"
        assert result["citation"]["name"] == "Paper"

        # Study-level
        assert result["crop_species"] == "Triticum aestivum"
        assert result["crop_pest"] == "Fusarium"

        # Assay-level
        assert result["measurementTechnique"] == "UAV imaging"
        assert result["measurementMethod"] == "NDVI"
        assert result["technologyType"] == "Multispectral sensor"
        assert result["technologyPlatform"] == "DJI Matrice 300"
        assert result["instrument"]["name"] == "RedEdge-MX"

        # Geographic
        assert result["location"]["geo"]["latitude"] == 49.44
        assert result["geo_country"] == "Germany"
        assert result["geo_state"] == "RP"
        assert result["geo_county"] == "KL"

        # Soil / Process
        assert result["soilType"] == "Luvisol"
        assert result["processType"] == "UAV sensing"

        # About (crop)
        assert result["about"]["name"] == "Wheat"
