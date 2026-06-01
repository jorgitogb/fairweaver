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
│   ├── plugins/
│   │   ├── loader.py             ← auto-discovers format plugins at startup
│   │   └── formats/
│   │       ├── isa_json_plugin.py
│   │       └── datacite_xml_plugin.py
│   ├── pyproject.toml            ← uv/hatchling config
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── Main.tsx              ← app entry point
│   │   ├── components/
│   │   │   ├── UploadZone.tsx
│   │   │   ├── PivotSelector.tsx
│   │   │   ├── MappingEditor.tsx
│   │   │   └── SuggestionPanel.tsx
│   │   └── api/
│   │       └── client.ts         ← typed API client (all fetch calls)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
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

| Method | Path                 | Description                                   |
| ------ | -------------------- | --------------------------------------------- |
| GET    | `/pivots`            | List registered pivot profiles                |
| POST   | `/pivots/recommend`  | AI-recommend best pivot for an input file     |
| GET    | `/mappings`          | List available YAML mappings                  |
| POST   | `/mappings/generate` | AI-generate a YAML mapping draft              |
| POST   | `/mappings/validate` | Validate a YAML mapping file                  |
| POST   | `/convert`           | Convert input → pivot JSON-LD                 |
| POST   | `/convert/chain`     | Bidirectional: source → pivot → target format |
| POST   | `/harvest/convert`   | Harvest from OAI-PMH + convert to pivot JSON-LD |

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

---

## Adding a format plugin

Create `backend/plugins/formats/myformat_plugin.py`:

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

- [ ] RAG pipeline over YAML mapping corpus (embeddings via GWDG API)
- [ ] Format plugins: RO-Crate, Darwin Core CSV, MIAPPE XLSX
- [ ] YAML mapping editor in the UI
- [ ] Custom pivot upload (JSON-LD context)
- [ ] Validation against 10 real NFDI4Agri datasets
- [ ] SSSOM export compatibility

---

## Contributing

YAML mappings are **CC0**. Code is **Apache 2.0**. PRs welcome.

See `AGENTS.md` for architecture notes and common issues if you are using an AI coding assistant.

**BioHackathon Germany 2026** · Göttingen · 07–11 December 2026
