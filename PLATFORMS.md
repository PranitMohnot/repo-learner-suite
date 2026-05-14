# Platforms

Skills in this suite are written agent-neutral and installable on multiple
CLI platforms. The instruction content (curriculum format, manifest contract,
exercise pipeline, quiz palette) is universal. Only plumbing differs.

| | Claude Code (default) | Codex CLI | Gemini CLI |
|---|---|---|---|
| **Install command** | `./install.sh` | `./install.sh --codex` | not yet supported |
| **Global skills dir** | `~/.claude/skills/` | `~/.agents/skills/` | — |
| **Project skills dir** | `.claude/skills/` | `.agents/skills/` | — |
| **Slash commands** | `/learn`, `/learn analyze`, etc. (in `~/.claude/commands/`) | none — invoke in prose | — |
| **Project instructions** | `CLAUDE.md` | `AGENTS.md` | `GEMINI.md` |
| **AskUserQuestion equivalent** | `AskUserQuestion` tool | `ask_user` (or just prompt in prose) | — |
| **TodoWrite equivalent** | `TodoWrite` tool | none built-in; skills manage state themselves | — |
| **Mock-student model** | Haiku (fast tier) | GPT-5 Mini or your tier's fast equivalent | — |
| **Subagent dispatch** | `Agent` tool (parallel-friendly) | `task_spawn` (conservative — may inline) | — |
| **Notebook kernel registration** | `ipykernel install --user` | same | — |

## Invocation differences in detail

### Claude Code
Slash commands route through `commands/learn.md`. The orchestrator skill
parses arguments. Implicit invocation works too — description matching on
phrases like "help me learn this repo."

### Codex CLI
No documented slash-command surface. Skills are invoked by description
matching (same model as CC) or by explicit prefix in some clients
(`$repo-learner ...`). The skill prose works the same — Codex's model
reads the same SKILL.md and follows the same instructions.

In practice: ask Codex "analyze this codebase," "tutor me on section 1.1,"
"quiz me on section 1.3," and the right skill activates.

### Gemini CLI (not yet supported)
Skills activate via a different mechanism — `activate_skill` tool, metadata
loaded at session start, full content fetched on demand. This differs
enough from the "always-loaded SKILL.md" model that some adaptation work
is needed. If you want this, file an issue.

## Subagent behavior caveat (Codex)

Codex is conservative about dispatching parallel subagents. Even with
explicit "spawn N subagents in parallel" wording, it may inline the work
instead. Practical effect on this suite: exercise-gen's Stage 4a fan-out
(one notebook per subagent) may run serially on Codex. Output is correct
either way — just slower.

If you see serialized validation runs on a 10+ exercise set and want true
parallelism, prompt Codex more explicitly: "Use the task_spawn tool to
dispatch N agents in parallel, one per notebook spec."

## Mock-student model defaults

The `exercise-gen/SKILL.md` says "use the cheapest capable model available."
Concretely:

- **Claude Code:** Haiku (the fastest current tier).
- **Codex CLI:** GPT-5 Mini, or whatever the current fast tier is at the
  time. Codex's model picker changes faster than this doc; trust the
  current default.
- The skill prose stays neutral. Mapping happens at dispatch time.

## What to do if Codex (or another platform) diverges further

If platform differences grow beyond what this doc can map in a table, the
right move is to add a small adapter — a script + skill that transforms the
main-branch sources into a platform-specific install tree. Not needed yet.

## Origins

This doc consolidates lessons from earlier `codex-port` and `gemini-port`
branches that hand-maintained separate skill copies. That approach drifted;
this single-source-of-truth approach replaces it.
