# Platforms

Skills in this suite are written agent-neutral and installable on multiple
CLI platforms. The instruction content (curriculum format, manifest contract,
exercise pipeline, quiz palette) is universal. Only plumbing differs.

| | Claude Code (default) | Codex CLI | Gemini CLI |
|---|---|---|---|
| **Install command** | `./install.sh` | `./install.sh --codex` | `./install.sh --gemini` |
| **Global skills dir** | `~/.claude/skills/` | `~/.agents/skills/` | `~/.gemini/skills/` |
| **Project skills dir** | `.claude/skills/` | `.agents/skills/` | `.gemini/skills/` |
| **Slash commands** | `/learn`, `/learn analyze`, etc. (in `~/.claude/commands/`) | none — invoke in prose | `/learn ...` (in `~/.gemini/commands/`) |
| **Project instructions** | `CLAUDE.md` | `AGENTS.md` | `GEMINI.md` |
| **AskUserQuestion equivalent** | `AskUserQuestion` tool | `ask_user` (or just prompt in prose) | prompt in prose |
| **TodoWrite equivalent** | `TodoWrite` tool | none built-in; skills manage state themselves | none built-in |
| **Mock-student model** | Haiku (fast tier) | GPT-5 Mini or your tier's fast equivalent | Gemini Flash |
| **Subagent dispatch** | `Agent` tool (parallel-friendly) | `task_spawn` (conservative — may inline) | platform-native; behavior varies |
| **Skill activation model** | always-loaded SKILL.md | always-loaded SKILL.md | metadata loaded at session start, full content via `activate_skill` |
| **Notebook kernel registration** | `ipykernel install --user` | same | same |

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

## Languages

Python is currently the only supported notebook language, but the suite
is built around a language-adapter contract so adding more is a localized
change rather than a refactor. The orchestrator auto-detects the repo's
language (`.py` / `pyproject.toml` / `requirements.txt` → python) and
persists `repo.language` to `learn/internals/.config.json`. Downstream
skills read it; the analyzer itself is language-agnostic.

### The adapter boundary

Each supported language is described by a `LanguageProfile` in
[`exercise-gen/scripts/scaffold_notebook.py`](exercise-gen/scripts/scaffold_notebook.py).
The profile is *only* irreducible plumbing — things the agent cannot
reasonably infer at cell-generation time:

| Field | Why it's in the profile |
|---|---|
| `kernel_name`, `kernel_display_name`, `kernel_language` | Jupyter kernelspec values; concrete strings the agent can't guess |
| `env_managers` (dict: name → install command) | Shell commands that must match what users actually have installed |
| `default_env_manager` | Picked when nothing else is specified |
| (function) env-file generator | Writes `requirements.txt` and the language's equivalents |
| (in `reconcile.py`) forbidden manager set | Names to ban in user-facing artifacts when `env_manager` is different |
| (in `repo-learner/SKILL.md`) detection row | File extensions + project markers for auto-detection |

Things deliberately NOT in the profile:

- Setup / validation / scaffold idioms. The agent knows these from its
  training; enumerating them grows linearly per language without value.
- Allow / forbidden package lists for the "self-contained" rule. Same
  reason — the agent knows what's heavy or platform-specific for each
  ecosystem.

This keeps profiles tiny (~30 lines per language) and avoids paternalizing
the model. It also means each new language is a localized change.

### Adding a new language

1. Add a branch to `generate_env_files` in `scaffold_notebook.py` that
   writes the language's env file(s).
2. Add a `LanguageProfile` entry to `LANGUAGE_PROFILES`.
3. Add the language to the detection table in `repo-learner/SKILL.md`.
4. Add forbidden package-manager names to `reconcile.py`'s
   `PACKAGE_MANAGERS`.

That's it. Don't add per-language prose to skill files — let the agent's
training carry the idioms.

When `LANGUAGE_PROFILES` grows past ~3 languages, promote to YAML files
under `language-profiles/<name>.yaml` loaded at startup. The interface
above is already the schema.

### Polyglot repos

The run-wide `--language` flag (or `.config.json:repo.language`) sets the
notebook default. Individual `ExerciseSpec` entries can override
`language` to mix kernels in one curriculum (when multiple language
profiles exist). Use sparingly; mixed-kernel curricula are harder to
follow than single-language ones.

## Gemini frontmatter overlay

Gemini wants an `allowed-tools:` list in skill frontmatter — a permission
boundary listing the tool names a skill is allowed to invoke. The tool
names are Gemini-specific (`read_file`, `run_shell_command`, etc.) and
would be noise in CC/Codex installs.

Convention: each skill directory carries a `gemini.skill-meta.yaml` file
holding just the Gemini-specific frontmatter additions. The shared
`SKILL.md` stays platform-neutral. `install.sh --gemini` merges the
overlay into the installed `SKILL.md`'s frontmatter (inserted right
before the closing `---`). `install.sh` and `install.sh --codex` ignore
the overlay file and ship `SKILL.md` byte-identical to source.

If a future platform needs its own frontmatter additions, follow the same
convention: a `<platform>.skill-meta.yaml` per skill, merged only when
that platform's install flag is set.

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
