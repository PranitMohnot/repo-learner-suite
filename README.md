# repo-learner-suite

A suite of agent skills for deeply learning unfamiliar codebases through
structured curricula, exercises, Socratic tutoring, and adaptive quizzes.

Primary target is Claude Code. Codex CLI is supported via a flag on
`install.sh` — see [PLATFORMS.md](PLATFORMS.md) for the mapping. Gemini CLI
is not yet supported (its skill activation model differs enough to need
real work).

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

# Claude Code (default — installs to ~/.claude/skills/)
./install.sh

# Codex CLI (installs to ~/.agents/skills/, no slash commands)
./install.sh --codex

# Per-project only (append --local)
./install.sh --local
./install.sh --codex --local
```

## Update

Re-run `./install.sh`. Overwrites skill definitions only — `learn/`
directories inside projects (curricula, notebooks, progress) are untouched.

## Quick Start

On Claude Code:

```
/learn                               # Smart default — picks up where you left off
/learn analyze .                     # Deep-scan → full learning package
/learn exercises                     # Generate Jupyter notebooks
/learn tutor 1.1                     # Socratic tutoring
/learn quiz 1.1                      # Adaptive quiz
/learn status                        # Progress summary
```

On Codex, slash commands aren't available — just ask the agent in plain
prose: "analyze this codebase," "tutor me on section 1.1," "quiz me," etc.
Description-based skill invocation does the routing.

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
