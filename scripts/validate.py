"""Validate generated test code: Python syntax, YAML format, (optional) pytest collect.

Reads every text file under the given directory and reports validation errors
as JSON. This is the deterministic judge for the agent's self-healing loop:
generate -> validate -> read errors -> fix -> validate again.

By default only the dependency-free static checks run (syntax + YAML). Pass
--collect to also run `pytest --collect-only`; that imports the test modules, so
run it only in an environment where the code-under-test's deps (e.g. requests)
are installed — otherwise a missing dep shows up as a false "error".

Exit 0 = all good; exit 1 = errors found; exit 2 = bad invocation.

Usage:
    python scripts/validate.py <generated_code_dir> [--collect]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _core.validator import validate_files  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path, help="directory of generated code")
    ap.add_argument(
        "--collect",
        action="store_true",
        help="also run pytest --collect-only (needs code-under-test deps installed)",
    )
    args = ap.parse_args()

    root = args.directory
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            files[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # skip binary artifacts

    errors = validate_files(files, collect=args.collect)
    json.dump(
        {"ok": not errors, "errors": errors},
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
