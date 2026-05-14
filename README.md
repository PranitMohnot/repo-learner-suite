# repo-learner-suite

A suite of Claude Code skills for deeply learning unfamiliar codebases through
structured curricula, exercises, Socratic tutoring, and adaptive quizzes.

## Skills

| Skill | Purpose | Token cost |
|-------|---------|-----------|
| **repo-learner** | Orchestrator — routes `/learn` commands, one recommended action | Minimal |
| **repo-analyzer** | Deep-reads codebase → curriculum, overview, cheatsheet, quiz bank | High |
| **exercise-gen** | Generates Jupyter notebook exercises with Haiku validation | High |
| **code-tutor** | Socratic tutoring per curriculum section | Low per turn |
| **code-quiz** | Adaptive quizzes, edits its own question bank over time | Low per turn |

## Install

```bash
chmod +x install.sh

# Global install (default — available in all projects)
./install.sh

# Per-project only
./install.sh --local
```

## Update

Re-run `./install.sh`. Overwrites skill definitions only — your `learn/` directories
(curricula, notebooks, progress) inside projects are untouched.

## Quick Start

```
/learn                               # Smart default — picks up where you left off
/learn analyze .                     # Deep-scan → full learning package
/learn exercises                     # Generate Jupyter notebooks
/learn tutor 1.1                     # Socratic tutoring
/learn quiz 1.1                      # Adaptive quiz
/learn status                        # Progress summary
```

## What it produces

```
learn/
├── README.md              # THE entry point — phase-grouped checklists
├── path.html              # Clickable companion (localStorage + export)
├── overview.md            # Big-picture: what, who, why, how
├── curriculum.md          # Phased learning path with anchored sections
├── cheatsheet.md          # Quick-reference card
├── notebooks/             # Exercise notebooks
│   ├── README.md          # Setup (detects uv/pip) + exercise sequence
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── exercise-*.ipynb
└── internals/             # Build artifacts (accessible, not highlighted)
    ├── .config.json       # User familiarity answers
    ├── exercise-candidates.md
    ├── exercise-plan.md
    └── quiz-bank.md       # Mutable — quiz skill edits this over time
```

## UX flow

1. `/learn` or `/learn analyze .` — asks 3-4 questions (domain familiarity, framework
   familiarity, env manager, open-ended). One call, then hands-off.
2. Pipeline runs end-to-end: analyze → generate exercises → validate with Haiku. No
   mid-pipeline stops.
3. User opens `learn/README.md` — phase-grouped checklist with Read/Do/Test columns.
4. Recommended three-pane setup: `path.html` in preview, current artifact in editor,
   `/learn` chat as driver.

## Pedagogy

Exercise types progress naturally: Use → Modify → Debug → Create → Compare. Each
exercise introduces exactly one new concept. Exercises map to curriculum sections so
the README.md checklist rows have natural Read/Do/Test entries.

Analysis follows a global→local cognitive flow (project overview → architecture →
local functions), mirroring how expert code auditors onboard new codebases.
