# Writing Evolution Scenarios

A scenario is a test case for your deployed agent chain. You write one
the way you'd write a smoke test: pick a real customer journey, decide
what "healthy" looks like at each step, declare it.

This page walks you through authoring one from scratch, then shows
three fully worked examples for different chain shapes. Read
[Evolution Health Checks](/docs/advanced/evolution-health-checks) first
if you haven't — it covers the underlying concepts. This page is the
hands-on part.

## The seven decisions you make per scenario

Authoring a scenario is just answering seven questions:

1. **What real customer journey am I testing?** (billing complaint, refund request, scheduled report, etc.)
2. **What entry point fires the chain?** (e.g. `greet_user`)
3. **What input does the chain receive?** (e.g. `{ "message": "I was charged twice on June 5" }`)
4. **Which agents should run live vs return canned stubs?** (humans always stubbed; LLMs almost always live; programmatic always live)
5. **Which agents do I care enough about to spot-check?** (not necessarily all of them)
6. **For each of those agents, which output fields matter?** (not all `yields` keys)
7. **How tight should each expectation be?** (Goldilocks rule from the concepts page)

Three of these decisions (steps 5–7) are where most operators get
stuck. The rest is data entry. Most of this page is about getting
steps 5–7 right.

## Step-by-step: your first scenario

Open the Scenarios tab on the Evolution page in Studio and hit the
`+` button.

### 1. Name and tags

Use a name that describes the customer behaviour you're testing, not
the chain mechanics. Good names: `billing-complaint`, `refund-approved`,
`urgent-escalation`. Bad names: `test-1`, `greeter-test`, `scenario-a`.

Tags are for filtering later. Useful conventions: a domain tag
(`billing`, `support`, `onboarding`), a cadence tag (`daily`, `weekly`),
and optionally a severity tag (`smoke` for cheap quick checks, `slow`
for expensive validation runs).

### 2. Entry point

Pick from the dropdown. The editor walks the `can_call` graph
starting from this entry point's target agent and shows you only the
agents this chain can reach. If an agent you want to test isn't in
the list, either the entry point is wrong or your `can_call`
conditions never route to it.

### 3. Input

After you pick an entry point, the editor seeds input fields from
that agent's `inputs` schema. Fill them with **realistic** values — a
sentence a real customer would type, a number in the range your
customers actually use, a category your `can_call` conditions
distinguish on.

> If the entry agent declares `inputs: { message: string }`, you'll
> see one labeled `message` field. Type something concrete:
> `"I was charged twice for the same item on June 5."`

Don't use placeholder text like `"test"` or `"hello"`. Half the value
of evolution comes from running the chain through inputs that exercise
the real branching logic. `"test"` rarely does.

### 4. Stubbing agents

Each agent in the chain shows up with a **Live / Stub** toggle.

**Live** = the agent runs for real during scoring. Real LLM call,
real cost, real latency.

**Stub** = the agent returns whatever canned payload you write. No
real execution.

Defaults: humans → stub, everyone else → live. You can override.

| When to stub | Why |
|---|---|
| Human agent | Real human input would block the chain forever |
| Expensive LLM agent you've validated separately | Skip the cost, focus the score on the other agents |
| External integration agent | Avoid calling a third-party API during every health check |
| LLM agent whose output is genuinely non-deterministic | Pin a representative response so scoring isn't a coin flip |

When to NOT stub: any agent whose behaviour the scenario is actually
checking. Stubbing an LLM agent and then declaring expectations on it
is testing your own stub against itself — pointless.

For each stubbed agent, write a response that matches its `yields`
schema. If the agent ever produces multiple replies in one chain
(rare — only happens with FIFO loops), enter each in order; the Nth
call pops the Nth payload.

### 5. Pick which agents to spot-check

This is the first real judgment call. You **don't** have to declare
expectations on every reachable agent. Default to declaring on
agents whose output most directly reflects whether the chain did the
right thing for the customer.

For a customer-support chain:

- **The agent the customer sees the result of** (advisor, recommender) — almost always declare.
- **The agent that classifies the request** (greeter producing `detected_sentiment`, intent classifier) — usually declare, because misclassification cascades.
- **The agent that decides which branch to take** (router, dispatcher) — usually declare, same reason.
- **Intermediate processing agents** (data shaper, enricher) — declare if your customer's experience depends on what it produces. Skip if it's just a pass-through.

Three or four declared agents is plenty for most chains.

### 6. Pick which fields per agent

Within each agent you chose to spot-check, decide which `yields` keys
matter. Same logic as agents — declare the ones that reflect
contract-level behaviour; skip the ones that are noise.

Heuristics:

- **Status / enum-like keys**: almost always declare. Cheap to
  validate, catches lots of regressions.
