# Traceability & Observability

LeafMesh provides full traceability across every multi-agent workflow. Every session, agent invocation, LLM call, tool execution, and handoff is captured automatically — giving you complete visibility into what your agents are doing, why, and how long it takes.

## How Traceability Works

Every time you call `mesh_call()`, LeafMesh automatically creates a **session** — a complete record of everything that happened during that request. Inside the session, every agent, every LLM call, every tool execution, and every handoff is captured as a **span** in a parent-child hierarchy.

You don't instrument anything. It's built into the runtime.

```
session:sess_abc123
└── mesh:triage
    └── agent:triage
        ├── precompose:context_processor
        ├── connector:llm
        │   └── llm:openai/gpt-4o
        │       └── tool:web_search
        │           └── llm:openai/gpt-4o  (follow-up after tool)
        ├── chain:format_output
        └── compose:shaper
```

When an agent hands off to another agent, the next agent gets its own subtree under the same session — so you can trace the full execution path across your entire swarm.

## What You Can See

### Session Overview

Every session captures:
- **Duration** — Total end-to-end time
- **Agent count** — How many agents were involved
- **LLM calls** — Number of model invocations
- **Token usage** — Total tokens consumed
- **Cost** — Total LLM cost in USD
- **Status** — Success, error, or in-progress
- **Input / Output** — What went in and what came out

### Agent Execution Tree

For each agent in a session, LeafMesh groups its activity into four phases:

| Phase | What It Captures |
|-------|-----------------|
| **Precompose** | Context processors and input transformations that run before the agent executes |
| **Connector** | The core execution — LLM calls, tool invocations, human-in-the-loop interactions |
| **Chain** | Post-processing steps like output formatting and validation |
| **Compose** | Output shaping and final assembly |

Each phase shows duration, status, and any errors — so you can pinpoint exactly where time is spent or where failures occur.

### Span Types

Every span is classified by type so you can filter and understand what's happening at each level:

| Span Type | What It Represents |
|-----------|-------------------|
| `session` | The top-level request |
| `mesh` | A mesh call routing to an agent |
| `agent` | An agent's full execution |
| `precompose` | A `@pre_compose` decorator processor |
| `connector` | The agent's execution connector (LLM, human, system) |
| `llm` | An LLM model invocation |
| `tool` | A tool function call |
| `chain` | A `@chain` or `@conditional_chain` post-processor |
| `compose` | A `@compose` output shaper |

### Agent Types

LeafMesh tracks what kind of agent is executing:

| Agent Type | Description |
|------------|-------------|
| `llm` | LLM-powered agent |
| `programmatic` | Rule-based / code-only agent |
| `human` | Human-in-the-loop agent |
| `external` | External system agent |

## Built-in Dashboard

The LeafMesh dashboard gives you all of this out of the box — no configuration required. Key views include:

### KPI Overview
Real-time cards showing total sessions, traces, errors, token usage, and LLM cost across your deployment. Delta indicators show trends compared to the previous period.

### Session Explorer
Browse and search sessions with filters for environment, status, agent, and time range. Click into any session to see the full execution tree.

### Traceability View
The core debugging view. Left panel shows the agent tree with expandable phases (precompose → connector → chain → compose). Right panel shows the waterfall timeline — every span laid out on a time axis so you can see parallelism, bottlenecks, and handoff latency at a glance.

### Agent Performance
Per-agent statistics including invocation counts, error rates, and latency percentiles (p50, p90, p99). Identify which agents are slow or unreliable.

### LLM Cost Analytics
Cost breakdown by model and provider over time. Track spending trends, compare model costs, and identify optimization opportunities — like switching expensive agents to cheaper models.

### Agent Flow Graph
Topology visualization showing which agents call which. See the full communication pattern across your swarm.

## Environment Filtering

All dashboard views support environment scoping — filter by `production`, `staging`, or any custom environment token. This lets you compare behavior across environments or focus on production issues.

## What Gets Captured Automatically

You don't need to add any instrumentation code. LeafMesh captures all of this from the runtime:

- **Every agent invocation** — which agent, who called it, how long it took
- **Every LLM call** — provider, model, tokens, cost, latency
- **Every tool execution** — which tool, success/failure, duration
- **Every handoff** — agent-to-agent routing decisions
- **Every decorator** — precompose, chain, compose processing steps
- **Input and output** — at every level of the hierarchy
- **Errors and exceptions** — with full context about where they occurred

## Next Steps

- **[Distributed Tracing](tracing)** — How tracing works in LeafMesh
- **[Performance Metrics](metrics)** — Metrics collection
- **[Dashboard](dashboard)** — Platform-level analytics

---

*LeafMesh — Full traceability for multi-agent systems*
