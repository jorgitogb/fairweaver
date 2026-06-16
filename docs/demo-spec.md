# FAIRagro Demo Suite — Specification

## Goal
Create complete demo package: Schema.org → ARC RO-Crate conversion with 3 FAIRagro compliance levels (basic/intermediate/full). Includes mock data (2 themes × 3 levels), PlantUML architecture diagrams, UI compliance badge, and documentation.

## Business Value
- Showcase FAIRweaver at BioHackathon Germany 2026
- Reusable test data for CI/CD
- Non-technical audience understanding of conversion pipeline
- Validate FAIRagro template compliance classification

## Functional Requirements

### FR-1: Mock Data Generation (12 files)
`sample-data/demo/`:
- **Theme A**: Wheat phenotyping (drone NDVI, drought stress, RPTU Kaiserslautern)
- **Theme B**: Maize genomics (RNA-Seq, heat stress, IPK Gatersleben)
- Each theme: 3 Schema.org files + 3 ARC RO-Crate files (basic/intermediate/full)

### FR-2: Compliance Level Definitions (from `fairagro_template.yaml`)

| Level | Sections Included |
|-------|------------------|
| **Basic** 🔴 | `required_fields` only — Investigation(name, description, creator, identifier, license, datePublished, contacts, publications) + Study(name, description, designDescriptors) + Assay(name, description, measurementTechnique, measurementMethod, technologyType, technologyPlatform) |
| **Intermediate** 🟡 | Basic + `recommended_fields` + all `validation_rules` pass |
| **Full** 🟢 | Intermediate + `publishable_requirements` + `reproducible_requirements` + `fairagro_requirements` |

### FR-3: POST /compliance/classify
New endpoint accepting file, returning compliance level plus field breakdown.

### FR-4: UI Compliance Badge
Colored pill (🔴 Basic / 🟡 Intermediate / 🟢 Full) shown when Schema.org file loaded.

### FR-5: PlantUML Diagrams (3)
- Detailed technical (C4 Container model)
- Simplified executive (high-level flow)
- Animated step-by-step (slide-friendly)

### FR-6: Documentation (`docs/demo/`)
- ARC composition breakdown
- Compliance comparison table (Default ARC vs 3 FAIRagro levels)
- Field mapping matrix

## Non-Functional Requirements
- Generator script idempotent, completions < 5s
- All 12 files use coherent cross-file data (same researchers, locations)
- All generated files pass `FairagroArcValidator` at target level

## Constraints
- Python 3.12+, `arctrl` for ARC generation
- PlantUML source (`.puml`) committed
- No new npm dependencies for badge — use Tailwind existing colors

## Acceptance Criteria
1. [ ] `generate_demo_data.py` creates 12 files successfully
2. [ ] All ARC files pass `FairagroArcValidator` at target level
3. [ ] `POST /compliance/classify` returns correct level for each Schema.org file
4. [ ] UI shows correct badge for each file
5. [ ] 3 PlantUML diagrams render cleanly
6. [ ] `ruff check`, `npm run typecheck`, `npm test` all pass

## Risks
- arctrl version mismatch — pin in pyproject.toml
- Validator strictness — test early, adjust template if needed

## Dependencies
- arctrl (present in `.venv`)
- Existing FAIRweaver API endpoints

## Test Strategy
- **Unit**: validate generated file structure and compliance levels
- **Integration**: full conversion pipeline with all 6 Schema.org files
- **Regression**: add to existing test suite
