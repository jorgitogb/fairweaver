# Compliance Level Comparison

## FAIRagro Template Requirements (from `fairagro_template.yaml`)

| Section | Basic | Intermediate | Full |
|---------|-------|-------------|------|
| Investigation required fields | name, description, creator, identifier, license, datePublished, contacts, publications | ✓ | ✓ |
| Investigation recommended fields | — | alternative_titles, keywords, publisher, investigationIdentifier | ✓ |
| Study required fields | name, description, designDescriptors | ✓ | ✓ |
| Study recommended fields | — | about, studyDesignType, studyPersonnel | ✓ |
| Assay required fields | name, description, measurementTechnique, measurementMethod, technologyType, technologyPlatform | ✓ | ✓ |
| Assay recommended fields | — | about, assayCategory, assayType | ✓ |
| Crop metadata (study) | — | — | crop_species, crop_pest |
| Sensor metadata (assay) | — | — | sensorType, sensorPlatformType, manufacturer, model |
| Validation rules | — | All rules pass | ✓ |
| Publication requirements | — | — | publications, funder, ORCIDs |
| Reproducibility | — | — | CWL workflows, runs |
| Data path annotations | — | — | Resolvable data paths |

## Compliance Classification Thresholds

Computed by `POST /compliance/classify`:

| Level | Required Score | Recommended Score | Full Score |
|-------|---------------|-------------------|------------|
| Basic | ≥ 80% | — | — |
| Intermediate | ≥ 80% | ≥ 40% | — |
| Full | ≥ 90% | ≥ 70% | ≥ 50% |

## Example: Wheat Theme

| File | Required Score | Recommended Score | Full Score | Classified Level |
|------|---------------|-------------------|------------|-----------------|
| `schema-org-wheat-basic.json` | 100% | 57% | 0% | Basic |
| `schema-org-wheat-intermediate.json` | 100% | 71% | 0% | Intermediate |
| `schema-org-wheat-full.json` | 100% | 71% | 62% | Full |

## Visual Badge

In the UI, compliance level is shown as a colored pill:

```
🛡 Basic          — red background
🛡 Intermediate   — amber/yellow background
🛡 Full           — green background
```

Each badge shows the level name and numeric score.
