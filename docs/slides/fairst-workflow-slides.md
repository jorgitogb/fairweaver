# FAIRweaver: Schema.org → ARC → FAIRagro Workflow

---

## Slide 1 — High-Level Pipeline

```mermaid
flowchart LR
    S["<b>Schema.org JSON-LD</b>"]:::primary --> P["Parse & Normalize"]
    R["RO-Crate"]:::supported --> P
    O["INSPIRE / SQL"]:::other --> P
    P --> C["ARC RO-Crate<br/>Generation"]
    C --> V["FAIRagro<br/>Validation"]
    V --> J["FAIRagro<br/>JSON-LD"]
    V --> F["ARC RO-Crate<br/>File"]

    classDef primary fill:#bbdefb,stroke:#1565c0,stroke-width:3px,color:#0d47a1
    classDef supported fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20
    classDef other fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray: 5 5,color:#616161
```

**What happens:**

- **Primary input:** Schema.org JSON-LD 
- **Other sources:** INSPIRE, SQL Database
- `Parse & Normalize`: format detection, plugin load, template selection
- **ARC Generation:** builds Investigation → Study → Assay hierarchy
- **Validation:** `FairagroArcValidator` checks against `fairagro_arc_v2` template (DataPLANT + FAIRagro)
- **Output:** FAIRagro Search Hub JSON-LD + downloadable ARC RO-Crate file

---

## Slide 2 — Three ARC RO-Crate Examples: Structural Comparison

### Option A: Markdown Table

| Aspect | Drone Flyover | Benjamin (ZALF) | Wheat Full (Synthetic) |
|--------|---------------|-----------------|------------------------|
| **Domain** | Drone imagery / phenotyping | Long-term crop phenology | Wheat drought phenotyping |
| **Context** | Bioschemas (`Sample`, `LabProtocol`, `LabProcess`) | Bioschemas + MIAPPE propertyIDs | Schema.org only |
| **Entities** | 1 Investigation, 1 Study, 1 Assay, 240+ Files | 1 Investigation, 1 Study, 1 Assay, 30+ Processes/Samples | 1 Investigation, 1 Study, 1 Assay, 3 Files |
| **Investigation** | Minimal (name, description, creator) | Implicit (via Organization/Person) | Full (name, description, creator, identifier, license, datePublished, contacts, publications) |
| **Study** | Only via `about` LabProcess | Via Source/Sample/Process chain | Explicit Study entity with designDescriptors, crop_species, crop_pest |
| **Assay** | Minimal (name, measurementTechnique) | Via LabProcess/Protocol | Full (measurementTechnique, measurementMethod, technologyType, technologyPlatform, instrument) |
| **Crop Metadata** | ❌ None | Via PropertyValue (MIAPPE propertyIDs) | Explicit fields (crop_species, crop_pest, URIs) |
| **Sensor Metadata** | ❌ None | ❌ None | Explicit (drone_manufacturer, drone_model) |
| **Location/Geo/Soil** | ❌ None | ❌ None | Explicit entities |
| **Data Files** | 240+ image files (labeled/unlabeled) | Referenced via columnIndex | 3 TIFF samples |
| **Compliance Level** | Basic RO-Crate | Deep ISA + MIAPPE | Full FAIRagro-ready |

### Option B: Mermaid Entity Hierarchy Diagram

