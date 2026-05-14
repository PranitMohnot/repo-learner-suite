# Exercise Types

Five exercise types for learning a codebase, ordered from guided to independent.
Each type produces a different kind of understanding. The progression is natural:
call the API → change its behavior → find bugs → build something new → compare approaches.

## Type 1: Use

**What the learner does:** Call the API correctly to accomplish a stated goal. Follow
an existing pattern with new inputs.

**When to use:** First exercises in a sequence. The learner needs to know the basic
vocabulary before they can think critically about it.

**What it tests:** Can they get the library to do the thing? Do they know the function
signatures, required arguments, return types?

**Structure:**
- Show a working example (guided cells)
- Ask them to do a similar thing with different inputs
- Validate the output matches expected

**Good examples (varied domains):**
- *Data library:* "Use `pd.merge()` to join the `orders` and `customers` DataFrames on
  `customer_id`, keeping only orders that have a matching customer."
- *HTTP client:* "Use `httpx.AsyncClient` to make a GET request to the /users endpoint
  with a timeout of 5 seconds and parse the JSON response."
- *ML framework:* "Use `model.fit()` to train the classifier on the provided dataset.
  Pass in a validation split of 20% and set early stopping with patience=3."

**Bad example:** "Use the library." (Too vague — what specifically?)

**Pitfall:** These can be too easy. Make sure the learner has to read the docs or code
to figure out the arguments — not just copy-paste from the guided example with one number
changed. The guided example should use a *different* function or pattern from the exercise.

## Type 2: Modify

**What the learner does:** Take working code and change its behavior in a specific way.
The change requires understanding what the code does, not just where to edit.

**When to use:** After "use" exercises. The learner knows the API; now they need to
understand the *effect* of different choices.

**What it tests:** Do they understand what the parameters/design choices actually control?
Can they predict the effect of a change before running it?

**Structure:**
- Provide complete, working code
- Ask them to modify it to achieve a different behavior
- Include a "predict before you run" prompt
- Validate the modified behavior

**Good examples:**
- *Task queue:* "The worker pool below uses 4 threads. Modify it to use async I/O instead.
  Before running: predict how throughput will change for CPU-bound vs I/O-bound tasks.
  Then benchmark both and explain the result."
- *ORM:* "The query below uses eager loading for related objects. Modify it to use lazy
  loading. Before running: predict which page will load faster — the list view or the
  detail view. Then profile both."

**Bad example:** "Change the threshold from 0.5 to 0.3." (Too mechanical — no understanding
required.)

**Pitfall:** Make sure the modification requires understanding, not just text substitution.
If the learner can succeed by grep-and-replace, the exercise isn't doing its job.

## Type 3: Debug

**What the learner does:** Given broken code, find the bug and fix it. The bug should
be conceptual (misunderstanding how the library works), not syntactic (typos).

**When to use:** Mid-sequence. The learner needs enough context to have an opinion about
what "correct" looks like.

**What it tests:** Can they read code critically? Do they understand the library's
invariants well enough to spot violations?

**Structure:**
- Provide code that runs but produces wrong results (or crashes with an informative error)
- The bug should be plausible — something a real user would actually do wrong
- Ask them to identify the bug, explain why it's wrong, and fix it
- Validate the fix

**Good examples:**
- *Event system:* "This code registers two event handlers, but only the first one fires.
  The code runs without errors. Find the bug." (The bug: the second handler overwrites
  the first because `on()` replaces instead of appending — need `add_listener()` instead.)
- *Data pipeline:* "This ETL pipeline silently drops ~15% of rows during the join step.
  No errors are raised. Find where the data loss happens and fix it." (The bug: an inner
  join where a left join was needed — unmatched keys are silently dropped.)

**Bad example:** "Fix the typo on line 12." (No understanding required.)

**Design the bug carefully.** The best debug exercises teach a specific misconception.
Think about what users commonly get wrong (check GitHub issues if available) and encode
that misunderstanding in the broken code. The learner should have an "aha" moment when
they find it.

## Type 4: Create

