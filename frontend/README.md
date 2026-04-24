# FAIR Weaver

Data transformation platform for FAIR (Findable, Accessible, Interoperable, Reusable) metadata.

## Tech Stack

- **Frontend**: React + Vite + TypeScript
- **Backend**: FastAPI (Python 3.12+)

## Quick Start

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && uv sync && uv run uvicorn main:app --reload

# Docker (full stack)
docker compose up
```

## Project Structure

```
frontend/
├── src/
│   ├── components/    # React components
│   │   ├── MappingEditor.tsx
│   │   ├── PivotSelector.tsx
│   │   ├── SuggestionPanel.tsx
│   │   └── UploadZone.tsx
│   ├── App.tsx
│   └── main.tsx
└── index.html

backend/
├── main.py           # FastAPI entry
├── plugins/          # Format plugins
├── mappings/         # Field mappings
└── pivot_registry.yaml
```

## API Endpoints

- `GET /pivots` - List pivots
- `POST /pivots/recommend` - Recommend pivot for file
- `POST /convert` - Convert to pivot
- `POST /convert/chain` - Source → pivot → target