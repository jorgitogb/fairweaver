# FAIRweaver Workflow — Speaker Notes & Technical Reference

Detailed notes for each slide in the presentation.

---

## Slide 1 — High-Level Pipeline

### Speaker Notes

The FAIRweaver pipeline transforms research datasets into FAIRagro-compliant metadata. The process has four stages.

**1. Input Sources:**
- **Primary:** Schema.org JSON-LD — the most common format for dataset metadata. Parsed via `schema_org` / `schema_org_arc` plugins.
- **Supported:** RO-Crate — already structured as Investigation/Study/Assay. Parsed via `ro_crate` plugin.
- **Other sources:** INSPIRE, SQL Database — future plugins would follow the same pipeline pattern.

**2. Parse & Normalize:** This step combines three operations:
- `detect_format()` — identifies format from file extension + content sniffing
- `plugin.load()` — calls the format-specific parser (e.g., `schema_org_load(content)`)
- `_auto_select_template()` — analyzes parsed fields to select the best ARC template (fairagro_plant_phenotyping, fairagro_genomics, fairagro_sensor, or fairagro_searchhub)

**3. ARC RO-Crate Generation:** The parsed data is converted into an ARC RO-Crate structure. ARC (Annotated Research Context) is a packaging format developed by DataPLANT that wraps ISA (Investigation-Study-Assay) metadata in RO-Crate JSON-LD. The system creates a hierarchy: Investigation (root) → Study → Assay. The primary method is `_fallback_convert_to_arc()` which produces richer entity hierarchies than the ARCtrl library.

**4. Validation:** The generated ARC is checked by `FairagroArcValidator` against the `fairagro_arc_v2` template. This ensures compliance with both DataPLANT ARC specification and FAIRagro Search Hub requirements.

**5. Output:** Two artifacts are produced:
- FAIRagro Search Hub JSON-LD — for indexing and discovery
- ARC RO-Crate file — downloadable, version-containable for GitLab registry

### Technical Details

- Entry point: `POST /convert/arc-export` in `main.py:873`
- Core processing: `_process_single_arc_export()` at `main.py:901`
- Format detection: `detect_format()` function (extension + content analysis)
- Template selection: `_auto_select_template()` at `main.py:1225`
- ARC generation: `_fallback_convert_to_arc()` at `main.py:985`
- Validation: `FairagroArcValidator.validate()` at `fairagro_validator.py:29`
- FAIRagro JSON-LD: `_arc_to_fairagro_jsonld()` at `main.py:57`

### Key Files
- `backend/main.py` — API endpoints and conversion orchestration
- `backend/formats/schema_org_plugin.py` — Schema.org loader
- `backend/formats/ro_crate_plugin.py` — RO-Crate loader with FAIRagro extraction
- `backend/arc_templates/fairagro_template.yaml` — FAIRagro ARC template definition
- `backend/arc_templates/fairagro_validator.py` — Validation logic

---

## Slide 2 — Schema.org → ARC Entity Mapping

### Speaker Notes

This slide shows how Schema.org fields map to the ARC entity hierarchy. The mapping creates a three-level structure:

**Investigation** is the root entity (at `./` in the RO-Crate). It holds all core metadata: name, description, identifier, license, datePublished, keywords, publisher, and version. The creator field links to a Person entity.

**Study** is derived from the dataset. Its name becomes "Study of {dataset name}". Crop and pest fields from Schema.org are mapped here using `crop_species` and `crop_pest` properties.

**Assay** holds measurement-related fields. `measurementTechnique` and `measurementMethod` come from the Schema.org dataset. If an instrument is specified with `additionalType`, it becomes `technologyType` on the Assay. The instrument itself becomes a separate entity linked via `instrument`.

**Always added:** The `isa.investigation.xlsx` file entity is required by DataPLANT ARC specification, even if not present in the input.

### Field Mapping Table

| Schema.org Field | Target Entity | Target Field | Notes |
|---|---|---|---|
| `@id` / `identifier` | Investigation | `identifier` | |
| `name` | Investigation | `name` | Also used for Study/Assay names |
| `description` | Investigation | `description` | |
| `creator` (Person) | Person entity → Investigation | `creator` | Creates `#Person_*` entity |
| `creator.affiliation` | Organization entity → Person | `affiliation` | Creates `#Org_*` entity |
| `datePublished` | Investigation | `datePublished` | |
| `license` | Investigation | `license` | |
| `keywords` | Investigation | `keywords` | |
| `publisher` | Organization entity → Investigation | `publisher` | |
| `url` | Investigation | `url` | |
| `version` | Investigation | `version` | |
| `inLanguage` | Investigation | `inLanguage` | |
| `alternateName` | Investigation | `alternative_titles` | Array |
| `measurementTechnique` | Assay | `measurementTechnique` | |
| `instrument.name` | Instrument entity → Assay | `technologyPlatform` | |
| `instrument.additionalType` | Assay | `technologyType` | |
| `funder` | Investigation | `funder` | String |
| `citation` | Publication entity → Investigation | `investigationPublications` | `ScholarlyArticle` type |
| `crop_species` | Study | `crop_species` | From `about` or direct |
| `crop_pest` | Study | `crop_pest` | |

