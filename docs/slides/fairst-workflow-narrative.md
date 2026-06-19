# FAIRweaver Workflow — Narrative Explanation

A continuous walkthrough of the Schema.org → ARC → FAIRagro pipeline.
For mixed-technical audiences: you get the concepts, the architecture, and the open problems.

---

## 1. The Problem

Agricultural research data lives across dozens of repositories with different schemas,
formats, and conventions. ARCs (Annotated Research Contexts) are the emerging standard for
packaging that data, and FAIRagro's Search Hub is where researchers discover it. Someone
needs to bridge the gap: take metadata from any source, map it into an ARC, then extract
the FAIRagro-specific schema for Search Hub ingestion. That someone is FAIRweaver's
conversion pipeline.

The challenge is structural. Every ARC is a JSON-LD graph, and different research groups
model the same domain concepts at different depths and in different graph locations. The
pipeline must handle that variability — or define conventions to eliminate it.

---

## 2. The Pipeline

The pipeline is strictly sequential. Output B (FAIRagro JSON) is derived from
Output A (ARC RO-Crate) — not a parallel output.

Two harvest paths converge on the same FAIRagro JSON schema:
- **Path 1 (solid):** Direct harvest from GitLab DataHub where ARCs are stored
- **Path 2 (dashed):** Via FAIRagro Middleware API (federated service)

Both paths produce identical FAIRagro schema.json ingested into SearchHub.

---

## 3. The Compliance Spectrum

| Case | Input File | ARC Output | FAIRagro Output |
|------|------------|------------|-----------------|
| **Synthetic** | `schema-org-wheat-full.json` | `arc-ro-crate-wheat-full` ✓ compliant | Full extraction ✓ |
| **Real — Small** | `arc-ro-crate-dronflyover.json` (<10 MB) | Manual, partial ⚠ | Partial — mappable fields only |
| **Real — Large** | `arc-ro-crate-muenchenberg-lte.json` (>100 MB) | Manual, partial ⚠ | Basic harvest only |

💡 If an ARC follows the FAIRagro specification → full metadata extraction.
If not → only basic information is harvested.

The pattern is clear: compliance determines extraction depth. Well-structured ARCs
enable full, automated extraction; unstructured ones yield only basic metadata.
This is not a pipeline limitation — it's a signal that the community needs modeling
conventions.

---

## 4. Inside the Graph (Slides 3 & 4)

Two real ARCs, one problem: same domain concepts at different graph depths.

### Drone Flyover (UC13)

Following the ISA hierarchy: Investigation → Study → Assay. Two Agrischemas concepts live
at very different traversal depths:

- **sensorType** is 1 hop from Assay via `measurementMethod` → DefinedTerm.
- **cropSpecies** is 4 hops from Study via `about` → LabProcess → `object` → Sample →
  `additionalProperty` → PropertyValue.

The sensorType path is short and direct. The cropSpecies path requires traversing five
nodes with specific predicates at each step. The parser must know the exact path — any
deviation and it loses the concept.

### Müncheberg LTE

A structurally different ARC. Investigation connects directly to 27+ Assays; a Study entity
exists (`studies/LTE-V140-Muencheberg/`) but is NOT linked via the Investigation's `hasPart`
chain. Crop species surfaces via a shorter alternative path: Source →
`additionalProperty` → CharacteristicValue (2 hops instead of 4). Müncheberg also has
the same long LabProcess chain as the drone flyover (via `Study.about` → LabProcess →
`object` → Source → `additionalProperty`), so both paths coexist. Sensor metadata is
absent because this ARC is about crop phenology, not remote sensing.

### What This Tells Us

| Aspect | Drone Flyover | Müncheberg LTE |
|---|---|---|
| Study entity | Explicit, in hasPart chain | Present but disconnected (not in hasPart) |
| Crop species path (short) | 4 hops via LabProcess | 2 hops via additionalProperty |
| Crop species path (long) | Same as short (only path) | ALSO via LabProcess → Source → additionalProperty |
| Sensor metadata | Present (DefinedTerm) | Absent |
| Assay count | 1 | 27+ |

A generic parser cannot reliably extract crop species from both ARCs without knowing
which structural pattern to apply. This variability is the core motivation for
standardization.

---

## 5. The Standardization Gap (Slide 5)

After examining both ARCs, a required traversal path emerges for unambiguous crop
extraction:

```
Study → about → LabProcess → object → Sample/additionalType:Material
  → additionalProperty → PropertyValue/propertyID
```

The terminal node — PropertyValue with a `propertyID` — is critical. `name: Organism` and
`value: Solanum tuberosum` are human-readable but machine-ambiguous. The `propertyID`
linking to an ontology term (e.g., `agrovoc:c_49904`) makes it semantically precise and
machine-resolvable.

| Question | Details |
|----------|---------|
| **Structure: ?** | How to formally specify the required traversal path? |
| **propertyID: SSSOM mapping** | How to standardize ontology term mappings? |

These are not FAIRweaver problems. They are community-level standardization problems
that FAIRweaver exposes and quantifies.

---

## Glossary

| Term | Meaning |
|---|---|
| **ARC** | Annotated Research Context — a self-contained research package with data, metadata, and code |
| **RO-Crate** | Research Object Crate — a JSON-LD packaging format that ARC builds on |
| **JSON-LD** | JSON with a `@context` that maps keys to IRIs, enabling semantic linking |
| **Agrischemas** | A family of schema.org extensions for agricultural research concepts |
| **FAIRagro Schema** | The specific JSON structure that FAIRagro Search Hub ingests |
| **propertyID** | A field in PropertyValue that links to an ontology term (e.g., `agrovoc:c_49904`) |
| **SSSOM** | Simple Standard for Sharing Ontological Mappings — a format for cross-ontology term alignment |
| **ISA** | Investigation → Study → Assay — the standard hierarchy for experimental metadata |
| **Pivot** | An intermediate schema that FAIRweaver converts source formats into before producing output |
| **OAI-PMH** | Open Archives Initiative Protocol for Metadata Harvesting — a standard for repository interoperability |
