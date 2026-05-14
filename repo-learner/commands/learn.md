# /learn

Entry point for the repo-learner skill suite.

## Routing

Parse the first word of $ARGUMENTS as the subcommand. If empty, check state and
recommend ONE action (see orchestrator SKILL.md for the logic — never dump a menu).

| Subcommand | Sub-skill |
|---|---|
| `analyze [path] [--focus topic]` | repo-analyzer |
| `exercises [section]` | exercise-gen |
| `tutor [section-id]` | code-tutor |
| `quiz [section-id\|--full]` | code-quiz |
| `status` | Parse `learn/README.md` checkboxes, summarize progress |

## Fresh run (no learn/ directory)

1. Auto-detect: primary language, framework, lockfile/package manager.
2. **MANDATORY: Ask 3-4 questions in one call** (see orchestrator SKILL.md
   "Front-Loaded Questions"). Do NOT skip this and assume defaults — the user
   has preferences (especially env manager) that you cannot infer.
3. Save answers to `learn/internals/.config.json`.
4. Hand off to repo-analyzer, then exercise-gen. No stops between.

## Status

Parse checkbox state from `learn/README.md` table rows. Count checked vs unchecked
per phase. Suggest the next unchecked section.
