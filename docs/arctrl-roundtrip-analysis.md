# arctrl Round-Trip Fidelity Analysis

## Summary

Converting an ARC RO-Crate JSON-LD → ARC Scaffold (via arctrl) → ARC RO-Crate JSON-LD results in **significant data loss** and **non-equivalent output**.

This document was produced to support a bug report / feature request to the arctrl library developers.

## Test Case

**Input:** `sample-data/demo/arc-ro-crate-wheat-basic.json` (11 entities)

- Investigation: `#Investigation_wheat`
- Study: `#Study_wheat`
- Assay: `#Assay_wheat`
- Persons: `#Mühlhaus_Timo`, `#Maus_Oliver`
- Organization: `#Organization_RPTU_University_of_Kaiserslautern_Plant_Phenomics_Group`
- Files: 3 sample TIFF files

**Process:**

1. Parse input RO-Crate
2. Build arctrl objects (`ArcInvestigation`, `ArcStudy`, `ArcAssay`, `Person`)
3. Write scaffold via `ARC.Write()`
4. Load scaffold via `ARC.load()`
5. Export RO-Crate via `ARC.to_rocrate_json_string()`

**Output:** 11 entities (same count, different content)

## Issues Identified

### 1. Entity ID Transformation

**Input IDs:**

```
#Investigation_wheat
#Study_wheat
#Assay_wheat
#Mühlhaus_Timo
#Maus_Oliver
#Organization_RPTU_University_of_Kaiserslautern_Plant_Phenomics_Group
assays/wheat/dataset/sample1.tiff
assays/wheat/dataset/sample2.tiff
assays/wheat/dataset/sample3.tiff
```

**Output IDs:**

```
./
studies/Study_wheat/
assays/Assay_wheat/
http://orcid.org/0000-0003-3925-6778
http://orcid.org/0000-0002-8241-5300
#Organization_RPTU_University_of_Kaiserslautern
```

**Problem:** All original fragment identifiers are lost. arctrl normalizes to path-based IDs.

### 2. File References Lost

All 3 sample file entities (`sample1.tiff`, `sample2.tiff`, `sample3.tiff`) are completely absent from the output.

**Problem:** arctrl does not preserve file entities unless they are explicitly mapped to the ISA data model.

### 3. Person Identifier Changes

**Input:**

```json
{
  "@id": "#Mühlhaus_Timo",
  "@type": "Person",
  "name": "Timo Mühlhaus",
  "identifier": {
    "@type": "PropertyValue",
    "propertyID": "orcid",
    "value": "0000-0003-3925-6778"
  }
}
```

**Output:**

```json
{
  "@id": "http://orcid.org/0000-0003-3925-6778",
  "@type": "Person",
  "name": "Timo Mühlhaus"
}
```

**Problem:** ORCID is used as the `@id` instead of preserving the original fragment identifier.

### 4. Context Version Change

**Input:**

```json
"@context": [
  "https://w3id.org/ro/crate/1.1/context",
  {"@vocab": "https://schema.org/"}
]
```

**Output:**

```json
"@context": [
  "https://w3id.org/ro/crate/1.2/context",
  {
    "Sample": "https://bioschemas.org/Sample",
    "LabProtocol": "https://bioschemas.org/LabProtocol",
    "LabProcess": "https://bioschemas.org/LabProcess",
    "computationalTool": "https://bioschemas.org/properties/computationalTool",
    "labEquipment": "https://bioschemas.org/properties/labEquipment",
    "reagent": "https://bioschemas.org/properties/reagent",
    "intendedUse": "https://bioschemas.org/properties/intendedUse",
    "executesLabProtocol": "https://bioschemas.org/properties/executesLabProtocol",
    "parameterValue": "https://bioschemas.org/properties/parameterValue",
    "columnIndex": "https://w3id.org/ro/terms/arc#columnIndex"
  }
]
```

**Problem:** RO-Crate context version changes from 1.1 to 1.2, and vocabulary mappings differ.

### 5. Field Value Changes

**datePublished:**

- Input: `"2024-09-15"`
- Output: `"2026-06-24T15:16:18.592"` (current timestamp)

**license:**

- Input: `"https://creativecommons.org/licenses/by/4.0/"`
- Output: `{"@id": "#LICENSE"}` (object reference)

**identifier:**

- Input: `"10.5447/fairweaver/2024/wheat-drought-001"`
- Output: `"wheat-drought-001"` (sanitized)

### 6. Entity Type Changes

**Input entity types:**

```
CreativeWork: 1
Dataset: 4
Person: 2
Organization: 1
File: 3
```

**Output entity types:**

```
Organization: 1
Person: 2
DefinedTerm: 2
PropertyValue: 1
Dataset: 3
CreativeWork: 2
```

**Problem:** New entity types appear (`DefinedTerm`, `PropertyValue`), `File` entities disappear.

## Impact

### FAIRagro Compliance

The output RO-Crate **does not maintain FAIRagro compliance** because:

1. File references are lost (required for data provenance)
2. Identifier changes break cross-references
3. Context version change may affect validation

### Round-Trip Fidelity

The transformation is **lossy**:

- 9 out of 11 original entity IDs are lost
- All file references disappear
- Metadata fields are modified or regenerated

## Questions for arctrl Developers

1. **Is there a way to preserve original entity IDs** when writing/reading scaffolds?
2. **How should file entities be handled?** Should they be added to the `Datamap` or tracked separately?
3. **Can the RO-Crate context version be controlled** (e.g., force 1.1 instead of 1.2)?
4. **Is there a "preserve metadata" mode** that keeps original field values instead of regenerating them?
5. **What is the recommended workflow** for round-trip conversion (RO-Crate → Scaffold → RO-Crate) without data loss?

## Environment

- arctrl version: 3.0.5
- Python: 3.14.4
- Platform: macOS
- FAIRweaver commit: (latest on `main` at time of analysis)

## Test Code

```python
import json
import tempfile
from pathlib import Path
from arctrl import ARC
from arc_scaffold_builder import build_scaffold_from_rocrate

# Load input
with open("sample-data/demo/arc-ro-crate-wheat-basic.json") as f:
    input_rocrate = json.load(f)

# Create scaffold
with tempfile.TemporaryDirectory() as tmp:
    scaffold_dir = Path(tmp) / "test"
    build_scaffold_from_rocrate(input_rocrate, scaffold_dir)

    # Read back and export
    arc = ARC.load(str(scaffold_dir))
    output_rocrate_str = arc.to_rocrate_json_string(spaces=2)(arc)
    output_rocrate = json.loads(output_rocrate_str)

# Compare input vs output
print(f"Input entities: {len(input_rocrate['@graph'])}")
print(f"Output entities: {len(output_rocrate['@graph'])}")
```

## Conclusion

The current arctrl round-trip conversion is **not suitable for preserving FAIRagro-compliant RO-Crate metadata**. The scaffold is useful for editing in ARC tools, but exporting back to RO-Crate loses critical information.

### Recommendations

1. Keep the original RO-Crate alongside the scaffold.
2. Use manual `@graph` construction (as in `main.py::_fallback_convert_to_arc`) for lossless conversion.
3. Wait for arctrl improvements to preserve metadata fidelity before relying on round-trip conversion.
