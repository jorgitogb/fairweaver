# FAIRweaver — Agent Guide

This file is the authoritative reference for AI coding agents (Cursor, Copilot, Claude Code, etc.)
working on this codebase. Read it fully before making any change.

---

## Quick Commands

```bash
# Backend
cd backend && uv sync && uv run uvicorn main:app --reload
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs

# Frontend
cd frontend && npm install && npm run dev
# UI: http://localhost:5173

# Typecheck frontend without building
cd frontend && npm run typecheck

# Full stack
cp .env.example .env   # set OPENAI_API_KEY
docker compose up
# Backend: http://localhost:8000  |  Frontend: http://localhost:8080
```

---

## Architecture Overview

FAIRweaver is a **monorepo** with two independent services that communicate only via REST:

```
┌─────────────────────────────────────┐
│  frontend/  (React + Vite + TS)     │  port 5173 (dev) / 8080 (prod)
│  All API calls via src/api/client.ts│
└────────────────┬────────────────────┘
                 │ HTTP/JSON
┌────────────────▼────────────────────┐
│  backend/  (FastAPI + Python 3.12)  │  port 8000
│  main.py → mapping_engine.py        │
│         → ai_client.py              │
│         → plugins/loader.py         │
└─────────────────────────────────────┘
```

**Rule:** Frontend never reads files directly. Backend never touches the DOM.
Any new capability must be exposed as a REST endpoint first, then consumed by the UI.

---

## Design Patterns in Use

Understanding these patterns is essential before modifying or extending the codebase.
Do not replace them with ad-hoc code — extend them.

### 1. Strategy Pattern — Format Plugins

**Where:** `backend/plugins/formats/*_plugin.py`

Each format (ISA-JSON, DataCite, Darwin Core…) is a plugin that implements the same interface:

```python
FORMAT_ID = "isa_json"          # unique identifier used in API calls
LABEL     = "ISA-JSON"          # human-readable label for the UI
EXTENSIONS = [".json"]          # for auto-detection

def load(content: bytes) -> dict:
    """Parse raw file bytes → flat dict for the mapping engine."""
    ...

def write(json_ld: dict) -> dict:
    """Convert pivot JSON-LD → this format's output structure."""
    ...
```

`plugins/loader.py` discovers all `*_plugin.py` files at startup using `importlib` — no registration
needed. Adding a new format = adding one file. Never add format logic to `main.py` or
`mapping_engine.py`.

### 2. Registry Pattern — Pivot Profiles

**Where:** `backend/pivot_registry.yaml` + `MappingEngine._load_registry()`

Pivots (Bioschemas, AgroSchemas, Schema.org…) are data, not code. They live in a YAML registry
that the engine reads at startup. To add a new pivot, edit the YAML — no Python changes needed.

```yaml
bioschemas_dataset:
  label: "Bioschemas Dataset"
  context_url: "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"
  domains: [genomics, biodiversity, general]
  required_fields: [identifier, name, description, url, keywords, license]
  recommended_fields: [creator, datePublished, publisher, version]
```

The engine scores input fields against `required_fields` + `recommended_fields` to produce
a coverage percentage. This drives both the AI recommendation and the SuggestionPanel UI.

### 3. Facade Pattern — MappingEngine

**Where:** `backend/mapping_engine.py`

`MappingEngine` is the single entry point for all conversion logic. `main.py` calls it;
`ai_client.py` is called by it. Nothing else should call `ai_client.py` directly.

```
main.py (HTTP layer)
    └── MappingEngine (domain logic)
            ├── pivot registry
            ├── YAML mapping files
            ├── format plugin dispatch
            └── ai_client (AI generation + RAG)
```

### 4. Graceful Degradation — AI Fallback

**Where:** `mapping_engine.py → generate_mapping()`

Every AI call is wrapped in `try/except`. If the GWDG API is unavailable, the engine falls back
to rule-based field matching. This ensures the platform works even without an API key.

```python
try:
    mapping = generate_mapping_ai(...)   # GWDG API
except Exception:
    mapping = self._rule_based_mapping() # deterministic fallback
```

Never remove this pattern. Never let an AI failure raise an HTTP 500.

### 5. Typed API Contract — client.ts

**Where:** `frontend/src/api/client.ts`

