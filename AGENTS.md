# FAIRweaver — Agent Guide

This file is the authoritative reference for AI coding agents (Cursor, Copilot, Claude Code, etc.)
working on this codebase. Read it fully before making any change.

---

## Engineering Operating System

Every change follows **SDD + TDD**. No exceptions, no shortcuts.

### Operating Principles (Checklist)

- [ ] 1. Never start coding without a problem statement, expected behaviour, constraints, and acceptance criteria.
- [ ] 2. Every change begins with a specification (see `## Specification Template`).
- [ ] 3. Write a failing test first (TDD). See TDD workflow below.
- [ ] 4. Implement the minimum code to pass the test. Refactor safely.
- [ ] 5. Keep work atomic — one micro-task = one concern = one clear outcome.
- [ ] 6. Respect code size limits (see below). State override reason when exceeding.
- [ ] 7. After every change: validate (lint, typecheck, test, diff review).
- [ ] 8. If a test fails twice → try a meaningfully different approach. Fail three times → stop, explain, ask for input.
- [ ] 9. Every 3-5 steps: surface current state, risks, and next recommendation before proceeding.
- [ ] 10. When proposing solutions, present options with tradeoffs and recommend one.
- [ ] 11. Prefer simplicity, readability, testability over clever code.
- [ ] 12. Document rationale and trade-offs in commit body, not code comments.
- [ ] 13. Evaluate security, performance, and edge cases before implementation.
- [ ] 14. Preserve existing architecture, conventions, and public contracts.
- [ ] 15. Never ship an entire feature in one pass — break into milestones and micro-tasks.

### Specification-First Rule

No implementation begins without a spec. For small changes the spec is the issue/PR description;
for anything non-trivial use the template in `## Specification Template`.

### TDD Workflow

```
1. Understand the requirement → write the spec.
2. Write a failing test that defines expected behaviour.
3. Run the test — confirm it fails for the right reason.
4. Write the minimum production code to make it pass.
5. Run the test — confirm it passes.
6. Refactor if needed — run tests again.
7. Repeat for each micro-task.
```

**TDD scope by layer:**

- **Backend (plugins, mapping_engine, main):** strict TDD — test first, implement second.
- **Frontend (components, hooks):** strict TDD — unit tests (Vitest) or component tests before implementation.
- **AI layer (ai_client.py, MappingEngine.generate_mapping_ai):** TDD on the rule-based fallback path (deterministic). AI-specific code uses contract tests (input/output schema validation) plus mocked LLM responses. The existing graceful-degradation pattern is the testable surface — never remove it.

### Code Size Limits (Soft Cap)

- Max **50 lines production code** and **30 lines test code** per step, unless:
  - The change is mechanical/coordinated across files (e.g. rename across codebase), OR
  - You explicitly state the override reason and the user approves.
- When a step exceeds the cap: stop, explain what was completed, explain why, state next recommended step, wait for confirmation.

### Failure Handling Protocol

- **First failure:** analyse root cause, document it, try a different approach.
- **Second failure:** try a meaningfully different strategy (different abstraction, different layer, different technique). Document what changed.
- **Third failure:** stop implementation. Explain all three attempts and why they failed. Summarise findings. Present alternative architectural directions. Request human input before continuing.
- Never retry the same approach expecting different results.

### Context Verification Checkpoint

After every 3-5 implementation steps, pause and surface:

- **Current state:** what exists now?
- **Remaining work:** what is left?
- **Risks:** what concerns remain?
- **Recommendation:** what should be done next?

Then wait for confirmation before continuing.

### Decision Framework

When there are multiple viable approaches:

1. Present all options.
2. Explain tradeoffs for each (complexity, scalability, maintainability, risk, migration cost).
3. Recommend one approach with justification.
4. Let the user decide before proceeding.

### Anti-Big-Bang Rule

Forbidden:

- Generating full applications or features in one pass.
- Replacing large architecture sections without approval.
- Modifying many files simultaneously without incremental checkpoints.
- Solving unrelated problems in a single change.

Prefer iterative delivery. Each step should be independently verifiable.

### Refactoring Threshold

When complexity increases, stop and evaluate:

- Is duplication growing?
- Is coupling increasing?
- Are responsibilities unclear?
- Is testability getting worse?

If yes → propose refactoring before adding more functionality.

---

## Quick Commands

