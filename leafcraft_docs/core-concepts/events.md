# Event System

LeafMesh uses an event-driven architecture. Events are emitted automatically as agents execute, sessions progress, and mesh calls flow through the system. Customers consume events via a Server-Sent Events (SSE) endpoint.

## How Events Work

Events are emitted automatically. You do not need to publish or subscribe to events in your application code — the platform handles emission internally. To observe events externally, use the REST API's SSE endpoint.

## Event Categories

Events fall into a small number of high-level categories that you can subscribe to:

| Category | When |
|----------|------|
| `agent.*` | Agent lifecycle and execution (responses, errors, wake-ups) |
| `mesh.*` | Inter-agent calls and routing |
| `session.*` | Session lifecycle (created, updated, timed out, completed) |
| `workflow.*` | Workflow-level events (paused, resumed) |
| `human.*` | Human-in-the-loop events (input requested/received/timed out, handoff, escalation, connection state) |
| `manager.*` | Coordination decisions and interventions |
| `system.*` | System and configuration lifecycle |

## Observing Events via REST API

The API server (default port `18820`) provides an SSE endpoint for real-time event streaming:

```bash
# Stream all events in real time
curl -N http://localhost:18820/api/events/stream

# Stream events for a specific session
curl -N http://localhost:18820/api/events/stream?session_id=user_123
```

From a browser or frontend application:

```javascript
const eventSource = new EventSource("http://localhost:18820/api/events/stream");
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Event: ${data.type}`, data);
};
```

## Analytics

Aggregate analytics are exposed through SDK convenience methods:

- `leafmesh.get_usage_analytics()` — aggregated stats across event categories
- `leafmesh.get_llm_cache_stats()` — cache performance summary

## Event Flow Example

When an agent completes execution, a cascade of events fires through the internal event backbone — the agent response is observed, automatic coordination classifies the event, and (if needed) intervention or follow-up events are emitted. The entire cascade is asynchronous, so it does not block the original agent call.

For normal-flow events (no intervention needed), the overhead is negligible.

## Next Steps

- **[Architecture](architecture)** — How events flow through the control plane
- **[Session Management](sessions)** — Event-driven session lifecycle
- **[Self-Healing](../advanced/self-healing)** — Event-driven failure detection

---

*LeafMesh — Event-driven coordination*
