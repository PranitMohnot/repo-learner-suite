---
name: exercise-gen
description: >
  Generate Jupyter notebook exercises from a codebase analysis. Reads the
  manifest at learn/internals/exercise-plan.md, scaffolds notebooks (or short
  inline blocks where the manifest says so), runs MANDATORY mock-student +
  nbconvert validation, then inserts links into learn/curriculum.md at the step markers
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

#### Stage 4b: Env files

Before validation can run, the notebooks need installable env files.

- Read `learn/internals/.config.json` for `user.env_manager` (and
  `repo.language`). Never mention any other manager in user-facing files.
- Call `scaffold_notebook.py`'s `generate_env_files(specs, output_dir,
  language=...)`. For Python: writes `requirements.txt` + `pyproject.toml`.
  Adding a language extends `LANGUAGE_PROFILES` and the corresponding
  generator branch.

#### Stage 4c: Env install (MANDATORY)

Run the user's chosen install command before any validation. The previous
pipeline implicitly required this but never executed it — the result was
nbconvert validation either skipping silently or failing on missing deps.

1. Look up the install command:
   `LANGUAGE_PROFILES[repo.language].env_managers[user.env_manager]`.
2. Run it via the Bash tool in `learn/notebooks/`. Use a generous timeout
   (60–300s for a fresh project). Stream output so the user sees progress.
3. If it fails, diagnose:
   - Network issue → retry once, then surface to the user.
   - Missing system dep (e.g. compiler, system library) → tell the user
     specifically what's missing, with the platform-specific install
     command.
   - Version conflict → revisit `dependencies` in the manifest; loosen
     pins or substitute.
   Don't silently skip — Stage 4d needs the env to exist.

4. **Register the notebook env as a named Jupyter kernel.** Without this
   step, editors (VS Code in particular) have no idea which Python to
   use when the user opens a notebook, and they get dumped into a kernel
   picker with no obvious right answer. The notebook's
   `kernelspec.name` is set by `scaffold_notebook.py` to `learn-<repo>`;
   this step actually registers that name against the venv.

   From `learn/notebooks/`, run (Python + uv example):
   ```
   uv run python -m ipykernel install --user --name=learn-<repo> --display-name="Learn <Repo>"
   ```
   For pip: `python -m ipykernel install --user --name=...` after
   `source .venv/bin/activate`. For other env managers, the equivalent
   `<manager> run python -m ipykernel ...` form.

   Confirm by running `jupyter kernelspec list` — the new kernel name
   should appear.

#### Stage 4d: Validation (MANDATORY — two channels)

`scaffold_notebook.py` emits a `learn/internals/validation/exercise-NN.validation.json`
stub per notebook. Both channels must fill it in:

**Channel 1: Mock-student validation (pedagogical check).** Spawn a
fast-tier model as a mock-student subagent per notebook with this brief.
Use the cheapest capable model available — on Claude Code, Haiku; on
other agents, the equivalent fast tier. The point is fresh eyes, not raw
capability.

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
- `validation_passed: false` (mock student's approach was reasonable) →
  loosen assertions.
- `stuck_points` → fix missing info and ambiguity; leave genuine difficulty.
- `solution_matches: false` → solution is wrong; fix it.

When the mock student passes, set `validator_passed: true` in
`validation_report.json` (and attach the JSON report under `validator_report`).

Apply fixes silently. Only surface to the user if an exercise had to be
cut entirely.

**Channel 2: nbconvert execute (environment check).** This channel verifies
the *environment*, not solution correctness — that's Channel 1's job. In
the venv installed by Stage 4c, run:

```
jupyter nbconvert --to notebook --execute --allow-errors learn/notebooks/exercise-NN-*.ipynb
```

`--allow-errors` is required. The scaffold cell intentionally raises
`NotImplementedError` (Python) or the language equivalent — it's a
placeholder for the learner. Likewise the validation cell will fail because
the scaffold isn't filled in. **Those failures are expected** and do NOT
fail this check.

What you actually verify after the run: inspect the executed notebook's
cell outputs and confirm:
- The setup cell ran without error (imports succeeded).
- Every guided walkthrough cell ran without error.
- The only cells with errors are the scaffold and validation cells.

If a setup or guided cell errored, the env is broken. Fix the underlying
issue (missing dep, wrong wheel for the platform, OS-specific code path) —
don't paper over it. Solution correctness is Channel 1's job, not this one.

When both channels write to `validation_report.json` and pass, update the
manifest: `status: validated`.

The orchestrator's reconciliation pass will refuse to finish if any
`validation_report.json` is empty or marks failure. Do not skip this stage.

#### Stage 4e: Insertion

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

### Stage 5: Notebook README

After all entries are `inserted`, generate `learn/notebooks/README.md`:
setup instructions leading with the detected env_manager (from
`.config.json`), plus the Jupyter kernel registration hint appropriate
to the language (for Python: `python -m ipykernel install ...`).

The env files (`requirements.txt` + `pyproject.toml` for Python; other
files when additional languages are added) were generated in Stage 4b;
this stage only writes the README that points at them.

## Light mode

If `.config.json:tuning.depth == "light"`, three things change.
Comprehensive mode (the default) is unaffected.

- **Candidates (Stage 1):** mine 5–8 candidates instead of 12–18. Be more
  ruthless about pre-filtering.
- **Selection (Stage 2):** select 3–5 exercises instead of 8–12. Skew toward
  high-value `use` and `modify` exercises tied to Phase 1; drop `compare`
  and most `architectural` candidates.
- **Validation (Stage 4d):** skip Channel 1 (mock-student validation).
  Keep Channel 2 (nbconvert execute) — it's cheap and catches the real
  env bugs. Still write the `validation_report.json` with
  `validator_passed: true` and a `validator_skipped_reason: "light mode"`
  field so reconciliation passes.

Stage 4c (env install) still runs in Light mode — without it, the
nbconvert check in Stage 4d cannot run.

Subagent fan-out, marker discipline, manifest insertion, and reconciliation
are identical to comprehensive mode.

## Test mode

If `.config.json:tuning.mode == "test"`, run a smoke-test variant. The
output directory is `learn_test/`; all paths shift accordingly. Light
mode's behavior applies on top (depth is forced to `light` in test mode).

- **Stages 1–2 (Mining + Selection):** skipped entirely. repo-analyzer's
  manifest already contains the 1 entry in test mode. Read it directly.
- **Stage 3 (Scaffolding):** expand the manifest entry into a full
  `ExerciseSpec` as usual — design setup / walkthrough / your-turn /
  scaffold / validation / solution cells against the real source files
  the analyzer cited.
- **Stage 4a (Generation):** generate 1 notebook. No subagent fan-out
  (1 < 4 threshold anyway).
- **Stage 4b (Env files):** emit normally.
- **Stage 4c (Env install):** MANDATORY. This is one of the main things
  test mode is meant to catch — a freshly-detected env_manager not
  actually working on the user's platform.
- **Stage 4d (Validation):** Channel 1 (mock-student) is SKIPPED (Light
  mode behavior). Channel 2 (nbconvert) runs against the 1 notebook.
  Set `validator_skipped_reason: "light mode"` in the report.
- **Stage 4e (Insertion):** insert into the 1 section's exercise marker.
- **Stage 5 (Notebook README):** emit normally.

Test mode is repo-dependent throughout. The 1 exercise's setup cell, task
description, scaffold, validation, and solution must all reference real
symbols and files from the codebase. The point is to verify the adapter
+ pipeline shape produces a working artifact for this codebase — not to
produce a stock template.

## Dependency selection — reason about platform compatibility

Notebooks must run on the *user's* system, not on an idealized one. There
is no blocklist of libraries — a library that's fine on Linux x86 may be
broken on Apple Silicon, and vice versa. Reason about the specific
combination before including any dependency.

Before adding a dep to a notebook's setup cell:

1. Read `user.platform` from `learn/internals/.config.json` (set by the
   orchestrator at Step 0 — e.g. `macos-arm64`, `linux-x86_64`,
   `windows-x86_64`).
2. Reason about whether the dep will install and run on that platform.
   Concrete failure modes worth checking:
   - CUDA-only libraries on CPU systems
   - Apple Silicon compatibility issues (libraries shipping x86-only
     wheels, sims with no arm64 binaries, etc.)
   - Linux-specific sim/UI components on Mac or Windows
   - System libraries that need a compiler toolchain the user may not have
3. If the dep is problematic on this platform:
   - Prefer a lighter substitute that works on the user's platform
     (e.g. visualize state with the language's plotting library instead
     of importing a sim engine).
   - Or synthesize the case in-notebook from baseline utilities
     (e.g. Euler integration instead of a physics engine).
   - If neither is feasible, document the limitation in the notebook's
     title cell and skip the exercise rather than ship something the
     user can't run.

When uncertain about platform compatibility, ask via AskUserQuestion
rather than guess.

There is no per-language allow/deny list. The model knows the platform
gotchas for each ecosystem from its training. The point of this rule is
that "library X is heavy" is not a useful framing — "library X breaks on
the user's specific platform" is.

## Language conventions

Read `learn/internals/.config.json:repo.language` before generating cells.
Use the language's idiomatic patterns for:

- **Setup cell:** load dependencies in the language's standard way.
- **Validation cell:** assert each expected property using the language's
  idiomatic assertion mechanism. End with one success-confirmation line.
- **Scaffold stubs:** return nothing / raise the language's standard
  "not implemented" signal so the cell parses but fails until completed.
- **Function signatures, naming, assignment, comments:** follow the
  language's conventions.

The notebook plumbing (kernel name, env-file format, env-manager install
commands) is handled by `scripts/scaffold_notebook.py`'s `LANGUAGE_PROFILES`
table — that's the adapter layer. This skill stays language-agnostic at
the prose level.

### Polyglot support

The run-wide `--language` flag sets the default. Individual `ExerciseSpec`
entries can override `language` to mix kernels in one curriculum (e.g. a
Python project with a C++ extension where one exercise builds the
extension). Set `spec.language` explicitly when overriding; otherwise the
run-wide default applies.

## Quality Checklist

After Stage 4d (validation) for every notebook, confirm:

- [ ] Setup cell runs without error on the user's platform.
- [ ] Every guided cell runs and produces visible output.
- [ ] Scaffold cells parse without syntax errors.
- [ ] Validation cells pass when given the solution.
- [ ] Early "use" exercises are completable from the walkthrough alone.
- [ ] Exercise order has no forward dependencies.
- [ ] Every dependency was evaluated for platform compatibility before
      inclusion (no library known-broken on `user.platform` slipped in).
- [ ] Ambiguity ≠ difficulty: instructions are specific.
- [ ] Solution is a runnable code cell with `source_hidden` set.

After Stage 4e (insertion) for the manifest:

- [ ] Every entry has `status: inserted`.
- [ ] No `pending` placeholders remain in curriculum.md.
- [ ] No `<parameter>`, `<antml`, or other tool fragments in any
      generated artifact.
- [ ] No package manager other than `.config.json:env_manager` mentioned
      in user-facing files.

## Pipeline cadence

Run end-to-end for the user; run QA exhaustively for yourself. Internal
checks (candidate filtering, mock-student validation, nbconvert, artifact
grep, self-questioning between stages) are part of the pipeline, not pauses.
Pause only when genuinely blocked (unresolvable dep, missing file,
ambiguous instruction the manifest can't answer). Use AskUserQuestion
when you must ask. Prefer one question over silent guessing; prefer silent
guessing over a low-quality default.