```bash
# Backend (Python 3.12+ required)
cd backend && uv sync && uv run uvicorn main:app --reload
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs

# Frontend (Node.js 20+)
cd frontend && npm install && npm run dev
# UI: http://localhost:5173

# Typecheck frontend without building
cd frontend && npm run typecheck

# Run tests
cd backend && python -m pytest tests/
cd frontend && npm test

# Full stack
cp .env.example .env   # set OPENAI_API_KEY
docker compose up
# Backend: http://localhost:8000  |  Frontend: http://localhost:8080
```

---

## Architecture Overview

FAIRweaver is a **monorepo** with two independent services that communicate only via REST:

```
┌─────────────────────────────────────┐
│  frontend/  (React + Vite + TS)     │  port 5173 (dev) / 8080 (prod)
│  All API calls via src/api/client.ts│
└────────────────┬────────────────────┘
                 │ HTTP/JSON
┌────────────────▼────────────────────┐
│  backend/  (FastAPI + Python 3.12)  │  port 8000
│  main.py → mapping_engine.py        │
│         → ai_client.py              │
│         → formats/*_plugin.py       │
└─────────────────────────────────────┘
```

**Rule:** Frontend never reads files directly. Backend never touches the DOM.
Any new capability must be exposed as a REST endpoint first, then consumed by the UI.

---

## Design Patterns in Use

Understanding these patterns is essential before modifying or extending the codebase.
Do not replace them with ad-hoc code — extend them.

### 1. Strategy Pattern — Format Plugins

**Where:** `backend/formats/*_plugin.py`

Each format (ISA-JSON, DataCite, Darwin Core…) is a plugin that implements the same interface:

```python
FORMAT_ID = "isa_json"          # unique identifier used in API calls
LABEL     = "ISA-JSON"          # human-readable label for the UI
EXTENSIONS = [".json"]          # for auto-detection

def load(content: bytes) -> dict:
    """Parse raw file bytes → flat dict for the mapping engine."""
    ...

def write(json_ld: dict) -> dict:
    """Convert pivot JSON-LD → this format's output structure."""
    ...
```

`plugins/loader.py` discovers all `*_plugin.py` files at startup using `importlib` — no registration
needed. Adding a new format = adding one file. Never add format logic to `main.py` or
`mapping_engine.py`.

### 2. Registry Pattern — Pivot Profiles

**Where:** `backend/pivot_registry.yaml` + `MappingEngine._load_registry()`

Pivots (Bioschemas, AgroSchemas, Schema.org…) are data, not code. They live in a YAML registry
that the engine reads at startup. To add a new pivot, edit the YAML — no Python changes needed.

```yaml
bioschemas_dataset:
  label: "Bioschemas Dataset"
  context_url: "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"
  domains: [genomics, biodiversity, general]
  required_fields: [identifier, name, description, url, keywords, license]
  recommended_fields: [creator, datePublished, publisher, version]
```

The engine scores input fields against `required_fields` + `recommended_fields` to produce
a coverage percentage. This drives both the AI recommendation and the SuggestionPanel UI.

### 3. Facade Pattern — MappingEngine

**Where:** `backend/mapping_engine.py`

`MappingEngine` is the single entry point for all conversion logic. `main.py` calls it;
`ai_client.py` is called by it. Nothing else should call `ai_client.py` directly.

```
main.py (HTTP layer)
    └── MappingEngine (domain logic)
            ├── pivot registry
            ├── YAML mapping files
            ├── format plugin dispatch
            └── ai_client (AI generation + RAG)
```

### 4. Graceful Degradation — AI Fallback

**Where:** `mapping_engine.py → generate_mapping()`

Every AI call is wrapped in `try/except`. If the GWDG API is unavailable, the engine falls back
to rule-based field matching. This ensures the platform works even without an API key.

```python
try:
    mapping = generate_mapping_ai(...)   # GWDG API
except Exception:
    mapping = self._rule_based_mapping() # deterministic fallback
```

Never remove this pattern. Never let an AI failure raise an HTTP 500.

### 5. Typed API Contract — client.ts

**Where:** `frontend/src/api/client.ts`

All TypeScript interfaces that mirror the backend's JSON responses live here. When you add a new
field to a backend response, add it to the interface in `client.ts` first, then consume it in
the component. Never use `any` for API response types.

---

## Current Work

