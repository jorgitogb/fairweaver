# API Documentation

## Overview

The FAIRagro-MI backend exposes a REST API for metadata conversion, validation, and ARC export.

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

## Endpoints

### Metadata Conversion

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pivots` | List registered pivot profiles |
| POST | `/pivots/recommend` | AI-recommend best pivot for an input file |
| GET | `/mappings` | List available YAML mappings |
| POST | `/mappings/generate` | AI-generate a YAML mapping draft |
| POST | `/mappings/validate` | Validate a YAML mapping file |
| POST | `/convert` | Convert input → pivot JSON-LD |
| POST | `/convert/chain` | Bidirectional: source → pivot → target format |
| POST | `/convert/arc-export` | Convert Schema.org → ARC RO-Crate |

### Harvest & OAI-PMH

| Method | Path | Description |
|--------|------|-------------|
| POST | `/harvest/convert` | Harvest from OAI-PMH + convert to pivot JSON-LD |
| GET | `/oai-pmh` | OAI-PMH 2.0 server (fairagro_arc format) |
| POST | `/list-sets` | List OAI-PMH metadata sets |

### ARC & Validation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/arc/validate/fairagro` | Validate ARC against FAIRagro template |
| POST | `/compliance/classify` | Classify FAIRagro compliance level |
| GET | `/template-fields/{id}` | ARC template field structure |
| POST | `/arc/scaffold` | Generate ARC scaffold ZIP from RO-Crate |

### Utilities

| Method | Path | Description |
|--------|------|-------------|
| GET | `/source-formats/schema-org` | Schema.org field definitions |

## Example: Convert to ARC RO-Crate

```bash
curl -X POST "http://localhost:8000/convert/arc-export" \
  -F "file=@dataset.json" \
  -F "source_format=auto" \
  -F "pivot_id=fairagro_searchhub" \
  -F "preview=true"
```

## Example: Validate ARC

```bash
curl -X POST "http://localhost:8000/arc/validate/fairagro" \
  -F "file=@arc-ro-crate.json"
```

## Example: Generate Scaffold

```bash
curl -X POST "http://localhost:8000/arc/scaffold" \
  -F "file=@ro-crate.json" \
  -F "arc_name=my-arc" \
  --output my-arc.zip
```

## Error Handling

- `400` — Invalid input file or unsupported format
- `422` — Invalid request parameters
- `500` — Server-side error during conversion

Error response:
```json
{"detail": "Error message describing the issue"}
```
