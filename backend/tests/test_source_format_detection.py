from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)


class TestSourceFormatDetection:
    """Test source format detection functionality."""

    def test_detect_format_json_with_schema_org_context(self):
        """Test format detection for JSON with schema.org context."""
        content = json.dumps(
            {"@context": "https://schema.org/", "@type": "Dataset", "name": "Test Dataset"}
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data
        assert "validation" in data

    def test_detect_format_json_with_ro_crate_context(self):
        """Test format detection for JSON with RO-Crate context."""
        content = json.dumps(
            {
                "@context": ["https://schema.org/", "https://w3id.org/ro/crate/1.0"],
                "@graph": [{"@id": "ro-crate-metadata.json", "@type": "CreativeWork"}],
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

    def test_detect_format_json_with_graph(self):
        """Test format detection for JSON with @graph."""
        content = json.dumps(
            {"@graph": [{"@id": "https://example.org/investigation", "@type": "Dataset"}]}
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

    def test_detect_format_oai_dc_xml(self):
        """Test format detection for OAI DC XML — unsupported by arc-export."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
  <dc:title>Test Dataset</dc:title>
  <dc:creator>Test Author</dc:creator>
</oai_dc:dc>"""

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.xml", content, "application/xml")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_detect_format_csv(self):
        """Test format detection for CSV files — unsupported by arc-export."""
        content = b'"name","description","creator"\n"Test","Test Dataset","Test Author"'

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.csv", content, "text/csv")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_detect_format_xlsx(self):
        """Test format detection for XLSX files — unsupported by arc-export."""
        content = b"PK\x03\x04"

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={
                "file": (
                    "test.xlsx",
                    content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_detect_format_with_explicit_format(self):
        """Test format detection when source_format is explicitly provided."""
        content = json.dumps(
            {"@context": "https://schema.org/", "@type": "Dataset", "name": "Test Dataset"}
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.json", content.encode(), "application/json")},
            data={"source_format": "schema_org", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data

    def test_detect_format_unsupported_file_extension(self):
        """Test format detection for unsupported file extension returns 400."""
        content = json.dumps({"name": "Test"})

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.unknown", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_detect_format_invalid_json(self):
        """Test format detection for invalid JSON content returns 400."""
        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.json", b"not json", "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_detect_format_empty_file(self):
        """Test format detection for empty file returns 400."""
        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.json", b"", "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_format_detection_fallback_to_default(self):
        """Test that format detection falls back to default for unknown extensions."""
        content = json.dumps({"name": "Test"})

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test.unknown", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 400

    def test_schema_org_detection_specific_pattern(self):
        """Test specific pattern matching for schema.org detection."""
        # Test with full schema.org context URL
        content = json.dumps({"@context": "https://schema.org/", "@type": "Dataset"})

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test_schema_org.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200

        # Test with http schema.org
        content = json.dumps({"@context": "http://schema.org/", "@type": "Dataset"})

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test_schema_org2.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200

    def test_ro_crate_detection(self):
        """Test RO-Crate format detection."""
        content = json.dumps(
            {
                "@context": ["https://schema.org/", "https://w3id.org/ro/crate/1.0"],
                "@graph": [{"@id": "ro-crate-metadata.json", "@type": "CreativeWork"}],
            }
        )

        resp = client.post(
            "/convert/arc-export?preview=true",
            files={"file": ("test_rocrate.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "preview" in data