- **Lists / collections**: declare presence (`~truthy`) or count
  (`~gte:1`), rarely contents.
- **Numeric scores / counts**: declare a sensible range
  (`~gte:1`, `~lt:100`), not exact values.
- **Free-form text**: declare a substring (`~contains:refund`) or
  a structural pattern (`~regex:^\\d{6}$`), almost never exact text.
- **Internal / debugging fields**: skip. (e.g. trace IDs, token
  counts, internal flags).

### 7. Tightness — the Goldilocks rule

For each declared field, pick the loosest operator that still catches
the regression you're worried about. Three failure modes:

**Too strict** — the score swings on LLM jitter, not real regressions.

```yaml
greeting: "Hello! How can I help you today?"   # exact-match an LLM string
```

The model rewords its greeting every prompt edit, every LLM upgrade.
This expectation will fire false alarms forever.

**Too loose** — the score stays 100 even when the chain breaks.

```yaml
greeting: "~truthy"
detected_sentiment: "~truthy"
```

The agent passes by returning literally any non-empty value. You're
declaring "did the agent return something" — that's already covered
by the structural compliance check. You've added zero diagnostic
signal.

**Just right** — catches breakage; survives jitter.

```yaml
greeting: "~contains:help"
detected_sentiment: "~in:[negative,neutral,positive]"
status: "greeted"
```

A good check: "if the LLM model upgrades tonight and nothing else
changes, will this expectation still pass?" If yes, robust. If no,
you're testing the LLM's prose rather than your chain's behaviour.

### Save and run

Save the scenario. Then either run it once from the `+` button in
the Health Checks tab (one-off), or attach it to a Schedule for daily
runs.

The **first** completed run shows `First health check for this
scenario set: X/100.` That's your baseline. The **second** run with
the same scenarios shows the drift line — `unchanged`, `improved`,
`declined`, or `REGRESSED`. From then on, the summary tells you
whether yesterday's chain matches today's.

## Worked example 1: Customer-support chain (LLM-heavy)

The chain: `greeter → processor → researcher → advisor`. Greeter
classifies sentiment; processor turns the greeter's output into
actionable items; researcher gathers context; advisor produces
recommendations.

### Yields schemas

```yaml
greeter_agent:
  yields:
    greeting: string
    user_input: string
    detected_sentiment: string
    status: string

processor_agent:
  yields:
    processed_items: list
    item_count: number
    status: string
    alert: string

researcher_agent:
  yields:
    findings: list
    query: string
    analysis: object
    status: string

advisor_agent:
  yields:
    recommendations: list
    risk_assessment: string
    priority_score: number
    next_steps: list
    status: string
```

### A real scenario: "customer complains about being double-charged"

```yaml
name: "billing-double-charge"
tags: ["billing", "daily", "smoke"]
entry_point: greet_user
input:
  message: "You charged my card twice on June 5 for the same order. Please refund the duplicate."
agent_stubs:
  # No humans in this chain to stub. All agents run live.
expected_outcomes:
  greeter_agent:
    status: "greeted"
    detected_sentiment: "~in:[negative,neutral]"
    greeting: "~truthy"
  processor_agent:
    status: "processed"
    item_count: "~gte:1"
    alert: "~falsy"
  researcher_agent:
    status: "~in:[completed,no_results]"
    findings: "~truthy"
  advisor_agent:
    status: "advised"
    priority_score: "~gte:5"
    recommendations: "~truthy"
    next_steps: "~truthy"
```

What this catches:

- **Greeter starts saying complaints are "positive"** — `~in:[negative,neutral]` fails.
- **Greeter returns an empty greeting** — `~truthy` fails.
- **Processor sees no items in the request** — `~gte:1` fails.
- **Processor raises an alert it shouldn't** — `~falsy` fails.
- **Researcher's query failed entirely** — `status` not in `[completed, no_results]`.
- **Advisor returns no recommendations** — `~truthy` fails.
- **Advisor downgrades a clear billing complaint to priority 0** — `~gte:5` fails.

What this deliberately doesn't check:

- The exact wording of the greeting (LLM jitter).
- The exact recommendations (LLM jitter).
- Researcher's internal `query` field (debugging only).
- Advisor's `risk_assessment` text (LLM jitter — could spot-check via `~contains:` if there's a specific keyword you care about).

## Worked example 2: Data-processing chain (programmatic-heavy)

The chain: `validator → enricher → router → exporter`. Validator
checks the input format; enricher adds derived fields; router decides
where to send the result; exporter writes to a downstream system.

Programmatic agents are deterministic — their output is the same for
the same input. You can be much stricter with expectations because
there's no LLM variance to absorb.

### A real scenario: "valid CSV row passes through the pipeline"

