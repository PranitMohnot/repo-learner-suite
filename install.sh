#!/bin/bash
# Install (or update) repo-learner skill suite for Claude Code
#
# Usage:
#   ./install.sh            # Install/update globally (default)
#   ./install.sh --local    # Install to current project only
#
# To update: just re-run this script. It overwrites all skill files.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS="repo-learner repo-analyzer exercise-gen code-tutor code-quiz"

if [ "$1" = "--local" ]; then
    BASE=".claude/skills"
    echo "Installing repo-learner suite to project at $BASE/..."
else
    BASE="$HOME/.claude/skills"
    echo "Installing repo-learner suite globally to $BASE/..."
fi

# Detect fresh install vs update
if [ -f "$BASE/repo-learner/SKILL.md" ]; then
    echo "(Updating existing installation)"
    IS_UPDATE=true
else
    IS_UPDATE=false
fi

for skill in $SKILLS; do
    src="$SCRIPT_DIR/$skill"
    dst="$BASE/$skill"

    if [ ! -d "$src" ]; then
        echo "  SKIP $skill (not found at $src)"
        continue
    fi

    mkdir -p "$dst"
    # Copy SKILL.md
    cp "$src/SKILL.md" "$dst/SKILL.md"

    # Copy references/ if exists
    if [ -d "$src/references" ]; then
        mkdir -p "$dst/references"
        cp "$src/references/"* "$dst/references/"
    fi

    # Copy scripts/ if exists
    if [ -d "$src/scripts" ]; then
        mkdir -p "$dst/scripts"
        cp "$src/scripts/"* "$dst/scripts/"
    fi

    echo "  ✓ $skill"
done

# Install slash commands
if [ "$1" = "--local" ]; then
    CMD_DIR=".claude/commands"
else
    CMD_DIR="$HOME/.claude/commands"
fi

mkdir -p "$CMD_DIR"

# Generate slash commands from skill commands/ directories
for skill in $SKILLS; do
    if [ -d "$SCRIPT_DIR/$skill/commands" ]; then
        cp "$SCRIPT_DIR/$skill/commands/"*.md "$CMD_DIR/" 2>/dev/null || true
    fi
done

echo ""
echo "Installed $( echo $SKILLS | wc -w | tr -d ' ' ) skills."
echo ""
echo "Commands:"
echo "  /learn analyze <path>    Analyze a codebase (expensive, thorough)"
echo "  /learn exercises         Generate Jupyter notebook exercises"
echo "  /learn tutor [section]   Socratic tutoring mode"
echo "  /learn quiz [section]    Adaptive quiz"
echo "  /learn status            Check your progress"
echo ""
echo "Start with:  /learn analyze ."
echo ""
echo "To update later, re-run this script."