### Template Auto-Selection Logic

The system analyzes parsed fields to select the best ARC template:
- `crop_species`, `crop_pest`, `organism` → `fairagro_plant_phenotyping`
- `sequencing`, `dna`, `rna`, `genome` → `fairagro_genomics`
- `drone`, `sensor`, `measurementTechnique` → `fairagro_sensor`
- Default → `fairagro_searchhub`

### Key Files
- `backend/main.py:985` — `_fallback_convert_to_arc()`
- `backend/formats/schema_org_arc_plugin.py:66` — ARCtrl-based conversion

---

## Slide 3 — ARC → FAIRagro JSON-LD Enrichment

### Speaker Notes

After ARC generation, the system produces FAIRagro Search Hub compliant JSON-LD. This involves two steps: field extraction and semantic enrichment.

**Step 1: Field Extraction** (`ro_crate_plugin.load()`):
The plugin traverses the ARC `@graph` to extract:
- Citation block from Investigation entity
- Crop block: Study → about → LabProcess → Sample → Organism
- Sensor block: Assay → measurementTechnique/Method + LabProcess → Drone params
- MIAPPE blocks: Taxonomy, Geolocation, Germplasm, Soil depths, Process types
- Investigation metadata: contacts, publications, citation

**Step 2: Semantic Enrichment** (`_arc_to_fairagro_jsonld()`):
Extracted fields are wrapped in Bioschemas/AgroSchemas profiles:

1. **Core Dataset**: Standard Schema.org Dataset with identifier array, keywords as DefinedTerm, about array
2. **Crop Biosample**: `@type: BioSample` with `additionalType: AGRO_00000325`, contains MIAPPE propertyIDs for Species (`MIAPPE_0043`), Variety, Grain Weight, ICC Code, Infection Taxon/Label
3. **Soil Sample**: `@type: Sample` with `additionalType: agrovoc/c_7156`, contains sampling depth with AGRO propertyID and ENVO unit terms
4. **Process LabProcess**: `@type: LabProcess` with `additionalType: AGRO_00002071`, wraps protocol names (Tillage, Irrigation, Harvest, etc.)
5. **Spatial Coverage**: City (with geo point + elevation), Country, State, County — priority chain for coordinates

### Spatial Coverage Priority Chain

1. Field geolocation (AGRO propertyIDs: `AGRO_00000574`, `AGRO_00000575`, `AGRO_00000612`)
2. Biological material geolocation (MIAPPE: `MIAPPE_0045`, `MIAPPE_0046`, `MIAPPE_0047`)
3. Material source geolocation (MIAPPE: `MIAPPE_0052`, `MIAPPE_0053`, `MIAPPE_0054`)
4. Drone geolocation (from LabProcess parameterValues: Longitude, Latitude, Date and Time)

### Key Files
- `backend/ro_crate_plugin.py:268` — `_extract_fields()`
- `backend/main.py:57` — `_arc_to_fairagro_jsonld()`

---

## Slide 4 — Three-Tier Compliance

### Speaker Notes

The `FairagroArcValidator` checks the generated ARC against three compliance levels. Each level has specific requirements, and the validation result includes which levels pass.

**DataPLANT ARC** (highest priority):
- Required files: `isa.investigation.xlsx`, `ro-crate-metadata.json`
- Required entity: Investigation with metadata
- ARC directory structure (currently skipped in JSON-only mode)

**FAIRagro**:
- Required entities: Investigation, Study, Assay, Source, LabProcess, Sample, Dataset, Person, Organization, LabProtocol
- Required fields per entity from template (e.g., Assay must have `measurementTechnique`)
- Creator must be present on Investigation

**Publishable** (superset of DataPLANT ARC):
- All DataPLANT ARC requirements
- Investigation must have `identifier` and `license`
- ISA file must be present

### Validation Rule Types

| Rule Type | Description | Example |
|---|---|---|
| `required` | Entity must have field | `Investigation.creator` |
| `at_least_one` | One of multiple fields required | `Investigation.creator \| Investigation.investigationContacts` |
| `required_fields` | Multiple fields on entity type | Assay: measurementTechnique, technologyType, technologyPlatform |
| `path_resolution` | Data path references valid | (file system check, currently skipped) |
| `directory_structure` | ARC dirs exist | (file system check, currently skipped) |
| `file_existence` | Required files exist | (file system check, currently skipped) |

### Template Structure (`fairagro_arc_v2`)

```yaml
template_id: fairagro_arc_v2
required_entities: [Investigation, Study, Assay, Source, LabProcess, Sample, 
                    Dataset, Person, Organization, LabProtocol]
required_fields:
  Investigation: [name, description, identifier]
  Study: [name]
  Assay: [name, measurementTechnique, technologyType, technologyPlatform]
  Person: [name]
  ...
validation_rules:
  - type: required
    path: Investigation.creator
  - type: at_least_one
    path: Investigation.creator, Investigation.investigationContacts
  ...
```

