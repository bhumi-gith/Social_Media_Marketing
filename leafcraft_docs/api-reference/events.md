# Event System

LeafMesh automatically generates events as agents execute, sessions progress, and mesh calls route between agents. You do not need to subscribe to or publish events manually — everything happens automatically based on your YAML configuration.

## Observing Events

Events are emitted in real time and are visible through **Studio's Activity tab** (live feed, agent-, and session-filtered views).

### Programmatic access

Use the Python SDK for aggregated statistics:

```python
analytics  = leafmesh.get_usage_analytics()
cache_stats = leafmesh.get_llm_cache_stats()
```

For raw events, subscribe via the SSE endpoint exposed by the API server and filter on `event.type`.

## Event Types

LeafMesh generates events across several categories. These are emitted automatically — you observe them through the SSE endpoint or activity feed.

### Session Events
| Event | When |
|-------|------|
| `session.created` | New session created |
| `session.updated` | Session data updated |
| `session.completed` | Session completed |
| `session.expired` | Session TTL expired |

### Agent Events
| Event | When |
|-------|------|
| `agent.registered` | Agent registered during startup |
| `agent.activated` | Agent activated |
| `agent.deactivated` | Agent deactivated |
| `agent.call.started` | Agent begins processing a request |
| `agent.call.completed` | Agent finishes processing |
| `agent.call.failed` | Agent execution failed |
| `agent.yields.stored` | Agent yields stored in Redis |

### Mesh Events
| Event | When |
|-------|------|
| `mesh.call.started` | Agent-to-agent call initiated |
| `mesh.call.completed` | Agent-to-agent call completed |
| `mesh.call.failed` | Agent-to-agent call failed |

### LLM Events
| Event | When |
|-------|------|
| `llm.request` | LLM call initiated |
| `llm.response` | LLM response received |
| `llm.cache.hit` | Response served from cache |
| `llm.cost.tracked` | Token cost recorded |

### Workflow Events
| Event | When |
|-------|------|
| `workflow.step.started` | Workflow step begins |
| `workflow.step.completed` | Workflow step finishes |
| `workflow.paused` | Workflow paused (e.g., human-in-the-loop) |
| `workflow.resumed` | Workflow resumed |
| `workflow.complete` | Entire workflow finished |

### Human-in-the-Loop Events
| Event | When |
|-------|------|
| `human.input.requested` | Human agent triggered |
| `human.input.received` | Human responded |
| `human.input.timeout` | Human did not respond in time |

### System Events
| Event | When |
|-------|------|
| `system.started` | Platform started |
| `system.stopped` | Platform stopped |
| `config.loaded` | Configuration loaded |

### Self-Healing Events
| Event | When |
|-------|------|
| `healing.triggered` | Health issue detected |
| `healing.action.taken` | Recovery action executed |
| `healing.completed` | Recovery completed |

## How It Works

All events are emitted automatically as your agents execute. LeafMesh manages event routing and delivery internally. You interact with events through:

1. **Studio's Activity tab** — live feed and paginated history
2. **`leafmesh.get_usage_analytics()`** — aggregated statistics from Python
3. **SSE endpoint** — real-time stream for custom integrations

No manual event subscription or publishing is needed.

## Next Steps

- **[Core API](core-adk)** — LeafMesh reference
- **[Configuration](configuration)** — YAML configuration reference

---

*LeafMesh — Event system reference*
