# Predictive Analytics

LeafMesh learns per-model performance from your live traffic and uses
that knowledge to route requests to the model that has historically
done best on similar work. Alongside this, it surfaces aggregated
usage analytics for cost tracking, agent-level statistics, and
custom dashboards.

## Adaptive model selection

The platform tracks, for each model you use, how it has performed
in the past: response time, quality, cost, success rate, and other
runtime signals. When a new request comes in, it routes the request
to the model whose track record on similar work looks best.

You don't categorise requests by hand — the platform does that
automatically. Prediction accuracy improves as the history grows.

To enable adaptive selection on an agent, configure
`optimization_strategy` in YAML:

```yaml
agents:
  my_agent:
    model: "gpt-4o"                     # Default fallback model
    optimization_strategy: "performance"  # Use adaptive selection
```

If the platform doesn't yet have enough history to confidently pick
a model, the configured default is used.

## Usage analytics

System-wide aggregated analytics are exposed through a single call:

```python
analytics = leafmesh.get_usage_analytics()

# Returns:
# {
#     "total_events": 15847,
#     "events_by_type": {"agent.call.completed": 3421, ...},
#     "processing_rates": {...},
#     "error_rate": 0.02,
# }
```

## LLM cost tracking

Cost-related signals are aggregated separately so you can see cache
effectiveness at a glance:

```python
cache_stats = leafmesh.get_llm_cache_stats()

# Returns:
# {
#     "hit_rate": 0.34,
#     "total_requests": 5000,
#     "cache_hits": 1700,
#     "estimated_savings": 42.50
# }
```

## Per-agent statistics

```python
agent_stats = leafmesh.get_agent_stats()

# Per agent:
# {
#     "execution_count": 1247,
#     "error_rate": 0.015,
#     "avg_response_ms": 850,
#     "current_status": "healthy"
# }
```

## Building custom analytics

For pre-aggregated statistics in Python, use
`leafmesh.get_usage_analytics()` and `leafmesh.get_llm_cache_stats()`.
For richer dashboarding, point your monitoring stack at the standard
metrics endpoints documented in the observability section.

## Next Steps

- **[Adaptive Execution](../models/adaptive-execution)** — Model selection strategies
- **[Anomaly Detection](anomaly-detection)** — Detecting system anomalies
- **[Monitoring](../observability/monitoring)** — System monitoring

---

*LeafMesh — Performance prediction and analytics*
