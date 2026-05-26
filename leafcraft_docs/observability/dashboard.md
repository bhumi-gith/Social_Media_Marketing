# Monitoring Dashboard

Building custom monitoring dashboards for LeafMesh systems.

## LeafCraft Dashboard

The **LeafCraft dashboard** is the primary way to monitor your agents — it provides full traceability, session explorer, agent performance, LLM cost analytics, and more out of the box (see [Traceability API](traceability-api) for details).

This page covers building **additional custom dashboards** using the LeafMesh analytics APIs for use cases like internal tooling or custom monitoring.

## Data Sources for Custom Dashboards

### 1. Health Check Endpoint

Poll the API server health endpoint:

```
GET /health
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

### 2. LeafMesh Analytics API

```python
# Usage analytics
analytics = leafmesh.get_usage_analytics()

# Agent statistics
agent_stats = leafmesh.get_agent_stats()

# Cache statistics
cache_stats = leafmesh.get_llm_cache_stats()
```

## Building a Custom Dashboard

### FastAPI Dashboard Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/dashboard/metrics")
async def dashboard_metrics():
    return {
        "analytics": leafmesh.get_usage_analytics(),
        "agents": leafmesh.get_agent_stats(),
        "cache": leafmesh.get_llm_cache_stats()
    }
    # For component health status, use the built-in health endpoint:
    # GET http://localhost:18820/health
```

### Key Metrics to Display

| Panel | Metrics | Source |
|-------|---------|--------|
| System Health | Agent health | Health endpoint |
| Agent Performance | Response times, error rates | `leafmesh.get_agent_stats()` |
| LLM Costs | Total cost, cost by model, cache savings | `leafmesh.get_llm_cache_stats()` |
| Event Flow | Events/second | `leafmesh.get_usage_analytics()` |

## Integration with Grafana

Export metrics to Prometheus for Grafana dashboards:

```python
from prometheus_client import Gauge, Counter, start_http_server

agent_errors = Counter("swarm_agent_errors_total", "Agent errors", ["agent"])
agent_latency = Gauge("swarm_agent_latency_ms", "Agent response time", ["agent"])
cache_hit_rate = Gauge("swarm_cache_hit_rate", "LLM cache hit rate")

async def export_metrics():
    """Periodically export metrics to Prometheus"""
    agent_stats = leafmesh.get_agent_stats()
    for agent, stats in agent_stats.items():
        agent_latency.labels(agent=agent).set(stats.get("avg_response_ms", 0))

    cache = leafmesh.get_llm_cache_stats()
    cache_hit_rate.set(cache.get("hit_rate", 0))
```

## Next Steps

- **[Traceability API](traceability-api)** — REST API for session/agent/span hierarchy
- **[Alerting](alerting)** — Alert configuration
- **[Monitoring](monitoring)** — System monitoring
- **[Metrics](metrics)** — Metrics reference

---

*LeafMesh — Building monitoring dashboards*
