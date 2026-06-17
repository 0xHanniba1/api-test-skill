import json
import subprocess
import sys


def test_parse_reports_missing_file_without_traceback(tmp_path):
    missing = tmp_path / "missing.yaml"

    result = subprocess.run(
        [sys.executable, "scripts/parse.py", str(missing)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Failed to read" in result.stderr
    assert "Traceback" not in result.stderr


def test_parse_refuses_markdown_without_traceback(tmp_path):
    document = tmp_path / "api.md"
    document.write_text("# API docs\n\nGET /users", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/parse.py", str(document)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "free-form/Markdown doc" in result.stderr
    assert "Traceback" not in result.stderr


def test_parse_reports_invalid_structured_file_without_traceback(tmp_path):
    document = tmp_path / "broken.yaml"
    document.write_text("openapi: [broken\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/parse.py", str(document)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Failed to detect format" in result.stderr
    assert "invalid YAML/JSON" in result.stderr
    assert "Traceback" not in result.stderr


def test_parse_reports_unknown_structured_file_without_traceback(tmp_path):
    document = tmp_path / "unknown.yaml"
    document.write_text("info: {title: Missing API version}\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/parse.py", str(document)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Failed to detect format" in result.stderr
    assert "unsupported structured API document" in result.stderr
    assert "Traceback" not in result.stderr


def test_parse_rejects_structured_doc_with_no_endpoints(tmp_path):
    document = tmp_path / "empty-openapi.yaml"
    document.write_text(
        """openapi: 3.0.0
info: {title: Empty, version: 1.0.0}
paths: {}
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/parse.py", str(document)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Parsed endpoints are not usable" in result.stderr
    assert "must contain at least one endpoint" in result.stderr
    assert "Traceback" not in result.stderr


def test_parse_rejects_duplicate_postman_endpoints(tmp_path):
    document = tmp_path / "duplicates.postman.json"
    document.write_text(
        json.dumps(
            {
                "info": {
                    "name": "Duplicates",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                },
                "item": [
                    {"name": "List users A", "request": "https://api.example.com/users"},
                    {"name": "List users B", "request": "https://api.example.com/users"},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/parse.py", str(document)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Parsed endpoints are not usable" in result.stderr
    assert "duplicate endpoint: GET /users" in result.stderr
    assert "Traceback" not in result.stderr


def test_plan_files_reports_invalid_json_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    endpoints.write_text("{not json", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/plan_files.py", str(endpoints)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Failed to load endpoints" in result.stderr
    assert "Traceback" not in result.stderr


def test_plan_files_rejects_duplicate_endpoints_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    endpoints.write_text(
        json.dumps(
            [
                {"method": "GET", "path": "/users"},
                {"method": "get", "path": "users"},
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/plan_files.py", str(endpoints)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "duplicate endpoint: GET /users" in result.stderr
    assert "Traceback" not in result.stderr


def test_plan_files_rejects_empty_endpoints_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    endpoints.write_text("[]", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/plan_files.py", str(endpoints)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "must contain at least one endpoint" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_cases_reports_invalid_drafts_shape_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    drafts = tmp_path / "drafts.json"
    endpoints.write_text(
        json.dumps([{"method": "GET", "path": "/users"}]),
        encoding="utf-8",
    )
    drafts.write_text("[]", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_cases.py",
            "--endpoints",
            str(endpoints),
            "--drafts",
            str(drafts),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "drafts JSON must be an object" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_cases_rejects_missing_draft_key_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    drafts = tmp_path / "drafts.json"
    endpoints.write_text(
        json.dumps([{"method": "GET", "path": "/users"}]),
        encoding="utf-8",
    )
    drafts.write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_cases.py",
            "--endpoints",
            str(endpoints),
            "--drafts",
            str(drafts),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing drafts for endpoint(s): GET /users" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_cases_rejects_unexpected_draft_key_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    drafts = tmp_path / "drafts.json"
    endpoints.write_text(
        json.dumps([{"method": "GET", "path": "/users"}]),
        encoding="utf-8",
    )
    drafts.write_text(
        json.dumps(
            {
                "GET /users": [
                    {
                        "scenario": "ok",
                        "input": None,
                        "expected_status": 200,
                        "expected_response": "ok",
                        "priority": "P0",
                    }
                ],
                "GET /typo": [
                    {
                        "scenario": "typo",
                        "input": None,
                        "expected_status": 200,
                        "expected_response": "typo",
                        "priority": "P2",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_cases.py",
            "--endpoints",
            str(endpoints),
            "--drafts",
            str(drafts),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "unexpected drafts for endpoint(s): GET /typo" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_cases_rejects_duplicate_endpoints_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    drafts = tmp_path / "drafts.json"
    endpoints.write_text(
        json.dumps(
            [
                {"method": "GET", "path": "/users"},
                {"method": "GET", "path": "/users"},
            ]
        ),
        encoding="utf-8",
    )
    drafts.write_text(
        json.dumps(
            {
                "GET /users": [
                    {
                        "scenario": "ok",
                        "input": None,
                        "expected_status": 200,
                        "expected_response": "ok",
                        "priority": "P0",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_cases.py",
            "--endpoints",
            str(endpoints),
            "--drafts",
            str(drafts),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "duplicate endpoint: GET /users" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_cases_rejects_empty_endpoints_without_traceback(tmp_path):
    endpoints = tmp_path / "endpoints.json"
    drafts = tmp_path / "drafts.json"
    endpoints.write_text("[]", encoding="utf-8")
    drafts.write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_cases.py",
            "--endpoints",
            str(endpoints),
            "--drafts",
            str(drafts),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "must contain at least one endpoint" in result.stderr
    assert "Traceback" not in result.stderr
