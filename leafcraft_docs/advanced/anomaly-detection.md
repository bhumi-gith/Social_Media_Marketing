# Anomaly Detection

LeafMesh detects anomalies through built-in health monitoring and automatic coordination decisions on every event.

## Health-Based Anomaly Detection

The platform continuously tracks per-agent runtime metrics:

| Metric | Description |
|--------|-------------|
| Response time | How long an agent takes to produce output |
| Error rate | Fraction of requests that fail |
| Consecutive failures | A streak of back-to-back failures |
| Quality score | Aggregated signal of recent output quality |

When metrics breach configurable health thresholds, the platform marks the agent as degraded and triggers an appropriate recovery action. See the configuration reference for tunable thresholds.

## Health Reporting

Each agent has a health state that reflects whether it is operating normally, showing early-warning signs, in active trouble, non-responsive, or in the middle of a recovery action. Operators see these states surfaced via dashboards and the management API — you do not have to model the state machine yourself.

## Event-Driven Detection

Anomaly detection is event-driven, not polling-based:

```
Agent error occurs
    │
    ▼
Platform receives the failure signal
    │
    ▼
Health metrics update
    │
    ▼
Thresholds are re-evaluated
    │
    ▼
If a threshold is crossed → recovery action is triggered
```

This means **zero overhead during normal operation** — the system only activates when errors actually occur.

## Automatic Coordination Decisions

Beyond raw health metrics, the platform classifies every event and applies automatic coordination decisions when patterns look unusual — for example, retrying a flaky agent, watching a chain with low confidence, calling off a contradictory chain, or escalating a sustained failure to a human. You do not configure these by hand; they happen as part of normal execution.

## Intelligence Function Anomaly Detection

Build custom anomaly detection in intelligence functions:

```python
async def analyzer(llm_response, input_data, context):
    # Load baseline from your external database or API
    baseline = await database.get_baseline("default")
    if not baseline:
        baseline = {"mean": 100.0, "std": 10.0}

    # Check current values against baseline
    value = llm_response.get("measurement", 0)
    z_score = abs(value - baseline["mean"]) / max(baseline["std"], 0.01)

    llm_response["is_anomaly"] = z_score > 3.0
    llm_response["z_score"] = round(z_score, 2)

    return llm_response
```

## Recovery Actions for Anomalies

When the platform detects an anomaly it applies graduated recovery. Depending on the nature of the failure it may restart the agent (preserving session state), route traffic away from it, isolate it from the mesh, scale capacity up, roll a recent configuration change back, or bring up a backup agent. Operators see the action that was taken; the platform decides which one to apply.

## Monitoring Anomaly Events

Recovery activity is exposed via the analytics surface:

```python
analytics = leafmesh.get_usage_analytics()
# Inspect recovery event counts for anomaly frequency
```

## Next Steps

- **[Self-Healing](self-healing)** — Complete self-healing reference
- **[Predictive Analytics](predictive-analytics)** — Performance prediction
- **[Alerting](../observability/alerting)** — Alert configuration

---

*LeafMesh — Automatic anomaly detection and response*
