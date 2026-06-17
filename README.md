# api-test-skill

English | [简体中文](README.zh-CN.md)

Agent-driven skill that turns an API document into test cases and runnable
**pytest + requests** code. The LLM work is done by the **host agent** (Claude
Code / Codex) — this project ships only deterministic scripts plus reusable test
knowledge, and needs **no API keys**.

Companion to **api-test-gen** (the standalone CLI version): same domain,
different shape. `api-test-gen` calls an LLM itself; `api-test-skill` hands the
LLM work to the agent and keeps only the parts that must be reliable and
repeatable.

## Deterministic (scripts) vs. agent's job

| Deterministic — `scripts/` | Agent's judgment |
|---|---|
| Parse Swagger/OpenAPI/Postman → endpoints | Read free-form docs, extract endpoints |
| Filenames, tag grouping, knowledge selection | Design which test cases matter |
| TC-XXX numbering, canonical Markdown rendering | Write pytest/requests code |
| Syntax / YAML / pytest-collect validation | Self-heal failing validation |

## Usage (Claude Code / Codex)

The agent reads `SKILL.md` → `instructions/workflow.md`, then:

```bash
uv sync                                          # one-time: install pydantic/pyyaml/pytest
uv run python scripts/parse.py api.yaml > endpoints.json
uv run python scripts/plan_files.py endpoints.json --depth quick --arch flat
# agent reads instructions/ + knowledge/, designs drafts.json
uv run python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json -o out/testcases.md
# agent writes code per instructions/code-gen-*.md
uv run python scripts/validate.py out/           # syntax + YAML; agent reads errors, fixes, repeats
# uv run python scripts/validate.py out/ --collect  # also check imports/collection (needs `pip install requests` first)
```

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

## Setup

Python ≥ 3.11 with `pydantic` + `pyyaml` (and `pytest` to collect/run generated
tests). With uv: `uv sync`, then prefix script calls with `uv run`.

## Why no LLM in this project

Parsing specs, naming files, numbering cases, and checking syntax must be
reliable — those are scripts. Choosing which cases matter and writing the code
need judgment — that's the agent. Self-healing is native: generate → `validate.py`
→ read errors → fix, with no hidden LLM-repair pass.
