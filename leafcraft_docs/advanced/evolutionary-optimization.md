# Configuration Exploration (Advanced)

> **Health-check mode is the default.** Most operators want
> [Evolution Health Checks](/docs/advanced/evolution-health-checks) —
> the daily regression detector that re-runs your scenarios against
> the live mesh and flags drift. The configuration-exploration mode
> described here is advanced and rarely needed.
>
> Only use this mode when you have a concrete tuning question
> (e.g. "is there a temperature / timeout / routing combination that
> scores higher on my scenarios?") and a budget for the extra LLM
> spend the exploration will cost.

## What this mode does

In health-check mode, evolution scores your live mesh **as is** once
per scenario and tells you whether today's run matches yesterday's.

In configuration-exploration mode, evolution scores **multiple
variants** of your mesh config against the same scenarios and
proposes the best-scoring variant as a configuration you can review
and apply. It runs as a separate co-located service alongside your
runtime mesh — the runtime keeps serving customer traffic; the
exploration service handles its workload in isolation.

> **No YAML configuration required.** Operators kick off runs from
> Studio (or via the REST API) — scenarios and run parameters live
> in the job request, not in your mesh config.

## How a job works

1. **Operator starts a job** with one or more test scenarios + optional
   parameter overrides. The live mesh's current config is the baseline
   by default.
2. **The platform explores variants** of the baseline config, scoring
   each against your scenarios.
3. **Scoring runs through the live mesh.** Each scenario fires through
   your real agents — real LLM calls, real responses, real timing. No
   second mesh is spawned.
4. **Telemetry stays clean.** Scoring traffic is tagged so production
   dashboards (cost, agent activity, session lists) automatically
   exclude it. The Evolution page in Studio is the one place that
   includes it.
5. **Final result**: the best variant is serialized as YAML. Operator
   reviews, downloads, applies through their own deployment workflow.

Variants that would produce invalid configs (cycles in `can_call`,
dangling agent references, unparseable conditions, orphaned agents)
are validated and rejected — invalid configurations never get scored.

## What exploration can change

| Knob | Example |
|----------|---------|
| Agent connections | Add/remove `can_call` edges, e.g. add a fallback route from router to advisor |
| Communication patterns | Mesh-wide timeouts, chain depth |
| Agent parameters | Temperature, model, max tokens — e.g. swap a heavyweight model for a smaller one |
| Workflow sequences | Entry-point target, ordering |
| Resource allocation | Session retention |
| Timeout settings | Manager + chain timeouts |

## Where exploration helps and where it doesn't

**Effective for:**
- LLM temperatures and model assignments
- Timeout tuning
- Routing topologies
- Resource allocations

**Not effective for:**
- Agent prompts (no automated quality signal exists for prose)
- `can_call` conditions (encode business logic — random changes
  produce nonsense)
- Tool configurations (domain-specific)

## Test scenarios

Each scenario is fired against every variant. Scenarios have weights
so critical flows count more toward the final ranking.

A scenario looks like:

- **Name** — human label shown in Studio
- **Entry point** — which mesh entry point to call
- **Input** — the data sent to the entry agent
- **Expected outcome** — keys the response should contain
- **Weight** — how much this scenario counts overall
- **Timeout** — per-scenario safety cap

See [Writing Evolution Scenarios](/docs/advanced/evolution-writing-scenarios)
for the full authoring guide and supported match operators.

## Operator-supplied job metadata

Every job carries operator-friendly fields for Studio's history page:

| Field | Purpose |
|---|---|
| `name` | Human-friendly title shown in the job list |
| `tags` | Filter/group runs ("billing", "weekly", "perf") |
| `note` | Longer free-text description |
| `parent_job_id` | Link a rerun back to a previous job for traceability |

Every completed job records the baseline score, the final best score,
the improvement percentage, and a plain-English summary like
*"Significant improvement found: +12.3% over baseline. Review the
proposed config before applying."*

## Telemetry isolation

Activity emitted during scoring is tagged so dashboards know it's
automated probing, not real customer traffic. Production dashboards
(sessions list, per-agent stats, LLM cost, token usage) exclude
exploration events by default — operators see real customer spend
and activity, not inflated numbers from scoring runs. The Evolution
page in Studio is the one place that opts in to seeing scoring data.

## Recommended workflow

1. **Pick a few test scenarios** that represent your most critical
   production flows — start with two or three, expand later.
2. **Start a job** with a modest run size — real-agent scoring uses
   real LLM tokens, so size the exploration to your budget.
3. **Watch progress** in Studio's Evolution page (updates stream in
   live).
4. **Review the proposed configuration's YAML** when the run completes.
   Compare against your current config; cherry-pick changes.
5. **Press Apply** in Studio (records acceptance), download the YAML,
   integrate through your normal deployment workflow.

Configuration exploration is a **suggestion engine** — it never
writes back to your mesh config on its own. The running config is
unchanged until you explicitly apply.

## Next Steps

- **[Evolution Health Checks](evolution-health-checks)** — the default mode
- **[Self-Healing](self-healing)** — Automatic failure recovery
- **[Predictive Analytics](predictive-analytics)** — Performance prediction
- **[Configuration](../core-concepts/configuration)** — Configuration system

---

*LeafMesh — Configuration exploration as an advanced complement to health-check mode.*
