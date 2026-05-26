# Debugging Tools

Techniques for debugging LeafMesh agent systems using Studio, event tracing, and component status queries.

## Inspection

Every agent execution is automatically captured. Debug through:

- **Studio** — Sessions tab for per-session traces, Activity tab for the live event feed, Agents tab for status
- **REST API** — `GET /session/{session_id}` returns the full session record (yields, conversation, mesh calls) for programmatic inspection

## Component Status

Query system health via the health endpoint:

```
GET http://localhost:18820/health
```

```json
{
  "status": "healthy",
  "components": {
    "backend": {"status": "connected", "latency_ms": 2},
    "scheduler": {"status": "running"}
  }
}
```

Agent-level statistics are available via the SDK:

```python
agent_stats = leafmesh.get_agent_stats()
for agent, stats in agent_stats.items():
    print(f"{agent}: calls={stats.get('execution_count')}, errors={stats.get('error_count')}")
```

## Event Tracing

Events are automatically captured and surfaced as a live feed. Watch them in **Studio's Activity tab** — filter by event type (`agent.call.failed`, etc.) or by `session_id`. All agent errors, mesh calls, and lifecycle events are captured automatically.

For programmatic access, use `leafmesh.get_usage_analytics()` for aggregated statistics.

## Common Debugging Scenarios

### Agent Returns Unexpected Output

1. Check yields schema matches what the LLM is producing
2. Inspect the session's conversation history in **Studio's Sessions tab**
3. Verify pre-compose processors are returning expected data

### Chain Not Routing Correctly

1. Check yields values against can_call conditions
2. Verify condition syntax is correct
3. Watch the session's events in **Studio's Activity tab** — filter by `session_id` to see yields and routing decisions in real time

### Agent Timing Out

1. Check LLM provider status
2. Check model configuration (some models are slower)
3. Check tool execution time if tools are involved

### Mesh Call Failing

1. Check that the target agent exists in the configuration
2. Verify the target agent's model/provider is available
3. Check call depth limits
4. Browse the registered agents in **Studio's Agents tab** to confirm what's running

## Health Check Endpoint

The API services expose a health endpoint:

```json
{
  "status": "healthy",
  "components": {
    "backend": {"status": "connected", "latency_ms": 2},
    "scheduler": {"status": "running", "scheduled_agents": 4}
  }
}
```

## Next Steps

- **[Testing Framework](testing)** — Automated testing
- **[Best Practices](best-practices)** — Development guidelines
- **[State Management](../memory/state-management)** — Session state patterns

---

*LeafMesh — Debugging multi-agent systems*
