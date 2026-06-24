# Requirements: Create ARC Scaffold from RO-Crate

## R1
WHEN the user uploads an ARC RO-Crate JSON-LD file, the system MUST accept it via a dedicated endpoint and parse its `@graph` entities.

## R2
WHEN the parsed RO-Crate contains at least one Investigation entity, the system MUST generate a full ARC scaffold directory using the arctrl library.

## R3
WHEN the system generates an ARC scaffold, it MUST create the directory structure `studies/`, `assays/`, `workflows/`, `runs/` alongside `isa.investigation.xlsx` at the scaffold root.

## R4
WHEN the RO-Crate contains Study entities, the system MUST create one subdirectory under `studies/` per study containing `isa.study.xlsx`, `resources/`, and `protocols/`.

## R5
WHEN the RO-Crate contains Assay entities, the system MUST create one subdirectory under `assays/` per assay containing `isa.assay.xlsx`, `dataset/`, and `protocols/`.

## R6
WHEN the RO-Crate contains Person entities linked to the Investigation or Studies, the system MUST map them to arctrl `Person` objects and include them in the generated XLSX metadata.

## R7
WHEN the scaffold is generated, the system MUST package the directory tree into a ZIP file and return it as a downloadable response.

## R8
IF the uploaded file is not valid JSON or has no `@graph`, the system MUST respond with HTTP 400 and a clear error message.

## R9
IF the RO-Crate `@graph` contains no Investigation entity, the system MUST respond with HTTP 400 and a clear error message.

## R10
IF arctrl fails to write the scaffold, the system MUST log the error and attempt a deterministic fallback before raising HTTP 500.

---

## Traceability

- R1 → T1, T13
- R2 → T2, T3
- R3 → T4
- R4 → T5, T6
- R5 → T7, T8
- R6 → T9, T10
- R7 → T11, T13
- R8 → T14
- R9 → T14
- R10 → T15
