# Message System

LeafMesh's message system manages how data flows between users, agents, and the LLM. The platform automatically constructs structured message arrays from your YAML configuration, conversation history, and input data — you don't write the wiring yourself.

## Message Flow

```
User Input → Message Assembly → LLM Messages Array → Provider
                │
                ├── System prompt (from YAML)
                ├── Yields schema (from YAML)
                ├── Conversation history (auto-injected)
                └── Current input (from mesh_call)
```

## Automatic Message Assembly

The platform assembles the complete message array sent to the LLM:

1. **System message**: The agent's `prompt` field from YAML, plus the yields schema formatted as instructions
2. **History messages**: Recent conversation entries, formatted as user/assistant pairs
3. **User message**: The current `input_data` from `mesh_call()`

This happens automatically — there's no API to call directly.

## Message Types

Messages in the conversation history are categorized by type:

| Type | Description |
|------|-------------|
| `user_message` | Direct user input |
| `agent_response` | Agent LLM response |
| `mesh_call` | Inter-agent communication |
| `tool_result` | Tool execution result |

Each message includes attribution:

```python
{
    "role": "user|assistant|system",
    "content": "The message content",
    "timestamp": "2026-02-26T10:30:00Z",
    "agent_name": "solver",
    "type": "agent_response"
}
```

## Context Window Management

Recent conversation history is automatically injected into each call to provide multi-turn context without exceeding context limits. Older messages roll off as the conversation grows.

## Pre-Compose: Controlling What the LLM Sees

The pre-compose pipeline runs **before** messages are assembled, allowing you to modify the input data:

```python
from leafmesh import pre_compose

async def enrich(input_data, context):
    """Add context before the LLM sees the request"""
    baseline = await database.get_baseline("default")
    return {**input_data, "baseline": baseline}

@pre_compose(input_processor=enrich)
async def analyzer(llm_response, input_data, context):
    return llm_response
```

## Next Steps

- **[Message Types](types)** — Detailed message type reference
- **[Message Routing](routing)** — How messages flow through the mesh
- **[Session Management](../core-concepts/sessions)** — Conversation history storage

---

*LeafMesh — Structured message construction*
