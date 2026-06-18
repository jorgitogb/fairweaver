# FAIRweaver: Schema.org → ARC → FAIRagro Workflow

---

## Slide 1 — FAIRagro Metadata Transformation Pipeline

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

```mermaid
flowchart TD
    I["@type: Dataset / additionalType: Investigation"]
    S["@type: Dataset / additionalType: Study"]
    A["@type: Dataset / additionalType: Assay"]
    I -->|"hasPart"| S
    S -->|"hasPart"| A

    A -->|"measurementMethod"| DT["@type: DefinedTerm<br/>name: digital camera<br/>termCode: OBI:0001048"]
    label1["(Agrischemas: sensorType)"]

    S -->|"about"| LP["@type: LabProcess"]
    LP -->|"object"| SM["@type: Sample / additionalType: Material"]
    SM -->|"additionalProperty"| PV["@type: PropertyValue<br/>name: Organism<br/>value: Solanum tuberosum<br/>propertyID: agrovoc:c_49904"]
    label2["(Agrischemas: cropSpecies)"]

    classDef isa fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef leaf fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
    classDef labelbox fill:none,stroke:none,color:#2e7d32

    class I,S,A isa
    class DT,LP,SM,PV leaf
    class label1,label2 labelbox
```

**Example ARC RO-Crate:** UC13 drone-flyover

---

## Slide 4 — Required Modeling Pattern & Standardization Gap

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

