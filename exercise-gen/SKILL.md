---
name: exercise-gen
description: >
  Generate Jupyter notebook exercises from a codebase analysis. Produces scaffolded,
  runnable notebooks that teach a library or codebase through hands-on exercises with
  progressive difficulty. Trigger on "generate exercises", "make me notebooks", "create
  practice problems", "build exercises for this repo", "/learn exercises", or any request
  to create hands-on learning materials from a codebase. Also trigger when the user has
  a curriculum.md and wants exercises generated for specific sections. This skill pairs
  with repo-analyzer (which produces the curriculum) but can also run standalone if
  pointed at a codebase directly.
---

# Exercise Generator

Produce scaffolded Jupyter notebooks that teach a codebase through hands-on exercises.
Each notebook is self-contained, runnable, and progresses from guided usage through
independent creation.

This skill follows a 4-stage pipeline: candidate mining → selection → scaffolding →
generation+validation. Do not skip stages — the quality of exercises depends on careful
candidate selection before any code is generated.

Read `references/exercise-types.md` before starting. It defines the exercise taxonomy
and when to use each type.

## Pipeline

### Stage 1: Candidate Mining

Scan the codebase to identify "exercisable surfaces" — places where a learner can
do something concrete that builds understanding.

**What to scan for:**

1. **Public API functions with clear I/O.** Functions where the user passes something
   in and gets something interpretable back. These are natural "use it" exercises.
   - Look at: top-level exports, `__init__.py` re-exports, documented API functions
   - Skip: internal helpers, underscore-prefixed, trivially thin wrappers

2. **Configuration and setup patterns.** How do you initialize this thing? What knobs
   does it expose? These become "set up and configure" exercises.
   - Look at: constructors, `from_config()` patterns, environment variables, YAML/JSON schemas
   - Focus on: the configs that actually change behavior in interesting ways

3. **Extension points.** Subclass this, register that, implement this interface. These
   are the best exercises because they force the learner to understand the abstraction.
   - Look at: abstract base classes, plugin/registry patterns, callback hooks, middleware
   - Rank by: how much the learner has to understand to extend correctly

4. **Workflows visible in examples/tests.** The authors already wrote the exercises —
   they just called them "examples" or "tests."
   - Look at: `examples/`, `demos/`, tutorial notebooks, test files (especially integration tests)
   - Extract: the workflow pattern, strip it to a skeleton, turn it into an exercise

5. **Error-handling paths and common mistakes.** Things people get wrong. These become
   "debug this" exercises.
   - Look at: GitHub issues (if accessible), error messages, validation logic, edge cases in tests
   - Focus on: errors that teach something about the design, not just typo-level bugs

6. **Comparison points.** Places where there are two ways to do something. These become
   "compare approaches" exercises.
   - Look at: deprecated-vs-new API, verbose-vs-shortcut, different backends/strategies

**Output of Stage 1:** A candidate list saved to `learn/internals/exercise-candidates.md`.
For each candidate:

```markdown
### Candidate: [short name]
- **Surface:** [which file/function/class]
- **Type:** use | modify | create | debug | compare
- **Exercises:** [what the learner would do — 1-2 sentences]
- **Concepts tested:** [what they need to understand]
- **Dependencies:** [what they need to know first — other candidates or curriculum sections]
- **Difficulty:** beginner | intermediate | advanced
- **Confidence:** high | medium | low (how sure are you this makes a good exercise?)
```

Aim for 20-40 candidates. Cast a wide net — Stage 2 filters.

### Stage 2: Selection and Ordering

Select 8-15 exercises from the candidates and sequence them. This is where pedagogy
matters most.

**Selection criteria (in priority order):**

1. **Forces active understanding.** The learner must think, not just copy. Reject exercises
   where the answer is "paste the example and change one variable."

2. **Builds on previous exercises.** Each exercise should reuse or extend something from
   an earlier one. Isolated exercises don't build cumulative understanding.

3. **Covers the important surfaces.** The exercise set should span the library's key
   capabilities. Don't write 5 exercises about config and 0 about the core API.

