#!/usr/bin/env python3
"""Test script for ARC template functionality."""

import json
import requests
import sys

def test_get_template():
    """Test getting FAIRagro ARC template."""
    print("Testing GET /arc/templates/fairagro...")
    try:
        response = requests.get("http://localhost:8000/arc/templates/fairagro")
        if response.status_code == 200:
            template = response.json()
            print(f"✅ Template retrieved successfully:")
            print(f"   Template ID: {template['template_id']}")
            print(f"   Name: {template['name']}")
            print(f"   Version: {template['version']}")
            print(f"   Required entities: {', '.join(template['required_entities'])}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validate_arc():
    """Test validating an ARC file against FAIRagro template."""
    print("\nTesting POST /arc/validate/fairagro...")
    
    # Create a minimal valid ARC structure
    arc_data = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}
            },
            {
                "@id": "#investigation",
                "@type": "Dataset",
                "additionalType": "Investigation",
                "name": "Test Investigation",
                "description": "Test description",
                "creator": {"@id": "#person1"},
                "identifier": "test-001",
                "license": "CC-BY-4.0",
                "datePublished": "2024-01-01"
            },
            {
                "@id": "#study",
                "@type": "Dataset",
                "additionalType": "Study",
                "name": "Test Study",
                "description": "Test study description"
            },
            {
                "@id": "#assay",
                "@type": "Dataset",
                "additionalType": "Assay",
                "name": "Test Assay",
                "measurementTechnique": "Drone",
                "measurementMethod": "RGB Camera"
            },
            {
                "@id": "#person1",
                "@type": "Person",
                "name": "John Doe"
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/arc/validate/fairagro",
            files={"file": ("test_arc.json", json.dumps(arc_data), "application/json")}
        )
        
        if response.status_code == 200:
            validation = response.json()
            print(f"✅ Validation successful:")
            print(f"   Valid: {validation['valid']}")
            print(f"   Template: {validation['template_id']} v{validation['template_version']}")
            if not validation['valid']:
                print(f"   Errors: {len(validation['errors'])}")
                for error in validation['errors']:
                    print(f"     - {error}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validate_invalid_arc():
    """Test validating an invalid ARC file."""
    print("\nTesting validation of invalid ARC (missing required entities)...")
    
    # Create an invalid ARC (missing Study and Assay)
    arc_data = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}
            },
            {
                "@id": "#investigation",
                "@type": "Dataset",
                "additionalType": "Investigation",
                "name": "Test Investigation",
                "description": "Test description",
                "creator": {"@id": "#person1"},
                "identifier": "test-001",
                "license": "CC-BY-4.0",
                "datePublished": "2024-01-01"
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/arc/validate/fairagro",
            files={"file": ("invalid_arc.json", json.dumps(arc_data), "application/json")}
        )
        
        if response.status_code == 200:
            validation = response.json()
            print(f"✅ Validation completed:")
            print(f"   Valid: {validation['valid']}")
            if not validation['valid']:
                print(f"   Expected errors found: {len(validation['errors'])}")
                for error in validation['errors']:
                    print(f"     - {error}")
                return True
            else:
                print("❌ Expected validation errors but got none")
                return False
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing FAIRagro ARC Template System")
    print("=" * 50)
    
    results = []
    results.append(test_get_template())
    results.append(test_validate_arc())
    results.append(test_validate_invalid_arc())
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