All TypeScript interfaces that mirror the backend's JSON responses live here. When you add a new
field to a backend response, add it to the interface in `client.ts` first, then consume it in
the component. Never use `any` for API response types.

---

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/). Every commit title must follow:

```
<type>(<scope>): <short description in imperative mood>
```

### Types

| Type       | When to use                          |
| ---------- | ------------------------------------ |
| `feat`     | New capability visible to users      |
| `fix`      | Bug fix                              |
| `refactor` | Code change with no behaviour change |
| `perf`     | Performance improvement              |
| `test`     | Adding or fixing tests               |
| `docs`     | Documentation only                   |
| `chore`    | Tooling, deps, config (no prod code) |
| `ci`       | CI/CD changes                        |

### Scope

Use the affected layer: `backend`, `frontend`, `plugin`, `pivot`, `mapping`, `docker`, `ai`

### Examples

```bash
feat(plugin): add Darwin Core CSV loader
fix(backend): handle empty field_rules in YAML mapping validator
refactor(mapping-engine): extract _score_pivot_coverage into separate method
perf(ai): cache embedding vectors in-memory to avoid redundant API calls
docs(agents): add design pattern explanations
chore(deps): bump openai to 1.52.0
feat(frontend): add confidence score badge to PivotSelector cards
fix(frontend): prevent double submit on convert button click
feat(pivot): add MIAPPE pivot profile to registry
test(plugin): add round-trip test for ISA-JSON loader and writer
```

### Rules for agents

- One logical change per commit. Do not bundle a fix and a refactor in the same commit.
- The description must complete the sentence _"If applied, this commit will…"_
- No period at the end of the title.
- Body (optional): explain _why_, not _what_. The diff shows what.

---

## Branch Naming Convention

```
<type>/<short-slug>
```

```bash
feat/darwin-core-plugin
fix/yaml-validator-empty-rules
refactor/mapping-engine-coverage-scoring
docs/update-agents-guide
chore/bump-openai-client
```

Always branch from `main`. Never commit directly to `main`.

---

## Issue Title Convention

```
[type] Short description of the problem or feature
```

```
[bug] Plugin not loading when FORMAT_ID contains uppercase letters
[feature] Add RO-Crate JSON-LD format plugin
[refactor] Split MappingEngine into smaller services
[docs] Document YAML mapping schema fields
[chore] Add pre-commit hook for ruff and tsc
```

---

## Code Style Rules

### Python (backend)

- Python 3.12+ only. Use modern syntax: `X | Y` union types, `match`, `TypeAlias`.
- All public functions must have a docstring explaining _what_ and _why_, not _how_.
- Type-annotate every function signature — inputs and return type.
- Use `pathlib.Path` for all file paths, never `os.path`.
- Raise `HTTPException` only in `main.py`. Raise plain `ValueError` / `RuntimeError` in engine/plugins.
- Do not use `print()` for debugging — use `import logging; logger = logging.getLogger(__name__)`.
- Format with `ruff format`, lint with `ruff check` before committing.

```bash
cd backend && uv run ruff check . && uv run ruff format .
```

### TypeScript (frontend)

- No `any`. Use proper types or `unknown` with a type guard.
- All API response types must be defined in `src/api/client.ts` and imported — never inlined.
- Components must have a typed `Props` interface defined above the component function.
- Use `const` by default. Use `let` only when reassignment is necessary.
- Async state: always use TanStack Query (`useQuery` / `useMutation`) — never raw `useState` + `useEffect` for API data.
- Run typecheck before committing: `npm run typecheck`.

---

## How to Add a New Feature

1. **Define the API contract first.** Add the endpoint to `main.py` (even as a stub returning `{}`) and the TypeScript interface to `client.ts`.
2. **Implement backend logic** in the appropriate layer (`mapping_engine.py`, a new plugin, or `ai_client.py`). Do not put business logic in `main.py`.
3. **Write the API call** in `client.ts`.
4. **Build the UI component.** Keep components focused — one responsibility per file.
5. **Test the full flow** end-to-end: upload a real file, verify the output.
6. **Commit** following the convention above.

## How to Fix a Bug

