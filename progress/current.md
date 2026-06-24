# Progress — Current session

## Feature

create-arc-scaffold-from-rocrate

## Plan

- [x] Backend scaffold builder (RO-Crate → arctrl ARC)
- [x] POST /arc/scaffold endpoint returning ZIP
- [x] Frontend API function createArcScaffold()
- [x] ArcScaffoldCreator UI component
- [x] Integration into App.tsx
- [x] Backend tests (8 passing)
- [x] Frontend component tests (3 passing)
- [x] Ruff check/format clean
- [x] Frontend typecheck clean
- [x] init.sh passes

## Notes

- arctrl `ARC.Write()` internally calls `asyncio.run()`, so endpoint wraps builder in `asyncio.to_thread()` to avoid event-loop conflict inside FastAPI.
- Mapping coverage: Investigation, Study, Assay, Person (creator/author/contact/contributor), ontology annotations for measurement/technology.
- ZIP is generated in-memory and streamed as `application/zip` download.
- Identifier sanitization extracts the last path segment from URLs/paths and removes characters forbidden by ARC tooling, producing clean folder and XLSX identifiers (e.g. `wheat-drought-001`).
- ZIP decompression now yields a single flat folder (e.g. `wheat-drought-001/isa.investigation.xlsx`) instead of nested directories.

## Files touched

- `backend/arc_scaffold_builder.py` (new)
- `backend/main.py`
- `backend/tests/test_arc_scaffold_builder.py` (new)
- `frontend/src/api/client.ts`
- `frontend/src/components/ArcScaffoldCreator.tsx` (new)
- `frontend/tests/components/ArcScaffoldCreator.test.tsx` (new)
- `frontend/src/App.tsx`
- `specs/create-arc-scaffold-from-rocrate/requirements.md` (new)
- `specs/create-arc-scaffold-from-rocrate/design.md` (new)
- `specs/create-arc-scaffold-from-rocrate/tasks.md` (new)
- `feature_list.json`

## Blockers

- Pre-existing `test_ro_crate_miappe_integration.py` failures due to missing sample files (`arc-ro-crate-benjamin.json`, `arc-ro-crate-metadata-matthiasL.json`). Not introduced by this feature; new tests pass.

## Next steps

- Human review and approval to mark feature `done` in `feature_list.json`.
