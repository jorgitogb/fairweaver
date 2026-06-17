from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)


class TestLivePreview:
    """Test live preview functionality for ARC conversion."""

    def test_live_preview_schema_org_conversion(self):
        """Test live preview for schema.org to ARC conversion."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Live Preview Test Dataset",
                "description": "Testing live preview functionality",
                "creator": [{"@type": "Person", "name": "Live Preview User"}],
                "identifier": "live-preview-test-001",
                "datePublished": "2023-01-01",
                "license": "CC-BY-4.0",
                "keywords": ["live", "preview", "testing"],
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("live_preview_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        assert "validation" in data

        preview = data["preview"]
        assert "@context" in preview
        assert "@graph" in preview

        graph = preview["@graph"]
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Live Preview Test Dataset":
                investigation_found = True
                break

        assert investigation_found

    def test_live_preview_template_specific_data(self):
        """Test live preview with template-specific data."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Template-Specific Preview",
                "description": "Testing template-specific live preview",
                "creator": [{"@type": "Organization", "name": "Template Org"}],
                "identifier": "template-specific-001",
                "datePublished": "2023-02-01",
                "license": "MIT",
                "keywords": ["template", "specific"],
                "publisher": "Test Publisher",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={
                "file": ("template_specific_preview.json", content.encode(), "application/json")
            },
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        preview = data["preview"]
        assert "@graph" in preview

        assert "validation" in data
        validation = data["validation"]
        assert "valid" in validation or "errors" in validation

    def test_live_preview_with_validation_errors(self):
        """Test live preview with validation errors."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Validation Error Test",
                "creator": [{"@type": "Person", "name": "Error User"}],
                "identifier": "validation-error-001",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("validation_error_preview.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        assert "validation" in data

        preview = data["preview"]
        assert "@graph" in preview

    def test_live_preview_file_download(self):
        """Test live preview vs file download functionality."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "File Download Test",
                "description": "Testing preview vs download",
                "creator": [{"@type": "Person", "name": "Download User"}],
                "identifier": "download-test-001",
                "datePublished": "2023-03-01",
                "license": "CC-BY-4.0",
            }
        )

        preview_resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("download_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert preview_resp.status_code == 200
        preview_data = preview_resp.json()
        assert "preview" in preview_data
        assert "validation" in preview_data

        download_resp = client.post(
            "/convert/arc-export",
            files={"file": ("download_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert download_resp.status_code == 200
        assert "content-disposition" in download_resp.headers
        assert "attachment" in download_resp.headers["content-disposition"]

    def test_live_preview_template_auto_selection(self):
        """Test live preview with auto template selection."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Auto-Selected Template Preview",
                "description": "Testing auto template selection",
                "creator": [{"@type": "Person", "name": "Auto Select User"}],
                "identifier": "auto-select-001",
                "datePublished": "2023-04-01",
                "license": "CC-BY-4.0",
                "crop_species": "Sorghum bicolor",
                "crop_pest": "Stem borer",
                "organism": "Sorghum bicolor",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("auto_select_preview.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        preview = data["preview"]
        assert "@graph" in preview

        investigation_found = False
        for entity in preview["@graph"]:
            if entity.get("name") == "Auto-Selected Template Preview":
                investigation_found = True
                break

        assert investigation_found

        assert "validation" in data

    def test_live_preview_multiple_files_batch(self):
        """Test live preview with multiple files in batch."""
        content1 = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Batch Preview Dataset 1",
                "description": "First dataset in batch preview",
                "creator": [{"@type": "Person", "name": "Batch User 1"}],
                "identifier": "batch-preview-001",
                "datePublished": "2023-05-01",
                "license": "CC-BY-4.0",
            }
        )

        resp1 = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("batch_preview_1.json", content1.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp1.status_code == 200
        data1 = resp1.json()
        assert "preview" in data1

    def test_live_preview_error_recovery(self):
        """Test live preview error recovery."""
        # Invalid JSON detected by format detection, returns 400
        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("error_recovery_test.json", b"not json", "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_live_preview_performance(self):
        """Test live preview performance."""
        import time

        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Performance Preview Test",
                "description": "Testing performance of live preview",
                "creator": [{"@type": "Person", "name": "Performance User"}],
                "identifier": "performance-preview-001",
                "datePublished": "2023-06-01",
                "license": "CC-BY-4.0",
            }
        )

        start_time = time.time()

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("performance_preview.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        assert resp.status_code == 200
        data = resp.json()

        assert elapsed_time < 3.0, f"Live preview generation took too long: {elapsed_time}s"

        assert "preview" in data
        assert "validation" in data

    def test_live_preview_data_integrity(self):
        """Test live preview data integrity."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Integrity Test Dataset",
                "description": "Testing data integrity in live preview",
                "creator": [{"@type": "Person", "name": "Integrity User"}],
                "identifier": "integrity-test-001",
                "datePublished": "2023-07-01",
                "license": "CC-BY-4.0",
                "keywords": ["integrity", "test"],
                "publisher": "Integrity Publisher",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("integrity_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        preview = data["preview"]

        assert "@context" in preview
        assert "@graph" in preview

        graph = preview["@graph"]
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Integrity Test Dataset":
                investigation_found = True
                break

        assert investigation_found

        assert "validation" in data

    def test_live_preview_endpoint_consistency(self):
        """Test live preview endpoint consistency."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Consistency Preview Test",
                "description": "Testing consistency across live preview requests",
                "creator": [{"@type": "Organization", "name": "Consistency Org"}],
                "identifier": "consistency-preview-001",
                "datePublished": "2023-08-01",
                "license": "MIT",
            }
        )

        results = []
        for i in range(3):
            resp = client.post(
                "/convert/arc-export?preview=true",
                files={"file": ("consistency_test.json", content.encode(), "application/json")},
                data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
            )

            assert resp.status_code == 200
            data = resp.json()
            results.append(data)

        for i, result in enumerate(results):
            assert "preview" in result
            assert "validation" in result

            preview = result["preview"]
            assert "@context" in preview
            assert "@graph" in preview

            graph = preview["@graph"]
            investigation_found = False
            for entity in graph:
                if entity.get("name") == "Consistency Preview Test":
                    investigation_found = True
                    break

            assert investigation_found, f"Request {i} should have found the investigation entity"

    def test_live_preview_with_template_fields(self):
        """Test live preview integration with template fields."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Template Fields Preview Test",
                "description": "Testing live preview with template field integration",
                "creator": [{"@type": "Person", "name": "Template Fields User"}],
                "identifier": "template-fields-preview-001",
                "datePublished": "2023-09-01",
                "license": "CC-BY-4.0",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("template_fields_preview.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        assert "validation" in data

        preview = data["preview"]
        assert "@graph" in preview

        graph = preview["@graph"]
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Template Fields Preview Test":
                investigation_found = True
                assert "name" in entity
                assert "description" in entity
                break

        assert investigation_found

    def test_live_preview_response_structure(self):
        """Test live preview response structure completeness."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Response Structure Test",
                "description": "Testing response structure completeness",
                "creator": [{"@type": "Person", "name": "Structure User"}],
                "identifier": "structure-test-001",
                "datePublished": "2023-10-01",
                "license": "CC-BY-4.0",
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("response_structure_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "preview" in data
        assert "validation" in data

        preview = data["preview"]
        assert "@context" in preview
        assert "@graph" in preview

        validation = data["validation"]
        assert "valid" in validation or "errors" in validation
        assert "template_id" in validation
        assert "template_version" in validation

        expected_fields = ["preview", "validation"]
        for field in expected_fields:
            assert field in data, f"Missing required field: {field}"
