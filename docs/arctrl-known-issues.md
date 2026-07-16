# arctrl Known Issues — XLSX to RO-Crate Conversion

This document tracks bugs in arctrl where data is correctly written to XLSX files
but lost or corrupted when DataHub/arctrl generates RO-Crate from those files.

**Premise**: The XLSX files are created by FAIRweaver using arctrl lib and contain
correct data per ISA-XLSX specification.

---

## Issue 1: datePublished Always Overwritten with Current Timestamp

**Status**: arctrl bug (not fixed)

**XLSX data** (correct):
```
Investigation Public Release Date    2024-09-15
```

**RO-Crate output** (wrong):
```json
{
  "@id": "./",
  "datePublished": "2026-07-16T11:25:26.0744769"
}
```

**Root cause**: `arctrl/py/Conversion/date_time.py` → `try_from_string()` always
returns `None` because the Thoth.Json decoder expects a JSON-encoded string
(wrapped in quotes) but receives a bare string. The fallback `default_arg(None, now())`
then uses the current timestamp.

**Code path**:
```python
# arctrl/py/Conversion/investigation.py line 52
date_published: Any = default_arg(bind(_arrow4477, investigation.PublicReleaseDate), now())
```

**Impact**: The original `datePublished` from the input is lost in every round-trip.

**Workaround**: Post-process the RO-Crate JSON after arctrl generates it, replacing
`datePublished` with the value from `arc.PublicReleaseDate` (which IS correctly
preserved in the XLSX read).

---

## Issue 2: License Defaults to "ALL RIGHTS RESERVED BY THE AUTHORS"

**Status**: arctrl behavior (ISA spec limitation)

**XLSX data**: N/A — ISA-XLSX specification has no license field in the INVESTIGATION
section.

**RO-Crate output** (wrong):
```json
{
  "@id": "#LICENSE",
  "@type": "CreativeWork",
  "text": "ALL RIGHTS RESERVED BY THE AUTHORS"
}
```

**Root cause**: arctrl stores license in a separate `LICENSE` plaintext file in the
ARC root directory, not in the XLSX. If no `LICENSE` file exists, arctrl uses the
default string per ISA-RO-Crate profile.

**ARC specification reference**:
> If a license of choice shall apply to an ARC, the license information MUST be
> included in the root of the ARC in a plaintext file named `LICENSE`.

**Impact**: License URL (e.g., `https://creativecommons.org/licenses/by/4.0/`) is
lost in round-trip.

**Workaround**: FAIRweaver's `arc_scaffold_builder.py` should write a `LICENSE` file
to the scaffold root directory containing the license URL/text from the input RO-Crate.

---

## Issue 3: Publication Authors Treated as Single Person Entity

**Status**: arctrl behavior

**XLSX data** (correct):
```
Investigation Publication Author List    Mühlhaus T; Schmidhalter U
```

**RO-Crate output** (wrong):
```json
{
  "@id": "#Person_Mühlhaus_T;_Schmidhalter_U",
  "@type": "Person",
  "givenName": "Mühlhaus T; Schmidhalter U"
}
```

**Root cause**: arctrl's RO-Crate generation treats the author list string as a
single Person's `givenName` instead of creating separate Person entities or using
the `authorList` property on the ScholarlyArticle.

**Impact**: Author information is semantically incorrect in the RO-Crate.

**Workaround**: Post-process the RO-Crate JSON to create proper Person entities
and link them to the ScholarlyArticle via `author` property.

---

## Issue 4: Publisher Comment Contains Internal ID

**Status**: FAIRweaver scaffold builder bug (not arctrl)

**XLSX data** (correct):
```
Comment[Investigation Publisher]    #Publisher_RPTU_University_of_Kaiserslautern,_Plant_Phenomics_Group
```

**RO-Crate output** (wrong):
```json
{
  "@id": "#LDComment_Investigation_Publisher_#Publisher_RPTU_University_of_Kaiserslautern,_Plant_Phenomics_Group",
  "text": "#Publisher_RPTU_University_of_Kaiserslautern,_Plant_Phenomics_Group"
}
```

**Root cause**: FAIRweaver's `_add_comment_if_exists()` stores the publisher entity
reference ID instead of extracting the actual publisher name.

**Impact**: Comment value contains internal ID instead of human-readable name.

**Workaround**: Fix `_add_comment_if_exists()` to resolve entity references and
extract the `name` property before storing as Comment value.

---

## Issue 5: Investigation-Level Fields Only in Comments

**Status**: arctrl limitation (ISA spec compliant)

**Fields affected**:
- `keywords` → `Comment[Investigation Keywords]`
- `funder` → `Comment[Investigation Funding Agency]`
- `publisher` → `Comment[Investigation Publisher]`
- `alternateName` → `Comment[Investigation Alternative Title]`
- `url` → `Comment[Investigation URL]`
- `version` → `Comment[Investigation Version]`
- `inLanguage` → `Comment[Investigation Language]`

**Root cause**: arctrl's `ArcInvestigation` class has no native properties for these
fields. They can only be stored as Comments in the XLSX, which is valid per ISA
specification.

**Impact**: These fields are not present on the Investigation entity in the RO-Crate
output (only in Comments).

**Workaround**: Post-process the RO-Crate JSON to add these fields to the
Investigation entity from the Comment values.

---

## Summary Table

| Issue | Type | XLSX Correct? | RO-Crate Correct? | Workaround |
|-------|------|---------------|-------------------|------------|
| datePublished | arctrl bug | ✅ Yes | ❌ No | Post-process |
| license | arctrl limitation | N/A | ❌ No | Write LICENSE file |
| Publication authors | arctrl behavior | ✅ Yes | ❌ No | Post-process |
| Publisher Comment value | FAIRweaver bug | ✅ Yes | ❌ No | Fix scaffold builder |
| Investigation fields | arctrl limitation | ✅ Yes (in Comments) | ❌ No (only in Comments) | Post-process |

---

## Recommended Fix Strategy

For FAIRweaver to produce correct RO-Crate output from XLSX files generated by arctrl:

1. **Fix scaffold builder bugs** (Publisher Comment value, missing entities)
2. **Write LICENSE file** to scaffold root directory
3. **Post-process RO-Crate** after arctrl generates it:
   - Restore `datePublished` from `arc.PublicReleaseDate`
   - Restore `license` from input or LICENSE file
   - Create proper Person entities for publication authors
   - Add Investigation-level fields from Comments

---

## Files Referenced

- `arctrl/py/Conversion/date_time.py` — buggy `try_from_string()`
- `arctrl/py/Conversion/investigation.py` — `composeInvestigation()` with fallback
- `arctrl/py/Spreadsheet/arc_investigation.py` — XLSX read/write
- `backend/arc_scaffold_builder.py` — FAIRweaver scaffold builder
- `backend/formats/schema_org_arc_plugin.py` — has post-processing workaround
- `docs/arctrl-roundtrip-analysis.md` — prior round-trip analysis
