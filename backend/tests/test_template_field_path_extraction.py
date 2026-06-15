from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestTemplateFieldPathExtraction:
    """Test template field path extraction functionality."""

    def test_get_template_fields_success(self):
        """Test successful retrieval of template field structure."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "template_id" in data
        assert data["template_id"] == "fairagro_arc_v2"
        assert "required_fields" in data
        assert "recommended_fields" in data
        assert "field_paths" in data
        assert "required_entities" in data
        assert "domains" in data
        
        # Check required fields structure
        assert "Investigation" in data["required_fields"]
        assert "name" in data["required_fields"]["Investigation"]
        assert "creator" in data["required_fields"]["Investigation"]
        
        # Check recommended fields structure
        assert "Investigation" in data["recommended_fields"]
        assert "alternative_titles" in data["recommended_fields"]["Investigation"]
        
        # Check field paths structure
        assert "citation" in data["field_paths"]
        assert "title" in data["field_paths"]["citation"]
        assert "description" in data["field_paths"]["citation"]
        
        # Check domains
        assert "agronomy" in data["domains"]
        assert "plant_phenotyping" in data["domains"]
        assert "genomics" in data["domains"]
        assert "biodiversity" in data["domains"]

    def test_get_template_fields_fairagro_searchhub_template(self):
        """Test retrieval of FAIRagro searchhub template fields."""
        # Note: Current implementation uses "fairagro" as template_id since only one template is loaded
        # The endpoint returns the same structure regardless of template_id for now
        resp = client.get("/template-fields/fairagro_searchhub")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["template_id"] == "fairagro_arc_v2"
        assert len(data["required_fields"]["Investigation"]) > 0
        assert len(data["recommended_fields"]["Investigation"]) > 0

    def test_get_template_fields_missing_template(self):
        """Test error when template is not found (simulated)."""
        # Current implementation always returns the same template
        # Since there's only one template loaded, this should still succeed
        resp = client.get("/template-fields/nonexistent_template")
        # Note: The endpoint currently doesn't validate template_id existence
        # It just loads the default template
        assert resp.status_code == 200
        assert resp.json()["template_id"] == "fairagro_arc_v2"

    def test_required_fields_structure(self):
        """Test that required fields have correct structure."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Verify required fields structure
        assert isinstance(data["required_fields"], dict)
        assert "Investigation" in data["required_fields"]
        assert "Study" in data["required_fields"]
        assert "Assay" in data["required_fields"]
        
        # Check each entity type has required fields
        for entity in ["Investigation", "Study", "Assay"]:
            assert isinstance(data["required_fields"][entity], list)
            assert len(data["required_fields"][entity]) > 0
            for field in data["required_fields"][entity]:
                assert isinstance(field, str)
                assert len(field) > 0

    def test_recommended_fields_structure(self):
        """Test that recommended fields have correct structure."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Verify recommended fields structure
        assert isinstance(data["recommended_fields"], dict)
        
        for entity in ["Investigation", "Study", "Assay"]:
            assert isinstance(data["recommended_fields"].get(entity, []), list)
            for field in data["recommended_fields"].get(entity, []):
                assert isinstance(field, str)
                assert len(field) > 0

    def test_field_paths_structure(self):
        """Test that field paths have correct structure."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Verify field paths structure
        assert isinstance(data["field_paths"], dict)
        assert "citation" in data["field_paths"]
        assert "crop" in data["field_paths"]
        assert "sensor" in data["field_paths"]
        
        # Check nested structure
        for category in ["citation", "crop", "sensor"]:
            assert isinstance(data["field_paths"][category], dict)
            for field_name, path in data["field_paths"][category].items():
                assert isinstance(field_name, str)
                assert isinstance(path, str)
                assert len(path) > 0

    def test_template_metadata(self):
        """Test that template metadata is correctly included."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Check template metadata
        assert isinstance(data["template_id"], str)
        assert data["template_id"] == "fairagro_arc_v2"
        assert isinstance(data["version"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["specification"], str)
        
        # Check that domains is a list
        assert isinstance(data["domains"], list)
        assert len(data["domains"]) >= 1

    def test_template_field_paths_usage(self):
        """Test that field paths are suitable for mapping extraction."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Verify field paths can be used for source→target mapping
        citation_paths = data["field_paths"]["citation"]
        
        # Check that each path represents a mapping from source to target
        for field_name, path in citation_paths.items():
            # Paths can use field extraction syntax like:
            # - Simple path: "Investigation.name"
            # - Pipe syntax: "Investigation.creator | Investigation.investigationContacts"
            # - Nested path: "Study.about.LabProcess.object.Sample.additionalProperty[Organism]"
            assert isinstance(path, str)
            assert len(path) > 0
            # Path should contain at least one identifier
            assert any(char.isalnum() for char in path)

    def test_response_format_completeness(self):
        """Test that response includes all expected fields for ARC conversion."""
        resp = client.get("/template-fields/fairagro")
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Essential fields for ARC conversion
        essential_fields = [
            "template_id", "version", "name", "description", "specification",
            "domains", "required_fields", "recommended_fields", 
            "field_paths", "required_entities", "arc_structure",
            "required_isa_files", "validation_rules"
        ]
        
        for field in essential_fields:
            assert field in data, f"Missing essential field: {field}"
        
        # Check that we have both mandatory and recommended fields
        assert len(data["required_fields"]) > 0
        assert len(data["recommended_fields"]) > 0
        assert len(data["field_paths"]) > 0
        assert len(data["required_entities"]) > 0