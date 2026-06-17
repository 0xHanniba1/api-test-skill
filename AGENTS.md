# api-test-skill Agent Rules

This repository is a Codex-compatible skill for generating API test cases and
pytest + requests code from API documents.

## Before Work

- Read `SKILL.md`, then `instructions/workflow.md`.
- Keep the deterministic/agent split intact:
  - scripts parse specs, plan filenames, render TC-XXX cases, and validate output;
  - the host agent designs cases, writes generated code, and fixes validation errors.
- Use the project Python environment. Prefer `uv run python scripts/<script>.py ...`.

## Generation Workflow

1. Parse structured API docs with `scripts/parse.py`; for Markdown/free-form docs,
   extract `endpoints.json` yourself in the same schema.
2. Run `scripts/plan_files.py` and use its filenames exactly.
3. Read `instructions/testcase-gen.md` plus every `knowledge/*.md` file named in
   the plan before drafting cases.
4. Render cases with `scripts/render_cases.py`; do not hand-number `TC-XXX` ids.
5. Generate flat or layered code using the matching `instructions/code-gen-*.md`.
6. Run `scripts/validate.py <out>` and fix errors until it returns `ok: true`.

## Project Validation

For changes to this repository, run:

```bash
uv run pytest
uv run ruff check .
```

Do not hardcode URLs, tokens, credentials, or environment-specific values in
generated tests. Use `API_BASE_URL`, `API_TOKEN`, and pytest fixtures instead.
