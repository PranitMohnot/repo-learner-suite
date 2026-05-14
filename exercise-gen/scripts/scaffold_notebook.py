#!/usr/bin/env python3
"""
scaffold_notebook.py — Generate Jupyter notebooks from structured exercise specs.

Usage:
    python scaffold_notebook.py --spec exercise_spec.json --output learn/notebooks/

Or import and call directly:
    from scaffold_notebook import generate_notebook, ExerciseSpec
    spec = ExerciseSpec(...)
    generate_notebook(spec, "output.ipynb")

The spec format is designed so Claude can construct it programmatically after
completing Stages 1-3 of the exercise-gen pipeline.
"""

import json
import re
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

try:
    import nbformat
    from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
except ImportError:
    print("nbformat not found. Installing...")
    os.system(f"{sys.executable} -m pip install nbformat --break-system-packages -q")
    import nbformat
    from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug. Strips parens, special chars, etc."""
    s = title.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)  # strip non-alphanumeric (except space/hyphen)
    s = re.sub(r'[\s]+', '-', s)          # spaces to hyphens
    s = re.sub(r'-+', '-', s)             # collapse multiple hyphens
    return s.strip('-')


@dataclass
class CellSpec:
    """A single cell in the notebook."""
    cell_type: str  # "markdown" or "code"
    source: str
    metadata: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------
# Language adapters
# ----------------------------------------------------------------------------
#
# Each supported language registers a LanguageProfile here. The profile holds
# only irreducible plumbing — things the agent cannot reasonably infer at cell-
# generation time (kernel names, env file formats, install commands).
#
# Things deliberately NOT in the profile:
#   - Validation / setup / scaffold idioms — the agent knows these from its
#     training on the language.
#   - "Self-contained" allow / deny lists — same. Telling the agent that
#     framework X is "heavy" or that library Y is "standard" is paternalizing —
#     trust the agent's training to recognize idioms per ecosystem.
#
# Adding a new language (e.g. cpp):
#   1. Implement a `write_env_files_<lang>(specs, output_dir)` function.
#   2. Add a LanguageProfile entry to LANGUAGE_PROFILES below.
#   3. Add the language to repo-learner/SKILL.md's detection table.
#   4. Add forbidden package-manager names to reconcile.py's PACKAGE_MANAGERS.
#
# When this list grows past ~3 languages, promote LANGUAGE_PROFILES to YAML
# files under `language-profiles/<name>.yaml` and load them at startup.

@dataclass(frozen=True)
class LanguageProfile:
    name: str                            # canonical, lowercase
    kernel_name: str                     # jupyter kernelspec.name
    kernel_display_name: str             # jupyter kernelspec.display_name
    kernel_language: str                 # jupyter kernelspec.language
    env_managers: dict[str, str]         # manager-name → install command snippet
    default_env_manager: str             # used when none specified

    @property
    def code_language(self) -> str:
        # Back-compat alias for older callers; same as kernel_language.
        return self.kernel_language


LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "python": LanguageProfile(
        name="python",
        kernel_name="python3",
        kernel_display_name="Python 3",
        kernel_language="python",
        env_managers={
            "uv":     "uv venv && uv sync",
            "pip":    "python -m venv .venv && source .venv/bin/activate\npip install -r requirements.txt",
            "poetry": "poetry install",
            "conda":  "conda env create -f environment.yml && conda activate learn",
        },
        default_env_manager="pip",
    ),
    # To add a new language: see the "Adding a new language" comment block
    # above. The contract is intentionally tiny — register a profile here,
    # add a generator branch in generate_env_files, add forbidden managers
    # to reconcile.py, and add a detection row in repo-learner/SKILL.md.
}


@dataclass
class ExerciseSpec:
    """Full specification for one exercise notebook."""
    number: int
    title: str
    goal: str
    exercise_type: str  # use | modify | create | debug | compare
    curriculum_section: str = ""  # e.g. "1.1" — maps to curriculum
    prerequisites: list[str] = field(default_factory=list)
    estimated_minutes: int = 20
    setup_code: str = ""
    guided_cells: list[CellSpec] = field(default_factory=list)
    task_description: str = ""
    scaffold_code: str = ""
    validation_code: str = ""
    stretch_goal: Optional[str] = None
    solution_code: str = ""
    solution_explanation: str = ""
    dependencies: list[str] = field(default_factory=list)  # pkg names
    language: str = "python"                # see LANGUAGE_PROFILES
    kernel_name: str = ""                   # blank → derived from language
    kernel_display_name: str = ""           # blank → derived from language

    def resolved_kernel(self) -> tuple[str, str, str]:
        """Returns (kernel_name, kernel_display_name, code_language)."""
        p = LANGUAGE_PROFILES.get(self.language, LANGUAGE_PROFILES["python"])
        return (
            self.kernel_name or p.kernel_name,
            self.kernel_display_name or p.kernel_display_name,
            p.kernel_language,
        )


def generate_notebook(spec: ExerciseSpec, output_path: str) -> str:
    """Generate a .ipynb file from an ExerciseSpec. Returns the output path."""
    nb = new_notebook()
    kname, kdisplay, clang = spec.resolved_kernel()
    nb.metadata.kernelspec = {
        "display_name": kdisplay,
        "language": clang,
        "name": kname,
    }

    # Title and context
    context_text = ""
    if spec.curriculum_section:
        sec = spec.curriculum_section
        context_text = (
            f"\n\n**Context:** Companion to "
            f"[curriculum.md §{sec}](../curriculum.md#s{sec})."
        )
    prereq_text = ""
    if spec.prerequisites:
        prereq_links = ", ".join(spec.prerequisites)
        prereq_text = f"\n\n**Prerequisites:** {prereq_links}"

    # Each cell gets a `role:<name>` tag in metadata so check_executed_notebook.py
    # can classify outcomes (env-health check after nbconvert --execute).
    def _tag(cell, role):
        tags = cell.metadata.setdefault("tags", [])
        tags.append(f"role:{role}")
        return cell

    nb.cells.append(_tag(new_markdown_cell(
        f"# Exercise {spec.number}: {spec.title}\n\n"
        f"**Goal:** {spec.goal}\n\n"
        f"**Type:** {spec.exercise_type} · "
        f"**Estimated time:** ~{spec.estimated_minutes} minutes"
        f"{context_text}"
        f"{prereq_text}"
    ), "title"))

    # Setup cell
    if spec.setup_code:
        nb.cells.append(_tag(new_markdown_cell("## Setup\n\nRun this cell first to load dependencies."), "setup-header"))
        nb.cells.append(_tag(new_code_cell(spec.setup_code), "setup"))

    # Guided walkthrough cells — no synthetic "Walkthrough" header; the spec's
    # own markdown cells frame the narrative against curriculum.md context.
    for cell_spec in spec.guided_cells:
        if cell_spec.cell_type == "markdown":
            nb.cells.append(_tag(new_markdown_cell(cell_spec.source), "guided-md"))
        else:
            nb.cells.append(_tag(new_code_cell(cell_spec.source), "guided-code"))

    # Task description
    nb.cells.append(_tag(new_markdown_cell(
        f"## Your turn\n\n{spec.task_description}"
    ), "your-turn"))

    # Scaffold cell
    if spec.scaffold_code:
        nb.cells.append(_tag(new_code_cell(spec.scaffold_code), "scaffold"))

    # Validation cell
    if spec.validation_code:
        nb.cells.append(_tag(new_markdown_cell(
            "## Check your work\n\nRun the cell below to validate your solution."
        ), "validation-header"))
        nb.cells.append(_tag(new_code_cell(spec.validation_code), "validation"))

    # Stretch goal
    if spec.stretch_goal:
        nb.cells.append(_tag(new_markdown_cell(
            f"## Stretch goal (optional)\n\n{spec.stretch_goal}"
        ), "stretch-header"))
        nb.cells.append(_tag(new_code_cell("# Your stretch goal code here\n"), "stretch"))

    # Solution stays as a runnable code cell. source_hidden collapses it in
    # JupyterLab; VS Code and classic Jupyter show it expanded. Acceptable
    # trade-off — solutions must be runnable. See suite TODO.md for the
    # cross-viewer collapse question.
    if spec.solution_code:
        nb.cells.append(_tag(new_markdown_cell(
            "---\n\n## Solution\n\nTry the exercise before expanding."
        ), "solution-header"))
        solution_cell = _tag(new_code_cell(spec.solution_code), "solution")
        solution_cell.metadata["jupyter"] = {"source_hidden": True}
        nb.cells.append(solution_cell)

        if spec.solution_explanation:
            explanation_cell = _tag(new_markdown_cell(spec.solution_explanation), "solution-explanation")
            explanation_cell.metadata["jupyter"] = {"source_hidden": True}
            nb.cells.append(explanation_cell)

    # Write the notebook
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    return str(output)


def emit_validation_stub(spec: ExerciseSpec, validation_dir: str) -> str:
    """Write an empty validation_report.json for this exercise.

    The reconciliation pass refuses to declare pipeline "done" until both
    validator_passed and nbconvert_passed are true. Emitting the stub at
    scaffold time ensures the file exists for reconciliation to inspect even
    if a validation channel crashed.
    """
    report = {
        "exercise": f"{spec.number:02d}",
        "title": spec.title,
        "curriculum_section": spec.curriculum_section,
        "validator_passed": None,
        "nbconvert_passed": None,
        "validator_report": None,
        "nbconvert_log": None,
    }
    out = Path(validation_dir) / f"exercise-{spec.number:02d}.validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    return str(out)


def generate_env_files(
    specs: list[ExerciseSpec],
    output_dir: Path,
    language: str = "python",
    project_name: str = "learn-exercises",
    repo_root: Optional[Path] = None,
    repo_name: Optional[str] = None,
) -> list[str]:
    """Generate language-appropriate environment files.

    Python: writes requirements.txt + pyproject.toml. Includes the host
    repo as an editable local install (without it, `import <repo>` from
    a setup cell fails with ModuleNotFoundError).

    To add a new language: add a branch here that writes the language's
    env file(s) and returns their paths. See the "Adding a new language"
    comment block at the top of this module.

    Args:
        repo_root: Path to the host repo being learned. If None, defaults
            to `output_dir.parent.parent` (i.e. learn/notebooks/ → repo root).
            Pass explicitly if the layout differs.
        repo_name: Importable name of the host repo. If None, derived from
            repo_root's basename. Used as the [tool.uv.sources] key and
            should match what the notebooks `import`.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    all_deps = sorted({d for s in specs for d in s.dependencies})

    # Resolve the host repo (the thing being learned). Default layout:
    # <repo>/learn[_test]/notebooks/, so up two levels.
    if repo_root is None:
        repo_root = output_dir.parent.parent
    repo_root = Path(repo_root).resolve()
    if repo_name is None:
        repo_name = repo_root.name
    # Relative path from output_dir (where the env files live) to repo_root.
    rel_to_repo = os.path.relpath(repo_root, output_dir.resolve())

    # Python (default)
    py_deps = set(all_deps) | {"jupyter", "nbformat"}
    req_lines = sorted(py_deps)
    # Editable install of the host repo so `import <repo_name>` works.
    req_lines.append(f"-e {rel_to_repo}")
    req_path = output_dir / "requirements.txt"
    req_path.write_text("\n".join(req_lines) + "\n")
    written.append(str(req_path))

    deps_str = ", ".join(f'"{d}"' for d in sorted(py_deps))
    pyproj = (
        f'[project]\n'
        f'name = "{project_name}"\n'
        f'version = "0.1.0"\n'
        f'description = "Exercise notebooks for learning the codebase"\n'
        f'requires-python = ">=3.10"\n'
        f'dependencies = [{deps_str}, "{repo_name}"]\n'
        f'\n'
        f'[tool.uv.sources]\n'
        f'{repo_name} = {{ path = "{rel_to_repo}", editable = true }}\n'
    )
    pyproj_path = output_dir / "pyproject.toml"
    pyproj_path.write_text(pyproj)
    written.append(str(pyproj_path))
    return written


