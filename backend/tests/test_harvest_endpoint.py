from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from sickle.oaiexceptions import CannotDisseminateFormat


client = TestClient(app)

SAMPLE_RECORDS = {
    "records": [
        {
            "identifier": "oai:test:1",
            "datestamp": "2023-01-01",
            "set_spec": ["public"],
            "metadata": {"title": ["Test Dataset"]},
            "metadata_format": "oai_dc",
        }
    ],
    "total": 1,
    "metadata_format": "oai_dc",
}


class TestHarvestEndpoint:
    def test_harvest_success(self):
        with patch("main.harvest") as mock_harvest:
            mock_harvest.return_value = SAMPLE_RECORDS
            resp = client.post(
                "/harvest",
                json={"base_url": "https://example.org/oai", "metadata_prefix": "oai_dc"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["records"]) == 1
        assert data["records"][0]["identifier"] == "oai:test:1"

    def test_harvest_missing_base_url(self):
        resp = client.post(
            "/harvest",
            json={"metadata_prefix": "oai_dc"},
        )
        assert resp.status_code == 422

    def test_harvest_invalid_prefix(self):
        resp = client.post(
            "/harvest",
            json={"base_url": "https://example.org/oai", "metadata_prefix": "oai_xyz"},
        )
        assert resp.status_code == 422

    def test_harvest_invalid_format_returns_400(self):
        with patch("main.harvest") as mock_harvest:
            mock_harvest.side_effect = CannotDisseminateFormat(
                'metadataPrefix "oai_datacite" unknown.'
            )
            resp = client.post(
                "/harvest",
                json={"base_url": "https://example.org/oai", "metadata_prefix": "oai_datacite"},
            )
        assert resp.status_code == 400
        assert "oai_datacite" in resp.json()["detail"]

    def test_harvest_connection_error(self):
        with patch("main.harvest") as mock_harvest:
            mock_harvest.side_effect = ConnectionError("Connection refused")
            resp = client.post(
                "/harvest",
                json={"base_url": "https://example.org/oai", "metadata_prefix": "oai_dc"},
            )
        assert resp.status_code == 502
        assert "Connection refused" in resp.json()["detail"]


SAMPLE_SETS = [
    {"spec": "public", "name": "Public datasets"},
    {"spec": "restricted", "name": "Restricted datasets"},
]


class TestListSetsEndpoint:
    def test_list_sets_success(self):
        with patch("main.list_sets") as mock_list:
            mock_list.return_value = SAMPLE_SETS
            resp = client.post(
                "/list-sets",
                json={"base_url": "https://example.org/oai"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sets"]) == 2
        assert data["sets"][0]["spec"] == "public"
        assert data["sets"][1]["name"] == "Restricted datasets"

    def test_list_sets_connection_error(self):
        with patch("main.list_sets") as mock_list:
            mock_list.side_effect = ConnectionError("Connection refused")
            resp = client.post(
                "/list-sets",
                json={"base_url": "https://example.org/oai"},
            )
        assert resp.status_code == 502
