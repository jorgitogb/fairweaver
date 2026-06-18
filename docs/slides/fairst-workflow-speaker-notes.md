# FAIRweaver Workflow — Speaker Notes & Technical Reference

Detailed notes for each slide in the presentation.

---

## Slide 1 — FAIRagro Metadata Transformation Pipeline

### Speaker Notes

This slide shows the end-to-end metadata flow from RDI metadata to FAIRagro Search Hub ingestion.

The pipeline is **sequential**, not parallel:
1. **Input:** Schema.org JSON-LD from Research Data Infrastructures (RDIs)
2. **Transformation:** FAIRagro template/spec applied as transformation rules
3. **Output A:** `arc-rocrate-metadata.json` — the Annotated Research Context (ARC RO-Crate)
4. **Output B:** `FAIRagro schema.json` — derived *from* Output A, not a parallel output

There are **two paths** from ARC RO-Crate to FAIRagro JSON:
- **Path 1 (solid arrow):** Direct harvest from GitLab-based ARC storage (DataHub)
- **Path 2 (dashed arrow):** Via FAIRagro Middleware API — a federated service orchestrating the full workflow

Both paths produce the same FAIRagro JSON-LD consumed by the Search Hub. The key insight: Output B is a *consequence* of Output A.

### Technical Details

- Entry point: `POST /convert/arc-export` in `backend/main.py`
- ARC generation: `_fallback_convert_to_arc()`
- FAIRagro JSON-LD: `_arc_to_fairagro_jsonld()`
- Middleware endpoint: `POST /harvest/convert`

### Key Files
- `backend/main.py` — API endpoints and conversion orchestration
- `backend/formats/schema_org_plugin.py` — Schema.org loader
- `backend/formats/ro_crate_plugin.py` — RO-Crate loader with FAIRagro extraction

---

## Slide 2 — Three File Scenarios: Input → ARC → FAIRagro Output

### Speaker Notes

We tested the pipeline with three concrete files to show how structure quality drives extraction quality:

**Synthetic** (`schema-org-wheat-full.json`):
- Manually crafted Schema.org with all FAIRagro-required fields
- Fully compliant ARC → full extraction

**Real — Small** (`arc-ro-crate-dronflyover.json`, <10 MB):
- Real agronomic ARC from UC13 drone flyover
- Partial compliance → only mappable fields extracted

**Real — Large** (`arc-ro-crate-metadata-muenchenberg-lte.json`, >100 MB):
- Real agronomic ARC from Müncheberg long-term experiment
- Partial compliance → basic harvest only

**Key message:** Compliance determines extraction depth. Well-structured ARCs enable full, automated extraction; unstructured ones yield only basic metadata.

---

## Slide 3 — Examining ARC Structure: Domain Objects at Different Depths

### Speaker Notes

This slide examines how Agrischemas concepts are embedded inside an ARC RO-Crate graph, using the UC13 drone-flyover example.

**The diagram shows the ISA hierarchy:**
- Investigation → hasPart → Study → hasPart → Assay

**Two Agrischemas concepts live at very different depths:**

**sensorType** — found via a short, direct path:
- Assay → `measurementMethod` → DefinedTerm
- Just 1 hop from Assay
- DefinedTerm holds: `name: digital camera`, `termCode: OBI:0001048`

**cropSpecies** — requires a much deeper traversal:
- Study → `about` → LabProcess → `object` → Sample/Material → `additionalProperty` → PropertyValue
- 4 hops from Study
- PropertyValue holds: `name: Organism`, `value: Solanum tuberosum`, `propertyID: agrovoc:c_49904`

**The depth asymmetry is the core challenge:** A generic parser must navigate multiple structural patterns to extract the same conceptual information. This is why standardization matters.

### Key Point
The `propertyID` in the PropertyValue is critical — it links to an ontology term (AGROVOC) that enables semantic interoperability. Without it, the parser cannot reliably identify what the value represents.

---

## Slide 4 — Müncheberg ARC: A Different Structural Pattern

### Speaker Notes

This slide shows that the Müncheberg ARC uses a completely different structural convention for the same domain concepts.

**Key structural differences:**

**No explicit Study entity:**
- Investigation connects directly to multiple Assays (27+)
- The Study layer is absent — no intermediate grouping entity

**Crop species at Source level:**
- In Müncheberg: `Source (V140_MNC)` → `additionalProperty` → `CharacteristicValue`
- Just 2 hops from Source
- Uses MIAPPE propertyIDs (`MIAPPE_0040` for Biological material ID)

**No sensor metadata:**
- This ARC is about crop phenology, not remote sensing
- No drone, camera, or sensor information

**Multiple assays, repeated patterns:**
- 27+ assays (crop-phenology-monitoring, plant-carbon-analysis, etc.)
- Each assay has its own LabProcess chain

**Comparison table reinforces the contrast:**
- Drone: 4-hop crop path, 1 assay, has sensor
- Müncheberg: 2-hop crop path, 27+ assays, no sensor

**This motivates standardization:** Without agreed modeling conventions, the parser must handle multiple structural patterns to extract the same information.

---

## Slide 5 — Required Modeling Pattern & Standardization Gap

### Speaker Notes

After examining both ARCs, we can define the required pattern for reliable crop extraction.

**Required path for Crop (blue/bold boxes):**
1. Study (`@type: Dataset / additionalType: Study`)
2. → `about` → LabProcess
3. → `object` → Sample with `additionalType: Material`
4. → `additionalProperty` → PropertyValue
5. → `propertyID` pointing to an ontology term (e.g., AGROVOC)

**Why propertyID matters more than name/value:**
- `name: Organism` and `value: Solanum tuberosum` alone are insufficient
- `propertyID: agrovoc:c_49904` enables unambiguous semantic mapping
- Without the ontology link, the parser cannot distinguish "Organism" from other PropertyValue names

**Two open standardization questions:**
1. **Structure:** How do we formally specify the required traversal path? (e.g., "always follow Study → about → LabProcess → object → Sample → additionalProperty → PropertyValue with propertyID")
2. **propertyID:** How do we standardize ontology mappings? SSSOM is one candidate.

**These questions lead directly into the next part of the presentation:** the modeling approach proposal.

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