def generate_readme(
    specs: list[ExerciseSpec],
    output_path: str,
    env_manager: str = "pip",
    kernel_name: str = "python3",
    language: str = "python",
) -> str:
    """Generate README.md with exercise sequence + setup instructions.

    Only references the user's chosen env_manager. Never lists alternatives —
    the .config.json env_manager is the source of truth.
    """
    profile = LANGUAGE_PROFILES.get(language, LANGUAGE_PROFILES["python"])
    install_cmd = profile.env_managers.get(env_manager) or profile.env_managers[profile.default_env_manager]

    # Python kernel registration hint. Other languages (when added) should
    # branch here and supply their own one-time-setup hint.
    # Using `uv run` (or analog) ensures the kernel is registered against the
    # notebooks/ venv, not the user's global Python.
    display_name = f"Learn {kernel_name.removeprefix('learn-')}" if kernel_name.startswith("learn-") else kernel_name
    if env_manager == "uv":
        kernel_register = f"uv run python -m ipykernel install --user --name={kernel_name} --display-name=\"{display_name}\""
    else:
        kernel_register = f"python -m ipykernel install --user --name={kernel_name} --display-name=\"{display_name}\""

    setup_block = (
        "```bash\n"
        f"{install_cmd}\n"
        "\n"
        f"# Register the notebooks' venv as a Jupyter kernel (one-time):\n"
        f"{kernel_register}\n"
        "```\n"
        f"\n"
        f"Then pick **\"{display_name}\"** from your editor's kernel picker. "
        f"In JupyterLab it shows up automatically; in VS Code, reload the "
        f"notebook view after registering.\n"
    )

    lines = [
        "# Exercises\n",
        "Work through these notebooks in order. Each one builds on the previous.\n",
        "## Setup\n",
        setup_block,
        "## Exercise Sequence\n",
        "| # | Title | Type | Time | Goal |",
        "|---|-------|------|------|------|",
    ]

    for spec in sorted(specs, key=lambda s: s.number):
        filename = f"exercise-{spec.number:02d}-{slugify(spec.title)}.ipynb"
        lines.append(
            f"| {spec.number} | [{spec.title}]({filename}) | "
            f"{spec.exercise_type} | ~{spec.estimated_minutes}min | {spec.goal} |"
        )

    total_time = sum(s.estimated_minutes for s in specs)
    lines.append(f"\n**Total estimated time:** ~{total_time} minutes\n")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        f.write("\n".join(lines))

    return str(output)


