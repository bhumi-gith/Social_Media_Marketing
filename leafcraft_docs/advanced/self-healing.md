# Self-Healing Networks

LeafMesh detects degraded or failing agents and applies graduated
recovery automatically — restarting them, routing around them,
falling back to a backup, or escalating — without operator
intervention. You configure the policy; the platform makes the
runtime decisions.

## How self-healing works

Self-healing is **event-driven, not polling-based**. The platform
listens for agent and mesh failure signals and only activates when
real errors occur. There is zero overhead during normal operation.

When the platform detects a problem:

1. Health metrics for the affected agent are updated (response time,
   error rate, consecutive failures, quality score).
2. The agent's health is reassessed against your configured thresholds.
3. The appropriate recovery action is selected based on severity.
4. The action is executed — restart, reroute traffic, fall back to a
   backup, isolate the agent, etc.
5. A recovery event is recorded with full context for audit.

## Configuration

Enable self-healing in your YAML config:

```yaml
self_healing:
  enabled: true
  detection_interval: 15          # Seconds between health re-evaluations
  max_recovery_attempts: 5        # Max recovery attempts per agent
  recovery_strategies:
    - "restart_agent"             # First: restart the failed agent
    - "failover_to_backup"        # Second: switch to backup
    - "circuit_breaker"           # Third: stop calling the broken agent
```

The strategies are tried in order. If the first strategy fails, the
platform tries the next one.

## Health assessment

### Agent health states

Each agent has a health state that reflects whether it is operating
normally, showing early-warning signs, in active trouble,
non-responsive, or in the middle of a recovery action. Operators see
these states in dashboards and the management API — you do not have
to model the state machine yourself.

### Metrics tracked

The platform collects these metrics for each agent. The thresholds
that move an agent between states are configurable — see the
configuration reference for tunable values.

| Metric | Description |
|--------|-------------|
| `response_time_ms` | Average response time |
| `error_rate` | Ratio of errors to total requests |
| `success_rate` | Ratio of successes to total requests |
| `consecutive_failures` | Failures without an intervening success |
| `quality_score` | Output quality from downstream validation |
| `memory_usage_mb` | Agent memory consumption |
| `last_heartbeat` | Timestamp of the most recent heartbeat |

## Graduated recovery actions

When the platform detects a problem, it picks an appropriate
recovery action from the strategies you've enabled. Behaviour by
strategy:

| Strategy | When it's chosen | What it does |
|--------|-----------|----------|
| `restart_agent` | Transient errors, memory pressure | Graceful restart with session preservation |
| `failover_to_backup` | Agent consistently failing | Brings up a backup agent with identical configuration |
| `reroute_traffic` | Agent degraded but partially working | Redirects mesh routing away from the failing agent |
| `scale_up` | Load-related failures | Increases agent capacity |
| `circuit_breaker` / `quarantine` | Systematic failures, unknown cause | Isolates the agent from the mesh until reviewed |
| `rollback_config` | Failure after a config change | Reverts to the last known-good configuration |

During restart or failover, active sessions are transferred so other
agents' `can_call` rules route to healthy instances and the user
does not experience a disconnection.

## Recovery events

All recovery actions are recorded as audit events:

| Event | When |
|-------|------|
| `healing.triggered` | A health issue is detected |
| `healing.action.taken` | A specific recovery action begins |
| `healing.completed` | The recovery action finishes (success or failure) |

These events create a persistent record for post-incident analysis.

## Interaction with the Manager

Self-healing and the Manager are complementary systems:

| System | Scope | Mechanism |
|--------|-------|-----------|
| **Manager** | Per-session protection | Tracks failed agents per session, prevents routing to known-failing agents |
| **Self-healing** | System-wide recovery | Restarts agents, spawns backups, reroutes traffic globally |

The Manager provides **immediate** per-session protection (stops
routing to a failing agent within the current session). Self-healing
provides **global** recovery (restarts the agent so it works for all
sessions).

