# Evolution Operator Runbook

You wrote the scenarios. The schedule is firing them daily. Today the
summary line says **REGRESSED** instead of **unchanged**. What now?

This page is the on-call's playbook. It covers triage, root cause
analysis, common false alarms, when to ignore, when to act, and how
to document what you found so the next on-call benefits.

Read [Evolution Health Checks](/docs/advanced/evolution-health-checks)
for concepts and [Writing Evolution Scenarios](/docs/advanced/evolution-writing-scenarios)
for authoring. This page assumes you've got both.

## Severity bands and what they mean

The summary line at the top of every completed job tells you the
magnitude of drift versus the last run of the same scenarios.

| Summary | Delta | What it usually means | Default action |
|---|---|---|---|
| `Health check unchanged` | abs delta < 0.1 | Quiet day. Chain is doing exactly what it did yesterday. | None. Close tab. |
| `Health check improved` | positive delta | Someone shipped a fix, an LLM upgrade rolled out, your scenarios got easier. | Open the breakdown, confirm it's the change you expected. |
| `Health check slightly down` | -3 < delta < 0 | LLM variance. Real regressions rarely produce sub-3-point drops. | Glance at the breakdown. If nothing stands out, ignore. |
| `Health check declined` | -10 < delta ≤ -3 | One agent's value compliance likely slipped. Something concrete changed. | Triage (see below). |
| `Health check REGRESSED` | delta ≤ -10 | Something material broke or got reconfigured. Almost always actionable. | Triage immediately. |

These bands are guidance, not hard rules. They reflect realistic LLM
jitter: day-to-day variance on a healthy chain is typically small.
Anything above 3 points is worth investigating; above 10 is almost
certainly real.

## The triage decision tree

```
Open the job's per-agent breakdown.
│
├─ Did one specific agent drop while others stayed at 100?
│  └─ YES → Single-agent regression. Skip to "Drill into one agent".
│
├─ Did multiple agents drop together?
│  ├─ All by the same amount? → Likely a config or input change upstream.
│  │                            Check the entry-point input and routing.
│  └─ Different amounts?       → Likely a real chain quality regression.
│                                Walk the chain start-to-finish.
│
└─ Did the SAME agent show "expected to participate; no response captured"?
   └─ YES → Chain didn't reach this agent. Skip to "Chain didn't fire".
```

## Drill into one agent

Open the scenario card, expand the agent row that dropped. Three
things to look at:

### 1. Schema issues

If `Schema match` is below 1.0, the response shape changed. Examples:

- Missing required key — agent stopped producing a `yields` field
  (typo in a prompt rewrite, missing return in a programmatic agent).
- Type mismatch — `item_count` came back as `"five"` instead of `5`.
  Usually means an LLM agent's `response_format` got dropped or
  changed, or a programmatic agent's return type got coerced.

**Action**: this is almost always a code or config change. Look at
git history for the agent's prompt / code since the last successful
run. Common culprits: someone edited the prompt and removed the
`yields:` formatting instruction; someone changed an LLM model and
the new model handles structured output differently.

### 2. Missed value-compliance keys

If value compliance dropped, look at the `missed` rows. Each one
tells you the key, the expected operator, and the actual value:

```
processor_agent  score=75  schema=ok  value=partial
   matched: status
   missed:  item_count — ~gte:1: actual=0
```

Read literally: "we expected item_count >= 1, agent returned 0."
That's a real signal. Now ask:

- **Is the chain actually receiving the right input?** Look at the
  scenario's `input` field at the top of the card. Did someone
  change the scenario? Did the entry agent's `inputs` schema change?
- **Did upstream agents produce what this agent expected?** Open the
  upstream agent's row. If `processor_agent` got 0 items because
  `greeter_agent` returned an empty `user_input`, that's where to
  look.
- **Did the agent's behaviour change?** Same input, same upstream
  output, different agent response → look at the agent's prompt /
  code / model.

### 3. Response preview

Lazy-expand the agent's response. Compare it visually to a previous
run's response (from a job before the regression). Often the change
is obvious — an LLM started returning markdown wrapping, a
programmatic agent started returning a wrapped dict instead of a
flat one, an enum-like field is producing values outside your `~in:`
set.

**Note on what's in the "actual" payload:** Framework-injected
metadata (`_llm_provider`, `_llm_tokens`, `_success`, `_agent_name`,
`_chain_history`, etc.) is stripped from the displayed payload
before comparison. What you see in the "actual" view is exactly the
keys the agent's YAML `yields:` schema declared — no noise. If your
expected key isn't in the actual, the agent really didn't produce
it; it wasn't filtered out.

