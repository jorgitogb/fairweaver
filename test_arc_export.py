#!/usr/bin/env python3
"""Test script for ARC export functionality."""

import json
import requests
import sys
import zipfile
import io

def test_schema_org_to_arc():
    """Test converting Schema.org to ARC format."""
    print("Testing Schema.org to ARC conversion...")
    
    # Create a sample Schema.org file
    schema_data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Test Plant Phenotyping Dataset",
        "description": "Plant phenotyping data from field trials",
        "creator": {
            "@type": "Person",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "affiliation": "Research Institute"
        },
        "identifier": "PP-2024-001",
        "license": "CC-BY-4.0",
        "datePublished": "2024-01-15",
        "keywords": ["plant phenotyping", "agronomy", "field trials"],
        "measurementTechnique": "Drone-based RGB imaging",
        "measurementMethod": "DJI Matrice 300 RTK"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/convert/arc-export",
            files={"file": ("test_schema.json", json.dumps(schema_data), "application/json")},
            params={
                "source_format": "schema_org",
                "pivot_id": "auto",
                "preview": "true"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Conversion successful:")
            print(f"   Filename: {result['filename']}")
            print(f"   Valid: {result['validation']['valid']}")
            print(f"   Template: {result['validation']['template_id']}")
            
            # Show preview structure
            preview = result['preview']
            print(f"   Investigation: {preview['@graph'][1]['name']}")
            print(f"   Entities: {len(preview['@graph'])}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_arc_preview():
    """Test ARC preview functionality."""
    print("\nTesting ARC preview...")
    
    # Create a simple Schema.org file
    simple_data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Simple Test",
        "description": "Test dataset",
        "creator": "John Smith"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/convert/arc-export",
            files={"file": ("simple.json", json.dumps(simple_data), "application/json")},
            params={"preview": "true"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Preview successful:")
            print(f"   Auto-selected template: {result['validation']['template_id']}")
            print(f"   Validation errors: {len(result['validation']['errors'])}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_batch_processing():
    """Test batch ARC processing."""
    print("\nTesting batch ARC processing...")
    
    # Create a ZIP with multiple JSON files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add first file
        file1 = {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Dataset 1",
            "description": "First dataset",
            "crop_species": "Zea mays"
        }
        zipf.writestr("dataset1.json", json.dumps(file1))
        
        # Add second file
        file2 = {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Dataset 2",
            "description": "Second dataset",
            "measurementTechnique": "Spectroscopy"
        }
        zipf.writestr("dataset2.json", json.dumps(file2))
    
    zip_buffer.seek(0)
    
    try:
        response = requests.post(
            "http://localhost:8000/convert/arc-export",
            files={"file": ("batch.zip", zip_buffer.getvalue(), "application/zip")},
            params={
                "batch": "true",
                "preview": "true"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Batch processing successful:")
            print(f"   Files processed: {len(result['batch_preview'])}")
            for item in result['batch_preview']:
                print(f"     - {item['filename']}: {item['result']['validation']['template_id']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_template_auto_selection():
    """Test automatic template selection."""
    print("\nTesting automatic template selection...")
    
    # Test plant phenotyping data
    plant_data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Plant Data",
        "crop_species": "Triticum aestivum",
        "organism": "Wheat"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/convert/arc-export",
            files={"file": ("plant.json", json.dumps(plant_data), "application/json")},
            params={
                "pivot_id": "auto",
                "preview": "true"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            template = result['validation']['template_id']
            # Check if auto-selection is working by checking the template version
            # Our updated template should be selected for plant data
            if template == 'fairagro_arc_v2':
                print(f"✅ Template selected: {template} (auto-selection working)")
                return True
            else:
                print(f"❌ Unexpected template: {template}")
                return False
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing ARC Export Functionality")
    print("=" * 50)
    
    results = []
    results.append(test_schema_org_to_arc())
    results.append(test_arc_preview())
    results.append(test_batch_processing())
    results.append(test_template_auto_selection())
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