1. **Reproduce it first.** Identify the exact input that triggers the bug.
2. **Locate the layer.** Is it in format detection? Mapping? Conversion? AI call? Isolate before touching code.
3. **Fix the root cause**, not the symptom. Do not add `try/except` to hide a bug.
4. **Add a note in the commit body** explaining what caused it and how the fix addresses it.

## How to Refactor

1. **No behaviour change.** A refactor must not change any API response, UI output, or log message.
2. **One thing at a time.** Rename OR restructure OR extract — not all three in one commit.
3. **Run typecheck and linting** after every refactor to confirm nothing broke silently.
4. **Use `refactor` commit type** so the change is easy to skip when bisecting bugs.

---

## What Agents Must NOT Do

- ❌ Do not add new dependencies without checking the existing stack first.
- ❌ Do not modify `pivot_registry.yaml` as part of a code refactor — pivots are data, not code.
- ❌ Do not put AI logic in `main.py` or format logic in `mapping_engine.py`.
- ❌ Do not use `any` in TypeScript.
- ❌ Do not catch exceptions silently without at least logging them.
- ❌ Do not hardcode model names — they come from environment variables.
- ❌ Do not commit `.env` files. Ever.
- ❌ Do not remove the AI fallback pattern (graceful degradation).
- ❌ Do not call `ai_client.py` functions directly from `main.py` — always go through `MappingEngine`.

---

## Environment Variables

| Variable              | Default                               | Purpose                                |
| --------------------- | ------------------------------------- | -------------------------------------- |
| `OPENAI_API_KEY`      | —                                     | GWDG Academic Cloud API key (required) |
| `OPENAI_BASE_URL`     | `https://chat-ai.academiccloud.de/v1` | OpenAI-compatible endpoint             |
| `OPENAI_MODEL`        | `meta-llama-3.1-8b-instruct`          | Model for AI calls                     |
| `PIVOT_REGISTRY_PATH` | `/app/pivot_registry.yaml`            | Path to pivot registry                 |
| `LOG_LEVEL`           | `info`                                | Logging verbosity                      |

---

## File Detection Logic

| Extension | Detected format   | Note                                                         |
| --------- | ----------------- | ------------------------------------------------------------ |
| `.json`   | `isa_json`        | Switches to `ro_crate` if content has `@type` and `ro-crate` |
| `.xml`    | `datacite_xml`    |                                                              |
| `.csv`    | `darwin_core_csv` |                                                              |
| `.xlsx`   | `miappe_xlsx`     |                                                              |

Fallback: `isa_json`. Detection logic lives in `main.py → detect_format()`.

---

## Common Issues

| Problem                      | Cause                                                                 | Fix                                                                                 |
| ---------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Plugin not loading           | `FORMAT_ID` not defined at module level                               | Add `FORMAT_ID = "my_format"` as a module-level variable                            |
| Mapping not applied          | File not in `backend/mappings/` or wrong `source_format`/`pivot` keys | Check YAML keys match registry and plugin `FORMAT_ID`                               |
| Format detected wrongly      | Extension mismatch or ambiguous JSON content                          | Override via `source_format` query param in API call                                |
| Missing fields not shown     | Pivot `required_fields` list empty                                    | Add fields to pivot entry in `pivot_registry.yaml`                                  |
| CORS error in dev            | Frontend not on port 5173                                             | Vite must run on 5173; proxy is configured for that port only                       |
| TypeScript error on build    | Missing type in `client.ts`                                           | Add the interface before using it in a component                                    |
| `uv sync` fails              | Python < 3.12                                                         | Check `python --version`; install 3.12+ via `uv python install 3.12`                |
| `pyproject.toml` build error | Missing `[tool.hatch.build.targets.wheel]` packages config            | Ensure `packages = ["backend"]` is defined                                          |
| AI call returns garbled YAML | Model not following instructions                                      | Lower `temperature` (use 0.1 for mapping gen); strip markdown fences before parsing |

---

## Python Environment Reference

```bash
cd backend
uv sync                          # install all deps from pyproject.toml
uv run uvicorn main:app --reload # run dev server
uv run ruff check .              # lint
uv run ruff format .             # format
uv pip install -e .              # editable install if needed
```

Python 3.12+ is required. The codebase uses `str | None` union syntax, `match` statements,
and `typing.TypeAlias` — none of which work on 3.11 or below.
