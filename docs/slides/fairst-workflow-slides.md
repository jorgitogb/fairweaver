# FAIRweaver: Schema.org → ARC → FAIRagro Workflow

---

## FAIRagro Metadata Transformation Pipeline

```mermaid
flowchart LR
    subgraph INPUT["Input"]
        I["Schema.org JSON-LD<br/>(RDI / Research Data Infrastructure)"]
    end

    subgraph TRANSFORM["Transformation"]
        T["FAIRagro Template/Spec<br/>Applied as Transformation Rules"]
    end

    subgraph OUTPUT_A["Output A — ARC RO-Crate"]
        A["arc-rocrate-metadata.json<br/>(Annotated Research Context)"]
    end

    subgraph HARVEST["Harvest Paths to FAIRagro JSON"]
        H1["Path 1: DataHub Harvest<br/>(GitLab ARC Storage)"]
        H2["Path 2: Middleware API<br/>(Federated Service Orchestration)"]
    end

    subgraph OUTPUT_B["Output B — FAIRagro SearchHub"]
        B["FAIRagro schema.json<br/>→ FAIRagro SearchHub Ingestion"]
    end

    I --> T
    T --> A
    A -->|harvest| H1
    A -.->|orchestrate| H2
    H1 --> B
    H2 --> B

    classDef in fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef trans fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100
    classDef outa fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
    classDef harvest fill:#fce4ec,stroke:#c2185b,stroke-width:2px,stroke-dasharray: 5 5,color:#880e4f
    classDef outb fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#4a148c

    class I in
    class T trans
    class A outa
    class H1,H2 harvest
    class B outb
```

**Key Points:**

- **Sequential dependency**: Output B (FAIRagro JSON) is derived *from* Output A (ARC RO-Crate) — not a parallel output
- **Two harvest paths** converge on the same FAIRagro JSON schema:
  - **Path 1 (solid)**: Direct harvest from GitLab DataHub where ARCs are stored
  - **Path 2 (dashed)**: Via FAIRagro Middleware API (federated service that orchestrates the full workflow)
- Both paths produce identical `FAIRagro schema.json` ingested into SearchHub

---

## Three File Scenarios: Input → ARC → FAIRagro Output

| Case | Input File | ARC Output | FAIRagro Output |
|------|-----------|------------|-----------------|
| **Synthetic** | `schema-org-wheat-full.json` | `arc-ro-crate-wheat-full` ✅ compliant | Full extraction ✅ |
| **Real — Small** | `arc-ro-crate-dronflyover.json` (<10 MB) | Manual, partial ⚠️ | Partial — mappable fields only |
| **Real — Large** | `arc-ro-crate-muenchenberg-lte.json` (>100 MB) | Manual, partial ⚠️ | Basic harvest only |

**💡 If an ARC follows the FAIRagro specification → full metadata extraction. If not → only basic information is harvested.**

---

## Examining ARC Structure: Domain Objects at Different Depths

**Goal:**

- Understand how Agrischemas concepts map into ARC RO-Crate
- Show that equivalent domain concepts require very different traversal depths

```mermaid
flowchart TD
    I["@type: Dataset / additionalType: Investigation"]
    S["@type: Dataset / additionalType: Study"]
    A["@type: Dataset / additionalType: Assay<br/>drone_image_capture"]
    I -->|"hasPart"| S
    I -->|"hasPart"| A

    A -->|"measurementMethod"| DT["@type: DefinedTerm<br/>name: digital camera<br/>termCode: OBI:0001048<br/><b>Agrischemas: sensorType</b>"]

    S -->|"about"| LP["@type: LabProcess"]
    LP -->|"object"| SM["@type: Sample / additionalType: Material"]
    SM -->|"additionalProperty"| PV["@type: PropertyValue<br/>name: Organism<br/>value: Solanum tuberosum<br/>valueReference: NCBITaxon_4113<br/><b>Agrischemas: cropSpecies</b>"]

    classDef isa fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef leaf fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20

    class I,S,A isa
    class DT,LP,SM,PV leaf
```

**Example ARC RO-Crate:** UC13 drone-flyover

