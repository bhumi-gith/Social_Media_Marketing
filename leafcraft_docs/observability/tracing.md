# Distributed Tracing

LeafMesh automatically traces requests across agents, giving you full visibility into multi-agent workflows.

## Overview

LeafMesh automatically instruments:

- **LLM calls**: Model, token counts, latency, cache hit/miss
- **Mesh communications**: From/to agents, payload size, duration
- **Session operations**: Create, resume, end lifecycle
- **Tool executions**: Tool name, duration, success/failure

No setup is required — tracing activates automatically when your license key is set.

## PII Redaction (default ON)

Content-bearing fields — agent prompts, user messages, tool inputs and outputs, and LLM completions — are redacted before leaving your process and replaced with a `<redacted bytes:N>` placeholder. The trace structure (agent names, model IDs, token counts, latencies, cost, tool names, status flags) flows through unchanged, so dashboards and call-graph analysis remain fully useful.

This is the **default behavior** required for SOC 2 / ISO 27001 / GDPR-aligned deployments. Customer prompts and PII never leave your process.

To ship raw content (only recommended for fully self-hosted deployments with strict access control), opt out:

```bash
export LEAFMESH_OTEL_REDACT_PII=0
```

The redaction toggle does **not** affect: token counts, costs, agent / model / tool names, status, span timing, or any non-content metadata.

## Trace Structure

A typical multi-agent request generates a trace like:

```
mesh_call (root)
├── agent: triage
│   └── llm: gpt-4o-mini, tokens=150
├── mesh: triage → specialist
├── agent: specialist
│   ├── precompose: enrich_context
│   ├── llm: gpt-4o, tokens=800
│   ├── tool: web_request
│   └── llm: gpt-4o, tokens=400 (follow-up after tool)
```

## What You Can See in Traces

### LLM Call Details

| Detail | Description |
|--------|-------------|
| Model name | Which model was used |
| Provider | openai, anthropic, etc. |
| Token counts | Input and output tokens |
| Cache status | Whether the response came from cache |
| Duration | How long the call took |

### Mesh Call Details

| Detail | Description |
|--------|-------------|
| Source agent | Which agent initiated the call |
| Target agent | Which agent was called |
| Call depth | How deep in the chain |
| Session | Which session the call belongs to |

### Agent Execution Details

| Detail | Description |
|--------|-------------|
| Agent name | Which agent ran |
| Agent type | llm, programmatic, human |
| Model | LLM model used (if applicable) |

## Correlation

Traces correlate with business data through session IDs:

- **Trace**: Shows timing and flow of a request
- **Session data**: Shows the actual data at each step (browse in the Studio Sessions tab)

Use the trace to find slow steps, then jump to session data for the business context of that step.

## Next Steps

- **[Traceability API](traceability-api)** — REST API reference for querying traces, sessions, and spans
- **[Performance Metrics](metrics)** — Metrics collection
- **[Dashboard](dashboard)** — Building dashboards
- **[Monitoring](monitoring)** — Built-in monitoring

---

*LeafMesh — Distributed tracing built in*
