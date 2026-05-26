# Message Types

Every message in LeafMesh's conversation system has a type that identifies its origin and purpose.

## Type Reference

| Type | Role | Source |
|------|------|--------|
| `user_message` | `user` | Direct user input via `mesh_call()` |
| `agent_response` | `assistant` | Agent's LLM-generated or intelligence-function response |
| `mesh_call` | `system` | Inter-agent mesh communication |
| `tool_result` | `system` | Result from a tool execution |

## Message Structure

```python
{
    "role": "user",                        # OpenAI-compatible role
    "content": "What is 2 + 2?",          # Message content
    "timestamp": "2026-02-26T10:30:00Z",  # ISO 8601 timestamp
    "agent_name": "solver",               # Which agent handled this
    "type": "user_message"                # Message type
}
```

## How Types Are Used

- **Message assembly** formats `user_message` and `agent_response` entries as user/assistant pairs in the LLM message array
- **Session storage** keeps all message types in the conversation history
- **Debugging** uses the `type` and `agent_name` fields to reconstruct the full interaction chain

## Next Steps

- **[Message System](overview)** — How messages are constructed
- **[Session Management](../core-concepts/sessions)** — Conversation history

---

*LeafMesh — Typed, attributed messages*
