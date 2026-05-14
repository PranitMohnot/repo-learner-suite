---
name: repo-analyzer
description: >
  Deep-read a codebase and generate a structured learning curriculum with a
  cheatsheet and quiz bank. Trigger on "/learn analyze", "analyze this repo",
  "scan this codebase", or when another skill (repo-learner orchestrator)
  delegates analysis. This is the expensive first step — it reads broadly
  before any tutoring or exercises can happen. Produces learn/curriculum.md
  (THE document, with overview as Section 0), learn/cheatsheet.md,
  learn/internals/exercise-plan.md (the manifest), and
  learn/internals/quiz-bank.md.
---

# Repo Analyzer

Deep-scan a codebase and produce the foundational learning artifacts. This is
the most token-expensive skill in the suite — it reads most of the codebase
before generating anything.

Read the Shared Contracts in `repo-learner/SKILL.md` (manifest schema, step
marker convention, reconciliation rules) before starting. This skill writes the
artifacts those contracts govern.

## Analysis Flow

Follow the global→local cognitive flow identified in codebase comprehension
research (Gao et al., 2025 — CodeMap):

### Level 1: Global (Project Overview)
- Read README, docs/, CONTRIBUTING, build config.
- Identify: project purpose, target users, key dependencies, ecosystem
  position.
- Output: Section 0 of `learn/curriculum.md` (see below).

### Level 2: Structural (Architecture)
- Map module/package structure via directory tree + imports.
- Identify: core abstractions, data flow, entry points, extension points.
- Read tests directory for coverage map.
- Output: architecture parts of curriculum sections.

### Level 3: Local (Functions and Variables)
- Deep-read public API, key internal modules, examples.
- Identify: function signatures, patterns, gotchas, underdocumented behavior.
- Output: detailed curriculum sections, cheatsheet, quiz bank.

## Output Artifacts

### `learn/curriculum.md` — THE document

One file. The learner scrolls through it top to bottom, clicking out to
notebooks/terminal/source files only when a step calls for it. There is no
separate README, no separate overview, no separate path table.

#### Structure

```
Section 0: Overview          (plain-English big picture — see below)
Section 1.1, 1.2, …          (Phase 1: usage)
Section 2.1, 2.2, …          (Phase 2: internals)
Section 3.1, 3.2, …          (Phase 3: extension)
```

Phase weighting comes from `learn/internals/.config.json` (user familiarity
answers). Skim Phase 2/3 when the user already knows the domain; deepen them
when they want internals.

#### Section 0: Overview

Replaces the old standalone `overview.md`. Plain English, plain code, high
level. 1–2 pages. What this project is, who it's for, what problem it solves,
how it's structured, what prerequisites the learner needs. Includes a
"how to use this curriculum" banner at the top with the two viewing modes
(markdown vs `curriculum.html`).

#### Sections 1.1+

Every section starts with an anchor and a one-line goal:

```markdown
<a id="s1.3"></a>
### Section 1.3: First custom validator — email + phone

**Goal:** read a complete, minimal pydantic model with cross-field validation.
```

After that, the section is a **curated sequence of steps**. There is no
required template. Each step is a checkbox item preceded by a step marker
(see Shared Contracts). A step can be anything that teaches the concept:

- read a specific file/lines
- run a demo or command
- do an exercise (link out to a notebook, or an inline code block)
- answer a checkpoint question (inline, with hidden answer)
- expand a hint dropdown
- compare two approaches
- a short prose passage you want them to read
- a "watch out for" warning
- a self-check you want them to think about

Mix freely. The goal is teaching, not section template compliance. If a
section is best taught as "read three files in a row, then one checkpoint,"
that's a complete section. If another is best taught as "run this demo, then
read the code that made it work, then do the exercise, then a checkpoint,"
that's also complete.

#### Step markers (mandatory)

Every checkbox-step gets a marker on the line immediately above it:

```markdown
<!-- step:1.3:read-retry-transport -->
- [ ] Read [transports/retry.py:24-90](src/transports/retry.py)
      — focus on the `handle_async_request` method.

<!-- step:1.3:run-the-demo -->
- [ ] Run `python -m examples.retry_demo` and observe how 503 responses
      are retried with exponential backoff.
```

- Section ID matches the `<a id="sX.Y">` anchor.
- Slug is kebab-case, unique within the section, derived from the step's
  intent (`read-validator`, `run-the-demo`, `exercise-03`,
  `checkpoint-async`, `compare-eager-vs-lazy`).
- Markers are invisible in rendered markdown and stable across edits.

#### Exercise slots

For each exercise the manifest will place into a section, emit a placeholder
checkbox preceded by an `exercise-NN` marker:

```markdown
<!-- step:1.3:exercise-03 -->
- [ ] Exercise 03 — pending (will be filled by exercise-gen)
```

