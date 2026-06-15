# API Documentation - Schema.org to ARC Playground

## Overview

The Schema.org to ARC Playground API provides endpoints for converting schema.org JSON-LD files to ARC RO-Crate format using FAIRagro templates. The API includes template field path extraction, source format detection, and ARC conversion capabilities.

## Available Endpoints

### GET /template-fields/{template_id}

**Summary**: Get template field structure for ARC conversion

**Description**: Retrieves the field structure (mandatory vs recommended) for a given FAIRagro ARC template. This endpoint returns comprehensive template information including required fields, recommended fields, field extraction paths, and template metadata.

**Parameters**:
- `template_id` (string, required): The template identifier. Currently supports "fairagro" for the standard FAIRagro ARC template.

**Response**:
```json
{
  "template_id": "fairagro_arc_v2",
  "version": "2.0.0",
  "name": "FAIRagro ARC Template (DataPLANT Compliant)",
  "description": "Standard ARC structure for FAIRagro Search Hub compatibility, fully compliant with DataPLANT ARC specification v3.0",
  "specification": "DataPLANT ARC v3.0 + FAIRagro Search Hub v1.0",
  "domains": ["agronomy", "plant_phenotyping", "biodiversity", "genomics"],
  "required_fields": {
    "Investigation": ["name", "description", "creator", "identifier", "license", "datePublished", "investigationContacts", "investigationPublications"],
    "Study": ["name", "description", "studyDesignDescriptors"],
    "Assay": ["name", "description", "measurementTechnique", "measurementMethod", "technologyType", "technologyPlatform"]
  },
  "recommended_fields": {
    "Investigation": ["alternative_titles", "keywords", "publisher", "investigationIdentifier"],
    "Study": ["about", "studyDesignType", "studyPersonnel"],
    "Assay": ["about", "measurementTechnique", "measurementMethod", "assayCategory", "assayType"]
  },
  "field_paths": {
    "citation": {
      "title": "Investigation.name",
      "description": "Investigation.description",
      "author": "Investigation.creator | Investigation.investigationContacts",
      "otherId": "Investigation.identifier | Investigation.investigationIdentifier",
      "productionDate": "Investigation.datePublished",
      "license": "Investigation.license"
    },
    "crop": {
      "cropSpecies": "Study.about.LabProcess.object.Sample.additionalProperty[Organism]",
      "cropPest": "Study.about.LabProcess.object.Sample.additionalProperty[Infection Taxon]"
    },
    "sensor": {
      "sensorType": "Assay.measurementTechnique | Assay.technologyType",
      "sensorPlatformType": "Assay.measurementMethod | Assay.technologyPlatform",
      "sensorPlatformManufacturerName": "Assay.about.LabProcess.additionalProperty[Drone Manufacturer]",
      "sensorPlatformModelName": "Assay.about.LabProcess.additionalProperty[Drone Model]"
    }
  },
  "required_entities": ["Investigation", "Study", "Assay"],
  "arc_structure": {
    "required_directories": [".arc", "studies", "assays", "workflows", "runs"],
    "required_files": ["isa.investigation.xlsx", "ro-crate-metadata.json"],
    "optional_files": ["LICENSE", "README.md"]
  },
  "required_isa_files": ["isa.investigation.xlsx", "studies/*/isa.study.xlsx", "assays/*/isa.assay.xlsx", "workflows/*/workflow.cwl", "runs/*/run.cwl"],
  "validation_rules": [...]
}
```

**Example Usage**:
```bash
curl -X GET "http://localhost:8000/api/template-fields/fairagro" -H "Content-Type: application/json"
```

**Response Codes**:
- `200`: Successfully retrieved template field structure
- `500`: Internal server error occurred while loading template fields

---

### POST /convert/arc-export

**Summary**: Convert input file to ARC RO-Crate format

**Description**: Converts schema.org JSON-LD, OAI-PMH, or other supported formats to ARC RO-Crate format with optional batch processing and preview mode.

**Parameters**:
- `file` (file, required): Input file to convert (supports JSON, XML, CSV, XLSX)
- `source_format` (string, optional): Source format ("auto", "schema_org", "oai_dc", "ro_crate", "darwin_core_csv", "isa_json", "datacite_xml", "miappe_xlsx"). Defaults to "auto".
- `pivot_id` (string, optional): Template to use ("fairagro_searchhub", "fairagro_plant_phenotyping", "fairagro_genomics", "fairagro_sensor", "auto"). Defaults to "fairagro_searchhub".
- `batch` (boolean, optional): Enable batch processing mode. Defaults to false.
- `preview` (boolean, optional): Enable preview mode to return converted data without file download. Defaults to false.

**Request** (Multipart form data):
```bash
curl -X POST "http://localhost:8000/api/convert/arc-export" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@dataset.json" \
  -F "source_format=auto" \
  -F "pivot_id=auto" \
  -F "batch=false" \
  -F "preview=true"
```

