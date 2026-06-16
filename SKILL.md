---
name: api-test-skill
description: Generate API test automation (test cases + pytest/requests code) from an API document — Swagger/OpenAPI, Postman, or free-form Markdown. Use when the user wants to turn an API spec into test cases or runnable pytest code, scaffold an API test project, or add tests for new endpoints. Deterministic parsing, naming, TC-XXX numbering, and validation run as bundled scripts; the agent designs the cases and writes the code. No API keys required.
---

# API Test Skill

Turn an API document into test cases and runnable pytest + requests code. You do
the reasoning; bundled scripts handle the deterministic parts (parsing, naming,
TC-XXX numbering, syntax/collect validation). **No API keys — you are the LLM.**

## How to use

Read **`instructions/workflow.md`** and follow its 7 steps. In short:

1. `python scripts/parse.py <doc> > endpoints.json` — structured docs; read free-form docs yourself
2. `python scripts/plan_files.py endpoints.json --depth <quick|full> --arch <flat|layered>`
3. Read `instructions/testcase-gen.md` + the `knowledge/*.md` modules the plan names
4. Design case drafts → `drafts.json`
5. `python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json -o testcases.md`
6. Generate code per `instructions/code-gen-flat.md` or `instructions/code-gen-layered.md`
7. `python scripts/validate.py <out>` (syntax + YAML) → read errors → fix → repeat until ok (your self-heal loop); add `--collect` after `pip install requests` to also check imports/collection

## Setup

Needs Python with `pydantic` and `pyyaml` (plus `pytest` to collect/run tests).
With uv: `uv sync`, then prefix script calls with `uv run`.

## Knowledge modules

`knowledge/` holds reusable test-design guidance — `base`, `param-validation`,
`pagination`, `file-upload`, `auth-testing`, `idempotency`. `plan_files.py`
selects the relevant ones per endpoint based on its shape and the chosen depth.

## Design

The split is deliberate: anything that must be **reliable and repeatable**
(parsing specs, naming files, numbering cases, checking syntax) is a script;
anything that needs **judgment** (which cases matter, how to write the code) is
yours. Self-healing is native — you generate, run `validate.py`, read the
errors, and fix — instead of a hidden LLM-repair pass.
