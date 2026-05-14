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
| `/learn test` | full pipeline in test mode → `learn_test/` (see below) |

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

### Step 0: auto-detect language + platform (silent)

Sniff the repo before asking anything:

| Signal | Language |
|---|---|
| `*.py`, `pyproject.toml`, `setup.py`, `requirements.txt`, `uv.lock`, `poetry.lock` | python |

Currently only Python is supported by the notebook scaffolder. Other
languages will be added as language profiles (see
`exercise-gen/scripts/scaffold_notebook.py:LANGUAGE_PROFILES`). If a
repo's primary language is not python, surface that to the user and ask
how to proceed.

Persist as `repo.language` in `.config.json`. Downstream skills
(exercise-gen, code-quiz) read it.

Also detect the user's platform via `uname -ms` (or `ver` on Windows).
Map to a canonical string:

| `uname -ms` output | `user.platform` |
|---|---|
| `Darwin arm64` | `macos-arm64` |
| `Darwin x86_64` | `macos-x86_64` |
| `Linux x86_64` | `linux-x86_64` |
| `Linux aarch64` | `linux-arm64` |
| Windows (any) | `windows-x86_64` |

Persist as `user.platform` in `.config.json`. exercise-gen reads it during
dependency selection (see exercise-gen/SKILL.md → "Dependency selection")
to avoid shipping notebooks with platform-broken deps.

**What to ask (adapt to the detected repo + language):**

1. **Domain familiarity.** "How familiar are you with [domain]?" Options:
   `[none / textbook / built one]`. Show detected default inline.

2. **Language/framework familiarity.** Detect the primary framework and ask
   the equivalent question — e.g. "Pandas familiarity?",
   "Async/await familiarity?". Skip if the repo uses no specialized
   framework.

3. **Environment manager.** Auto-detect from lockfiles (uv.lock → uv,
   poetry.lock → poetry, requirements.txt → pip). Show detected default:
   "I detected `uv.lock` — use uv?" Options: `[uv / pip / poetry / conda]`.

4. **Depth.** "Comprehensive (default — deep read, 8–12 exercises, full
   QA) or Light (~1/4 cost — leaner curriculum, 3–5 exercises, skips
   mock-student validation)?" Persist as `tuning.depth: comprehensive | light`
   in `.config.json`. Default to `comprehensive` if the user accepts
   defaults.

5. **Open-ended catch-all.** "Anything else I should know? (learning goals,
   time constraints, areas of interest)" — free text, optional.

**Rules:**
- Ask only what the user uniquely knows; auto-detect everything else.
- Show detected defaults inline. "Use all defaults" is always an option but
  is never silently chosen for them.
- Persist answers to `learn/internals/.config.json`. All downstream skills
  read it. Never reference a package manager other than the one stored
  there in user-facing artifacts.

**`.config.json` schema** (the canonical paths downstream skills read):

```json
{
  "user": {
    "domain_familiarity": "none | textbook | built_one",
    "framework_familiarity": "...",
    "env_manager": "uv | pip | poetry | conda",
    "platform": "macos-arm64 | linux-x86_64 | ...",
    "goal_notes": "free text from the open-ended question"
  },
  "repo": {
    "name": "...",
    "language": "python | ...",
    "root": "absolute path to the repo being learned"
  },
  "tuning": {
    "depth": "comprehensive | light",
    "mode": "normal | test"
  }
}
```

Downstream skills depend on these paths exactly:
- `reconcile.py` reads `user.env_manager` and `repo.language`.
- `scaffold_notebook.py:generate_env_files` derives the host-repo
  editable-install path from `repo.root` (or the orchestrator passes it
  explicitly).
- `exercise-gen` reads `user.platform` for dependency selection.
- `tuning.depth` and `tuning.mode` gate Light mode and Test mode
  behavior across all skills.

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
    └── validation/         # Per-notebook mock-student + nbconvert reports
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
  - `validated`      — mock-student + nbconvert checks passed.
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

