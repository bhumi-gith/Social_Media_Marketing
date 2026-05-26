# Memory & State

LeafMesh automatically manages all session state, conversation history, and agent data in Redis. You configure Redis in YAML and LeafMesh handles everything else.

## Redis Configuration

Configure Redis in your `config.yaml`:

```yaml
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: "${REDIS_PASSWORD}"    # Optional, from environment
  session_ttl: 7200                # Session TTL in seconds (default: 2h)
  default_ttl: 3600                # General data TTL (default: 1h)
  auto_storage: true               # Auto-store sessions and yields (default: true)
```

## What Gets Stored Automatically

When `auto_storage: true` (the default), LeafMesh automatically persists:

| Data | Description | TTL |
|------|-------------|-----|
| Session metadata | Session state and lifecycle | `session_ttl` (2h) |
| Conversation history | Messages between user and agents | `session_ttl` (2h) |
| Agent yields | Structured output from each agent | `default_ttl` (1h) |
| Mesh communications | Agent-to-agent call data | `default_ttl` (1h) |
| Manager decisions | Coordination decisions | `default_ttl` (1h) |

You do not need to manually store or retrieve any of this data. LeafMesh reads and writes it as part of the normal request pipeline.

## Inspecting Data

Browse session activity, agent details, and the global event feed in **Studio's Sessions, Agents, and Activity tabs**. For programmatic access from Python use the SDK:

```python
analytics = leafmesh.get_usage_analytics()
agents    = leafmesh.list_agents()
```

## Reading Upstream Yields in Intelligence Functions

In intelligence functions, upstream agent yields are passed as `input_data`:

```python
async def downstream_agent(llm_response, input_data, context):
    # input_data contains the upstream agent's yields
    upstream_result = input_data.get("analysis")
    return llm_response
```

This happens automatically based on your `can_call` routing rules in YAML. When agent A calls agent B, agent A's yields become agent B's `input_data`.

## Smart Memory

Agents can load relevant context from past interactions before executing. Configure the `memory` field on any agent:

```yaml
agents:
  support_agent:
    memory:
      strategy: "hybrid"           # "recent" | "relevant" | "hybrid"
      limit: 10                    # Max posts to load
      cross_session: true          # Recall from other sessions
      relevance_weight: 0.6        # Tunable relevance weight
      recency_weight: 0.4          # Tunable recency weight
      decay_hours: 168             # Memory decay half-life (tunable)
```

Memory is loaded automatically before agent execution — no code needed. The strategy controls how posts are selected:

- **`"recent"`**: Last N posts, chronological order (current session only)
- **`"relevant"`**: All posts scored against current input, top N returned
- **`"hybrid"`**: Current session always included, cross-session ranked by a tunable relevance + recency blend

The exact weights and decay half-life are configurable per agent — see the link below for tuning guidance.

See **[Smart Memory Strategies](../memory/long-term)** for detailed configuration and tuning.

## Session Continuity

Pass the same `session_id` to `mesh_call` to maintain conversation context:

```python
# First message — creates a new session
result1 = await leafmesh.mesh_call("support", {"message": "My API is down"}, session_id="user_123")

# Follow-up — continues the same session with full history
result2 = await leafmesh.mesh_call("support", {"message": "It's the payments API"}, session_id="user_123")
```

LeafMesh automatically loads conversation history from Redis and includes it in the LLM prompt for context continuity.

## Analytics

Get aggregated usage statistics:

```python
analytics  = leafmesh.get_usage_analytics()
cache_stats = leafmesh.get_llm_cache_stats()
```

## Next Steps

- **[Redis Integration](../memory/redis-integration)** — Redis configuration details
- **[State Management](../memory/state-management)** — State patterns
- **[Short-Term Memory](../memory/short-term)** — Session management

---

*LeafMesh — Memory system reference*