**Response**:
```json
{
  "preview": {
    "@context": ["https://schema.org/", "https://w3id.org/ro/crate/1.0"],
    "@graph": [...]
  },
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "template_id": "fairagro_arc_v2",
    "template_version": "2.0.0"
  },
  "filename": "dataset_arc-ro-crate.json"
}
```

**Response Codes**:
- `200`: Conversion completed successfully
- `400`: Invalid input file or unsupported format
- `422`: Invalid request parameters
- `500`: Internal server error during conversion

---

## API Usage Examples

### 1. Get Template Fields

This example retrieves the field structure for the FAIRagro template:

```bash
curl -X GET "http://localhost:8000/api/template-fields/fairagro" \
  -H "Content-Type: application/json"
```

**Expected Response** (excerpt):
```json
{
  "template_id": "fairagro_arc_v2",
  "required_fields": {
    "Investigation": ["name", "description", "creator", "identifier", "license", "datePublished"],
    "Study": ["name", "description"],
    "Assay": ["name", "description", "measurementTechnique"]
  },
  "field_paths": {
    "citation": {
      "title": "Investigation.name",
      "author": "Investigation.creator | Investigation.investigationContacts"
    }
  }
}
```

### 2. Convert schema.org Dataset to ARC

This example converts a schema.org JSON-LD file to ARC format:

```bash
cat > dataset.json << EOF
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "Genomics Research Dataset",
  "description": "A dataset containing genomic sequencing data",
  "creator": [{"@type": "Person", "name": "Dr. Smith"}],
  "identifier": "genomics-dataset-001",
  "datePublished": "2023-01-15",
  "license": "CC-BY-4.0",
  "keywords": ["genomics", "sequencing", "DNA"]
}
EOF

curl -X POST "http://localhost:8000/api/convert/arc-export" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@dataset.json" \
  -F "source_format=auto" \
  -F "pivot_id=auto" \
  -F "preview=true"
```

### 3. Auto-Select Template Based on Content

This example uses the `pivot_id=auto` parameter to automatically select the best template:

```bash
curl -X POST "http://localhost:8000/api/convert/arc-export" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@dataset.json" \
  -F "source_format=auto" \
  -F "pivot_id=auto" \
  -F "preview=true"
```

For content with fields like "sequencing" or "genome", the system will automatically select the "fairagro_genomics" template.

## Supported Formats

### Source Formats
- **schema_org**: schema.org JSON-LD with `"@context": "https://schema.org/"`
- **oai_dc**: OAI-PMH DC metadata
- **ro_crate**: RO-Crate JSON-LD
- **darwin_core_csv**: Darwin Core CSV format
- **isa_json**: ISA JSON format
- **datacite_xml**: DataCite XML format
- **miappe_xlsx**: MIAPPE XLSX format

### Template Types
- **fairagro_searchhub**: Standard FAIRagro Search Hub template
- **fairagro_plant_phenotyping**: Plant phenotyping template (auto-selected for agronomy data)
- **fairagro_genomics**: Genomics template (auto-selected for sequencing data)
- **fairagro_sensor**: Sensor data template (auto-selected for measurement data)

## Error Handling

The API returns detailed error messages for various failure scenarios:

### Common Errors
- **400 Bad Request**: Invalid file format or malformed JSON/XML
- **422 Unprocessable Entity**: Invalid request parameters (e.g., missing file)
- **500 Internal Server Error**: Server-side errors during conversion

### Error Response Format
```json
{
  "detail": "Error message describing the issue"
}
```

## Testing

### Unit Tests

See `backend/tests/` for comprehensive unit tests:

- `test_template_field_path_extraction.py`: Tests for template field structure retrieval
- `test_source_format_detection.py`: Tests for automatic format detection
- `test_schema_org_to_arc_conversion.py`: Tests for schema.org to ARC conversion

### Integration Tests

The API is tested with:
- Schema.org JSON-LD files with various fields
- OAI-PMH metadata harvesting
- Batch processing of multiple files
- Template auto-selection based on content

## Response Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 422 | Unprocessable Entity (invalid parameters) |
| 500 | Internal Server Error |

## API Versioning

Current API version: `v1.0.0`

## Rate Limiting

The API does not currently implement rate limiting. For production use, consider implementing rate limiting at the application level.

## Security Considerations

1. **File Upload Validation**: All uploaded files are validated for format and size
2. **Input Sanitization**: User inputs are properly sanitized before processing
3. **Error Message Handling**: Detailed error messages are provided but do not expose sensitive system information
4. **CORS Configuration**: Only allowed origins can access the API

## Authentication

The API does not currently require authentication. For production deployment, consider implementing authentication mechanisms.

## Future Enhancements

1. **API Versioning**: Implement proper API versioning
2. **Authentication**: Add OAuth2 or JWT authentication
3. **Rate Limiting**: Implement rate limiting for production use
4. **Monitoring**: Add comprehensive monitoring and logging
5. **Documentation Updates**: Keep documentation in sync with API changes

## Contact

For questions or support, please refer to the project documentation or contact the development team.