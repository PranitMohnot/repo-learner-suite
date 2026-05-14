---
name: exercise-gen
description: >
  Generate Jupyter notebook exercises from a codebase analysis. Reads the
  manifest at learn/internals/exercise-plan.md, scaffolds notebooks (or short
  inline blocks where the manifest says so), runs MANDATORY Haiku + nbconvert
  validation, then inserts links into learn/curriculum.md at the step markers
  the analyzer placed. Trigger on "generate exercises", "make me notebooks",
  "create practice problems", "build exercises for this repo",
  "/learn exercises", or any request to create hands-on learning materials
  from a codebase. Pairs with repo-analyzer (which produces the manifest)
  but can run standalone if pointed at a codebase directly — in that case it
  writes the manifest itself.
---

# Exercise Generator

Produce scaffolded Jupyter notebooks that teach a codebase through hands-on
exercises. Each notebook is self-contained, runnable on its own, and
progresses from guided usage through independent creation.

This skill is **manifest-driven**. The manifest at
`learn/internals/exercise-plan.md` is the source of truth for which exercises
exist, where they slot into curriculum.md, and how each is rendered. Read the
Shared Contracts in `repo-learner/SKILL.md` before starting.

Read `references/exercise-types.md` for the exercise taxonomy (use / modify /
debug / create / compare) and when to use each. Read
`references/subagent-brief-template.md` before fanning out to subagents.

## Notebook-first, with narrow inline exceptions

Default emission is `.ipynb`. Two narrow exceptions allowed:

1. **`compare` exercises** — table or side-by-side prose comparisons fit
   naturally inline.
2. **Short copy-paste-run blocks** — fewer than ~15 lines, no scaffold, no
   validation, no solution. Pure "run this and observe."

Everything else is a notebook. The long-term direction is "everything becomes
a notebook" — treat inline as an exception you should be reluctant to use,
not a co-equal option.

## Pipeline

