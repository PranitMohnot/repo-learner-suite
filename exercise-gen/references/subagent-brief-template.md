# Subagent Brief Template

This is the shared brief for per-notebook generation subagents during Stage
4a fan-out. The main exercise-gen agent dispatches one subagent per notebook
when count > 4. Each subagent receives this template **plus one exercise
spec** — nothing else of the parent's context.

Below is the brief to send. Substitute the placeholders with concrete values
from `learn/internals/.config.json` and the target spec before dispatching.

---

## Brief

You are generating exactly ONE Jupyter notebook for the
`{{ project_name }}` codebase. The notebook teaches one exercise. Your only
output artifact is the `.ipynb` file at the path specified in the spec.

### Inputs you receive

1. This brief.
2. One exercise spec (manifest entry + notebook-structure plan) at the
   bottom of your prompt.

### Your task

Construct an `ExerciseSpec` Python object matching the spec, then call
`exercise_gen.scripts.scaffold_notebook.generate_notebook(spec, output_path)`.
The script handles JSON formatting, cell metadata, and file write.

### Notebook cell sequence

```
1. Title + curriculum back-link (markdown)
2. Setup (code) — imports, fixtures, helpers; runs without error
3. Walkthrough (alternating markdown + code, 2–4 cells)
   — code cells are COMPLETE and RUNNABLE, not scaffolded
   — include print/display so output is visible
   — do not re-explain concepts from curriculum.md; link back to §{{ section }}
4. "Your turn" (markdown) — specific, unambiguous task
5. Scaffold (code) — signature + type hints + TODO comments
   — TODOs say WHAT, not HOW
   — stubs return None or raise NotImplementedError
6. Validation (code) — 3+ test cases (basic, edge, non-trivial)
   — descriptive assertion messages
   — final line: print("All tests passed.")
7. Stretch goal (markdown, optional) — harder extension, no scaffold
8. Solution (code, source_hidden) — runnable, complete
9. Solution explanation (markdown, source_hidden, optional)
```

### Hard constraints

- **Self-contained.** Notebook runs with ONLY `{{ library_name }}` + numpy,
  matplotlib, scipy. No PyBullet, MuJoCo, pygame, Isaac, or other sim envs.
  No GUI frameworks. If a working example needs sim, synthesize state in-
  notebook or run Euler integration with matplotlib plots.
- **Self-contained imports.** Every import the notebook uses appears in
  the setup cell.
- **Filename slugging.** `learn/notebooks/exercise-{NN}-{slug}.ipynb`. No
  parens, no special chars, no spaces.
- **No tool fragments.** Your output is the notebook only. Do not leak
  `<parameter>`, `<antml`, `<function`, or any other tool-call XML into
  cell content.
- **Package manager.** If the notebook references install commands, use
  only `{{ env_manager }}`. Never mention alternatives.
- **Scaffold parses.** The scaffold cell must be valid Python syntax even
  with stubs.
- **Validation passes against the solution.** If your validation cell
  asserts something the solution doesn't satisfy, fix one or the other.

### Quality bar

- Early exercises ("use" type) should be completable from the walkthrough
  alone. If the walkthrough doesn't teach enough, expand it.
- Ambiguity is a bug; difficulty is the point. Instructions must be
  specific.
- Plot anything that can be plotted (trajectories, distributions, images).
  A plot is worth a thousand assertions for intuition.

### Output

Write the `.ipynb` to the path in the spec. Report back the path and a
one-line summary ("Generated exercise-NN-title.ipynb — N cells.").
Validation, insertion, and manifest updates are NOT your job — the main
agent handles those after collecting all subagents' notebooks.

---

## Substitution variables

- `{{ project_name }}` — from `.config.json:repo.name`
- `{{ library_name }}` — typically same as project_name
- `{{ section }}` — the spec's `section` field, e.g. "1.3"
- `{{ env_manager }}` — from `.config.json:user.env_manager`

## What goes at the bottom of the subagent prompt

The single exercise spec as YAML (the manifest entry) followed by the
notebook-structure plan from Stage 3. Nothing more.
