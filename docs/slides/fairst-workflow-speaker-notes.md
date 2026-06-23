# FAIRweaver Workflow — Speaker Notes & Technical Reference

Detailed notes for each slide in the presentation.

---

## Pipeline Overview — The Map (Slide 1a)

### Speaker Notes

This slide acts as the "you are here" map. The pipeline has 6 stages across 2 harvest paths. Key to state upfront:
1. **Schema.org → ARC RO-Crate** is FAIRweaver's conversion work.
2. **ARC RO-Crate is placed on the DataHub** as a full ARC (with auto-generated data).
3. **Both harvest paths read from the DataHub**, not directly from the ARC RO-Crate.
4. **SearchHub is the consumer** — it ingests the ARC RO-Crate (either directly or via Middleware) and produces the `schema.json`.

Mention the reference image: `diagrams/FAIRagro_TA3_TA4_Retreat_2006_Slot2_impulse.png` for the full FAIRagro infrastructure architecture.

### Technical Details

Same entry points and files as before. The diagram is `diagrams/slide1-pipeline.mmd`.

---

## Stage 1 · Input: FAIRagro Publication Metadata Set (Slide 1b)

### Speaker Notes

"This is what arrives from an RDI — a valid FAIRagro metadata record." Point at the JSON block. Emphasize:
1. **Fully valid** against the FAIRagro Core Metadata Specification §2 — all 6 required fields present (`name`, `description`, `url`, `keywords`, `license`, `identifier`).
2. **Naming conventions** — `author` (not `creator`, per §2.1.3), `spatialCoverage` (not `location`, per §2.1.12), `keywords` are `DefinedTerm` objects (not strings), `identifier` is a `PropertyValue` (not a bare string).
3. **Flat structure** — everything is at one level. No ISA hierarchy. Inline objects.

Mention: "This is the FAIRagro Publication Metadata Set. Domain entities (Crop, Soil, Sensor) go into the Agrischemas part — next slide."
Source: `https://knowledgebase.fairagro.net/en/tech-guides/core_metadata_specification/`

---

## Stage 1bis · Agrischemas: Same record, the `about` array (Slide 1b-bis)

### Speaker Notes

"Continuation of slide 1b. Same `@id` (`10.5447/<RDI>/2024/wheat-drought-001`), same `Dataset` — we're now looking at what's inside the `about` array."

Walk through the modeling convention (Section 3):
1. **`about` links domain entities to the Dataset** — not flat properties.
2. **Each entity has a specific type** — Crop is `BioSample` + `additionalType: AGRO_00000325` (agricultural crop, §3.1). Sensor is `Product` + `additionalType: sosa:Sensor` (§3.4).
3. **Properties go into `additionalProperty: PropertyValue`** — with `name`, `propertyID` (a URI to a semantic concept, e.g. AGROVOC), and `value`.
4. **`propertyID` is critical** — it links to an ontology term (AGROVOC `c_331243` = taxonomic species). This is what enables semantic search in the SearchHub.

"Compare: earlier slide 1b showed 'where, who, what' (Publication Metadata Set). This slide shows 'which crop, which sensor' (Agrischemas)."

Reference: Full Agrischemas tables at `knowledgebase.fairagro.net/en/tech-guides/core_metadata_specification/#3-agrischemas`

---

## Stage 2 · Transformation: FAIRagro Template Applied (Slide 1c)

### Speaker Notes

"The YAML is the bridge between FAIRagro input and ARC output." Three rule types to highlight:
1. **Direct copy** — `name` → `Investigation.name` (unchanged).
2. **Re-distribution** — `about/BioSample` → `Study.crop` and `about/Product` → `Assay.instrument`. Agrischemas domain entities are routed to the correct ISA level.
3. **Extract** — `author` → `Investigation.creator` with `extract_person`; `spatialCoverage` → `Investigation.location` with `extract_place`. Inline objects get pulled out into their own graph entities.

Make the audience notice: the input uses FAIRagro names (`author`, `spatialCoverage`), the output uses RO-Crate names (`creator`, `location`). The YAML handles the mapping — no manual work needed.

### Technical Details
- Source: `backend/mappings/schema_org-arc_ro_crate.yaml`
- The `field_rules` list is read by `MappingEngine.apply_rules()` at conversion time.

---

## Stage 3 · Output A: ARC RO-Crate (Slide 1d)

### Speaker Notes

"Now the flat input is a linked-data graph." Walk through the JSON:
1. The root `@graph` array contains separate entities.
2. `Investigation` (`@id: ./`) has global metadata + `hasPart` → `Study`.
3. `Study` has domain fields (crop_species) + `hasPart` → `Assay`.
4. `Assay` has measurement metadata.
5. Extracted entities (`Person`, `Sensor`) sit as top-level graph nodes, referenced by `@id`.

