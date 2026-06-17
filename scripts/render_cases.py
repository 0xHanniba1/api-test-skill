"""Render agent-authored test-case drafts into the canonical Markdown document.

The agent produces, per endpoint, a JSON array of test-case drafts. This script
validates them against the schema, assigns global TC-XXX ids deterministically,
and renders the canonical testcases.md. The Markdown stays human-reviewable and
editable; downstream code generation re-parses it.

Drafts file format — a JSON object mapping "<METHOD> <PATH>" to a draft array:
    {
      "POST /pets": [
        {"scenario": "...", "input": {...}, "expected_status": 201,
         "expected_response": "...", "priority": "P0"}
      ]
    }

Usage:
    python scripts/render_cases.py --endpoints endpoints.json --drafts drafts.json \
        [-o testcases.md] [--start-index N]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _core.endpoints import EndpointListError, validate_endpoint_list  # noqa: E402
from _core.parser.base import ApiEndpoint  # noqa: E402
from _core.testcase_document import (  # noqa: E402
    TestCaseDocumentError,
    parse_drafts,
    render_endpoint_section,
)


class InputLoadError(ValueError):
    """Raised when input JSON cannot be loaded or validated."""


def _load_endpoints(path: Path) -> list[ApiEndpoint]:
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise InputLoadError(f"cannot read endpoints file: {error}") from error
    except json.JSONDecodeError as error:
        raise InputLoadError(f"invalid endpoints JSON: {error}") from error

    if not isinstance(data, list):
        raise InputLoadError("endpoints JSON must be an array")

    try:
        endpoints = [ApiEndpoint.model_validate(item) for item in data]
        validate_endpoint_list(endpoints)
        return endpoints
    except ValidationError as error:
        raise InputLoadError(f"invalid endpoint schema: {error}") from error
    except EndpointListError as error:
        raise InputLoadError(str(error)) from error


def _load_drafts_map(path: Path) -> dict[str, Any]:
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise InputLoadError(f"cannot read drafts file: {error}") from error
    except json.JSONDecodeError as error:
        raise InputLoadError(f"invalid drafts JSON: {error}") from error

    if not isinstance(data, dict):
        raise InputLoadError('drafts JSON must be an object keyed by "<METHOD> <PATH>"')
    return data


def _endpoint_key(endpoint: ApiEndpoint) -> str:
    return f"{endpoint.method} {endpoint.path}"


def _validate_draft_keys(
    endpoints: list[ApiEndpoint], drafts_map: dict[str, Any]
) -> None:
    expected_keys = [_endpoint_key(endpoint) for endpoint in endpoints]
    expected = set(expected_keys)
    actual = set(drafts_map)
    missing = [key for key in expected_keys if key not in actual]
    unexpected = sorted(actual - expected)

    errors = []
    if missing:
        errors.append(f"missing drafts for endpoint(s): {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected drafts for endpoint(s): {', '.join(unexpected)}")
    if errors:
        raise InputLoadError("; ".join(errors))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--endpoints", required=True, type=Path)
    ap.add_argument(
        "--drafts",
        required=True,
        type=Path,
        help='JSON mapping "<METHOD> <PATH>" -> [draft, ...]',
    )
    ap.add_argument("-o", "--output", type=Path, help="write to file instead of stdout")
    ap.add_argument("--start-index", type=int, default=1)
    args = ap.parse_args()

    try:
        endpoints = _load_endpoints(args.endpoints)
        drafts_map = _load_drafts_map(args.drafts)
        _validate_draft_keys(endpoints, drafts_map)
    except InputLoadError as error:
        print(f"Failed to load input: {error}", file=sys.stderr)
        return 1

    idx = args.start_index
    sections = []
    try:
        for ep in endpoints:
            drafts = parse_drafts(
                json.dumps(drafts_map[_endpoint_key(ep)], ensure_ascii=False)
            )
            section_md, idx = render_endpoint_section(ep, drafts, idx)
            sections.append(section_md)
    except TestCaseDocumentError as error:
        print(f"Invalid drafts: {error}", file=sys.stderr)
        return 1

    document = "\n\n".join(sections) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
        print(
            f"Wrote {args.output} ({idx - args.start_index} cases)", file=sys.stderr
        )
    else:
        sys.stdout.write(document)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
