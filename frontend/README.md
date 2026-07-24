# FAIRagro-MI — Frontend

React + Vite + TypeScript UI for the FAIRagro metadata inspector.

## Quick Start

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm test         # run tests
npm run typecheck # TypeScript check
```

## Scripts

| Script | Command |
|--------|---------|
| `dev` | `vite` — development server |
| `build` | `vite build` — production build |
| `test` | `vitest run` — run tests once |
| `typecheck` | `tsc --noEmit` — TypeScript validation |
| `lint` | `eslint .` — lint check |

## Components

| Component | Purpose |
|-----------|---------|
| `UploadZone.tsx` | File drag-and-drop upload |
| `ArcCrateView.tsx` | ARC RO-Crate preview (ARC / JSON-LD / Validation tabs) |
| `ArcScaffoldCreator.tsx` | Generate ARC scaffold ZIP from RO-Crate |
| `ComplianceBadge.tsx` | FAIRagro compliance level indicator |
| `ArcEntityTree.tsx` | Entity tree view for ARC structure |
| `ArcHierarchyTree.tsx` | Hierarchical tree for ARC elements |
| `MiappeExtractionTree.tsx` | MIAPPE field extraction display |
| `JsonHighlight.tsx` | Syntax-highlighted JSON viewer |

## API Client

All backend calls are in `src/api/client.ts`.
