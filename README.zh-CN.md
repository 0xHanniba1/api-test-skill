# api-test-skill

[English](README.md) | 简体中文

由 agent 驱动的 skill：把 API 文档转成测试用例和可运行的 **pytest + requests** 代码。
LLM 的活由**宿主 agent**（Claude Code / Codex）完成——本项目只提供确定性脚本和可复用的测试知识，**不需要任何 API key**。

它是 **api-test-gen**（独立 CLI 版本）的姊妹项目：同一领域，不同形态。`api-test-gen` 自己调用 LLM；
`api-test-skill` 把 LLM 的活交给 agent，只保留那些必须可靠、可重复的部分。

## 确定性（脚本） vs. agent 的判断

| 确定性 —— `scripts/` | 交给 agent 判断 |
|---|---|
| 解析 Swagger/OpenAPI/Postman → endpoints | 读自由文本文档、抽取 endpoints |
| 文件命名、按 tag 分组、知识模块选择 | 设计哪些测试用例值得写 |
| TC-XXX 编号、渲染规范 Markdown | 编写 pytest/requests 代码 |
| 语法 / YAML / pytest-collect 校验 | 校验失败时自愈 |

## 用法（Claude Code / Codex）

agent 读取 `SKILL.md` → `instructions/workflow.md`，然后：

```bash
uv sync                                          # 一次性：安装 pydantic/pyyaml/pytest
uv run python scripts/parse.py api.yaml > endpoints.json
uv run python scripts/plan_files.py endpoints.json --depth quick --arch flat
# agent 读 instructions/ + knowledge/，设计 drafts.json
uv run python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json -o out/testcases.md
# agent 按 instructions/code-gen-*.md 写代码
uv run python scripts/validate.py out/           # 语法 + YAML；agent 读报错、修复、重跑
# uv run python scripts/validate.py out/ --collect  # 额外检查 import/collection（需先 `pip install requests`）
```

## 目录结构

```
api-test-skill/
├── SKILL.md              # Claude Code 入口
├── AGENTS.md             # Codex 入口和仓库规则
├── instructions/         # 与宿主无关的工作流 + 生成指引
│   ├── workflow.md  testcase-gen.md  code-gen-flat.md  code-gen-layered.md
├── knowledge/            # 可复用测试设计模块（base、pagination、auth …）
├── scripts/
│   ├── parse.py  plan_files.py  render_cases.py  validate.py
│   └── _core/            # 确定性库（解析、命名、编号、校验、写盘）
└── tests/                # 确定性核心的测试
```

## 环境

Python ≥ 3.11，需 `pydantic` + `pyyaml`（运行/收集生成的测试还需 `pytest`）。
用 uv：`uv sync`，之后脚本调用前加 `uv run`。

## 为什么这个项目里没有 LLM

解析规范、命名文件、编号用例、检查语法——这些必须可靠，所以是脚本。
判断哪些用例重要、怎么写代码——这些需要判断力，交给 agent。
自愈是原生的：生成 → `validate.py` → 读报错 → 修复，没有隐藏的 LLM 修复步骤。
