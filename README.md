# repo-learner-suite

A suite of agent skills for deeply learning unfamiliar codebases through
structured curricula, exercises, Socratic tutoring, and adaptive quizzes.

**Agents:** Claude Code, Codex CLI, Gemini CLI — one source, install per
platform. See [PLATFORMS.md](PLATFORMS.md) for the mapping.

**Languages:** Python today, with a language-adapter contract for adding
more (see [PLATFORMS.md](PLATFORMS.md) → Languages). The orchestrator
auto-detects the repo (`.py` / `pyproject.toml` / `requirements.txt` →
python) and notebooks emit with the matching kernel + env-file
scaffolding.

## Skills

| Skill | Purpose | Token cost |
|-------|---------|-----------|
| **repo-learner** | Orchestrator — routes `/learn` commands, one recommended action | Minimal |
| **repo-analyzer** | Deep-reads codebase → curriculum, cheatsheet, quiz bank | High |
| **exercise-gen** | Generates Jupyter notebook exercises with mock-student validation | High |
| **code-tutor** | Socratic tutoring per curriculum section | Low per turn |
| **code-quiz** | Adaptive quizzes, edits its own question bank over time | Low per turn |

## Install

```bash
chmod +x install.sh

# Claude Code, global (default — installs to ~/.claude/skills/)
./install.sh
./install.sh --claude              # explicit equivalent

# Codex CLI, global (installs to ~/.agents/skills/, no slash commands)
./install.sh --codex

# Gemini CLI, global (installs to ~/.gemini/skills/, with slash commands)
./install.sh --gemini

# Multiple platforms at once
./install.sh --claude --gemini
./install.sh --all                 # all three

# Per-project (append --local to any of the above)
./install.sh --local
./install.sh --gemini --local
```

## Update

Re-run `./install.sh` with the same flags. Overwrites skill definitions
only — `learn/` directories inside projects (curricula, notebooks,
progress) are untouched.

## Quick Start

### Claude Code

```
/learn                               # Smart default — picks up where you left off
/learn analyze .                     # Deep-scan → full learning package
/learn exercises                     # Generate Jupyter notebooks
/learn tutor 1.1                     # Socratic tutoring
/learn quiz 1.1                      # Adaptive quiz
/learn status                        # Progress summary
```

### Codex CLI

Slash commands aren't available on Codex — invoke in plain prose. Skill
description matching does the routing.

```
analyze this codebase                # → repo-analyzer
make me exercises                    # → exercise-gen
tutor me on section 1.1              # → code-tutor
quiz me on section 1.3               # → code-quiz
help me learn this repo              # → repo-learner (orchestrator)
```

### Gemini CLI

Same slash commands as Claude Code (use Shift+Tab to toggle Plan / Auto
modes):

```
/learn                               # Smart default
/learn analyze .                     # Deep-scan → full learning package
/learn exercises                     # Generate Jupyter notebooks
/learn tutor 1.1                     # Socratic tutoring
/learn quiz 1.1                      # Adaptive quiz
/learn status                        # Progress summary
```

Prose invocation also works (autonomous skill activation on phrases like
"help me learn this repo").

## What it produces

```
learn/
├── curriculum.md          # THE document. Section 0 = overview. Per-step
│                          # checkboxes. Exercises linked inline.
├── curriculum.html        # Interactive HTML mirror (clickable checkboxes,
│                          # localStorage, hint/solution dropdowns).
├── cheatsheet.md          # Quick-reference card.
├── notebooks/             # Exercise notebooks
│   ├── README.md          # Setup (uses your env_manager) + sequence
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── exercise-*.ipynb
└── internals/             # Build artifacts
    ├── .config.json       # User familiarity answers
    ├── exercise-candidates.md
    ├── exercise-plan.md   # Manifest — coordinates analyzer + exercise-gen
    ├── quiz-bank.md       # Mutable — quiz skill edits this over time
    └── validation/        # Per-notebook mock-student + nbconvert reports
```

## UX flow

1. `/learn` (or "help me learn this codebase" on Codex) — asks 4–5 questions
   (domain familiarity, framework familiarity, env manager, depth
   preference, open-ended). One call, then hands off.
2. Pipeline runs end-to-end: analyze → generate exercises → validate
   (mock-student + nbconvert) → regenerate curriculum.html → reconcile.
3. User opens `learn/curriculum.md` — or `learn/curriculum.html` for the
   interactive companion. Scrolls through, clicking out to notebooks and
   terminal as the curriculum directs.

## Depth modes

Front-loaded question: **Comprehensive** (default — deep read, 8–12
exercises, full QA) or **Light** (~1/4 cost — leaner curriculum, 3–5
exercises, skips mock-student validation; nbconvert still runs).

## Pedagogy

Exercise types progress naturally: Use → Modify → Debug → Create → Compare.
Each exercise introduces exactly one new concept. Quizzes mix six question
types (recall, conceptual, predictive, diagnostic, applied, architectural)
without ever naming them to the user.

Analysis follows a global→local cognitive flow (project overview →
architecture → local functions), mirroring how expert code auditors onboard
new codebases.

## License

MIT — see [LICENSE](LICENSE).