Cross-reference: "Slides 3 and 4 examine how real ARCs deviate from this ideal — some skip the Study layer, some embed crop species at the Source level. But this is the *target* structure the template produces."

---

## Stage 4a · Harvest Path 1: DataHub Direct (Slide 1e)

### Speaker Notes

"Simplest path: direct from DataHub to SearchHub." Key points:
1. **ARCs live on the DataHub** as GitLab repos (full ARC packages with data).
2. **SearchHub reads directly** via the GitLab API — no middleware in the loop.
3. **SearchHub ingests** the ARC RO-Crate from the DataHub and produces `schema.json`.

When to use: single RDI deployment, tight coupling with FAIRagro ecosystem, simplest deployment with no additional services.

### Technical Details
- GitLab API: reads ARC `ro-crate-metadata.json` from GitLab repos in the DataHub.
- The SearchHub performs ingestion directly (no FAIRweaver conversion needed at harvest time — the ARC is already in RO-Crate format).

---

## Stage 4b · Harvest Path 2: Middleware API (Slide 1f)

### Speaker Notes

"Federated path: the Middleware harvests from the DataHub and exposes an API for the SearchHub." Key points:
1. **ARCs always live on the DataHub** — same as Path 1. The Middleware never stores ARCs itself.
2. **The Middleware harvests from the DataHub** — reads ARC RO-Crates from GitLab repos.
3. **The Middleware exposes an API** — OAI-PMH for standards-compliant harvest, or REST for direct access. The SearchHub calls this API to get ARCs.
4. **The Middleware adds federation capabilities** — mTLS, plugin extensibility, multi-RDI orchestration.

When to use: multi-RDI federation, cross-institutional scenarios, when security (mTLS) or plugin extensibility is needed. The dashed arrow in the pipeline map represents this orchestrated harvest path.

### Technical Details
- Middleware API endpoints: OAI-PMH (`ListRecords`, `GetRecord`) or REST endpoints.
- The ARC is always a GitLab repo on the DataHub. The Middleware is a read-through cache/service — it harvests from the DataHub on demand.
- Reference: `diagrams/FAIRagro_TA3_TA4_Retreat_2006_Slot2_impulse.png`

---

## Stage 5 · Output B: FAIRagro SearchHub JSON (Slide 1g)

### Speaker Notes

"SearchHub-ready. Notice the domain blocks." The ARC graph is flattened again — but now organized by FAIRagro domain:
- `citation` — metadata about the record itself (title, author, identifiers).
- `crop` — what was studied (species, ontology ref).
- `sensor` — how it was measured (instrument, platform).
- `location`, `geographicCoverage` — where.
- `soil`, `process` — environmental context.

The block structure is defined by `pivot_registry.yaml` (the `fairagro_searchhub` entry). Only blocks with matching data appear. Missing blocks (e.g., if the ARC had no soil data) are simply absent.

Cross-reference: "Slide 2 explains the compliance spectrum — how ARCs that don't follow the FAIRagro template only get partial blocks."

---

## Pipeline Summary (Slide 1h)

### Speaker Notes

"Recap and then hand off to the next section."

Three messages to land:
1. **ARC is the source of truth** — all SearchHub data flows through the ARC first. Invest in good ARC structure, get good SearchHub output.
2. **Two paths, one output** — pick by topology. The `schema.json` is identical either way.
3. **What's next**: Slide 2 shows the compliance spectrum (synthetic vs. real ARCs). Slides 3–5 dive into structural analysis of real ARCs.

Transition: "The pipeline works. But extraction depth varies by ARC structure. Let's look at three real cases."

### Key Files
- `backend/main.py` — API endpoints and conversion orchestration
- `backend/formats/schema_org_plugin.py` — Schema.org loader
- `backend/formats/ro_crate_plugin.py` — RO-Crate loader with FAIRagro extraction
- `backend/mappings/schema_org-arc_ro_crate.yaml` — Template rules
- `backend/mappings/arc_ro_crate-fairagro_searchhub.yaml` — ARC → SearchHub mapping

---

## Three File Scenarios: Input → ARC → FAIRagro Output

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

## Examining ARC Structure: Domain Objects at Different Depths

### Speaker Notes

This slide examines how Agrischemas concepts are embedded inside an ARC RO-Crate graph, using the UC13 drone-flyover example.

**The diagram shows the ISA hierarchy (corrected from real data):**
- Investigation → hasPart → Study and Investigation → hasPart → Assay (siblings, not nested)
- Study → hasPart → Assay does NOT exist in the real data — that edge is empty

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

## Müncheberg ARC: A Different Structural Pattern

### Speaker Notes

This slide shows that the Müncheberg ARC uses a different structural convention for the same domain concepts.

**Key structural differences:**

