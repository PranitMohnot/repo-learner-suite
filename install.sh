#!/bin/bash
# Install (or update) repo-learner skill suite.
#
# Usage:
#   ./install.sh                       # Claude Code, global (default)
#   ./install.sh --claude              # Claude Code, global (explicit)
#   ./install.sh --codex               # Codex CLI, global
#   ./install.sh --gemini              # Gemini CLI, global
#   ./install.sh --all                 # Install to all three
#   ./install.sh --gemini --codex      # Or combine any flags
#   ./install.sh --local               # Per-project (append to any above)
#
# Targets (global / --local):
#   Claude Code  ~/.claude/skills/  /  ./.claude/skills/
#   Codex CLI    ~/.agents/skills/  /  ./.agents/skills/
#   Gemini CLI   ~/.gemini/skills/  /  ./.gemini/skills/
#
# See PLATFORMS.md for the platform mapping. Re-run to update —
# overwrites skill files only; user-generated learn/ directories are
# never touched.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS="repo-learner repo-analyzer exercise-gen code-tutor code-quiz"

DO_CLAUDE=false
DO_CODEX=false
DO_GEMINI=false
LOCAL=false

for arg in "$@"; do
    case "$arg" in
        --claude) DO_CLAUDE=true ;;
        --codex)  DO_CODEX=true ;;
        --gemini) DO_GEMINI=true ;;
        --all)    DO_CLAUDE=true; DO_CODEX=true; DO_GEMINI=true ;;
        --local)  LOCAL=true ;;
        -h|--help)
            sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Unknown arg: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

# Default to Claude Code when no platform flag is given.
if ! $DO_CLAUDE && ! $DO_CODEX && ! $DO_GEMINI; then
    DO_CLAUDE=true
fi

install_for() {
    local platform=$1
    local skills_base cmd_dir

    case "$platform" in
        claude)
            if $LOCAL; then skills_base=".claude/skills"; cmd_dir=".claude/commands"
            else            skills_base="$HOME/.claude/skills"; cmd_dir="$HOME/.claude/commands"; fi
            ;;
        codex)
            if $LOCAL; then skills_base=".agents/skills"; cmd_dir=""
            else            skills_base="$HOME/.agents/skills"; cmd_dir=""; fi
            ;;
        gemini)
            if $LOCAL; then skills_base=".gemini/skills"; cmd_dir=".gemini/commands"
            else            skills_base="$HOME/.gemini/skills"; cmd_dir="$HOME/.gemini/commands"; fi
            ;;
    esac

    echo ""
    echo "=== $platform → $skills_base/ ==="
    if [ -f "$skills_base/repo-learner/SKILL.md" ]; then
        echo "(updating existing installation)"
    fi

    for skill in $SKILLS; do
        local src="$SCRIPT_DIR/$skill"
        local dst="$skills_base/$skill"
        if [ ! -d "$src" ]; then
            echo "  SKIP $skill (not found at $src)"
            continue
        fi
        mkdir -p "$dst"

        # SKILL.md: if a <platform>.skill-meta.yaml overlay exists, merge it
        # into the installed file's frontmatter (just before the closing ---).
        # Else plain copy — keeps the source SKILL.md platform-neutral.
        local overlay="$src/$platform.skill-meta.yaml"
        if [ -f "$overlay" ]; then
            local second_dashes
            second_dashes=$(grep -n '^---$' "$src/SKILL.md" | sed -n '2p' | cut -d: -f1)
            if [ -n "$second_dashes" ]; then
                # Use printf '%s\n' "$(<file)" idiom: strips any trailing
                # newlines from the overlay, then emits exactly one. Avoids
                # the closing --- getting smushed onto the last overlay line
                # if the overlay file is missing a trailing newline.
                head -n $((second_dashes - 1)) "$src/SKILL.md" > "$dst/SKILL.md"
                printf '%s\n' "$(cat "$overlay")" >> "$dst/SKILL.md"
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

    # Slash commands — only for platforms with a real slash surface.
    if [ -n "$cmd_dir" ]; then
        mkdir -p "$cmd_dir"
        for skill in $SKILLS; do
            if [ -d "$SCRIPT_DIR/$skill/commands" ]; then
                cp "$SCRIPT_DIR/$skill/commands/"*.md "$cmd_dir/" 2>/dev/null || true
            fi
        done
    fi

    print_usage "$platform"
}

print_usage() {
    local platform=$1
    case "$platform" in
        claude)
            cat <<'EOF'

  Slash commands installed.
    /learn                   Smart default — picks up where you left off
    /learn analyze <path>    Analyze a codebase (expensive, thorough)
    /learn exercises         Generate Jupyter notebook exercises
    /learn tutor [section]   Socratic tutoring
    /learn quiz [section]    Adaptive quiz
    /learn status            Progress summary
  Start with:  /learn analyze .
EOF
            ;;
        codex)
            cat <<'EOF'

  No slash commands on Codex. Invoke in prose:
    "analyze this codebase"        → repo-analyzer
    "tutor me on section 1.1"      → code-tutor
    "quiz me on section 1.3"       → code-quiz
    "make me exercises"            → exercise-gen
    "help me learn this repo"      → repo-learner (orchestrator)
EOF
            ;;
        gemini)
            cat <<'EOF'

  Slash commands installed (same as Claude Code):
    /learn                   Smart default
    /learn analyze <path>    Analyze a codebase
    /learn exercises         Generate Jupyter notebook exercises
    /learn tutor [section]   Socratic tutoring
    /learn quiz [section]    Adaptive quiz
    /learn status            Progress summary
  Prose invocation also works (autonomous skill activation).
  Use Shift+Tab to toggle Plan / Auto modes.
EOF
            ;;
    esac
}

if $DO_CLAUDE; then install_for "claude"; fi
if $DO_CODEX;  then install_for "codex";  fi
if $DO_GEMINI; then install_for "gemini"; fi

echo ""
echo "Done. See PLATFORMS.md for the full mapping. Re-run to update."
