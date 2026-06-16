"""Plan deterministic filenames and knowledge modules for a set of endpoints.

Reads endpoints JSON (from parse.py or hand-authored) and emits, per endpoint
(flat) or per tag (layered), the target filenames and which knowledge modules
to load — so the agent knows what to write and what guidance to read before
generating cases and code. Naming is deterministic and collision-safe; never
let the model invent filenames.

Usage:
    python scripts/plan_files.py <endpoints.json> [--depth quick|full] [--arch flat|layered]
Output: a JSON plan on stdout.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _core.knowledge_loader import select_skills  # noqa: E402
from _core.naming import (  # noqa: E402
    assign_endpoint_filenames,
    group_endpoints_by_tag,
)
from _core.parser.base import ApiEndpoint  # noqa: E402
from _core.testcase_document import EndpointSection  # noqa: E402


def _load_endpoints(path: Path) -> list[ApiEndpoint]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [ApiEndpoint.model_validate(item) for item in data]


def _plan_flat(endpoints: list[ApiEndpoint], depth: str) -> list[dict]:
    sections = tuple(
        EndpointSection(
            method=e.method, path=e.path, summary="", cases=(), markdown=""
        )
        for e in endpoints
    )
    filenames = assign_endpoint_filenames(sections)
    return [
        {
            "method": e.method,
            "path": e.path,
            "file": filenames[(e.method, e.path)],
            "knowledge": select_skills(e, depth),
        }
        for e in endpoints
    ]


def _plan_layered(endpoints: list[ApiEndpoint], depth: str) -> list[dict]:
    groups = group_endpoints_by_tag(endpoints)
    plan = []
    for tag, eps in groups.items():
        knowledge = sorted({s for e in eps for s in select_skills(e, depth)})
        plan.append(
            {
                "tag": tag,
                "endpoints": [f"{e.method} {e.path}" for e in eps],
                "files": {
                    "data": f"data/{tag}.yaml",
                    "api": f"api/{tag}_api.py",
                    "service": f"services/{tag}_flow.py",
                    "tests": f"tests/test_{tag}.py",
                },
                "knowledge": knowledge,
            }
        )
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("endpoints", type=Path, help="endpoints JSON from parse.py")
    ap.add_argument("--depth", default="quick", choices=["quick", "full"])
    ap.add_argument("--arch", default="flat", choices=["flat", "layered"])
    args = ap.parse_args()

    endpoints = _load_endpoints(args.endpoints)
    plan = (
        _plan_flat(endpoints, args.depth)
        if args.arch == "flat"
        else _plan_layered(endpoints, args.depth)
    )

    json.dump(
        {"arch": args.arch, "depth": args.depth, "plan": plan},
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
