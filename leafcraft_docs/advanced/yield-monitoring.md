# Monitoring & Alerting Patterns

How to build multi-agent monitoring systems with LeafMesh. This guide covers scheduled agents, anomaly detection, adaptive thresholds, and alert escalation — using simple examples you can adapt to any domain.

## Overview

A monitoring system in LeafMesh uses specialized agents that each handle one concern:

- **Collector agent**: Gathers data on a schedule
- **Analyzer agent**: Detects anomalies and computes metrics
- **Alert agent**: Decides severity and notifies the right people
- **Supervisor agent** (human): Handles escalations that need judgment

These agents coordinate through YAML-defined `can_call` rules. The system runs continuously using `wake_up` scheduling.

## Basic Monitoring Swarm

### Configuration

```yaml
name: "monitoring_swarm"
version: "1.0.0"
architecture: "managed_mesh"

redis:
  host: "localhost"
  port: 6379
  session_ttl: 86400  # 24 hours

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_response_time: 60

mesh:
  call_timeout: 120
  max_retries: 2
  retry_backoff: 2

agents:
  # Runs every 5 minutes, collects readings
  collector:
    name: "collector"
    agent_type: "programmatic"
    communication_type: "chain"
    wake_up: "*/5 * * * *"
    yields:
      readings: "array"
      timestamp: "string"
      source: "string"
    can_call:
      - agent: "analyzer"
        condition: "readings != []"

  # Analyzes readings for anomalies
  analyzer:
    name: "analyzer"
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 500
    prompt: |
      You analyze numeric readings and detect anomalies.
      Flag any value that deviates more than 2 standard deviations
      from the mean. Report the anomaly count and severity.
    yields:
      anomaly_count: "number"
      severity: "string"
      analysis: "string"
      flagged_values: "array"
    can_call:
      - agent: "alerter"
        condition: "anomaly_count > 0"

  # Sends alerts based on severity
  alerter:
    name: "alerter"
    model: "gpt-4o-mini"
    temperature: 0.0
    max_tokens: 200
    prompt: |
      You determine the appropriate alert action based on severity.
      For "low" severity: log and monitor.
      For "medium" severity: send notification.
      For "high" severity: escalate to human supervisor immediately.
    yields:
      action: "string"
      message: "string"
      escalate: "boolean"
    can_call:
      - agent: "supervisor"
        condition: "escalate == true"

  # Human-in-the-loop for high-severity issues
  supervisor:
    name: "supervisor"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    human_timeout_seconds: 1800
    yields:
      decision: "string"
      notes: "string"
```

### Implementation

```python
import asyncio
from datetime import datetime
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("monitoring_swarm.yaml")


async def collector(llm_response, input_data, context):
    """Collect data from your source — replace with your actual data source"""
    import random

    # Simulate readings (replace with real data: API call, DB query, sensor, etc.)
    readings = [random.gauss(100, 10) for _ in range(20)]

    # Inject occasional anomaly for demonstration
    if random.random() < 0.3:
        readings.append(random.gauss(200, 5))  # Outlier

    return {
        "readings": [round(r, 2) for r in readings],
        "timestamp": datetime.now().isoformat(),
        "source": "demo_sensor"
    }


async def analyzer(llm_response, input_data, context):
    """Detect anomalies using simple statistical analysis"""
    readings = input_data.get("readings", [])

    if not readings:
        return {"anomaly_count": 0, "severity": "none", "analysis": "No data", "flagged_values": []}

    # Compute statistics
    mean = sum(readings) / len(readings)
    variance = sum((x - mean) ** 2 for x in readings) / len(readings)
    std_dev = variance ** 0.5

    # Flag values beyond 2 standard deviations
    threshold = 2 * std_dev
    flagged = [r for r in readings if abs(r - mean) > threshold]

    # Determine severity
    anomaly_ratio = len(flagged) / len(readings)
    if anomaly_ratio > 0.1:
        severity = "high"
    elif anomaly_ratio > 0.05:
        severity = "medium"
    elif len(flagged) > 0:
        severity = "low"
    else:
        severity = "none"

    return {
        "anomaly_count": len(flagged),
        "severity": severity,
        "analysis": f"Processed {len(readings)} readings. Mean: {mean:.2f}, StdDev: {std_dev:.2f}. "
                    f"Found {len(flagged)} anomalies ({anomaly_ratio:.1%} anomaly rate).",
        "flagged_values": flagged
    }


async def alerter(llm_response, input_data, context):
    """Decide alert action based on severity"""
    severity = input_data.get("severity", "none")
    anomaly_count = input_data.get("anomaly_count", 0)
    analysis = input_data.get("analysis", "")

    if severity == "high":
        return {
            "action": "escalate",
            "message": f"HIGH SEVERITY: {anomaly_count} anomalies detected. {analysis}",
            "escalate": True
        }
    elif severity == "medium":
        return {
            "action": "notify",
            "message": f"Warning: {anomaly_count} anomalies detected. {analysis}",
            "escalate": False
        }
    else:
        return {
            "action": "log",
            "message": f"Low-level anomaly detected: {anomaly_count} items flagged.",
            "escalate": False
        }


async def main():
    await leafmesh.start()
    print("Monitoring swarm started. Collector runs every 5 minutes.\n")

    # Manual trigger for demonstration
    result = await leafmesh.mesh_call(
        "collector",
        input_data={},
        session_id="monitoring_demo"
    )
    print(f"Pipeline result: {result}")

    await leafmesh.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Scheduled Agents with `wake_up`

The `wake_up` field uses cron syntax to run agents on a schedule:

```yaml
agents:
  # Every 5 minutes
  frequent_collector:
    wake_up: "*/5 * * * *"

  # Every hour at minute 0
  hourly_reporter:
    wake_up: "0 * * * *"

  # Every day at midnight
  daily_digest:
    wake_up: "0 0 * * *"

  # Every Monday at 9 AM
  weekly_summary:
    wake_up: "0 9 * * 1"
