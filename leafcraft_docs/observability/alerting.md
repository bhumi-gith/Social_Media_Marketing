# Alerting & Notifications

Setting up alerts for LeafMesh system health and performance.

## Built-in Alerting: Self-Healing

LeafMesh's self-healing system provides automatic alerting and response. Agents transition through health states (healthy / degraded / critical / failed / recovering) and the platform takes appropriate action — rerouting traffic, restarting, spawning backups, or quarantining — surfacing the corresponding alerts in your dashboard.

## Dashboard Alerts

The LeafCraft dashboard surfaces:

- **Agent health changes** — degraded / critical / failed transitions
- **Self-healing actions** — restarts, reroutes, quarantines
- **Manager interventions** — when the Manager re-routes around a failure
- **Cost spikes** — high-cost LLM calls
- **Error rate increases** — per-agent error thresholds

Configure notification channels (Slack, PagerDuty, email) directly in the dashboard.

## Metric-Based Alerting

Periodically check metrics against thresholds:

```python
async def check_thresholds(leafmesh):
    """Run periodically via a scheduled agent or external cron"""
    agent_stats = leafmesh.get_agent_stats()

    for agent, stats in agent_stats.items():
        # Error rate alert
        if stats.get("error_rate", 0) > 0.1:
            await alert(f"High error rate: {agent} at {stats['error_rate']:.1%}")

        # Response time alert
        if stats.get("avg_response_ms", 0) > 5000:
            await alert(f"Slow agent: {agent} at {stats['avg_response_ms']}ms")

    # Cost alert
    cache = leafmesh.get_llm_cache_stats()
    # Track cumulative costs against budget
```

## Alert Channels

| Channel | Use Case | Integration |
|---------|----------|-------------|
| Slack | Team notifications | Webhook API |
| PagerDuty | Critical incidents | Event API |
| Email | Reports, summaries | SMTP |
| Grafana | Dashboard alerts | Prometheus metrics |

## Using Scheduled Agents for Alerting

```yaml
agents:
  health_reporter:
    agent_type: "programmatic"
    wake_up: "every 5 minutes"
    yields:
      status: "string"
      alerts: "string"
```

```python
async def health_reporter(llm_response, input_data, context):
    stats = leafmesh.get_agent_stats()
    alerts = []
    for agent, s in stats.items():
        if s.get("error_rate", 0) > 0.1:
            alerts.append(f"{agent}: error rate {s['error_rate']:.1%}")
    if alerts:
        await send_alert("\n".join(alerts))
    return {"status": "checked", "alerts": str(alerts)}
```

## Next Steps

- **[Monitoring](monitoring)** — System monitoring
- **[Dashboard](dashboard)** — Building dashboards
- **[Self-Healing](../advanced/self-healing)** — Automatic recovery

---

*LeafMesh — Alerting and notification patterns*