4. **Mix of exercise types.** Don't make them all "use" exercises. The progression should
   ramp naturally:
   - Start with 2-3 "use" exercises (call the API, see what it does)
   - Then 2-3 "modify" exercises (change behavior, predict effects)
   - Then 1-2 "debug" exercises (find and fix conceptual bugs)
   - Then 1-2 "create" exercises (build something new)
   - Optionally 1 "compare" exercise (two approaches, evaluate tradeoffs)

5. **Each exercise earns its place.** If you can't articulate what NEW understanding the
   exercise produces (beyond what the previous ones already covered), cut it.

**Ordering rules:**
- Prerequisites before dependents (topological sort on dependencies)
- Simpler before complex
- Core API before extensions
- Happy path before error handling
- If a curriculum.md exists, align exercises with curriculum sections — each exercise
  should map to one or more sections. Skip curriculum sections that don't admit
  hands-on exercises. This alignment lets the README.md path table have natural
  Read/Do/Test columns per row.

**Output of Stage 2:** An exercise plan saved to `learn/internals/exercise-plan.md`:

```markdown
# Exercise Plan

## Exercise 1: [Title]
- **Type:** use
- **Curriculum section:** 1.1
- **Goal:** [one sentence — what can the learner do after this]
- **Builds on:** nothing (first exercise)
- **Notebook structure:**
  - Intro: [what this exercise covers and why]
  - Setup: [imports, data prep]
  - Guided step 1: [description]
  - Guided step 2: [description]
  - Your turn: [the actual task]
  - Validation: [how to check their answer]
  - Stretch goal: [optional harder extension]

## Exercise 2: [Title]
...
```

**Output of Stage 2:** An exercise plan saved to `learn/internals/exercise-plan.md`.
Plan flows directly into Stage 3 — no user checkpoint. The front-loaded questions
at pipeline start replace this.

### Stage 3: Notebook Scaffolding

For each exercise in the plan, design the cell-by-cell structure. This is the blueprint
that Stage 4 turns into actual .ipynb files.

**Notebook structure (every exercise follows this pattern):**

```
Cell 1 [markdown]: Title + context
  - Exercise number and name
  - One paragraph: what you'll learn and why it matters
  - Prerequisites (link to earlier notebooks if any)

Cell 2 [code]: Setup
  - Imports
  - Data loading / fixture creation
  - Any helper functions the learner needs but shouldn't have to write
  - This cell should run without error as-is

Cell 3+ [markdown + code]: Guided walkthrough (2-4 cells)
  - Alternate markdown (explanation) and code (working example)
  - The code cells are COMPLETE and RUNNABLE — not scaffolded
  - The learner reads and runs these to build context
  - Include print() or display() calls so output is visible

Cell N [markdown]: "Your turn"
  - Clear task description
  - Specific, unambiguous — not "explore the API" but "write a function that..."
  - Expected output format described

Cell N+1 [code]: Scaffold
  - Function signature with docstring
  - TODO comments marking where to fill in
  - Type hints on parameters and return
  - Enough structure that the learner knows the shape of the answer

Cell N+2 [code]: Validation
  - Assertions that check the learner's code works
  - Clear error messages on failure: "Expected X, got Y"
  - Test multiple cases including edge cases
  - Print success message when all pass

Cell N+3 [markdown]: Stretch goal (optional)
  - A harder extension for learners who finish early
  - No scaffold — just the task description

Cell N+4 [code]: Solution (collapsed)
  - Complete working solution
  - Comments explaining WHY, not just WHAT
  - Use notebook metadata to collapse: "jupyter": {"source_hidden": true}
  - Preceded by a markdown cell: "Expand to see solution (try first!)"
```

**Rules for scaffold cells:**
- The scaffold must PARSE. Stub functions return `None` or `raise NotImplementedError`.
- Include type hints — they're documentation.
- TODO comments say WHAT to do, not HOW: `# TODO: Filter items where score > threshold`
  not `# TODO: Use list comprehension with if clause`
