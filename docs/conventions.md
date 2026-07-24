# Conventions

> Style, naming, and formatting rules for this project.

## Language

### Python (backend)

- Python 3.12+ only. Use modern syntax: `X | Y` union types, `match`, `TypeAlias`.
- Indent with 4 spaces.
- Single quotes for strings.
- Trailing commas in multi-line collections.
- Use `pathlib.Path` for all file paths, never `os.path`.
- Raise `HTTPException` only in `main.py`. Raise plain `ValueError` / `RuntimeError` in engine/plugins.
- Do not use `print()` for debugging — use `logging`.
- Format with `ruff format`, lint with `ruff check`.

### TypeScript (frontend)

- Strict mode enabled.
- Indent with 2 spaces.
- No semicolons (Prettier default).
- Double quotes for strings.
- Use `type` over `interface` for simple shapes.
- Prefer `unknown` over `any`.
- All API response types must be defined in `src/api/client.ts`.

## Imports

- Group: stdlib → external → internal. One blank line between groups.
- No wildcard imports.
- Sort alphabetically within each group.

## Git

- Conventional commits: `feat(module): description`.
- Branch naming: `feat/description`, `fix/description`.
- Max 72 characters in the subject line.

## Tests

- One assertion per test where possible.
- Test names describe behavior: `should <expected> when <condition>`.
- Use temp directories, not mocks, for filesystem tests.
- Clean up after tests (temp dirs, env vars).
