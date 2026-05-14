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
- **`learn/README.md` exists, no checkboxes ticked:** "Your curriculum is ready —
  open `learn/README.md`. Start with Section 1.1, or say `tutor`, `quiz`, `exercises`."
- **Some checkboxes ticked:** "You're on Section X.Y. Pick up where you left off?"
  → recommend the next unchecked section. One escape line at the end:
  "Or: `tutor`, `quiz`, `exercises`, `status`."

Never dump a decision tree. One recommended action, one escape line.

## Front-Loaded Questions (MANDATORY — start of any fresh pipeline)

**DO NOT SKIP THIS STEP.** Before reading any code, ask the user 3-4 questions in a
single call. This is not a "mid-pipeline pause" — it is the required first step. The
"no pauses" rule means no stopping between analysis and exercise generation. It does
NOT mean "assume defaults and skip the questions." The user's answers directly change
what gets produced (tutoring depth, exercise scaffolding, environment setup).

**What to ask (adapt to the detected repo):**

1. **Domain familiarity.** Detect the library's domain from README/docs and ask:
   "How familiar are you with [domain]?" Options: `[none / textbook / built one]`.
   Show detected default inline.

2. **Language/framework familiarity.** Detect primary language + key framework:
   "JAX familiarity?" `[none / numpy+jit / advanced]`. Skip if the repo is vanilla
   Python/JS/etc. with no specialized framework.

3. **Environment manager.** Auto-detect from lockfiles (uv.lock → uv, poetry.lock →
   poetry, requirements.txt → pip). Show detected default: "I detected `uv.lock` —
   use uv?" Options: `[uv / pip / conda / other]`. Users have strong preferences here
   — do not assume.

4. **Open-ended catch-all.** "Anything else I should know? (learning goals, time
   constraints, specific areas of interest)" — free text, optional.

**Rules:**
- Ask ONLY what the user uniquely knows. Auto-detect everything else silently.
- Show detected defaults inline per question. "Use all defaults" is always an option
  but is never silently chosen on the user's behalf.
- Familiarity answers change tutoring depth and exercise scaffolding — pass them
  through to code-tutor and exercise-gen via a `learn/internals/.config.json`.
- After the user answers, the rest of the pipeline runs end-to-end without stopping.
  This is the ONLY pause — but it IS a pause, and it IS required.

## Shared State

All sub-skills read/write to `<repo-root>/learn/`:

```
learn/
├── README.md              # THE entry point. Phase-grouped checklists.
├── path.html              # Clickable companion (localStorage + export)
├── overview.md            # From repo-analyzer
├── curriculum.md          # From repo-analyzer (anchored sections)
├── cheatsheet.md          # From repo-analyzer
├── notebooks/             # From exercise-gen
│   ├── README.md          # Setup + exercise sequence
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── exercise-*.ipynb
└── internals/             # Build artifacts (accessible but not highlighted)
    ├── .config.json        # User answers from front-loaded questions
    ├── exercise-candidates.md
    ├── exercise-plan.md
    ├── generate_notebooks.py
    └── quiz-bank.md        # Source bank for /learn quiz (mutable)
```

## Progress Tracking

Progress lives in `learn/README.md` as markdown checkboxes:

```markdown
## Phase 1: Usage

| | Section | Read | Do | Test |
|---|---|---|---|---|
| [ ] | 1.1 Core API | [curriculum](#s1.1) | [notebook](notebooks/exercise-01-...) | `/learn quiz 1.1` |
| [x] | 1.2 Config   | [curriculum](#s1.2) | [notebook](notebooks/exercise-02-...) | `/learn quiz 1.2` |
```

No separate `.progress` file. The orchestrator parses these checkboxes. `learn/path.html`
mirrors this state in localStorage with a round-trip export button.

## Silent Defaults (never ask the user about these)

- Haiku validation: always run. Token cost is acceptable.
- Subagent fan-out: auto when exercise count > ~6-8. Not user-facing.
- Filename slugging: always strip non-alphanumerics.
- Output directory: always `learn/`.
- Build artifact location: always `learn/internals/`.
