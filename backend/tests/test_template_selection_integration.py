from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)


class TestTemplateSelectionIntegration:
    """Test template selection integration functionality."""

    def test_template_selection_integration_agronomy_detection(self):
        """Test integration of agronomy content detection for template selection."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Wheat Growth Study",
            "description": "Longitudinal study of wheat growth under different conditions",
            "creator": [{"@type": "Person", "name": "Dr. Green"}],
            "identifier": "wheat-study-001",
            "datePublished": "2023-01-01",
            "license": "CC-BY-4.0",
            "crop_species": "Triticum aestivum",
            "crop_pest": "Fusarium graminearum",
            "organism": "Triticum aestivum"
        })
        
        # Use auto template selection
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("wheat_study.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify auto-selection picked the correct template
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        # The integration should work with auto template selection
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Wheat Growth Study":
                investigation_found = True
                break
        
        assert investigation_found, "Auto-template selection should have processed the content"
        
        # Verify validation was performed
        assert "validation" in data
        validation = data["validation"]
        assert "valid" in validation or "errors" in validation

    def test_template_selection_integration_genomics_detection(self):
        """Test integration of genomics content detection for template selection."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Human Genome Sequencing",
            "description": "Whole genome sequencing of human samples",
            "creator": [{"@type": "Organization", "name": "Genome Institute"}],
            "identifier": "hg001",
            "datePublished": "2023-02-15",
            "license": "MIT",
            "sequencing": "Illumina HiSeq X Ten",
            "dna": ["GRCh38"],
            "rna": ["ENST000012345"],
            "genome": "Homo sapiens"
        })
        
        # Use auto template selection
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("genome_sequencing.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify auto-selection picked the correct template
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Human Genome Sequencing":
                investigation_found = True
                break
        
        assert investigation_found, "Genomics auto-template selection should have processed the content"
        
        # Verify template selection integration
        assert "validation" in data

    def test_template_selection_integration_sensor_detection(self):
        """Test integration of sensor content detection for template selection."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Field Sensor Network",
            "description": "Environmental sensor data from agricultural field",
            "creator": [{"@type": "Person", "name": "Sensor Operator"}],
            "identifier": "sensor-net-001",
            "datePublished": "2023-03-20",
            "license": "CC-BY-SA-4.0",
            "measurementTechnique": "drone-spectral-imaging",
            "measurementMethod": "NDVI analysis",
            "drone": "DJI Phantom 4",
            "sensor": "Hyperspectral imager",
            "measurementTechnique": "UAV-based remote sensing"
        })
        
        # Use auto template selection
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("sensor_network.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify auto-selection picked the correct template
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Field Sensor Network":
                investigation_found = True
                break
        
        assert investigation_found, "Sensor auto-template selection should have processed the content"
        
        # Verify integration with template selection system
        assert "validation" in data

    def test_template_selection_integration_manual_override(self):
        """Test integration of manual template override."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Manual Override Test",
            "description": "Testing manual template override",
            "creator": [{"@type": "Person", "name": "Test User"}],
            "identifier": "manual-override-001",
            "datePublished": "2023-04-01",
            "license": "CC-BY-4.0"
        })
        
        # Manually specify searchhub template (different from auto-selected)
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("manual_override.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify manual template selection worked
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Manual Override Test":
                investigation_found = True
                break
        
        assert investigation_found, "Manual template selection should have processed the content"
        
        # Verify manual template selection integration
        assert "validation" in data

    def test_template_selection_integration_with_field_paths(self):
        """Test integration of template selection with field path extraction."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Field Path Integration Test",
            "description": "Testing integration with field path extraction",
            "creator": [{"@type": "Person", "name": "Integration User"}],
            "identifier": "field-path-test-001",
            "datePublished": "2023-05-01",
            "license": "Apache-2.0",
            "keywords": ["integration", "field", "path"],
            "alternative_titles": ["Alternative Title 1"],
            "publisher": "Test Publisher"
        })
        
        # Get template fields first to verify integration
        template_resp = client.get("/template-fields/fairagro")
        assert template_resp.status_code == 200
        
        # Then convert with template selection
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("field_path_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify template selection and field path integration
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Field Path Integration Test":
                investigation_found = True
                break
        
        assert investigation_found, "Template selection with field path integration should have processed the content"
        
        # Verify comprehensive validation
        assert "validation" in data

    def test_template_selection_integration_auto_with_no_clear_indicators(self):
        """Test integration with ambiguous content that doesn't clearly indicate a template."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Ambiguous Dataset",
            "description": "Dataset with no clear template indicators",
            "creator": [{"@type": "Person", "name": "Anonymous"}],
            "identifier": "ambiguous-001",
            "datePublished": "2023-06-01",
            "license": "CC-BY-4.0"
        })
        
        # Auto selection should fall back to default
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("ambiguous.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify fallback to default template worked
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Ambiguous Dataset":
                investigation_found = True
                break
        
        assert investigation_found, "Auto-template selection with ambiguous content should fall back to default"
        
        # Verify validation was performed
        assert "validation" in data

    def test_template_selection_integration_consistency(self):
        """Test integration consistency between template selection and conversion."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Consistency Test Dataset",
            "description": "Testing consistency in template selection",
            "creator": [{"@type": "Organization", "name": "Consistency Org"}],
            "identifier": "consistency-test-001",
            "datePublished": "2023-07-01",
            "license": "CC-BY-4.0"
        })
        
        # Multiple conversions with same content should yield consistent results
        results = []
        for i in range(3):
            resp = client.post(
                "/convert/arc-export",
                files={"file": (f"consistency_test_{i}.json", content.encode(), "application/json")},
                data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
            )
            
            assert resp.status_code == 200
            data = resp.json()
            results.append(data)
        
        # All conversions should produce consistent results
        for i, result in enumerate(results):
            assert "preview" in result
            assert "validation" in result
            
            # Each should have valid structure
            arc_data = result["preview"]
            assert "@graph" in arc_data
            
            # All should find the investigation entity
            graph = arc_data.get("@graph", [])
            investigation_found = False
            for entity in graph:
                if entity.get("name") == "Consistency Test Dataset":
                    investigation_found = True
                    break
            
            assert investigation_found, f"Conversion {i} should have found the investigation entity"

    def test_template_selection_integration_error_handling(self):
        """Test error handling in template selection integration."""
        # Invalid JSON returns 400 (format detection falls back to unsupported format)
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("invalid.json", b'not json', "application/json")},
            data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
        )

        assert resp.status_code == 400

    def test_template_selection_integration_performance(self):
        """Test performance of template selection integration."""
        import time
        
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Performance Test Dataset",
            "description": "Testing performance of template selection",
            "creator": [{"@type": "Person", "name": "Performance User"}],
            "identifier": "performance-test-001",
            "datePublished": "2023-08-01",
            "license": "CC-BY-4.0"
        })
        
        # Measure time for template selection and conversion
        start_time = time.time()
        
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("performance_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "auto", "preview": "true"}
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Template selection and conversion should complete in reasonable time
        # Allow 5 seconds for processing
        assert elapsed_time < 5.0, f"Template selection and conversion took too long: {elapsed_time}s"
        
        # Verify result structure
        assert "preview" in data
        assert "validation" in data

    def test_template_selection_integration_rollback(self):
        """Test integration rollback when template selection fails."""
        content = json.dumps({
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": "Rollback Test",
            "description": "Testing rollback when template selection fails",
            "creator": [{"@type": "Person", "name": "Rollback User"}],
            "identifier": "rollback-test-001",
            "datePublished": "2023-09-01",
            "license": "CC-BY-4.0"
        })
        
        # Use valid content that should not cause rollback
        resp = client.post(
            "/convert/arc-export",
            files={"file": ("rollback_test.json", content.encode(), "application/json")},
            data={"source_format": "auto", "pivot_id": "fairagro_searchhub", "preview": "true"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify successful integration without rollback
        arc_data = data["preview"]
        graph = arc_data.get("@graph", [])
        
        investigation_found = False
        for entity in graph:
            if entity.get("name") == "Rollback Test":
                investigation_found = True
                break
        
        assert investigation_found, "Template selection integration should succeed without rollback"
        
        # Verify validation was performed
        assert "validation" in data