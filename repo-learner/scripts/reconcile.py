#!/usr/bin/env python3
"""
reconcile.py — Final QA pass for a learn/ directory.

Runs the six checks defined in repo-learner/SKILL.md Shared Contracts. The
pipeline is not "done" until every check passes. Exit code 0 on success,
nonzero on any failure.

Usage:
    python reconcile.py [--learn-dir PATH] [--strict]

Defaults to ./learn relative to cwd. --strict makes warnings into errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------- result model ----------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool = True
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------- helpers ---------------------------------------------------------

MANIFEST_YAML_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
STEP_MARKER_RE = re.compile(r"<!--\s*step:([\d.]+):([a-z0-9-]+)\s*-->")
EXERCISE_SLOT_RE = re.compile(r"exercise-(\d+)")
TOOL_FRAGMENT_RES = [
    re.compile(r"<\s*parameter\b", re.IGNORECASE),
    re.compile(r"<\s*antml", re.IGNORECASE),
    re.compile(r"<\s*function_calls\b", re.IGNORECASE),
    re.compile(r"<\s*invoke\b", re.IGNORECASE),
]

PACKAGE_MANAGERS = {"uv", "pip", "poetry", "conda"}


def parse_manifest(learn_dir: Path) -> list[dict]:
    """Parse YAML blocks from exercise-plan.md. Each entry is one exercise."""
    path = learn_dir / "internals" / "exercise-plan.md"
    if not path.exists():
        return []
    text = path.read_text()
    entries = []
    for block in MANIFEST_YAML_RE.findall(text):
        try:
            entries.append(_parse_simple_yaml(block))
        except ValueError as e:
            entries.append({"_parse_error": str(e), "_raw": block})
    return entries


def _parse_simple_yaml(block: str) -> dict:
    """Minimal YAML subset: `key: value`, no nesting, no lists. Sufficient
    for our manifest schema. Strings in quotes preserve their value."""
    out = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"bad manifest line: {line!r}")
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        out[k.strip()] = v
    return out


def load_config(learn_dir: Path) -> dict:
    path = learn_dir / "internals" / ".config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def user_facing_files(learn_dir: Path) -> list[Path]:
    """Files the user opens — used for env-manager scans."""
    candidates = [
        learn_dir / "curriculum.md",
        learn_dir / "curriculum.html",
        learn_dir / "cheatsheet.md",
        learn_dir / "notebooks" / "README.md",
    ]
    candidates += sorted((learn_dir / "notebooks").glob("exercise-*.ipynb"))
    return [p for p in candidates if p.exists()]


def all_generated_md(learn_dir: Path) -> list[Path]:
    """All generated markdown + notebooks — used for tool-fragment scan.

    Wider than user_facing_files because tool-XML leaks can happen in any
    agent-generated file, including internals/. The user-facing scope is too
    narrow to catch them.
    """
    md = sorted(learn_dir.rglob("*.md"))
    ipynb = sorted(learn_dir.rglob("*.ipynb"))
    html = sorted(learn_dir.rglob("*.html"))
    return md + ipynb + html


# ---------- checks ----------------------------------------------------------

def check_manifest_inserted(learn_dir: Path, manifest: list[dict]) -> CheckResult:
    r = CheckResult(name="1. Manifest entries all inserted")
    if not manifest:
        r.failures.append("no manifest entries found at internals/exercise-plan.md")
        r.passed = False
        return r
    for entry in manifest:
        if "_parse_error" in entry:
            r.failures.append(f"manifest parse error: {entry['_parse_error']}")
            continue
        ex = entry.get("exercise", "?")
        status = entry.get("status")
        if status != "inserted":
            r.failures.append(f"exercise {ex}: status={status!r} (expected 'inserted')")
    r.passed = not r.failures
    return r


def check_no_pending_placeholders(learn_dir: Path) -> CheckResult:
    r = CheckResult(name="2. No 'pending' placeholders in curriculum.md")
    path = learn_dir / "curriculum.md"
    if not path.exists():
        r.failures.append("curriculum.md not found")
        r.passed = False
        return r
    text = path.read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = STEP_MARKER_RE.search(line)
        if not m:
            continue
        section, slug = m.group(1), m.group(2)
        if not EXERCISE_SLOT_RE.match(slug):
            continue  # only exercise slots get the "pending" treatment
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        # Pending if the line right after marker still says "pending" or is empty checkbox stub.
        if "pending" in next_line.lower():
            r.failures.append(f"{path}:{i+2}: exercise slot {section}:{slug} still pending")
    r.passed = not r.failures
    return r


def check_notebooks_exist_and_parse(learn_dir: Path, manifest: list[dict]) -> CheckResult:
    r = CheckResult(name="3. Every notebook exists and is valid nbformat")
    for entry in manifest:
        if entry.get("emission") != "notebook":
            continue
        nb_path = entry.get("notebook_path")
        if not nb_path:
            r.failures.append(f"exercise {entry.get('exercise', '?')}: emission=notebook but no notebook_path")
            continue
        full = learn_dir / nb_path
        if not full.exists():
            r.failures.append(f"missing notebook: {nb_path}")
            continue
        try:
            data = json.loads(full.read_text())
            if "cells" not in data:
                r.failures.append(f"{nb_path}: not a valid notebook (no 'cells' key)")
            elif data.get("nbformat", 0) < 4:
                r.warnings.append(f"{nb_path}: nbformat < 4")
        except json.JSONDecodeError as e:
            r.failures.append(f"{nb_path}: JSON parse error — {e}")
    r.passed = not r.failures
    return r


def check_validation_reports(learn_dir: Path, manifest: list[dict]) -> CheckResult:
    r = CheckResult(name="4. Validation reports complete and passing")
    validation_dir = learn_dir / "internals" / "validation"
    for entry in manifest:
        if entry.get("emission") != "notebook":
            continue
        ex = entry.get("exercise", "?")
        try:
            n = int(ex)
        except (TypeError, ValueError):
            r.failures.append(f"manifest entry has non-integer exercise: {ex!r}")
            continue
        report_path = validation_dir / f"exercise-{n:02d}.validation.json"
        if not report_path.exists():
            r.failures.append(f"missing validation report: {report_path.name}")
            continue
        try:
            report = json.loads(report_path.read_text())
        except json.JSONDecodeError as e:
            r.failures.append(f"{report_path.name}: JSON error — {e}")
            continue
        if report.get("validator_passed") is not True:
            r.failures.append(f"{report_path.name}: validator_passed != true")
        if report.get("nbconvert_passed") is not True:
            r.failures.append(f"{report_path.name}: nbconvert_passed != true")
    r.passed = not r.failures
    return r


def check_no_tool_fragments(learn_dir: Path) -> CheckResult:
    r = CheckResult(name="5. No tool/XML fragments in generated artifacts")
    for path in all_generated_md(learn_dir):
        text = path.read_text(errors="replace")
        for pat in TOOL_FRAGMENT_RES:
            for m in pat.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                snippet = text[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
                r.failures.append(f"{path}:{line_no}: '{m.group(0)}' near …{snippet}…")
                break  # one hit per file per pattern is enough
    r.passed = not r.failures
    return r


def check_env_manager_consistency(learn_dir: Path, config: dict) -> CheckResult:
    r = CheckResult(name="6. No alternative package managers in user-facing files")
    env_manager = (config.get("user") or {}).get("env_manager")
    if not env_manager:
        r.warnings.append(".config.json missing user.env_manager — skipping check")
        r.passed = True
        return r
    forbidden = PACKAGE_MANAGERS - {env_manager}
    for path in user_facing_files(learn_dir):
        text = path.read_text(errors="replace")
        for mgr in forbidden:
            # word-boundary match; case-insensitive
            for m in re.finditer(rf"\b{re.escape(mgr)}\b", text, re.IGNORECASE):
                line_no = text.count("\n", 0, m.start()) + 1
                # Skip false positives: "conda" inside a URL, "pip" inside "pipeline", etc.
                # Word boundary already handles "pipeline"; URLs are rare in our artifacts.
                r.failures.append(f"{path}:{line_no}: references '{mgr}' (env_manager is '{env_manager}')")
                break  # one hit per file per manager
    r.passed = not r.failures
    return r


# ---------- driver ----------------------------------------------------------

def render_result(r: CheckResult) -> str:
    icon = "PASS" if r.passed else "FAIL"
    lines = [f"[{icon}] {r.name}"]
    for w in r.warnings:
        lines.append(f"       warn: {w}")
    for f in r.failures:
        lines.append(f"       fail: {f}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile a learn/ directory")
    parser.add_argument("--learn-dir", default="learn", help="Path to learn/ directory")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    learn_dir = Path(args.learn_dir).resolve()
    if not learn_dir.is_dir():
        print(f"error: {learn_dir} is not a directory", file=sys.stderr)
        return 2

    manifest = parse_manifest(learn_dir)
    config = load_config(learn_dir)

    results = [
        check_manifest_inserted(learn_dir, manifest),
        check_no_pending_placeholders(learn_dir),
        check_notebooks_exist_and_parse(learn_dir, manifest),
        check_validation_reports(learn_dir, manifest),
        check_no_tool_fragments(learn_dir),
        check_env_manager_consistency(learn_dir, config),
    ]

    print(f"Reconciliation: {learn_dir}\n")
    for r in results:
        print(render_result(r))
        print()

    any_failed = any(not r.passed for r in results)
    any_warned = any(r.warnings for r in results)
    if any_failed:
        return 1
    if args.strict and any_warned:
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