> **Note:** In the real data, Assay and Study are siblings under Investigation (via `hasPart`), not a nested chain. The Study does NOT contain the Assay via its own `hasPart` — that edge is empty. See the itemised data in `figure-code-snippets.md`.

---

## Müncheberg ARC: A Different Structural Pattern

**Goal:**
- Show another real ARC with a different structural pattern
- Reinforce that parser must handle multiple modeling conventions

```mermaid
flowchart TD
    I["@type: Dataset / additionalType: Investigation"]
    A1["@type: Dataset / additionalType: Assay<br/>crop-phenology-monitoring"]
    A2["@type: Dataset / additionalType: Assay<br/>plant-carbon-analysis"]
    AX["@type: Dataset / additionalType: Assay<br/>... 27+ assays"]
    I -->|"hasPart"| A1
    I -->|"hasPart"| A2
    I -.->|"hasPart"| AX

    S["@type: Dataset / additionalType: Study<br/>LTE V140 Müncheberg<br/>(disconnected — not in hasPart chain)"]

    SR["@type: Sample / additionalType: Source<br/>V140_MNC"]
    SR -->|"additionalProperty"| CV["@type: PropertyValue<br/>additionalType: CharacteristicValue<br/>name: Biological material ID<br/>value: zeamay_C38_7<br/>propertyID: MIAPPE_0040"]

    classDef isa fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef flat fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100
    classDef crop fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px,color:#1b5e20
    classDef disconnected fill:#f5f5f5,stroke:#bdbdbd,color:#9e9e9e,stroke-dasharray: 5 5

    class I isa
    class A1,A2,AX flat
    class S disconnected
    class SR,CV crop
```

| Aspect | Drone Flyover | Müncheberg LTE |
|--------|--------------|----------------|
| **Study entity** | Explicit, in hasPart chain | Present but disconnected (not in hasPart; `hasPart: []`) |
| **Crop species path (short)** | Study → LabProcess → Sample → PropertyValue (4 hops) | Source → additionalProperty → CharacteristicValue (2 hops) |
| **Crop species path (long)** | Same as short (only path) | ALSO via Study/LabProcess → object → Source → additionalProperty |
| **Sensor metadata** | Present (DefinedTerm) | Absent |
| **Assay count** | 1 | 27+ |

**Example ARC RO-Crate:** Müncheberg LTE

> **Note:** Müncheberg does have a Study entity (`studies/LTE-V140-Muencheberg/`) and LabProcess chains (via `Study.about`), just like the drone flyover. The key difference is that the Investigation's `hasPart` connects directly to the Assays, skipping the Study. The crop species path also has a shorter alternative at the Source level.

---

## Required Modeling Pattern & Standardization Gap

**Goal:**

- Define the required path for unambiguous extraction
- Identify what still needs standardization

```mermaid
flowchart TD
    I["@type: Dataset / additionalType: Investigation"]
    S["@type: Dataset / additionalType: Study"]
    A["@type: Dataset / additionalType: Assay"]
    I -.->|"hasPart"| S
    S -.->|"hasPart"| A

    LP["@type: LabProcess"]
    SM["@type: Sample / additionalType: Material"]
    PV["@type: PropertyValue<br/>name: Organism<br/>value: Solanum tuberosum<br/>propertyID: agrovoc:c_49904"]

    S -->|"about"| LP
    LP -->|"object"| SM
    SM -->|"additionalProperty"| PV

    classDef inactive fill:#f5f5f5,stroke:#bdbdbd,color:#9e9e9e,stroke-dasharray: 5 5
    classDef required fill:#e3f2fd,stroke:#1565c0,stroke-width:3px,color:#0d47a1
    classDef keyfield fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px,color:#1b5e20

    class I,A inactive
    class S,LP,SM required
    class PV keyfield
```

**In bold:** required objects/properties to represent Crop

**Example ARC RO-Crate:** UC13 drone-flyover

**Open questions:**

| | |
|---|---|
| **Structure: ?** | How to formally specify the required traversal path? |
| **propertyID: SSSOM mapping** | How to standardize ontology term mappings? |

---
