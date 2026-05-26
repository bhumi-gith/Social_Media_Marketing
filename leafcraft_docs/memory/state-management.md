# State Management

State in LeafMesh is automatic and stored in Redis. This page covers patterns for working with state within agent executions.

## Automatic State

LeafMesh auto-stores these without explicit calls:
- Session metadata and conversation history
- Agent yields after each execution
- Mesh communications between agents
- Coordination decisions and observations

All of this is configured through YAML:

```yaml
redis:
  host: "localhost"
  port: 6379
  auto_storage: true       # Auto-persist everything (default: true)
  default_ttl: 3600        # 1 hour for general data
  session_ttl: 7200        # 2 hours for sessions
```

## Working with State in Intelligence Functions

Use the `context` and `input_data` parameters to access state:

```python
async def counter_agent(llm_response, input_data, context):
    session_id = context.get("session_id", "default")
    yields = context.get("yields", {})

    return {**llm_response, "session": session_id}
```

## Accessing Upstream Yields

When agent B is called by agent A via `can_call`, agent A's yields are passed as `input_data`:

```python
async def checker(llm_response, input_data, context):
    # input_data contains the upstream agent's yields
    claimed_answer = input_data.get("answer")
    return {"is_correct": claimed_answer == 42}
```

## Session-Scoped Storage

All state in LeafMesh is automatically scoped per session — session metadata, conversation history, agent yields, and mesh communications are kept isolated so different sessions never collide.

These records are managed automatically. Browse them in **Studio's Sessions tab**, or query them via the platform's REST API.

## Next Steps

- **[Short-Term Memory](short-term)** — Full session management
- **[Redis Integration](redis-integration)** — Redis configuration
- **[Context Threading](context-threading)** — Parallel session threads

---

*LeafMesh — Explicit, inspectable state*