```mermaid
flowchart TB
    subgraph DF["Drone Flyover"]
        DF_I["Dataset<br/>additionalType: Investigation<br/>name, description, creator"]
        DF_S["Dataset<br/>additionalType: Study"]
        DF_A["Dataset<br/>additionalType: Assay<br/>measurementTechnique"]
        DF_F["240+ File entities<br/>labeled + unlabeled"]
        DF_I --> DF_S
        DF_S --> DF_A
        DF_A --> DF_F
    end

    subgraph BEN["Benjamin (ZALF)"]
        BEN_O["Organization<br/>Leibniz-ZALF"]
        BEN_P["Person<br/>Dietmar Barkusky"]
        BEN_SRC["Sample<br/>additionalType: Source<br/>V140_MNC"]
        BEN_PROC["LabProcess<br/>CropPhenology_0..27"]
        BEN_PROTO["LabProtocol<br/>CropPhenology"]
        BEN_SAMP["Sample<br/>additionalType: Sample<br/>V140_MNC_1971..2001"]
        BEN_PV["PropertyValue<br/>CharacteristicValue<br/>MIAPPE propertyIDs"]
        BEN_O --> BEN_P
        BEN_SRC --> BEN_PV
        BEN_PROC --> BEN_PROTO
        BEN_PROC --> BEN_SRC
        BEN_PROC --> BEN_SAMP
        BEN_PROC --> BEN_PV
    end

    subgraph WF["Wheat Full (Synthetic)"]
        WF_I["Dataset<br/>additionalType: Investigation<br/>FULL citation block"]
        WF_S["Dataset<br/>additionalType: Study<br/>designDescriptors, crop_species, crop_pest"]
        WF_A["Dataset<br/>additionalType: Assay<br/>measurementTechnique, method, technologyType, platform"]
        WF_INST["Sensor<br/>Micasense RedEdge-MX"]
        WF_LOC["Place + GeoCoordinates"]
        WF_GEO["DefinedRegion<br/>country, state, county"]
        WF_SOIL["Thing<br/>additionalType: SoilType<br/>Luvisol"]
        WF_PROC["Thing<br/>additionalType: Process<br/>UAV-based remote sensing"]
        WF_PUB["ScholarlyArticle"]
        WF_I --> WF_S
        WF_I --> WF_PUB
        WF_S --> WF_A
        WF_A --> WF_INST
        WF_I --> WF_LOC
        WF_I --> WF_GEO
        WF_I --> WF_SOIL
        WF_I --> WF_PROC
    end

    classDef df fill:#bbdefb,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef ben fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100
    classDef wf fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20

    class DF_I,DF_S,DF_A,DF_F df
    class BEN_O,BEN_P,BEN_SRC,BEN_PROC,BEN_PROTO,BEN_SAMP,BEN_PV ben
    class WF_I,WF_S,WF_A,WF_INST,WF_LOC,WF_GEO,WF_SOIL,WF_PROC,WF_PUB wf
```

---

## Slide 3 — FAIRagro Compliance: Required Fields Assessment

| FAIRagro Block | Required Field | Drone Flyover | Benjamin (ZALF) | Wheat Full |
|----------------|----------------|---------------|-----------------|------------|
| **citation** | `name` | ⚠️ In Investigation | ⚠️ Implicit | ✅ Investigation.name |
| | `description` | ⚠️ In Investigation | ⚠️ Implicit | ✅ Investigation.description |
| | `creator` | ✅ In Investigation | ⚠️ Person exists, not linked as creator | ✅ Investigation.creator[] |
| | `identifier` | ❌ Missing | ❌ Missing | ✅ Investigation.identifier |
| | `license` | ❌ Missing | ❌ Missing | ✅ Investigation.license |
| | `datePublished` | ❌ Missing | ❌ Missing | ✅ Investigation.datePublished |
| **generalExtended** | `license` | ❌ Missing | ❌ Missing | ✅ Investigation.license |
| | `sourceDatasetURI` | ❌ Missing | ❌ Missing | ✅ `@id` present |
| **crop** | `cropSpecies` | ❌ None | ⚠️ Via MIAPPE propertyID (zeamay, seccer, betvul...) | ✅ Study.crop_species |
| | `cropPest` | ❌ None | ❌ None | ✅ Study.crop_pest |
| | `cropSpeciesURI` | ❌ None | ❌ None | ✅ Study.crop_species_uri |
| | `cropPestURI` | ❌ None | ❌ None | ✅ Study.crop_pest_uri |
| **sensor** | `sensorType` | ❌ None | ❌ None | ✅ Assay.measurementTechnique |
| | `sensorPlatformType` | ❌ None | ❌ None | ✅ Assay.measurementMethod |
| | `sensorPlatformManufacturerName` | ❌ None | ❌ None | ✅ `#Instrument_wheat` |
| | `sensorPlatformModelName` | ❌ None | ❌ None | ✅ `#Instrument_wheat.name` |
| **location** | `longitude` | ❌ None | ❌ None | ✅ Location.geo.longitude |
| | `latitude` | ❌ None | ❌ None | ✅ Location.geo.latitude |
| **geographicCoverage** | `country` | ❌ None | ❌ None | ✅ GeographicCoverage.country |
| | `state` | ❌ None | ❌ None | ✅ GeographicCoverage.state |
| | `county` | ❌ None | ❌ None | ✅ GeographicCoverage.county |

