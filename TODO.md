# repo-learner-suite — Long-term TODOs

Internal wishlist. Not user-facing. Move items into GitHub issues when work
starts on them.

## Notebook UX

### Cross-viewer collapse for runnable solution cells

**Problem:** `cell.metadata.jupyter.source_hidden = True` collapses code cells
in JupyterLab but not in VS Code or classic Jupyter Notebook. Solutions show
expanded in those viewers, defeating the "try first, then peek" intent.

**Current state:** We accept this. Solutions stay as runnable code cells with
`source_hidden` set; users on VS Code see them expanded. notebooks/README.md
recommends JupyterLab for the intended experience.

**Constraints:**
- Solutions MUST be runnable. Wrapping the code in a `<details>` markdown
  block (the obvious fix for collapse) makes them non-runnable.
- Hints can be markdown `<details>` — non-runnable is fine for hints.

**Possible directions:**
- A "Solutions" sidecar notebook that gets opened separately?
- A JupyterLab extension shipped with the suite?
- Wait for VS Code to respect `jupyter.source_hidden`?
- A pre-cell that hides the next cell via JS (fragile, viewer-dependent)?

## Inline → notebook migration

**Goal:** Eventually every exercise is a notebook. `emission: inline` exists
only as a transitional convenience for `compare` exercises and short copy-
paste-run blocks.

**Why:** Notebooks give structure (setup, scaffold, validation, solution,
hints), versioning, kernel state, and a uniform UX. Inline blocks fragment
this.

**What's blocking full notebook-only:**
- `compare` exercises with side-by-side prose are awkward in notebook form.
- Very short "run this and observe" steps feel heavy as a full notebook.

**Possible directions:**
- A "compare" notebook template with two parallel scaffold sections.
- A "micro-notebook" emission with just title + one code cell.
- Decide it's not worth it and keep inline as a stable category.

## Curriculum.html — offline mode

Currently loads marked.js from a CDN. Works fine online; breaks for users
without internet. Options: vendor marked.min.js (~30 KB) into the suite and
inline it at build time, or write a minimal Python-side markdown renderer
and emit pre-rendered HTML. Decide before shipping more widely.

## Re-dogfood across domains

Re-run the full pipeline on 2–3 repos from different domains to verify the
curriculum-as-single-doc shape generalizes. Good candidates: a small web
framework (Flask/FastAPI app), a data-pipeline library, a CLI tool
(click/typer-based), and one heavier framework (pandas, sqlalchemy). Avoid
re-running on the same domain twice — the goal is to catch shape biases
that one dogfood couldn't.

## Executed-notebook role-classifier helper

After `nbconvert --execute --allow-errors`, Stage 4d requires inspecting
each cell's output to confirm setup + guided cells succeeded and only
scaffold + validation cells errored. Currently the agent walks the
notebook JSON by hand each time. This is exactly where a regression
could slip back in (e.g. the original `--allow-errors` bug).

A small helper (e.g. `exercise-gen/scripts/check_executed_notebook.py`)
would take the executed `.ipynb`, classify each cell by role (using
ordinal or tags added at scaffold time), and emit a structured per-cell
verdict the agent can drop straight into `validator_report`. Surfaced by
the frax dogfood; not yet blocking.
