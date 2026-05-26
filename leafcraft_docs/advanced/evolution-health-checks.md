# Evolution Health Checks

Evolution is LeafMesh's regression detector for deployed agent chains. It
runs the same scenarios against your live mesh on a schedule, scores
the results, and tells you when today's run is different from
yesterday's — so you find out about drift before your customers do.

This page explains what evolution is, how to author scenarios, what
expectations mean, what each match operator does in plain English, and
how the score is computed.

## What evolution is (and isn't)

**Evolution is a tripwire.** You declare what a healthy run of your
chain looks like (here are the scenarios I care about, here's what
each agent should produce). Evolution re-runs those scenarios every
day and tells you when reality starts diverging from your declaration.

**Evolution is NOT a benchmark.** It doesn't compare your agents to a
gold standard or to some external reference. It compares them to
**yesterday's version of themselves**.

**Evolution is NOT BDD.** You don't write step-by-step "given/when/then"
flows. You declare scenarios (an input + expectations against the
chain's outputs) and the system measures whether those expectations
hold.

**Evolution is NOT a config tuner.** Earlier framings called this
"evolutionary optimization" because the platform can also be put into
a config-exploration mode. That mode still exists but isn't what most
operators need. **Health-check mode is the default and recommended
usage** — the live config is the only thing scored, no exploration.

## The mental model: scenario → chain → expectations

```
  Scenario                 Mesh chain                  What you score
  ----------------         ------------                ------------------
  input: "I was            greeter →                   greeter:
   charged twice"           processor →                  status == "greeted"
                            researcher →                processor:
                            advisor                      item_count >= 1
                                                        advisor:
                                                          recommendations ≠ ∅
```

A **scenario** has three parts:

1. **Input** — what gets sent to the entry point of the chain.
2. **Agent stubs** (optional) — canned responses for agents you don't
   want to actually run (typically humans, sometimes expensive LLM
   agents you've already validated).
3. **Expected outcomes** — per-agent dictionaries of fields and the
   match conditions they should satisfy.

When the scenario runs, evolution calls your real mesh, captures each
agent's response, and asks: *did the actual response match what the
operator declared as healthy?*

## How scoring works

Each agent in the chain produces a score from 0 to 100 — a composite
of two ideas:

- **Structural compliance** — does the response have the right shape
  (the keys and types declared in the agent's `yields` schema)?
- **Value compliance** — do the operator's declared expectations match?

Structural compliance comes for free: it's read off the agent's
`yields` declaration in your config. You don't need to write anything
for this to work.

Value compliance is what the operator authors. The match operators
described below are the vocabulary you use.

The scenario score is the (weighted) mean of the participating
agents' scores. Scenarios where an agent threw an error or where the
scenario timed out are capped at lower ceilings so a partial failure
can't quietly look healthy.

Stubbed agents are **excluded** from the average (they're inputs to
the test, not part of the test). Agents you declared expectations on
but that never fired in the chain are **counted as 0** (you tested
them; the chain failed to reach them; that's a real failure).

The job score is the weighted mean of scenario scores. A score of 100
means every participating agent produced a schema-valid response that
satisfied every operator expectation. Anything less, you'll see in the
per-agent breakdown.

## Drift detection (vs last run)

Each completed job is fingerprinted by its scenario set (sorted by
name + entry point). When you run the same set again, evolution looks
up the previous job with the same fingerprint and frames the new
score as **delta vs that run**.

| Delta from previous | What the summary says |
|---|---|
| First run for this set | `First health check ... Future runs will compare against this as the baseline.` |
| Within 0.1 | `Health check unchanged: 85.4/100 (same as last run).` |
| Above last run | `Health check improved: 92.0/100 (↑ 7.0 vs last run at 85.0/100).` |
| Down by < 3 | `Health check slightly down ... Small drift — may be LLM variance.` |
| Down by 3 to 10 | `Health check declined ... Worth investigating which agent drifted.` |
| Down by 10+ | `Health check REGRESSED ... Open the per-agent breakdown to triage.` |

These bands are guidance, not hard rules — they reflect realistic
LLM jitter (small day-to-day movement is usually noise; large drops
are almost always a real change worth investigating).

## Authoring a scenario in Studio

The Scenarios tab on the Evolution page is the editor. Fields:

1. **Name + tags** — for filtering and search later.
2. **Entry point** — pick from the mesh's declared entry points. The
   editor walks the chain from this entry point and shows you every
   agent it can reach.
3. **Input** — fields are seeded automatically from the entry-point
   agent's `inputs` schema. Fill them with realistic example values.
4. **Agents in chain** — toggle each one between **live** (runs the
   real agent during scoring) and **stub** (returns a canned response).
   Humans default to stub; everything else defaults to live.
5. **Expected outcomes** — one block per reachable agent. The keys
   come from each agent's `yields` schema. Fill in the fields you care
   about; leave the rest blank.
6. **Run parameters** — weight (relative importance when averaging
   multiple scenarios) and per-scenario timeout.

Blank expected-outcome fields are ignored on save. You only declare
the spot-checks you actually care about.

## The match operators

The string you put in each expected-outcome field is either a literal
value (exact equality) or an operator-prefixed expression. There are
**eight operators** and that's it — frozen scope.

### Exact equality (no operator prefix)

```yaml
status: "greeted"
```

The agent's response must contain `status` with exactly the value
`"greeted"`. Character-for-character match. Most useful for status
codes, enum-like fields, anything that should be one of a known set
of words.

**Watch out**: don't use exact equality on free-form LLM text. The
agent will say `"Hi there!"` one day and `"Hi!"` the next and your
score will swing for no real reason.

### `~contains:str` — substring (case-insensitive)

```yaml
greeting: "~contains:help"
```

Passes when the response contains the word `"help"` somewhere — case
doesn't matter. `"How can I HELP you?"` passes, `"Welcome!"` doesn't.

Best for: catching whether a specific keyword (refund, escalation,
sorry) landed in a long LLM response, without caring about the words
around it.

### `~regex:pattern` — regex match

```yaml
ticket_id: "~regex:^TKT-\\d{6}$"
```

Passes when the response matches the regular expression. `TKT-123456`
passes, `ticket-123456` fails. Power tool — skip if you don't already
know regex syntax.

Built-in safety: 100ms execution timeout, plus rejection of patterns
with nested quantifiers, backreferences, or quantified lookbehinds
(the classic ReDoS shapes).

### `~gte:N`, `~gt:N`, `~lte:N`, `~lt:N` — numeric comparators

```yaml
item_count: "~gte:1"           # at least 1 item processed
priority_score: "~gte:5"       # priority must be 5 or higher
response_time_ms: "~lt:2000"   # response under 2 seconds
```

| Operator | Reads as | Boundary |
|---|---|---|
| `~gte:N` | "at least N" | N passes, N-1 fails |
| `~gt:N` | "more than N" | N+1 passes, N fails |
| `~lte:N` | "at most N" | N passes, N+1 fails |
| `~lt:N` | "below N" | N-1 passes, N fails |

Best for: scores, counts, durations, prices — any number with a "good
range" but no single right answer. The agent's response value is
coerced to a number (string `"5"` works); booleans are deliberately
rejected so `True` doesn't accidentally satisfy `~gte:1`.

### `~in:[a,b,c]` — set membership

```yaml
detected_sentiment: "~in:[negative,neutral,positive]"
status: "~in:[approved,denied,pending]"
```

Passes when the response value is one of the listed members. Loose
equivalent of exact equality for fields where the LLM might
legitimately pick any of several valid words.

Whitespace inside the brackets is tolerated. Members containing
commas aren't supported — write a regex if you need that.

### `~truthy` and `~falsy` — presence checks

```yaml
recommendations: "~truthy"   # agent produced at least one
error: "~falsy"              # error field should be empty/null
```

`~truthy` passes when the value is non-empty (not empty list, not
empty string, not `null`, not `0`, not `False`).
`~falsy` is the inverse.

Best for: you don't care about the content, only that the agent
produced output (or didn't).

## Writing good expectations: the Goldilocks rule

Each expectation is **one opinion you have about a good response**.
Three failure modes to avoid:

**Too strict** — the score swings on LLM jitter, not real regressions:

```yaml
# Bad: LLM rewords its greeting every run
greeting: "Hello! How can I help you today?"
```

**Too loose** — the score stays 100 even when the chain breaks:

```yaml
# Bad: passes when greeter returns literally anything non-empty
greeting: "~truthy"
detected_sentiment: "~truthy"
```

**Just right** — tight enough to catch real breakage, loose enough to
survive LLM jitter:

```yaml
greeting: "~contains:help"
detected_sentiment: "~in:[negative,neutral,positive]"
status: "greeted"
```

Useful framing: ask yourself, *"if the LLM model upgraded tonight and
nothing else changed, would this expectation still pass?"* If yes,
it's robust. If no, you're testing the LLM's prose rather than your
chain's behaviour.

## Recommended patterns by agent type

| Agent type | Use mostly | Avoid |
|---|---|---|
| LLM agents | `~contains:`, `~in:[...]`, `~truthy`, `~regex:` for structural fields, status enums | Exact equality on free-form text |
| Programmatic agents | Exact equality, `~gte:` / `~lte:` | `~contains:` (their output is deterministic; use full equality) |
| External agents | Match operators on the documented response fields; `~truthy` on optional ones | Asserting on raw API payloads |
| Human agents | Almost always stubbed; expectations rarely needed | Running them live (they'd block on an inbox) |

## How stubs interact with scoring

When you mark an agent as **stubbed** in the editor, you're saying
"return this canned response, don't actually run the agent." That
agent's row in the breakdown will show `stubbed`, a score of 100, and
be **excluded from the scenario average**.

Why excluded? The stub is the operator's own canned response. Scoring
the operator's response against itself is tautological. The stub is an
**input to the test**, not part of the test being scored.

If you declared expectations on a stubbed agent, those expectations
are skipped (the editor hides them with a `Stubbed — response is
fixed by your stub above. Not scored.` note when the toggle flips to
stub mode).

## What "agent never invoked" means in the breakdown

Two cases where you'll see this:

1. **Chain didn't reach the agent.** The agent's `can_call` graph
   doesn't connect to anything that fired during this scenario.
2. **Chain was still running when scoring ended.** The settle poll
   waits up to your scenario's `timeout` for the agent to appear in
   mesh communications. If your `advisor_agent` has a 60-second LLM
   call and your scenario timeout is 30 seconds, advisor will look
   "never invoked" even though it eventually fires.

If you see this for an agent you expected to participate, bump the
scenario timeout first. Then check the agent's `can_call` conditions
to make sure the chain actually routes there in this scenario's
input.

## Setting up a daily schedule

Once you have one or more scenarios saved, the Schedules tab lets you
declare cron-style runs. Pick a daily time (HH:MM, 24-hour) and a set
of scenarios. The runner fires them at that time, scores them, and
the result lands in your Health Checks tab with the drift-vs-last-run
summary line.

Typical pattern: one schedule per cohort of scenarios, run early in
the morning. The summary line is what the on-call should glance at —
"unchanged" means quiet day, anything else is worth a look.

### Per-schedule run sizing (Advanced)

Each schedule carries its own hyperparameters in an **Advanced**
section. The defaults are tuned for health-check mode — you only need
to touch these if you're intentionally moving into config-exploration
mode.

- **Population size** (default health-check) — leave as default to
  score the live config once per scenario. Larger values turn the run
  into a config search.
- **Generations** (default health-check) — leave as default for a
  single pass. Larger values explore multiple rounds.
- **Stop after (seconds)** — wall-clock cap. The job is cancelled if
  it exceeds this; partial results are still preserved (see below).

The dialog footer shows a live `total runs = N` preview so you can
see total LLM cost before submitting. Defaults keep schedules cheap:
one pass per scenario. Bump them only when you actually want to
explore config variations on a weekly cadence.

### Mid-flight cancel preserves the partial result

Cancelling a long-running job (UI button OR wall-clock cap) does not
throw away what was already scored. The best result so far — its
per-agent rollup and scenario results — is persisted, so the
cancelled job's detail card still shows the full breakdown.

The job's human summary reads:

> "Cancelled before completion — partial result persisted (best
> fitness 67.50)."

If cancel hits before any scoring finished (very short runs), the
breakdown is genuinely empty and the UI shows "Per-scenario
breakdown not produced — job cancelled before completion" instead of
fabricating a fake-healthy result.

### Clean "actual" output

The scenario-result detail strips framework-injected metadata
(`_llm_provider`, `_llm_tokens`, `_success`, `_agent_name`,
`_chain_history`, etc.) from the displayed actual payload, so the
side-by-side `expected` vs `actual` only shows the keys the agent's
YAML `yields:` schema declared. No noise, no false mismatches on
fields the operator never declared on.

## Common pitfalls

**1. Expecting too many keys per agent.**
Six expectations on one agent means six things have to be right; one
wrong drags that agent's value compliance down. Spot-check 2 or 3
fields per agent — the ones that matter for the contract this agent
upholds.

**2. Using exact equality on LLM prose.**
`"greeting": "Hello there!"` will fail the moment the LLM says
`"Hi there!"`. Use `~contains:hello` instead.

**3. Forgetting to stub humans.**
A human agent without a stub will block for an inbox event that
never comes; the scenario times out. Either stub the human or
restructure the chain so scoring doesn't depend on a human turn.

**4. Treating the score as a percentage of correctness.**
The score is composite (schema + values, averaged across agents).
It's most useful as a delta — yesterday 92, today 76, somebody
should look. Don't read 85 as "85% correct."

## What to do when a run regresses

The summary line tells you the magnitude:

- `slightly down` (< 3 points): probably LLM variance. Worth a
  glance, not an alarm.
- `declined` (3–10 points): one agent's value compliance likely
  slipped. Open the per-scenario breakdown to see which agent and
  which keys missed.
- `REGRESSED` (10+ points): something material changed. Most often
  it's one of: a config edit nobody told you about, an LLM model
  upgrade you forgot rolled out, or an agent prompt that's started
  producing the wrong field. Per-agent breakdown will point you at
  the agent; the matched/missed keys list will point you at the
  field.

## Scoping evolution to your environment

Evolution runs are isolated from your normal mesh activity. Sessions
created during scoring are tagged so they don't appear in your
normal session lists unless you flip the `Include evolution` toggle
on the sessions page. Job results, saved scenarios, and schedules
are all scoped to the environment they were created in.

## Limits and trade-offs we don't hide from you

- **No semantic similarity.** Evolution doesn't know that "Hi!" is
  semantically equivalent to "Hello!". The match operators are
  literal. If you need semantic matching, that's a paid LLM-judge
  signal we deliberately did not build into scoring (cost predictability
  beats cleverness).
- **No regression on prose quality.** If your LLM starts giving worse
  answers but still produces schema-valid, expectation-matching
  responses, evolution will say "unchanged." Schema + value matching
  catches structural and contract-level drift; it doesn't catch
  "answers got worse but still legal."
- **Each run is an independent scoring call** through your real
  agents. Daily scheduling × big scenario sets × big LLM calls = real
  spend. Keep your scenario count reasonable (10–50 is plenty for
  most chains) and set tight timeouts.

## Where to go next

Read [Writing Evolution Scenarios](/docs/advanced/evolution-writing-scenarios) for a step-by-step walkthrough of authoring your first scenario, plus three fully worked examples (LLM chain, programmatic chain, human-in-the-loop chain) you can adapt to your own agents.