**Study entity is disconnected:**
- Investigation connects directly to multiple Assays (27+) via `hasPart`
- A Study entity exists (`studies/LTE-V140-Muencheberg/`) but is NOT linked via Investigation's `hasPart`
- The Study layer is not in the ISA's `hasPart` chain — it's a separate graph node

**Crop species at Source level (short path):**
- In Müncheberg: `Source (V140_MNC)` → `additionalProperty` → `CharacteristicValue`
- Just 2 hops from Source
- Uses MIAPPE propertyIDs (`MIAPPE_0040` for Biological material ID)

**Both ARCs share the long LabProcess path:**
- Müncheberg ALSO follows the Study → `about` → LabProcess → `object` → Source pattern
- `Process_S_LTE-V140-Muencheberg_Materials-*` entities exist with `object: {"@id": "#Source_V140_MNC"}`
- So the "required" pattern from slide 5 is present in BOTH ARCs — what differs is the *alternative path*

**No sensor metadata:**
- This ARC is about crop phenology, not remote sensing
- No drone, camera, or sensor information

**Multiple assays, repeated patterns:**
- 27+ assays (crop-phenology-monitoring, plant-carbon-analysis, etc.)
- Each assay has its own LabProcess chain

**Comparison table reinforces the contrast:**
- Drone: Study in hasPart chain, 4-hop crop path, 1 assay, has sensor
- Müncheberg: Study disconnected, 2-hop + 4-hop crop paths, 27+ assays, no sensor

**This motivates standardization:** Without agreed modeling conventions, the parser must handle multiple structural patterns to extract the same information.

---

## Required Modeling Pattern & Standardization Gap

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

### Decoding the figure (visual legend)

The diagram uses **three visual encodings** to communicate priority. Point at them when presenting:

| Visual | Class | Nodes | Meaning |
|---|---|---|---|
| Gray fill, dashed border | `inactive` | `I` Investigation, `A` Assay | Optional wrappers. Omit for MVP; parser still works. |
| Blue fill, bold border | `required` | `S` Study, `LP` LabProcess, `SM` Sample | Must publish. Drop one and the chain breaks. |
| Green fill, bold border | `keyfield` | `PV` PropertyValue | The ontology anchor — what makes it searchable + interoperable. |

**Edge styles carry meaning too:**
- **Dashed arrows** (`-.->`) mark `hasPart` links inside the ISA hierarchy → soft, skippable relationships.
- **Solid arrows** (`-->`) mark the mandatory `about → object → additionalProperty` chain → hard requirement.

**Reading order (top → bottom, left → right):**
1. Top tier = hierarchy you can drop (`I → S → A`).
2. Middle tier = mandatory spine (`S → LP → SM`).
3. Bottom node = the search hook (`SM → PV[agrovoc:c_49904]`).

**One-liner to say out loud:** "If you only publish four boxes — Study, LabProcess, Sample, and a PropertyValue with an agrovoc `propertyID` — your dataset is FAIR-discoverable. The grayed-out Investigation and Assay are context, not blockers."

**Two open standardization questions:**
1. **Structure:** How do we formally specify the required traversal path? (e.g., "always follow Study → about → LabProcess → object → Sample → additionalProperty → PropertyValue with propertyID")
2. **propertyID:** How do we standardize ontology mappings? SSSOM is one candidate.

**These questions lead directly into the next part of the presentation:** the modeling approach proposal.

### Delivery script (2 min, tight)

**Audience:** FAIRagro retreat — mixed researchers + devs. Researchers need motivation, devs need the path spec.

**0:00–0:15 — Hook**
> "Publishing ISA doesn't mean shipping all 3 levels. You can drop Investigation and Assay. Here's the minimum viable graph."

**0:15–1:15 — Walk the figure (top → bottom, color = priority)**
- Point at `I`, `A` (gray dashed) → "Optional. Skip."
- Point at `S` (blue) → "Study is the anchor."
- Point at `LP`, `SM` (blue) → "LabProcess + Sample. Chain `about → object`."
- Point at `PV` (green) → pause 1s → "This. `propertyID: agrovoc:c_49904`. Without it, no semantic search."

**1:15–1:45 — Land the gap**
> "Two questions: how do we formally specify this path (SHACL candidate), and how do we standardize `propertyID` mappings (SSSOM candidate). Next slide."

**1:45–2:00 — Buffer** (one quick Q)

**Tactic by audience:**
- Researchers: green box is the ROI. One ontology term = searchable across all of FAIRagro.
- Devs: blue chain is what the parser must validate. Shape spec is the engineering work.
- Mixed Q: "researchers ask 'what do I publish?', devs ask 'what do I parse?' — same answer: these 4 boxes."

**Risk / fallback:**
- "Why not just Dataset?" → "No ontology link = invisible to cross-repo search."
- "What about traits/variables?" → defer to slide 4 comparison or live demo.

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
  "oai_identifier": "oai:<RDI>:dataset"
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