- **Completed:** OAI-PMH harvest & convert flow for FAIRagro Search Hub
- **Completed:** ARC export system with Schema.org to ARC conversion, auto-template selection, batch processing, and validation
- **Completed:** Slot 6 architecture diagrams — Middleware federation service (RDI→Middleware→GitLab→SearchHub), RDI sources (E!DAL-PGP, Bonares, EDAPHOBASE, OpenAGRAR), Agrischemas as aspirational model, domain-specific entity mapping with coverage gaps
- **In Progress:** Frontend components integrated into main application
- **Next:** Test the frontend components with various file types and edge cases

---

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/). Every commit title must follow:

```
<type>(<scope>): <short description in imperative mood>
```

### Types

| Type       | When to use                          |
| ---------- | ------------------------------------ |
| `feat`     | New capability visible to users      |
| `fix`      | Bug fix                              |
| `refactor` | Code change with no behaviour change |
| `perf`     | Performance improvement              |
| `test`     | Adding or fixing tests               |
| `docs`     | Documentation only                   |
| `chore`    | Tooling, deps, config (no prod code) |
| `ci`       | CI/CD changes                        |

### Scope

Use the affected layer: `backend`, `frontend`, `plugin`, `pivot`, `mapping`, `docker`, `ai`

### Examples

```bash
feat(plugin): add Darwin Core CSV loader
fix(backend): handle empty field_rules in YAML mapping validator
refactor(mapping-engine): extract _score_pivot_coverage into separate method
perf(ai): cache embedding vectors in-memory to avoid redundant API calls
docs(agents): add design pattern explanations
chore(deps): bump openai to 1.52.0
feat(frontend): add confidence score badge to PivotSelector cards
fix(frontend): prevent double submit on convert button click
feat(pivot): add MIAPPE pivot profile to registry
test(plugin): add round-trip test for ISA-JSON loader and writer
```

### Rules for agents

- One logical change per commit. Do not bundle a fix and a refactor in the same commit.
- The description must complete the sentence _"If applied, this commit will…"_
- No period at the end of the title.
- Body (optional): explain _why_, not _what_. The diff shows what.

---

## Branch Naming Convention

```
<type>/<short-slug>
```

```bash
feat/darwin-core-plugin
fix/yaml-validator-empty-rules
refactor/mapping-engine-coverage-scoring
docs/update-agents-guide
chore/bump-openai-client
```

Always branch from `main`. Never commit directly to `main`.

---

## Issue Title Convention

```
[type] Short description of the problem or feature
```

```
[bug] Plugin not loading when FORMAT_ID contains uppercase letters
[feature] Add RO-Crate JSON-LD format plugin
[refactor] Split MappingEngine into smaller services
[docs] Document YAML mapping schema fields
[chore] Add pre-commit hook for ruff and tsc
```

---

## Code Style Rules

### Python (backend)

- Python 3.12+ only. Use modern syntax: `X | Y` union types, `match`, `TypeAlias`.
- All public functions must have a docstring explaining _what_ and _why_, not _how_.
- Type-annotate every function signature — inputs and return type.
- Use `pathlib.Path` for all file paths, never `os.path`.
- Raise `HTTPException` only in `main.py`. Raise plain `ValueError` / `RuntimeError` in engine/plugins.
- Do not use `print()` for debugging — use `import logging; logger = logging.getLogger(__name__)`.
- Format with `ruff format`, lint with `ruff check` before committing.

```bash
cd backend && uv run ruff check . && uv run ruff format .
```

### TypeScript (frontend)

- No `any`. Use proper types or `unknown` with a type guard.
- All API response types must be defined in `src/api/client.ts` and imported — never inlined.
- Components must have a typed `Props` interface defined above the component function.
- Use `const` by default. Use `let` only when reassignment is necessary.
- Async state: always use TanStack Query (`useQuery` / `useMutation`) — never raw `useState` + `useEffect` for API data.
- Run typecheck before committing: `npm run typecheck`.

---

## How to Add a New Feature

