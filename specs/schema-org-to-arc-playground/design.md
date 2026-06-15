# Design

## Files Created/Modified

- `frontend/src/App.tsx` — Remove harvest mode, ARC mode toggle. Single upload flow.
- `frontend/src/components/PivotSelector.tsx` — Rename to `TemplateSelector.tsx`. Show only FAIRagro ARC templates.
- `frontend/src/components/ComparisonView.tsx` — Add mandatory/recommended fields sections, confidence scores.
- `frontend/src/components/MappingEditor.tsx` — Replace placeholder with YAML editor + live preview.
- `frontend/src/api/client.ts` — Remove harvest functions, add `getSourceFormats()`, `getTemplateFields()`.
- `backend/main.py` — Remove OAI-PMH endpoints. Add `GET /source-formats/schema-org`, `GET /template-fields/<template_id>`.
- `backend/mapping_engine.py` — No changes needed.

## New Functions/Methods

### Backend
- `get_source_formats()` — Return schema.org field definitions with descriptions
- `get_template_fields(template_id: str)` — Return FAIRagro template field structure (mandatory vs recommended)
- `_auto_select_template(parsed_data: dict)` — Already exists in main.py, use for template selection

### Frontend  
- `getTemplateRecommendation(file: File)` — Call backend for template recommendation
- `getSourceFields(templateId: string)` — Load and display source fields for template
- `livePreview()` — Real-time ARC preview when YAML changes

## Alternative Rejected

### Option 1: Keep full application complexity
**Rejected because:**
- User wants "small features, not all functionality"
- 80% of current code is for OAI-PMH harvesting and chain conversion
- Would overwhelm users trying to learn the full platform

**Alternative considered:** Keep all modes (upload, harvest, arc) with reduced complexity

### Option 2: Use existing mapping_editor.tsx as-is
**Rejected because:**
- MappingEditor.tsx is just a placeholder showing YAML editor "coming in hackathon week"
- Need to build actual YAML editing with live preview
- Current design doesn't support the rich features required

### Option 3: Use existing pivot_selector.tsx as template selector
**Rejected because:**
- PivotSelector.tsx is for pivot selection (Bioschemas, AgroSchemas, Schema.org, etc.)
- Need to switch to FAIRagro ARC template selection (different semantics)
- Would require major refactoring of the UI

## Integration Points

### Data Flow
1. **User uploads schema.org JSON** → Schema.org plugin → flat field extraction
2. **User selects FAIRagro template** → backend template recommendation → template metadata
3. **Auto-mapping** → Mapping engine conversion → JSON-LD output
4. **Live preview** → RO-Crate plugin → ARC structure
5. **Manual editing** → YAML parsing → re-conversion → preview update
6. **Export** → RO-Crate plugin → download JSON

### API Contract
```
POST /convert → { output, field_rules, missing_fields, confidence }
POST /convert/arc-export → { preview, validation, filename }
GET /source-formats/schema-org → { fields: FieldDef[] }
GET /template-fields/<id> → { template, fields: FieldGroup[] }
```

## Error Handling

- **Schema.org parsing errors:** Show file format guidelines
- **Template validation errors:** Highlight invalid YAML with line numbers
- **ARC generation errors:** Show template-specific validation errors
- **Network errors:** Retry with exponential backoff
- **File size limits:** Show progress indicator with estimated time

## Performance Considerations

- **Live preview:** Throttle updates to 500ms debounce
- **Large files:** Show file size estimate before processing
- **YAML parsing:** Use efficient parser, avoid re-parsing on every keystroke
- **ARC generation:** Cache last template for faster switching

## Learning Mode

### Why EARS pattern?
- Event-based patterns (WHEN...MUST) capture user interactions naturally
- State-based patterns (WHILE...MUST) reflect continuous user workflows
- Disjunct patterns (IF...THEN...MUST) handle error conditions clearly
- Ubiquitous patterns (The system MUST...) express system capabilities

### Why these design decisions?
- Focused API: Single purpose endpoints for simple mental model
- Reuse existing patterns: Leverage existing mapping engine and plugin architecture
- Progressive enhancement: Start simple, add complexity as needed
- Separation of concerns: Keep frontend and backend responsibilities clear

### Why this task order?
- Backend first: API contract and template system must exist before UI
- Core conversion: Must work before adding manual editing
- Fields visualization: Requires understanding field structure
- Template support: Needed for all other features
- Export functionality: Required for user value proposition

## Validation

### Existing Tests to Reuse
- `test_arc_export.py` — ARC export functionality
- `test_arc_template.py` — Template validation
- `test_conversion.py` — Conversion logic

### New Tests Required
- Template selection tests
- Manual mapping tests
- Live preview tests
- Export validation tests

### Test Traceability
- All new tests must map to at least one R<n> requirement
- Existing tests remain valid for existing pivots
- New tests follow same naming pattern as existing tests