#!/usr/bin/env python3
"""
Process EDAL JSON file to create individual ARC RO-Crate files.

This script:
1. Reads the EDAL JSON file containing multiple datasets
2. Extracts individual dataset objects
3. Processes each through Schema.org → ARC conversion
4. Creates a ZIP file with all ARC outputs
"""

import json
import requests
import zipfile
import io
import os
import shutil

def process_edal_file(input_file: str, output_zip: str):
    """
    Process EDAL JSON file and create ARC files.
    
    Args:
        input_file: Path to EDAL JSON file
        output_zip: Path to output ZIP file
    """
    print(f"📖 Reading EDAL file: {input_file}")
    
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print("❌ Error: Expected JSON array of datasets")
        return False
    
    print(f"📊 Found {len(data)} datasets in the file")
    
    # Create temporary directory for individual JSON files
    temp_dir = "temp_edal_files"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Process each dataset
    arc_files = []
    
    for i, dataset in enumerate(data):
        dataset_id = dataset.get("@id", f"dataset_{i}")
        print(f"\n🔧 Processing dataset {i+1}/{len(data)}: {dataset_id}")
        
        # Save as temporary JSON file
        temp_file = f"{temp_dir}/{dataset_id.replace('/', '_')}.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        # Process through ARC export API
        try:
            with open(temp_file, 'rb') as f:
                files = {'file': (os.path.basename(temp_file), f, 'application/json')}
                params = {
                    'source_format': 'schema_org',
                    'pivot_id': 'auto',  # Auto-select template
                    'batch': 'false',   # Process individually
                    'preview': 'false'  # Get actual ARC file
                }
                
                response = requests.post(
                    "http://localhost:8000/convert/arc-export",
                    files=files,
                    params=params
                )
            
            if response.status_code == 200:
                # Get filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename_match = content_disposition.split('filename=')[1].strip('"')
                    arc_filename = filename_match or f"dataset_{i}_arc-ro-crate.json"
                else:
                    arc_filename = f"dataset_{i}_arc-ro-crate.json"
                
                # Save ARC file
                arc_content = response.content
                arc_filepath = f"{temp_dir}/{arc_filename}"
                with open(arc_filepath, 'wb') as f:
                    f.write(arc_content)
                
                arc_files.append(arc_filepath)
                print(f"✅ Created: {arc_filename}")
                
                # Get validation info
                arc_data = json.loads(arc_content)
                if '_validation' in arc_data:
                    validation = arc_data['_validation']
                    if not validation['valid']:
                        print(f"   ⚠️  Validation warnings: {len(validation['errors'])}")
                        for error in validation['errors'][:3]:  # Show first 3 errors
                            print(f"      - {error}")
                        if len(validation['errors']) > 3:
                            print(f"      ... and {len(validation['errors']) - 3} more")
            else:
                print(f"❌ Failed to process {dataset_id}: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error processing {dataset_id}: {str(e)}")
        
        # Create ZIP file
        if arc_files:
            print(f"\n📦 Creating ZIP archive with {len(arc_files)} ARC files...")
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for arc_file in arc_files:
                    arc_filename = os.path.basename(arc_file)
                    zipf.write(arc_file, arc_filename)
            
            print(f"✅ Success! Created {output_zip}")
            print(f"   Size: {os.path.getsize(output_zip) / 1024:.1f} KB")
            print(f"   Contains {len(arc_files)} ARC RO-Crate files")
            
            # Clean up temporary files
            shutil.rmtree(temp_dir)
            
            return True
        else:
            print("❌ No ARC files were created")
            return False

if __name__ == "__main__":
    print("🚀 EDAL to ARC Batch Processor")
    print("=" * 50)
    
    input_file = "/Users/brizuela/Downloads/edal.json"
    output_zip = "/Users/brizuela/Downloads/edal_arc_export_batch.zip"
    
    success = process_edal_file(input_file, output_zip)
    
    if success:
        print("\n🎉 Processing complete!")
        print(f"📁 Output: {output_zip}")
    else:
        print("\n❌ Processing failed")
