# Test-case design

For each endpoint, design test cases as a JSON array. Each case object:

```json
{
  "scenario": "场景描述",
  "input": {"参数或请求体字段": "值"},
  "expected_status": 200,
  "expected_response": "预期响应描述",
  "priority": "P0"
}
```

## Rules
- Do **not** add ids, Markdown headings, or tables — `render_cases.py` assigns
  global TC-XXX numbers.
- The **first** case of every endpoint must be the happy path, priority `P0`.
- `input` must be a valid JSON value; use `null` when there is no input.
- `expected_status` is an int or string; `priority` is one of `P0` / `P1` / `P2`
  (P0 = core happy path, P1 = important failure, P2 = edge case).
- Apply the loaded `knowledge/*.md` modules — they tell you which scenarios this
  endpoint's shape demands.

## Coverage by depth
- **quick**: happy path + the most important failure(s).
- **full**: happy path + validation errors + auth + boundary/edge, guided by the
  loaded knowledge (param-validation, pagination, file-upload, auth-testing,
  idempotency).

## Aggregate into drafts.json
Collect every planned endpoint into one object keyed by `"<METHOD> <PATH>"`
(the exact method+path from `endpoints.json`):

```json
{
  "POST /pets": [
    {"scenario": "创建成功", "input": {"name": "doggie"}, "expected_status": 201, "expected_response": "返回创建的 pet", "priority": "P0"},
    {"scenario": "缺少 name", "input": {}, "expected_status": 400, "expected_response": "校验错误", "priority": "P1"}
  ],
  "GET /pets": [
    {"scenario": "列表正常返回", "input": null, "expected_status": 200, "expected_response": "返回 pet 数组", "priority": "P0"}
  ]
}
```

Every endpoint in the plan must have an entry, or `render_cases.py` will error.
