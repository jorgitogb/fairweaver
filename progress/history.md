# Progress — History

> Append-only log of completed sessions. Newest entry at the bottom.

---

(No sessions recorded yet.)

---

## Session 2 — 2026-06-15: Completed schema-org-to-arc-playground implementation

**Feature:** `schema-org-to-arc-playground`

**Accomplished:**

- Fixed 47 test failures → all 80 tests green
- Fixed Form() bool param parsing for preview/batch in /convert/arc-export
- Fixed ro_crate_write to strip @context and add @id/additionalType for JSON-LD input
- Fixed main.py to pass converted["json_ld"] to ro_crate_write
- Rewrote schema_org-arc_ro_crate.yaml mapping to target flat ARC Investigation fields
- Updated 5 test files to match actual endpoint behavior
- Marked feature done in feature_list.json

**Key learnings:**

- FastAPI Form() required for bool params from multipart data
- Entity @id=#investigation, additionalType=Investigation in ARC RO-Crate
- detect_format catches JSONDecodeError silently, falls back to isa_json
- schema_org → MappingEngine → ro_crate_write pipeline requires flat field targets
