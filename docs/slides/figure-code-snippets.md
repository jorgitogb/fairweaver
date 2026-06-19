# Code Snippets Supporting Slide Figures

JSON excerpts from the example ARC files that illustrate the structural patterns shown in the slides.

---

## Slide 3 — Drone Flyover ARC Structure

### ISA Hierarchy

**Investigation** (root Dataset)
```json
{
  "@id": "./",
  "@type": "Dataset",
  "additionalType": "Investigation",
  "identifier": "AgDaFair_Drone_Flyovers",
  "datePublished": "2026-01-29T14:30:55.9873990",
  "hasPart": [
    { "@id": "assays/drone_image_capture/" },
    { "@id": "studies/plant_plots/" }
  ],
  "name": "Untitled ARC"
}
```

**Study**
```json
{
  "@id": "studies/plant_plots/",
  "@type": "Dataset",
  "additionalType": "Study",
  "identifier": "plant_plots",
  "name": "Plant Plots",
  "description": "potato plants were pton plots in a large distance to each other...",
  "about": [
    { "@id": "#Process_S_plant_plots_plant_plots_KF_0" },
    { "@id": "#Process_S_plant_plots_plant_plots_KF_1" }
  ]
}
```

**Assay**
```json
{
  "@id": "assays/drone_image_capture/",
  "@type": "Dataset",
  "additionalType": "Assay",
  "identifier": "drone_image_capture",
  "description": "The drone flew to preselected geolocations to take one picture of each plant.",
  "hasPart": [
    { "@id": "assays/drone_image_capture/dataset/labeled/0.jpg" },
    { "@id": "assays/drone_image_capture/dataset/labeled/1.jpg" }
  ],
  "measurementMethod": {
    "@id": "https://bioregistry.io/OBI:0001048"
  },
  "measurementTechnique": {
    "@id": "#OA_Drone"
  }
}
```

### sensorType Path (1 hop from Assay)

**DefinedTerm** referenced by `measurementMethod`
```json
{
  "@id": "https://bioregistry.io/OBI:0001048",
  "@type": "DefinedTerm",
  "name": "digital camera",
  "termCode": "https://bioregistry.io/OBI:0001048"
}
```

**Traversal:** Assay → `measurementMethod` → DefinedTerm (`OBI:0001048`)

### cropSpecies Path (4 hops from Study)

**Step 1:** Study → `about` → LabProcess
```json
{
  "@id": "#Process_S_plant_plots_plant_plots_KF_0",
  "@type": "LabProcess",
  "name": "plant_plots_KF_0",
  "object": {
    "@id": "#Material_KF10"
  },
  "executesLabProtocol": {
    "@id": "#Protocol_plant_plots_KF"
  }
}
```

**Step 2:** LabProcess → `object` → Sample/Material
```json
{
  "@id": "#Material_KF10",
  "@type": "Sample",
  "additionalType": "Material",
  "name": "KF10",
  "additionalProperty": [
    { "@id": "#CharacteristicValue_Organism_Solanum_tuberosum" },
    { "@id": "#CharacteristicValue_Infection_Label_PVY_positiv" }
  ]
}
```

**Step 3:** Sample → `additionalProperty` → PropertyValue
```json
{
  "@id": "#CharacteristicValue_Organism_Solanum_tuberosum",
  "@type": "PropertyValue",
  "additionalType": "CharacteristicValue",
  "name": "Organism",
  "value": "Solanum tuberosum",
  "valueReference": "http://purl.obolibrary.org/obo/NCBITaxon_4113",
  "columnIndex": "0"
}
```

**Traversal:** Study → `about` → LabProcess → `object` → Sample/Material → `additionalProperty` → PropertyValue

---

## Slide 4 — Müncheberg LTE ARC Structure

### Flat Structure (No Study Entity)

**Investigation** connects directly to 27+ Assays
```json
{
  "@id": "./",
  "@type": "Dataset",
  "additionalType": "Investigation",
  "identifier": "Muencheberg_LTE",
  "hasPart": [
    { "@id": "assays/crop-phenology-monitoring/" },
    { "@id": "assays/plant-carbon-analysis/" },
    { "@id": "assays/soil-moisture-monitoring/" }
  ]
}
```

**Assay** (27+ assays, no intermediate Study)
```json
{
  "@id": "assays/crop-phenology-monitoring/",
  "@type": "Dataset",
  "additionalType": "Assay",
  "identifier": "crop-phenology-monitoring",
  "about": [
    { "@id": "#Process_A_crop-phenology-monitoring_CropPhenology_0" },
    { "@id": "#Process_A_crop-phenology-monitoring_CropPhenology_1" }
  ]
}
```

