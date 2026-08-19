from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)


class TestComplianceClassify:
    """Test compliance classification endpoint."""

    def test_classify_valid_json_object(self):
        """Test classify with a valid JSON object returns 200."""
        content = json.dumps(
            {
                "@context": "https://schema.org/",
                "@type": "Dataset",
                "name": "Test Dataset",
                "description": "A test dataset",
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "identifier": "test-001",
            }
        )

        resp = client.post(
            "/compliance/classify",
            files={"file": ("test.json", content.encode(), "application/json")},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "level" in data
        assert "overall_score" in data
        assert data["level"] in ("basic", "intermediate", "full")

    def test_classify_returns_422_for_json_array(self):
        """Test classify returns 422 with helpful message when given a JSON array."""
        content = json.dumps(
            [
                {"name": "Dataset 1", "description": "First dataset"},
                {"name": "Dataset 2", "description": "Second dataset"},
            ]
        )

        resp = client.post(
            "/compliance/classify",
            files={"file": ("list.json", content.encode(), "application/json")},
        )

        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "array" in detail.lower() or "object" in detail.lower()
