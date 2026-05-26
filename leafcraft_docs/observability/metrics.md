# Performance Metrics

Metrics available in LeafMesh for monitoring system health and performance.

## Built-in Metrics

### Agent Health Metrics

LeafMesh tracks per-agent metrics automatically and surfaces them in the dashboard:

| Metric | Description |
|--------|-------------|
| `response_time_ms` | Average response time |
| `error_rate` | Error ratio |
| `success_rate` | Success ratio |
| `active_sessions` | Current sessions |
| `consecutive_failures` | Failures without success |
| `uptime_seconds` | Time since last start |
| `quality_score` | Output quality |

### LLM Cost Metrics

Every LLM call contributes cost data — model, prompt/completion tokens, estimated cost, response time, cache hit/miss — which is aggregated in the dashboard and accessible via:

```python
cache_stats = leafmesh.get_llm_cache_stats()
```

### Event Processing Metrics

```python
analytics = leafmesh.get_usage_analytics()
```

| Metric | Description |
|--------|-------------|
| `total_events` | Total events processed |
| `events_by_type` | Breakdown by event type |
| `processing_rates` | Events/second |

## Performance Baselines

Typical performance characteristics:

| Operation | Expected Latency |
|-----------|-----------------|
| Request routing | 10-50ms |
| Condition evaluation | ~1ms |
| LLM call (fast model) | 300-1000ms |
| LLM call (capable model) | 500-5000ms |
| Tool execution | Varies |
| Mesh call overhead | 5-20ms |

The LLM call dominates request latency; framework overhead is small.

## Custom Metrics

Build custom metrics using the public APIs:

```python
async def collect_custom_metrics():
    analytics = leafmesh.get_usage_analytics()
    agent_stats = leafmesh.get_agent_stats()
    cache_stats = leafmesh.get_llm_cache_stats()

    return {
        "total_events": analytics.get("total_events", 0),
        "error_rate": analytics.get("error_rate", 0),
        "agents": agent_stats,
        "cache_hit_rate": cache_stats.get("hit_rate", 0),
        "estimated_savings": cache_stats.get("estimated_savings", 0)
    }
```

## Adaptive Model Selection Metrics

When adaptive model selection is enabled, LeafMesh tracks per-model history (response time, output quality, cost per request, success rate, throughput) and uses it to inform future routing decisions.

## Next Steps

- **[Dashboard](dashboard)** — Building monitoring dashboards
- **[Alerting](alerting)** — Alert configuration
- **[Monitoring](monitoring)** — System monitoring overview

---

*LeafMesh — Performance metrics reference*
