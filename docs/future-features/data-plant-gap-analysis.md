# FAIRagro-MI — DataPLANT Gap Analysis & Future Features

> **Date:** 23 Jun 2026
> **Source:** Competitive analysis of [DataPLANT Toolbox](https://nfdi4plants.github.io/toolbox/) vs FAIRagro-MI v0.1.0.dev0
> **Purpose:** Identify features DataPLANT has that we lack, find strategic opportunities, and build a prioritized backlog grounded in our unique value.

---

## 1. Strategic Position

| Dimension | DataPLANT | FAIRagro-MI |
|-----------|-----------|-------------|
| Scope | Plant biology (NFDI4Plants) | Agriculture + cross-domain (NFDI4Agri / NFDI-wide) |
| Role | ARC RDM ecosystem owner (creation, storage, publishing) | Metadata interoperability layer (conversion, validation, classification) |
| Core asset | ARC framework, ISA-based metadata annotation | Format-agnostic pivot engine, OAI-PMH server, AI mapping generation |

**Our niche:** We are the "metadata in flight" tool — any source format → any pivot → any target format.
DataPLANT owns **ARC creation/storage**. We own **conversion, validation, and quality classification** of metadata as it moves between systems.

**Golden rule:** Build where we strengthen this interoperability niche. Link out to DataPLANT for ARC management.

---

## 2. What FAIRagro-MI Has Today

### Format plugins (7)

| Plugin | Format |
|--------|--------|
| `isa_json_plugin.py` | ISA-JSON (ARC native) |
| `datacite_xml_plugin.py` | DataCite XML |
| `darwin_core_csv_plugin.py` | Darwin Core CSV |
| `schema_org_plugin.py` | Schema.org JSON-LD |
| `ro_crate_plugin.py` | RO-Crate JSON-LD |
| `schema_org_arc_plugin.py` | Schema.org → ARC |
| `oai_dc_plugin.py` | OAI-PMH Dublin Core |

### Pivot profiles (7)

`bioschemas_dataset`, `bioschemas_taxon`, `bioschemas_biosample`, `agrischemas_fieldtrial`,
`agrischemas_cropvariety`, `schemaorg_generic`, `fairagro_searchhub` (7 blocks: citation, crop, sensor, location, soil, etc.)

### REST endpoints (11)

`/pivots`, `/pivots/recommend`, `/mappings`, `/mappings/generate`, `/mappings/validate`,
`/convert`, `/convert/chain`, `/convert/arc-export`, `/harvest/convert`, `/arc/validate/fairagro`,
`/oai-pmh` (server), `/compliance/classify`, `/list-sets`, `/source-formats/schema-org`,
`/template-fields/{id}`

### Frontend components (7)

`UploadZone`, `ArcCrateView` (6-tab: ARC / JSON-LD / Validation / Entities / Hierarchy / MIAPPE),
`ComplianceBadge`, `ArcEntityTree`, `ArcHierarchyTree`, `MiappeExtractionTree`, `JsonHighlight`

### Unique value

- OAI-PMH server with `fairagro_arc` metadata format (DataPLANT has no server)
- AI-powered mapping generation via GWDG Academic Cloud
- 3-tier compliance classification: basic (red) / intermediate (amber) / full (green)
- Auto-template selection based on content analysis
- 12 demo files (wheat/maize × 3 levels × 2 formats)
- Graceful degradation: rule-based fallback when AI is unavailable

---

## 3. What DataPLANT Has — Gaps We Lack

| # | Scope | DataPLANT Tool | Why It Matters for Our Users | Effort |
|---|-------|----------------|------------------------------|--------|
| G1 | DMP generation | [DataPLAN](https://dmpg.nfdi4plants.org/) — multi-funder templates (H2020, DFG, BMBF, NSF...) + AI text→DMP + offline mode | No FAIRagro-equivalent DMP tool exists. Researchers writing grants need plans before metadata. | Medium |
| G2 | ELN → ARC ETL | [elab2ARC](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/resources/elab2arc/) — eLabFTW experiments → ARC assay folder, protocols, datasets | Lab notebooks are the *source of truth* for experimental metadata. We only accept files; we don't pull from ELNs. | Medium |
| G3 | Continuous Quality Control | [CQC pipelines](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/arc-validation/cqc-pipelines/) — re-validate on every commit via DataHUB CI | We do one-shot validation. CQC = "validate on every upload/change" — CI-style reliability. | Medium |
| G4 | Auto-README / ARC Summary | [ARC Summary](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/resources/arc-summary/) — generates README.md from ARC metadata, customizable sections | After converting to ARC, users want a human-readable summary. We dump raw JSON-LD. | Quick |
| G5 | DataHUB push (GitLab) | ARCitect's sync / ARC Commander's `connect` — push ARC to GitLab | We generate ARC files. Users must manually download and upload to GitLab. | Medium |
| G6 | Publication workflow (DOI + submit) | [ARChigator](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/datahub/data-publications/datahub-data-publications-archigator/) — metadata review, CQC check, publish→DOI | No way to publish a converted ARC to a real repository with a DOI. Dead-end after conversion. | Medium |
| G7 | Annotation table in browser (Swate-lite) | [Swate](https://swate-alpha.nfdi4plants.org/) — ontology-driven metadata annotation, building blocks, term search, templates | We accept pre-annotated files but don't help users annotate. Leaves the hardest part unaddressed. | Large |
| G8 | Multi-ELN adapter | elab2ARC (eLabFTW only) | eLabFTW is one of many; Chemotion, LabArchives, RSpace, openBIS also exist in FAIRagro. | Large |
| G9 | ARC CLI (headless) | [ARC Commander](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/arc-commander/) — init, clone, sync, ISA edits, export | Some users (e.g., HPC workflows) need CLI, not web. | Quick |
| G10 | GitLab CI/CD jobs | DataHUB CI — run own CI/CD jobs on ARC repos | If we integrate with GitLab, we should provide a validation CI template. | Small |

---

## 4. Where We WIN vs DataPLANT

| Our Unique Strength | DataPLANT Gap | Strategic Value |
|---------------------|---------------|-----------------|
| **Format-agnostic pivot engine** — any source ↔ any pivot ↔ any target | DataPLANT is ARC-ISA only. No Darwin Core, no DataCite, no OAI-DC. | Cross-format bridging is our core multiplier. Every new format plugin = exponential value. |
| **OAI-PMH server** (`/oai-pmh`, `fairagro_arc`) | No OAI-PMH server. DataPLANT relies on a planned external service. | We are the *only* tool in the NFDI space that serves FAIRagro-converted metadata via OAI-PMH out of the box. |
| **AI mapping generation** (GWDG Academic Cloud, 3 models) | No AI mapping. ARC templates are hand-curated. | Mapping generation saves hours per new format. GWDG is free for German academic users. |
| **Live compliance classification** (basic/intermediate/full) | Single-pass validation (pass/fail). No progressive disclosure. | Users understand quality at a glance. The badge drives adoption (nobody wants "red"). |
| **Cross-domain pivots** (7 profiles) | ISA/ARC only. | We serve agronomy, genomics, biodiversity, soil science, plant phenotyping — not just plants. |
| **Domain-agnostic architecture** | Plant-specific. | Every non-plant NFDI consortium is a potential user (NFDI4Chem, NFDI4Biodiversity, NFDI4Earth...). |
| **Graceful degradation** (rule-based fallback) | No AI fallback pattern. | Our tool works without an API key. DataPLANT tools don't degrade — they're deterministic but less flexible. |

---

## 5. Proposed Feature Backlog

### Quick Wins (≤1 day each)

#### F1 · Auto-README / ARC Summary generator

**What:** After ARC export, auto-generate a `README.md` with investigation/study/assay names, contacts, keywords, provenance graph, and a summary table. Inspired by DataPLANT's ARC Summary tool.

**Why:** Users exporting ARC RO-Crate get raw JSON-LD. A human-readable summary makes the output immediately useful for sharing, grant reporting, and onboarding.

**Pattern:** Strategy — `backend/arc_summary/summary_generator.py` (reads ARC `@graph`, produces sections per YAML config).

**Reference:** `AGENTS.md` → Strategy Pattern (format plugins), `backend/arc_templates/fairagro_validator.py`

**Depends on:** Existing ARC export pipeline (`/convert/arc-export`). No new dependencies.

**Target user:** ARC producers sharing data with collaborators, PIs writing reports.

**Acceptance:**

- [ ] `POST /arc/summarize` accepts ARC JSON and returns markdown string
- [ ] Sections: Investigation, Studies, Assays, Contacts, Keywords, Provenance
- [ ] Customizable via `.arc_summary.yml` uploaded alongside ARC
- [ ] Frontend: "Generate Summary" button in ArcCrateView

---

#### F2 · SSSOM export (Simple Standard for Sharing Ontology Mappings)

**What:** Export YAML field mappings as SSSOM (TSV format) — the standard for ontology mapping registries like OBO Foundry and BioPortal.

**Why:** Our YAML mappings are valuable beyond FAIRagro. SSSOM export makes them consumable by the broader semantic-web community.

**Pattern:** Format plugin — `backend/formats/sssom_plugin.py` (write-only, implements `write(json_ld) -> dict`).

**Reference:** `AGENTS.md` → Strategy Pattern (format plugins), `backend/formats/` directory, [SSSOM spec](https://mapping-commons.github.io/sssom/)

**Depends on:** Existing YAML mapping engine (`mapping_engine.py`). `sssom-py` library.

**Target user:** Ontology curators, mapping registry maintainers.

**Acceptance:**

- [ ] `POST /convert/chain?target_format=sssom` returns valid SSSOM TSV
- [ ] Each field rule → SSSOM row with `subject_id`, `predicate_id`, `object_id`, `mapping_justification`
- [ ] Round-trip validation: SSSOM output validates against SSSOM schema

---

#### F3 · CSV/Tab annotation table (Swate-lite in browser)

**What:** Browser-based annotation table — columns for field name, value, ontology term URI, unit. No Excel required. Users fill in metadata using the pivot's required/recommended fields as column headers.

**Why:** Swate is Excel/VSCode-only and plant-focused. Researchers in other domains (soil, biodiversity, genomics) need a lightweight, web-native annotation tool that feeds our conversion pipeline.

**Pattern:** Component — `frontend/src/components/AnnotationTable.tsx` + endpoint `POST /annotate` (accepts table rows, produces flat dict).

**Reference:** `AGENTS.md` → Typed API Contract (client.ts), `frontend/src/components/` directory pattern, `frontend/src/api/client.ts`

**Depends on:** Pivot registry (field definitions). `@tanstack/react-table` (already in deps? check).

**Target user:** Wet-lab researchers without Excel, cross-domain annotators.

**Acceptance:**

- [ ] Editable table with columns: Field Name, Value, Ontology Term (autocomplete), Unit
- [ ] Column headers auto-populated from selected pivot's `required_fields` + `recommended_fields`
- [ ] "Convert" button sends table rows to `/convert` and shows result
- [ ] "Download CSV" and "Download JSON" export from table

---

#### F4 · Per-pivot coverage heatmap

**What:** Visual heatmap showing coverage % per pivot block (e.g., citation: 80%, crop: 40%, sensor: 0%). Currently we show a single aggregate confidence number.

**Why:** The FAIRagro Search Hub pivot has 7 blocks. "73% overall" hides that citation is perfect but sensor is empty. Block-level granularity tells users exactly where to improve.

**Pattern:** Component — `frontend/src/components/CoverageHeatmap.tsx` consuming `ConvertResult.missing_fields`.

**Reference:** `AGENTS.md` → Facade Pattern (MappingEngine), `frontend/src/components/ComplianceBadge.tsx`, `backend/pivot_registry.yaml` (block structure).

**Depends on:** Existing `/convert` response (already includes per-field `missing_fields` with `level`).

**Target user:** Dataset owners comparing metadata readiness across standards.

**Acceptance:**

- [ ] Heatmap grid: rows = pivot blocks, cells colored green/amber/red by coverage %
- [ ] Hover tooltip: field list with present/missing breakdown
- [ ] Click cell → filter missing fields list below

---

### Medium Features (1–2 weeks)

#### F5 · eLabFTW / ELN connector

**What:** Port the elab2ARC pattern — fetch experiments from eLabFTW API, extract metadata (title, description, attachments, linked resources), convert to ARC RO-Crate via our existing pipeline.

**Why:** elab2ARC is plant-specific. FAIRagro researchers use eLabFTW too, and our pipeline produces richer ARC entities (Investigation/Study/Assay with domain-specific objects) than the basic ARC Commander output elab2ARC produces.

**Pattern:** Strategy — `backend/elns/*_adapter.py` each implements `fetch(experiment_id) -> dict` and `convert(eln_data) -> arc_dict`. The `load_plugins` auto-discovery pattern from `backend/plugins/loader.py` is reused.

**Reference:** `AGENTS.md` → Strategy Pattern (format plugins), `backend/plugins/loader.py`, `backend/ai_client.py` (API client pattern).

**Depends on:** Existing ARC export pipeline (`/convert/arc-export`), eLabFTW API credentials.

**Target user:** Wet-lab researchers migrating from ELN to FAIRagro-compliant ARC.

**Acceptance:**

- [ ] `POST /eln/convert` accepts `eln_type`, `instance_url`, `api_key`, `experiment_id`
- [ ] Fetches eLabFTW experiment + linked experiments/resources + attachments
- [ ] Main text → assay protocol `.md`, attachments → dataset folder, metadata → ISA
- [ ] Returns ARC RO-Crate via existing `_fallback_convert_to_arc`
- [ ] Only eLabFTW adapter in first iteration; adapter interface designed for extensibility

---

#### F6 · CQC-style validation webhook

**What:** Re-validate an ARC on every upload or programmatic trigger. Track validation history across time (commit-style). Expose a webhook endpoint for GitLab CI or external CQC pipelines.

**Why:** One-shot validation catches problems once. CQC catches regressions when metadata changes. Critical for production-quality data publishing.

**Pattern:** Endpoint + in-memory store — `backend/cqc.py` with `validate_on_upload()` hook and `validation_history` dict. Follows the existing `arc_record_store` pattern.

**Reference:** `AGENTS.md` → Facade Pattern (MappingEngine), `backend/main.py:_ensure_store_populated()` (lazy init pattern), `backend/oai_pmh.py` (stateful in-memory store pattern).

**Depends on:** Existing `/arc/validate/fairagro` endpoint.

**Target user:** DataHUB CI/CD pipelines, repository curators, data stewards.

**Acceptance:**

- [ ] Every `/convert/arc-export` call auto-triggers validation and stores history
- [ ] `GET /cqc/history/{oai_identifier}` returns timestamped validation results
- [ ] `POST /cqc/webhook` validates a given ARC JSON and returns result (for external CI)
- [ ] Validation status badge: "Passing" (green last N runs), "Failing" (red), "Unknown" (gray)

---

#### F7 · FAIRagro DMP generator

**What:** A lightweight, FAIRagro-specific Data Management Plan generator. Pre-filled questions about agricultural data (crops, sensors, soil, weather stations). Templates for DFG, BMBF, Horizon Europe. AI-assisted text→DMP conversion (inspired by DataPLAN's alpha AI feature).

**Why:** DataPLAN covers all plant science. No tool covers FAIRagro's domain-specific concerns (field trials, precision agriculture, soil science, UAV sensors). Researchers must fill generic DMPs that miss domain context.

**Pattern:** Template registry (YAML) + Facade generator — `backend/dmp/templates/*.yaml` (one per funder), `backend/dmp/generator.py` (fills template from metadata), `ai_client.py` (text→DMP conversion).

**Reference:** `AGENTS.md` → Registry Pattern (pivot_registry.yaml), Facade Pattern (MappingEngine), `backend/ai_client.py`.

**Depends on:** GWDG AI client (for text→DMP). `pivot_registry.yaml` (field definitions to pre-fill). New: `backend/dmp/` directory.

**Target user:** PIs writing grant proposals, data stewards documenting plans.

**Acceptance:**

- [ ] `GET /dmp/templates` lists available funder templates
- [ ] `POST /dmp/generate` accepts `template_id` + `metadata_file` → pre-filled DMP document
- [ ] `POST /dmp/ai-fill` accepts free text + `template_id` → AI-extracted DMP fields
- [ ] Export: JSON (for import), Word (.docx), PDF, plain text
- [ ] Templates: DFG, BMBF, Horizon Europe, FAIRagro generic

---

#### F8 · ARC Commander CLI wrapper

**What:** Headless CLI for ARC operations — validate, convert, summarize, export — callable from shell scripts and CI/CD.

**Why:** ARC Commander is ARC life-cycle. Our CLI would be conversion pipeline — complementary, not competing. Users on HPC clusters or in automated workflows need a CLI.

**Pattern:** CLI wrapper — `backend/cli.py` using `argparse` or `typer`. Reuses `MappingEngine` + `FairagroArcValidator` + summary generator (F1).

**Reference:** `AGENTS.md` → Facade Pattern (MappingEngine), `backend/main.py` (endpoint wiring).

**Depends on:** Core engine (no new backend logic). F1 (summary generator).

**Target user:** HPC users, CI/CD pipelines, automated harvesters.

**Acceptance:**

- [ ] `fairweaver convert input.json --source schema_org --pivot fairagro_searchhub`
- [ ] `fairweaver validate arc.json --template fairagro`
- [ ] `fairweaver summarize arc.json --output README.md`
- [ ] `fairweaver harvest https://example.org/oai --prefix oai_dc --pivot fairagro_searchhub`
- [ ] Piped: `cat input.json | fairweaver convert --source schema_org`

---

#### F9 · GitLab DataHUB push

**What:** After ARC export, push the generated ARC to a GitLab DataHUB instance via the GitLab API. User provides a Personal Access Token (PAT) and target project path.

**Why:** We generate ARC. Users manually download and upload. Closing this loop makes us a one-click "convert and publish" tool.

**Pattern:** Adapter — `backend/repositories/gitlab_adapter.py` implementing `push(arc_data, project_path, pat) -> commit_sha`. Follows the existing `ai_client.py` pattern (thin API wrapper with retries).

**Reference:** `AGENTS.md` → Adapter Pattern, `backend/ai_client.py` (API client pattern).

**Depends on:** ARC export pipeline. GitLab API (no new Python deps — `requests` or `httpx` already in pyproject.toml).

**Target user:** Anyone publishing ARCs to a DataHUB.

**Acceptance:**

- [ ] `POST /repositories/gitlab/push` accepts `arc_json`, `project_id`, `access_token`
- [ ] Creates or updates ARC repo on GitLab
- [ ] Creates commit with generated ARC files (isa.*.xlsx stubs + ro-crate-metadata.json)
- [ ] Returns commit SHA + GitLab project URL
- [ ] Frontend: "Push to DataHUB" button in ArcCrateView (after ARC tab)

---

#### F10 · DOI minting (DataCite API)

**What:** Mint a DOI for a converted ARC via the DataCite REST API. User provides DataCite credentials (repository prefix + password). The DOI points to the ARC's landing page or GitLab repo.

**Why:** Without a DOI, the ARC is not formally published. ARChigator handles this in DataPLANT. We need the equivalent for FAIRagro.

**Pattern:** Adapter — `backend/repositories/datacite_adapter.py` implementing `mint_doi(metadata: dict, url: str) -> doi_string`. Follows the same adapter pattern as F9.

**Reference:** `AGENTS.md` → Adapter Pattern, `backend/ai_client.py`.

**Depends on:** DataCite API credentials. F9 (GitLab push) for the target URL.

**Target user:** ARC publishers needing persistent identifiers.

**Acceptance:**

- [ ] `POST /repositories/datacite/mint` accepts `arc_metadata`, `target_url`, `credentials`
- [ ] Registers DOI with DataCite using ARC metadata as DataCite XML
- [ ] Returns DOI string (e.g., `10.1234/fairagro.abc123`)
- [ ] DOI resolves to target_url (the GitLab ARC project from F9)
- [ ] Stores DOI in ARC's OAI-PMH record store

---

### Strategic Features (multi-week)

#### F11 · Multi-ELN adapter pattern

**What:** Generalize F5 (eLabFTW) to a multi-ELN adapter framework. Add adapters for Chemotion, LabArchives, RSpace, openBIS. Each adapter implements the same `fetch()` / `convert()` interface.

**Pattern:** Strategy — same as F5, but `backend/elns/adapter_registry.yaml` (registry pattern, like pivot_registry.yaml) lists available adapters. `backend/elns/loader.py` auto-discovers adapter plugins at startup.

**Reference:** `AGENTS.md` → Strategy Pattern + Registry Pattern, `backend/plugins/loader.py`, `backend/pivot_registry.yaml`.

**Depends on:** F5 (eLabFTW adapter as reference implementation).

**Target user:** Any researcher using an ELN who wants FAIRagro-compliant ARCs.

**Acceptance:**

- [ ] Adapter interface: `class ElnAdapter(Protocol): fetch(id) -> dict; convert(data) -> dict`
- [ ] Auto-discovery via `backend/elns/loader.py` (mirrors `plugins/loader.py`)
- [ ] ELN registry: `backend/elns/adapter_registry.yaml` with label, domains, auth method
- [ ] `GET /eln/adapters` returns available ELN adapters
- [ ] `POST /eln/convert` dispatches to appropriate adapter based on `eln_type`

---

#### F12 · Real-time ontology annotation (Swate-lite in browser)

**What:** Full browser-based Swate-like annotation experience. Ontology term search (OLS, Bioportal API), building blocks (reusable annotation templates), term validation, JSON import/export. Builds on F3 (annotation table).

**Why:** Swate is Excel/VSCode-only and plant-focused. A web-native, domain-agnostic annotation tool feeds our conversion pipeline with semantically rich metadata.

**Pattern:** Component cascade — `AnnotationTable` (F3) + `TermSearch` + `BuildingBlockSelector` + `OntologyBrowser`. Backend: `/ontologies/search` (proxies OLS/Bioportal).

**Reference:** `AGENTS.md` → Typed API Contract, Facade Pattern (new `OntologyService` facade).

**Depends on:** F3 (annotation table as base), OLS API (<https://www.ebi.ac.uk/ols4/api>), Bioportal API.

**Target user:** Cross-domain researchers annotating agricultural data with ontology terms.

**Acceptance:**

- [ ] Term search with autocomplete (OLS + Bioportal)
- [ ] Building blocks: saved annotation column templates (parameter + unit + term)
- [ ] Template library per domain (agronomy, soil, genomics)
- [ ] Export: ISA-Tab JSON, our flat dict (for `/convert`), CSV
- [ ] Import: Swate JSON templates (interoperability with Swate)

---

#### F13 · Repository adapters (e!DAL-PGP, BonaRes, Pangaea)

**What:** Direct push adapters for key FAIRagro repositories. Not just OAI-PMH harvest (which we already do), but *write-back*: convert our output to their expected format and push.

**Why:** OAI-PMH is harvest-only. To close the loop, we need to push converted metadata *into* repositories. Each adapter handles auth, format mapping, and upload.

**Pattern:** Strategy — `backend/repositories/e!dal_adapter.py`, `bonaRes_adapter.py`, `pangaea_adapter.py`. Same interface as F9 (GitLab adapter).

**Reference:** `AGENTS.md` → Strategy Pattern, `backend/repositories/gitlab_adapter.py` (F9).

**Depends on:** F9 (reference implementation), F10 (DOI minting for some repos).

**Target user:** FAIRagro data providers publishing to domain repositories.

**Acceptance:**

- [ ] `POST /repositories/push` with `repository_id` + `arc_data` + `credentials`
- [ ] e!DAL-PGP: Schema.org JSON-LD upload via REST API
- [ ] BonaRes: INSPIRE XML via OAI-PMH or REST
- [ ] Pangaea: DataCite XML via OAI-PMH or direct API
- [ ] Returns repository URL + identifier

---

#### F14 · ARC Summary generator with full section customization

**What:** Upgrade F1 (quick summary) to full ARC Summary feature parity with DataPLANT. Customizable YAML config, ProvenanceGraph (ASA + ArcTables), OverviewTable, per-study/per-assay detail sections.

**Why:** F1 gives a basic README. This makes ARC documentation a first-class output — competitive with DataPLANT's ARC Summary tool but for our domain-specific ARCs.

**Pattern:** Same as F1 but expanded — `backend/arc_summary/summary_generator.py` reads `.arc/arc_summary.yml` config and produces per-section markdown.

**Reference:** `AGENTS.md` → Registry Pattern + Strategy Pattern, [DataPLANT ARC Summary docs](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/resources/arc-summary/).

**Depends on:** F1 (base summary generator).

**Target user:** ARC producers needing publication-quality documentation.

**Acceptance:**

- [ ] Sections: Investigation, TOC, ProvenanceGraph (AsISA + AsArcTables), OverviewTable, Studies, Assays
- [ ] Customizable via `.arc/arc_summary.yml` — reorder/remove sections
- [ ] ProvenanceGraph: Mermaid.js flowchart showing study↔assay relationships
- [ ] OverviewTable: markdown table with key metadata
- [ ] Merge request auto-creation (if pushing to GitLab via F9)

---

#### F15 · Live Coverage Heatmap — multi-dataset matrix

**What:** Upgrade F4 (per-dataset heatmap) to a multi-dataset coverage matrix. Upload multiple datasets, see coverage across all pivots in a matrix view. Identify which datasets are "ready" for which standards.

**Why:** FAIRagro Search Hub ingests from multiple RDIs. A matrix view helps curators prioritize: "We have 10 datasets, which ones meet FAIRagro minimum? Which need Bioschemas enrichment?"

**Pattern:** Component — `frontend/src/components/CoverageMatrix.tsx` consuming multiple `ConvertResult` objects.

**Reference:** `AGENTS.md` → Typed API Contract, `frontend/src/components/CoverageHeatmap.tsx` (F4).

**Depends on:** F4 (per-dataset heatmap).

**Target user:** Data stewards managing multiple datasets, FAIRagro Search Hub curators.

**Acceptance:**

- [ ] Matrix: rows = datasets, columns = pivot profiles, cells = coverage %
- [ ] Color-coded: green (≥required), amber (≥recommended), red (<required)
- [ ] Click cell → expand field-level breakdown
- [ ] "Batch export" → export all datasets meeting a threshold as ARCs (via existing batch processor)

---

## 6. Anti-Features — DO NOT Build

These are capabilities DataPLANT already owns. Building them in FAIRagro-MI would dilute our niche and create user confusion.

| Anti-feature | Why we don't build it | What we do instead |
|-------------|----------------------|-------------------|
| ARC creation GUI (ARCitect, ARCManager) | DataPLANT has 3 mature tools for this (ARCitect, ARCManager, ARC Commander). Rebuilding is wasted effort. | Link out from our UI: "Open in ARCitect" / "Open in ARCManager". |
| DataHUB storage layer | Infrastructure play — they own the GitLab instance. We're a consumer. | F9 (GitLab push) makes us a client of their infrastructure. |
| Excel-based annotation (Swate) | Swate is the canonical Excel annotation tool. Browser + Excel would fragment user workflow. | F3 (annotation table in browser) and F12 (ontology annotation in browser) instead. |
| ARC Commander (full CLI) | Their CLI (`arc`) is mature — init, clone, sync, ISA edits, export. Rebuilding is pointless. | F8 (CLI wrapper) provides conversion commands only. Delegate ARC lifecycle to `arc` CLI. |
| CQC pipelines as CI infrastructure | DataHUB CI is a GitLab feature. We're not building a GitLab instance. | F6 (validation webhook) provides the *validation step* that CI pipelines can call. |
| ELN server (eLabFTW deployment) | eLabFTW is a separate product. We're an integration layer. | F5 (ELN connector) and F11 (multi-ELN adapters) pull from existing ELN instances. |
| DataPLAN full DMP infrastructure | DataPLAN is a complete DMP tool with 10+ templates, offline mode, caching, and a publication. Rebuilding is massive scope creep. | F7 (FAIRagro DMP) is lightweight, domain-specific, and feeds our pipeline — not a general-purpose DMP. |
| ARC publication archive (ARChive) | The ARChive is their Zenodo-like repository. We don't run infrastructure. | F10 (DOI minting) makes our ARCs citable without building a repository. |
| ARC validation packages authoring tool | DataPLANT has a package system with validation package authoring. We consume their packages. | Link to their validation packages. Our validator applies one template (FAIRagro). |

---

## 7. Decision Framework

When evaluating a new feature, answer these 5 questions:

| # | Question | If "no" → defer or reject |
|---|----------|---------------------------|
| 1 | Does it strengthen **conversion / validation / classification** (our core niche)? | Defer — it's outside our scope. |
| 2 | Is it **domain-agnostic** (NFDI-wide, not just plants)? | Reject unless explicitly FAIRagro-funded. |
| 3 | Does it fill a gap **DataPLANT does NOT own**? | Defer — build integration instead of competition. |
| 4 | Does it follow existing **patterns** (Strategy, Facade, Registry, Adapter)? | Reject — ad-hoc code violates AGENTS.md rules. |
| 5 | Can it be delivered in **≤2 weeks** (or split into Quick Wins first)? | Split into micro-tasks. No big-bang features. |

**Example evaluations:**

| Feature | Q1 (core?) | Q2 (agnostic?) | Q3 (gap?) | Q4 (pattern?) | Q5 (≤2w?) | Verdict |
|---------|-----------|---------------|----------|-------------|----------|---------|
| F1 (README gen) | Yes | Yes | Yes | Yes (Strategy) | Yes (Quick) | BUILD |
| F7 (DMP gen) | Partial | No (FAIRagro) | Yes | Yes (Registry+Facade) | Medium | BUILD (with FAIRagro scoping) |
| Swate clone | Yes | Yes | No (DataPLANT owns) | Yes | Large | REJECT — use F3/F12 as Swate-lite |
| ARCitect clone | No | No | No | Yes | Large | REJECT — link out |

---

## 8. Backlog Metadata

| ID | Priority | Effort | Depends on | Target user | Status |
|----|----------|--------|------------|-------------|--------|
| F1 | 1 (HIGH) | Quick | ARC export | ARC producers | proposed |
| F2 | 2 (MED) | Quick | Mapping engine | Ontology curators | proposed |
| F3 | 2 (MED) | Quick | Pivot registry | Wet-lab researchers | proposed |
| F4 | 3 (LOW) | Quick | /convert | Data owners | proposed |
| F5 | 1 (HIGH) | Medium | ARC export, ELN API | Wet-lab researchers | proposed |
| F6 | 1 (HIGH) | Medium | /arc/validate/fairagro | CI/CD, curators | proposed |
| F7 | 2 (MED) | Medium | GWDG AI, pivot registry | PIs, stewards | proposed |
| F8 | 3 (LOW) | Quick | Core engine, F1 | HPC users, CI/CD | proposed |
| F9 | 1 (HIGH) | Medium | ARC export, GitLab PAT | ARC publishers | proposed |
| F10 | 2 (MED) | Medium | F9, DataCite API | ARC publishers | proposed |
| F11 | 3 (LOW) | Large | F5 | ELN users | proposed |
| F12 | 3 (LOW) | Large | F3, OLS API | Cross-domain researchers | proposed |
| F13 | 3 (LOW) | Large | F9, F10 | Repository contributors | proposed |
| F14 | 3 (LOW) | Medium | F1 | ARC producers | proposed |
| F15 | 3 (LOW) | Medium | F4 | Data stewards | proposed |

**Priority key:** 1 = core differentiator, 2 = complements core, 3 = nice-to-have

---

## 9. References

### DataPLANT tools (source of analysis)

- [DataPLANT Toolbox](https://nfdi4plants.github.io/toolbox/)
- [ARCitect](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/arcitect/)
- [Swate](https://swate-alpha.nfdi4plants.org/)
- [DataPLAN](https://dmpg.nfdi4plants.org/)
- [ARCManager](https://nfdi4plants.org/nfdi4plants.knowledgebase/arc-manager/)
- [elab2ARC](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/resources/elab2arc/)
- [ARC Summary](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/resources/arc-summary/)
- [CQC pipelines](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/arc-validation/cqc-pipelines/)
- [ARChigator](https://nfdi4plants.github.io/nfdi4plants.knowledgebase/datahub/data-publications/datahub-data-publications-archigator/)

### Our docs

- `AGENTS.md` — design patterns, code conventions, workflow
- `docs/middleware-connector-architecture.md` — middleware federation service design
- `docs/architecture/` — PlantUML pipeline diagrams
- `README.md` — project overview and roadmap

### External specs

- [SSSOM spec](https://mapping-commons.github.io/sssom/)
- [DataCite API](https://support.datacite.org/docs/api)
- [GitLab API](https://docs.gitlab.com/ee/api/)
- [OLS API](https://www.ebi.ac.uk/ols4/api)
- [eLabFTW API](https://doc.elabftw.net/api.html)
