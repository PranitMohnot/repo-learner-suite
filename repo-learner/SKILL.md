---
name: repo-learner
description: >
  Orchestrator for the repo-learner skill suite. Routes /learn commands to specialized
  sub-skills for analyzing codebases, generating exercises, tutoring, and quizzing.
  Trigger on any /learn command, "help me learn this repo", "teach me this codebase",
  "I want to understand this project", or any request to systematically learn a codebase.
  Also trigger when the user references an existing learn/ directory.
---

# Repo Learner — Orchestrator

Routes `/learn` commands to the right sub-skill.

## Command Routing

| Command | Sub-skill |
|---------|-----------|
| `/learn analyze <path>` | repo-analyzer |
| `/learn exercises [section]` | exercise-gen |
| `/learn tutor [section]` | code-tutor |
| `/learn quiz [section]` | code-quiz |
| `/learn status` | (self — parse README.md checkboxes) |

## No subcommand — always lead with one action

Check state and recommend ONE thing:

- **No `learn/` directory:** "Let's start. I'll analyze the codebase and build your
  learning path." → run analyze pipeline. No menus.
- **`learn/curriculum.md` exists, no checkboxes ticked:** "Your curriculum is ready —
  open `learn/curriculum.md` (or `learn/curriculum.html` for interactive). Start
  with Section 0 (overview), or say `tutor`, `quiz`, `exercises`."
- **Some checkboxes ticked:** "You're on Section X.Y. Pick up where you left off?"
  → recommend the next unchecked step. One escape line at the end:
  "Or: `tutor`, `quiz`, `exercises`, `status`."

Never dump a decision tree. One recommended action, one escape line.

## Front-Loaded Questions (start of any fresh pipeline)

Before reading any code, ask the user 3–4 questions in a single
AskUserQuestion call. The user's answers directly shape tutoring depth,
exercise scaffolding, and environment setup — they cannot be auto-detected.

**What to ask (adapt to the detected repo):**

1. **Domain familiarity.** "How familiar are you with [domain]?" Options:
   `[none / textbook / built one]`. Show detected default inline.

2. **Language/framework familiarity.** Detect the primary framework and ask
   the equivalent question — e.g. "Pandas familiarity? `[none / basics / deep]`"
   or "Async/await familiarity? `[none / sync-only / async-fluent]`". Skip if
   the repo uses no specialized framework.

3. **Environment manager.** Auto-detect from lockfiles (uv.lock → uv,
   poetry.lock → poetry, requirements.txt → pip). Show detected default:
   "I detected `uv.lock` — use uv?" Options: `[uv / pip / conda / other]`.

4. **Open-ended catch-all.** "Anything else I should know? (learning goals,
   time constraints, areas of interest)" — free text, optional.

**Rules:**
- Ask only what the user uniquely knows; auto-detect everything else.
- Show detected defaults inline. "Use all defaults" is always an option but
  is never silently chosen for them.
- Persist answers to `learn/internals/.config.json`. All downstream skills
  read it. Never reference a package manager other than the one stored
  there in user-facing artifacts.

## Shared State

All sub-skills read/write to `<repo-root>/learn/`:

```
learn/
├── curriculum.md          # THE document. Section 0 = overview. Per-step
│                          # checkboxes. Exercises linked inline. From
│                          # repo-analyzer; exercise-gen edits at markers.
├── curriculum.html        # Interactive HTML mirror of curriculum.md
│                          # (clickable checkboxes + localStorage, hint/
│                          # solution dropdowns, syntax highlight).
├── cheatsheet.md          # Quick-reference card (separate from narrative).
├── notebooks/             # From exercise-gen
│   ├── README.md          # Setup + exercise sequence
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── exercise-*.ipynb
└── internals/             # Build artifacts (accessible but not highlighted)
    ├── .config.json        # User answers from front-loaded questions
    ├── exercise-candidates.md
    ├── exercise-plan.md    # The manifest — see Shared Contracts below.
    ├── quiz-bank.md        # Source bank for /learn quiz (mutable)
    └── validation/         # Per-notebook Haiku + nbconvert reports
        └── exercise-NN.validation.json
```

No separate README.md, no separate overview.md, no path.html. Section 0 of
curriculum.md is the overview. curriculum.html is the interactive mirror.

## Progress Tracking

Progress lives in `learn/curriculum.md` as per-step markdown checkboxes inside
each section. The orchestrator parses these checkboxes. `learn/curriculum.html`
mirrors them via localStorage with a round-trip export-to-markdown button.

A section looks like:

```markdown
<a id="s1.3"></a>
### Section 1.3: First custom dataframe pipeline — sales aggregation

<!-- step:1.3:read-pipeline -->
- [ ] Read [pipelines/sales.py:14-60](src/pipelines/sales.py)
      — focus on the `groupby().agg()` chain.

<!-- step:1.3:run-the-demo -->
- [ ] Run `python -m examples.sales_demo` and inspect the resulting
      summary table.

<!-- step:1.3:exercise-03 -->
- [ ] [Exercise 03 — sales aggregation](notebooks/exercise-03-sales-agg.ipynb)

<!-- step:1.3:checkpoint-multi-index -->
> **Checkpoint:** Why does `.reset_index()` come after `.agg()` and not before?
> <details><summary>Answer</summary>
> `.agg()` operates on the grouper's MultiIndex; resetting earlier collapses
> the grouping key into a column and changes what `.agg` is grouping over …
> </details>
```

## Shared Contracts (manifest + markers + reconciliation)

