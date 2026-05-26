# Message Formatting

The platform controls how messages are formatted before being sent to the LLM. This includes assembling the system prompt, injecting the yields schema, and constructing the conversation history — all automatically based on your YAML config.

## System Message Construction

The system message is automatically constructed from:

1. **Agent prompt**: The `prompt` field from YAML
2. **Yields schema**: Formatted as output instructions so the LLM knows what structure to produce

```yaml
agents:
  solver:
    prompt: |
      You solve math problems step by step.
    yields:
      answer: "number"
      steps: "array"
```

The LLM receives a system message that combines the prompt with instructions to produce output matching the yields schema.

## History Formatting

Conversation history entries are formatted as alternating user/assistant messages:

```
System: You solve math problems step by step. [yields schema]
User: What is 2 + 2?
Assistant: {"answer": 4, "steps": ["2 + 2 = 4"]}
User: Now multiply that by 3
```

Recent messages from the session are included automatically. This provides multi-turn context without exceeding token limits.

## Input Data Formatting

The `input_data` dictionary from `mesh_call()` is formatted as the current user message. The platform serializes the dictionary into a format the LLM can process.

## Pre-Compose Influence

Pre-compose processors run before the message is formatted, modifying what gets sent to the LLM:

```python
async def clean_input(input_data, context):
    """Remove sensitive fields before LLM sees them"""
    cleaned = {k: v for k, v in input_data.items() if k != "api_key"}
    return cleaned
```

## Next Steps

- **[Message System](overview)** — Full message flow
- **[LLM Agents](../agents/llm-agents)** — Agent execution pipeline

---

*LeafMesh — Controlled message construction*