- Don't scaffold too much. Leave room for the learner to make structural decisions.
- Don't scaffold too little. The learner should know what function to write and what it
  should return.

**Rules for validation cells:**
- Test at least 3 cases: basic, edge, and non-trivial
- Assertions should have descriptive messages
- Always `print("✓ All tests passed!")` at the end
- If the exercise produces a plot or visualization, include a visual check too

### Stage 4: Generation and Validation

Use the `scripts/scaffold_notebook.py` script to generate .ipynb files from structured
JSON exercise specs. Notebooks aren't "done" until each one passes Haiku validation.

**Subagent fan-out (when exercise count > ~6-8):** Each subagent gets the exercise plan
+ shared code snippets + one exercise spec; produces one notebook. Main agent runs a
stitcher pass after: dedupes setup code, verifies cross-references, lints filenames.
Below the threshold, generate sequentially. This is automatic — not user-facing.

For each exercise in the plan:

1. Construct the exercise spec as a Python dict/JSON following the schema in the script
2. Call the script or use `nbformat` directly to produce the .ipynb
3. Save to `learn/notebooks/exercise-XX-title.ipynb` (slug-stripped filename — no parens,
   no special chars)

**Haiku validation (part of this stage's contract):**

After generating each notebook, spawn a Haiku subagent as a simulated student:

```
You are a student learning a new codebase. You have access to ONLY the information
in this notebook — no prior knowledge of the library. Work through the notebook:

1. Run the setup cell. Report any import errors or missing dependencies.
2. Read and run each guided walkthrough cell. Note anything confusing.
3. Read the "Your turn" task description. Attempt the exercise using ONLY
   what the walkthrough taught you. Do NOT look at the solution.
4. Run the validation cell against your attempt. Report pass/fail.
5. If you got stuck, explain exactly WHERE and WHY — what information was
   missing or ambiguous?

Output a JSON report:
{
  "exercise": "<title>",
  "setup_runs": true/false,
  "guided_cells_run": true/false,
  "could_complete_without_solution": true/false,
  "validation_passed": true/false,
  "stuck_points": ["<description of where/why>"],
  "ambiguities": ["<unclear instructions>"],
  "missing_info": ["<concepts needed but not taught in walkthrough>"],
  "solution_matches": true/false
}
```

**What to fix based on Haiku's report:**

- `setup_runs: false` → Fix imports, dependencies, or data paths. Hard blocker.
- `could_complete_without_solution: false` → Walkthrough gap or ambiguous task. Fix it.
- `validation_passed: false` (but Haiku's approach was reasonable) → Loosen assertions.
- `stuck_points` → Fix missing info (a) and ambiguity (b). Leave genuine difficulty (c).
- `solution_matches: false` → Solution is wrong. Fix it.

If a notebook fails validation with the provided solution, do not deliver it. If Haiku
can't complete it but the solution works, review whether the gap is intentional difficulty
or accidental omission.

This is internal QA — the user doesn't see Haiku's reports. Apply fixes silently. Only
surface details if an exercise had to be cut entirely.

**After all notebooks pass validation:**

Detect the parent repo's package manager from lockfiles and lead with that:

- Generate `learn/notebooks/requirements.txt` (always)
- Generate `learn/notebooks/pyproject.toml` (always — minimal, with the exercise deps)
- `learn/notebooks/README.md` documenting both `uv sync` and `pip install -r requirements.txt`
  paths, with the detected manager first

## Quality Checklist

After Haiku validation and fixes, confirm:

- [ ] Every setup cell runs without error
- [ ] Every guided example cell runs and produces visible output
- [ ] Scaffold cells parse without syntax errors
- [ ] Validation cells pass when given the solution
- [ ] The early exercises (the "use" type ones) are completable from the walkthrough
      alone — if the walkthrough doesn't teach enough to complete them, it's broken
- [ ] Exercise order has no forward dependencies
- [ ] Each notebook is self-contained
- [ ] Instructions are specific enough that ambiguity doesn't cause failure
      (actual difficulty is fine — that's the point)