def from_json(spec_path: str) -> list[ExerciseSpec]:
    """Load exercise specs from a JSON file."""
    with open(spec_path) as f:
        data = json.load(f)

    specs = []
    for item in data["exercises"]:
        guided = [
            CellSpec(
                cell_type=c["cell_type"],
                source=c["source"],
                metadata=c.get("metadata", {})
            )
            for c in item.get("guided_cells", [])
        ]
        specs.append(ExerciseSpec(
            number=item["number"],
            title=item["title"],
            goal=item["goal"],
            exercise_type=item["exercise_type"],
            curriculum_section=item.get("curriculum_section", ""),
            prerequisites=item.get("prerequisites", []),
            estimated_minutes=item.get("estimated_minutes", 20),
            setup_code=item.get("setup_code", ""),
            guided_cells=guided,
            task_description=item.get("task_description", ""),
            scaffold_code=item.get("scaffold_code", ""),
            validation_code=item.get("validation_code", ""),
            stretch_goal=item.get("stretch_goal"),
            solution_code=item.get("solution_code", ""),
            solution_explanation=item.get("solution_explanation", ""),
            dependencies=item.get("dependencies", []),
            language=item.get("language", "python"),
            kernel_name=item.get("kernel_name", ""),
            kernel_display_name=item.get("kernel_display_name", ""),
        ))

    return specs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate exercise notebooks from specs")
    parser.add_argument("--spec", required=True, help="Path to exercise spec JSON")
    parser.add_argument("--output", required=True, help="Output directory for notebooks (learn/notebooks/)")
    parser.add_argument("--validation-dir", help="Directory for validation_report.json stubs (default: ../internals/validation/)")
    parser.add_argument("--language", default="python", choices=list(LANGUAGE_PROFILES),
                        help="Notebook language (default: python). Individual specs can override.")
    parser.add_argument("--env-manager", default="",
                        help="Package manager for the notebooks/ README. Defaults per language.")
    parser.add_argument("--kernel-name", default="",
                        help="Override Jupyter kernel name. Default: 'learn-<repo>' (e.g. learn-frax).")
    parser.add_argument("--kernel-display-name", default="",
                        help="Override Jupyter kernel display name. Default: 'Learn <Repo>'.")
    parser.add_argument("--repo-root", default="",
                        help="Path to the host repo being learned. Default: <output>/../..")
    parser.add_argument("--repo-name", default="",
                        help="Importable name of the host repo. Default: <repo_root>.name.")
    args = parser.parse_args()

    specs = from_json(args.spec)
    output_dir = Path(args.output)
    validation_dir = Path(args.validation_dir) if args.validation_dir else output_dir.parent / "internals" / "validation"

    profile = LANGUAGE_PROFILES[args.language]
    if not args.env_manager:
        args.env_manager = profile.default_env_manager

    # Resolve repo identity once (env files, kernelspec name, README all need it).
    repo_root = Path(args.repo_root).resolve() if args.repo_root else output_dir.parent.parent.resolve()
    repo_name = args.repo_name or repo_root.name

    # Derive kernel name/display from repo identity (per-project, no clash with
    # the system default "python3" kernel). Override with CLI flag if needed.
    if not args.kernel_name:
        # For Python, name the kernel after the repo so each project gets its
        # own registered kernel. For non-Python langs, use the language default
        # (kernels there aren't typically per-project).
        args.kernel_name = f"learn-{slugify(repo_name)}" if args.language == "python" else profile.kernel_name
    if not args.kernel_display_name:
        args.kernel_display_name = f"Learn {repo_name}" if args.language == "python" else profile.kernel_display_name

    # Apply the run-wide language + kernel name to any specs that left them blank.
    for spec in specs:
        if not spec.language:
            spec.language = args.language
        if not spec.kernel_name:
            spec.kernel_name = args.kernel_name
        if not spec.kernel_display_name:
            spec.kernel_display_name = args.kernel_display_name

    for spec in specs:
        filename = f"exercise-{spec.number:02d}-{slugify(spec.title)}.ipynb"
        path = generate_notebook(spec, output_dir / filename)
        stub = emit_validation_stub(spec, validation_dir)
        print(f"Generated: {path}")
        print(f"  Stub:    {stub}")

    generate_env_files(specs, output_dir, language=args.language, repo_root=repo_root, repo_name=repo_name)
    generate_readme(
        specs, output_dir / "README.md",
        env_manager=args.env_manager,
        kernel_name=args.kernel_name,
        language=args.language,
    )
    print(f"\nGenerated {len(specs)} notebooks in {output_dir}/ ({args.language})")
    print(f"Kernel name: {args.kernel_name}  (register with: uv run python -m ipykernel install --user --name={args.kernel_name} --display-name='{args.kernel_display_name}')")
