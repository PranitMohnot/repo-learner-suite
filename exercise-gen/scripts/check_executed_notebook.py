#!/usr/bin/env python3
"""
check_executed_notebook.py — Classify cell outcomes in an executed notebook.

Used by Stage 4d (Channel 2: nbconvert --execute --allow-errors) to verify
*environment health*, not solution correctness. The notebook's scaffold cell
intentionally raises (NotImplementedError or the language equivalent), so a
naive "did nbconvert succeed?" check is meaningless. What we actually need:

- Setup + guided code cells succeeded → env is healthy.
- Scaffold + validation cells errored → expected, not a problem.
- Any other surprise → flag.

This script reads `cell.metadata.tags` looking for `role:<name>` entries
set by scaffold_notebook.py at generation time. Cells without a role tag
are ignored (they're headers, stretch placeholders, etc. that don't affect
env health).

Usage:
    python check_executed_notebook.py <executed.ipynb> [<report.json>]

Exit code:
    0 — env healthy (all expected-success cells ran without error)
    1 — env unhealthy (at least one expected-success cell errored)
    2 — bad invocation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Cells with these role tags must run without error. Anything else doesn't
# affect env health — scaffold + validation cells are SUPPOSED to error
# while the scaffold is unfilled, headers don't execute, solution may
# error depending on whether the env supports it independently.
EXPECTED_SUCCESS = {"setup", "guided-code"}


def get_role(cell: dict) -> str | None:
    tags = (cell.get("metadata") or {}).get("tags") or []
    for t in tags:
        if isinstance(t, str) and t.startswith("role:"):
            return t.split(":", 1)[1]
    return None


def first_error(cell: dict) -> tuple[str, str] | None:
    for out in cell.get("outputs") or []:
        if out.get("output_type") == "error":
            return out.get("ename", "?"), out.get("evalue", "")
    return None


def classify(nb_path: Path) -> dict:
    nb = json.loads(nb_path.read_text())
    cells_out: list[dict] = []
    env_healthy = True

    for i, cell in enumerate(nb.get("cells", [])):
        role = get_role(cell)
        err = first_error(cell)
        entry: dict = {"cell": i, "role": role, "errored": bool(err)}
        if err:
            entry["error"] = {"ename": err[0], "evalue": err[1][:200]}

        if role in EXPECTED_SUCCESS:
            if err:
                entry["status"] = "UNEXPECTED_FAILURE"
                env_healthy = False
            else:
                entry["status"] = "OK"
        elif role is None:
            entry["status"] = "IGNORED"  # no role tag, e.g. markdown header
        else:
            # Other roles: scaffold / validation / solution / etc.
            # We don't require success or failure here.
            entry["status"] = "NOT_CHECKED"

        cells_out.append(entry)

    return {
        "notebook": str(nb_path),
        "env_healthy": env_healthy,
        "cells": cells_out,
    }


def render(report: dict) -> str:
    lines = [f"Notebook: {Path(report['notebook']).name}"]
    lines.append(f"Env healthy: {report['env_healthy']}")
    lines.append("")
    for c in report["cells"]:
        role = c.get("role") or "—"
        status = c["status"]
        marker = "✓" if status == "OK" else ("✗" if status == "UNEXPECTED_FAILURE" else " ")
        line = f"  [{marker}] cell {c['cell']:2}  role={role:<14} status={status}"
        if c.get("errored") and c.get("error"):
            line += f"  ({c['error']['ename']})"
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(__doc__.split("Usage:")[1].strip(), file=sys.stderr)
        return 2

    nb_path = Path(sys.argv[1])
    if not nb_path.exists():
        print(f"error: {nb_path} not found", file=sys.stderr)
        return 2

    report = classify(nb_path)
    print(render(report))

    if len(sys.argv) == 3:
        Path(sys.argv[2]).write_text(json.dumps(report, indent=2))

    return 0 if report["env_healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
