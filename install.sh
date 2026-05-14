#!/bin/bash
# Install (or update) repo-learner skill suite.
#
# Usage:
#   ./install.sh                    # Claude Code, global    (~/.claude/skills/)
#   ./install.sh --local            # Claude Code, project   (./.claude/skills/)
#   ./install.sh --codex            # Codex CLI, global      (~/.agents/skills/)
#   ./install.sh --codex --local    # Codex CLI, project     (./.agents/skills/)
#   ./install.sh --gemini           # Gemini CLI, global     (~/.gemini/skills/)
#   ./install.sh --gemini --local   # Gemini CLI, project    (./.gemini/skills/)
#
# See PLATFORMS.md for the platform mapping. Re-run to update — overwrites
# skill files only; user-generated learn/ directories are never touched.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS="repo-learner repo-analyzer exercise-gen code-tutor code-quiz"

PLATFORM="claude"
LOCAL=false
for arg in "$@"; do
    case "$arg" in
        --codex)  PLATFORM="codex" ;;
        --gemini) PLATFORM="gemini" ;;
        --local)  LOCAL=true ;;
        -h|--help)
            sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Unknown arg: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

# Resolve install roots based on platform + scope.
if [ "$PLATFORM" = "gemini" ]; then
    if $LOCAL; then
        SKILLS_BASE=".gemini/skills"
        CMD_DIR=".gemini/commands"
    else
        SKILLS_BASE="$HOME/.gemini/skills"
        CMD_DIR="$HOME/.gemini/commands"
    fi
    echo "Installing for Gemini CLI to $SKILLS_BASE/..."
elif [ "$PLATFORM" = "codex" ]; then
    if $LOCAL; then
        SKILLS_BASE=".agents/skills"
        CMD_DIR=""  # Codex has no documented slash-command surface
    else
        SKILLS_BASE="$HOME/.agents/skills"
        CMD_DIR=""
    fi
    echo "Installing for Codex CLI to $SKILLS_BASE/..."
else
    if $LOCAL; then
        SKILLS_BASE=".claude/skills"
        CMD_DIR=".claude/commands"
    else
        SKILLS_BASE="$HOME/.claude/skills"
        CMD_DIR="$HOME/.claude/commands"
    fi
    echo "Installing for Claude Code to $SKILLS_BASE/..."
fi

# Detect fresh install vs update
if [ -f "$SKILLS_BASE/repo-learner/SKILL.md" ]; then
    echo "(Updating existing installation)"
fi

for skill in $SKILLS; do
    src="$SCRIPT_DIR/$skill"
    dst="$SKILLS_BASE/$skill"

    if [ ! -d "$src" ]; then
        echo "  SKIP $skill (not found at $src)"
        continue
    fi

    mkdir -p "$dst"

    # Install SKILL.md. For Gemini, merge gemini.skill-meta.yaml into the
    # frontmatter (just before the closing `---`). For other platforms,
    # plain copy — keeps the source SKILL.md platform-neutral.
    overlay="$src/gemini.skill-meta.yaml"
    if [ "$PLATFORM" = "gemini" ] && [ -f "$overlay" ]; then
        second_dashes=$(grep -n '^---$' "$src/SKILL.md" | sed -n '2p' | cut -d: -f1)
        if [ -n "$second_dashes" ]; then
            head -n $((second_dashes - 1)) "$src/SKILL.md" > "$dst/SKILL.md"
            cat "$overlay" >> "$dst/SKILL.md"
            tail -n +"$second_dashes" "$src/SKILL.md" >> "$dst/SKILL.md"
        else
            cp "$src/SKILL.md" "$dst/SKILL.md"
        fi
    else
        cp "$src/SKILL.md" "$dst/SKILL.md"
    fi

    if [ -d "$src/references" ]; then
        mkdir -p "$dst/references"
        cp "$src/references/"* "$dst/references/"
    fi

    if [ -d "$src/scripts" ]; then
        mkdir -p "$dst/scripts"
        cp "$src/scripts/"* "$dst/scripts/"
    fi

    echo "  ✓ $skill"
done

# Slash commands
if [ -n "$CMD_DIR" ]; then
    mkdir -p "$CMD_DIR"
    for skill in $SKILLS; do
        if [ -d "$SCRIPT_DIR/$skill/commands" ]; then
            cp "$SCRIPT_DIR/$skill/commands/"*.md "$CMD_DIR/" 2>/dev/null || true
        fi
    done
fi

count=$(echo $SKILLS | wc -w | tr -d ' ')
echo ""
echo "Installed $count skills."
echo ""

if [ "$PLATFORM" = "codex" ]; then
    cat <<'EOF'
Codex usage:
  Slash commands are not installed (Codex doesn't have an equivalent surface).
  Invoke the suite in prose:
    "analyze this codebase"        → repo-analyzer
    "tutor me on section 1.1"      → code-tutor
    "quiz me on section 1.3"       → code-quiz
    "make me exercises"            → exercise-gen
    "help me learn this repo"      → repo-learner (orchestrator)

See PLATFORMS.md for the full mapping and caveats.
EOF
elif [ "$PLATFORM" = "gemini" ]; then
    cat <<'EOF'
Gemini usage:
  Slash commands:
    /learn analyze <path>    Analyze a codebase (expensive, thorough)
    /learn exercises         Generate Jupyter notebook exercises
    /learn tutor [section]   Socratic tutoring mode
    /learn quiz [section]    Adaptive quiz
    /learn status            Check your progress

  Interactive activation:
    Skills trigger autonomously on phrases like "help me learn this repo".
    Use Shift+Tab to toggle between Plan and Auto modes.

Start with:  /learn analyze .
EOF
else
    cat <<'EOF'
Commands:
  /learn analyze <path>    Analyze a codebase (expensive, thorough)
  /learn exercises         Generate Jupyter notebook exercises
  /learn tutor [section]   Socratic tutoring mode
  /learn quiz [section]    Adaptive quiz
  /learn status            Check your progress

Start with:  /learn analyze .
EOF
fi

echo ""
echo "To update later, re-run this script."