```

When `wake_up` fires, LeafMesh invokes the agent automatically with empty `input_data`. The agent's intelligence function runs, produces yields, and `can_call` rules route the output to downstream agents.

## Adaptive Thresholds

Static thresholds miss anomalies in changing systems. Use session memory to adapt thresholds over time:

```python
async def adaptive_analyzer(llm_response, input_data, context):
    """Analyzer that learns what 'normal' looks like"""
    readings = input_data.get("readings", [])
    session_id = context.get("session_id", "default")

    # Load historical baseline from memory
    baseline = context.get("memory", {}).get("baseline", {
        "running_mean": 100.0,
        "running_std": 10.0,
        "samples_seen": 0
    })

    # Update running statistics (exponential moving average)
    alpha = 0.1  # Learning rate
    current_mean = sum(readings) / len(readings) if readings else baseline["running_mean"]
    current_std = (sum((x - current_mean) ** 2 for x in readings) / len(readings)) ** 0.5 if readings else baseline["running_std"]

    new_mean = baseline["running_mean"] * (1 - alpha) + current_mean * alpha
    new_std = baseline["running_std"] * (1 - alpha) + current_std * alpha

    # Use adaptive threshold
    threshold = new_mean + (2 * new_std)
    flagged = [r for r in readings if r > threshold]

    # Store updated baseline
    updated_baseline = {
        "running_mean": round(new_mean, 4),
        "running_std": round(new_std, 4),
        "samples_seen": baseline["samples_seen"] + len(readings)
    }

    # Save to session memory for next invocation
    await context.get("set_memory", lambda *a: None)(
        session_id, "baseline", updated_baseline
    )

    return {
        "anomaly_count": len(flagged),
        "severity": "high" if len(flagged) > 2 else "low" if flagged else "none",
        "adaptive_threshold": round(threshold, 2),
        "baseline_mean": round(new_mean, 2),
        "flagged_values": flagged,
        "analysis": f"Adaptive threshold: {threshold:.2f} (mean: {new_mean:.2f}, std: {new_std:.2f}). "
                    f"Total samples processed: {updated_baseline['samples_seen']}."
    }
```

The threshold adapts automatically. After 100 invocations, it has learned what "normal" looks like for your system. No manual tuning required.

## Multi-Stage Alert Escalation

Chain agents for progressively more serious responses:

```yaml
agents:
  analyzer:
    name: "analyzer"
    # ...
    can_call:
      - agent: "auto_remediate"
        condition: "severity == 'low'"
      - agent: "notify_team"
        condition: "severity == 'medium'"
      - agent: "page_oncall"
        condition: "severity == 'high'"

  auto_remediate:
    name: "auto_remediate"
    agent_type: "programmatic"
    yields:
      action_taken: "string"
      success: "boolean"
    can_call:
      - agent: "notify_team"
        condition: "success == false"

  notify_team:
    name: "notify_team"
    model: "gpt-4o-mini"
    prompt: "Compose a clear, concise alert notification for the engineering team."
    yields:
      notification: "string"
      channel: "string"

  page_oncall:
    name: "page_oncall"
    model: "gpt-4o-mini"
    prompt: "Compose an urgent page for the on-call engineer with context and recommended actions."
    yields:
      page_content: "string"
      urgency: "string"
    can_call:
      - agent: "human_oncall"
        condition: "urgency == 'critical'"

  human_oncall:
    name: "human_oncall"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    human_timeout_seconds: 900
```

This creates a 4-tier escalation path — all defined declaratively:

1. **Low**: Auto-remediate. If remediation fails, escalate to team notification.
2. **Medium**: Notify the engineering team via chat/email.
3. **High**: Page the on-call engineer with context.
4. **Critical**: Escalate to human on-call for manual decision.

## Pre-Compose for Data Enrichment

Use the pre-compose pipeline to enrich monitoring data before the LLM sees it:

```python
from leafmesh import pre_compose

