"""Parse a structured API document (Swagger/OpenAPI/Postman) into endpoints JSON.

Free-form / Markdown docs are NOT handled here — the host agent should read
those directly and extract endpoints itself. This script only covers the
formats where deterministic parsing is more reliable than an LLM.

Usage:
    python scripts/parse.py <doc> [--format auto|swagger|postman]
Output: a JSON array of endpoints on stdout.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _core.endpoints import EndpointListError, validate_endpoint_list  # noqa: E402
from _core.parser.detect import FormatDetectionError, detect_format  # noqa: E402
from _core.parser.postman import parse_postman  # noqa: E402
from _core.parser.swagger import parse_openapi  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("doc", type=Path, help="Path to the API document")
    ap.add_argument(
        "--format", default="auto", choices=["auto", "swagger", "postman"]
    )
    args = ap.parse_args()

    try:
        fmt = detect_format(args.doc) if args.format == "auto" else args.format
    except (OSError, UnicodeDecodeError) as error:
        print(f"Failed to read {args.doc}: {error}", file=sys.stderr)
        return 1
    except FormatDetectionError as error:
        print(f"Failed to detect format for {args.doc}: {error}", file=sys.stderr)
        return 1

    if fmt == "markdown":
        print(
            "This looks like a free-form/Markdown doc. Read it directly and extract "
            "endpoints yourself; this script only parses Swagger/OpenAPI and Postman.",
            file=sys.stderr,
        )
        return 2

    try:
        if fmt == "swagger":
            endpoints = parse_openapi(args.doc)
        elif fmt == "postman":
            endpoints = parse_postman(args.doc)
        else:
            print(f"Unsupported format: {fmt}", file=sys.stderr)
            return 2
        validate_endpoint_list(endpoints)
    except EndpointListError as error:
        print(f"Parsed endpoints are not usable: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Failed to parse {args.doc}: {error}", file=sys.stderr)
        return 1

    json.dump(
        [e.model_dump() for e in endpoints],
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
