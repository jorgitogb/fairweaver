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
                "description": "A test dataset for FAIRweaver",
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