Stages 1–2 produce the manifest (if it doesn't already exist). Stages 3–5
consume it.

### Stage 1: Candidate Mining

Scan the codebase to identify "exercisable surfaces" — places where a learner
can do something concrete that builds understanding.

**What to scan for:**

1. **Public API functions with clear I/O.** Natural "use" exercises.
2. **Configuration and setup patterns.** "Set up and configure" exercises.
3. **Extension points.** Subclass / register / implement — the best
   exercises, because they force understanding of the abstraction.
4. **Workflows visible in examples/tests.** The authors already wrote these
   — extract the pattern, strip to skeleton.
5. **Error-handling paths and common mistakes.** "Debug" exercises.
6. **Comparison points.** Two ways to do the same thing → "compare"
   exercises.

**Output:** `learn/internals/exercise-candidates.md`. Per candidate:

```markdown
### Candidate: [short name]
- **Surface:** [which file/function/class]
- **Type:** use | modify | create | debug | compare
- **Exercises:** [what the learner would do — 1-2 sentences]
- **Concepts tested:** [what they need to understand]
- **Dependencies:** [prerequisite candidates or curriculum sections]
- **Difficulty:** beginner | intermediate | advanced
- **Confidence:** high | medium | low
```

**Aim for 12–18 candidates.** Pre-filter during mining — skip candidates
that obviously don't teach anything new. Cast a focused net, not a wide one.

### Stage 2: Selection, Ordering, and Manifest Emission

Select 8–12 exercises from the candidates and sequence them.

**Selection criteria (priority order):**

1. **Forces active understanding.** The learner must think, not just copy.
2. **Builds on previous exercises.** Cumulative understanding.
3. **Covers the important surfaces.** Span the library's key capabilities.
4. **Mix of exercise types.** Progression ramps naturally (use → modify →
   debug → create → optional compare).
5. **Each exercise earns its place.** If you can't articulate what NEW
   understanding it produces beyond the previous ones, cut it.

**Ordering rules:**
- Prerequisites before dependents.
- Simpler before complex.
- Core API before extensions.
- Happy path before error handling.
- Align with curriculum sections: each exercise maps to one or more
  sections. Skip curriculum sections that don't admit hands-on exercises.

**Output: the manifest at `learn/internals/exercise-plan.md`.** See the
Shared Contracts in `repo-learner/SKILL.md` for the schema. Each exercise
entry is a markdown section with a yaml code fence at the top.

If repo-analyzer already wrote a draft manifest with `status: planned`
entries, treat that as ground truth — only add/modify entries if the
analyzer's plan is genuinely incomplete. Do not silently replace the
analyzer's choices.

### Stage 2.5: Emission Decision

For each manifest entry, set `emission: notebook` (default) or
`emission: inline`. Inline only when:

- `type: compare` AND the comparison fits in a markdown table or side-by-
  side code blocks.
- `type: use` AND the exercise is a short copy-paste-run block (no scaffold,
  no validation, no solution).

Otherwise: notebook. If unsure, choose notebook.

### Stage 3: Notebook Scaffolding (or inline block design)

#### For `emission: notebook`

Design the cell-by-cell structure. This is the blueprint for Stage 4.

```
Cell 1 [markdown]: Title + curriculum back-link
  - Exercise number, name, type, estimated time
  - One-line goal
  - Back-link: "Context: you just read §X.Y in [curriculum.md](../curriculum.md#sX.Y)"
  - Prerequisites (link to earlier notebooks if any)

Cell 2 [code]: Setup
  - Imports
  - Data loading / fixture creation
  - Helper functions the learner needs but shouldn't have to write
  - Runs without error as-is

Cell 3+ [markdown + code]: Guided walkthrough (2-4 cells)
  - Alternate markdown (explanation) and code (working example)
  - Code cells are COMPLETE and RUNNABLE — not scaffolded
  - Include print()/display() so output is visible
  - Don't re-explain concepts from curriculum.md — link back instead

Cell N [markdown]: "Your turn"
  - Specific, unambiguous task
  - Expected output format described
  - Optional: hint dropdowns inside <details> tags

Cell N+1 [code]: Scaffold
  - Function signature with docstring
  - TODO comments marking where to fill in (WHAT, not HOW)
  - Type hints on parameters and return
  - Parses without syntax errors

Cell N+2 [code]: Validation
  - Assertions checking the learner's code works
  - Clear error messages: "Expected X, got Y"
  - At least 3 cases: basic, edge, non-trivial
  - Print success message when all pass

Cell N+3 [markdown]: Stretch goal (optional)
  - Harder extension, no scaffold

Cell N+4 [code]: Solution
  - Runnable code cell. scaffold_notebook.py sets source_hidden so it
    starts collapsed in JupyterLab. Other viewers show it expanded.
```

**Rules for scaffold cells:**
- Stub functions return `None` or `raise NotImplementedError`.
- Include type hints — they're documentation.
- TODO comments say WHAT, not HOW: `# TODO: Filter items where score > threshold`
  not `# TODO: Use list comprehension with if clause`.
- Don't scaffold too much (no structural decisions left) or too little
  (the learner can't tell what function to write).

**Rules for validation cells:**
- 3+ cases: basic, edge, non-trivial.
- Assertions have descriptive messages.
- Always `print("All tests passed.")` at the end.
- Visual check for any plots.

#### For `emission: inline`

Write the markdown block that will replace the curriculum placeholder.
For `compare`: a table or side-by-side prose with code samples. For short
`use`: a fenced code block + one expected-output line. Keep under ~20 lines
of markdown total.

### Stage 4: Generation, Validation, Insertion

This stage is gated. A notebook is not "done" until each gate passes.

#### Stage 4a: Generation

For each notebook exercise: construct an `ExerciseSpec` and call
`scripts/scaffold_notebook.py`. Save to
`learn/notebooks/exercise-NN-title.ipynb` (slug-stripped filename — no
parens, no special chars).

For each inline exercise: prepare the markdown block as a string. Do NOT
insert it yet.

After generation, update the manifest: `status: scaffolded`.

**Subagent fan-out (when notebook count > 4):** One subagent per notebook.
Each gets `references/subagent-brief-template.md` + its single exercise
spec. Main agent runs a stitcher pass after: dedupe setup code, verify
cross-references, lint filenames. Below the threshold, generate
sequentially.

#### Stage 4b: Validation (MANDATORY — two channels)

`scaffold_notebook.py` emits a `learn/internals/validation/exercise-NN.validation.json`
stub per notebook. Both channels must fill it in:

**Channel 1: Haiku-as-student (pedagogical check).** Spawn a Haiku subagent
per notebook with this brief:

```
You are a student learning a new codebase. You have access to ONLY the
information in this notebook — no prior knowledge of the library. Work
through it:

1. Run the setup cell. Report import errors or missing dependencies.
2. Read and run each guided cell. Note anything confusing.
3. Read "Your turn." Attempt using ONLY what the walkthrough taught.
   Do NOT look at the solution.
4. Run the validation cell against your attempt.
5. If stuck, explain exactly where and why.

Output JSON:
{
  "exercise": "<title>",
  "setup_runs": true/false,
  "guided_cells_run": true/false,
  "could_complete_without_solution": true/false,
  "validation_passed": true/false,
  "stuck_points": [...],
  "ambiguities": [...],
  "missing_info": [...],
  "solution_matches": true/false
}
```

Fix-up rules:
- `setup_runs: false` → fix imports/deps. Hard blocker.
- `could_complete_without_solution: false` → walkthrough gap or ambiguity.
- `validation_passed: false` (Haiku's approach was reasonable) → loosen
  assertions.
- `stuck_points` → fix missing info and ambiguity; leave genuine difficulty.
- `solution_matches: false` → solution is wrong; fix it.

Apply fixes silently. Only surface to the user if an exercise had to be
cut entirely.

**Channel 2: nbconvert execute (execution check).** In a fresh virtual env
matching `learn/notebooks/requirements.txt`, run:

```
jupyter nbconvert --to notebook --execute learn/notebooks/exercise-NN-*.ipynb
```

This catches env mismatches that Haiku misses (a wheel missing on the
target platform, version skew, OS-specific failures). Fix the underlying
issue, not the symptom — if a dep is missing, add it to requirements.txt;
if a code path is OS-specific, generalize it.

When both channels write to `validation_report.json` and pass, update the
manifest: `status: validated`.

The orchestrator's reconciliation pass will refuse to finish if any
`validation_report.json` is empty or marks failure. Do not skip this stage.

#### Stage 4c: Insertion

For each entry with `status: validated`, edit `learn/curriculum.md`:

1. Find the line containing `<!-- step:SECTION:SLOT -->` (where SLOT is
   the manifest's `slot` field).
2. The next line is the placeholder: `- [ ] Exercise NN — pending` or
   similar.
3. Replace ONLY that one line with the real content:
   - For `emission: notebook`:
     ```markdown
     - [ ] [Exercise NN — title](notebooks/exercise-NN-title.ipynb)
     ```
   - For `emission: inline`: replace the one placeholder line with the
     inline markdown block (which may be multiple lines).

Update the manifest: `status: inserted`.

You MUST NOT touch any other line. The marker is invariant: leave it in
place above the inserted content.

### Stage 5: Notebook Environment Files

After all entries are `inserted`:

- Read `learn/internals/.config.json` for the user's `env_manager`. Never
  mention any other manager in user-facing files.
- Generate `learn/notebooks/requirements.txt` (always).
- Generate `learn/notebooks/pyproject.toml` (always — minimal, with the
  exercise deps).
- Generate `learn/notebooks/README.md`: setup instructions leading with
  the detected manager, plus how to register the venv as a Jupyter kernel:
  ```
  python -m ipykernel install --user --name=learn-<project>
  ```

## Self-contained notebook rule

Notebooks must be runnable with ONLY the library under study + standard
scientific Python (numpy, matplotlib, scipy). NO simulation environments
(PyBullet, MuJoCo, pygame, Isaac), NO GUI frameworks, NO heavy optional
dependencies. If a working example needs sim, synthesize the state in-
notebook or run Euler integration with matplotlib for visualization.

## Quality Checklist

After Stage 4b for every notebook, confirm:

- [ ] Setup cell runs without error.
- [ ] Every guided cell runs and produces visible output.
- [ ] Scaffold cells parse without syntax errors.
- [ ] Validation cells pass when given the solution.
- [ ] Early "use" exercises are completable from the walkthrough alone.
- [ ] Exercise order has no forward dependencies.
- [ ] Notebook is self-contained (no sim envs, no GUI frameworks).
- [ ] Ambiguity ≠ difficulty: instructions are specific.
- [ ] Solution is a runnable code cell with `source_hidden` set.

After Stage 4c for the manifest:

- [ ] Every entry has `status: inserted`.
- [ ] No `pending` placeholders remain in curriculum.md.
- [ ] No `<parameter>`, `<antml`, or other tool fragments in any
      generated artifact.
- [ ] No package manager other than `.config.json:env_manager` mentioned
      in user-facing files.

## Pipeline cadence

Run end-to-end for the user; run QA exhaustively for yourself. Internal
checks (candidate filtering, Haiku validation, nbconvert, artifact grep,
self-questioning between stages) are part of the pipeline, not pauses.
Pause only when genuinely blocked (unresolvable dep, missing file,
ambiguous instruction the manifest can't answer). Use AskUserQuestion
when you must ask. Prefer one question over silent guessing; prefer silent
guessing over a low-quality default.
