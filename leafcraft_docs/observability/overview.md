# Observability Overview

LeafMesh maintains a clean separation between business state (sessions, agent yields, conversation history) and operational monitoring (traces, metrics, logs). Each is optimized for its purpose.

## Observability is Built In

Observability is a **core part** of LeafMesh — not optional. When `LEAFMESH_LICENSE_KEY` is set, tracing, metrics, and log export auto-enable at startup with zero YAML configuration needed.

```bash
# That's it — observability is automatic
export LEAFMESH_LICENSE_KEY="your-license-key"
```

### What Gets Instrumented Automatically

- **LLM calls** — model name, token counts, latency, provider
- **Mesh communications** — source/target agents, duration, depth
- **Session operations** — session lifecycle events
- **HTTP requests** — outbound HTTP auto-instrumented
- **System metrics** — CPU, memory, process-level metrics
- **Log export** — All LeafMesh logs forwarded automatically (use [`LeafMeshLogger`](logging) for your own code)
- **PII redacted by default** — Customer prompts, user messages, tool I/O, and LLM completions are redacted before leaving your process; structural metadata (agent names, token counts, latencies, cost, status) flows through unchanged.

## The Observability Boundary

```
Business State                      Operational Monitoring
──────────────                      ──────────────────────
Sessions, conversation history      Distributed traces
Agent yields                        Request latency spans
Mesh communications                 Error rate metrics
                                    Throughput counters
                                    Resource utilization
                                    Log export

Query: "What happened in session X?"    Query: "Why was agent B slow?"
→ Studio Sessions tab                    → Dashboard
```

## Built-in Analytics

LeafMesh provides built-in analytics independent of the dashboard:

```python
# Event statistics
analytics = await leafmesh.get_usage_analytics()

# LLM cache effectiveness
cache_stats = await leafmesh.get_llm_cache_stats()
```

## Data Grouping in Telemetry

All telemetry data is grouped by four dimensions:

| Dimension | Source | Description |
|-----------|--------|-------------|
| `license_key` | `LEAFMESH_LICENSE_KEY` | Groups data by license holder |
| `organization_id` | From license validation | Organization scope |
| `env_token` | `LEAFMESH_ENV_TOKEN` | Environment (dev/staging/prod) |
| `service_name` | `config.name` (YAML) | Project name |

## Why the Separation Matters

- **Different retention**: Business data may need months; traces may rotate daily
- **Different access patterns**: Business queries by session; operational queries by time range
- **Different compliance**: Business data may be regulated; trace data typically isn't
- **No interference**: Operational queries don't affect business-critical data

## Next Steps

- **[Logging](logging)** — Send your application logs to the LeafCraft dashboard
- **[System Monitoring](monitoring)** — Built-in monitoring
- **[Distributed Tracing](tracing)** — What you can trace
- **[Performance Metrics](metrics)** — Metrics collection
- **[Dashboard](dashboard)** — Building dashboards
- **[Traceability API](traceability-api)** — REST API for the traceability dashboard
- **[Alerting](alerting)** — Alert configuration

---

*LeafMesh — Observability with clean boundaries*
