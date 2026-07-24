# Architecture

> What "good work" means in this project.

## Structure

- `backend/` — FastAPI Python service. One module per file. Keep files focused.
- `frontend/` — React + Vite + TypeScript UI. One component per file.
- `backend/tests/` — Automated Python tests. One test file per module.
- `frontend/tests/` — Automated TypeScript tests. One test file per component.
- `specs/` — Per-feature specifications (requirements, design, tasks).
- `progress/` — Session state and history.
- `docs/` — Project documentation.

## Principles

- **State on disk, not in chat.** Agents write results to files. The human reads from disk, never from agent text responses.
- **One feature at a time.** The team focuses on one change. No parallel features in the same session.
- **Specs before code.** The spec-author writes the spec. The human approves it. Then the implementer writes code.
- **Tests are mandatory.** No task is `done` without passing tests.
- **Traceability.** Every test maps to a requirement. Every requirement has at least one test.

## Naming

- Python files: `snake_case.py`
- TypeScript files: `kebab-case.ts` for utilities, `PascalCase.tsx` for components
- Functions: `camelCase` for TypeScript, `snake_case` for Python
- Classes: `PascalCase` everywhere
- Constants: `UPPER_SNAKE_CASE` everywhere

## Error handling

- Return error objects, never throw in business logic.
- API entry points catch and format errors for humans.
- Log errors to stderr, output to stdout.

## Dependencies

- Minimal. No framework unless the project already uses one.
- No new dependency without a justification.
