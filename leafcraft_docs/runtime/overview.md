# Runtime Overview

The LeafMesh runtime manages your platform lifecycle, event processing, and request handling so you can focus on agent configuration.

## Lifecycle

```
LeafMesh.from_yaml("config.yaml")    # 1. Load & validate config
    │
await leafmesh.start()                # 2. Initialize the platform
    │
await leafmesh.mesh_call(...)         # 3. Process requests
    │
await leafmesh.stop()                 # 4. Graceful shutdown
```

`from_yaml()` loads and validates configuration. `start()` brings the platform online — connections, agent registration, event handlers, schedulers, and observability all activate automatically. `stop()` performs a graceful shutdown.

## Request Execution Pipeline

When `leafmesh.mesh_call()` is called:

1. **Session**: Create or resume the session
2. **Pre-compose**: Run context, input, and others processors (if configured)
3. **Prompt assembly**: Construct structured messages with yields schema
4. **LLM call**: Send to the configured provider
5. **Tool execution**: Process any tool calls from the LLM (loop until done or max reached)
6. **Yields parsing**: Parse LLM response against the agent's yields schema
7. **Condition evaluation**: Evaluate `can_call` rules against parsed yields
8. **Intelligence function**: Run the auto-discovered intelligence function (if registered)
9. **Mesh routing**: Execute downstream agent calls (if conditions match)
10. **Auto-storage**: Persist yields, mesh calls, and conversation automatically

## Public API

LeafMesh exposes a focused public API. Everything underneath — sessions, events, routing, persistence — is managed automatically:

```python
leafmesh = LeafMesh.from_yaml("config.yaml")
await leafmesh.start()

# Execute agent workflows
result = await leafmesh.mesh_call("entry_point", input_data={...}, session_id="...")

# Analytics
stats = leafmesh.get_usage_analytics()    # Event statistics
cache = leafmesh.get_llm_cache_stats()    # LLM cache metrics
agents = leafmesh.get_agent_stats()       # Per-agent metrics

# Discover mesh topology
leafmesh.discover()

await leafmesh.stop()
```

For runtime introspection — session data, agent listings, and the event stream — use **Studio**. The local server exposes `GET /health` for liveness checks:

```bash
curl http://localhost:18820/health
```

## Lazy Initialization

`LeafMesh.from_yaml()` only loads and validates configuration. Network connections, event subscriptions, and background workers come up during `leafmesh.start()`.

## Graceful Shutdown

`leafmesh.stop()` shuts down cleanly — in-flight work is allowed to drain, background tasks are stopped in a safe order, and connections are closed last. This prevents events from being dropped on shutdown.

## Next Steps

- **[Context Engineering](context-engineering)** — Context window management
- **[Runtime Optimization](optimization)** — Performance tuning
- **[Configuration](../core-concepts/configuration)** — Configuration system

---

*LeafMesh — Runtime execution environment*