```yaml
name: "csv-row-happy-path"
tags: ["pipeline", "daily"]
entry_point: ingest_row
input:
  raw_row: "1234,jane.doe@example.com,250.00,2026-05-15"
  source: "uploads_q2"
expected_outcomes:
  validator_agent:
    status: "valid"
    schema_version: "v3"
    error_count: 0           # exact equality on a programmatic count
  enricher_agent:
    status: "enriched"
    enriched_fields: "~gte:4"   # at least 4 derived columns added
    customer_tier: "~in:[bronze,silver,gold,platinum]"
  router_agent:
    destination: "~in:[warehouse,error_queue,review_queue]"
    routing_decision: "~truthy"
  exporter_agent:
    status: "exported"
    rows_written: 1          # exact — programmatic agent should always write exactly 1
    target_table: "~regex:^[a-z_]+$"
```

Notice the differences from Example 1:

- More **exact** matches (`error_count: 0`, `rows_written: 1`,
  `schema_version: "v3"`). Programmatic agents don't drift; exact
  match is appropriate.
- The one LLM-ish field (`routing_decision`) is checked only with
  `~truthy` — that field could be a free-form reason string from a
  classifier, in which case looser is safer.

## Worked example 3: Human-in-the-loop chain

The chain: `intake → triage → human_approver → fulfilment`. Triage
decides whether the request needs human approval; if so, it routes to
`human_approver`; the approver's decision routes to fulfilment.

A human approver can't run live during scoring — they'd block on an
inbox. You stub them.

### A real scenario: "approved refund flows to fulfilment"

```yaml
name: "refund-approved-end-to-end"
tags: ["approval", "weekly"]
entry_point: handle_refund_request
input:
  amount: 145.00
  reason: "duplicate charge"
  customer_tier: "gold"
agent_stubs:
  human_approver:
    decision: "approved"
    approver_id: "operator_42"
    note: "verified against transaction log"
expected_outcomes:
  intake_agent:
    status: "intake_complete"
    request_type: "refund"
  triage_agent:
    routing_decision: "~in:[approve_auto,needs_human,reject_auto]"
    confidence: "~gte:0.5"
  fulfilment_agent:
    status: "completed"
    fulfilled_amount: 145.00
    fulfilment_method: "~in:[card_refund,credit_note,wire_transfer]"
```

Notes on stub design:

- The stub mirrors the schema the live human approver would produce
  (`decision`, `approver_id`, `note`). Look at the agent's `yields` to
  know which fields downstream agents will read.
- `human_approver` doesn't get a row in `expected_outcomes`. Even if
  you wrote one, it would be ignored — stubbed agents short-circuit
  scoring (the editor hides the expectations block in stub mode).
- The scenario only **tests the downstream behaviour**. Did triage
  route to the human? (Implicit — if it didn't, fulfilment wouldn't
  receive an `approved` signal.) Did fulfilment produce the right
  amount, method, status? Those are what the customer sees.

A different scenario for the same chain would stub the human with
`decision: "denied"` and assert on a different fulfilment outcome
(`status: "rejected"`, no `fulfilled_amount`, etc.). One scenario per
human decision branch.

## Workshop: critique three scenarios

Three scenarios for the same hypothetical "support escalation"
chain. One is bad, one is mediocre, one is solid.

### A — bad

```yaml
name: "test1"
entry_point: handle_message
input:
  message: "hello"
expected_outcomes:
  greeter_agent:
    greeting: "Hi! How can I help you?"
  router_agent:
    routing_decision: "general_support"
  resolver_agent:
    response: "Thanks for reaching out!"
```

Problems:

- `"test1"` tells you nothing six months from now.
- `"hello"` doesn't exercise the chain's branching — it'll route to
  the catch-all path every time.
- Three exact-match strings on LLM output. Any prompt tweak or model
  upgrade fires false alarms.
- No tags — can't filter or group.

### B — mediocre

```yaml
name: "support-escalation"
tags: ["support"]
entry_point: handle_message
input:
  message: "URGENT: my account got hacked, locked out, need help NOW"
expected_outcomes:
  greeter_agent:
    greeting: "~truthy"
    detected_sentiment: "~truthy"
  router_agent:
    routing_decision: "~truthy"
  resolver_agent:
    response: "~truthy"
```

Better:

- Name describes the customer journey.
- Input is realistic and exercises the urgent-escalation branch.
- One tag.

Still weak:

- Every expectation is `~truthy`. The structural compliance check
  already covers "did the agent return something." This adds nothing
  on top.
- Score will sit at 100 even if the chain misclassifies an urgent
  request as general support — because `routing_decision: ~truthy`
  passes any non-empty string.

### C — solid

