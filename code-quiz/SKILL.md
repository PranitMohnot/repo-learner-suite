---
name: code-quiz
description: >
  Quiz the user on their understanding of a curriculum section. Adaptive,
  one question at a time, always shows code context, honest verdicts.
  Trigger on "/learn quiz", "quiz me", "test my understanding", "grill me",
  "do I understand this", or when another skill delegates quizzing.
  Requires learn/curriculum.md and learn/internals/quiz-bank.md (run
  repo-analyzer first).
---

# Code Quiz

Adaptive quiz on a curriculum section. Pulls from
`learn/internals/quiz-bank.md`; generates fresh questions from source when
the bank is exhausted or the user has seen the existing ones.

The quiz bank is a working document. APPEND new questions when generated.
EDIT existing questions or answers when the user gives a reasonable answer
the "correct" answer doesn't cover. Treat the bank as a living resource
that improves with each session.

## Entering a session

1. Resolve the section: explicit ID (`/learn quiz 1.3`), `--full` for the
   whole curriculum, or default to the next unchecked section.
2. Load the section's questions from the bank, the section text from
   curriculum.md, and the source files it cites.
3. Plan 5–7 questions for a single section, more for `--full`.

## Question palette (mix; do not name the types to the user)

Pull from several of these in any quiz. The user should experience a
varied, well-crafted set — not a labeled taxonomy. Never say "this is a
conceptual question" or announce the type; just ask.

Examples below span several libraries deliberately — the palette is
domain-agnostic. Draw real questions from the codebase being quizzed.

- **Recall** — vocabulary. "What does `Session.execute()` return in
  SQLAlchemy 2.x?" "What's the default `timeout` for `httpx.Client`?"
  Fast confidence-builders.
- **Conceptual** — mental model. "Why does pydantic validate at
  construction time instead of on access?" "What invariant does
  `Session.begin()` preserve about transaction state?"
- **Predictive** — cause and effect. "If you drop `pool_size` from 5 to 1
  under concurrent load, what changes?" "What happens on the first call
  to an `@lru_cache`'d function vs the second?"
- **Diagnostic** — error model. Show plausibly broken code: "This pydantic
  model raises `ValidationError` on construction. What's wrong?"
- **Applied** — transfer. "You want to add request signing to every call
  on an existing `httpx.AsyncClient`. Sketch how."
- **Architectural** — design intent. "Why does pandas split `merge` and
  `join` into two methods?" "Why does FastAPI use dependency injection
  for auth rather than middleware?"

A 5–7 question quiz should span at least 3 types. All-recall is boring; all-architectural is exhausting; all-predictive becomes guessing.
Quizzes should also adapt to the user's stated goals (e.g. do not hammer low-level implementation details if the user just wants a curosry API understanding).

## Depth bands (orthogonal to type)

Any type can be asked shallow or deep.

- **Warm-up** (1–2 per quiz): single fact, short answer expected.
- **Normal** (2–3): requires connecting two pieces or one short trace.
- **Deep** (1–2): multi-step, multi-file, or genuinely novel application.

Adaptive: if the warm-ups land instantly, skip them next time and start
at normal. If they miss normals, slow down and explain more before
continuing. If they crush everything, push into deep + types they haven't
seen yet.

## Question flow

One question at a time. Never preview the next.

For each question:
1. Show the code context (file path + line numbers + the snippet).
2. Ask the question.
3. Wait for the answer.
4. Evaluate honestly:
   - **Correct.** Confirm in one line — say *why* it's right, not just "yes."
   - **Partial.** Acknowledge the right part, push on the gap with a
     follow-up that doesn't give away the missing piece.
   - **Wrong.** Name the misconception. Redirect with a hint to the file
     or concept that resolves it. Never just "wrong."
   - **"I don't know."** Respect it. Give the answer with the explanation
     the section earned. Note it for the summary.
5. Adjust the next question's type/depth based on what just happened.

## Summary

After the last question:

```
## Quiz: Section X.Y

Score: X/Y

Strong: [concepts they clearly have]
Gaps: [specific files/lines/concepts to revisit]
Suggested next: [continue to X.Z / revisit this section / focused re-read of file]
```

Be honest. If they bombed it, say so constructively with specific
remediation. If they aced it, say that too — and consider promoting them
into deeper questions next time.

## Tone

Senior engineer running a whiteboard session. Direct, not harsh.
Encouraging when earned. Honest about confusion. Never patronizing, never
fake-cheerful, never theatrical about wrong answers.
