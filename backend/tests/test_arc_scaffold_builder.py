import json
import shutil
from pathlib import Path

from arctrl import XlsxController
from fastapi.testclient import TestClient

from arc_scaffold_builder import build_scaffold_from_rocrate, sanitize_arc_identifier, zip_scaffold
from main import app


class TestArcScaffoldBuilder:
    """Unit tests for ARC scaffold builder."""

    def test_build_scaffold_investigation_only(self, tmp_path: Path):
        """A minimal RO-Crate with an Investigation entity produces a scaffold."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_test",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Test Investigation",
                    "description": "A test investigation",
                    "identifier": "test-123",
                    "datePublished": "2024-01-01",
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)

        assert output_dir.exists()
        assert (output_dir / "isa.investigation.xlsx").exists()
        assert (output_dir / "studies").exists()
        assert (output_dir / "assays").exists()
        assert (output_dir / "workflows").exists()
        assert (output_dir / "runs").exists()

    def test_build_scaffold_with_study(self, tmp_path: Path):
        """A Study entity produces a subdirectory with isa.study.xlsx."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_test",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Test Investigation",
                    "description": "A test investigation",
                    "identifier": "test-123",
                    "hasPart": [{"@id": "#Study_test"}],
                },
                {
                    "@id": "#Study_test",
                    "@type": "Dataset",
                    "additionalType": "Study",
                    "name": "Test Study",
                    "description": "A test study",
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)

        study_dir = output_dir / "studies" / "Study_test"
        assert study_dir.exists()
        assert (study_dir / "isa.study.xlsx").exists()

    def test_build_scaffold_with_assay(self, tmp_path: Path):
        """An Assay entity produces a subdirectory with isa.assay.xlsx."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_test",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Test Investigation",
                    "description": "A test investigation",
                    "identifier": "test-123",
                    "hasPart": [{"@id": "#Study_test"}],
                },
                {
                    "@id": "#Study_test",
                    "@type": "Dataset",
                    "additionalType": "Study",
                    "name": "Test Study",
                    "description": "A test study",
                    "hasPart": [{"@id": "#Assay_test"}],
                },
                {
                    "@id": "#Assay_test",
                    "@type": "Dataset",
                    "additionalType": "Assay",
                    "name": "Test Assay",
                    "description": "A test assay",
                    "measurementTechnique": "Imaging",
                    "technologyType": "Multispectral sensor",
                    "about": [{"@id": "#Study_test"}],
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)

        assay_dir = output_dir / "assays" / "Assay_test"
        assert assay_dir.exists()
        assert (assay_dir / "isa.assay.xlsx").exists()

    def test_build_scaffold_with_person(self, tmp_path: Path):
        """A Person entity linked to the Investigation becomes a contact."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_test",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Test Investigation",
                    "description": "A test investigation",
                    "identifier": "test-123",
                    "creator": [{"@id": "#Person_jane"}],
                },
                {
                    "@id": "#Person_jane",
                    "@type": "Person",
                    "givenName": "Jane",
                    "familyName": "Doe",
                    "email": "jane@example.com",
                    "identifier": {
                        "@type": "PropertyValue",
                        "propertyID": "orcid",
                        "value": "0000-0001-2345-6789",
                    },
                    "affiliation": {"@type": "Organization", "name": "Example University"},
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)

        inv = XlsxController.Investigation().from_xlsx_file(
            str(output_dir / "isa.investigation.xlsx")
        )
        assert len(inv.Contacts) == 1
        contact = inv.Contacts[0]
        assert contact.FirstName == "Jane"
        assert contact.LastName == "Doe"

    def test_zip_scaffold(self, tmp_path: Path):
        """zip_scaffold packages the scaffold directory into a ZIP archive."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_test",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Test Investigation",
                    "description": "A test investigation",
                    "identifier": "test-123",
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)
        zip_bytes = zip_scaffold(output_dir, arc_name="Test Investigation")

        assert len(zip_bytes) > 0
        assert zip_bytes[:4] == b"PK\x03\x04"

        zip_path = tmp_path / "scaffold.zip"
        zip_path.write_bytes(zip_bytes)
        shutil.unpack_archive(zip_path, tmp_path / "unpacked")

        unpacked = tmp_path / "unpacked" / "Test Investigation"
        assert unpacked.exists()
        assert (unpacked / "isa.investigation.xlsx").exists()

    def test_build_scaffold_with_url_identifier(self, tmp_path: Path):
        """A URL identifier is sanitized so the scaffold can be opened."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_wheat",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Wheat Drought Phenotyping",
                    "description": "A wheat trial",
                    "identifier": "https://doi.org/10.5447//2024/wheat-drought-001",
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)

        inv = XlsxController.Investigation().from_xlsx_file(
            str(output_dir / "isa.investigation.xlsx")
        )
        assert inv.Identifier == "wheat-drought-001"

    def test_zip_scaffold_url_identifier_flat_structure(self, tmp_path: Path):
        """The ZIP folder name is sanitized to a single flat directory."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_wheat",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Wheat Drought Phenotyping",
                    "identifier": "https://doi.org/10.5447//2024/wheat-drought-001",
                },
            ],
        }

        output_dir = tmp_path / "scaffold"
        build_scaffold_from_rocrate(rocrate, output_dir)
        zip_bytes = zip_scaffold(output_dir, arc_name="wheat-drought-001")

        zip_path = tmp_path / "scaffold.zip"
        zip_path.write_bytes(zip_bytes)
        shutil.unpack_archive(zip_path, tmp_path / "unpacked")

        entries = list((tmp_path / "unpacked").iterdir())
        assert len(entries) == 1
        assert entries[0].name == "wheat-drought-001"
        assert (entries[0] / "isa.investigation.xlsx").exists()


class TestSanitizeArcIdentifier:
    """Unit tests for identifier sanitization helper."""

    def test_url_identifier_extracts_last_segment(self):
        assert (
            sanitize_arc_identifier("https://doi.org/10.5447//2024/wheat-drought-001")
            == "wheat-drought-001"
        )

    def test_path_identifier_extracts_last_segment(self):
        assert (
            sanitize_arc_identifier("10.5447/fairweaver/2024/wheat-drought-001")
            == "wheat-drought-001"
        )

    def test_plain_identifier_preserved(self):
        assert sanitize_arc_identifier("wheat-001") == "wheat-001"

    def test_forbidden_characters_replaced(self):
        assert sanitize_arc_identifier("a:b/c.d") == "c d"

    def test_empty_value_defaults_to_arc(self):
        assert sanitize_arc_identifier("") == "arc"
        assert sanitize_arc_identifier(None) == "arc"


class TestArcScaffoldEndpoint:
    """Integration tests for the POST /arc/scaffold endpoint."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_returns_zip(self):
        """POST /arc/scaffold returns a ZIP download for a valid RO-Crate."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_test",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Test Investigation",
                    "description": "A test investigation",
                    "identifier": "test-123",
                },
            ],
        }
        resp = self.client.post(
            "/arc/scaffold",
            files={"file": ("ro-crate.json", json.dumps(rocrate).encode(), "application/json")},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        assert resp.content[:4] == b"PK\x03\x04"

    def test_endpoint_invalid_json_400(self):
        """POST /arc/scaffold rejects non-JSON input."""
        resp = self.client.post(
            "/arc/scaffold",
            files={"file": ("not-json.txt", b"not json", "text/plain")},
        )
        assert resp.status_code == 400

    def test_endpoint_missing_investigation_400(self):
        """POST /arc/scaffold rejects RO-Crate without Investigation."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "Only a dataset",
                },
            ],
        }
        resp = self.client.post(
            "/arc/scaffold",
            files={"file": ("ro-crate.json", json.dumps(rocrate).encode(), "application/json")},
        )
        assert resp.status_code == 400

    def test_endpoint_sanitizes_url_identifier(self):
        """POST /arc/scaffold sanitizes URL identifiers in filename and ZIP."""
        rocrate = {
            "@context": "https://w3id.org/ro/crate/1.1",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": "https://w3id.org/ro/crate/1.1",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "#Investigation_wheat",
                    "@type": "Dataset",
                    "additionalType": "Investigation",
                    "name": "Wheat Drought Phenotyping",
                    "identifier": "https://doi.org/10.5447//2024/wheat-drought-001",
                },
            ],
        }
        resp = self.client.post(
            "/arc/scaffold",
            files={"file": ("ro-crate.json", json.dumps(rocrate).encode(), "application/json")},
        )
        assert resp.status_code == 200
        content_disposition = resp.headers.get("content-disposition", "")
        assert "wheat-drought-001_scaffold.zip" in content_disposition

        import zipfile
        import io

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            top_dirs = {name.split("/")[0] for name in zf.namelist() if "/" in name}
            assert top_dirs == {"wheat-drought-001"}
            assert any(name == "wheat-drought-001/isa.investigation.xlsx" for name in zf.namelist())
