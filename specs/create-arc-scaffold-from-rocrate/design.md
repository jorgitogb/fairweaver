# Design: Create ARC Scaffold from RO-Crate

## Components

| Component | File | Responsibility |
|-----------|------|----------------|
| Scaffold Builder | `backend/arc_scaffold_builder.py` | Parse RO-Crate `@graph`, map entities to arctrl objects, write scaffold |
| HTTP Endpoint | `backend/main.py` | Expose `POST /arc/scaffold`, package ZIP, return download |
| API Client | `frontend/src/api/client.ts` | `createArcScaffold(file)` returns Blob |
| UI Component | `frontend/src/components/ArcScaffoldCreator.tsx` | Upload / download button for scaffold ZIP |
| App Integration | `frontend/src/App.tsx` | Render component when RO-Crate result is available |
| Tests | `backend/tests/test_arc_scaffold_builder.py` | Unit tests for builder logic |

## Data Flow

```
RO-Crate JSON file
  → POST /arc/scaffold
    → ro_crate_plugin.load() extracts entities
    → arc_scaffold_builder.build_scaffold_from_rocrate()
      → Build ArcInvestigation
      → Add ArcStudy per Study entity
      → Add ArcAssay per Assay entity
      → Map Person entities to contacts
      → ARC.Write(temp_dir)
    → shutil.make_archive() creates ZIP
  → Response: application/zip
```

## RO-Crate → arctrl Mapping

| RO-Crate Entity | arctrl Object | Mapped Fields |
|-----------------|---------------|---------------|
| Investigation | `ArcInvestigation` | identifier, title, description, contacts, publications |
| Study | `ArcStudy` | identifier, title, description, contacts |
| Assay | `ArcAssay` | identifier, title, measurementType, technologyType |
| Person | `Person` | first_name, last_name, email, orcid, affiliation |

## API Contract

### Request

```http
POST /arc/scaffold
Content-Type: multipart/form-data

file=<RO-Crate JSON>
```

### Success Response

```http
200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename="<investigation-id>_scaffold.zip"
```

### Error Responses

| Status | Condition |
|--------|-----------|
| 400 | Invalid JSON or missing `@graph` |
| 400 | No Investigation entity found |
| 500 | arctrl write and fallback both fail |

## Error Handling

- All arctrl calls wrapped in `try/except`
- Logger emits warnings for missing optional fields
- Deterministic fallback creates Investigation-only scaffold if full mapping fails

## Performance

- Use `tempfile.TemporaryDirectory()` for scaffold output
- ZIP created with `shutil.make_archive()`
- Temp directory cleaned up automatically on response completion

## Dependencies

- `arctrl>=3.0.5` (already declared in `pyproject.toml`)
- `shutil`, `tempfile`, `zipfile` (stdlib)
- No new external dependencies