1. **Write a specification.** Use `## Specification Template` to define the goal, requirements, inputs/outputs, edge cases, acceptance criteria, and test strategy. For simple changes, the spec can be the issue description; for non-trivial work, write it out.
2. **Write failing tests first (TDD).** Write tests that define the expected behaviour of the new feature. Run them — they must fail for the right reasons before you write any production code.
3. **Split into micro-tasks.** Each micro-task solves one concern, touches one responsibility area, and has one clear outcome. Execute one at a time.
4. **Define the API contract.** Add the endpoint to `main.py` (even as a stub returning `{}`) and the TypeScript interface to `client.ts`.
5. **Implement backend logic** in the appropriate layer (`mapping_engine.py`, a new plugin, or `ai_client.py`). Do not put business logic in `main.py`.
6. **Write the API call** in `client.ts`.
7. **Build the UI component.** Keep components focused — one responsibility per file.
8. **Integrate into main application** by updating the main App.tsx component.
9. **Validate the full flow** end-to-end: upload a real file, verify the output. Run `ruff check`, `ruff format`, `npm run typecheck`, `npm test`.
10. **Commit** following the convention above.

## How to Fix a Bug

1. **Reproduce it first.** Identify the exact input that triggers the bug. Document it — this is your regression test.
2. **Locate the layer.** Is it in format detection? Mapping? Conversion? AI call? Isolate before touching code.
3. **Write a failing regression test** that captures the bug's expected behaviour. Run it — confirm it fails for the right reason.
4. **Fix the root cause**, not the symptom. Do not add `try/except` to hide a bug.
5. **Verify the regression test passes.** Then run the full test suite to confirm no regressions.
6. **Add a note in the commit body** explaining what caused it and how the fix addresses it.
7. **Three-strike rule:** If you fail to fix a bug twice, try a meaningfully different approach. Fail three times → stop, explain all attempts, present alternatives, request human input.

## How to Refactor

1. **No behaviour change.** A refactor must not change any API response, UI output, or log message.
2. **Behaviour preservation contract.** Before refactoring: confirm all tests pass. After refactoring: confirm the same tests still pass. A refactor that breaks tests is not a refactor.
3. **One thing at a time.** Rename OR restructure OR extract — not all three in one commit.
4. **Coverage must not decrease.** Refactoring may improve test coverage but must never remove or weaken existing tests.
5. **Run typecheck and linting** after every refactor to confirm nothing broke silently.
6. **Use `refactor` commit type** so the change is easy to skip when bisecting bugs.

---

## What Agents Must NOT Do

- ❌ Do not add new dependencies without checking the existing stack first.
- ❌ Do not modify `pivot_registry.yaml` as part of a code refactor — pivots are data, not code.
- ❌ Do not put AI logic in `main.py` or format logic in `mapping_engine.py`.
- ❌ Do not use `any` in TypeScript.
- ❌ Do not catch exceptions silently without at least logging them.
- ❌ Do not hardcode model names — they come from environment variables.
- ❌ Do not commit `.env` files. Ever.
- ❌ Do not remove the AI fallback pattern (graceful degradation).
- ❌ Do not call `ai_client.py` functions directly from `main.py` — always go through `MappingEngine`.
- ❌ Do not implement frontend components without first consulting the AGENTS.md documentation.
- ❌ Do not write production code before writing a failing test.
- ❌ Do not skip specification even for "small" changes — the spec can be a one-line issue description.
- ❌ Do not produce >50 lines of production code in one step without stating an override reason.
- ❌ Do not silently retry the same failed approach more than twice — escalate after three failures.

---

## Environment Variables

| Variable              | Default                               | Purpose                                |
| --------------------- | ------------------------------------- | -------------------------------------- |
| `OPENAI_API_KEY`      | —                                     | GWDG Academic Cloud API key (required) |
| `OPENAI_BASE_URL`     | `https://chat-ai.academiccloud.de/v1` | OpenAI-compatible endpoint             |
| `OPENAI_MODEL`        | `meta-llama-3.1-8b-instruct`          | Model for AI calls                     |
| `PIVOT_REGISTRY_PATH` | `/app/pivot_registry.yaml`            | Path to pivot registry                 |
| `LOG_LEVEL`           | `info`                                | Logging verbosity                      |

---

## File Detection Logic

| Extension | Detected format   | Note                                                         |
| --------- | ----------------- | ------------------------------------------------------------ |
| `.json`   | `isa_json`        | Switches to `ro_crate` if content has `@type` and `ro-crate` |
| `.xml`    | `datacite_xml`    |                                                              |
| `.csv`    | `darwin_core_csv` |                                                              |
| `.xlsx`   | `miappe_xlsx`     |                                                              |