These contracts let repo-analyzer and exercise-gen work without colliding.

### The manifest — `learn/internals/exercise-plan.md`

Single source of truth for "where does each exercise live and how is it
rendered." repo-analyzer writes the initial manifest (Stage 2 of the analysis
pipeline). exercise-gen reads it, updates `status` and `notebook_path` as it
works, and writes the final state.

Each exercise entry is a markdown section with a `yaml` code fence at the top
holding the machine-readable fields, followed by free-form prose:

````markdown
## Exercise 3: Joint-limit avoidance from scratch

```yaml
exercise: 3
section: "1.3"
type: create                       # use | modify | debug | create | compare
emission: notebook                 # notebook | inline
slot: exercise-03                  # slug; resolves to <!-- step:1.3:exercise-03 -->
notebook_path: notebooks/exercise-03-joint-limits.ipynb
status: planned                    # planned | scaffolded | validated | inserted
```

**Goal:** …
**Builds on:** Exercise 2.
**Notebook structure:** …
````

Field rules:
- `emission: inline` is reserved for `compare` exercises and short copy-paste-
  run blocks (no scaffold/validation). Default is `notebook`. The long-term
  direction is everything becomes a notebook — inline is an exception.
- `slot` is a kebab-case slug, unique within its section. Resolves to the
  marker `<!-- step:SECTION:SLOT -->` in curriculum.md.
- `status` lifecycle:
  - `planned`        — manifest entry exists, no artifact yet.
  - `scaffolded`     — notebook (or inline block) emitted; not yet validated.
  - `validated`      — Haiku + nbconvert checks passed.
  - `inserted`       — curriculum.md placeholder replaced with real link/block.
- `notebook_path` is required when `emission: notebook`. Omit for inline.

### Marker convention — curriculum.md

Every checkbox step in a section is preceded by an HTML-comment marker on its
own line:

```markdown
<!-- step:SECTION:slug -->
- [ ] …step content…
```

- `SECTION` is the section ID, e.g. `1.3`.
- `slug` is kebab-case, unique within the section. Slug derives from step
  intent: `read-validator`, `run-the-demo`, `exercise-03`, `checkpoint-async`,
  `compare-eager-vs-lazy`. The analyzer picks them.
- Markers are invisible in rendered markdown and stable across edits to
  surrounding prose.

Markers serve three purposes: (1) exercise-gen looks up insertion points via
the manifest's `slot` field, (2) curriculum.html's parser keys on them, (3)
reconciliation cross-checks them.

For exercise slots specifically, the analyzer initially emits a placeholder
checkbox after the marker (e.g. `- [ ] Exercise 03 — pending`). exercise-gen
replaces that one line with the real link (notebook) or the real inline block.
It MUST NOT edit anything outside that one line.

### Pipeline order (orchestrator)

1. Front-loaded questions → write `internals/.config.json`.
2. repo-analyzer → curriculum.md (with markers + exercise-pending stubs),
   cheatsheet.md, draft `internals/exercise-plan.md`, `internals/quiz-bank.md`.
3. exercise-gen → notebooks, validation reports, replaces pending stubs in
   curriculum.md, updates manifest to `status: inserted`.
4. Regenerate `learn/curriculum.html` from the final curriculum.md by
   running `repo-analyzer/scripts/curriculum_html.py`.
5. Reconciliation pass — see below. Runs the script
   `repo-learner/scripts/reconcile.py`. Fail loud if any check fails.

### Reconciliation pass (orchestrator, end of pipeline)

Concrete runner: `repo-learner/scripts/reconcile.py --learn-dir learn`.
The orchestrator refuses to declare "done" until all of:

1. Every manifest entry has `status: inserted`.
2. Every `<!-- step:X.Y:exercise-NN -->` marker in curriculum.md is followed by
   a real link or fenced code block — no `pending` stubs remain.
3. Every `notebook_path` in the manifest exists on disk and parses as valid
   `nbformat` JSON.
4. Every notebook has a `internals/validation/exercise-NN.validation.json`
   report with both `haiku_passed: true` and `nbconvert_passed: true`.
5. Artifact grep: no `<parameter>`, `<antml`, `<function`, or other tool-call
   fragments in any user-facing file (curriculum.md, curriculum.html,
   cheatsheet.md, notebooks/*.ipynb, notebooks/README.md).
6. Package-manager consistency: no manager other than the one in
   `.config.json:env_manager` is mentioned in user-facing files.

If any check fails, fix it (regenerate, re-validate, re-insert). Do not
silently skip.

## Silent Defaults (never ask the user about these)

- Haiku validation + nbconvert execute: both always run.
- Subagent fan-out: 1 agent per notebook when exercise count > 4. Each agent
  gets the shared brief template (see `exercise-gen/references/`) + its one
  spec. Main agent runs a stitcher pass after.
- Filename slugging: always strip non-alphanumerics.
- Output directory: always `learn/`.
- Build artifact location: always `learn/internals/`.
- Reconciliation: always run as the final stage. Refuses to declare "done"
  unless all six checks pass (see Shared Contracts above).

## Pipeline cadence — "no stopping" rule

Run the pipeline end-to-end for the user; run QA exhaustively for yourself.
After the initial questions, do not pause for user input unless you are
genuinely blocked (unresolvable dependency, missing file, ambiguous
instruction). Internal checks — Haiku validation, nbconvert execute, artifact
grep, self-questioning — are part of the pipeline, not pauses. When you must
ask, use AskUserQuestion. Prefer one question over silent guessing; prefer
silent guessing over a low-quality default.