### 4. Cancelled jobs still show the breakdown

Cancelling a job (manually from the UI OR via the wall-clock cap)
does NOT throw away what was already scored. The cancelled job's
detail card shows:

- The best score reached before cancel.
- The per-agent rollup for whatever scenarios completed.
- The scenario results for whatever passes finished.

The job summary line reads "Cancelled before completion — partial
result persisted (best fitness X.XX)." Use this when triaging a
slow scenario: cancel after a minute, look at the breakdown to see
which agent was burning time, then fix and re-run.

If cancel hits before any scoring finished (rare, but possible on
very short max-runtimes), the breakdown is genuinely empty and the
UI says so explicitly — no fake-healthy fallback.

## Chain didn't fire

If an agent shows `participated=false` with the reason `"expected to
participate; no response captured before deadline"`, the chain
didn't reach this agent. Three causes, in order of frequency:

### Cause A: timeout too short

The chain WAS firing the agent, but it took longer than the
scenario's `timeout` to settle. Bump the scenario timeout (60s →
120s) and re-run. If the agent now participates, this was the cause.

### Cause B: routing change

Look at the upstream agent's `can_call` declaration. Did someone
change the condition? Example: `processor_agent` used to call
`advisor_agent` whenever `item_count > 0`, but someone tightened it
to `item_count > 5`. Your scenario produces 1–3 items, so advisor
never fires.

### Cause C: upstream agent errored

Look at the upstream agent's row. If it errored, the chain never
produced the input the downstream agent needed. The downstream
agent's "never invoked" is a secondary symptom; the primary
regression is upstream.

## Common root causes mapped to symptoms

After a few months on-call you'll recognise these. Listing them up
front saves the first week of confusion.

### "All agents dropped 50 points overnight"

Almost always: someone changed the scenarios. Open the scenarios
editor and look at the expected_outcomes for the scenario that
dropped. Compare against last week's expectations (Studio shows the
edit history). The fix is usually backing out an over-tightened
expectation.

### "One agent went from 100 to 0"

Almost always: that agent crashed (look for `error` in its row) or
its schema changed and stopped matching. Schema compliance fully
failing with no schema issues listed → response wasn't a dict (agent
returned a string). Schema compliance partially failing with issues
listed → response keys changed.

### "Score dropped 5 points, no specific agent is obviously broken"

Look for small value-compliance drops across one or two agents. This
is the classic "the LLM started giving slightly different responses"
case. If your expectations are too strict for LLM jitter, this is
the symptom — and the fix is loosening one or two operators (exact
match → `~contains:` or `~in:[...]`).

### "Score keeps oscillating between two values run-to-run"

Either: a stubbed agent has a FIFO list of responses cycling, OR
your value-match expectations include something genuinely
non-deterministic (a timestamp, a UUID, a random-suffixed ID). Find
the field that flips and either drop it from expectations or use a
regex that matches its shape.

### "Score is 30 because of timeout, but the chain actually completes"

The mesh_call returned in time but the settle window didn't capture
all downstream agents. Bump the scenario `timeout` to at least the
slowest LLM call in your chain × 1.5.

### "All scenarios regressed today, not just one"

Something fleet-wide changed. Candidates: LLM provider upgrade,
infrastructure migration, mesh deployment, environment-wide config
update. Check the change log before investigating per-agent.

## When to ignore

You'll see `declined` summaries that aren't worth acting on. Common
benign causes:

- **First run after a major prompt rewrite.** The next-day baseline
  reset will absorb this. Wait one more run.
- **LLM model upgrade just rolled out.** Score may stabilise 5–10
  points lower than before; that's the new normal. Re-baseline by
  letting the next 3 runs complete; if they're all similar,
  re-tighten any over-strict expectations.
- **Holiday / weekend / off-hours.** Some chains have variance
  driven by upstream traffic patterns. If your chain reads cached
  data, cache hit ratios fluctuate. Not actionable.
- **Score dropped 2 points across a 10-scenario job.** That's noise.
  Walk away.

The rule of thumb: **if you can't explain the drop in one sentence
after looking at the breakdown, it's probably jitter.**

## When to act

Triage immediately if:

- **REGRESSED band** (10+ point drop). Almost always real.
- **A schema-compliance issue** appears on an agent that hasn't been
  edited recently. Schema regressions don't happen from LLM jitter;
  they happen from code / config changes.
- **An agent that used to participate now shows "never invoked"** in
  multiple consecutive runs. Chain routing changed.
- **The same expectation fails across multiple scenarios.** That
  agent's behaviour changed in a way that affects multiple journeys.