async def enrich_with_history(input_data, context):
    """Pull historical context from your data store before analysis"""
    source = input_data.get("source", "unknown")
    # Load last 24 hours of readings from your store of choice
    history = await your_history_store.get(f"history:{source}")
    return {"historical_readings": history or [], **input_data}

async def clean_readings(input_data, context):
    """Remove null values and obvious sensor errors"""
    readings = input_data.get("readings", [])
    cleaned = [r for r in readings if r is not None and -1000 < r < 10000]
    return {**input_data, "readings": cleaned, "removed_count": len(readings) - len(cleaned)}

@pre_compose(
    context_processor=enrich_with_history,
    input_processor=clean_readings
)
async def analyzer(llm_response, input_data, context):
    # input_data now has historical_readings and cleaned readings
    readings = input_data["readings"]
    historical = input_data.get("historical_readings", [])

    # Compare current readings against historical baseline
    # ... analysis logic ...

    return {"anomaly_count": 0, "severity": "none", "analysis": "Normal"}
```

The pre-compose pipeline runs **before** the LLM call. It is deterministic Python — no LLM involvement. This keeps LLM prompts clean and focused while your data enrichment happens in code you control.

## Monitoring with Tools

Register custom tools that agents can invoke:

```yaml
agents:
  collector:
    name: "collector"
    agent_type: "programmatic"
    tools: ["database_query", "http_request"]
    wake_up: "*/5 * * * *"
```

```python
from leafmesh import tool

@tool("database_query")
async def query_database(query: str, parameters: list = None):
    """Execute a read-only database query"""
    # Replace with your actual database connection
    import aiosqlite
    async with aiosqlite.connect("monitoring.db") as db:
        cursor = await db.execute(query, parameters or [])
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@tool("http_request")
async def fetch_endpoint(url: str, headers: dict = None):
    """Fetch data from an HTTP endpoint"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers or {}) as resp:
            return await resp.json()
```

Now the collector agent can pull data from databases and APIs using the tools defined in its YAML config.

## Production Deployment

### Self-Healing for Monitoring Agents

Monitoring agents that go down silently are worse than no monitoring. Enable self-healing:

```yaml
self_healing:
  enabled: true
  detection_interval: 15       # Check every 15 seconds
  max_recovery_attempts: 5
  recovery_strategies:
    - "restart_agent"           # First: restart the failed agent
    - "failover_to_backup"      # Second: switch to backup
    - "circuit_breaker"         # Third: stop calling broken downstream
```

If the `collector` agent crashes, self-healing detects the failure within 15 seconds, restarts it, and the `wake_up` schedule resumes automatically.

### Observability for the Monitoring System

Yes — you monitor the monitoring system:

```yaml
observability:
  service_name: "monitoring_swarm"
  metrics_retention_minutes: 1440  # 24 hours
```

Access the observability dashboard to see:
- Agent health status
- Processing latency per agent
- Error rates and retry counts
- Alert volume over time

### File Organization for Larger Systems

```
monitoring_system/
├── config.yaml                 # Swarm configuration
├── main.py                     # Entry point
├── agency/
│   ├── __init__.py
│   ├── agency_client.py        # LeafMesh init + agent registration
│   ├── collector_agent.py      # Data collection logic
│   ├── analyzer_agent.py       # Anomaly detection logic
│   ├── alerter_agent.py        # Alert routing logic
│   └── tools/
│       ├── database.py         # Database query tool
│       └── notifications.py    # Notification tool
```

```python
# agency/agency_client.py
from leafmesh import LeafMesh

_leafmesh = None

async def initialize(config_path: str):
    global _leafmesh
    _leafmesh = LeafMesh.from_yaml(config_path)
    await _leafmesh.start()

    from . import collector_agent, analyzer_agent, alerter_agent
    collector_agent.register(_leafmesh)
    analyzer_agent.register(_leafmesh)
    alerter_agent.register(_leafmesh)

    return _leafmesh
```

```python
# main.py
import asyncio
from agency.agency_client import initialize

async def main():
    leafmesh = await initialize("config.yaml")
    print("Monitoring system running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns Summary

| Pattern | When to Use |
|---------|------------|
| `wake_up` scheduling | Periodic data collection or health checks |
| Adaptive thresholds | Systems where "normal" changes over time |
| Multi-stage escalation | Tiered alert severity with different responses |
| Pre-compose enrichment | Adding historical context before analysis |
| Custom tools | Accessing databases, APIs, or external services |
| Human-in-the-loop | High-severity decisions that need judgment |
| Self-healing | Ensuring the monitoring system itself stays up |

## Next Steps

- **[Self-Healing Guide](self-healing)** — Deep dive into recovery strategies
- **[Tools Reference](../tools/overview)** — Built-in and custom tools
- **[Memory System](../memory/short-term)** — Session state for adaptive logic
- **[Agent Configuration](../api-reference/agent-config)** — Full YAML reference

---

*LeafMesh — Build monitoring systems that watch, learn, and act*