### Key Files
- `backend/fairagro_validator.py:29` — `FairagroArcValidator.validate()`
- `backend/pivot_registry.yaml:105` — `fairagro_searchhub` pivot definition

---

## Slide 5 — Middleware Federation Architecture

### Speaker Notes

FAIRweaver operates as a middleware service in the FAIRagro ecosystem, connecting multiple data sources to the FAIRagro Search Hub. This is the Slot 6 architecture.

### Data Sources (RDI Layer)

| Source | Domain | Data Type |
|---|---|---|
| E!DAL-PGP | Plant genomics | Phenotyping data, gene expression |
| Bonares | Agricultural research | Soil samples, crop trials |
| EDAPHOBASE | Soil science | Soil profile databases |
| OpenAGRAR | Agricultural research | Multi-domain agricultural data |

### Middleware Responsibilities

1. **Harvesting**: Connects to OAI-PMH endpoints on each source repository
2. **Normalization**: Converts heterogeneous Schema.org/Dublin Core metadata to flat dictionaries
3. **ARC Generation**: Builds Investigation/Study/Assay hierarchy with crop/sensor enrichment
4. **Validation**: Ensures FAIRagro template compliance before storage
5. **Storage**: Stores validated ARCs in GitLab ARC registry (version-controlled)
6. **Indexing**: Publishes FAIRagro JSON-LD to Search Hub for discovery

### API Endpoints for Middleware

| Endpoint | Method | Purpose |
|---|---|---|
| `/harvest` | POST | Raw OAI-PMH harvest (returns records) |
| `/harvest/convert` | POST | Harvest + convert to FAIRagro pivot |
| `/convert/arc-export` | POST | Single file → ARC + FAIRagro |
| `/list-sets` | POST | Discover available sets on source |
| `/oai-pmh` | GET | Serve as OAI-PMH endpoint (consumer → FAIRweaver) |

### Data Flow

```
Source Repository (OAI-PMH)
    ↓ harvest()
FAIRweaver Middleware
    ↓ schema_org_load() / normalize_oai_dc()
    ↓ engine.convert_nested()
    ↓ _fallback_convert_to_arc()
    ↓ FairagroArcValidator.validate()
    ↓ _arc_to_fairagro_jsonld()
GitLab ARC Registry ← arc_record_store
    ↓ (future: push)
FAIRagro Search Hub ← FAIRagro JSON-LD
```

### Key Files
- `backend/main.py:685` — `/harvest/convert` endpoint
- `backend/oai_pmh.py` — OAI-PMH harvesting logic
- `backend/main.py:473` — Demo data pre-population

---

## Appendix: Key Code References

| Component | File | Line | Function/Class |
|---|---|---|---|
| Format detection | `main.py` | ~575 | `detect_format()` |
| Schema.org loader | `formats/schema_org_plugin.py` | 8 | `load()` |
| Schema.org → ARC | `main.py` | 985 | `_fallback_convert_to_arc()` |
| ARC extraction | `formats/ro_crate_plugin.py` | 268 | `_extract_fields()` |
| FAIRagro JSON-LD | `main.py` | 57 | `_arc_to_fairagro_jsonld()` |
| Validation | `fairagro_validator.py` | 29 | `FairagroArcValidator.validate()` |
| ARC export endpoint | `main.py` | 873 | `POST /convert/arc-export` |
| Harvest + convert | `main.py` | 685 | `POST /harvest/convert` |
| Template selection | `main.py` | 1225 | `_auto_select_template()` |
| OAI-PMH serving | `main.py` | 1325 | `GET /oai-pmh` |

## Appendix: API Endpoints

### POST /convert/arc-export
Convert Schema.org JSON to ARC RO-Crate.

**Parameters:**
- `file` (UploadFile) — Schema.org JSON file
- `source_format` (str) — `auto`, `schema_org`, or `ro_crate`
- `pivot_id` (str) — `auto`, `fairagro_searchhub`, etc.
- `batch` (bool) — ZIP batch processing
- `preview` (bool) — Return preview with validation

**Response (preview=true):**
```json
{
  "preview": { "@context": [...], "@graph": [...] },
  "fairagro_jsonld": { "@type": "Dataset", ... },
  "validation": { "valid": true, "errors": [], "warnings": [] },
  "filename": "dataset_arc-ro-crate.json",
  "oai_identifier": "oai:fairweaver:dataset"
}
```

### POST /harvest/convert
Harvest from OAI-PMH and convert to FAIRagro pivot.

**Request body:**
```json
{
  "base_url": "https://repo.example.org/oai",
  "metadata_prefix": "oai_dc",
  "set": "wheat",
  "max_records": 10,
  "pivot_id": "fairagro_searchhub"
}
```

### GET /oai-pmh
FAIRweaver as OAI-PMH provider. Supports verbs: `GetRecord`, `ListRecords`, `ListIdentifiers`, `ListSets`.