## How to investigate efficiently

The breakdown gives you most of what you need. Two API endpoints help
when you need raw detail:

- **The scenario card's `Input` preview** shows what was actually
  sent. Compare it against what you THINK you're testing — sometimes
  someone edited the scenario.
- **The lazy-expand on each agent's response** shows the full reply
  (up to 2KB, truncated otherwise). Comparing today's response
  against last week's response is the single highest-signal
  investigation step.

Beyond that, the **logs** for the sessions evolution created contain
the full agent reasoning. If you flip the `Include evolution` toggle
on the sessions page, those sessions show up alongside real customer
sessions; from there it's the same drill-down as any session debug.

## Suppressing false alarms

If a scenario fires a `declined` summary repeatedly and the cause is
known-and-accepted (e.g., model variance you've decided to tolerate),
you have two options:

**Option 1**: loosen the offending expectation. If
`detected_sentiment: ~in:[negative,neutral]` fails 5% of the time
because the LLM occasionally classifies a polite complaint as
"positive", change the operator to `~in:[negative,neutral,positive]`
or drop the expectation entirely. The drop in signal precision is
the price you pay for not crying wolf.

**Option 2**: lower the scenario's `weight` field. If a scenario
contributes 1.0 today and you bring it to 0.5, its score still
appears in the breakdown but its influence on the job average is
halved. Useful for noisy scenarios you want to keep around for
diagnostic value without letting them dominate the alert path.

Don't disable scenarios silently. Either fix them, deprioritise them
with `weight`, or delete them. A scenario that you've decided to
ignore but left in is just noise in everyone else's mental model.

## What to write down

When you investigate a regression, even if you ignore it, leave a
trail. Useful template:

```
Job ID: job_xyz
Scenario(s) affected: billing-complaint
Severity: REGRESSED (95.4 → 78.0)

What changed:
  - advisor_agent.priority_score went from 8 to 3
  - advisor_agent.recommendations went from 4 items to 1

Root cause:
  - Prompt edit at commit abc1234 removed the "high-priority for
    billing" instruction.

Action taken:
  - Reverted the prompt edit at abc1234.
  - Next run: 96.1 (back in band).

If this happens again:
  - Check advisor's prompt history first. The "high-priority for
    billing" line is load-bearing for the priority_score expectation.
```

Three minutes to write, hours saved next time it happens.

## Coordinating with the team

When the regression isn't yours to fix:

- **Owner is the agent's author**, not the evolution operator.
  Forward the per-agent breakdown to whoever last touched that
  agent's prompt / code / config.
- **Don't disable the scenario unilaterally.** The author needs the
  signal that their change broke things.
- **Don't apply a "best configuration" without review.** Evolution's
  apply button is for operators who explicitly want to migrate the
  chain to a configuration that came out of an exploration run; it's
  NOT the right tool for "fix the regression." Fix the regression at
  the source.

If a regression IS yours to fix:

- **One commit per regression.** Even if you have multiple things to
  change, separate them so the next health check tells you whether
  each fix worked.
- **Run the affected scenario manually after the fix** before
  declaring it resolved. The daily schedule isn't the place to
  validate a fix — that's what the `+` button on Health Checks is
  for.

## Escalation

Most regressions resolve at the operator level. Escalate when:

- A REGRESSED summary fires three days in a row without a known
  cause.
- A regression coincides with a customer complaint or a support
  ticket spike. Treat the customer-facing symptom as the priority;
  evolution gave you a head start.
- Multiple unrelated scenarios all REGRESSED at once. Something
  fleet-wide moved; this isn't a single-agent problem.

The on-call's job isn't to know the answer — it's to be the first
to see the signal and route it to whoever owns it.

## A note on the trend chart

The line chart on the Health Checks page shows score over time. Two
things to look for:

- **Step changes**: a sudden cliff or jump usually corresponds to a
  deployment. Cross-reference with your deploy log.
- **Slow drift**: a gradual decline over weeks (4-5 points per
  month) usually means scenarios are out of date with how the chain
  actually behaves now. Time to revisit the expectations and either
  loosen the ones that are catching noise or tighten the ones that
  no longer catch real regressions.

The trend is a leading indicator. The summary line tells you about
yesterday vs today. The trend tells you about this month vs last.

## Where to go next

- [Evolution Health Checks](/docs/advanced/evolution-health-checks) — concepts and scoring model.
- [Writing Evolution Scenarios](/docs/advanced/evolution-writing-scenarios) — authoring playbook with worked examples.
- This page — operator runbook (you are here).