```yaml
name: "urgent-account-hack-escalation"
tags: ["support", "urgent", "security", "daily"]
entry_point: handle_message
input:
  message: "URGENT: my account got hacked, locked out, need help NOW. Account ID 88234."
expected_outcomes:
  greeter_agent:
    detected_sentiment: "~in:[negative]"
    urgency_level: "~in:[high,critical]"
  router_agent:
    routing_decision: "~in:[security_team,account_recovery]"
    confidence: "~gte:0.7"
  resolver_agent:
    status: "escalated"
    priority: "~in:[p1,p2]"
    ticket_id: "~regex:^TKT-\\d{6}$"
    next_action: "~truthy"
```

Why it's solid:

- Name + tags describe what's being tested AND when it should run.
- Input includes an account-ID-shaped fragment to exercise structured
  extraction.
- Each expectation tests a **contract** the chain has with the
  customer: sentiment classification, routing to the right team,
  ticket ID format, etc.
- Loose enough that LLM jitter (different prose, different exact
  recommendations) doesn't fire false alarms.
- Tight enough that real regressions (misclassified urgency, routing
  to general support, missing ticket ID) WILL fail the scoring.

## Iterating on scenarios over time

You don't have to get a scenario right on the first try. Workable
pattern:

1. **Write a loose first version.** `~truthy` on most fields, exact
   match only on enum-like status codes. Save and run.
2. **Look at the actual response** in the per-agent breakdown. See
   what real values appear in each field.
3. **Tighten the expectations** based on what healthy looks like.
   Move `~truthy` → `~contains:` or `~in:[...]` for fields with
   stable value sets. Add `~gte:` / `~lte:` for numeric ranges.
4. **Run again.** Score should still be 100 (if not, you tightened
   too far — back off).
5. **Set up the schedule.** Once you have a stable baseline, attach
   the scenario to a daily run and watch the drift line over a week.

The Goldilocks rule isn't something you nail on day one. It's
something you converge to over a week of runs.

## When to add a new scenario

One scenario per **customer journey** that matters. Not one per
agent, not one per code path. The minimum sensible scenario set for
most operators:

- One happy-path scenario per major customer journey (e.g.
  billing-complaint, refund-request, support-escalation, status-check).
- One adversarial scenario per major customer journey that exercises
  edge cases your chain is supposed to handle (urgent escalations,
  multi-issue messages, ambiguous intent).
- One scenario per human-decision branch (approved, denied, escalated)
  if your chain has human-in-the-loop steps.

That's typically 8–15 scenarios for a real production chain. More than
about 30 starts to be expensive and rarely adds diagnostic value —
the score becomes a long average that smears over what's actually
changing.

## Anti-patterns to avoid

**Asserting on internal/debugging fields.** `_llm_tokens`,
`_trace_id`, `_agent_name` — these are observability metadata, not
contract surface. Don't put them in `expected_outcomes`.

**Cargo-culting expectations from one agent to another.** Each agent's
`yields` are different. Don't copy `status: "greeted"` from greeter
to processor — processor probably doesn't yield that field.

**Asserting on every yields key.** If your agent declares 8 fields
but only 3 of them matter for the customer, only assert on those 3.
A scenario with 8 expectations doesn't catch 8x more regressions; it
just has 8x more places to false-alarm.

**Testing the same thing across multiple scenarios.** If
`billing-complaint`, `refund-request`, and `urgent-billing` all assert
`detected_sentiment: ~in:[negative,neutral]`, you'll see the same
failure three times when the sentiment classifier breaks. Useful for
redundancy; expensive for daily cost.

**Forgetting to update the scenario when the agent changes.** If you
edit an agent's `yields` schema to add a new required key, the
existing scenarios won't know — they'll keep passing because they
never asserted on the new key. Worth re-reviewing your scenarios
whenever you change an agent's contract.

## A note on cost

Each scenario in each scheduled run is one full chain execution
through your live agents. Real LLM calls, real cost. Math:

```
daily cost ≈ (scenarios per schedule)
           × (LLM calls per chain)
           × (avg cost per LLM call)
           × 1 run / day
```

A 10-scenario schedule running daily on a chain with 4 LLM calls
costing $0.001 each = $0.04 per day, $14/year. Reasonable. A
50-scenario schedule on a chain with 8 LLM calls = $0.40 per day,
$146/year. Worth budgeting.

If your chain is expensive, prefer fewer scenarios with deeper
expectations over many scenarios with shallow ones.

## Where to go next

You've got the conceptual framing (the
[Evolution Health Checks](/docs/advanced/evolution-health-checks)
page) and the authoring playbook (this page). The remaining piece is
operational — running scheduled checks and acting on regressions.
That's covered in the operator runbook section of the
[Self-Healing Networks](/docs/advanced/self-healing) page.
