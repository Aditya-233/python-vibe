#!/usr/bin/env python3
"""Review one small first-party .py file in a project (default: OpenSRE).

  PYTHONPATH=src python scripts/review.py \\
    --project /Users/yauhenbichel/DevBox/tracer-cloud/opensre

  PYTHONPATH=src python scripts/review.py \\
    --project /Users/yauhenbichel/DevBox/tracer-cloud/opensre \\
    --file tools/system/fleet_monitoring/provider_ids.py

  PYTHONPATH=src python scripts/review.py --project … --file path.py --fix \\
    "fix the NameError in provider_from_classified_name"
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harness.project_scan import list_small_py_files  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project",
        type=Path,
        default=Path("/Users/yauhenbichel/DevBox/tracer-cloud/opensre"),
    )
    parser.add_argument("--file")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="apply a rewrite (keeps .bak). Default is review-only.",
    )
    parser.add_argument("task", nargs="?", default="list concrete bugs")
    parser.add_argument("--engine", default="auto")
    args, rest = parser.parse_known_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        sys.exit(f"not a directory: {project}")

    rel = args.file
    if not rel:
        candidates = list_small_py_files(project, limit=1)
        if not candidates:
            sys.exit("no small first-party .py files")
        rel = str(candidates[0].relative_to(project))
        print(f"picked {rel} ({candidates[0].stat().st_size} bytes)", file=sys.stderr)

    vibe = ROOT / "scripts" / "vibe.py"
    cmd = [
        sys.executable,
        str(vibe),
        "--engine",
        args.engine,
        "--project",
        str(project),
        "--file",
        rel,
    ]
    if args.fix:
        cmd.append("--apply")
    else:
        cmd.append("--review")
    cmd.append(args.task)
    cmd.extend(a for a in rest if a != "--")
    raise SystemExit(subprocess.call(cmd, cwd=ROOT))


if __name__ == "__main__":
    main()