## Example: monitoring system with self-healing

```yaml
name: "monitored_swarm"
version: "1.0.0"
architecture: "managed_mesh"

redis:
  host: "localhost"
  port: 6379
  session_ttl: 86400

self_healing:
  enabled: true
  detection_interval: 15
  max_recovery_attempts: 3
  recovery_strategies:
    - "restart_agent"
    - "failover_to_backup"
    - "circuit_breaker"

agents:
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

  analyzer:
    name: "analyzer"
    model: "gpt-4o-mini"
    temperature: 0.1
    prompt: |
      Analyze numeric readings and detect anomalies.
      Flag values that deviate more than 2 standard deviations from the mean.
    yields:
      anomaly_count: "number"
      severity: "string"
    can_call:
      - agent: "alerter"
        condition: "anomaly_count > 0"

  alerter:
    name: "alerter"
    model: "gpt-4o-mini"
    temperature: 0.0
    prompt: |
      Determine alert action based on severity.
      Low: log. Medium: notify. High: escalate to human.
    yields:
      action: "string"
      message: "string"
      escalate: "boolean"
    can_call:
      - agent: "supervisor"
        condition: "escalate == true"

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

If the `analyzer` agent fails (LLM timeout, provider outage),
self-healing:

1. Detects the failure within the configured detection interval.
2. Attempts `restart_agent` — re-initializes the agent with its
   original config.
3. If restart fails, attempts `failover_to_backup` — brings up a
   backup agent.
4. If backup fails, triggers `circuit_breaker` — stops routing to
   the analyzer and logs an alert.
5. Records every action as an audit event.

The `collector` continues running on schedule. When the analyzer
recovers, self-healing restores normal routing automatically.

## Observability for self-healing

Monitor the healing system itself through the observability
dashboard:

```yaml
observability:
  service_name: "my_swarm"
  metrics_retention_minutes: 1440  # 24 hours
```

The dashboard shows:

- Agent health status
- Recovery action history (what was tried, when, success/failure)
- Error rates and response times per agent
- Mesh communication patterns and failures

## Configuration patterns

### Development

```yaml
self_healing:
  enabled: true
  detection_interval: 30            # Less frequent checks
  max_recovery_attempts: 2
  recovery_strategies:
    - "restart_agent"               # Only restart in dev
```

### Production

```yaml
self_healing:
  enabled: true
  detection_interval: 10            # Frequent monitoring
  max_recovery_attempts: 5
  recovery_strategies:
    - "restart_agent"
    - "failover_to_backup"
    - "reroute_traffic"
    - "circuit_breaker"
```

### High availability

```yaml
self_healing:
  enabled: true
  detection_interval: 5             # Near real-time monitoring
  max_recovery_attempts: 10
  recovery_strategies:
    - "restart_agent"
    - "failover_to_backup"
    - "reroute_traffic"
    - "scale_up"
    - "quarantine"
    - "rollback_config"
```

## Key design decisions

**Event-driven, not polling.** The platform reacts as soon as a
failure signal arrives, without waiting for a polling cycle.

**Graduated response.** A transient error triggers a restart.
Systematic failures trigger isolation and traffic rerouting. The
severity of the recovery action matches the severity of the problem.

**Session preservation.** Active sessions are transferred to backup
agents during restart or failover. The user does not experience a
disconnection — the mesh routes traffic to healthy instances
transparently.

**Audit trail.** Every recovery action is recorded with full
context: agent, health status, selected action, current metrics,
backup agent (if spawned), and recovery time. This enables
post-incident analysis: "Which agents required healing? How often?
What actions resolved the issue?"

## Next Steps

- **[Monitoring Patterns](yield-monitoring)** — Build monitoring systems with scheduled agents
- **[Architecture Guide](../core-concepts/architecture)** — How self-healing fits into the control plane
- **[Agent Configuration](../api-reference/agent-config)** — Full YAML reference

---

*LeafMesh — Systems that detect, recover, and learn from failures*
