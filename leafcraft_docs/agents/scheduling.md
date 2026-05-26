# Scheduled Agents

Any agent type can be scheduled using the `wake_up` field. LeafMesh triggers the agent on a cron, interval, or keyword schedule.

## Configuration

```yaml
agents:
  # Every 5 minutes
  collector:
    name: "collector"
    agent_type: "programmatic"
    wake_up: "*/5 * * * *"
    yields:
      readings: "array"
      timestamp: "string"
    can_call:
      - agent: "analyzer"
        condition: "readings != []"

  # Every hour at :00
  reporter:
    name: "reporter"
    model: "gpt-4o-mini"
    wake_up: "0 * * * *"
    yields:
      summary: "string"

  # Every day at midnight
  daily_digest:
    name: "daily_digest"
    model: "gpt-4o"
    wake_up: "0 0 * * *"
    yields:
      report: "string"
```

## Schedule Formats

| Format | Example | Meaning |
|--------|---------|---------|
| Cron (5-field) | `*/5 * * * *` | Every 5 minutes |
| Cron (5-field) | `0 9 * * 1` | Every Monday at 9 AM |
| Interval | `every 30 seconds` | Every 30 seconds |
| Interval | `every 5 minutes` | Every 5 minutes |
| Keyword | `hourly` | Top of every hour |
| Keyword | `daily` | Midnight |
| Keyword | `weekly` | Sunday midnight |

Cron expressions follow the standard five-field format: `minute hour day-of-month month day-of-week`.

## How It Works

When `wake_up` fires:

1. The scheduler publishes a scheduled-run event
2. The agent is invoked with empty `input_data`
3. The full pipeline executes: pre-compose → LLM call (or intelligence function) → yields parsing → can_call evaluation
4. Downstream agents are triggered if conditions match

```
Scheduler timer fires
    │
    ▼
Scheduled-run event published
    │
    ▼
Agent pipeline executes
    │  (empty input_data)
    ▼
can_call conditions evaluated
    │
    ▼
Downstream agents triggered
```

The execution follows the same pipeline as interactive calls. Scheduled agents are not special — they just have an automatic trigger.

## Runtime Schedule Management

```python
# Schedule an agent dynamically
leafmesh.schedule_agent("collector", "every 60 seconds")

# Unschedule an agent
leafmesh.unschedule_agent("collector")
```

Execution tracking records last execution time, execution count, and next run time.

## Common Patterns

### Periodic Data Collection

```yaml
agents:
  sensor_collector:
    name: "sensor_collector"
    agent_type: "programmatic"
    wake_up: "*/5 * * * *"
    yields:
      readings: "array"
      timestamp: "string"
    can_call:
      - agent: "analyzer"
        condition: "readings != []"
```

```python
# Function name "sensor_collector" matches the YAML agent name — auto_discover finds it
async def sensor_collector(llm_response, input_data, context):
    """Collect sensor data every 5 minutes"""
    import random
    from datetime import datetime

    readings = [round(random.gauss(100, 10), 2) for _ in range(20)]
    return {
        "readings": readings,
        "timestamp": datetime.now().isoformat()
    }
```

### Health Reporting

```yaml
agents:
  health_reporter:
    name: "health_reporter"
    model: "gpt-4o-mini"
    wake_up: "0 9 * * *"       # Daily at 9 AM
    prompt: |
      Summarize the system health metrics into a brief report.
      Include any anomalies or concerns.
    yields:
      report: "string"
      status: "string"
    can_call:
      - agent: "human_reviewer"
        condition: "status == 'critical'"
```

### Cache Maintenance

```yaml
agents:
  cache_monitor:
    name: "cache_monitor"
    agent_type: "programmatic"
    wake_up: "every 30 minutes"
    yields:
      hit_rate: "number"
      action_taken: "string"
```

```python
# Function name "cache_monitor" matches the YAML agent name — auto_discover finds it
async def cache_monitor(llm_response, input_data, context):
    """Check cache health and invalidate if needed"""
    stats = await leafmesh.get_llm_cache_stats()
    hit_rate = stats.get("hit_rate", 0)

    action = "none"
    if hit_rate < 0.3:
        action = "invalidated_stale_entries"

    return {
        "hit_rate": round(hit_rate, 2),
        "action_taken": action
    }
```

## Isolation

The scheduler runs in a background event loop, isolated from the main execution loop. Scheduled agent executions do not block interactive request processing.

## Next Steps

- **[Agent Types](overview)** — All four agent types
- **[Monitoring Patterns](../advanced/yield-monitoring)** — Scheduled monitoring systems
- **[Agent Configuration](../api-reference/agent-config)** — Full YAML reference

---

*LeafMesh — Time-triggered agents, same pipeline*
