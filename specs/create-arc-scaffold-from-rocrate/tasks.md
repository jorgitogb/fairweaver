# Tasks: Create ARC Scaffold from RO-Crate

## T1 — Scaffold builder skeleton
Create `backend/arc_scaffold_builder.py` with `build_scaffold_from_rocrate()` function signature and docstring.

## T2 — Investigation-only mapping
Implement extraction of Investigation entity from `@graph` and creation of `ArcInvestigation` via arctrl.

## T3 — Test Investigation-only scaffold
Write failing test for Investigation-only RO-Crate, then make it pass.

## T4 — Verify directory structure
Ensure scaffold root contains `isa.investigation.xlsx`, `studies/`, `assays/`, `workflows/`, `runs/`.

## T5 — Study mapping
Extract Study entities and add them to the Investigation with `InitStudy()`.

## T6 — Test Study mapping
Write failing test for RO-Crate with Investigation + Study, then make it pass.

## T7 — Assay mapping
Extract Assay entities and register them under the correct Study.

## T8 — Test Assay mapping
Write failing test for Investigation + Study + Assay, then make it pass.

## T9 — Person/Contact mapping
Map Person entities to arctrl `Person` objects and attach to Investigation/Study.

## T10 — Test Person mapping
Write failing test verifying contacts appear in generated scaffold.

## T11 — ZIP packaging helper
Add `_package_scaffold(scaffold_dir)` returning ZIP bytes.

## T12 — Test ZIP packaging
Write failing test verifying ZIP contains expected files, then make it pass.

## T13 — `POST /arc/scaffold` endpoint
Add endpoint to `main.py` that accepts file, calls builder, returns ZIP download.

## T14 — Endpoint error handling
Implement 400 responses for invalid JSON, missing `@graph`, and missing Investigation.

## T15 — Endpoint integration test
Write integration test for `POST /arc/scaffold`.

## T16 — Frontend API function
Add `createArcScaffold(file)` to `frontend/src/api/client.ts`.

## T17 — `ArcScaffoldCreator` component
Create `frontend/src/components/ArcScaffoldCreator.tsx` with upload/download UI.

## T18 — Component test
Write Vitest test for `ArcScaffoldCreator`.

## T19 — Integrate into App.tsx
Render `ArcScaffoldCreator` when ARC result is available.

## T20 — Validation
Run `ruff check`, `ruff format`, frontend typecheck, and full test suite.
