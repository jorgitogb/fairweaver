# Requirements

## R1
WHEN the user uploads a schema.org JSON-LD file and selects a FAIRagro ARC template, the system MUST convert the input metadata to ARC RO-Crate format with template-based field mapping.

## R2
WHILE the user is editing custom mappings in the YAML editor, the system MUST show a live preview of the ARC RO-Crate output that updates in real-time.

## R3
WHEN the user clicks "Export ARC RO-Crate", the system MUST download a valid ARC RO-Crate JSON file that conforms to the selected FAIRagro template.

## R4
WHEN the system processes an input file, it MUST show which mandatory fields are mapped, which are missing, and which are recommended fields.

## R5
WHILE the user is viewing the mapping interface, the system MUST display all 4 FAIRagro templates (searchhub, plant_phenotyping, genomics, sensor) with auto-selection based on content.

## R6
IF the user wants to save a custom mapping profile, the system MUST allow them to download it as a YAML file and later import it back.

## R7
WHEN the system detects unsupported input formats, it MUST show an error message with supported formats.

## R8
WHILE the user is comparing source and target fields, the system MUST display confidence scores for each mapped field.

## R9
IF the user manually corrects a mapping, the system MUST validate that the resulting ARC structure is syntactically correct.

## R10
WHEN the system generates an ARC RO-Crate, it MUST include all mandatory entities (Investigation, Study, Assay) for the selected template.

## R11
IF the input metadata has errors, the system MUST show validation errors before attempting conversion.

## R12
WHEN the user views the template selector, the system MUST show brief descriptions of each FAIRagro template's purpose.

## R13
WHILE the user is working with the mapping editor, the system MUST allow them to switch between different FAIRagro templates and see updated mappings.

## R14
IF the user uploads an invalid schema.org file, the system MUST show parsing errors with file format guidelines.

## R15
WHEN the user exports to ARC format, the system MUST generate a filename that includes the template name and timestamp.

## R16
IF the user wants to test their mappings, the system MUST provide a "Validate Only" mode that checks field mappings without generating a complete ARC RO-Crate.

## R17
WHILE the user is viewing conversion results, the system MUST display a summary of all mappings with source→target pairs.

## R18
IF the user wants to compare two different input files, the system MUST allow them to upload both and show side-by-side mapping differences.

## R19
WHEN the user accesses the playground, the system MUST show a welcome screen with example files and quick start instructions.

## R20
IF the system encounters an error during conversion, it MUST log the error and show a user-friendly error message with recovery options.

---

## Traceability

- R1 → T1
- R2 → T2
- R3 → T3
- R4 → T4
- R5 → T5
- R6 → T6
- R7 → T7
- R8 → T8
- R9 → T9
- R10 → T10
- R11 → T11
- R12 → T12
- R13 → T13
- R14 → T14
- R15 → T15
- R16 → T16
- R17 → T17
- R18 → T18
- R19 → T19
- R20 → T20