# Workflow: API doc → test cases → pytest code

You are generating API test automation. The **deterministic** work (parsing,
naming, TC-XXX numbering, validation) is done by scripts under `scripts/`; you
do the **reasoning** (designing cases, writing code) and the **self-healing**.
There is no LLM call inside this project — you are the model.

Run scripts with the project's Python. With uv: `uv run python scripts/X.py`.

## Steps

1. **Parse the API doc → endpoints.**
   - Structured doc (Swagger/OpenAPI/Postman):
     `python scripts/parse.py <doc> > endpoints.json`
   - Free-form / Markdown doc: `parse.py` will refuse it. Read the doc yourself
     and hand-write `endpoints.json` in the same shape. Run `parse.py` on any
     structured sample once to see the exact field shape (method, path, summary,
     description, tags, parameters, request_body, content_type, ...).

2. **Plan files + knowledge.**
   `python scripts/plan_files.py endpoints.json --depth <quick|full> --arch <flat|layered>`
   Returns, per endpoint (flat) or per tag (layered), the deterministic
   filename(s) and the knowledge modules to load. **Use these filenames exactly —
   never invent your own.**

3. **Read guidance before designing cases.**
   - Read `instructions/testcase-gen.md`.
   - Read each `knowledge/*.md` named in the plan.

4. **Design test-case drafts.** For each endpoint, produce a JSON array of case
   drafts per `testcase-gen.md`. Aggregate into `drafts.json`:
   `{ "<METHOD> <PATH>": [ {draft}, ... ], ... }` — one entry per planned endpoint.

5. **Render the canonical test-case document.**
   `python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json -o testcases.md`
   Validates your drafts, assigns global TC-XXX ids, writes a human-reviewable
   `testcases.md`. On error, fix `drafts.json` and re-run — never hand-number.

6. **Generate code.**
   - flat: read `instructions/code-gen-flat.md`; write one test file per endpoint
     using the planned filenames, plus `conftest.py`.
   - layered: read `instructions/code-gen-layered.md`; write the five-layer
     project (base/data/api/services/tests + conftest + Jenkinsfile + requirements).

7. **Validate and self-heal.**
   `python scripts/validate.py <output_dir>` → `{"ok": true}` or
   `{"ok": false, "errors": {file: msg}}`. If not ok, read the errors, fix the
   offending files, re-run until ok. **This is your self-healing loop** — the
   scripts do not repair code, you do.
   - Default runs dependency-free static checks (Python syntax + YAML).
   - Add `--collect` only after installing the generated code's deps (e.g.
     `pip install requests pyyaml`) — `--collect` imports the test modules, so a
     missing dep would otherwise look like a code error. A clean static pass plus
     a `pip install` then `--collect` pass is the strongest signal.

## Output layout
- flat: `<out>/conftest.py` + `<out>/test_*.py`
- layered: `<out>/{base,data,api,services,tests}/` + `Jenkinsfile` + `requirements.txt`

## Running the generated tests
Inside the output dir: `API_BASE_URL=... API_TOKEN=... pytest -v`.

## Incremental mode
Adding endpoints later: filter `endpoints.json` to the new ones, run
`render_cases.py --start-index N` (N = next free TC number, from the existing
doc), append the new sections to `testcases.md`, and write only the new code
files. Do not renumber or overwrite existing files.