**Legend:** ✅ Complete | ⚠️ Partial | ❌ Missing

**Summary:**

- **Wheat Full**: 100% — meets all FAIRagro Search Hub required fields
- **Benjamin**: ~20% — has crop data (MIAPPE), but missing citation, sensor, location, geo blocks
- **Drone Flyover**: ~10% — file-centric with minimal metadata structure

---

## Slide 4 — Gap Analysis & Transformation Pipeline

### Option A: Gap Analysis Summary

```
FAIRagro Mapping Pipeline (arc_ro_crate-fairagro_searchhub.yaml)
────────────────────────────────────────────────────────────────
ARC RO-Crate  →  21 field_rules  →  FAIRagro Search Hub JSON-LD
    │
    ├── Citation Block (7 rules)        ← Investigation fields
    ├── GeneralExtended Block (2 rules) ← license, @id
    ├── Crop Block (8 rules)            ← Study fields
    ├── Sensor Block (4 rules)          ← Assay fields
    ├── Location Block (3 rules)        ← drone coordinates
    ├── GeographicCoverage (3 rules)    ← country / state / county
    ├── Soil Block (1 rule)             ← soil depths
    └── Process Block (1 rule)          ← agricultural processes
```

**Key Findings:**

1. **Only Wheat Full** is FAIRagro-ready out-of-the-box
2. **Benjamin** has crop data via MIAPPE propertyIDs — needs SSSOM mapping to FAIRagro crop block
3. **Drone Flyover** is file-heavy but metadata-light — needs Investigation/Study/Assay enrichment
4. **Proposed Agrischemas model** (slides 7-9) standardizes: `Sample/Material` + `PropertyValue` + `propertyID: agrovoc:...`

### Option B: Mapping Pipeline Flowchart

```mermaid
flowchart LR
    subgraph INPUT["Input ARC RO-Crate"]
        A1["Drone Flyover<br/>Bioschemas context<br/>File-centric"]
        A2["Benjamin<br/>MIAPPE propertyIDs<br/>Process-centric"]
        A3["Wheat Full<br/>Schema.org + FAIRagro fields<br/>Complete"]
    end

    subgraph MAP["Mapping Engine<br/>arc_ro_crate-fairagro_searchhub.yaml"]
        M1["field_rules: 21 rules"]
        M2["transforms:<br/>parse_person, wrap_other_id,<br/>wrap_sensor_type, wrap_description"]
    end

    subgraph BLOCKS["FAIRagro Blocks"]
        B1["citation<br/>title, author, description,<br/>otherId, productionDate,<br/>subject, keywords"]
        B2["generalExtended<br/>license, sourceDatasetURI"]
        B3["crop<br/>cropSpecies, cropPest,<br/>variety, grainWeight..."]
        B4["sensor<br/>sensorType, platformType,<br/>manufacturer, model"]
        B5["location<br/>longitude, latitude, dateTime"]
        B6["geographicCoverage<br/>country, state, county"]
        B7["soil<br/>soilLayer"]
        B8["process<br/>processType"]
    end

    subgraph OUTPUT["FAIRagro Search Hub JSON-LD"]
        O["Validated +<br/>confidence scored"]
    end

    A1 --> M1
    A2 --> M1
    A3 --> M1
    M1 --> B1
    M1 --> B2
    M1 --> B3
    M1 --> B4
    M1 --> B5
    M1 --> B6
    M1 --> B7
    M1 --> B8
    B1 --> O
    B2 --> O
    B3 --> O
    B4 --> O
    B5 --> O
    B6 --> O
    B7 --> O
    B8 --> O

    classDef gap fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef partial fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef ok fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px

    class A1 gap
    class A2 partial
    class A3 ok
```

**Transformation Implications:**

- Need **SSSOM mapping tables**: MIAPPE/agrovoc → FAIRagro crop/sensor vocabularies
- Need **template selection logic**: auto-detect ARC type → apply appropriate enrichment

---