**What the learner does:** Build something new that isn't a copy of an existing example.
They must make design decisions, not just implementation decisions.

**When to use:** Late in the sequence. The learner has used, modified, and debugged the
library enough to create something independently.

**What it tests:** Can they apply the library to a novel problem? Can they structure
their own code around the library's patterns?

**Structure:**
- State the goal, not the method
- Provide minimal scaffold — just the function signature and a description of expected behavior
- Validation checks behavior, not implementation (don't assert they used a specific function)
- Include multiple valid approaches in the solution

**Good examples:**
- *Web framework:* "Build a rate-limiting middleware that limits each IP to 100 requests
  per minute. It should work with the existing middleware chain and return a 429 response
  with a Retry-After header when the limit is hit."
- *Plotting library:* "Create a reusable `dashboard()` function that takes a DataFrame
  and generates a 2x2 grid of plots: distribution, time series, correlation matrix, and
  top-N bar chart. It should accept a config dict for customization."

**Bad example:** "Implement `MyHandler` that subclasses `HandlerBase`." (Too prescriptive
about implementation — let them figure out the approach.)

**Pitfall:** These can be too hard if the learner hasn't been prepared by earlier exercises.
Every concept needed for the "create" exercise should have appeared in a "use" or "modify"
exercise earlier. The novelty is in the *combination*, not in any single concept.

## Type 5: Compare

**What the learner does:** Implement the same thing two different ways, compare the results,
and articulate the tradeoffs.

**When to use:** When the library has genuine design alternatives (different solvers,
different formulations, eager vs lazy, approximate vs exact).

**What it tests:** Can they evaluate approaches critically? Do they understand the
tradeoff space?

**Structure:**
- Ask for two implementations (or provide one, ask for the other)
- Ask them to compare on specific dimensions (performance, accuracy, ease of use, robustness)
- Ask them to recommend one for a stated use case
- Validate both implementations work; the recommendation is assessed qualitatively

**Good examples:**
- *Caching library:* "Implement the same endpoint cache using (a) an LRU strategy and
  (b) a TTL strategy. Compare: which performs better under bursty traffic? Which is safer
  for data that changes frequently? When would you choose each?"
- *ML preprocessing:* "Normalize the feature matrix using (a) min-max scaling and
  (b) standard scaling. Train the same model on both. Compare accuracy, sensitivity to
  outliers, and interpretability of feature importances."

**Bad example:** "Which is better, approach A or approach B?" (No implementation — just opinion.)

## Sequencing Rules

Within a notebook sequence, types should generally progress:

```
Use → Use → Modify → Modify → Debug → Create → Compare (optional)
```

But this isn't rigid. A well-designed sequence might interleave:

```
Use (basic API) → Modify (see effect of params) → Use (advanced API) → Debug
(common mistake with advanced API) → Create (combine basic + advanced) → Compare
```

The rule is: **each exercise should require exactly one new concept** beyond what the
learner already practiced. Two new things at once is confusing. Zero new things is boring.

## Notebook-Specific Guidance

**Narrative cells matter.** The markdown cells between code aren't filler — they're the
curriculum. Each narrative cell should:
- Connect this exercise to the previous one ("Now that you can define custom validators,
  let's see what happens when you compose them")
- State the goal before the code appears
- Explain the WHY before showing the HOW
- Not explain more than what's needed for the current exercise

**Guided examples should be interesting on their own.** Don't make them trivial setup
for the real exercise. The learner should find the guided example genuinely informative,
not just "yeah yeah, get to the exercise." A good guided example makes the learner want
to modify it before they even reach the "Your turn" cell.

**Outputs should be visual when possible.** If the library produces anything that can be
plotted (trajectories, distributions, images, graphs), plot it in the guided examples AND
validate it in the exercise. A plot is worth 1000 assert statements for building intuition.

**Estimated time per exercise type:**
- Use: 10-20 minutes
- Modify: 15-30 minutes
- Debug: 20-40 minutes
- Create: 30-60 minutes
- Compare: 30-45 minutes
