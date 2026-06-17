# api-test-skill

[English](README.md) | 简体中文

`api-test-skill` 是一个面向 Codex / Claude Code 的 skill，用来把 API 文档转成可审阅的测试用例，以及可运行的 **pytest + requests** 代码。

这个 skill 给 agent 提供一套可重复的工作流：解析结构化接口文档、规划文件名、选择 API 测试知识、渲染带编号的测试用例，并校验生成结果。

如果你需要同一套流程的独立命令行工具，用 **api-test-gen**。这个仓库是 skill 形态。

## 职责分工

| `scripts/` 负责 | 宿主 agent 负责 |
|---|---|
| 解析 Swagger / OpenAPI / Postman 为 endpoints | 阅读自由文本或 Markdown 文档，提取 endpoints |
| 规划文件名、按 tag 分组、选择知识模块 | 判断哪些测试用例值得写 |
| 分配 TC-XXX 编号，渲染规范 Markdown | 编写 pytest + requests 代码 |
| 校验 Python 语法、YAML 和可选的 pytest collect | 读取校验错误并修复生成结果 |

## 快速开始

agent 先读 `SKILL.md`，再读 `instructions/workflow.md`，然后执行工作流：

```bash
uv sync
uv run python scripts/parse.py api.yaml > endpoints.json
uv run python scripts/plan_files.py endpoints.json --depth quick --arch flat

# agent 读取 plan、instructions/ 和被选中的 knowledge/*.md，
# 然后设计 drafts.json。
uv run python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json -o out/testcases.md

# agent 把生成的 pytest 代码写入 out/。
uv run python scripts/validate.py out/
```

`parse.py` 只处理结构化 API 文档。自由文本或 Markdown 文档需要 agent 直接阅读，并按同样的 schema 手写 `endpoints.json`。

只有在安装好生成项目的运行依赖之后，才加 `--collect`。flat 输出通常需要 `pytest requests`；layered 输出使用生成的 `requirements.txt`，其中包含 `pytest`、`requests` 和 `pyyaml`。

## 输出模式

- `--arch flat`：生成 `<out>/conftest.py`，以及每个 endpoint 一个 `test_*.py` 文件。
- `--arch layered`：按 API tag 生成 `base/`、`data/`、`api/`、`services/`、`tests/`、`Jenkinsfile` 和 `requirements.txt`。

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

## 开发

需要 Python 3.11 或更高版本。

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

skill 脚本依赖 `pydantic` 和 `pyyaml`。项目测试和 lint 依赖 `pytest` 和 `ruff`。生成出来的测试项目有自己的运行依赖，通常是 `pytest`、`requests`，有 YAML 数据时还需要 `pyyaml`。

## 设计

解析规范、命名文件、编号用例、检查语法，这些需要可重复，所以放在脚本里。判断测试覆盖范围和编写真实测试代码需要上下文判断，所以交给宿主 agent。

修复循环是显式的：生成，运行 `validate.py`，读取错误，修复输出，然后重复。
