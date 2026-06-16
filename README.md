# 🧬 FAIRweaver

> AI-assisted metadata interoperability platform with selectable pivot.  
> BioHackathon Germany 2026 · de.NBI Cloud · Apache 2.0

FAIRweaver converts research metadata between formats (ISA-JSON, DataCite, RO-Crate, Darwin Core, MIAPPE) using a **selectable interoperability pivot** — Bioschemas, AgroSchemas, Schema.org, or your own JSON-LD context. An AI model generates portable YAML mapping files and suggests missing FAIR fields. All AI inference runs via the [GWDG Academic Cloud API](https://docs.hpc.gwdg.de/services/saia/index.html) — no local GPU required.

---

## Quickstart (development)

### Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- A GWDG Academic Cloud API key → [docs.hpc.gwdg.de/services/saia](https://docs.hpc.gwdg.de/services/saia/index.html)

### 1. Backend

```bash
cd backend
cp ../.env.example ../.env   # add your OPENAI_API_KEY
uv sync
uv run uvicorn main:app --reload
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

### 3. Full stack with Docker

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
docker compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:8080
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in your key:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://chat-ai.academiccloud.de/v1
OPENAI_MODEL=meta-llama-3.1-8b-instruct
LOG_LEVEL=info
```

The API is OpenAI-compatible — `OPENAI_BASE_URL` points to GWDG by default but can be swapped for any compatible endpoint.

---

## Project structure

```
fairweaver/
├── backend/
│   ├── main.py                   ← FastAPI app + all REST endpoints
│   ├── mapping_engine.py         ← pivot registry, YAML mapping, conversion
│   ├── ai_client.py              ← GWDG API wrapper (mapping gen, suggestions, RAG)
│   ├── pivot_registry.yaml       ← registered pivot profiles
│   ├── mappings/                 ← community YAML mapping files (CC0)
│   ├── arc_templates/            ← ARC validation templates + fairagro_validator.py
│   ├── formats/                  ← format plugins (auto-discovered)
│   │   ├── isa_json_plugin.py
│   │   ├── datacite_xml_plugin.py
│   │   ├── schema_org_plugin.py
│   │   ├── ro_crate_plugin.py
│   │   ├── darwin_core_csv_plugin.py
│   │   ├── schema_org_arc_plugin.py
│   │   └── oai_dc_plugin.py
│   ├── plugins/loader.py         ← auto-discovers format plugins at startup
│   ├── pyproject.toml            ← uv/hatchling config
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── Main.tsx              ← app entry point
│   │   ├── components/
│   │   │   ├── UploadZone.tsx
│   │   │   ├── PivotSelector.tsx
│   │   │   ├── MappingEditor.tsx
│   │   │   ├── SuggestionPanel.tsx
│   │   │   ├── ComparisonView.tsx
│   │   │   ├── ArcExportPanel.tsx
│   │   │   ├── ArcBatchProcessor.tsx
│   │   │   ├── ArcTemplateSelector.tsx
│   │   │   ├── ArcCrateView.tsx
│   │   │   ├── ComplianceBadge.tsx
│   │   │   ├── HarvestZone.tsx
│   │   │   └── SimplePivotSelector.tsx
│   │   ├── api/
│   │   │   └── client.ts         ← typed API client (all fetch calls)
│   │   └── App.tsx               ← main application with demo flow
│   ├── package.json
│   ├── vite.config.js
│   ├── tsconfig.json
│   └── Dockerfile
├── sample-data/
│   └── demo/                     ← 12 demo files (2 themes x 3 levels x 2 formats)
│       ├── schema-org-{wheat,maize}-{basic,intermediate,full}.json
│       ├── arc-ro-crate-{wheat,maize}-{basic,intermediate,full}.json
│       └── generate_demo_data.py
├── docs/
│   ├── architecture/             ← PlantUML pipeline diagrams
│   ├── demo/                     ← ARC composition & compliance docs
│   └── demo-spec.md              ← FAIRagro demo suite specification
├── docker-compose.yml
├── .env.example
├── AGENTS.md                     ← guide for AI coding assistants
└── README.md
```

---

## AI models (GWDG Academic Cloud)

| Task                        | Default model                | Override env var |
| --------------------------- | ---------------------------- | ---------------- |
| YAML mapping generation     | `llama-3.3-70b-instruct`     | `OPENAI_MODEL`   |
| Real-time field suggestions | `meta-llama-3.1-8b-instruct` | —                |
| Embeddings / RAG            | `e5-mistral-7b-instruct`     | —                |

All available models: [docs.hpc.gwdg.de/services/chat-ai/models](https://docs.hpc.gwdg.de/services/chat-ai/models/index.html)

---

## API endpoints

| Method | Path                        | Description                                    |
| ------ | --------------------------- | ---------------------------------------------- |
| GET    | `/pivots`                   | List registered pivot profiles                 |
| POST   | `/pivots/recommend`         | AI-recommend best pivot for an input file      |
| GET    | `/mappings`                 | List available YAML mappings                   |
| POST   | `/mappings/generate`        | AI-generate a YAML mapping draft               |
| POST   | `/mappings/validate`        | Validate a YAML mapping file                   |
| POST   | `/convert`                  | Convert input → pivot JSON-LD                  |
| POST   | `/convert/chain`            | Bidirectional: source → pivot → target format  |
| POST   | `/convert/arc-export`       | Convert Schema.org → ARC RO-Crate              |
| POST   | `/harvest/convert`          | Harvest from OAI-PMH + convert to pivot JSON-LD |
| POST   | `/arc/validate/fairagro`    | Validate ARC against FAIRagro template         |
| POST   | `/compliance/classify`      | Classify FAIRagro compliance level (basic/intermediate/full) |
| GET    | `/oai-pmh`                  | OAI-PMH 2.0 server (fairagro_arc format)       |
| POST   | `/list-sets`                | List OAI-PMH metadata sets                     |
| GET    | `/source-formats/schema-org` | Schema.org field definitions                   |
| GET    | `/template-fields/{id}`     | ARC template field structure                   |

Interactive docs at `http://localhost:8000/docs`

---

## Workflow

### 1. File Upload Flow

1. **Upload** a metadata file (ISA-JSON, DataCite XML, Darwin Core CSV, MIAPPE XLSX, RO-Crate JSON-LD)
2. **AI recommends** the best interoperability pivot (Bioschemas, AgroSchemas, Schema.org)
3. **Select pivot** — choose from available interoperability profiles
4. **Convert** — get JSON-LD output with field coverage, matched fields, and missing fields
5. **Review** — see which required/recommended fields are present or missing

### 2. OAI-PMH Harvest Flow

1. **Enter endpoint** — provide OAI-PMH base URL (e.g., `https://ws.pangaea.de/oai/provider`)
2. **Select format** — choose `oai_dc` (Dublin Core) or `oai_datacite`
3. **Optional filters** — set spec, from date, until date
4. **Harvest & convert** — fetch records and map to FAIRagro Search Hub pivot
5. **Review results** — accordion list showing each record with coverage %, matched fields, and missing fields

### 3. ARC Export Flow

1. **Upload Schema.org JSON** via the ARC Export panel
2. **Compliance badge** shown — Basic (red), Intermediate (amber), Full (green)
3. **Convert & preview** — ARC RO-Crate JSON-LD with 3-tab viewer (ARC / FAIRagro JSON-LD / Validation)
4. **FAIRagro JSON-LD** — auto-derived from ARC, formatted for Search Hub consumption
5. **OAI-PMH serving** — converted records published automatically to `GET /oai-pmh` (fairagro_arc format)
6. **Download** ARC RO-Crate or FAIRagro JSON-LD file

### 4. FAIRagro Demo Suite

The repo ships with 12 pre-built demo files (2 agricultural themes × 3 compliance levels × 2 formats):

| Theme        | Compliance Levels        | Institution              |
| ------------ | ------------------------ | ------------------------ |
| Wheat 🌾     | Basic / Intermediate / Full | RPTU Kaiserslautern    |
| Maize 🌽     | Basic / Intermediate / Full | IPK Gatersleben        |

Start the backend and visit `http://localhost:8000/oai-pmh?verb=ListRecords&metadataPrefix=fairagro_arc` — 6 demo ARC records are served immediately. Upload the Schema.org demo files through the UI to see compliance badge + ArcCrateView output.

---

## Adding a format plugin

Create `backend/formats/myformat_plugin.py`:

```python
FORMAT_ID = "my_format"
LABEL = "My Format"
EXTENSIONS = [".xyz"]

def load(content: bytes) -> dict:
    # Parse bytes → flat dict for the mapping engine
    ...

def write(json_ld: dict) -> dict:
    # Convert pivot JSON-LD → target format
    ...
```

The plugin is auto-discovered on next startup — no registration needed.

---

## Adding a pivot

Add an entry to `backend/pivot_registry.yaml`:

```yaml
my_consortium_schema:
  label: "My Consortium Schema"
  context_url: "https://myorg.org/schema/v1"
  domains: [my_domain]
  required_fields: [identifier, name, description]
  recommended_fields: [license, creator]
```

---

## Roadmap (hackathon week · 07–11 Dec 2026)

- [x] Format plugins: RO-Crate, Darwin Core CSV, schema.org, schema.org→ARC, OAI-DC
- [x] Schema.org → ARC RO-Crate conversion with 3 compliance levels
- [x] FAIRagro JSON-LD export from ARC RO-Crate
- [x] OAI-PMH 2.0 server (fairagro_arc metadata format)
- [x] Compliance badge + ArcCrateView 3-tab UI
- [x] Demo suite: 12 files across 2 agricultural themes
- [ ] YAML mapping editor in the UI
- [ ] Custom pivot upload (JSON-LD context)
- [ ] Validation against 10 real NFDI4Agri datasets
- [ ] RAG pipeline over YAML mapping corpus (embeddings via GWDG API)
- [ ] SSSOM export compatibility

---

## Contributing

YAML mappings are **CC0**. Code is **Apache 2.0**. PRs welcome.

See `AGENTS.md` for architecture notes and common issues if you are using an AI coding assistant.

**BioHackathon Germany 2026** · Göttingen · 07–11 December 2026