### cropSpecies Path (2 hops from Source)

**Step 1:** Source (Sample with additionalType: Source)
```json
{
  "@id": "#Source_V140_MNC",
  "@type": "Sample",
  "additionalType": "Source",
  "name": "V140_MNC",
  "additionalProperty": [
    { "@id": "#CharacteristicValue_Biological_material_ID_zeamay_C38_7" },
    { "@id": "#CharacteristicValue_plant_structure_development_stage_seedling_shoot_emergence_stage" },
    { "@id": "#CharacteristicValue_remark" }
  ]
}
```

**Step 2:** Source → `additionalProperty` → CharacteristicValue
```json
{
  "@id": "#CharacteristicValue_Biological_material_ID_zeamay_C38_7",
  "@type": "PropertyValue",
  "additionalType": "CharacteristicValue",
  "name": "Biological material ID",
  "value": "zeamay_C38_7",
  "propertyID": "http://purl.obolibrary.org/obo/MIAPPE_0040",
  "columnIndex": "0"
}
```

**Traversal:** Source → `additionalProperty` → PropertyValue (CharacteristicValue)

---

## Slide 5 — Required Modeling Pattern

### Required Path for Crop Species (from Drone Flyover)

```
Study
  └─ about ──► LabProcess
                  └─ object ──► Sample (additionalType: Material)
                                   └─ additionalProperty ──► PropertyValue
                                                                └─ propertyID → ontology term
```

**PropertyValue with propertyID** (idealized example)
```json
{
  "@type": "PropertyValue",
  "name": "Organism",
  "value": "Solanum tuberosum",
  "propertyID": "http://purl.obolibrary.org/obo/agrovoc:c_49904"
}
```

**Note:** The actual drone flyover file uses `valueReference` instead of `propertyID`:
```json
{
  "@id": "#CharacteristicValue_Organism_Solanum_tuberosum",
  "@type": "PropertyValue",
  "name": "Organism",
  "value": "Solanum tuberosum",
  "valueReference": "http://purl.obolibrary.org/obo/NCBITaxon_4113"
}
```

This inconsistency is part of the standardization gap.

---

## Comparison Table Data

| Aspect | Drone Flyover | Müncheberg LTE |
|--------|---------------|----------------|
| **Study entity** | Explicit (`studies/plant_plots/`) | Absent |
| **Crop species path** | Study → LabProcess → Sample → PropertyValue | Source → PropertyValue |
| **Crop species depth** | 4 hops | 2 hops |
| **Sensor metadata** | Present (DefinedTerm with OBI:0001048) | Absent |
| **Assay count** | 1 (drone_image_capture) | 27+ |
| **propertyID usage** | Inconsistent (uses valueReference) | Consistent (MIAPPE_0040) |
| **Ontology terms** | NCBITaxon (species) | MIAPPE (plant traits) |

---

## Source Files

- Drone flyover: `sample-data/demo/arc-ro-crate-dronflyover.json` (115,507 lines)
- Müncheberg LTE: `sample-data/demo/arc-ro-crate-metadata-muenchenberg-lte.json` (3,389,559 lines)
- Synthetic wheat (input): `sample-data/demo/schema-org-wheat-full.json` (147 lines)
- Synthetic wheat (output): `sample-data/demo/arc-ro-crate-wheat-full.json` (256 lines)

---

## Slide 2 — Synthetic Example: Schema.org → ARC Mapping

This section shows how a flat Schema.org JSON-LD transforms into a structured ARC RO-Crate with ISA hierarchy.

