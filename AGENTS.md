# FAIRweaver Agent Guide

## Quick Commands

```bash
# Backend (using uv)
cd backend && uv sync && uv run uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker full stack
cp .env.example .env && docker compose up
```

## Architecture

- **Monorepo**: `backend/` (FastAPI) + `frontend/` (React/Vite)
- **Entry points**: `backend/main.py`, `frontend/src/Main.tsx`
- **API port**: 8000 | **Frontend port**: 5173

## Plugin System (Critical)

- Location: `backend/plugins/formats/`
- Must define `FORMAT_ID` variable
- Pattern: `*_plugin.py`
- Auto-loaded on startup via `plugins/loader.py`

## Pivot Registry

- File: `backend/pivot_registry.yaml`
- Defines required/recommended fields per pivot
- Examples: `bioschemas_dataset`, `agrischemas_fieldtrial`, `schemaorg_generic`

## Mapping Files

- Location: `backend/mappings/`
- Format: YAML with `field_rules` array
- Each rule: source, target, required, confidence, transform

## File Detection

| Extension | Format |
|----------|-------|
| .json | isa_json (or ro_crate if content has @type) |
| .xml | datacite_xml |
| .csv | darwin_core_csv |
| .xlsx | miappe_xlsx |

Fallback: `isa_json`

## API Endpoints

- `GET /pivots` - List pivots
- `POST /pivots/recommend` - Recommend pivot for file
- `GET /mappings` - List mappings
- `POST /mappings/generate` - Generate mapping
- `POST /mappings/validate` - Validate mapping
- `POST /convert` - Convert to pivot
- `POST /convert/chain` - Source → pivot → target

## Common Issues

1. **Plugin not loading**: Check `FORMAT_ID` is defined
2. **Mapping not found**: Ensure file exists in `backend/mappings/`
3. **Format detection wrong**: Verify file extension matches content
4. **Missing fields**: Check pivot's required_fields in registry
5. **CORS error**: Frontend must be on localhost:5173
6. **Build errors**: Use `uv pip install -e .` in venv; requires Python 3.12+
7. **pyproject.toml issues**: Uses hatchling; ensure packages defined in `[tool.hatch.build.targets.wheel]`

## Python Environment

- **Backend requires**: Python 3.12+ (uses `typing.TypeAlias` syntax)
- **Package manager**: uv (not pip)
- **Setup**: `cd backend && uv sync && uv run uvicorn main:app --reload`
- **Editable install**: `uv pip install -e .` for development
- **pyproject.toml**: Modern Python packaging config with hatchling build backend
