---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    font-size: 24px;
  }
  h1 {
    color: #1565c0;
  }
  h2 {
    color: #2e7d32;
  }
  table {
    font-size: 18px;
  }
  blockquote {
    border-left: 4px solid #2e7d32;
    padding-left: 16px;
    color: #555;
  }
  img {
    display: block;
    margin: 0 auto;
    max-height: 450px;
  }
---

# FAIRweaver: Schema.org → ARC → FAIRagro Workflow

---

## Slide 1 — FAIRagro Metadata Transformation Pipeline

![Pipeline diagram](diagrams/slide1-pipeline.png)

---

## Slide 1 — Key Points

- **Sequential dependency**: Output B (FAIRagro JSON) is derived *from* Output A (ARC RO-Crate) — not a parallel output
- **Two harvest paths** converge on the same FAIRagro JSON schema:
  - **Path 1 (solid)**: Direct harvest from GitLab DataHub where ARCs are stored
  - **Path 2 (dashed)**: Via FAIRagro Middleware API (federated service that orchestrates the full workflow)
- Both paths produce identical `FAIRagro schema.json` ingested into SearchHub

---

## Slide 2 — Three File Scenarios: Input → ARC → FAIRagro Output

| Case | Input File | ARC Output | FAIRagro Output |
|------|-----------|------------|-----------------|
| **Synthetic** | `schema-org-wheat-full.json` | `arc-ro-crate-wheat-full` ✅ compliant | Full extraction ✅ |
| **Real — Small** | `arc-ro-crate-dronflyover.json` (<10 MB) | Manual, partial ⚠️ | Partial — mappable fields only |
| **Real — Large** | `arc-ro-crate-muenchenberg-lte.json` (>100 MB) | Manual, partial ⚠️ | Basic harvest only |

**💡 If an ARC follows the FAIRagro specification → full metadata extraction. If not → only basic information is harvested.**

---

## Slide 3 — Examining ARC Structure: Domain Objects at Different Depths

**Goal:**
- Understand how Agrischemas concepts map into ARC RO-Crate
- Show that equivalent domain concepts require very different traversal depths

![Drone flyover structure](diagrams/slide3-drone.png)

**Example ARC RO-Crate:** UC13 drone-flyover

---

## Slide 4 — Müncheberg ARC: A Different Structural Pattern

**Goal:**
- Show another real ARC with a different structural pattern
- Reinforce that parser must handle multiple modeling conventions

![Müncheberg structure](diagrams/slide4-muenchenberg.png)

**Example ARC RO-Crate:** Müncheberg LTE

---

## Slide 4 — Comparison: Drone Flyover vs Müncheberg

| Aspect | Drone Flyover | Müncheberg LTE |
|--------|--------------|----------------|
| **Study entity** | Explicit | Absent |
| **Crop species path** | Study → LabProcess → Sample → PropertyValue | Source → additionalProperty → CharacteristicValue |
| **Crop species depth** | 4 hops | 2 hops |
| **Sensor metadata** | Present | Absent |
| **Assay count** | 1 | 27+ |

---

## Slide 5 — Required Modeling Pattern & Standardization Gap

**Goal:**
- Define the required path for unambiguous extraction
- Identify what still needs standardization

![Required pattern](diagrams/slide5-required.png)

**In bold:** required objects/properties to represent Crop

**Example ARC RO-Crate:** UC13 drone-flyover

---

## Slide 5 — Open Questions

| | |
|---|---|
| **Structure: ?** | How to formally specify the required traversal path? |
| **propertyID: SSSOM mapping** | How to standardize ontology term mappings? |
