# FAIRweaver Mappings

Community-contributed YAML mapping files for format → pivot conversion.

## Schema

```yaml
source_format: isa_json       # Required: source format ID (e.g., isa_json, datacite_xml)
pivot: agrischemas_fieldtrial # Required: pivot ID from registry
version: "0.1.0"        # Required: semantic version
author: fairweaver-community # Optional: author name
description: "Maps..."      # Optional: description
field_rules:               # Required: array of field rules
  - source: study.identifier   # Source field path (nullable = computed/derived)
    target: identifier       # Required: target pivot field
    required: true         # Is required by pivot profile
    confidence: 0.95     # 0.0-1.0 mapping confidence
    transform: null       # Optional: transform function name
    note: "..."        # Optional: human-readable note
```

## Field Rules

| Field | Required | Description |
|-------|----------|-------------|
| `source` | Yes* | Dot-notation path to field. Use `null` if computed/derived. |
| `target` | Yes | Target field name from pivot profile |
| `required` | Yes | Whether pivot marks this as required |
| `confidence` | Yes | 0.0 (none) to 1.0 (exact) |
| `transform` | No | Transform function name |
| `note` | No | Human-readable explanation |

### Confidence Scores

| Score | Meaning |
|-------|---------|
| 0.95-1.0 | Exact field name match |
| 0.6-0.9 | Fuzzy/alias match |
| 0.0-0.5 | No direct equivalent - manual entry needed |

### Transform Functions

Built-in transforms (can be extended):
- `date_iso8601` - Parse to ISO 8601 date
- `uppercase` - Convert to uppercase
- `lowercase` - Convert to lowercase
- `strip` - Trim whitespace
- `uri` - Validate as URI

## Adding a New Mapping

1. Create `mappings/<source>-<pivot>.yaml`
2. Follow the schema above
3. Test with `POST /mappings/validate` endpoint

## Example

See `isa_json-agrischema_fieldtrial.yaml` for a complete example.

## License

YAML mappings are CC0 (public domain). Contribute freely!