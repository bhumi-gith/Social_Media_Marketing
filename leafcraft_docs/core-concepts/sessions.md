# Session Management

Sessions are the state containers for multi-turn conversations and multi-agent workflows. They are created automatically, stored in Redis, and provide conversation continuity across agent interactions.

## Automatic Session Management

Sessions are created on first use and reused automatically:

```python
# First call creates the session
result = await leafmesh.mesh_call(
    "solver",
    input_data={"message": "What is 2 + 2?"},
    session_id="user_123"
)

# Second call reuses the session — agent has conversation history
result2 = await leafmesh.mesh_call(
    "solver",
    input_data={"message": "Now multiply that by 3"},
    session_id="user_123"
)
```

Conversation history is injected into agent prompts automatically as user/assistant pairs.

## What Gets Stored

The platform automatically persists per-session state including:

- **Session metadata** — created/updated timestamps, state, configuration snapshot
- **Conversation history** — every message exchanged in the session
- **Agent yields** — declared outputs from each agent, available to downstream agents
- **Mesh communications** — inter-agent call records
- **Coordination decisions** — actions taken by automatic coordination

| Data | TTL |
|------|-----|
| Session metadata + conversation history | `session_ttl` (default 7200s, configurable) |
| Agent yields, mesh communications, coordination decisions | `default_ttl` (default 3600s, configurable) |

All storage is automatic when `auto_storage: true` (the default). No explicit save calls are needed.

## Conversation History Structure

Each entry is a structured record:

```python
{
    "role": "user|assistant|system",
    "content": "The message content",
    "timestamp": "2026-02-26T10:30:00Z",
    "agent_name": "solver",
    "type": "user_message|agent_response|mesh_call|tool_result"
}
```

The `type` field distinguishes between direct user messages, agent LLM responses, inter-agent mesh communications, and tool execution results.

## Inspecting Sessions

Browse session state in **Studio's Sessions tab**, or query it via the REST API:

```bash
curl http://localhost:18820/api/sessions/user_123
curl http://localhost:18820/api/sessions/user_123/history
curl http://localhost:18820/api/sessions/user_123/yields
```

## Using Session Context in Intelligence Functions

The `context` parameter in intelligence functions provides session information:

```python
async def context_aware(llm_response, input_data, context):
    session_id = context.get("session_id", "default")

    # Access yields from upstream agents via input_data
    previous_answer = input_data.get("answer")

    return {
        "response": llm_response.get("response", ""),
        "has_history": previous_answer is not None
    }
```

## Session Threading

For complex workflows where multiple agents work on different aspects simultaneously, the system creates session "threads" that inherit context from parent sessions while maintaining independent execution paths. Thread results are merged back into the parent session on completion.

## Redis Configuration

```yaml
redis:
  host: "localhost"
  port: 6379
  auto_storage: true         # Auto-persist everything (default)
  default_ttl: 3600          # 1 hour for general data
  session_ttl: 7200          # 2 hours for sessions
```

## Next Steps

- **[Session & State](../memory/short-term)** — Detailed Redis persistence patterns
- **[Architecture](architecture)** — How sessions fit in the control plane
- **[Configuration](configuration)** — Redis configuration options

---

*LeafMesh — Automatic session management*
