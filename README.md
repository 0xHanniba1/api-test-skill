# api-test-skill

English | [简体中文](README.zh-CN.md)

`api-test-skill` is a Codex / Claude Code skill for turning API documents into
reviewable test cases and runnable **pytest + requests** code.

The skill gives the agent a repeatable workflow: parse structured specs, plan
filenames, select API-testing knowledge, render numbered test cases, and validate
the generated output.

If you want the same workflow as a standalone command-line tool, use
**api-test-gen**. This repo is the skill version.

## Responsibility split

| `scripts/` handle | The host agent handles |
|---|---|
| Parse Swagger / OpenAPI / Postman into endpoints | Read free-form or Markdown docs and extract endpoints |
| Plan filenames, tag grouping, and knowledge modules | Decide which test cases are worth writing |
| Assign TC-XXX ids and render canonical Markdown | Write pytest + requests code |
| Validate Python syntax, YAML, and optional pytest collection | Read validation errors and fix the generated output |

## Quick start

The agent should read `SKILL.md`, then `instructions/workflow.md`, then run the
workflow:

```bash
uv sync
uv run python scripts/parse.py api.yaml > endpoints.json
uv run python scripts/plan_files.py endpoints.json --depth quick --arch flat

# The agent reads the plan, instructions/, and selected knowledge/*.md,
# then designs drafts.json.
uv run python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json -o out/testcases.md

# The agent writes generated pytest code into out/.
uv run python scripts/validate.py out/
```

`parse.py` intentionally handles only structured API docs. For free-form or
Markdown docs, the agent reads the document directly and hand-writes
`endpoints.json` in the same schema.

Add `--collect` only after installing the generated project's runtime
dependencies. For flat output, that is usually `pytest requests`. For layered
output, use the generated `requirements.txt`, which includes `pytest`,
`requests`, and `pyyaml`.

## Output modes

- `--arch flat`: writes `<out>/conftest.py` plus one `test_*.py` file per
  endpoint.
- `--arch layered`: writes `base/`, `data/`, `api/`, `services/`, `tests/`,
  `Jenkinsfile`, and `requirements.txt`, grouped by API tag.

## Layout

```
api-test-skill/
├── SKILL.md              # Claude Code entry
├── AGENTS.md             # Codex entry and repository rules
├── instructions/         # host-agnostic workflow + generation guidance
│   ├── workflow.md  testcase-gen.md  code-gen-flat.md  code-gen-layered.md
├── knowledge/            # reusable test-design modules (base, pagination, auth, ...)
├── scripts/
│   ├── parse.py  plan_files.py  render_cases.py  validate.py
│   └── _core/            # deterministic library (parser, naming, numbering, validator, output)
└── tests/                # tests for the deterministic core
```

## Development

Python 3.11 or newer is required.

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

The skill scripts depend on `pydantic` and `pyyaml`. Project tests and linting
use `pytest` and `ruff`. Generated test projects have their own runtime
dependencies, usually `pytest`, `requests`, and sometimes `pyyaml`.

## Design

Parsing specs, naming files, numbering cases, and checking syntax should be
repeatable, so they live in scripts. Choosing test coverage and writing test code
requires judgment, so the host agent does that work.

The repair loop is explicit: generate, run `validate.py`, read the errors, fix
the output, and repeat.
