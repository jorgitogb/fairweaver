# Slot 6: ARC Structure Analysis - Standardization Need

**Presenters:** Jorge & Julian

---

## Slide: ARC Structural Variations - Why Standardization Matters

### Example 1: Drone Flyover ARC (INSPIRE2ARC Sensor Data)

```
arc-ro-crate-drone-flyover.json
├── Dataset (root)
│   ├── name: "Drone Flyover Survey"
│   ├── description: "Multispectral imagery collection"
│   ├── creator: [person refs]
│   └── hasPart: [Study]
│
├── Study (Investigation)
│   ├── name: "Drone Survey Study"
│   ├── description: "Study of flyover survey methodology"
│   └── hasPart: [Assay]
│
├── Assay (data collection)
│   ├── name: "Multispectral Imaging"
│   ├── measurementTechnique: "Multispectral sensor"
│   └── about: [Study]
│
└── Sensor (data source)
    ├── name: "DJI Mavic 2"
    ├── description: "Consumer drone with RGB + thermal camera"
    └── sensorType: "UAV"
```

### Example 2: Benjamin's LTE ARC

```
arc-ro-crate-benjamin.json
├── Dataset (root)  
│   ├── name: "Wheat Phenotyping Dataset"
│   ├── description: "Multi-temporal UAV-based NDVI imaging"
│   ├── creator: [person refs]
│   ├── location: [Place]
│   ├── geographicCoverage: [DefinedRegion]
│   └── hasPart: [Investigation]
│
├── Investigation
│   ├── name: "Wheat Drought Phenotyping Field Trial"
│   ├── description: "Detailed experimental setup"
│   ├── funder: "DFG"
│   ├── investigator: [persons]
│   └── hasPart: [Study]
│
├── Study
│   ├── name: "Wheat Field Trial"
│   ├── description: "Field study details"
│   ├── studyDesignType: "RCBD"
│   └── hasPart: [Assay]
│
├── Assay
│   ├── name: "Wheat Multispectral imaging"
│   ├── measurementTechnique: "Multispectral imaging"
│   ├── technologyPlatform: "DJI Matrice 300 RTK"
│   └── about: [Study]
│
└── Sensor (embedded at assay level)
    ├── name: "Micasense RedEdge-MX"
    ├── description: "Multispectral sensor"
    └── manufacturer: "Micasense"
```

---

## Key Structural Differences

| Aspect | Drone Flyover ARC | Benjamin's LTE ARC |
|--------|-------------------|-------------------|
| **Sensor Location** | Embedded in Assay | Embedded in Assay |
| **Metadata Depth** | Basic (1-2 levels) | Deep (5-6 levels) |
| **Spatial Coverage** | Minimal | Comprehensive |
| **Temporal Coverage** | None | Explicit (dates) |
| **Entity Relationships** | Simple | Complex (nested) |
| **Provenance** | Missing | Present (creator, funder) |

---

## Challenge: Information Placement Variability

### Same Information, Different Locations

| Information | Drone Flyover | Benjamin's LTE |
|-------------|---------------|----------------|
| **Sensor Details** | In Assay | In Assay |
| **Location Data** | Minimal | Complete |
| **Temporal Info** | None | Explicit |
| **Study Design** | Basic | Detailed |
| **Research Context** | Missing | Rich (funder, publications) |

### Vast Structural Differences

1. **Level 1 - Basic:** 3 entities (Dataset → Investigation → Study → Assay)
2. **Level 2 - Enhanced:** 5+ entities with metadata
3. **Level 3 - Full:** 1000+ entities with deep nesting

---

## Goal: Standardize Modeling Patterns

### Current State

- **Inconsistent entity placement** across ARCs
- **Missing structural conventions** for common elements
- **Information siloed** across different ARC sections

### Needed Standardization

- **Common entity models** for sensors, locations, processes
- **Predetermined metadata pathways** for field-specific info
- **Consistent hierarchical structures** for different data types
- **Cross-ARC interoperability** through standardized schemas

### Recommendation

Define **ARC modeling guidelines** that specify:

1. Which entities should contain spatial/temporal info
2. Where sensor metadata should be located
3. How to structure research context (funder, publication)
4. Consistent field-specific extensions to core models
