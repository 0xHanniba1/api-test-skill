import json
import subprocess
import sys
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_parse_plan_render_cli_workflow(tmp_path):
    endpoints_path = tmp_path / "endpoints.json"
    drafts_path = tmp_path / "drafts.json"
    testcases_path = tmp_path / "testcases.md"

    parse_result = _run_cli("scripts/parse.py", str(FIXTURES / "petstore.yaml"))
    assert parse_result.returncode == 0, parse_result.stderr
    endpoints_path.write_text(parse_result.stdout, encoding="utf-8")
    endpoints = json.loads(parse_result.stdout)

    assert [f"{ep['method']} {ep['path']}" for ep in endpoints] == [
        "GET /pets",
        "POST /pets",
        "GET /pets/{petId}",
    ]

    plan_result = _run_cli(
        "scripts/plan_files.py",
        str(endpoints_path),
        "--depth",
        "quick",
        "--arch",
        "flat",
    )
    assert plan_result.returncode == 0, plan_result.stderr
    plan = json.loads(plan_result.stdout)

    planned = {f"{item['method']} {item['path']}": item for item in plan["plan"]}
    assert planned["GET /pets"]["file"] == "test_get_pets.py"
    assert "param-validation.md" in planned["GET /pets"]["knowledge"]
    assert "auth-testing.md" in planned["POST /pets"]["knowledge"]

    drafts_path.write_text(
        json.dumps(
            {
                "GET /pets": [
                    {
                        "scenario": "list pets successfully",
                        "input": {"limit": 10},
                        "expected_status": 200,
                        "expected_response": "returns a pet list",
                        "priority": "P0",
                    }
                ],
                "POST /pets": [
                    {
                        "scenario": "create pet successfully",
                        "input": {"name": "doggie"},
                        "expected_status": 201,
                        "expected_response": "returns the created pet",
                        "priority": "P0",
                    }
                ],
                "GET /pets/{petId}": [
                    {
                        "scenario": "get pet by id successfully",
                        "input": {"petId": 1},
                        "expected_status": 200,
                        "expected_response": "returns the requested pet",
                        "priority": "P0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    render_result = _run_cli(
        "scripts/render_cases.py",
        "--endpoints",
        str(endpoints_path),
        "--drafts",
        str(drafts_path),
        "-o",
        str(testcases_path),
    )
    assert render_result.returncode == 0, render_result.stderr

    testcases = testcases_path.read_text(encoding="utf-8")
    assert "## GET /pets" in testcases
    assert "## POST /pets" in testcases
    assert "## GET /pets/{petId}" in testcases
    assert "TC-001" in testcases
    assert "TC-002" in testcases
    assert "TC-003" in testcases