1. Step 0: silently detect language + platform; persist to `.config.json`.
2. Front-loaded questions → write the rest of `internals/.config.json`.
3. repo-analyzer → curriculum.md (with markers + exercise-pending stubs),
   cheatsheet.md, draft `internals/exercise-plan.md`, `internals/quiz-bank.md`.
4. exercise-gen, internally:
   - Stage 4a: generate notebook `.ipynb` files.
   - Stage 4b: emit env files (`requirements.txt` + `pyproject.toml` for
     Python; per-language variants when other languages are added).
   - Stage 4c: **run the env install command** (e.g. `uv sync`).
     MANDATORY — Stage 4d's nbconvert validation needs the env to exist.
   - Stage 4d: validate (mock-student + nbconvert).
   - Stage 4e: replace pending stubs in curriculum.md, update manifest.
5. Regenerate `learn/curriculum.html` from the final curriculum.md by
   running `repo-analyzer/scripts/curriculum_html.py`.
6. Reconciliation pass — see below. Runs the script
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
   report with both `validator_passed: true` and `nbconvert_passed: true`.
5. Artifact grep: no `<parameter>`, `<antml`, `<function`, or other tool-call
   fragments in any user-facing file (curriculum.md, curriculum.html,
   cheatsheet.md, notebooks/*.ipynb, notebooks/README.md).
6. Package-manager consistency: no manager other than the one in
   `.config.json:env_manager` is mentioned in user-facing files.

If any check fails, fix it (regenerate, re-validate, re-insert). Do not
silently skip.

## Silent Defaults (never ask the user about these)

- Mock-student validation + nbconvert execute: both always run.
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
instruction). Internal checks — mock-student validation, nbconvert execute, artifact
grep, self-questioning — are part of the pipeline, not pauses. When you must
ask, use AskUserQuestion. Prefer one question over silent guessing; prefer
silent guessing over a low-quality default.

## Test mode

`/learn test` runs the full pipeline as a smoke test against the real
repo and writes to `learn_test/` (never to `learn/`). It's intended for:

- Verifying the suite works on a new codebase before committing to a
  full run.
- Debugging changes to the suite itself.
- Quickly inspecting what shape the agent's adaptation produces for an
  unfamiliar repo.

**What's different in test mode:**

- Output directory: `learn_test/` instead of `learn/`. All paths in the
  shared-state tree shift accordingly (`learn_test/curriculum.md`,
  `learn_test/internals/.config.json`, etc.).
- `.config.json:tuning.mode == "test"` is persisted, alongside the rest.
- `tuning.depth` is forced to `light` internally (test mode is about
  pipeline structure, not analysis thoroughness).
- repo-analyzer: produces Section 0 (overview) + Section 1.1 only.
  Trimmed cheatsheet (~30 lines). 3 quiz seeds covering different palette
  types. Manifest has 1 entry — the simplest "use" exercise from the
  candidates.
- exercise-gen: 1 exercise. No subagent fan-out. **All Stage 4 sub-stages
  still run** (generate → emit env files → install env → validate →
  insert). This is the whole point — the smoke test catches Stage 4c
  (env install) failures, validation crashes, insertion bugs.
- Reconciliation runs against `learn_test/` and must pass — the 1 entry
  must be fully inserted, the 1 notebook must validate, etc.

**What's the same:**

- Front-loaded questions still run. They're adapter inputs (env_manager,
  language, platform), and skipping them would defeat the "adaptivity
  works" check.
- All artifacts must be repo-dependent. The single section must describe
  the actual codebase. The single exercise must reference real source
  files. Test mode is a *minimal real run*, not a stock template.
- curriculum.html still regenerates.

**Cleanup:**

`learn_test/` is meant to be inspected and discarded. To turn a test run
into a real run, `rm -rf learn && mv learn_test learn` and re-run the
analyzer in normal mode to fill in the rest. (Or just re-run from
scratch — test mode is fast.)
