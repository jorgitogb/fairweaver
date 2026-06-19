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

## 2. The Pipeline (Slide 1)

The pipeline is strictly sequential. Schema.org JSON-LD from an RDI (Research Data
Infrastructure) enters at the top, gets transformed by FAIRagro templates, and produces
two outputs in order:

1. **Output A — ARC RO-Crate.** A JSON-LD document that follows the ARC specification.
2. **Output B — FAIRagro JSON.** Derived from Output A, not produced independently.

Output B's dependency on Output A is the key architectural insight. If the ARC is
incomplete, the FAIRagro extraction is incomplete too. There is no shortcut.

Two paths feed the ARC into Search Hub:

- **Path 1 (direct harvest):** GitLab DataHub stores the ARC; a harvester reads it and
  produces FAIRagro JSON.
- **Path 2 (orchestrated):** The FAIRagro Middleware API coordinates the full workflow,
  from harvest through conversion to ingestion. The dashed line in the diagram signals
  this path is still being stabilized.

Both paths converge on the same FAIRagro schema.json consumed by Search Hub.

---

## 3. The Compliance Spectrum (Slide 2)

Three test files illustrate the relationship between ARC quality and extraction depth:

**Synthetic (`schema-org-wheat-full.json`):** A manually crafted input designed to cover
every FAIRagro-required field. The resulting ARC is fully compliant; extraction gets
everything. This proves the pipeline works when the input follows the rules.

**Real — Small (`arc-ro-crate-dronflyover.json`, <10 MB):** An actual agronomic ARC from
the UC13 drone flyover. It follows the ISA Investigation → Study → Assay hierarchy but
uses non-standard property names and missing optional fields. Result: partial extraction.
Only fields that map unambiguously to the FAIRagro schema come through.

**Real — Large (`arc-ro-crate-muenchenberg-lte.json`, >100 MB):** A long-term experiment
ARC from Müncheberg with 27+ assays but a flatter structure. Many domain-specific fields
don't match any FAIRagro template key. Result: basic harvest only — title, description,
identifier, creator. Most of the rich agronomic detail is lost.

The pattern is clear: compliance determines extraction depth. If an ARC follows the
FAIRagro specification, you get full extraction. If not, you get the intersection of
what's present and what's mappable. This is not a pipeline limitation — it's a signal
that the community needs modeling conventions.

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

Two open questions remain:

1. **Structure specification.** How do we formally specify a required graph traversal path
   so that tools can validate compliance automatically? A shape expression (ShEx) or
   SHACL shape? A simple property-path DSL in the pivot registry YAML?

2. **Ontology mapping standardization.** `propertyID` values need a shared vocabulary of
   mappings so that every ARC uses the same ontology term for "crop species." SSSOM
   (Simple Standard for Sharing Ontological Mappings) is a candidate — but it needs
   community adoption.

These are not FAIRweaver problems. They are community-level standardization problems that
FAIRweaver exposes and quantifies.

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
