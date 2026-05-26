# Long-Term Memory

Long-term memory in LeafMesh refers to data that persists beyond individual sessions. While session data has a TTL (default: 2 hours), long-term patterns use extended TTLs configured in YAML.

## How Long-Term Storage Works

LeafMesh auto-stores session data with the configured `session_ttl` and `default_ttl`. For data that needs to persist longer, configure appropriate TTLs in your YAML:

```yaml
redis:
  host: "localhost"
  port: 6379
  auto_storage: true
  default_ttl: 3600        # 1 hour for general data
  session_ttl: 7200        # 2 hours for sessions
```

---

## Smart Memory Strategies

Agents can load relevant context from past interactions before executing. Configure the `memory` field on any agent to control how much history the agent sees and how it selects what to include.

### Enabling Memory

```yaml
agents:
  support_agent:
    name: "support_agent"
    model: "gpt-4o"
    memory:
      strategy: "hybrid"
      limit: 10
      cross_session: true
      cross_session_limit: 50
      relevance_weight: 0.5      # Tunable: weight given to topical relevance
      recency_weight: 0.5        # Tunable: weight given to how recent the post is
      decay_hours: 168           # Tunable: how quickly older posts lose weight
```

Or use the shorthand for simple cases:

```yaml
agents:
  support_agent:
    memory: true               # Enables memory with defaults (strategy: "recent", limit: 10)
```

### Memory Strategies

| Strategy | Behavior | Best For |
|----------|----------|----------|
| `"recent"` | Last N posts from the current session only. Chronological order. | Fast conversational agents, chatbots |
| `"relevant"` | Scores ALL posts (current + cross-session) against the current input. Returns top N by relevance. | Knowledge retrieval, FAQ agents |
| `"hybrid"` | Current session posts always included. Cross-session posts scored for relevance and merged. Deduplicates automatically. | General-purpose agents that need both context and recall |

### How Relevance Scoring Works

When `"relevant"` or `"hybrid"` strategy is used, each past interaction is scored against the current user input. The platform blends two qualitative signals:

- **Topical relevance** — how closely the past interaction matches the current input
- **Recency** — how recently the past interaction occurred

You control how these two signals are balanced via configuration:

- **Higher `relevance_weight`**: Prioritizes topical match
- **Higher `recency_weight`**: Prioritizes recent interactions
- **Lower `decay_hours`**: Memory fades faster (good for fast-moving topics)
- **Higher `decay_hours`**: Memory persists longer (good for reference knowledge)

No vector database is required — recall is fast and works well for most use cases.

### Cross-Session Recall

When `cross_session: true`, the agent can access posts from other sessions within the same system. This enables agents to "remember" past user interactions across separate conversations.

```yaml
memory:
  strategy: "hybrid"
  cross_session: true
  cross_session_limit: 50     # Max cross-session posts to consider
```

Cross-session recall is automatically enabled when using the `"relevant"` strategy. For `"hybrid"`, set `cross_session: true` explicitly.

### Configuration Reference

| Field | Default | Description |
|-------|---------|-------------|
| `strategy` | `"recent"` | Memory selection strategy: `"recent"`, `"relevant"`, or `"hybrid"` |
| `limit` | `10` | Maximum number of memory posts to load into context |
| `cross_session` | `false` | Enable recall from other sessions |
| `cross_session_limit` | `50` | Max cross-session posts to consider for relevance scoring |
| `relevance_weight` | tunable | Weight given to topical relevance (0.0–1.0) |
| `recency_weight` | tunable | Weight given to recency (0.0–1.0) |
| `decay_hours` | tunable | Controls how quickly older posts lose weight |

### Memory in the Agent Prompt

Memory context is automatically injected into the LLM prompt before the agent executes. The agent sees two sections:

1. **Current session** — Recent posts from the active conversation
2. **Relevant history** — Cross-session posts ranked by relevance (if enabled)

You do not need to write any code to access memory. It is loaded and formatted automatically based on your YAML configuration.

---

## Adaptive Thresholds Pattern

Agents can build long-term knowledge through their yields. Each execution's yields are stored in Redis, and downstream agents can use accumulated results:

```python
async def adaptive_analyzer(llm_response, input_data, context):
    readings = input_data.get("readings", [])
    baseline = input_data.get("baseline", {"mean": 100.0, "std": 10.0})

    # Use baseline from input to detect anomalies
    threshold = baseline["mean"] + (2 * baseline["std"])
    flagged = [r for r in readings if r > threshold]

    # Return updated stats as yields — auto-stored in Redis
    return {
        "anomaly_count": len(flagged),
        "severity": "high" if len(flagged) > 2 else "low" if flagged else "none",
        "updated_mean": round(sum(readings) / len(readings), 4) if readings else baseline["mean"]
    }
```

The yields are automatically stored and can be retrieved by downstream agents or via the REST API.

## Session vs Long-Term Data

| Concern | Persistence | TTL |
|---------|------------|-----|
| Conversation history | Automatic | `session_ttl` (2h default) |
| Agent yields | Automatic | `default_ttl` (1h default) |
| Agent memory | Automatic | Configurable via `memory` config |
| Baselines / models | Stored as yields, re-consumed | Configurable via YAML |

## Inspecting Long-Term Data

Browse stored yields and historical state in **Studio's Sessions tab**, or query them via the platform's REST API.

## Next Steps

- **[Short-Term Memory](short-term)** — Session and state management
- **[Memory Retrieval](retrieval)** — How data flows to agents
- **[Redis Integration](redis-integration)** — Redis configuration
- **[State Management](state-management)** — State patterns

---

*LeafMesh — Persistent state beyond sessions*
