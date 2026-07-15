# Progress — Current session

## Task

Generate a complete, DataHub-ready ARC scaffold from demo RO-Crate data using arctrl for maximum compatibility.

## Plan

- [x] Enhance `arc_scaffold_builder.py` to leverage more arctrl features
  - [x] Study design descriptors → `ArcStudy.StudyDesignDescriptors`
  - [x] Study personnel → `ArcStudy.Contacts`
  - [x] Investigation publications → `ArcInvestigation.Publications`
  - [x] Ontology source references (NCBITaxon) → `ArcInvestigation.OntologySourceReferences`
- [x] Add tests for new arctrl mappings (TDD)
- [x] Create `backend/generate_datahub_scaffold.py` utility
- [x] Generate scaffold from `sample-data/demo/arc-ro-crate-wheat-full.json`
- [x] Add placeholder TIFF data files in assay dataset folder
- [x] Add LICENSE file (CC-BY-4.0)
- [x] Copy source RO-Crate alongside scaffold
- [x] Verify scaffold loads cleanly with `ARC.load()`
- [x] Run ruff check/format
- [x] Run scaffold tests (19 passing)

## Notes

- Generated scaffold: `sample-data/demo/arc-scaffold-wheat-drought/`
- ARC identifier: `wheat-drought-001`
- Structure: Investigation + Study (`Study_wheat`) + Assay (`Assay_wheat`) + 2 contacts + 1 publication + NCBITaxon ontology source.
- Placeholder TIFFs (8-byte header) placed in `assays/Assay_wheat/dataset/` to match arctrl folder naming.
- Full backend test suite has pre-existing failures in `test_ro_crate_miappe_integration.py` due to missing sample files; not introduced by this change.

## Files touched

- `backend/arc_scaffold_builder.py` — enhanced arctrl mappings
- `backend/tests/test_arc_scaffold_builder.py` — new tests
- `backend/generate_datahub_scaffold.py` — new generator script
- `sample-data/demo/arc-scaffold-wheat-drought/` — generated scaffold artifact

## Next steps

- User will review scaffold and push to GitLab DataHub.
