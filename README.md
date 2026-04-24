# 🧬 FAIRweaver

> AI-assisted metadata interoperability platform with selectable pivot.
> BioHackathon Germany 2026 · de.NBI Cloud · Apache 2.0

FAIRweaver converts research metadata between formats (ISA-JSON, DataCite, RO-Crate, Darwin Core, MIAPPE) using a **selectable interoperability pivot** (Bioschemas, AgroSchemas, Schema.org, or your own JSON-LD context). A local AI model (Ollama) generates portable YAML mappings and suggests missing FAIR fields — all inference runs on-premise, no data leaves your environment.

---

## Quickstart (development)

### 1. Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:5173
```

### 3. Full stack with Docker (includes Ollama)

```bash
cp .env.example .env
docker compose up
# UI + API at http://localhost:8000
```

Pull the AI model on first run:
```bash
docker compose exec ollama ollama pull mistral:7b-instruct-q4_K_M
```

---

## Project structure

```
fairweaver/
├── backend/
│   ├── main.py                  ← FastAPI app
│   ├── mapping_engine.py        ← pivot registry, YAML mapping, conversion
│   ├── pivot_registry.yaml      ← registered pivot profiles
│   ├── mappings/                ← community YAML mapping files
│   ├── plugins/
│   │   ├── loader.py            ← auto-discovers format plugins
│   │   └── formats/
│   │       ├── isa_json_plugin.py
│   │       └── datacite_xml_plugin.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              ← main UI
│   │   ├── components/
│   │   │   ├── UploadZone.jsx
│   │   │   ├── PivotSelector.jsx
│   │   │   ├── MappingEditor.jsx
│   │   │   └── SuggestionPanel.jsx
│   │   └── api/
│   │       └── client.js        ← all API calls
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Adding a new format plugin

Create `backend/plugins/formats/myformat_plugin.py`:

```python
FORMAT_ID = "my_format"
LABEL = "My Format"
EXTENSIONS = [".xyz"]

def load(content: bytes) -> dict:
    # Parse bytes → flat dict
    ...

def write(json_ld: dict) -> dict:
    # Convert pivot JSON-LD → target format
    ...
```

That's it — the plugin is auto-discovered on next startup.

---

## Adding a new pivot

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

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pivots` | List registered pivot profiles |
| POST | `/pivots/recommend` | AI-recommend best pivot for input file |
| GET | `/mappings` | List available YAML mappings |
| POST | `/mappings/generate` | AI-generate a YAML mapping draft |
| POST | `/mappings/validate` | Validate a YAML mapping file |
| POST | `/convert` | Convert input → pivot JSON-LD |
| POST | `/convert/chain` | Convert input → pivot → target format |

Interactive docs: `http://localhost:8000/docs`

---

## Roadmap (hackathon week — Dec 2026)

- [ ] Ollama + RAG pipeline over YAML mapping corpus
- [ ] Additional format plugins: RO-Crate, Darwin Core CSV, MIAPPE XLSX
- [ ] YAML mapping editor in the UI
- [ ] Custom pivot upload (JSON-LD context)
- [ ] Validation against 10 real NFDI4Agri datasets
- [ ] SSSOM export compatibility

---

## Contributing

YAML mappings are CC0. Code is Apache 2.0. PRs welcome — see plugin docs above.

**BioHackathon Germany 2026** · Göttingen · 07–11 December 2026