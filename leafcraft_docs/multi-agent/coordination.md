# Coordination Patterns

LeafMesh provides automatic coordination across a multi-agent chain -- retrying transient failures, halting runaway chains, and escalating decisions that need human review. You tune the behavior through a small set of YAML knobs; the platform handles the rest.

## What the Coordinator Does

The coordinator continuously observes the chain and intervenes when needed. Typical behaviors:

- **Retry** an agent when a call fails transiently (rate limit, transient network error)
- **Halt** the current chain when an unrecoverable error occurs
- **Escalate** to a human reviewer when configured conditions are met
- **Continue** quietly when nothing needs attention -- the most common outcome

All intervention behavior is reactive and deterministic. The coordinator never originates work; it only acts on signals from the agents in flight.

## Coordination Configuration

You control coordinator behavior through `coordination_rules`:

```yaml
manager:
  enabled: true
  model: "gpt-4o-mini"        # Model used for lightweight classification
  coordination_rules:
    max_agent_calls: 10       # Maximum agent calls per session
    max_call_depth: 5         # Maximum chained call depth
    max_retries: 3            # Maximum retries per agent on transient failure
    score_threshold: 0.7      # Minimum classifier confidence to act
```

| Field | Description |
|-------|-------------|
| `max_agent_calls` | Hard cap on the number of agent calls per session. Once reached, no further calls are allowed. |
| `max_call_depth` | Maximum chain depth (A → B → C → ...). Prevents runaway recursive call patterns. |
| `max_retries` | How many times the coordinator may retry a single agent before giving up and escalating or halting. |
| `score_threshold` | The minimum confidence required for the coordinator to take an action other than "continue." |

## Coordination Flow

```
Agent completes (success, failure, timeout, or low-quality output)
    │
    ▼
Coordinator observes the event
    │
    ▼
Classifies the event and decides whether to intervene
    │
    ├── Continue       → No action, chain proceeds normally
    ├── Retry          → Re-run the agent (bounded by max_retries)
    ├── Halt           → Stop the current chain
    └── Escalate       → Route to a human reviewer
```

In normal operation, the coordinator almost always returns "continue" -- intervention is the exception, not the rule.

## Intervention History

Every coordinator decision is recorded and available via the REST API:

```bash
# Query intervention history for a session
curl http://localhost:18820/decisions/{session_id}
```

This provides a complete audit trail of every coordination decision in a session.

## Self-Healing Integration

Coordination operates alongside LeafMesh's self-healing system:

- **Coordinator**: Per-session protection -- tracks failed agents, prevents routing to known-bad targets within the current chain.
- **Self-healing**: System-wide recovery -- restarts failed agents, spawns backups, and reroutes traffic across instances.

Both react to error signals independently and complement each other.

## Next Steps

- **[Self-Healing](../advanced/self-healing)** — Automatic failure recovery
- **[Event System](../core-concepts/events)** — Event delivery and durable history
- **[Mesh Architecture](mesh-architecture)** — Routing infrastructure

---

*LeafMesh — Automatic coordination across multi-agent chains*
