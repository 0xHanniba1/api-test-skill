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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _core.parser.base import ApiEndpoint  # noqa: E402
from _core.testcase_document import (  # noqa: E402
    TestCaseDocumentError,
    parse_drafts,
    render_endpoint_section,
)


def _load_endpoints(path: Path) -> list[ApiEndpoint]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [ApiEndpoint.model_validate(item) for item in data]


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

    endpoints = _load_endpoints(args.endpoints)
    drafts_map = json.loads(args.drafts.read_text(encoding="utf-8"))

    idx = args.start_index
    sections = []
    try:
        for ep in endpoints:
            key = f"{ep.method} {ep.path}"
            raw = drafts_map.get(key)
            if raw is None:
                print(f"Missing drafts for endpoint: {key}", file=sys.stderr)
                return 1
            drafts = parse_drafts(json.dumps(raw, ensure_ascii=False))
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
