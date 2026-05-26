# System Monitoring

Built-in monitoring capabilities in LeafMesh.

## Built-in Analytics

### Usage Analytics

```python
analytics = leafmesh.get_usage_analytics()
```

Returns aggregated statistics:

| Metric | Description |
|--------|-------------|
| `total_events` | Total events processed |
| `events_by_type` | Event counts grouped by type |
| `processing_rates` | Events per second |
| `error_rate` | Ratio of error events to total events |

### LLM Cache Statistics

```python
cache_stats = leafmesh.get_llm_cache_stats()
```

| Metric | Description |
|--------|-------------|
| `hit_rate` | Cache hit ratio |
| `total_requests` | Total LLM requests |
| `cache_hits` | Requests served from cache |
| `estimated_savings` | Estimated cost savings from caching |

### Agent Statistics

```python
agent_stats = leafmesh.get_agent_stats()
```

Per-agent metrics:

| Metric | Description |
|--------|-------------|
| `execution_count` | Total executions |
| `error_count` | Total errors |
| `error_rate` | Error ratio |
| `avg_response_ms` | Average response time |
| `current_status` | Current health status |

## Health Check Endpoint

The API server provides a liveness endpoint with overall agent health:

```
GET http://localhost:18820/health
```

```json
{
  "status": "healthy",
  "agents": {
    "total_registered": 8,
    "healthy": 7,
    "degraded": 1,
    "failed": 0
  }
}
```

## Periodic Monitoring Script

```python
async def monitor_system(leafmesh):
    """Run as a scheduled agent or external script"""
    analytics = leafmesh.get_usage_analytics()
    agent_stats = leafmesh.get_agent_stats()

    # Check error rates
    for agent, stats in agent_stats.items():
        if stats.get("error_rate", 0) > 0.1:
            print(f"WARNING: {agent} error rate: {stats['error_rate']}")
```

## Next Steps

- **[Distributed Tracing](tracing)** — What you can trace
- **[Performance Metrics](metrics)** — Detailed metrics
- **[Alerting](alerting)** — Alert configuration

---

*LeafMesh — Built-in system monitoring*