Fallback: `isa_json`. Detection logic lives in `main.py → detect_format()`.

---

## Common Issues

| Problem                      | Cause                                                                 | Fix                                                                                 |
| ---------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Plugin not loading           | `FORMAT_ID` not defined at module level                               | Add `FORMAT_ID = "my_format"` as a module-level variable                            |
| Mapping not applied          | File not in `backend/mappings/` or wrong `source_format`/`pivot` keys | Check YAML keys match registry and plugin `FORMAT_ID`                               |
| Format detected wrongly      | Extension mismatch or ambiguous JSON content                          | Override via `source_format` query param in API call                                |
| Missing fields not shown     | Pivot `required_fields` list empty                                    | Add fields to pivot entry in `pivot_registry.yaml`                                  |
| CORS error in dev            | Frontend not on port 5173                                             | Vite must run on 5173; proxy is configured for that port only                       |
| TypeScript error on build    | Missing type in `client.ts`                                           | Add the interface before using it in a component                                    |
| `uv sync` fails              | Python < 3.12                                                         | Check `python --version`; install 3.12+ via `uv python install 3.12`                |
| `pyproject.toml` build error | Missing `[tool.hatch.build.targets.wheel]` packages config            | Ensure `packages = ["."]` is defined                                              |
| AI call returns garbled YAML | Model not following instructions                                      | Lower `temperature` (use 0.1 for mapping gen); strip markdown fences before parsing |

---

## Python Environment Reference

```bash
cd backend
uv sync                          # install all deps from pyproject.toml
uv run uvicorn main:app --reload # run dev server
uv run ruff check .              # lint
uv run ruff format .             # format
uv pip install -e .              # editable install if needed
```

Python 3.12+ is required. The codebase uses `str | None` union syntax, `match` statements,
and `typing.TypeAlias` — none of which work on 3.11 or below.

---

## Specification Template

Every non-trivial change starts here. Fill in all sections. For trivial changes (typo fix,
YAML-only pivot addition), the spec can be the issue title + one-line acceptance criteria.

```markdown
### Goal
What problem are we solving?

### Business Value
Why does this matter? What breaks if we don't do this?

### Functional Requirements
1. FR-1: <what the system must do>
2. FR-2: ...

### Non-Functional Requirements
Performance, scalability, security, reliability, accessibility, maintainability.

### Constraints
Technical, architectural, organizational, dependency, or platform constraints.

### Inputs / Outputs
Explicit contracts, schemas, API behaviour, data flow.

### Edge Cases
- Empty / malformed inputs
- Timeouts, retries, partial failures
- Concurrent / race conditions
- Backward compatibility impact

### Acceptance Criteria
1. [ ] Criterion 1 (concrete, measurable)
2. [ ] Criterion 2
3. [ ] Criterion 3

### Risks
Likely failure points and implementation hazards.

### Dependencies
Services, modules, APIs, infrastructure, or feature flags needed.

### Test Strategy
- Unit tests: what classes/functions and why
- Integration tests: which endpoints or flows
- E2E tests: which user journeys
- Regression tests: what bug is captured
- Contract tests: input/output schema validation (for AI layer)
```

### Example: Add Darwin Core CSV Format Plugin

**Goal:** Users can upload Darwin Core CSV files and have them converted to JSON-LD pivot format.

**Business Value:** Enables biodiversity researchers to use FAIRweaver with the most common biodiversity data format.

**FR-1:** Plugin loads `.csv` files with Darwin Core header row and produces flat dict.
**FR-2:** Plugin writes JSON-LD from pivot format back to Darwin Core CSV.
**FR-3:** Auto-detection activates when file extension is `.csv`.

**Edge Cases:** CSV with no header row → raise `ValueError` with clear message. CSV with extra columns beyond Darwin Core spec → ignore silently.

**Acceptance Criteria:**

1. [ ] `test_load_darwin_core_csv` passes with sample DwC file
2. [ ] `test_write_darwin_core_csv` round-trips correctly
3. [ ] `detect_format()` returns `darwin_core_csv` for `.csv` extension
4. [ ] `ruff check` + `ruff format` clean

**Test Strategy:** Unit tests for `load()` and `write()` functions. Round-trip test (load → write → load → compare). Integration test via `/convert` endpoint with Darwin Core CSV payload.