### Input: Schema.org JSON-LD (Flat Structure)

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "@id": "https://doi.org/10.5447/fairweaver/2024/wheat-drought-001",
  "name": "Wheat Drought Phenotyping Field Trial 2024",
  "description": "Multi-temporal drone-based NDVI and multispectral imaging...",
  "identifier": "10.5447/fairweaver/2024/wheat-drought-001",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "datePublished": "2024-09-15",
  "creator": {
    "@type": "Person",
    "givenName": "Timo",
    "familyName": "Mühlhaus",
    "email": "timo.muehlhaus@rptu.de",
    "affiliation": {
      "@type": "Organization",
      "name": "RPTU University of Kaiserslautern"
    },
    "identifier": {
      "@type": "PropertyValue",
      "propertyID": "orcid",
      "value": "0000-0003-3925-6778"
    }
  },
  "keywords": ["wheat", "drought stress", "NDVI", "phenotyping"],
  "publisher": {
    "@type": "Organization",
    "name": "RPTU University of Kaiserslautern, Plant Phenomics Group"
  },
  "funder": {
    "@type": "Organization",
    "name": "DFG – German Research Foundation"
  },
  "studyDesignType": "Randomized complete block design",
  "studyDesignDescriptors": ["wheat", "drought stress", "NDVI"],
  "crop_species": "Triticum aestivum",
  "crop_species_uri": "http://purl.obolibrary.org/obo/NCBITaxon_4565",
  "measurementTechnique": "Multispectral imaging",
  "measurementMethod": "NDVI calculation from red and near-infrared reflectance bands",
  "technologyPlatform": "DJI Matrice 300 RTK UAV",
  "instrument": {
    "@type": "Thing",
    "name": "Micasense RedEdge-MX",
    "description": "Multispectral sensor on DJI Matrice 300 RTK UAV"
  },
  "location": {
    "@type": "Place",
    "name": "RPTU Field Station Kaiserslautern",
    "geo": {
      "@type": "GeoCoordinates",
      "latitude": 49.4401,
      "longitude": 7.7491
    }
  },
  "country": "Germany",
  "state": "Rhineland-Palatinate",
  "soilType": "Luvisol"
}
```

### Output: ARC RO-Crate (ISA Hierarchy)

#### 1. Investigation (root Dataset)

```json
{
  "@id": "#Investigation_wheat",
  "@type": "Dataset",
  "additionalType": "Investigation",
  "name": "Wheat Drought Phenotyping Field Trial 2024",
  "description": "Multi-temporal drone-based NDVI and multispectral imaging...",
  "identifier": "10.5447/fairweaver/2024/wheat-drought-001",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "datePublished": "2024-09-15",
  "creator": [
    { "@id": "#Mühlhaus_Timo" },
    { "@id": "#Maus_Oliver" }
  ],
  "hasPart": [
    { "@id": "#Study_wheat" }
  ],
  "keywords": ["wheat", "drought stress", "NDVI", "phenotyping"],
  "publisher": {
    "@id": "#Organization_RPTU_University_of_Kaiserslautern_Plant_Phenomics_Group"
  },
  "funder": "DFG – German Research Foundation",
  "investigationContacts": [
    { "@id": "#Mühlhaus_Timo" }
  ],
  "investigationPublications": [
    { "@id": "#Publication_wheat" }
  ]
}
```

**Mapping rules:**
- `name`, `description`, `identifier`, `license`, `datePublished` → copied to Investigation
- `creator` (inline object) → extracted as separate Person entity, referenced by `@id`
- `publisher`, `funder` → copied to Investigation (Organization extracted separately)
- `keywords` → copied to Investigation
- `investigationContacts`, `investigationPublications` → preserved as Investigation-level fields

#### 2. Study (intermediate entity)

```json
{
  "@id": "#Study_wheat",
  "@type": "Dataset",
  "additionalType": "Study",
  "name": "Wheat Field Trial",
  "description": "Field study: Wheat Drought Phenotyping Field Trial 2024",
  "hasPart": [
    { "@id": "#Assay_wheat" }
  ],
  "studyDesignType": "Randomized complete block design",
  "studyDesignDescriptors": ["wheat", "drought stress", "NDVI"],
  "studyPersonnel": [
    { "@id": "#Mühlhaus_Timo" }
  ],
  "crop_species": "Triticum aestivum",
  "crop_species_uri": "http://purl.obolibrary.org/obo/NCBITaxon_4565",
  "crop_pest": "Zymoseptoria tritici",
  "crop_pest_uri": "http://purl.obolibrary.org/obo/NCBITaxon_5284"
}
```

**Mapping rules:**
- `studyDesignType`, `studyDesignDescriptors`, `studyPersonnel` → Study-level fields
- `crop_species`, `crop_species_uri`, `crop_pest`, `crop_pest_uri` → Study-level domain fields
- `name` derived from Investigation name + "Field Trial" suffix
- `description` prefixed with "Field study: "

#### 3. Assay (measurement entity)

```json
{
  "@id": "#Assay_wheat",
  "@type": "Dataset",
  "additionalType": "Assay",
  "name": "Wheat Multispectral imaging",
  "description": "Multispectral imaging assay for Wheat Drought Phenotyping Field Trial 2024",
  "measurementTechnique": "Multispectral imaging",
  "measurementMethod": "NDVI calculation from red and near-infrared reflectance bands",
  "technologyType": "Multispectral imaging sensor",
  "technologyPlatform": "DJI Matrice 300 RTK UAV",
  "about": [
    { "@id": "#Study_wheat" }
  ],
  "assayCategory": "measurement",
  "assayType": "imaging_assay",
  "instrument": [
    { "@id": "#Instrument_wheat" }
  ]
}
```

**Mapping rules:**
- `measurementTechnique`, `measurementMethod`, `technologyType`, `technologyPlatform` → Assay-level fields
- `assayCategory`, `assayType` → Assay-level classification
- `instrument` (inline Thing) → extracted as separate Sensor entity, referenced by `@id`
- `about` → back-reference to Study

#### 4. Extracted Entities

**Person** (from inline `creator`)
```json
{
  "@id": "#Mühlhaus_Timo",
  "@type": "Person",
  "givenName": "Timo",
  "familyName": "Mühlhaus",
  "name": "Timo Mühlhaus",
  "email": "timo.muehlhaus@rptu.de",
  "identifier": {
    "@type": "PropertyValue",
    "propertyID": "orcid",
    "value": "0000-0003-3925-6778"
  },
  "affiliation": {
    "@type": "Organization",
    "name": "RPTU University of Kaiserslautern"
  }
}
```

**Sensor** (from inline `instrument`)
```json
{
  "@id": "#Instrument_wheat",
  "@type": "Sensor",
  "name": "Micasense RedEdge-MX",
  "description": "Multispectral sensor on DJI Matrice 300 RTK UAV"
}
```

**Location** (from inline `location`)
```json
{
  "@id": "#Location_wheat",
  "@type": "Place",
  "name": "RPTU Field Station Kaiserslautern",
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 49.4401,
    "longitude": 7.7491
  }
}
```

**Geographic Coverage** (from `country`, `state`, `county`)
```json
{
  "@id": "#GeographicCoverage_wheat",
  "@type": "DefinedRegion",
  "name": "Kaiserslautern, Rhineland-Palatinate, Germany",
  "country": "Germany",
  "state": "Rhineland-Palatinate",
  "county": "Kaiserslautern"
}
```

**Soil** (from `soilType`)
```json
{
  "@id": "#Soil_wheat",
  "@type": "Thing",
  "name": "Luvisol",
  "additionalType": "SoilType"
}
```

### Mapping Summary

| Schema.org Field | ARC RO-Crate Location | Transformation |
|---|---|---|
| `@type: Dataset` (root) | Investigation + Study + Assay | Split into ISA hierarchy |
| `name`, `description` | Investigation | Copied |
| `identifier`, `license`, `datePublished` | Investigation | Copied |
| `creator` (Person) | Investigation.creator | Extracted as separate entity, referenced by `@id` |
| `publisher`, `funder` | Investigation | Copied (Organization extracted) |
| `keywords` | Investigation | Copied |
| `investigationContacts` | Investigation | Preserved |
| `investigationPublications` | Investigation | Preserved (Publication extracted) |
| `studyDesignType`, `studyDesignDescriptors` | Study | Moved to Study level |
| `studyPersonnel` | Study | Moved to Study level |
| `crop_species`, `crop_species_uri` | Study | Moved to Study level (domain fields) |
| `crop_pest`, `crop_pest_uri` | Study | Moved to Study level (domain fields) |
| `measurementTechnique`, `measurementMethod` | Assay | Moved to Assay level |
| `technologyType`, `technologyPlatform` | Assay | Moved to Assay level |
| `assayCategory`, `assayType` | Assay | Moved to Assay level |
| `instrument` (Thing) | Assay.instrument | Extracted as Sensor entity, referenced by `@id` |
| `location` (Place) | Investigation.location | Extracted as Place entity, referenced by `@id` |
| `country`, `state`, `county` | Investigation.geographicCoverage | Combined into DefinedRegion entity |
| `soilType` | Investigation.soil | Extracted as Thing with additionalType: SoilType |
| `processType` | Investigation.process | Extracted as Thing with additionalType: Process |

### Key Transformation Patterns

1. **Flattening → Hierarchy**: Schema.org's flat structure becomes ISA hierarchy (Investigation → Study → Assay)
2. **Inline → Referenced**: Inline objects (Person, Organization, Instrument, Location) become separate entities with `@id` references
3. **Field Distribution**: Fields are distributed across ISA levels based on semantic scope:
   - Investigation-level: project-wide metadata (identifier, license, funder, contacts)
   - Study-level: experimental design and domain concepts (crop species, design type)
   - Assay-level: measurement specifics (technique, method, platform, instrument)
4. **Context Switching**: `@context` changes from `https://schema.org` to RO-Crate context with Schema.org vocabulary overlay
5. **Back-references**: Assay includes `about: [{@id: "#Study_wheat"}]` to link back to parent Study