exercise-gen replaces this one line with the real link (when emission is
`notebook`) or a fenced code block (when emission is `inline`). It only
touches that one line.

#### Checkpoints — inline questions with hidden answers

Use sparingly as light comprehension checks within a section:

```markdown
<!-- step:1.3:checkpoint-clone -->
> **Checkpoint:** Why does the retry loop clone the request before each attempt?
>
> <details><summary>Answer</summary>
>
> The request body is a stream — reading it consumes it. Re-sending the
> same request object after a failure would send an empty body …
>
> </details>
```

Blockquote + `<details>`. The blank lines around the `<details>` content are
required for fenced code blocks inside to render correctly.

#### Hints — collapsed dropdowns

Attach to exercises, checkpoints, or any step where a stuck learner would
benefit:

```markdown
<details><summary>Stuck? Hint 1</summary>

Look at how `client_demo.py:30-34` orders the `async with` block around
the session — the lifecycle matters here.

</details>
```

Default to collapsed (`<details>` is collapsed by default). Multiple hints =
multiple `<details>` blocks, each more revealing than the last.

#### "Watch out for" / "Depends on"

Free-form prose between steps. Not every section needs them. Use them where
the gotcha or dependency genuinely needs to be flagged.

#### Example shapes (inspiration, not templates)

These are illustrative, not prescriptive. Mix freely or invent new shapes.

**Reading-heavy** (Phase 2 internals):
read file → read file → checkpoint → self-check questions.

**Demo-first** (Phase 1 usage):
run demo → read the code that made it work → exercise → checkpoint.

**Exercise-first** (advanced/extension):
try this exercise cold → read the source you needed → comparison with the
alternative approach.

**Hybrid:** any mix of the above plus prose, watch-outs, and hints. The
analyzer chooses what teaches best.

### `learn/cheatsheet.md`

Under 200 lines. Reference card for someone already coding, not narrative.
Import patterns, common usage snippets, key API reference, error table, file
map. Separate from curriculum.md because its purpose is different (lookup,
not learning).

### `learn/internals/exercise-plan.md` (the manifest)

Write a draft manifest as part of analysis. For each exercise the analyzer
plans to recommend, emit a manifest entry (see Shared Contracts in
`repo-learner/SKILL.md` for the schema) with `status: planned`. exercise-gen
will pick this up, fill in `notebook_path`, run validation, and update the
status as it works.

Pair each manifest entry with an `exercise-NN` step marker + placeholder
checkbox in the matching curriculum section. The `slot` field in the manifest
must match the slug of that step marker.

### `learn/internals/quiz-bank.md`

3–5 seed questions per curriculum section. Each question includes a code
snippet for context (file path + line numbers + the snippet). Answers go
behind `<details>` tags.

Aim for variety across the seed set — not all recall, not all conceptual.
The code-quiz skill will mix from a richer palette (recall, conceptual,
predictive, diagnostic, applied, architectural — see
`code-quiz/SKILL.md`); seed the bank so it has at least 3 different types
represented per section.

The quiz skill reads AND edits this file. Treat it as a living resource.

## Light mode

If `.config.json:tuning.depth == "light"`, run the leaner variant. Comprehensive
mode (the default) is unaffected.

- Level 1 (Global): unchanged.
- Level 2 (Structural): map structure, but deep-read only the 3–5
  most-referenced files; skim the rest.
- Level 3 (Local): produce Phase 1 sections only. Mention Phase 2/3 in a
  single trailing "Going deeper" paragraph pointing at file locations, no
  full sections.
- Cheatsheet: cap at ~80 lines (vs ~200).
- Quiz bank: skip the seed. Leave a stub note in `internals/quiz-bank.md`
  saying questions will be generated by code-quiz on first run.
- Manifest: still draft it for Phase 1 exercises (exercise-gen needs it).

Everything else (markers, anchors, manifest schema, reconciliation) is
identical to comprehensive mode.

## What this skill does NOT produce

- No `learn/README.md` (the curriculum is the entry point).
- No `learn/overview.md` (folded into Section 0 of the curriculum).
- No `learn/path.html` (replaced by `learn/curriculum.html`, generated
  downstream from the curriculum markdown — not this skill's job).

## Quality Standards

- File paths and line ranges cited in curriculum must be verified to exist.
- Step markers must be unique within their section.
- Manifest `slot` values must match a real step marker in curriculum.md.
- Checkpoint/hint `<details>` blocks must have blank lines around any fenced
  code they contain.
- Cheatsheet snippets must be syntactically correct.
- Read `learn/internals/.config.json` before referencing any package manager.
  Never mention a manager other than `env_manager` in user-facing artifacts.
- Be honest about code quality — flag confusing, underdocumented, or poorly
  designed areas. Do not paper over them.
