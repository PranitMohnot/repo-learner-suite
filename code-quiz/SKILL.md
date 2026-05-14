---
name: code-quiz
description: >
  Quiz the user on their understanding of a codebase, either per-section from a
  curriculum or on recent code changes. Adaptive difficulty, one question at a time,
  always shows code context, honest verdicts. Trigger on "/learn quiz", "quiz me",
  "test my understanding", "grill me", "do I understand this", or when another skill
  delegates quizzing. Works in two modes: curriculum quiz (from learn/quiz-bank.md)
  and diff quiz (from git changes, for post-autonomous-session comprehension checks).
---

# Code Quiz

Adaptive quiz on codebase understanding. Two modes:

## Mode 1: Curriculum Quiz (`/learn quiz [section-id | --full]`)

Pull questions from `learn/internals/quiz-bank.md`. If the user has seen them, generate
fresh questions from the section's source files.

**The quiz bank is a working document.** When generating fresh questions, APPEND them to
`learn/internals/quiz-bank.md` so they're available for future runs. If a question turns
out to be ambiguous or misleading (user gives a reasonable answer that the "correct" answer
doesn't cover), edit the question or answer in the bank. Treat quiz-bank.md as a living
resource that improves with each quiz session.

## Mode 2: Diff Quiz (`/quiz` or `/quiz last N commits`)

Quiz on recent code changes — designed for after autonomous Claude Code sessions.

1. Gather the diff scope:
   - No args → `git diff` + `git diff --cached`. If empty, `git diff HEAD~1`.
   - `last N commits` → `git diff HEAD~N`
   - `<branch>` → `git diff main..<branch>`
2. Run `git diff --stat` for the overview, then read the full diff.
3. Generate questions from the changes.

## Question Flow

**One at a time. Always.** Don't show the next question until the current one is answered.

For each question:
1. Show the code context (snippet with file path and line numbers)
2. Ask the question
3. Wait
4. Evaluate and give feedback
5. Adjust difficulty, proceed

## Difficulty Distribution (5-7 questions for a section quiz)

- 2 warm-up: "What does X return?", "What type is Y?"
- 2-3 conceptual: "Why X instead of Y?", "What's the tradeoff?"
- 1-2 hard: "What breaks if you change Z?", "Trace this through 3 modules"

**Adaptive:** If they nail warm-ups instantly → skip to conceptual. If they miss
conceptuals → slow down, explain more. If crushing everything → add expert questions.

## Evaluating Answers

- **Correct:** Confirm briefly. "Right. The semaphore bounds concurrent connections."
- **Partially correct:** Acknowledge the right part, push on the gap.
- **Wrong:** Explain the misconception, redirect. Never just "wrong."
- **"I don't know":** Respect it. Give the answer with explanation. Note for summary.

## Summary

After all questions:

```
## Quiz Results: [Section or Diff scope]

**Score: X/Y**

**Strong areas:** [what they understand well]

**Gaps to address:** [specific files/concepts to review, with line references]

**Verdict:** [Ready to continue / Review these areas first / Do not merge until...]
```

Be honest. If they bombed it, say so constructively with specific remediation steps.

## Pre-PR Mode

When the user says "quiz me before I PR" or "don't let me merge until I pass":
- Full quiz on the diff
- Require correct answers on all hard questions
- End with explicit "ready to merge" / "not ready — review these areas" verdict
